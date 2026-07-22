"""模型路由 — Pro/Flash 双模型策略管理器。

Task 4: 根据 skill frontmatter 的 model 字段路由到 Pro/Flash。
不同 model 等级使用独立 session。
"""

from __future__ import annotations

import logging
import uuid
from typing import Dict, Optional

from ..settings import settings

logger = logging.getLogger(__name__)


class ModelRoute:
    """模型路由结果。"""

    def __init__(
        self,
        model_name: str,
        model_grade: str,
        temperature: float,
        session_id: str,
    ) -> None:
        self.model_name = model_name
        self.model_grade = model_grade
        self.temperature = temperature
        self.session_id = session_id


class ModelRouter:
    """模型路由器 — 维护 Pro/Flash 独立 session 池。"""

    def __init__(self) -> None:
        # 模型等级 → session_id 映射
        self._sessions: Dict[str, str] = {}
        # 会话级前缀快照（用于缓存诊断）
        self._prefix_snapshots: Dict[str, str] = {}

    def route(self, model_grade: str) -> ModelRoute:
        """路由到指定模型等级的 session。

        Args:
            model_grade: "pro" 或 "flash"。

        Returns:
            模型路由结果（含模型名称、temperature、session_id）。
        """
        is_pro = model_grade == "pro"
        model_name = settings.pro_model if is_pro else settings.flash_model
        temperature = settings.pro_temperature if is_pro else settings.flash_temperature

        # 获取或创建 session
        if model_grade not in self._sessions:
            session_id = f"session_{model_grade}_{uuid.uuid4().hex[:8]}"
            self._sessions[model_grade] = session_id
            logger.info("创建新 session: %s (model=%s)", session_id, model_name)

        session_id = self._sessions[model_grade]

        return ModelRoute(
            model_name=model_name,
            model_grade=model_grade,
            temperature=temperature,
            session_id=session_id,
        )

    def reset_session(self, model_grade: str) -> None:
        """重置指定模型等级的 session（触发新 session 创建）。"""
        old_id = self._sessions.pop(model_grade, None)
        if old_id:
            logger.info("session 已重置: %s (model=%s)", old_id, model_grade)

    def get_session_id(self, model_grade: str) -> Optional[str]:
        """获取指定模型等级的当前 session_id。"""
        return self._sessions.get(model_grade)

    def all_session_ids(self) -> Dict[str, str]:
        """返回所有活跃 session: {model_grade: session_id}。"""
        return dict(self._sessions)
