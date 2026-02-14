from breakpoint import evaluate


def test_cost_warn_on_increase():
    decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0},
        candidate={"output": "same", "cost_usd": 1.24},
    )
    assert decision.status == "WARN"
    assert "COST_WARN_INCREASE" in decision.codes


def test_pii_blocks_email():
    decision = evaluate(
        baseline={"output": "hello"},
        candidate={"output": "contact me at hi@example.com", "cost_usd": 1.0},
    )
    assert decision.status == "BLOCK"
    assert "PII_BLOCK_EMAIL" in decision.codes


def test_pii_credit_card_uses_luhn_check():
    decision = evaluate(
        baseline={"output": "hello"},
        candidate={"output": "test 4111 1111 1111 1111", "cost_usd": 1.0},
    )
    assert decision.status == "BLOCK"
    assert "PII_BLOCK_CREDIT_CARD" in decision.codes

    not_a_card = evaluate(
        baseline={"output": "hello"},
        candidate={"output": "test 4111 1111 1111 1112", "cost_usd": 1.0},
    )
    assert "PII_BLOCK_CREDIT_CARD" not in not_a_card.codes


def test_drift_blocks_empty_candidate():
    decision = evaluate(
        baseline={"output": "long baseline text", "cost_usd": 1.0},
        candidate={"output": "  ", "cost_usd": 1.0},
    )
    assert decision.status == "BLOCK"
    assert "DRIFT_BLOCK_EMPTY" in decision.codes


def test_strict_promotes_warn_to_block():
    decision = evaluate(
        baseline={"output": "abc", "cost_usd": 1.0},
        candidate={"output": "abcdef", "cost_usd": 1.24},
        strict=True,
    )
    assert decision.status == "BLOCK"
    assert "STRICT_PROMOTED_WARN" in decision.codes


def test_missing_cost_data_warns():
    decision = evaluate(
        baseline={"output": "hello"},
        candidate={"output": "hello there"},
    )
    assert decision.status in {"WARN", "BLOCK"}
    assert "COST_WARN_MISSING_DATA" in decision.codes
    assert "cost" in decision.details


def test_cost_low_baseline_warns():
    decision = evaluate(
        baseline={"output": "hello", "cost_usd": 0.0001},
        candidate={"output": "hello", "cost_usd": 0.0003},
    )
    assert decision.status == "WARN"
    assert "COST_WARN_LOW_BASELINE" in decision.codes


def test_latency_warn_on_increase():
    decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0, "latency_ms": 100},
        candidate={"output": "same", "cost_usd": 1.0, "latency_ms": 140},
    )
    assert decision.status == "WARN"
    assert "LATENCY_WARN_INCREASE" in decision.codes


def test_latency_blocks_on_large_increase():
    decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0, "latency_ms": 100},
        candidate={"output": "same", "cost_usd": 1.0, "latency_ms": 200},
    )
    assert decision.status == "BLOCK"
    assert "LATENCY_BLOCK_INCREASE" in decision.codes


def test_latency_missing_data_warns():
    decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0},
        candidate={"output": "same", "cost_usd": 1.0},
    )
    assert decision.status == "WARN"
    assert "LATENCY_WARN_MISSING_DATA" in decision.codes


def test_latency_metadata_mapping():
    decision = evaluate(
        baseline={"output": "same", "cost_usd": 1.0},
        candidate={"output": "same", "cost_usd": 1.0},
        metadata={"baseline_latency_ms": 100, "candidate_latency_ms": 140},
    )
    assert decision.status == "WARN"
    assert "LATENCY_WARN_INCREASE" in decision.codes
