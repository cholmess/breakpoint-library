import json
import subprocess
import sys
from pathlib import Path


CLI_GOLDEN_DIR = Path(__file__).parent / "fixtures" / "cli_golden"


def _run_evaluate_text(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "breakpoint.cli.main",
            "evaluate",
            *args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def _read_golden(name: str) -> str:
    return (CLI_GOLDEN_DIR / name).read_text(encoding="utf-8")


def test_cli_evaluate_json_output(tmp_path):
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
    candidate_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.25}), encoding="utf-8")

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
    assert "Final Decision: BLOCK" in result.stdout
    assert "Policy Results:" in result.stdout
    assert "Summary:" in result.stdout
    assert "Exit Code: 0" in result.stdout


def test_cli_text_output_has_deterministic_summary_order(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(
        json.dumps({"output": "hello world", "cost_usd": 1.0, "latency_ms": 100}),
        encoding="utf-8",
    )
    candidate_path.write_text(
        json.dumps({"output": "hello world expanded", "cost_usd": 1.4, "latency_ms": 160}),
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
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines[0] == "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    assert lines[1] == "BreakPoint Evaluation"
    assert lines[2] == "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    assert "Final Decision: BLOCK" in lines
    assert "Policy Results:" in lines
    policy_results_index = lines.index("Policy Results:")
    assert lines[policy_results_index + 1].startswith("✓ No PII detected:")
    assert lines[policy_results_index + 2].startswith("✓ Response format:")
    assert lines[policy_results_index + 3].startswith("✗ Cost:")
    assert lines[policy_results_index + 4].startswith("✓ Latency:")
    assert lines[policy_results_index + 5].startswith("✗ Output drift:")
    assert lines[-2] == "Exit Code: 0"
    assert lines[-1] == "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


def test_cli_text_output_matches_allow_golden():
    result = _run_evaluate_text(
        "examples/quickstart/baseline.json",
        "examples/quickstart/candidate_allow.json",
        "--mode",
        "full",
    )
    assert result.returncode == 0
    assert result.stdout == _read_golden("allow.txt")


def test_cli_text_output_matches_warn_golden():
    result = _run_evaluate_text(
        "examples/quickstart/baseline.json",
        "examples/quickstart/candidate_warn.json",
        "--mode",
        "full",
    )
    assert result.returncode == 0
    assert result.stdout == _read_golden("warn.txt")


def test_cli_text_output_matches_block_golden():
    result = _run_evaluate_text(
        "examples/install_worthy/baseline.json",
        "examples/install_worthy/candidate_format_regression.json",
        "--mode",
        "full",
    )
    assert result.returncode == 0
    assert result.stdout == _read_golden("block.txt")


def test_cli_empty_candidate_marks_drift_as_block(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(
        json.dumps({"output": "long baseline text", "cost_usd": 1.0, "latency_ms": 100}),
        encoding="utf-8",
    )
    candidate_path.write_text(
        json.dumps({"output": "   ", "cost_usd": 1.0, "latency_ms": 100}),
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
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Final Decision: BLOCK" in result.stdout
    assert "✗ Output drift:" in result.stdout


def test_cli_block_summary_lists_all_blocking_reasons():
    result = _run_evaluate_text(
        "examples/quickstart/baseline.json",
        "examples/quickstart/candidate_block.json",
        "--mode",
        "full",
    )

    assert result.returncode == 0
    assert "- Cost increased by 40.0% (>=40%)." in result.stdout
    assert "- Latency increased by 70.0% (>60%)." in result.stdout
    assert "- PII detected: EMAIL(1). Total matches: 1." in result.stdout
    assert "1 additional non-blocking signal(s) detected." in result.stdout


def test_cli_decision_header_by_status():
    allow_result = _run_evaluate_text(
        "examples/quickstart/baseline.json",
        "examples/quickstart/candidate_allow.json",
    )
    warn_result = _run_evaluate_text(
        "examples/quickstart/baseline.json",
        "examples/quickstart/candidate_warn.json",
    )
    block_result = _run_evaluate_text(
        "examples/install_worthy/baseline.json",
        "examples/install_worthy/candidate_format_regression.json",
        "--mode",
        "full",
    )

    assert "Final Decision: ALLOW" in allow_result.stdout
    assert "Final Decision: WARN" in warn_result.stdout
    assert "Final Decision: BLOCK" in block_result.stdout


def test_cli_text_output_shows_pii_counts(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.0}), encoding="utf-8")
    candidate_path.write_text(
        json.dumps({"output": "contact me at hi@example.com and alt@example.com", "cost_usd": 1.0}),
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
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Final Decision: BLOCK" in result.stdout
    assert "Policy Results:" in result.stdout
    assert "✗ No PII detected: Detected 2 match(es)." in result.stdout


def test_cli_exit_codes_enabled(tmp_path):
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
                "candidate": {"output": "hello", "cost_usd": 1.25},
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
    candidate_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.25}), encoding="utf-8")

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
    candidate_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.25}), encoding="utf-8")

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
    candidate_path.write_text(json.dumps({"output": "hello", "cost_usd": 1.25}), encoding="utf-8")

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


def test_cli_config_presets_lists_names():
    result = subprocess.run(
        [sys.executable, "-m", "breakpoint.cli.main", "config", "presets"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    names = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    assert {"chatbot", "support", "extraction"}.issubset(names)


def test_cli_evaluate_with_preset_works(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(
        json.dumps({"output": "hello", "cost_usd": 1.0, "latency_ms": 100}),
        encoding="utf-8",
    )
    candidate_path.write_text(
        json.dumps({"output": "hello world", "cost_usd": 1.25, "latency_ms": 100}),
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
            "--mode",
            "full",
            "--preset",
            "chatbot",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.0.0"


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
            "--mode",
            "full",
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


def test_cli_lite_rejects_full_only_flags(tmp_path):
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
            "--config",
            "policy.json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "--config require --mode full" in result.stderr


def test_cli_accept_risk_cost_is_one_shot_lite_override(tmp_path):
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
            "--accept-risk",
            "cost",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Accepted Risk Override (one-shot): cost" in result.stdout
    assert "Final Decision: ALLOW" in result.stdout


def test_cli_accept_risk_rejected_in_full_mode(tmp_path):
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
            "--mode",
            "full",
            "--accept-risk",
            "cost",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "--accept-risk is only available in --mode lite" in result.stderr


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
