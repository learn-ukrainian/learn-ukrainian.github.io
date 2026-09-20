# Grammar Dataset Specification: UA-GEC Redo & Acceptance Invariants (#8342, #8339)

> **Parent Epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
> **Specific Issues:** [#8342](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8342) (Grammar set redo), [#8339](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8339) (Acceptance checker)
> **Target Model:** Gemma 3 4B fine-tuning on Hugging Face (Pro GPU infrastructure)
> **Established Date:** 2026-09-20 (Cross-Model Deliberation: Astra, Grok 4.6, Gemini 3.1 Pro)

---

## 1. Context & Motivation

In the review of Epic #6321 and PR #8345, the previous grammar release `uldr_v05_grammar_valency` (35,000 lines) was analyzed:
* **93% passivity:** 32,629 of 35,000 rows were labeled as controls ("nothing wrong here"), with only 2,371 rows of real corrections.
* **Template collapse:** 13 question patterns covered the entire 35,000-line dataset.
* **Class deficit:** 8 of 20 error categories had fewer than 50 examples.

Issue #8342 replaces this dataset by rebuilding from the human-annotated corrections in UA-GEC (~8,900 instances). To prevent repeating earlier design failures, this specification defines the architectural parameters, dataset composition, grounding chains, and acceptance gates established by cross-model consensus.

---

## 2. Core Dataset Architecture

### 2.1. Control-to-Correction Ratio (Preventing Both Passivity & Hyper-Correction)

* **Target Ratio:** **20%–25% clean controls : 75%–80% real corrections** (approx. 1:3 to 1:4 ratio).
* **Rationale:**
  * Avoids the **93% passivity trap** of `uldr_v05` (which taught the model that doing nothing was statistically optimal).
  * Avoids the **hyper-correction trap** of 0%–10% controls (where models trained exclusively on errors hallucinate defects in standard Ukrainian).
  * 20%–25% provides sufficient negative anchors to delineate the "do not touch" boundary without diluting correction learning.
* **Control Provenance:**
  * Controls must **never be synthetic**.
  * Draw ~2,200–2,800 controls from:
    1. Vetted clean sentences from editor-reviewed corpora (e.g., BRUK / Brown-UK).
    2. Gold corrected target sentences from complex UA-GEC instances.
    3. "Hard negatives" (grammatically intricate sentences with multiple genitives, participles, or apparent calques that are authentic literary Ukrainian).
* **Prompt Neutrality:** Both classes must receive identical neutral instructions (e.g. *"Check and correct the Ukrainian text if needed"*), never signaling whether an error is present.

---

### 2.2. Thin Error Categories (<50 examples in UA-GEC)

* **Policy:** **Preserve natural distribution. Zero synthetic reverse-corruption.**
* **Rules:**
  * Synthetic "breaking" of clean sentences by LLMs to manufacture fake errors produces unauthentic slips that do not match human error distributions and violates Roadmap Rule 1 & Rule 2.
  * Thin categories are retained as-is in training data. At train time, fine-grained sparse codes may be mapped to overarching linguistic families (e.g. valency/government classes).
  * In evaluation, thin categories must be tracked in **stratified evaluation slices** so they are visible and not obscured by micro-averages.
  * **100% of examples in categories with <50 instances** must be manually reviewed during the independent sampling phase.

---

### 2.3. Task Mix & Explanation Strategy

* **Dual-Objective Task Mix:**
  * **40%–50% silent rewrites** (direct text-to-text correction).
  * **50%–60% explained corrections** (correction + concise grammatical rationale).
  * *Crucial benefit:* Prevents a 4B model from over-indexing on generating explanatory essays when the user prompt only requests proofreading.
* **Grounding Evidence Chain:**
  * Every explanation must resolve against a strict evidence tuple: `(UA-GEC annotation) -> (VESUM morphological validation) -> (Pravopys 2019 paragraph / Academic Syntax Authority)`.
  * *Note on VESUM scope:* VESUM validates inflection, lemma, and morphology; syntax and verbal government must cite established academic syntax sources (e.g. dictionary of verbal government).
* **Rhetorical Frame Diversity:**
  * Use 4–6 distinct frames (pedagogical citation, direct contrast, procedural question test, structural shift) to eliminate template concentration.

---

## 3. Mechanical Acceptance Thresholds (#8339 Gate)

The acceptance script (#8339) must enforce the following gates before the grammar dataset is admitted:

| Metric | Passing Threshold | Rationale |
| :--- | :--- | :--- |
| **Control Share** | **20% – 30%** (target 25%) | Fails if <10% (hyper-correction risk) or >35% (passive risk). |
| **Exact Duplicates** | **0** duplicate examples | Ignores IDs/metadata; exact source/target copies are barred. |
| **Near-Duplicate Swaps** | **0** word/number-swapped padding rows | Catches synthetic duplication. |
| **Template Concentration** | Largest skeleton **≤5%**; top-10 skeletons **≤25%–30%** | Measured by delexicalizing quoted spans and numbers. |
| **Skeleton Entropy** | $H / \log(K) \ge 0.80$ | Ensures high distributional diversity across prompts and explanations. |
| **Split Integrity** | **0** shared UA-GEC document IDs | Split strictly by document ID to avoid sentence leakage. |
| **Citation Hit Rate** | **≥85%** of explained rows cite verified sources | Unresolvable citations must fail the row. |
| **Sampling for Human Review** | **300 random instances + 100% of thin categories** | Drawn by tool, approved by language reviewer. |
| **Held-Out Behavioral Target** | **Unnecessary-edit rate on clean test ≤2%** (95% upper bound ≤3%) | Validates that Gemma 3 4B does not hallucinate errors on clean Ukrainian. |

---

## 4. Execution Roadmap for #8342

1. **Extraction & Re-alignment:**
   - Extract in-split human-annotated sentences from UA-GEC.
   - Separate into silent rewrite prompts (40–50%) and explained prompts (50–60%).
   - Select 20%–25% authentic clean controls from Brown-UK and vetted UA-GEC targets.
2. **Grounding & Evidence Verification:**
   - Run morphological verification against VESUM.
   - Run syntax and government verification against academic references.
3. **Acceptance Verification (#8339):**
   - Run the automated gate to ensure 0 duplicates, entropy $\ge 0.80$, and 0 document split leakage.
4. **Hugging Face Fine-Tuning & Scorecard (#8338):**
   - Train Gemma 3 4B on Hugging Face Pro GPU infrastructure.
   - Benchmark against held-out UA-GEC evaluation split + 1,000 clean preservation sentences.
