import json
import subprocess
import sys


def test_cli_evaluate_json_output(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.0}), encoding="utf-8")
    candidate_path.write_text(json.dumps({"output": "hello world", "cost_usd": 1.25}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "breakpoint.cli.main",
            "evaluate",
            str(baseline_path),
            str(candidate_path),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.0.0"
    assert payload["status"] == "WARN"
    assert "COST_INCREASE_WARN" in payload["reason_codes"]


def test_cli_strict_blocks(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.0}), encoding="utf-8")
    candidate_path.write_text(json.dumps({"output": "hello world", "cost_usd": 1.25}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "breakpoint.cli.main",
            "evaluate",
            str(baseline_path),
            str(candidate_path),
            "--strict",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "STATUS: BLOCK" in result.stdout


def test_cli_exit_codes_enabled(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.0}), encoding="utf-8")
    candidate_path.write_text(json.dumps({"output": "hello world", "cost_usd": 1.25}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "breakpoint.cli.main",
            "evaluate",
            str(baseline_path),
            str(candidate_path),
            "--exit-codes",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_cli_combined_input_single_file(tmp_path):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(
        json.dumps(
            {
                "baseline": {"output": "hello", "cost_usd": 1.0},
                "candidate": {"output": "hello world", "cost_usd": 1.25},
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "breakpoint.cli.main", "evaluate", str(payload_path), "--exit-codes"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_cli_stdin_input(tmp_path):
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps({"output": "hello world", "cost_usd": 1.25}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "breakpoint.cli.main",
            "evaluate",
            "-",
            str(candidate_path),
            "--exit-codes",
            "--json",
        ],
        input=json.dumps({"output": "hello", "cost_usd": 1.0}),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "WARN"
    assert "reason_codes" in payload


def test_cli_json_validation_error_contract(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps({"output": "hello"}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "breakpoint.cli.main",
            "evaluate",
            str(baseline_path),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.0.0"
    assert payload["status"] == "BLOCK"
    assert payload["reason_codes"] == ["INPUT_VALIDATION_ERROR"]


def test_cli_fail_on_block_does_not_fail_warn(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.0}), encoding="utf-8")
    candidate_path.write_text(json.dumps({"output": "hello world", "cost_usd": 1.25}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "breakpoint.cli.main",
            "evaluate",
            str(baseline_path),
            str(candidate_path),
            "--fail-on",
            "block",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_fail_on_block_fails_block(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.0}), encoding="utf-8")
    candidate_path.write_text(
        json.dumps({"output": "contact me at hi@example.com", "cost_usd": 1.0}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "breakpoint.cli.main",
            "evaluate",
            str(baseline_path),
            str(candidate_path),
            "--fail-on",
            "block",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2


def test_cli_fail_on_warn_fails_warn(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.0}), encoding="utf-8")
    candidate_path.write_text(json.dumps({"output": "hello world", "cost_usd": 1.25}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "breakpoint.cli.main",
            "evaluate",
            str(baseline_path),
            str(candidate_path),
            "--fail-on",
            "warn",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_cli_config_print_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "breakpoint.cli.main", "config", "print", "--compact"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "cost_policy" in payload
    assert "latency_policy" in payload


def test_cli_env_override_changes_result(tmp_path):
    config_path = tmp_path / "policy.json"
    config_path.write_text(
        json.dumps(
            {
                "environments": {
                    "dev": {"cost_policy": {"warn_increase_pct": 5, "block_increase_pct": 10}},
                }
            }
        ),
        encoding="utf-8",
    )

    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.0}), encoding="utf-8")
    candidate_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.08}), encoding="utf-8")

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
            "--env",
            "dev",
            "--json",
            "--fail-on",
            "warn",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "WARN"
    assert "COST_INCREASE_WARN" in payload["reason_codes"]


def test_cli_config_print_with_env_applies_overrides(tmp_path):
    config_path = tmp_path / "policy.json"
    config_path.write_text(
        json.dumps(
            {
                "cost_policy": {"warn_increase_pct": 20, "block_increase_pct": 35},
                "environments": {
                    "dev": {"cost_policy": {"warn_increase_pct": 5, "block_increase_pct": 10}},
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
            "config",
            "print",
            "--config",
            str(config_path),
            "--env",
            "dev",
            "--compact",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["cost_policy"]["warn_increase_pct"] == 5
    assert "environments" not in payload
