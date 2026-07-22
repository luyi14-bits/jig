# TASK-003: Agent 核心重构 — 双层 Prompt + 多 Skill 挂载 + Dispatcher + CR Agent PRD

> **版本**：v0.1 | **作者**：PM Mentor | **日期**：2026-07-14 | **状态**：初稿

---

## 1. Executive Summary

本次迭代完成 Jig 的核心架构升级：让每个 Agent 真正拥有完整的 SKILL.md body 作为 system prompt，支持用户向 Agent 动态挂载多个 Skill，新增群聊入口 Dispatcher 和 Code-Review Agent。这是从"空壳 Agent"到"真正按 skill 运行的 Agent"的关键重构。

## 2. Problem Statement

| 痛点 | 严重度 | 现状 |
|------|:----:|------|
| Agent 只有一句话 prompt，SKILL.md 正文被丢弃 | 🔴 | `ROLE_PRESETS["pm"] = "你是产品经理..."` 而非 189 行 PM 方法论 |
| 用户新增 skill 需改代码 | 🔴 | `ROLE_PRESETS` 硬编码，用户不能 `--attach` 导入 |
| 没有群聊入口 | 🟠 | 用户需手动指定 Agent，无法自然语言输入 |
| Coding → TDD 之间无代码审查环节 | 🟠 | 编码后直接测试，遗漏质量检查 |
| Agent 工作无留痕 | 🟠 | 无自动 LOG.md 写入 |
| 用户不能自定义 Agent 显示名 | 🟡 | `agent_name` 字段缺失 |

## 3. Goals & Metrics

| 指标 | 当前 | 目标 |
|------|:----:|:----:|
| SKILL.md body 保留 | 0% | 100%（10/10 skill） |
| 用户导入 skill | 改代码 | `--attach skill1,skill2` |
| PreToolUse 硬约束 | 无 | tools 白名单有效 |
| 代码审查环节 | 无 | CR Agent 产出一份 CR Report |
| 群聊入口 | 无 | Dispatcher 接收自然语言 |

## 4. User Stories

### Story 1: SKILL.md body 作为 Agent prompt
- **GIVEN** 一个完整的 SKILL.md（含 frontmatter + body）
- **WHEN** AgentFactory 创建 Agent
- **THEN** body 全文作为 system prompt 注入
- **AND** `--inspect` 显示完整的组装 prompt

### Story 2: 用户导入多个 Skill
- **GIVEN** 用户有 3 个自写 SKILL.md
- **WHEN** `--attach skill1,skill2,skill3`
- **THEN** 指定 Agent 的 prompt 拼接这 3 个 skill body
- **AND** 按加载顺序，后覆盖前

### Story 3: 群聊入口
- **GIVEN** Dispatcher 正在运行
- **WHEN** 用户输入"帮我做一个登录功能"
- **THEN** Dispatcher 理解意图 → 路由到 PM Agent → 启动 SOP 管道

### Story 4: Code-Review 环节
- **GIVEN** Coding Agent 完成编码
- **WHEN** HandoverPackage 传递到 CR Agent
- **THEN** CR Agent 审查代码 → 产出 CR Report → 传递到 TDD Agent

## 5. Functional Requirements

### FR-1: SkillDef body 保留
- **FR-1.1** SkillParser 提取 frontmatter 之后的 body 全文存入 SkillDef.body
- **FR-1.2** SkillDef 新增 `body` 和 `agent_name` 字段
- **FR-1.3** `--inspect` 显示组装后的完整 prompt

### FR-2: 双层 prompt 组装
- **FR-2.1** AgentFactory 拼装顺序：全局约束 → 角色预设 → Skill A body → Skill B body → ...
- **FR-2.2** 全局约束写在新文件 `global_constraints.py`（禁止越权、交接协议、留痕规则、安全红线）
- **FR-2.3** CLI 新增 `--attach skill1,skill2` 参数

### FR-3: Dispatcher 群聊入口
- **FR-3.1** Dispatcher 接收自然语言，理解意图后路由到 PM Agent
- **FR-3.2** CLI 新增 `--chat` 模式

### FR-4: Code-Review Agent
- **FR-4.1** 创建 `skills/Luyi14-code-review/SKILL.md`
- **FR-4.2** CR Agent 审查代码风格、潜在 Bug、安全红线、性能反模式
- **FR-4.3** 产出 CR Report（HandoverPackage）

### FR-5: Agent 自动留痕
- **FR-5.1** Agent 完成后自动调用 `write_log()` 写 LOG.md
- **FR-5.2** 日志格式：日期 → 任务摘要 → 产出 → 交接目标

### FR-6: Agent 自定义显示名
- **FR-6.1** Skill frontmatter 支持 `agent_name` 可选字段
- **FR-6.2** CLI 和日志显示使用此名称

## 6. Out of Scope

- MCP 工具集成（下一迭代）
- DevOps Agent（下一迭代）
- Tauri 桌面应用（P2）
- PreToolUse hooks 硬约束（下一迭代与 MCP 一起）

## 7. Open Questions

| # | 问题 | 状态 |
|---|------|:----:|
| 1 | 多 Skill body 总长度超 token 限制的策略？truncation vs 摘要？ | 先用截断 |
