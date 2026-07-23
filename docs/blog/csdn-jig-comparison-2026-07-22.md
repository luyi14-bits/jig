---
copyright: true
author: luyi14-bits
date: 2026-07-22
---

# 2026 Agent 框架选型指南 — LangGraph vs CrewAI vs PydanticAI vs Jig

> 四个框架，四种设计哲学。没有绝对最好的，只有最合适的。本文从安全、编排、记忆、成本、扩展性五个维度横评，帮你选对框架。

---

## 一、全景概览

| 维度 | LangGraph | CrewAI | PydanticAI | **Jig** |
|------|:---------:|:------:|:----------:|:-------:|
| **Stars** | 37k+ | 55k+ | 18k+ | — |
| **发布时间** | 2024 | 2023 | 2024 | 2026 |
| **核心隐喻** | 图状态机 | 角色团队 | 类型安全 | 硬约束 Harness |
| **语言** | Python/JS | Python | Python | Python/TS(规划)/Rust(规划) |
| **开源协议** | MIT | MIT | MIT | MIT |

---

## 二、安全维度：唯一有代码级事前拦截的框架

这是 Jig 和所有竞品之间**最本质的差异**。

| 能力 | LangGraph | CrewAI | PydanticAI | **Jig** |
|------|:---------:|:------:|:----------:|:-------:|
| 工具调用拦截时机 | ❌ 事后 | ❌ 事后 | ❌ 事后 | ✅ **事前** |
| 拦截实现方式 | prompt-only | prompt-only | prompt-only | ✅ **代码级** |
| 白名单/黑名单 | ❌ | ❌ | ❌ | ✅ **ConfigManager 配置** |
| PreToolUse 钩子 | ❌ | ❌ | ❌ | ✅ **自定义回调** |
| 断路器 | ❌ | ❌ | ❌ | ✅ **三态熔断** |
| 漂移检测 | ❌ | ❌ | ❌ | ✅ **语义漂移监控** |

**LangGraph** 的约束全部写在节点 prompt 里——"不要删除文件"，Agent 完全可以忽略。  
**CrewAI** 同理，Guardrails 是可选插件，不在核心。  
**PydanticAI** 有 `@agent.tool_validator`——运行时校验，不是执行前拦截。  
**Jig 的 ToolGuard** 在工具调用真正执行之前就拦截了。三层检查（白名单 → 黑名单 → PreToolUse 钩子）全部在代码层，Agent 绕不过去。

如果你需要 Agent 执行环境的安全保障——Jig 是唯一选择。

---

## 三、编排维度：图 vs 角色 vs 类型 vs 管道

| 能力 | LangGraph | CrewAI | PydanticAI | **Jig** |
|------|:---------:|:------:|:----------:|:-------:|
| 核心模型 | 有向图 | 顺序/层级 | 单一 Agent | 混合管道 |
| 条件路由 | ✅ 原生 | ❌ | ❌ | ✅ GraphOrchestrator |
| 并行执行 | ✅ | ✅ | ❌ | ✅ |
| 自环/循环 | ✅ | ❌ | ❌ | ✅ LoopEngine |
| 预设角色 | ❌ 需自建 | ✅ 通用 | ❌ 单一 | ✅ 12 个行业角色 |
| 自定义 Agent | ✅ 节点函数 | ✅ Agent 类 | ✅ @agent 装饰器 | ✅ SKILL.md 文件 |

**怎么选**：

- 你的工作流是复杂图结构，需要条件分支 + 并行 + 自环 → **LangGraph**
- 你只需要简单的角色团队聊天 → **CrewAI**
- 你只需要一个带类型校验的单 Agent → **PydanticAI**
- 你想要开箱即用的完整开发管道（PM → Spec → Coding → Review → TDD → 验收 → 安全审计） → **Jig**

---

## 四、记忆维度：谁记得最久

| 能力 | LangGraph | CrewAI | PydanticAI | **Jig** |
|------|:---------:|:------:|:----------:|:-------:|
| 短期记忆 | ✅ 对话历史 | ✅ 对话历史 | ✅ 上下文 | ✅ append-only |
| 工作区记忆 | ✅ Checkpoint | ❌ | ❌ | ✅ ContextPartitioner |
| 语义记忆 | ❌ | ❌ | ❌ | ✅ EmbeddingIndex |
| 持久化 | ✅ SQLite/Postgres | ❌ | ❌ | ✅ SQLite |
| 缓存优化 | ❌ | ❌ | ❌ | ✅ SHA-256 前缀哈希 |
| 压缩策略 | ❌ | ❌ | ❌ | ✅ summarize/truncate/hybrid |

LangGraph 的 Persistent 层只保存状态快照，不跨 session。CrewAI 和 PydanticAI 根本没有记忆体系——每次对话从零开始。

Jig 的 4 层记忆体系是唯一兼顾短期+长期+语义+持久化的方案。

---

## 五、成本维度：谁帮你省钱

| 能力 | LangGraph | CrewAI | PydanticAI | **Jig** |
|------|:---------:|:------:|:----------:|:-------:|
| 模型路由 | ❌ 手动选 | ❌ 手动选 | ❌ 手动选 | ✅ Flash/Pro 自动 |
| Token 预算 | ❌ | ❌ | ❌ | ✅ Session+月度 |
| 费用估算 | ❌ | ❌ | ❌ | ✅ 实时统计 |
| 缓存节省 | ❌ | ❌ | ❌ | ✅ 2%费用 |
| 断路器(防止超支) | ❌ | ❌ | ❌ | ✅ 超限熔断 |

**数据参考**：使用 Jig 的 Flash-first 策略 + SHA-256 前缀缓存，典型场景可降低 60-70% API 费用。

---

## 六、外部集成维度

| 能力 | LangGraph | CrewAI | PydanticAI | **Jig** |
|------|:---------:|:------:|:----------:|:-------:|
| MCP 协议 | ✅ Client | ✅ Client | ❌ | ✅ **Client + Server** |
| A2A 协议 | ❌ | ✅ 实验性 | ❌ | ✅ **支持** |
| 外部 Agent 管控 | ❌ | ❌ | ❌ | ✅ **Meta-Harness** |
| VisionTool | ❌ | ❌ | ❌ | ✅ **插件，免费本地** |

Jig 在外部集成上的优势来自它的 Harness 架构——外部 Agent 的工具调用同样经过 ToolGuard 拦截。LangGraph 和 CrewAI 没有这个能力。

---

## 七、选型建议

| 你的场景 | 推荐框架 |
|---------|---------|
| 复杂图工作流 | **LangGraph** |
| 快速搭建角色团队 | **CrewAI** |
| 类型安全的单 Agent | **PydanticAI** |
| **安全的 Agent 执行环境** | **Jig** — 唯一选项 |
| DeepSeek 深度优化 | **Jig** — 其他框架没做 |
| 全链路 SOP 管道 | **Jig** — 开箱即用 |
| 低 API 成本 | **Jig** — 成本路由 + 缓存 |

---

## 八、总结

四个框架不完全是竞争关系——它们在设计哲学上有根本差异：

- **LangGraph** 是最好的图编排引擎
- **CrewAI** 是上手最快的角色团队框架
- **PydanticAI** 是类型安全和结构化输出的标杆
- **Jig** 是**唯一在代码级实现事前安全拦截**的框架，且 DeepSeek 优化、4 层记忆、成本治理、外部 Agent 管控都是独占能力

**选择框架不是选功能最多的，是选最契合你场景的。**

> Jig 开源地址：[https://github.com/luyi14-bits/jig](https://github.com/luyi14-bits/jig)  
> 如果这篇对比对你有帮助，欢迎 Star ⭐

**作者**：luyi14-bits | **协议**：MIT
