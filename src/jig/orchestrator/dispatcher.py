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
from .intent_router import classify_query, hyde_rewrite
from .graph_engine import GraphOrchestrator, GraphNode, GraphEdge
from ..adapters.external_agent import MetaHarness
from .orchestrator import create_dev_workflow
from ..core.agent_factory import AgentFactory

logger = logging.getLogger(__name__)


class Dispatcher:
    """群聊入口 Dispatcher。

    接收用户输入，启动完整的 SOP 管道（PM → Spec → Coding → Acceptance），
    使用 SOPRunner 确保 Checkpoint 保存、失败恢复、重试和 escalate。
    """

    def __init__(self, registry=None, agent_factory=None, model_router=None, provider=None, skill_dir: str = ""):
        """群聊入口 Dispatcher。

        支持两种构造方式：
        1. 显式传入 registry + agent_factory（框架内使用）
        2. 仅传 skill_dir（CLI 便捷模式，自动构建）
        """
        if registry is None or agent_factory is None:
            from ..core.skill_registry import SkillRegistry
            registry = SkillRegistry()
            if skill_dir:
                registry.register_skill_dir(skill_dir)
                registry.load_all()
            agent_factory = None  # AgentFactory 为纯 classmethod 工厂
        self._registry = registry
        self._agent_factory = agent_factory
        self._router = model_router
        self._provider = provider
        self._meta_harness = MetaHarness()
        # 接线 ConversationCompressor — 长上下文压缩
        from ..adapters.conversation_compressor import ConversationCompressor
        self._compressor = ConversationCompressor(mode="hybrid", max_history_tokens=8000)
        # 接线 EmbeddingIndex — 意图语义检索
        from ..adapters.embedding_index import EmbeddingIndex
        self._embedding = EmbeddingIndex()
        # 接线 RepoMapBuilder — 代码库上下文增强
        from ..adapters.repo_map import RepoMapBuilder
        self._repo_map = RepoMapBuilder()

    def handle(self, user_message: str) -> str:
        """处理用户输入：启动完整 SOP 管道，返回执行结果。"""
        logger.info("Dispatcher 收到: %s", user_message[:80])

        # 输入校验
        if not user_message:
            return "错误: 输入为空"
        if len(user_message) > 102400:
            return "错误: 输入超过最大长度(100KB)"

        # 长上下文压缩 — 超过阈值时压缩输入
        if len(user_message) > 4000:
            compressed = self._compressor.compress(
                [{"role": "user", "content": user_message}]
            )
            if compressed:
                new_len = len(compressed[0].get("content", ""))
                if new_len < len(user_message):
                    logger.info("输入压缩: %d → %d 字符", len(user_message), new_len)
                    user_message = compressed[0]["content"]

        # 意图分类 — 短查询/长难句使用不同策略
        query_type = classify_query(user_message)
        if query_type in ("complex", "multi_turn"):
            user_message = hyde_rewrite(user_message)
            logger.info("HyDE 改写: %s", user_message[:60])

        # MetaHarness — 外部 Agent 请求路由
        if query_type == "external":
            return self._meta_harness.route("claude", user_message)

        # GraphOrchestrator — 复杂查询使用图模式
        graph_mode = query_type == "complex"
        if graph_mode:
            g = GraphOrchestrator()
            for nick, agent in [("pm","Luyi14-pm-mentor"),("spec","Luyi14-spec-pipeline"),
                                 ("coding","Luyi14-coding-ethics"),("accept","Luyi14-acceptance-testing")]:
                g.add_node(GraphNode(name=nick, agent=agent))
            for a, b in [("pm","spec"),("spec","coding"),("coding","accept")]:
                g.add_edge(GraphEdge(a, b))
            provider = self._get_provider()
            ctx = {"user_request": user_message, "skills_dir": str(Path("skills").resolve())}
            result = g.run("pm", ctx)
            return f"✅ Graph管道完成: {result.get('accept','')[:200] if isinstance(result, dict) else str(result)[:200]}"

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

        # 代码相关查询 — 附加 Repo Map 上下文
        code_keywords = ("代码", "实现", "重构", "函数", "bug", "修复", "优化", "refactor", "implement")
        if any(k in user_message.lower() for k in code_keywords):
            repo_map = self._repo_map.build(Path.cwd(), token_budget=1024)
            if repo_map and not repo_map.startswith("[Repo Map] 目录不存在"):
                context["repo_map"] = repo_map[:1500]
                logger.info("已附加 Repo Map 上下文 (%d 字符)", len(repo_map[:1500]))

        result = runner.run(sop, context)

        # 构造返回信息
        if result.confidence >= 0.5:
            summary = f"✅ SOP 管道执行完成\n\n{result.summary}\n\n共完成 {len(result.artifacts.get('completed_steps', []))} 个阶段"
        else:
            failed_at = result.artifacts.get("failed_at", "?")
            summary = f"❌ 管道在阶段 {failed_at} 失败，已 escalate"

        return summary

    def handle_stream(self, user_message: str):
        """流式处理 — 逐步产出 SSE 事件。"""
        provider = self._get_provider()
        runner = self._create_runner(provider)
        sop = SOPNode(name="stream", mode="sequential", sub_steps=[
            SOPNode(name="pm", skill_ref="Luyi14-pm-mentor"),
            SOPNode(name="spec", skill_ref="Luyi14-spec-pipeline"),
            SOPNode(name="coding", skill_ref="Luyi14-coding-ethics"),
            SOPNode(name="accept", skill_ref="Luyi14-acceptance-testing"),
        ])
        ctx = {"user_request": user_message, "skills_dir": str(Path("skills").resolve())}
        yield from runner.run_stream(sop, ctx)

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
