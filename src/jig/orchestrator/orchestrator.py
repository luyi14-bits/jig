"""编排调度器 — SOP 树执行引擎。

Task 8: 支持顺序/层级/并行三种调度模式。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import concurrent.futures

from ..core.skill_def import HandoverPackage, SOPNode


logger = logging.getLogger(__name__)


class OrchestratorBase(ABC):
    """编排调度器基类。"""

    def __init__(self, max_depth: int = 5) -> None:
        self._max_depth = max_depth
        self._execution_log: List[Dict[str, Any]] = []

    @abstractmethod
    def execute(self, sop_node: SOPNode, context: Dict[str, Any]) -> HandoverPackage:
        """执行 SOP 树节点。"""

    def _log_step(self, node_name: str, status: str, detail: str = "") -> None:
        """记录执行步骤。"""
        entry = {"node": node_name, "status": status, "detail": detail}
        self._execution_log.append(entry)
        logger.info("[SOP] %s: %s — %s", node_name, status, detail)

    @property
    def execution_log(self) -> List[Dict[str, Any]]:
        return list(self._execution_log)


class SequentialOrchestrator(OrchestratorBase):
    """顺序调度器 — 串行执行子 Agent，结果依次传递。

    SOP-ORCH-001.1: 每个步骤按顺序执行，前一步的输出作为后一步的输入。
    """

    def __init__(self, agent_resolver, max_depth: int = 5) -> None:
        """初始化顺序调度器。

        Args:
            agent_resolver: Agent 解析函数，接收 skill_name → Agent 实例。
        """
        super().__init__(max_depth)
        self._agent_resolver = agent_resolver

    def execute(self, sop_node: SOPNode, context: Dict[str, Any]) -> HandoverPackage:
        """执行顺序 SOP 节点。"""
        self._log_step(sop_node.name, "开始", f"mode={sop_node.mode}, sub_steps={len(sop_node.sub_steps)}")

        current_context = dict(context)
        last_handover: Optional[HandoverPackage] = None

        for i, step in enumerate(sop_node.sub_steps):
            self._log_step(step.name, "执行中", f"step={i+1}/{len(sop_node.sub_steps)}")

            if step.sub_steps:
                # 递归展开子 SOP
                sub_orchestrator = SequentialOrchestrator(self._agent_resolver, self._max_depth)
                handover = sub_orchestrator.execute(step, current_context)
            elif step.skill_ref and self._agent_resolver:
                # 叶子节点：解析 Agent 并执行
                agent = self._agent_resolver(step.skill_ref)
                if agent:
                    if last_handover:
                        agent.receive_handover(last_handover)
                    # Agent 执行其任务
                    handover = agent.prepare_handover(
                        target=step.name,
                        summary=f"第 {i+1} 步执行完成: {step.description}",
                        artifacts=current_context.get("artifacts", {}),
                    )
                else:
                    self._log_step(step.name, "跳过", f"Agent {step.skill_ref} 未找到")
                    continue
            else:
                self._log_step(step.name, "跳过", "无子步骤且无 skill_ref")
                continue

            # 传递结果
            current_context["last_handover"] = handover
            if handover:
                current_context["artifacts"] = handover.artifacts
            last_handover = handover

        self._log_step(sop_node.name, "完成", f"共 {len(sop_node.sub_steps)} 个子步骤")

        return last_handover or HandoverPackage(
            source_agent=sop_node.name,
            target_agent="",
            summary="顺序执行完成",
        )


class HierarchicalOrchestrator(OrchestratorBase):
    """层级调度器 — 递归展开树形 SOP，每层维护独立上下文。

    SOP-ORCH-001.3: 递归展开树形 SOP，层级上下文隔离。
    """

    def __init__(self, agent_resolver, max_depth: int = 5) -> None:
        super().__init__(max_depth)
        self._agent_resolver = agent_resolver
        self._current_depth = 0

    def execute(self, sop_node: SOPNode, context: Dict[str, Any]) -> HandoverPackage:
        """递归执行层级 SOP。

        每层创建独立的上下文作用域，避免父子层污染。
        """
        self._current_depth += 1
        if self._current_depth > self._max_depth:
            self._log_step(sop_node.name, "终止", f"超过最大深度 {self._max_depth}")
            self._current_depth -= 1
            return HandoverPackage(
                source_agent=sop_node.name,
                target_agent="",
                summary=f"最大递归深度 {self._max_depth} 已达",
                confidence=0.5,
            )

        self._log_step(
            sop_node.name, "开始",
            f"depth={self._current_depth}, mode={sop_node.mode}",
        )

        # 当前层级独立上下文
        local_context = dict(context)
        layer_context: Dict[str, Any] = {}

        for step in sop_node.sub_steps:
            self._log_step(step.name, "执行中", f"depth={self._current_depth}")

            if step.sub_steps:
                # 递归执行子 SOP
                child = HierarchicalOrchestrator(self._agent_resolver, self._max_depth)
                child._current_depth = self._current_depth
                handover = child.execute(step, local_context)
            elif step.skill_ref:
                agent = self._agent_resolver(step.skill_ref)
                if agent:
                    handover = agent.prepare_handover(
                        target=step.name,
                        summary=f"层级执行: {step.description}",
                    )
                else:
                    continue
            else:
                continue

            layer_context[step.name] = handover

        self._current_depth -= 1

        self._log_step(sop_node.name, "完成", f"depth={self._current_depth}, 子节点={len(sop_node.sub_steps)}")

        return HandoverPackage(
            source_agent=sop_node.name,
            target_agent="",
            summary=f"层级SOP执行完成: {sop_node.name}",
            artifacts=layer_context,
        )


class ParallelOrchestrator(OrchestratorBase):
    """并行调度器 — 同时执行多个子 Agent，聚合结果。

    PAR-ORCH-001: 支持同时执行多个子 Agent，可设置 max_concurrency。
    """

    def __init__(self, agent_resolver, max_concurrency: int = 3, max_depth: int = 5) -> None:
        super().__init__(max_depth)
        self._agent_resolver = agent_resolver
        self._max_concurrency = max_concurrency

    def execute(self, sop_node: SOPNode, context: Dict[str, Any]) -> HandoverPackage:
        self._log_step(
            sop_node.name, "开始并行",
            f"sub_steps={len(sop_node.sub_steps)}, max_concurrency={self._max_concurrency}",
        )

        results: Dict[str, Any] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_concurrency) as executor:
            future_map = {}
            for step in sop_node.sub_steps:
                future = executor.submit(self._execute_single, step, context)
                future_map[future] = step.name

            for future in concurrent.futures.as_completed(future_map):
                name = future_map[future]
                try:
                    result = future.result()
                    results[name] = result
                    self._log_step(name, "完成", "并行执行成功")
                except Exception as e:
                    results[name] = {"error": str(e)}
                    self._log_step(name, "失败", str(e))

        self._log_step(sop_node.name, "完成", f"并行执行完毕, 成功={sum(1 for r in results.values() if r is not None and "error" not in r)}/{len(results)}")

        return HandoverPackage(
            source_agent=sop_node.name,
            target_agent="",
            summary=f"并行SOP执行完成: {sop_node.name}",
            artifacts=results,
        )

    def _execute_single(self, step: SOPNode, context: Dict[str, Any]) -> Any:
        if step.skill_ref and self._agent_resolver:
            agent = self._agent_resolver(step.skill_ref)
            if agent:
                return agent.prepare_handover(target=step.name, summary=f"并行执行: {step.description}")
        return None


class CheckpointManager:
    """检查点管理器 — 持久化 Agent 执行状态。

    CHECKPOINT-001: 支持保存/恢复，JSON 格式持久化。
    """

    def __init__(self, checkpoint_dir: str = "") -> None:
        import os
        self._checkpoint_dir = checkpoint_dir or os.path.join(os.path.expanduser("~"), ".tree-sop", "checkpoints")
        os.makedirs(self._checkpoint_dir, exist_ok=True)

    def save(self, session_id: str, state: Dict[str, Any]) -> str:
        import json, os
        path = os.path.join(self._checkpoint_dir, f"{session_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        logger.info("检查点已保存: session=%s, path=%s", session_id, path)
        return path

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        import json, os
        path = os.path.join(self._checkpoint_dir, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def resume(self, session_id: str) -> Optional[Dict[str, Any]]:
        state = self.load(session_id)
        if state:
            logger.info("从检查点恢复: session=%s", session_id)
        return state

    def list_checkpoints(self) -> List[str]:
        import os
        return [f.replace(".json", "") for f in os.listdir(self._checkpoint_dir) if f.endswith(".json")]


# 预定义开发工作流模板
def create_dev_workflow() -> SOPNode:
    """创建完整开发工作流 SOP 树。

    WORKFLOW-001: brainstorm -> plan -> code -> test -> review
    """
    return SOPNode(
        name="dev-workflow",
        description="完整开发工作流",
        mode="sequential",
        sub_steps=[
            SOPNode(name="brainstorm", description="需求调研与头脑风暴", skill_ref="pm-mentor"),
            SOPNode(name="plan", description="编写 Spec 与任务拆分", skill_ref="spec-pipeline"),
            SOPNode(name="code", description="编码实现", skill_ref="coding-ethics"),
            SOPNode(name="test", description="测试与自测", skill_ref="test-driven-development"),
            SOPNode(name="review", description="验收与审查", skill_ref="acceptance-testing"),
        ],
    )
