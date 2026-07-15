# Tree-SOP Agent — Technical Whitepaper

> **Version**: Alpha 0.2 | **Last Updated**: 2026-07-15
> **Status**: Architecture Design Document

---

## 1. System Architecture Overview

Tree-SOP Agent is a **multi-agent orchestration framework** for vibe-coding workflows. It implements a **role-preset + skill-mounting** architecture: 11 pre-defined Agent roles (PM, Spec, Coding, Code-Review, TDD, Acceptance, Security, DevOps, Secretary, Trinity, LOOP SOP) form a complete software development pipeline. Users mount arbitrary SKILL.md files onto these Agents as knowledge augmentation.

### 1.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Control Plane (Harness)                    │
│  LOOP SOP · ToolGuard · GlobalConstraints · MemoryRouter    │
├─────────────────────────────────────────────────────────────┤
│                   Agent Plane                                │
│  SkillParser → SkillRegistry → AgentFactory → Agent         │
│  HandoverPackage · Dispatcher · IntentRouter                 │
├─────────────────────────────────────────────────────────────┤
│                   Orchestration Plane                        │
│  SequentialOrch · ParallelOrch · HierarchicalOrch           │
│  CheckpointManager · ConversationCompressor                │
├─────────────────────────────────────────────────────────────┤
│                   Tool Plane                                 │
│  MCPClient · ToolGuard · RepoMap · EmbeddingIndex           │
│  DeepSeekAdapter · CacheEngine · ContextPartitioner         │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 SOP Pipeline

```
User Input → Dispatcher → PM → Trinity → Spec-Pipeline → Coding
    → Code-Review → TDD → Acceptance + Security → DevOps → Secretary
```

Each node produces a `HandoverPackage` consumed by the next node. LOOP SOP monitors gate conditions across all transitions.

---

## 2. Harness Engineering System

The Harness is the **meta-control layer** that governs Agent behavior through three sub-systems: orchestration gating, constraint enforcement, and execution assurance. Unlike typical Agent frameworks that rely solely on prompt engineering, Tree-SOP Agent implements **hard constraints** at the harness level.

### 2.1 Orchestration Gating — LOOP SOP

The LOOP Standard Operating Procedure defines a **5-stage gating matrix**:

| Gate | Condition | Violation Handling |
|------|-----------|-------------------|
| G0→G1 | PRD complete + priority confirmed + Out-of-Scope defined | Return to Phase 0 |
| G1→G2 | Spec + Tasks + Checklist ready + BREAKING annotated | Return to Phase 1 |
| G2→G3 | Self-test exit(0) + all tests green + 24-item checklist passed | Return to Phase 2 (max 3 retries) |
| G3→G4 | Acceptance PASS + Security zero-red | Return to Phase 2 |
| G4→end | Version snapshot + kanban updated + audit trail complete | Return to Phase 4 |

**Convergence invariant**: The defect count MUST decrease every iteration. If an iteration shows no defect reduction, the loop is considered broken and escalates to human decision.

**Degradation triggers**:
- Phase 2 internal loop > 3 iterations → freeze coding → Trinity architecture review
- Same bug regressed twice → mark as "root cause unidentified" → escalate
- Acceptance failed 2 consecutive rounds → pause → PM re-evaluates feasibility
- New defects > fixed defects → direction error → return to Phase 0
- Total iterations > 10 → abort → escalate to human

### 2.2 Constraint Enforcement — ToolGuard + GlobalConstraints

#### 2.2.1 ToolGuard — PreToolUse Hard Constraints

A three-layer interception mechanism applied before every tool invocation:

| Layer | Mechanism | Function |
|-------|-----------|----------|
| **Soft** | Prompt behavior guidance | Methodology / conventions |
| **Hard 1** | Tools whitelist | Agent-permitted tool set |
| **Hard 2** | Denylist | Globally prohibited operations (rm -rf, drop table, etc.) |
| **Hard 3** | PreToolUse hooks | Runtime interception & validation |

Example whitelist configurations:

| Agent Role | Permitted Tools |
|------------|----------------|
| PM | web_search, fetch_page, Read, Grep |
| Coding | Read, Write, Edit, Bash, Glob, Git |
| Acceptance | Read, Grep, Glob, Bash(pytest), Bash(build) |
| Security | Read, Grep, Glob, web_search, fetch_page |

#### 2.2.2 GlobalConstraints — Immutable Shared Prompt Prefix

A fixed prefix prepended to every Agent's system prompt, placed in the immutable context zone for DeepSeek cache hit optimization:

1. **Role boundary enforcement**: PM shall not write code. Coding shall not perform acceptance. Acceptance shall not modify code.
2. **Handover protocol**: Every Agent MUST produce a `HandoverPackage` upon completion. `confidence < 0.8` triggers automatic degradation.
3. **Audit trail**: Every execution MUST be logged to `skills/{name}/LOG.md`. No log = no trace = rejected.
4. **Security redlines**: No bare `except: pass`. No plaintext API key storage. Sensitive data MUST be encrypted before persistence.

### 2.3 Execution Assurance (Design)

The following components are in the specification phase:

#### 2.3.1 CircuitBreaker

A three-state circuit breaker pattern:

| State | Behavior |
|-------|----------|
| **CLOSED** | Normal operation. Failures increment a counter. |
| **OPEN** | Failure threshold exceeded. Requests are rejected without execution. Exponential backoff timer starts. |
| **HALF_OPEN** | Timer expires. Probe request allowed. Success → CLOSED. Failure → OPEN with increased backoff. |

#### 2.3.2 DriftDetector

Validates Agent output against expected schema after every `HandoverPackage` emission:

- Field completeness (all required HandoverPackage fields present)
- Type matching (summary is str, confidence is float 0.0–1.0, etc.)
- Confidence threshold (confidence < 0.8 triggers degradation)
- Artifact file existence check (if artifacts reference file paths)

#### 2.3.3 IntentRouter — HyDE + Decomposition

Routes user queries based on complexity classification:

| Query Type | Strategy |
|------------|----------|
| **Simple command** (≤15 chars, unambiguous) | Direct route to PM Agent. No rewriting. |
| **Long/complex sentence** (>30 chars, multi-condition) | HyDE: generate hypothetical PRD summary → route based on summary content |
| **Multi-turn complex intent** (crosses 3+ turns of context) | Decomp: decompose into N sub-intents → parallel route to multiple Agents |

---

## 3. Memory Architecture

The memory system follows a **four-layer design**, from static cache optimization to persistent long-term storage.

```
Layer 1: CacheEngine (Prompt Prefix Caching)
Layer 2: ContextPartitioner (Three-Zone Context)
Layer 3: EmbeddingIndex + ConversationCompressor (Retrieval + Compression)
Layer 4: CheckpointManager + write_log (Persistence)
```

### 3.0 Memory Architecture Topology

The four layers interact as a pipeline: static cache → partitioned context → retrieval/compression → persistence.

```
┌──────────────────────────────────────────────────────────────────┐
│                       MEMORY DATA FLOW                           │
│                                                                  │
│  User Request                                                    │
│      │                                                           │
│      ▼                                                           │
│  ┌─────────────────────┐                                         │
│  │ Layer 1: CacheEngine │  Prefix assembly + hash snapshot        │
│  │ base_prompt → style  │  Detects changes → cache miss warning   │
│  │ → lang → mem → idx   │  <memory-update> XML blocks            │
│  └─────────┬───────────┘                                         │
│            │ immutable prefix                                    │
│            ▼                                                     │
│  ┌─────────────────────┐                                         │
│  │ Layer 2: ContextPar- │  Three-zone partitioning                │
│  │ titioner             │  immutable / append-only / volatile     │
│  │                      │  auto_compress_threshold = 8000 tok    │
│  └─────────┬───────────┘                                         │
│            │ append-only overflow                                │
│            ▼                                                     │
│  ┌─────────────────────┐     ┌──────────────────────┐            │
│  │ Layer 3a: Conver-   │     │ Layer 3b: Embedding-  │            │
│  │ sationCompressor    │     │ Index                 │            │
│  │ hybrid/trunc/summar │     │ semantic skill search │            │
│  └─────────┬───────────┘     └──────────┬───────────┘            │
│            │ compressed history         │ top-K skills            │
│            └──────────┬─────────────────┘                        │
│                       ▼                                          │
│  ┌─────────────────────┐                                         │
│  │ Layer 4: Persistence │                                        │
│  │ CheckpointManager    │  ~/.tree-sop/checkpoints/{id}.json     │
│  │ write_log()          │  skills/{name}/LOG.md                  │
│  └─────────────────────┘                                         │
│                                                                  │
│  Cross-cutting: HandoverPackage flows Agent A → Agent B          │
│  with structured summary + artifacts + decisions + confidence    │
└──────────────────────────────────────────────────────────────────┘
```

**Layer responsibilities at a glance:**

| Layer | Component | Trigger | Output |
|-------|-----------|---------|--------|
| 1 | CacheEngine | Session start / memory change | SHA-256 prefix snapshot, cache hit/miss diagnostic |
| 2 | ContextPartitioner | Every API call | Partitioned messages (immutable + append-only) |
| 3a | ConversationCompressor | `estimated_tokens > threshold` | Compressed message list |
| 3b | EmbeddingIndex | Agent skill lookup | Top-K relevant skills by semantic similarity |
| 4 | CheckpointManager + write_log | Step completion / session end | JSON checkpoint + LOG.md entry |

### 3.1 Layer 1 — CacheEngine (Prompt Prefix Caching)

**Responsibility**: Maximize DeepSeek API cache hit rate to reduce latency and cost.

**Fixed-order prefix assembly**:
```
base_prompt → output_style → language → memory → skill_index
```

Each segment is wrapped in `<!-- {key} -->` markers. The assembled prefix is hashed (SHA-256) and compared against the previous snapshot for change detection.

**Key design decisions**:
- Skill body content is EXCLUDED from the cache prefix. Only `name + description` indices are included.
- Memory updates use `<memory-update>` XML blocks appended to user turns, avoiding prefix invalidation.
- `CacheDiagnostic` tracks `prefix_changed`, `change_reasons` (per-segment diff), and `session_hit_rate`.

**Cost model**: DeepSeek Context Caching prices cached reads at ~1/50th of uncached reads. Target: >99% session-level hit rate.

### 3.2 Layer 2 — ContextPartitioner (Three-Zone Context)

**Responsibility**: Partition API context into three zones with distinct caching and lifecycle behaviors.

| Zone | Content | Lifecycle | Cache Behavior |
|------|---------|-----------|----------------|
| **Immutable** | System prompt + tools + memory | Frozen after first set | Full session cache hit |
| **Append-only** | Conversation history (user/assistant turns) | Grows monotonically | Stable growth, tail-only misses |
| **Volatile** | Reasoning traces, temp plans | Per-turn ephemeral | NEVER sent to API |

**Auto-compression**: When `estimated_tokens()` exceeds `auto_compress_threshold` (default 8,000), `compress_if_needed()` delegates to `ConversationCompressor` and repartitions the result.

### 3.3 Layer 3 — Retrieval & Compression

#### 3.3.1 ConversationCompressor

Three compression strategies:

| Mode | Strategy | Use Case |
|------|----------|----------|
| **Truncate** | Keep last `keep_last_n` rounds, discard rest | Memory-constrained environments |
| **Summarize** | Replace all history with one LLM-generated summary | Long-running sessions |
| **Hybrid** (default) | Summarize middle history + keep last N rounds verbatim | Balance between context preservation and token budget |

**Summary generation**: Currently offline keyword extraction (decision/action keywords). Production design calls for DeepSeek Flash (cheap model) LLM summarization, with offline fallback as safety net.

#### 3.3.2 EmbeddingIndex — Semantic Skill Retrieval

Indexes SKILL.md body content for semantic search:

- **Online mode**: `sentence-transformers` (all-MiniLM-L6-v2) → cosine similarity
- **Offline fallback**: Keyword intersection + name-match bonus (5x weight)
- **Search scope**: Currently skill definitions only. Enhanced design adds conversation memory indexing.

### 3.4 Layer 4 — Persistence

#### 3.4.1 CheckpointManager

JSON-based session state serialization:

```python
save(session_id, state)    →  ~/.tree-sop/checkpoints/{session_id}.json
load(session_id)           →  Dict or None
resume(session_id)         →  load() + log
list_checkpoints()         →  [session_id, ...]
```

Restores execution state (current step, results, context) for interrupted SOP pipelines.

#### 3.4.2 Agent Audit Trail (write_log)

Every Agent automatically appends to `skills/{agent_name}/LOG.md` after task completion:

```markdown
## 2026-07-14

### Execution: {task_summary}
- **Artifact**: {output description}
- **Handover target**: {target_agent}
- **Agent**: {agent_name}
```

### 3.5 Agent-to-Agent Memory Transfer — HandoverPackage

Agents do NOT share memory. Context passes through a structured **HandoverPackage**:

```
HandoverPackage {
    source_agent: str,          # Origin Agent
    target_agent: str,          # Destination Agent
    summary: str,               # Execution synopsis
    artifacts: Dict[str, Any],  # Produced files / data
    decisions: List[str],       # Key decision log
    open_issues: List[str],     # Outstanding items
    confidence: float           # 0.0–1.0; < 0.8 triggers degradation
}
```

The orchestrator (`SequentialOrchestrator` / `ParallelOrchestrator` / `HierarchicalOrchestrator`) serializes HandoverPackage chains across the SOP pipeline.

### 3.6 Memory Architecture Enhancement (Design)

The following extensions are in the specification phase (`IDEA-022`):

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LocalStore** | SQLite (3 tables: profiles, sessions, memory_log) | Zero-dependency persistent memory |
| **MemoryRouter** | Routing layer | Working→immutable / Summary→Flash / Episodic→SQLite / Semantic→EmbeddingIndex |
| **Consolidator** | Scheduled tasks | Low-value memory decay + Similar memory merging |
| **Cross-session RAG** | EmbeddingIndex on conversation history | Retrieve relevant past decisions across sessions |

---

## 4. Comparative Analysis

| Dimension | GPT (OpenAI) | Gemini (Google) | Claude (Anthropic) | **Tree-SOP Agent** |
|-----------|:------------:|:---------------:|:------------------:|:------------------:|
| **Metadata store** | Built-in session state | Structured KV | Project knowledge | Design phase (SQLite) |
| **User profile** | Persistent, learnable | System instruction | CLAUDE.md | Design phase |
| **Summary engine** | LLM-generated | RAG-retrieved | LLM auto-summary | Offline keywords → Flash LLM |
| **Cross-session memory** | Vector DB (assistants API) | Vector DB + RAG | Project knowledge files | Design phase (SQLite + EmbeddingIndex) |
| **Hard constraints** | None (prompt-only) | None (prompt-only) | Hooks + denylist | **✅ ToolGuard + GlobalConstraints** |
| **Orchestration gating** | Function calling only | Tool use only | Hooks + pre/post | **✅ LOOP SOP 5-stage gate matrix** |
| **Cost optimization** | Prompt caching | Context caching (>32K) | Prompt caching | **✅ 4-layer memory + Flash/Pro routing** |
| **Per-call cost** | Medium | Low (cached) | High (uncached) | **Very low (local SQLite + Flash)** |

**Key differentiator**: Tree-SOP Agent is the only framework with a **hard-constraint Harness layer** (ToolGuard + LOOP SOP gates). All others rely on prompt-only soft constraints.

---

## 5. Extensibility Design

| IDEA | Component | Priority | Status |
|:----:|-----------|:--------:|:------:|
| 018 | Tauri desktop shell | P0 | Spec phase |
| 020 | HyDE rewriting + Intent decomposition | P1 | Spec phase |
| 021 | Circuit breaker + Drift detection | P1 | Spec phase |
| 022 | SQLite memory + Flash summary + RAG | P0 | Spec phase |

---

## 6. Centralized Harness Architecture Analysis

### 6.1 Motivation

The current architecture is **distributed-context**: each Agent maintains its own `ContextPartitioner` (three-zone context), its own `Agent` instance with private `_context`, `_handover_in/out`, and `_execution_log`. Agents communicate exclusively through structured `HandoverPackage` objects. The Orchestrator (Sequential / Hierarchical / Parallel) sits outside the Agents, driving execution order.

An alternative approach — **Centralized Harness** — consolidates all message routing, context management, and memory into a single message bus that all Agents share. This section analyzes what happens to the multi-Agent conversation model under a centralized design.

### 6.2 Architecture Comparison

```
Current: Distributed Context                      Alternative: Centralized Harness

  Agent A ──┐                                      Agent A ──┐
  (own Ctx)  │                                                 │
             ├── HandoverPackage ──►                          ├──►  Central Harness
  Agent B ──┘                                      Agent B ──┤   ┌──────────────────┐
  (own Ctx)                                                   │   │ Shared Message Bus│
             │                                                ├──►│ Unified Context   │
  Agent C ──┘                                      Agent C ──┘   │ Central Memory    │
  (own Ctx)                                                    │   │ Central Router    │
                                                                   └──────────────────┘
```

### 6.3 Impact Analysis: Multi-Agent Conversation Under Centralized Harness

#### 6.3.1 Context Partitioning Model (Highest Impact)

| Aspect | Current (Distributed) | Centralized Harness |
|--------|----------------------|---------------------|
| Immutable zone | Per-Agent: each has own system prompt + role preset | Single shared immutable prefix for all Agents |
| Append-only zone | Isolated per Agent; Agent B cannot see Agent A's history | Globally shared; all Agents see full conversation history |
| Volatile zone | Per-Agent reasoning traces | May degrade to single global scratch area |
| Token pressure | N Agents × M rounds = N independent windows of M | 1 window of N×M rounds |

**Benefit**: Agent B directly "sees" what Agent A said and did — no information loss through HandoverPackage indirection.

**Risk**: Context window explodes. 5 Agents × 3 rounds each = 15 rounds in one window. `ConversationCompressor` triggers frequently, and summary quality degrades because it compresses mixed-role conversations.

#### 6.3.2 Cache Prefix Hit Rate

The current `CacheEngine` relies on a fixed prefix per session (`_immutable_frozen = True`), achieving near-100% cache hit.

Under centralized Harness:
- If all Agents share one system prompt → prefix stays stable → **cache unaffected**
- If Harness switches system prompts per Agent role (PM vs Coding role presets differ) → prefix changes on every Agent switch → **cache miss rate spikes**, API cost increases

**Mitigation**: Harness maintains multiple prefix snapshots, dispatching by Agent role. But this converges back toward the distributed model.

#### 6.3.3 Agent Handover Protocol

Current `HandoverPackage` is a structured schema enforcing:
- `summary`, `artifacts`, `decisions`, `open_issues`, `confidence`
- `confidence < 0.8` → automatic degradation trigger

Under centralized Harness:
- Agents no longer "package and hand over"; they post messages to the shared bus
- `artifacts` → shared filesystem references on the bus
- `decisions` / `open_issues` → pinned or tagged messages
- Degradation logic migrates into Harness internals

**Benefit**: More flexible interaction patterns — broadcast, subscribe, query — not limited to chain-based handover.

**Risk**: Loss of structural enforcement. Agents may omit critical information without the mandatory HandoverPackage schema.

#### 6.3.4 Orchestrator Absorption

| Current | Centralized |
|---------|-------------|
| `SequentialOrchestrator` — external driver, serial Agent execution | Becomes Harness serial conversation mode |
| `ParallelOrchestrator` — `ThreadPoolExecutor`, concurrent Agents | Becomes Harness multi-Agent concurrent posting |
| `HierarchicalOrchestrator` — recursive sub-SOP with layer isolation | Becomes Harness sub-conversation / nested session |
| `Dispatcher` — single entry point, intent routing | Becomes Harness native routing |

The entire `orchestrator/` module could be refactored into Harness sub-modules or absorbed entirely.

#### 6.3.5 Skill Retrieval Pattern

| Current | Centralized |
|---------|-------------|
| Each Agent calls `EmbeddingIndex.search()` when activated | Harness performs search once upon receiving user input |
| Agent knows its own domain → higher precision | Harness must understand all skill semantics → potential precision loss |
| N Agents = N searches | 1 search, routed to target Agent with relevant skills injected |

Trade-off: efficiency vs retrieval precision.

#### 6.3.6 Checkpoint Granularity

| Current | Centralized |
|---------|-------------|
| Per-session checkpoint (one SOP workflow) | Entire group-chat snapshot |
| Fine-grained: can restore a single Agent state | Coarse-grained: must restore full bus state |
| Must rebuild Agent relationship graph on resume | Simpler: restore bus state directly |

### 6.4 Summary: Four Gains, Four Losses

| Dimension | Verdict | Detail |
|-----------|:-------:|--------|
| Information fidelity | 🟢 Gain | No HandoverPackage information loss; Agents see full conversation |
| Context window pressure | 🔴 Loss | N Agents' dialogue in one window; compression triggers more often |
| Cache hit rate | 🔴 Loss | Multi-role prefix switching → cache invalidation → higher API cost |
| Scheduling flexibility | 🟢 Gain | Beyond chain-based handover: broadcast, subscribe, query patterns |
| Structural enforcement | 🔴 Loss | No mandatory HandoverPackage schema; critical info may be missed |
| Implementation complexity | 🟢 Gain | Eliminates `orchestrator/` module overhead; single entry point |
| Recoverability | 🟢 Gain | Single snapshot for entire session; simpler restore |
| API cost | 🔴 Loss | Larger context windows + lower cache hit rate → higher token consumption |

### 6.5 Recommended Hybrid: Central Harness + Per-Agent Views

The optimal architecture is neither purely distributed nor purely centralized, but a **Central Harness with Per-Agent Views**:

```
Central Harness
├── Shared Message Bus (physical append-only storage)
├── Shared Memory + Skill Index (immutable prefix)
└── Per-Agent View (each Agent filters its own perspective from the bus)
    ├── Agent A sees only its role-relevant messages
    ├── Agent B receives explicit upstream via HandoverPackage
    └── Harness handles routing + filtering + compression
```

**Properties preserved from current architecture**:
- Cache-friendly immutable prefix (one per session, not per Agent)
- Structured HandoverPackage enforcement (still required, just posted to bus instead of passed directly)
- Per-Agent volatile zone (reasoning traces remain private)

**Properties gained from centralization**:
- Unified routing and scheduling
- Single checkpoint snapshot
- Cross-Agent visibility when needed (explicit opt-in via bus subscription)

**Design decisions to resolve**:
1. **Shared context vs filtered views**: Pure shared context causes window explosion. Harness should maintain logical partitions — each Agent sees shared prefix + role-filtered view — effectively promoting `ContextPartitioner` from Agent-level to Harness-level.
2. **Free-form messages vs structured handover**: Abandoning `HandoverPackage` schema risks information loss. Compromise: Harness still requires structured blocks (e.g., `<handover>` XML) from each Agent, just posted to the shared bus rather than passed as Python objects.

---

*This document describes the architecture as designed and implemented in Alpha 0.1.*
