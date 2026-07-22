# Loop #3 PRD: Durable Execution + Graph 编排

**IDEA**: 060 + 061
**Priority**: P1 (重大缺失)
**Version**: v0.6.0
**Date**: 2026-07-22

## 1. Executive Summary
Jig 当前只有线性/并行/层级三种硬编码编排模式。缺少图工作流（LangGraph 的核心卖点）和持久化执行（崩溃恢复）。本 PRD 覆盖这两个重大缺失，合并为同一个 Loop。

## 2. Requirements

### Durable Execution (IDEA-060)
- FR-1: CheckpointManager 提升为框架级，所有 SOP 管道节点执行后自动保存
- FR-2: 崩溃恢复：Session 重启后从最后检查点恢复
- FR-3: 异步长时间运行支持

### Graph 编排 (IDEA-061)
- FR-4: GraphNode 定义（节点 = Agent 或子管道）
- FR-5: GraphEdge 定义（条件路由 / 上下文传递 / 超时）
- FR-6: GraphOrchestrator 执行引擎（拓扑排序 → 条件分支 → 自环 → 递归）
- FR-7: 可视化状态查询接口

## 3. Out of Scope
- LangGraph 兼容模式（v0.7.0）
- 可视化编辑器（v1.0）

## 4. Success Metrics
- `GraphOrchestrator` 支持线性 + 条件 + 并行 + 自环
- `CheckpointManager` 在 SOP 节点级自动保存
- 崩溃后 `resume()` 可恢复到最后检查点
