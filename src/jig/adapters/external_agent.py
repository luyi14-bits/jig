"""外部 Agent 兼容层（Meta-Harness）。

IDEA-049: 让 Claude Code / Codex / Cursor / Pi 等第三方 Agent 
能接入 Jig 的硬约束管控体系。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .mcp_protocol import MCPServer
from ..core.skill_registry import SkillRegistry

logger = logging.getLogger(__name__)


class ExternalAgentAdapter:
    """外部 Agent 适配器基类。

    实现 start / send / stop / observe 生命周期。
    """

    def start(self, config: Dict[str, Any]) -> None:
        raise NotImplementedError

    def send(self, prompt: str) -> str:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class ClaudeCodeAdapter(ExternalAgentAdapter):
    """Claude Code 适配器。"""

    def start(self, config: Dict[str, Any] = None) -> None:
        logger.info("Claude Code 适配器已启动")

    def send(self, prompt: str) -> str:
        from ..orchestrator.dispatcher import Dispatcher
        d = Dispatcher(skill_dir="skills")
        return d.handle(prompt)

    def stop(self) -> None:
        logger.info("Claude Code 适配器已停止")


class MetaHarness:
    """Meta-Harness — 统一管理外部 Agent 的接入和硬约束穿透。

    外部 Agent 的工具调用经过 ToolGuard 三层拦截后，
    才能访问 Jig 的内部 Agent。
    """

    def __init__(self) -> None:
        self._registry = SkillRegistry()
        self._registry.register_skill_dir("skills")
        self._registry.load_all()
        self._mcp = MCPServer(self._registry)
        self._adapters: Dict[str, ExternalAgentAdapter] = {}

    def register_adapter(self, name: str, adapter: ExternalAgentAdapter) -> None:
        """注册外部 Agent 适配器。

        Args:
            name: 适配器名称（如 'claude-code', 'codex'）
            adapter: ExternalAgentAdapter 实例
        """
        self._adapters[name] = adapter
        adapter.start({})

    def route(self, source: str, prompt: str) -> str:
        """路由请求到指定的外部 Agent 或默认 PM Agent。

        优先走已注册的外部 Agent 适配器；
        未注册则回退到 PM Agent。

        Args:
            source: 来源适配器名称
            prompt: 用户输入

        Returns:
            外部 Agent 或 PM Agent 的响应字符串
        """
        adapter = self._adapters.get(source)
        if adapter:
            return adapter.send(prompt)
        return self._mcp.call_tool("Luyi14-pm-mentor", {"prompt": prompt})
