# PRD: Agent Runtime + 协作恢复机制 (IDEA-063)

**Priority**: P0 (框架核心方向)  
**Version**: v0.7.0  
**Date**: 2026-07-23

## 1. Executive Summary

当前 Agent 本质是"高级 Skill"——一个携带 prompt 和 config 的壳，被编排器当函数调。没有状态机、没有生命周期、没有自主决策循环。框架的重心应转向 Runtime（运行时），让 Agent 成为真正的运行时实体，具备自我恢复和协作能力。

## 2. Problem Statement

- Agent 没有状态机：一次 call 就结束，无法 pause/resume/recover
- Checkpoint 有两套互不关联的实现（loop_engine + orchestrator），无法统一 rollback
- 失败处理太薄弱：ParallelOrchestrator 里只有 `except: log + continue`
- 协作只有线性 HandoverPackage，没有 escalation / recovery chain / 协商
- 代码已提前实现（`agent_runtime.py`），但未走完整 SOP 流程，需要正式验收

## 3. Functional Requirements

- FR-1: AgentRuntime 状态机（idle → running → waiting → paused → error → recovered → done）
- FR-2: 生命周期钩子（on_init / on_run / on_pause / on_resume / on_error / on_stop）
- FR-3: Auto-Checkpoint（每次状态变更自动保存 context + memory + state）
- FR-4: Auto-Rollback（失败后回滚到最近成功 checkpoint）
- FR-5: Retry Policy（可配置 max_retries，默认 3 次）
- FR-6: Timeline 事件日志（状态变更 / 重试 / checkpoint）
- FR-7: 统一 CheckpointManager（合并两套实现）
- FR-8: 失败 Escalation 链（Agent A 失败 → Agent B 接管 → 人工介入）

## 4. Out of Scope

- 真 Replay（从 timeline 重新执行）→ v0.8.0
- Agent 间协商/投票机制 → v0.9.0
- 与现有 AgentFactory 的集成 → IDEA-063 Spec 中细化

## 5. Success Metrics

- AgentRuntime 12 测试全绿（已通过）
- 两套 CheckpointManager 合并为统一实现
- Timeline 可完整回放 Agent 执行过程
