"""缓存引擎 — 前缀组装、字节级不变性保障、诊断。

Task 5: 
- 固定顺序前缀组装：base prompt → output style → language → memory → skill index
- 前缀 hash 快照对比，检测变更
- <memory-update> XML 块机制
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PrefixSnapshot:
    """前缀快照，用于检测缓存前缀是否发生变化。"""
    hash: str
    segments: Dict[str, str] = field(default_factory=dict)
    assembled: str = ""

    def matches(self, other: "PrefixSnapshot") -> bool:
        return self.hash == other.hash


@dataclass
class CacheDiagnostic:
    """缓存诊断记录。"""
    prefix_changed: bool = False
    change_reasons: List[str] = field(default_factory=list)
    session_hit_rate: float = 0.0
    total_requests: int = 0
    cached_requests: int = 0
    prefix_snapshot: Optional[PrefixSnapshot] = None
    previous_prefix_hash: Optional[str] = None


class CacheEngine:
    """缓存前缀引擎。

    负责组装和管理 DeepSeek 缓存前缀，确保 session 内字节级不变性。
    """

    PREFIX_ORDER = ["base_prompt", "output_style", "language", "memory", "skill_index"]

    def __init__(self) -> None:
        self._current_snapshot: Optional[PrefixSnapshot] = None
        self._previous_snapshot: Optional[PrefixSnapshot] = None
        self._diagnostic = CacheDiagnostic()

    def assemble_prefix(
        self,
        base_prompt: str,
        output_style: str = "",
        language: str = "",
        memory: str = "",
        skill_index: str = "",
    ) -> PrefixSnapshot:
        """按固定顺序组装缓存前缀。

        FR-4.1: 前缀组装顺序固定。
        FR-4.2: skill 正文不进缓存前缀（skill_index 仅含 name + description）。

        Args:
            base_prompt: 基础系统提示词。
            output_style: 输出风格指令。
            language: 语言偏好。
            memory: 持久化记忆内容。
            skill_index: skill 索引（仅 name + description，不含正文）。

        Returns:
            组装后的前缀快照（含 hash）。
        """
        segments = {
            "base_prompt": base_prompt,
            "output_style": output_style,
            "language": language,
            "memory": memory,
            "skill_index": skill_index,
        }

        assembled = self._join_segments(segments)
        hash_value = self._hash(assembled)

        snapshot = PrefixSnapshot(
            hash=hash_value,
            segments=segments,
            assembled=assembled,
        )

        # 检测前缀变更
        self._detect_change(snapshot)

        # 更新诊断
        self._diagnostic.prefix_snapshot = snapshot
        self._diagnostic.total_requests += 1

        self._previous_snapshot = self._current_snapshot
        self._current_snapshot = snapshot

        return snapshot

    def create_memory_update_block(self, update_content: str) -> str:
        """创建 <memory-update> XML 块。

        FR-4.3: 记忆更新走 XML 块附着 user turn，不进前缀。
        """
        return f"<memory-update>\n{update_content}\n</memory-update>"

    def record_cache_hit(self) -> None:
        """记录一次缓存命中。"""
        self._diagnostic.cached_requests += 1

    @property
    def diagnostic(self) -> CacheDiagnostic:
        """获取当前诊断数据。"""
        if self._diagnostic.total_requests > 0:
            self._diagnostic.session_hit_rate = (
                self._diagnostic.cached_requests / self._diagnostic.total_requests
            )
        return self._diagnostic

    def _join_segments(self, segments: Dict[str, str]) -> str:
        """按固定顺序拼接各段。

        使用分隔符确保段之间不会混淆。
        """
        parts = []
        for key in self.PREFIX_ORDER:
            value = segments.get(key, "")
            if value:
                parts.append(f"<!-- {key} -->\n{value}\n")
        return "\n".join(parts)

    def _hash(self, content: str) -> str:
        """计算前缀内容的 SHA-256 hash。"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _detect_change(self, new_snapshot: PrefixSnapshot) -> None:
        """检测前缀是否发生变化。"""
        if self._previous_snapshot is None:
            self._diagnostic.prefix_changed = False
            return

        old_hash = self._previous_snapshot.hash
        new_hash = new_snapshot.hash

        if old_hash != new_hash:
            self._diagnostic.prefix_changed = True
            self._diagnostic.previous_prefix_hash = old_hash

            # 定位变化段
            for key in self.PREFIX_ORDER:
                old_val = self._previous_snapshot.segments.get(key, "")
                new_val = new_snapshot.segments.get(key, "")
                if old_val != new_val:
                    self._diagnostic.change_reasons.append(
                        f"{key}: 长度 {len(old_val)} → {len(new_val)}"
                    )

            logger.warning(
                "缓存前缀变更! hash: %s → %s, reasons: %s",
                old_hash[:12],
                new_hash[:12],
                "; ".join(self._diagnostic.change_reasons),
            )
        else:
            self._diagnostic.prefix_changed = False
            self._diagnostic.change_reasons.clear()

    def mark_cache_breakpoint(self, segment_key: str = "") -> str:
        """插入缓存断点标记（DeepSeek/Anthropic 风格）。"""
        if segment_key:
            return f"<!-- cache_breakpoint: {segment_key} -->"
        return "<!-- cache_control: ephemeral -->"

    def keepalive(self) -> None:
        """定时 ping 防缓存过期。"""
        logger.debug("Cache keepalive ping")

    @property
    def stats(self) -> 'CacheStats':
        """当前缓存统计。"""
        diag = self.diagnostic
        saved = diag.cached_requests * 0.02
        return CacheStats(
            hit_rate=diag.session_hit_rate,
            total_requests=diag.total_requests,
            cached_requests=diag.cached_requests,
            estimated_savings_usd=round(saved, 4),
        )


@dataclass
class CacheStats:
    """缓存统计数据。"""
    hit_rate: float = 0.0
    total_requests: int = 0
    cached_requests: int = 0
    estimated_savings_usd: float = 0.0

