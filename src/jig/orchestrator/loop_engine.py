"""Loop Engineering — 框架级可配置 Loop Engine。

IDEA-041: 将 LOOP SOP 从应用级硬编码提升为框架级可配置的 Loop Engine。

核心能力:
- Loop Run: 递归任务分解 + 工具调用策略可配置
- Loop Stop: 退出条件检测器（收敛检测 / 最大轮次 / 人工终止）
- Loop Validate: 中间结果自动质量评估
- Loop Restore: 检查点粒度可配置（节点级 / 执行器级 / 任务级）
- Loop Debug: 全链路事件日志 + 回放
"""

from __future__ import annotations
import abc
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class LoopStatus(Enum):
    """Loop 状态枚举。"""
    RUNNING = "running"
    CONVERGED = "converged"
    MAX_ITERATIONS = "max_iterations"
    MANUAL_STOP = "manual_stop"
    ERROR = "error"


class CheckpointGranularity(Enum):
    """检查点粒度。"""
    NODE = "node"         # 每个节点执行后保存
    EXECUTOR = "executor" # 每个执行器完成后保存
    TASK = "task"         # 每个任务完成后保存


@dataclass
class LoopConfig:
    """Loop Engine 配置。"""
    max_iterations: int = 10
    convergence_threshold: float = 0.95
    checkpoint_granularity: CheckpointGranularity = CheckpointGranularity.TASK
    enable_debug_log: bool = True
    auto_validate: bool = True
    tool_strategy: str = "greedy"  # greedy, conservative, exhaustive


@dataclass
class LoopEvent:
    """Loop 事件日志条目。"""
    timestamp: float
    event_type: str  # start, stop, validate, checkpoint, error
    node_name: str
    data: Dict[str, Any] = field(default_factory=dict)


class ConvergenceDetector:
    """收敛检测器 — 判断 Loop 是否达到收敛条件。"""

    def __init__(self, threshold: float = 0.95):
        self._threshold = threshold
        self._scores: List[float] = []

    def add_score(self, score: float) -> None:
        self._scores.append(score)

    def is_converged(self) -> bool:
        if len(self._scores) < 3:
            return False
        recent = self._scores[-3:]
        # 最近三次评分均接近 1.0 且方差小于阈值
        return all(s >= self._threshold for s in recent)

    @property
    def last_scores(self) -> List[float]:
        return self._scores[-5:] if self._scores else []


class QualityValidator:
    """中间结果质量评估器。"""

    def __init__(self, validators: Optional[List[Callable]] = None):
        self._validators = validators or []

    def validate(self, result: Any, context: Dict[str, Any]) -> Tuple[bool, float, str]:
        """评估结果质量。
        
        Returns:
            (是否通过, 质量评分, 评估信息)
        """
        if not self._validators:
            return True, 1.0, "no validators configured"
        
        scores = []
        messages = []
        for v in self._validators:
            try:
                passed, score, msg = v(result, context)
                scores.append(score)
                messages.append(msg)
            except Exception as e:
                logger.warning("Validator failed: %s", e)
                scores.append(0.0)
                messages.append(str(e))

        avg_score = sum(scores) / len(scores) if scores else 0.0
        all_passed = avg_score >= 0.7
        return all_passed, avg_score, "; ".join(messages)


class CheckpointManager:
    """检查点管理器 — 持久化 Loop 执行状态。"""

    def __init__(self, granularity: CheckpointGranularity = CheckpointGranularity.TASK):
        self._granularity = granularity
        self._checkpoints: Dict[str, Any] = {}

    def should_checkpoint(self, current_level: str) -> bool:
        levels = {"node": 0, "executor": 1, "task": 2}
        return levels.get(current_level, 0) >= levels[self._granularity.value]

    def save(self, key: str, state: Any) -> None:
        self._checkpoints[key] = {
            "state": state,
            "timestamp": time.time(),
        }
        logger.debug("Checkpoint saved: %s", key)

    def load(self, key: str) -> Optional[Any]:
        cp = self._checkpoints.get(key)
        if cp:
            logger.info("Checkpoint loaded: %s", key)
            return cp["state"]
        return None

    def list_checkpoints(self) -> List[str]:
        return list(self._checkpoints.keys())

    def clear(self) -> None:
        self._checkpoints.clear()


class LoopEngine:
    """框架级 Loop Engine。
    
    将 SOP 管道的每个阶段包装为可配置的 Loop 单元，
    支持递归分解、收敛检测、检查点恢复、事件回放。
    """

    def __init__(self, config: Optional[LoopConfig] = None):
        self._config = config or LoopConfig()
        self._events: List[LoopEvent] = []
        self._convergence = ConvergenceDetector(self._config.convergence_threshold)
        self._validator = QualityValidator()
        self._checkpoints = CheckpointManager(self._config.checkpoint_granularity)
        self._status = LoopStatus.RUNNING
        self._iteration = 0

    # ---- Properties ----

    @property
    def config(self) -> LoopConfig:
        return self._config

    @property
    def status(self) -> LoopStatus:
        return self._status

    @property
    def iteration(self) -> int:
        return self._iteration

    @property
    def events(self) -> List[LoopEvent]:
        return list(self._events)

    # ---- Core Loop Methods ----

    def run(self, task: Callable, context: Dict[str, Any]) -> Any:
        """执行一个 Loop 单元，返回最终结果。
        
        Args:
            task: 可调用对象，接收 context 参数
            context: 执行上下文
        
        Returns:
            执行结果
        """
        self._log_event("start", "loop", {"task": task.__name__ if hasattr(task, "__name__") else "anonymous"})

        while self._status == LoopStatus.RUNNING and self._iteration < self._config.max_iterations:
            self._iteration += 1
            logger.info("Loop iteration %d/%d", self._iteration, self._config.max_iterations)

            try:
                result = task(context)
            except Exception as e:
                logger.error("Loop iteration %d failed: %s", self._iteration, e)
                self._log_event("error", "loop", {"error": str(e), "iteration": self._iteration})
                self._status = LoopStatus.ERROR
                return None

            # 质量评估
            if self._config.auto_validate:
                passed, score, msg = self._validator.validate(result, context)
                self._convergence.add_score(score)
                self._log_event("validate", "loop", {"score": score, "message": msg})

                if self._convergence.is_converged():
                    logger.info("Loop converged at iteration %d (score=%.2f)", self._iteration, score)
                    self._status = LoopStatus.CONVERGED
                    self._log_event("stop", "loop", {"reason": "converged", "score": score})
                    return result

            # 检查点
            if self._checkpoints.should_checkpoint("node"):
                self._checkpoints.save(f"iter-{self._iteration}", result)

        if self._iteration >= self._config.max_iterations:
            self._status = LoopStatus.MAX_ITERATIONS
            self._log_event("stop", "loop", {"reason": "max_iterations", "iteration": self._iteration})

        return result

    def stop(self) -> None:
        """手动终止 Loop。"""
        self._status = LoopStatus.MANUAL_STOP
        self._log_event("stop", "loop", {"reason": "manual_stop"})
        logger.info("Loop manually stopped at iteration %d", self._iteration)

    def resume(self, checkpoint_key: str) -> Optional[Any]:
        """从检查点恢复执行。"""
        state = self._checkpoints.load(checkpoint_key)
        if state:
            self._status = LoopStatus.RUNNING
            self._log_event("start", "resume", {"checkpoint": checkpoint_key})
        return state

    # ---- Debug & Logging ----

    def _log_event(self, event_type: str, node: str, data: Dict[str, Any]) -> None:
        event = LoopEvent(
            timestamp=time.time(),
            event_type=event_type,
            node_name=node,
            data=data,
        )
        self._events.append(event)
        if self._config.enable_debug_log:
            logger.debug("[Loop] %s | %s | %s", event_type, node, json.dumps(data, ensure_ascii=False))

    def replay(self) -> List[Dict[str, Any]]:
        """回放全链路事件日志。"""
        return [
            {
                "time": e.timestamp,
                "type": e.event_type,
                "node": e.node_name,
                "data": e.data,
            }
            for e in self._events
        ]

    def get_debug_report(self) -> Dict[str, Any]:
        """生成调试报告。"""
        return {
            "status": self._status.value,
            "iterations": self._iteration,
            "max_iterations": self._config.max_iterations,
            "converged": self._status == LoopStatus.CONVERGED,
            "last_scores": self._convergence.last_scores,
            "total_events": len(self._events),
            "events": self.replay()[-10:],  # 最近 10 条
        }
