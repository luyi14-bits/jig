# 测试 Dispatcher 路由逻辑
import pytest
from jig.orchestrator.dispatcher import Dispatcher
from jig.core.skill_def import SkillDef


def test_dispatcher_missing_pm():
    """无 PM Agent 时应返回执行结果（SOPRunner fallback）。"""
    registry = _MockRegistry()
    factory = _MockFactory(registry)
    d = Dispatcher(registry, factory)
    result = d.handle("写一个 hello world")
    assert result is not None
    assert "SOP 管道执行完成" in result or "完成" in result


class _MockRegistry:
    def __init__(self):
        self._skills = {}

    def get(self, name):
        return self._skills.get(name)

    def add_skill(self, name, skill_def):
        self._skills[name] = skill_def
        return self

    def list_skills(self):
        return list(self._skills.keys())

    def get_loaded_skill_names(self):
        return list(self._skills.keys())

    def register_skill_dir(self, path):
        pass

    def load_all(self):
        pass


class _MockFactory:
    def __init__(self, registry):
        self._registry = registry

    def create_agent(self, skill_def):
        class _MockAgent:
            skill_name = skill_def.name
            config = type("cfg", (), {"role_preset": skill_def.body or "test"})()
            def set_context(self, k, v): pass
            def get_context(self, k, d=""): return ""
            def log_execution(self, m): pass
            def prepare_handover(self, target="", summary="ok", decisions=None, confidence=0.5, artifacts=None):
                from jig.core.skill_def import HandoverPackage
                return HandoverPackage(source_agent=self.skill_name, target_agent=target, summary=summary, decisions=decisions or [], confidence=confidence, artifacts=artifacts or {})
            def write_log(self, **kw): pass
        return _MockAgent()

    def create_agent_by_skill_ref(self, skill_ref, registry=None):
        sd = self._registry.get(skill_ref)
        return self.create_agent(sd) if sd else None


def _make_skill_def(name="Luyi14-pm-mentor"):
    return SkillDef(name=name, description="test", model="flash",
                    body="You are a PM agent.",
                    model_name=None, sub_skills=[], tags=[], metadata={},
                    tools=[], agent_name=None)
