"""Dispatcher — 群聊入口/需求路由系统组件。

接收用户自然语言，启动真实 SOP 管道。
每个 Agent 真实调用 LLM，失败从 Checkpoint 恢复，
支持 retry + escalate。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ..adapters.model_provider import BaseModelProvider, DeepSeekProvider
from ..core.skill_def import SOPNode
from ..core.agent_factory import AgentFactory

logger = logging.getLogger(__name__)


class Dispatcher:
    """群聊入口 Dispatcher。

    接收用户输入，启动完整的 SOP 管道（PM → Spec → Coding → Acceptance），
    使用 SOPRunner 确保 Checkpoint 保存、失败恢复、重试和 escalate。
    """

    def __init__(self, registry, agent_factory, model_router=None, provider=None):
        self._registry = registry
        self._agent_factory = agent_factory
        self._router = model_router
        self._provider = provider

    def handle(self, user_message: str) -> str:
        """处理用户输入：启动完整 SOP 管道，返回执行结果。"""
        logger.info("Dispatcher 收到: %s", user_message[:80])

        provider = self._get_provider()
        runner = self._create_runner(provider)

        # 构建最小 SOP 树：PM → Spec → Coding → Acceptance
        sop = SOPNode(
            name="minimal-closed-loop",
            description="最小闭环：PM 分析需求 → Spec 拆任务 → Coding 实现 → Acceptance 验收",
            mode="sequential",
            sub_steps=[
                SOPNode(name="pm-analysis", description="需求分析", skill_ref="Luyi14-pm-mentor"),
                SOPNode(name="spec-breakdown", description="Spec 拆解", skill_ref="Luyi14-spec-pipeline"),
                SOPNode(name="coding", description="编码实现", skill_ref="Luyi14-coding-ethics"),
                SOPNode(name="acceptance", description="验收确认", skill_ref="Luyi14-acceptance-testing"),
            ],
        )

        context = {
            "user_request": user_message,
            "skills_dir": str(Path("skills").resolve()),
        }

        result = runner.run(sop, context)

        # 构造返回信息
        if result.confidence >= 0.5:
            summary = f"✅ SOP 管道执行完成\n\n{result.summary}\n\n共完成 {len(result.artifacts.get('completed_steps', []))} 个阶段"
        else:
            failed_at = result.artifacts.get("failed_at", "?")
            summary = f"❌ 管道在阶段 {failed_at} 失败，已 escalate"

        return summary

    def handle_stream(self, user_message: str):
        """流式处理 — 逐步产出结果（预留接口）。"""
        raise NotImplementedError("流式模式待实现")

    def _get_provider(self) -> BaseModelProvider:
        """获取 LLM Provider。无 Key 时返回 mock provider。"""
        if self._router:
            try:
                return self._router.get("deepseek")
            except KeyError:
                pass
        from ..adapters.model_provider import DeepSeekProvider
        from ..settings import settings
        api_key = settings.deepseek_api_key
        return DeepSeekProvider(api_key=api_key or "")

    def _create_runner(self, provider: BaseModelProvider):
        """创建 SOPRunner。"""
        from .sop_runner import SOPRunner
        return SOPRunner(
            provider=provider,
            max_retries=3,
            checkpoint_dir=".sop_checkpoints",
        )
