# Spec: 12-Factor Agents Compliance (IDEA-056)

**Priority**: P1 | **Est**: 1 week

## Why
3 of 12 factors are unmet: #4 (Structured Output Validation), #9 (HITL API), #11 (OpenTelemetry). Each represents a production-readiness gap.

## What Changes
- OTel: full trace (Agent calls, Tool calls, Memory ops, Harness gates) + metrics
- Structured Output: Pydantic model auto-validation for all Agent outputs
- HITL: approval/modify/veto/supplement API at decision points

## Merge Notes
Merges IDEA-038 (OTel) + IDEA-039 (Structured Output) + IDEA-040 (HITL) into one compliance spec.

## Checkpoints
- [ ] OTel traces for all 4 component types
- [ ] Metrics dashboard (token usage, API latency, cache hit rate)
- [ ] All Agent outputs validated against Pydantic schema
- [ ] HITL endpoints deployed and tested
