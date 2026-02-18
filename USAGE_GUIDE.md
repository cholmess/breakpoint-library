# BreakPoint Library - Usage Guide & Test Results

This guide shows you how to use BreakPoint Library and includes actual test results from running the examples.

## Enhanced Output Format

The BreakPoint CLI now provides detailed output including:

- **Input Comparison**: Shows baseline → candidate values for output length, cost, tokens, latency, and model
- **Policy Results**: Color-coded policy checks with inline threshold indicators (🟢 ALLOW, 🟡 WARN, 🔴 BLOCK) and threshold warnings
- **Detailed Metrics**: All calculated metrics displayed in one section
- **Reason Codes**: Machine-readable codes for programmatic use

This enhanced format makes it easier to understand exactly what changed and why a decision was made. Color indicators and threshold information are integrated directly into the Policy Results section for quick visual scanning.

## Quick Start

### Basic Command Format

```bash
python3 -m breakpoint.cli.main evaluate <baseline.json> <candidate.json>
```

### Using JSON Output (for CI)

```bash
python3 -m breakpoint.cli.main evaluate <baseline.json> <candidate.json> --json
```

## Available Example Files

### Quickstart Examples (`examples/quickstart/`)
- `baseline.json` - Baseline output
- `candidate_allow.json` - Should result in ALLOW
- `candidate_warn.json` - Should result in WARN
- `candidate_block.json` - Should result in BLOCK

### Realistic Scenarios (`examples/install_worthy/`)
- `baseline.json` - Baseline with structured output
- `candidate_cost_model_swap.json` - Cost regression scenario
- `candidate_format_regression.json` - Format regression scenario
- `candidate_pii_verbosity.json` - PII leak scenario
- `candidate_killer_tradeoff.json` - Cost blowup scenario

### Additional Test Examples (`test_examples/`)
- `baseline_short.json` / `candidate_empty.json` - Empty output detection
- `baseline_token_cost.json` / `candidate_token_cost_spike.json` - Token-based cost calculation
- `baseline_fast.json` / `candidate_latency_issue.json` - Combined cost and drift issues
- `baseline_clean.json` / `candidate_valid_credit_card.json` - PII detection with email
- `baseline_borderline.json` / `candidate_true_borderline.json` - Borderline WARN case

## Test Results

### Test 1: ALLOW Case

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate examples/quickstart/baseline.json examples/quickstart/candidate_allow.json
```

**Actual Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 46 chars → 46 chars
  Cost: $1.0000 → $1.0100
  Latency: 100ms → 102ms
  Model: gpt-4.1-mini → gpt-4.1-mini

Final Decision: ALLOW

Policy Results:
🟢 ✓ No PII detected: No matches.
🟢 ✓ Response format: No schema drift detected.
🟢 ✓ Cost: No issues. ($1.0000 → $1.0100, +$0.0100)
🟢 ✓ Latency: No issues. (100ms → 102ms, +2ms)
🟢 ✓ Output drift: No issues. (46 → 46 chars)

Summary:
No risky deltas detected against configured policies.

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ✅ ALLOW - Safe to deploy

---

### Test 2: WARN Case

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate examples/quickstart/baseline.json examples/quickstart/candidate_warn.json
```

**Actual Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 46 chars → 70 chars
  Cost: $1.0000 → $1.2500
  Latency: 100ms → 135ms
  Model: gpt-4.1-mini → gpt-4.1-mini

Final Decision: WARN

Policy Results:
🟢 ✓ No PII detected: No matches.
🟢 ✓ Response format: No schema drift detected.
🟡 ⚠ Cost: Delta +25.00%. ($1.0000 → $1.2500, +$0.2500) [🟡 WARN threshold exceeded]
🟢 ✓ Latency: No issues. (100ms → 135ms, +35ms)
🟡 ⚠ Output drift: Length delta +52.17%. (46 → 70 chars) [🟡 WARN threshold exceeded]

Detailed Metrics:
  Cost delta %: +25.00%
  Cost delta USD: +0.250000
  Length delta %: +52.17%

Summary:
Cost increased by 25.0% (>=20%).
1 additional signal(s) detected.

Reason Codes:
  - COST_INCREASE_WARN
  - DRIFT_LENGTH_WARN

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ⚠️ WARN - Review recommended before deploying

---

### Test 3: BLOCK Case

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate examples/quickstart/baseline.json examples/quickstart/candidate_block.json
```

**Actual Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 46 chars → 50 chars
  Cost: $1.0000 → $1.4000
  Latency: 100ms → 170ms
  Model: gpt-4.1-mini → gpt-4.1-mini

Final Decision: BLOCK

Policy Results:
🔴 ✗ No PII detected: Detected 1 match(es). [Types: EMAIL(1)]
🟢 ✓ Response format: No schema drift detected.
🔴 ✗ Cost: Delta +40.00%. ($1.0000 → $1.4000, +$0.4000) [🔴 BLOCK threshold exceeded]
🟢 ✓ Latency: No issues. (100ms → 170ms, +70ms)
🟢 ✓ Output drift: No issues. (46 → 50 chars)

Detailed Metrics:
  Cost delta %: +40.00%
  Cost delta USD: +0.400000
  PII blocked total: 1
  PII blocked type count: 1

Summary:
- Cost increased by 40.0% (>=40%).
- PII detected: EMAIL(1). Total matches: 1.

Reason Codes:
  - COST_INCREASE_BLOCK
  - PII_EMAIL_BLOCK

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ❌ BLOCK - **DO NOT DEPLOY** - Critical issues detected

---

### Test 4: Realistic Scenario - Cost Regression

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_cost_model_swap.json
```

**Actual Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 140 chars → 140 chars
  Cost: $0.4500 → $0.6600
  Tokens In: 50000 → 50000
  Tokens Out: 10000 → 10000
  Latency: 180ms → 210ms
  Model: gpt-4.1-mini → gpt-4.1

Final Decision: BLOCK

Policy Results:
🟢 ✓ No PII detected: No matches.
🟢 ✓ Response format: No schema drift detected.
🔴 ✗ Cost: Delta +46.67%. ($0.4500 → $0.6600, +$0.2100) [🔴 BLOCK threshold exceeded]
🟢 ✓ Latency: No issues. (180ms → 210ms, +30ms)
🟢 ✓ Output drift: No issues. (140 → 140 chars)

Detailed Metrics:
  Cost delta %: +46.67%
  Cost delta USD: +0.210000

Summary:
- Cost increased by 46.7% (>=40%).

Reason Codes:
  - COST_INCREASE_BLOCK

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ❌ BLOCK - Cost increased by 46.7% after model swap (output appears equivalent but cost spike violates policy)

---

### Test 5: Realistic Scenario - Format Regression

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_format_regression.json
```

**Actual Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 140 chars → 38 chars
  Cost: $0.4500 → $0.4500
  Tokens In: 50000 → 50000
  Tokens Out: 10000 → 10000
  Latency: 180ms → 185ms
  Model: gpt-4.1-mini → gpt-4.1-mini

Final Decision: BLOCK

Policy Results:
🟢 ✓ No PII detected: No matches.
🟢 ✓ Response format: No schema drift detected.
🟢 ✓ Cost: No issues.
🟢 ✓ Latency: No issues. (180ms → 185ms, +5ms)
🔴 ✗ Output drift: Length delta +72.86%. (140 → 38 chars) [🔴 BLOCK threshold exceeded]

Detailed Metrics:
  Length delta %: +72.86%
  Short ratio: 0.271429

Summary:
- Response length compressed: baseline 140 chars vs candidate 38 chars (72.9%, block threshold 70%).
1 additional non-blocking signal(s) detected.

Reason Codes:
  - DRIFT_LENGTH_BLOCK
  - DRIFT_TOO_SHORT_WARN

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ❌ BLOCK - Response length compressed by 72.9% (would break downstream parsers)

---

### Test 6: Realistic Scenario - PII Leak

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate examples/install_worthy/baseline.json examples/install_worthy/candidate_pii_verbosity.json
```

**Actual Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 140 chars → 401 chars
  Cost: $0.4500 → $0.5200
  Tokens In: 50000 → 50000
  Tokens Out: 10000 → 18000
  Latency: 180ms → 225ms
  Model: gpt-4.1-mini → gpt-4.1-mini

Final Decision: BLOCK

Policy Results:
🔴 ✗ No PII detected: Detected 4 match(es). [Types: EMAIL(2), PHONE(2)]
🟢 ✓ Response format: No schema drift detected.
🟢 ✓ Cost: No issues. ($0.4500 → $0.5200, +$0.0700)
🟢 ✓ Latency: No issues. (180ms → 225ms, +45ms)
🔴 ✗ Output drift: Length delta +186.43%. (140 → 401 chars) [🔴 BLOCK threshold exceeded]

Detailed Metrics:
  Length delta %: +186.43%
  PII blocked total: 4
  PII blocked type count: 2

Summary:
- PII detected: EMAIL(2), PHONE(2). Total matches: 4.
- Response length expanded: baseline 140 chars vs candidate 401 chars (186.4%, block threshold 70%).

Reason Codes:
  - PII_EMAIL_BLOCK
  - PII_PHONE_BLOCK
  - DRIFT_LENGTH_BLOCK

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ❌ BLOCK - PII detected (2 emails, 2 phone numbers) + verbosity drift (186.4% expansion)

---

## New Test Examples

The following are additional test cases demonstrating various scenarios beyond the original examples.

### Test 7: Empty Output Detection

**Scenario:** Testing detection of completely empty output (critical failure case).

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate test_examples/baseline_short.json test_examples/candidate_empty.json
```

**Actual Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 14 chars → 0 chars
  Cost: $0.0500 → $0.0500
  Latency: 30ms → 30ms
  Model: gpt-3.5-turbo → gpt-3.5-turbo

Final Decision: BLOCK

Policy Results:
🟢 ✓ No PII detected: No matches.
🟢 ✓ Response format: No schema drift detected.
🟢 ✓ Cost: No issues.
🟢 ✓ Latency: No issues.
🔴 ✗ Output drift: Policy violation detected. (14 → 0 chars) [🔴 BLOCK threshold exceeded]

Summary:
- Candidate output is empty.

Reason Codes:
  - DRIFT_EMPTY_OUTPUT_BLOCK

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ❌ BLOCK - Empty output is immediately blocked (critical failure protection)

---

### Test 8: Token-based Cost Calculation

**Scenario:** Testing cost calculation from tokens when `cost_usd` is not directly provided.

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate test_examples/baseline_token_cost.json test_examples/candidate_token_cost_spike.json
```

**Actual Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 64 chars → 167 chars
  Tokens In: 1500 → 1500
  Tokens Out: 500 → 1200
  Latency: 250ms → 380ms
  Model: gpt-4 → gpt-4

Final Decision: BLOCK

Policy Results:
🟢 ✓ No PII detected: No matches.
🟢 ✓ Response format: No schema drift detected.
🟢 ✓ Cost: No issues.
🟢 ✓ Latency: No issues. (250ms → 380ms, +130ms)
🔴 ✗ Output drift: Length delta +160.94%. (64 → 167 chars) [🔴 BLOCK threshold exceeded]

Detailed Metrics:
  Length delta %: +160.94%

Summary:
- Response length expanded: baseline 64 chars vs candidate 167 chars (160.9%, block threshold 70%).
1 additional non-blocking signal(s) detected.

Reason Codes:
  - COST_WARN_MISSING_DATA
  - DRIFT_LENGTH_BLOCK

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ❌ BLOCK - Output drift detected (160.9% expansion). Demonstrates token-based inputs and output length monitoring.

---

### Test 9: Combined Cost and Drift Issues

**Scenario:** Testing case with both cost increase and significant output drift.

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate test_examples/baseline_fast.json test_examples/candidate_latency_issue.json
```

**Actual Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 52 chars → 152 chars
  Cost: $0.1000 → $0.1200
  Latency: 50ms → 450ms
  Model: gpt-3.5-turbo → gpt-3.5-turbo

Final Decision: BLOCK

Policy Results:
🟢 ✓ No PII detected: No matches.
🟢 ✓ Response format: No schema drift detected.
🟡 ⚠ Cost: Delta +20.00%. ($0.1000 → $0.1200, +$0.0200) [🟡 WARN threshold exceeded]
🟢 ✓ Latency: No issues. (50ms → 450ms, +400ms)
🔴 ✗ Output drift: Length delta +192.31%. (52 → 152 chars) [🔴 BLOCK threshold exceeded]

Detailed Metrics:
  Cost delta %: +20.00%
  Cost delta USD: +0.020000
  Length delta %: +192.31%

Summary:
- Response length expanded: baseline 52 chars vs candidate 152 chars (192.3%, block threshold 70%).
1 additional non-blocking signal(s) detected.

Reason Codes:
  - COST_INCREASE_WARN
  - DRIFT_LENGTH_BLOCK

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ❌ BLOCK - Multiple issues: cost at WARN threshold (20%) and output drift at BLOCK (192.3%). Demonstrates how multiple policy violations aggregate.

---

### Test 10: PII Detection with Email

**Scenario:** Testing PII detection with email addresses in output.

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate test_examples/baseline_clean.json test_examples/candidate_valid_credit_card.json
```

**Actual Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 63 chars → 181 chars
  Cost: $0.5000 → $0.5200
  Latency: 120ms → 125ms
  Model: gpt-3.5-turbo → gpt-3.5-turbo

Final Decision: BLOCK

Policy Results:
🔴 ✗ No PII detected: Detected 1 match(es). [Types: EMAIL(1)]
🟢 ✓ Response format: No schema drift detected.
🟢 ✓ Cost: No issues. ($0.5000 → $0.5200, +$0.0200)
🟢 ✓ Latency: No issues. (120ms → 125ms, +5ms)
🔴 ✗ Output drift: Length delta +187.30%. (63 → 181 chars) [🔴 BLOCK threshold exceeded]

Detailed Metrics:
  Length delta %: +187.30%
  PII blocked total: 1
  PII blocked type count: 1

Summary:
- PII detected: EMAIL(1). Total matches: 1.
- Response length expanded: baseline 63 chars vs candidate 181 chars (187.3%, block threshold 70%).

Reason Codes:
  - PII_EMAIL_BLOCK
  - DRIFT_LENGTH_BLOCK

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ❌ BLOCK - PII detected (email) + output drift (187.3% expansion). Demonstrates PII detection and combined violations.

---

### Test 11: Borderline WARN Case

**Scenario:** Testing case that's just under BLOCK thresholds but exceeds WARN thresholds.

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate test_examples/baseline_borderline.json test_examples/candidate_true_borderline.json
```

**Actual Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 73 chars → 118 chars
  Cost: $1.0000 → $1.1900
  Latency: 100ms → 110ms
  Model: gpt-4 → gpt-4

Final Decision: WARN

Policy Results:
🟢 ✓ No PII detected: No matches.
🟢 ✓ Response format: No schema drift detected.
🟢 ✓ Cost: No issues. ($1.0000 → $1.1900, +$0.1900)
🟢 ✓ Latency: No issues. (100ms → 110ms, +10ms)
🟡 ⚠ Output drift: Length delta +61.64%. (73 → 118 chars) [🟡 WARN threshold exceeded]

Detailed Metrics:
  Length delta %: +61.64%

Summary:
Response length expanded: baseline 73 chars vs candidate 118 chars (61.6%, threshold 35%).

Reason Codes:
  - DRIFT_LENGTH_WARN

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ⚠️ WARN - Cost at 19% (just under 20% WARN), drift at 61.6% (WARN level, under 70% BLOCK). Demonstrates threshold boundary detection.

---

## JSON Output Example

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate examples/quickstart/baseline.json examples/quickstart/candidate_warn.json --json
```

**Actual Output:**
```json
{
  "schema_version": "1.0.0",
  "status": "WARN",
  "reasons": [
    "Cost increased by 25.0% (>=20%).",
    "Response length expanded: baseline 46 chars vs candidate 70 chars (52.2%, threshold 35%)."
  ],
  "reason_codes": [
    "COST_INCREASE_WARN",
    "DRIFT_LENGTH_WARN"
  ],
  "metrics": {
    "cost_delta_pct": 25.0,
    "cost_delta_usd": 0.25,
    "length_delta_pct": 52.1739
  },
  "metadata": {
    "strict": false,
    "mode": "lite",
    "baseline_model": "gpt-4.1-mini",
    "candidate_model": "gpt-4.1-mini"
  }
}
```

## Exit Codes (for CI Integration)

- `0` = ALLOW (safe to deploy)
- `1` = WARN (review recommended)
- `2` = BLOCK (do not deploy)

## CI Integration Example

```bash
# Fail on WARN or BLOCK
python3 -m breakpoint.cli.main evaluate baseline.json candidate.json --json --fail-on warn

# Fail only on BLOCK
python3 -m breakpoint.cli.main evaluate baseline.json candidate.json --json --fail-on block
```

## Input JSON Format

Each input file should contain:

```json
{
  "output": "The model output text (required)",
  "cost_usd": 1.0,
  "tokens_in": 5000,
  "tokens_out": 1000,
  "latency_ms": 150,
  "model": "gpt-4.1-mini"
}
```

Only `output` is required. All other fields are optional but help with policy evaluation.

## Python API Usage

```python
from breakpoint import evaluate

decision = evaluate(
    baseline_output="Hello! How can I help?",
    candidate_output="Hello! I can help with your account.",
    metadata={
        "baseline_tokens": 100,
        "candidate_tokens": 125,
        "baseline_cost_usd": 1.0,
        "candidate_cost_usd": 1.25
    }
)

print(f"Status: {decision.status}")
print(f"Reasons: {decision.reasons}")
```

## Default Policy Thresholds (Lite Mode)

- **Cost:** WARN at +20%, BLOCK at +40%
- **PII:** BLOCK on first detection (email, phone, credit card)
- **Drift:** WARN at +35% length delta, BLOCK at +70%
- **Empty output:** Always BLOCK

## Tips

1. Always test with your baseline before deploying model changes
2. Use `--json` flag for CI/CD integration
3. Use `--fail-on warn` to catch issues early in CI
4. Review WARN cases manually - they may be acceptable trade-offs
5. BLOCK cases should always be investigated before deployment

---

*Generated: $(date)*
*BreakPoint Library Version: 0.1.1*

