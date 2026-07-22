"""MemoryManager — 统一记忆管线。

整合 CacheEngine / ContextPartitioner / EmbeddingIndex / ConversationCompressor。
三层架构：LocalStore(SQLite) → MemoryRouter(分层路由) → Consolidator(老化/合并)。
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LocalStore:
    """SQLite 持久化存储 — zero-dependency。

    三个表：
    - profiles: agent TEXT, key TEXT, value_json TEXT, updated_at REAL
    - sessions: session_id TEXT UNIQUE, metadata_json TEXT, created_at REAL
    - memory_log: id INTEGER PK, agent TEXT, type TEXT, content_json TEXT, created_at REAL
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = str(Path.home() / ".tree-sop" / "memory.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_tables()

    def _init_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS profiles (
                agent TEXT NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (agent, key)
            );
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT UNIQUE NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memory_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT NOT NULL,
                type TEXT NOT NULL,
                content_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memory_log_agent ON memory_log(agent);
            CREATE INDEX IF NOT EXISTS idx_memory_log_type ON memory_log(type);
        """)
        self._conn.commit()

    # ── Profiles ──
    def set_profile(self, agent: str, key: str, value: Any) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO profiles (agent, key, value_json, updated_at) VALUES (?, ?, ?, ?)",
            (agent, key, json.dumps(value), time.time()),
        )
        self._conn.commit()

    def get_profile(self, agent: str, key: str, default: Any = None) -> Any:
        row = self._conn.execute(
            "SELECT value_json FROM profiles WHERE agent=? AND key=?", (agent, key)
        ).fetchone()
        return json.loads(row[0]) if row else default

    def get_all_profiles(self, agent: str) -> Dict[str, Any]:
        rows = self._conn.execute(
            "SELECT key, value_json FROM profiles WHERE agent=?", (agent,)
        ).fetchall()
        return {row[0]: json.loads(row[1]) for row in rows}

    # ── Sessions ──
    def save_session(self, session_id: str, metadata: Dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO sessions (session_id, metadata_json, created_at) VALUES (?, ?, ?)",
            (session_id, json.dumps(metadata), time.time()),
        )
        self._conn.commit()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT metadata_json FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    # ── Memory Log ──
    def log_memory(self, agent: str, mem_type: str, content: Dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO memory_log (agent, type, content_json, created_at) VALUES (?, ?, ?, ?)",
            (agent, mem_type, json.dumps(content), time.time()),
        )
        self._conn.commit()

    def query_memory(
        self, agent: str = "", mem_type: str = "", limit: int = 50
    ) -> List[Dict[str, Any]]:
        conditions = []
        params = []
        if agent:
            conditions.append("agent=?")
            params.append(agent)
        if mem_type:
            conditions.append("type=?")
            params.append(mem_type)
        where = " AND ".join(conditions) if conditions else "1=1"
        rows = self._conn.execute(
            f"SELECT agent, type, content_json, created_at FROM memory_log WHERE {where} ORDER BY created_at DESC LIMIT ?",
            params + [limit],
        ).fetchall()
        return [
            {"agent": r[0], "type": r[1], "content": json.loads(r[2]), "created_at": r[3]}
            for r in rows
        ]

    def close(self) -> None:
        self._conn.close()


class MemoryRouter:
    """分层记忆路由。

    working    → ContextPartitioner.immutable（现有，不变）
    summary    → ConversationCompressor（Flash 摘要升级）
    episodic   → SQLite memory_log（新增）
    semantic   → EmbeddingIndex（增强，加对话索引）
    """

    def __init__(self, store: LocalStore) -> None:
        self._store = store

    def route(self, mem_type: str, agent: str, content: Dict[str, Any]) -> str:
        """路由一条记忆到对应层。

        Args:
            mem_type: working / summary / episodic / semantic
            agent: Agent 名称
            content: 记忆内容

        Returns:
            存储位置描述（用于日志）
        """
        if mem_type == "working":
            # 已由 ContextPartitioner 处理，不需额外存储
            return "context_partitioner.immutable"

        if mem_type == "summary":
            self._store.log_memory(agent, "summary", content)
            return f"sqlite.memory_log (summary)"

        if mem_type == "episodic":
            self._store.log_memory(agent, "episodic", content)
            return f"sqlite.memory_log (episodic)"

        if mem_type == "semantic":
            # EmbeddingIndex 由外部调用 add_conversation
            self._store.log_memory(agent, "semantic", content)
            return f"sqlite.memory_log (semantic) + EmbeddingIndex"

        raise ValueError(f"Unknown memory type: {mem_type}")


class Consolidator:
    """记忆合并与老化。

    forget() — 基于访问频率和时效性评分，低价值记忆标记删除。
    merge()  — 相同 topic 的连续摘要合并为一条综合摘要。
    """

    def __init__(self, store: LocalStore) -> None:
        self._store = store

    def forget(self, agent: str = "", threshold_days: int = 30) -> int:
        """删除低价值记忆。

        Args:
            agent: 指定 Agent（空=全部）
            threshold_days: 超过此天数的旧记忆被删除

        Returns:
            删除条数
        """
        cutoff = time.time() - threshold_days * 86400
        if agent:
            deleted = self._store._conn.execute(
                "DELETE FROM memory_log WHERE agent=? AND created_at<?", (agent, cutoff)
            ).rowcount
        else:
            deleted = self._store._conn.execute(
                "DELETE FROM memory_log WHERE created_at<?", (cutoff,)
            ).rowcount
        self._store._conn.commit()
        logger.info("Forget: 删除了 %d 条记忆 (agent=%s, >%d天)", deleted, agent or "*", threshold_days)
        return deleted

    def merge(self, agent: str, topic: str) -> bool:
        """合并同一 topic 的连续摘要。

        Args:
            agent: Agent 名称
            topic: 主题关键词

        Returns:
            是否执行了合并
        """
        rows = self._store._conn.execute(
            "SELECT id, content_json FROM memory_log WHERE agent=? AND type='summary' ORDER BY created_at ASC LIMIT 20",
            (agent,),
        ).fetchall()
        if len(rows) < 2:
            return False

        # 提取包含 topic 的条目
        relevant = []
        for rid, cj in rows:
            content = json.loads(cj)
            summary_text = content.get("summary", "") if isinstance(content, dict) else str(content)
            if topic.lower() in summary_text.lower():
                relevant.append((rid, summary_text))

        if len(relevant) < 2:
            return False

        # 合并为一条综合摘要
        merged = " | ".join([s for _, s in relevant])
        new_content = {"summary": f"[合并] {topic}: {merged}", "merged_from": [r[0] for r in relevant]}
        self._store.log_memory(agent, "summary", new_content)

        # 删除原条目
        ids = [r[0] for r in relevant]
        placeholders = ",".join("?" * len(ids))
        self._store._conn.execute(
            f"DELETE FROM memory_log WHERE id IN ({placeholders})", ids
        )
        self._store._conn.commit()
        logger.info("Merge: 合并了 %d 条 '%s' 摘要为 1 条", len(relevant), topic)
        return True
