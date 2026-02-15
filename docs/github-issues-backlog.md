# GitHub Issue Backlog (Install-Worthy Release)

Last updated: 2026-02-15
Source plan: `PLAN.md`

## How to use

1. Create issues top-to-bottom (P0 first).
2. Add labels exactly as listed.
3. Link dependencies in GitHub using `blocked by #<issue>`.
4. Track release readiness against the hard gate in `PLAN.md`.

## Priority Order

- P0: #1, #2, #3, #4
- P1: #5, #6, #7
- P2: #8, #9, #10

---

## 1) P0: Redesign CLI Output for 30-Second Scan

- Suggested title: `CLI: add deterministic 30-second verdict summary`
- Labels: `priority:P0`, `area:cli`, `type:feature`, `release:install-worthy`
- Depends on: none
- Blocks: #2, #9

### Issue body

Problem
Current output can feel technical but not immediately actionable. First-time users need instant clarity.

Scope
- Add a fixed summary layout in text output:
  - `VERDICT`
  - `Top reasons`
  - `Key deltas`
  - `Recommended action`
- Ensure stable ordering of reasons and deltas.
- Keep concise format as default.

Acceptance criteria
- Same input always produces same output ordering.
- User can identify main risk and next action in under 30 seconds.
- Output includes at least one quantified delta when non-`ALLOW`.

---

## 2) P0: Quantified Delta Rendering in CLI + JSON

- Suggested title: `Engine/CLI: surface quantified deltas for all triggered policies`
- Labels: `priority:P0`, `area:engine`, `area:cli`, `type:feature`
- Depends on: #1
- Blocks: #7, #8

### Issue body

Problem
Generic warnings do not create trust. Users need concrete numbers.

Scope
- Ensure all default policy triggers include measurable deltas where possible.
- Align text and JSON output facts.
- Add metadata fields needed for display without breaking schema contract.

Acceptance criteria
- Cost: percent and absolute estimate when available.
- Drift/verbosity: ratio or percent change.
- PII: type and count.
- JSON output contains same core facts shown in text output.

---

## 3) P0: Demo Fixture Set (Killer + 3 Realistic Examples)

- Suggested title: `Examples: add killer demo and 3 production-like regression scenarios`
- Labels: `priority:P0`, `area:examples`, `type:feature`, `type:docs`
- Depends on: none
- Blocks: #4, #5

### Issue body

Problem
Value is still abstract without believable regressions.

Scope
- Add fixture sets for:
  - A: cost regression
  - B: output format regression
  - C: PII + verbosity drift
- Add one killer scenario where candidate looks better but introduces critical tradeoffs.

Acceptance criteria
- At least two scenarios return non-`ALLOW`.
- Example files are runnable directly with existing CLI.
- Scenarios are deterministic and documented.

---

## 4) P0: One-Command Demo Entrypoint

- Suggested title: `DX: add one-command demo path (<5 min to first signal)`
- Labels: `priority:P0`, `area:dx`, `area:examples`, `type:feature`
- Depends on: #3
- Blocks: #5

### Issue body

Problem
If setup takes too long, users churn before seeing value.

Scope
- Add `make demo` (or equivalent script) to run baseline vs candidate scenarios.
- Print clear expectation of likely `ALLOW/WARN/BLOCK` outcomes.
- Include quick troubleshooting hints for common failures.

Acceptance criteria
- Fresh clone to meaningful result in <5 minutes.
- Command succeeds without extra configuration.
- Demo output visibly includes concrete regression findings.

---

## 5) P1: README Rewrite (Pain-First + 60-Second Trial)

- Suggested title: `Docs: rewrite README to lead with pain and immediate outcome`
- Labels: `priority:P1`, `area:docs`, `type:docs`, `release:install-worthy`
- Depends on: #3, #4
- Blocks: #10

### Issue body

Problem
Architecture-first docs reduce adoption; users buy outcomes.

Scope
- New opening focused on model/prompt regression pain.
- Add `Try in 60 seconds` near top.
- Include 3 copy-paste examples with expected outcomes.
- Move architecture details below quickstart and examples.

Acceptance criteria
- README communicates user value before implementation details.
- New users can run first example without reading additional docs.
- All commands in README verified in CI/tests or manual smoke check.

---

## 6) P1: Format/Schema Break Detection Hardening

- Suggested title: `Policy: strengthen output contract break detection`
- Labels: `priority:P1`, `area:policy`, `type:feature`, `type:quality`
- Depends on: #2
- Blocks: #8

### Issue body

Problem
Structured output regressions are a high-cost failure mode and must be obvious.

Scope
- Improve detection for common format failures (invalid JSON, missing required keys, type mismatches where applicable).
- Improve reason text from vague drift language to specific contract failures.

Acceptance criteria
- Fixture for format break consistently triggers `WARN/BLOCK` per thresholds.
- Reason output names the exact contract failure symptom.

---

## 7) P1: Threshold Tuning for Trust (False Positive Reduction)

- Suggested title: `Calibration: tune default thresholds to reduce noisy WARN/BLOCK`
- Labels: `priority:P1`, `area:policy`, `type:quality`
- Depends on: #2
- Blocks: #10

### Issue body

Problem
Noisy warnings erode trust and reduce long-term adoption.

Scope
- Review default thresholds for cost, drift, latency, and verbosity.
- Adjust defaults and document rationale.
- Validate with fixture suite and existing tests.

Acceptance criteria
- Threshold changes are documented and deterministic.
- Demonstrable reduction in low-signal warnings on provided examples.

---

## 8) P2: Golden Tests for Output Contract and Ordering

- Suggested title: `Tests: add golden snapshots for CLI structure and reason ordering`
- Labels: `priority:P2`, `area:test`, `type:test`
- Depends on: #2, #6
- Blocks: #10

### Issue body

Problem
Output regressions can silently break user trust and CI parsing.

Scope
- Add golden tests for text output structure.
- Add assertions for deterministic ordering of reasons.
- Keep snapshots resilient to irrelevant formatting changes where possible.

Acceptance criteria
- Snapshot/golden tests catch structural regressions.
- Deterministic ordering covered by automated tests.

---

## 9) P2: Action Guidance Standardization

- Suggested title: `CLI: standardize final recommended action line`
- Labels: `priority:P2`, `area:cli`, `type:feature`
- Depends on: #1
- Blocks: #10

### Issue body

Problem
Users should never wonder what to do after seeing a verdict.

Scope
- Add a consistent final action line for each status:
  - `ALLOW`: safe to ship
  - `WARN`: ship with review
  - `BLOCK`: stop deploy and investigate

Acceptance criteria
- Final action line appears in every evaluation output.
- Wording is concise, deterministic, and status-specific.

---

## 10) P2: Release Gate Audit Issue

- Suggested title: `Release: install-worthy hard gate audit`
- Labels: `priority:P2`, `area:release`, `type:process`, `release:install-worthy`
- Depends on: #5, #7, #8, #9
- Blocks: publish

### Issue body

Problem
Publishing without strict criteria risks a weak first impression.

Scope
- Audit against `PLAN.md` publish checklist.
- Record pass/fail evidence links (tests, screenshots, docs, demo output).
- Decide `go/no-go` for release.

Acceptance criteria
- Every hard-gate checkbox in `PLAN.md` is explicitly marked pass/fail.
- `go/no-go` decision documented with evidence.

---

## Milestone Suggestion

- Milestone: `Install-Worthy v0.x`
- Target date: 2026-03-08

## Label Set Suggestion

- `priority:P0`, `priority:P1`, `priority:P2`
- `area:cli`, `area:engine`, `area:policy`, `area:examples`, `area:docs`, `area:test`, `area:release`, `area:dx`
- `type:feature`, `type:docs`, `type:test`, `type:quality`, `type:process`
- `release:install-worthy`
