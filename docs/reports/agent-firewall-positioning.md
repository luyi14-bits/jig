# Agent Firewall — Jig 定位白皮书

> **版本**：v1.0  
> **日期**：2026-07-23  
> **状态**：战略定位文档

---

## 1. 为什么是 "Agent Firewall" 而不是 "Agent Framework"

当前市场把 "Harness" 定义成 Agent 编排的便利层。**但便利不等于安全。**

当 deepagents、OpenAI Agents SDK 说 "harness" 时，它们的"安全"停留在 prompt 级别：

```python
# deepagents / OpenAI — 所谓的安全只是一句 prompt
"You should not delete files..."
# → Agent 可以完全忽略这条指令
```

而 Jig 的 ToolGuard 是在**工具执行前用代码拦截**的架构级安全：

```python
# Jig — 代码级不可绕过
from jig import ToolGuard
if not ToolGuard.check("bash", "rm -rf /"):
    raise BlockedError("拦截")
```

**这不是"更好的 Agent 框架"——这是一个新品类：Agent Firewall。**

---

## 2. 市场格局：巨头的盲区

| 项目 | 安全机制 | 级别 | 可否绕过 |
|------|---------|:----:|:--------:|
| deepagents | Prompt 约束 | Prompt | ✅ 可绕过 |
| OpenAI Agents SDK | Guardrails (prompt) | Prompt | ✅ 可绕过 |
| LangGraph | 无 | — | — |
| CrewAI | 无 | — | — |
| Pydantic AI | 无 | — | — |
| **Jig ToolGuard** | **代码级事前拦截** | **Code** | **❌ 不可绕过** |

**核心洞察**：没有人承认"prompt 级别的安全不是真安全"。Jig 不争"谁的框架更好"——在 Agent 安全这件事上，其他框架根本没有立场。

---

## 3. Jig 的三层防线

### 第一层：ToolGuard（事前拦截）
- 白名单/黑名单规则引擎
- MCP 调用级别的权限控制
- Bash、文件系统、网络请求三域隔离

### 第二层：Loop SOP（过程管控）
- 5 级门禁（PRD→Spec→Tasks→Code→Acceptance）
- 收敛检测：死循环/质量退化自动停
- Checkpoint 保存/恢复

### 第三层：CircuitBreaker + DriftDetector（熔断+偏移检测）
- 连续失败自动熔断
- 输出模式偏移检测（突然开始输出代码而非文本）

这三层合在一起，构成一个**完整的 Agent 执行安全体系**——在工具执行前拦截，在执行中管控，在执行后检测。

---

## 4. 战略杠杆：Meta-Harness

Jig 的内置 Agent 很好，但最有战略价值的不是"让用户在 Jig 内用 Agent"——而是**让用户在任何 Agent 框架上使用 Jig 的安全层**。

Meta-Harness（IDEA-049）将实现：
- `ToolGuard + Claude Code` — 给 Anthropic 的 Agent 加安全层
- `ToolGuard + Codex` — 给 OpenAI 的 Agent 加安全层
- `ToolGuard + Cursor` — 给 Cursor 的 Agent 加安全层

这样 Jig 不需要在任何 Agent 框架的赛道中竞争——它成为**所有 Agent 的共享安全层**。

---

## 5. 竞品对比

| 维度 | deepagents | OpenAI SDK | LangGraph | CrewAI | **Jig** |
|------|:----------:|:----------:|:---------:|:------:|:-------:|
| Pre-execution Safety | ❌ | ❌ | ❌ | ❌ | **✅ ToolGuard** |
| Multi-Model | ✅ | ❌(仅OpenAI) | ✅ | ✅ | **✅** |
| Graph Orchestration | ✅ | ✅ | ✅ | ❌ | **✅** |
| Streaming | ✅ | ✅ | ❌ | ❌ | **✅** |
| Loop Convergence | ❌ | ❌ | ❌ | ❌ | **✅ LOOP SOP** |
| Durable Execution | ❌ | ❌ | ✅ | ❌ | **⚠️ WIP** |
| DeepSeek Optimization | ❌ | ❌ | ❌ | ❌ | **✅ 原生** |
| External Agent Adapter | ❌ | ❌ | ❌ | ❌ | **⚠️ WIP** |

---

## 6. 一句话定位

> **Jig is the Agent Firewall. Intercept before they act.**

Pipeline:
> "Your agents can now promise safety. Ours can prove it."
