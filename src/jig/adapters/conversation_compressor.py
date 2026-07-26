"""对话压缩器 — 长对话历史自动压缩。

第 4 层压缩：当对话超过阈值时，用 LLM 摘要中间轮次。
支持三种模式：summarize / truncate / hybrid。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConversationCompressor:
    """对话历史压缩器。

    当 append-only 区超过 max_history_tokens 时，自动压缩中间轮次。

    Usage:
        compressor = ConversationCompressor(mode="hybrid")
        compressed = compressor.compress(messages, model="deepseek-v4-flash")
        print(f"压缩率: {compressor.compression_ratio:.0%}")
    """

    def __init__(
        self,
        mode: str = "hybrid",
        max_history_tokens: int = 8000,
        keep_last_n: int = 3,
    ) -> None:
        """
        Args:
            mode: summarize / truncate / hybrid
            max_history_tokens: 触发压缩的 token 阈值
            keep_last_n: hybrid 模式下保留的最后轮数
        """
        self.mode = mode
        self.max_history_tokens = max_history_tokens
        self.keep_last_n = keep_last_n
        self._original_token_count = 0
        self._compressed_token_count = 0

    def compress(self, messages: List[Dict[str, Any]], model: str = "deepseek-v4-flash") -> List[Dict[str, Any]]:
        """压缩对话历史。

        Args:
            messages: 完整消息列表（含 system prompt + 历史 + 最近轮次）
            model: 模型名称（当前未实际调用 LLM，保留接口）

        Returns:
            压缩后的消息列表。
        """
        if not messages:
            return messages

        # 估算 token 数
        self._original_token_count = self._estimate_tokens(messages)

        # 如果未超阈值，不压缩
        if self._original_token_count <= self.max_history_tokens:
            self._compressed_token_count = self._original_token_count
            return messages

        # 分离 system prompt 和对话历史
        system_msgs = [m for m in messages if m.get("role") == "system"]
        history = [m for m in messages if m.get("role") != "system"]

        if not history:
            self._compressed_token_count = self._original_token_count
            return messages

        if self.mode == "truncate":
            result = self._truncate(system_msgs, history)
        elif self.mode == "summarize":
            result = self._summarize(system_msgs, history, model)
        else:  # hybrid
            result = self._hybrid(system_msgs, history, model)

        self._compressed_token_count = self._estimate_tokens(result)
        logger.info(
            "对话压缩: %s 模式, %d → %d tokens (压缩率 %.0f%%)",
            self.mode,
            self._original_token_count,
            self._compressed_token_count,
            self.compression_ratio * 100,
        )
        return result

    @property
    def compression_ratio(self) -> float:
        """压缩率：0.0 = 完全压缩, 1.0 = 未压缩。"""
        if self._original_token_count == 0:
            return 1.0
        return 1.0 - (self._original_token_count - self._compressed_token_count) / self._original_token_count

    def _truncate(self, system_msgs: List[Dict], history: List[Dict]) -> List[Dict]:
        """截断模式：保留最后 keep_last_n 轮。"""
        return system_msgs + history[-(self.keep_last_n * 2):]

    def _summarize(self, system_msgs: List[Dict], history: List[Dict], model: str) -> List[Dict]:
        """摘要模式：历史全部替换为一条摘要消息。"""
        summary_text = self._make_summary(history, model)
        summary_msg = {"role": "system", "content": f"[对话摘要]\n{summary_text}"}
        return system_msgs + [summary_msg]

    def _hybrid(self, system_msgs: List[Dict], history: List[Dict], model: str) -> List[Dict]:
        """混合模式：历史中间部分摘要 + 保留最后 keep_last_n 轮。"""
        if len(history) <= self.keep_last_n * 2:
            return system_msgs + history

        keep = history[-(self.keep_last_n * 2):]
        middle = history[:-(self.keep_last_n * 2)]

        if middle:
            summary_text = self._make_summary(middle, model)
            summary_msg = {"role": "system", "content": f"[对话摘要]\n{summary_text}"}
            return system_msgs + [summary_msg] + keep

        return system_msgs + keep

    def _make_summary(self, messages: List[Dict], model: str) -> str:
        """生成对话摘要。

        当前为离线降级模式：提取关键决策点。
        生产环境应调用 DeepSeek Flash 做 LLM 摘要。
        """
        decisions = []
        actions = []
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, str):
                # 提取关键决策关键词
                if any(kw in content for kw in ["决定", "通过", "采用", "不选", "改成"]):
                    decisions.append(content[:120])
                elif any(kw in content for kw in ["完成", "已", "执行", "创建"]):
                    actions.append(content[:80])

        parts = []
        if decisions:
            parts.append("决策记录:\n" + "\n".join(f"- {d}" for d in decisions[-5:]))
        if actions:
            parts.append("已完成:\n" + "\n".join(f"- {a}" for a in actions[-5:]))
        if not parts:
            parts.append(f"共 {len(messages)} 轮对话")

        return "\n\n".join(parts)

    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """粗略估算 token 数（字符数 / 3.5）。"""
        total_chars = 0
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        total_chars += len(part.get("text", ""))
        return int(total_chars / 3.5)
