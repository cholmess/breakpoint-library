# BreakPoint User Guide

This guide explains how to use BreakPoint to evaluate AI output changes and decide whether a release is safe.

## What BreakPoint Does

BreakPoint compares a `baseline` output against a `candidate` output and returns one decision:

- `ALLOW`: safe to ship
- `WARN`: risk detected, review required
- `BLOCK`: do not ship

## Install

From the repository root:

```bash
pip install -e .
```

Verify CLI is available:

```bash
breakpoint --help
```

## Input JSON Format

BreakPoint expects either:

1. Two files: `baseline.json` and `candidate.json`
2. One combined payload file containing both `baseline` and `candidate`

Each record needs at least:

- `output` (string)

Optional metadata used by policies:

- `cost_usd` (number)
- `tokens_total` (number)
- `tokens_in` / `tokens_out` (number)
- `latency_ms` (number)
- `model` (string)

Minimal single-record example:

```json
{
  "output": "Here is your model response."
}
```

Combined payload example:

```json
{
  "baseline": { "output": "Old response", "cost_usd": 0.02 },
  "candidate": { "output": "New response", "cost_usd": 0.03 }
}
```

## Quick Start (2-file mode)

```bash
breakpoint evaluate baseline.json candidate.json
```

Get machine-readable output:

```bash
breakpoint evaluate baseline.json candidate.json --json
```

Fail CI on warnings and blocks:

```bash
breakpoint evaluate baseline.json candidate.json --json --fail-on warn
```

## Understanding Exit Codes

Exit codes are stable:

- `0` => `ALLOW`
- `1` => `WARN`
- `2` => `BLOCK`

Use this for CI gating.

## Lite Mode vs Full Mode

Default mode is `lite` (zero-config):

```bash
breakpoint evaluate baseline.json candidate.json
```

Lite defaults include:

- Cost: `WARN` at `+20%`, `BLOCK` at `+40%`
- PII: `BLOCK` on first detection
- Drift: `WARN` at `+35%`, `BLOCK` at `+70%`
- Empty output: always `BLOCK`

Use `full` mode for advanced governance:

```bash
breakpoint evaluate baseline.json candidate.json --mode full --config policy.json --json
```

Full mode supports:

- Config-driven policies
- Presets/environments
- Waivers
- Output contract policy
- Latency policy
- Custom pricing models

## Common Workflows

Evaluate one combined payload:

```bash
breakpoint evaluate payload.json --json
```

Inspect merged config:

```bash
breakpoint config print --config policy.json --env dev
```

Use example scenarios from this repo:

```bash
breakpoint evaluate examples/quickstart/baseline.json examples/quickstart/candidate_allow.json --json
breakpoint evaluate examples/quickstart/baseline.json examples/quickstart/candidate_warn.json --json --fail-on warn
breakpoint evaluate examples/quickstart/baseline.json examples/quickstart/candidate_block.json --json --fail-on block
```

## CI Integration

Use:

- `examples/ci/github-actions-breakpoint.yml`

Recommended setting:

- `--fail-on warn` for stricter quality gates

If you only want hard failures:

- `--fail-on block`

## Troubleshooting

- `ModuleNotFoundError: breakpoint`
  - Run `pip install -e .` from repo root.
- Unexpected warnings due to missing metrics
  - Add `cost_usd`, token counts, and `latency_ms` to both baseline and candidate.
- Config environment errors
  - Ensure `--env` matches a key under `environments` in your config JSON.
- Validation issues in JSON output
  - Check `reason_codes` to identify the failing policy/input contract.

## Next Docs

- Full mode: `docs/user-guide-full-mode.md` (config, presets, environments, waivers, output contract, latency, custom pricing)
- Quickstart: `docs/quickstart-10min.md`
- Presets: `docs/policy-presets.md`
- CI templates: `docs/ci-templates.md`
- Install-worthy examples: `docs/install-worthy-examples.md`
