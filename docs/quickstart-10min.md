# 10-Minute Quickstart

This walkthrough gets you from install to a reproducible `BLOCK` decision in about 10 minutes.

## Prerequisites

- Python 3.10+
- Local clone of this repository

## 1) Install (1 minute)

```bash
pip install -e .
```

## 2) Run ALLOW / WARN / BLOCK samples with CLI (4 minutes)

All sample files are in `examples/quickstart/`.

ALLOW:

```bash
breakpoint evaluate examples/quickstart/baseline.json examples/quickstart/candidate_allow.json --json
```

Expected status: `ALLOW`

WARN:

```bash
breakpoint evaluate examples/quickstart/baseline.json examples/quickstart/candidate_warn.json --json --fail-on warn
```

Expected status: `WARN`, exit code `1`

BLOCK:

```bash
breakpoint evaluate examples/quickstart/baseline.json examples/quickstart/candidate_block.json --json --fail-on block
```

Expected status: `BLOCK`, exit code `2`

## 3) Run with environment overrides (2 minutes)

Use environment-aware policy thresholds:

```bash
breakpoint evaluate \
  examples/quickstart/baseline.json \
  examples/quickstart/candidate_warn.json \
  --mode full \
  --config examples/quickstart/custom_policy.json \
  --env dev \
  --json
```

Inspect merged config:

```bash
breakpoint config print --config examples/quickstart/custom_policy.json --env dev --compact
```

## 4) Run with Python API (2 minutes)

```python
import json
from pathlib import Path

from breakpoint import evaluate

baseline = json.loads(Path("examples/quickstart/baseline.json").read_text(encoding="utf-8"))
candidate = json.loads(Path("examples/quickstart/candidate_block.json").read_text(encoding="utf-8"))

decision = evaluate(baseline=baseline, candidate=candidate)
print(decision.status)        # BLOCK
print(decision.reason_codes)  # includes PII_EMAIL_BLOCK
print(decision.to_dict())     # contract v1 payload
```

## Expected Output Notes

- Decision payload includes `schema_version`, `status`, `reasons`, `reason_codes`.
- Optional `metrics` and `metadata` appear when available.
- Exit code mapping is stable:
  - `0` => `ALLOW`
  - `1` => `WARN`
  - `2` => `BLOCK`

## Troubleshooting

- `ModuleNotFoundError: breakpoint`: run `pip install -e .` from repo root.
- Unexpected `WARN` from missing data: include `cost_usd` and `latency_ms` in baseline and candidate.
- Config env error: ensure `--env` matches a key inside `environments` in config JSON.
- Validation error in JSON mode: inspect `reason_codes` for `INPUT_VALIDATION_ERROR`.
