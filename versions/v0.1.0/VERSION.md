# 版本快照记录

## v0.1.0 (2026-07-13)
- **初始版本**：Jig 系统核心引擎
- **功能**：
  - Skill 定义格式解析器（YAML frontmatter → SkillDef）
  - Skill → Agent 映射引擎（SkillRegistry + AgentFactory）
  - DeepSeek Pro/Flash 双模型策略（独立 session）
  - 缓存前缀组装引擎（字节级不变性保障 + 变更检测）
  - reasoning_content + Function Calling 适配层
  - 三层 Context 分区架构（immutable/append-only/volatile）
  - SOP 编排调度器（顺序/层级）
  - CLI 自测脚本 + pytest 单元测试套件
- **测试覆盖**：29/29 全绿（7 自测 + 22 pytest）
- **验收**：✅ PASS | **安全**：✅ PASS
- **回退命令**：将 `versions/v0.1.0/*` 覆盖回项目根目录即可
