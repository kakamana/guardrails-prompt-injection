# Data Card — #23 Guardrails & Prompt Injection Defense

## Dataset composition
| Layer | Source | Rows | Schema |
|---|---|---|---|
| Prompt corpus | template generator (`src/prompt_guard/data.py`) | 30,000 | `prompt_id, text, is_injection, injection_type, severity` |
| Red-team set | held-out from generator | 5,000 | same schema |
| Output corpus | template generator (`src/prompt_guard/data.py`) | 5,000 | `output_id, text, is_leakage` |

## Class balance
- Benign prompts: 25,000 (83.3%)
- Injection prompts: 5,000 (16.7%)
  - `override`: 1,250
  - `role_confusion`: 1,250
  - `system_impersonation`: 1,250
  - `indirect_tool_output`: 1,250

## Field semantics
- `text` — UTF-8 prompt up to ~4,000 chars
- `is_injection` — 0 / 1
- `injection_type` — one of the four types or `none`
- `severity` — `low` / `med` / `high`

## Known biases
- Synthetic — does not capture every real-world injection variant; refresh the generator quarterly.
- English only.

## PII
None. Fully synthetic.

## Splits
- Train 16,000 + val 4,000 + held-out red-team 5,000 + extra evaluation pool 5,000.

## Reproducing
```bash
python -m prompt_guard.data
```
Deterministic with seed=42.

## Licensing
- All synthetic content is MIT (this repo).
