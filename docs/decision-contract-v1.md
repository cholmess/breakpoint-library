# Decision Contract v1

This document defines the deterministic output contract for BreakPoint decisions.

## Scope

- Applies to `evaluate()` API output and CLI JSON output.
- Defines stable field names and meanings for Phase 1.
- Defines reason code taxonomy and validation behavior.

## Schema Version

- `schema_version` is required.
- Current version: `1.0.0`.
- Any breaking output change requires a new major schema version.

## Decision JSON Shape

```json
{
  "schema_version": "1.0.0",
  "status": "WARN",
  "reasons": [
    "Cost increased by 24%",
    "Output drift detected"
  ],
  "reason_codes": [
    "COST_INCREASE_WARN",
    "DRIFT_LENGTH_WARN"
  ],
  "metrics": {
    "cost_delta_pct": 24.0,
    "latency_delta_pct": 12.3,
    "length_delta_pct": 31.5
  },
  "metadata": {
    "baseline_model": "gpt-4o-mini",
    "candidate_model": "gpt-4.1-mini",
    "strict": false
  }
}
```

## Field Contract

- `schema_version` (`string`, required): semantic version of the output contract.
- `status` (`string`, required): one of `ALLOW`, `WARN`, `BLOCK`.
- `reasons` (`array[string]`, required): human-readable explanations in deterministic order.
- `reason_codes` (`array[string]`, required): machine-readable codes in deterministic order, positionally aligned with `reasons`.
- `metrics` (`object`, optional): normalized numeric metrics used to derive policy decisions.
- `metadata` (`object`, optional): normalized runtime context and input annotations.

Additional metadata fields (optional):
- `waivers_applied` (`array[object]`, optional): list of applied waivers with `reason_code`, `expires_at`, and audit fields.

## Determinism Rules

- Same normalized inputs must produce byte-equivalent JSON output.
- `reasons` and `reason_codes` order must be stable.
- Float metrics must be normalized to a fixed precision before serialization.
- Absent optional fields must be omitted consistently.

## Reason Code Taxonomy (v1)

Cost policy:
- `COST_INCREASE_WARN`
- `COST_INCREASE_BLOCK`

Latency policy:
- `LATENCY_INCREASE_WARN`
- `LATENCY_INCREASE_BLOCK`

PII policy:
- `PII_EMAIL_BLOCK`
- `PII_PHONE_BLOCK`
- `PII_CREDIT_CARD_BLOCK`
- `PII_SSN_BLOCK`

Drift policy:
- `DRIFT_EMPTY_OUTPUT_WARN`
- `DRIFT_TOO_SHORT_WARN`
- `DRIFT_LENGTH_WARN`
- `DRIFT_SIMILARITY_WARN`

Aggregator/system:
- `STRICT_MODE_PROMOTION_BLOCK`
- `INPUT_VALIDATION_ERROR`
- `CONFIG_VALIDATION_ERROR`

## Validation Contract

Input validation must fail fast with actionable messages.

Minimum required:
- Baseline output text exists.
- Candidate output text exists.

Policy-dependent required metadata:
- Cost policy: either explicit `cost_usd` values or resolvable token + model pricing data.
- Latency policy: baseline and candidate latency values if latency policy is enabled.

Error response contract (CLI JSON mode):

```json
{
  "schema_version": "1.0.0",
  "status": "BLOCK",
  "reasons": [
    "Missing required field: candidate.output"
  ],
  "reason_codes": [
    "INPUT_VALIDATION_ERROR"
  ]
}
```

## CLI/API Parity

- `evaluate()` and CLI JSON mode must emit the same decision payload shape.
- CLI text mode may be condensed, but content must map 1:1 to JSON payload.

## Exit Code Mapping (P0 target)

- `0`: `ALLOW`
- `1`: `WARN`
- `2`: `BLOCK`

This mapping is part of the CI gate contract and must be treated as stable once released.

CLI failure policy:
- `--exit-codes`: equivalent to `--fail-on warn` for backward compatibility.
- `--fail-on warn`: non-zero on `WARN` and `BLOCK`.
- `--fail-on block`: non-zero only on `BLOCK`.

## Backward Compatibility

- New optional fields may be added in minor versions.
- Existing required fields cannot be renamed or removed in minor versions.
- New reason codes may be added; existing published codes cannot change meaning.
