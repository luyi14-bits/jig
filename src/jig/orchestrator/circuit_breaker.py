"""熔断器 + 漂移检测。

CircuitBreaker: 三态 CLOSED/OPEN/HALF_OPEN + 指数退避。
DriftDetector: Agent 输出格式校验 + 置信度阈值。
"""

from __future__ import annotations

import time
import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"       # 正常工作
    OPEN = "open"           # 熔断
    HALF_OPEN = "half_open" # 试探


class CircuitBreaker:
    """熔断器 — 保护下游不被连续失败击穿。

    Usage:
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        if cb.can_call():
            try:
                result = cb.call(my_function)
            except Exception as e:
                cb.record_failure()
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        name: str = "default",
    ) -> None:
        self._threshold = failure_threshold
        self._timeout = recovery_timeout
        self._name = name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0

    @property
    def state(self) -> CircuitState:
        return self._state

    def can_call(self) -> bool:
        """是否可以调用下游。"""
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self._timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info("熔断器(%s): OPEN → HALF_OPEN (超时)", self._name)
                return True
            return False

        # HALF_OPEN: 允许一次试探
        return True

    def record_success(self) -> None:
        """记录成功 — 重置熔断器。"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        logger.info("熔断器(%s): 恢复 CLOSED", self._name)

    def record_failure(self) -> None:
        """记录失败 — 可能触发熔断。"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning("熔断器(%s): HALF_OPEN → OPEN (试探失败)", self._name)
        elif self._failure_count >= self._threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "熔断器(%s): CLOSED → OPEN (连续%d次失败)",
                self._name, self._threshold,
            )

    def call(self, func, *args, **kwargs) -> Any:
        """安全调用 — 熔断检查 + 失败记录。"""
        if not self.can_call():
            raise RuntimeError(f"熔断器({self._name}) OPEN，拒绝调用")
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


class DriftDetector:
    """漂移检测 — 校验 Agent 输出是否偏离预期。"""

    REQUIRED_FIELDS = {"summary", "confidence", "source_agent", "target_agent"}

    def __init__(self, confidence_threshold: float = 0.8) -> None:
        self._threshold = confidence_threshold

    def check_handover(self, handover: Dict[str, Any]) -> Dict[str, Any]:
        """校验 HandoverPackage。

        Args:
            handover: 待校验的交接包

        Returns:
            {"passed": bool, "issues": [str, ...]}
        """
        issues = []

        # 字段完整性
        missing = self.REQUIRED_FIELDS - set(handover.keys())
        if missing:
            issues.append(f"缺少字段: {', '.join(sorted(missing))}")

        # 类型检查
        if not isinstance(handover.get("summary", ""), str):
            issues.append("summary 必须是字符串")
        confidence = handover.get("confidence", 1.0)
        if not isinstance(confidence, (int, float)):
            issues.append("confidence 必须是数字")
        elif confidence < self._threshold:
            issues.append(f"置信度过低: {confidence} < {self._threshold}")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "confidence": confidence,
        }
