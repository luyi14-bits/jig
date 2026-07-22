# Jig — Technical Whitepaper v4

> **Version**: Alpha 0.2 | Framework Architecture Edition  
> **Date**: 2026-07-22  
> **Audience**: Developers evaluating Jig as their agent framework

---

## 0. Executive Summary

Jig is an **agent framework** — a tool for developers to build their own agents. It provides: (1) a **hard-constraint Harness layer** (ToolGuard) that intercepts tool calls *before* execution, (2) **DeepSeek-native optimization** (SHA-256 prefix caching, cost-aware routing), and (3) a **complete SOP pipeline** for multi-agent collaboration.

**Key metrics**: 41 modules · 112 tests · 12 preset agents · Multi-model (DeepSeek + OpenAI) · Graph orchestration · SSE streaming

---

## 1. Why Another Agent Framework?

The agent framework landscape divides into two camps:

| Camp | Examples | Gap |
|------|----------|-----|
| **Orchestration frameworks** | LangGraph, CrewAI, PydanticAI | No hard-constraint safety — all rely on prompt-only guardrails that agents can bypass |
| **Agent apps** | Reasonix, Deep Code, Pi | Terminal tools for end users, not frameworks for developers |

Jig fills the gap: a **framework** (for developers, `pip install jig`) with **hard-constraint safety** (ToolGuard pre-execution interception) that neither camp provides.

### What Jig does that others don't

| Capability | Jig | LangGraph | CrewAI | PydanticAI |
|-----------|:---:|:---------:|:------:|:----------:|
| Pre-execution tool interception | ✅ **ToolGuard** | ❌ | ❌ | ❌ |
| DeepSeek SHA-256 prefix caching | ✅ | ❌ | ❌ | ❌ |
| Loop convergence engine | ✅ | ❌ | ❌ | ❌ |
| Cost-aware routing (Flash/Pro) | ✅ | ❌ | ❌ | ❌ |

---

## 2. Five-Layer Architecture

```
Control Plane (Harness):   LOOP SOP · ToolGuard · GlobalConstraints · CircuitBreaker
Agent Plane:               SkillParser → SkillRegistry → AgentFactory → Agents
Orchestration Plane:       Sequential · Parallel · Graph · LoopEngine · Checkpoint
Tool Plane:                MCPClient·Server · RepoMap · EmbeddingIndex · ModelRouter
Plugin Plane:              VisionTool · ImageReader · PluginMarket (optional contrib)
```

### Control Plane
Enforces safety and process across all agents. Immutable — agents cannot modify their own constraints.

### Agent Plane
Converts SKILL.md definitions into runnable Agent instances. The SkillParser validates frontmatter, extracts body, and passes to AgentFactory for instantiation.

### Orchestration Plane
Drives the SOP pipeline. Supports sequential, parallel, hierarchical, and graph-based execution. The LoopEngine adds convergence detection and event replay.

### Tool Plane
Manages tool access. Every tool call passes through ToolGuard's three-layer check: whitelist → denylist → PreToolUse hook.

### Plugin Plane
Optional capability extensions (VisionTool, ImageReader, etc.) that are not part of the core framework.

---

## 3. Harness: The Hard-Constraint Layer

### ToolGuard — 3-Layer Interception

```
Agent Tool Call
      │
      ▼
 [Layer 1: Whitelist]  ── Fail → Block + Log (violation recorded)
      │ Pass
      ▼
 [Layer 2: Denylist]   ── Hit  → Block + Log 
      │ Pass
      ▼
 [Layer 3: PreToolUse Hook] ── Fail → Block + Log
      │ Pass
      ▼
   Execute Tool
```

### LOOP SOP — 5-Stage Gating

| Gate | Entry | Pass Criteria |
|------|-------|--------------|
| G0→1 | Raw idea | PRD complete + priority set + Out of Scope |
| G1→2 | PRD accepted | Spec + Tasks + Checklist ready |
| G2→3 | Spec accepted | Self-test exit(0) + tests green |
| G3→4 | Code submitted | Acceptance PASS + Security zero-red |
| G4→end | Release ready | Version snapshot + Kanban + trace log |

---

## 4. Memory Architecture

| Layer | Component | Mechanism | Scope |
|:-----:|-----------|-----------|:-----:|
| 1 | CacheEngine | SHA-256 prefix hashing for DeepSeek cache | Session |
| 2 | ContextPartitioner | Immutable / append-only / volatile 3-zone | Session |
| 3 | EmbeddingIndex | Semantic retrieval + keyword fallback | Cross-session |
| 4 | LocalStore | SQLite (profiles / sessions / memory_log) | Persistent |

---

## 5. Building Agents with Jig

See the full guide: [Building Agents with Jig](guides/building-agents.md)

### Quick example

```python
from jig import Jig

# 3-line agent pipeline
app = Jig()
result = app.run("Review this PR for security issues")
print(result)
```

### Custom agent via SKILL.md

```yaml
---
name: security-reviewer
description: "Performs security code review"
model: pro
tools: [read]
---

## Role
Senior security engineer. Review code for OWASP Top 10 vulnerabilities.
```

```python
app = Jig(skills_dir="./skills")
agents = app.list_agents()
# → security-reviewer is loaded automatically
```

---

## 6. Roadmap

| Phase | Content | Status |
|-------|---------|:------:|
| Base | Skill→Agent mapping + DeepSeek dual-model | ✅ v0.1–0.4 |
| Memory | 4-layer memory + SQLite | ✅ vA.0.2 |
| Safety | CircuitBreaker + DriftDetector + RiskMode | ✅ vA.0.3 |
| Multi-model | DeepSeek + OpenAI + streaming | ✅ v0.5.0 |
| Graph | GraphOrchestrator + Durable | ✅ v0.6.0 |
| Docs | MkDocs + building-agents guide | ✅ Current |
| Package | PyPI release + CI | 🚧 |

---

*Jig is open source under MIT License. Copyright (c) 2026 Jig Contributors.*
