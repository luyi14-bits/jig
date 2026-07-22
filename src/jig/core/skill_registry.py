"""Skill 注册表 — 加载、验证、注册 Skill 定义。

SkillRegistry 是全局单例，维护所有已加载 skill 的索引。
遵循第八荣（API 调用走封装层）：所有 SKILL.md 访问都必须通过注册表。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from .skill_def import SkillDef
from .skill_parser import SkillParser, SkillParseError

logger = logging.getLogger(__name__)


class SkillRegistry:
    """全局 Skill 注册表（单例模式）。

    负责：
    - 从文件系统加载 SKILL.md
    - 维护 name → SkillDef 映射
    - 提供按名称/标签/模型查询
    """

    _instance: Optional["SkillRegistry"] = None

    def __new__(cls) -> "SkillRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._skills: Dict[str, SkillDef] = {}
        self._skill_dirs: List[Path] = []
        self._initialized = True

    def register_skill_dir(self, directory: str | Path) -> None:
        """注册一个技能目录（递归搜索 SKILL.md）。

        Args:
            directory: 包含 SKILL.md 文件的目录路径。
        """
        path = Path(directory)
        if not path.is_dir():
            logger.warning("技能目录不存在，跳过: %s", directory)
            return
        self._skill_dirs.append(path)

    def load_all(self) -> int:
        """加载所有已注册目录中的 skill。

        Returns:
            成功加载的 skill 数量。
        """
        count = 0
        for skill_dir in self._skill_dirs:
            skill_files = list(skill_dir.rglob("SKILL.md"))
            for skill_file in skill_files:
                try:
                    skill_def = SkillParser.parse_file(skill_file)
                    self._skills[skill_def.name] = skill_def
                    count += 1
                    logger.info("已加载 skill: %s (from %s)", skill_def.name, skill_file)
                except SkillParseError as e:
                    logger.error("Skill 解析失败 [%s]: %s", skill_file, e)
        return count

    def load_single(self, filepath: str | Path) -> SkillDef:
        """加载单个 SKILL.md 文件并注册。

        Args:
            filepath: SKILL.md 文件路径。

        Returns:
            解析后的 SkillDef 实例。

        Raises:
            SkillParseError: 解析失败。
        """
        skill_def = SkillParser.parse_file(filepath)
        self._skills[skill_def.name] = skill_def
        logger.info("已加载单个 skill: %s (from %s)", skill_def.name, filepath)
        return skill_def

    def get(self, name: str) -> Optional[SkillDef]:
        """按名称获取 SkillDef。

        Args:
            name: Skill 名称。

        Returns:
            SkillDef 实例，未找到时返回 None。
        """
        return self._skills.get(name)

    def list_all(self) -> List[SkillDef]:
        """列出所有已加载的 skill。"""
        return list(self._skills.values())

    def list_by_model(self, model: str) -> List[SkillDef]:
        """按模型等级过滤。

        Args:
            model: "pro" 或 "flash"。

        Returns:
            匹配的 SkillDef 列表。
        """
        return [s for s in self._skills.values() if s.model == model]

    def list_by_tag(self, tag: str) -> List[SkillDef]:
        """按标签过滤。"""
        return [s for s in self._skills.values() if tag in s.tags]

    def count(self) -> int:
        """已加载的 skill 数量。"""
        return len(self._skills)

    def clear(self) -> None:
        """清空注册表（主要用于测试）。"""
        self._skills.clear()
        self._skill_dirs.clear()
