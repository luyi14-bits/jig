# CHANGELOG

All notable changes to this project will be documented in this file.

## [Alpha 0.2] - 2026-07-15

> IDEA-028 ~ IDEA-030 批次交付 — 版本对齐 + Skills 补齐 + 端到端测试

### Fixed
- 版本一致性问题 — README / CHANGELOG / server / 白皮书统一为 Alpha 0.2

## [Alpha 0.1] - 2026-07-14

> 首个公开发布版本。预置 11 个 Agent 角色，完整 SOS 管道，Tauri 桌面应用壳。

### Added
- Tauri v2 桌面应用壳（desktop/ 目录）
- React 前端框架（Vite + TypeScript）
- Agent 调度面板（11 个 Agent 状态可视化）
- 群聊输入模式（Dispatcher 路由）
- Rust 后端 `list_skills` + `run_pipeline` 命令对接 Python 引擎
- 5 轮 LOOP 迭代完成，25 个阶段全部 PASS

### Added — 上下文 5 层压缩体系
- RepoMap 代码图谱（`repo_map.py`）：tree-sitter 风格 AST 符号提取 + PageRank 排序
- 对话压缩器（`conversation_compressor.py`）：summarize/truncate/hybrid 三模式
- 向量检索索引（`embedding_index.py`）：语义搜索 skill body，支持离线关键词降级
- 缓存断点标记（`cache_engine.py`）：`mark_cache_breakpoint()` + `keepalive()` + `CacheStats`
- 自动压缩触发（`context.py`）：`compress_if_needed()` + `estimated_tokens()`

## [v0.4.0] - 2026-07-14

### Added
- MCP 客户端（web-search / fetch_page 内置工具）
- ToolGuard 三层硬约束（whitelist/denylist/PreToolUse hook）
- DevOps Agent（skills/Luyi14-devops/SKILL.md）
- 12 个 Skill 总加载（原有10 + Code-Review + DevOps）

## [v0.3.0] - 2026-07-14

### Added
- SkillParser 保留 SKILL.md body 全文 → Agent system prompt 使用 body（PM Agent: 60字→4692字）
- AgentFactory 双层 prompt 组装：全局约束（共享）+ 角色 body（专属）+ N×skill 挂载
- `global_constraints.py` — 所有 Agent 共享的不可变约束层（越权禁止/交接协议/留痕/安全）
- `--attach skill1,skill2` 参数 — 用户可动态挂载多 Skill，无需改代码
- `--chat` 群聊模式 — Dispatcher 入口，接收自然语言路由 PM Agent
- Code-Review Agent（`skills/Luyi14-code-review/SKILL.md`）
- Agent 自动 `write_log()` — 完成后自动写 LOG.md 留痕
- `agent_name` 字段 — frontmatter 自定义显示名

## [v0.2.0] - 2026-07-13

### Added
- ParallelOrchestrator：并行子 Agent 执行 + max_concurrency 控制
- CheckpointManager：JSON 检查点保存/恢复/resume
- 预定义开发工作流模板（brainstorm → plan → code → test → review）
- FastAPI 独立部署服务（POST /execute + GET /status）
- cache-guard CI 测试（TestReleaseCacheHitGuard）

### Testing
- 全量测试：36/36（+14 迭代 2 新增）

## [v0.1.0] - 2026-07-13

### Added
- Skill 定义格式解析器（YAML frontmatter → SkillDef）
- Skill → Agent 映射引擎（SkillRegistry + AgentFactory）
- DeepSeek Pro/Flash 双模型策略（独立 session 管理）
- 缓存前缀组装引擎（字节级不变性保障 + 变更检测）
- reasoning_content + Function Calling 适配层
- 三层 Context 分区架构（immutable/append-only/volatile）
- SOP 编排调度器（顺序/层级两种模式）
- CLI 自测脚本 auto_test.py（7/7 通过）
- pytest 单元测试套件（22/22 全绿）
- 验收报告 + 安全审计报告

### Changed
- 项目从 Phase 0 调研进入 Phase 1-4 完整开发迭代
- 管线看板 6 个 P0 想法 → 并入 TASK-001 交付

## [0.0.1] - 2026-07-13

### Added
- 项目创建
- 完成 Phase 0：开源 Agent 框架调研
