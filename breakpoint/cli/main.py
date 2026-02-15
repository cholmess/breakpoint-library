import argparse
import json
import sys

from breakpoint.engine.errors import ConfigValidationError
from breakpoint.engine.config import available_presets, load_config
from breakpoint.engine.metrics import summarize_decisions
from breakpoint.engine.evaluator import evaluate

_METRIC_DISPLAY_ORDER = [
    "cost_delta_pct",
    "cost_delta_usd",
    "latency_delta_pct",
    "latency_delta_ms",
    "length_delta_pct",
    "short_ratio",
    "pii_blocked_total",
    "pii_blocked_type_count",
    "similarity",
]

_METRIC_LABELS = {
    "cost_delta_pct": "Cost delta %",
    "cost_delta_usd": "Cost delta USD",
    "latency_delta_pct": "Latency delta %",
    "latency_delta_ms": "Latency delta ms",
    "length_delta_pct": "Length delta %",
    "short_ratio": "Short ratio",
    "pii_blocked_total": "PII blocked total",
    "pii_blocked_type_count": "PII blocked type count",
    "similarity": "Similarity",
}


def main() -> int:
    parser = argparse.ArgumentParser(prog="breakpoint")
    subparsers = parser.add_subparsers(dest="command", required=True)

    evaluate_parser = subparsers.add_parser("evaluate", help="Compare baseline and candidate.")
    evaluate_parser.add_argument("baseline_path", help="Path to baseline JSON input.")
    evaluate_parser.add_argument(
        "candidate_path",
        nargs="?",
        default=None,
        help="Path to candidate JSON input. If omitted, baseline_path must contain {baseline:..., candidate:...}.",
    )
    evaluate_parser.add_argument("--strict", action="store_true", help="Promote WARN to BLOCK.")
    evaluate_parser.add_argument("--config", help="Path to custom JSON config.")
    evaluate_parser.add_argument(
        "--preset",
        choices=available_presets(),
        help="Built-in policy preset name (merged before --config).",
    )
    evaluate_parser.add_argument("--env", help="Config environment name (for environments.<name> overrides).")
    evaluate_parser.add_argument("--json", action="store_true", help="Emit JSON decision output.")
    evaluate_parser.add_argument(
        "--exit-codes",
        action="store_true",
        help="Return non-zero exit codes for WARN/BLOCK (useful for CI).",
    )
    evaluate_parser.add_argument(
        "--fail-on",
        choices=["warn", "block"],
        help="Return non-zero based on threshold: warn fails on WARN/BLOCK, block fails only on BLOCK.",
    )
    evaluate_parser.add_argument(
        "--now",
        help="Evaluation time for waiver expiry checks (ISO-8601, e.g. 2026-02-15T00:00:00Z).",
    )

    config_parser = subparsers.add_parser("config", help="Inspect BreakPoint configuration.")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)
    config_print_parser = config_subparsers.add_parser("print", help="Print the effective merged config JSON.")
    config_print_parser.add_argument("--config", help="Path to custom JSON config.")
    config_print_parser.add_argument(
        "--preset",
        choices=available_presets(),
        help="Built-in policy preset name (merged before --config).",
    )
    config_print_parser.add_argument("--env", help="Config environment name (for environments.<name> overrides).")
    config_print_parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON (no indentation).",
    )
    config_subparsers.add_parser("presets", help="List built-in preset names.")

    metrics_parser = subparsers.add_parser("metrics", help="Compute metrics from decision JSON artifacts.")
    metrics_subparsers = metrics_parser.add_subparsers(dest="metrics_command", required=True)
    metrics_summarize_parser = metrics_subparsers.add_parser(
        "summarize", help="Summarize ALLOW/WARN/BLOCK counts and reason codes from decision JSON files."
    )
    metrics_summarize_parser.add_argument(
        "paths",
        nargs="+",
        help="One or more JSON files or directories (directories are scanned recursively for *.json). Use '-' for stdin.",
    )
    metrics_summarize_parser.add_argument("--json", action="store_true", help="Emit summary as JSON.")

    args = parser.parse_args()
    if args.command == "evaluate":
        return _run_evaluate(args)
    if args.command == "config" and args.config_command == "print":
        return _run_config_print(args)
    if args.command == "config" and args.config_command == "presets":
        return _run_config_presets(args)
    if args.command == "metrics" and args.metrics_command == "summarize":
        return _run_metrics_summarize(args)
    return 1


def _run_evaluate(args: argparse.Namespace) -> int:
    try:
        stdin_cache: dict[str, str] = {}
        if args.candidate_path is None:
            payload = _read_json(args.baseline_path, stdin_cache)
            baseline_data, candidate_data = _split_combined_input(payload)
        else:
            baseline_data = _read_json(args.baseline_path, stdin_cache)
            candidate_data = _read_json(args.candidate_path, stdin_cache)

        decision = evaluate(
            baseline=baseline_data,
            candidate=candidate_data,
            strict=args.strict,
            config_path=args.config,
            config_environment=args.env,
            metadata={"evaluation_time": args.now} if args.now else None,
            preset=args.preset,
        )
    except Exception as exc:
        error_code = "CONFIG_VALIDATION_ERROR" if isinstance(exc, ConfigValidationError) else "INPUT_VALIDATION_ERROR"
        if args.json:
            print(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "status": "BLOCK",
                        "reasons": [str(exc)],
                        "reason_codes": [error_code],
                    },
                    indent=2,
                )
            )
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(decision.to_dict(), indent=2))
        return _result_exit_code(
            status=decision.status,
            exit_codes_enabled=args.exit_codes,
            fail_on=args.fail_on,
        )

    _print_text_decision(decision)
    return _result_exit_code(
        status=decision.status,
        exit_codes_enabled=args.exit_codes,
        fail_on=args.fail_on,
    )


def _run_config_print(args: argparse.Namespace) -> int:
    config = load_config(args.config, environment=args.env, preset=args.preset)
    if args.compact:
        print(json.dumps(config, sort_keys=True))
    else:
        print(json.dumps(config, indent=2, sort_keys=True))
    return 0


def _run_config_presets(_args: argparse.Namespace) -> int:
    for name in available_presets():
        print(name)
    return 0


def _run_metrics_summarize(args: argparse.Namespace) -> int:
    try:
        summary = summarize_decisions(list(args.paths))
    except Exception as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
        return 0

    payload = summary.to_dict()
    print(f"TOTAL: {payload['total']}")
    print("STATUS_COUNTS:")
    for key in sorted(payload["by_status"].keys()):
        print(f"- {key}: {payload['by_status'][key]}")
    print("TOP_REASON_CODES:")
    items = sorted(payload["reason_code_counts"].items(), key=lambda kv: (-kv[1], kv[0]))
    for code, count in items[:20]:
        print(f"- {code}: {count}")
    if payload["waivers_applied_total"] > 0:
        print(f"WAIVERS_APPLIED_TOTAL: {payload['waivers_applied_total']}")
        waived = sorted(payload["waived_reason_code_counts"].items(), key=lambda kv: (-kv[1], kv[0]))
        if waived:
            print("TOP_WAIVED_REASON_CODES:")
            for code, count in waived[:20]:
                print(f"- {code}: {count}")
    return 0


def _read_json(path: str, stdin_cache: dict[str, str]) -> dict:
    if path == "-":
        if "stdin" not in stdin_cache:
            stdin_cache["stdin"] = sys.stdin.read()
        return json.loads(stdin_cache["stdin"])
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _split_combined_input(payload: dict) -> tuple[dict, dict]:
    if not isinstance(payload, dict):
        raise ValueError("Combined input must be a JSON object.")
    baseline = payload.get("baseline")
    candidate = payload.get("candidate")
    if not isinstance(baseline, dict) or not isinstance(candidate, dict):
        raise ValueError("Combined input must contain object keys 'baseline' and 'candidate'.")
    return baseline, candidate


def _exit_code(status: str) -> int:
    if status == "ALLOW":
        return 0
    if status == "WARN":
        return 1
    if status == "BLOCK":
        return 2
    return 2


def _result_exit_code(status: str, exit_codes_enabled: bool, fail_on: str | None) -> int:
    threshold = fail_on
    if threshold is None and exit_codes_enabled:
        threshold = "warn"
    if threshold is None:
        return 0

    normalized = status.upper()
    if threshold == "warn":
        return _exit_code(normalized) if normalized in {"WARN", "BLOCK"} else 0
    if threshold == "block":
        return _exit_code(normalized) if normalized == "BLOCK" else 0
    return 0


def _print_text_decision(decision) -> None:
    print(f"VERDICT: {decision.status}")

    print("TOP_REASONS:")
    if decision.reasons:
        for reason in decision.reasons:
            print(f"- {reason}")
    else:
        print("- None")

    print("KEY_DELTAS:")
    delta_lines = _metric_lines(decision.metrics)
    if delta_lines:
        for line in delta_lines:
            print(f"- {line}")
    else:
        print("- None")

    print(f"RECOMMENDED_ACTION: {_recommended_action(decision.status)}")


def _metric_lines(metrics: dict) -> list[str]:
    if not isinstance(metrics, dict):
        return []

    lines: list[str] = []
    for key in _METRIC_DISPLAY_ORDER:
        value = metrics.get(key)
        if not isinstance(value, (int, float)):
            continue
        label = _METRIC_LABELS.get(key, key)
        lines.append(f"{label}: {_format_metric_value(key, float(value))}")
    return lines


def _format_metric_value(key: str, value: float) -> str:
    if key.endswith("_count") or key.endswith("_total"):
        return str(int(value))
    if key.endswith("_pct"):
        return f"{value:+.2f}%"
    if key.endswith("_usd"):
        return f"{value:+.6f}"
    if key.endswith("_ms"):
        return f"{value:+.2f}"
    return f"{value:.6f}"


def _recommended_action(status: str) -> str:
    normalized = status.upper()
    if normalized == "ALLOW":
        return "Safe to ship."
    if normalized == "WARN":
        return "Ship with review."
    if normalized == "BLOCK":
        return "Stop deploy and investigate."
    return "Review result."


if __name__ == "__main__":
    raise SystemExit(main())
