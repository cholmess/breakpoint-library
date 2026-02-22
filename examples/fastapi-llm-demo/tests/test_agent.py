"""Pytest + BreakPoint assert_stable example (stretch)."""

import json
from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parent.parent


def test_good_candidate_vs_baseline(breakpoint):
    """Assert that the pre-baked good candidate passes policy checks."""
    with open(DEMO_ROOT / "candidates" / "good.json") as f:
        candidate = json.load(f)
    breakpoint.assert_stable(
        candidate["output"],
        candidate_metadata={
            "tokens_in": candidate["tokens_in"],
            "tokens_out": candidate["tokens_out"],
            "cost_usd": candidate["cost_usd"],
            "model": candidate["model"],
        },
        name="good",
    )
