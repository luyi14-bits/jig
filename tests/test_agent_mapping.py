"""Agent 映射引擎单元测试。"""

import pytest

from jig.core.skill_def import SkillDef
from jig.core.skill_registry import SkillRegistry
from jig.core.agent_factory import AgentFactory, Agent


class TestSkillRegistry:
    """测试 Skill 注册表。"""

    def setup_method(self):
        self.registry = SkillRegistry()
        self.registry.clear()

    def test_register_and_get(self):
        """注册和查询 skill。"""
        skill = SkillDef(name="test-skill", description="测试")
        self.registry._skills["test-skill"] = skill
        assert self.registry.get("test-skill") is skill
        assert self.registry.get("not-exists") is None

    def test_list_all(self):
        """列出所有 skill。"""
        self.registry._skills["a"] = SkillDef(name="a", description="A")
        self.registry._skills["b"] = SkillDef(name="b", description="B")
        assert len(self.registry.list_all()) == 2

    def test_list_by_model(self):
        """按模型等级过滤。"""
        self.registry._skills["p1"] = SkillDef(name="p1", description="P1", model="pro")
        self.registry._skills["p2"] = SkillDef(name="p2", description="P2", model="pro")
        self.registry._skills["f1"] = SkillDef(name="f1", description="F1", model="flash")
        assert len(self.registry.list_by_model("pro")) == 2
        assert len(self.registry.list_by_model("flash")) == 1

    def test_clear(self):
        """清空注册表。"""
        self.registry._skills["test"] = SkillDef(name="test", description="T")
        self.registry.clear()
        assert self.registry.count() == 0


class TestAgentFactory:
    """测试 Agent 工厂。"""

    def test_create_flash_agent(self):
        """Flash skill 应创建 Flash 模型 Agent。"""
        skill = SkillDef(name="flash-dev", description="编码", model="flash")
        agent = AgentFactory.create_agent(skill)
        assert agent.skill_name == "flash-dev"
        assert agent.config.model_grade == "flash"

    def test_create_pro_agent(self):
        """Pro skill 应创建 Pro 模型 Agent。"""
        skill = SkillDef(name="pm-lead", description="PM", model="pro")
        agent = AgentFactory.create_agent(skill)
        assert agent.config.model_grade == "pro"

    def test_agent_context_isolation(self):
        """并发 Agent 上下文应隔离。"""
        skill1 = SkillDef(name="agent-a", description="A", model="flash")
        skill2 = SkillDef(name="agent-b", description="B", model="flash")
        agent1 = AgentFactory.create_agent(skill1)
        agent2 = AgentFactory.create_agent(skill2)

        agent1.set_context("key", "value-a")
        agent2.set_context("key", "value-b")

        assert agent1.get_context("key") == "value-a"
        assert agent2.get_context("key") == "value-b"

    def test_handover_package(self):
        """交接包应包含正确的来源/目标。"""
        skill = SkillDef(name="src-agent", description="Source", model="flash")
        agent = AgentFactory.create_agent(skill)

        handover = agent.prepare_handover(
            target="dest-agent",
            summary="任务完成",
            decisions=["使用 Flash 模型"],
            confidence=0.95,
        )

        assert handover.source_agent == "src-agent"
        assert handover.target_agent == "dest-agent"
        assert handover.confidence == 0.95
        assert len(handover.decisions) == 1

    def test_receive_handover(self):
        """接收交接包应更新上下文。"""
        from jig.core.skill_def import HandoverPackage

        skill1 = SkillDef(name="agent-1", description="First", model="flash")
        skill2 = SkillDef(name="agent-2", description="Second", model="flash")
        agent1 = AgentFactory.create_agent(skill1)
        agent2 = AgentFactory.create_agent(skill2)

        handover = agent1.prepare_handover(
            target="agent-2",
            summary="第一阶段完成",
            artifacts={"output": "data"},
        )
        agent2.receive_handover(handover)

        assert agent2.get_context("handover_from") == "agent-1"
        assert agent2.get_context("previous_summary") == "第一阶段完成"
