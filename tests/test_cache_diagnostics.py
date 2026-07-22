"""Tests for CacheDiagnosticPanel."""

from jig.adapters.cache_diagnostics import CacheDiagnosticPanel


class TestCacheDiagnosticPanel:
    def test_record_snapshot(self):
        panel = CacheDiagnosticPanel()
        result = panel.record_snapshot({
            "session_id": "test-sess",
            "prefix_hash": "abc123",
            "prefix_length": 500,
            "immutable_frozen": True,
            "total_requests": 10,
            "cached_requests": 8,
            "hit_rate": 0.8,
            "cold_start": False,
            "estimated_savings_usd": 0.05,
        })
        assert result.session_id == "test-sess"
        assert result.hit_rate == 0.8

    def test_get_report_with_data(self):
        panel = CacheDiagnosticPanel()
        panel.record_snapshot({
            "session_id": "s1", "prefix_hash": "h1", "prefix_length": 100,
            "immutable_frozen": True, "total_requests": 10, "cached_requests": 8,
            "hit_rate": 0.8, "cold_start": False, "estimated_savings_usd": 0.05,
        })
        report = panel.get_report()
        assert report["status"] == "active"
        assert "recommendations" in report

    def test_get_report_empty(self):
        panel = CacheDiagnosticPanel()
        report = panel.get_report()
        assert report["status"] == "no_data"

    def test_recommendations_generated(self):
        panel = CacheDiagnosticPanel()
        panel.record_snapshot({
            "session_id": "s1", "prefix_hash": "h1", "prefix_length": 100,
            "immutable_frozen": False, "total_requests": 5, "cached_requests": 1,
            "hit_rate": 0.2, "cold_start": True, "estimated_savings_usd": 0.001,
        })
        report = panel.get_report()
        assert len(report["recommendations"]) >= 2

    def test_clear_history(self):
        panel = CacheDiagnosticPanel()
        panel.record_snapshot({"session_id": "s1", "prefix_hash": "h1",
            "prefix_length": 100, "immutable_frozen": True, "total_requests": 1,
            "cached_requests": 1, "hit_rate": 1.0, "cold_start": False,
            "estimated_savings_usd": 0.0})
        panel.clear_history()
        assert panel.get_report()["status"] == "no_data"
