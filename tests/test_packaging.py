import json
from importlib import resources


def test_default_policies_json_is_packaged():
    resource = resources.files("breakpoint.config").joinpath("default_policies.json")
    with resource.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    assert "cost_policy" in payload
    assert "pii_policy" in payload
    assert "drift_policy" in payload


def test_presets_are_packaged():
    package = "breakpoint.config.presets"
    expected = {"chatbot.json", "support.json", "extraction.json"}
    files = {p.name for p in resources.files(package).iterdir() if p.is_file()}
    assert expected.issubset(files)
