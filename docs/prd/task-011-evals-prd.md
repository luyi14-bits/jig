# PRD: Evals 评测系统 (IDEA-062)

## Why
框架需要量化评测：每次 Agent 响应是否正确、是否有害、是否满足 SOP 标准。

## Requirements
- R1: 评测集定义（JSON: input + expected output + criteria）
- R2: `jig eval <dataset>` 命令
- R3: 指标：准确率 / 有害率 / SOP 符合率
- R4: 评测报告输出 (JSON/Markdown)
- R5: Diff 模式：两次评测结果对比

## Tasks
1. EvalRunner class (2h)
2. 内置评测集 (sop_follow、harmlessness) (1h)
3. CLI eval 命令 (1h)
4. Report generator (1h)
5. Integration tests (1h)

## Out of Scope
- 用户反馈在线收集
- A/B 测试平台
