"""Tests for AgentRuntime."""

from jig.core.agent_runtime import AgentRuntime, AgentState, AgentResult


class TestAgentRuntime:
    def test_initial_state(self):
        rt = AgentRuntime("test")
        assert rt.state == AgentState.IDLE
        assert rt.name == "test"

    def test_run_success(self):
        rt = AgentRuntime("test")
        result = rt.run(lambda ctx: "ok")
        assert result.success
        assert result.output == "ok"
        assert rt.state == AgentState.DONE

    def test_run_with_context(self):
        rt = AgentRuntime("test")
        result = rt.run(lambda ctx: ctx["value"], {"value": 42})
        assert result.success
        assert result.output == 42

    def test_retry_on_failure(self):
        rt = AgentRuntime("test", max_retries=2)
        attempts = {"n": 0}

        def failing_task(ctx):
            attempts["n"] += 1
            if attempts["n"] < 2:
                raise RuntimeError(f"attempt {attempts['n']} failed")
            return "recovered"

        result = rt.run(failing_task)
        assert result.success
        assert result.output == "recovered"
        assert result.retries == 1

    def test_max_retries_exhausted(self):
        rt = AgentRuntime("test", max_retries=2)

        def always_fail(ctx):
            raise RuntimeError("always fails")

        result = rt.run(always_fail)
        assert not result.success
        assert result.error is not None
        assert rt.state == AgentState.ERROR

    def test_checkpoints_created(self):
        rt = AgentRuntime("test")
        rt.run(lambda ctx: "ok")
        assert len(rt.get_checkpoints()) >= 2

    def test_pause_and_resume(self):
        rt = AgentRuntime("test")
        rt.pause()
        assert rt.state == AgentState.PAUSED
        rt.resume()
        assert rt.state == AgentState.RUNNING

    def test_timeline(self):
        rt = AgentRuntime("test")
        rt.run(lambda ctx: "ok")
        timeline = rt.get_timeline()
        assert len(timeline) >= 3

    def test_debug_report(self):
        rt = AgentRuntime("test")
        rt.run(lambda ctx: "ok")
        report = rt.get_debug_report()
        assert report["state"] == "done"
        assert report["retries"] == 0
        assert report["checkpoints"] >= 2

    def test_hooks_integration(self):
        rt = AgentRuntime("test")
        events = {"on_run": False, "on_error": False, "on_rollback": False}

        def run_hook(ctx):
            events["on_run"] = True
            return "ok"

        def error_hook(e):
            events["on_error"] = True

        rt.register_hooks(on_run=run_hook, on_error=error_hook)
        rt.run(lambda ctx: "ok")
        assert events["on_run"]

    def test_lifecycle_on_error(self):
        rt = AgentRuntime("test", max_retries=0)
        result = rt.run(lambda ctx: 1/0)
        assert not result.success
        assert rt.state == AgentState.ERROR

    def test_name_unique(self):
        rt1 = AgentRuntime("a")
        rt2 = AgentRuntime("a")
        assert rt1._id != rt2._id
