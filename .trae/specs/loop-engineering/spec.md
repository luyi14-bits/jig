# Spec: Loop Engineering Framework (IDEA-041)

**Priority**: P0 | **Est**: 2 weeks

## Why
LOOP SOP is hardcoded in application layer. Adding new Agent roles requires manual scheduler modification. In 2026, Loop Engineering is a core differentiator for Agent frameworks.

## What Changes
1. Loop Run: recursive task decomposition + configurable tool strategy
2. Loop Stop: convergence detection / max iterations / manual terminate
3. Loop Validate: auto quality assessment of intermediate results
4. Loop Restore: configurable checkpoint granularity (node/executor/task)
5. Loop Debug: full event log + replay

## BREAKING
`OrchestratorBase` interface must be refactored. Only affects internal orchestration code; public API unchanged.

## Requirements (Gherkin)
```gherkin
Feature: Loop Engineering
  Scenario: Configured loop runs with convergence detection
    Given a LoopEngine with max_iterations=10
    When the loop runs 5 iterations and converges
    Then the loop stops with status "converged"
    And the checkpoints are restorable
```
