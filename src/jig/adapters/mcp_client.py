"""MCP 客户端 — 外部工具集成层。

提供 web-search 等内置 MCP 工具，供 Agent 调用。
所有 MCP 工具注册到 ModelRouter，按 Agent 白名单分配。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP 工具客户端。

    内置工具：
    - web_search: 搜索网页
    - fetch_page: 获取页面内容

    后续可扩展：git-ops, file-system 等。
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Any] = {
            "web_search": self._web_search,
            "fetch_page": self._fetch_page,
        }

    def get_tool(self, name: str):
        """获取工具函数。"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """列出所有可用工具。"""
        return list(self._tools.keys())

    def call(self, tool_name: str, **kwargs) -> Any:
        """调用 MCP 工具。"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"MCP 工具 '{tool_name}' 不存在，可用: {self.list_tools()}")
        logger.info("MCP 调用: %s, args=%s", tool_name, kwargs)
        return tool(**kwargs)

    def _web_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """搜索网页（模拟实现，后续接入真实搜索引擎）。"""
        logger.info("web_search: query=%s, max=%d", query, max_results)
        return {
            "query": query,
            "results": [
                {"title": f"Result {i+1} for {query}", "url": f"https://example.com/{i}"}
                for i in range(min(max_results, 3))
            ],
        }

    def _fetch_page(self, url: str) -> Dict[str, Any]:
        """获取页面内容（模拟实现）。"""
        logger.info("fetch_page: url=%s", url)
        return {"url": url, "content": f"Simulated content for {url}", "status": 200}


class ToolGuard:
    """工具调用硬约束 — whitelist / denylist / PreToolUse hook。

    确保 Agent 只能调用其角色允许的工具，不能越权。
    """

    # 各 Agent 角色的工具白名单
    WHITELIST: Dict[str, List[str]] = {
        "pm": ["web_search", "fetch_page", "Read", "Grep"],
        "spec": ["Read", "Write", "Grep", "Glob"],
        "coding": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        "code-review": ["Read", "Grep", "Glob", "Bash(pytest)"],
        "tdd": ["Read", "Bash(pytest)", "Grep", "Glob"],
        "acceptance": ["Read", "Grep", "Glob", "Bash(pytest)", "Bash(build)"],
        "security": ["Read", "Grep", "Glob", "web_search", "fetch_page"],
        "devops": ["Bash", "Git(push/pull/tag)", "Read", "Write", "Glob"],
        "secretary": ["Read", "Write", "Glob", "Git", "Bash"],
        "mentor": ["Read", "Grep", "Glob"],
    }

    # 全局黑名单（所有 Agent 禁止）
    DENYLIST: List[str] = [
        "Bash(rm -rf /)",
        "Bash(drop table)",
        "Bash(shutdown)",
        "Write(/etc/)",
        "Write(~/.ssh/)",
        "Git(push --force)",
    ]

    @classmethod
    def check(cls, agent_role: str, tool_name: str, tool_args: str = "") -> bool:
        """PreToolUse 检查。

        Returns:
            True = 允许调用, False = 拦截

        检查顺序：
        1. 黑名单匹配 → 拦截
        2. 白名单有定义且不匹配 → 拦截
        3. 白名单无定义（宽松模式）→ 放行
        """
        # 1. 黑名单
        for denied in cls.DENYLIST:
            if tool_name in denied or (tool_args and tool_args in denied):
                logger.warning(
                    "ToolGuard 拦截: %s 尝试调用黑名单工具 %s(%s)",
                    agent_role, tool_name, tool_args,
                )
                return False

        # 2. 白名单
        allowed = cls.WHITELIST.get(agent_role)
        if allowed is not None:
            for allowed_tool in allowed:
                if tool_name in allowed_tool:
                    return True
            logger.warning(
                "ToolGuard 拦截: %s 尝试调用未授权工具 %s（白名单: %s）",
                agent_role, tool_name, allowed,
            )
            return False

        # 3. 未配置白名单 → 放行
        return True
