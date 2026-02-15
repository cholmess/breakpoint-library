import json
import subprocess
import sys

import pytest

from breakpoint import evaluate


def test_waiver_removes_warn_and_records_metadata(tmp_path):
    config_path = tmp_path / "policy.json"
    config_path.write_text(
        json.dumps(
            {
                "waivers": [
                    {
                        "reason_code": "COST_INCREASE_WARN",
                        "expires_at": "2026-12-31T00:00:00Z",
                        "reason": "Known cost variance for dev.",
                        "issued_by": "team-ai",
                        "ticket": "BP-123",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    decision = evaluate(
        baseline={"output": "hello", "cost_usd": 1.0, "latency_ms": 100},
        candidate={"output": "hello", "cost_usd": 1.25, "latency_ms": 100},
        config_path=str(config_path),
        metadata={"evaluation_time": "2026-02-15T00:00:00Z"},
    )

    assert decision.status == "ALLOW"
    assert decision.reason_codes == []
    assert decision.metadata["waivers_applied"][0]["reason_code"] == "COST_INCREASE_WARN"
    assert decision.metadata["waivers_applied"][0]["expires_at"] == "2026-12-31T00:00:00Z"


def test_expired_waiver_does_not_apply(tmp_path):
    config_path = tmp_path / "policy.json"
    config_path.write_text(
        json.dumps(
            {
                "waivers": [
                    {
                        "reason_code": "COST_INCREASE_WARN",
                        "expires_at": "2026-01-01T00:00:00Z",
                        "reason": "Expired waiver.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    decision = evaluate(
        baseline={"output": "hello", "cost_usd": 1.0, "latency_ms": 100},
        candidate={"output": "hello", "cost_usd": 1.25, "latency_ms": 100},
        config_path=str(config_path),
        metadata={"evaluation_time": "2026-02-15T00:00:00Z"},
    )

    assert decision.status == "WARN"
    assert "COST_INCREASE_WARN" in decision.reason_codes


def test_waivers_require_evaluation_time(tmp_path):
    config_path = tmp_path / "policy.json"
    config_path.write_text(
        json.dumps(
            {
                "waivers": [
                    {
                        "reason_code": "COST_INCREASE_WARN",
                        "expires_at": "2026-12-31T00:00:00Z",
                        "reason": "Needs evaluation_time.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="evaluation_time is required"):
        evaluate(
            baseline={"output": "hello", "cost_usd": 1.0, "latency_ms": 100},
            candidate={"output": "hello", "cost_usd": 1.25, "latency_ms": 100},
            config_path=str(config_path),
        )


def test_cli_reports_config_validation_error_for_bad_waivers(tmp_path):
    config_path = tmp_path / "policy.json"
    config_path.write_text(json.dumps({"waivers": {}}), encoding="utf-8")

    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.0}), encoding="utf-8")
    candidate_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.25}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "breakpoint.cli.main",
            "evaluate",
            str(baseline_path),
            str(candidate_path),
            "--config",
            str(config_path),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["reason_codes"] == ["CONFIG_VALIDATION_ERROR"]
