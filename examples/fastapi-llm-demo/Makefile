.PHONY: install good bad-tokens bad-pii bad-format demo-all show-cost-diff

DEMO_DIR := $(dir $(lastword $(MAKEFILE_LIST)))
BASELINE := app/baselines/baseline.json

install:
	@if [ -f ../../pyproject.toml ]; then \
		pip install -e ../..; \
		pip install requests fastapi uvicorn; \
	else \
		pip install -r requirements.txt; \
	fi

good:
	@breakpoint evaluate $(BASELINE) candidates/good.json

bad-tokens:
	@breakpoint evaluate $(BASELINE) candidates/bad_tokens.json

bad-pii:
	@breakpoint evaluate $(BASELINE) candidates/bad_pii.json

bad-format:
	@breakpoint evaluate $(BASELINE) candidates/bad_format.json

show-cost-diff:
	@echo "--- good (baseline) vs bad_tokens ---"
	@echo 'Baseline: tokens_out ~1000, cost $$0.045'
	@echo 'Bad:      tokens_out 1700, cost $$0.076 (+68%)'
	@echo
	@echo "Same output text, but verbose prompt → cost spike → BLOCK"

demo-all: good bad-tokens bad-pii bad-format
