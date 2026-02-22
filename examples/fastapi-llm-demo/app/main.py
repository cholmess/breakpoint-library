"""FastAPI app with /chat endpoint (optional for demo)."""

from fastapi import FastAPI
from pydantic import BaseModel

from .llm import call_llm

app = FastAPI(title="BreakPoint Demo", description="LLM chat endpoint for demo")


class ChatRequest(BaseModel):
    prompt_variant: str = "good"
    message: str | None = None


@app.post("/chat")
def chat(req: ChatRequest):
    """Call LLM and return artifact (output, tokens, cost, etc.)."""
    result = call_llm(req.prompt_variant, req.message)
    return result
