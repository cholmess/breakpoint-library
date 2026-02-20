import json
from breakpoint.engine.policies.output_contract import evaluate_output_contract_policy

def evaluate(baseline: dict, candidate: dict, config: dict = None):
    return evaluate_output_contract_policy(
        baseline=baseline, 
        candidate=candidate, 
        config=config or {"enabled": True, "warn_on_missing_keys": True, "warn_on_type_mismatch": True}
    )

def test_recursive_missing_keys():
    baseline = {"output": json.dumps({"user": {"name": "Alice", "age": 30}})}
    candidate = {"output": json.dumps({"user": {"name": "Alice"}})}
    result = evaluate(baseline, candidate)
    
    assert result.status == "WARN"
    assert "CONTRACT_WARN_MISSING_KEYS" in result.codes
    assert "user.age" in result.details["missing_keys"]

def test_recursive_type_mismatch():
    baseline = {"output": json.dumps({"data": {"items": [1, 2, 3]}, "flag": True})}
    candidate = {"output": json.dumps({"data": {"items": ["1", "2"]}, "flag": "true"})}
    result = evaluate(baseline, candidate)
    
    assert result.status == "WARN"
    assert "CONTRACT_WARN_TYPE_MISMATCH" in result.codes
    assert "data.items[0]" in result.details["type_mismatches"]
    assert "flag" in result.details["type_mismatches"]

def test_recursive_deeply_nested():
    baseline = {"output": json.dumps({"a": {"b": {"c": {"d": "value"}}}})}
    candidate = {"output": json.dumps({"a": {"b": {"c": {"d": 123}}}})}
    result = evaluate(baseline, candidate)
    
    assert result.status == "WARN"
    assert "CONTRACT_WARN_TYPE_MISMATCH" in result.codes
    assert "a.b.c.d" in result.details["type_mismatches"]

def test_nested_allow():
    baseline = {"output": json.dumps({"user": {"profile": {"active": True, "tags": ["a", "b"]}}})}
    candidate = {"output": json.dumps({"user": {"profile": {"active": True, "tags": ["c", "d"]}}})}
    result = evaluate(baseline, candidate)
    
    assert result.status == "ALLOW"
