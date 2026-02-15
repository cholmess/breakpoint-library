# v0.2.0-rc2 Fresh-Clone Validation

Date: 2026-02-15

## Goal

Validate first-run behavior from a clean clone context.

## Environment

- Clone path: `/tmp/breakpoint-library-fresh-rc2`
- Command path tested: quickstart WARN scenario

## Attempt 1 (full install path)

Attempted:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

Result:
- Blocked by network-restricted environment while resolving build dependency (`setuptools>=68`).
- This is an environment limitation, not a project-specific packaging failure.

## Attempt 2 (fallback functional check in fresh clone)

Executed directly from clean clone:

```bash
python -m breakpoint.cli.main evaluate \
  examples/quickstart/baseline.json \
  examples/quickstart/candidate_warn.json \
  --json --fail-on warn
```

Observed:
- Status: `WARN`
- Reason codes: `COST_INCREASE_WARN`, `LATENCY_INCREASE_WARN`
- Elapsed runtime: `<1s`

## Conclusion

- Functional fresh-clone evaluation path is verified in this environment.
- Full install-path validation should be repeated once network access is available (or in CI) to complete the external-user installability check.
