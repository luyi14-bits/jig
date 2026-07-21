# Spec: Harness as a Service (IDEA-057)

**Priority**: P1 | **Est**: 2 weeks

## Why
The hard-constraint Harness layer (ToolGuard + SOP gating) is AgentHarness's unique differentiator. Making it available as a standalone module lets LangGraph and CrewAI users adopt it without migrating frameworks.

## What Changes
1. ToolGuard modular extraction: whitelist/denylist/PreToolUse as independent module
2. SOP gate standalone: 5-stage gating with configurable checkers
3. LangGraph adapter example
4. CrewAI adapter example

## Merge Notes
Merges with IDEA-049 (External Agent Compatibility). Both require the same modularization.

## Requirements
- R1: `pip install agent-harness[harness]` installs just the Harness layer
- R2: LangGraph example runs end-to-end
- R3: CrewAI example runs end-to-end
