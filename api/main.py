"""FastAPI for the guardrails project.

Endpoints:
    GET  /health
    POST /check_prompt   - classify an incoming user prompt
    POST /check_output   - classify a model output for leakage

Vendor-neutral: this stack sits in front of any hosted endpoint
(e.g. GPT-4o-mini, Mistral-Large, Llama-3-Instruct).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Guardrails - Prompt Injection Defense", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DISCLAIMER = (
    "Defense-in-depth: pair this guardrail with vendor-side controls "
    "and red-team refresh. No single layer is sufficient on its own."
)


class PromptIn(BaseModel):
    text: str = Field(..., max_length=10000)


class PromptOut(BaseModel):
    safe: bool
    injection_detected: bool
    injection_type: str
    severity: str
    canonicalized_text: str
    score: float
    disclaimer: str = DISCLAIMER


class OutputIn(BaseModel):
    text: str = Field(..., max_length=10000)


class OutputOut(BaseModel):
    safe: bool
    leakage_detected: bool
    score: float
    disclaimer: str = DISCLAIMER


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/check_prompt", response_model=PromptOut)
def check_prompt(p: PromptIn) -> PromptOut:
    try:
        from src.prompt_guard.serve import check_prompt as _check  # type: ignore
    except Exception:
        from prompt_guard.serve import check_prompt as _check
    res = _check(p.text)
    return PromptOut(
        safe=not bool(res["is_injection"]),
        injection_detected=bool(res["is_injection"]),
        injection_type=res["injection_type"],
        severity=res["severity"],
        canonicalized_text=res["canonicalized"],
        score=res["score"],
    )


@app.post("/check_output", response_model=OutputOut)
def check_output(o: OutputIn) -> OutputOut:
    try:
        from src.prompt_guard.serve import check_output as _check  # type: ignore
    except Exception:
        from prompt_guard.serve import check_output as _check
    res = _check(o.text)
    return OutputOut(
        safe=bool(res["safe"]),
        leakage_detected=bool(res["leakage_detected"]),
        score=res["score"],
    )
