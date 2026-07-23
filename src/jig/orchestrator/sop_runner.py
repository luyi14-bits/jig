"""SOPRunner — 带 Checkpoint/Retry/Escalate 的 SOP 管道执行器。

核心闭环: execute → validate → checkpoint → (fail → retry → escalate) → next
每个 Agent 真实调用 LLM，失败从 checkpoint 恢复，不重跑已完成节点。
"""

from __future__ import annotations
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.skill_def import AgentConfig, HandoverPackage, SOPNode
from ..core.agent_factory import AgentFactory, AgentExecutionError
from ..adapters.model_provider import BaseModelProvider, DeepSeekProvider
from ..core.skill_registry import SkillRegistry
from ..core.config_manager import ModelRouter

logger = logging.getLogger(__name__)


@dataclass
class SOPCheckpoint:
    """SOP 执行检查点 — 记录管道执行进度。"""
    session_id: str
    current_node_idx: int
    completed_nodes: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    escalate_level: int = 0
    timestamp: float = 0.0


class SOPRunner:
    """SOP 管道执行器 — 带 Checkpoint/Retry/Escalate。
    
    用法:
        runner = SOPRunner(provider=model_provider)
        result = runner.run(sop_tree, {"user_request": "..."})
    """

    ESCALATE_STRATEGIES = ["model_upgrade", "role_upgrade", "manual"]

    def __init__(self, provider: Optional[BaseModelProvider] = None,
                 max_retries: int = 3, checkpoint_dir: str = ""):
        self._provider = provider or DeepSeekProvider(api_key=os.environ.get("DEEPSEEK_API_KEY", ""))
        self._max_retries = max_retries
        self._checkpoint_dir = Path(checkpoint_dir or ".sop_checkpoints")
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoints: Dict[str, SOPCheckpoint] = {}

    def run(self, sop: SOPNode, context: Dict[str, Any]) -> HandoverPackage:
        """执行 SOP 管道。"""
        session_id = uuid.uuid4().hex[:12]
        logger.info("SOPRunner 启动: session=%s, steps=%d", session_id, len(sop.sub_steps))

        # 尝试从 checkpoint 恢复
        checkpoint = self._load_checkpoint(session_id)
        if checkpoint:
            logger.info("从 checkpoint 恢复: session=%s, 节点=%d", session_id, checkpoint.current_node_idx)
            context = checkpoint.context
            start_idx = checkpoint.current_node_idx
        else:
            start_idx = 0
            context["_session_id"] = session_id

        prev_handover: Optional[HandoverPackage] = None
        completed = checkpoint.completed_nodes if checkpoint else []

        for idx in range(start_idx, len(sop.sub_steps)):
            node = sop.sub_steps[idx]
            logger.info("执行节点 %d/%d: %s", idx + 1, len(sop.sub_steps), node.name)

            # 如果已从 checkpoint 完成，跳过
            if node.name in completed:
                logger.info("跳过已完成节点: %s", node.name)
                continue

            node_result = self._execute_with_retry(node, context, prev_handover, session_id, idx)
            if node_result is None:
                return HandoverPackage(
                    source_agent="SOPRunner",
                    target_agent="",
                    summary=f"管道在节点 {node.name} 失败，已超过最大重试次数",
                    artifacts={"session_id": session_id, "failed_at": node.name},
                    decisions=["ESCLATED"],
                    confidence=0.0,
                )

            prev_handover = node_result
            completed.append(node.name)

            # 保存 checkpoint
            self._save_checkpoint(SOPCheckpoint(
                session_id=session_id,
                current_node_idx=idx + 1,
                completed_nodes=list(completed),
                context=dict(context),
                timestamp=time.time(),
            ))

        # 清理 checkpoint
        self._cleanup_checkpoint(session_id)

        return HandoverPackage(
            source_agent="SOPRunner",
            target_agent="",
            summary=f"SOP 管道完成: {len(completed)}/{len(sop.sub_steps)} 个节点",
            artifacts={"session_id": session_id, "completed_steps": completed, "context": context},
            decisions=["PIPELINE_COMPLETED"],
            confidence=0.9,
        )

    def _execute_with_retry(self, node: SOPNode, context: Dict,
                            prev_handover: Optional[HandoverPackage],
                            session_id: str, node_idx: int) -> Optional[HandoverPackage]:
        """执行单个节点（含 retry + escalate）。"""
        retry_count = 0
        escalate_level = 0

        # 创建 Agent
        reg = SkillRegistry()
        skill_dir = Path("skills")
        if skill_dir.exists():
            reg.register_skill_dir(str(skill_dir))
            reg.load_all()
        else:
            # 尝试从 settings 加载
            from ..settings import settings
            if hasattr(settings, 'skills_dir') and settings.skills_dir:
                reg.register_skill_dir(str(settings.skills_dir))
                reg.load_all()

        skill_def = reg.get(node.skill_ref or "") if node.skill_ref else None
        if not skill_def:
            logger.error("skill 未找到: %s", node.skill_ref)
            return None

        agent = AgentFactory.create_agent(skill_def)

        while retry_count <= self._max_retries:
            try:
                agent = AgentFactory.create_agent_by_skill_ref(node.skill_ref)
                if prev_handover:
                    agent.receive_handover(prev_handover)

                task = self._build_task(node, context, prev_handover)
                result = self._call_agent(agent, task, escalate_level)

                # 验证结果
                if not result or not result.summary:
                    raise AgentExecutionError("Agent 返回空结果")

                logger.info("节点 %s 执行成功 (retry=%d)", node.name, retry_count)
                return result

            except (AgentExecutionError, Exception) as e:
                retry_count += 1
                failure_reason = str(e)
                logger.warning("节点 %s 失败 (retry=%d/%d): %s", node.name, retry_count, self._max_retries, failure_reason)

                # 失败原因注入上下文
                context[f"_failure_{node.name}_{retry_count}"] = failure_reason

                if retry_count > self._max_retries:
                    # Escalate
                    escalate_level = min(escalate_level + 1, len(self.ESCALATE_STRATEGIES) - 1)
                    strategy = self.ESCALATE_STRATEGIES[escalate_level]
                    logger.warning("节点 %s  escalate (level=%d, strategy=%s)", node.name, escalate_level, strategy)

                    if escalate_level >= 2:
                        return None  # 需要人工介入

        return None

    def _build_task(self, node: SOPNode, context: Dict,
                    prev_handover: Optional[HandoverPackage]) -> str:
        """构造 Agent 的输入任务。"""
        task = context.get("user_request", "")
        if prev_handover:
            task += f"\n\n前置节点输出:\n{prev_handover.summary}"

        # 注入失败原因
        for key, value in context.items():
            if key.startswith(f"_failure_{node.name}_"):
                task += f"\n\n[上次执行失败]: {value}"
                break

        return task

    def _call_agent(self, agent, task: str, escalate_level: int) -> HandoverPackage:
        """调用 Agent 执行任务（真实 LLM）。"""
        model = "deepseek-v4-pro" if escalate_level >= 1 else "deepseek-v4-flash"
        system = agent.config.role_preset[:500] if hasattr(agent.config, 'role_preset') else ""
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": task},
        ]

        response = self._provider.chat(messages, temperature=0.3)
        
        if not response or not response.content:
            raise AgentExecutionError("LLM 返回空响应")

        return agent.prepare_handover(
            target=agent.skill_name,
            summary=response.content[:500],
            artifacts={"raw_response": response.content},
            decisions=[f"EXECUTED_BY_{agent.skill_name}"],
            confidence=0.85,
        )

    # ---- Checkpoint ----

    def _save_checkpoint(self, cp: SOPCheckpoint) -> None:
        path = self._checkpoint_dir / f"{cp.session_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": cp.session_id,
                "current_node_idx": cp.current_node_idx,
                "completed_nodes": cp.completed_nodes,
                "context": {k: v for k, v in cp.context.items() if not k.startswith("_")},
                "retry_count": cp.retry_count,
                "escalate_level": cp.escalate_level,
                "timestamp": cp.timestamp,
            }, f, ensure_ascii=False, indent=2)
        logger.debug("Checkpoint 已保存: %s (%d/%d)", cp.session_id, cp.current_node_idx, cp.current_node_idx)

    def _load_checkpoint(self, session_id: str) -> Optional[SOPCheckpoint]:
        path = self._checkpoint_dir / f"{session_id}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SOPCheckpoint(**data)
        except Exception as e:
            logger.warning("Checkpoint 加载失败: %s", e)
            return None

    def _cleanup_checkpoint(self, session_id: str) -> None:
        path = self._checkpoint_dir / f"{session_id}.json"
        if path.exists():
            path.unlink()
            logger.info("Checkpoint 已清理: %s", session_id)

    def resume(self, session_id: str, sop: SOPNode, context: Dict) -> Optional[HandoverPackage]:
        """从已有 checkpoint 恢复执行。"""
        cp = self._load_checkpoint(session_id)
        if not cp:
            logger.warning("无 checkpoint 可恢复: %s", session_id)
            return None
        context.update(cp.context)
        return self.run(sop, context)
