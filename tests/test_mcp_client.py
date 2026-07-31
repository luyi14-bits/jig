"""Tests for MCPClient + ToolGuard — 对齐真实 API。"""

import pytest

from src.jig.adapters.mcp_client import MCPClient, ToolGuard


class TestToolGuard:
    def test_whitelist_allow(self):
        assert ToolGuard.check("coding", "Read") is True
        assert ToolGuard.check("pm", "web_search") is True

    def test_whitelist_deny(self):
        assert ToolGuard.check("pm", "Bash") is False
        assert ToolGuard.check("mentor", "Write") is False

    def test_denylist_blocks(self):
        assert ToolGuard.check("devops", "Bash", "rm -rf /") is False
        assert ToolGuard.check("devops", "Git", "push --force") is False

    def test_unknown_role_allows(self):
        assert ToolGuard.check("unknown_role", "anything") is True


class TestMCPClient:
    def test_instantiate(self):
        client = MCPClient()
        assert client is not None

    def test_list_tools(self):
        client = MCPClient()
        tools = client.list_tools()
        assert "web_search" in tools
        assert "fetch_page" in tools

    def test_call_web_search(self):
        client = MCPClient()
        result = client.call("web_search", query="jig framework")
        assert "results" in result
        assert len(result["results"]) > 0

    def test_call_fetch_page(self):
        client = MCPClient()
        result = client.call("fetch_page", url="https://example.com")
        assert result["status"] == 200

    def test_call_unknown_tool_raises(self):
        client = MCPClient()
        with pytest.raises(ValueError):
            client.call("nonexistent_tool")

    def test_get_tool(self):
        client = MCPClient()
        assert client.get_tool("web_search") is not None
        assert client.get_tool("nope") is None
