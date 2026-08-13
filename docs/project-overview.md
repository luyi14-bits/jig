# Jig — 项目简述

> 版本 v0.6.3 · Python 3.10+ · MIT License

## 一句话定位

**Jig** 是一个具备"执行前安全门禁"的 Python 多 Agent 编排框架：所有工具调用在**代码层**经过 Agent Firewall（白名单/黑名单/PreToolUse 钩子）后才执行——Agent 自主性靠架构保证，而非提示词约束。

## 核心能力

| 能力 | 说明 |
|------|------|
| 🛡️ **Agent Firewall** | 执行前三层拦截：黑名单 → 白名单 → 钩子，防止越权工具调用 |
| 🧠 **DeepSeek 原生优化** | SHA-256 前缀缓存、Flash 优先成本路由（CostAwareRouter）、Tool-Call Repair、Token 预算熔断 |
| 🤖 **11 个预设 Agent** | PM / Spec / Coding / Acceptance / Security / TDD / DevOps / 秘书 / 导师等，按 SOP 管线协作 |
| 🌐 **多模型 + 流式** | DeepSeek + OpenAI 双 Provider，SSE 流式输出（/stream 端点） |
| 🔄 **Loop Engineering** | 收敛检测（ConvergenceDetector）、质量校验、重试+升级（CircuitBreaker + 漂移检测） |
| 🗄️ **4 层记忆** | append-only / 工作区 / 压缩 / 整合（SQLite 持久化） |
| 🧩 **图编排** | 复杂查询走 GraphOrchestrator 图管道 |
| 🛡️ **HITL 人工审批** | `requires_approval` 节点暂停，`approve/reject` 恢复/跳过 |
| 🔌 **外部 Agent 治理** | MetaHarness 统一管理外部 Agent 接入，A2A 跨框架路由 |
| 🧪 **评测系统** | EvalRunner + 评测集 + `jig eval` 命令，量化 SOP 符合率 |

## 工程指标

- **197/197 测试全绿**，27 个测试文件
- **39 项看板已发布**（6 想法池 / 3 规划中）
- 核心模块 19 个全部可导入，无孤立死代码（9 个已接线）
- 版本治理：v0.6.3（本地）→ 已发布 PyPI v0.6.1（`pip install jig-toolguard`）

## CLI / API

```bash
jig --list                 # 列出所有 Agent
jig --chat                 # 群聊模式
jig --server               # FastAPI 服务 (同步)
jig --server-async         # FastAPI 服务 (异步+队列)
jig eval dataset.json      # 运行评测集
jig --market-list          # 插件市场列表
jig --hitl-status          # 待审批 HITL 查看
```

```python
from jig import Jig
app = Jig(skills_dir="./skills")
result = app.run("帮我分析这个需求")
```

## 生态

- **GitHub**: github.com/luyi14-bits/jig
- **PyPI**: pypi.org/project/jig-toolguard
- **PR #696**: 已提交 deepseek-ai/awesome-deepseek-integration（AI Agent frameworks 分类，含官方 SVG logo）
- **PR #310**: 已提交 deepseek-ai/awesome-deepseek-agent

## 下一步

1. 修复 MetaHarness ClaudeCodeAdapter 递归风险 + ToolGuard 穿透补全
2. 发布 v0.6.3 → PyPI
3. PyPI v1.0 正式发布（文档站点 + 示例库 + 版本治理）
