# BreakPoint AI

[![PyPI version](https://badge.fury.io/py/breakpoint-ai.svg)](https://pypi.org/project/breakpoint-ai/)
[![Tests](https://github.com/cholmess/breakpoint-ai/actions/workflows/test.yml/badge.svg)](https://github.com/cholmess/breakpoint-ai/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Local-first CI gate for LLM output changes.**

Changing prompts or models can introduce subtle regressions: cost spikes, PII leaks, format drift, or empty outputs. BreakPoint compares a known-good baseline artifact to a candidate output and returns one of three decisions: **ALLOW**, **WARN**, or **BLOCK**. It runs entirely locally—no SaaS, no telemetry, no API keys.

## What BreakPoint Solves

Traditional CI assumes deterministic behavior. LLM output is not deterministic. BreakPoint answers the question: *Is this change acceptable to ship?* You store a baseline (approved output) and compare new candidates against it before merging or deploying.

## Lite Mode (Zero Config)

Out of the box, BreakPoint applies these checks:

- **Cost:** WARN at +20%, BLOCK at +40%
- **PII:** Immediate BLOCK on email, phone, credit card (Luhn), SSN
- **Drift:** WARN at +35% length delta, BLOCK at +70%, BLOCK on empty output

Exit codes:

| Code | Decision |
|------|----------|
| 0 | ALLOW |
| 1 | WARN |
| 2 | BLOCK |

For config-driven policies, output contract, latency checks, presets, or waivers, use `--mode full` (see `docs/user-guide-full-mode.md`).

## 60-Second Quickstart

```bash
pip install breakpoint-ai
breakpoint evaluate baseline.json candidate.json
```

Each JSON needs at least an `output` field (string). Optional: `cost_usd`, `tokens_in`, `tokens_out`, `model`, `latency_ms`.

Example BLOCK output:

```text
Final Decision: BLOCK

Policy Results:
  ✗ Cost: Delta +68.89%. ($0.0450 → $0.0760)
  ✗ PII: US phone number pattern detected

Reason Codes: COST_INCREASE_BLOCK, PII_PHONE_BLOCK
```

## CI Integration

Minimal GitHub Actions workflow:

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

`--fail-on warn` fails the CI step on WARN or BLOCK. Use `fail_on: block` to fail only on BLOCK. Template: `examples/ci/github-actions-breakpoint.yml`.

## When To Use BreakPoint

- Shipping LLM features to production
- Merging prompt or model changes via PR
- Cost-sensitive systems

## When It May Not Be Necessary

- One-off experiments
- Hobby scripts
- Non-production workflows

## Why Local-First?

Most AI observability tools require sending prompts and outputs to SaaS. BreakPoint runs entirely on your machine. Artifacts stay in your repo. No network calls for evaluation.

## Try in 60 Seconds – FastAPI Demo

Watch BreakPoint catch a +68% token cost regression before it hits production:

![BreakPoint catching cost regression in FastAPI LLM demo](docs/demo-fastapi.gif)

Fork-and-play with pre-baked artifacts. No API keys required.

```bash
git clone https://github.com/cholmess/breakpoint-ai
cd breakpoint-ai/examples/fastapi-llm-demo
make install
make good        # Should PASS
make bad-tokens  # Should BLOCK
```

## Four Realistic Examples

```bash
# Baseline for all: examples/install_worthy/baseline.json

breakpoint evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_cost_model_swap.json    # BLOCK
breakpoint evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_format_regression.json # BLOCK
breakpoint evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_pii_verbosity.json      # BLOCK
breakpoint evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_killer_tradeoff.json   # BLOCK
```

Details: `docs/install-worthy-examples.md`.

## CLI

```bash
breakpoint evaluate baseline.json candidate.json
breakpoint evaluate payload.json                    # combined JSON with baseline + candidate
breakpoint evaluate baseline.json candidate.json --json --fail-on warn
```

## Input Schema

Each JSON object must have at least `output` (string). Optional: `cost_usd`, `model`, `tokens_total`, `tokens_in`, `tokens_out`, `latency_ms`. Combined format:

```json
{
  "baseline": { "output": "..." },
  "candidate": { "output": "..." }
}
```

## Pytest Plugin

```python
def test_my_agent(breakpoint):
    response = call_my_llm("Hello")
    breakpoint.assert_stable(response, candidate_metadata={"cost_usd": 0.002})
```

Baselines in `baselines/` next to the test file. Update with `BREAKPOINT_UPDATE_BASELINES=1 pytest`.

## Python API

```python
from breakpoint import evaluate

decision = evaluate(
    baseline_output="hello",
    candidate_output="hello there",
    metadata={"baseline_tokens": 100, "candidate_tokens": 140},
)
print(decision.status, decision.reasons)
```

## Troubleshooting

- `ModuleNotFoundError: breakpoint`: `pip install breakpoint-ai`
- File not found: Check paths; files must exist.
- JSON validation: Ensure at least `output` (string) in each object.

## Additional Docs

- `docs/user-guide.md`
- `docs/user-guide-full-mode.md`
- `docs/quickstart-10min.md`
- `docs/install-worthy-examples.md`
- `docs/baseline-lifecycle.md`
- `docs/ci-templates.md`
- `docs/value-metrics.md`
- `docs/policy-presets.md`
- `docs/release-gate-audit.md`
- `docs/terminal-output-lite-vs-full.md`

## Topics

For discoverability: `ai`, `llm`, `evaluation`, `ci`, `quality-gate`, `github-actions`, `breakpoint`, `llmops`, `ai-safety`, `regression-testing`, `mlops`, `guardrails`.

---

## Maintainer

BreakPoint is maintained by Christopher Holmes Silva.

- X: [https://x.com/cholmess](https://x.com/cholmess)
- LinkedIn: [https://linkedin.com/in/christopher-holmes-silva](https://www.linkedin.com/in/cholmess/)

Feedback and real-world usage stories are welcome—[open an issue](https://github.com/cholmess/breakpoint-ai/issues) or email [c.holmes.silva@gmail.com](mailto:c.holmes.silva@gmail.com).
