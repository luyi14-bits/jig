"""Skill 解析器单元测试。"""

import pytest
from pydantic import ValidationError

from jig.core.skill_parser import SkillParser, SkillParseError


class TestSkillParser:
    """测试 YAML frontmatter 解析器。"""

    VALID_SKILL = """---
name: "test-agent"
description: "A test skill for unit testing"
model: "flash"
tools:
  - name: "search"
    type: "api"
    description: "Search API"
  - name: "exec"
    type: "shell"
tags:
  - "test"
  - "demo"
sub_skills:
  - "sub-skill-1"
---

# Test content
"""

    def test_parse_valid(self):
        """有效 frontmatter 应正确解析。"""
        skill = SkillParser.parse_content(self.VALID_SKILL)
        assert skill.name == "test-agent"
        assert skill.model == "flash"
        assert len(skill.tools) == 2
        assert skill.tools[0].name == "search"
        assert "test" in skill.tags
        assert len(skill.sub_skills) == 1

    def test_missing_frontmatter(self):
        """缺失 frontmatter 应抛出 SkillParseError。"""
        content = "# Just a markdown file\nno frontmatter here"
        with pytest.raises(SkillParseError, match="缺少 YAML frontmatter"):
            SkillParser.parse_content(content)

    def test_missing_required_field(self):
        """缺失必填字段应抛出 SkillParseError。"""
        content = """---
name: "test-skill"
---
"""
        with pytest.raises(SkillParseError, match="缺少必填字段"):
            SkillParser.parse_content(content)

    def test_invalid_name_format(self):
        """无效 name 格式应抛出 SkillParseError。"""
        content = """---
name: "has space and 中文"
description: "test"
---
"""
        with pytest.raises(SkillParseError, match="name 字段格式无效"):
            SkillParser.parse_content(content)

    def test_invalid_yaml(self):
        """无效 YAML 应抛出 SkillParseError。"""
        content = """---
name: "test"
description: "test"
invalid: [yaml: broken}
---
"""
        with pytest.raises(SkillParseError, match="YAML 解析错误"):
            SkillParser.parse_content(content)

    def test_empty_tools(self):
        """tools 字段为空列表应正常解析。"""
        content = """---
name: "empty-tools"
description: "No tools needed"
---
"""
        skill = SkillParser.parse_content(content)
        assert len(skill.tools) == 0

    def test_pro_model(self):
        """Pro 模型 skill 应正确解析 model 字段。"""
        content = """---
name: "pm-agent"
description: "Product manager"
model: "pro"
---
"""
        skill = SkillParser.parse_content(content)
        assert skill.model == "pro"

    @pytest.mark.parametrize("name,expected", [
        ("valid-name", True),
        ("valid.name", True),
        ("valid_name", True),
        ("name123", True),
        ("123name", True),
        ("UPPERCASE", True),
    ])
    def test_valid_names(self, name, expected):
        """多种有效 name 格式应通过验证。"""
        content = f"""---
name: "{name}"
description: "test skill"
---
"""
        skill = SkillParser.parse_content(content)
        assert skill.name == name
