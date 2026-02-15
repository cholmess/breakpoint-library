# BreakPoint v0.2.0-rc2 Release Notes

Date: 2026-02-15
Status: Release Candidate

## Summary

`v0.2.0-rc2` closes the remaining install-worthy gaps from `rc1`.

Highlights:
- Pain-led README opening and stronger value narrative.
- Killer demo scenario aligned to realistic prompt/model changes.
- Infrastructure-style CLI output with policy-level signal and explicit exit code.
- Default policy tuning for earlier WARN signal (`cost +15%`, `latency +25%`) while keeping BLOCK conservative.
- CI template hardened for copy-paste adoption, artifact retention, and deterministic gate enforcement.
- Drift warnings upgraded from abstract text to symptom-specific messages.

## What Changed Since rc1

### 1) README and adoption flow

- Reworked opening to lead with deployment risk and outcome.
- Added direct `ALLOW · WARN · BLOCK` positioning.
- Added CI copy-paste guidance and explicit `--fail-on warn` behavior.

Files:
- `README.md`

### 2) Demo package quality

- Updated killer scenario to represent small prompt change + model upgrade causing large cost/latency and format drift.
- Synced docs and runner labels with this scenario.

Files:
- `examples/install_worthy/candidate_killer_tradeoff.json`
- `docs/install-worthy-examples.md`
- `scripts/run-install-worthy-demo.sh`

### 3) CLI text output UX

- Text mode now renders a consistent evaluation panel:
  - `BreakPoint Evaluation`
  - `Final Decision`
  - `Policy Results` (`✓ / ⚠ / ✗`)
  - `Summary`
  - `Exit Code`
- Kept JSON contract and exit-code behavior stable for CI.

Files:
- `breakpoint/cli/main.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_golden/*.txt`

### 4) Default policy posture

- Cost WARN threshold tightened to `+15%` (BLOCK remains `+35%`).
- Latency WARN threshold tightened to `+25%` (BLOCK remains `+60%`).
- Drift defaults remain tuned for low-noise baselines (`75`, `0.30`, `0.10`).

Files:
- `breakpoint/config/default_policies.json`
- `docs/value-metrics.md`

### 5) CI template hardening

- Added env-driven inputs to workflow for fast copy-paste customization.
- Captures gate exit code, uploads artifact always, enforces result in final step.
- Clarified `--fail-on warn` and `--fail-on block` semantics in docs.

Files:
- `examples/ci/github-actions-breakpoint.yml`
- `docs/ci-templates.md`
- `tests/test_ci_templates.py`

### 6) Drift messaging improvements

- Drift policy now reports concrete symptoms:
  - baseline vs candidate char counts,
  - compression ratio and likely detail loss,
  - low-overlap missing baseline terms.
- CLI drift line now shows measurable symptom text when risk is present.

Files:
- `breakpoint/engine/policies/drift.py`
- `breakpoint/cli/main.py`

## Validation

Automated:

```bash
pytest -q
```

Result on 2026-02-15:
- `54 passed`

Manual demo smoke:

```bash
make demo
```

Result:
- Scenario A: `BLOCK`
- Scenario B: `BLOCK`
- Scenario C: `BLOCK`
- Scenario D: `BLOCK`

## Notes

- This RC is intended for final publish readiness checks.
- Next step after tagging: gather one external fresh-clone feedback pass and then cut stable `v0.2.0`.
