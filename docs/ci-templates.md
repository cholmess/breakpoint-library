# CI Templates (P1)

BreakPoint includes two starter CI templates for pipeline gating:

- GitHub Actions: `examples/ci/github-actions-breakpoint.yml`
- Generic shell runner: `examples/ci/run-breakpoint-gate.sh`

## GitHub Actions

Copy `examples/ci/github-actions-breakpoint.yml` into:

`/.github/workflows/breakpoint-gate.yml`

Behavior:

- Installs BreakPoint
- Runs evaluation with `--json --fail-on warn`
- Uploads `breakpoint-decision.json` as a build artifact

Adjust paths and threshold as needed:

- Baseline/candidate input paths in the `breakpoint evaluate` step
- Gate policy with `--fail-on warn|block`

Recommended behavior:
- Keep `continue-on-error: true` on the gate step so artifacts are always uploaded.
- Enforce result in a final step using captured exit code.
- Default to `--fail-on warn` for release branches.

Copy-paste workflow:

```yaml
name: breakpoint-gate

on:
  pull_request:
  push:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    env:
      BREAKPOINT_BASELINE: examples/quickstart/baseline.json
      BREAKPOINT_CANDIDATE: examples/quickstart/candidate_warn.json
      BREAKPOINT_FAIL_ON: warn
      BREAKPOINT_OUTPUT: breakpoint-decision.json
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: |
          python -m pip install --upgrade pip
          pip install .
      - id: gate
        continue-on-error: true
        shell: bash
        run: |
          set +e
          breakpoint evaluate "$BREAKPOINT_BASELINE" "$BREAKPOINT_CANDIDATE" --json --fail-on "$BREAKPOINT_FAIL_ON" > "$BREAKPOINT_OUTPUT"
          code=$?
          echo "exit_code=$code" >> "$GITHUB_OUTPUT"
          exit 0
      - if: always()
        uses: actions/upload-artifact@v4
        with:
          name: breakpoint-decision
          path: ${{ env.BREAKPOINT_OUTPUT }}
      - if: always()
        shell: bash
        run: |
          code="${{ steps.gate.outputs.exit_code }}"
          if [ "$code" -ne 0 ]; then
            exit "$code"
          fi
```

## Generic CI Shell

Use the script in any CI provider that can run shell commands:

```bash
./examples/ci/run-breakpoint-gate.sh
```

Optional environment variables:

- `BREAKPOINT_BASELINE` (default: `examples/quickstart/baseline.json`)
- `BREAKPOINT_CANDIDATE` (default: `examples/quickstart/candidate_warn.json`)
- `BREAKPOINT_FAIL_ON` (default: `warn`)
- `BREAKPOINT_OUTPUT` (default: `breakpoint-decision.json`)

Example with stricter policy:

```bash
BREAKPOINT_CANDIDATE=examples/quickstart/candidate_block.json \
BREAKPOINT_FAIL_ON=block \
./examples/ci/run-breakpoint-gate.sh
```

## Notes

- Exit behavior follows existing contract:
  - `ALLOW` => `0`
  - `WARN` => `1`
  - `BLOCK` => `2`
- `--fail-on warn` treats `WARN` and `BLOCK` as failing outcomes.
- `--fail-on block` allows `WARN` and fails only on `BLOCK`.
- If your pipeline requires explicit artifact retention, archive `breakpoint-decision.json`.
