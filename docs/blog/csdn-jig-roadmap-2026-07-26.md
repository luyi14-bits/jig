---
copyright: true
top: false
author: luyi14-bits
date: 2026-07-26
updated: 2026-07-26
tags: [Agent, 架构, 路线图, Jig, ToolGuard]
---

# Jig 技术路线：从 Agent 编排框架到预执行安全门禁

> 2026 年的 Agent 框架赛道已经拥挤不堪——LangGraph 37k★、CrewAI 55k★、PydanticAI 18k★，巨头 OpenAI 和 LangChain 也在争相定义 "Harness"。
> Jig 选择了一条不一样的路：**不做"又一个编排框架"，而是做 Agent 防火墙。**

---

## 一、起点：为什么不做"又一个 LangGraph"

2026 年初规划 Jig 时，Agent 框架有三大类：

- **编排型**: LangGraph、CrewAI——定义如何连接 Agent
- **SDK 型**: OpenAI Agents SDK、PydanticAI——定义如何调用 LLM
- **工具型**: MCP 协议、A2A 协议——定义如何对接工具

再做一套编排框架，用户凭什么选？答案是**安全**。

所有竞品的安全机制都停在 prompt 层面——靠"劝"不靠"拦"。deepagents 自己承认：*"trust the LLM" model.* 翻译成人话：Agent 想干什么就干什么，安全边界全靠 prompt 劝说。

于是 Jig 的路线图锚定了一个不同的问题：

> **我们不给 Agent 更多能力——我们给 Agent 安上"事前拦截"的安全门禁。**

---

## 二、路线图全景

```
v0.1         v0.2         v0.4         v0.5         v0.6         未来
 │            │            │            │            │            │
 ▼            ▼            ▼            ▼            ▼            ▼
Skill→Agent  Memory+     Circuit-     Multi-Model  Graph+        Meta-
Mapping      Config      Breaker      +Streaming   Durable       Harness
+ToolGuard   +Context    +Drift       +CostRouter  +LoopEngine   +PyPI
             +SQLite     +RiskMode                            +Docs
```

### Phase 1-2：奠基（v0.1.0）

**核心交付**：Skill→Agent 映射 + DeepSeek 双模型

关键决策：**SKILL.md 声明式 Agent 定义**。用 Markdown frontmatter 而非 Python 类：

```yaml
# skills/my-agent/SKILL.md
---
name: my-agent
description: "安全审计 Agent"
model: pro
tools: [read, grep, search]
---
```

每一行 YAML 自动翻译成一个 Agent。非开发者的 PM 也能写配置。

同时，**ToolGuard 在 v0.1 就定型了**——工具调用前用代码拦截，而非事后 prompt 审查：

```python
class ToolGuard:
    WHITELIST = {"pm": ["Read", "Grep"], "coding": ["Write", "Bash"]}
    DENYLIST = ["Bash(rm -rf /)"]
    
    @classmethod
    def check(cls, role, tool) -> bool: ...  # 代码级阻断
```

这个接口从 v0.1 至今一行未改——这是 Jig 最引以为豪的设计稳定性。

### Phase 3-4：编排调度（v0.2.0）

**核心交付**：并行编排 + 检查点 + FastAPI + cache-guard

关键决策：**Checkpoint 优先于 Durable Execution**。在实现"长时间运行"之前，先保证"崩溃可恢复"。每个节点执行后自动保存 checkpoing：

```python
self._save_checkpoint(SOPCheckpoint(
    session_id=session_id,
    current_node_idx=idx + 1,
    completed_nodes=list(completed),
))
```

### Phase 5：全管道自闭环（v0.4.0）

**核心交付**：MCP 协议 + ToolGuard 三层硬约束 + DevOps Agent

管道从 PM → Spec → Coding → Acceptance 四节点打通。每个 Agent 真实调用 DeepSeek API。

### Phase 6-8：安全与记忆（vA.0.2-3）

**核心交付**：Memory 四层体系 + CircuitBreaker + 风险模式

四层记忆的设计（Cache→Partition→Embedding→SQLite），每层解决一个不同的问题：

| 层 | 技术 | 解决的问题 |
|:---:|------|-----------|
| 1 Cache | DeepSeek 前缀缓存 | 最近 N 轮对话，零开销 |
| 2 Partition | 时间窗口分区 | 长对话自动归档 |
| 3 Embedding | 向量索引 | 语义找回历史信息 |
| 4 SQLite | 持久化存储 | 跨 Session 记忆 |

CircuitBreaker 的三态熔断是真正的生产级安全防护：

```
CLOSED → (连续3次失败) → OPEN → (超时) → HALF_OPEN → (成功) → CLOSED
```

### Phase 9：多模型 + 流式（v0.5.0）

**核心交付**：OpenAIProvider + SSE 流式 + CostAwareRouter

这是关键转折——Jig 从 DeepSeek-only 扩展到多模型。架构采用"先 DeepSeek 后泛化"的策略：

```python
class BaseModelProvider:
    def chat(self, messages, **kw) -> ModelResponse: ...
    def chat_stream(self, messages, **kw) -> Iterator[StreamChunk]: ...

class DeepSeekProvider(BaseModelProvider): ...  # 极致优化
class OpenAIProvider(BaseModelProvider): ...    # 兼容扩展
```

接口只有 2 个方法。够用，不冗余。

### Phase 10：图编排 + 收敛引擎（v0.6.0）

**核心交付**：GraphOrchestrator + LoopEngine + SOPRunner

条件路由、并行分支、自环——GraphOrchestrator 让 SOP 管道从线性变为 DAG：

```python
GraphEdge("analyze", "approve", condition=is_complex)
GraphEdge("analyze", "skip", condition=is_simple)
```

LoopEngine 的收敛检测解决了 Agent 最常见的 bug——**停不下来**：

```python
class ConvergenceDetector:
    def is_converged(self) -> bool:
        if len(self._scores) < 3:
            return False
        return all(s >= self._threshold for s in self._scores[-3:])
```

---

## 三、技术架构

```
Agent Firewall (Control Plane):  ToolGuard · LOOP SOP · GlobalConstraints · CircuitBreaker
Agent Plane:                     SkillParser → SkillRegistry → AgentFactory → Agents
Orchestration Plane:             SOPRunner · Graph · LoopEngine · Memory · Checkpoint
Tool Plane:                      MCP · ModelRouter · CacheEngine · CostAwareRouter · Streaming
```

四层架构，每层职责明确。Agent 防火墙层（Control Plane）是 Jig 与所有竞品的核心差异。

---

## 四、竞品对比

| 维度 | deepagents | OpenAI SDK | LangGraph | CrewAI | PydanticAI | **Jig** |
|------|:----------:|:----------:|:---------:|:------:|:----------:|:-------:|
| 事前安全拦截 | ❌ "trust LLM" | ❌ | ❌ | ❌ | ❌ | ✅ **代码级** |
| 硬约束 | ❌ prompt-only | ❌ prompt-only | ❌ | ❌ | ❌ | ✅ **白名单+黑名单** |
| DeepSeek 缓存 | — | — | — | — | — | ✅ **SHA-256** |
| 外部 Agent 治理 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **Meta-Harness** |
| 收敛检测 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **LoopEngine** |

---

## 五、当前状态

- **版本**: v0.6.0（124 测试全绿）
- **已发布**: 37 项 IDEA
- **预置 Agent**: 11 个（PM / Spec / Coding / Review / TDD / Acceptance / Security / DevOps / Secretary / Trinity / LOOP SOP）
- **包名**: `pip install jig-toolguard`（PyPI），`from jig import Jig`（导入）
- **GitHub**: `github.com/luyi14-bits/jig`

---

## 六、未来规划

### 近期（Next）

| IDEA | 内容 |
|:----:|------|
| Meta-Harness | 外部 Agent 治理层——用 Jig 的 ToolGuard 管控 Claude Code、Codex |
| PyPI 发布 | 正式发布到 PyPI |
| 文档站 | MkDocs 完整部署到 GitHub Pages |

### 远期（Later）

| IDEA | 内容 |
|:----:|------|
| Durable Execution | 中断恢复 + 长时间运行 |
| Graph 工作流 | 图编排增强 |
| OTel | 可观测性 |
| Evals | Agent 评测系统 |

---

## 七、开源

Jig 完全开源（MIT 协议）。如果你对 Agent 安全感兴趣，欢迎：

- **GitHub**: `github.com/luyi14-bits/jig`
- **安装**: `pip install jig-toolguard`
- **文档站**: 建设中

---

*Jig 不是一个"又一个 Agent 框架"。它是所有框架都选择 "trust the LLM" 的时候，唯一选择了 "verify before execute" 的那个。*
