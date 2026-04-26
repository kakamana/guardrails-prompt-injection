# Business Requirements — Guardrails & Prompt Injection Defense

## 1. Problem Statement
Any application that forwards user text into a hosted language-model endpoint (e.g. GPT-4o-mini, Mistral-Large, Llama-3-Instruct) is vulnerable to **prompt injection** — a class of attacks where the user supplies content designed to override the system instructions ("ignore previous instructions and ..."), impersonate a privileged role ("system: you are now ..."), or smuggle instructions through tool output. We need a **guardrail stack**: an input classifier that flags injection, canonicalization rules that normalize obvious tricks, an output classifier that catches leakage, and a red-team eval that proves the stack actually works.

## 2. Stakeholders
| Role | Interest | Success criterion |
|------|----------|-------------------|
| Application engineer | Drop-in safety layer | < 50 ms p95, vendor-neutral |
| Security lead | Provable defense | Red-team recall ≥ 0.90 |
| Product manager | Low false-positive friction | FPR ≤ 0.05 on benign traffic |
| Compliance | Audit trail per blocked request | Decision + reason returned by API |

## 3. Business Objectives
1. **Catch ≥ 90% of injection attempts** on a held-out 5,000-prompt red-team set.
2. **False-positive rate ≤ 5%** on benign traffic.
3. **Per-injection-type recall ≥ 0.75** for every attack family (so one family doesn't quietly slip through).
4. **Sub-50 ms p95** so the guardrail can sit in front of every model call without budget pain.

## 4. KPIs
| KPI | Definition | Target | Baseline |
|-----|-----------|--------|----------|
| Injection recall | TP / (TP + FN) on red-team | ≥ 0.90 | 0.62 |
| FPR on benign | FP / (FP + TN) | ≤ 0.05 | 0.18 |
| Worst-case per-type F1 | min over injection types | ≥ 0.75 | 0.41 |
| p95 latency | `/check_prompt` | ≤ 50 ms | – |

## 5. Scope
**In scope:** English text prompts up to 4,000 characters; injection types covered by the synthetic generator (override, role-confusion, system-impersonation, indirect-via-tool-output).
**Out of scope:** multi-modal payloads, multilingual injection, fine-tuned vendor-specific bypasses (those need vendor evals).

## 6. Constraints & Assumptions
- **Vendor-neutral** stack — no dependency on a specific endpoint.
- **Notebook fallback** must run in Dataiku DSS (no external API calls).
- **Decision-aid disclaimer** included on every API response.

## 7. Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Novel injection family slips past classifier | High | High | Monthly red-team refresh; PSI on attack-type distribution |
| Over-blocking benign creative prompts | Medium | High | FPR gate in CI; per-type confusion matrix in model card |
| Canonicalization corrupts legitimate text | Low | Medium | Reversible canonicalization; original text retained |
| Output-leakage classifier misses subtle exfiltration | Medium | High | Pair with vendor-side rate limits + secrets-scrubber |
