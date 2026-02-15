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

## ✅ Adoption Readiness Addendum (Phase 1)

Goal: Make BreakPoint usable in real pipelines, not just technically complete.

### P0 (Must-have for real adoption)
- Stable JSON output contract with schema versioning
- Clear exit codes for CI usage (`0=ALLOW`, `1=WARN`, `2=BLOCK`)
- End-to-end quickstart (baseline/candidate generation + evaluation)
- Baseline governance (how to create, refresh, and version snapshots)
- Policy calibration controls (threshold overrides per project/environment)

#### P0 Execution Backlog (Start Here)

P0-1 — Decision Contract v1
- Deliverable: `Decision` JSON schema v1 with fixed fields (`schema_version`, `status`, `reasons`, `reason_codes`, `metrics`, `metadata`)
- Definition of Done:
  - CLI/API output is deterministic for identical input
  - `schema_version` is required and documented
  - Invalid payloads fail with actionable error messages

P0-2 — CI Gate Behavior
- Deliverable: standard exit code mapping + configurable failure policy (`--fail-on warn|block`)
- Definition of Done:
  - Exit codes are stable and tested
  - Docs include copy-paste CI usage examples
  - WARN/BLOCK behavior is explicit in both text and JSON outputs

P0-3 — Baseline Lifecycle
- Deliverable: baseline spec (`baseline.json`) + update policy (when to refresh, who approves, rollback path)
- Definition of Done:
  - Baseline file format is documented and versioned
  - Team can reproduce decision results from a stored baseline
  - Rollback procedure is documented and tested with sample data

P0-4 — Policy Calibration
- Deliverable: project-level threshold overrides in config (`cost`, `latency`, `drift`, `pii`)
- Definition of Done:
  - Overrides work per environment (`dev`, `staging`, `prod`)
  - Default policy remains safe when no config is provided
  - Misconfigured thresholds fail fast with clear validation errors

P0-5 — 10-Minute Quickstart
- Deliverable: one runnable path from install to first BLOCK in under 10 minutes
- Definition of Done:
  - Includes sample baseline/candidate files
  - Shows both CLI and Python API usage
  - Includes expected outputs and troubleshooting section

#### P0 Sequence (Recommended)
1. P0-1 Decision Contract v1
2. P0-2 CI Gate Behavior
3. P0-4 Policy Calibration
4. P0-3 Baseline Lifecycle
5. P0-5 10-Minute Quickstart

#### Current Sprint Focus
- Completed: P0-1 Decision Contract v1
- Completed: P0-2 CI Gate Behavior
- Completed: P0-3 Baseline Lifecycle
- Completed: P0-4 Policy Calibration
- Completed: P0-5 10-Minute Quickstart
- Next focus: P1 CI templates and waivers

### P1 (High-value after P0)
- Built-in CI templates (GitHub Actions + generic shell example)
- Waivers/suppressions with expiration and reason
- Value metrics beyond vanity metrics (false-positive rate, prevented bad deploys)
- Policy presets by use case (chatbot, support, extraction)

### Delivery Plan (Weeks 1–6)

#### Week 1–2 (Core + Contracts)
- Implement `Decision` schema with `schema_version`, `status`, `reasons`, and machine-readable reason codes
- Define deterministic reason code taxonomy (ex: `COST_INCREASE_WARN`, `PII_EMAIL_BLOCK`)
- Add strict input validation for required metadata per policy

#### Week 3 (CLI + Pipeline Integration)
- Add `--output json` and `--output text` modes
- Add deterministic exit codes for CI/CD gates
- Add `--fail-on warn|block` behavior for team policy preferences

#### Week 4 (Onboarding + Baseline Ops)
- Publish 10-minute quickstart with reproducible sample data
- Add baseline lifecycle guide: create, approve, refresh cadence, rollback baseline
- Document threshold tuning playbook to reduce false positives

#### Week 5–6 (Adoption Loop)
- Ship CI examples (GitHub Actions + generic shell)
- Add waiver mechanism with expiry and audit fields
- Track adoption value metrics in docs/examples and collect structured feedback from alpha users

---

## 📊 Metrics to Track

- GitHub stars
- pip installs
- Active usage examples
- Issues filed
- Feature requests
- False-positive rate
- BLOCK decisions later confirmed as true positives
- Time-to-decision inside CI runs

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
