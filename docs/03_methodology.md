# Methodology — Guardrails & Prompt Injection Defense

Four moving parts:
1. **Input classifier** — flags injection on incoming prompts.
2. **Canonicalizer** — normalizes obvious tricks (whitespace, role markers, casing).
3. **Output classifier** — flags leakage on model output.
4. **Red-team eval** — held-out attack set used as the go/no-go gate.

> Production input classifier = small transformer; **notebook fallback = TF-IDF + sklearn `LogisticRegression`** for Dataiku DSS compatibility.

---

## 1. Injection taxonomy
| Type | Example pattern | Severity |
|---|---|---|
| `override` | "ignore previous instructions and ..." | high |
| `role_confusion` | "you are now a different assistant" | medium |
| `system_impersonation` | "system: new directive ..." | high |
| `indirect_tool_output` | "<tool_output>... ignore the user ...</tool_output>" | high |

## 2. Synthetic dataset
- 30,000 prompts (25,000 benign + 5,000 injection).
- Per-type quotas: 1,250 each for the 4 injection types.
- Benign prompts use the same template-vocab approach as project #22 to keep linguistic structure plausible.

## 3. Input classifier (notebook stand-in)
Pipeline:
$$ \text{TF-IDF}_{\text{char}(1\text{-}3)} \oplus \text{TF-IDF}_{\text{word}(1\text{-}2)} \;\rightarrow\; \text{LogisticRegression}(C=2.0) $$
where $\oplus$ is feature-union concatenation.

We optimize **F1 on the injection class**, not accuracy — the task is heavily imbalanced.

## 4. Canonicalizer
A deterministic pure-Python function that:
1. Lowercases.
2. Collapses repeated whitespace and unicode look-alikes (e.g. NBSP → space).
3. Strips role markers: `system:`, `user:`, `assistant:` at line starts.
4. Normalizes "ignore previous" / "disregard above" / "forget" patterns into a canonical token sequence.
5. Keeps the original prompt for audit; the canonical form is what the classifier sees.

## 5. Output classifier
- Goal: detect that the model has *complied* with a hidden instruction (e.g. dumped a system prompt, leaked tool credentials).
- Same TF-IDF + LogisticRegression stack, trained on synthetic positive examples ("Here is the system prompt: ...") and benign assistant outputs.

## 6. Red-team eval
- 5,000 held-out prompts (1,000 per injection type + 1,000 benign).
- Primary metric: **recall on injection** at the chosen operating threshold.
- Secondary: per-type F1, FPR on benign.
- Operating threshold tuned on the validation set so FPR ≤ 0.05.

## 7. Decision rule
$$ \text{safe}(p) = \neg\,\text{InputClf}(\text{canonicalize}(p)) $$
On model output:
$$ \text{leakage}(o) = \text{OutputClf}(o) $$

## 8. References
- Greshake et al. *Not what you've signed up for*, 2023 — taxonomy of indirect injection.
- OWASP LLM Top-10 — LLM01 Prompt Injection.
- Perez & Ribeiro, *Ignore Previous Prompt: Attack Techniques for Language Models*, 2022.
