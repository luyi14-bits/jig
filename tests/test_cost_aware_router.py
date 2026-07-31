"""Tests for CostAwareRouter + TokenBudget — 对齐真实 API。"""

from src.jig.adapters.cost_aware_router import CostAwareRouter, TokenBudget


class TestTokenBudget:
    def test_initial_can_call(self):
        tb = TokenBudget(session_budget=1000, monthly_budget=100000)
        assert tb.can_call() is True

    def test_record_call(self):
        tb = TokenBudget(session_budget=1000, monthly_budget=100000)
        tb.record_call(tokens=100, cost_usd=0.01)
        assert tb.remaining_session == 900

    def test_session_exhausted(self):
        tb = TokenBudget(session_budget=100, monthly_budget=100000)
        tb.record_call(tokens=101, cost_usd=0.01)
        assert tb.can_call() is False

    def test_monthly_exhausted(self):
        tb = TokenBudget(session_budget=100000, monthly_budget=30)
        tb.record_call(tokens=10, cost_usd=1)
        tb.record_call(tokens=10, cost_usd=20)
        tb.record_call(tokens=10, cost_usd=20)
        assert tb.can_call() is False

    def test_total_cost(self):
        tb = TokenBudget(session_budget=100000, monthly_budget=100000)
        tb.record_call(tokens=10, cost_usd=1.0)
        tb.record_call(tokens=10, cost_usd=2.0)
        assert tb.total_cost == 3.0

    def test_hit_rate(self):
        tb = TokenBudget(session_budget=100000, monthly_budget=100000)
        tb.record_call(tokens=10, cost_usd=0.01, cache_hit=True)
        tb.record_call(tokens=10, cost_usd=0.01, cache_hit=False)
        assert tb.hit_rate == 0.5


class TestCostAwareRouter:
    def test_short_prompt_flash(self):
        router = CostAwareRouter()
        assert router.route("你好") == "flash"

    def test_long_prompt_pro(self):
        router = CostAwareRouter()
        long_prompt = "请详细分析这个系统架构" + "，包括模块交互和性能瓶颈" * 10
        assert router.route(long_prompt) == "pro"

    def test_forced_model(self):
        router = CostAwareRouter()
        assert router.route("你好", forced_model="pro") == "pro"
        assert router.route("很长的查询" * 50, forced_model="flash") == "flash"

    def test_budget_exhausted_returns_empty(self):
        tb = TokenBudget(session_budget=10, monthly_budget=100000)
        router = CostAwareRouter(budget=tb)
        tb.record_call(tokens=100, cost_usd=1.0)
        assert router.route("你好") == ""

    def test_stats(self):
        router = CostAwareRouter()
        router.route("你好")
        router.route("很长" * 100)
        stats = router.stats
        assert stats["flash"] >= 1
        assert stats["pro_upgrade"] >= 1

    def test_estimate_cost_flash(self):
        router = CostAwareRouter()
        cost = router.estimate_cost(1000, "flash")
        assert cost == 0.0001

    def test_estimate_cost_cache_hit(self):
        router = CostAwareRouter()
        cost = router.estimate_cost(1000, "pro", cache_hit=True)
        assert cost == 0.002 * 0.02

    def test_reset_session(self):
        tb = TokenBudget(session_budget=10, monthly_budget=100000)
        router = CostAwareRouter(budget=tb)
        tb.record_call(tokens=100, cost_usd=1.0)
        assert router.route("你好") == ""
        router.reset_session()
        assert router.route("你好") == "flash"
