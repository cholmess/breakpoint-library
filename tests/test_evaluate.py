import json

import pytest

from breakpoint import evaluate


def test_cost_warn_on_increase():
    decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0},
        candidate={"output": "same", "cost_usd": 1.24},
    )
    assert decision.status == "WARN"
    assert decision.schema_version == "1.0.0"
    assert "COST_INCREASE_WARN" in decision.reason_codes


def test_pii_blocks_email():
    decision = evaluate(
        baseline={"output": "hello"},
        candidate={"output": "contact me at hi@example.com and alt@example.com", "cost_usd": 1.0},
    )
    assert decision.status == "BLOCK"
    assert "PII_EMAIL_BLOCK" in decision.reason_codes
    assert decision.metrics["pii_blocked_total"] == 2
    assert decision.metrics["pii_blocked_type_count"] == 1


def test_pii_credit_card_uses_luhn_check():
    decision = evaluate(
        baseline={"output": "hello"},
        candidate={"output": "test 4111 1111 1111 1111", "cost_usd": 1.0},
    )
    assert decision.status == "BLOCK"
    assert "PII_CREDIT_CARD_BLOCK" in decision.reason_codes

    not_a_card = evaluate(
        baseline={"output": "hello"},
        candidate={"output": "test 4111 1111 1111 1112", "cost_usd": 1.0},
    )
    assert "PII_CREDIT_CARD_BLOCK" not in not_a_card.reason_codes


def test_drift_blocks_empty_candidate():
    decision = evaluate(
        baseline={"output": "long baseline text", "cost_usd": 1.0},
        candidate={"output": "  ", "cost_usd": 1.0},
    )
    assert decision.status == "BLOCK"
    assert "DRIFT_EMPTY_OUTPUT_BLOCK" in decision.reason_codes


def test_strict_promotes_warn_to_block():
    decision = evaluate(
        baseline={"output": "abc", "cost_usd": 1.0},
        candidate={"output": "abc", "cost_usd": 1.24},
        strict=True,
    )
    assert decision.status == "BLOCK"
    assert "STRICT_MODE_PROMOTION_BLOCK" in decision.reason_codes


def test_missing_cost_data_warns():
    decision = evaluate(
        baseline={"output": "hello"},
        candidate={"output": "hello there"},
    )
    assert decision.status in {"WARN", "BLOCK"}
    assert "COST_WARN_MISSING_DATA" in decision.reason_codes
    assert "cost" in decision.details


def test_cost_low_baseline_warns():
    decision = evaluate(
        baseline={"output": "hello", "cost_usd": 0.0001},
        candidate={"output": "hello", "cost_usd": 0.0003},
    )
    assert decision.status == "WARN"
    assert "COST_WARN_LOW_BASELINE" in decision.reason_codes


def test_latency_warn_on_increase():
    decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0, "latency_ms": 100},
        candidate={"output": "same", "cost_usd": 1.0, "latency_ms": 140},
        mode="full",
    )
    assert decision.status == "WARN"
    assert "LATENCY_INCREASE_WARN" in decision.reason_codes
    assert decision.metrics["latency_delta_pct"] == 40.0


def test_latency_blocks_on_large_increase():
    decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0, "latency_ms": 100},
        candidate={"output": "same", "cost_usd": 1.0, "latency_ms": 200},
        mode="full",
    )
    assert decision.status == "BLOCK"
    assert "LATENCY_INCREASE_BLOCK" in decision.reason_codes


def test_latency_missing_data_warns():
    decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0},
        candidate={"output": "same", "cost_usd": 1.0},
        mode="full",
    )
    assert decision.status == "WARN"
    assert "LATENCY_WARN_MISSING_DATA" in decision.reason_codes


def test_latency_metadata_mapping():
    decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0},
        candidate={"output": "same", "cost_usd": 1.0},
        metadata={"baseline_latency_ms": 100, "candidate_latency_ms": 140},
        mode="full",
    )
    assert decision.status == "WARN"
    assert "LATENCY_INCREASE_WARN" in decision.reason_codes


def test_output_contract_blocks_invalid_json_when_baseline_is_json():
    decision = evaluate(
        baseline={"output": "{\"id\":1,\"summary\":\"ok\"}", "cost_usd": 1.0},
        candidate={"output": "not-json", "cost_usd": 1.0},
        mode="full",
    )
    assert decision.status == "BLOCK"
    assert "OUTPUT_CONTRACT_INVALID_JSON_BLOCK" in decision.reason_codes
    assert decision.metrics["output_contract_invalid_json_count"] == 1


def test_output_contract_warns_on_missing_keys():
    decision = evaluate(
        baseline={"output": "{\"id\":1,\"summary\":\"ok\",\"severity\":\"medium\"}", "cost_usd": 1.0},
        candidate={"output": "{\"id\":2,\"summary\":\"ok\"}", "cost_usd": 1.0},
        mode="full",
    )
    assert decision.status == "WARN"
    assert "OUTPUT_CONTRACT_MISSING_KEYS_WARN" in decision.reason_codes
    assert decision.metrics["output_contract_missing_keys_count"] == 1


def test_output_contract_warns_on_type_mismatch():
    decision = evaluate(
        baseline={"output": "{\"id\":1,\"summary\":\"ok\"}", "cost_usd": 1.0},
        candidate={"output": "{\"id\":\"1\",\"summary\":\"ok\"}", "cost_usd": 1.0},
        mode="full",
    )
    assert decision.status == "WARN"
    assert "OUTPUT_CONTRACT_TYPE_MISMATCH_WARN" in decision.reason_codes
    assert decision.metrics["output_contract_type_mismatch_count"] == 1


def test_default_drift_tuning_reduces_moderate_length_noise():
    decision = evaluate(
        baseline={"output": "a" * 100, "cost_usd": 1.0, "latency_ms": 100},
        candidate={"output": "a" * 130, "cost_usd": 1.0, "latency_ms": 100},
    )
    assert decision.status == "ALLOW"


def test_environment_override_changes_thresholds(tmp_path):
    config_path = tmp_path / "policy.json"
    config_path.write_text(
        json.dumps(
            {
                "environments": {
                    "dev": {"cost_policy": {"warn_increase_pct": 5, "block_increase_pct": 10}},
                    "prod": {"cost_policy": {"warn_increase_pct": 50, "block_increase_pct": 70}},
                }
            }
        ),
        encoding="utf-8",
    )

    dev_decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0, "latency_ms": 100},
        candidate={"output": "same", "cost_usd": 1.08, "latency_ms": 100},
        config_path=str(config_path),
        config_environment="dev",
        mode="full",
    )
    assert dev_decision.status == "WARN"
    assert "COST_INCREASE_WARN" in dev_decision.reason_codes

    prod_decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0, "latency_ms": 100},
        candidate={"output": "same", "cost_usd": 1.08, "latency_ms": 100},
        config_path=str(config_path),
        config_environment="prod",
        mode="full",
    )
    assert prod_decision.status == "ALLOW"


def test_lite_mode_ignores_latency_and_output_contract():
    decision = evaluate(
        baseline={"output": "{\"id\":1}", "cost_usd": 1.0, "latency_ms": 100},
        candidate={"output": "not-json", "cost_usd": 1.0, "latency_ms": 180},
    )
    assert decision.status == "ALLOW"
    assert "LATENCY_INCREASE_WARN" not in decision.reason_codes
    assert "OUTPUT_CONTRACT_INVALID_JSON_BLOCK" not in decision.reason_codes


def test_invalid_config_thresholds_fail_fast(tmp_path):
    config_path = tmp_path / "invalid_policy.json"
    config_path.write_text(
        json.dumps(
            {
                "cost_policy": {
                    "warn_increase_pct": 40,
                    "block_increase_pct": 30,
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="block_increase_pct"):
        evaluate(
            baseline={"output": "same", "cost_usd": 1.0},
            candidate={"output": "same", "cost_usd": 1.08},
            config_path=str(config_path),
        )


def test_invalid_output_contract_config_fails_fast(tmp_path):
    config_path = tmp_path / "invalid_contract_policy.json"
    config_path.write_text(
        json.dumps(
            {
                "output_contract_policy": {
                    "enabled": "yes",
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="output_contract_policy.enabled"):
        evaluate(
            baseline={"output": "{\"id\":1}", "cost_usd": 1.0},
            candidate={"output": "{\"id\":2}", "cost_usd": 1.0},
            config_path=str(config_path),
        )
