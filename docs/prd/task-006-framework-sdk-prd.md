# TASK-006: 框架 SDK 核心 — PRD

> **版本**: v0.1 | **日期**: 2026-07-20 | **门禁**: G0→G1

## 1. Executive Summary
合并 IDEA-036（SDK API）+ 049（外部 Agent 兼容）+ 044（MCP 协议）+ 041（Loop Engineering）。提供框架的公开入口、外部 Agent 接入、MCP 双向通信、Loop Engineering 工程化。

## 2. FR
| ID | 需求 | Pri |
|:--:|------|:---:|
| FR-1 | AgentHarness API 类，5 行代码跑通管道 | P0 |
| FR-2 | MetaHarness：Claude Code / Codex 等外部 Agent 接入 ToolGuard | P0 |
| FR-3 | MCPServer：MCP 双向 Server + Client | P0 |
| FR-4 | CostAwareRouter 的 Gate 循环集成 | P0 |
| FR-5 | 外部 Agent 经过 ToolGuard 三层拦截 | P0 |

## 3. Out of Scope
- A2A 协议（IDEA-045，P1）
- 可视化编排（废弃）

## 4. Success Metrics
- AgentHarness API：`from agent_harness import AgentHarness` 成功
- MetaHarness：`route("claude", "prompt")` 返回结果
- MCP：`list_tools() + call_tool()` 正常
- 全量回归 62/62
