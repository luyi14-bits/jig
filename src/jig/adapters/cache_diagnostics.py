"""缓存诊断面板 — 可视化缓存性能指标。

IDEA-047: 将 cache-guard 从测试工具升级为框架级缓存诊断面板。
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import time


@dataclass
class CacheDiagnosticResult:
    """单次缓存诊断结果。"""
    session_id: str
    prefix_hash: str
    prefix_length: int
    immutable_frozen: bool
    total_requests: int
    cached_requests: int
    hit_rate: float
    cold_start: bool
    estimated_savings_usd: float
    timestamp: float = 0.0


class CacheDiagnosticPanel:
    """缓存诊断面板。

    聚合 CacheEngine 的统计数据，提供可读的诊断报告。
    """

    def __init__(self):
        self._history: List[CacheDiagnosticResult] = []

    def record_snapshot(self, engine_stats: Dict) -> CacheDiagnosticResult:
        """记录一次缓存快照。"""
        result = CacheDiagnosticResult(
            session_id=engine_stats.get("session_id", ""),
            prefix_hash=engine_stats.get("prefix_hash", ""),
            prefix_length=engine_stats.get("prefix_length", 0),
            immutable_frozen=engine_stats.get("immutable_frozen", False),
            total_requests=engine_stats.get("total_requests", 0),
            cached_requests=engine_stats.get("cached_requests", 0),
            hit_rate=engine_stats.get("hit_rate", 0.0),
            cold_start=engine_stats.get("cold_start", True),
            estimated_savings_usd=engine_stats.get("estimated_savings_usd", 0.0),
            timestamp=time.time(),
        )
        self._history.append(result)
        return result

    def get_report(self) -> Dict:
        """生成诊断报告。"""
        if not self._history:
            return {"status": "no_data", "message": "无缓存数据"}

        latest = self._history[-1]
        total_savings = sum(r.estimated_savings_usd for r in self._history)
        avg_hit_rate = sum(r.hit_rate for r in self._history) / len(self._history)

        return {
            "status": "active" if latest.immutable_frozen else "warming",
            "current": {
                "hit_rate": round(latest.hit_rate * 100, 1),
                "prefix_hash": latest.prefix_hash[:16],
                "prefix_length": latest.prefix_length,
                "cold_start": latest.cold_start,
            },
            "aggregate": {
                "total_requests": latest.total_requests,
                "cached_requests": latest.cached_requests,
                "avg_hit_rate": round(avg_hit_rate * 100, 1),
                "estimated_savings_usd": round(total_savings, 4),
                "snapshots": len(self._history),
            },
            "recommendations": self._generate_recommendations(latest),
        }

    def _generate_recommendations(self, r: CacheDiagnosticResult) -> List[str]:
        recs = []
        if not r.immutable_frozen:
            recs.append("不可变前缀未冻结 — 调用 freeze_prefix() 以提高缓存命中率")
        if r.hit_rate < 0.5:
            recs.append("缓存命中率偏低 — 检查前缀组装顺序是否稳定")
        if r.cold_start:
            recs.append("冷启动 — 首轮请求缓存未命中，属正常现象")
        if r.estimated_savings_usd > 0.1:
            recs.append(f"缓存已节省 ${r.estimated_savings_usd:.4f} — 前缀策略有效")
        return recs

    def clear_history(self) -> None:
        self._history.clear()
