"""Tests for CircuitBreaker + DriftDetector — 对齐真实 API。"""

from src.jig.orchestrator.circuit_breaker import CircuitBreaker, DriftDetector, CircuitState


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_can_call_closed(self):
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.can_call() is True

    def test_open_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_call() is False

    def test_recovery_half_open(self):
        import time
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        # 超时 0 → 立即进入半开
        time.sleep(0.01)
        assert cb.can_call() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_reset_on_success(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_call_success(self):
        cb = CircuitBreaker()
        result = cb.call(lambda: "ok")
        assert result == "ok"

    def test_call_failure_recorded(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

        def boom():
            raise ValueError("boom")

        try:
            cb.call(boom)
        except ValueError:
            pass
        assert cb.state == CircuitState.CLOSED  # 1 次失败未达阈值
        try:
            cb.call(boom)
        except ValueError:
            pass
        assert cb.state == CircuitState.OPEN


class TestDriftDetector:
    def test_valid_handover_passes(self):
        d = DriftDetector()
        result = d.check_handover({
            "summary": "任务完成",
            "confidence": 0.95,
            "source_agent": "pm",
            "target_agent": "spec",
        })
        assert result["passed"] is True
        assert result["issues"] == []

    def test_missing_fields(self):
        d = DriftDetector()
        result = d.check_handover({"summary": "ok"})
        assert result["passed"] is False
        assert any("缺少字段" in i for i in result["issues"])

    def test_low_confidence(self):
        d = DriftDetector(confidence_threshold=0.8)
        result = d.check_handover({
            "summary": "不确定",
            "confidence": 0.3,
            "source_agent": "a",
            "target_agent": "b",
        })
        assert result["passed"] is False
        assert any("置信度" in i for i in result["issues"])

    def test_wrong_types(self):
        d = DriftDetector()
        result = d.check_handover({
            "summary": 123,
            "confidence": "high",
            "source_agent": "a",
            "target_agent": "b",
        })
        assert result["passed"] is False
