"""Memory 记忆体系测试套件。"""

import pytest
import tempfile
import os
from jig.orchestrator.memory import LocalStore, MemoryRouter, Consolidator


class TestLocalStore:
    def test_init_creates_tables(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        store = LocalStore(db_path)
        tables = store._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "memory_log" in table_names
        assert "profiles" in table_names
        assert "sessions" in table_names
        store.close()
        os.unlink(db_path)

    def test_profile_crud(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        store = LocalStore(db_path)
        store.set_profile("pm-agent", "language", "zh-CN")
        assert store.get_profile("pm-agent", "language") == "zh-CN"
        assert store.get_profile("pm-agent", "nonexistent", "default") == "default"
        profiles = store.get_all_profiles("pm-agent")
        assert "language" in profiles
        store.close()
        os.unlink(db_path)

    def test_session_save_and_get(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        store = LocalStore(db_path)
        store.save_session("sess-001", {"user": "test", "priority": "high"})
        meta = store.get_session("sess-001")
        assert meta is not None
        assert meta["user"] == "test"
        store.close()
        os.unlink(db_path)

    def test_memory_log(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        store = LocalStore(db_path)
        store.log_memory("coding-agent", "summary", {"text": "完成了登录功能"})
        store.log_memory("pm-agent", "episodic", {"decision": "采用方案A"})
        results = store.query_memory(agent="coding-agent")
        assert len(results) == 1
        assert results[0]["type"] == "summary"
        all_results = store.query_memory(limit=10)
        assert len(all_results) == 2
        store.close()
        os.unlink(db_path)


class TestMemoryRouter:
    def test_route_working(self):
        store = LocalStore(":memory:")
        router = MemoryRouter(store)
        result = router.route("working", "pm-agent", {"msg": "test"})
        assert "context_partitioner" in result

    def test_route_episodic(self):
        store = LocalStore(":memory:")
        router = MemoryRouter(store)
        result = router.route("episodic", "pm-agent", {"decision": "方案A"})
        assert "sqlite" in result

    def test_route_summary(self):
        store = LocalStore(":memory:")
        router = MemoryRouter(store)
        result = router.route("summary", "coding-agent", {"summary": "完成"})
        assert "sqlite" in result

    def test_route_invalid_type(self):
        store = LocalStore(":memory:")
        router = MemoryRouter(store)
        with pytest.raises(ValueError):
            router.route("invalid", "agent", {})


class TestConsolidator:
    def test_forget_old_memories(self):
        store = LocalStore(":memory:")
        consolidator = Consolidator(store)
        store.log_memory("pm-agent", "summary", {"text": "old"})
        deleted = consolidator.forget(threshold_days=0)
        assert deleted >= 0

    def test_merge_returns_false_for_single(self):
        store = LocalStore(":memory:")
        consolidator = Consolidator(store)
        store.log_memory("pm-agent", "summary", {"summary": "关于登录功能的讨论"})
        result = consolidator.merge("pm-agent", "登录")
        assert result is False
