import argparse
import json
import sys

from breakpoint.engine.config import load_config
from breakpoint.engine.evaluator import evaluate


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

    config_parser = subparsers.add_parser("config", help="Inspect BreakPoint configuration.")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)
    config_print_parser = config_subparsers.add_parser("print", help="Print the effective merged config JSON.")
    config_print_parser.add_argument("--config", help="Path to custom JSON config.")
    config_print_parser.add_argument("--env", help="Config environment name (for environments.<name> overrides).")
    config_print_parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON (no indentation).",
    )

    args = parser.parse_args()
    if args.command == "evaluate":
        return _run_evaluate(args)
    if args.command == "config" and args.config_command == "print":
        return _run_config_print(args)
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
        )
    except Exception as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "status": "BLOCK",
                        "reasons": [str(exc)],
                        "reason_codes": ["INPUT_VALIDATION_ERROR"],
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

    print(f"STATUS: {decision.status}")
    for reason in decision.reasons:
        print(f"- {reason}")
    return _result_exit_code(
        status=decision.status,
        exit_codes_enabled=args.exit_codes,
        fail_on=args.fail_on,
    )


def _run_config_print(args: argparse.Namespace) -> int:
    config = load_config(args.config, environment=args.env)
    if args.compact:
        print(json.dumps(config, sort_keys=True))
    else:
        print(json.dumps(config, indent=2, sort_keys=True))
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


if __name__ == "__main__":
    raise SystemExit(main())
