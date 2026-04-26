# Evaluation Plan — Guardrails & Prompt Injection Defense

## 1. Held-out red-team set
- 5,000 prompts (1,000 per injection type + 1,000 benign), carved before training.
- Never seen by classifier or canonicalizer.

## 2. Primary scorecard
| Metric | Target |
|---|---|
| Recall on injection | ≥ 0.90 |
| FPR on benign | ≤ 0.05 |
| Worst-type F1 | ≥ 0.75 |
| p95 `/check_prompt` latency | ≤ 50 ms |

## 3. Per-type confusion
Confusion matrix at the operating threshold; rows = true type, columns = predicted-injected/benign.

## 4. Threshold sweep
Plot FPR vs recall as the threshold varies; mark the chosen operating point.

## 5. Canonicalizer ablation
Compare classifier-only vs classifier+canonicalizer recall. The canonicalizer should pick up the easy case-flips and unicode tricks.

## 6. Output-classifier eval
Held-out 1,000 outputs (500 leakage + 500 benign). Targets: recall ≥ 0.85, FPR ≤ 0.05.

## 7. Latency
Measure p50 / p95 over 1,000 calls of `POST /check_prompt`.

## 8. Deployment readiness checklist
- [ ] Red-team recall ≥ 0.90
- [ ] Benign FPR ≤ 0.05
- [ ] Worst-type F1 ≥ 0.75
- [ ] `mlops/model_card.md` populated with red-team table
