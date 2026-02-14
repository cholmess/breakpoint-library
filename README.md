# BreakPoint Library

Local-first policy engine to compare baseline vs candidate LLM outputs and return `ALLOW`, `WARN`, or `BLOCK`.

## Quickstart

```bash
pip install -e .
breakpoint evaluate baseline.json candidate.json
```

## CLI

Evaluate two JSON files:

```bash
breakpoint evaluate baseline.json candidate.json
```

Evaluate a single combined JSON file:

```bash
breakpoint evaluate payload.json
```

Emit JSON and non-zero exit codes (useful for CI):

```bash
breakpoint evaluate baseline.json candidate.json --json --exit-codes
```

Exit codes:
- `0` = `ALLOW`
- `2` = `WARN`
- `3` = `BLOCK`

Print the effective (merged) config:

```bash
breakpoint config print
breakpoint config print --config custom_policy.json
```

## Input schema

Each input JSON is an object with at least:
- `output` (string)

Optional fields (used by policies):
- `cost_usd` (number)
- `model` (string)
- `tokens_total` (number)
- `tokens_in` / `tokens_out` (number)
- `latency_ms` (number)

Combined input schema:

```json
{
  "baseline": { "output": "..." },
  "candidate": { "output": "..." }
}
```

## Python API

```python
from breakpoint import evaluate

decision = evaluate(
    baseline_output="hello",
    candidate_output="hello there",
    metadata={"baseline_tokens": 100, "candidate_tokens": 140},
)
print(decision.status)
print(decision.reasons)
```
