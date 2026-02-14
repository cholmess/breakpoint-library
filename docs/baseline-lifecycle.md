# Baseline Lifecycle v1

This document defines how to create, approve, refresh, and roll back BreakPoint baselines.

## Baseline File Format

Baseline files are JSON objects with contract versioning:

```json
{
  "baseline_schema_version": "1.0.0",
  "id": "support-bot-default",
  "created_at": "2026-02-15T00:00:00Z",
  "created_by": "team-handle",
  "approved_by": "reviewer-handle",
  "notes": "Initial approved baseline",
  "input": {
    "output": "Hello! How can I help?",
    "cost_usd": 1.0,
    "latency_ms": 100,
    "model": "gpt-4.1-mini"
  }
}
```

Required fields:
- `baseline_schema_version` (`string`)
- `id` (`string`)
- `created_at` (`ISO-8601 string`)
- `created_by` (`string`)
- `approved_by` (`string`)
- `input` (`object`) compatible with BreakPoint baseline input schema

## Decision Evaluation Pattern

Use the baseline `input` object against a candidate payload:

```bash
breakpoint evaluate baseline_input.json candidate_input.json --json --fail-on warn
```

For lifecycle-managed files:
1. Extract `input` from baseline artifact.
2. Evaluate candidate against that `input`.
3. Store decision JSON artifact in CI for traceability.

## Refresh Policy

Refresh baseline when one of these is true:
- Product behavior intentionally changed and approved.
- Repeated false positives are caused by stale baseline assumptions.
- Model/provider migration is complete and accepted.

Recommended cadence:
- Fast-moving teams: weekly.
- Stable teams: biweekly or release-based.

Approval rule:
- `created_by` and `approved_by` must be different people.

## Versioning and Storage

- Keep baseline files under version control in a dedicated folder.
- Use immutable IDs for each logical flow (`id`).
- Never edit historical baseline files in place; add a new file with a new timestamp.
- Keep at least one previous approved baseline for rollback.

## Rollback Procedure

1. Identify the last known-good baseline artifact.
2. Re-run evaluation using that baseline and the same candidate.
3. Confirm decision returns expected status.
4. Update CI config to point at rollback baseline.
5. Open a follow-up issue to analyze why the new baseline was rejected.

## Sample Layout

```text
baselines/
  support-bot/
    baseline-2026-02-01.json
    baseline-2026-02-15.json
```

## Reproducibility Requirements

- Evaluating the same baseline + candidate inputs must produce the same decision payload.
- Baseline artifacts must include enough context (`model`, `cost`, `latency`) to avoid ambiguous policy paths.
- CI must archive baseline ID + decision payload per run.
