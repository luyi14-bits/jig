# DeepSeek Optimization Gap Analysis

> AgentHarness Alpha 0.2 vs awesome-deepseek-agent ecosystem
> Date: 2026-07-21 | Methodology: Luyi14-acceptance-testing + Luyi14-code-review

## Benchmark Projects

| Project | Stars | Type | DeepSeek Specific |
|---------|-------|------|:-----------------:|
| **Reasonix** | N/A | Terminal coding agent | ✅ Native (cache-first, flash-first) |
| **Deep Code** | N/A | Terminal AI assistant | ✅ Agent Skills + reasoning effort |
| **Pi** | N/A | Terminal coding harness | ✅ Tree-structured sessions |
| **AgentHarness** | ~0 | Multi-Agent framework | ✅ FR-2/3 (repair + effort) |

---

## Dimension-by-Dimension Comparison

### 1. Cache Optimization

| Aspect | Reasonix | Deep Code | Pi | AgentHarness |
|--------|----------|-----------|----|--------------|
| Strategy | Cache-first loop | — | — | SHA-256 prefix hashing |
| Prefix stabilization | ✅ | — | — | ✅ immutable_frozen |
| Per-session cache | ✅ | — | — | ✅ CacheEngine stats |
| Cost visualization | — | — | — | ✅ CacheStats (hit_rate, savings) |

**Verdict**: 🟢 **Leader** — AgentHarness has the most structured cache system with stats tracking.

### 2. Reasoning Effort Control

| Aspect | Reasonix | Deep Code | Pi | AgentHarness |
|--------|----------|-----------|----|--------------|
| Levels | flash/pro/preset max | deep thinking max | — | low/medium/high |
| Configurable | ✅ `/pro` TUI command | ✅ CLI flag | — | ✅ `reasoning_effort` setter |
| Per-request | ✅ | ✅ | — | ✅ In `prepare_request` |
| Max thinking | — | ✅ | — | ⚠️ Missing `max` level |

**Verdict**: 🟡 **On par** — Has configurable levels but missing `max` thinking mode.

### 3. Tool-Call Repair

| Aspect | Reasonix | Deep Code | Pi | AgentHarness |
|--------|----------|-----------|----|--------------|
| JSON repair | ✅ automatic | — | — | ✅ 4 strategies (code block, trailing comma, missing quotes) |
| FC fallback | ✅ | — | — | ✅ reasoner→chat auto-degrade |
| Repair stats | — | — | — | ✅ `repair_stats` property |

**Verdict**: 🟢 **Leader** — Most comprehensive repair system with fallback chain.

### 4. Cost Control

| Aspect | Reasonix | Deep Code | Pi | AgentHarness |
|--------|----------|-----------|----|--------------|
| Flash-first | ✅ default | — | — | ✅ CostAwareRouter |
| Token budget | — | — | — | ✅ session + monthly budget |
| Cost estimation | — | — | — | ✅ `estimate_cost` with cache discount |
| Circuit breaker | — | — | — | ✅ CircuitBreaker (drift + iteration limit) |

**Verdict**: 🟢 **Leader** — Only framework with multi-level cost governance.

### 5. MCP Integration

| Aspect | Reasonix | Deep Code | Pi | AgentHarness |
|--------|----------|-----------|----|--------------|
| MCP Client | ✅ native | — | ✅ | ✅ MCPClient |
| MCP Server | — | — | — | ✅ MCPServer |
| ToolGuard layer | — | — | — | ✅ whitelist/denylist/pre-tool-use |

**Verdict**: 🟢 **Leader** — Only framework with bidirectional MCP + security layer.

### 6. Model Naming Compliance

| Aspect | Required | Reasonix | Deep Code | Pi | AgentHarness |
|--------|:--------:|:---------:|:---------:|:--:|:------------:|
| Uses v4 names | ✅ Yes | ✅ | ✅ | ✅ | ❌ **Uses `deepseek-chat`** |

**Verdict**: 🔴 **Must fix** — `deepseek_adapter.py:49` uses `deepseek-chat` (V3 deprecated name). See CONTRIBUTING.md §1.

### 7. 1M Context Window

| Aspect | Required | Reasonix | Deep Code | Pi | AgentHarness |
|--------|:--------:|:---------:|:---------:|:--:|:------------:|
| 1M context configured | ✅ Yes | ✅ | ✅ | ✅ | ❌ **Not mentioned** |

**Verdict**: 🔴 **Must add** — No code or documentation mentions the 1M context window.

---

## Summary

| Dimension | Status | Action |
|-----------|:------:|--------|
| Cache optimization | 🟢 Leader | No fix needed |
| Reasoning effort | 🟡 On par | Add `max` level |
| Tool-Call Repair | 🟢 Leader | No fix needed |
| Cost control | 🟢 Leader | No fix needed |
| MCP integration | 🟢 Leader | No fix needed |
| Model naming | 🔴 **Fix required** | `deepseek-chat` → `deepseek-v4-flash` |
| 1M context window | 🔴 **Fix required** | Add to code + PR guide |
| Bilingual docs | ❌ Needs creation | Write en + zh-CN guide |
| README table entry | ❌ Needs creation | Add to awesome list |

---

## Priority Action Items

1. **P0** — Fix model naming: `deepseek_adapter.py:49` change `"deepseek-chat"` → `"deepseek-v4-flash"`
2. **P0** — Add 1M context window configuration to adapter
3. **P1** — Add `max` reasoning effort level
4. **P1** — Write bilingual PR guide for awesome-deepseek-agent
5. **P2** — Add cache cost visualization example to README
