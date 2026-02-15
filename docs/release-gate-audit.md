# Release Gate Audit (Install-Worthy v0.x)

Date: 2026-02-15
Decision owner: Christopher Holmes
Audit source: `PLAN.md` hard gate checklist

## Gate Results

1. Demo run shows at least one surprising/useful regression finding
- Result: PASS
- Evidence:
  - `make demo` returns multiple `BLOCK` outcomes with concrete reasons (cost spike, invalid JSON contract break, PII, latency/verbosity drift).
  - Demo runner: `scripts/run-install-worthy-demo.sh`
  - Scenarios: `examples/install_worthy/`

2. CLI output includes quantified deltas (not just generic warnings)
- Result: PASS
- Evidence:
  - Deterministic sections: `VERDICT`, `TOP_REASONS`, `KEY_DELTAS`, `RECOMMENDED_ACTION`
  - Quantified metrics include cost/latency/drift/PII/contract counts in `KEY_DELTAS`
  - CLI implementation: `breakpoint/cli/main.py`
  - Golden snapshots: `tests/fixtures/cli_golden/`

3. JSON contract and exit codes are stable and tested
- Result: PASS
- Evidence:
  - Contract v1 output (`schema_version`, `status`, `reasons`, `reason_codes`, optional metrics/metadata)
  - Exit-code behavior covered in `tests/test_cli.py`
  - Contract behavior covered in `tests/test_evaluate.py`

4. README includes 3 copy-paste examples with expected outcomes
- Result: PASS
- Evidence:
  - `README.md` includes three realistic examples and expected verdicts.
  - Supporting scenario doc: `docs/install-worthy-examples.md`

5. No required configuration for first useful run
- Result: PASS
- Evidence:
  - `make demo` works with defaults and no custom policy file.
  - Baseline + candidate fixtures are bundled in repository.

## Go / No-Go

- Decision: GO
- Rationale: All hard-gate items pass with reproducible local evidence and automated coverage.

## Validation Commands Used

```bash
make demo
pytest -q tests/test_cli.py
pytest -q tests/test_evaluate.py
pytest -q tests/test_install_worthy_examples.py
pytest -q tests/test_quickstart_samples.py
```
