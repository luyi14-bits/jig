# TASK-005: DeepSeek 深度优化包 — PRD

> **版本**: v0.1 | **作者**: PM (Luyi14-pm-mentor) | **日期**: 2026-07-20 | **门禁**: G0→G1

---

## 1. Executive Summary

将 Jig 的 DeepSeek 集成从"能用"升级到"标杆水平"。目标：进入 awesome-deepseek-agent 官方推荐列表。合并 IDEA-037（reasoning_effort）+ 050（成本感知）+ 051（Tool-Call Repair）+ 047（参数透传）。

## 2. Problem Statement

| 痛点 | 频次 | 严重度 |
|------|:----:|:------:|
| API 费用不可控，Pro/Flash 无成本感知 | 每次调用 | 🔴 高 |
| DeepSeek FC 返回格式异常时直接崩溃 | 偶发 | 🟠 中 |
| reasoning_effort 无法由用户控制 | 每次 | 🟡 低 |
| 无 token 追踪和预算上限 | 持续 | 🟡 低 |

## 3. User Stories

- **作为开发者**，我希望所有 Agent 默认用 Flash 低成本运行，复杂任务自动升级 Pro
- **作为架构师**，我希望每个 Agent 可配置 reasoning_effort（low/medium/high）
- **作为运维**，我希望设置 session 级 Token 预算，超限自动熔断
- **作为开发者**，我希望 DeepSeek FC 格式错误被自动修复而非崩溃

## 4. FR

| ID | 需求 | 优先级 |
|:--:|------|:------:|
| FR-1 | 成本感知路由：默认 Flash，复杂度超阈值自动升级 Pro | P0 |
| FR-2 | Token 预算：session 级预算，超限熔断 | P0 |
| FR-3 | reasoning_effort：每个 Agent 可配 low/medium/high | P0 |
| FR-4 | Tool-Call Repair：FC 错误 3 层自动修复 | P0 |
| FR-5 | 成本追踪：每次调用记录 token + 费用 | P1 |

## 5. Technical Considerations

- `CostAwareRouter` 新增到 ModelRouter 同级，不破坏现有路由链
- `DeepSeekAdapter` 增强修复逻辑，不改变现有接口
- `reasoning_effort` 通过 AgentFactory 的 agent config 传入

## 6. Dependencies

- 现有 `DeepSeekAdapter`（reasoning_content 处理、FC 降级）已就绪
- 现有 `CacheEngine`（前缀 hash、缓存诊断）已就绪

## 7. Out of Scope

- 多模型抽象层（IDEA-037 原范围，延后到 v2）
- 缓存节省可视化 UI

## 8. Success Metrics

| 指标 | 目标 |
|------|------|
| CostAwareRouter 测试 | 6/6 通过 |
| Tool-Call Repair 测试 | 5/5 通过 |
| reasoning_effort 测试 | 3/3 通过 |
| 全量回归 | 无回归 |
