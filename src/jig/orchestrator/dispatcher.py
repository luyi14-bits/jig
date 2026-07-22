"""Dispatcher — 群聊入口/需求路由系统组件。

接收用户自然语言，理解意图后路由到 PM Agent 启动 SOP 管道。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Dispatcher:
    """群聊入口 Dispatcher。

    职责：
    1. 接收用户自然语言输入
    2. 理解意图 → 路由到正确的 Agent
    3. 默认路由：PM Agent（启动标准 SOP 管道）
    """

    def __init__(self, skill_dir: str = "skills") -> None:
        from ..core.skill_registry import SkillRegistry
        from ..core.agent_factory import AgentFactory

        self._registry = SkillRegistry()
        self._registry.register_skill_dir(skill_dir)
        self._registry.load_all()
        self._agent_factory = AgentFactory()
        logger.info("Dispatcher 已初始化, 加载 %d 个 skill", self._registry.count())

    def handle(self, user_message: str) -> str:
        """处理用户消息。

        当前实现：直接路由到 PM Agent 启动 SOP 管道。
        后续升级：用 DeepSeek Pro 做意图识别后智能路由。

        Args:
            user_message: 用户自然语言输入。

        Returns:
            处理结果的摘要。
        """
        logger.info("Dispatcher 收到: %s", user_message[:80])

        # 查找 PM Agent
        pm_skill = self._registry.get("Luyi14-pm-mentor")
        if not pm_skill:
            return "错误: 未找到 PM Agent（Luyi14-pm-mentor）"

        agent = self._agent_factory.create_agent(pm_skill)
        logger.info("Dispatcher 路由到: %s", agent.skill_name)

        agent.set_context("user_request", user_message)
        agent.set_context("request_summary", user_message[:120])

        # 模拟 Agent 执行（后续由 LLM 驱动）
        agent.log_execution(f"收到用户需求: {user_message[:60]}...")

        handover = agent.prepare_handover(
            target="spec-pipeline",
            summary=f"需求分析完成: {user_message[:80]}",
            decisions=["路由到 PM Agent -> Spec-Pipeline"],
            confidence=0.9,
        )

        agent.write_log(
            task_summary=f"处理用户需求: {user_message[:60]}",
            output=f"Handover -> {handover.target_agent}",
            target=handover.target_agent,
        )

        return f"已路由到 {agent.skill_name}，准备启动 SOP 管道"

    @property
    def registry(self):
        return self._registry
