"""端到端 LOOP SOP 集成测试。

模拟一次完整的 5 阶段管道：加载 skills → Dispatcher 路由 → Agent 协作 → 验收。
"""

import pytest
from pathlib import Path
from jig.core.skill_registry import SkillRegistry
from jig.core.skill_parser import SkillParser
from jig.core.agent_factory import AgentFactory


class TestE2ELOOP:
    """端到端 LOOP SOP 集成测试。"""

    SKILL_DIR = Path(__file__).parent.parent / "skills"

    @pytest.fixture
    def registry(self):
        r = SkillRegistry()
        r.clear()
        if self.SKILL_DIR.exists():
            r.register_skill_dir(str(self.SKILL_DIR))
            r.load_all()
        return r

    def test_all_skills_loadable(self, registry):
        """阶段 0 准入检查：所有 skill 可加载。"""
        count = registry.count()
        assert count >= 10, f"期待至少 10 个 skill，实际 {count}"
        print(f"[OK] 已加载 {count} 个 skill")

    def test_all_skills_parse_correctly(self):
        """每个 SKILL.md 能被 SkillParser 正确解析。"""
        if not self.SKILL_DIR.exists():
            pytest.skip("skills 目录不存在")
        errors = []
        for md_file in sorted(self.SKILL_DIR.rglob("SKILL.md")):
            try:
                skill = SkillParser.parse_file(str(md_file))
                assert skill.name, f"SKILL.md 缺少 name: {md_file}"
                assert skill.description, f"SKILL.md 缺少 description: {md_file}"
            except Exception as e:
                errors.append(f"{md_file.name}: {e}")
        assert not errors, f"解析错误: {errors}"
        print(f"[OK] 全部 SKILL.md 解析通过")

    def test_agent_team_is_complete(self, registry):
        """11 个核心角色应该都存在。"""
        required_roles = {
            "Luyi14-pm-mentor", "Luyi14-spec-pipeline", "Luyi14-coding-ethics",
            "Luyi14-code-review", "Luyi14-test-driven-development",
            "Luyi14-acceptance-testing", "Luyi14-security-academy",
            "Luyi14-devops", "Luyi14-project-secretary",
            "Luyi14-trinity-mentors", "Luyi14-loop-sop",
        }
        loaded = {s.name for s in registry.list_all()}
        missing = required_roles - loaded
        assert not missing, f"缺少核心角色: {missing}"
        print(f"[OK] 11 个核心角色全部就绪")

    def test_dispatcher_routes_to_pm(self, registry):
        """Dispatcher 收到需求后路由到 PM Agent。"""
        from jig.orchestrator.dispatcher import Dispatcher
        if not self.SKILL_DIR.exists():
            pytest.skip("skills 目录不存在")
        d = Dispatcher(skill_dir=str(self.SKILL_DIR))
        result = d.handle("帮我做一个登录功能")
        assert "PM" in result or "pm" in result, f"Dispatcher 未路由到 PM: {result}"
        print(f"[OK] Dispatcher 路由成功: {result}")

    def test_full_pipeline_tasks(self):
        """验证各阶段的关键交付物存在。"""
        # 阶段 1: Spec 文档
        spec_dir = Path(__file__).parent.parent / ".trae" / "specs"
        spec_count = len(list(spec_dir.rglob("spec.md"))) if spec_dir.exists() else 0
        print(f"[OK] Spec 文档数: {spec_count}")

        # 阶段 2: 核心模块存在
        src_dir = Path(__file__).parent.parent / "src" / "jig"
        core_files = list(src_dir.rglob("*.py"))
        assert len(core_files) >= 15, f"核心模块数不足: {len(core_files)}"
        print(f"[OK] 核心模块数: {len(core_files)}")

        # 阶段 3: 测试套件
        test_dir = Path(__file__).parent.parent / "tests"
        test_files = list(test_dir.rglob("test_*.py"))
        print(f"[OK] 测试文件数: {len(test_files)}")

    def test_checkpoint_persistence(self):
        """阶段 4: 检查点持久化。"""
        import tempfile
        from jig.orchestrator.orchestrator import CheckpointManager
        with tempfile.TemporaryDirectory() as tmp:
            mgr = CheckpointManager(checkpoint_dir=tmp)
            path = mgr.save("test-loop-e2e", {"phase": 4, "status": "done"})
            assert path is not None
            state = mgr.load("test-loop-e2e")
            assert state["phase"] == 4
        print(f"[OK] 检查点持久化正常")

    def test_all_tests_pass(self):
        """全量测试确保通过。"""
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        output = result.stdout + result.stderr
        assert result.returncode == 0, f"测试失败:\n{output}"
        # 提取通过数
        for line in output.splitlines():
            if "passed" in line and "failed" not in line:
                print(f"[OK] 全量测试: {line.strip()}")
