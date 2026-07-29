"""Tests for SQLiteCheckpointStore."""

import tempfile
from pathlib import Path
from src.jig.orchestrator.checkpoint_store import SQLiteCheckpointStore


class TestSQLiteCheckpointStore:
    def setup_method(self):
        self._tmp = tempfile.mktemp(suffix=".db")
        self.store = SQLiteCheckpointStore(self._tmp)

    def teardown_method(self):
        self.store.close()
        Path(self._tmp).unlink(missing_ok=True)

    def test_save_and_load(self):
        cp = {
            "session_id": "test-1",
            "current_node_idx": 3,
            "completed_nodes": ["a", "b"],
            "context": {"user": "test"},
            "retry_count": 1,
            "escalate_level": 0,
        }
        self.store.save("test-1", cp)
        loaded = self.store.load("test-1")
        assert loaded is not None
        assert loaded["current_node_idx"] == 3
        assert len(loaded["completed_nodes"]) == 2
        assert loaded["context"]["user"] == "test"

    def test_load_missing(self):
        assert self.store.load("nonexistent") is None

    def test_save_updates(self):
        cp1 = {"session_id": "s1", "current_node_idx": 1, "completed_nodes": ["a"],
               "context": {}, "retry_count": 0, "escalate_level": 0}
        self.store.save("s1", cp1)
        cp2 = dict(cp1, current_node_idx=2, completed_nodes=["a", "b"])
        self.store.save("s1", cp2)
        loaded = self.store.load("s1")
        assert loaded["current_node_idx"] == 2
        assert len(loaded["completed_nodes"]) == 2

    def test_node_results(self):
        self.store.save_node_result("s1", "node_a", output="ok", duration_ms=100)
        self.store.save_node_result("s1", "node_b", error="fail", duration_ms=50)
        results = self.store.get_node_results("s1")
        assert len(results) == 2
        assert results[0]["node_name"] == "node_a"
        assert results[0]["output"] == "ok"
        assert results[1]["error"] == "fail"

    def test_list_sessions(self):
        self.store.save("s1", {"session_id": "s1", "current_node_idx": 1,
                               "completed_nodes": [], "context": {},
                               "retry_count": 0, "escalate_level": 0})
        self.store.save("s2", {"session_id": "s2", "current_node_idx": 0,
                               "completed_nodes": [], "context": {},
                               "retry_count": 0, "escalate_level": 0})
        sessions = self.store.list_sessions()
        assert len(sessions) >= 2

    def test_delete(self):
        self.store.save("s1", {"session_id": "s1", "current_node_idx": 0,
                               "completed_nodes": [], "context": {},
                               "retry_count": 0, "escalate_level": 0})
        self.store.save_node_result("s1", "node_a")
        self.store.delete("s1")
        assert self.store.load("s1") is None
        assert len(self.store.get_node_results("s1")) == 0
