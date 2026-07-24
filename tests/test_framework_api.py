# 框架公开 SDK API 集成测试 — Loop #2
import pytest
from jig import Jig


def test_jig_init_with_skills():
    """Jig(skills_dir=...) 初始化应加载技能。"""
    app = Jig(skills_dir="./skills")
    assert app.skill_count > 0
    assert app.skill_count >= 11


def test_jig_list_agents():
    """Jig.list_agents() 应返回包含 name/description/model 的列表。"""
    app = Jig(skills_dir="./skills")
    agents = app.list_agents()
    assert isinstance(agents, list)
    assert len(agents) >= 11
    # 检查每条记录包含必要字段
    first = agents[0]
    assert "name" in first or "skill_name" in first
    # 至少有一位 PM Agent
    names = [a.get("name") or a.get("skill_name", "") for a in agents]
    assert any("pm" in n.lower() or "PM" in n for n in names)


def test_jig_run_returns_string():
    """Jig.run() 应返回非空字符串。"""
    app = Jig(skills_dir="./skills")
    result = app.run("写一个 Python hello world 函数")
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0


def test_jig_run_with_empty_input():
    """空输入不应崩溃。"""
    app = Jig(skills_dir="./skills")
    result = app.run("")
    assert result is not None


def test_mcp_server_list_tools():
    """MCPServer.list_tools() 应返回工具列表。"""
    from jig.server.app import app as fastapi_app
    from jig.core.skill_registry import SkillRegistry
    registry = SkillRegistry()
    registry.register_skill_dir("./skills")
    registry.load_all()
    from jig.adapters.mcp_protocol import MCPProtocol
    mcp = MCPProtocol(registry)
    tools = mcp.list_tools()
    assert isinstance(tools, list)
    # 至少返回一些工具（PM Agent 的 web_search / fetch_page 等）
    assert len(tools) >= 1


def test_mcp_protocol_docstrings():
    """MCPServer 公开方法应有 docstring。"""
    from jig.adapters.mcp_protocol import MCPProtocol
    assert MCPProtocol.__init__.__doc__ is not None
    assert MCPProtocol.list_tools.__doc__ is not None
    assert MCPProtocol.call_tool.__doc__ is not None


def test_external_agent_adapter_docstrings():
    """MetaHarness 公开 API 应有 docstring。"""
    from jig.adapters.external_agent import MetaHarness
    assert MetaHarness.register_adapter.__doc__ is not None
    assert MetaHarness.route.__doc__ is not None
