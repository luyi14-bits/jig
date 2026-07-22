"""核心数据模型定义。

遵循第五荣（类型声明完整清晰）：所有结构化数据使用 Pydantic BaseModel。
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class ToolType(str, Enum):
    """工具类型枚举。"""
    MCP_SERVER = "mcp_server"
    SHELL = "shell"
    API = "api"


class ToolDecl(BaseModel):
    """工具声明。

    描述 Agent 可以使用的工具类型和访问方式。
    """
    name: str = Field(description="工具名称（全局唯一）")
    tool_type: ToolType = Field(description="工具类型")
    endpoint: Optional[str] = Field(default=None, description="工具端点 URL 或命令路径")
    description: str = Field(default="", description="工具功能描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数 schema")


class SOPNode(BaseModel):
    """SOP 树节点。

    支持顺序（sequential）和并行（parallel）两种子节点调度方式。
    递归结构：一个 SOPNode 可包含子 SOPNode 列表。
    """
    name: str = Field(description="节点名称（全局唯一）")
    description: str = Field(default="", description="节点功能描述")
    skill_ref: Optional[str] = Field(default=None, description="引用的 skill 名称（叶子节点）")
    mode: str = Field(default="sequential", description="调度模式: sequential / parallel")
    sub_steps: List[SOPNode] = Field(default_factory=list, description="子 SOP 节点列表（树形结构）")
    max_retries: int = Field(default=3, description="子节点执行失败时的最大重试次数")
    timeout_seconds: Optional[int] = Field(default=None, description="节点执行超时秒数")


class SkillDef(BaseModel):
    """Skill 定义的数据模型。

    对应 SKILL.md 文件的 YAML frontmatter 解析结果。
    """
    name: str = Field(description="Skill 名称（全局唯一标识符）")
    description: str = Field(description="Skill 功能描述（≤200 字符）")
    tools: List[ToolDecl] = Field(default_factory=list, description="Skill 声明的工具列表")
    model: str = Field(default="flash", description="模型等级: pro / flash")
    model_name: Optional[str] = Field(default=None, description="指定具体模型名称（可选覆盖）")
    sub_skills: List[str] = Field(default_factory=list, description="子 Skill 引用列表（树形 SOP）")
    tags: List[str] = Field(default_factory=list, description="标签分类")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="自定义元数据")
    body: str = Field(default="", description="SKILL.md frontmatter 之后的 Markdown 正文（Agent system prompt）")
    agent_name: Optional[str] = Field(default=None, description="用户自定义 Agent 显示名")


class SessionConfig(BaseModel):
    """Session 配置。

    每个模型等级（Pro/Flash）维护独立的 Session 配置。
    """
    model: str = Field(description="模型名称")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="采样温度")
    max_tokens: int = Field(default=4096, description="最大输出 token 数")
    timeout_seconds: int = Field(default=60, description="请求超时秒数")
    tool_choice: Optional[Dict[str, Any]] = Field(
        default=None,
        description="显式工具选择，格式: {\"type\": \"function\", \"function\": {\"name\": \"...\"}}",
    )


class AgentConfig(BaseModel):
    """Agent 配置。

    从 SkillDef 转换而来，用于实例化 Agent。
    """
    skill_name: str = Field(description="来源 skill 名称")
    role_preset: str = Field(description="角色预设（system prompt）")
    model_grade: str = Field(description="模型等级: pro / flash")
    tools: List[ToolDecl] = Field(default_factory=list, description="可用工具列表")
    session_config: SessionConfig = Field(description="Session 配置")
    sop_definition: Optional[SOPNode] = Field(default=None, description="SOP 树定义（如适用）")
    tags: Set[str] = Field(default_factory=set, description="标签集合")
    attached_skills: List["SkillDef"] = Field(default_factory=list, description="用户挂载的额外 Skill 定义")


class HandoverPackage(BaseModel):
    """Agent 交接包。

    当 SOP 编排中一个 Agent 完成工作后，将结果打包传递给下一个 Agent。
    """
    source_agent: str = Field(description="来源 Agent 名称")
    target_agent: str = Field(description="目标 Agent 名称")
    summary: str = Field(description="执行摘要")
    artifacts: Dict[str, Any] = Field(default_factory=dict, description="产出物（文件路径 / 数据）")
    decisions: List[str] = Field(default_factory=list, description="关键决策记录")
    open_issues: List[str] = Field(default_factory=list, description="待处理问题")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="结果置信度")
