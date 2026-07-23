"""Jig — 公开 SDK API。

核心入口，5 行代码跑通整条 SOP 管道。

Usage:
    from jig import Jig
    app = Jig()
    app.run("帮我做一个登录功能")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from .core.skill_registry import SkillRegistry
from .core.agent_factory import AgentFactory
from .orchestrator.dispatcher import Dispatcher
from .adapters.model_provider import ModelRouter, DeepSeekProvider, OpenAIProvider, StreamChunk

logger = logging.getLogger(__name__)


class Jig:
    """Jig 框架主入口。

    所有用户从这里开始。5 行示例：

        from jig import Jig
        app = Jig(skills_dir="./skills")
        result = app.run("帮我做一个登录功能")
        print(result)
    """

    def __init__(
        self,
        skills_dir: str = "./skills",
        api_key: Optional[str] = None,
        default_model: str = "flash",
    ) -> None:
        self._skills_dir = Path(skills_dir)
        self._api_key = api_key
        self._default_model = default_model

        # 加载 skills
        self._registry = SkillRegistry()
        if self._skills_dir.exists():
            self._registry.register_skill_dir(str(self._skills_dir))
            count = self._registry.load_all()
            logger.info("Jig 初始化: %d 个 skill 已加载", count)
        else:
            logger.warning("skills 目录不存在: %s", skills_dir)

        self._dispatcher = Dispatcher(
            registry=self._registry,
            agent_factory=AgentFactory,
        )

    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有可用 Agent。"""
        return [
            {"name": s.name, "description": s.description[:60], "model": s.model}
            for s in self._registry.list_all()
        ]

    def run(self, prompt: str) -> str:
        """运行 SOP 管道。

        Args:
            prompt: 用户输入需求

        Returns:
            执行结果摘要
        """
        return self._dispatcher.handle(prompt)

    @property
    def skill_count(self) -> int:
        return self._registry.count()
