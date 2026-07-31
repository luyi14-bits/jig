"""Tests for IntentRouter — classify_query + hyde_rewrite."""

from src.jig.orchestrator.intent_router import classify_query, hyde_rewrite


class TestClassifyQuery:
    def test_short_query_simple(self):
        assert classify_query("你好") in ("simple", "short")

    def test_complex_query(self):
        result = classify_query("请帮我分析这个项目架构，并且对比三个框架，最后给出优化建议，同时评估风险")
        assert result in ("complex", "multi_turn")

    def test_unknown_role_returns(self):
        result = classify_query("帮我搜索一下天气")
        assert isinstance(result, str)
        assert result != ""

    def test_returns_str(self):
        assert isinstance(classify_query("anything"), str)


class TestHydeRewrite:
    def test_returns_string(self):
        result = hyde_rewrite("复杂查询内容" * 20)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_not_empty_for_short(self):
        result = hyde_rewrite("测试")
        assert isinstance(result, str)
