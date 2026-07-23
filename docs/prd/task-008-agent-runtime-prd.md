# PRD: Agent Runtime — State + Lifecycle + 协作恢复 Loop (IDEA-063)

**Priority**: P0 (框架核心方向)
**Version**: v0.7.0
**Date**: 2026-07-23

## 1. Executive Summary

Agent 不应是"高级 Skill"（prompt + config 的壳），而应是有状态、有周期、能协作的运行时实体。三核心概念分离：**State**（状态机）、**Checkpoint**（进度快照）、**Memory**（长期知识），互不混合。失败恢复遵循 **fail → summarize → upgrade → retry** 闭环。

## 2. Problem Statement

- Agent 没有状态机：一次 call 就结束，无法 pause/resume/recover
- State / Checkpoint / Memory 在三处混用，无清晰边界
- 失败处理太弱：只有 `except: log + continue`，无总结/升级/重试
- 两套 CheckpointManager 各自为政
- Prompt 已成熟（300行 vs 500行无意义），框架重心应转向 Runtime

## 3. Conceptual Separation

| 概念 | 定义 | 存储 | 生命周期 |
|------|------|------|:--------:|
| State | idle/running/waiting/failed/retrying/recovered/done | 内存 | Session |
| Checkpoint | 执行进度快照（当前步骤+上下文+已完成） | JSON/SQLite | 持久化 |
| Memory | 长期可检索知识/经验/用户偏好 | SQLite/Embedding | 跨 Session |

## 4. Fail → Summarize → Upgrade → Retry Loop

```
Agent Error
   │
   ▼
[Summarize]  ── 分析原因 + 提取教训 + 写入 Memory
   │
   ▼
[Upgrade]    ── 三选一/多级串联:
   │             ① 模型升级：Flash → Pro
   │             ② 策略升级：放宽约束 / 换工具 / 加上下文
   │             ③ 角色升级：escale 给更强 Agent
   │
   ▼
[Retry]      ── 用升级后的配置重新执行
   │
   └── 成功 → done | 再失败 → summarize → upgrade → retry (max N)
```

不是简单的 retry loop，而是有反思的闭环。

## 5. Requirements

- R1: State 状态机（idle/running/waiting/failed/retrying/recovered/done）
- R2: Checkpoint（进度快照，独立于 State/Memory）
- R3: Memory（长期知识，Agent 只引用不拥有）
- R4: 失败策略：summarize(分析原因+提取教训) → upgrade(模型/策略/角色) → retry
- R5: 生命周期钩子（on_init/on_run/on_error/on_stop）
- R6: 统一 CheckpointManager（合并两套实现）

## 6. Out of Scope
- Agent 间协商/投票 → v0.8.0
- 与 AgentFactory 深度集成 → 跟随迭代
