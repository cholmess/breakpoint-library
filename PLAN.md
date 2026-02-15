# BreakPoint Product Plan (Install-Worthy Bar)

Last updated: 2026-02-15
Owner: Christopher Holmes

## Objective

Make BreakPoint feel immediately necessary to indie developers by proving, in under 30 seconds, that it catches model/prompt regressions they would otherwise miss.

## Product Bar (Must Be True Before Publish)

- [ ] A first-time user can run one command and see at least one concrete regression signal.
- [ ] CLI output clearly answers: `What changed?`, `How bad?`, `What should I do next?`
- [ ] README leads with pain and outcome, not architecture.
- [ ] Demo includes realistic model/prompt change scenarios and returns `WARN` or `BLOCK` for clear reasons.

## Scope Guardrails

In scope:
- Local-first CLI and Python library
- Deterministic policy decisions (`ALLOW | WARN | BLOCK`)
- Opinionated defaults with minimal config
- CI-friendly behavior and stable JSON contract

Out of scope (for this phase):
- SaaS/dashboard features
- Repo-wide AI scanning
- Agentic automation loops
- Enterprise governance workflows

## Critical User Value Signals (Default Policies)

These must be surfaced by default with quantified deltas:

- [ ] Cost spike (`%` and absolute estimate)
- [ ] Output contract break (schema/format mismatch)
- [ ] PII exposure (type + count)
- [ ] Quality/content drift (summary or key-info loss proxy)
- [ ] Verbosity drift (`tokens/chars`, ratio)

## 3-Week Execution Plan

## Week 1: 30-Second Wow Output
Target dates: 2026-02-16 to 2026-02-22

### Deliverables
- [ ] CLI summary block with deterministic structure:
  - `VERDICT`
  - `Top reasons`
  - `Key deltas`
  - `Recommended action`
- [ ] High-signal text output with clear severity wording
- [ ] JSON output parity with text output (same core facts)

### Definition of done
- [ ] For identical input, output order/content is stable
- [ ] A user can scan results in <30 seconds and identify the risk
- [ ] At least one fixture produces `BLOCK` with obvious justification

## Week 2: Demo + Examples That Sell Value
Target dates: 2026-02-23 to 2026-03-01

### Deliverables
- [ ] One killer demo scenario (model swap + slight prompt tweak)
- [ ] Three realistic examples with expected outputs:
  - Example A: cost regression
  - Example B: output format regression
  - Example C: PII + verbosity drift
- [ ] Single command entry point (`make demo` or equivalent)

### Definition of done
- [ ] Fresh clone to first meaningful signal in <5 minutes
- [ ] Each example includes “why this matters in production”
- [ ] At least 2 examples produce non-`ALLOW` outcomes

## Week 3: Packaging Narrative + Publish Gate
Target dates: 2026-03-02 to 2026-03-08

### Deliverables
- [ ] README rewrite with pain-first opening
- [ ] `Try in 60 seconds` section near top
- [ ] Minimal API documentation (only what users need to ship)
- [ ] Publish checklist and release candidate validation pass

### Definition of done
- [ ] README communicates value before architecture details
- [ ] Install + run + interpret flow validated by a new user path
- [ ] Publish decision uses objective checklist below

## Publish Checklist (Hard Gate)

Do not publish until all are checked:

- [ ] Demo run shows at least one surprising/useful regression finding
- [ ] CLI output includes quantified deltas (not just generic warnings)
- [ ] JSON contract and exit codes are stable and tested
- [ ] README includes 3 copy-paste examples with expected outcomes
- [ ] No required configuration for first useful run

## Work Breakdown (Implementation)

## A. Output Experience
- [ ] Standardize reason formatting and ranking
- [ ] Add concise severity labels and thresholds in output
- [ ] Ensure final line always includes action guidance

## B. Detection Quality
- [ ] Tune thresholds to reduce noisy WARNs
- [ ] Add/validate format-break detector for common structured outputs
- [ ] Improve drift messaging from abstract to specific symptom

## C. Docs + Demo Assets
- [ ] Create realistic baseline/candidate fixture pairs
- [ ] Add before/after snippets to docs
- [ ] Keep architecture section below quickstart/value proof

## D. Verification
- [ ] Golden tests for CLI output shape and reason ordering
- [ ] Regression tests for each headline risk type
- [ ] Smoke test for quickstart command path

## Success Metrics (First 30 Days Post-Release)

- [ ] >=70% of first runs produce at least one non-trivial signal in sample/demo mode
- [ ] <=20% false-positive rate on `WARN/BLOCK` in early user feedback
- [ ] >=3 reports of “caught issue before deploy” from real users
- [ ] Median time to useful result <5 minutes

## Risks and Mitigations

- Risk: Tool feels abstract or redundant
  - Mitigation: Lead with concrete diffs and quantified impact in every example
- Risk: Too many false positives reduce trust
  - Mitigation: Tight defaults, clear calibration guidance, deterministic output
- Risk: Scope creep before adoption
  - Mitigation: Enforce publish gate and out-of-scope list

## Immediate Next Actions

- [ ] Implement Week 1 CLI output spec in code
- [ ] Build killer demo fixture set
- [ ] Rewrite README opening + `Try in 60 seconds`
- [ ] Add publish checklist status section to release process
