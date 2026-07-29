"""Tests for MetricsCollector."""

from src.jig.adapters.metrics import MetricsCollector, timed


class TestMetricsCollector:
    def test_record_and_summary(self):
        c = MetricsCollector()
        c.record("test_op", 100.0)
        c.record("test_op", 200.0)
        s = c.summary("test_op")
        assert s.count == 2
        assert s.avg_ms == 150.0
        assert s.max_ms == 200.0
        assert s.min_ms == 100.0

    def test_record_error(self):
        c = MetricsCollector()
        c.record("err_op", 50.0, error=True)
        s = c.summary("err_op")
        assert s.errors == 1
        assert s.error_rate == 1.0

    def test_empty_summary(self):
        c = MetricsCollector()
        s = c.summary("nonexistent")
        assert s.count == 0
        assert s.total_ms == 0.0

    def test_timed_decorator(self):
        c = MetricsCollector()
        collector_ref = c

        original_collector = __import__("src.jig.adapters.metrics", fromlist=["_collector"])._collector
        import src.jig.adapters.metrics as m
        m._collector = c  # temporarily replace

        @timed("timed_fn")
        def my_fn():
            return 42

        result = my_fn()
        assert result == 42
        s = c.summary("timed_fn")
        assert s.count >= 1

        m._collector = original_collector  # restore

    def test_timed_decorator_error(self):
        c = MetricsCollector()
        import src.jig.adapters.metrics as m
        original = m._collector
        m._collector = c

        @timed("err_fn")
        def fail_fn():
            raise ValueError("fail")

        try:
            fail_fn()
        except ValueError:
            pass

        s = c.summary("err_fn")
        assert s.errors >= 1
        m._collector = original

    def test_metrics_text_format(self):
        c = MetricsCollector()
        c.record("node_exec", 150.0)
        text = c.metrics_text()
        assert "jig_node_exec_count" in text
        assert "jig_node_exec_total_ms" in text
        assert "jig_node_exec_avg_ms" in text
        assert "150" in text

    def test_metrics_text_empty(self):
        c = MetricsCollector()
        text = c.metrics_text()
        assert text == ""
