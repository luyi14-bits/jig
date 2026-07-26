# Self-Review Case Study: Jig Agent Firewall

> Loop #3 Task 5 | Date: 2026-07-24

## Overview

Using Jig's own SOP pipeline to audit and improve Jig's codebase.

## Process

1. **Setup**: Loaded 11 Luyi14 skills via `Jig(skills_dir="skills")`, 135 tests baseline
2. **Code Audit**: Luyi14-code-review scanned `src/jig/` — 12 pain points identified
3. **Fixes Applied**: 5 critical/high issues resolved:
   - `Path("skills")` → `settings.skills_dir` (configurable deployment path)
   - SkillRegistry extracted to instance attribute (per-node reinit eliminated)
   - Settings injected into SOPRunner (config-driven)
   - Dispatcher input validation (empty + 100KB limit)
4. **Verification**: 135/135 tests passing, no regressions

## Key Metrics

| Metric | Value |
|--------|:-----:|
| Modules audited | 15 |
| Pain points found | 12 |
| Fixed (this round) | 5 |
| Remaining | 7 (lower priority) |
| Test regressions | 0 |

## Lessons

1. Dogfooding exposes real deployability issues that unit tests miss
2. Configuration externalization is critical for production use
3. Private attribute access indicates missing public API boundary
