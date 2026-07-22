# TASK-002: 编排调度 + 状态管理 + 开发工作流 + 独立部署 PRD

> **版本**：v0.1 | **作者**：PM Mentor | **日期**：2026-07-13 | **状态**：初稿

---

## 1. Executive Summary

本迭代为 Jig 引擎添加企业级能力：并行编排调度、状态检查点恢复、完整开发工作流链、FastAPI 独立部署、以及 cache-guard CI 工程纪律。目标是让引擎从"核心可用"升级到"生产就绪"。

## 2. Problem Statement

| 痛点 | 频率 | 严重度 | 影响 |
|------|:----:|:------:|------|
| 子 Agent 只能串行执行，无法并行加速 | 每次多 Agent 任务 | 🔴 严重 | 响应时间随 Agent 数线性增长 |
| 流程中断后无法恢复 | 每次失败重试 | 🔴 严重 | 从头开始，浪费已完成工作 |
| 缺乏端到端开发工作流模板 | 每次新项目 | 🟠 中等 | 需要重复编写 SOP 定义 |
| 无法独立部署为后端服务 | 集成需求 | 🟢 轻度 | 依赖 AI 编程工具环境 |
| 缓存命中率退化无自动检测 | 每次发版 | 🟠 中等 | 费用不可控 |

## 3. Goals & Metrics

| 指标 | 当前 | 目标 |
|------|:----:|:----:|
| 并行调度 | 仅顺序 | 并行度 ≥3 Agent |
| 检查点恢复 | 无 | 任意节点可恢复 |
| 工作流模板 | 无 | 1 套完整开发 SOP |
| 独立部署 | 仅 CLI | REST API |
| cache-guard CI | 无 | CI 自动阻断退化 |

## 4. PRD

### FR-1: 并行调度模式
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-1.1 | ParallelOrchestrator 支持同时执行多个子 Agent | P1 |
| FR-1.2 | 支持设置最大并行数（max_concurrency） | P1 |
| FR-1.3 | 全部子 Agent 完成后聚合结果 | P1 |

### FR-2: 检查点管理
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-2.1 | CheckpointManager 支持保存/恢复 Agent 状态 | P1 |
| FR-2.2 | 检查点持久化到 JSON 文件 | P1 |
| FR-2.3 | 支持 resume() 从指定检查点继续 | P1 |

### FR-3: 开发工作流链
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-3.1 | 预定义 SOP 模板：brainstorm→plan→code→test→review | P1 |
| FR-3.2 | 工作流链支持自定义阶段注入 | P1 |

### FR-4: FastAPI 独立部署
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-4.1 | FastAPI 服务端，暴露 REST API | P2 |
| FR-4.2 | POST /execute 接受 SOP 定义并执行 | P2 |
| FR-4.3 | GET /status/{session_id} 查询执行状态 | P2 |

### FR-5: cache-guard CI 工程纪律
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-5.1 | TestReleaseCacheHitGuard 测试 | P1 |
| FR-5.2 | PR 模板添加 Cache-impact 声明 | P1 |

## 5. Out of Scope

- GUI 管理界面：P3 后续
- WebSocket 实时日志：P3 后续
- 负载均衡：P3 后续

## 6. Open Questions

| # | 问题 | 状态 |
|---|------|:----:|
| 1 | FastAPI 是否加入依赖？ | 按 optional extras |
| 2 | 检查点默认存储路径？ | `~/.tree-sop/checkpoints/` |
