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


def decomp_intent(query: str, context: List[str]) -> List[Dict[str, str]]:
    """Decomp 意图分解 — 将多轮复杂需求拆为子意图。

    Args:
        query: 当前用户输入
        context: 历史对话（最近几轮）

    Returns:
        子意图列表：[{"agent": "pm", "task": "..."}, ...]
    """
    sub_intents = []

    # 关键词匹配拆解
    if "登录" in query or "注册" in query:
        sub_intents.append({"agent": "pm", "task": f"需求分析: {query}"})
        sub_intents.append({"agent": "spec", "task": f"任务拆分: 登录/注册模块"})
        sub_intents.append({"agent": "security", "task": "安全审计: 身份验证流程"})

    if "管理" in query or "后台" in query:
        sub_intents.append({"agent": "pm", "task": f"管理后台需求: {query}"})
        sub_intents.append({"agent": "coding", "task": "实现管理后台功能"})

    if "数据库" in query or "存储" in query:
        sub_intents.append({"agent": "spec", "task": "数据库设计"})
        sub_intents.append({"agent": "coding", "task": "实现数据持久化"})

    if "部署" in query or "发布" in query:
        sub_intents.append({"agent": "devops", "task": "构建部署流程"})
        sub_intents.append({"agent": "security", "task": "部署安全审查"})

    if not sub_intents:
        sub_intents.append({"agent": "pm", "task": f"需求分析: {query}"})

    return sub_intents
