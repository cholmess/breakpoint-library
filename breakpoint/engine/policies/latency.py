from breakpoint.engine.policies.base import PolicyResult


def evaluate_latency_policy(baseline: dict, candidate: dict, thresholds: dict) -> PolicyResult:
    baseline_latency = _resolve_latency_ms(baseline)
    candidate_latency = _resolve_latency_ms(candidate)

    if baseline_latency is None or candidate_latency is None:
        details = {}
        if baseline_latency is not None:
            details["baseline_latency_ms"] = baseline_latency
        if candidate_latency is not None:
            details["candidate_latency_ms"] = candidate_latency
        return PolicyResult(
            policy="latency",
            status="WARN",
            reasons=["Insufficient latency data; unable to compute full latency delta."],
            codes=["LATENCY_WARN_MISSING_DATA"],
            details=details,
        )

    min_baseline_latency = float(thresholds.get("min_baseline_latency_ms", 50.0))
    if baseline_latency < min_baseline_latency:
        return PolicyResult(
            policy="latency",
            status="WARN",
            reasons=[
                f"Baseline latency {baseline_latency:.1f}ms is below minimum {min_baseline_latency:.1f}ms; percent delta is unreliable."
            ],
            codes=["LATENCY_WARN_LOW_BASELINE"],
            details={
                "baseline_latency_ms": baseline_latency,
                "min_baseline_latency_ms": min_baseline_latency,
            },
        )

    delta_ms = candidate_latency - baseline_latency
    increase_pct = (delta_ms / baseline_latency) * 100

    block_threshold = float(thresholds.get("block_increase_pct", 60))
    warn_threshold = float(thresholds.get("warn_increase_pct", 30))
    warn_delta_ms = float(thresholds.get("warn_delta_ms", 0.0))
    block_delta_ms = float(thresholds.get("block_delta_ms", 0.0))

    if (block_delta_ms > 0 and delta_ms > block_delta_ms) or increase_pct > block_threshold:
        return PolicyResult(
            policy="latency",
            status="BLOCK",
            reasons=[
                f"Latency increased by {increase_pct:.1f}% (>{block_threshold:.0f}%)."
                + (f" Absolute delta {delta_ms:.1f}ms (>{block_delta_ms:.1f}ms)." if block_delta_ms > 0 else "")
            ],
            codes=["LATENCY_BLOCK_INCREASE"],
            details={
                "baseline_latency_ms": baseline_latency,
                "candidate_latency_ms": candidate_latency,
                "increase_pct": increase_pct,
                "delta_ms": delta_ms,
            },
        )

    if (warn_delta_ms > 0 and delta_ms > warn_delta_ms) or increase_pct > warn_threshold:
        return PolicyResult(
            policy="latency",
            status="WARN",
            reasons=[
                f"Latency increased by {increase_pct:.1f}% (>{warn_threshold:.0f}%)."
                + (f" Absolute delta {delta_ms:.1f}ms (>{warn_delta_ms:.1f}ms)." if warn_delta_ms > 0 else "")
            ],
            codes=["LATENCY_WARN_INCREASE"],
            details={
                "baseline_latency_ms": baseline_latency,
                "candidate_latency_ms": candidate_latency,
                "increase_pct": increase_pct,
                "delta_ms": delta_ms,
            },
        )

    return PolicyResult(
        policy="latency",
        status="ALLOW",
        details={
            "baseline_latency_ms": baseline_latency,
            "candidate_latency_ms": candidate_latency,
            "increase_pct": increase_pct,
            "delta_ms": delta_ms,
        },
    )


def _resolve_latency_ms(record: dict) -> float | None:
    value = record.get("latency_ms")
    if isinstance(value, (int, float)):
        return float(value)
    return None
