"""Skill 插件市场 — 第三方 SKILL.md 包分发机制。

IDEA-048: 通过 pip 包分发和安装第三方 SKILL.md。
"""

from __future__ import annotations
from pathlib import Path
from typing import List


class PluginMarket:
    """Skill 插件市场。"""

    def __init__(self, install_dir: str = "./skills") -> None:
        self._install_dir = Path(install_dir)

    def install_package(self, package_name: str) -> str:
        """从 pip 安装 skill 包。"""
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True, text=True)
        return result.stdout + result.stderr

    def list_installed(self) -> List[str]:
        """列出已安装的 skill 包。"""
        if not self._install_dir.exists():
            return []
        return [d.name for d in self._install_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
