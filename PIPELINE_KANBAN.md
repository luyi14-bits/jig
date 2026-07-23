# 管线看板

> 最后更新：2026-07-20（最终轮：自查修正 + 全量交付） | 维护人：项目秘书
> 数据来源：需求对话 + 调研报告 + Reasonix 源码分析 + DeepSeek API 文档 + 2026 框架技术路线调研

---

## 看板总览

| 💡 想法池 | 📝 规划中 | 🔨 开发中 | ✅ 验收中 | 🚀 已发布 | ❌ 废弃 |
|-----------|-----------|-----------|-----------|-----------|---------|
| 15 项 | 8 项 | 0 项 | 0 项 | 29 项 | 3 项 |

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

### IDEA-032：pip 包发布
- **来源**：框架化基础设施
- **描述**：pyproject.toml 已就位
- **优先级**：P1
- **状态**：✅ 已交付（pyproject.toml 存在，可 pip install）

### IDEA-033：真实 LLM 冒烟测试
- **来源**：Alpha 0.2 规划
- **描述**：test_smoke_live.py，验证 DeepSeek API 可用（4 测试，需 API Key）
- **优先级**：P1
- **状态**：✅ 已交付（`tests/test_smoke_live.py`，4 测试需 API Key 运行）

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
- **🎯 关联目标**：goals-guide Phase 3 方向E — Harness 即服务

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
- **状态**：✅ 已有代码（`api.py` + `.trae/specs/framework-core-apis/`）

### IDEA-037：DeepSeek 深度优化包
- **来源**：awesome-deepseek-agent 对标 — 目标进入官方推荐列表
- **描述**：聚焦 DeepSeek V4 极致优化，暂缓多模型抽象。把 DS 优化到标杆水平后再做泛化
- **对标**：Reasonix / Pi / Deep Code — deepseek-chat 官方生态
- **核心技术点**：
  - reasoning_effort 可配置接口（对标 Pi thinkingLevelMap / Deep Code reasoningEffort）
  - reasoning_content 精准处理 + token 计量（已有，需增强）
  - DeepSeek 专用参数透传（top_p、frequency_penalty 等）
  - thinking 模式下 token 预算控制
  - 多模型抽象延后到 v2
- **优先级**：P0（DS 优先，官方曝光）
- **状态**：等待 Spec
- **🎯 关联目标**：goals-guide Phase 1 方向D — 进入 awesome-deepseek-agent 推荐列表

### IDEA-050：DeepSeek 成本感知调度
- **来源**：awesome-deepseek-agent — Reasonix flash-first cost control
- **描述**：在 ModelRouter 基础上增加成本感知层。默认 Flash，Token 预算内自动，复杂度超阈值自动升级 Pro
- **对标**：Reasonix — 默认 Flash /pro /preset max
- **核心技术点**：
  - 默认策略：所有 Agent 默认用 Flash，Token 预算内自动
  - 智能切换：复杂度检测 → 自动升级到 Pro（类似 Reasonix /pro）
  - 成本追踪：每次 API 调用记录 token 消耗 + 费用
  - 预算上限：session 级 / 月度 Token 预算，超限熔断
  - 缓存节省可视化：每次请求展示 Cache Hit/Miss 费用对比
- **优先级**：P0
- **状态**：✅ 代码已交付（`cost_aware_router.py`）

### IDEA-051：自动 Tool-Call Repair
- **来源**：awesome-deepseek-agent — Reasonix automatic tool-call repair
- **描述**：DeepSeek Function Calling 返回格式错误时自动修复，而非直接失败
- **对标**：Reasonix — 内置 tool-call repair，DeepSeek API 兼容性自愈
- **核心技术点**：
  - JSON 解析修复：FC 返回非标准 JSON 时自动纠正常见错误
  - 参数补齐：缺失必填参数时，基于上下文推断默认值
  - 重试策略：修复失败 → 错误注入下一轮 prompt，最多重试 3 次
  - 降级路径：FC 反复失败 → 降级为纯文本模式
- **优先级**：P1
- **状态**：等待 Spec
- **🎯 关联目标**：goals-guide Phase 1 方向D — Tool-Call Repair 是 PR 差异化亮点之一

### IDEA-052：awesome-deepseek-agent 提 PR
- **来源**：goals-guide Phase 1 方向D
- **描述**：对照 awesome-deepseek-agent 已推荐项目（Reasonix / Pi / Deep Code），补齐差距后向仓库提 PR，目标进入官方推荐列表
- **核心行动**：
  - DS 优化自查 → 列出差距清单（缓存/成本/FC修复/MCP）
  - awesome-deepseek-agent 仓库调研 → 阅读收录标准（双语+模型命名+1M上下文）
  - 准备 PR 素材（对比表 + guide 文档）
- **指标**：GitHub stars 100+，DS 官方社交媒体至少 1 次提及
- **优先级**：P0
- **状态**：等待 Spec
- **🎯 关联目标**：goals-guide Phase 1 方向D + 立即行动 #1, #3

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
- **🎯 关联目标**：goals-guide Phase 3 方向B — 12-Factor #11 OTel

### IDEA-039：结构化输出验证
- **来源**：12-Factor Agents #4
- **描述**：所有 Agent 输出必须是结构化的、可验证的，基于 Pydantic Model 自动校验
- **对标**：PydanticAI 的结构化输出 + LangGraph 的 state schema
- **优先级**：P1（12-Factor 合规）
- **状态**：等待 Spec
- **🎯 关联目标**：goals-guide Phase 3 方向B — 12-Factor #4 结构化输出

### IDEA-040：Human-in-the-Loop API
- **来源**：12-Factor Agents #9
- **描述**：为关键决策提供标准化的 HITL 介入点 API（审批 / 修改 / 否决 / 补充信息）
- **对标**：LangGraph 的 interrupt_before / interrupt_after + MS Agent FW 的审批中间件
- **优先级**：P1（12-Factor 合规）
- **状态**：等待 Spec
- **🎯 关联目标**：goals-guide Phase 3 方向B — 12-Factor #9 HITL

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
- **状态**：✅ 已交付（`loop_engine.py` + 20 测试）
- **🎯 关联目标**：goals-guide Phase 3 方向B — Loop Engineering 框架级

### IDEA-042：pip 包发布 + 文档站点
- **来源**：框架化必备基础设施
- **描述**：pyproject.toml + pip install agent-harness + 文档站点（快速开始 / API 参考 / 示例）
- **对标**：LangGraph / CrewAI / PydanticAI 文档质量
- **优先级**：P1
- **状态**：等待 Spec（IDEA-032 升级版）
- **🎯 关联目标**：goals-guide Phase 2 方向A — pip包+文档站点+示例

### IDEA-043：框架技术路线文档化
- **来源**：2026 框架技术路线调研
- **描述**：明确架构归属 — "Harness + 混合编排"创新路线
- **产出**：技术白皮书 v3：框架化架构设计（已交付）
- **优先级**：P1
- **状态**：✅ **已交付**（`docs/technical-whitepaper-v3.md` 15KB）

### IDEA-044：MCP 协议完整支持
- **来源**：2026 跨框架标准 — MCP 协议
- **描述**：MCP Server + Client 双向支持（代码已存在：`mcp_protocol.py`），让 Jig 可作为 MCP 工具被其他框架调用
- **对标**：CrewAI v1.10.1 MCP 集成
- **优先级**：P0
- **状态**：✅ **规划中**（代码已存在：`src/jig/adapters/mcp_protocol.py`）

### IDEA-045：A2A 协议探索
- **来源**：2026 跨框架通信标准 — A2A
- **描述**：探索 Agent-to-Agent Protocol，允许 Jig 与其他框架的 Agent 跨框架协作
- **对标**：CrewAI A2A 协议
- **优先级**：P1（升级 — 跨框架协作通道）
- **状态**：等待 Spec

### IDEA-047：框架级缓存诊断面板
- **来源**：IDEA-011 升级 + DeepSeek 缓存优化差异化
- **描述**：将 cache-guard 从测试工具升级为框架级缓存诊断面板，可视化展示前缀命中率 / 冷启动 / 缓存节省成本
- **优先级**：P1
- **状态**：✅ 已交付（`cache_diagnostics.py` + 5 测试）

### IDEA-048：Skill 插件市场
- **来源**：对标 Superpowers Skill 生态
- **描述**：建立 Skill 插件分发机制，开发者可发布和安装第三方 SKILL.md 包
- **优先级**：P3
- **状态**：等待 Spec

### IDEA-049：外部 Agent 兼容层（Meta-Harness）
- **来源**：框架双模定位 — "既要提供 Agent，也要兼容外部 Agent" + 对标 Omnigent
- **描述**：提供统一的外部 Agent 适配接口，让 Claude Code / Codex / Cursor / Pi 等第三方 Agent 能接入 Jig 的硬约束管控体系
- **对标**：Omnigent（7.5k★）— meta-harness 统一编排 + Policy 审批
- **核心技术点**：
  - ExternalAgentAdapter 抽象基类：start / send / stop / observe
  - 预置适配器：ClaudeCodeAdapter / CodexAdapter / PiAdapter
  - Harness 穿透：外部 Agent 工具调用经过 ToolGuard 三层拦截
  - 管道接入：外部 Agent 可作为 SOP 管道中的一个节点
  - 混合编排：内置 Agent（13 角色）+ 外部 Agent 在同一管道中协作
- **与 Omnigent 差异**：Omnigent Harness 外挂（事后审批），Jig ToolGuard 内置（事前阻断）
- **优先级**：P0（框架双模核心）
- **状态**：✅ **规划中**（Spec 已就位：`.trae/specs/ds-ecosystem-pr/`）

### IDEA-053：真实项目验证
- **来源**：goals-guide.html Phase 1 方向 C
- **描述**：用 Jig 完成 1 个真实小项目（Web 工具 / 数据处理 / 内部工具），从 0 到 1 跑通全链路，记录每个痛点
- **指标**：1 份案例文档，暴露并修复 ≥10 个真实痛点
- **优先级**：P0（验证期核心）
- **状态**：✅ **规划中**（Spec 已就位：`.trae/specs/real-project-validation/`）

### IDEA-055：示例库（3 个完整示例）
- **来源**：goals-guide.html Phase 2 方向 A
- **描述**：3 个完整示例（1 个 Web 工具 + 1 个数据处理 + 1 个代码审查 Agent）
- **优先级**：P1
- **状态**：等待 Spec
- **🎯 关联目标**：goals-guide Phase 2 方向A

### IDEA-056：社区运营
- **来源**：goals-guide.html Phase 2 方向 A
- **描述**：GitHub Discussions 开启 + README 打磨 + 贡献指南完善
- **优先级**：P1
- **状态**：等待 Spec
- **🎯 关联目标**：goals-guide Phase 2 方向A

### IDEA-057：版本治理（Beta→RC→v1.0）
- **来源**：goals-guide.html Phase 2 方向 A
- **描述**：Beta → RC → v1.0 三轮发布，每轮收集用户反馈
- **优先级**：P1
- **状态**：✅ **规划中**（Spec 已就位：`.trae/specs/examples-community/`）
- **🎯 关联目标**：goals-guide Phase 2 方向A

### IDEA-058：多模型支持
- **来源**：gap-vs-5-frameworks.md 致命缺失
- **描述**：LLM Provider 抽象层，支持 OpenAI / Anthropic / Ollama / 本地模型
- **核心行动**：BaseLLM 抽象接口 → DeepSeekProvider / OpenAIProvider / AnthropicProvider → ModelRouter 泛化
- **优先级**：P0（框架不成立）
- **状态**：等待 Spec

### IDEA-059：流式输出
- **来源**：gap-vs-5-frameworks.md 致命缺失
- **描述**：run() → run_stream() 异步迭代器，SOP 节点级 yield 实时推送
- **核心行动**：StreamingOrchestrator → Dispatcher.stream() → SOP 节点 yield
- **优先级**：P0（框架不成立）
- **状态**：等待 Spec

### IDEA-060：Durable Execution
- **来源**：gap-vs-5-frameworks.md 重大缺失
- **描述**：中断恢复 + 长时间运行。CheckpointManager 提升到框架级
- **核心行动**：SOP 管道节点执行后自动保存 → 崩溃恢复 → 异步长时间运行
- **优先级**：P1
- **状态**：等待 Spec

### IDEA-061：Graph 工作流
- **来源**：gap-vs-5-frameworks.md 重大缺失
- **描述**：图编排替代线性管道。GraphOrchestrator 节点=Agent 边=条件/上下文/超时
- **核心行动**：GraphNode + GraphEdge 定义 → 条件路由 → 自环 → 递归
- **优先级**：P1
- **状态**：等待 Spec

### IDEA-062：Evals 评测系统
- **来源**：gap-vs-5-frameworks.md 重大缺失
- **描述**：系统化 Agent 精度评测，结合 LoopEngine QualityValidator 做自动化评估
- **核心行动**：EvalRunner → 测试集定义 → 自动评分 → 回归报告
- **优先级**：P2
- **状态**：等待 Spec

### IDEA-063：Agent Runtime + 协作恢复机制
- **来源**：老板战略调整 — 框架重心从 prompt 转向 runtime
- **描述**：Agent 不应只是"高级 Skill"，而应具备：状态机(idle/running/waiting/error/recovered/done)、生命周期(on_init/on_run/on_pause/on_resume/on_error/on_stop)、执行的上下文、Memory、工具集、周期
- **核心技术点**：
  - Agent Runtime 状态机 + 生命周期钩子
  - Checkpoint→Rollback→Replay 闭环（自动保存、失败回滚、重放）
  - 协作机制：失败 escalation、recovery chain、Agent 间协商
  - 统一 CheckpointManager（合并 loop_engine 和 orchestrator 的两套实现）
- **优先级**：P0（框架核心方向）
- **状态**：等待 Spec

## 📝 规划中

### Loop 合并组

| Loop | 合并 | 工时 | 包含 IDEA |
|:----:|------|:---:|:---------:|
| #1 | awesome PR | 1天 | 052 |
| #2 | **多模型 + 流式** | 4天 | 058+059 |
| #3 | **Durable + Graph** | 7天 | 060+061 |
| #4 | 真实项目验证 | 3天 | 053 |
| #5 | pip + 文档站点 | 2天 | 042 |
| #6 | **OTel + Evals** | 4天 | 038+062 |

> 已就位 Spec：IDEA-052 → `.trae/specs/ds-ecosystem-pr/`
> IDEA-053 → `.trae/specs/real-project-validation/`
> IDEA-055/056/057 → `.trae/specs/examples-community/`

> 优先级 P0 任务：058+059 多模型+流式 / 052 awesome PR / 053 真实项目 / 049 外部Agent / 044 MCP

---

## 🔨 开发中

> Loop #4 — IDEA-053 真实项目验证（狗食自审）

> 执行：全 SOP 管道自审 AgentHarness 自身代码库

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
