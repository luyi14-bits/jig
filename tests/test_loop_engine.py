"""Tests for LoopEngine."""

from jig.orchestrator.loop_engine import (
    LoopEngine, LoopConfig, LoopStatus,
    ConvergenceDetector, QualityValidator, CheckpointManager,
    CheckpointGranularity,
)


class TestConvergenceDetector:
    def test_not_converged_with_few_scores(self):
        d = ConvergenceDetector()
        d.add_score(0.5)
        assert not d.is_converged()

    def test_converged_when_all_above_threshold(self):
        d = ConvergenceDetector(threshold=0.9)
        d.add_score(0.5)
        d.add_score(0.92)
        d.add_score(0.95)
        d.add_score(0.98)
        assert d.is_converged()

    def test_not_converged_when_below_threshold(self):
        d = ConvergenceDetector(threshold=0.9)
        d.add_score(0.5)
        d.add_score(0.6)
        d.add_score(0.7)
        assert not d.is_converged()

    def test_last_scores_returns_recent(self):
        d = ConvergenceDetector()
        for s in range(10):
            d.add_score(float(s))
        assert len(d.last_scores) == 5


class TestQualityValidator:
    def test_no_validators_passes(self):
        v = QualityValidator()
        passed, score, msg = v.validate("result", {})
        assert passed
        assert score == 1.0

    def test_custom_validator(self):
        def always_pass(r, ctx):
            return True, 0.8, "ok"
        v = QualityValidator([always_pass])
        passed, score, msg = v.validate("x", {})
        assert passed
        assert score == 0.8

    def test_failing_validator(self):
        def always_fail(r, ctx):
            return False, 0.3, "bad"
        v = QualityValidator([always_fail])
        passed, score, msg = v.validate("x", {})
        assert not passed
        assert score == 0.3


class TestCheckpointManager:
    def test_save_and_load(self):
        m = CheckpointManager()
        m.save("test-key", {"value": 42})
        loaded = m.load("test-key")
        assert loaded == {"value": 42}

    def test_load_nonexistent(self):
        m = CheckpointManager()
        assert m.load("nonexistent") is None

    def test_list_checkpoints(self):
        m = CheckpointManager()
        m.save("a", 1)
        m.save("b", 2)
        assert len(m.list_checkpoints()) == 2

    def test_clear(self):
        m = CheckpointManager()
        m.save("a", 1)
        m.clear()
        assert len(m.list_checkpoints()) == 0

    def test_granularity_task(self):
        m = CheckpointManager(CheckpointGranularity.TASK)
        assert not m.should_checkpoint("node")
        assert not m.should_checkpoint("executor")
        assert m.should_checkpoint("task")


class TestLoopEngine:
    def test_loop_converges(self):
        engine = LoopEngine(LoopConfig(max_iterations=10, convergence_threshold=0.9))
        counter = {"i": 0}

        def task(ctx):
            counter["i"] += 1
            return {"score": min(0.5 + counter["i"] * 0.15, 1.0)}

        # Monkey-patch validator to use the return score
        def auto_score(r, ctx):
            return True, r["score"], "auto"

        engine._validator = QualityValidator([auto_score])
        result = engine.run(task, {})
        assert result is not None
        assert engine.status == LoopStatus.CONVERGED
        assert 3 <= engine.iteration <= 10

    def test_max_iterations(self):
        engine = LoopEngine(LoopConfig(max_iterations=3, convergence_threshold=0.99))
        counter = {"i": 0}

        def always_low(r, ctx):
            return True, 0.1, "low score"

        engine._validator = QualityValidator([always_low])
        engine.run(lambda ctx: 42, {})
        assert engine.status == LoopStatus.MAX_ITERATIONS
        assert engine.iteration == 3

    def test_manual_stop(self):
        engine = LoopEngine()
        engine.stop()
        assert engine.status == LoopStatus.MANUAL_STOP

    def test_task_error(self):
        engine = LoopEngine(LoopConfig(max_iterations=5))

        def failing_task(ctx):
            raise RuntimeError("test error")

        result = engine.run(failing_task, {})
        assert result is None
        assert engine.status == LoopStatus.ERROR

    def test_events_logged(self):
        engine = LoopEngine(LoopConfig(max_iterations=1, convergence_threshold=0.99))
        engine.run(lambda ctx: "ok", {})
        assert len(engine.events) >= 2  # start + stop (or validate)

    def test_replay(self):
        engine = LoopEngine(LoopConfig(max_iterations=1, convergence_threshold=0.99))
        engine.run(lambda ctx: "ok", {})
        replay = engine.replay()
        assert len(replay) >= 2

    def test_debug_report(self):
        engine = LoopEngine(LoopConfig(max_iterations=2, convergence_threshold=0.99))
        engine.run(lambda ctx: "ok", {})
        report = engine.get_debug_report()
        assert "status" in report
        assert "iterations" in report
        assert "events" in report
        assert "last_scores" in report

    def test_resume_from_checkpoint(self):
        engine = LoopEngine()
        engine._checkpoints.save("resume-key", {"resumed": True})
        state = engine.resume("resume-key")
        assert state == {"resumed": True}
        assert engine.status == LoopStatus.RUNNING
