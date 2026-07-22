"""DeepSeek 适配器 — reasoning_content + Function Calling 兼容 + 深度优化。

FR-3: reasoning_effort 可配置（low/medium/high）
FR-2: 自动 Tool-Call Repair（FC 格式错误自愈）
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DeepSeekAdapter:
    """DeepSeek API 适配器（增强版）。

    新增能力：
    - reasoning_effort 可配置（FR-3）
    - 自动 Tool-Call Repair（FR-2）
    - FC 格式错误自愈
    """

    REASONER_MODELS = {"deepseek-reasoner", "deepseek-reasoner-v4", "deepseek-v4-pro"}

    def __init__(self, reasoning_effort: str = "medium") -> None:
        self._last_reasoning_content: Optional[str] = None
        self._fc_fallback_triggered = False
        self._repair_count = 0
        self._repair_success = 0
        self._reasoning_effort = reasoning_effort  # low / medium / high

    @property
    def reasoning_effort(self) -> str:
        return self._reasoning_effort

    @reasoning_effort.setter
    def reasoning_effort(self, value: str) -> None:
        if value in ("low", "medium", "high"):
            self._reasoning_effort = value

    def prepare_request(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Any = None,
        model: str = "deepseek-v4-flash",
    ) -> Dict[str, Any]:
        """准备 API 请求参数（含 reasoning_effort 注入）。"""
        if tools and model in self.REASONER_MODELS:
            logger.warning("模型 %s 不支持 FC，自动降级到 deepseek-v4-flash", model)
            model = "deepseek-v4-flash"
            self._fc_fallback_triggered = True

        processed_messages = self._process_messages(messages)
        processed_tool_choice = self._process_tool_choice(tool_choice)

        request: Dict[str, Any] = {
            "model": model,
            "messages": processed_messages,
        }

        if tools:
            request["tools"] = tools
        if processed_tool_choice is not None:
            request["tool_choice"] = processed_tool_choice

        # 注入 reasoning_effort（仅 Pro 模型）
        if model != "flash" and self._reasoning_effort != "medium":
            request["reasoning_effort"] = self._reasoning_effort

        return request

    def repair_function_call(self, raw: str) -> Tuple[bool, Optional[Dict]]:
        """自动修复 FC 返回格式错误（FR-2）。

        Args:
            raw: 模型返回的原始字符串

        Returns:
            (是否修复成功, 修复后的 JSON)
        """
        # 尝试直接解析
        raw_clean = raw.strip()
        try:
            return True, json.loads(raw_clean)
        except json.JSONDecodeError:
            pass

        # 修复 1: 去除代码块标记
        if raw_clean.startswith("```"):
            raw_clean = re.sub(r"^```(?:json)?\n", "", raw_clean)
            raw_clean = re.sub(r"\n```$", "", raw_clean)
            try:
                result = json.loads(raw_clean)
                self._repair_success += 1
                return True, result
            except json.JSONDecodeError:
                pass

        # 修复 2: 去除多余括号
        raw_clean = re.sub(r",\s*([}\]])", r"\1", raw_clean)
        try:
            result = json.loads(raw_clean)
            self._repair_success += 1
            return True, result
        except json.JSONDecodeError:
            pass

        # 修复 3: 补齐缺失的引号
        raw_clean = re.sub(r"(?<=[:\s])([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*:)", r'"\1"', raw_clean)
        try:
            result = json.loads(raw_clean)
            self._repair_success += 1
            return True, result
        except json.JSONDecodeError:
            pass

        self._repair_count += 1
        return False, None

    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """处理 API 响应，提取 reasoning_content。"""
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})

        reasoning = message.get("reasoning_content")
        if reasoning is not None:
            self._last_reasoning_content = reasoning
        else:
            self._last_reasoning_content = None

        return response

    def _process_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        processed = []
        for msg in messages:
            msg_copy = dict(msg)
            if msg.get("role") == "assistant":
                has_tool_calls = bool(msg.get("tool_calls"))
                if has_tool_calls:
                    if "reasoning_content" not in msg_copy and self._last_reasoning_content:
                        msg_copy["reasoning_content"] = self._last_reasoning_content
                else:
                    msg_copy.pop("reasoning_content", None)
            processed.append(msg_copy)
        return processed

    def _process_tool_choice(self, tool_choice: Any) -> Any:
        if tool_choice is None:
            return None
        if tool_choice == "required":
            logger.warning("tool_choice='required' 在 DeepSeek 上不可靠，建议指定函数名称")
            return "required"
        if isinstance(tool_choice, dict):
            return tool_choice
        if isinstance(tool_choice, str):
            return {"type": "function", "function": {"name": tool_choice}}
        return tool_choice

    @property
    def repair_stats(self) -> Dict[str, int]:
        return {"attempts": self._repair_count, "successes": self._repair_success}

    @property
    def last_reasoning_content(self) -> Optional[str]:
        return self._last_reasoning_content

    @property
    def fc_fallback_triggered(self) -> bool:
        return self._fc_fallback_triggered
