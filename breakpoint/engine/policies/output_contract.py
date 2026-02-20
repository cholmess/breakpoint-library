import json

from breakpoint.engine.policies.base import PolicyResult


def evaluate_output_contract_policy(baseline: dict, candidate: dict, config: dict) -> PolicyResult:
    if not bool(config.get("enabled", True)):
        return PolicyResult(policy="output_contract", status="ALLOW")

    baseline_raw = baseline.get("output", "")
    candidate_raw = candidate.get("output", "")
    baseline_text = baseline_raw if isinstance(baseline_raw, str) else str(baseline_raw)
    candidate_text = candidate_raw if isinstance(candidate_raw, str) else str(candidate_raw)

    baseline_payload, baseline_error = _parse_json(baseline_text)
    if baseline_error is not None:
        return PolicyResult(policy="output_contract", status="ALLOW")

    candidate_payload, candidate_error = _parse_json(candidate_text)
    if candidate_error is not None:
        if bool(config.get("block_on_invalid_json", True)):
            return PolicyResult(
                policy="output_contract",
                status="BLOCK",
                reasons=["Output contract break: candidate output is not valid JSON."],
                codes=["CONTRACT_BLOCK_INVALID_JSON"],
                details={"invalid_json": True, "invalid_json_count": 1},
            )
        return PolicyResult(
            policy="output_contract",
            status="WARN",
            reasons=["Output contract risk: candidate output is not valid JSON."],
            codes=["CONTRACT_WARN_INVALID_JSON"],
            details={"invalid_json": True, "invalid_json_count": 1},
        )

    reasons: list[str] = []
    codes: list[str] = []
    details: dict = {}

    if type(baseline_payload) is not type(candidate_payload):
        reasons.append(
            f"Output contract break: top-level JSON type changed from {_json_type_name(baseline_payload)} "
            f"to {_json_type_name(candidate_payload)}."
        )
        codes.append("CONTRACT_BLOCK_TYPE_CHANGE")
        details["top_level_type_changed"] = True

    missing_keys: list[str] = []
    type_mismatches: list[str] = []

    def _compare_schema(b_node: object, c_node: object, path: str):
        b_type = _json_type_name(b_node)
        c_type = _json_type_name(c_node)

        if b_type != c_type:
            # Avoid duplicate top-level type matching since it's already caught
            if path:
                type_mismatches.append(path)
            return

        if b_type == "object":
            b_keys = set(b_node.keys())
            c_keys = set(c_node.keys())

            for k in b_keys - c_keys:
                missing_keys.append(f"{path}.{k}" if path else k)

            for k in b_keys & c_keys:
                next_path = f"{path}.{k}" if path else k
                _compare_schema(b_node[k], c_node[k], next_path)

        elif b_type == "array":
            if b_node and c_node:
                # Compare representative element (index 0)
                next_path = f"{path}[0]"
                _compare_schema(b_node[0], c_node[0], next_path)

    if type(baseline_payload) is type(candidate_payload):
        _compare_schema(baseline_payload, candidate_payload, "")
            
    if missing_keys and bool(config.get("warn_on_missing_keys", True)):
        missing_keys.sort()
        reasons.append(
            "Output contract regression: missing keys "
            + ", ".join(missing_keys[:10])
            + ("." if len(missing_keys) <= 10 else f" (+{len(missing_keys) - 10} more).")
        )
        codes.append("CONTRACT_WARN_MISSING_KEYS")

    if type_mismatches and bool(config.get("warn_on_type_mismatch", True)):
        type_mismatches.sort()
        reasons.append(
            "Output contract regression: type mismatch for keys "
            + ", ".join(type_mismatches[:10])
            + ("." if len(type_mismatches) <= 10 else f" (+{len(type_mismatches) - 10} more).")
        )
        codes.append("CONTRACT_WARN_TYPE_MISMATCH")

    if missing_keys:
        details["missing_keys"] = missing_keys
        details["missing_keys_count"] = len(missing_keys)
    if type_mismatches:
        details["type_mismatches"] = type_mismatches
        details["type_mismatches_count"] = len(type_mismatches)

    if any(code.startswith("CONTRACT_BLOCK_") for code in codes):
        return PolicyResult(policy="output_contract", status="BLOCK", reasons=reasons, codes=codes, details=details)
    if reasons:
        return PolicyResult(policy="output_contract", status="WARN", reasons=reasons, codes=codes, details=details)
    return PolicyResult(policy="output_contract", status="ALLOW", details=details)


def _parse_json(value: str) -> tuple[object | None, str | None]:
    try:
        return json.loads(value), None
    except json.JSONDecodeError as exc:
        return None, str(exc)


def _json_type_name(value: object) -> str:
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    return type(value).__name__
