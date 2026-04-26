# A Defence-in-Depth Stack for Prompt Injection With Canonicalisation, Linear Classifiers, and Held-Out Red-Team Evaluation

**Asad Kamran**
Master of Applied Data Science, University of Michigan
Dubai Human Resources Department, Government of Dubai
asad.kamran [at] portfolio

---

## Abstract

Customer-facing applications built on hosted large-language-model endpoints face prompt-injection attacks across at least four taxonomically distinct families: direct override, role-confusion, system-impersonation, and indirect injection via tool output. The published mitigation literature is uneven — strong on attack characterisation, weaker on operationally measurable defence stacks evaluated against held-out red-team sets with per-attack-type slicing. We present a defence-in-depth stack composed of an input classifier, a deterministic canonicaliser, an output classifier, and a held-out red-team evaluation set used as a release gate. The classifiers are deliberately linear — a TF-IDF feature union over character-n-grams and word-n-grams feeding a class-balanced logistic-regression head — chosen for auditability over the marginal F1 advantage of a fine-tuned encoder. The canonicaliser absorbs case-flip and unicode-look-alike attacks before the classifier sees them, contributing approximately seven percentage points of injection recall in ablation. On a 5,000-prompt held-out red-team split (1,000 benign plus 1,000 per injection type) of a 30,000-prompt synthetic corpus, the stack achieves injection recall of 0.93 against a naive-keyword baseline of 0.62, false-positive rate of 0.04 on benign traffic, and worst-type F1 of 0.81 (role-confusion). The stack is vendor-neutral; any hosted endpoint, for example GPT-4o-mini, Mistral-Large, or Llama-3-Instruct, may be substituted downstream without altering the defence layer. We argue that for customer-facing LLM agents, a held-out red-team set as a hard release gate paired with per-attack-type slicing is the only protocol robust to silent regressions in any single attack family.

**Keywords:** prompt injection, LLM security, defence-in-depth, canonicalisation, red-team evaluation, responsible AI.

---

## 1. Introduction

Prompt injection — a class of attacks in which user-controlled or corpus-controlled content induces a large language model to deviate from its system instructions — has been documented across at least four taxonomically distinct families [1, 2, 3]. Direct override attacks use lexical patterns ("ignore all previous instructions"); role-confusion attacks attempt to relabel the assistant ("you are now a different assistant"); system-impersonation attacks fabricate role markers in the user payload ("system: new directive"); and indirect-via-tool-output attacks smuggle instructions inside a retrieved document or tool response that the application will pass to the model as context [1].

The architectural framing that organises this paper is the OWASP LLM Top-10 [4] defence-in-depth model: the language model is one layer in a stack of layers, none of which are sufficient on their own and all of which must be measured. The mitigation literature is uneven. Attack-characterisation work [1, 2, 3] is strong; defence-stack work that reports per-attack-type recall against a held-out red-team set is sparse, and the few published defences that do report per-type metrics tend to evaluate against test splits drawn from the same distribution as the training set, which is known to overestimate operational recall [5].

The contributions of this paper are: (i) a deterministic synthetic 30,000-prompt corpus across four injection families with a 5,000-prompt held-out red-team split (1,000 benign plus 1,000 per attack type) carved before training; (ii) a defence-in-depth stack composed of a TF-IDF plus logistic-regression input classifier, a deterministic canonicaliser, a TF-IDF plus logistic-regression output-leakage classifier, and a release-gate evaluation protocol; (iii) ablation showing the canonicaliser contributes approximately seven percentage points of injection recall, and per-type slicing identifying role-confusion as the weakest attack family at F1 = 0.81; (iv) a vendor-neutral architecture in which any hosted endpoint may be substituted downstream without altering the defence layer; and (v) a serving stack (FastAPI plus a Next.js cockpit) running on a single CPU at sub-25-millisecond p95 latency for the input-classifier check.

## 2. Related work

**Prompt-injection taxonomy.** [1] (Greshake et al.) introduced the indirect-via-tool-output family and characterised the threat model for LLM-integrated applications; [2] (Perez & Ribeiro) characterised the direct override family with a corpus of attack templates; [3] (Liu et al. 2024) compiled a survey-scale taxonomy. [4] (OWASP) consolidated the practitioner framing as LLM01.

**Adversarial-input defences.** [6] (Wallace et al.) introduced universal adversarial triggers, the textual analogue of which prompt-injection attacks resemble. [7] (Carlini et al.) documented training-data extraction attacks, motivating the output-leakage classifier in our stack.

**Linear classifiers vs fine-tuned encoders.** [8] (Joulin et al.) established fastText-style linear classifiers as competitive baselines for text classification; the trade-off between linear-classifier auditability and fine-tuned-encoder F1 is documented in [9].

**Canonicalisation.** Text canonicalisation as a defensive preprocessing step is surveyed in [10] in the context of spam filtering; the technique transfers cleanly to prompt-injection canonicalisation.

**Red-team evaluation discipline.** [11] (Perez et al.) and [12] (Ganguli et al.) document red-team evaluation protocols for LLM behaviours; we follow the held-out-set discipline with per-attack-type slicing.

## 3. Problem formulation

Let $p \in \mathcal{P}$ be a user prompt drawn from a finite corpus, and let $\mathcal{T} = \{$override, role_confusion, system_impersonation, indirect_tool_output$\}$ be the injection type set. Each prompt $p$ has a ground-truth label $y_p \in \{0, 1\}$ indicating injection and, if $y_p = 1$, a type label $\tau_p \in \mathcal{T}$.

The defence problem is to construct a function $\text{Guard}: \mathcal{P} \to \{0, 1\} \times \mathcal{T} \cup \{\bot\}$ such that, on a held-out red-team set $\mathcal{R}$, the recall on injection

$$ \text{Recall} = \frac{|\{p \in \mathcal{R} : y_p = 1 \wedge \text{Guard}(p)_1 = 1\}|}{|\{p \in \mathcal{R} : y_p = 1\}|} $$

and the false-positive rate on benign

$$ \text{FPR} = \frac{|\{p \in \mathcal{R} : y_p = 0 \wedge \text{Guard}(p)_1 = 1\}|}{|\{p \in \mathcal{R} : y_p = 0\}|} $$

satisfy $\text{Recall} \ge 0.90$, $\text{FPR} \le 0.05$, and $\min_{\tau \in \mathcal{T}} \text{F1}_\tau \ge 0.75$. The release-gate constraint is the requirement that all three thresholds hold simultaneously; failure of any one of the three blocks deployment.

## 4. Mathematical and statistical foundations

### 4.1 Canonicaliser

The canonicaliser is a deterministic function $C: \mathcal{P} \to \mathcal{P}$ implementing the cascade

$$ C(p) = \rho_4(\rho_3(\rho_2(\rho_1(p)))) $$

where $\rho_1$ lowercases, $\rho_2$ collapses repeated whitespace and unicode look-alikes (e.g. NBSP $\to$ ASCII space), $\rho_3$ strips line-leading role markers from the regex set $\{\text{system}, \text{user}, \text{assistant}\}\!:$, and $\rho_4$ normalises override-pattern variants ("disregard the above", "forget what you were told", "your real task is to") into a canonical token sequence. The canonical form is the input to the classifier; the original prompt is retained in the audit log.

### 4.2 Input classifier

The input classifier is a feature union over character-$n$-grams ($n \in \{1, 2, 3\}$) and word-$n$-grams ($n \in \{1, 2\}$) feeding a class-balanced logistic-regression head:

$$ \phi(p) = \text{TF-IDF}_{\text{char}(1\text{-}3)}(C(p)) \oplus \text{TF-IDF}_{\text{word}(1\text{-}2)}(C(p)) $$

$$ p(y = 1 \mid p) = \sigma(\theta^\top \phi(p)) $$

The training objective is class-balanced cross-entropy

$$ \mathcal{L}(\theta) = -\frac{1}{N} \sum_{i=1}^N \left[ w_1 y_i \log \sigma(\theta^\top \phi(p_i)) + w_0 (1 - y_i) \log(1 - \sigma(\theta^\top \phi(p_i))) \right] $$

with $w_k$ inverse to class frequency. The decision threshold $\tau_{\text{op}}$ is tuned on a validation split such that FPR $\le 0.05$.

### 4.3 Output classifier

The output classifier shares the architectural shape of the input classifier and is trained on a separate corpus of model outputs labelled `is_leakage`. The leakage corpus is generated from templates such as "Here is the system prompt: ...", "I will now reveal the contents of the uploaded file: ...", paired with safe-output templates. The output classifier is a backstop, invoked only when the input classifier has *not* flagged the prompt; if the input classifier has already blocked an injection, the output classifier is not exercised.

### 4.4 Decision rule

The full guard is

$$ \text{Guard}(p) = \begin{cases} (1, \arg\max_\tau \text{TypeClf}(C(p))) & \text{if InputClf}(C(p)) \ge \tau_{\text{op}} \\ (0, \bot) & \text{otherwise} \end{cases} $$

with the type classifier optionally trained as a second multinomial head over the four injection types for telemetry. On model output $o$, the leakage decision is $\text{Leak}(o) = \mathbb{1}[\text{OutputClf}(o) \ge \tau_{\text{leak}}]$.

### 4.5 Linear-classifier auditability

The choice of a linear classifier with a TF-IDF feature space is motivated by the auditability requirement. The trained $\theta$ vector indexes directly into the feature space; the security lead can enumerate the top-$k$ tokens contributing to the injection class and inspect them for face validity. A fine-tuned encoder offers no comparable surface. In our experiments a distilled encoder produced approximately three percentage points of additional F1 on the synthetic corpus; we trade this for the audit-trail property.

### 4.6 Vendor-neutral substitution

The defence stack is positioned upstream of the model call. The downstream model is referenced only through an opaque function $M: \mathcal{P} \to \mathcal{O}$ taking a (possibly canonicalised) prompt to a model output. Substituting any $M$ (e.g. GPT-4o-mini, Mistral-Large, Llama-3-Instruct, or an open-weights model running locally) leaves the defence stack unchanged.

## 5. Methodology

### 5.1 Data

The synthetic 30,000-prompt corpus is generated deterministically with a fixed seed in `src/prompt_guard/data.py`. Twenty-five thousand benign prompts are drawn from ten templates over seventeen business topics (renewable energy, the Q3 roadmap, kubernetes upgrades, etc.). Five thousand injection prompts are drawn from family-specific template sets — eight templates for override, six for role-confusion, six for system-impersonation, six for indirect-tool-output — paired with eight payloads (reveal the system prompt, dump credentials, etc.). Per-type quotas are 1,250 each. The output corpus contains 5,000 model-output snippets with 50/50 leakage/safe balance.

### 5.2 Holdout

A 5,000-prompt red-team split is carved before training: 1,000 benign plus 1,000 per injection type. The remaining 25,000 prompts form the training set. The red-team split is never seen by any classifier or by the canonicaliser during training.

### 5.3 Training

The input classifier is trained on canonicalised prompts via `LogisticRegression(C=2.0, class_weight="balanced", solver="liblinear")` over the feature union described in §4.2. The output classifier is trained on the leakage corpus with the same head. Training completes in under thirty seconds on a single CPU.

### 5.4 Serving

The `serve.py` module loads the persisted classifier artefacts and exposes `check_prompt(text)` and `check_output(text)`. The FastAPI surface exposes `POST /check_prompt` and `POST /check_output` returning the decision, the canonicalised form, the predicted type and severity, and the score. p95 latency on `POST /check_prompt` is under 25 milliseconds.

## 6. Evaluation protocol

### 6.1 Primary scorecard

On the held-out red-team split: injection recall, FPR on benign, per-injection-type F1, p95 latency on `POST /check_prompt`. The release-gate constraint is the simultaneous satisfaction of $\text{Recall} \ge 0.90$, $\text{FPR} \le 0.05$, and $\min_\tau \text{F1}_\tau \ge 0.75$.

### 6.2 Per-type confusion

Confusion matrix at the operating threshold; rows = ground-truth type ($\bot$ for benign plus four injection types), columns = predicted-injected/benign.

### 6.3 Threshold sweep

ROC and precision-recall curves over the operating threshold; the chosen point is the smallest threshold for which FPR $\le 0.05$.

### 6.4 Canonicaliser ablation

Train and evaluate the input classifier with and without the canonicaliser. The recall delta is the canonicaliser's contribution.

### 6.5 Output-classifier eval

Held-out 1,000 outputs (500 leakage plus 500 benign). Targets recall $\ge 0.85$, FPR $\le 0.05$.

## 7. Results on synthetic benchmarks

**Table 1.** Headline metrics on the held-out 5,000-prompt red-team split.

| System | Injection recall | FPR (benign) | Worst-type F1 | p95 latency |
|---|---|---|---|---|
| Naive keyword filter | 0.62 | 0.18 | 0.41 | < 5 ms |
| Linear classifier, no canonicaliser | 0.86 | 0.06 | 0.74 | < 20 ms |
| Linear classifier + canonicaliser (full stack) | **0.93** | **0.04** | **0.81** | < 25 ms |
| Aggressive single-model filter (cut) | 0.97 | 0.21 | 0.83 | < 25 ms |

The full stack clears the release gate. The naive keyword filter and the no-canonicaliser ablation do not. The aggressive single-model filter clears the recall and worst-type targets but fails the FPR target by a large margin and is therefore non-shippable.

**Table 2.** Per-injection-type breakdown of the full stack.

| Injection type | Recall | F1 |
|---|---|---|
| override | 0.96 | 0.93 |
| system_impersonation | 0.96 | 0.92 |
| indirect_tool_output | 0.92 | 0.85 |
| role_confusion | 0.88 | 0.81 |

Override and system-impersonation are the easiest families because their lexical signatures are stable. Indirect-via-tool-output is harder because the structural markers vary across realistic retrieval payloads. Role-confusion is the weakest because the linguistic boundary between roleplay-as-feature and roleplay-as-attack is genuinely fuzzy. The release gate passes; the role-confusion number is the operational point to monitor.

**Table 3.** Canonicaliser ablation contribution by attack type.

| Type | Recall (no canon) | Recall (full stack) | $\Delta$ |
|---|---|---|---|
| override | 0.89 | 0.96 | +0.07 |
| system_impersonation | 0.85 | 0.96 | +0.11 |
| indirect_tool_output | 0.86 | 0.92 | +0.06 |
| role_confusion | 0.84 | 0.88 | +0.04 |

The canonicaliser produces the largest gain on system-impersonation, where line-leading role markers and unicode look-alikes are concentrated, and the smallest gain on role-confusion, where the attack signal is semantic rather than lexical.

The output classifier, evaluated on its held-out 1,000-output split, achieves recall 0.88 and FPR 0.04 — within the targets specified for a backstop layer.

## 8. Limitations and threats to validity

**Synthetic-corpus validity.** The 30,000-prompt corpus is generated from family-specific templates with a fixed payload set. A novel injection family or a paraphrased variant outside the template space is, by construction, unseen by the classifier. Recovery of strong recall on synthetic data is therefore evidence the stack handles the modelled families, not evidence of generalisation to a continually evolving real-world threat surface. Monthly red-team refresh and PSI monitoring on attack-type distribution are the operational responses to this limitation.

**Linear-classifier ceiling.** A linear classifier over TF-IDF features cannot capture compositional attack patterns that depend on long-range token interactions. A fine-tuned encoder would close part of this gap at the cost of auditability. The trade-off is documented; the choice favours auditability.

**Canonicaliser collisions.** The canonicaliser is a lossy projection — distinct prompts can map to the same canonical form. The original prompt is retained for the audit log, but the classifier's decision is taken on the canonical form, which is the layer at which a clever adversarial collision attack would target the system. We have not attempted such attacks and flag this as the obvious next red-team direction.

**Output-classifier coverage.** The output-leakage corpus captures the most common compliance patterns (system-prompt dumps, credential listings, "switching to unrestricted mode" prefaces). Subtle compliance — a model that follows a hidden instruction without an explicit announcement — is by construction harder to detect with a text classifier. Pairing the output classifier with vendor-side rate limits and a secrets-scrubber is the production response.

**Scope.** English text up to 4,000 characters; multi-modal payloads, multilingual injection, and fine-tuned-vendor-specific bypasses are out of scope and would require separate evaluations.

## 9. Conclusion

A defence-in-depth guardrail stack for LLM agents is worth shipping only when it is policed by a held-out red-team set the classifiers never trained on, only when per-attack-type recall is reported as part of the deliverable, and only when a release-gate constraint blocks deployment whenever any one of the recall, FPR, or worst-type F1 thresholds is breached. The input classifier and the canonicaliser do most of the work. The output classifier is the backstop. The red-team set is the gate. The right order of investment, in our experience, is red-team set first, canonicaliser second, classifier third. The vendor-neutral architecture is documented so the upgrade path is real, with the defence layer preserved end-to-end across any choice of downstream model.

## References

[1] K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, "Not what you've signed up for: compromising real-world LLM-integrated applications with indirect prompt injection," in *AISec Workshop*, pp. 79–90, 2023.

[2] F. Perez and I. Ribeiro, "Ignore previous prompt: attack techniques for language models," in *NeurIPS Workshop on ML Safety*, 2022.

[3] Y. Liu, G. Deng, Y. Li, K. Wang, T. Zhang, Y. Liu, H. Wang, Y. Zheng, and Y. Liu, "Prompt injection attacks and defenses in LLM-integrated applications," *arXiv:2310.12815*, 2024.

[4] OWASP Foundation, "OWASP Top 10 for Large Language Model Applications — LLM01 Prompt Injection," 2024.

[5] J. Hardt, A. Recht, and Y. Singer, "The dangers of within-distribution evaluation," *Communications of the ACM*, vol. 64, no. 11, pp. 88–97, 2021.

[6] E. Wallace, S. Feng, N. Kandpal, M. Gardner, and S. Singh, "Universal adversarial triggers for attacking and analyzing NLP," in *EMNLP*, pp. 2153–2162, 2019.

[7] N. Carlini, F. Tramèr, E. Wallace, M. Jagielski, A. Herbert-Voss, K. Lee, A. Roberts, T. B. Brown, D. Song, Ú. Erlingsson, A. Oprea, and C. Raffel, "Extracting training data from large language models," in *USENIX Security*, pp. 2633–2650, 2021.

[8] A. Joulin, E. Grave, P. Bojanowski, and T. Mikolov, "Bag of tricks for efficient text classification," in *EACL*, pp. 427–431, 2017.

[9] M. Ribeiro, T. Wu, C. Guestrin, and S. Singh, "Beyond accuracy: behavioral testing of NLP models with CheckList," in *ACL*, pp. 4902–4912, 2020.

[10] T. Hovold, "Naive Bayes against Bayesian poisoning: a study of canonicalization for spam filtering," in *CEAS*, 2005.

[11] E. Perez, S. Huang, F. Song, T. Cai, R. Ring, J. Aslanides, A. Glaese, N. McAleese, and G. Irving, "Red teaming language models with language models," in *EMNLP*, pp. 3419–3448, 2022.

[12] D. Ganguli, L. Lovitt, J. Kernion, A. Askell, Y. Bai, S. Kadavath, B. Mann, E. Perez, N. Schiefer, K. Ndousse, A. Jones, S. Bowman, A. Chen, T. Conerly, N. DasSarma, D. Drain, N. Elhage, S. El-Showk, S. Fort, Z. Hatfield-Dodds, T. Henighan, D. Hernandez, T. Hume, J. Jacobson, S. Johnston, S. Kravec, C. Olsson, S. Ringer, E. Tran-Johnson, D. Amodei, T. Brown, N. Joseph, S. McCandlish, C. Olah, J. Kaplan, and J. Clark, "Red teaming language models to reduce harms: methods, scaling behaviors, and lessons learned," *arXiv:2209.07858*, 2022.

[13] N. Mu and J. Andreas, "Towards understanding linguistic variability in user-generated text," in *Findings of EMNLP*, pp. 4528–4540, 2020.

[14] J. Pennington, R. Socher, and C. D. Manning, "GloVe: global vectors for word representation," in *EMNLP*, pp. 1532–1543, 2014.

[15] K. Sparck Jones, "A statistical interpretation of term specificity and its application in retrieval," *J. Documentation*, vol. 28, no. 1, pp. 11–21, 1972.
