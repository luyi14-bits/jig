"""Dispatcher — 群聊入口/需求路由系统组件。

接收用户自然语言，理解意图后路由到对应 Agent，
调用真实 LLM 产出结果。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Dispatcher:
    """群聊入口 Dispatcher。

    接收用户输入，路由到对应 Agent，调用真实 LLM 产出结果。
    这是最小闭环的关键组件——不再 mock。
    """

    def __init__(self, registry, agent_factory, model_router=None):
        self._registry = registry
        self._agent_factory = agent_factory
        self._router = model_router

    def handle(self, user_message: str) -> str:
        """处理用户输入：路由到 Agent → 调用 LLM → 返回结果。"""
        logger.info("Dispatcher 收到: %s", user_message[:80])

        # 查找 PM Agent
        pm_skill = self._registry.get("Luyi14-pm-mentor")
        if not pm_skill:
            return "错误: 未找到 PM Agent（Luyi14-pm-mentor）"

        agent = self._agent_factory.create_agent(pm_skill)
        logger.info("Dispatcher 路由到: %s", agent.skill_name)

        agent.set_context("user_request", user_message)
        agent.set_context("request_summary", user_message[:120])

        # 调用真实 LLM
        response = self._call_llm(agent, user_message)

        agent.log_execution(f"LLM 已处理: {user_message[:60]}...")

        handover = agent.prepare_handover(
            target="spec-pipeline",
            summary=f"需求分析完成: {response[:200] if response else user_message[:80]}",
            decisions=["路由到 PM Agent -> LLM 分析 -> Spec-Pipeline"],
            confidence=0.85,
        )

        agent.write_log(
            task_summary=f"处理用户需求: {user_message[:60]}",
            output=f"LLM 响应 -> {handover.target_agent}",
            target=handover.target_agent,
        )

        return f"PM Agent 已分析需求\n\n{response if response else '分析完成，等待进入下一阶段'}"

    def _call_llm(self, agent, user_message: str) -> str:
        """调用真实 LLM 处理用户需求。"""
        try:
            if self._router:
                provider = self._router.get("deepseek")
            else:
                from ..adapters.model_provider import DeepSeekProvider
                from ..settings import settings
                api_key = settings.deepseek_api_key
                if not api_key:
                    return self._mock_response(user_message)
                provider = DeepSeekProvider(api_key=api_key)

            system_prompt = f"""你是 {agent.skill_name}（{agent.role_description}）。

你的职责：分析用户需求，产出需求分析报告。

需求分析报告格式：
1. 一句话总结
2. 核心功能点（最多5点）
3. 技术方案建议
4. Open Questions（最多3个）"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]

            response = provider.chat(messages, temperature=0.3)
            return response.content

        except Exception as e:
            logger.error("LLM 调用失败: %s", e)
            return self._mock_response(user_message)

    def _mock_response(self, user_message: str) -> str:
        """当 LLM 不可用时的降级响应。"""
        return (
            f"【需求分析报告 - Mock 模式】\n\n"
            f"1. 一句话总结\n"
            f"   用户需求: {user_message[:100]}\n\n"
            f"2. 核心功能点\n"
            f"   - 需求分析\n"
            f"   - 方案设计\n"
            f"   - 实施规划\n\n"
            f"3. 技术方案建议\n"
            f"   建议使用 Jig 框架的 SOP 管道进行实施\n\n"
            f"4. Open Questions\n"
            f"   - 具体技术栈未指定\n"
            f"   - 时间要求未明确\n\n"
            f"[Mock 模式 — 配置 JIG_API_KEY 可启用真实 LLM 分析]"
        )
