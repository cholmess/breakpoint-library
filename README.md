# BreakPoint Library

Prevent bad AI releases before they hit production.

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

Default command:

```bash
breakpoint evaluate baseline.json candidate.json
```

Lite mode defaults:
- Cost: `WARN` at `+20%`, `BLOCK` at `+40%`
- PII: `BLOCK` on first detection (email, phone, credit card)
- Drift: `WARN` at `+35%` length delta, `BLOCK` at `+70%`
- Empty output: always `BLOCK`

Lite is local, deterministic, and zero-config.

## Full Mode (Optional Advanced)

Use Full mode when you want config-driven governance and CI enforcement:

```bash
breakpoint evaluate baseline.json candidate.json --mode full --json --fail-on warn
```

Full mode adds advanced controls:
- Output contract enforcement
- Latency policy
- Presets/environments
- Waivers
- Custom pricing models

Example terminal output when those controls are in play (output contract, latency, cost, drift):

```bash
breakpoint evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_format_regression.json --mode full
```

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: full

Final Decision: BLOCK

Policy Results:
✓ No PII detected: No matches.
✗ Response format: Invalid JSON detected (1).
✓ Cost: No issues.
✓ Latency: Delta +2.78%.
✗ Output drift: Length delta +72.86%, similarity 0.067164.

Summary:
- Output contract break: candidate output is not valid JSON.
- Response length compressed: baseline 140 chars vs candidate 38 chars (72.9%, block threshold 70%).
2 additional non-blocking signal(s) detected.

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Here **Response format** = output contract enforcement; **Latency** = latency policy; **Cost** can use custom pricing when you pass token counts + model. Presets/environments and waivers change thresholds and appear in the same layout.

**Example: human-readable output (Full mode)**

```bash
breakpoint evaluate examples/quickstart/baseline.json examples/quickstart/candidate_warn.json --mode full
```

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: full

Final Decision: WARN

Policy Results:
✓ No PII detected: No matches.
✓ Response format: No schema drift detected.
⚠ Cost: Delta +25.00%.
⚠ Latency: Delta +35.00%.
⚠ Output drift: Length delta +52.17%, similarity 0.400000.

Summary:
Cost increased by 25.0% (>=20%).
2 additional signal(s) detected.

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Example: JSON output (Full mode, for CI)**

```bash
breakpoint evaluate examples/quickstart/baseline.json examples/quickstart/candidate_warn.json --mode full --config examples/quickstart/custom_policy.json --env dev --json
```

```json
{
  "schema_version": "1.0.0",
  "status": "BLOCK",
  "reasons": [
    "Cost increased by 25.0% (>=20%).",
    "Latency increased by 35.0% (>20%).",
    "Response length expanded: baseline 46 chars vs candidate 70 chars (52.2%, threshold 35%)."
  ],
  "reason_codes": [
    "COST_INCREASE_BLOCK",
    "LATENCY_INCREASE_WARN",
    "DRIFT_LENGTH_WARN"
  ],
  "metrics": {
    "cost_delta_pct": 25.0,
    "cost_delta_usd": 0.25,
    "latency_delta_pct": 35.0,
    "latency_delta_ms": 35.0,
    "length_delta_pct": 52.1739,
    "similarity": 0.4
  },
  "metadata": {
    "strict": false,
    "mode": "full",
    "baseline_model": "gpt-4.1-mini",
    "candidate_model": "gpt-4.1-mini",
    "ci": true
  }
}
```

(With stricter env thresholds, the same candidate can yield `BLOCK` and non-zero exit code.)

**What you see in the terminal**

When you run without `--json`, the CLI prints the human-readable block above: a divider line, **Mode**, **Final Decision** (ALLOW / WARN / BLOCK), **Policy Results** (✓ ⚠ ✗ per policy), **Summary**, and **Exit Code**. There are no colors or external UI libraries—plain text and Unicode symbols only so it stays dependency-free and CI-friendly. A richer terminal UI (e.g. colored status, panels, or metric tables) was considered but deprioritized for cost and simplicity; the current output is the supported terminal experience.

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

### Copy-Paste GitHub Actions Gate

Use the template:
- `examples/ci/github-actions-breakpoint.yml`

Copy it to:
- `.github/workflows/breakpoint-gate.yml`

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

Waivers (suppressions, Full mode):

```bash
breakpoint evaluate baseline.json candidate.json --mode full --config policy.json --now 2026-02-15T00:00:00Z --json
```

Config inspection:

```bash
breakpoint config print
breakpoint config print --config custom_policy.json
breakpoint config print --config custom_policy.json --env dev
```

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

## Additional Docs

- `docs/user-guide.md`
- `docs/user-guide-full-mode.md` (Full mode: config, presets, environments, waivers)
- `docs/quickstart-10min.md`
- `docs/install-worthy-examples.md`
- `docs/baseline-lifecycle.md`
- `docs/ci-templates.md`
- `docs/value-metrics.md`
- `docs/policy-presets.md`
- `docs/release-gate-audit.md`
