# BreakPoint Library

Local-first policy engine to compare baseline vs candidate LLM outputs and return `ALLOW`, `WARN`, or `BLOCK`.

## Quickstart

```bash
pip install -e .
breakpoint evaluate baseline.json candidate.json
```

Detailed 10-minute walkthrough:
- `docs/quickstart-10min.md`

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
- `1` = `WARN`
- `2` = `BLOCK`

Gate threshold options:

```bash
# fail on WARN or BLOCK
breakpoint evaluate baseline.json candidate.json --fail-on warn

# fail only on BLOCK
breakpoint evaluate baseline.json candidate.json --fail-on block
```

Waivers (suppressions):

```bash
breakpoint evaluate baseline.json candidate.json --config policy.json --now 2026-02-15T00:00:00Z --json
```

Print the effective (merged) config:

```bash
breakpoint config print
breakpoint config print --config custom_policy.json
breakpoint config print --config custom_policy.json --env dev
```

Baseline lifecycle guidance:
- `docs/baseline-lifecycle.md`

CI templates:
- `docs/ci-templates.md`

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
