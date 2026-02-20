# Adapting BreakPoint to a Real Use Case

This guide explains how to use BreakPoint in your real pipeline (not just the demo): from generating baseline and candidate to integrating it in CI or in code.

## 1. What You Need to Define

- **Baseline**: the “known good” output from your current model (in prod or the one you’ve approved).
- **Candidate**: the output from the new model (prompt change, model change, or parameter change) that you want to validate before deploying.

BreakPoint compares both and returns `ALLOW` / `WARN` / `BLOCK`.

## 2. JSON Format

Each record (baseline or candidate) is a JSON object with at least `output` and, if you want cost/latency policies, optional metrics:

```json
{
  "output": "The text returned by the model.",
  "cost_usd": 0.02,
  "tokens_in": 1000,
  "tokens_out": 500,
  "tokens_total": 1500,
  "latency_ms": 1200,
  "model": "gpt-4.1-mini"
}
```

- **Minimum**: `{"output": "..."}`.
- **Recommended in production**: include `cost_usd`, `tokens_*`, and `latency_ms` so cost and latency policies don’t WARN on missing data.

## 3. How to Get Baseline and Candidate in Real Life

### Option A: From Your Code (LLM Call)

After calling your model, build the object and pass it to BreakPoint via the API or save it as JSON.

Conceptual example:

```python
import json
from pathlib import Path
from breakpoint import evaluate

# Your real function that calls the LLM
def call_my_llm(prompt: str, model: str) -> dict:
    # ... your OpenAI / Anthropic / etc. client ...
    response = client.chat.completions.create(model=model, messages=[...])
    usage = response.usage
    return {
        "output": response.choices[0].message.content,
        "tokens_in": usage.prompt_tokens,
        "tokens_out": usage.completion_tokens,
        "tokens_total": usage.total_tokens,
        "latency_ms": response_elapsed_ms,  # if you measure it
        "model": model,
        "cost_usd": your_cost_function(usage),  # if you compute it
    }

# 1) Baseline: once you approve the current output, save it
baseline = call_my_llm("Summarize this ticket", "gpt-4.1-mini")
Path("baselines/support-bot/baseline.json").write_text(
    json.dumps(baseline, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

# 2) Candidate: in CI or before deploy, generate the new output
candidate = call_my_llm("Summarize this ticket", "gpt-4.1-nano")  # new model

# 3) Evaluate with the API
decision = evaluate(baseline=baseline, candidate=candidate)
print(decision.status, decision.reason_codes)
if decision.status != "ALLOW":
    raise SystemExit(2)  # or 1 for WARN
```

Here “real use case” means: same prompt (or set of representative prompts), baseline = approved output, candidate = output from the new model/config.

### Option B: CLI with Files (e.g. in CI)

1. **Create/update the baseline** when you approve a behavior (manually or via script).
2. **On each PR or before deploy**: your pipeline generates the candidate (script that calls the LLM and writes `candidate.json`).
3. **Run BreakPoint**:

```bash
breakpoint evaluate baselines/support-bot/baseline.json candidate.json --json --fail-on warn
```

Use the exit code (0/1/2) to fail the build or deploy.

## 4. Where to Store the Baseline

- **Versioned folder** (recommended): e.g. `baselines/<flow>/baseline.json` or dated `baseline-2026-02-15.json`.
- **One baseline per flow** (e.g. “support-bot”, “summarizer”) so the comparison is stable.
- When you intentionally change behavior, **update the baseline** (new file or agreed replacement) and get it approved (review; see `docs/baseline-lifecycle.md`).

That way in a real use case you always compare “last approved version” vs “new candidate”.

## 5. CI Integration (GitHub Actions)

Copy and adapt `examples/ci/github-actions-breakpoint.yml`:

1. **Generate the candidate** in a previous step (script that calls your LLM and writes `candidate.json`).
2. **Point the env vars** to your repo’s baseline and candidate:

```yaml
env:
  BREAKPOINT_BASELINE: baselines/support-bot/baseline.json
  BREAKPOINT_CANDIDATE: candidate.json   # generated in the previous step
  BREAKPOINT_FAIL_ON: warn
  BREAKPOINT_OUTPUT: breakpoint-decision.json
```

3. The “Run BreakPoint gate” step already uses `breakpoint evaluate ... --json --fail-on $BREAKPOINT_FAIL_ON` and the exit code to fail the job.

In a real use case, the “candidate” should be the actual output of your model in that pipeline (same prompt/inputs you define for the gate).

## 6. Using the API in Your Application

You can call BreakPoint from your code without writing files:

```python
from breakpoint import evaluate

# With objects already loaded (e.g. from your LLM)
decision = evaluate(
    baseline={"output": "...", "cost_usd": 0.02, "tokens_total": 100},
    candidate={"output": "...", "cost_usd": 0.03, "tokens_total": 140},
)
if decision.status == "BLOCK":
    raise ValueError("Candidate blocked:", decision.reasons)
```

Or with just text and metadata (BreakPoint fills baseline/candidate internally):

```python
decision = evaluate(
    baseline_output="approved response",
    candidate_output="new response",
    metadata={"baseline_tokens": 100, "candidate_tokens": 140},
)
```

Useful when you already have baseline and candidate in memory (tests, validation script, internal service).

## 7. Quick Summary for a Real Use Case

| Step | Action |
|------|--------|
| 1 | Define one or more “flows” (e.g. a prompt or set of representative prompts). |
| 2 | Generate and save a baseline per flow (approved output + metrics if you use them). |
| 3 | On each change (model, prompt, params), generate the candidate with the same input. |
| 4 | Evaluate: `breakpoint evaluate baseline.json candidate.json --json --fail-on warn` or `evaluate(baseline=..., candidate=...)`. |
| 5 | If ALLOW → you can deploy. If WARN/BLOCK → review and, if intentional, update the baseline with an approval process. |

With this you can use BreakPoint in a real use case: same data schema, stable baseline per flow, candidate generated by your pipeline, and CI or API to block risky deployments.
