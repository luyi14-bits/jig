# AgentHarness — 自研多 Agent 编排框架
#
# SPDX-License-Identifier: MIT

"""AgentHarness: 自研多 Agent 编排框架 — 13 个预设角色、4 层记忆、硬约束 Harness。

快速开始:
    from forge import AgentHarness
    app = AgentHarness(skills_dir="./skills")
    result = app.run("帮我做一个登录功能")
    print(result)

核心组件:
- AgentHarness: 框架主入口（公开 SDK API）
- SkillRegistry: 加载和注册 skill 定义
- AgentFactory: 从 skill 定义创建 Agent 实例
- ModelRouter: Pro/Flash 双模型路由
- DeepSeekAdapter: reasoning_content + Function Calling 适配
- CacheEngine: 缓存前缀组装 + 诊断
- ContextPartitioner: 三层上下文分区
"""

from .api import AgentHarness

__all__ = [
    "AgentHarness",
]
