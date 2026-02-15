import json
from pathlib import Path

from breakpoint import evaluate


SAMPLES_DIR = Path(__file__).parent.parent / "examples" / "install_worthy"


def _load(name: str) -> dict:
    return json.loads((SAMPLES_DIR / name).read_text(encoding="utf-8"))


def test_install_worthy_examples_are_reproducible():
    baseline = _load("baseline.json")

    cost_model_swap = evaluate(baseline=baseline, candidate=_load("candidate_cost_model_swap.json"))
    format_regression = evaluate(baseline=baseline, candidate=_load("candidate_format_regression.json"))
    pii_verbosity = evaluate(baseline=baseline, candidate=_load("candidate_pii_verbosity.json"))
    killer_tradeoff = evaluate(baseline=baseline, candidate=_load("candidate_killer_tradeoff.json"))

    assert cost_model_swap.status == "BLOCK"
    assert "COST_INCREASE_BLOCK" in cost_model_swap.reason_codes

    assert format_regression.status == "BLOCK"
    assert "OUTPUT_CONTRACT_INVALID_JSON_BLOCK" in format_regression.reason_codes

    assert pii_verbosity.status == "BLOCK"
    assert "PII_EMAIL_BLOCK" in pii_verbosity.reason_codes
    assert pii_verbosity.metrics["pii_blocked_total"] == 4

    assert killer_tradeoff.status == "BLOCK"
    assert "COST_INCREASE_BLOCK" in killer_tradeoff.reason_codes
    assert "LATENCY_INCREASE_BLOCK" in killer_tradeoff.reason_codes
