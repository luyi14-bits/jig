# TASK-005: DeepSeek 深度优化包 — PRD

> **版本**: v0.1 | **作者**: PM (Luyi14-pm-mentor) | **日期**: 2026-07-20

---

## 1. Executive Summary

合并 IDEA-037 + 050 + 051，将 AgentHarness 的 DeepSeek 集成优化到标杆水平。目标是进入 awesome-deepseek-agent 官方推荐列表。核心产出：成本感知调度、自动 Tool-Call Repair、reasoning_effort 可配置。

## 2. Problem Statement

| 痛点 | 频率 | 严重度 |
|------|:----:|:------:|
| API 费用不可控（Pro/Flash 无成本感知） | 每次调用 | 🔴 |
| DeepSeek FC 返回格式异常时直接崩溃 | 偶发 | 🟠 |
| reasoning_effort 无法由用户控制 | 每次 | 🟡 |
| token 消耗无追踪、无预算上限 | 持续 | 🟡 |

## 3. FR

### FR-1: 成本感知调度 (IDEA-050)
- FR-1.1: 所有 Agent 默认用 Flash
- FR-1.2: 复杂度超阈值自动升级 Pro
- FR-1.3: 每次调用记录 token + 费用
- FR-1.4: session 级 Token 预算，超限熔断

### FR-2: Tool-Call Repair (IDEA-051)
- FR-2.1: FC 返回非标准 JSON 自动纠正常见错误
- FR-2.2: 缺失必填参数时推断默认值
- FR-2.3: 修复失败重试最多 3 次
- FR-2.4: 持续失败降级为纯文本

### FR-3: reasoning_effort 可配置 (IDEA-037)
- FR-3.1: 暴露 `reasoning_effort` 参数到 Agent config
- FR-3.2: 支持 `low / medium / high` 三档

## 4. RICE 评分

| IDEA | Reach | Impact | Confidence | Effort(d) | RICE |
|:----:|:-----:|:------:|:----------:|:---------:|:----:|
| 050 | 5 | 5 | 4 | 2 | 50 |
| 051 | 4 | 4 | 3 | 1 | 48 |
| 037 | 5 | 3 | 4 | 1 | 60 |

合并后总 Effort: 3 人天

## 5. Out of Scope
- 多模型抽象（延后 v2）
- 缓存节省可视化 UI
