"""成本感知调度路由器 — Flash-first + Token 预算控制。

对标 Reasonix 的 flash-first 策略：默认 Flash，按需 /pro，/preset max。
"""

from __future__ import annotations
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TokenBudget:
    """Token 预算追踪器。"""

    def __init__(self, session_budget: int = 100000, monthly_budget: int = 5000000) -> None:
        self._session_budget = session_budget
        self._monthly_budget = monthly_budget
        self._session_used = 0
        self._monthly_used = 0
        self._total_cost_usd = 0.0
        self._cache_hits = 0
        self._cache_misses = 0

    def record_call(self, tokens: int, cost_usd: float, cache_hit: bool = False) -> None:
        self._session_used += tokens
        self._monthly_used += tokens
        self._total_cost_usd += cost_usd
        if cache_hit:
            self._cache_hits += 1
        else:
            self._cache_misses += 1

    def can_call(self) -> bool:
        return self._session_used < self._session_budget and self._monthly_used < self._monthly_budget

    @property
    def remaining_session(self) -> int:
        return max(0, self._session_budget - self._session_used)

    @property
    def hit_rate(self) -> float:
        total = self._cache_hits + self._cache_misses
        return self._cache_hits / total if total > 0 else 0.0

    @property
    def total_cost(self) -> float:
        return self._total_cost_usd


class CostAwareRouter:
    """成本感知路由器 — 默认 Flash，按需升级 Pro。

    Flash-first 策略：
    - 所有 Agent 默认路由到 Flash 模型
    - 短查询（<100 token）用 Flash（低 temperature 保证确定性）
    - 长/复杂查询自动升级到 Pro
    - Token 预算超限时主动熔断
    """

    FLASH_COST_PER_1K = 0.0001   # Flash 每 1k token 价格
    PRO_COST_PER_1K = 0.002      # Pro 每 1k token 价格

    def __init__(self, budget: Optional[TokenBudget] = None) -> None:
        self._budget = budget or TokenBudget()
        self._upgrade_count = 0
        self._flash_count = 0

    def route(self, prompt: str, forced_model: str = "") -> str:
        """选择模型。

        Args:
            prompt: 用户输入
            forced_model: 强制指定模型（覆盖策略）

        Returns:
            "flash" 或 "pro"
        """
        if forced_model in ("pro", "flash"):
            return forced_model

        if not self._budget.can_call():
            logger.warning("Token 预算超限，拒绝调用")
            return ""

        # 短查询用 Flash
        if len(prompt) < 100:
            self._flash_count += 1
            return "flash"

        # 长查询升级到 Pro
        self._upgrade_count += 1
        return "pro"

    def estimate_cost(self, tokens: int, model: str, cache_hit: bool = False) -> float:
        """估算费用。"""
        rate = self.FLASH_COST_PER_1K if model == "flash" else self.PRO_COST_PER_1K
        cost = (tokens / 1000) * rate
        if cache_hit:
            cost *= 0.02  # DeepSeek 缓存命中仅 2% 费用
        return cost

    @property
    def stats(self) -> Dict[str, int]:
        return {"flash": self._flash_count, "pro_upgrade": self._upgrade_count,
                "remaining_session_tokens": self._budget.remaining_session}

    def reset_session(self) -> None:
        self._budget = TokenBudget()
        self._upgrade_count = 0
        self._flash_count = 0
