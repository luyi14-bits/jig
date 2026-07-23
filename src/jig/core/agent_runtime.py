"""Agent Runtime — State + Checkpoint + Memory 分离。

三核心概念互不耦合:

- State:   Agent 运行时状态机 (idle→running→failed→retrying→recovered→done)
- Checkpoint: 执行进度快照，用于恢复 (独立于 State 和 Memory)
- Memory:  长期可检索知识，Agent 只引用不拥有

失败恢复: fail → summarize → upgrade → retry
"""

from __future__ import annotations
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent 运行时状态。独立于 Checkpoint 和 Memory。"""
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    FAILED = "failed"
    RETRYING = "retrying"
    PAUSED = "paused"
    RECOVERED = "recovered"
    DONE = "done"


class UpgradeStrategy(Enum):
    """升级策略。"""
    MODEL = "model"         # Flash → Pro
    POLICY = "policy"       # 放宽约束 / 换工具
    ROLE = "role"           # escalate 给更强 Agent


@dataclass
class Checkpoint:
    """执行进度快照 — 只记录进度，不混入 State 或 Memory。"""
    id: str = ""
    step: str = ""           # 当前执行到哪一步
    context: Dict = field(default_factory=dict)
    completed: List[str] = field(default_factory=list)  # 哪些已完成
    timestamp: float = 0.0


@dataclass
class Lesson:
    """从失败中提取的教训。"""
    cause: str = ""
    action: str = ""
    suggestion: str = ""


@dataclass
class AgentResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    retries: int = 0
    lesson: Optional[Lesson] = None
    upgrade_path: List[str] = field(default_factory=list)


class AgentRuntime:
    """Agent 运行时 — State / Checkpoint / Memory 分离。

    Core loop: fail → summarize → upgrade → retry
    """

    def __init__(self, name: str, max_retries: int = 3):
        self._name = name
        self._id = uuid.uuid4().hex[:12]
        # State (session, volatile)
        self._state = AgentState.IDLE
        self._context: Dict[str, Any] = {}
        # Checkpoint (persistent snapshots)
        self._checkpoints: List[Checkpoint] = []
        # Memory (long-term knowledge) — 只引用，不拥有
        self._memory_ref: Optional[Callable] = None
        # Retry state
        self._retry_count = 0
        self._max_retries = max_retries
        self._lessons: List[Lesson] = []
        self._upgrade_history: List[str] = []
        # Timeline
        self._timeline: List[Dict] = []
        # Lifecycle hooks
        self._on_run: Optional[Callable] = None

    # ---- Properties ----

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def context(self) -> Dict:
        return dict(self._context)

    @property
    def retries(self) -> int:
        return self._retry_count

    @property
    def checkpoints(self) -> List[Checkpoint]:
        return list(self._checkpoints)

    # ---- Public API ----

    def run(self, task: Callable, context: Optional[Dict] = None) -> AgentResult:
        """执行 Agent 任务。失败自动走 fail→summarize→upgrade→retry 闭环。"""
        if context:
            self._context.update(context)

        self._transition_to(AgentState.RUNNING)
        self._save_checkpoint("start")

        while self._retry_count <= self._max_retries:
            try:
                result = task(self._context) if self._on_run else task(self._context)
                self._save_checkpoint("completed")
                self._transition_to(AgentState.DONE)
                return AgentResult(
                    success=True, output=result, retries=self._retry_count,
                    upgrade_path=list(self._upgrade_history),
                )

            except Exception as e:
                self._retry_count += 1
                self._transition_to(AgentState.FAILED)
                self._save_checkpoint("failed")

                # ----- Summarize -----
                lesson = self._summarize_failure(e)
                self._lessons.append(lesson)
                logger.info("%s: 失败总结 — %s", self._name, lesson.cause)

                if self._retry_count > self._max_retries:
                    self._transition_to(AgentState.DONE)
                    return AgentResult(
                        success=False, error=str(e), retries=self._retry_count,
                        lesson=lesson, upgrade_path=list(self._upgrade_history),
                    )

                # ----- Upgrade -----
                strategy = self._choose_upgrade()
                upgrade_msg = self._apply_upgrade(strategy)
                self._upgrade_history.append(f"{strategy.value}:{upgrade_msg}")

                # ----- Retry -----
                self._transition_to(AgentState.RETRYING)
                self._save_checkpoint(f"retry-{self._retry_count}")

        return AgentResult(success=False, retries=self._retry_count)

    def pause(self) -> None:
        self._transition_to(AgentState.PAUSED)
        self._save_checkpoint("paused")

    def resume(self) -> None:
        self._transition_to(AgentState.RUNNING)

    def restore_checkpoint(self, cp_id: str) -> bool:
        """从指定检查点恢复进度（不恢复 State 和 Memory）。"""
        for cp in self._checkpoints:
            if cp.id == cp_id:
                self._context = dict(cp.context)
                self._transition_to(AgentState.RECOVERED)
                return True
        return False

    # ---- Internal: Summarize / Upgrade / Retry ----

    def _summarize_failure(self, error: Exception) -> Lesson:
        """分析失败原因，提取教训。"""
        error_str = str(error)
        if "timeout" in error_str.lower():
            return Lesson(cause="工具调用超时", action="增加超时时间或优化工具调用",
                          suggestion=f"尝试升级到 Pro 模型或增加超时 {error_str}")
        elif "401" in error_str or "unauthorized" in error_str.lower():
            return Lesson(cause="认证失败", action="检查 API Key", suggestion="验证 API Key 配置")
        elif "token" in error_str.lower() and "limit" in error_str.lower():
            return Lesson(cause="Token 超限", action="截断上下文或加大 Token 限制",
                          suggestion="尝试缩小上下文窗口")
        else:
            return Lesson(cause=error_str[:100], action="重试",
                          suggestion="升级模型或策略后重试")

    def _choose_upgrade(self) -> UpgradeStrategy:
        """自动选择升级策略。"""
        if self._retry_count <= 1:
            return UpgradeStrategy.MODEL
        elif self._retry_count <= 2:
            return UpgradeStrategy.POLICY
        else:
            return UpgradeStrategy.ROLE

    def _apply_upgrade(self, strategy: UpgradeStrategy) -> str:
        """执行升级。"""
        if strategy == UpgradeStrategy.MODEL:
            self._context.setdefault("model", "pro")
            return "deepseek-v4-pro"
        elif strategy == UpgradeStrategy.POLICY:
            self._context["timeout"] = self._context.get("timeout", 30) * 2
            return f"timeout:{self._context['timeout']}s"
        elif strategy == UpgradeStrategy.ROLE:
            self._context["escalated"] = True
            return "escalated"
        return ""

    # ---- State Management ----

    def _transition_to(self, new_state: AgentState) -> None:
        old = self._state
        self._state = new_state
        self._timeline.append({
            "time": time.time(), "from": old.value, "to": new_state.value,
            "retry": self._retry_count,
        })

    # ---- Checkpoint (纯进度快照，不含 State/Memory) ----

    def _save_checkpoint(self, step: str) -> None:
        cp = Checkpoint(
            id=uuid.uuid4().hex[:8],
            step=step,
            context=dict(self._context),
            completed=[e["to"] for e in self._timeline[-5:] if e["to"] != "failed"],
            timestamp=time.time(),
        )
        self._checkpoints.append(cp)

    # ---- Queries ----

    def get_timeline(self) -> List[Dict]:
        return list(self._timeline)

    def get_lessons(self) -> List[Lesson]:
        return list(self._lessons)

    def get_debug_report(self) -> Dict:
        return {
            "agent": self._name,
            "state": self._state.value,
            "retries": self._retry_count,
            "max_retries": self._max_retries,
            "checkpoints": [c.step for c in self._checkpoints],
            "upgrades": self._upgrade_history,
            "lessons": [{"cause": l.cause, "action": l.action} for l in self._lessons],
        }
