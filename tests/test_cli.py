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
    assert "VERDICT: BLOCK" in result.stdout
    assert "TOP_REASONS:" in result.stdout
    assert "KEY_DELTAS:" in result.stdout
    assert "RECOMMENDED_ACTION: Stop deploy and investigate." in result.stdout


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
    assert lines[0] == "VERDICT: BLOCK"
    assert lines[1] == "TOP_REASONS:"
    assert "KEY_DELTAS:" in lines
    assert "RECOMMENDED_ACTION: Stop deploy and investigate." in lines

    key_deltas_index = lines.index("KEY_DELTAS:")
    deltas = []
    for line in lines[key_deltas_index + 1 :]:
        if line.startswith("RECOMMENDED_ACTION:"):
            break
        if line.startswith("- "):
            deltas.append(line)
    assert deltas == [
        "- Cost delta %: +40.00%",
        "- Cost delta USD: +0.400000",
        "- Latency delta %: +60.00%",
        "- Latency delta ms: +60.00",
        "- Length delta %: +81.82%",
        "- Similarity: 0.666667",
    ]


def test_cli_text_output_matches_allow_golden():
    result = _run_evaluate_text(
        "examples/quickstart/baseline.json",
        "examples/quickstart/candidate_allow.json",
    )
    assert result.returncode == 0
    assert result.stdout == _read_golden("allow.txt")


def test_cli_text_output_matches_warn_golden():
    result = _run_evaluate_text(
        "examples/quickstart/baseline.json",
        "examples/quickstart/candidate_warn.json",
    )
    assert result.returncode == 0
    assert result.stdout == _read_golden("warn.txt")


def test_cli_text_output_matches_block_golden():
    result = _run_evaluate_text(
        "examples/install_worthy/baseline.json",
        "examples/install_worthy/candidate_format_regression.json",
    )
    assert result.returncode == 0
    assert result.stdout == _read_golden("block.txt")


def test_cli_recommended_action_by_status():
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
    )

    assert "RECOMMENDED_ACTION: Safe to ship." in allow_result.stdout
    assert "RECOMMENDED_ACTION: Ship with review." in warn_result.stdout
    assert "RECOMMENDED_ACTION: Stop deploy and investigate." in block_result.stdout


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
    assert "VERDICT: BLOCK" in result.stdout
    assert "KEY_DELTAS:" in result.stdout
    assert "- PII blocked total: 2" in result.stdout
    assert "- PII blocked type count: 1" in result.stdout


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
