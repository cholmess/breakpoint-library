import argparse
import json
import os
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
    "output_contract_invalid_json_count",
    "output_contract_missing_keys_count",
    "output_contract_type_mismatch_count",
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
    "output_contract_invalid_json_count": "Output contract invalid JSON count",
    "output_contract_missing_keys_count": "Output contract missing keys count",
    "output_contract_type_mismatch_count": "Output contract type mismatch count",
    "similarity": "Similarity",
}

_POLICY_DISPLAY_ORDER = ["pii", "output_contract", "cost", "latency", "drift"]
_POLICY_LABELS = {
    "pii": "No PII detected",
    "output_contract": "Response format",
    "cost": "Cost",
    "latency": "Latency",
    "drift": "Output drift",
}
_SECTION_DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


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
    evaluate_parser.add_argument(
        "--mode",
        choices=["lite", "full"],
        default="lite",
        help="Execution mode: lite (default) or full.",
    )
    evaluate_parser.add_argument("--strict", action="store_true", help="Promote WARN to BLOCK.")
    evaluate_parser.add_argument(
        "--accept-risk",
        action="append",
        choices=["cost", "pii", "drift"],
        default=[],
        help="Lite mode only. Explicitly accept a named risk for this run (repeatable).",
    )
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
    evaluate_parser.add_argument(
        "--project-key",
        help="Optional project identifier to include in decision metadata (for KPI summaries).",
    )
    evaluate_parser.add_argument(
        "--run-id",
        help="Optional run identifier to include in decision metadata (for joining external analytics).",
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
    metrics_summarize_parser.add_argument(
        "--installs",
        help="Optional JSON snapshot file with install counts by source (for KPI summaries).",
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
        _validate_evaluate_mode_flags(args)
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
            mode=args.mode,
            config_path=args.config,
            config_environment=args.env,
            metadata=_evaluation_metadata(args),
            preset=args.preset,
            accepted_risks=list(args.accept_risk),
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

    exit_code = _result_exit_code(
        status=decision.status,
        exit_codes_enabled=args.exit_codes,
        fail_on=args.fail_on,
    )
    _print_text_decision(
        decision, 
        exit_code=exit_code, 
        mode=args.mode, 
        accepted_risks=list(args.accept_risk),
        baseline_data=baseline_data,
        candidate_data=candidate_data
    )
    return exit_code


def _validate_evaluate_mode_flags(args: argparse.Namespace) -> None:
    mode = args.mode
    if mode == "full" and args.accept_risk:
        raise ValueError("--accept-risk is only available in --mode lite.")
    if mode == "lite":
        full_only_flags = []
        if args.config:
            full_only_flags.append("--config")
        if args.preset:
            full_only_flags.append("--preset")
        if args.env:
            full_only_flags.append("--env")
        if args.now:
            full_only_flags.append("--now")
        if full_only_flags:
            raise ValueError(
                f"{', '.join(full_only_flags)} require --mode full. "
                "Lite mode allows one-shot CLI overrides via --accept-risk only."
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
        summary = summarize_decisions(list(args.paths), installs_path=args.installs)
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
    print("MODE_COUNTS:")
    for key in sorted(payload["mode_counts"].keys()):
        print(f"- {key}: {payload['mode_counts'][key]}")
    print(f"OVERRIDE_DECISION_TOTAL: {payload['override_decision_total']}")
    print("OVERRIDE_RISK_COUNTS:")
    for key in sorted(payload["override_risk_counts"].keys()):
        print(f"- {key}: {payload['override_risk_counts'][key]}")
    print(f"CI_DECISION_TOTAL: {payload['ci_decision_total']}")
    print(f"UNIQUE_PROJECT_TOTAL: {payload['unique_project_total']}")
    print(f"REPEAT_PROJECT_TOTAL: {payload['repeat_project_total']}")
    print(f"INSTALLS_TOTAL: {payload['installs_total']}")
    print("INSTALLS_BY_SOURCE:")
    for key in sorted(payload["installs_by_source"].keys()):
        print(f"- {key}: {payload['installs_by_source'][key]}")
    return 0


def _evaluation_metadata(args: argparse.Namespace) -> dict | None:
    payload: dict[str, object] = {}
    if args.now:
        payload["evaluation_time"] = args.now
    if args.project_key:
        payload["project_key"] = args.project_key
    if args.run_id:
        payload["run_id"] = args.run_id
    if _is_ci_environment():
        payload["ci"] = True
    return payload or None


def _is_ci_environment() -> bool:
    ci = str(os.environ.get("CI", "")).strip().lower()
    gha = str(os.environ.get("GITHUB_ACTIONS", "")).strip().lower()
    return ci in {"1", "true", "yes"} or gha in {"1", "true", "yes"}


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


def _print_text_decision(
    decision, 
    exit_code: int, 
    mode: str, 
    accepted_risks: list[str],
    baseline_data: dict | None = None,
    candidate_data: dict | None = None
) -> None:
    print(_SECTION_DIVIDER)
    print("BreakPoint Evaluation")
    print(_SECTION_DIVIDER)
    print()
    print(f"Mode: {mode}")
    print()
    if mode == "lite" and accepted_risks:
        accepted = ", ".join(sorted(set(accepted_risks)))
        print(f"Accepted Risk Override (one-shot): {accepted}")
        print()
    
    # Input Comparison Section
    if baseline_data and candidate_data:
        print("Input Comparison:")
        _print_comparison(baseline_data, candidate_data)
        print()
    
    print(f"Final Decision: {decision.status}")
    print()
    print("Policy Results:")
    policy_statuses = _policy_status_by_reason_code(decision.reason_codes)
    for policy in _POLICY_DISPLAY_ORDER:
        status = policy_statuses.get(policy, "ALLOW")
        detail = _policy_detail_enhanced(
            policy, 
            status, 
            decision.metrics, 
            decision.details,
            baseline_data,
            candidate_data
        )
        # Add color indicator and threshold info inline
        color_indicator = _get_color_indicator(status)
        threshold_info = _get_threshold_info(policy, status, decision.metrics, baseline_data, candidate_data)
        detail_with_threshold = f"{detail}{threshold_info}" if threshold_info else detail
        print(f"{color_indicator} {_status_symbol(status)} {_policy_label(policy)}: {detail_with_threshold}")
    print()
    
    # Detailed Metrics Section
    if decision.metrics:
        print("Detailed Metrics:")
        for key in _METRIC_DISPLAY_ORDER:
            value = decision.metrics.get(key)
            if isinstance(value, (int, float)):
                label = _METRIC_LABELS.get(key, key)
                formatted = _format_metric_value(key, float(value))
                print(f"  {label}: {formatted}")
        print()
    
    print("Summary:")
    if decision.reasons:
        if decision.status.upper() == "BLOCK":
            block_reasons = _reasons_with_severity(decision.reasons, decision.reason_codes, "BLOCK")
            if block_reasons:
                for reason in block_reasons:
                    print(f"- {reason}")
                non_block_count = len(decision.reasons) - len(block_reasons)
                if non_block_count > 0:
                    print(f"{non_block_count} additional non-blocking signal(s) detected.")
            else:
                print(decision.reasons[0])
                if len(decision.reasons) > 1:
                    print(f"{len(decision.reasons) - 1} additional signal(s) detected.")
        else:
            print(decision.reasons[0])
            if len(decision.reasons) > 1:
                print(f"{len(decision.reasons) - 1} additional signal(s) detected.")
    else:
        print("No risky deltas detected against configured policies.")
    print()
    
    # Reason Codes Section
    if decision.reason_codes:
        print("Reason Codes:")
        for code in decision.reason_codes:
            print(f"  - {code}")
        print()
    
    print(f"Exit Code: {exit_code}")
    print(_SECTION_DIVIDER)


def _status_symbol(status: str) -> str:
    normalized = status.upper()
    if normalized == "BLOCK":
        return "✗"
    if normalized == "WARN":
        return "⚠"
    return "✓"


def _policy_label(policy: str) -> str:
    return _POLICY_LABELS.get(policy, policy)


def _policy_status_by_reason_code(reason_codes: list[str]) -> dict[str, str]:
    statuses = {policy: "ALLOW" for policy in _POLICY_DISPLAY_ORDER}
    for code in reason_codes:
        policy = _policy_from_reason_code(code)
        if policy is None:
            continue
        severity = _severity_from_reason_code(code)
        current = statuses.get(policy, "ALLOW")
        if severity == "BLOCK":
            statuses[policy] = "BLOCK"
        elif severity == "WARN" and current == "ALLOW":
            statuses[policy] = "WARN"
    return statuses


def _policy_from_reason_code(code: str) -> str | None:
    if code.startswith("PII_"):
        return "pii"
    if code.startswith("OUTPUT_CONTRACT_"):
        return "output_contract"
    if code.startswith("COST_"):
        return "cost"
    if code.startswith("LATENCY_"):
        return "latency"
    if code.startswith("DRIFT_"):
        return "drift"
    return None


def _severity_from_reason_code(code: str) -> str:
    if code.endswith("_BLOCK"):
        return "BLOCK"
    if code.endswith("_WARN"):
        return "WARN"
    return "ALLOW"


def _reasons_with_severity(reasons: list[str], reason_codes: list[str], severity: str) -> list[str]:
    matching: list[str] = []
    for index, reason in enumerate(reasons):
        code = reason_codes[index] if index < len(reason_codes) else ""
        if _severity_from_reason_code(code) == severity:
            matching.append(reason)
    return matching


def _get_color_indicator(status: str) -> str:
    """Get color indicator for status."""
    normalized = status.upper()
    if normalized == "BLOCK":
        return "🔴"
    elif normalized == "WARN":
        return "🟡"
    return "🟢"


def _get_threshold_info(policy: str, status: str, metrics: dict, baseline_data: dict | None, candidate_data: dict | None) -> str:
    """Get threshold information to append to policy detail."""
    if status.upper() == "ALLOW" or not baseline_data or not candidate_data:
        return ""
    
    threshold_info = ""
    
    if policy == "cost":
        baseline_cost = baseline_data.get("cost_usd")
        candidate_cost = candidate_data.get("cost_usd")
        if isinstance(baseline_cost, (int, float)) and isinstance(candidate_cost, (int, float)) and candidate_cost > baseline_cost:
            increase = ((candidate_cost - baseline_cost) / baseline_cost) * 100
            epsilon = 0.01
            if increase + epsilon >= 40:
                threshold_info = " [🔴 BLOCK threshold exceeded]"
            elif increase + epsilon >= 20:
                threshold_info = " [🟡 WARN threshold exceeded]"
    
    elif policy == "drift":
        baseline_output = str(baseline_data.get("output", ""))
        candidate_output = str(candidate_data.get("output", ""))
        baseline_len = len(baseline_output)
        candidate_len = len(candidate_output)
        if baseline_len > 0:
            delta_pct = abs(candidate_len - baseline_len) / baseline_len * 100
            if delta_pct >= 70:
                threshold_info = " [🔴 BLOCK threshold exceeded]"
            elif delta_pct >= 35:
                threshold_info = " [🟡 WARN threshold exceeded]"
    
    return threshold_info


def _print_comparison(baseline: dict, candidate: dict) -> None:
    """Print detailed comparison between baseline and candidate."""
    baseline_output = baseline.get("output", "")
    candidate_output = candidate.get("output", "")
    baseline_len = len(str(baseline_output))
    candidate_len = len(str(candidate_output))
    
    print(f"  Output Length: {baseline_len} chars → {candidate_len} chars")
    
    baseline_cost = baseline.get("cost_usd")
    candidate_cost = candidate.get("cost_usd")
    if isinstance(baseline_cost, (int, float)) and isinstance(candidate_cost, (int, float)):
        print(f"  Cost: ${baseline_cost:.4f} → ${candidate_cost:.4f}")
    
    baseline_tokens_in = baseline.get("tokens_in")
    candidate_tokens_in = candidate.get("tokens_in")
    baseline_tokens_out = baseline.get("tokens_out")
    candidate_tokens_out = candidate.get("tokens_out")
    if isinstance(baseline_tokens_in, (int, float)) and isinstance(candidate_tokens_in, (int, float)):
        print(f"  Tokens In: {int(baseline_tokens_in)} → {int(candidate_tokens_in)}")
    if isinstance(baseline_tokens_out, (int, float)) and isinstance(candidate_tokens_out, (int, float)):
        print(f"  Tokens Out: {int(baseline_tokens_out)} → {int(candidate_tokens_out)}")
    
    baseline_latency = baseline.get("latency_ms")
    candidate_latency = candidate.get("latency_ms")
    if isinstance(baseline_latency, (int, float)) and isinstance(candidate_latency, (int, float)):
        print(f"  Latency: {int(baseline_latency)}ms → {int(candidate_latency)}ms")
    
    baseline_model = baseline.get("model")
    candidate_model = candidate.get("model")
    if baseline_model or candidate_model:
        print(f"  Model: {baseline_model or 'N/A'} → {candidate_model or 'N/A'}")


def _policy_detail_enhanced(
    policy: str, 
    status: str, 
    metrics: dict,
    details: dict,
    baseline_data: dict | None,
    candidate_data: dict | None
) -> str:
    """Enhanced policy detail with more information."""
    # Start with base detail
    base_detail = _policy_detail(policy, status, metrics)
    
    # Add additional context based on policy
    if policy == "cost" and baseline_data and candidate_data:
        baseline_cost = baseline_data.get("cost_usd")
        candidate_cost = candidate_data.get("cost_usd")
        if isinstance(baseline_cost, (int, float)) and isinstance(candidate_cost, (int, float)):
            delta = candidate_cost - baseline_cost
            if abs(delta) > 0.0001:
                sign = "+" if delta > 0 else ""
                base_detail += f" (${baseline_cost:.4f} → ${candidate_cost:.4f}, {sign}${delta:.4f})"
    
    if policy == "drift" and baseline_data and candidate_data:
        baseline_output = str(baseline_data.get("output", ""))
        candidate_output = str(candidate_data.get("output", ""))
        baseline_len = len(baseline_output)
        candidate_len = len(candidate_output)
        if baseline_len > 0:
            base_detail += f" ({baseline_len} → {candidate_len} chars)"
    
    if policy == "pii" and details.get("pii"):
        pii_details = details["pii"]
        type_counts = pii_details.get("blocked_type_counts", {})
        if type_counts:
            types = ", ".join([f"{k}({v})" for k, v in sorted(type_counts.items())])
            base_detail += f" [Types: {types}]"
    
    if policy == "latency" and baseline_data and candidate_data:
        baseline_latency = baseline_data.get("latency_ms")
        candidate_latency = candidate_data.get("latency_ms")
        if isinstance(baseline_latency, (int, float)) and isinstance(candidate_latency, (int, float)):
            delta = candidate_latency - baseline_latency
            if abs(delta) > 0.1:
                sign = "+" if delta > 0 else ""
                base_detail += f" ({int(baseline_latency)}ms → {int(candidate_latency)}ms, {sign}{int(delta)}ms)"
    
    return base_detail


def _policy_detail(policy: str, status: str, metrics: dict) -> str:
    if policy == "pii":
        blocked_total = metrics.get("pii_blocked_total")
        if isinstance(blocked_total, (int, float)) and blocked_total > 0:
            return f"Detected {int(blocked_total)} match(es)."
        return "No matches."

    if policy == "output_contract":
        invalid_count = metrics.get("output_contract_invalid_json_count")
        missing_count = metrics.get("output_contract_missing_keys_count")
        mismatch_count = metrics.get("output_contract_type_mismatch_count")
        if isinstance(invalid_count, (int, float)) and invalid_count > 0:
            return f"Invalid JSON detected ({int(invalid_count)})."
        if (isinstance(missing_count, (int, float)) and missing_count > 0) or (
            isinstance(mismatch_count, (int, float)) and mismatch_count > 0
        ):
            missing_value = int(missing_count) if isinstance(missing_count, (int, float)) else 0
            mismatch_value = int(mismatch_count) if isinstance(mismatch_count, (int, float)) else 0
            return f"Format drift detected (missing keys: {missing_value}, type mismatches: {mismatch_value})."
        return "No schema drift detected."

    if policy == "cost":
        value = metrics.get("cost_delta_pct")
        if isinstance(value, (int, float)):
            return f"Delta {_format_metric_value('cost_delta_pct', float(value))}."
        return _fallback_detail(status)

    if policy == "latency":
        value = metrics.get("latency_delta_pct")
        if isinstance(value, (int, float)):
            return f"Delta {_format_metric_value('latency_delta_pct', float(value))}."
        return _fallback_detail(status)

    if policy == "drift":
        length_delta = metrics.get("length_delta_pct")
        if isinstance(length_delta, (int, float)):
            similarity = metrics.get("similarity")
            if isinstance(similarity, (int, float)):
                return (
                    f"Length delta {_format_metric_value('length_delta_pct', float(length_delta))}, "
                    f"similarity {_format_metric_value('similarity', float(similarity))}."
                )
            return f"Length delta {_format_metric_value('length_delta_pct', float(length_delta))}."
        if status.upper() == "ALLOW":
            return _fallback_detail(status)
        short_ratio = metrics.get("short_ratio")
        if isinstance(short_ratio, (int, float)):
            return f"Compression ratio {_format_metric_value('short_ratio', float(short_ratio))}."
        similarity = metrics.get("similarity")
        if isinstance(similarity, (int, float)):
            return f"Similarity {_format_metric_value('similarity', float(similarity))}."
        return _fallback_detail(status)

    return _fallback_detail(status)


def _fallback_detail(status: str) -> str:
    normalized = status.upper()
    if normalized == "BLOCK":
        return "Policy violation detected."
    if normalized == "WARN":
        return "Risky delta detected."
    return "No issues."


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
