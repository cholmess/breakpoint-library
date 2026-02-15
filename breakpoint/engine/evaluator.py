from breakpoint.engine.aggregator import aggregate_policy_results
from breakpoint.engine.config import load_config
from breakpoint.engine.policies.cost import evaluate_cost_policy
from breakpoint.engine.policies.drift import evaluate_drift_policy
from breakpoint.engine.policies.latency import evaluate_latency_policy
from breakpoint.engine.policies.pii import evaluate_pii_policy
from breakpoint.engine.waivers import (
    Waiver,
    apply_waivers_to_policy_results,
    parse_evaluation_time,
    parse_waivers,
)
from breakpoint.models.decision import Decision


def evaluate(
    baseline_output: str | None = None,
    candidate_output: str | None = None,
    metadata: dict | None = None,
    baseline: dict | None = None,
    candidate: dict | None = None,
    strict: bool = False,
    config_path: str | None = None,
    config_environment: str | None = None,
) -> Decision:
    config = load_config(config_path, environment=config_environment)
    metadata_input = metadata or {}
    baseline_record, candidate_record = _normalize_inputs(
        baseline_output=baseline_output,
        candidate_output=candidate_output,
        metadata=metadata_input,
        baseline=baseline,
        candidate=candidate,
    )

    policy_results = [
        evaluate_cost_policy(
            baseline=baseline_record,
            candidate=candidate_record,
            thresholds=config["cost_policy"],
            pricing=config.get("model_pricing", {}),
        ),
        evaluate_latency_policy(
            baseline=baseline_record,
            candidate=candidate_record,
            thresholds=config.get("latency_policy", {}),
        ),
        evaluate_pii_policy(
            candidate=candidate_record,
            patterns=config["pii_policy"]["patterns"],
            allowlist=config["pii_policy"].get("allowlist", []),
        ),
        evaluate_drift_policy(
            baseline=baseline_record,
            candidate=candidate_record,
            thresholds=config["drift_policy"],
        ),
    ]

    waivers = parse_waivers(config.get("waivers"))
    applied_waivers: list[Waiver] = []
    if waivers:
        evaluation_time_raw = metadata_input.get("evaluation_time") or metadata_input.get("now")
        if not isinstance(evaluation_time_raw, str) or not evaluation_time_raw.strip():
            raise ValueError(
                "Waivers are configured, but metadata.evaluation_time is required (ISO-8601). "
                "CLI: pass --now. Python: pass metadata={'evaluation_time': '...'}"
            )
        evaluation_time = parse_evaluation_time(evaluation_time_raw)
        policy_results, applied_waivers = apply_waivers_to_policy_results(
            policy_results, waivers=waivers, evaluation_time=evaluation_time
        )

    aggregated = aggregate_policy_results(policy_results, strict=strict)
    metadata_payload = _decision_metadata(baseline_record, candidate_record, strict, applied_waivers)
    return Decision(
        schema_version=aggregated.schema_version,
        status=aggregated.status,
        reasons=aggregated.reasons,
        reason_codes=aggregated.reason_codes,
        metrics=aggregated.metrics,
        metadata=metadata_payload,
        details=aggregated.details,
    )


def _normalize_inputs(
    baseline_output: str | None,
    candidate_output: str | None,
    metadata: dict,
    baseline: dict | None,
    candidate: dict | None,
) -> tuple[dict, dict]:
    baseline_record = dict(baseline or {})
    candidate_record = dict(candidate or {})

    if "output" not in baseline_record and baseline_output is not None:
        baseline_record["output"] = baseline_output
    if "output" not in candidate_record and candidate_output is not None:
        candidate_record["output"] = candidate_output

    _apply_metadata_overrides(baseline_record, candidate_record, metadata)

    if "output" not in baseline_record:
        raise ValueError("Baseline output is required.")
    if "output" not in candidate_record:
        raise ValueError("Candidate output is required.")

    return baseline_record, candidate_record


def _apply_metadata_overrides(baseline: dict, candidate: dict, metadata: dict) -> None:
    key_map = {
        "baseline_tokens": ("baseline", "tokens_total"),
        "candidate_tokens": ("candidate", "tokens_total"),
        "baseline_tokens_in": ("baseline", "tokens_in"),
        "baseline_tokens_out": ("baseline", "tokens_out"),
        "candidate_tokens_in": ("candidate", "tokens_in"),
        "candidate_tokens_out": ("candidate", "tokens_out"),
        "baseline_model": ("baseline", "model"),
        "candidate_model": ("candidate", "model"),
        "baseline_latency_ms": ("baseline", "latency_ms"),
        "candidate_latency_ms": ("candidate", "latency_ms"),
        "baseline_cost_usd": ("baseline", "cost_usd"),
        "candidate_cost_usd": ("candidate", "cost_usd"),
    }
    for key, value in metadata.items():
        mapping = key_map.get(key)
        if not mapping:
            continue
        side, field_name = mapping
        target = baseline if side == "baseline" else candidate
        if field_name not in target:
            target[field_name] = value


def _decision_metadata(baseline: dict, candidate: dict, strict: bool, applied_waivers: list[Waiver]) -> dict:
    metadata = {"strict": strict}

    if isinstance(baseline.get("model"), str):
        metadata["baseline_model"] = baseline["model"]
    if isinstance(candidate.get("model"), str):
        metadata["candidate_model"] = candidate["model"]

    if applied_waivers:
        metadata["waivers_applied"] = [
            {
                "reason_code": w.reason_code,
                "expires_at": w.expires_at,
                "reason": w.reason,
                **({"ticket": w.ticket} if w.ticket else {}),
                **({"issued_by": w.issued_by} if w.issued_by else {}),
            }
            for w in applied_waivers
        ]

    return metadata
