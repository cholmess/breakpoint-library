# Value Metrics (P1-2)

BreakPoint is most useful when you can quantify outcomes, not just usage.

## What to Track

Core pipeline metrics:

- `warn_rate`: WARN / total
- `block_rate`: BLOCK / total
- `top_reason_codes`: which rules fire most often
- `waiver_rate`: waivers applied / total
- `mode_mix`: lite vs full usage counts
- `override_rate`: decisions with explicit `accepted_risks` / total
- `override_risk_mix`: accepted risk types (`cost`, `pii`, `drift`)
- `ci_decision_rate`: decisions tagged as CI / total
- `repeat_project_rate`: projects with >=2 decisions / unique projects

Outcome metrics (requires human/system feedback):

- `false_positive_rate`: fraction of WARN/BLOCK later judged safe
- `true_positive_rate`: fraction of BLOCK that prevented a bad deploy

## Default Thresholds (2026-02-15)

Current defaults are calibrated for early signal while keeping `BLOCK` conservative:

- Cost:
  - `warn_increase_pct`: `20`
  - `block_increase_pct`: `40`
  - `warn_delta_usd`: `0.0`
  - `block_delta_usd`: `0.0`
- Drift:
  - `warn_length_delta_pct`: `35`
  - `block_length_delta_pct`: `70`
  - `warn_short_ratio`: `0.30`
- PII:
  - first detection (email/phone/credit card) => `BLOCK`
- Full mode only:
  - latency policy
  - output contract policy
  - waivers/presets/config strict mode

Rationale:
- `WARN` should appear earlier for meaningful regressions.
- `BLOCK` remains reserved for clear risk or policy violations.
- Presets and project configs can tighten drift or add absolute deltas for stricter workflows.

## Store Decision Artifacts

In CI, always save the decision JSON artifact (example: `breakpoint-decision.json`).

GitHub Actions template:
- `examples/ci/github-actions-breakpoint.yml`

## Summarize Metrics Locally or In CI

Summarize one file:

```bash
breakpoint metrics summarize breakpoint-decision.json
```

Summarize a directory of decision artifacts (recursive scan of `*.json`):

```bash
breakpoint metrics summarize ./artifacts --json
```

Notes:

- Summary reads BreakPoint decision JSON (contract fields `schema_version`, `status`, `reasons`, `reason_codes`).
- If `metadata.waivers_applied` exists, it is counted as waiver usage.
- JSON output fields include:
  - `total`, `by_schema_version`, `by_status`
  - `reason_code_counts`, `waivers_applied_total`, `waived_reason_code_counts`
  - `mode_counts`, `override_decision_total`, `override_risk_counts`
  - `ci_decision_total`, `unique_project_total`, `repeat_project_total`

To enrich KPI summaries at decision time:

```bash
breakpoint evaluate baseline.json candidate.json --json --project-key my-repo --run-id build-123
```

`ci` metadata is auto-tagged when `CI=true` or `GITHUB_ACTIONS=true`.

## Install Snapshot Ingestion (Phase 6)

You can merge install proxies into the same summary by passing `--installs`:

```bash
breakpoint metrics summarize ./artifacts --installs installs_snapshot.json --json
```

Snapshot format:

```json
{
  "sources": {
    "pypi_downloads": 1200,
    "github_clones": 250,
    "github_watchers": 30
  }
}
```

Output adds:
- `installs_total`
- `installs_by_source`

## Joining To Feedback (Optional)

For outcome metrics like false-positive rate, you need a stable join key.

BreakPoint decisions can be joined by:

- the build/run identifier you store alongside the artifact, or
- a stable hash of the decision JSON.

Python helper:

```python
from breakpoint.engine.metrics import decision_fingerprint

fingerprint = decision_fingerprint(decision.to_dict())
```
