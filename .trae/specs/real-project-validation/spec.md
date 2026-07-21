# Spec: Real Project Validation (IDEA-053)

**Version**: 1.0 · **Status**: Draft · **Owner**: Spec-Pipeline

## Why

The framework needs real user validation. Dogfooding AgentHarness on a real project will expose ≥10 genuine pain points that no amount of unit testing can find. The SOP pipeline — Dispatcher → PM → Trinity → Spec → Coding → Review → TDD → Acceptance ∥ Security → DevOps → Secretary — must complete end-to-end.

## Meta

- **Priority**: P0
- **Idea**: IDEA-053
- **Estimated effort**: 2 weeks (1d scope + 5d coding + 2d review + 2d fixes)
- **Validation**: docs/real-project-proposal.md

## What Changes

1. Run full SOP pipeline on a self-hosted code review of AgentHarness itself
2. Record every pain point (≥10)
3. Fix each pain point
4. Write case study document

## Requirements

- R1: Pipeline completes without manual intervention (max 3 overrides)
- R2: ≥10 real pain points documented and fixed
- R3: Case study published in docs/
