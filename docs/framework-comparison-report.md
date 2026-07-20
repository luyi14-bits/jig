# AgentHarness 框架对比技术报告

> **版本**: Alpha 0.2 | **日期**: 2026-07-17 | **类型**: 自研框架 vs 开源竞品

---

## 0. 摘要

AgentHarness 是一个**自研的 Python 多 Agent 编排框架**，直接对标 CrewAI / MetaGPT / AutoGen / Superpowers。核心差异化在于**硬约束 Harness 层**（ToolGuard 三层拦截 + LOOP SOP 5 级门禁）和**四层记忆体系**（CacheEngine → ContextPartitioner → EmbeddingIndex → SQLite）。在硬约束和记忆架构上拥有真正的技术壁垒，但在 GitHub 影响力和社区生态上差距显著。

---

## 1. 开源 Agent 框架全景（2026-07）

| 框架 | Stars | 语言 | 定位 | 趋势 |
|------|:----:|:----:|------|:----:|
| Superpowers | 258k | TS/JS | 技能驱动 AI 编程 | 🔥 爆发 |
| LangChain | 142k | Python | LLM 应用平台 | 📈 持续 |
| MetaGPT | 69.4k | Python | 软件公司模拟 | 📈 稳定 |
| AutoGen | 59.8k | Python | 多 Agent 对话 | 📈 微软支持 |
| CrewAI | 55.8k | Python | 角色编排 | 📈 快速增长 |
| LangGraph | 37.7k | Python | 图状态机编排 | 📈 |
| OpenAI Agents SDK | 28k | Python | OpenAI 官方 Agent | 📈 |
| Mastra | 26.4k | TypeScript | TS Agent 框架 | 🆕 新星 |
| Swarm | 21.8k | Python | OpenAI 轻量实验 | 📈 |
| elizaOS | 18.8k | TS | AI Agent 框架 | 🆕 |
| PydanticAI | 18.7k | Python | Pydantic Agent | 📈 |
| CAMEL | 17.4k | Python | 角色扮演 | 🆕 |
| Microsoft Agent FW | 12.2k | C#/TS | 微软官方 | 🆕 |
| **AgentHarness** | **—** | **Python** | **自研多 Agent** | **🚧 新项目** |

---

## 2. AgentHarness 自研架构

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

### 3.1 CrewAI (55.8k★)

| 维度 | CrewAI | AgentHarness |
|------|--------|----------------|
| **硬约束** | ❌ prompt-only | ✅ ToolGuard + 门禁 |
| **Skill→Agent** | ❌ 无 | ✅ SKILL.md 自动映射 |
| **缓存优化** | ❌ 无 | ✅ 前缀 hash |
| **角色体系** | 通用可定义 | 13 预设 + 用户挂载 |
| **记忆** | 简单短期 | 四层体系 |
| **桌面** | ❌ | ✅ Tauri v2 |

### 3.2 MetaGPT (69.4k★)

| 维度 | MetaGPT | AgentHarness |
|------|---------|----------------|
| **角色** | 4 个固定 | 13 预设 + 可扩展 |
| **SOP** | 硬编码 pipeline | 多模式编排 |
| **自定义 Skill** | ❌ 不支持 | ✅ SKILL.md 挂载 |
| **维护状态** | Jan 21 后停滞 | 活跃开发 |
| **硬约束** | ❌ | ✅ |

### 3.3 AutoGen (59.8k★, Microsoft)

| 维度 | AutoGen | AgentHarness |
|------|---------|----------------|
| **定位** | 通用对话路由 | 软件开发专用 |
| **预设角色** | ❌ 需自建 | ✅ 13 个 |
| **Harness** | ❌ | ✅ |
| **记忆** | 对话历史 | 四层分层 |

### 3.4 Superpowers (258k★)

| 维度 | Superpowers | AgentHarness |
|------|-------------|----------------|
| **本质** | AI 编程工具插件 | 独立 Python 框架 |
| **运行方式** | Claude Code/Codex 内 | CLI/桌面/后端 |
| **SKILL.md** | ✅ (Inspo 格式) | ✅ (扩展格式) |
| **多 Agent** | ❌ 单 Agent | ✅ 13 角色编排 |
| **硬约束** | ❌ | ✅ |

### 3.5 Mastra (26.4k★)

| 维度 | Mastra | AgentHarness |
|------|-------|----------------|
| **语言** | TypeScript | Python |
| **生态** | 前端全栈 | LLM 深度集成 |
| **角色** | 通用 Agent | 预制 + 自定义 |

---

## 4. 关键维度矩阵

| 维度 | CrewAI | MetaGPT | AutoGen | Superpowers | Mastra | LangGraph | **AgentHarness** |
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

| 维度 | AgentHarness 现状 | 高星框架 | 差距 | 建议优先级 |
|------|:---:|:--------:|:----:|:----------:|
| GitHub 影响力 | ~0 | Superpowers 258k | 🔴 巨大 | P1 发布 PyPI + 英文 README |
| 社区生态 | 单人 | 数百贡献者 | 🔴 巨大 | P1 开源运营 |
| 文档教程 | 白皮书 | 完整文档站 | 🟠 大 | P1 MkDocs 文档站 |
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

AgentHarness 在**技术架构**上有真实壁垒（硬约束 Harness 独一无二），但在**社区影响力**上几乎为零。建议按此优先级追赶：

1. **P0**：PyPI 发布 + GitHub Actions CI → 解决"装不了/测不了"问题
2. **P1**：英文 README + MkDocs 文档站 → 解决"看不懂"问题
3. **P1**：发布对比博文到 Hacker News / Reddit → 解决"没人知道"问题
4. **P2**：对接 MCP Hub 生态 → 解决"插件太少"问题

**竞争定位建议**：不打"另一个多 Agent 框架"牌，而是打 **"唯一拥有硬约束 Harness 的多 Agent 框架"**。这是所有高星框架都没有的能力。

---

*本报告基于 Alpha 0.2 版本。框架数据采集于 2026-07-17。*
