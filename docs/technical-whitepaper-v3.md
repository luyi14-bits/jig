# AgentHarness — Technical Whitepaper v3

> **Version**: Alpha 0.2 · Framework Architecture Edition
> **Date**: 2026-07-21 · **Type**: Framework Architecture Whitepaper
> **Author**: Project Secretary (Luyi14-project-secretary)

---

## 0. Executive Summary

AgentHarness is a **self-built multi-agent orchestration framework** — not a wrapper around existing agent libraries. Its core differentiator is a **hard-constraint Harness layer** (ToolGuard + LOOP SOP gating) that intercepts tool calls *before* execution, a capability absent in prompt-only orchestration frameworks (CrewAI, MetaGPT, AutoGPT).

**Key metrics**: 13 Agent roles · 4-tier memory architecture · 5-stage LOOP SOP gating · 3-layer ToolGuard · 62/62 tests passing · 28 delivered features

**Architecture lineage**: AgentHarness was designed from scratch as a framework, not evolved from an application. The public SDK API (`from forge import AgentHarness`), external Agent compatibility layer (Meta-Harness), and MCP protocol support enable third-party developers to build on top of it.

---

## 1. Framework Architecture

### 1.1 Four-Layer Design

```
┌──────────────────────────────────────────────────────────────┐
│                 Control Plane (Harness)                       │
│  LOOP SOP · ToolGuard · GlobalConstraints · MemoryRouter     │
│  CircuitBreaker · DriftDetector · RiskMode                   │
├──────────────────────────────────────────────────────────────┤
│                 Agent Plane                                   │
│  SkillParser → SkillRegistry → AgentFactory → 13 Agents      │
│  HandoverPackage · Dispatcher · IntentRouter (HyDE + Decomp) │
├──────────────────────────────────────────────────────────────┤
│                 Orchestration Plane                           │
│  SequentialOrch · ParallelOrch · HierarchicalOrch            │
│  CheckpointManager · CircuitBreaker · DriftDetector          │
├──────────────────────────────────────────────────────────────┤
│                 Tool Plane                                    │
│  MCPClient · MCPProtocol · RepoMap · EmbeddingIndex          │
│  DeepSeekAdapter · CacheEngine · ContextPartitioner          │
│  CostAwareRouter · TokenBudget                                │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 From Application to Framework

The architecture evolved through three phases:

| Phase | Focus | Key Decision |
|-------|-------|-------------|
| v0.1-v0.4 (Day 1-3) | Skill→Agent mapping engine | SKILL.md with YAML frontmatter → runnable Agent |
| vA.0.1-vA.0.3 (Day 4-7) | Pipeline orchestration + memory | Hard-constraint Harness over prompt-only gating |
| Alpha 0.2 (Day 8+) | **Framework SDK** | Public API + External Agent layer + MCP protocol |

The framework SDK boundary is defined in `src/jig/api.py`. External consumers interact through:

```python
from forge import AgentHarness

# 5-line pipeline
app = AgentHarness(skills_dir="./skills")
result = app.run("Build a login flow")
print(result)
```

### 1.3 Meta-Harness: External Agent Compatibility Layer

AgentHarness can govern external agents (Claude Code, Codex, Cursor, Pi) through the Meta-Harness layer:

```
External Agent ──→ MetaHarness ──→ ToolGuard ──→ Execution
                      │
                      ├── ClaudeCodeAdapter
                      ├── CodexAdapter
                      └── PiAdapter
```

Each adapter implements `start / send / stop / observe`. Tool calls from external agents pass through AgentHarness's ToolGuard interception, enabling hard-constraint governance over tools that lack their own.

---

## 2. Harness Engineering

### 2.1 LOOP SOP — 5-Stage Gating

Every pipeline stage gates against defined criteria. Failed gates trigger auto-degrade (circuit breaker, drift detection, max-iteration cap).

| Gate | Entry Check | Pass Criteria | Auto-Degrade |
|------|-------------|--------------|--------------|
| G0→1 | Raw idea | PRD complete + priority set + Out of Scope clear | Return to Stage 0 |
| G1→2 | PRD accepted | Spec + Tasks + Checklist ready + BREAKING marked | Return to Stage 1 |
| G2→3 | Spec accepted | Self-test exit(0) + tests green + 24 checks | Return to Stage 2 (max 3×) |
| G3→4 | Code submitted | Acceptance PASS + Security zero-red | Return to Stage 2 |
| G4→end | Release ready | Version snapshot + Kanban updated + trace logged | Return to Stage 4 |

### 2.2 ToolGuard — 3-Layer Hard Constraint

Unlike prompt-only guardrails (easily bypassed by the Agent), ToolGuard operates at the code level:

```
Agent Tool Call
      │
      ▼
 [Layer 1: Whitelist] ── Fail → Block + Log
      │ Pass
      ▼
 [Layer 2: Denylist]  ── Hit  → Block + Log
      │ Pass
      ▼
 [Layer 3: PreToolUse Hook] ── Fail → Block + Log
      │ Pass
      ▼
   Execute Tool
```

Whitelist and Denylist are user-configurable via `ConfigManager.agent_overrides.allow_tools` / `deny_tools`. PreToolUse hooks are developer-defined callbacks that inspect arguments before execution.

### 2.3 CircuitBreaker + DriftDetector **[NEW]**

The `CircuitBreaker` implements a three-state machine (CLOSED → OPEN → HALF_OPEN) that prevents cascading failures:

- **CLOSED**: Normal operation, call counter increments on each failure
- **OPEN**: Service degraded, all calls blocked for cooldown period
- **HALF_OPEN**: Probe mode, allows limited calls to test recovery

`DriftDetector` monitors model outputs for semantic drift — when an Agent begins producing outputs that deviate from expected patterns, it triggers a gate re-check.

### 2.4 Risk Mode

Risk Mode (`ConfigManager.enable_risk_mode`) bypasses all ToolGuard restrictions. It requires explicit acknowledgment (`risk_mode_acknowledged_at`) and is designed for controlled debugging sessions only.

---

## 3. Memory Architecture

### 3.1 Four-Layer Design

| Layer | Component | Mechanism | Persistence |
|:-----:|-----------|-----------|:-----------:|
| 1 | **CacheEngine** | SHA-256 prefix hashing for DeepSeek Cache Hit max | Session (volatile) |
| 2 | **ContextPartitioner** | immutable / append-only / volatile 3-zone context | Session (volatile) |
| 3 | **EmbeddingIndex** | Semantic retrieval + keyword fallback | In-memory |
| 4 | **LocalStore** | SQLite 3-table: profiles / sessions / memory_log | Disk (persistent) |

### 3.2 CacheEngine — DeepSeek Cost Optimization

The CacheEngine maintains prefix stability through:

```python
class CacheEngine:
    def assemble_prefix(self) -> str:
        # Order: base prompt → output style → language → memory → skill index
        prefix = f"<system>{self._system_prompt}</system>"
        prefix += f"<memory>{self._memory_context}</memory>"
        prefix += f"<skills>{self._skill_index}</skills>"
        return prefix
    
    def snapshot(self) -> str:
        return hashlib.sha256(self._prefix.encode()).hexdigest()
```

Once the prefix is frozen (`immutable_frozen = True`), it achieves near-100% cache hit rate across the session. Only the append-only zone (conversation history) grows per turn.

### 3.3 ContextPartitioner — 3-Zone Context

| Zone | Contents | Cached? | API Cost |
|------|----------|:-------:|:--------:|
| Immutable | system prompt + tools + memory | ✅ Near-100% | One-time |
| Append-only | conversation history (append only) | ✅ Tail-miss only | Per-turn growth |
| Volatile | reasoning traces, scratchpad | ❌ Never sent | Zero |

### 3.4 MemoryRouter + Consolidator **[NEW]**

The `MemoryRouter` classifies new information into four types and routes accordingly:

- **Working**: Volatile, used for current task context
- **Episodic**: Session-bound, SQLite for persistence
- **Semantic**: Indexed in EmbeddingIndex for cross-session retrieval
- **Summary**: Flash-compressed version of long conversations

`Consolidator` runs periodically to merge similar memories and decay low-value ones.

---

## 4. Agent System

### 4.1 13 Preset Roles

| # | Role | Skill | Model |
|---|------|-------|:-----:|
| 0 | **Dispatcher** | Built-in | — |
| 1 | **PM** | `Luyi14-pm-mentor` | Pro |
| 2 | **Trinity** | `Luyi14-trinity-mentors` (3 AI/ML experts) | Pro |
| 3 | **Spec-Pipeline** | `Luyi14-spec-pipeline` | Pro |
| 4 | **Coding** | Built-in (Coding Ethics) | Flash |
| 5 | **Code-Review** | `Luyi14-code-review` | Pro |
| 6 | **TDD** | `Luyi14-test-driven-development` | Flash |
| 7 | **Acceptance** | `Luyi14-acceptance-testing` | Flash |
| 8 | **Security** | `Luyi14-security-academy` | Pro |
| 9 | **DevOps** | `Luyi14-devops` | Flash |
| 10 | **Secretary** | `Luyi14-project-secretary` | Flash |
| 11 | **LOOP SOP** | `Luyi14-loop-sop` | Pro |
| 12 | **Story Writer** | `luyi14-horror-story-writer` | Flash |

### 4.2 Skill → Agent Mapping Engine

```
SKILL.md (YAML frontmatter + markdown body)
    │
    ▼
SkillParser → validates frontmatter, extracts body
    │
    ▼
SkillRegistry → indexes by name, tags, tools
    │
    ▼
AgentFactory → assembles AgentConfig (role_preset from body)
    │
    ▼
Agent.write_log(task, output, agent_name) → skills/<name>/LOG.md
```

Each Agent's prompt is assembled in two layers:
1. **Global constraints** (immutable, shared across all Agents): Coding Ethics (八荣八耻), acceptance criteria, security rules
2. **Role body** (from SKILL.md): the full markdown body, reserved without summarization

### 4.3 IntentRouter: HyDE + Decomp **[NEW]**

`IntentRouter.classify_query()` routes user input to the appropriate Agent using three strategies:

- **Simple instruction** (< 10 tokens, one intent): Direct routing
- **HyDE rewrite**: Hypothetical Document Embeddings to expand short queries
- **Decomp**: Multi-intent decomposition for complex requests

```python
class IntentRouter:
    def route(self, query: str) -> List[str]:
        if len(query.split()) < 10:
            return self._direct_route(query)
        return self._decomp_intent(query)
```

### 4.4 Cost-Aware Routing **[NEW]**

`CostAwareRouter` implements a Flash-first strategy:

- Default: Flash model for all Agents
- Upgrade: Long/complex queries (>100 tokens) → Pro model
- Budget: Session + Monthly token caps, auto-circuit-break on exceed

---

## 5. Safety & Observability

### 5.1 CircuitBreaker 3-State Machine **[NEW]**

| State | Behavior | Recovery |
|-------|----------|----------|
| CLOSED | Normal operation, failure counter increments | — |
| OPEN | All calls blocked for cooldown | Timer-based HALF_OPEN |
| HALF_OPEN | Probe: allows limited test calls | Success → CLOSED; Failure → OPEN |

### 5.2 DriftDetector **[NEW]**

Monitors Agent outputs for semantic drift using embedding similarity. When an Agent's outputs deviate significantly from historical patterns, DriftDetector flags the session for human review.

### 5.3 Security Audit Results (Alpha 0.2)

| Audit | Result |
|-------|:------:|
| Code review (4 dimensions) | ✅ PASS (style, bugs, security, performance) |
| Security audit (3 experts) | ✅ PASS (Miessler, Kettle, Ormandy) |
| Model naming compliance | ✅ v4 naming (`deepseek-v4-flash`/`deepseek-v4-pro`) |
| Known vulnerabilities | 2 CRITICAL in archived desktop code (not active) |

### 5.4 Audit Trail

Every Agent action is logged to `skills/<name>/LOG.md` with:
- `write_log(task, output, agent_name)` — structured task completion
- HandoverPackage transmission record
- Gate pass/fail history

---

## 6. Comparative Analysis

| Dimension | LangGraph | CrewAI | MS Agent FW | PydanticAI | **AgentHarness** |
|-----------|:---------:|:------:|:-----------:|:----------:|:----------------:|
| **Hard Constraint** | ❌ Prompt-only | ❌ Prompt-only | ❌ Prompt-only | ❌ Prompt-only | ✅ **ToolGuard + Gating** |
| **Harness Level** | ❌ | ❌ | ❌ | ❌ | ✅ **Built-in framework harness** |
| **Role System** | Generic graph | Generic | Plugin-based | Single Agent | ✅ **13 preset + custom** |
| **Memory** | Checkpoint | Short-term | State | — | ✅ **4-tier + 5-level compression** |
| **Cache Optimization** | — | — | — | — | ✅ **SHA-256 prefix hashing** |
| **Failure Handling** | Retry | Manual retry | Retry | — | ✅ **Auto-degrade + CircuitBreaker** |
| **License** | MIT | MIT | MIT | MIT | **MIT** |

**Unique differentiators**:
- AgentHarness is the **only framework with a hard-constraint Harness layer** operating at the code level
- **Only framework with DeepSeek-specific cache optimization** (prefix hashing, cost-aware routing, Tool-Call Repair)
- **Only framework with a gated SOP pipeline** that applies across all Agents uniformly

---

## 7. Centralized Harness Analysis

### 7.1 Distributed vs Centralized Architecture

| Aspect | Current (Distributed) | Centralized Alternative |
|--------|----------------------|------------------------|
| Context | Per-Agent partitioned | Shared message bus |
| Cache | Per-Agent prefix hits | Single prefix, role-switching cost |
| Handover | HandoverPackage schema | Free-form bus messages |
| Orchestration | External driver | Native to bus |
| Checkpoint | Per-session | Full bus state snapshot |

### 7.2 Recommended Hybrid: Central Harness + Per-Agent Views

The optimal compromise:
- **Shared bus** for physical message storage (append-only)
- **Per-Agent views** that filter the bus to role-relevant messages
- **Structured handover** preserved (XML blocks on bus)
- **Cache-friendly** immutable prefix maintained per session

---

## 8. Roadmap & Ecosystem

### 8.1 Three-Phase Strategy

| Phase | Period | Goal | Target |
|-------|--------|------|--------|
| 1: Verification | 2026 Q3 | Real project validation + DS ecosystem capture | 100+ stars, 1 DS mention |
| 2: Release | 2026 Q4 | Beta→RC→v1.0 | 500+ downloaders/month |
| 3: Deepening | 2027 H1 | 12-Factor compliance + Harness-as-a-Service | 2k+ stars |

### 8.2 Ecosystem Position

AgentHarness targets the **Harness layer** — not agent framework compatibility (LangGraph), not community size (CrewAI), not general LLM platform (LangChain). The only framework with a code-level hard constraint layer that governs ALL Agents uniformly, regardless of whether they are built-in or external.

### 8.3 Key Upcoming Milestones

| Item | Status | Target |
|------|--------|--------|
| awesome-deepseek-agent PR | 🚧 Docs prepared | 2026-08 |
| Real project validation | 🚧 Spec drafted | 2026-08 |
| Documentation site | 📝 Planned | 2026-09 |
| v1.0 Release | 📝 Planned | 2026-12 |

---

*This document describes the AgentHarness architecture as of Alpha 0.2 (2026-07-21). Components in 🚧 are in progress; 📝 are planned.*
