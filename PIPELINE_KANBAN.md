# 管线看板

> 最后更新：2026-07-15（第十四轮：Tauri 原生桌面 IDEA-018 交付） | 维护人：项目秘书
> 数据来源：需求对话 + 调研报告 + Reasonix 源码分析 + DeepSeek API 文档

---

## 看板总览

| 💡 想法池 | 📝 规划中 | 🔨 开发中 | ✅ 验收中 | 🚀 已发布 | ❌ 废弃 |
|-----------|-----------|-----------|-----------|-----------|---------|
| 3 项 | 0 项 | 0 项 | 0 项 | 6 项 | 1 项 |

---

## 💡 想法池

> 未经 Spec 细化的原始想法，等待评估和排期。

### IDEA-001：Skill → Agent 自动映射引擎
- **来源**：老板初始需求
- **描述**：将每个 skill 定义自动转换为一个独立 Agent，具备角色、目标、工具集
- **参考**：Superpowers 的 skill 自动触发机制
- **优先级**：P0（核心功能）
- **状态**：PRD 完成 ✅ → 并入 TASK-001

### IDEA-002：DeepSeek V4 Pro/Flash 混用策略
- **来源**：老板需求确认
- **描述**：规划/调研/审查用 Pro，编程/测试用 Flash，降低 60-70% API 成本
- **参考**：社区实测验证 Pro 规划 + Flash 执行方案 + Reasonix /effort 分级策略
- **优先级**：P0（核心功能）
- **状态**：PRD 完成 ✅ → 并入 TASK-001

### IDEA-003：Tree-SOP Skill 定义格式
- **来源**：老板 tree-sop 理念
- **描述**：设计结构化的 skill 定义文件格式（类似 SKILL.md），支持树形 SOP 结构
- **参考**：Superpowers SKILL.md + CrewAI Agent 定义
- **优先级**：P0（核心功能）
- **状态**：PRD 完成 ✅ → 并入 TASK-001

### IDEA-004：编排调度器
- **优先级**：P1
- **状态**：✅ 已交付 v0.2.0（并行调度模式）

### IDEA-005：状态管理与检查点
- **优先级**：P1
- **状态**：✅ 已交付 v0.2.0（CheckpointManager）

### IDEA-006：完整开发工作流
- **优先级**：P1
- **状态**：✅ 已交付 v0.2.0（dev_workflow 模板）

### IDEA-007：独立部署模式
- **优先级**：P2
- **状态**：✅ 已交付 v0.2.0（FastAPI 服务）

### IDEA-008：DeepSeek 缓存稳定前缀不变量
- **来源**：Reasonix 源码分析 + DeepSeek API 缓存机制
- **描述**：系统提示词（base prompt + tools + memory + skill 索引）在 session 内字节级不变；瞬时状态（plan mode、memory update、goal）走 XML 块拼到 user 消息尾部
- **参考**：Reasonix `internal/boot/boot.go` + `internal/control/input.go`
- **核心技术点**：
  - 前缀组装顺序：base prompt → output style → language → memory → skill 索引（仅名字+描述）
  - skill 正文按需加载，不进 prefix
  - plan mode 不改工具列表，执行时拦截写操作
  - 中途记忆更新用 `<memory-update>` XML 块附着 user turn
- **优先级**：P0（DeepSeek 专用版核心）
- **状态**：PRD 完成 ✅ → 并入 TASK-001

### IDEA-009：三层 Context 分区架构
- **来源**：Reasonix 架构设计
- **描述**：将发给 API 的 context 分为不可变前缀、追加日志、易失暂存三个区域
- **参考**：Reasonix context 三层分区
- **分区设计**：
  | 区 | 内容 | 缓存行为 |
  |----|------|---------|
  | 不可变前缀 | system + tools + memory | 整 session 命中缓存 |
  | 追加日志 | 对话历史（append-only） | 稳定增长，只有尾部 miss |
  | 易失暂存 | 推理过程、临时计划 | 不发给 API |
- **优先级**：P0（DeepSeek 专用版核心）
- **状态**：PRD 完成 ✅ → 并入 TASK-001

### IDEA-010：reasoning_content 精准处理 + Function Calling 适配层
- **来源**：Reasonix 协议层处理 + DeepSeek Function Calling 踩坑实录
- **描述**：处理 DeepSeek thinking 模式下的 reasoning_content 回传规则，以及 Function Calling 的多个兼容性陷阱
- **核心技术点**：
  - 带 tool_calls 的 assistant 消息：必须原样回传 `reasoning_content`，否则 400
  - 不带 tool_calls 的消息：不回传 reasoning_content，避免多余花费
  - `tool_choice="required"` 不像 OpenAI 倾向第一个函数，需显式指定
  - 多轮对话必须保留完整 tool_calls 历史
  - `temperature` 建议 ≤0.3 保证参数稳定
  - `deepseek-reasoner`（V4-Pro 思考模式）不支持 Function Calling
- **优先级**：P0（DeepSeek 专用版核心）
- **状态**：PRD 完成 ✅ → 并入 TASK-001

### IDEA-011：缓存诊断 + cache-guard 工程纪律
- **优先级**：P1
- **状态**：✅ 已交付 v0.2.0（TestReleaseCacheHitGuard）

### IDEA-012：Agent 角色预置 + 多 Skill 动态挂载
- **优先级**：P0
- **状态**：✅ 已交付 v0.3.0（body保留 + --attach + 双层prompt）

### IDEA-013：Code-Review Agent
- **优先级**：P0
- **状态**：✅ 已交付 v0.3.0（CR Agent SKILL.md + 审查四维度）

### IDEA-014：DevOps Agent
- **优先级**：P1
- **状态**：✅ 已交付 v0.4.0（skills/Luyi14-devops/SKILL.md）

### IDEA-015：Dispatcher 群聊入口
- **优先级**：P0
- **状态**：✅ 已交付 v0.3.0（--chat 模式 + 自动路由 PM Agent）

### IDEA-016：MCP 工具集成 + Agent 三层硬约束
- **优先级**：P1
- **状态**：✅ 已交付 v0.4.0（MCPClient + ToolGuard 三层约束）

### IDEA-018：真·Tauri 桌面应用（非 Webview 套壳）
- **优先级**：P0
- **状态**：✅ **已交付 vA.0.1**（Tauri v2 构建成功，8.4MB 原生 exe）

### IDEA-020：智能查询路由 — HyDE 改写 + 意图分解
- **来源**：架构讨论 — Dispatcher 增强
- **描述**：Dispatcher 根据查询复杂度分流：简单指令直路由（不改写），长难句先用 HyDE 生成假想文档再路由，多轮复杂意图用 Decomp 拆分子意图并行路由
- **关联**：IDEA-015 Dispatcher
- **优先级**：P1
- **状态**：等待 Spec

### IDEA-021：熔断机制 + 漂移检测
- **来源**：架构讨论 — "有防范查询漂移的熔断机制吗"
- **描述**：新增 CircuitBreaker（三态：CLOSED/OPEN/HALF_OPEN，连续失败计数 + 指数退避）+ DriftDetector（Agent 输出校验：字段完整性/类型匹配/置信度阈值）
- **关联**：LOOP SOP 降级触发规则
- **优先级**：P1
- **状态**：等待 Spec

### IDEA-022：Agent Memory 体系重构（SQLite + Flash Summary + RAG）
- **来源**：GPT/Gemini 记忆架构对照分析
- **描述**：新增 MemoryManager（SQLite 持久化 + Flash LLM 摘要 + 对话记忆 RAG + Consolidator 记忆合并/老化），整合现有 CacheEngine / ContextPartitioner / EmbeddingIndex 为统一记忆管线
- **关联**：IDEA-021 熔断（共享 Consolidator 老化机制）
- **设计要点**：
  - LocalStore：SQLite 三表（profiles / sessions / memory_log），零外部依赖
  - MemoryRouter：working→immutable / summary→Flash / episodic→SQLite / semantic→EmbeddingIndex
  - Consolidator：低价值记忆衰退 + 相似记忆融合
- **优先级**：P0（核心架构）
- **状态**：等待 Spec

## 📝 规划中

> 待排期：IDEA-022 (P0) Memory / IDEA-020 (P1) HyDE / IDEA-021 (P1) 熔断

---

## 🔨 开发中

> （暂无）

---

## ✅ 验收中

> （暂无）

---

## 🚀 已发布

> 已完成交付的任务。

### TASK-001：Skill → Agent 映射架构设计（DeepSeek 专用版） v0.1.0
- **验收结论**：✅ PASS
- **安全审计**：✅ PASS
- **测试覆盖**：29/29（100%）
- **版本快照**：`versions/v0.1.0/`

### TASK-002：编排调度 + 状态管理 + 开发工作流 + 独立部署 v0.2.0
- **验收结论**：✅ PASS
- **测试覆盖**：36/36（100%）
- **新增**：ParallelOrchestrator / CheckpointManager / dev workflow / FastAPI / cache-guard
- **版本快照**：`versions/v0.2.0/`

---

## ❌ 废弃

> IDEA-019（C++ 重构评估）已否决

### IDEA-019：C++ 重构评估（否决）
- **来源**：老板提问 — "需不需要 C++ 重构来提升利用率"
- **结论**：不需要。Python 胜任全部工作，瓶颈在 LLM 网络延迟。C++ 重构 = 投入 10 倍精力，收益 < 1%。

---

## 发布历史

| 版本 | 日期 | 内容 |
|------|------|------|
| vA.0.1 | 2026-07-15 | IDEA-018 真·Tauri 原生桌面（Rust 8.4MB exe + React invoke IPC） |
| Alpha 0.1 | 2026-07-14 | 首个公开发布 — Tauri桌面壳 + 11 Agent + 完整SOP管道，**想法池归零** |
| v0.4.0 | 2026-07-14 | TASK-004 MCP工具集成 + DevOps Agent（2×P1交付） |
| v0.3.0 | 2026-07-14 | TASK-003 Agent核心重构（body保留+双层prompt+Dispatcher+CR Agent，3×P0交付） |
| v0.2.0 | 2026-07-13 | TASK-002 编排调度+状态管理+工作流+部署+cache-guard（5 想法交付） |
| v0.1.0 | 2026-07-13 | TASK-001 Skill→Agent 映射引擎（6 P0 想法交付） |
| v0.0.1 | 2026-07-13 | 项目初始化 + Phase 0 调研完成 |

---

## 想法池评估规则

| 优先级 | 含义 | 入口条件 |
|--------|------|---------|
| P0 | 核心功能，不做项目不成立 | 直接进入 📝 规划中 |
| P1 | 重要功能，显著提升体验 | 排期后进入 📝 规划中 |
| P2 | 增强功能，锦上添花 | 资源允许时排期 |
| P3 | 探索性想法 | 暂不排期，持续观察 |

**流转规则**：想法池 → 编写 Spec → 规划中 → 开发 → 验收 → 发布
