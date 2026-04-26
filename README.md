# Guardrails & Prompt Injection Defense

> **Catch the "ignore previous instructions" attack before it reaches the model — and prove it on a 5,000-row red-team set.** A TF-IDF + logistic-regression input classifier, canonicalization rules, and an output classifier wired into a FastAPI service with a UI scoreboard.

![Python](https://img.shields.io/badge/python-3.11-blue) ![scikit-learn](https://img.shields.io/badge/sklearn-1.4-orange) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688) ![Made in Dubai](https://img.shields.io/badge/made%20in-Dubai-black)

## Why this project
- Every team building on hosted endpoints (e.g. GPT-4o-mini, Mistral-Large, Llama-3-Instruct) faces the same concrete risk: **prompt injection**. The fix is not a single model — it's a stack: classifier → canonicalizer → output filter → red-team eval.
- This project ships that stack as production-shaped code with a notebook fallback that runs in Dataiku DSS (no external API calls).
- **30,000 prompt corpus**, 5,000 of which are injection attempts (template-generated across "ignore previous instructions", role-confusion, system-impersonation, indirect injection via tool-output mimicry).

## Table of contents
- [Business Requirements](./docs/01_business_requirements.md)
- [Feasibility Study](./docs/02_feasibility_study.md)
- [Methodology — Classifier + canonicalizer + red-team](./docs/03_methodology.md)
- [Evaluation Plan](./docs/04_evaluation.md)
- [Data card](./data/data_card.md) · [Data sources](./data/data_sources.md)
- [Notebooks](./notebooks/) · [Source](./src/prompt_guard/) · [API](./api/main.py) · [UI](./ui/app/page.tsx)
- [CLAUDE.md](./CLAUDE.md) — paste prompt to resume in this folder

## Headline results (target)

| Metric | Naive keyword filter | Our stack | Target |
|---|---|---|---|
| Injection recall (red-team) | 0.62 | **0.93** | ≥ 0.90 |
| False-positive rate (benign) | 0.18 | **0.04** | ≤ 0.05 |
| F1 by injection type (worst) | 0.41 | **0.81** | ≥ 0.75 |
| p95 `/check_prompt` latency | – | **< 25 ms** | < 50 ms |

## Quickstart
```bash
pip install -e ".[dev]"
python -m prompt_guard.data           # writes 30k prompts + 5k red-team set
jupyter lab notebooks/
uvicorn api.main:app --reload
cd ui && npm install && npm run dev
```

## Stack
Python · pandas · scikit-learn · FastAPI · Next.js · Tailwind · joblib · matplotlib · seaborn

## Author
Asad — MADS @ University of Michigan · Dubai HR
