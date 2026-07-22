"""上下文压缩体系测试套件。"""
import pytest
from pathlib import Path
from jig.adapters.repo_map import RepoMapBuilder, PySymbolExtractor
from jig.adapters.conversation_compressor import ConversationCompressor
from jig.adapters.embedding_index import EmbeddingIndex
from jig.adapters.cache_engine import CacheEngine
from jig.core.skill_def import SkillDef

BUDGET_A = 500
BUDGET_B = 50000
BUDGET_C = 10

class TestRepoMap:
    def test_extract_symbols(self):
        text = "class MyClass:\n  pass\n\ndef top_func():\n  pass"
        syms = PySymbolExtractor.extract(text)
        found_classes = [s for s in syms if "MyClass" in s]
        found_funcs = [s for s in syms if "top_func" in s]
        assert len(found_classes) > 0
        assert len(found_funcs) > 0

    def test_build_repo_map(self):
        builder = RepoMapBuilder()
        src_dir = Path("src")
        if src_dir.exists():
            result = builder.build(src_dir, token_budget=BUDGET_A)
            assert isinstance(result, str) and len(result) > 0

    def test_build_for_skills(self):
        builder = RepoMapBuilder()
        skill_dir = Path("skills")
        if skill_dir.exists():
            result = builder.build_for_skills(skill_dir)
            assert isinstance(result, str)

class TestConversationCompressor:
    def test_no_compression_below_threshold(self):
        compressor = ConversationCompressor(max_history_tokens=BUDGET_B)
        msgs = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
        result = compressor.compress(msgs)
        assert len(result) == 2

    def test_hybrid_mode_summarizes(self):
        compressor = ConversationCompressor(mode="hybrid", max_history_tokens=BUDGET_C, keep_last_n=1)
        msgs = [{"role": "system", "content": "role"}]
        for idx in range(9):
            msgs.append({"role": "user", "content": "A" * 1000})
            msgs.append({"role": "assistant", "content": "ok"})
        result = compressor.compress(msgs)
        assert len(result) > 0

class TestEmbeddingIndex:
    @pytest.fixture
    def sample_skills(self):
        return [SkillDef(name="pm-agent", description="产品经理, PRD, 需求分析"),
                SkillDef(name="coding-agent", description="开发, Python, 编码"),
                SkillDef(name="security-agent", description="安全审计, CVE")]

    def test_add_and_count(self, sample_skills):
        index = EmbeddingIndex()
        index.add_skills(sample_skills)
        assert index.count() == 3

    def test_keyword_search(self, sample_skills):
        index = EmbeddingIndex()
        index.add_skills(sample_skills)
        results = index.search("PRD", top_k=2)
        assert len(results) > 0
        assert results[0]["name"] == "pm-agent"

    def test_search_empty(self):
        assert EmbeddingIndex().search("anything") == []

class TestCacheEnhancements:
    def test_cache_breakpoint(self):
        assert "cache_control" in CacheEngine().mark_cache_breakpoint()

    def test_cache_stats(self):
        engine = CacheEngine()
        engine.assemble_prefix(base_prompt="test")
        engine.record_cache_hit()
        assert engine.stats.total_requests >= 1

    def test_keepalive(self):
        CacheEngine().keepalive()
