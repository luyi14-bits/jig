"""Agent Runtime — 真正的 Agent 运行时实体。

核心设计:
- 状态机: idle → running → waiting → error → recovered → done
- 生命周期: on_init / on_run / on_pause / on_resume / on_error / on_stop
- Checkpoint 自动保存 + rollback
- Retry policy + recovery chain + escalation
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
    """Agent 运行时状态。"""
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"       # 等待其他 Agent 或人工介入
    PAUSED = "paused"         # 用户手动暂停
    ERROR = "error"
    RECOVERED = "recovered"   # 从错误中恢复
    DONE = "done"


@dataclass
class Checkpoint:
    """Agent 执行检查点。"""
    id: str = ""
    agent_name: str = ""
    state: AgentState = AgentState.IDLE
    context: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    retry_count: int = 0


@dataclass
class AgentResult:
    """Agent 执行结果。"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    checkpoints: int = 0
    retries: int = 0
    recovery_chain: List[str] = field(default_factory=list)


class AgentRuntime:
    """Agent 运行时 — 状态机 + 生命周期 + 检查点。

    用法:
        runtime = AgentRuntime("my-agent")
        runtime.on_init({"goal": "审查代码"})
        runtime.on_run(lambda ctx: do_something(ctx))
        print(runtime.state)  # → AgentState.DONE
    """

    def __init__(self, name: str, max_retries: int = 3):
        self._name = name
        self._id = uuid.uuid4().hex[:12]
        self._state = AgentState.IDLE
        self._context: Dict[str, Any] = {}
        self._memory: Dict[str, Any] = {}
        self._checkpoints: List[Checkpoint] = []
        self._max_retries = max_retries
        self._retry_count = 0
        self._recovery_chain: List[str] = []
        self._timeline: List[Dict] = []  # 完整事件日志

        # 生命周期钩子
        self._on_run: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
        self._on_rollback: Optional[Callable] = None

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
    def retry_count(self) -> int:
        return self._retry_count

    # ---- 生命周期钩子注册 ----

    def register_hooks(self, on_run=None, on_error=None, on_rollback=None) -> None:
        self._on_run = on_run
        self._on_error = on_error
        self._on_rollback = on_rollback

    # ---- 生命周期执行 ----

    def run(self, task: Callable, context: Optional[Dict] = None) -> AgentResult:
        """执行 Agent 任务，含自动 checkpoint + retry + rollback。"""
        if context:
            self._context.update(context)

        self._transition_to(AgentState.RUNNING)
        self._auto_checkpoint()

        while self._retry_count <= self._max_retries:
            try:
                self._timeline.append({"event": "run_start", "retry": self._retry_count, "time": time.time()})

                # 调用自定义执行逻辑
                if self._on_run:
                    result = self._on_run(self._context)
                else:
                    result = task(self._context) if task else None

                self._transition_to(AgentState.DONE)
                self._auto_checkpoint()
                self._timeline.append({"event": "run_success", "time": time.time()})

                return AgentResult(success=True, output=result, checkpoints=len(self._checkpoints), retries=self._retry_count)

            except Exception as e:
                self._retry_count += 1
                self._timeline.append({"event": "run_error", "error": str(e), "retry": self._retry_count, "time": time.time()})

                if self._retry_count <= self._max_retries:
                    # Rollback + retry
                    self._auto_rollback()
                    logger.warning("%s: 重试 %d/%d — %s", self._name, self._retry_count, self._max_retries, e)
                    self._transition_to(AgentState.RUNNING)
                    continue
                else:
                    # 重试耗尽 → error
                    self._transition_to(AgentState.ERROR)
                    logger.error("%s: 重试耗尽 — %s", self._name, e)

                    if self._on_error:
                        self._on_error(e)

                    return AgentResult(success=False, error=str(e), checkpoints=len(self._checkpoints), retries=self._retry_count)

    def pause(self) -> None:
        self._transition_to(AgentState.PAUSED)
        self._auto_checkpoint()

    def resume(self, checkpoint_id: Optional[str] = None) -> None:
        if checkpoint_id:
            self._rollback_to(checkpoint_id)
        self._transition_to(AgentState.RUNNING)

    # ---- Checkpoint / Rollback ----

    def _auto_checkpoint(self) -> None:
        cp = Checkpoint(
            id=uuid.uuid4().hex[:8],
            agent_name=self._name,
            state=self._state,
            context=dict(self._context),
            memory=dict(self._memory),
            timestamp=time.time(),
            retry_count=self._retry_count,
        )
        self._checkpoints.append(cp)
        logger.debug("%s: checkpoint %s (%s)", self._name, cp.id, self._state.value)

    def _auto_rollback(self) -> None:
        """回滚到最后一次成功 checkpoint。"""
        # 找一个非 Error 的 checkpoint
        for cp in reversed(self._checkpoints[:-1]):
            if cp.state != AgentState.ERROR:
                self._restore_checkpoint(cp)
                if self._on_rollback:
                    self._on_rollback(cp)
                logger.info("%s: rollback 到 checkpoint %s", self._name, cp.id)
                return

        logger.warning("%s: 没有可回滚的 checkpoint", self._name)

    def _rollback_to(self, cp_id: str) -> bool:
        for cp in self._checkpoints:
            if cp.id == cp_id:
                self._restore_checkpoint(cp)
                return True
        return False

    def _restore_checkpoint(self, cp: Checkpoint) -> None:
        self._context = dict(cp.context)
        self._memory = dict(cp.memory)
        self._retry_count = cp.retry_count
        self._transition_to(AgentState.RECOVERED)

    # ---- 状态管理 ----

    def _transition_to(self, new_state: AgentState) -> None:
        old = self._state
        self._state = new_state
        self._timeline.append({"event": "state_change", "from": old.value, "to": new_state.value, "time": time.time()})

    # ---- 查询 ----

    def get_timeline(self) -> List[Dict]:
        return list(self._timeline)

    def get_checkpoints(self) -> List[Checkpoint]:
        return list(self._checkpoints)

    def get_debug_report(self) -> Dict:
        return {
            "agent": self._name,
            "state": self._state.value,
            "retries": self._retry_count,
            "max_retries": self._max_retries,
            "checkpoints": len(self._checkpoints),
            "checkpoint_ids": [c.id for c in self._checkpoints],
            "timeline": self._timeline[-5:],
        }
