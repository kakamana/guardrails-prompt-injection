# Model Card — Guardrail Stack (input + canonicalizer + output)

## Intended use
Defense-in-depth layer that sits in front of any hosted language-model endpoint (e.g. GPT-4o-mini, Mistral-Large, Llama-3-Instruct). Flags injection-shaped inputs and leakage-shaped outputs.

## Training data
30,000 synthetic prompts (25,000 benign + 5,000 injection across four types) + 5,000 outputs for the leakage classifier. See `data/data_card.md`.

## Model family
- **Input classifier (notebook fallback):** TF-IDF (char 3-5 + word 1-2) + sklearn `LogisticRegression`.
- **Canonicalizer:** deterministic Python rules.
- **Output classifier:** TF-IDF + sklearn `LogisticRegression`.
- **Production swap-in:** small distilled encoder for the input classifier.

## Metrics (held-out red-team, to be filled)
| Metric | Target |
|--------|--------|
| Recall on injection | ≥ 0.90 |
| FPR on benign | ≤ 0.05 |
| Worst-type F1 | ≥ 0.75 |
| p95 `/check_prompt` latency | ≤ 50 ms |

## Limitations
- Synthetic training data — refresh red-team monthly.
- English only.
- The classifier sees the canonical form; sufficiently obfuscated inputs may bypass it.

## Ethical considerations
- Disclaimer on every API response.
- Block decisions are auditable per request (canonical text + score + type returned).

## Retraining
- Monthly + after every red-team refresh.

## Ownership
- DS lead: Asad
