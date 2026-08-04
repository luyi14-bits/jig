"""Tests for CLI commands: eval / market / hitl-status. """

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run_cli(*args: str) -> str:
    """运行 CLI 并返回 stdout。"""
    import os
    env = dict(os.environ)
    env["PYTHONPATH"] = "src" + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, "-m", "src.jig.cli.main", *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=Path(__file__).parent.parent,
        env=env,
        timeout=60,
    )
    out = (result.stdout or "") + (result.stderr or "")
    if not out:
        out = f"[rc={result.returncode}]"
    return out


class TestCLIEval:
    def test_eval_command(self):
        dataset = tempfile.mktemp(suffix=".json")
        Path(dataset).write_text(
            json.dumps([{"input": "hello", "expected": "hello"}]), encoding="utf-8"
        )
        out = run_cli("--eval", dataset, "--report", dataset.replace(".json", "-report.md"))
        assert "评测集: 1 条" in out
        assert "Eval:" in out
        report = Path(dataset.replace(".json", "-report.md"))
        assert report.exists()
        report.unlink(missing_ok=True)
        Path(dataset).unlink(missing_ok=True)

    def test_market_list_command(self):
        out = run_cli("--market-list")
        # PluginMarket 扫描 install_dir，输出 📦 列表
        assert isinstance(out, str)
        assert "📦" in out or out.strip() == ""

    def test_hitl_status_command(self):
        out = run_cli("--hitl-status")
        assert "待审批" in out

    def test_help_contains_new_commands(self):
        out = run_cli("--help")
        assert "--eval" in out
        assert "--market-install" in out
        assert "--market-list" in out
        assert "--hitl-status" in out
