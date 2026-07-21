# 项目秘书 留痕日志

> 所属 Skill：Luyi14-project-secretary | 维护人：项目秘书
> 用途：记录本 Skill 专业领域驱动下的所有变更，便于事后追溯和定责。

---

## 2026-07-21

### 更新：管线看板 — goals-guide 目标迁移至想法池
- **触发者**：LOOP SOP (Luyi14-loop-sop)
- **触发材料**：docs/goals-guide.html 三阶段战略目标
- **变更类型**：看板更新 + 新 IDEA 创建
- **变更摘要**：从 goals-guide.html 提取目标，8 个已有 IDEA 补 `🎯 关联目标` 标注，新增 IDEA-052 (awesome PR) 写入想法池，IDEA-053/055/056/057 补标注
- **涉及文件**：`PIPELINE_KANBAN.md`（+约 30 行）
- **看板统计**：💡 7 项 | 📝 0 项 | 🔨 0 项 | ✅ 0 项 | 🚀 22 项 | ❌ 3 项
- **验证**：编译零错误，看板统计已更新

---

## 2026-07-21

### 更新：发布 AgentHarness 目标指南 v1.0

- **触发者**：项目秘书 (Luyi14-project-secretary)
- **触发材料**：老板指令"写个目标指南" + 项目现状盘点（Alpha 0.2，21 项交付，想法池清零）+ 2026 框架技术路线调研 + 5 个发展方向分析
- **变更类型**：文档产出（战略指南）
- **变更摘要**：
  - 产出项目北极星文档 `docs/goals-guide.html`，作为项目所有决策的判断依据
  - 明确使命：让每个开发者用 5 行代码构建有硬约束保障的、DeepSeek 缓存优化的 Agent
  - 一句话定位：唯一一个把 Harness 硬约束和 DeepSeek 缓存优化做到框架级别的 Agent 框架
  - 定义三阶段目标：
    - Phase 1 验证期（2026 Q3）：DeepSeek 生态卡位 + 真实项目验证
    - Phase 2 发布期（2026 Q4）：Beta → RC → v1.0 正式发布
    - Phase 3 深化期（2027 Q1-Q2）：12-Factor 全合规 + Harness 即服务
  - 明确战略边界（6 项不做）：不竞争 LangChain/LangGraph/CrewAI/DeerFlow 的强项
  - 定义 5 条决策准则：DeepSeek 优先 > Harness 优先 > 真实验证优先 > 差异化优先 > 简洁优先
  - 列出 12 个里程碑时间线（7 个已完成 + 5 个未来）
  - 5 项风险与应对策略
  - 本周立即行动：DS 优化自查 + 真实项目选题 + awesome-deepseek-agent 调研
- **涉及文件**：
  - `docs/goals-guide.html`（新建，443 行 HTML 文档）
- **验证**：
  - 文档结构完整：使命 → 当前阶段 → 三阶段目标 → 战略边界 → 决策准则 → 里程碑 → 风险 → 立即行动
  - KPI 可衡量：每阶段有具体数字指标（stars / 下载量 / 案例数等）
  - 与之前调研报告 `docs/framework-tech-routes-2026.html` 一致，无矛盾
  - 战略边界与决策准则可在后续决策中直接引用

---

## 2026-07-13

### 创建：项目初始化 + 管线看板 + 想法池
- **触发者**：项目秘书 (Luyi14-project-secretary)
- **触发材料**：老板需求（将 skill 变成独立 agent 协助开发软件）+ Phase 0 调研报告
- **变更类型**：项目创建
- **变更摘要**：
  - 审计根目录标准文件 → 创建 README.md、.gitignore、CHANGELOG.md
  - 创建管线看板 PIPELINE_KANBAN.md（6 列流转 + 7 项想法池 + 1 项规划中）
  - 想法池包含：Skill→Agent 映射引擎、Pro/Flash 混用、Tree-SOP 定义格式、编排调度器、状态管理、开发工作流、独立部署
  - 规划中：TASK-001 Skill→Agent 映射架构设计
- **涉及文件**：
  - `README.md`（新建）
  - `.gitignore`（新建）
  - `CHANGELOG.md`（新建）
  - `PIPELINE_KANBAN.md`（新建）
- **验证**：所有文件创建成功，结构树与实际目录一致

---

### 更新：管线看板第二轮 — DeepSeek 缓存优化策略
- **触发者**：项目秘书 (Luyi14-project-secretary)
- **触发材料**：老板需求（DeepSeek 专用版 + 缓存命中率）+ Reasonix 源码分析文章 + DeepSeek API 官方缓存文档 + Function Calling 踩坑实录
- **变更类型**：看板升级（想法池扩充 + TASK-001 范围更新）
- **变更摘要**：
  - 想法池从 7 项扩充到 11 项，新增 4 项 DeepSeek 专用版核心想法：
    - IDEA-008：缓存稳定前缀不变量（P0）
    - IDEA-009：三层 Context 分区架构（P0）
    - IDEA-010：reasoning_content + Function Calling 适配层（P0）
    - IDEA-011：缓存诊断 + cache-guard 工程纪律（P1）
  - TASK-001 范围更新：增加 DeepSeek 缓存优化策略 + 4 个关键决策点
  - 关键发现：Reasonix 达到 99.82% 缓存命中率的 7 层策略，一天 4.35 亿 token 仅花 $12
  - DeepSeek 缓存价格：Cache Hit 是 Cache Miss 的 1/50~1/120
- **涉及文件**：
  - `PIPELINE_KANBAN.md`（更新看板总览 + 新增 IDEA-008~011 + TASK-001 范围更新）
- **验证**：看板总览数字与实际条目数一致（11 项想法池 + 1 项规划中）

---

## 2026-07-15

### 更新：迭代 6 ~ 13 全量交付，想法池归零
- **触发者**：LOOP SOP 总调度
- **触发材料**：老板指令 "继续loop模式，直到将想法池清空"
- **变更类型**：全量交付
- **变更摘要**：
  - 迭代 6 (IDEA-022): Memory 体系重构 — MemoryManager + LocalStore + MemoryRouter + Consolidator
  - 迭代 7~11 (IDEA-025~027): ConfigManager + 显示名/模型/权限/风险模式
  - 迭代 12 (IDEA-020): IntentRouter — HyDE 改写 + Decomp 分解
  - 迭代 13 (IDEA-021): CircuitBreaker + DriftDetector
  - 全量测试 62/62 通过
- **涉及文件**：
  - `src/agent_harness/orchestrator/memory.py`（新建）
  - `src/agent_harness/orchestrator/intent_router.py`（新建）
  - `src/agent_harness/orchestrator/circuit_breaker.py`（新建）
  - `src/agent_harness/core/config_manager.py`（新建）
  - `PIPELINE_KANBAN.md`（想法池归零）
- **验证**：62/62 全部通过，全量打包成功

---

## 2026-07-16 ~ 2026-07-17

### 更新：Tauri 桌面应用调试 + 安全审计 + 框架定位转向
- **触发者**：技术路线讨论
- **触发材料**：桌面应用 API/MCP 保存 bug 排查 + Luyi14 技能全面审计
- **变更类型**：Bug 修复 + 文档产出
- **变更摘要**：
  - Tauri 端修复：camelCase 命令名 + emoji 解析 + invoke ES import + withGlobalTauri
  - 前端修复：onClick 传 event 修复 + 错误提示 + savedMsg 状态
  - 产出 3 份安全/漏洞/审计报告
  - 产出技术白皮书 v2
  - 定位从"Agent 产品"转向"自研多 Agent 框架"
  - 12 个文件推送 GitHub
- **涉及文件**：
  - `desktop/src/App.tsx`
  - `desktop/src-tauri/src/lib.rs`
  - `docs/security-vulnerabilities-alpha-0.2.md`（新建）
  - `docs/security-audit-alpha-0.2.md`（新建）
  - `docs/BUG_REPORT.md`（新建）
  - `docs/technical-whitepaper-v2.md`（新建）
- **验证**：全量构建成功，API/MCP/Skill 三个功能修复

---

## 2026-07-17

### 更新：框架定位确认 + 技术路线调研
- **触发者**：老板决策 — "我们是作为框架的话就不去重点搞具体的软件了"
- **触发材料**：10+ 框架调研 + 最新 GitHub 数据采集
- **变更类型**：战略转向
- **变更摘要**：
  - 确认自研多 Agent 框架定位
  - 更新 README：副标题改为"自研多 Agent 编排框架"
  - 产出框架对比报告 `docs/framework-comparison-report.md`
  - 识别差距三大 P0：PyPI 发布 / CI/CD / 英文文档
  - 想法池新增 13 个框架化 IDEA（036~048）
- **涉及文件**：
  - `README.md`（框架定位重写）
  - `docs/framework-comparison-report.md`（新建）
  - `PIPELINE_KANBAN.md`（想法池扩充到 13 项）
- **验证**：GitHub 已推送
