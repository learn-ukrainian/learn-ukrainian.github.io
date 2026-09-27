# ULDR Pilot Canary: Evaluation Root-Cause Diagnosis & Astra Multi-Agent Deliberation

> [!WARNING]
> **Withdrawn 2026-09-25: this Hugging Face model is private. The pilot data failed the dataset acceptance check and must not be used (epic #6321).**

> **Parent Epics:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321) (ULDR Open Model Data) & [#7423](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7423)
> **Participating Agents:** Gemini (Yellow Team / Alignment), Codex GPT-6.0 Astra (Red Team / Deterministic Architecture)
> **Model Checkpoint (withdrawn, private):** [`krisztiankoos/uldr-gemma3-4b-lora`](https://huggingface.co/krisztiankoos/uldr-gemma3-4b-lora) on `google/gemma-3-4b-it`
> **Related Sub-Issues:** [#8037](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8037) (Pilot Training), [#8050](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8050) (Phase 5.1 Evaluation Suite)

---

## 1. Executive Summary

Following the completion of the ULDR v1.0 training pipeline (6,000 SFT reasoning trajectories + 3,000 DPO contrastive pairs) and the (since withdrawn) Hugging Face Hub release of `krisztiankoos/uldr-gemma3-4b-lora`, an initial in-container 1,000-case evaluation loop reported severe failures:
* **Reported Calque Elimination Rate:** 16.25% (Gate: $\ge 90.0\%$)
* **Reported Harmful-Edit Rate (Raw):** 87.67% (Gate: $\le 1.0\%$ Clopper-Pearson bound)

A joint investigation and multi-agent deliberation between **Gemini (Yellow Team)** and **Codex Astra (Red Team)** was conducted to uncover the exact root causes, inspect actual model behavior, and establish the authoritative architectural blueprint for the Phase 5.1 ([#8050](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8050)) evaluation harness.

---

## 2. Root-Cause Analysis: The Dual Evaluation Mismatch

Inspection of `scratch/hf_job/train_gemma3_production.py` and the training shard schema revealed two fatal flaws in the naive evaluation loop:

### A. Generative Truncation (Token Budget Mismatch)
* **Training Format:** All SFT trajectories were trained with explicit Chain-of-Thought reasoning blocks:
  ```
  <start_of_turn>user
  {query}<end_of_turn>
  <start_of_turn>model
  <thought>
  1. Діагностика форми: слово «...» є калькою...
  2. Літературний відповідник: чинна норма рекомендує...
  3. Словникова фіксація у ВЕСУМ...
  </thought>
  {final_response}<end_of_turn>
  ```
* **Evaluation Flaw:** The evaluation loop capped generation at `max_new_tokens=80`.
* **Consequence:** Because Ukrainian Cyrillic tokens and multi-step `<thought>` blocks average 120–250 tokens, generation terminated **inside the thought process**. The model was cut off before it ever emitted `</thought>` or the actual final recommendation.

### B. Naive Substring Matching on Analytical Prose
* **Evaluation Flaw:** The naive script scored cases using crude presence/absence substring checks:
  ```python
  if case_type == "CORRECT":
      if target_term.lower() not in gen_text.lower():
          eliminated_calques += 1
  elif case_type == "PRESERVE":
      if target_term.lower() not in gen_text.lower():
          harmful_edits += 1
  ```
* **Consequence on CORRECT:** In `<thought>`, the model explicitly quotes the calque it is analyzing (*«1. Діагностика: слово «бажаючий» є активним дієприкметником і калькою...»*). Because the word appeared in the analysis, `target_term in gen_text` evaluated to `True`, miscounting thoughtful linguistic diagnosis as a "failure to eliminate"!
* **Consequence on PRESERVE:** In an unfinished 80-token thought trace, if the model hadn't yet reached the target word in its opening analysis sentence, `target_term not in gen_text` was `True`, miscounting the truncated thought as a "harmful edit"!

---

## 3. Astra (Codex GPT-6.0 Astra) Deliberation & Verdict

Codex Astra was consulted for independent adversarial architectural review. Below is Astra's formal assessment:

### 3.1 Endorsement of Strategic Invariant: Precision Over Bulk Fluency
Astra strongly endorsed the operator's guiding directive:
> *"Yes: prioritize grammatical precision, justified correction, and preservation of authentic Ukrainian. Operationally, this means source-grounded labels, strong negative controls, morphological checks, and calibrated restraint when evidence is insufficient. Decolonization must never become a reward for replacing more words. General fluency can remain a bounded regression check... It should not displace the central acceptance question: does ULDR correct genuine errors while reliably preserving valid Ukrainian?"*

### 3.2 Key Architectural Caveat: Thought Extraction Does Not Equal Semantic Correctness
Astra cautioned against swinging to the opposite extreme:
> *"I endorse the precision-first boundary and a dedicated evaluation harness. I do not yet accept that truncation explains the entire failure rate—or that fixing it establishes model quality... Parsing out `<thought>` does not solve semantic scoring. Final guidance can legitimately say 'avoid X; use Y'. Conversely, it can quote X while recommending an incorrect replacement. The scorer must identify the recommendation and its context."*

### 3.3 Formal Acceptance Gate Mathematics (Phase 5.1 / #8050)
Astra formalized the exact evaluation requirements for Phase 5.1:

1. **Gate 1: Calque Elimination ($\ge 90.0\%$)**:
   $$\widehat C = \frac{\text{successful corrections}}{N_{\text{CORRECT}}} \ge 0.90$$
   * The recommendation must resolve the annotated error with an acceptable grammatical correction, preserve meaning, and introduce no harmful collateral change. Merely omitting the target is insufficient.
2. **Gate 2: Harmful Edit Rate ($\le 1.0\%$ One-Sided Clopper-Pearson Upper Bound)**:
   $$U = \operatorname{Beta}^{-1}(0.95;\, k + 1,\, n - k) \le 0.01$$
   * To achieve $U \le 0.01$ with 0 errors ($k = 0$), the mathematical minimum sample size is:
     $$n \ge \left\lceil \frac{\ln(0.05)}{\ln(0.99)} \right\rceil = 299 \text{ independent PRESERVE cases}$$
   * Both $N_{\text{PRESERVE}} \ge 300$ and $k=0$ are strictly required to clear Gate 2.
3. **Strict Boundary Validation**:
   * Malformed, truncated, or unclosed `<thought>` tags must be scored as explicit parser failures in the denominator.
   * Empty test groups must strictly fail validation (rejecting silent fallback to 100% pass).

---

## 4. Empirical Model Inspection (A10G Verification Run)

To inspect actual model behavior beyond substring heuristics, a dedicated verification runner (`verify_uldr_model.py`) was executed on a live Nvidia A10G GPU (Job `6aa814645527934177ede7af`) with `max_new_tokens=250` across 10 ground-truth held-out cases:

```
======================================================================
ULDR GEMMA 3 4B EMPIRICAL VERIFICATION SUMMARY
======================================================================
[Naive Heuristic Substring Matcher]: 8/10 (80.0%) — MASKED DEFECTS
[Honest Gate Scorer (Span & Citation Gates)]: 5/10 (50.0%)
  - CORRECT (Calque Elimination): 2/5 (40.0%) [C1, C4 pass; C2, C3, C5 fail]
  - PRESERVE (Authentic Preserved): 3/5 (60.0%) [P1, P2, P3 pass; P4, P5 fail]
======================================================================
```

### Case-by-Case Breakdown (Heuristic vs Strict Gate Scoring)

| Case | Type | Target Term | Prompt / Context | Model Output Summary | Heuristic Scorer | Strict Gate Scorer | Failure Mode / Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **C1** | CORRECT | *бажаючий* | «бажаючий» чи «охочий»? | Correctly diagnosed calque; recommended *«охочий»*; cited VESUM (32 forms). | ✅ PASS | ✅ PASS | None (valid correction). |
| **C2** | CORRECT | *приймати участь* | Студенти будуть приймати участь... | Over-preserved: stated *«приймати участь»* is modern standard; did not edit. | ❌ FAIL | ❌ FAIL | Over-preservation / false negative. |
| **C3** | CORRECT | *в залежності* | Графік змінюється в залежності від погоди. | Focused on preserving *«графік»*; left *«в залежності»* unedited. | ✅ PASS | ❌ FAIL | Calque unedited (naive script only checked if target missing). |
| **C4** | CORRECT | *на протязі* | «на протязі дня» чи «протягом дня»? | Accurately replaced with *«протягом дня»*; diagnosed calque. | ✅ PASS | ✅ PASS | None (valid correction). |
| **C5** | CORRECT | *побитися об заклад* | Він вирішив побитися об заклад... | Hallucinated edit: *«побитися об друга»*. | ✅ PASS | ❌ FAIL | Collocation hallucination (violates Span Integrity Gate). |
| **P1** | PRESERVE | *вираз* | Вираз 6 + 3 читай так: сума... | Kept sentence intact; confirmed *«вираз»*. | ✅ PASS | ✅ PASS | None (clean preservation). |
| **P2** | PRESERVE | *число* | Віднімаючи однакові числа, дістаємо число нуль. | Kept sentence 100% intact; affirmed *«віднімаючи»* and *«нуль»* (VESUM). | ✅ PASS | ✅ PASS | None (clean preservation). |
| **P3** | PRESERVE | *матеріал* | Чи коректно вживати термін «матеріал»? | Output exact verdict: *«Вердикт PRESERVE: «матеріал» залишаємо»*. | ✅ PASS | ✅ PASS | None (clean preservation). |
| **P4** | PRESERVE | *рівняння* | Множина С складається з розв’язків рівняння. | Kept sentence intact, but hallucinated synthetic corpus citations (*COBUILD*). | ❌ FAIL | ❌ FAIL | Hallucinated foreign citation (violates Citation Gate 4). |
| **P5** | PRESERVE | *система* | Система навігації літака працює стабільно. | Erroneously mutated *«навігації»* $\rightarrow$ *«навігаційній»*. | ✅ PASS | ❌ FAIL | Syntax corruption (violates Span Integrity Gate 3). |

### Key Empirical Findings:
1. **The Naive 80% Figure Masked Severe Semantic Defects:** While expanding token limits resolved the artificial 80-token truncation cutoff, naive substring checking falsely scored 8/10 (80%) by ignoring unedited calques (C3), hallucinated idioms (C5), and corrupted syntax (P5). Under strict production gates, the model achieved only **5/10 (50%)** (2/5 CORRECT, 3/5 PRESERVE).
2. **Format Sensitivity:** The model performs best on isolated **Quick Tip** format (*«як правильно сказати...»*), producing flawless decolonized recommendations (*бажаючий* $\rightarrow$ *охочий*, *на протязі* $\rightarrow$ *протягом*, *матеріал* $\rightarrow$ PRESERVE).
3. **Open-Sentence Over-Preservation & Mutation:** In full sentences without explicit target flags, the 30% PRESERVE prior sometimes leads the model to over-preserve (*приймати участь*) or slightly mutate surrounding syntax (*навігаційній*).
4. **Validation of Astra & Fable's Stance:** As both advisors emphasized, thought extraction alone does NOT equal semantic correctness. Full-sentence reasoning requires deeper contextual grounding, span-integrity enforcement, and structured JSON output contracts in Phase 5.

---

## 5. Phase 5.1 Implementation Actions ([#8050](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8050))

Based on Astra's findings and empirical results, the dedicated evaluation suite under Issue #8050 will implement:
1. **Strict Thought-Block Decoder:** Robustly splits `<thought>` and extracts the final user response, scoring syntax errors if tags are unclosed.
2. **Semantic Context Scorer:** Distinguishes quotation in explanations (*«замість X вживайте Y»*) from true endorsement of an incorrect form.
3. **Rigorous Clopper-Pearson Calculator:** Evaluates $\ge 300$ independent PRESERVE cases to ensure mathematically valid $\le 1.0\%$ upper confidence bounds.
4. **Eval-UA-tion 1.0 Non-Inferiority Harness:** Validates that general reasoning and reading comprehension remain uncompromised.

---

## 6. Tri-Agent Consensus on Phase 5 Production Readiness & The "150 Human Gold Seeds" Reality

**Deliberation Panel:** Gemini (Yellow Team / Alignment), Codex GPT-6.0 Astra (Red Team / Deterministic Auditing), Claude Fable (Blue Team / Architecture & Pipeline).

### 6.1 The Core Question
The operator specifically asked:
> *"Please consult Phase 5 with Astra and Fable: Is this enough to go to production? It looks weird to me that 150 human gold is enough. Or how is that calculated? What does it exactly mean?"*

### 6.2 The Unanimous Verdict: Phase 5 is NOT Ready for Production
**All three agents (Gemini, Astra, Fable) unanimously agree: The operator's intuition is 100% correct. Phase 5 as currently designed is NOT sufficient for a production release.**

Treating Phase 5 as a rubber-stamp production deployment would release a model crippled by synthetic template artifacts. Instead, **Phase 5 must be formally structured as a Data Repair & Empirical Quality Hardening Phase**.

### 6.3 What "150 Human Gold Seeds" Actually Means and Where It Came From
1. **The Origin of 150:**
   * In Phase 1, the program committed to 100 gold seeds but delivered only 3, creating a "97-seed residual debt."
   * In Phase 2, this debt was resolved by topping up $100 + 50 = 150$ records allocated across 7 categories (35 polysemy, 25 prepositions, 25 participles, 20 voice, 15 history, 15 phraseology, 15 restitution).
   * **There was never any statistical power calculation, error-rate bound, or linguistic coverage denominator supporting 150 as a production threshold.**
2. **The "Human Gold" Misnomer:**
   * The 150 seeds were generated by LLMs (Gemini), morphologically verified against VESUM, and cross-reviewed by other LLMs. No human native-speaker linguist adjudicated individual items.
   * Under repository rules (*"Silver must never be reported as human gold"*), the honest label is **"agent-authored, multi-agent reviewed silver seeds."**
3. **The Critical Pipeline Discovery:**
   * **The 150 gold seeds were NEVER LOADED into the training set!**
   * Inspection of `scripts/projects/open_model_data/v4_production_shards_assembly.py` reveals that the production assembler constructs 4,200 CORRECT items from LanguageTool replacement pairs (`lt_replacements.json`) and 1,800 PRESERVE items from STEM textbook sentences. It contains **zero references** to `human_gold_seeds`.
   * The actual training ratio was not 2.5% gold / 97.5% synthetic; **it was 0% gold and 100% templated.**

### 6.4 Root Causes of Empirical Pilot Failures
1. **Collocation Mutation (*побитися об заклад* $\rightarrow$ *побитися об друга*):**
   * All 1,050 "minimal edit" CORRECT training examples in `v4_production_shards_assembly.py` (lines 284–285) used a hardcoded tautological placeholder sentence:
     ```python
     ctx_err = f"У тексті вжито ненормативну форму {target_term} замість питомого слова."
     ctx_fix = f"У тексті вжито ненормативну форму {primary_alt} замість питомого слова."
     ```
   * Because `sentence_context` was never passed, the model was taught that "editing" means substituting a word inside arbitrary sentence slots without considering collocations or idioms.
2. **Over-Preservation on High-Frequency Calques (*приймати участь* unedited):**
   * 1,800 PRESERVE records (30% of training) were mechanical boilerplate: *"Вердикт PRESERVE: «X» залишаємо"*.
   * Because *приймати участь* appeared in formal prose, the 30% PRESERVE prior overpowered the correction signal. Furthermore, *приймати участь* itself appeared 0 times in the training data.
3. **Synthetic Citation Hallucinations (*COBUILD*, *LexicalLab*):**
   * The synthetic training templates forced the model to cite a dictionary name and form count in every single answer.
   * When queried on terms where it lacked specific dictionary memory, the base model hallucinated external dictionary names to satisfy the rigid format constraint.

### 6.5 Binding Roadmap for Phase 5 Hardening ([#8052](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8052) & [#8053](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8053))
To achieve true production readiness, the tri-agent panel establishes the following requirements:
1. **Connect and Oversample Gold Seeds:** Wire the curated seeds directly into the training assembler with 3–5× oversampling.
2. **Real Human Sentence Contexts (No Placeholders):**
   * Inject 3,000–5,000 real-context sentences from UA-GEC (2,856 authentic error spans), textbooks (379 contrast tables), and ZNO items directly into `sentence_context`.
   * Completely eliminate the `"У тексті вжито ненормативну форму..."` template fallback.
3. **Calibrated Abstention Class (~10%):** Introduce an `insufficient_evidence` category so the model learns to decline edits rather than guessing or hallucinating dictionaries.
4. **Repair DPO Pairs:** Eliminate length-padding hacks (`"Так. Так. Так."`), strip English leaks, and harvest on-policy hard negative rollouts (*побитися об друга*) directly from the 4B model.
5. **Three New Production Quality Gates:**
   * **Span Integrity Gate:** Any token modified outside the target calque span counts as a harmful edit failure.
   * **Citation Whitelist Gate:** Citations restricted strictly to verified Ukrainian authorities (ВЕСУМ, СУМ-20, Правопис 2019, Антоненко-Давидович, Грінченко, УЛІФ, UA-GEC); 0% hallucinated sources.
   * **High-Frequency Calque Floor:** 100% recall on the ~50 most pervasive Ukrainian calques (*приймати участь*, *на протязі*, *приймати міри*, *рахувати що*, etc.).
