---
copyright: true
top: false
author: luyi14-bits
date: 2026-07-23
updated: 2026-07-23
tags: [Agent, 架构, 设计, Harness, ToolGuard]
---

# Jig 设计之路：从零到 v0.6 的架构演进

> 每个关键决策背后都有取舍——为什么选硬约束、为什么四层记忆、为什么先 DeepSeek 后 OpenAI、为什么用孤儿分支做多语言。

---

## 一、缘起：为什么不做"又一个 LangGraph"

2026 年初规划 Jig 时，Agent 框架赛道已经有三类玩家：

- **编排型**：LangGraph（37k★）、CrewAI（55k★）——定义如何连接 Agent
- **SDK 型**：OpenAI Agents SDK（28k★）、PydanticAI（18k★）——定义如何调用 LLM
- **工具型**：MCP 协议、A2A 协议——定义如何对接工具

当时我们问了自己一个核心问题：

> *再做一个编排框架，用户凭什么选你？*

答案是**安全**。所有竞品的安全机制都停在 prompt 层面——靠劝，不靠拦。2026 年 Agent 即将从 POC 走向生产，谁先解决"Agent 越权执行危险命令"的问题，谁就拿到了企业市场的入场券。

于是我们决定：**不做编排框架，做 Agent 防火墙。**

---

## 二、v0.1~0.4：奠基——Skill→Agent 映射与 ToolGuard 雏形

### 核心决策 #1：SKILL.md 声明式 Agent 定义

我们不另起炉灶写 Python 配置类，而是复用 Markdown 的 frontmatter 做 Agent 声明：

```yaml
# skills/my-agent/SKILL.md
---
name: my-agent
description: "安全审计 Agent"
model: pro
tools: [read, grep, search]
---
```

每一行 YAML 翻译成一个 Python 类。SkillParser → SkillRegistry → AgentFactory，三段式管道。

**为什么选 Markdown 而非纯 Python？** 让非开发者的 PM 也能写 Agent 配置。

### 核心决策 #2：ToolGuard 事前拦截而非事后审查

这是 Jig 的"灵魂"决策。当时参考了 Kubernetes 的 Admission Webhook 模式——在请求到达 etcd 之前拦截。于是我们在 Agent 工具调用请求到达实际执行函数之前，插入了一个 Guard 层：

```python
class ToolGuard:
    WHITELIST = { ... }   # 按角色精确授权
    DENYLIST = [ ... ]    # 全局禁止操作
    
    @classmethod
    def check(cls, role, tool, args) -> bool:
        # 在工具执行前返回 True/False
```

这个设计在 v0.1 就定型了，后续版本没有改过接口——只扩展了规则。

### 核心决策 #3：四层记忆

为什么是四层，不是三层或五层？因为每个问题需要不同粒度的上下文：

1. **Cache（前缀缓存）** — 最近 N 轮对话，装在 DeepSeek 缓存前缀里，命中率 >99%
2. **Partition（分区压缩）** — 长对话按窗口分区，过期自动归档
3. **Embedding（向量索引）** — 语义搜索，找回 Cache 命中不到的历史信息
4. **SQLite（持久化）** — 跨 Session 持久，Agent 下次启动还能回忆

---

## 三、v0.5：多模型与流式——泛化但不失控

### 核心决策 #4：先 DeepSeek，后 OpenAI

不是技术原因——而是产品原因。Jig 的 ToolGuard + 前缀缓存对 DeepSeek 的 API 架构做了大量适配，如果一开始就做泛化抽象，会浪费大量时间在"设计模式"而非"实际效果"上。

做法是：先用 `DeepSeekProvider` 做到极致（SHA-256 缓存 + Flash-first 成本路由 + FC 自动修复），再抽象出 `BaseModelProvider` 接口：

```python
class BaseModelProvider:
    def chat(self, messages, **kw) -> ModelResponse: ...
    def chat_stream(self, messages, **kw) -> Iterator[StreamChunk]: ...

class DeepSeekProvider(BaseModelProvider): ...
class OpenAIProvider(BaseModelProvider): ...
```

接口只有 2 个方法。够用，不冗余。

### 核心决策 #5：SSE 流式先于 WebSocket

Streaming 选择了 Server-Sent Events（SSE）而不是 WebSocket，原因很简单：

- SSE 只需要 HTTP，不依赖长连接库
- SSE 天然支持文本流式输出——Agent 的 `chat_stream` 返回值是 `Iterator[StreamChunk]`
- WebSocket 留给未来双向通信场景

---

## 四、v0.6：图编排与收敛检测——Loop Engineering

### 核心决策 #6：先 Graph 后 Durable

Durable Execution（持久化执行+中断恢复）是 PydanticAI v2.16 刚追上的功能。Jig 选择先做 Graph 再补 Durable，因为 GraphOrchestrator 能覆盖更广泛的应用场景：

```python
# 条件路由、并行分支、自环
GraphEdge("analyze", "approve", condition=is_complex)
GraphEdge("analyze", "skip", condition=is_simple)
```

条件路由在真实 SOP 管道中至少节省了 40% 的判断代码。

### 核心决策 #7：LoopEngine 收敛检测

Agent 最常见的 bug 不是"做错了"，而是**停不下来**（死循环、重复输出、质量退化）。

LoopEngine 的 ConvergenceDetector 监控每一次迭代的输出变化，当收敛曲线趋于平稳或开始发散时，自动 STOP：

```python
class ConvergenceDetector:
    def check(self, history: List[str]) -> LoopDecision:
        if len(history) >= 10:
            return LoopDecision.STOP  # 迭代次数超限
        if similarity(history[-2], history[-1]) > 0.95:
            return LoopDecision.STOP  # 收敛
        return LoopDecision.CONTINUE
```

---

## 五、架构演进全景

```
v0.1         v0.2         v0.4         v0.5         v0.6         未来
 │            │            │            │            │            │
 ▼            ▼            ▼            ▼            ▼            ▼
Skill→Agent  Memory+     Circuit-     Multi-Model  Graph+        Meta-
Mapping      Config      Breaker      +Streaming   Durable       Harness
+ToolGuard   +Context    +Drift       +CostRouter  +LoopEngine   +PyPI
             +SQLite     +RiskMode                            +Docs
```

从 v0.1 到 v0.6，核心 API 没有 break——ToolGuard 的 `check()` 接口从 v0.1 到现在一行未改。这是 Jig 最引以为豪的设计稳定性。

---

## 六、多语言 SDK：为什么孤儿分支

TypeScript SDK 和 Rust Harness 没有放在 `src/` 下，而是用 git orphan branch 独立管理：

```bash
# TypeScript SDK 在 ts 分支
git checkout --orphan ts
# Rust Harness 在 rust 分支
git checkout --orphan rust
```

**为什么？** 因为 Python / TypeScript / Rust 的构建工具链互相冲突。`pyproject.toml` 和 `Cargo.toml` 在同一个目录下，IDE 会报错。用孤儿分支实现：

- 各语言独立构建、独立版本号
- 仓库统一在一个 GitHub repo 下（`github.com/luyi14-bits/jig`），0 维度的品牌一致性
- 共享 Issues 和 Discussions（还在同一个仓库）

---

## 七、总结：架构原则

回顾所有决策，有三条铁律贯穿始终：

1. **安全先于功能** — ToolGuard 在 v0.1 就定型，后续所有新功能不得绕过 Guard
2. **接口先于实现** — BaseModelProvider 在只有 DeepSeek 时就设计了，OpenAI 实现花了 2 小时
3. **收敛先于扩展** — 不做"更多的功能"，而是做"让功能停得下来的机制"

下一个阶段（v0.7+）：Meta-Harness 外部 Agent 治理层。让 Jig 的 ToolGuard 能管控 Claude Code、Codex、Cursor 的工具调用——从一个 Agent 框架进化成**所有 Agent 的共享安全层**。

---

**GitHub**: https://github.com/luyi14-bits/jig  
**技术白皮书**: `docs/technical-whitepaper-v3.md`  
**定位文档**: `docs/agent-firewall-positioning.md`
