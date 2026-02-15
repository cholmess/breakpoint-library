import json
from pathlib import Path

from breakpoint import evaluate


SAMPLES_DIR = Path(__file__).parent.parent / "examples" / "quickstart"


def _load(name: str) -> dict:
    return json.loads((SAMPLES_DIR / name).read_text(encoding="utf-8"))


def test_quickstart_samples_statuses_are_reproducible():
    baseline = _load("baseline.json")
    candidate_allow = _load("candidate_allow.json")
    candidate_warn = _load("candidate_warn.json")
    candidate_block = _load("candidate_block.json")

    decision_allow = evaluate(baseline=baseline, candidate=candidate_allow)
    decision_warn = evaluate(baseline=baseline, candidate=candidate_warn)
    decision_block = evaluate(baseline=baseline, candidate=candidate_block)

    assert decision_allow.status == "ALLOW"
    assert decision_warn.status == "WARN"
    assert decision_block.status == "BLOCK"
