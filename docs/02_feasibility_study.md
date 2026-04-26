# Feasibility Study — Guardrails & Prompt Injection Defense

## 1. Data feasibility
- **30,000 prompts total**, of which **5,000 are injection attempts** (~17%).
- Templates per attack type (override / role-confusion / system-impersonation / indirect-via-tool-output) keep the synthetic data realistic and the train/test split clean.
- Schema: `prompt_id, text, is_injection, injection_type, severity`.
- A separate **red-team test set** carved out before training: 5,000 prompts (1,000 per injection type + 1,000 benign).
- No external scraping; no PII; deterministic with seed=42.

## 2. Technical feasibility
- **Production stack:**
  - Input classifier — small transformer (e.g. distilled encoder)
  - Canonicalization — regex + role-marker stripping + whitespace normalization
  - Output classifier — secrets / role-leak detector
  - Red-team set + CI gate
- **Notebook fallback (Dataiku-compatible):**
  - Input classifier — TF-IDF (1-3 char n-grams + 1-2 word n-grams) + sklearn `LogisticRegression`
  - Canonicalization — pure-Python rule set (lowercase, normalize whitespace, strip role markers)
  - Output classifier — TF-IDF + sklearn `LogisticRegression`
- **Compute:** runs on a single CPU; full training in under 60 seconds.

## 3. Economic feasibility
| Line item | Monthly cost |
|-----------|--------------|
| 1× small container (API + UI) | ~$8 |
| Storage | ~$1 |
| **Total** | **~$9 / mo** |

Value: a single successful injection that exfiltrates a system prompt or a customer record can trigger a public incident response — many multiples of the guardrail's annual cost.

## 4. Operational feasibility
- **Retraining:** monthly + after every red-team refresh.
- **Monitoring:** PSI on attack-type distribution; per-type recall trend; FPR alarm.
- **Human-in-the-loop:** every blocked request stores its `injection_type` and `severity` so the security lead can spot-check.

## 5. Ethical / legal feasibility
- All synthetic; no PII.
- Disclaimer on every response — the guardrail is a defense-in-depth layer, not a sole control.

## 6. Recommendation
**Go.** The fallback stack is provable, the cost is trivial, and the red-team set is the primary deliverable for any security review.
