"""Inference helpers used by the FastAPI layer."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib

from .features import canonicalize


MODEL_DIR = Path(__file__).resolve().parents[2] / "models"


@lru_cache(maxsize=1)
def _load_artifacts() -> dict:
    return dict(
        input=joblib.load(MODEL_DIR / "input_clf.pkl"),
        output=joblib.load(MODEL_DIR / "output_clf.pkl"),
    )


# Lightweight rule-based classifier used as a stub when model artifacts are absent.
_QUICK_INJECTION_HINTS = [
    "ignore previous", "disregard", "forget what", "override your",
    "you are now", "system:", "<system>", "<tool_output>",
    "reveal the system", "dump all", "act as if", "pretend you are",
]


def _rule_based_check(text: str) -> dict:
    canon = canonicalize(text)
    matches = [p for p in _QUICK_INJECTION_HINTS if p in canon]
    is_inj = bool(matches)
    if "system" in canon and "directive" in canon:
        itype = "system_impersonation"
    elif "tool_output" in canon:
        itype = "indirect_tool_output"
    elif "you are now" in canon or "pretend" in canon:
        itype = "role_confusion"
    elif is_inj:
        itype = "override"
    else:
        itype = "none"
    severity = "high" if is_inj and itype != "role_confusion" else ("med" if is_inj else "none")
    return dict(
        is_injection=int(is_inj),
        injection_type=itype,
        severity=severity,
        canonicalized=canon,
        score=float(min(1.0, 0.5 + 0.1 * len(matches))) if is_inj else 0.0,
    )


def check_prompt(text: str, threshold: float = 0.5) -> dict:
    canon = canonicalize(text)
    try:
        art = _load_artifacts()
    except Exception:
        return _rule_based_check(text)
    proba = float(art["input"].predict_proba([canon])[0, 1])
    is_inj = int(proba >= threshold)
    # heuristic injection_type tagging from canonical patterns
    itype = "none"
    if is_inj:
        if "tool_output" in canon:
            itype = "indirect_tool_output"
        elif "canon_role_marker" in canon or "canon_role_tag" in canon:
            itype = "system_impersonation"
        elif "you are now" in canon or "pretend" in canon or "act as if" in canon:
            itype = "role_confusion"
        else:
            itype = "override"
    severity = "high" if (is_inj and itype != "role_confusion") else ("med" if is_inj else "none")
    return dict(
        is_injection=is_inj,
        injection_type=itype,
        severity=severity,
        canonicalized=canon,
        score=proba,
    )


def check_output(text: str, threshold: float = 0.5) -> dict:
    try:
        art = _load_artifacts()
    except Exception:
        leaky = any(s in text.lower() for s in [
            "system prompt", "secret token", "credentials", "ignore safety", "uploaded file",
        ])
        return dict(safe=int(not leaky), leakage_detected=int(leaky), score=1.0 if leaky else 0.0)
    proba = float(art["output"].predict_proba([text])[0, 1])
    leakage = int(proba >= threshold)
    return dict(safe=int(not leakage), leakage_detected=leakage, score=proba)
