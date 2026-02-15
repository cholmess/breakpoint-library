import json
import subprocess
import sys


def test_cli_metrics_summarize_json(tmp_path):
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "status": "WARN",
                "reasons": ["x"],
                "reason_codes": ["COST_INCREASE_WARN"],
                "metadata": {
                    "mode": "lite",
                    "accepted_risks": ["cost", "drift"],
                    "project_key": "kpi-proj",
                    "ci": True,
                    "waivers_applied": [{"reason_code": "COST_INCREASE_WARN", "expires_at": "2026-12-31"}],
                },
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "breakpoint.cli.main",
            "metrics",
            "summarize",
            str(decision_path),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["total"] == 1
    assert payload["by_status"]["WARN"] == 1
    assert payload["reason_code_counts"]["COST_INCREASE_WARN"] == 1
    assert payload["waivers_applied_total"] == 1
    assert payload["waived_reason_code_counts"]["COST_INCREASE_WARN"] == 1
    assert payload["mode_counts"]["lite"] == 1
    assert payload["override_decision_total"] == 1
    assert payload["override_risk_counts"]["cost"] == 1
    assert payload["override_risk_counts"]["drift"] == 1
    assert payload["ci_decision_total"] == 1
    assert payload["unique_project_total"] == 1
