"""A2A 协议探索 — Agent-to-Agent 跨框架通信。

IDEA-045: 允许 AgentHarness 与其他框架的 Agent 跨框架协作。
"""

from __future__ import annotations
import json
from typing import Any, Dict, List


class A2AMessage:
    """A2A 消息格式。"""

    def __init__(self, source: str, target: str, action: str, payload: Dict[str, Any]) -> None:
        self.source = source
        self.target = target
        self.action = action
        self.payload = payload

    def to_json(self) -> str:
        return json.dumps({"source": self.source, "target": self.target,
                          "action": self.action, "payload": self.payload})

    @classmethod
    def from_json(cls, raw: str) -> "A2AMessage":
        d = json.loads(raw)
        return cls(d["source"], d["target"], d["action"], d.get("payload", {}))


class A2ARouter:
    """A2A 路由器 — 跨框架消息路由。"""

    def __init__(self) -> None:
        self._routes: Dict[str, Any] = {}

    def register(self, agent_id: str, handler: Any) -> None:
        self._routes[agent_id] = handler

    def route(self, msg: A2AMessage) -> str:
        handler = self._routes.get(msg.target)
        if handler:
            return handler(msg)
        return json.dumps({"error": f"未知 Agent: {msg.target}"})
