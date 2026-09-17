"""Tests for 闭环断点修复 + 孤儿串起（本次迭代新增行为）。"""

import pytest

from src.jig.adapters.mcp_client import ToolGuard
from src.jig.adapters.model_provider import ModelRouter
from src.jig.orchestrator.sop_runner import SOPRunner
from src.jig.core.agent_factory import AgentExecutionError
from src.jig.core.skill_def import ToolDecl


class TestToolGuardRoleAlias:
    """ToolGuard 角色名归一化：Luyi14-xxx 全名 → WHITELIST 短名。"""

    def test_pm_full_name_maps_to_pm(self):
        # Luyi14-pm-mentor 应归一化到 pm，命中白名单（web_search 在 pm 白名单）
        assert ToolGuard.check("Luyi14-pm-mentor", "web_search") is True

    def test_coding_full_name_maps_to_coding(self):
        assert ToolGuard.check("Luyi14-coding-ethics", "Bash") is True

    def test_pm_full_name_denied_bash(self):
        # pm 白名单无 Bash，应拦截（而非宽松放行）
        assert ToolGuard.check("Luyi14-pm-mentor", "Bash") is False

    def test_secretary_full_name_maps(self):
        assert ToolGuard.check("Luyi14-project-secretary", "Write") is True

    def test_trinity_full_name_maps_to_mentor(self):
        # mentor 白名单无 Write，应拦截
        assert ToolGuard.check("Luyi14-trinity-mentors", "Write") is False

    def test_short_name_still_works(self):
        # 传入短名也应命中（幂等）
        assert ToolGuard.check("coding", "Read") is True


class TestModelRouterAllSessionIds:
    """model_router 删除后补回的 all_session_ids（CLI 依赖）。"""

    def test_all_session_ids_exists(self):
        assert hasattr(ModelRouter(), "all_session_ids")

    def test_all_session_ids_empty_initially(self):
        assert ModelRouter().all_session_ids() == {}

    def test_all_session_ids_after_route(self):
        router = ModelRouter()
        router.route("flash")
        ids = router.all_session_ids()
        assert "flash" in ids


class TestToolGuardPrecision:
    """ToolGuard 越权修复：白名单精确匹配 + 黑名单核心词包含匹配。"""

    def test_code_review_can_only_bash_pytest(self):
        # code-review 白名单只有 Bash(pytest)，不能调用任意 Bash
        assert ToolGuard.check("Luyi14-code-review", "Bash", "pytest") is True
        assert ToolGuard.check("Luyi14-code-review", "Bash", "ls") is False

    def test_denylist_catches_rm_rf_variants(self):
        # 黑名单核心词 "rm -rf" 应拦变体
        assert ToolGuard.check("Luyi14-coding-ethics", "Bash", "rm -rf /") is False
        assert ToolGuard.check("Luyi14-coding-ethics", "Bash", "rm -rf /tmp") is False
        assert ToolGuard.check("Luyi14-coding-ethics", "Bash", "sudo rm -rf /") is False

    def test_coding_can_bash_safe_command(self):
        # coding 白名单有纯 "Bash"，安全命令放行
        assert ToolGuard.check("Luyi14-coding-ethics", "Bash", "ls") is True

    def test_denylist_catches_drop_table(self):
        assert ToolGuard.check("Luyi14-coding-ethics", "Bash", "drop table users") is False


class TestToolGuardStaticCheck:
    """sop_runner._check_toolguard 静态校验：黑名单硬阻断 + 白名单告警。"""

    def _make_agent(self, skill_name, tool_names):
        """构造一个最小 agent，只含 _check_toolguard 需要的属性。"""
        class _MockAgent:
            pass
        agent = _MockAgent()
        agent.skill_name = skill_name
        from src.jig.core.skill_def import AgentConfig, SessionConfig
        agent.config = AgentConfig(
            skill_name=skill_name,
            role_preset="",
            model_grade="flash",
            session_config=SessionConfig(model="deepseek-flash"),
            tools=[ToolDecl(name=n, tool_type="shell") for n in tool_names],
        )
        return agent

    def test_pm_skill_tools_not_blocked(self):
        # pm skill 声明 Read/Write/Bash/Glob，白名单外工具只告警、不 raise（回归测试）
        agent = self._make_agent("Luyi14-pm-mentor", ["Read", "Write", "Bash", "Glob"])
        runner = SOPRunner.__new__(SOPRunner)  # 绕过 __init__ 副作用
        runner._check_toolguard(agent)  # 不应 raise

    def test_dangerous_tool_blocked(self):
        # 声明含危险核心词的工具应被黑名单硬阻断
        agent = self._make_agent("Luyi14-coding-ethics", ["Bash", "rm -rf /"])
        runner = SOPRunner.__new__(SOPRunner)
        with pytest.raises(AgentExecutionError):
            runner._check_toolguard(agent)

