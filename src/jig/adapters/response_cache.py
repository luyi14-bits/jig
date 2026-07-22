"""响应缓存 — 相同输入重复请求返回缓存结果。

IDEA-039: 减少重复 API 调用，降低成本。
"""

from __future__ import annotations
import hashlib
import time
from typing import Any, Dict, Optional


class ResponseCache:
    """简单响应缓存，基于 prompt hash 的精确匹配。"""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds

    def _hash(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()

    def get(self, prompt: str) -> Optional[str]:
        key = self._hash(prompt)
        entry = self._cache.get(key)
        if entry and time.time() - entry["ts"] < self._ttl:
            return entry["result"]
        return None

    def set(self, prompt: str, result: str) -> None:
        key = self._hash(prompt)
        self._cache[key] = {"result": result, "ts": time.time()}

    def clear(self) -> None:
        self._cache.clear()
