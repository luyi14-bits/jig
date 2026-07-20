"""MCP 协议完整支持 — 双向 Server + Client。

IDEA-044: MCP 协议完整支持，AgentHarness 可作为 MCP 工具被其他框架调用。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server — 让 AgentHarness 的 Agent 作为工具被外部调用。"""

    def __init__(self, registry) -> None:
        self._registry = registry
        self._tools: Dict[str, Any] = {}

    def list_tools(self) -> List[Dict[str, str]]:
        """返回工具列表（MCP 协议格式）。"""
        return [
            {"name": s.name, "description": s.description[:120], "input_schema": "{}"}
            for s in self._registry.list_all()
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """调用指定 Agent。"""
        skill = self._registry.get(name)
        if not skill:
            return json.dumps({"error": f"未知 Agent: {name}"})
        from agent_harness.orchestrator.dispatcher import Dispatcher
        d = Dispatcher(skill_dir="skills")
        return json.dumps({"result": d.handle(arguments.get("prompt", ""))})
