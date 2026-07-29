"""SQLiteCheckpointStore — Durable checkpoint storage.

Replaces file-based JSON checkpoints with SQLite-backed persistence.
Supports interrupt/resume from any completed node.
"""

from __future__ import annotations
import json
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class SQLiteCheckpointStore:
    """SQLite-backed checkpoint store for durable execution."""

    def __init__(self, db_path: str = ".sop_checkpoints.db"):
        self._db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                session_id TEXT PRIMARY KEY,
                current_node_idx INTEGER NOT NULL DEFAULT 0,
                completed_nodes TEXT NOT NULL DEFAULT '[]',
                context TEXT NOT NULL DEFAULT '{}',
                retry_count INTEGER NOT NULL DEFAULT 0,
                escalate_level INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS node_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                node_name TEXT NOT NULL,
                output TEXT,
                error TEXT,
                duration_ms INTEGER,
                timestamp TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def save(self, session_id: str, checkpoint: dict) -> None:
        now = datetime.utcnow().isoformat()
        self._conn.execute("""
            INSERT INTO checkpoints (session_id, current_node_idx, completed_nodes,
                                     context, retry_count, escalate_level, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                current_node_idx=excluded.current_node_idx,
                completed_nodes=excluded.completed_nodes,
                context=excluded.context,
                retry_count=excluded.retry_count,
                escalate_level=excluded.escalate_level,
                updated_at=excluded.updated_at
        """, (
            session_id,
            checkpoint.get("current_node_idx", 0),
            json.dumps(checkpoint.get("completed_nodes", [])),
            json.dumps(checkpoint.get("context", {})),
            checkpoint.get("retry_count", 0),
            checkpoint.get("escalate_level", 0),
            now, now
        ))
        self._conn.commit()

    def load(self, session_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM checkpoints WHERE session_id = ?", (session_id,)
        ).fetchone()
        if not row:
            return None
        return {
            "session_id": row[0],
            "current_node_idx": row[1],
            "completed_nodes": json.loads(row[2]),
            "context": json.loads(row[3]),
            "retry_count": row[4],
            "escalate_level": row[5],
            "created_at": row[6],
            "updated_at": row[7],
        }

    def list_sessions(self) -> List[dict]:
        rows = self._conn.execute(
            "SELECT session_id, current_node_idx, updated_at FROM checkpoints ORDER BY updated_at DESC"
        ).fetchall()
        return [
            {"session_id": r[0], "current_node_idx": r[1], "updated_at": r[2]}
            for r in rows
        ]

    def save_node_result(self, session_id: str, node_name: str,
                         output: str = "", error: str = "",
                         duration_ms: int = 0) -> None:
        self._conn.execute("""
            INSERT INTO node_results (session_id, node_name, output, error,
                                      duration_ms, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, node_name, output, error, duration_ms,
              datetime.utcnow().isoformat()))
        self._conn.commit()

    def get_node_results(self, session_id: str) -> List[dict]:
        rows = self._conn.execute(
            "SELECT node_name, output, error, duration_ms, timestamp FROM node_results "
            "WHERE session_id = ? ORDER BY id", (session_id,)
        ).fetchall()
        return [
            {"node_name": r[0], "output": r[1], "error": r[2],
             "duration_ms": r[3], "timestamp": r[4]}
            for r in rows
        ]

    def delete(self, session_id: str) -> None:
        self._conn.execute("DELETE FROM checkpoints WHERE session_id = ?", (session_id,))
        self._conn.execute("DELETE FROM node_results WHERE session_id = ?", (session_id,))
        self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
