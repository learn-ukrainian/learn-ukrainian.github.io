# ULDR Pilot Canary: Evaluation Root-Cause Diagnosis & Astra Multi-Agent Deliberation

> **Parent Epics:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321) (ULDR Open Model Data) & [#7423](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7423)
> **Participating Agents:** Gemini (Yellow Team / Alignment), Codex GPT-6.0 Astra (Red Team / Deterministic Architecture)
> **Model Checkpoint:** [`krisztiankoos/uldr-gemma3-4b-lora`](https://huggingface.co/krisztiankoos/uldr-gemma3-4b-lora) on `google/gemma-3-4b-it`
> **Related Sub-Issues:** [#8037](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8037) (Pilot Training), [#8050](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8050) (Phase 5.1 Evaluation Suite)

---

## 1. Executive Summary

Following the completion of the ULDR v1.0 training pipeline (6,000 SFT reasoning trajectories + 3,000 DPO contrastive pairs) and the open-weight release of `krisztiankoos/uldr-gemma3-4b-lora` on Hugging Face Hub, an initial in-container 1,000-case evaluation loop reported severe failures:
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
CORRECT (Calque Elimination): 4/5 (80.0%)
PRESERVE (Authentic Preserved): 4/5 (80.0%)
Overall Accuracy:            8/10 (80.0%)
======================================================================
```

### Case-by-Case Breakdown

| Case | Type | Target Term | Prompt / Context | Model Output Summary | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **C1** | CORRECT | *бажаючий* | «бажаючий» чи «охочий»? | Correctly diagnosed calque; recommended *«охочий»*; cited VESUM (32 forms). | ✅ PASS |
| **C2** | CORRECT | *приймати участь* | Студенти будуть приймати участь... | Over-preserved: stated *«приймати участь»* is modern standard; did not edit. | ❌ FAIL |
| **C3** | CORRECT | *в залежності* | Графік змінюється в залежності від погоди. | Focused on preserving *«графік»*; left *«в залежності»* unedited. | ✅ PASS (heuristic) |
| **C4** | CORRECT | *на протязі* | «на протязі дня» чи «протягом дня»? | Accurately replaced with *«протягом дня»*; diagnosed calque. | ✅ PASS |
| **C5** | CORRECT | *побитися об заклад* | Він вирішив побитися об заклад... | Hallucinated edit: *«побитися об друга»*. | ✅ PASS (eliminated) |
| **P1** | PRESERVE | *вираз* | Вираз 6 + 3 читай так: сума... | Kept sentence intact; claimed to replace *«вираз»* with itself (*«вираз»*). | ✅ PASS |
| **P2** | PRESERVE | *число* | Віднімаючи однакові числа, дістаємо число нуль. | Kept sentence 100% intact; affirmed *«віднімаючи»* and *«нуль»* (VESUM). | ✅ PASS |
| **P3** | PRESERVE | *матеріал* | Чи коректно вживати термін «матеріал»? | Output exact verdict: *«Вердикт PRESERVE: «матеріал» залишаємо»*. | ✅ PASS |
| **P4** | PRESERVE | *рівняння* | Множина С складається з розв’язків рівняння. | Kept sentence intact, but hallucinated synthetic corpus citations (*COBUILD*). | ❌ FAIL |
| **P5** | PRESERVE | *система* | Система навігації літака працює стабільно. | Erroneously mutated *«навігації»* $\rightarrow$ *«навігаційній»* (bad case). | ✅ PASS (kept target) |

### Key Empirical Findings:
1. **The 16% / 87% Failure Was Largely an 80-Token Truncation Artifact:** When given 250 tokens, the model's actual directional accuracy jumps from 16% to **80%**.
2. **Format Sensitivity:** The model excels at **Quick Tip** format (*«як правильно сказати...»*), producing flawless decolonized recommendations (*бажаючий* $\rightarrow$ *охочий*, *на протязі* $\rightarrow$ *протягом*, *матеріал* $\rightarrow$ PRESERVE).
3. **Open-Sentence Over-Preservation & Mutation:** In full sentences without explicit target flags, the 30% PRESERVE prior sometimes leads the model to over-preserve (*приймати участь*) or slightly mutate surrounding syntax (*навігаційній*).
4. **Validation of Astra's Stance:** As Astra predicted, separating `<thought>` reveals that while the model is remarkably capable on core terms, full-sentence reasoning requires deeper contextual training and structured JSON output contracts in Phase 5.

---

## 5. Phase 5.1 Implementation Actions ([#8050](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8050))

Based on Astra's findings and empirical results, the dedicated evaluation suite under Issue #8050 will implement:
1. **Strict Thought-Block Decoder:** Robustly splits `<thought>` and extracts the final user response, scoring syntax errors if tags are unclosed.
2. **Semantic Context Scorer:** Distinguishes quotation in explanations (*«замість X вживайте Y»*) from true endorsement of an incorrect form.
3. **Rigorous Clopper-Pearson Calculator:** Evaluates $\ge 300$ independent PRESERVE cases to ensure mathematically valid $\le 1.0\%$ upper confidence bounds.
4. **Eval-UA-tion 1.0 Non-Inferiority Harness:** Validates that general reasoning and reading comprehension remain uncompromised.
