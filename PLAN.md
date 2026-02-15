# BreakPoint Strategic Plan (Lite vs Full)

Last updated: 2026-02-15
Owner: Christopher Holmes
Status: Finalized strategic decisions captured

## Core Positioning

BreakPoint is a local decision engine that tells developers whether an AI change is safe to ship.

- Lite mode is the default, zero-friction safety layer.
- Full mode is the advanced policy and CI enforcement layer.
- Use one command surface: `breakpoint evaluate`.
- Activate advanced behavior with `--mode full`.

## Finalized Decisions

### 1) Lite Overrides

- Lite allows one-shot CLI overrides only.
- No persistent waivers in Lite.
- No saved config edits in Lite.
- Override must be explicit and named, e.g. `--accept-risk cost`.

### 2) Full-Only Features (Day 1)

- Persistent waivers.
- Presets and environments.
- Strict mode via config.
- Output contract enforcement.
- Latency policy.
- Custom pricing models.

### 3) Strict Mode Behavior

- Lite: allow `--strict` as a single explicit flag.
- Full: supports config-based strict enforcement.

### 4) Override Logging in Lite

- Print override reason to terminal only.
- No file logging or audit trail in Lite.

### 5) Lite Default Thresholds

- Cost: `WARN >= +20%`, `BLOCK >= +40%`.
- PII: `BLOCK` on first detection (email, credit card, phone).
- Drift: `WARN >= +35% length delta`, `BLOCK >= +70% length delta`.
- Empty output: always `BLOCK`.

### 6) Drift Scope

- Lite includes basic drift only (length + structure).
- Semantic/embedding drift is reserved for paid tier.

### 7) Paid Tier Sequencing

- First monetizable capability: semantic drift (embedding-based).
- Second: stronger PII detection (ML-based).
- Third: CI reporting and structured reports.

### 8) Command Surface

- Keep a single command surface: `breakpoint evaluate`.
- Advanced capabilities exposed via `--mode full`.
- No separate advanced subcommand.

### 9) 30-Day KPI Priority

1. Installs
2. Active usage
3. Repeated usage
4. CI adoption
5. Override rate

### 10) README Positioning

- Lead with: Lite works out of the box.
- Present advanced capabilities as optional.
- Avoid enterprise-heavy positioning.
- Emphasize clarity, determinism, and trust.

## Mode Boundary Matrix

- Lite includes:
  - Cost policy with fixed defaults
  - PII detection (regex baseline)
  - Basic drift (length + structure)
  - `--strict` flag
  - One-shot explicit risk acceptance
- Lite excludes:
  - Presets/environments
  - Waivers
  - Output contract policy
  - Latency policy
  - Custom pricing models
  - Persistent policy edits
- Full includes:
  - Config-driven policy activation and thresholds
  - Waivers, presets, environments
  - Strict config behavior
  - Output contract and latency policies
  - Custom pricing models

## Implementation Plan

## Phase 1: Policy and CLI Boundary Enforcement

- [x] Add mode-aware policy loading so Lite only evaluates cost/pii/basic_drift.
- [x] Gate Full-only flags/options behind `--mode full` with clear errors.
- [x] Add/confirm `--accept-risk <named-risk>` behavior for Lite one-shot overrides.
- [x] Add/confirm `--strict` in Lite as non-persistent behavior.
- [x] Ensure no Lite path writes waiver/config artifacts.

## Phase 2: Threshold Alignment

- [x] Update Lite cost thresholds to `WARN +20`, `BLOCK +40`.
- [x] Update Lite drift thresholds to `WARN +35`, `BLOCK +70`.
- [x] Enforce Lite empty-output `BLOCK`.
- [x] Enforce Lite PII immediate `BLOCK` on first email/phone/credit card match.

## Phase 3: UX and Messaging

- [x] Show explicit mode in CLI output (`Mode: lite|full`).
- [x] Show explicit override acknowledgment in terminal output when used.
- [x] Ensure decision summary language stays deterministic and calm.
- [x] Keep Full mode visible but secondary in README and quickstart.

## Phase 4: Validation and Release Readiness

- [x] Add tests for Lite/Full feature gating.
- [x] Add tests for finalized Lite thresholds and empty-output block rule.
- [x] Add tests for `--accept-risk` explicit naming and one-shot behavior.
- [x] Add tests proving no persistent artifacts in Lite override flow.
- [x] Add test coverage for `--strict` in Lite and config strict in Full.

## KPI Instrumentation Plan (30 Days)

- [x] Track installs (ingest local installs snapshot with package downloads + GitHub clone/watch proxy into `metrics summarize`).
- [x] Track active usage (decision artifact totals via `metrics summarize`).
- [x] Track repeated usage (project-key based repeat-project counts).
- [x] Track CI adoption (auto-tagged `ci` metadata and CI decision totals).
- [x] Track override rate and accepted risk types.

## Paid Value Proposition

- Prevent hidden cost explosions.
- Prevent embarrassing production mistakes.
- Provide higher-confidence shipping decisions through deeper intelligence.
