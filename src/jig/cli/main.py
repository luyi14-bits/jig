"""Tree-SOP Agent CLI 入口。"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ..core.skill_registry import SkillRegistry
from ..core.agent_factory import AgentFactory
from ..adapters.model_router import ModelRouter
from ..adapters.cache_engine import CacheEngine
from ..adapters.context import ContextPartitioner
from ..adapters.deepseek_adapter import DeepSeekAdapter

logger = logging.getLogger(__name__)


def main() -> None:
    """CLI 主入口。"""
    parser = argparse.ArgumentParser(
        description="Tree-SOP Agent — Skill → Agent 自动映射引擎",
    )
    parser.add_argument(
        "--skill-dir",
        "-s",
        type=str,
        default=".",
        help="SKILL.md 所在目录路径",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="列出所有已加载的 skill",
    )
    parser.add_argument(
        "--inspect",
        "-i",
        type=str,
        default=None,
        metavar="SKILL_NAME",
        help="查看指定 skill 的 Agent 配置",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="启用详细日志",
    )
    parser.add_argument(
        "--attach",
        "-a",
        type=str,
        default=None,
        metavar="SKILL_NAMES",
        help="向 Agent 挂载额外 Skill（逗号分隔，例: skill1,skill2）",
    )
    parser.add_argument(
        "--chat",
        "-c",
        action="store_true",
        help="群聊模式（Dispatcher 入口）",
    )

    args = parser.parse_args()

    # 日志级别
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # 加载 skill
    registry = SkillRegistry()
    skill_dir = Path(args.skill_dir).resolve()
    if skill_dir.is_dir():
        registry.register_skill_dir(str(skill_dir))
        count = registry.load_all()
        print(f"已加载 {count} 个 skill（来源: {skill_dir}）")
    else:
        print(f"目录不存在: {skill_dir}")
        sys.exit(1)

    # --list: 列出所有 skill
    if args.list:
        print("\n=== 已加载 Skill 列表 ===")
        for skill in registry.list_all():
            model_emoji = "🚀" if skill.model == "pro" else "⚡"
            print(f"  {model_emoji} {skill.name}: {skill.description[:60]}")
        print(f"\n总计: {registry.count()} 个 skill")
        return

    # --inspect: 查看指定 skill
    if args.inspect:
        skill_def = registry.get(args.inspect)
        if not skill_def:
            print(f"未找到 skill: {args.inspect}")
            sys.exit(1)

        # 解析挂载的 skill
        attached = []
        if args.attach:
            for name in args.attach.split(","):
                name = name.strip()
                sk = registry.get(name)
                if sk:
                    attached.append(sk)
                    print(f"  已挂载 skill: {name}")
                else:
                    print(f"  警告: skill '{name}' 未找到, 跳过")

        agent = AgentFactory.create_agent(skill_def, attached_skills=attached)
        config = agent.config
        display_name = skill_def.agent_name or skill_def.name

        print(f"\n=== Agent 配置: {display_name} ({skill_def.name}) ===")
        print(f"  模型等级: {config.model_grade}")
        print(f"  模型名称: {config.session_config.model}")
        print(f"  Temperature: {config.session_config.temperature}")
        body_len = len(skill_def.body) if skill_def.body else 0
        print(f"  角色 body 长度: {body_len} 字符")
        if attached:
            for sk in attached:
                print(f"  挂载 skill: {sk.name} ({len(sk.body)} 字符)")
        total_prompt_len = len(config.role_preset)
        print(f"  组装后 prompt 总长度: {total_prompt_len} 字符")
        print(f"  工具数: {len(config.tools)}")
        if args.verbose:
            print(f"\n--- 完整 Prompt ---\n{config.role_preset[:1000]}...")
        return

    # --chat: 群聊模式
    if args.chat:
        from ..orchestrator.dispatcher import Dispatcher
        dispatcher = Dispatcher(skill_dir=str(skill_dir))
        print("\n=== Tree-SOP Agent 群聊模式 ===")
        print("输入 'exit' 或 'quit' 退出")
        print(f"已加载 {dispatcher.registry.count()} 个 skill\n")
        while True:
            try:
                user_input = input("\n> ")
                if user_input.lower() in ("exit", "quit"):
                    print("Bye!")
                    break
                result = dispatcher.handle(user_input)
                print(f"  {result}")
            except KeyboardInterrupt:
                print("\nBye!")
                break
        return

    # 默认模式：输出系统概览
    router = ModelRouter()
    cache = CacheEngine()
    adapter = DeepSeekAdapter()

    print("\n=== Tree-SOP Agent 系统概览 ===")
    print(f"  Skill 总数: {registry.count()}")
    print(f"  Pro skill: {len(registry.list_by_model('pro'))}")
    print(f"  Flash skill: {len(registry.list_by_model('flash'))}")
    print(f"  Model Router session: {router.all_session_ids()}")
    print(f"  Cache 前缀变更检测: {'启用' if cache.diagnostic else '未启用'}")
    print(f"  FC 适配器: {'已就绪' if not adapter.fc_fallback_triggered else '已降级'}")


if __name__ == "__main__":
    main()
