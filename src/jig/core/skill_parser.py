"""Skill 定义解析器 — YAML frontmatter → SkillDef。

遵循第十五荣（接口契约即法律）：不假设输入格式，严格验证。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .skill_def import SkillDef, SOPNode, ToolDecl, ToolType


class SkillParseError(Exception):
    """Skill 解析错误。"""


class SkillParser:
    """YAML frontmatter 解析器。

    从 `---` 分隔的 Markdown 文件中提取 YAML frontmatter，
    解析为 SkillDef 数据模型。
    """

    FRONTMATTER_PATTERN = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

    REQUIRED_FIELDS = {"name", "description"}

    @classmethod
    def parse_file(cls, filepath: str | Path) -> SkillDef:
        """从文件路径解析 Skill 定义。

        Args:
            filepath: SKILL.md 文件路径。

        Returns:
            解析后的 SkillDef 实例。

        Raises:
            SkillParseError: 文件不存在、frontmatter 缺失或验证失败。
        """
        path = Path(filepath)
        if not path.exists():
            raise SkillParseError(f"文件不存在: {filepath}")
        if not path.is_file():
            raise SkillParseError(f"路径不是文件: {filepath}")

        content = path.read_text(encoding="utf-8")
        return cls.parse_content(content, str(filepath))

    @classmethod
    def parse_content(cls, content: str, source: str = "<string>") -> SkillDef:
        """从字符串内容解析 Skill 定义。

        Args:
            content: Markdown 文件内容（含 frontmatter）。
            source: 来源描述（用于错误信息）。

        Returns:
            解析后的 SkillDef 实例。

        Raises:
            SkillParseError: frontmatter 缺失或验证失败。
        """
        match = cls.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise SkillParseError(f"缺少 YAML frontmatter（--- 分隔块）: {source}")

        raw_yaml = match.group(1)
        body = content[match.end():].strip()
        try:
            data: Dict[str, Any] = yaml.safe_load(raw_yaml)
        except yaml.YAMLError as e:
            raise SkillParseError(f"YAML 解析错误: {e}") from e

        if not isinstance(data, dict):
            raise SkillParseError(f"frontmatter 必须是字典结构，得到 {type(data).__name__}: {source}")

        return cls._validate_and_build(data, source, body)

    @classmethod
    def _validate_and_build(cls, data: Dict[str, Any], source: str, body: str = "") -> SkillDef:
        """验证并构建 SkillDef。"""
        # 验证必填字段
        missing = cls.REQUIRED_FIELDS - set(data.keys())
        if missing:
            raise SkillParseError(
                f"缺少必填字段 [{'/'.join(sorted(missing))}]: {source}"
            )

        # 验证 name 格式
        name = str(data["name"])
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$", name):
            raise SkillParseError(
                f"name 字段格式无效（须以字母/数字开头，仅含字母/数字/.-_）: {name}"
            )

        # 解析工具声明
        tools_raw = data.get("tools", [])
        if isinstance(tools_raw, list):
            tools = cls._parse_tools(tools_raw)
        else:
            tools = []

        # 解析 SOP 树形定义
        sop_raw = data.get("sop")
        sop_node = cls._parse_sop_node(sop_raw) if sop_raw else None

        # 构建 SkillDef
        return SkillDef(
            name=name,
            description=str(data.get("description", "")),
            tools=tools,
            model=str(data.get("model", "flash")),
            model_name=str(data["model_name"]) if "model_name" in data else None,
            sub_skills=list(data.get("sub_skills", [])),
            tags=list(data.get("tags", [])),
            metadata=dict(data.get("metadata", {})),
            body=body,
            agent_name=str(data["agent_name"]) if "agent_name" in data else None,
        )

    @classmethod
    def _parse_tools(cls, tools_raw: List[Any]) -> List[ToolDecl]:
        """解析工具声明列表。"""
        tools = []
        for item in tools_raw:
            if isinstance(item, str):
                tools.append(ToolDecl(name=item, tool_type=ToolType.API))
            elif isinstance(item, dict):
                name = str(item.get("name", ""))
                tool_type_str = str(item.get("type", "api"))
                try:
                    tool_type = ToolType(tool_type_str)
                except ValueError:
                    tool_type = ToolType.API
                tools.append(ToolDecl(
                    name=name,
                    tool_type=tool_type,
                    endpoint=str(item["endpoint"]) if "endpoint" in item else None,
                    description=str(item.get("description", "")),
                    parameters=dict(item.get("parameters", {})),
                ))
        return tools

    @classmethod
    def _parse_sop_node(cls, data: Dict[str, Any]) -> SOPNode:
        """递归解析 SOP 树节点。"""
        sub_steps_raw = data.get("sub_steps", [])
        sub_steps = [cls._parse_sop_node(s) for s in sub_steps_raw] if sub_steps_raw else []

        return SOPNode(
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            skill_ref=str(data["skill_ref"]) if "skill_ref" in data else None,
            mode=str(data.get("mode", "sequential")),
            sub_steps=sub_steps,
            max_retries=int(data.get("max_retries", 3)),
            timeout_seconds=int(data["timeout_seconds"]) if "timeout_seconds" in data else None,
        )
