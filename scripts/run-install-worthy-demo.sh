#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CLI=(python -m breakpoint.cli.main)
BASELINE="examples/install_worthy/baseline.json"

if [[ ! -f "$BASELINE" ]]; then
  echo "ERROR: Missing demo baseline file: $BASELINE" >&2
  echo "Troubleshooting: run this command from the repository root." >&2
  exit 1
fi

echo "BreakPoint Install-Worthy Demo"
echo "Repository: $ROOT_DIR"
echo
echo "Expected outcomes:"
echo "- Scenario A (cost model swap): BLOCK"
echo "- Scenario B (format regression): WARN"
echo "- Scenario C (PII + verbosity): BLOCK"
echo "- Scenario D (killer tradeoff): BLOCK"
echo

run_case() {
  local label="$1"
  local candidate="$2"

  echo "== $label =="
  "${CLI[@]}" evaluate "$BASELINE" "$candidate"
  echo
}

run_case "Scenario A: Cost regression from model swap" "examples/install_worthy/candidate_cost_model_swap.json"
run_case "Scenario B: Structured-output format regression" "examples/install_worthy/candidate_format_regression.json"
run_case "Scenario C: PII + verbosity drift" "examples/install_worthy/candidate_pii_verbosity.json"
run_case "Scenario D: Killer tradeoff" "examples/install_worthy/candidate_killer_tradeoff.json"

echo "Done."
echo "Troubleshooting:"
echo "- If imports fail, run: pip install -e ."
echo "- If files are missing, verify examples/install_worthy exists and rerun from repo root."
echo "- For machine-readable output, append --json to individual evaluate commands."
