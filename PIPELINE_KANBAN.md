# 管线看板

> 最后更新：2026-07-20（第二十轮：桌面归档 + 框架化战略转向） | 维护人：项目秘书
> 数据来源：需求对话 + 调研报告 + Reasonix 源码分析 + DeepSeek API 文档 + 2026 框架技术路线调研

---

## 看板总览

| 💡 想法池 | 📝 规划中 | 🔨 开发中 | ✅ 验收中 | 🚀 已发布 | ❌ 废弃 |
|-----------|-----------|-----------|-----------|-----------|---------|
| 11 项 | 0 项 | 0 项 | 0 项 | 12 项 | 3 项 |

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
- **优先级**：P1
- **状态**：✅ **已交付**（intent_router.py: classify_query + hyde_rewrite + decomp_intent）

### IDEA-021：熔断机制 + 漂移检测
- **优先级**：P1
- **状态**：✅ **已交付**（circuit_breaker.py: CircuitBreaker + DriftDetector）

### IDEA-022：Agent Memory 体系重构（SQLite + Flash Summary + RAG）
- **优先级**：P0
- **状态**：✅ **已交付 vA.0.2**（MemoryManager + LocalStore + MemoryRouter + Consolidator）

### IDEA-023：Agent 自定义显示名（非覆盖映射）
- **优先级**：P1
- **状态**：✅ **已交付**（ConfigManager.set_agent_display_name）

### IDEA-024：Agent 模型分配自定义（Pro/Flash 覆盖）
- **优先级**：P0
- **状态**：✅ **已交付**（ConfigManager.agent_overrides.model）

### IDEA-025：DS API Key + MCP Server 配置界面
- **优先级**：P0
- **状态**：✅ **已交付**（ConfigManager + config.json 持久化）

### IDEA-026：工具白名单 & 用户自定义权限
- **优先级**：P1
- **状态**：✅ **已交付**（ConfigManager.agent_overrides.allow_tools / deny_tools）

### IDEA-027：风险模式（God Mode）
- **优先级**：P1
- **状态**：✅ **已交付**（ConfigManager.enable_risk_mode / risk_mode_acknowledged_at）

### IDEA-031：Tauri 桌面应用增强（已废弃）
- **优先级**：P1
- **状态**：已废弃（战略调整：专注框架核心）

### IDEA-032：pip 包发布
- **来源**：Alpha 0.2 规划
- **描述**：添加 pyproject.toml，支持 pip install
- **优先级**：P1
- **状态**：等待 Spec

### IDEA-033：真实 LLM 冒烟测试
- **来源**：Alpha 0.2 规划
- **描述**：test_smoke_live.py，验证 DeepSeek API 可用
- **优先级**：P1
- **状态**：等待 Spec

### IDEA-034：用户指南
- **来源**：Alpha 0.2 规划
- **描述**：docs/user-guide.md — 快速开始 / CLI 使用 / Skill 自定义
- **优先级**：P2
- **状态**：等待 Spec

### IDEA-035：FastAPI 服务增强
- **来源**：Alpha 0.2 规划
- **描述**：异步执行 + 持久化 + token 认证
- **优先级**：P2
- **状态**：等待 Spec

---

> ⚡ **战略转向（2026-07-20）**：以下 IDEA-036~048 基于框架技术路线深度调研，将 Tree-SOP 从"Agent 应用"升级为"Agent 框架"。
> 调研报告：`docs/framework-tech-routes-2026.html`
> 核心壁垒：Harness 硬约束 + 四层记忆 + DeepSeek 缓存优化 + Skill→Agent 映射

### IDEA-036：公开 SDK API 设计
- **来源**：2026 框架技术路线调研 — 对标 PydanticAI
- **描述**：设计面向外部开发者的公开 API（Agent / Tool / Harness / Memory 四层接口），让其他开发者能基于 Tree-SOP 构建自己的 Agent
- **对标**：PydanticAI 的 `Agent / Tool / Dependencies` 三层抽象
- **核心技术点**：
  - Agent 定义接口：role + goal + tools + model + harness_config
  - Tool 注册接口：类型安全的函数注册 + 白名单/黑名单
  - Harness 配置接口：ToolGuard 级别 + LOOP SOP 门禁级别
  - Memory 配置接口：四层记忆可独立开关 + 后端选择
- **优先级**：P0（框架化基石）
- **状态**：等待 Spec

### IDEA-037：LLM Provider 抽象层
- **来源**：2026 框架技术路线调研 — 对标 Spring AI ChatClient
- **描述**：抽象 LLM 调用层，从 DeepSeek 专用扩展为多模型适配（DeepSeek / OpenAI / Anthropic / Ollama），同时保留 DeepSeek 缓存优化作为差异化特性
- **对标**：Spring AI 的统一 ChatClient 接口 + PydanticAI 的模型无关设计
- **核心技术点**：
  - LLMProvider 抽象基类：chat / chat_stream / embed / function_call
  - DeepSeekProvider：保留前缀 hash 缓存优化 + reasoning_content 处理
  - OpenAIProvider / AnthropicProvider：标准适配
  - 模型分配策略：per-agent model binding（Pro/Flash 混用）
- **优先级**：P0（框架化基石）
- **状态**：等待 Spec

### IDEA-038：OpenTelemetry 可观测性接入
- **来源**：12-Factor Agents #11 + 对标 MS Agent FW
- **描述**：接入 OpenTelemetry 标准，提供完整的调用链追踪、性能指标采集、异常监控
- **对标**：MS Agent FW 的 OTel 原生 + LangGraph 的 LangSmith 追踪
- **核心技术点**：
  - Agent 执行 Trace：每次 Agent 调用生成 Span
  - Tool 调用 Trace：工具名 + 参数 + 耗时 + 结果
  - Memory 操作 Trace：缓存命中/未命中 + 上下文压缩
  - Harness 门禁 Trace：LOOP SOP 5 级门禁通过/拦截
  - Metrics：token 用量 / API 耗时 / 缓存命中率 / 熔断次数
- **优先级**：P1（12-Factor 合规）
- **状态**：等待 Spec

### IDEA-039：结构化输出验证
- **来源**：12-Factor Agents #4
- **描述**：所有 Agent 输出必须是结构化的、可验证的，基于 Pydantic Model 自动校验
- **对标**：PydanticAI 的结构化输出 + LangGraph 的 state schema
- **优先级**：P1（12-Factor 合规）
- **状态**：等待 Spec

### IDEA-040：Human-in-the-Loop API
- **来源**：12-Factor Agents #9
- **描述**：为关键决策提供标准化的 HITL 介入点 API（审批 / 修改 / 否决 / 补充信息）
- **对标**：LangGraph 的 interrupt_before / interrupt_after + MS Agent FW 的审批中间件
- **优先级**：P1（12-Factor 合规）
- **状态**：等待 Spec

### IDEA-041：Loop Engineering 工程化
- **来源**：2026 Agent 核心话题 — Loop Engineering
- **描述**：将 LOOP SOP 从应用级硬编码提升为框架级可配置的 Loop Engine，解决五个核心问题
- **核心技术点**：
  - Loop 运行：任务递归分解 + 工具调用策略可配置
  - Loop 停止：退出条件检测器（收敛检测 / 最大轮次 / 人工终止）
  - Loop 验证：中间结果自动质量评估
  - Loop 恢复：检查点粒度可配置（节点级 / 执行器级 / 任务级）
  - Loop 调试：全链路事件日志 + 回放
- **优先级**：P0（2026 核心差异化）
- **状态**：等待 Spec

### IDEA-042：pip 包发布 + 文档站点
- **来源**：框架化必备基础设施
- **描述**：pyproject.toml + pip install tree-sop-agent + 文档站点（快速开始 / API 参考 / 示例）
- **对标**：LangGraph / CrewAI / PydanticAI 文档质量
- **优先级**：P1
- **状态**：等待 Spec（IDEA-032 升级版）

### IDEA-043：框架技术路线文档化
- **来源**：2026 框架技术路线调研
- **描述**：明确 Tree-SOP 的架构归属 — "Harness + 混合编排"创新路线，与七大模式的关系文档化
- **产出**：
  - 架构决策记录（ADR）：为什么选 Harness 路线而非图状态机/角色团队
  - 技术白皮书 v3：框架化架构设计
  - 对标文档：vs LangGraph / CrewAI / MS Agent FW / PydanticAI
- **优先级**：P1
- **状态**：等待 Spec

### IDEA-044：MCP 协议完整支持
- **来源**：2026 跨框架标准 — MCP 协议
- **描述**：从 MCPClient 基础集成升级为完整 MCP Server + Client 双向支持，让 Tree-SOP Agent 可作为 MCP 工具被其他框架调用
- **对标**：CrewAI v1.10.1 MCP 集成
- **优先级**：P1
- **状态**：等待 Spec（IDEA-016 升级版）

### IDEA-045：A2A 协议探索
- **来源**：2026 跨框架通信标准 — A2A
- **描述**：探索 Agent-to-Agent Protocol，允许 Tree-SOP Agent 与其他框架的 Agent 跨框架协作
- **对标**：CrewAI A2A 协议
- **优先级**：P2
- **状态**：等待 Spec

### IDEA-046：可视化编排界面
- **来源**：对标 LangGraph Studio / Google ADK
- **描述**：在 Tauri 桌面应用中增加可视化编排器，支持拖拽式 Agent 工作流构建
- **对标**：LangGraph Studio / Spring AI Alibaba Admin / Google ADK 可视化构建器
- **优先级**：P2
- **状态**：等待 Spec（IDEA-031 升级版）

### IDEA-047：框架级缓存诊断面板
- **来源**：IDEA-011 升级 + DeepSeek 缓存优化差异化
- **描述**：将 cache-guard 从测试工具升级为框架级缓存诊断面板，可视化展示前缀命中率 / 冷启动 / 缓存节省成本
- **优先级**：P1
- **状态**：等待 Spec

### IDEA-048：Skill 插件市场
- **来源**：对标 Superpowers Skill 生态
- **描述**：建立 Skill 插件分发机制，开发者可发布和安装第三方 SKILL.md 包
- **优先级**：P3
- **状态**：等待 Spec

## 📝 规划中

> 所有想法池等待排期，优先级 P0 的 IDEA-036/037/041 为框架化第一批任务

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
- **结论**：Python 胜任全部工作，瓶颈在 LLM 网络延迟。

### IDEA-031：Tauri 桌面应用增强（已废弃）
- **来源**：战略调整
- **结论**：聚焦框架核心，桌面不再投入

### IDEA-046：可视化编排界面（已废弃）
- **来源**：战略调整
- **结论**：与 IDEA-031 同步废弃，专注框架核心

---

## 发布历史

| 版本 | 日期 | 内容 |
|------|------|------|
| Alpha 0.2 | 2026-07-15 | IDEA-028~030 版本对齐 + Skills 补齐(5→12) + E2E 集成测试 |
| vA.0.3 | 2026-07-15 | IDEA-025~027 配置+权限+风险模式 + IDEA-020 HyDE + IDEA-021 熔断，**想法池归零** |
| vA.0.2 | 2026-07-15 | IDEA-022 Memory 体系重构（SQLite + MemoryRouter + Consolidator） |
| vA.0.1 | 2026-07-15 | IDEA-018 真·Tauri 原生桌面（Rust 8.4MB exe + React invoke IPC） |
| Alpha 0.1 | 2026-07-14 | 首个公开发布 — Tauri桌面壳 + 11 Agent + 完整SOP管道 |
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
