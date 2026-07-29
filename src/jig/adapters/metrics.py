"""OTel-compatible metrics for Jig framework.

Lightweight metrics collection without requiring OpenTelemetry SDK.
Exposes /metrics endpoint for Prometheus scraping.
"""

from __future__ import annotations
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass
class MetricSummary:
    """聚合指标。"""
    count: int = 0
    total_ms: float = 0.0
    errors: int = 0
    min_ms: float = float("inf")
    max_ms: float = 0.0

    @property
    def avg_ms(self) -> float:
        return round(self.total_ms / max(self.count, 1), 2)

    @property
    def error_rate(self) -> float:
        return round(self.errors / max(self.count, 1), 4)


class MetricsCollector:
    """线程安全的 metrics 采集器。"""

    def __init__(self):
        self._metrics: Dict[str, List[float]] = defaultdict(list)
        self._errors: Dict[str, int] = defaultdict(int)

    def record(self, name: str, duration_ms: float, error: bool = False) -> None:
        self._metrics[name].append(duration_ms)
        if error:
            self._errors[name] += 1

    def summary(self, name: str) -> MetricSummary:
        durations = self._metrics.get(name, [])
        if not durations:
            return MetricSummary()
        return MetricSummary(
            count=len(durations),
            total_ms=sum(durations),
            errors=self._errors.get(name, 0),
            min_ms=min(durations),
            max_ms=max(durations),
        )

    def all_summaries(self) -> Dict[str, MetricSummary]:
        return {k: self.summary(k) for k in list(self._metrics.keys())}

    def metrics_text(self) -> str:
        """Prometheus text format output."""
        lines: List[str] = []
        for name, summary in sorted(self.all_summaries().items()):
            safe = name.replace("-", "_").replace(" ", "_")
            lines.append(f"# HELP jig_{safe} Jig metric")
            lines.append(f"# TYPE jig_{safe} gauge")
            lines.append(f'jig_{safe}_count{{name="{name}"}} {summary.count}')
            lines.append(f'jig_{safe}_total_ms{{name="{name}"}} {summary.total_ms}')
            lines.append(f'jig_{safe}_avg_ms{{name="{name}"}} {summary.avg_ms}')
            lines.append(f'jig_{safe}_errors{{name="{name}"}} {summary.errors}')
        return "\n".join(lines)


# Global collector
_collector = MetricsCollector()


def get_collector() -> MetricsCollector:
    return _collector


def timed(name: str) -> Callable:
    """Decorator: record duration to metrics collector."""
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                _collector.record(name, duration)
                return result
            except Exception:
                duration = (time.perf_counter() - start) * 1000
                _collector.record(name, duration, error=True)
                raise
        return wrapper
    return decorator
