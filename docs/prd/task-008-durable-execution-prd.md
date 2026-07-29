# Spec: Durable Execution (IDEA-060)

## Why
SOP pipeline lacks long-running execution with interrupt/resume. Checkpoints exist but are file-based and synchronous.

## Requirements
- R1: `SOPRunner.arun()` async method for long-running pipelines
- R2: SQLite-based checkpoint persistence (replace `.sop_checkpoints/` files)
- R3: Resume from any completed node (not just last)
- R4: Timeout per node (configurable)
- R5: Webhook notification on completion/failure

## Tasks
1. SQLite checkpoint store (1h)
2. `SOPRunner.arun()` async method (2h)
3. Node-level timeout support (1h)
4. Resume from any node (1h)
5. Integration tests (1h)

## Out of Scope
- Distributed execution (single-process only)
- Queue/worker system
