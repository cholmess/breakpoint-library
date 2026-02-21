# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.9] - 2026-02-22

### Added
- Zero-friction echo example in README (no pre-built JSON needed)
- Baseline definition for first-time users
- Tests/CI badge in README
- PyPI long description with explicit markdown content-type

## [0.1.8] - 2026-02-22

### Added
- `breakpoint --version` CLI flag
- Recommended action line in text output (Safe to ship / Ship with review / Stop deploy and investigate)
- CI workflow for tests and demo smoke (.github/workflows/test.yml)
- Dev dependencies: pytest-cov, ruff

### Changed
- .gitignore: dist/, *.egg-info/, build artifacts

## [0.1.7] - 2025-02-21

### Added
- LICENSE (MIT)
- CHANGELOG.md
- PyPI classifiers and keywords
- README badges (PyPI, License)
- Feedback CTA for first-time users
- Troubleshooting section in README

## [0.1.6] - 2025-02-21

### Added
- GitHub Action for CI/CD integration
- Lite mode (default): zero-config cost, PII, and drift detection
- Full mode: config-driven policies, output contract, latency checks, presets
- Pytest plugin for LLM output stability testing
- Python API for programmatic evaluation
- CLI with JSON output support for CI integration
- Comprehensive documentation and examples

### Features
- Cost regression detection (WARN at +20%, BLOCK at +40%)
- PII detection (email, phone, credit card, SSN)
- Output drift detection using semantic similarity
- Output contract validation (Full mode)
- Latency monitoring (Full mode)
- Policy presets for common use cases
- Environment-aware configuration
- Waiver support for controlled exceptions
