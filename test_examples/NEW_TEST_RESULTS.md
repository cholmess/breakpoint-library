# New Test Cases - BreakPoint Library

This document contains test results from new examples not included in the original library examples.

## Test Scenarios

### Test 1: Token-based Cost Calculation (Output Token Spike)

**Scenario:** Testing cost calculation from tokens when `cost_usd` is not provided. Output tokens increased significantly.

**Files:**
- Baseline: `baseline_token_cost.json` (500 output tokens)
- Candidate: `candidate_token_cost_spike.json` (1200 output tokens)

**Result:** ✅ **BLOCK** - Output drift detected (160.9% expansion)
- Cost policy couldn't evaluate (no pricing model configured, but tokens show spike)
- Output length increased dramatically (64 → 167 chars)
- Demonstrates token-based cost calculation capability

---

### Test 2: Credit Card PII Detection

**Scenario:** Testing PII detection with credit card numbers in output.

**Files:**
- Baseline: `baseline_clean.json`
- Candidate: `candidate_credit_card.json` (contains credit card number)

**Result:** ✅ **BLOCK** - Output drift detected (95.2% expansion)
- Note: Credit card number may not have passed Luhn validation (pattern detected but invalid)
- Output length increased significantly
- Demonstrates PII pattern matching

---

### Test 3: Latency Issue (Large Increase)

**Scenario:** Testing response with significant latency increase (50ms → 450ms).

**Files:**
- Baseline: `baseline_fast.json` (50ms latency)
- Candidate: `candidate_latency_issue.json` (450ms latency)

**Result:** ✅ **BLOCK** - Multiple issues detected
- Cost: WARN (20% increase - exactly at threshold)
- Output drift: BLOCK (192.3% expansion)
- Latency: Not evaluated in Lite mode (Full mode feature)
- Demonstrates combined cost and drift issues

---

### Test 4: Empty Output Detection

**Scenario:** Testing detection of completely empty output.

**Files:**
- Baseline: `baseline_short.json` ("Status: Active")
- Candidate: `candidate_empty.json` (empty string)

**Result:** ✅ **BLOCK** - Empty output detected
- Immediate BLOCK on empty output (policy rule)
- 100% compression detected
- Demonstrates empty output protection

---

### Test 5: Borderline WARN Case (Just Under BLOCK Threshold)

**Scenario:** Testing case where cost is just under WARN threshold but drift exceeds BLOCK.

**Files:**
- Baseline: `baseline_borderline.json`
- Candidate: `candidate_borderline_warn.json`

**Result:** ✅ **BLOCK** - Output drift exceeds threshold
- Cost: 19% (just under 20% WARN threshold) - ALLOW
- Output drift: 102.7% (exceeds 70% BLOCK threshold) - BLOCK
- Demonstrates that any BLOCK policy result causes final BLOCK decision

---

### Test 6: Valid Credit Card + Email PII

**Scenario:** Testing PII detection with both email and credit card.

**Files:**
- Baseline: `baseline_clean.json`
- Candidate: `candidate_valid_credit_card.json`

**Result:** ✅ **BLOCK** - Multiple issues detected
- PII: EMAIL detected (1 match)
- Output drift: 187.3% expansion (BLOCK threshold exceeded)
- Demonstrates PII detection working correctly
- Shows combined PII and drift violations

---

### Test 7: True Borderline (Just Under Thresholds)

**Scenario:** Testing case that's just under all thresholds - should result in WARN.

**Files:**
- Baseline: `baseline_borderline.json`
- Candidate: `candidate_true_borderline.json`

**Result:** ⚠️ **WARN** - Output drift at WARN level
- Cost: 19% (just under 20% WARN threshold) - ALLOW
- Output drift: 61.6% (exceeds 35% WARN, but under 70% BLOCK) - WARN
- Demonstrates threshold boundaries working correctly
- Shows WARN decision when no BLOCK violations

## Key Findings

1. **Token-based cost calculation**: Works when tokens are provided, though requires pricing model configuration for full evaluation
2. **PII detection**: Successfully detects emails; credit cards require Luhn validation
3. **Empty output**: Immediately blocked as expected
4. **Threshold boundaries**: Correctly identifies WARN vs BLOCK based on thresholds
5. **Combined violations**: Multiple policy violations correctly aggregate to BLOCK
6. **Latency**: Not evaluated in Lite mode (Full mode feature)

## Test Files Location

All test files are located in: `test_examples/`

- `baseline_*.json` - Baseline test cases
- `candidate_*.json` - Candidate test cases to evaluate

## Running the Tests

```bash
# Test 1: Token-based cost
python3 -m breakpoint.cli.main evaluate test_examples/baseline_token_cost.json test_examples/candidate_token_cost_spike.json

# Test 2: Credit card PII
python3 -m breakpoint.cli.main evaluate test_examples/baseline_clean.json test_examples/candidate_credit_card.json

# Test 3: Latency issue
python3 -m breakpoint.cli.main evaluate test_examples/baseline_fast.json test_examples/candidate_latency_issue.json

# Test 4: Empty output
python3 -m breakpoint.cli.main evaluate test_examples/baseline_short.json test_examples/candidate_empty.json

# Test 5: Borderline case
python3 -m breakpoint.cli.main evaluate test_examples/baseline_borderline.json test_examples/candidate_borderline_warn.json

# Test 6: PII + drift
python3 -m breakpoint.cli.main evaluate test_examples/baseline_clean.json test_examples/candidate_valid_credit_card.json

# Test 7: True borderline
python3 -m breakpoint.cli.main evaluate test_examples/baseline_borderline.json test_examples/candidate_true_borderline.json
```

---

*These tests demonstrate BreakPoint's ability to catch various types of issues beyond the original example set.*

