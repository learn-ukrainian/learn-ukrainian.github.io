# Grammar Dataset Specification: UA-GEC Redo & Acceptance Invariants (#8342, #8339)

> **Parent Epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
> **Specific Issues:** [#8342](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8342) (Grammar set redo), [#8339](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8339) (Acceptance checker), [#8338](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8338) (Training & diagnostic scorecard)
> **Target Model:** Gemma 3 4B fine-tuning on Hugging Face (Pro GPU infrastructure)
> **Established Date:** 2026-09-20 (Cross-Model Deliberation: Astra, Grok 4.6, Gemini 3.1 Pro; Revised per Round 6 CF Review)

---

## 1. Context & Motivation

In the review of Epic #6321 and PR #8345, the previous grammar release `uldr_v05_grammar_valency` (35,000 lines) was analyzed:
* **93% passivity:** 32,629 of 35,000 rows were labeled as controls ("nothing wrong here"), with only 2,371 rows of real corrections.
* **Template collapse:** 13 question patterns covered 100% of the 35,000-line dataset ($K=13$).
* **Class deficit:** 8 of 20 error categories had fewer than 50 examples.

Issue #8342 replaces this dataset by rebuilding from authentic human-annotated sentences in UA-GEC. The old `uldr_v05_grammar_valency` release files are quarantined and marked "do not use".

This document defines the binding specification, composition ratios, rights boundaries, grounding authorities, and mechanical acceptance gates (#8339) for the replacement dataset.

---

## 2. Core Dataset Architecture

### 2.1. Control-to-Correction Ratio & Provenance

* **Single Binding Mixture Interval:**
  * **Clean Controls:** Strictly **20.0% to 30.0%** of unique training examples (target: **25.0%**).
  * **Real Corrections:** Strictly **70.0% to 80.0%** of unique training examples (target: **75.0%**).
  * **Acceptance Rule:** The checker fails closed if clean controls are **< 20.0%** (hyper-correction risk) or **> 30.0%** (passivity risk).
* **Control Provenance (Zero Synthetic Text):**
  * Controls must **never be synthetically manufactured** by rule engines, corruption scripts, or LLM prompt generation.
  * Controls are drawn exclusively from two verified sources:
    1. Vetted clean sentences from editor-reviewed corpora (e.g. BRUK / Brown-UK).
    2. Gold target sentences from complex UA-GEC instances, restricted strictly to documents within the **90% train partition** (see §2.4), never from the validation or held-out test splits.
  * *Hard Negatives:* A priority subset of (1) and (2) comprising grammatically intricate sentences with legal complex syntax (multiple genitives, participial clauses, or standard constructions that surface as apparent calques).
* **Neutral Ukrainian Instructions:**
  * Both classes (clean controls and corrections) must receive identical, prompt-neutral Ukrainian instructions, such as:
    * `«Перевірте текст і відредагуйте його згідно з нормами сучасної української літературної мови, якщо є помилки.»`
    * `«Виправте помилки в тексті, якщо вони присутні. Якщо текст правильний, залиште його без змін.»`
  * The prompt must never disclose or imply whether an error is present. English prompts are an explicit non-goal.

---

### 2.2. Error Scope, Denominator & Thin Categories

* **Pinned Source & Closed In-Scope Tag Set:**
  * Source: Upstream UA-GEC repository pinned to commit [`4757f72f192c4a41e4c8fb1d9690a948f87cf6d6`](https://github.com/grammarly/ua-gec/commit/4757f72f192c4a41e4c8fb1d9690a948f87cf6d6) (as tracked in `docs/projects/ua-eval-harness/THIRD_PARTY_NOTICES.md`).
  * Annotation Layer: Extracted **exclusively from `gec-fluency/train`** (1,706 documents).
  * Multi-Annotator Handling: The 45 documents in `gec-fluency/train` annotated by two independent annotators (sharing `doc_id` but differing in `doc.meta.annotator_id`) keep **both annotator targets as parallel valid corrections** (matching `THIRD_PARTY_NOTICES.md` and the evaluation harness convention). Both annotations remain bound under the same `doc_id` during document-level splits.
  * Unified In-Scope Tag Rule: To preserve strict alignment with the evaluation harness protocol, in-scope tags are **strictly all tags matching prefix `G/*` plus `F/Calque`**:
    * **Grammar (`G/*`):** `G/Case`, `G/Gender`, `G/Number`, `G/Aspect`, `G/Tense`, `G/VerbVoice`, `G/PartVoice`, `G/VerbAForm`, `G/Prep`, `G/Participle`, `G/Particle`, `G/UngrammaticalStructure`, `G/Comparison`, `G/Conjunction`, `G/Other`
    * **Grammaticalized Lexicon:** `F/Calque`
  * Excluded Complement Tags: All remaining categories (`Punctuation`, `Spelling`, `F/Other`, `F/Style`, `F/PoorFlow`, `F/Repetition`, and non-calque fluency `F/Collocation`) are excluded from in-scope grammar error tagging and classification.
  * Co-Occurring Out-of-Scope Edits (Clean Model Target): Per cross-family review requirements, when an in-scope grammar error co-occurs with other edits (e.g. concurrent `Spelling` or `Punctuation` errors in the same sentence), all non-noop edits from that annotator are applied to produce the target sentence. This ensures the model learns to generate orthographically clean, valid Ukrainian sentences rather than preserving concurrent typos. In-scope tagging, classification, and reasoning explanations remain strictly focused on the grammatical errors.
  * Global Pair-Level Uniqueness & Cross-Split Deduplication: Deduplication is strictly enforced across the dataset by content pair `(original_text, corrected_text)`. Distinct multi-annotator targets for the same source sentence are retained where they represent genuine alternative corrections. All evaluation split sentences (`original_text`, `corrected_text`, and clean controls) are strictly forbidden from the training split to guarantee zero data leakage.
* **Thin Categories (<50 examples in UA-GEC):**
  * **Preserve natural distribution. Zero synthetic reverse-corruption.**
  * LLM-generated "broken sentences" (reverse GEC) are strictly forbidden—they produce unauthentic slips that do not mirror human error distributions and violate Roadmap Rule 1 & Rule 2.
  * Sparse categories are retained as-is in the dataset. At training time, fine-grained sparse codes may be mapped to overarching linguistic families (e.g. valency/government classes) for loss weighting, but raw annotations remain unmodified.
  * In evaluation, thin categories must be reported in **stratified evaluation slices** so they are not obscured by micro-averages.
  * **100% of examples in categories with <50 instances** must be manually inspected during independent sampling.

---

### 2.3. Task Mix & Facet-Aware Explanation Grounding

* **Task Mix Partition:**
  * Correction rows are partitioned to balance proofreading efficiency and pedagogical reasoning:
    * **45% Silent Rewrites:** Direct text correction without metalinguistic commentary.
    * **55% Explained Corrections:** Direct text correction accompanied by concise, authoritative grammatical reasoning.
  * *Fail-Closed Citation Rule:* If an explanation cannot resolve an exact, authoritative citation, the row **drops its explanation and becomes a silent rewrite**. The post-drop ratio of explained corrections must remain strictly between **40.0% and 60.0%**.
* **Facet-Aware Authority Grounding:**
  * Citations must map directly to the specific linguistic facet being corrected, per [`ukrainian-linguistics.md`](../../../agents_extensions/shared/rules/ukrainian-linguistics.md) §4:
    * **Morphological inflection & wordforms:** VESUM (validates lemma, paradigm, inflectional features).
    * **Case government & valency:** Academic syntax authorities (e.g. *Словник дієслівного керування* / академічна граматика Вихованця). VESUM validates form existence, not context valency.
    * **Grammatical orthography & morpheme boundaries:** *Український правопис (2019)* citing the exact paragraph for in-scope compound prepositions (*з-під*, *з-над*) and hyphenated particles/pronouns (*будь-хто*, *казна-що*, *як-от*).
    * **Calques:** Борис Антоненко-Давидович (*Як ми говоримо*), Святослав Караванський (*Російсько-український словник складної лексики*). СУМ-20 is cited for explanatory definitions, not calque condemnation.
  * **100% of explained rows must carry a verified, resolvable citation.** Invented § numbers or generic "because Ukrainian grammar requires it" are strictly prohibited and fail the build.

---

### 2.4. Partition Integrity & Firewall

* **Official UA-GEC Test Firewall:**
  * All documents in the official UA-GEC `test` partition (`gec-fluency/test` and `gec-only/test`) are **frozen as held-out evaluation**.
  * No text, original sentence, or corrected target from the `test` partition may enter the training dataset, whether as a correction or as a clean control.
* **Document-Level Train/Validation Partition:**
  * Training and validation sets are partitioned **strictly by document ID (`doc_id`)** from `gec-fluency/train` at a frozen **90:10 ratio** using SHA-256 hashing:
    * Let $h = \text{int}(\text{SHA256}(\text{doc\_id}.\text{encode}(\text{'utf-8'})).\text{hexdigest}(), 16)$.
    * Document assigned to validation if $h \pmod{10} == 0$, else training.
  * Multi-annotator documents stay unified under their `doc_id` entirely within either the 90% train or the 10% validation slice.
  * 0 shared document IDs between train and validation splits.
  * 0 shared document IDs between training/validation and the official held-out `test` partition.
* **Near-Duplicate & Lemma Firewall:**
  * MinHash / Jaccard similarity $\ge 0.80$ against held-out evaluation documents is forbidden.
  * Per #8339 item 6, focal lexical items and verbal government pairs are evaluated by dictionary lemma base (e.g. *робити вигляд* and *зробити вигляд* are unified) to prevent train/test leakage through trivial aspectual prefixes.

---

### 2.5. Rights & Licensing Boundary

In accordance with Roadmap §3 Rule 8 and project licensing policy:
* **UA-GEC 2.0:** Licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
* **Brown-UK / БрУК:** Licensed under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)**.
* **Per-Source Rights Architecture:**
  * Rather than imposing a single blanket license overlay, rights and notices are tracked **per-source row** (matching `docs/projects/ua-eval-harness/THIRD_PARTY_NOTICES.md`).
  * Sentences derived from Brown-UK carry CC BY-NC-SA 4.0 notices.
  * Sentences derived from UA-GEC carry CC BY 4.0 notices.
  * No dataset-level ShareAlike or NonCommercial wrapper may be placed over CC BY 4.0 text (complying with CC BY 4.0 §2(a)(5)(b)).
  * No Brown-UK sentence may be released in training shards until its explicit per-source attribution record is finalized and verified.

---

## 3. Mechanical Acceptance Gates (#8339 Gate)

The automated acceptance checker built under [#8339](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8339) evaluates the dataset folder and **fails closed** (exit non-zero) if any of the following invariants are breached:

| Category | Invariant Check | Acceptance Threshold | Failure Action |
| :--- | :--- | :--- | :--- |
| **Mixture** | Clean Control Share | **20.0% to 30.0%** of unique examples | Fail if <20.0% or >30.0% |
| **Mixture** | Substantive Corrections | **70.0% to 80.0%** of unique examples | Fail if <70.0% or >80.0% |
| **Mixture** | Post-Drop Explained Corrections Share | **40.0% to 60.0%** of correction rows | Fail if <40.0% or >60.0% |
| **Duplicates** | Exact Duplicate Sentences | **0** duplicate `(source, target)` pairs | Fail if >0 |
| **Duplicates** | Near-Duplicate Padding | **0** synthetic word/number-swapped clones | Fail if >0 |
| **Concentration** | Top Substantive Skeleton | **≤5.0%** of rows in that field | Fail if >5.0% |
| **Concentration** | Top 10 Skeletons Combined | **≤25.0%** of rows in that field | Fail if >25.0% |
| **Concentration** | Normalized Skeleton Entropy | $H_{\text{norm}} \ge 0.80$, with $K \ge 50$ unique skeletons | Fail if $H_{\text{norm}} < 0.80$ or $K < 50$ |
| **Multi-field Check** | Skeletons Measured Separately | Question, reasoning, and answer evaluated independently | Fail if any single field collapses |
| **Split Integrity** | Document Leakage | **0** shared `doc_id`s between train, val, and held-out test | Fail if >0 |
| **Split Integrity** | Lemma-Normalized Overlap | **0** lemma-level overlap on focal constructions | Fail if detected |
| **Split Integrity** | MinHash Cross-Split Distance | **0** sentences with Jaccard similarity $\ge 0.80$ to test suite | Fail if detected |
| **Citations** | Resolvable Citation Hit Rate | **100.0%** of explained rows cite verified authorities | Fail if <100% |
| **Soviet Source Rule** | СУМ-11 Distortion Rule | **0** meanings/labels from СУМ-11; 0 words marked wrong/rare solely due to absence from СУМ-11 | Fail if detected |
| **Translation Rule** | Translation Dictionary Rule | **0** definitions derived from bilingual translation dictionaries | Fail if detected |
| **Self-Contradiction** | Internal Disagreement | **0** contradictory claims inside a single example | Fail if detected |
| **Dependencies** | Dictionary Accessibility | Required databases (`vesum.db`, `sources.db`) present and reachable | Fail closed if missing |
| **Human Audit** | Review Sample Package | Tool draws **300 random instances + 100% of thin categories (<50 instances)** | Blocks merge until reviewed |

### 3.1. Mathematical Definition of Normalized Skeleton Entropy

To provide exact reproducibility for the concentration check:
1. **Delexicalization:** In each field (question, reasoning, answer), every quoted span («…», "…") is replaced by `«…»` and every contiguous run of digits is replaced by `#`.
2. **Skeleton Frequencies:** Let $K$ be the number of distinct delexicalized skeletons, with empirical frequencies $p_1, p_2, \dots, p_K$ ($\sum p_i = 1$).
3. **Entropy Calculation:**
   $$H = -\sum_{i=1}^K p_i \ln p_i$$
   $$H_{\text{norm}} = \begin{cases} 0 & \text{if } K \le 1 \\ \frac{H}{\ln K} & \text{if } K > 1 \end{cases}$$
4. **Historical Baseline Proof (v05):** In `uldr_v05`, 13 question skeletons covered 100% of 35,000 lines ($K=13$). The gate $H_{\text{norm}} \ge 0.80 \land K \ge 50 \land \text{top-1} \le 5.0\%$ fails `uldr_v05` deterministically because $K = 13 < 50$.

---

## 4. Model Training & Behavioral Diagnostic Targets (#8338 Gate)

Static dataset acceptance (#8339) qualifies the dataset files. Behavioral verification of the fine-tuned Gemma 3 4B model occurs under [#8338](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8338):

1. **Relation to Production Gate 3 (Non-Negotiable Qualification):**
   * **Gate 3 (`PRODUCTION_RELEASE_PLAN.md` §3.2) remains binding for final production qualification:** $k = 0$ harmful edits on $N = 300$ clean sentences (Clopper-Pearson 95% upper bound $\le 0.994\%$).
   * The metrics below are intermediate diagnostic training targets for #8338 on development splits; they do **not** relax, replace, or supersede Gate 3.
2. **Intermediate Diagnostic Targets on Development Split (Carved from `gec-fluency/train`):**
   * Checkpoint selection during training is determined strictly by maximizing edit-level $F_{0.5}$ on in-scope tags (`F/Calque` + `G/*`) over the 10% validation split (`doc_id` disjoint from train), subject to passing the unnecessary-edit constraint.
   * Tested on a dedicated evaluation slice containing **at least $N \ge 1,000$ verified clean Ukrainian sentences** (drawn from unused Brown-UK sentences and validation gold target sentences, strictly disjoint by `doc_id` from the 90% training data and controls):
     * Diagnostic unnecessary-edit rate on clean sentences: point estimate $\le 1.0\%$, one-sided 95% Clopper-Pearson upper bound $< 2.0\%$.
   * Precision and recall are reported separately across coarse and fine error categories on the validation split.
3. **Frozen Final Scorecard (Post-Training Stop):**
   * Only after training is stopped and checkpoint selection is frozen, the official held-out UA-GEC `test` partition is evaluated once using the frozen `ua-eval-harness` protocol (`F/Calque` + all `G/*` tags) for the published repository scorecard.
   * Edit-level $F_{0.5}$ on the official test set must demonstrate measurable improvement over the baseline Gemma 3 4B checkpoint.
