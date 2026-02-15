import json
import subprocess
import sys

from breakpoint.engine.metrics import summarize_decisions


def test_summarize_decisions_counts_status_and_reason_codes(tmp_path):
    d1 = tmp_path / "d1.json"
    d2 = tmp_path / "d2.json"

    d1.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "status": "WARN",
                "reasons": ["Cost increased"],
                "reason_codes": ["COST_INCREASE_WARN"],
                "metadata": {
                    "mode": "lite",
                    "accepted_risks": ["cost"],
                    "project_key": "proj-a",
                    "ci": True,
                    "waivers_applied": [
                        {
                            "reason_code": "COST_INCREASE_WARN",
                            "expires_at": "2026-12-31T00:00:00Z",
                            "reason": "Temporary suppression",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    d2.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "status": "ALLOW",
                "reasons": [],
                "reason_codes": [],
                "metadata": {"mode": "full", "project_key": "proj-a"},
            }
        ),
        encoding="utf-8",
    )

    summary = summarize_decisions([str(tmp_path)])
    payload = summary.to_dict()
    assert payload["total"] == 2
    assert payload["by_status"]["ALLOW"] == 1
    assert payload["by_status"]["WARN"] == 1
    assert payload["reason_code_counts"]["COST_INCREASE_WARN"] == 1
    assert payload["waivers_applied_total"] == 1
    assert payload["waived_reason_code_counts"]["COST_INCREASE_WARN"] == 1
    assert payload["mode_counts"]["lite"] == 1
    assert payload["mode_counts"]["full"] == 1
    assert payload["override_decision_total"] == 1
    assert payload["override_risk_counts"]["cost"] == 1
    assert payload["ci_decision_total"] == 1
    assert payload["unique_project_total"] == 1
    assert payload["repeat_project_total"] == 1


def test_cli_metrics_summarize_json(tmp_path):
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "status": "BLOCK",
                "reasons": ["PII found"],
                "reason_codes": ["PII_EMAIL_BLOCK"],
                "metadata": {"mode": "lite", "project_key": "p-1"},
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
    assert payload["by_status"]["BLOCK"] == 1
    assert payload["reason_code_counts"]["PII_EMAIL_BLOCK"] == 1
    assert payload["mode_counts"]["lite"] == 1
    assert payload["unique_project_total"] == 1
