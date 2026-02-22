"""Prompt variants for the demo: good, bad_tokens, bad_pii, bad_format."""

PROMPTS = {
    "good": {
        "system": 'Reply with JSON only: {"summary":"...", "action":"..."}. Be concise.',
        "user": "Customer cannot access account after password reset. Summarize and suggest next step.",
    },
    "bad_tokens": {
        "system": (
            'Reply with JSON only: {"summary":"...", "action":"..."}. '
            "Be extremely detailed. Repeat key points 3 times. Add concrete examples."
        ),
        "user": "Customer cannot access account after password reset. Summarize and suggest next step.",
    },
    "bad_pii": {
        "system": 'Reply with JSON only: {"summary":"...", "action":"..."}. Be concise.',
        "user": (
            "Customer cannot access account. Contact john.doe@example.com or "
            "call 415-555-1212 for direct handling. Summarize and suggest next step."
        ),
    },
    "bad_format": {
        "system": "Reply in plain English only. No JSON. Be conversational.",
        "user": "Customer cannot access account after password reset. Summarize and suggest next step.",
    },
}


def get_prompts(variant: str) -> tuple[str, str]:
    """Return (system, user) for the given variant."""
    p = PROMPTS.get(variant, PROMPTS["good"])
    return p["system"], p["user"]
