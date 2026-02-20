# BreakPoint User Guide — Full Mode

This guide explains how to use BreakPoint in **Full mode**: config-driven policies, output contract enforcement, latency, presets, environments, waivers, and custom pricing.

## Terminal Output: How Full Differs from Lite

In **Lite** mode the terminal shows only the policies that run: **3 lines** (No PII, Cost, Output drift). **Response format** and **Latency** are not evaluated, so they are not shown.

In **Full** mode the terminal shows **5 lines**: No PII, **Response format**, Cost, **Latency**, Output drift. So you can tell the mode at a glance: Lite has 3 policy lines, Full has 5.

For a side-by-side reference in the same format (Command → Actual Output → Result), see **`docs/terminal-output-lite-vs-full.md`**.

## When to Use Full Mode

Use Full mode when you need:

- **Output contract enforcement** — baseline output is JSON; candidate must be valid JSON and respect keys/types.
- **Latency policy** — WARN/BLOCK on latency increase (e.g. +25% / +60%).
- **Presets** — built-in threshold bundles (e.g. `chatbot`, `support`, `extraction`).
- **Environments** — different thresholds per env (e.g. `dev` vs `prod`).
- **Waivers** — time-limited suppressions for specific reason codes (e.g. known cost variance).
- **Custom pricing** — cost derived from `tokens_in`/`tokens_out` + `model` using a pricing table.

Lite mode (default) does not support `--config`, `--preset`, `--env`, or `--now`; use Full mode for those.

## Enabling Full Mode

Always pass `--mode full`. Optionally pass a config file, preset, or environment:

```bash
breakpoint evaluate baseline.json candidate.json --mode full
breakpoint evaluate baseline.json candidate.json --mode full --config policy.json
breakpoint evaluate baseline.json candidate.json --mode full --config policy.json --env prod
breakpoint evaluate baseline.json candidate.json --mode full --preset extraction --json
```

Without `--config`, Full mode uses the built-in default policies (same shape as `breakpoint/config/default_policies.json`).

## Config File Structure

A Full-mode config is a JSON object. You can override only the sections you need; the rest are filled from the built-in defaults.

### Top-level keys

| Key | Purpose |
|-----|--------|
| `cost_policy` | `min_baseline_cost_usd`, `warn_increase_pct`, `block_increase_pct`, `warn_delta_usd`, `block_delta_usd` |
| `pii_policy` | `patterns` (email, phone, credit_card, ssn), `allowlist` |
| `output_contract_policy` | `enabled`, `block_on_invalid_json`, `warn_on_missing_keys`, `warn_on_type_mismatch` |
| `drift_policy` | `warn_length_delta_pct`, `block_length_delta_pct`, `warn_short_ratio`, `warn_min_similarity`, etc. |
| `latency_policy` | `min_baseline_latency_ms`, `warn_increase_pct`, `block_increase_pct`, `warn_delta_ms`, `block_delta_ms` |
| `strict_mode` | `enabled` — when true, WARN is promoted to BLOCK |
| `model_pricing` | Per-model `input_per_1k`, `output_per_1k` (or `per_1k`) in USD for cost resolution when `cost_usd` is missing |
| `environments` | Named overrides (e.g. `dev`, `prod`) that merge over the base config when you pass `--env` |
| `waivers` | Array of waiver objects (reason_code, expires_at, reason, issued_by, ticket) |

### Minimal custom config (environments only)

Example: `policy.json` with only environment overrides (other policies come from defaults):

```json
{
  "environments": {
    "dev": {
      "cost_policy": { "warn_increase_pct": 10, "block_increase_pct": 20 },
      "latency_policy": { "warn_increase_pct": 20, "block_increase_pct": 40 }
    },
    "prod": {
      "cost_policy": { "warn_increase_pct": 20, "block_increase_pct": 35 },
      "latency_policy": { "warn_increase_pct": 30, "block_increase_pct": 60 }
    }
  }
}
```

Run with an environment:

```bash
breakpoint evaluate baseline.json candidate.json --mode full --config policy.json --env dev --json
```

### Inspecting the effective config

To see the merged config (defaults + preset + your config + environment):

```bash
breakpoint config print
breakpoint config print --config policy.json --env prod
breakpoint config print --preset extraction --config policy.json --compact
```

Use `--preset` and/or `--config` and/or `--env` to match your evaluate command.

## Presets

Presets are built-in threshold bundles. They are merged *before* your `--config` file, so your config can override preset values.

List presets:

```bash
breakpoint config presets
```

Example output: `chatbot`, `support`, `extraction`.

Use a preset:

```bash
breakpoint evaluate baseline.json candidate.json --mode full --preset extraction --json
```

Inspect a preset’s effective config:

```bash
breakpoint config print --preset extraction
```

Presets only adjust thresholds (e.g. drift, cost, latency); they do not define output contract or PII patterns.

## Environments

Environments live under the `environments` key in your config. When you pass `--env <name>`, BreakPoint merges `environments.<name>` over the base config.

Example (same as the minimal config above):

```json
{
  "environments": {
    "dev": {
      "cost_policy": { "warn_increase_pct": 10, "block_increase_pct": 20 }
    },
    "prod": {
      "cost_policy": { "warn_increase_pct": 20, "block_increase_pct": 35 }
    }
  }
}
```

- `--env dev` → stricter cost thresholds (10% / 20%).
- `--env prod` → 20% / 35%.
- No `--env` → base config only.

Ensure `--env` matches a key under `environments`; otherwise you get a validation error.

## Waivers

Waivers let you temporarily suppress specific reason codes (e.g. a known cost increase until a fix ships). They apply only in Full mode and require an evaluation time so expiry can be checked.

### Config

Add a `waivers` array to your config. Each waiver must have:

- `reason_code` — e.g. `COST_INCREASE_WARN`, `LATENCY_INCREASE_WARN`
- `expires_at` — ISO-8601 UTC (e.g. `2026-12-31T00:00:00Z`)
- `reason` — short explanation
- `issued_by` — string (e.g. team or person)
- `ticket` — string (e.g. ticket ID)

Example:

```json
{
  "waivers": [
    {
      "reason_code": "COST_INCREASE_WARN",
      "expires_at": "2026-12-31T00:00:00Z",
      "reason": "Known cost variance for dev.",
      "issued_by": "team-ai",
      "ticket": "BP-123"
    }
  ]
}
```

### Providing evaluation time

Waivers require a single evaluation time (for expiry). Pass it via CLI or API.

CLI:

```bash
breakpoint evaluate baseline.json candidate.json --mode full --config policy.json --now 2026-02-15T00:00:00Z --json
```

Python:

```python
from breakpoint import evaluate

decision = evaluate(
    baseline={"output": "hello", "cost_usd": 1.0},
    candidate={"output": "hello", "cost_usd": 1.25},
    mode="full",
    config_path="policy.json",
    metadata={"evaluation_time": "2026-02-15T00:00:00Z"},
)
```

If waivers exist in config but no evaluation time is provided, BreakPoint raises an error and tells you to pass `--now` or `metadata.evaluation_time`.

### Behavior

- Only waivers whose `expires_at` is on or after the evaluation time are active.
- An active waiver that matches a policy result’s reason code suppresses that result (e.g. WARN becomes ALLOW for that policy); the decision can change from WARN to ALLOW.
- Applied waivers are listed in the decision payload under `metadata.waivers_applied` (reason_code, expires_at, etc.) for audit.

## Output Contract Policy

When the baseline `output` is valid JSON, Full mode can enforce that the candidate is also valid JSON and, optionally, that it has the same keys and value types.

Config (defaults):

- `output_contract_policy.enabled`: `true`
- `block_on_invalid_json`: `true` — candidate not valid JSON → BLOCK
- `warn_on_missing_keys`: `true` — candidate JSON missing keys present in baseline → WARN
- `warn_on_type_mismatch`: `true` — same key but different type → WARN

In the terminal this appears as **Response format** (✓ / ⚠ / ✗). No extra input fields are required beyond baseline/candidate `output`.

## Latency Policy

Full mode evaluates latency only when both baseline and candidate have `latency_ms` (or equivalent). Config:

- `min_baseline_latency_ms` — below this, policy may WARN (unreliable %)
- `warn_increase_pct` / `block_increase_pct` — percent increase thresholds
- `warn_delta_ms` / `block_delta_ms` — absolute increase (optional)

In the terminal this appears as **Latency** with a delta percent. Include `latency_ms` in your baseline and candidate JSON for this to apply.

## Custom Pricing (Cost from Tokens + Model)

If you omit `cost_usd` but provide `tokens_in`, `tokens_out` (or `tokens_total`) and `model`, Full mode can compute cost using `model_pricing` in the config.

Example default pricing:

```json
"model_pricing": {
  "gpt-4.1-mini": { "input_per_1k": 0.0004, "output_per_1k": 0.0016 },
  "gpt-4.1": { "input_per_1k": 0.002, "output_per_1k": 0.008 }
}
```

Rates are in USD per 1k tokens. Add your own model keys and rates in your config; they are merged with built-in defaults when you use `--config`.

## Strict Mode

In config: `"strict_mode": { "enabled": true }`. When enabled, any WARN is promoted to BLOCK. You can also use the CLI flag `--strict` for a one-shot strict run (same effect for that run).

## Input JSON Format (Same as Lite)

Full mode uses the same input schema as Lite:

- At least `output` (string) per record.
- Optional: `cost_usd`, `tokens_in`, `tokens_out`, `tokens_total`, `latency_ms`, `model`.

Either two files (baseline + candidate) or one combined file with `baseline` and `candidate` keys.

## Exit Codes and CI

Same as Lite: `0` = ALLOW, `1` = WARN, `2` = BLOCK. Use `--fail-on warn` or `--fail-on block` and `--json` for CI.

Full mode in CI example:

```bash
breakpoint evaluate baseline.json candidate.json --mode full --config policy.json --env prod --json --fail-on warn
```

Set `BREAKPOINT_BASELINE`, `BREAKPOINT_CANDIDATE`, `BREAKPOINT_FAIL_ON`, and optionally `--config` / `--env` in your workflow. If you use waivers, pass `--now` (e.g. from a build timestamp) so waiver expiry is correct.

## Common Workflows

**Evaluate with a preset (no custom config):**

```bash
breakpoint evaluate baseline.json candidate.json --mode full --preset extraction --json
```

**Evaluate with custom config and environment:**

```bash
breakpoint evaluate baseline.json candidate.json --mode full --config policy.json --env dev --json
```

**Evaluate with waivers (suppress a known WARN):**

```bash
breakpoint evaluate baseline.json candidate.json --mode full --config policy.json --now 2026-02-15T00:00:00Z --json
```

**Inspect what will be used:**

```bash
breakpoint config print --config policy.json --env prod
breakpoint config presets
```

## Troubleshooting

- **`--accept-risk` / `--config` / `--preset` / `--env` / `--now` not allowed**  
  You're in Lite mode. Add `--mode full`.

- **Config validation error: waivers**  
  When config has `waivers`, you must pass `--now` (CLI) or `metadata.evaluation_time` (API). Waiver entries must include `reason_code`, `expires_at`, `reason`, `issued_by`, `ticket`.

- **Config environment error**  
  The value of `--env` must exist under `environments` in your config JSON.

- **Unexpected WARN (cost or latency)**  
  Add `cost_usd` and/or `latency_ms` (and token counts + `model` if you rely on custom pricing) to both baseline and candidate so policies have enough data.

- **Output contract not firing**  
  Output contract applies only when the baseline `output` is valid JSON. If baseline is plain text, the policy does not enforce JSON on the candidate.

## Next Docs

- Main user guide (Lite + overview): `docs/user-guide.md`
- Presets detail: `docs/policy-presets.md`
- CI templates: `docs/ci-templates.md`
- Real use cases: `docs/use-case-real.md`
