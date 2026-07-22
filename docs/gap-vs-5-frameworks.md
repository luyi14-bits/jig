# Jig vs 5 Frameworks — 缺失清单

> 不看 Jig 有什么，看 Jig 缺什么。
> 对比对象：LangGraph / CrewAI / PydanticAI / MS Agent FW / Omnigent

---

## 🔴 致命缺失（框架不成立）

### 1. 多模型支持

| 谁有 | 支持情况 |
|------|---------|
| LangGraph | OpenAI / Anthropic / Google / AWS / Azure / Ollama / 20+ |
| PydanticAI | OpenAI / Anthropic / Google / Gemini / Mistral / 20+ |
| MS Agent FW | OpenAI / Azure / HuggingFace / 自定义 |
| CrewAI | OpenAI / Ollama / Azure / Google / 10+ |
| Omnigent | OpenAI / Anthropic / Google |
| **Jig** | ❌ **只有 DeepSeek** |

> **诊断**：`ModelRouter` 路由逻辑写死了 Pro/Flash 两种 DeepSeek 型号。没有 LLM Provider 抽象层。
> **根因**：IDEA-037 ("DS深度优化包") 的策略——先做 DeepSeek，多模型延后到 v2。但这个延后让 Jig 在多模型支持上为零。
> **修复方向**：需要 LLM Provider 抽象接口（`BaseLLM` → `DeepSeekProvider` / `OpenAIProvider` / `AnthropicProvider`），约 2 周。

### 2. 流式输出

| 谁有 | 说明 |
|------|------|
| LangGraph | 原生 streaming |
| CrewAI | `stream=True` 参数 |
| PydanticAI | `async def run_stream()` |
| MS Agent FW | `StreamingResponse` |
| Omnigent | ❌ |
| **Jig** | ❌ **`run()` 返回纯字符串** |

> **诊断**：整个 SOP 管道是同步阻塞的。`Dispatcher.handle()` 返回完整字符串，没有任何 `yield` 或 `async generator` 出口。
> **根因**：缺少 `StreamingOrchestrator` 和异步执行路径。`async_app.py` 虽然存在但只是 FastAPI 壳，内部仍是同步。
> **修复方向**：给 `Dispatcher` 加 `stream()` 方法 + SOP 节点级 `yield`，约 1 周。

### 3. 文档站点

| 谁有 | 说明 |
|------|------|
| LangGraph | langgraph.dev |
| CrewAI | docs.crewai.com |
| PydanticAI | pydantic.ai |
| MS Agent FW | learn.microsoft.com |
| Omnigent | ❌ |
| **Jig** | ❌ **只有 README + 白皮书** |

> **诊断**：没有 `jig.dev` 或 GitHub Pages 文档站。开发者无法搜索 API 参考、Quick Start、示例。
> **根因**：一直没排上优先级。IDEA-042 在想法池等 Spec。
> **修复方向**：MkDocs + GitHub Pages，把 docstrings 发布为 API 参考，约 3 天。

---

## 🟡 重大缺失（有它才算正经框架）

### 4. Durable Execution

| 谁有 | 说明 |
|------|------|
| LangGraph | 检查点 + 状态持久化 |
| PydanticAI | Run steps 持久化 |
| MS Agent FW | Conversation state 持久化 |
| CrewAI | ❌ |
| Omnigent | ❌ |
| **Jig** | ❌ **CheckpointManager 只存在于 LoopEngine 内部** |

> **诊断**：`CheckpointManager` 只有 LoopEngine 在用，且检查点生命周期仅限于 Loop 运行时。SOP 管道级没有持久化——崩溃后整体丢。
> **修复方向**：提升 CheckpointManager 到框架级，所有 SOP 管道节点执行后自动保存，约 1 周。

### 5. Graph 工作流

| 谁有 | 说明 |
|------|------|
| LangGraph | **核心卖点**：图状态机 |
| PydanticAI | `agent.run()` + DAG |
| MS Agent FW | 条件状态机 |
| CrewAI | ❌ |
| Omnigent | ❌ |
| **Jig** | ❌ **只有顺序/并行/层级三种硬编码模式** |

> **诊断**：`SequentialOrchestrator` / `ParallelOrchestrator` / `HierarchicalOrchestrator` 都是预设模式，没有给外部开发者自定义工作流的接口。要加自环、条件分支、递归节点需要改框架代码。
> **根因**：2026 年做 Agent 框架不做 Graph 工作流，就像做 Web 框架不支持路由。
> **修复方向**：GraphOrchestrator（节点 = Agent，边 = 条件/上下文/超时），约 2 周。

### 6. OTel 可观测性

| 谁有 | 说明 |
|------|------|
| LangGraph | LangSmith 全链路追踪 |
| PydanticAI | Logfire 集成 |
| MS Agent FW | 原生 OTel |
| CrewAI | ❌ |
| Omnigent | ❌ |
| **Jig** | ❌ **零可观测性** |

> **诊断**：没有 Trace/Metrics/Logging 体系。所有执行信息通过 logger 输出到 stdout，没有结构化数据。
> **根因**：IDEA-038 在想法池（等待 Spec）。
> **修复方向**：OpenTelemetry SDK 接入 + Agent/Tool/Memory/Harness 4 类 Span，约 1 周。

### 7. Human-in-the-Loop

| 谁有 | 说明 |
|------|------|
| LangGraph | `interrupt_before` / `interrupt_after` |
| PydanticAI | `human_confirm()` |
| MS Agent FW | 审批中间件 |
| CrewAI | ❌ |
| Omnigent | ❌ |
| **Jig** | ❌ |

> **诊断**：Pipeline 是全自动的。Agent 决策没有暂停/审批/修改/否决的介入点。IDEA-040 在想法池等 Spec。
> **修复方向**：增加 `interrupt()` API + 审批回调 + 修改/否决/补充信息端点，约 1 周。

### 8. Evals 系统

| 谁有 | 说明 |
|------|------|
| LangGraph | LangSmith evals |
| PydanticAI | **核心卖点**：`@agent.tool_validator` |
| MS Agent FW | Test harness |
| CrewAI | ❌ |
| Omnigent | ❌ |
| **Jig** | ❌ |

> **诊断**：没有评估框架输出质量的机制。测试覆盖是单元测试（62），不是 Agent 行为评估。
> **修复方向**：Agent 输出质量自动评估（结合 LoopEngine 的 QualityValidator），约 3 天。

---

## 🟢 有了更好，没有也能活

### 9. 声明式 Agent 定义

| 谁有 | 说明 |
|------|------|
| PydanticAI | `@agent.tool` + `agent.run()` 声明式 |
| MS Agent FW | YAML Agent 定义 |
| **Jig** | ❌ **只有 SKILL.md 文件方式** |

> **说明**：SKILL.md 方式对框架用户来说其实够用了。声明式 YAML 可以锦上添花，不是必须品。

### 10. 多语言 SDK

| 谁有 | 说明 |
|------|------|
| LangGraph | Python + JavaScript |
| MS Agent FW | Python + .NET |
| **Jig** | ❌ **只有 Python** |

> **说明**：站稳 Python 后再加语言。不急于一时。

### 11. 社区（Discord / Slack / Forum）

| 谁有 | 说明 |
|------|------|
| 全都有（除了 Omnigent） | 客服 + 用户交流 |
| **Jig** | ❌ |

> **说明**：有人用再建社区。

---

## 总结：Jig 唯一真实的壁垒

| 维度 | Jig | 5 个对手 |
|------|:---:|:---------:|
| ToolGuard 硬约束 | ✅ **独有** | ❌ 全是 prompt-only |
| DeepSeek 缓存优化 | ✅ **独有** | ❌ 没人专门做 |
| Loop 收敛引擎 | ✅ **独有** | ❌ |

**除以上三项外，Jig 在其他所有框架级能力上都是零。** 要做成一个正经框架（对标 LangGraph/PydanticAI），至少需要补齐 3 个 🔴 + 5 个 🟡。预计工期 8-10 周。
