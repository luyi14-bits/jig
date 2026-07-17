# Tree-SOP Agent — Technical Whitepaper v2

> **Version**: Alpha 0.2 | **Last Updated**: 2026-07-16
> **Status**: Production Design Reference

---

## 0. Executive Summary

Tree-SOP Agent is a **multi-agent orchestration framework** that predefines 13 Agent roles as pipeline nodes—Dispatcher, PM, Trinity, Spec, Coding, Code-Review, TDD, Acceptance, Security, DevOps, Secretary, LOOP SOP—and allows users to mount arbitrary SKILL.md files onto each Agent as knowledge augmentation. The system enforces behavior through a **hard-constraint Harness layer** (ToolGuard + LOOP SOP gating) and optimizes API costs through a **4-layer memory architecture** with DeepSeek Context Caching. Unlike prompt-only frameworks (CrewAI, MetaGPT, AutoGPT), Tree-SOP Agent implements PreToolUse interception, mandatory HandoverPackage schema, and 5-stage pipeline gating.

---

## 1. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Control Plane (Harness)                    │
│   LOOP SOP · ToolGuard · GlobalConstraints · MemoryRouter    │
├──────────────────────────────────────────────────────────────┤
│                    Agent Plane                                │
│   SkillParser → SkillRegistry → AgentFactory → Agent         │
│   HandoverPackage · Dispatcher · IntentRouter                │
├──────────────────────────────────────────────────────────────┤
│                    Orchestration Plane                        │
│   SequentialOrch · ParallelOrch · HierarchicalOrch           │
│   CheckpointManager · CircuitBreaker · DriftDetector         │
├──────────────────────────────────────────────────────────────┤
│                    Tool Plane                                 │
│   MCPClient · ToolGuard · RepoMap · EmbeddingIndex           │
│   DeepSeekAdapter · CacheEngine · ContextPartitioner         │
└──────────────────────────────────────────────────────────────┘
```

### SOP Pipeline

```
User → Dispatcher → PM → Trinity → Spec → Coding → Code-Review
     → TDD → Acceptance + Security → DevOps → Secretary
```

Each node produces a `HandoverPackage` → next node. LOOP SOP gates each transition.

---

## 2. Harness Engineering

### 2.1 LOOP SOP Gating

| Gate | Entry Condition | Violation |
|------|----------------|-----------|
| G0→G1 | PRD + priority + Out-of-Scope defined | Return Phase 0 |
| G1→G2 | Spec + Tasks + Checklist + BREAKING | Return Phase 1 |
| G2→G3 | exit(0) + all tests + 24-item checklist | Return Phase 2 (max 3×) |
| G3→G4 | Acceptance PASS + Security zero-red | Return Phase 2 |
| G4→end | Snapshot + kanban + audit trail | Return Phase 4 |

### 2.2 ToolGuard — Hard Constraints

Three-layer interception applied before every tool call:

| Layer | Mechanism |
|-------|-----------|
| Soft | Prompt behavior guidance |
| Hard 1 | Tools whitelist (Agent-permitted) |
| Hard 2 | Denylist (globally prohibited: rm -rf, drop table, etc.) |
| Hard 3 | PreToolUse hooks (runtime validation) |

### 2.3 GlobalConstraints

Immutable prefix placed in context zone for cache optimization:
1. Role boundary enforcement (PM does not code, Coding does not accept)
2. Handover protocol: confidence < 0.8 triggers degradation
3. Audit trail: every execution MUST log to LOG.md
4. Security redlines: no bare `except: pass`, no plaintext API key

### 2.4 Degradation Rules

| Condition | Action |
|-----------|--------|
| Phase 2 loop >3× | Freeze → Trinity review |
| Same bug regressed 2× | Root-cause escalation |
| Acceptance fail 2× | PM re-evaluates feasibility |
| New > fixed defects | Return to Phase 0 |
| Total iterations >10 | Abort → human escalation |

---

## 3. Memory Architecture

### Layer 1: CacheEngine (API Cache Optimization)

Fixed-order prefix assembly for DeepSeek Context Caching:

```
base_prompt → output_style → language → memory → skill_index
```

SHA-256 snapshot → change detection → per-segment diff.
Skill body excluded from prefix; only name + description in index.
`<memory-update>` XML blocks appended to user turns to avoid prefix invalidation.

### Layer 2: ContextPartitioner (Three-Zone)

| Zone | Content | Cache | Lifecycle |
|------|---------|-------|-----------|
| Immutable | System + tools + memory | Full session hit | Frozen after init |
| Append-only | Conversation history | Tail-only miss | Auto-compress at 8K+ |
| Volatile | Reasoning traces | Never sent to API | Per-turn ephemeral |

### Layer 3: EmbeddingIndex + ConversationCompressor

- Semantic skill body search (sentence-transformers / keyword fallback)
- Conversation history compression: truncate / summarize / hybrid modes
- Flash LLM summary (planned), offline keyword extraction (current)

### Layer 4: Persistence (CheckpointManager + write_log + SQLite)

- `CheckpointManager` — JSON checkpoint at `~/.tree-sop/checkpoints/`
- `Agent.write_log()` — structured audit to `skills/{name}/LOG.md`
- `LocalStore` — SQLite databases (profiles, sessions, memory_log)

### Agent-to-Agent: HandoverPackage

```python
HandoverPackage(
    source_agent, target_agent,
    summary, artifacts: Dict,
    decisions: List[str],
    open_issues: List[str],
    confidence: float       # < 0.8 → degradation
)
```

---

## 4. Configuration System

All user configuration centralized in `~/.tree-sop/`:

| File | Content |
|------|---------|
| `config.json` | API Key, MCP servers, agent overrides, risk mode |
| `memory.db` | SQLite: profiles, sessions, memory_log |
| `checkpoints/` | JSON execution state snapshots |

ConfigManager exposes property-based API:
- `api_key` getter/setter with automatic save()
- `add_mcp_server()` / `remove_mcp_server()`
- `set_agent_model()`, `set_agent_display_name()`
- `enable_risk_mode()` with timestamp acknowledgment

---

## 5. Safety Systems

### CircuitBreaker

Three-state: CLOSED (normal) → OPEN (fail threshold) → HALF_OPEN (probe).
Exponential backoff on repeated failures.

### DriftDetector

Validates HandoverPackage against schema:
- Field completeness (summary, confidence, source/target)
- Type matching
- Confidence threshold (< 0.8 triggers degradation)
- Artifact file existence check

### Risk Mode (God Mode)

Global switch bypassing all ToolGuard + PreToolUse.
Required: 3-second forced reading + explicit "I understand" acknowledgment.
Logged in LOG.md with timestamp.

---

## 6. Centralized Harness Analysis

### Current: Distributed Context

```
Agent A (own Ctx) → HandoverPackage → Agent B (own Ctx) → etc.
```
Each Agent maintains private context. Information passes through structured packages.

### Alternative: Centralized Harness

```
All Agents → Shared Message Bus (Harness)
             Per-Agent View (role-filtered subset)
```

**Trade-off analysis:**

| Metric | Distributed | Centralized | 
|--------|:-----------:|:-----------:|
| Info fidelity | Package loss | ✅ Full conversation |
| Context window pressure | N×M rounds | ⚠️ N×M in one window |
| Cache hit rate | Per-Agent prefix | ❌ Role-switching spikes |
| Scheduling | Chain only | ✅ Broadcast/subscribe |
| Structural enforcement | ✅ Mandatory schema | ⚠️ Schema optional |
| API cost | Lower | Higher |

**Recommended hybrid**: Central Harness + Per-Agent Views (shared immutable prefix, role-filtered append-only).

---

## 7. Comparative Analysis

| Dimension | CrewAI | MetaGPT | AutoGPT | OpenHands | **Tree-SOP Agent** |
|-----------|:------:|:-------:|:-------:|:---------:|:------------------:|
| Hard constraints | ❌ | ❌ | ❌ | ❌ | ✅ ToolGuard + Gates |
| Role system | Generic | Company sim | Single | Code agent | ✅ 13 roles + mounts |
| Memory | Short-term | Shared msg | Vector | Context | ✅ 4-layer |
| Cache optimization | — | — | — | — | ✅ Prefix hashing |
| Failure handling | Manual retry | Manual | Loop | None | ✅ Auto-degrade + CB |
| Desktop | ❌ | ❌ | ❌ | ❌ | ✅ Tauri v2 |
| License | MIT | MIT | Apache 2.0 | MIT | **AGPL v3** |

---

## 8. Security Audit Summary

| Phase | Rating | Key Issue |
|:-----:|:------:|-----------|
| 1 Infrastructure | ⚠️ Medium | API Key plaintext storage |
| 2 Defense-in-depth | ❌ High | No rate limiting, no encryption |
| 3 Generated code | ⚠️ Medium | Bare except in repo_map |
| 4 Observability | ✅ Low | Acceptable coverage |
| 5 Deanonymization | ✅ Low | Git config cleaned |

**Critical findings**: API Key stored as plaintext in `~/.tree-sop/config.json` (violates own `global_constraints.py`). Two bare `except: continue` in `repo_map.py`. SQL injection surface in `memory.py:238`.

---

*This document reflects the Alpha 0.2 codebase. Components marked as stub or simulated are planned for production readiness.*
