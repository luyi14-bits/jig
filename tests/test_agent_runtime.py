"""Tests for AgentRuntime (State/Checkpoint/Memory separated)."""

from jig.core.agent_runtime import AgentRuntime, AgentState, UpgradeStrategy


class TestAgentRuntime:
    def test_initial_state(self):
        rt = AgentRuntime("test")
        assert rt.state == AgentState.IDLE
        assert rt.retries == 0

    def test_run_success(self):
        rt = AgentRuntime("test")
        result = rt.run(lambda ctx: "ok")
        assert result.success
        assert result.output == "ok"
        assert rt.state == AgentState.DONE

    def test_run_with_context(self):
        rt = AgentRuntime("test")
        result = rt.run(lambda ctx: ctx["x"], {"x": 42})
        assert result.output == 42

    def test_retry_on_failure(self):
        """失败→总结→升级→重试 闭环."""
        rt = AgentRuntime("test", max_retries=2)
        attempt = {"n": 0}

        def task(ctx):
            attempt["n"] += 1
            if attempt["n"] < 2:
                raise RuntimeError("attempt failed")
            return "recovered"

        result = rt.run(task)
        assert result.success
        assert result.output == "recovered"
        assert result.retries == 1
        assert len(rt.get_lessons()) >= 1  # 有教训

    def test_max_retries_exhausted(self):
        rt = AgentRuntime("test", max_retries=2)
        result = rt.run(lambda ctx: 1/0)
        assert not result.success
        assert result.retries == 3  # 初始1次 + 重试2次 = 3

    def test_lesson_extracted_on_failure(self):
        rt = AgentRuntime("test", max_retries=0)
        rt.run(lambda ctx: 1/0)
        lessons = rt.get_lessons()
        assert len(lessons) >= 1

    def test_upgrade_path_on_retry(self):
        rt = AgentRuntime("test", max_retries=3)
        attempt = {"n": 0}

        def task(ctx):
            attempt["n"] += 1
            if attempt["n"] <= 2:
                raise RuntimeError(f"fail {attempt['n']}")
            return "ok"

        result = rt.run(task)
        assert result.success
        assert len(result.upgrade_path) >= 1  # 升级了

    def test_checkpoints_created(self):
        rt = AgentRuntime("test")
        rt.run(lambda ctx: "ok")
        assert len(rt.checkpoints) >= 2

    def test_restore_checkpoint(self):
        rt = AgentRuntime("test")
        rt.run(lambda ctx: "ok")
        cp_id = rt.checkpoints[0].id
        restored = rt.restore_checkpoint(cp_id)
        assert restored
        assert rt.state == AgentState.RECOVERED

    def test_pause(self):
        rt = AgentRuntime("test")
        rt.pause()
        assert rt.state == AgentState.PAUSED

    def test_timeline_logged(self):
        rt = AgentRuntime("test")
        rt.run(lambda ctx: "ok")
        assert len(rt.get_timeline()) >= 2

    def test_debug_report(self):
        rt = AgentRuntime("test")
        rt.run(lambda ctx: "ok")
        report = rt.get_debug_report()
        assert report["state"] == "done"
        assert "checkpoints" in report
        assert "lessons" in report
        assert "upgrades" in report

    def test_state_checkpoint_memory_separated(self):
        """State/Checkpoint/Memory 三者互不混合."""
        rt = AgentRuntime("test")
        rt.run(lambda ctx: "ok")

        # State 是字符串枚举
        assert isinstance(rt.state, AgentState)

        # Checkpoint 是独立对象
        for cp in rt.checkpoints:
            assert hasattr(cp, "step")
            assert hasattr(cp, "context")

        # Lessons 是独立对象
        assert hasattr(rt.get_debug_report(), "keys")
