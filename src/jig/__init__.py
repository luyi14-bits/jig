# Jig — 自研多 Agent 编排框架
#
# SPDX-License-Identifier: MIT

"""Jig: 自研多 Agent 编排框架 — 13 个预设角色、4 层记忆、硬约束 Harness。

快速开始:
    from jig import Jig
    app = Jig(skills_dir="./skills")
    result = app.run("帮我做一个登录功能")
    print(result)

二次开发:
    from jig import Jig, SkillRegistry, ConfigManager, LoopEngine
    from jig.adapters.cache_engine import CacheEngine
    
    app = Jig()
    app.add_agent("my-agent", "角色描述", tools=["read", "write"])
    app.attach_skill("path/to/skill.md")
    app.set_pipeline([pm_agent, coding_agent, qa_agent])
    result = await app.arun("任务描述", on_stage=my_callback)
"""

from .api import Jig
from .core.skill_registry import SkillRegistry
from .core.skill_parser import SkillParser
from .core.agent_factory import AgentFactory
from .core.config_manager import ConfigManager
from .orchestrator.loop_engine import LoopEngine, LoopConfig, LoopStatus
from .adapters.model_provider import (
    BaseModelProvider, DeepSeekProvider, OpenAIProvider,
    ModelRouter, ModelResponse, StreamChunk,
)
from .tools.image_reader import ImageReader

__all__ = [
    "Jig",
    "SkillRegistry",
    "SkillParser",
    "AgentFactory",
    "ConfigManager",
    "LoopEngine",
    "LoopConfig",
    "LoopStatus",
    "BaseModelProvider",
    "DeepSeekProvider",
    "OpenAIProvider",
    "ModelRouter",
    "ModelResponse",
    "StreamChunk",
    "ImageReader",
]
