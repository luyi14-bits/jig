# Jig 框架对比技术报告

> **版本**: Alpha 0.2 | **日期**: 2026-07-22 | **类型**: 自研框架 vs 开源竞品

---

## 0. 摘要

Jig 是一个**自研的 Python 多 Agent 编排框架**，对标 LangGraph / CrewAI / MS Agent FW / PydanticAI / Omnigent。核心差异化在于**硬约束 Harness 层**（ToolGuard 代码级拦截 + LOOP SOP 5 级门禁 + LoopEngine 收敛检测 + CircuitBreaker 熔断）和**四层记忆体系**（CacheEngine → ContextPartitioner → EmbeddingIndex → SQLite）。在硬约束、记忆架构和成本治理上拥有真正的技术壁垒。

---

## 1. 开源 Agent 框架全景（2026-07 更新）

| # | 框架 | Stars | 语言 | 定位 |
|---|------|:-----:|:----:|------|
| 1 | BettaFish | 41.8k | Python | 多Agent舆情分析 |
| 2 | deepagents | 26.6k | Python | "batteries-included agent harness" |
| 3 | Haystack | 26k | Python | LLM 编排管道 |
| 4 | OpenAI Agents SDK | 28k | Python | OpenAI 官方多Agent |
| 5 | PydanticAI | 18.7k | Python | 类型安全 Agent 框架 |
| 6 | MS Agent Framework | 12.3k | Python/.NET | 企业级多Agent编排 |
| 7 | Hive | 10.8k | Python | "Multi-Agent Harness for Production" |
| 8 | Upsonic | 7.9k | Python | 自主 Agent 构建 |
| 9 | Omnigent | 7.6k | Python | Meta-harness，编排外部Agent |
| 10 | Strands harness-sdk | 6.7k | Python/TS | Agent harness SDK |
| 11 | AG2 (AutoGen) | 4.8k | Python | 微软开源 AgentOS |
| 12 | CrewAI | ~55k | Python | 角色团队编排 |
| 13 | LangGraph | ~38k | Python | 图状态机编排 |
| **—** | **Jig** | **—** | **Python** | **自研 Harness 硬约束框架** |

---

## 2. Jig 自研架构

```
Control Plane (Harness): LOOP SOP · ToolGuard · GlobalConstraints · MemoryRouter
Agent Plane:            SkillParser → SkillRegistry → AgentFactory → Agent (13 roles)
Orchestration Plane:   Sequential · Parallel · Hierarchical · Checkpoint · CircuitBreaker
Tool Plane:            MCPClient · ToolGuard · RepoMap · EmbeddingIndex · CacheEngine · DeepSeekAdapter
```

### Harness 硬约束（独有）

| 约束层 | 机制 | 不可绕过 |
|--------|------|:--------:|
| ToolGuard | 白名单/黑名单/PreToolUse hooks | ✅ 代码级拦截 |
| LOOP SOP | 5 级门禁 G0→G4 + 6 条降级规则 | ✅ 门禁不通过不推进 |
| GlobalConstraints | 不可变 immutable prompt 区 | ✅ 无法被 Agent 覆盖 |

### 四层记忆

| 层 | 技术 | 效果 |
|:--:|------|------|
| 1 | CacheEngine | 前缀 hash → DeepSeek 缓存命中 >99% |
| 2 | ContextPartitioner | 不可变区缓存 + 可压缩历史 |
| 3 | EmbeddingIndex | 语义检索 skill 注入 |
| 4 | SQLite + Checkpoint | 跨 session + 断点恢复 |

---

## 3. 核心竞品深度对比

### 3.1 LangGraph / deepagents (26.6k★)

| 维度 | LangGraph | Jig |
|------|-----------|----------------|
| **硬约束** | ❌ prompt-only | ✅ ToolGuard + 门禁 |
| **编排模型** | 图状态机 | SOP 5 级管道 |
| **缓存优化** | ❌ 无 | ✅ DeepSeek 前缀 hash |
| **熔断降级** | Retry policy | ✅ CircuitBreaker + DriftDetector |
| **成本治理** | — | ✅ CostAwareRouter + TokenBudget |
| **记忆架构** | Checkpointer | 4 层 (Cache→Partition→Embedding→SQLite) |
| **外部Agent管控** | ❌ | ✅ Meta-Harness 适配器 |

### 3.2 CrewAI (~55k★)

| 维度 | CrewAI | Jig |
|------|--------|----------------|
| **硬约束** | ❌ prompt-only | ✅ ToolGuard + 门禁 |
| **Skill→Agent** | ❌ 无 | ✅ SKILL.md 自动映射 |
| **缓存优化** | ❌ 无 | ✅ 前缀 hash |
| **角色体系** | 通用可定义 | 13 预设 + 用户挂载 |
| **记忆** | 简单短期 | 四层体系 |
| **MCP** | ✅ Client | ✅ Client + Server |

### 3.3 MS Agent Framework (12.3k★)

| 维度 | MS Agent FW | Jig |
|------|-------------|----------------|
| **硬约束** | ❌ prompt-only | ✅ ToolGuard + 门禁 |
| **编排** | Plugin-based | SOP 5 级管道 |
| **企业治理** | Policy 审批（事后） | ✅ ToolGuard（事前阻断） |
| **缓存优化** | — | ✅ DeepSeek 前缀 hash |
| **记忆** | State | 4 层体系 |
| **License** | MIT | MIT |

### 3.4 PydanticAI (18.7k★)

| 维度 | PydanticAI | Jig |
|------|------------|----------------|
| **硬约束** | ❌ prompt-only | ✅ ToolGuard |
| **结构化输出** | ✅ 原生 Pydantic | ✅ 支持 |
| **多Agent** | ❌ Single | ✅ 13 角色 |
| **缓存优化** | — | ✅ DeepSeek 前缀 hash |
| **记忆** | Context | 4 层体系 |
| **License** | MIT | MIT |

### 3.5 Omnigent (7.6k★) — 最接近的竞品

| 维度 | Omnigent | Jig |
|------|----------|----------------|
| **管控模式** | 事后审批（Policy） | ✅ 事前阻断（ToolGuard） |
| **外部Agent** | ✅ 编排 | ✅ Meta-Harness |
| **缓存优化** | — | ✅ DeepSeek 前缀 hash |
| **熔断** | — | ✅ CircuitBreaker |
| **成本治理** | — | ✅ CostAwareRouter |
| **License** | Apache 2.0 | MIT |

**关键差异**：Omnigent 是"Harness 外挂"——它在 Agent 执行后审批结果。Jig 的 ToolGuard 在工具调用前直接拦截，这是架构级差异，不是配置差异。

### 3.6 AG2 / AutoGen (4.8k★, Microsoft)

| 维度 | AG2 | Jig |
|------|-----|----------------|
| **定位** | 通用 Agent 操作系统 | 框架化编排 |
| **硬约束** | ❌ | ✅ ToolGuard |
| **缓存优化** | — | ✅ DeepSeek 前缀 hash |
| **外部 Agent** | — | ✅ Meta-Harness |
### 3.4 Superpowers (258k★)

| 维度 | Superpowers | Jig |
|------|-------------|----------------|
| **本质** | AI 编程工具插件 | 独立 Python 框架 |
| **运行方式** | Claude Code/Codex 内 | CLI/桌面/后端 |
| **SKILL.md** | ✅ (Inspo 格式) | ✅ (扩展格式) |
| **多 Agent** | ❌ 单 Agent | ✅ 13 角色编排 |
| **硬约束** | ❌ | ✅ |

### 3.5 Mastra (26.4k★)

| 维度 | Mastra | Jig |
|------|-------|----------------|
| **语言** | TypeScript | Python |
| **生态** | 前端全栈 | LLM 深度集成 |
| **角色** | 通用 Agent | 预制 + 自定义 |

### 3.6 Omnigent (7.5k★)

| 维度 | Omnigent | Jig |
|------|----------|--------------|
| **定位** | Meta-harness — 在已有 Agent 外加统一层 | 内置 Harness — 框架自带硬约束 |
| **Agent 来源** | 外部（Claude Code/Codex/Pi） | 自产（13 预设 + Skill 挂载） |
| **硬约束** | Policy 审批（事后拦截） | ToolGuard（**事前**拦截） |
| **Harness 层级** | 外层套壳 | **框架级内置** |
| **编排** | 会话级协作 | SOP 管道 + 5 级门禁 |
| **记忆** | 会话同步 | 四层体系（CacheEngine→SQLite） |

**一句话差异**：Omnigent 是"给别人的 Agent 套缰绳"，Jig 是"自己的 Agent 自带缰绳"。

---

## 4. 关键维度矩阵

| 维度 | CrewAI | MetaGPT | AutoGen | Superpowers | Mastra | LangGraph | **Jig** |
|------|:------:|:-------:|:-------:|:-----------:|:------:|:---------:|:------------:|
| 硬约束层 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ 独有** |
| 门禁机制 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ 独有** |
| 缓存优化 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ 独有** |
| 预设角色 | ❌ | 4 | ❌ | ❌ | ❌ | ❌ | **13** |
| SKILL.md | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | **✅ +挂载** |
| 桌面应用 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ Tauri** |
| AGPL v3 | MIT | MIT | MIT | Apache | MIT | MIT | **✅** |

---

## 5. 差距分析与追赶路线

| 维度 | Jig 现状 | 高星框架 | 差距 | 建议优先级 |
|------|:---:|:--------:|:----:|:----------:|
| GitHub 影响力 | ~0 | Superpowers 258k | 🔴 巨大 | P1 发布 PyPI + 英文 README |
| 社区生态 | 单人 | 数百贡献者 | 🔴 巨大 | P1 开源运营 |
| 文档教程 | 白皮书 + 用户指南 | 完整文档站 | 🟠 大 | P1 MkDocs 文档站 |
| PyPI 发布 | ❌ | 全部已发布 | 🔴 必须做 | **P0** |
| CI/CD | ❌ | 全部有 | 🔴 必须做 | P0 GitHub Actions |
| 插件/MCP 生态 | 基础 | 数百 MCP | 🟠 大 | P2 对接 MCP Hub |
| 测试覆盖 | 47 | 数百 | 🟡 中 | P2 扩展 CI |
| 硬约束 Harness | ✅ **独有** | 无 | 🟢 **领先** | 核心卖点 |
| 记忆体系 | ✅ **四层** | 简单 | 🟢 **领先** | 同上 |
| 桌面应用 | ✅ **Tauri** | 无 | 🟢 **领先** | 差异化亮点 |

### 关键发现

1. **Superpowers 增长 3 倍**（76k→258k）：说明 AI 编程工具(Skill→Agent)方向市场验证成功。但 Tree-SOP 定位不同——它是独立框架而非插件。
2. **Mastra 崛起**（0→26.4k）：说明 TypeScript Agent 框架有市场需求。Tree-SOP 是 Python 原生，两者市场区隔，但也说明 Agent 框架赛道在快速膨胀。
3. **MetaGPT 停滞**：最后更新 Jan 2026，说明软件开发固定 pipeline 的框架竞争激烈。Tree-SOP 的可挂载 SKILL.md 体系是差异化方向。

---

## 6. 结论

Jig 在**技术架构**上有真实壁垒（硬约束 Harness 独一无二），但在**社区影响力**上几乎为零。建议按此优先级追赶：

1. **P0**：PyPI 发布 + GitHub Actions CI → 解决"装不了/测不了"问题
2. **P1**：英文 README + MkDocs 文档站 → 解决"看不懂"问题
3. **P1**：发布对比博文到 Hacker News / Reddit → 解决"没人知道"问题
4. **P2**：对接 MCP Hub 生态 → 解决"插件太少"问题

**竞争定位建议**：不打"另一个多 Agent 框架"牌，而是打 **"唯一拥有硬约束 Harness 的多 Agent 框架"**。这是所有高星框架都没有的能力。

---

*本报告基于 Alpha 0.2 版本。框架数据采集于 2026-07-17。*
