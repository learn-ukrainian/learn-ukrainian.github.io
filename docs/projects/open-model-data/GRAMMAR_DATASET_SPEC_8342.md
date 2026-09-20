# Grammar Dataset Specification: UA-GEC Redo & Acceptance Invariants (#8342, #8339)

> **Parent Epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
> **Specific Issues:** [#8342](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8342) (Grammar set redo), [#8339](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8339) (Acceptance checker), [#8338](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8338) (Model training & scorecard)
> **Target Model:** Gemma 3 4B fine-tuning on Hugging Face (Pro GPU infrastructure)
> **Established Date:** 2026-09-20 (Cross-Model Deliberation: Astra, Grok 4.6, Gemini 3.1 Pro; Revised per Round 1 CF Review)

---

## 1. Context & Motivation

In the review of Epic #6321 and PR #8345, the previous grammar release `uldr_v05_grammar_valency` (35,000 lines) was analyzed:
* **93% passivity:** 32,629 of 35,000 rows were labeled as controls ("nothing wrong here"), with only 2,371 rows of real corrections.
* **Template collapse:** 13 question patterns covered the entire 35,000-line dataset.
* **Class deficit:** 8 of 20 error categories had fewer than 50 examples.

Issue #8342 replaces this dataset by rebuilding from authentic human-annotated sentences in UA-GEC. The old `uldr_v05_grammar_valency` release files are quarantined and marked "do not use".

This document defines the binding specification, composition ratios, rights boundaries, grounding authorities, and mechanical acceptance gates (#8339) for the replacement dataset.

---

## 2. Core Dataset Architecture

### 2.1. Control-to-Correction Ratio & Provenance

* **Mixture Allocation:**
  * **Target Ratio:** **25% clean controls : 75% real corrections** (1:3 ratio).
  * **Allowed Range:** **20% to 30% clean controls** (70% to 80% corrections).
  * **Gate Failure:** Hard-fails if clean controls are **<15%** (hyper-correction risk) or **>35%** (passive model risk).
* **Control Provenance (Zero Synthetic Text):**
  * Controls must **never be synthetically manufactured** by rule engines or LLM prompt generation.
  * Controls are drawn exclusively from:
    1. Vetted clean sentences from editor-reviewed corpora (e.g. BRUK / Brown-UK).
    2. Gold target sentences from complex UA-GEC instances, restricted strictly to documents within the **training partition** (see §2.4).
    3. "Hard negatives" (grammatically intricate sentences with legal complex syntax, multiple genitives, or apparent calques that are standard literary Ukrainian).
* **Neutral Ukrainian Instructions:**
  * Both classes (clean controls and corrections) must receive identical, prompt-neutral Ukrainian instructions, such as:
    * `«Перевірте текст і виправте помилки, якщо вони є.»`
    * `«Відредагуйте речення згідно з нормами сучасної української літературної мови.»`
  * The prompt must never disclose or imply whether an error is present. English prompts are an explicit non-goal.

---

### 2.2. Error Scope, Denominator & Thin Categories

* **Correction Scope & Denominator:**
  * Drawn from human-annotated in-scope grammar and syntax error tags in the official UA-GEC 2.0 `train` split.
  * In-scope tags include grammatical categories: case government (`G/Case`, `G/Prep`), gender/number agreement (`G/Gender`, `G/Number`), verb morphology/aspect, syntax/valency, plus grammaticalized collocations (`F/Calque`, `F/Collocation`).
  * The dataset builder must record the exact baseline denominator of extracted unique error sentences from the pinned UA-GEC release.
* **Thin Categories (<50 examples in UA-GEC):**
  * **Preserve natural distribution. Zero synthetic reverse-corruption.**
  * LLM-generated "broken sentences" (reverse GEC) are strictly forbidden—they produce unauthentic slips that do not mirror human error distributions and violate Roadmap Rule 1 & Rule 2.
  * Sparse categories are retained as-is in the dataset. At training time, fine-grained sparse codes may be mapped to overarching linguistic families (e.g. valency/government classes) for loss weighting, but raw annotations remain unmodified.
  * In evaluation, thin categories must be reported in **stratified evaluation slices** so they are not obscured by micro-averages.
  * **100% of examples in categories with <50 instances** must be manually inspected during independent sampling.

---

### 2.3. Task Mix & Facet-Aware Explanation Grounding

* **Task Mix Partition:**
  * Correction rows are strictly partitioned so their shares sum to 100%:
    * **45% Silent Rewrites:** Direct text correction without metalinguistic commentary.
    * **55% Explained Corrections:** Direct text correction accompanied by concise, authoritative grammatical reasoning.
  * *Rationale:* Fine-tuning a 4B model exclusively on explanations causes it to hallucinate lengthy essays when the user only requests proofreading.
* **Facet-Aware Authority Grounding:**
  * Explanations must not use a single rigid tuple. Instead, citations must map directly to the specific linguistic facet being corrected, per [`ukrainian-linguistics.md`](../../../agents_extensions/shared/rules/ukrainian-linguistics.md) §4:
    * **Morphological inflection & wordforms:** VESUM (validates lemma, paradigm, inflectional features).
    * **Case government & valency:** Academic syntax authorities (e.g. *Словник дієслівного керування* / академічна граматика Вихованця). VESUM validates form existence, not context valency.
    * **Spelling, apostrophe, hyphens, prefixes:** *Український правопис (2019)* citing the exact paragraph.
    * **Calques & false collocations:** Бorys Antonenko-Davydovych (*Як ми говоримо*), СУМ-20.
  * **Fail-closed rule:** If an explanation cannot resolve an exact, authoritative citation, the row **drops its explanation and becomes a silent rewrite**. Invented § numbers or generic "because Ukrainian grammar requires it" are strictly prohibited.
  * **100% of explained rows must carry a verified, resolvable citation.**

---

### 2.4. Partition Integrity & Firewall

* **Official UA-GEC Test Firewall:**
  * All documents in the official UA-GEC `test` partition are **frozen as held-out evaluation**.
  * No text, original sentence, or corrected target from the `test` partition may enter the training dataset, whether as a correction or as a clean control.
* **Document-Level Split:**
  * Training and validation splits are partitioned **strictly by document ID (`doc_id`)**, never by random sentence shuffling.
  * 0 shared document IDs across splits.
* **Lemma-Level Cross-Split Protection:**
  * In accordance with Roadmap §3 Rule 6, idioms and focal lexical constructions are evaluated by dictionary lemma base (e.g. *робити вигляд* and *зробити вигляд* are treated as the same base) to ensure test evaluation measures generalization rather than rote memorization.

---

### 2.5. Rights & Licensing Boundary

In accordance with Roadmap §3 Rule 8 and project licensing policy:
* **UA-GEC 2.0:** Licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. Full author credit and provenance metadata are maintained.
* **Brown-UK / БрУК:** Licensed under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)**.
* **Dataset Rights Coexistence:**
  * The project dataset is non-commercial and permanent.
  * To respect the ShareAlike provision of Brown-UK without creating license incompatibility with pure CC BY 4.0 text, clean control sentences derived from Brown-UK must be clearly attributed with their CC BY-NC-SA 4.0 source provenance.
  * No dataset reproduces third-party text without a recorded rights attribution.

---

## 3. Mechanical Acceptance Gates (#8339 Gate)

The automated acceptance checker built under [#8339](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8339) evaluates the dataset folder and **fails closed** (exit non-zero) if any of the following invariants are breached:

| Category | Invariant Check | Acceptance Threshold | Failure Action |
| :--- | :--- | :--- | :--- |
| **Mixture** | Clean Control Share | **20% to 30%** of unique examples | Fail if <15% or >35% |
| **Mixture** | Substantive Corrections | **70% to 80%** of unique examples | Fail if <65% |
| **Duplicates** | Exact Duplicate Sentences | **0** duplicate `(source, target)` pairs | Fail if >0 |
| **Duplicates** | Near-Duplicate Padding | **0** synthetic word/number-swapped clones | Fail if >0 |
| **Concentration** | Top Substantive Skeleton | **≤5.0%** of substantive rows | Fail if >5.0% |
| **Concentration** | Top 10 Skeletons Combined | **≤25.0%** of substantive rows | Fail if >25.0% |
| **Concentration** | Skeleton Entropy | $H / \log(K) \ge 0.80$ (delexicalized: quoted spans masked to `«…»`, digits to `#`) | Fail if <0.80 |
| **Multi-field Check** | Skeletons Measured Separately | Question, reasoning, and answer evaluated independently | Fail if any collapses |
| **Split Integrity** | Document Leakage | **0** shared `doc_id`s between train and held-out test | Fail if >0 |
| **Split Integrity** | Lemma-Normalized Overlap | 0 lemma-level overlap on focal constructions | Fail if detected |
| **Citations** | Resolvable Citation Hit Rate | **100%** of explained rows cite verified authorities | Fail if <100% |
| **Soviet Source Rule** | СУМ-11 Distortion Rule | **0** meanings/labels from СУМ-11; 0 words marked wrong/rare solely due to absence from СУМ-11 | Fail if detected |
| **Translation Rule** | Translation Dictionary Rule | **0** definitions derived from bilingual translation dictionaries | Fail if detected |
| **Self-Contradiction** | Internal Disagreement | **0** contradictory claims inside a single example | Fail if detected |
| **Dependencies** | Dictionary Accessibility | Required databases (`vesum.db`, `sources.db`) present and reachable | Fail closed if missing |
| **Human Audit** | Review Sample Package | Tool draws **300 random instances + 100% of thin categories (<50 instances)** | Blocks merge until reviewed |

---

## 4. Model Training & Behavioral Evaluation Targets (#8338 Gate)

The static dataset checker (#8339) evaluates the dataset files. Behavioral verification of the fine-tuned Gemma 3 4B model occurs in [#8338](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8338):

1. **Clean Sentence Preservation (Gate 3 Alignment):**
   * Benchmarked on an independent held-out suite of **at least 1,000 verified clean Ukrainian sentences**.
   * Unnecessary-edit rate on clean sentences must achieve:
     * Point estimate: **$\le 1.0\%$**
     * One-sided 95% Clopper-Pearson upper confidence bound: **$< 2.0\%$**
   * *Relation to Gate 3:* Preserves the integrity of Gate 3 (`PRODUCTION_RELEASE_PLAN.md` §3.2) while establishing statistical bounds for fine-tuned LLM inference.
2. **Grammar Correction Precision:**
   * Edit-level $F_{0.5}$ on the official UA-GEC held-out test set must show measurable improvement over the base Gemma 3 4B checkpoint.
   * Precision and recall reported separately across both coarse error tags and fine-grained categories.
