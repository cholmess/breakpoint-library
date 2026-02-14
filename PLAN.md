# BreakPoint — Phase 1 Build Plan
Goal: Ship a simple, local-first decision engine for indie AI developers.

---

## 🎯 Mission (Phase 1)

Build a lightweight Python library that:

- Compares baseline vs candidate LLM outputs
- Applies simple, deterministic policies
- Returns: ALLOW | WARN | BLOCK
- Runs fully locally
- Has near-zero friction
- Is installable via pip

We are NOT building:
- Cloud dashboards
- Enterprise governance
- Codebase AI scanning
- Complex evaluation frameworks
- AI agents that analyze entire repos

---

## 🧠 Core API (MVP)

```python
from breakpoint import evaluate

decision = evaluate(
    baseline_output=baseline,
    candidate_output=candidate,
    metadata={
        "baseline_tokens": 1200,
        "candidate_tokens": 1500
    }
)

print(decision.status)   # ALLOW | WARN | BLOCK
print(decision.reasons)
```

---

## 🏗 Architecture

breakpoint/
│
├── engine/
│   ├── evaluator.py
│   ├── aggregator.py
│   └── policies/
│       ├── cost.py
│       ├── pii.py
│       ├── drift.py
│       ├── latency.py
│
├── models/
│   └── decision.py
│
├── cli/
│   └── main.py
│
├── config/
│   └── default_policies.json
│
└── __init__.py

---

## 📌 Policies (Phase 1 Scope)

### 1️⃣ Cost Policy
- Cost increase > 20% → WARN
- Cost increase > 35% → BLOCK

### 2️⃣ PII Policy
Detect via regex:
- Email addresses
- Phone numbers
- Credit card patterns
- SSN patterns

If detected → BLOCK

### 3️⃣ Output Drift Policy
Heuristic checks:
- Length delta %
- Empty output
- Extremely short vs baseline
- Basic semantic similarity (optional)

Large drift → WARN

### 4️⃣ Latency Policy
- Latency increase > 30% → WARN
- Latency increase > 60% → BLOCK

---

## 🔀 Aggregation Rules

BLOCK > WARN > ALLOW

- Any BLOCK → Final status = BLOCK
- Any WARN → Final status = WARN
- Otherwise → ALLOW

---

## 🖥 CLI (Minimal)

breakpoint evaluate baseline.json candidate.json

Output example:

STATUS: WARN
- Cost increased by 24%
- Output drift detected

Optional flags:
--strict
--config custom_policy.json

---

## 🚀 Milestones

### Week 1–2
- Implement policy engine
- Implement aggregator
- Build evaluate() interface
- Create Decision object model

### Week 3
- Add CLI
- Add config support
- Add structured output formatting

### Week 4
- Write documentation
- Add examples
- Publish GitHub alpha

### Week 5–6
- Publish to PyPI
- Announce publicly
- Collect feedback

---

## 📊 Metrics to Track

- GitHub stars
- pip installs
- Active usage examples
- Issues filed
- Feature requests

---

## 🧠 Phase 2 (Only If Adoption)

- Cost simulation at traffic scale
- Multi-model disagreement detection
- CI enforcement flag
- Policy presets

---

## 🎯 Positioning

BreakPoint is:

A local decision engine for AI builders.
Compare changes. Catch risk. Ship with confidence.

---

Keep it small.
Keep it deterministic.
Ship fast.
