# BreakPoint v0.2.0-rc1 Release Notes

Date: 2026-02-15
Status: Release Candidate

## Summary

This release candidate focuses on one goal: make BreakPoint install-worthy in the first minute.

Key outcomes:
- Deterministic CLI verdict format with actionable sections.
- Quantified deltas in text and JSON output.
- Realistic install-worthy demo scenarios with one-command execution.
- Stronger format/contract regression detection for structured outputs.
- Reduced noisy drift warnings via default threshold tuning.
- Golden snapshot tests for CLI output stability.

## What’s New

### 1) Deterministic 30-second CLI verdict output

`breakpoint evaluate` text output now follows a stable structure:
- `VERDICT`
- `TOP_REASONS`
- `KEY_DELTAS`
- `RECOMMENDED_ACTION`

This improves scanability and makes next action explicit for `ALLOW/WARN/BLOCK`.

### 2) Quantified deltas across high-signal risks

Decision metrics and CLI `KEY_DELTAS` now surface measurable changes including:
- Cost (`cost_delta_pct`, `cost_delta_usd`)
- Latency (`latency_delta_pct`, `latency_delta_ms`)
- Drift (`length_delta_pct`, `short_ratio`, `similarity`)
- PII (`pii_blocked_total`, `pii_blocked_type_count`)
- Output contract (`output_contract_invalid_json_count`, `output_contract_missing_keys_count`, `output_contract_type_mismatch_count`)

### 3) Output contract policy for structured output regressions

New policy: `output_contract_policy` (enabled by default)
- Blocks invalid JSON candidate output when baseline output is valid JSON.
- Blocks top-level JSON type changes.
- Warns on missing keys.
- Warns on key type mismatches.

New reason codes:
- `OUTPUT_CONTRACT_INVALID_JSON_BLOCK`
- `OUTPUT_CONTRACT_INVALID_JSON_WARN`
- `OUTPUT_CONTRACT_TYPE_CHANGE_BLOCK`
- `OUTPUT_CONTRACT_MISSING_KEYS_WARN`
- `OUTPUT_CONTRACT_TYPE_MISMATCH_WARN`

### 4) Install-worthy demo pack and one-command run

Added realistic scenarios in `examples/install_worthy/` and a one-command runner:

```bash
make demo
```

Demo includes model swap cost spike, format regression, PII/verbosity drift, and a killer tradeoff scenario.

### 5) README and docs overhaul for adoption

README now leads with pain/outcome and includes:
- `Try in 60 seconds`
- Three copy-paste examples with expected outcomes
- Direct links to install-worthy demo docs

### 6) Trust tuning and verification hardening

- Drift defaults tuned to reduce noisy WARNs:
  - `warn_length_delta_pct`: `75`
  - `warn_short_ratio`: `0.30`
  - `warn_min_similarity`: `0.10`
- Added CLI golden snapshots for ALLOW/WARN/BLOCK output stability.
- Added tests for action guidance strings and contract regression behavior.

## Behavior Changes To Note

- Format-regression scenarios that were previously `WARN` may now be `BLOCK` when candidate output is invalid JSON and baseline output is valid JSON.
- CLI text output format has changed to the fixed four-section layout.

## Validation

Release candidate validation completed:

```bash
pytest -q
```

Result:
- `53 passed` on 2026-02-15

Publish gate audit:
- `docs/release-gate-audit.md`

## Upgrade / Run

Install editable build:

```bash
pip install -e .
```

Quick demo:

```bash
make demo
```

JSON output for CI:

```bash
breakpoint evaluate baseline.json candidate.json --json --fail-on warn
```

## Known Follow-up

- Improve drift reason text to be more symptom-specific and less generic.
- Run beta-user feedback loop to quantify false-positive rate and true-positive catches.
