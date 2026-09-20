# Grammar Dataset Specification: UA-GEC Redo & Acceptance Invariants (#8342, #8339)

> **Parent Epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
> **Specific Issues:** [#8342](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8342) (Grammar set redo), [#8339](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8339) (Acceptance checker), [#8338](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8338) (Training & diagnostic scorecard)
> **Target Model:** Gemma 3 4B fine-tuning on Hugging Face (Pro GPU infrastructure)
> **Established Date:** 2026-09-20 (Cross-Model Deliberation: Astra, Grok 4.6, Gemini 3.1 Pro; Revised per Round 2 CF Review)

---

## 1. Context & Motivation

In the review of Epic #6321 and PR #8345, the previous grammar release `uldr_v05_grammar_valency` (35,000 lines) was analyzed:
* **93% passivity:** 32,629 of 35,000 rows were labeled as controls ("nothing wrong here"), with only 2,371 rows of real corrections.
* **Template collapse:** 13 question patterns covered 100% of the 35,000-line dataset (top-1 pattern covered 48.2%; top-10 patterns covered 98.4%).
* **Class deficit:** 8 of 20 error categories had fewer than 50 examples.

Issue #8342 replaces this dataset by rebuilding from authentic human-annotated sentences in UA-GEC. The old `uldr_v05_grammar_valency` release files are quarantined and marked "do not use".

This document defines the binding specification, composition ratios, rights boundaries, grounding authorities, and mechanical acceptance gates (#8339) for the replacement dataset.

---

## 2. Core Dataset Architecture

### 2.1. Control-to-Correction Ratio & Provenance

* **Single Binding Mixture Interval:**
  * **Clean Controls:** Strictly **20% to 30%** of unique training examples (target: **25%**).
  * **Real Corrections:** Strictly **70% to 80%** of unique training examples (target: **75%**).
  * **Acceptance Rule:** The checker fails closed if clean controls are **< 20.0%** (hyper-correction risk) or **> 30.0%** (passivity risk). No second or loose threshold exists.
* **Control Provenance (Zero Synthetic Text):**
  * Controls must **never be synthetically manufactured** by rule engines, corruption scripts, or LLM prompt generation.
  * Controls are drawn exclusively from two verified sources:
    1. Vetted clean sentences from editor-reviewed corpora (e.g. BRUK / Brown-UK).
    2. Gold target sentences from complex UA-GEC instances, restricted strictly to documents within the **training partition** (see §2.4).
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
  * Closed list of in-scope grammatical error tags:
    * **Morphology & Agreement:** `G/Case`, `G/Gender`, `G/Number`, `G/Agreement`, `G/Participle`
    * **Syntax & Government:** `G/Prep`, `G/Valency`, `G/VerbVoice`, `G/Tense`, `G/UngrammaticalStructure`, `G/Conjunction`
    * **Grammaticalized Lexicon:** `F/Calque`, `F/Collocation`
  * All other non-grammatical categories (e.g. `P/*` purely stylistic punctuation, `O/*` orthography/typos, `F/Other`) are excluded from this specific grammar set.
  * The extracted unique sentence count from this closed tag set on the UA-GEC `train` split forms the immutable baseline denominator $N_{\text{raw}}$.
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
  * *Fail-Closed Citation Rule:* If an explanation cannot resolve an exact, authoritative citation, the row **drops its explanation and becomes a silent rewrite**. The post-drop ratio of explained corrections must remain between **40% and 60%**.
* **Facet-Aware Authority Grounding:**
  * Citations must map directly to the specific linguistic facet being corrected, per [`ukrainian-linguistics.md`](../../../agents_extensions/shared/rules/ukrainian-linguistics.md) §4:
    * **Morphological inflection & wordforms:** VESUM (validates lemma, paradigm, inflectional features).
    * **Case government & valency:** Academic syntax authorities (e.g. *Словник дієслівного керування* / академічна граматика Вихованця). VESUM validates form existence, not context valency.
    * **Spelling, apostrophe, hyphens, prefixes:** *Український правопис (2019)* citing the exact paragraph.
    * **Calques & collocations:** Борис Антоненко-Давидович (*Як ми говоримо*), Святослав Караванський (*Пошук українського слова*). СУМ-20 is cited for explanatory definitions, not calque condemnation.
  * **100% of explained rows must carry a verified, resolvable citation.** Invented § numbers or generic "because Ukrainian grammar requires it" are strictly prohibited and fail the build.

---

### 2.4. Partition Integrity & Firewall

* **Official UA-GEC Test Firewall:**
  * All documents in the official UA-GEC `test` partition (`gec-fluency/test` and `gec-only/test`) are **frozen as held-out evaluation**.
  * No text, original sentence, or corrected target from the `test` partition may enter the training dataset, whether as a correction or as a clean control.
* **Document-Level Split:**
  * Training and validation splits are partitioned **strictly by document ID (`doc_id`)**, never by sentence shuffling.
  * 0 shared document IDs across train and test.
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
| **Duplicates** | Exact Duplicate Sentences | **0** duplicate `(source, target)` pairs | Fail if >0 |
| **Duplicates** | Near-Duplicate Padding | **0** synthetic word/number-swapped clones | Fail if >0 |
| **Concentration** | Top Substantive Skeleton | **≤5.0%** of rows in that field | Fail if >5.0% |
| **Concentration** | Top 10 Skeletons Combined | **≤25.0%** of rows in that field | Fail if >25.0% |
| **Concentration** | Normalized Skeleton Entropy | $H_{\text{norm}} \ge 0.80$, with $K \ge 50$ unique skeletons | Fail if $H_{\text{norm}} < 0.80$ or $K \le 1$ |
| **Multi-field Check** | Skeletons Measured Separately | Question, reasoning, and answer evaluated independently | Fail if any single field collapses |
| **Split Integrity** | Document Leakage | **0** shared `doc_id`s between train and held-out test | Fail if >0 |
| **Split Integrity** | Lemma-Normalized Overlap | **0** lemma-level overlap on focal constructions | Fail if detected |
| **Split Integrity** | MinHash Cross-Split Distance | **0** sentences with Jaccard similarity $\ge 0.80$ to test suite | Fail if detected |
| **Citations** | Resolvable Citation Hit Rate | **100.0%** of explained rows cite verified authorities | Fail if <100% |
| **Soviet Source Rule** | СУМ-11 Distortion Rule | **0** meanings/labels from СУМ-11; 0 words marked wrong/rare solely due to absence from СУМ-11 | Fail if detected |
| **Translation Rule** | Translation Dictionary Rule | **0** definitions derived from bilingual translation dictionaries | Fail if detected |
| **Self-Contradiction** | Internal Disagreement | **0** contradictory claims inside a single example | Fail if detected |
| **Dependencies** | Dictionary Accessibility | Required databases (`vesum.db`, `sources.db`) present and reachable | Fail closed if missing |
| **Human Audit** | Review Sample Package | Tool draws **300 random instances + 100% of thin categories (<50 instances)** | Blocks merge until reviewed |

### 3.1. Mathematical Definition of Normalized Skeleton Entropy

To provide exact reproduciblity for the concentration check:
1. **Delexicalization:** In each field (question, reasoning, answer), every quoted span («…», "…") is replaced by `«…»` and every contiguous run of digits is replaced by `#`.
2. **Skeleton Frequencies:** Let $K$ be the number of distinct delexicalized skeletons, with empirical frequencies $p_1, p_2, \dots, p_K$ ($\sum p_i = 1$).
3. **Entropy Calculation:**
   $$H = -\sum_{i=1}^K p_i \ln p_i$$
   $$H_{\text{norm}} = \begin{cases} 0 & \text{if } K \le 1 \\ \frac{H}{\ln K} & \text{if } K > 1 \end{cases}$$
4. **Historical Baseline Proof (v05):** In `uldr_v05`, 13 question skeletons covered 100% of 35,000 lines (top-1 was 48.2%, top-10 was 98.4%, $K=13$). The gate $H_{\text{norm}} \ge 0.80 \land K \ge 50 \land \text{top-1} \le 5.0\%$ fails `uldr_v05` deterministically.

---

## 4. Model Training & Behavioral Diagnostic Targets (#8338 Gate)

Static dataset acceptance (#8339) qualifies the dataset files. Behavioral verification of the fine-tuned Gemma 3 4B model occurs in [#8338](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8338):

1. **Relation to Production Gate 3 (Non-Negotiable Qualification):**
   * **Gate 3 (`PRODUCTION_RELEASE_PLAN.md` §3.2) remains binding for final production qualification:** $k = 0$ harmful edits on $N = 300$ clean sentences (Clopper-Pearson 95% upper bound $\le 0.994\%$).
   * The metrics below are intermediate diagnostic training targets for #8338 on development splits; they do **not** relax, replace, or supersede Gate 3.
2. **Intermediate Diagnostic Targets on Development Set:**
   * Tested on an independent set of $\ge 1,000$ verified clean sentences (disjoint from training controls):
     * Diagnostic unnecessary-edit rate: point estimate $\le 1.0\%$, one-sided 95% Clopper-Pearson upper bound $< 2.0\%$.
   * Edit-level $F_{0.5}$ on the official UA-GEC held-out test set must demonstrate measurable improvement over the baseline Gemma 3 4B checkpoint.
   * Precision and recall must be reported separately across coarse and fine error categories.
