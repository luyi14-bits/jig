# Real Project Validation — Pain Points Record

> Loop #3 Task 3 | Date: 2026-07-24
> Audited by: Luyi14-code-review (automated)

## Summary

Code audit of `src/jig/` core modules. Identified **12 pain points** across 6 categories.

---

## 🐛 Pain Points

### 1. CRITICAL: Hardcoded `"skills"` path in `dispatcher.py` and `sop_runner.py`
- **File**: `src/jig/orchestrator/sop_runner.py:135`, `dispatcher.py:75`
- **Issue**: `Path("skills")` hardcoded instead of using `settings.skills_dir`
- **Impact**: Cannot deploy to custom paths without modifying source

### 2. CRITICAL: `sop_runner.py` has duplicate `SkillRegistry` initialization
- **File**: `src/jig/orchestrator/sop_runner.py:134-140`
- **Issue**: Each `_execute_with_retry()` call reinitializes a `SkillRegistry` and re-registers all skills
- **Impact**: ~500ms overhead per node; memory leak potential

### 3. HIGH: `dispatcher.py` `_get_provider()` creates new provider per request
- **File**: `src/jig/orchestrator/dispatcher.py:90-98`
- **Issue**: `DeepSeekProvider` instantiated fresh each call. Should be singleton.
- **Impact**: Unnecessary API key parsing overhead

### 4. HIGH: `CostAwareRouter.route()` catches all exceptions
- **File**: `src/jig/adapters/cost_aware_router.py:75`
- **Issue**: Blanket `except Exception` swallows errors silently
- **Impact**: Debugging difficulty when routing fails silently

### 5. HIGH: No input validation on `user_message` parameter
- **File**: `src/jig/orchestrator/dispatcher.py:37`
- **Issue**: No length check, no encoding validation on user input
- **Impact**: Potential for very long inputs to cause OOM

### 6. MEDIUM: `MemoryRouter` uses `._store` (private attribute) in `sop_runner.py`
- **File**: `src/jig/orchestrator/sop_runner.py:133`
- **Issue**: `self._memory._store.save_session()` accesses private `_store`
- **Impact**: Breaks if `MemoryRouter` internal structure changes

### 7. MEDIUM: `ConfigManager` singleton race condition
- **File**: `src/jig/core/config_manager.py:49-52`
- **Issue**: Lazy init `_config_manager` in `settings.py` has no thread lock
- **Impact**: Thread-safe concern under concurrent requests

### 8. MEDIUM: `CircuitBreaker` recovery timeout is hardcoded in `sop_runner.py`
- **File**: `src/jig/orchestrator/sop_runner.py:57`
- **Issue**: `CircuitBreaker(failure_threshold=10, recovery_timeout=5)` hardcoded
- **Impact**: Not configurable per environment

### 9. MEDIUM: `StreamManager` subscriber queues grow unbounded
- **File**: `src/jig/adapters/streaming.py:26-31`
- **Issue**: `_subscribers` list grows without limit, no cleanup mechanism
- **Impact**: Memory leak under sustained streaming

### 10. LOW: `IntentRouter.classify_query()` uses simple heuristics
- **File**: `src/jig/orchestrator/intent_router.py:15-29`
- **Issue**: Word-count and comma-count based classification is fragile
- **Impact**: Misclassifies technical queries containing punctuation

### 11. LOW: `AutoTest` script path broken after refactor
- **File**: `scripts/auto_test.py`
- **Issue**: After `auto_test.py` moved to `scripts/`, its internal paths may be stale
- **Impact**: Self-test script may fail

### 12. LOW: Redundant `import os` in multiple files
- **File**: `src/jig/sop_runner.py`, `src/jig/dispatcher.py`
- **Issue**: `import os` unused after refactoring
- **Impact**: Code cleanliness only

---

## Stats

| Category | Count |
|----------|:-----:|
| CRITICAL | 2 |
| HIGH | 3 |
| MEDIUM | 4 |
| LOW | 3 |
| **Total** | **12** |
