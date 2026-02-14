from breakpoint.engine.policies.base import PolicyResult


def evaluate_cost_policy(
    baseline: dict, candidate: dict, thresholds: dict, pricing: dict
) -> PolicyResult:
    baseline_cost = _resolve_cost(baseline, pricing)
    candidate_cost = _resolve_cost(candidate, pricing)

    if baseline_cost is None or candidate_cost is None:
        return PolicyResult(
            policy="cost",
            status="WARN",
            reasons=["Insufficient cost data; unable to compute full cost delta."],
            codes=["COST_WARN_MISSING_DATA"],
        )

    min_baseline_cost = float(thresholds.get("min_baseline_cost_usd", 0.01))
    if baseline_cost < min_baseline_cost:
        return PolicyResult(
            policy="cost",
            status="WARN",
            reasons=[
                f"Baseline cost ${baseline_cost:.4f} is below minimum ${min_baseline_cost:.4f}; percent delta is unreliable."
            ],
            codes=["COST_WARN_LOW_BASELINE"],
            details={"baseline_cost_usd": baseline_cost, "min_baseline_cost_usd": min_baseline_cost},
        )

    delta_usd = candidate_cost - baseline_cost
    increase_pct = ((candidate_cost - baseline_cost) / baseline_cost) * 100
    block_threshold = float(thresholds.get("block_increase_pct", 35))
    warn_threshold = float(thresholds.get("warn_increase_pct", 20))
    warn_delta_usd = float(thresholds.get("warn_delta_usd", 0.0))
    block_delta_usd = float(thresholds.get("block_delta_usd", 0.0))

    if (block_delta_usd > 0 and delta_usd > block_delta_usd) or increase_pct > block_threshold:
        return PolicyResult(
            policy="cost",
            status="BLOCK",
            reasons=[
                f"Cost increased by {increase_pct:.1f}% (>{block_threshold:.0f}%)."
                + (f" Absolute delta ${delta_usd:.4f} (>{block_delta_usd:.4f})." if block_delta_usd > 0 else "")
            ],
            codes=["COST_BLOCK_INCREASE"],
            details={"increase_pct": increase_pct, "delta_usd": delta_usd},
        )
    if (warn_delta_usd > 0 and delta_usd > warn_delta_usd) or increase_pct > warn_threshold:
        return PolicyResult(
            policy="cost",
            status="WARN",
            reasons=[
                f"Cost increased by {increase_pct:.1f}% (>{warn_threshold:.0f}%)."
                + (f" Absolute delta ${delta_usd:.4f} (>{warn_delta_usd:.4f})." if warn_delta_usd > 0 else "")
            ],
            codes=["COST_WARN_INCREASE"],
            details={"increase_pct": increase_pct, "delta_usd": delta_usd},
        )
    return PolicyResult(policy="cost", status="ALLOW")


def _resolve_cost(record: dict, pricing: dict) -> float | None:
    direct_cost = record.get("cost_usd")
    if isinstance(direct_cost, (int, float)):
        return float(direct_cost)

    model_name = record.get("model")
    model_pricing = pricing.get(model_name, {}) if isinstance(model_name, str) else {}

    tokens_in = record.get("tokens_in")
    tokens_out = record.get("tokens_out")
    tokens_total = record.get("tokens_total")

    if isinstance(tokens_in, (int, float)) and isinstance(tokens_out, (int, float)):
        input_per_1k = model_pricing.get("input_per_1k")
        output_per_1k = model_pricing.get("output_per_1k")
        if isinstance(input_per_1k, (int, float)) and isinstance(output_per_1k, (int, float)):
            return (float(tokens_in) / 1000 * float(input_per_1k)) + (
                float(tokens_out) / 1000 * float(output_per_1k)
            )

    if isinstance(tokens_total, (int, float)):
        per_1k = model_pricing.get("per_1k")
        if isinstance(per_1k, (int, float)):
            return (float(tokens_total) / 1000) * float(per_1k)

    return None
