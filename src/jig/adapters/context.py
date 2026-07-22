"""三层 Context 分区架构。

Task 7: 将 API context 分为 immutable/append-only/volatile 三区。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class PartitionedContext:
    """分区后的上下文。"""
    immutable: List[Dict[str, Any]] = field(default_factory=list)
    append_only: List[Dict[str, Any]] = field(default_factory=list)
    volatile: List[Dict[str, Any]] = field(default_factory=list)

    def to_api_messages(self) -> List[Dict[str, Any]]:
        """合并为完整的 API 消息列表（volatile 区不发给 API）。"""
        return self.immutable + self.append_only


class ContextPartitioner:
    """三层 Context 分区器。

    | 区 | 内容 | 缓存行为 |
    |----|------|---------|
    | 不可变前缀 | system + tools + memory | 整 session 命中缓存 |
    | 追加日志 | 对话历史（append-only） | 稳定增长，只有尾部 miss |
    | 易失暂存 | 推理过程、临时计划 | 不发给 API |
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._immutable: List[Dict[str, Any]] = []
        self._append_only: List[Dict[str, Any]] = []
        self._volatile: List[Dict[str, Any]] = []
        self._immutable_frozen = False

    def set_immutable(self, system_prompt: str, tools: List[Dict[str, Any]], memory: str) -> None:
        """设置不可变前缀（系统提示词 + 工具 + 记忆）。

        CTX-PART-001.2: immutable 区整 session 字节级不变。

        Args:
            system_prompt: 系统提示词。
            tools: 工具定义列表。
            memory: 持久化记忆。

        Raises:
            RuntimeError: 不可变区已冻结后再次设置。
        """
        if self._immutable_frozen:
            raise RuntimeError(
                f"不可变前缀在 session {self._session_id} 中已冻结，不可修改"
            )

        self._immutable.append({"role": "system", "content": system_prompt})

        if memory:
            self._immutable.append({"role": "system", "content": f"[Memory]\n{memory}"})

        if tools:
            self._immutable.append({"role": "system", "content": f"[Tools]\n{json.dumps(tools, indent=2)}"})

        self._immutable_frozen = True
        logger.info(
            "不可变前缀已设置: session=%s, %d 条消息",
            self._session_id,
            len(self._immutable),
        )

    def append_message(self, message: Dict[str, Any]) -> None:
        """追加一条消息到对话历史。

        CTX-PART-001: append-only 区稳定增长。
        """
        self._append_only.append(message)

    def set_volatile(self, data: Dict[str, Any]) -> None:
        """设置易失暂存数据（不发给 API）。"""
        self._volatile = [data]

    def add_volatile_note(self, key: str, value: Any) -> None:
        """添加一条易失暂存笔记。"""
        if not self._volatile:
            self._volatile = [{}]
        self._volatile[0][key] = value

    def get_partitioned(self) -> PartitionedContext:
        """获取分区后的上下文。"""
        return PartitionedContext(
            immutable=list(self._immutable),
            append_only=list(self._append_only),
            volatile=list(self._volatile),
        )

    def build_api_messages(self) -> List[Dict[str, Any]]:
        """构建 API 请求的消息列表（volatile 区排除）。"""
        return self.get_partitioned().to_api_messages()

    def clear_append_only(self) -> None:
        """清空追加日志（用于 session 压缩）。"""
        self._append_only.clear()
        logger.info("append-only 区已清空: session=%s", self._session_id)

    def clear_volatile(self) -> None:
        """清空易失暂存区。"""
        self._volatile.clear()

    @property
    def total_message_count(self) -> int:
        """消息总数（不含 volatile）。"""
        return len(self._immutable) + len(self._append_only)

    @property
    def immutable_frozen(self) -> bool:
        return self._immutable_frozen

    def auto_compress_threshold(self, threshold: int = 8000) -> None:
        """设置自动压缩 token 阈值。"""
        self._auto_compress_threshold = threshold

    def estimated_tokens(self) -> int:
        """粗略估算当前上下文 token 数。"""
        return self.total_message_count * 50  # 粗略: 每消息约 50 token

    def compress_if_needed(self, compressor=None) -> bool:
        """如超过阈值则自动压缩。"""
        if not hasattr(self, '_auto_compress_threshold'):
            self._auto_compress_threshold = 8000
        est = self.estimated_tokens()
        if est <= self._auto_compress_threshold:
            return False
        if compressor is not None:
            all_msgs = self._immutable + self._append_only
            compressed = compressor.compress(all_msgs)
            # 重新分区
            self._immutable = [m for m in compressed if m.get('role') == 'system']
            self._append_only = [m for m in compressed if m.get('role') != 'system']
            return True
        return False

