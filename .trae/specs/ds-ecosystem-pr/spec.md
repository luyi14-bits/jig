# Spec: DeepSeek Ecosystem PR (IDEA-052)

**Version**: 1.0 · **Status**: Draft · **Owner**: Spec-Pipeline

---

## Why

AgentHarness has unique DeepSeek optimizations (prefix hashing, Tool-Call Repair, CostAwareRouter) that differentiate it from other agent frameworks. The `awesome-deepseek-agent` repository is the official DeepSeek ecosystem showcase with 4.8k★. Being listed there validates the framework and drives initial adoption.

## Meta

- **Priority**: P0
- **Idea**: IDEA-052
- **Estimated effort**: 3 days (1d gap analysis + 1d code fix + 1d PR + review)
- **Dependencies**: IDEA-037 (DS optimizations), task-005-deepseek-optimization

## What Changes

1. Fix model naming (`deepseek-chat` → `deepseek-v4-flash`) across 3 files (DONE)
2. Produce gap analysis document (DONE: `docs/deepseek-gap-analysis.md`)
3. Write bilingual PR guide (DONE: `docs/awesome-deepseek-agent-guide.md` + `zh-CN.md`)
4. Submit PR to awesome-deepseek-agent
5. Get PR reviewed and merged

## Impact

| File | Action |
|------|--------|
| `src/agent_harness/settings.py` | MODEL DONE |
| `src/agent_harness/adapters/deepseek_adapter.py` | MODEL DONE |
| `src/agent_harness/adapters/conversation_compressor.py` | MODEL DONE |
| `docs/deepseek-gap-analysis.md` | ADDED |
| `docs/awesome-deepseek-agent-guide.md` | ADDED |
| `docs/awesome-deepseek-agent-guide.zh-CN.md` | ADDED |

## Requirements

### ADDED

- R1: Model names must use `deepseek-v4-pro`/`deepseek-v4-flash` (not deprecated `deepseek-chat`)
- R2: PR guide must be bilingual (English + Simplified Chinese)
- R3: PR guide must include installation, configuration, first-run, and DeepSeek optimization sections
- R4: PR guide must include up-to-date pricing table from DeepSeek API docs
- R5: README table entry must be inserted in alphabetical order

### Scenario (Gherkin)

```gherkin
Feature: Awesome DeepSeek PR Submission

  Scenario: Submit PR
    Given all model names use v4 format
    And bilingual guide documents exist
    When I open a PR to awesome-deepseek-agent
    Then the CI checks pass
    And the maintainer reviews within 2 weeks
```
