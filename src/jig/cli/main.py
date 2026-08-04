"""Tree-SOP Agent CLI 入口。"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ..core.skill_registry import SkillRegistry
from ..core.agent_factory import AgentFactory
from ..adapters.model_provider import ModelRouter, DeepSeekProvider
from ..adapters.cache_engine import CacheEngine
from ..adapters.cache_diagnostics import CacheDiagnosticResult
from ..adapters.context import ContextPartitioner
from ..adapters.deepseek_adapter import DeepSeekAdapter

logger = logging.getLogger(__name__)


def main() -> None:
    """CLI 主入口。"""
    # 缓存诊断摘要
    try:
        diag = CacheDiagnostic()
        print(diag.summary())
    except Exception:
        pass

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
    parser.add_argument(
        "--server",
        action="store_true",
        help="启动 FastAPI 服务（同步模式）",
    )
    parser.add_argument(
        "--server-async",
        action="store_true",
        help="启动 FastAPI 服务（异步+队列模式）",
    )
    parser.add_argument(
        "--eval",
        type=str,
        default=None,
        metavar="DATASET.json",
        help="运行评测集并生成报告",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        metavar="REPORT.md",
        help="评测报告输出路径（配合 --eval）",
    )
    parser.add_argument(
        "--market-install",
        type=str,
        default=None,
        metavar="PACKAGE",
        help="从插件市场安装 skill 包",
    )
    parser.add_argument(
        "--market-list",
        action="store_true",
        help="列出已安装的市场 skill 包",
    )
    parser.add_argument(
        "--hitl-status",
        action="store_true",
        help="查看待审批的 HITL 暂停",
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

    # --server: 启动 FastAPI 服务
    if args.server:
        from ..server.app import app, run_server
        print("启动 FastAPI 服务（同步模式）: http://localhost:8000")
        run_server(host="0.0.0.0", port=8000)
        return

    # --server-async: 启动异步 FastAPI 服务
    if args.server_async:
        import uvicorn
        from ..server.async_app import app as async_app
        print("启动 FastAPI 服务（异步+队列模式）: http://localhost:8001")
        uvicorn.run(async_app, host="0.0.0.0", port=8001)
        return

    # --eval: 运行评测集
    if args.eval:
        from ..core.eval_runner import EvalRunner
        import json
        dataset_path = args.eval
        report_path = args.report or dataset_path.replace(".json", "-report.md")
        examples = EvalRunner.load_dataset(dataset_path)
        print(f"评测集: {len(examples)} 条")
        runner = EvalRunner()
        # 简单 echo judge（无 LLM key 时可用）
        report = runner.run(dataset_path, examples, lambda x: x)
        EvalRunner.save_report(report, report_path)
        print(report.summary_text)
        print(f"报告已保存: {report_path}")
        return

    # --market-install: 从插件市场安装 skill 包
    if args.market_install:
        from ..contrib.plugin_market import PluginMarket
        market = PluginMarket(install_dir=str(skill_dir))
        output = market.install_package(args.market_install)
        print(output)
        # 刷新注册表
        registry.register_skill_dir(str(skill_dir))
        registry.load_all()
        print(f"已刷新，当前 {registry.count()} 个 skill")
        return

    # --market-list: 列出已安装的市场包
    if args.market_list:
        from ..contrib.plugin_market import PluginMarket
        market = PluginMarket()
        for pkg in market.list_installed():
            print(f"  📦 {pkg}")
        return

    # --hitl-status: 查看待审批 HITL 暂停
    if args.hitl_status:
        from ..orchestrator.sop_runner import SOPRunner
        runner = SOPRunner()
        pending = runner.hitl_status()
        if pending:
            for sid, node in pending.items():
                print(f"  ⏸ {sid}: {node}")
        else:
            print("无待审批的 HITL 暂停")
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
