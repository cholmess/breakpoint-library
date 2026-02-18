# BreakPoint Library - Detailed Test Methodology

This document explains in detail how BreakPoint tests are performed, from input JSON files to final decisions.

## Overview

BreakPoint evaluates AI model outputs by comparing a **baseline** (known good output) against a **candidate** (new output to test). It runs multiple policy checks and aggregates the results into a single decision: `ALLOW`, `WARN`, or `BLOCK`.

## Test Data Structure

### Input Format

Each test uses two JSON files:

**Baseline JSON:**
```json
{
  "output": "Hello! How can I help with your account today?",
  "cost_usd": 1.0,
  "latency_ms": 100,
  "model": "gpt-4.1-mini"
}
```

**Candidate JSON:**
```json
{
  "output": "Contact me at hi@example.com and I will follow up.",
  "cost_usd": 1.4,
  "latency_ms": 170,
  "model": "gpt-4.1-mini"
}
```

### Required vs Optional Fields

- **Required:** `output` (string) - The actual text output from the model
- **Optional but used by policies:**
  - `cost_usd` - Direct cost in USD
  - `tokens_in` / `tokens_out` - Token counts (used to calculate cost if cost_usd not provided)
  - `tokens_total` - Total tokens (alternative to tokens_in/out)
  - `latency_ms` - Response latency in milliseconds
  - `model` - Model name (used for pricing calculations)

## Evaluation Process Flow

### Step 1: Input Normalization

The CLI reads the JSON files and passes them to the `evaluate()` function:

```python
baseline_data = _read_json(baseline_path)
candidate_data = _read_json(candidate_path)

decision = evaluate(
    baseline=baseline_data,
    candidate=candidate_data,
    mode="lite",  # or "full"
    strict=False
)
```

The evaluator normalizes inputs:
- Extracts `output` field (required)
- Applies metadata overrides if provided
- Validates that both baseline and candidate have `output` fields

### Step 2: Policy Evaluation

BreakPoint runs **multiple independent policy checks** in parallel. Each policy evaluates a specific aspect of the candidate compared to the baseline.

#### Policy 1: Cost Policy (`evaluate_cost_policy`)

**Purpose:** Detects cost increases that could impact budget.

**How it works:**
1. **Resolve cost values:**
   - First tries `cost_usd` field directly
   - If not present, calculates from tokens using model pricing:
     - `cost = (tokens_in / 1000 * input_price_per_1k) + (tokens_out / 1000 * output_price_per_1k)`
   - If `tokens_total` is provided, uses: `cost = (tokens_total / 1000) * price_per_1k`

2. **Calculate delta:**
   - `delta_usd = candidate_cost - baseline_cost`
   - `increase_pct = ((candidate_cost - baseline_cost) / baseline_cost) * 100`

3. **Apply thresholds (Lite mode defaults):**
   - `WARN` if `increase_pct >= 20%`
   - `BLOCK` if `increase_pct >= 40%`

4. **Return PolicyResult:**
   - Status: `ALLOW`, `WARN`, or `BLOCK`
   - Reasons: Human-readable explanation
   - Codes: Machine-readable codes like `COST_WARN_INCREASE` or `COST_BLOCK_INCREASE`
   - Details: Metrics like `increase_pct` and `delta_usd`

**Example from Test 3 (BLOCK case):**
- Baseline: `cost_usd: 1.0`
- Candidate: `cost_usd: 1.4`
- Increase: `(1.4 - 1.0) / 1.0 * 100 = 40%`
- Result: **BLOCK** (40% >= 40% threshold)

**Example from Test 2 (WARN case):**
- Baseline: `cost_usd: 1.0`
- Candidate: `cost_usd: 1.25`
- Increase: `(1.25 - 1.0) / 1.0 * 100 = 25%`
- Result: **WARN** (25% >= 20% threshold, but < 40%)

#### Policy 2: PII Policy (`evaluate_pii_policy`)

**Purpose:** Detects Personally Identifiable Information (PII) leaks in candidate output.

**How it works:**
1. **Extract text:** Gets the `output` field from candidate
2. **Pattern matching:** Uses regex patterns to detect:
   - **EMAIL:** Pattern matches email addresses
   - **PHONE:** Pattern matches phone numbers (US format)
   - **CREDIT_CARD:** Pattern matches credit card numbers + validates with Luhn algorithm

3. **Allowlist check:** Skips matches that match allowlist patterns (for known safe values)

4. **Credit card validation:** For credit cards, validates using Luhn algorithm to avoid false positives

5. **Return PolicyResult:**
   - If any PII detected: **BLOCK** (immediate block in Lite mode)
   - Status: `BLOCK`
   - Reasons: Lists detected types and counts, e.g., "PII detected: EMAIL(1). Total matches: 1."
   - Codes: `PII_BLOCK_EMAIL`, `PII_BLOCK_PHONE`, etc.

**Example from Test 3 (BLOCK case):**
- Candidate output: `"Contact me at hi@example.com and I will follow up."`
- Pattern match: `hi@example.com` matches EMAIL pattern
- Result: **BLOCK** (PII detected: EMAIL(1))

**Example from Test 6 (PII Leak):**
- Candidate output contains: `john.doe@example.com`, `ops+oncall@example.com`, `415-555-1212`, `212-555-0100`
- Pattern matches: 2 emails, 2 phone numbers
- Result: **BLOCK** (PII detected: EMAIL(2), PHONE(2). Total matches: 4.)

#### Policy 3: Drift Policy (`evaluate_drift_policy`)

**Purpose:** Detects significant changes in output length, structure, or content similarity.

**How it works:**
1. **Extract text:** Gets `output` from both baseline and candidate
2. **Empty check:** If candidate is empty → **BLOCK** immediately
3. **Length comparison:**
   - `baseline_len = len(baseline_text)`
   - `candidate_len = len(candidate_text)`
   - `delta_pct = abs(candidate_len - baseline_len) / baseline_len * 100`
   - `short_ratio = candidate_len / baseline_len`

4. **Apply thresholds (Lite mode defaults):**
   - `WARN` if `delta_pct >= 35%`
   - `BLOCK` if `delta_pct >= 70%`
   - `WARN` if `short_ratio < 0.35` (output is 65%+ shorter)

5. **Semantic similarity (Full mode only):**
   - Calculates similarity using token Jaccard or character n-gram Jaccard
   - `WARN` if similarity < threshold (default 0.15)

6. **Return PolicyResult:**
   - Status: `ALLOW`, `WARN`, or `BLOCK`
   - Reasons: Explains direction (expanded/compressed) and percentage
   - Codes: `DRIFT_WARN_LENGTH_DELTA`, `DRIFT_BLOCK_LENGTH_DELTA`, etc.

**Example from Test 2 (WARN case):**
- Baseline: `"Hello! How can I help with your account today?"` (46 chars)
- Candidate: `"Hello! I can help. Please share your account number and issue details."` (70 chars)
- Delta: `abs(70 - 46) / 46 * 100 = 52.17%`
- Result: **WARN** (52.17% >= 35% threshold, but < 70%)

**Example from Test 5 (Format Regression):**
- Baseline: `"{\"ticket_summary\":\"...\",\"severity\":\"medium\",...}"` (140 chars)
- Candidate: `"I fixed it. Customer should try again."` (38 chars)
- Delta: `abs(38 - 140) / 140 * 100 = 72.86%`
- Result: **BLOCK** (72.86% >= 70% threshold)

**Example from Test 6 (Verbosity Drift):**
- Baseline: 140 chars
- Candidate: 401 chars
- Delta: `abs(401 - 140) / 140 * 100 = 186.43%`
- Result: **BLOCK** (186.43% >= 70% threshold)

#### Policy 4: Latency Policy (Full mode only)

**Purpose:** Detects latency increases that could impact user experience.

**How it works:**
1. Extracts `latency_ms` from both baseline and candidate
2. Calculates percentage increase
3. Applies thresholds (configurable)
4. Returns `WARN` or `BLOCK` if thresholds exceeded

#### Policy 5: Output Contract Policy (Full mode only)

**Purpose:** Validates structured output format (JSON schema, required keys, type checking).

**How it works:**
1. Parses candidate output as JSON
2. Validates against expected schema/keys
3. Checks data types match expected types
4. Returns `BLOCK` if contract violations detected

### Step 3: Policy Result Aggregation

After all policies run, the `aggregate_policy_results()` function combines them:

```python
def aggregate_policy_results(results: list[PolicyResult], strict: bool = False) -> Decision:
    has_block = any(r.status == "BLOCK" for r in results)
    has_warn = any(r.status == "WARN" for r in results)
    
    if has_block:
        status = "BLOCK"
    elif has_warn:
        status = "WARN"
    else:
        status = "ALLOW"
    
    # In strict mode, promote WARN to BLOCK
    if strict and status == "WARN":
        status = "BLOCK"
    
    # Collect all reasons and codes
    reasons = [r for result in results for r in result.reasons]
    codes = [c for result in results for c in result.codes]
    
    # Extract metrics
    metrics = _extract_metrics(details)
    
    return Decision(status=status, reasons=reasons, reason_codes=codes, metrics=metrics)
```

**Aggregation Rules:**
1. **Any BLOCK → Final decision: BLOCK**
2. **No BLOCK but any WARN → Final decision: WARN**
3. **All ALLOW → Final decision: ALLOW**
4. **Strict mode:** WARN is promoted to BLOCK

**Example from Test 3:**
- Cost policy: **BLOCK** (40% increase)
- PII policy: **BLOCK** (email detected)
- Drift policy: **ALLOW** (no significant drift)
- **Final decision: BLOCK** (because at least one policy returned BLOCK)

**Example from Test 2:**
- Cost policy: **WARN** (25% increase)
- PII policy: **ALLOW** (no PII)
- Drift policy: **WARN** (52% length increase)
- **Final decision: WARN** (no BLOCK, but has WARN)

**Example from Test 1:**
- Cost policy: **ALLOW** (1% increase, below 20% threshold)
- PII policy: **ALLOW** (no PII)
- Drift policy: **ALLOW** (minimal length change)
- **Final decision: ALLOW** (all policies passed)

### Step 4: Decision Output

The final `Decision` object contains:
- `status`: `"ALLOW"`, `"WARN"`, or `"BLOCK"`
- `reasons`: List of human-readable explanations
- `reason_codes`: Machine-readable codes (e.g., `COST_INCREASE_WARN`, `PII_BLOCK_EMAIL`)
- `metrics`: Numeric values (e.g., `cost_delta_pct: 25.0`, `length_delta_pct: 52.17`)
- `metadata`: Mode, models, strict mode, etc.

### Step 5: CLI Formatting

The CLI formats the decision for display:

**Text output (default):**
- Box-drawing header/footer
- Mode indicator
- Final decision
- Policy results with checkmarks (✓) and crosses (✗)
- Summary with specific reasons
- Exit code

**JSON output (`--json` flag):**
- Machine-readable JSON format
- Includes all decision fields
- Suitable for CI/CD parsing

## Complete Test Example Walkthrough

### Test 3: BLOCK Case - Step by Step

**Input Files:**

Baseline (`baseline.json`):
```json
{
  "output": "Hello! How can I help with your account today?",
  "cost_usd": 1.0,
  "latency_ms": 100,
  "model": "gpt-4.1-mini"
}
```

Candidate (`candidate_block.json`):
```json
{
  "output": "Contact me at hi@example.com and I will follow up.",
  "cost_usd": 1.4,
  "latency_ms": 170,
  "model": "gpt-4.1-mini"
}
```

**Evaluation Steps:**

1. **Input Normalization:**
   - Baseline: `output="Hello! How can I help with your account today?"`, `cost_usd=1.0`
   - Candidate: `output="Contact me at hi@example.com and I will follow up."`, `cost_usd=1.4`

2. **Cost Policy Evaluation:**
   - Baseline cost: `1.0`
   - Candidate cost: `1.4`
   - Increase: `(1.4 - 1.0) / 1.0 * 100 = 40%`
   - Threshold check: `40% >= 40%` → **BLOCK**
   - Result: `PolicyResult(status="BLOCK", reasons=["Cost increased by 40.0% (>=40%)."], codes=["COST_BLOCK_INCREASE"])`

3. **PII Policy Evaluation:**
   - Candidate text: `"Contact me at hi@example.com and I will follow up."`
   - Regex match: `hi@example.com` matches EMAIL pattern
   - Result: `PolicyResult(status="BLOCK", reasons=["PII detected: EMAIL(1). Total matches: 1."], codes=["PII_BLOCK_EMAIL"])`

4. **Drift Policy Evaluation:**
   - Baseline length: `46 chars`
   - Candidate length: `54 chars`
   - Delta: `abs(54 - 46) / 46 * 100 = 17.39%`
   - Threshold check: `17.39% < 35%` → **ALLOW**
   - Result: `PolicyResult(status="ALLOW")`

5. **Aggregation:**
   - Has BLOCK: `True` (cost and PII both BLOCK)
   - Final status: **BLOCK**
   - Reasons: `["Cost increased by 40.0% (>=40%).", "PII detected: EMAIL(1). Total matches: 1."]`
   - Codes: `["COST_BLOCK_INCREASE", "PII_BLOCK_EMAIL"]`
   - Metrics: `{"cost_delta_pct": 40.0, "cost_delta_usd": 0.4}`

6. **Output:**
   ```
   Final Decision: BLOCK
   Policy Results:
   ✗ No PII detected: Detected 1 match(es).
   ✗ Cost: Delta +40.00%.
   ✓ Output drift: No issues.
   Summary:
   - Cost increased by 40.0% (>=40%).
   - PII detected: EMAIL(1). Total matches: 1.
   ```

## Key Design Principles

1. **Deterministic:** Same inputs always produce same outputs
2. **Local-first:** No external API calls, all evaluation happens locally
3. **Policy-based:** Each concern (cost, PII, drift) is evaluated independently
4. **Aggregated decisions:** Multiple policy results combined into single decision
5. **Configurable thresholds:** Defaults work out of box, but can be customized
6. **Strict mode:** Can promote WARN to BLOCK for zero-tolerance environments

## Default Thresholds (Lite Mode)

- **Cost:** WARN at +20%, BLOCK at +40%
- **PII:** BLOCK on first detection (any email, phone, or credit card)
- **Drift:** WARN at +35% length delta, BLOCK at +70%
- **Empty output:** Always BLOCK

## Exit Codes

- `0` = ALLOW (safe to deploy)
- `1` = WARN (review recommended)
- `2` = BLOCK (do not deploy)

These exit codes enable CI/CD integration where the pipeline can fail automatically on risky changes.

---

*This methodology ensures BreakPoint catches production risks before deployment while remaining fast, local, and deterministic.*

