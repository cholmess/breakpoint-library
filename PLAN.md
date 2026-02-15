# BreakPoint Product Plan (Install-Worthy Bar)

Last updated: 2026-02-15
Owner: Christopher Holmes

## Objective

Make BreakPoint feel immediately necessary to indie developers by proving, in under 30 seconds, that it catches model/prompt regressions they would otherwise miss.

## Product Bar (Must Be True Before Publish)

- [x] A first-time user can run one command and see at least one concrete regression signal.
- [x] CLI output clearly answers: `What changed?`, `How bad?`, `What should I do next?`
- [x] README leads with pain and outcome, not architecture.
- [x] Demo includes realistic model/prompt change scenarios and returns `WARN` or `BLOCK` for clear reasons.

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

- [x] Cost spike (`%` and absolute estimate)
- [x] Output contract break (schema/format mismatch)
- [x] PII exposure (type + count)
- [x] Quality/content drift (summary or key-info loss proxy)
- [x] Verbosity drift (`tokens/chars`, ratio)

## 3-Week Execution Plan

## Week 1: 30-Second Wow Output
Target dates: 2026-02-16 to 2026-02-22

### Deliverables
- [x] CLI summary block with deterministic structure:
  - `Final Decision`
  - `Policy Results`
  - `Summary`
  - `Exit Code`
- [x] High-signal text output with clear severity wording
- [x] JSON output parity with text output (same core facts)

### Definition of done
- [x] For identical input, output order/content is stable
- [x] A user can scan results in <30 seconds and identify the risk
- [x] At least one fixture produces `BLOCK` with obvious justification

## Week 2: Demo + Examples That Sell Value
Target dates: 2026-02-23 to 2026-03-01

### Deliverables
- [x] One killer demo scenario (model swap + slight prompt tweak)
- [x] Three realistic examples with expected outputs:
  - Example A: cost regression
  - Example B: output format regression
  - Example C: PII + verbosity drift
- [x] Single command entry point (`make demo` or equivalent)

### Definition of done
- [x] Fresh clone to first meaningful signal in <5 minutes
- [x] Each example includes “why this matters in production”
- [x] At least 2 examples produce non-`ALLOW` outcomes

## Week 3: Packaging Narrative + Publish Gate
Target dates: 2026-03-02 to 2026-03-08

### Deliverables
- [x] README rewrite with pain-first opening
- [x] `Try in 60 seconds` section near top
- [x] Minimal API documentation (only what users need to ship)
- [x] Publish checklist and release candidate validation pass

### Definition of done
- [x] README communicates value before architecture details
- [x] Install + run + interpret flow validated by a new user path
- [x] Publish decision uses objective checklist below

## Publish Checklist (Hard Gate)

Do not publish until all are checked:

- [x] Demo run shows at least one surprising/useful regression finding
- [x] CLI output includes quantified deltas (not just generic warnings)
- [x] JSON contract and exit codes are stable and tested
- [x] README includes 3 copy-paste examples with expected outcomes
- [x] No required configuration for first useful run

## Work Breakdown (Implementation)

## A. Output Experience
- [x] Standardize reason formatting and ranking
- [x] Add concise severity labels and thresholds in output
- [x] Ensure final line always includes action guidance

## B. Detection Quality
- [x] Tune thresholds to reduce noisy WARNs
- [x] Add/validate format-break detector for common structured outputs
- [x] Improve drift messaging from abstract to specific symptom

## C. Docs + Demo Assets
- [x] Create realistic baseline/candidate fixture pairs
- [x] Add before/after snippets to docs
- [x] Keep architecture section below quickstart/value proof

## D. Verification
- [x] Golden tests for CLI output shape and reason ordering
- [x] Regression tests for each headline risk type
- [x] Smoke test for quickstart command path

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

- [ ] Cut and push `v0.2.0-rc2` tag
- [ ] Publish release notes for `v0.2.0-rc2`
- [ ] Run one external-user validation pass (fresh clone feedback)
