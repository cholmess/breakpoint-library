# Terminal Output: Lite vs Full (Same Language)

This page shows the **same** output format for both modes so we’re aligned. The only difference is how many policy lines appear.

**Same command shape, same sections:** Command → Actual Output (header, Mode, Input Comparison, Final Decision, Policy Results, Summary, Exit Code).  
**Lite** = 3 policy lines (PII, Cost, Output drift).  
**Full** = 5 policy lines (PII, **Response format**, Cost, **Latency**, Output drift).

---

## Lite mode (default)

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate examples/quickstart/baseline.json examples/quickstart/candidate_allow.json
```

**Actual Output:**
```text
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
✓ No PII detected: No matches.
✓ Cost: No issues.
✓ Output drift: No issues.

Summary:
No risky deltas detected against configured policies.

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ✓ ALLOW – Safe to deploy

In Lite, **Response format** and **Latency** are not evaluated, so they do not appear in Policy Results.

---

## Full mode

**Command:**
```bash
python3 -m breakpoint.cli.main evaluate examples/quickstart/baseline.json examples/quickstart/candidate_allow.json --mode full
```

**Actual Output:**
```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: full

Input Comparison:
  Output Length: 46 chars → 46 chars
  Cost: $1.0000 → $1.0100
  Latency: 100ms → 102ms
  Model: gpt-4.1-mini → gpt-4.1-mini

Final Decision: ALLOW

Policy Results:
✓ No PII detected: No matches.
✓ Response format: No schema drift detected.
✓ Cost: No issues.
✓ Latency: No issues.
✓ Output drift: No issues.

Summary:
No risky deltas detected against configured policies.

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result:** ✓ ALLOW – Safe to deploy

In Full, **Response format** (output contract) and **Latency** are evaluated and shown as two extra lines.

---

## Summary

| Section           | Lite | Full |
|------------------|------|------|
| Mode             | `lite` | `full` |
| Input Comparison | Same | Same |
| Final Decision   | Same | Same |
| **Policy Results** | **3 lines**: PII, Cost, Drift | **5 lines**: PII, Response format, Cost, Latency, Drift |
| Summary          | Same | Same |
| Exit Code        | Same | Same |

So: same structure and wording; the only visible difference is **3 vs 5 policy lines** and the Mode label.
