# 战略定位决议 v2 (2026-07-22)

> Jig = Framework（造 Agent）+ Harness（管 Agent），内建而非外挂。

## 一句话定位

> **Jig 是一个让开发者用几行代码组装自己 Agent 的框架，内建 DeepSeek 缓存优化和 ToolGuard 硬约束。**  
> 对标 LangGraph 的"造 Agent"能力，但 Jig 造的 Agent 天生带缰绳。

## 核心差异化

| 层 | 能力 | 对标 |
|----|------|------|
| **Framework 层** | SDK API + add_agent + SKILL.md 挂载 + 12 预设角色 | LangGraph / PydanticAI |
| **Harness 层** | ToolGuard 事前拦截 + LOOP SOP 门禁 + CostAwareRouter + CircuitBreaker | **独有，无人区** |

**和 MS AGT 的区别**：AGT 是造好 Agent 后外挂管控。Jig 是造 Agent 时内建管控——出生就带缰绳。

**和 LangGraph 的区别**：LangGraph 是图编排，对 Agent 行为不做限制。Jig 是管道编排，Agent 从创建就被硬约束覆盖。

## Loop 排期

| Loop | 内容 | 工时 | 优先级 |
|:----:|------|:---:|:------:|
| #1 | awesome PR | 1天 | P0 |
| #2 | 多模型抽象 + 流式输出 | 4天 | P0 |
| #3 | Durable + Graph 编排 | 7天 | P1 |
| #4 | 真实项目验证 | 3天 | P0 |
| #5 | pip + 文档站点 | 2天 | P1 |
| #6 | OTel + Evals | 4天 | P2 |

## 别人为什么用 Jig

1. **DeepSeek 极致优化**（Reasonix 没有的框架级前缀缓存 + CostAwareRouter）
2. **Agent 天生带缰绳**（LangGraph/PydanticAI 没有的 ToolGuard 事前拦截）
3. **5 行代码组装 Agent + 12 预设角色即开即用**
4. **外挂式管控（MS AGT） vs 内建式管控（Jig）——架构级差异**
