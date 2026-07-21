# Real Project Proposal: Dogfood Code Review + Security Audit

> Phase 1 — Verification (2026 Q3) | Direction C: Eat your own dog food
> Estimated: 2 weeks · 2026-07-21 → 2026-08-04

## TL;DR

Use AgentHarness's own SOP pipeline to perform a **full code review + security audit of AgentHarness itself**. This validates the framework on a real, non-trivial project and produces immediate value.

---

## User Story (Gherkin)

```gherkin
Feature: Self-hosted Code Review Pipeline

  Scenario: Full pipeline code review
    Given a Python project at D:\Desktop\tree-sop-agent
    When I run "python run.py --project self --pipeline code-review"
    Then the Dispatcher routes to PM Agent
    And PM Agent produces a scope document
    And Trinity Agent performs architecture review
    And Spec-Pipeline splits the codebase into review tasks
    And Coding Agent iterates over each module
    And Code-Review Agent produces review reports
    And TDD Agent validates test coverage
    And Acceptance + Security run in parallel
    And Secretary Agent compiles the final report
```

## SOP Pipeline Used

```
Dispatcher ─→ PM ─→ Trinity ─→ Spec ─→ Coding ─→ Code-Review
          ─→ TDD ─→ Acceptance ∥ Security ─→ Secretary
```

## Involved Agents

| Agent | Role in This Project |
|-------|---------------------|
| Dispatcher | Receive "self-review" command, route to PM |
| PM (Pro) | Define review scope: which modules, what depth |
| Trinity (Pro) | Architecture-level review of 4-layer design |
| Spec-Pipeline (Pro) | Split codebase into reviewable chunks |
| Coding (Flash) | Iterate modules, prepare code for review |
| Code-Review (Pro) | Inspect each module for style/bugs/security |
| TDD (Flash) | Validate test coverage, suggest missing tests |
| Acceptance (Flash) | Verify checklist: 62 tests, all green |
| Security (Pro) | Full audit: injection, secrets, path traversal |
| DevOps (Flash) | Build verification, dependency audit |
| Secretary (Flash) | Compile report, update kanban |

## Expected Pain Points

1. **Dispatcher context window** — The entire codebase description may exceed context limits
2. **Coding Agent timeout** — DeepSeek API latency on large file iteration
3. **HandoverPackage overload** — 10 agents × 5 rounds = 50+ handover packages
4. **Security Audit depth** — Security Agent may need multiple passes for deep analysis
5. **Secretary aggregation** — Compiling 10+ review reports into one coherent document
6. **Configuration gaps** — First real run may expose missing config defaults
7. **Error handling** — Pipeline must recover gracefully from individual agent failures
8. **User feedback loop** — No built-in pause/resume for human review mid-pipeline
9. **Token budget** — Full pipeline may exceed session token limits
10. **Cache invalidation** — Different agents need different prefixes, reducing cache efficiency

## Success Criteria

| Criterion | Target | Verification |
|-----------|--------|-------------|
| Pipeline completes | 100% of agents produce output | HandoverPackage chain intact |
| Issues found | ≥10 real code issues | Secretary report |
| Test holes found | ≥3 missing test cases | TDD Agent report |
| Security vulnerabilities | ≥2 findings | Security Agent report |
| Review time | <30 minutes | CheckpointManager resume |
| User intervention | ≤3 manual interventions | Log analysis |

## Risks

| Risk | Mitigation |
|------|-----------|
| API cost high (>$5 per run) | Use Flash for Coding/TDD, Pro only for Review/Security |
| Pipeline deadlock | CircuitBreaker max-iteration cap |
| Checkpoint resume fails | Manual fallback: re-run from last successful checkpoint |
| Agent hallucination | ToolGuard blocks invalid tool calls |
