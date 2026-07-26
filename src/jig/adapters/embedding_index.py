"""向量检索索引 — 语义搜索 Skill 定义。

第 3 层压缩：通过 embedding 检索相关 skill body 注入上下文。
支持离线降级（token 关键词匹配）。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EmbeddingIndex:
    """Skill 语义检索索引。

    为 skill body 建立索引，通过语义搜索按需召回最相关的 skill。
    离线降级模式：用关键词匹配替代 embedding。

    Usage:
        index = EmbeddingIndex()
        index.add_skills(skill_defs)
        results = index.search("如何写 PRD", top_k=3)
    """

    def __init__(self, use_embedding: bool = False) -> None:
        """
        Args:
            use_embedding: True = 用 sentence-transformers 做向量检索
                           False = 离线关键词匹配降级
        """
        self._use_embedding = use_embedding
        self._docs: List[Dict[str, Any]] = []  # [{name, body, tags}]
        self._embeddings: List[List[float]] = []
        self._encoder = None

        if use_embedding:
            self._init_encoder()

    def _init_encoder(self) -> None:
        """初始化 embedding 编码器。"""
        try:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("embedding 编码器已加载: all-MiniLM-L6-v2")
        except ImportError:
            logger.warning("sentence-transformers 未安装, 降级到关键词匹配")
            self._use_embedding = False

    def add_skills(self, skill_defs: List) -> None:
        """添加多个 SkillDef 到索引。"""
        for sk in skill_defs:
            self._docs.append({
                "name": sk.name,
                "body": sk.body or sk.description,
                "tags": list(sk.tags) if hasattr(sk, "tags") else [],
                "agent_name": getattr(sk, "agent_name", None) or sk.name,
            })

        if self._use_embedding and self._encoder:
            texts = [d["body"] for d in self._docs]
            self._embeddings = self._encoder.encode(texts).tolist()

        logger.info("embedding 索引已更新: %d 个文档", len(self._docs))

    def add_skill(self, skill_def) -> None:
        """添加单个 SkillDef。"""
        self.add_skills([skill_def])

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索最相关的 skill。

        Args:
            query: 搜索查询
            top_k: 返回结果数

        Returns:
            按相关性排序的 skill 列表 [{name, agent_name, body[:200], score}]
        """
        if not self._docs:
            return []

        if self._use_embedding and self._encoder:
            return self._search_vector(query, top_k)
        else:
            return self._search_keyword(query, top_k)

    def _search_vector(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """向量检索（余弦相似度）。"""
        import numpy as np
        q_vec = np.array(self._encoder.encode([query])[0])
        scores = []
        for i, doc in enumerate(self._docs):
            d_vec = np.array(self._embeddings[i])
            cos_sim = np.dot(q_vec, d_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(d_vec) + 1e-8)
            scores.append((i, float(cos_sim)))

        scores.sort(key=lambda x: -x[1])
        return [
            {
                **self._docs[i],
                "body": self._docs[i]["body"][:200],
                "score": round(s, 4),
            }
            for i, s in scores[:top_k]
        ]

    def _search_keyword(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """关键词匹配降级检索。"""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored = []
        for doc in self._docs:
            body_lower = doc["body"].lower()
            # 关键词命中计数
            hits = sum(1 for w in query_words if w in body_lower)
            # 名称命中加成
            name_hit = 5 if doc["name"].lower() in query_lower else 0
            score = hits + name_hit
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: -x[0])
        return [
            {
                **doc,
                "body": doc["body"][:200],
                "score": s,
            }
            for s, doc in scored[:top_k]
        ]

    def count(self) -> int:
        """索引文档数。"""
        return len(self._docs)
