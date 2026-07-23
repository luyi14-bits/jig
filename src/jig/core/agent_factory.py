"""Agent 工厂 — 从 SkillDef 创建 Agent 实例。

遵循第一荣（模块导出清晰完整）：所有公开类在 __init__.py 注册。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..settings import settings
from .global_constraints import GLOBAL_CONSTRAINTS
from .skill_def import AgentConfig, HandoverPackage, SessionConfig, SkillDef, SOPNode, ToolDecl

logger = logging.getLogger(__name__)


class AgentExecutionError(Exception):
    """Agent 执行失败异常 — 包含失败信息供重试注入。"""
    def __init__(self, message: str, raw_output: str = ""):
        super().__init__(message)
        self.raw_output = raw_output


class Agent:
    """Agent 实例。

    封装 skill 定义的角色预设、工具集、模型配置和会话生命周期。
    每个 Agent 维护独立上下文，不与其他 Agent 共享状态。
    """

    def __init__(self, config: AgentConfig) -> None:
        self._config = config
        self._session_id: Optional[str] = None
        self._context: Dict[str, Any] = {}
        self._handover_in: Optional[HandoverPackage] = None
        self._handover_out: Optional[HandoverPackage] = None
        self._execution_log: List[str] = []
        logger.info("Agent 已创建: %s (model=%s)", config.skill_name, config.model_grade)

    @property
    def config(self) -> AgentConfig:
        return self._config

    @property
    def skill_name(self) -> str:
        return self._config.skill_name

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    def receive_handover(self, package: HandoverPackage) -> None:
        """接收上一个 Agent 的交接包。"""
        self._handover_in = package
        self._context["handover_from"] = package.source_agent
        self._context["previous_summary"] = package.summary
        self._context["previous_artifacts"] = package.artifacts
        logger.info(
            "Agent %s 收到交接包: from=%s, decisions=%d",
            self._config.skill_name,
            package.source_agent,
            len(package.decisions),
        )

    def set_context(self, key: str, value: Any) -> None:
        """设置上下文变量。"""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文变量。"""
        return self._context.get(key, default)

    def prepare_handover(
        self,
        target: str,
        summary: str,
        artifacts: Optional[Dict[str, Any]] = None,
        decisions: Optional[List[str]] = None,
        open_issues: Optional[List[str]] = None,
        confidence: float = 1.0,
    ) -> HandoverPackage:
        """准备传递给下一个 Agent 的交接包。"""
        self._handover_out = HandoverPackage(
            source_agent=self._config.skill_name,
            target_agent=target,
            summary=summary,
            artifacts=artifacts or {},
            decisions=decisions or [],
            open_issues=open_issues or [],
            confidence=confidence,
        )
        return self._handover_out

    def log_execution(self, message: str) -> None:
        """记录执行日志。"""
        self._execution_log.append(message)
        logger.debug("[Agent %s] %s", self._config.skill_name, message)

    def write_log(self, task_summary: str, output: str = "", target: str = "") -> None:
        """自动写 LOG.md 留痕。

        Args:
            task_summary: 任务摘要
            output: 产出物描述
            target: 交接目标 Agent
        """
        from pathlib import Path
        import datetime
        log_dir = Path(f"skills/{self.skill_name}")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "LOG.md"
        entry = f"""
## {datetime.date.today()}

### 执行：{task_summary}
- **产出**：{output or "-"}
- **交接目标**：{target or "-"}
- **Agent**：{self.skill_name}
"""
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
        logger.info("Agent %s 已写留痕日志: %s", self.skill_name, log_path)


class AgentFactory:
    """Agent 工厂 — 将 SkillDef 转换为可执行的 Agent 实例。"""

    # Pro 模型使用复杂推理的 skill 类型
    PRO_SKILL_TYPES = {"pm", "spec", "security", "mentor"}

    # 角色预设映射
    ROLE_PRESETS: Dict[str, str] = {
        "pm": "你是产品经理，负责需求定义、优先级排序和 PRD 编写。输出必须结构化、可执行。",
        "spec": "你是管线工程师，负责将需求转化为可执行的 Spec、任务拆分和验收清单。",
        "coding": "你是开发者，负责按 Spec 实现功能。默认使用 Flash 模型快速执行。",
        "tdd": "你是测试专家，负责编写测试用例和自测脚本。测试先行，红绿循环。",
        "acceptance": "你是验收人，独立验证交付物。不信任开发声明，逐项对照证据。",
        "security": "你是安全专家，负责代码审计、漏洞检测和打包安全。",
        "secretary": "你是项目秘书，负责文件管理、看板维护和留痕审计。",
        "mentor": "你是技术导师，负责架构评审和技术方案指导。",
    }

    @classmethod
    def create_agent(cls, skill_def: SkillDef, attached_skills: Optional[List[SkillDef]] = None) -> Agent:
        """从 SkillDef 创建 Agent 实例。

        Args:
            skill_def: 解析后的 Skill 定义。
            attached_skills: 用户挂载的额外 Skill 列表。

        Returns:
            配置完成的 Agent 实例。
        """
        # 确定模型等级
        model_grade = cls._resolve_model_grade(skill_def)

        # 构建 session 配置
        session_config = cls._build_session_config(skill_def, model_grade)

        # 构建角色预设（双层 prompt）
        role_preset = cls._build_role_preset(skill_def, attached_skills)

        # 创建 Agent 配置
        agent_config = AgentConfig(
            skill_name=skill_def.name,
            role_preset=role_preset,
            model_grade=model_grade,
            tools=skill_def.tools,
            session_config=session_config,
            tags=set(skill_def.tags),
        )

        return Agent(config=agent_config)

    @classmethod
    def _resolve_model_grade(cls, skill_def: SkillDef) -> str:
        """确定 skill 应该使用哪个模型等级。

        优先级：
        1. skill 自身的 model 字段显式指定
        2. skill 名称匹配默认映射
        3. 兜底：flash
        """
        if skill_def.model in ("pro", "flash"):
            return skill_def.model

        # 检查 skill 类型是否在默认映射中
        skill_type = skill_def.name.split("-")[0].lower()
        mapped = settings.default_model_mapping.get(skill_type)
        if mapped:
            return mapped.value if hasattr(mapped, "value") else mapped

        # 检查标签
        for skill_type_hint in cls.PRO_SKILL_TYPES:
            if skill_type_hint in skill_def.name.lower():
                return "pro"

        return "flash"

    @classmethod
    def _build_session_config(cls, skill_def: SkillDef, model_grade: str) -> SessionConfig:
        """构建 Session 配置。"""
        is_pro = model_grade == "pro"
        return SessionConfig(
            model=settings.pro_model if is_pro else settings.flash_model,
            temperature=settings.pro_temperature if is_pro else settings.flash_temperature,
        )

    @classmethod
    def _build_role_preset(cls, skill_def: SkillDef, attached_skills: Optional[List[SkillDef]] = None) -> str:
        """构建角色预设（双层 system prompt）。

        第一层：全局约束（所有 Agent 共享，不可变 → 命中缓存）
        第二层：角色专属约束（SKILL.md body 或 ROLE_PRESETS）
        第三层：挂载的 Skill body（用户导入）
        """
        parts = [GLOBAL_CONSTRAINTS]

        # 角色专属：优先使用 SKILL.md body 全文
        if skill_def.body.strip():
            parts.append(f"## 角色专属规则\n\n{skill_def.body}")
        else:
            # 兜底用 ROLE_PRESETS
            skill_lower = skill_def.name.lower()
            found = False
            for key, preset in cls.ROLE_PRESETS.items():
                if key in skill_lower:
                    parts.append(f"## 角色专属规则\n\n{preset}")
                    found = True
                    break
            if not found:
                parts.append(f"## 角色专属规则\n\n你是 {skill_def.name}。{skill_def.description}")

        # 挂载的 Skill body
        if attached_skills:
            for i, sk in enumerate(attached_skills):
                if sk.body.strip():
                    parts.append(f"## 挂载 Skill {i+1}: {sk.name}\n\n{sk.body}")

        return "\n\n---\n\n".join(parts)
