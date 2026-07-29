# PRD: Human-in-the-Loop 审核 (IDEA-040)

## Why
Agent 的自动化动作可能错误。执行关键操作（git push、文件删除、API 调用）前需要人工确认。

## Requirements
- R1: SOP Node 声明 `requires_approval=True` 时暂停
- R2: `sop_runner.approve(node_id)` 恢复执行
- R3: `sop_runner.reject(node_id)` 跳过节点
- R4: CLI `jig approve <id>` / `jig reject <id>` 命令
- R5: 超时自动拒绝

## Tasks
1. SOPRunner pause/resume (2h)
2. CLI approve/reject (1h)
3. Integration tests (1.5h)

## Out of Scope
- Web UI 审批面板
- 多人审批工作流
