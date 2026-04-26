"""Train + persist input/output classifiers for the guardrail stack.

Run as:
    python -m prompt_guard.models
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score, recall_score
from sklearn.pipeline import Pipeline

from .data import PROCESSED, write_all
from .features import build_input_pipeline, build_output_pipeline, canonicalize

MODEL_DIR = Path(__file__).resolve().parents[2] / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def make_input_clf(C: float = 2.0) -> Pipeline:
    return Pipeline(steps=[
        ("features", build_input_pipeline()),
        ("clf", LogisticRegression(
            C=C, class_weight="balanced", max_iter=1000, solver="liblinear",
        )),
    ])


def make_output_clf(C: float = 2.0) -> Pipeline:
    return Pipeline(steps=[
        ("features", build_output_pipeline()),
        ("clf", LogisticRegression(
            C=C, class_weight="balanced", max_iter=1000, solver="liblinear",
        )),
    ])


def train_input_classifier(prompts: pd.DataFrame) -> Pipeline:
    texts = prompts["text"].apply(canonicalize).tolist()
    y = prompts["is_injection"].values
    model = make_input_clf()
    model.fit(texts, y)
    return model


def train_output_classifier(outputs: pd.DataFrame) -> Pipeline:
    texts = outputs["text"].tolist()
    y = outputs["is_leakage"].values
    model = make_output_clf()
    model.fit(texts, y)
    return model


def evaluate_input(model: Pipeline, redteam: pd.DataFrame, threshold: float = 0.5) -> dict:
    texts = redteam["text"].apply(canonicalize).tolist()
    proba = model.predict_proba(texts)[:, 1]
    preds = (proba >= threshold).astype(int)
    y = redteam["is_injection"].values
    out = dict(
        threshold=threshold,
        recall_injection=float(recall_score(y, preds, pos_label=1)),
        f1_injection=float(f1_score(y, preds, pos_label=1)),
        fpr_benign=float(((preds == 1) & (y == 0)).sum() / max((y == 0).sum(), 1)),
        report=classification_report(y, preds, output_dict=True),
    )
    # Per-injection-type breakdown
    types = redteam["injection_type"].values
    per_type = {}
    for itype in np.unique(types):
        if itype == "none":
            continue
        mask = types == itype
        per_type[itype] = float(recall_score(y[mask], preds[mask], pos_label=1, zero_division=0))
    out["per_type_recall"] = per_type
    return out


def save(obj, name: str) -> Path:
    p = MODEL_DIR / name
    joblib.dump(obj, p)
    return p


def load(name: str):
    return joblib.load(MODEL_DIR / name)


def run_full_pipeline() -> dict:
    counts = write_all()
    train = pd.read_parquet(PROCESSED / "prompts_train.parquet")
    redteam = pd.read_parquet(PROCESSED / "redteam.parquet")
    outputs = pd.read_parquet(PROCESSED / "outputs.parquet")

    inp = train_input_classifier(train)
    save(inp, "input_clf.pkl")

    out = train_output_classifier(outputs)
    save(out, "output_clf.pkl")

    inp_eval = evaluate_input(inp, redteam, threshold=0.5)
    return dict(counts=counts, input_eval=inp_eval)


if __name__ == "__main__":
    summary = run_full_pipeline()
    e = summary["input_eval"]
    print(
        f"recall={e['recall_injection']:.3f} "
        f"f1_inj={e['f1_injection']:.3f} "
        f"fpr_benign={e['fpr_benign']:.3f}"
    )
    print("per-type:", e["per_type_recall"])
