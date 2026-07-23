# 测试 SOPRunner 管道执行
import pytest
from jig.orchestrator.sop_runner import (SOPRunner as _SOPRunner,
                                          SOPCheckpoint as _SOPCheckpoint)
from jig.core.skill_def import SOPNode, HandoverPackage


class _MockResp:
    content = "mock response"


class _MockProvider:
    def __init__(self):
        self.calls = []

    def chat(self, messages, **kw):
        self.calls.append(messages)
        return _MockResp()


def _node(name, desc="", skill_ref=None, mode="sequential", sub_steps=None):
    return SOPNode(
        name=name,
        description=desc,
        skill_ref=skill_ref,
        mode=mode,
        sub_steps=sub_steps or [],
    )


def test_sop_runner_basic():
    """单节点管道应正常执行。"""
    node = _node("root", skill_ref="pm")
    runner = _SOPRunner(provider=_MockProvider())
    result = runner.run(node, {"request": "hello"})
    assert isinstance(result, HandoverPackage)


def test_sop_runner_multi_step():
    """多节点管道应依次执行。"""
    node = _node("root", sub_steps=[
        _node("analyze", skill_ref="pm"),
        _node("spec", skill_ref="spec"),
    ])
    provider = _MockProvider()
    runner = _SOPRunner(provider=provider)
    result = runner.run(node, {"request": "test"})
    assert result.source_agent == "SOPRunner"
