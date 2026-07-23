---
copyright: true
top: false
author: luyi14-bits
date: 2026-07-22
updated: 2026-07-23
---

# Jig — 唯一自带"事前拦截"安全门禁的多 Agent 编排框架

> 不是又一个 LangGraph 克隆。ToolGuard 在工具执行前拦截——所有竞品都做不到。

---

## 一、为什么还需要一个 Agent 框架？

2026 年的 Agent 框架生态已经拥挤不堪：LangGraph 37k★、CrewAI 55k★、PydanticAI 18k★……但所有这些框架都共享一个致命的共同缺陷——

**它们的安全约束都是"事后"的。**

所谓的 Guardrails 全部是 prompt-only——写一句"不要删除文件"在系统提示词里，Agent 想绕过就能绕过。没有一个框架在代码层面做**事前拦截**。

Jig 就不一样。

它的核心是一个叫 **ToolGuard** 的硬约束层——Agent 的每一次工具调用，在真正执行之前就被拦截检查。白名单、黑名单、PreToolUse 钩子，三层把关，代码级阻断。

```
Agent 调工具 → 白名单检查 → 黑名单检查 → PreToolUse 钩子 → 执行
```

这才是真正的安全。

---

## 二、Jig 是什么？

**一句话**：给开发者用的 Agent 框架，不是给终端用户用的 Agent 软件。

```python
# 5 行代码启动一个 Agent 管道
from jig import Jig

app = Jig(model="deepseek-v4-flash")
result = app.run("帮我审查这段代码的安全性")
print(result)
```

### 核心能力

| 能力 | Jig 怎么做 | 竞品有吗 |
|------|-----------|:--------:|
| 事前安全拦截 | ToolGuard 三层 | ❌ 全部 prompt-only |
| DeepSeek 缓存优化 | SHA-256 前缀哈希 + 成本路由 | ❌ |
| 图编排 | GraphOrchestrator（条件/并行/循环） | ✅ LangGraph |
| 流式输出 | SSE chat_stream | ✅ |
| 多模型 | DeepSeek + OpenAI + 可扩展 | ✅ |
| 记忆体系 | 4 层（Cache→分区→Embedding→SQLite） | ❌ |
| 收敛引擎 | LoopEngine（检测+回放） | ❌ |
| 外部 Agent 管理 | Meta-Harness 适配器 | ❌ |

---

## 三、架构五层

```
控制层:  LOOP SOP · ToolGuard · 全局约束 · 断路器
Agent层:  Skill解析器 → 注册表 → 工厂 → Agent实例
编排层:  顺序 · 并行 · 图 · 循环引擎 · 检查点
工具层:  MCP · 仓库映射 · 嵌入索引 · 模型路由
插件层:  视觉工具 · 图片读取（可选）
```

每一层都是独立的，开发者可以替换任意一层。

---

## 四、三层 ToolGuard

```
Agent 调工具
    │
    ▼
[白名单]  ── 不通过 → 拦截 + 日志
    │ 通过
    ▼
[黑名单]  ── 命中   → 拦截 + 日志
    │ 通过
    ▼
[PreToolUse 钩子] ── 不通过 → 拦截 + 日志
    │ 通过
    ▼
  真正执行
```

白名单和黑名单通过 ConfigManager 配置：

```python
from jig import ConfigManager

cfg = ConfigManager()
cfg.set_agent_config("my-agent", {
    "allow_tools": ["read", "write"],
    "deny_tools": ["rm", "sudo"],
})
```

---

## 五、一分钟上手

```bash
pip install jig
export JIG_API_KEY="sk-your-key"
```

创建 `skills/my-agent/SKILL.md`：

```yaml
---
name: my-agent
description: "我自己的 Agent"
model: flash
tools: [read, write]
---

## 角色
你是一个代码审查助手...
```

运行：

```python
from jig import Jig

app = Jig(skills_dir="./skills")
result = app.run("审查 src/ 下的代码")
print(result)
```

---

## 六、与其他框架的对比

| 维度 | deepagents | OpenAI SDK | LangGraph | CrewAI | PydanticAI | **Jig** |
|------|:----------:|:----------:|:---------:|:------:|:----------:|:-------:|
| **事前安全拦截** | ❌ "trust LLM" | ❌ prompt-only | ❌ | ❌ | ❌ | ✅ **ToolGuard** |
| **DeepSeek 缓存** | — | — | — | — | — | ✅ **SHA-256** |
| **图编排** | ❌ | ✅ | ✅ 原生 | ❌ | ✅ | ✅ **GraphOrchestrator** |
| **流式** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **记忆** | 短期 | — | Checkpointer | 短期 | 上下文 | ✅ **4层** |
| **成本治理** | — | — | — | — | — | ✅ **成本路由** |
| **外部 Agent 治理** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **Meta-Harness** |
| **螺旋收敛** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **LoopEngine** |
| **多模型** | ✅ 20+ | ❌ OpenAI only | ✅ 20+ | ✅ 10+ | ✅ 20+ | ✅ DS+OpenAI |
| **开源协议** | MIT | MIT | MIT | MIT | MIT | MIT |

---

## 七、路线图

| 阶段 | 内容 | 状态 |
|------|------|:----:|
| 基础 | Skill→Agent 映射 + DS 双模型 | ✅ v0.1-0.4 |
| 记忆 | 4 层记忆 + SQLite | ✅ vA.0.2 |
| 安全 | 断路器 + 漂移检测 + 风险模式 | ✅ vA.0.3 |
| 多模型 | DeepSeek + OpenAI + 流式 | ✅ v0.5.0 |
| 图编排 | GraphOrchestrator | ✅ v0.6.0 |
| 文档 + Agent Firewall | MkDocs + 定位文章 + 对比博文 | ✅ 当前 |
| Meta-Harness | 外部 Agent 治理层（Claude Code/Codex 适配） | 🚧 |
| 包发布 | PyPI + CI | 🚧 |

---

## 八、总结

Jig 不是一个"又一个 Agent 框架"。它是**唯一一个在代码层面做事前安全拦截的框架**。

- 如果你需要真正安全的 Agent 执行环境——**Jig 是唯一选择**
- 如果你在用 DeepSeek——**Jig 做了其他框架都不做的缓存优化**
- 如果你觉得 LangGraph 太重、CrewAI 太泛——**Jig 提供开箱即用的 12 个预设角色 + 自定义 SKILL.md 挂载**

GitHub 开源地址：[https://github.com/luyi14-bits/jig](https://github.com/luyi14-bits/jig)

---

**作者**：luyi14-bits | **协议**：MIT | **欢迎 Star / Issue / PR**
