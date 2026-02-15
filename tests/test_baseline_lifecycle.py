import json
from pathlib import Path

from breakpoint import evaluate


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "baseline_lifecycle"


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def test_baseline_reproducibility_from_stored_artifacts():
    baseline_current = _load_json("baseline_current.json")
    candidate = _load_json("candidate.json")

    first = evaluate(baseline=baseline_current["input"], candidate=candidate).to_dict()
    second = evaluate(baseline=baseline_current["input"], candidate=candidate).to_dict()

    assert first == second


def test_baseline_rollback_changes_decision_with_sample_data():
    baseline_current = _load_json("baseline_current.json")
    baseline_previous = _load_json("baseline_previous.json")
    candidate = _load_json("candidate.json")

    current_decision = evaluate(baseline=baseline_current["input"], candidate=candidate)
    previous_decision = evaluate(baseline=baseline_previous["input"], candidate=candidate)

    assert current_decision.status == "BLOCK"
    assert previous_decision.status == "ALLOW"
