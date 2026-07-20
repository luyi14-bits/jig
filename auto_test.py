#!/usr/bin/env python3
"""AgentHarness CLI 自测脚本。

执行方式（不依赖 GUI / IDE）:
    python auto_test.py

遵循第二十一荣（自测循环多策略验证）：
- 每策略执行后验证结果
- 失败自动降级
- 聚合错误信息
"""

from __future__ import annotations

import importlib.util
import logging
import subprocess
import sys
from pathlib import Path

# ── 日志配置 ──
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("auto_test")


def check_dependencies() -> bool:
    """检查依赖是否完整。"""
    missing = []
    for pkg, mod_name in [("pydantic", "pydantic"), ("pydantic_settings", "pydantic_settings"),
                           ("pyyaml", "yaml"), ("pytest", "pytest")]:
        if importlib.util.find_spec(mod_name) is None:
            missing.append(pkg)
    if missing:
        print(f"[X] 缺少依赖: {', '.join(missing)}")
        print(f"   运行: pip install {' '.join(missing)}")
        return False
    return True


def test_skill_parser() -> bool:
    """测试 Skill 解析器。"""
    try:
        from agent_harness.core.skill_parser import SkillParser

        # 有效 frontmatter
        valid_content = """---
name: "test-skill"
description: "Test skill for self-test"
model: "flash"
tools:
  - name: "echo"
    type: "shell"
---
# Test content
"""
        skill = SkillParser.parse_content(valid_content)
        assert skill.name == "test-skill"
        assert skill.model == "flash"
        assert len(skill.tools) == 1
        assert skill.tools[0].name == "echo"
        print("[OK] Skill 解析器: 有效 frontmatter 解析正确")

        # 缺失字段
        invalid_content = """---
name: "test-skill"
---
"""
        try:
            SkillParser.parse_content(invalid_content)
            print("[X] Skill 解析器: 缺失字段未抛出异常")
            return False
        except Exception:
            print("[OK] Skill 解析器: 缺失字段正确抛出异常")

        return True
    except Exception as e:
        logger.error("Skill 解析器测试失败: %s", e)
        return False


def test_skill_registry() -> bool:
    """测试 Skill 注册表。"""
    try:
        from agent_harness.core.skill_registry import SkillRegistry
        from agent_harness.core.skill_parser import SkillParser

        registry = SkillRegistry()
        # 先清空（单例可能保留旧数据）
        registry.clear()

        # 加载 test_skill 目录中的 SKILL.md（如果有）
        test_dir = Path(__file__).parent / ".trae" / "specs"
        if test_dir.exists():
            registry.register_skill_dir(str(test_dir))

        # 手动注册一个 skill
        from agent_harness.core.skill_def import SkillDef
        fake_skill = SkillDef(name="self-test", description="自测 skill")
        registry._skills["self-test"] = fake_skill

        result = registry.get("self-test")
        assert result is not None
        assert result.name == "self-test"
        print("[OK] Skill 注册表: 注册和查询正确")

        skills = registry.list_all()
        assert len(skills) >= 1
        print(f"[OK] Skill 注册表: 总计 {len(skills)} 个 skill")

        return True
    except Exception as e:
        logger.error("Skill 注册表测试失败: %s", e)
        return False


def test_agent_factory() -> bool:
    """测试 Agent 工厂。"""
    try:
        from agent_harness.core.agent_factory import AgentFactory
        from agent_harness.core.skill_def import SkillDef

        skill = SkillDef(name="test-coding", description="编码 skill", model="flash")
        agent = AgentFactory.create_agent(skill)

        assert agent.skill_name == "test-coding"
        assert agent.config.model_grade == "flash"
        assert agent.config.session_config is not None
        print("[OK] Agent 工厂: Flash skill 正确创建 Agent")

        # Pro skill
        skill2 = SkillDef(name="test-pm", description="PM skill", model="pro")
        agent2 = AgentFactory.create_agent(skill2)
        assert agent2.config.model_grade == "pro"
        print("[OK] Agent 工厂: Pro skill 正确创建 Agent")

        # 交接包
        handover = agent.prepare_handover(
            target="next-agent",
            summary="测试完成",
            decisions=["使用 Flash 模型"],
        )
        assert handover.source_agent == "test-coding"
        assert handover.target_agent == "next-agent"
        print("[OK] Agent 工厂: 交接包生成正确")

        return True
    except Exception as e:
        logger.error("Agent 工厂测试失败: %s", e)
        return False


def test_cache_engine() -> bool:
    """测试缓存引擎。"""
    try:
        from agent_harness.adapters.cache_engine import CacheEngine

        engine = CacheEngine()

        # 第一次组装 -> 无变更
        snap1 = engine.assemble_prefix(
            base_prompt="You are a helpful assistant.",
            output_style="Use Chinese.",
            language="zh-CN",
            skill_index="test-skill: 测试",
        )
        assert snap1.hash is not None
        assert not engine.diagnostic.prefix_changed
        print("[OK] 缓存引擎: 首次前缀组装正确")

        # 第二次相同 -> 无变更
        snap2 = engine.assemble_prefix(
            base_prompt="You are a helpful assistant.",
            output_style="Use Chinese.",
            language="zh-CN",
            skill_index="test-skill: 测试",
        )
        assert snap2.hash == snap1.hash
        assert not engine.diagnostic.prefix_changed
        print("[OK] 缓存引擎: 相同前缀 hash 一致")

        # 第三次变更 memory -> 检测变更
        snap3 = engine.assemble_prefix(
            base_prompt="You are a helpful assistant.",
            output_style="Use Chinese.",
            language="zh-CN",
            memory="User prefers Python.",
            skill_index="test-skill: 测试",
        )
        assert snap3.hash != snap2.hash
        assert engine.diagnostic.prefix_changed
        assert len(engine.diagnostic.change_reasons) > 0
        print("[OK] 缓存引擎: 前缀变更正确检测")

        # memory-update block
        block = engine.create_memory_update_block("Updated memory content")
        assert "<memory-update>" in block
        assert "</memory-update>" in block
        print("[OK] 缓存引擎: memory-update XML 块正确")

        return True
    except Exception as e:
        logger.error("缓存引擎测试失败: %s", e)
        return False


def test_deepseek_adapter() -> bool:
    """测试 DeepSeek 适配器。"""
    try:
        from agent_harness.adapters.deepseek_adapter import DeepSeekAdapter

        adapter = DeepSeekAdapter()

        # FC 降级测试
        request = adapter.prepare_request(
            messages=[{"role": "user", "content": "hello"}],
            tools=[{"type": "function", "function": {"name": "test"}}],
            model="deepseek-reasoner",
        )
        assert request["model"] == "deepseek-chat"
        assert adapter.fc_fallback_triggered
        print("[OK] DeepSeek 适配器: reasoner -> chat 降级正确")

        # reasoning_content 保留（带 tool_calls）
        adapter2 = DeepSeekAdapter()
        messages_with_tools = [
            {"role": "assistant", "content": "", "tool_calls": [{"id": "call_1", "type": "function"}]},
        ]
        processed = adapter2.prepare_request(messages_with_tools)
        # 应保留 reasoning_content 字段
        print("[OK] DeepSeek 适配器: 消息处理无异常")

        return True
    except Exception as e:
        logger.error("DeepSeek 适配器测试失败: %s", e)
        return False


def test_context_partitioner() -> bool:
    """测试三层 Context 分区。"""
    try:
        from agent_harness.adapters.context import ContextPartitioner

        partitioner = ContextPartitioner(session_id="test-session")

        # 设置不可变前缀
        partitioner.set_immutable(
            system_prompt="You are a helpful assistant.",
            tools=[],
            memory="User memory content.",
        )
        assert partitioner.immutable_frozen
        print("[OK] Context 分区: 不可变前缀已冻结")

        # 追加日志
        partitioner.append_message({"role": "user", "content": "Hello"})
        partitioner.append_message({"role": "assistant", "content": "Hi"})
        assert partitioner.total_message_count == 4  # 2 immutable msg + 2 append-only
        print("[OK] Context 分区: append-only 区正确增长")

        # volatile 区
        partitioner.set_volatile({"plan": "step 1: ..."})
        partitioner.add_volatile_note("temp_note", "thinking...")

        api_msgs = partitioner.build_api_messages()
        # volatile 不应出现在 API 消息中
        assert len(api_msgs) == 4, f"expected 3, got {len(api_msgs)}"
        print("[OK] Context 分区: volatile 区不发给 API")

        return True
    except Exception as e:
        logger.error("Context 分区测试失败: %s", e)
        return False


def test_orchestrator() -> bool:
    """测试 SOP 编排器。"""
    try:
        from agent_harness.orchestrator import SequentialOrchestrator
        from agent_harness.core.skill_def import SOPNode

        # 构造简单顺序 SOP
        sop = SOPNode(
            name="root",
            description="根节点",
            mode="sequential",
            sub_steps=[
                SOPNode(name="step1", description="第一步", skill_ref="test-skill-1"),
                SOPNode(name="step2", description="第二步", skill_ref="test-skill-2"),
            ],
        )

        # 用 mock resolver
        def resolver(name):
            return None  # mock — 不真正执行

        orch = SequentialOrchestrator(agent_resolver=resolver)
        result = orch.execute(sop, {})
        assert result is not None
        assert len(orch.execution_log) > 0
        print("[OK] SOP 编排: 顺序调度执行正确")

        return True
    except Exception as e:
        logger.error("SOP 编排测试失败: %s", e)
        return False


def run_all_strategies() -> bool:
    """多策略验证：逐策略执行，全部 PASS 才返回 True。

    如果某个策略失败，继续执行下一个；全部失败时收集所有错误信息。
    """
    strategies = [
        ("SKILL 解析器", test_skill_parser),
        ("Skill 注册表", test_skill_registry),
        ("Agent 工厂", test_agent_factory),
        ("缓存引擎", test_cache_engine),
        ("DeepSeek 适配器", test_deepseek_adapter),
        ("Context 分区", test_context_partitioner),
        ("SOP 编排", test_orchestrator),
    ]

    errors = []
    passed = 0
    total = len(strategies)

    for name, strategy_fn in strategies:
        try:
            if strategy_fn():
                passed += 1
            else:
                errors.append(f"{name}: 失败")
        except Exception as e:
            errors.append(f"{name}: {e}")

    print(f"\n{'='*40}")
    print(f"自测结果: {passed}/{total} 通过")
    if errors:
        print(f"失败项:")
        for e in errors:
            print(f"  [X] {e}")
        print(f"{'='*40}")
        return False
    else:
        print(f"[OK] 全部通过!")
        print(f"{'='*40}")
        return True


def main():
    """自测脚本主入口。"""
    print("=" * 40)
    print(" AgentHarness 自测脚本")
    print("=" * 40)

    # 首先检查依赖
    if not check_dependencies():
        sys.exit(1)
    print("[OK] 依赖检查通过\n")

    # 确保 src/ 在 Python path 中
    src_dir = Path(__file__).parent / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir.resolve()))

    # 运行所有策略
    success = run_all_strategies()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
