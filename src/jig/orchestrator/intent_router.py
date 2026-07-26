"""意图路由 — HyDE 改写 + Decomp 意图分解。

第 0 层增强：Dispatcher 根据查询复杂度自动分流。
"""

from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


def classify_query(query: str, history_count: int = 0) -> str:
    """按复杂度分类查询。

    Returns:
        simple / complex / multi_turn
    """
    # 多轮：有上下文
    if history_count >= 3:
        return "multi_turn"

    # 长难句：>30 字或有逗号/从句
    if len(query) > 30 or re.search(r"[，,；;。.？?]", query):
        return "complex"

    return "simple"


def hyde_rewrite(query: str) -> str:
    """HyDE 改写 — 生成假想文档用于路由。

    不做 LLM 调用，只用规则扩展关键词。
    """
    expansions = {
        "登录": "用户登录功能，包含身份验证、会话管理",
        "注册": "用户注册功能，包含表单验证、数据持久化",
        "安全": "安全审计、漏洞扫描、渗透测试、CVE 检查",
        "部署": "构建、打包、发布、部署验证、回滚",
        "测试": "单元测试、集成测试、端到端测试、回归测试",
        "API": "API 接口设计、REST 端点、请求/响应格式",
        "数据库": "数据库设计、表结构、查询优化、ORM 映射",
    }
    expanded = query
    for keyword, expansion in expansions.items():
        if keyword in query:
            expanded += f"，涉及{expansion}"
    return expanded


