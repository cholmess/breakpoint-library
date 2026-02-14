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
    evaluate_parser.add_argument("--json", action="store_true", help="Emit JSON decision output.")
    evaluate_parser.add_argument(
        "--exit-codes",
        action="store_true",
        help="Return non-zero exit codes for WARN/BLOCK (useful for CI).",
    )

    config_parser = subparsers.add_parser("config", help="Inspect BreakPoint configuration.")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)
    config_print_parser = config_subparsers.add_parser("print", help="Print the effective merged config JSON.")
    config_print_parser.add_argument("--config", help="Path to custom JSON config.")
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
    )

    if args.json:
        print(
            json.dumps(
                {
                    "status": decision.status,
                    "reasons": decision.reasons,
                    "codes": decision.codes,
                    "details": decision.details,
                },
                indent=2,
            )
        )
        return _exit_code(decision.status) if args.exit_codes else 0

    print(f"STATUS: {decision.status}")
    for reason in decision.reasons:
        print(f"- {reason}")
    return _exit_code(decision.status) if args.exit_codes else 0


def _run_config_print(args: argparse.Namespace) -> int:
    config = load_config(args.config)
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
        return 2
    if status == "BLOCK":
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
