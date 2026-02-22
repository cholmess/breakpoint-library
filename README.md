# BreakPoint AI

[![PyPI](https://img.shields.io/pypi/v/breakpoint-ai?cache=bust)](https://pypi.org/project/breakpoint-ai/)
[![Tests](https://github.com/cholmess/breakpoint-ai/actions/workflows/test.yml/badge.svg)](https://github.com/cholmess/breakpoint-ai/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Prevent bad AI releases before they hit production.

```bash
pip install breakpoint-ai
```

You change a model.
The output looks fine.
But:
- Cost jumps +38%.
- A phone number slips into the response.
- The format breaks your downstream parser.

BreakPoint catches it before you deploy.

It runs locally.
Policy evaluation is deterministic from your saved artifacts.
It gives you one clear answer:

`ALLOW` · `WARN` · `BLOCK`

## Quick Example

**Baseline** = Output artifact representing approved behavior. You compare a new candidate against it.

Zero friction—no pre-built files:

```bash
echo '{"output": "hello world"}' > baseline.json
echo '{"output": "HELLO WORLD!"}' > candidate.json
breakpoint evaluate baseline.json candidate.json
```

Or with existing files:

```bash
breakpoint evaluate baseline.json candidate.json
```

```text
STATUS: BLOCK

Reasons:
- Cost increased by 38% (baseline: 1,000 tokens -> candidate: 1,380)
- Detected US phone number pattern
```

Ship with confidence.

## Lite First (Default)

This is all you need to get started:

```bash
breakpoint evaluate baseline.json candidate.json
```

Lite is local, deterministic, and zero-config. Out of the box:
- Cost: `WARN` at `+20%`, `BLOCK` at `+40%`
- PII: `BLOCK` on first detection (email, phone, credit card)
- Drift: `WARN` at `+35%`, `BLOCK` at `+70%`
- Empty output: always `BLOCK`

**Advanced option:** Need config-driven policies, output contract, latency, presets, or waivers? Use `--mode full` and see `docs/user-guide-full-mode.md`.

## Full Mode (If You Need It)

Add `--mode full` when you need config-driven policies, output contract, latency, presets, or waivers. Full details: `docs/user-guide-full-mode.md`.

```bash
breakpoint evaluate baseline.json candidate.json --mode full --json --fail-on warn
```

## CI First (Recommended)

```bash
breakpoint evaluate baseline.json candidate.json --json --fail-on warn
```

Why this is the default integration path:
- Machine-readable decision payload (`schema_version`, `status`, `reason_codes`, metrics).
- Non-zero exit code on risky changes.
- Easy to wire into existing CI without additional services.

Default policy posture (out of the box, Lite):
- Cost: `WARN` at `+20%`, `BLOCK` at `+40%`
- PII: `BLOCK` on first detection
- Drift: `WARN` at `+35%`, `BLOCK` at `+70%`

### GitHub Action (Marketplace)

Use the [BreakPoint Evaluate action](https://github.com/marketplace/actions/breakpoint-evaluate) in any workflow:

```yaml
- uses: cholmess/breakpoint-ai@v1
  with:
    baseline: baseline.json
    candidate: candidate.json
    fail_on: warn
    mode: lite
```

Pre-merge gate example:

```yaml
name: BreakPoint Gate
on:
  pull_request:
    branches: [main]
jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate candidate
        run: # ... produce candidate.json from your model
      - name: BreakPoint Evaluate
        uses: cholmess/breakpoint-ai@v1
        with:
          baseline: baseline.json
          candidate: candidate.json
          fail_on: warn
```

Or copy the template: `examples/ci/github-actions-breakpoint.yml` → `.github/workflows/breakpoint-gate.yml`

What `--fail-on warn` means:
- Any `WARN` or `BLOCK` fails the CI step.
- Exit behavior remains deterministic: `ALLOW=0`, `WARN=1`, `BLOCK=2`.

If you only want to fail on `BLOCK`, change:
- `BREAKPOINT_FAIL_ON: warn`
to:
- `BREAKPOINT_FAIL_ON: block`

## Try In 60 Seconds

```bash
pip install -e .
make demo
```

What you should see:
- Scenario A: `BLOCK` (cost spike)
- Scenario B: `BLOCK` (format/contract regression)
- Scenario C: `BLOCK` (PII + verbosity drift)
- Scenario D: `BLOCK` (small prompt change -> cost blowup)

## Four Realistic Examples

Baseline for all examples:
- `examples/install_worthy/baseline.json`

### 1) Cost regression after model swap

```bash
breakpoint evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_cost_model_swap.json
```

Expected: `BLOCK`
Why it matters: output appears equivalent, but cost increases enough to violate policy.

### 2) Structured-output behavior regression

```bash
breakpoint evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_format_regression.json
```

Expected: `BLOCK`
Why it matters: candidate drops expected structure and drifts from baseline behavior.

### 3) PII appears in candidate output

```bash
breakpoint evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_pii_verbosity.json
```

Expected: `BLOCK`
Why it matters: candidate introduces PII and adds verbosity drift.

### 4) Small prompt change -> big cost blowup

```bash
breakpoint evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_killer_tradeoff.json
```

Expected: `BLOCK`
Why it matters: output still looks workable, but detail-heavy prompt changes plus a model upgrade create large cost and latency increases with output-contract drift.

More scenario details:
- `docs/install-worthy-examples.md`

## CLI

Evaluate two JSON files:

```bash
breakpoint evaluate baseline.json candidate.json
```

Evaluate a single combined JSON file:

```bash
breakpoint evaluate payload.json
```

JSON output for CI/parsing:

```bash
breakpoint evaluate baseline.json candidate.json --json
```

Exit-code gating options:

```bash
# fail on WARN or BLOCK
breakpoint evaluate baseline.json candidate.json --fail-on warn

# fail only on BLOCK
breakpoint evaluate baseline.json candidate.json --fail-on block
```

Stable exit codes:
- `0` = `ALLOW`
- `1` = `WARN`
- `2` = `BLOCK`

Waivers, config, presets: see `docs/user-guide-full-mode.md`.

## Input Schema

Each input JSON is an object with at least:
- `output` (string)

Optional fields used by policies:
- `cost_usd` (number)
- `model` (string)
- `tokens_total` (number)
- `tokens_in` / `tokens_out` (number)
- `latency_ms` (number)

Combined input format:

```json
{
  "baseline": { "output": "..." },
  "candidate": { "output": "..." }
}
```

## Pytest Plugin

Assert LLM output stability in your tests:

```python
def test_my_agent(breakpoint):
    response = call_my_llm("Hello")
    breakpoint.assert_stable(response, candidate_metadata={"cost_usd": 0.002})
```

Baselines live in `baselines/` next to your test file. To create/update them:

```bash
BREAKPOINT_UPDATE_BASELINES=1 pytest
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

## Troubleshooting

- `ModuleNotFoundError: breakpoint`: Run `pip install breakpoint-ai` (or `pip install -e .` if developing).
- File not found errors: Ensure baseline and candidate JSON paths are correct and files exist.
- JSON validation errors: Verify your JSON files have at least an `output` field (string). See Input Schema above.

## Additional Docs

- `docs/user-guide.md`
- `docs/user-guide-full-mode.md` (Full mode: config, presets, environments, waivers)
- `docs/terminal-output-lite-vs-full.md` (Lite vs Full terminal output, same format)
- `docs/quickstart-10min.md`
- `docs/install-worthy-examples.md`
- `docs/baseline-lifecycle.md`
- `docs/ci-templates.md`
- `docs/value-metrics.md`
- `docs/policy-presets.md`
- `docs/release-gate-audit.md`

## Topics

Add these topics in your repo settings for discoverability: `ai`, `llm`, `evaluation`, `ci`, `quality-gate`, `github-actions`, `breakpoint`.

## Contact

**First-time user?** We'd love your feedback — [open an issue](https://github.com/cholmess/breakpoint-ai/issues) or email [c.holmes.silva@gmail.com](mailto:c.holmes.silva@gmail.com).

Suggestions and feedback: [c.holmes.silva@gmail.com](mailto:c.holmes.silva@gmail.com) or [open an issue](https://github.com/cholmess/breakpoint-ai/issues).
