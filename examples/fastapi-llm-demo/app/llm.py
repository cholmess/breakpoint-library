"""LLM call wrapper using Ollama HTTP API (or OpenAI fallback)."""

import os
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# Nominal rates for cost estimation (demo only)
INPUT_RATE = 1e-5  # per token
OUTPUT_RATE = 3e-5  # per token


def call_ollama(system: str, user: str, model: str = DEFAULT_MODEL) -> dict:
    """Call Ollama /api/generate (non-streaming). Returns artifact dict."""
    try:
        import requests
    except ImportError:
        raise ImportError("Install requests: pip install requests")

    url = f"{OLLAMA_URL.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": user,
        "system": system,
        "stream": False,
    }
    start = time.perf_counter()
    resp = requests.post(url, json=payload, timeout=120)
    latency_ms = int((time.perf_counter() - start) * 1000)
    resp.raise_for_status()
    data = resp.json()

    response_text = data.get("response", "")
    prompt_eval_count = data.get("prompt_eval_count") or 0
    eval_count = data.get("eval_count") or 0

    cost_usd = (prompt_eval_count * INPUT_RATE) + (eval_count * OUTPUT_RATE)
    return {
        "output": response_text,
        "tokens_in": prompt_eval_count,
        "tokens_out": eval_count,
        "cost_usd": round(cost_usd, 4),
        "latency_ms": latency_ms,
        "model": model,
    }


def call_llm(prompt_variant: str, user_message: str | None = None, model: str = DEFAULT_MODEL) -> dict:
    """
    Call LLM with the given prompt variant.
    Returns dict with output, tokens_in, tokens_out, cost_usd, latency_ms, model.
    """
    from .prompts import get_prompts

    system, default_user = get_prompts(prompt_variant)
    user = user_message if user_message is not None else default_user

    if os.getenv("OPENAI_API_KEY"):
        return _call_openai(system, user, model)
    return call_ollama(system, user, model)


def _call_openai(system: str, user: str, model: str) -> dict:
    """Fallback: call OpenAI if OPENAI_API_KEY is set."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Install openai: pip install openai")

    client = OpenAI()
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model=model or "gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    latency_ms = int((time.perf_counter() - start) * 1000)
    msg = resp.choices[0].message
    usage = resp.usage
    tokens_in = usage.prompt_tokens if usage else 0
    tokens_out = usage.completion_tokens if usage else 0
    cost_usd = (tokens_in * INPUT_RATE) + (tokens_out * OUTPUT_RATE)
    return {
        "output": msg.content or "",
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost_usd, 4),
        "latency_ms": latency_ms,
        "model": model or "gpt-4o-mini",
    }
