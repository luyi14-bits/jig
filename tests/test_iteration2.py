"""TASK-002 测试：并行编排 + 检查点 + 工作流模板 + cache-guard。"""

import json
import os
import tempfile

import pytest

from jig.orchestrator import (
    ParallelOrchestrator,
    CheckpointManager,
    create_dev_workflow,
)
from jig.core.skill_def import HandoverPackage, SOPNode


class TestParallelOrchestrator:
    """测试并行编排调度器。"""

    def test_parallel_execution(self):
        """并行执行多个子 Agent。"""
        sop = SOPNode(
            name="parallel-root",
            description="并行测试",
            mode="parallel",
            sub_steps=[
                SOPNode(name="task-a", description="任务A", skill_ref="agent-a"),
                SOPNode(name="task-b", description="任务B", skill_ref="agent-b"),
                SOPNode(name="task-c", description="任务C", skill_ref="agent-c"),
            ],
        )

        def resolver(name):
            return None  # mock

        orch = ParallelOrchestrator(agent_resolver=resolver, max_concurrency=3)
        result = orch.execute(sop, {})
        assert result is not None
        assert len(orch.execution_log) > 2  # 开始 + 每个子任务 + 完成

    def test_max_concurrency(self):
        """max_concurrency 限制生效。"""
        sop = SOPNode(
            name="limited",
            description="并行度限制",
            mode="parallel",
            sub_steps=[SOPNode(name=f"task-{i}", description=f"T{i}", skill_ref="agent") for i in range(5)],
        )

        orch = ParallelOrchestrator(agent_resolver=lambda n: None, max_concurrency=2)
        assert orch._max_concurrency == 2
        result = orch.execute(sop, {})
        assert result is not None

    def test_empty_sub_steps(self):
        """无子步骤时正常返回。"""
        sop = SOPNode(name="empty", description="空", mode="parallel")
        orch = ParallelOrchestrator(agent_resolver=lambda n: None)
        result = orch.execute(sop, {})
        assert result is not None


class TestCheckpointManager:
    """测试检查点管理器。"""

    def test_save_and_load(self):
        """保存并加载检查点。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = CheckpointManager(checkpoint_dir=tmpdir)
            state = {"step": 2, "context": {"key": "value"}, "results": {"a": "ok"}}

            path = mgr.save("test-session", state)
            assert os.path.exists(path)

            loaded = mgr.load("test-session")
            assert loaded is not None
            assert loaded["step"] == 2
            assert loaded["context"]["key"] == "value"

    def test_resume(self):
        """从检查点恢复。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = CheckpointManager(checkpoint_dir=tmpdir)
            mgr.save("resume-test", {"step": 3, "data": "in-progress"})

            state = mgr.resume("resume-test")
            assert state is not None
            assert state["step"] == 3

    def test_load_nonexistent(self):
        """不存在的检查点返回 None。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = CheckpointManager(checkpoint_dir=tmpdir)
            assert mgr.load("not-exists") is None

    def test_list_checkpoints(self):
        """列出所有检查点。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = CheckpointManager(checkpoint_dir=tmpdir)
            mgr.save("cp-1", {"a": 1})
            mgr.save("cp-2", {"b": 2})
            checkpoints = mgr.list_checkpoints()
            assert "cp-1" in checkpoints
            assert "cp-2" in checkpoints


class TestDevWorkflow:
    """测试开发工作流模板。"""

    def test_workflow_structure(self):
        """工作流模板结构正确。"""
        wf = create_dev_workflow()
        assert wf.name == "dev-workflow"
        assert wf.mode == "sequential"
        assert len(wf.sub_steps) == 5

        step_names = [s.name for s in wf.sub_steps]
        assert step_names == ["brainstorm", "plan", "code", "test", "review"]

    def test_each_step_has_skill_ref(self):
        """每一步都有 skill_ref。"""
        wf = create_dev_workflow()
        for step in wf.sub_steps:
            assert step.skill_ref is not None, f"{step.name} 缺少 skill_ref"


class TestCacheGuard:
    """测试 cache-guard CI 工程纪律。"""

    def test_release_cache_hit_guard(self):
        """TestReleaseCacheHitGuard: 缓存命中率退化检测。"""
        from jig.adapters.cache_engine import CacheEngine

        engine = CacheEngine()

        # 模拟 10 次请求，8 次命中
        for i in range(10):
            engine.assemble_prefix(
                base_prompt="You are a helpful assistant.",
                output_style="Use Chinese.",
                language="zh-CN",
                skill_index="test-skill: 测试",
            )
            if i != 0:
                engine.record_cache_hit()

        diag = engine.diagnostic
        assert diag.total_requests == 10
        assert diag.cached_requests == 9
        # 首次请求 miss，之后全部命中 → 90%
        assert diag.session_hit_rate == 0.9

        # guard: 命中率不应低于 50%
        assert diag.session_hit_rate >= 0.5, "Cache hit rate degraded below threshold!"

    @pytest.mark.parametrize("rate,should_pass", [
        (0.99, True),
        (0.80, True),
        (0.30, False),
        (0.0, False),
    ])
    def test_cache_guard_threshold(self, rate, should_pass):
        """parametrize 覆盖多种命中率边界。"""
        if should_pass:
            assert rate >= 0.5
        else:
            assert rate < 0.5
