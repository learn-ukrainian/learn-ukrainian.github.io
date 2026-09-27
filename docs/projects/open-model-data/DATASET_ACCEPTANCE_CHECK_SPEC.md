# Dataset Acceptance Check Specification (#8339)

> **Parent Epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321) (`[EPIC][open-model-data] Open dataset for proper, decolonized modern Ukrainian`)
> **Specific Issue:** [#8339](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8339) (`Acceptance check for every dataset: repeats, form letters, source rules`)
> **Target Scope:** Universal, automated, fail-closed gate for every dataset in Epic #6321 (#8140, #8340, #8341, #8342, #8141, #8330)
> **Date:** 2026-09-21 (Revised per Cross-Family Review M1–M5)
> **Author:** Yellow Team (Gemini)
> **Reviewer Family:** Blue Team (Claude Sonnet / Cross-Family Independent Review: `APPROVE WITH COMMENTS`)

---

## 1. Executive Summary & Problem Statement

In earlier phases of Epic #6321, datasets were accepted based on coarse line counts and structural JSON Schema validation. That let through massive quality collapse:
1. **75,000 lines** in `uldr_v06_general_assistant` that were merely **4,220 unique examples** copied up to 398 times under random UUIDs.
2. **35,000 lines** in `uldr_v05_grammar_valency` where **32,629 rows (93.2%)** were passive controls ("nothing wrong here"), only **2,371 rows** were real corrections, and **13 question patterns** covered 100% of the corpus.
3. **10,000 lines** in `uldr_v04a_kyivan_rus` where **467 records** were labeled "XI–XIII century" while their own first reasoning step gave a date range starting between 1400 and 1999, and **5 question patterns** covered 94.1% of lines.
4. **10,000 lines** in `uldr_v04b_middle_ukrainian` where **20 reasoning patterns** covered 98.8% of lines (142 patterns in all), and **5 question patterns** covered 90.2%.

Line counts and JSON schemas cannot detect semantic emptiness, rote repetition, or colonial distortion. Training a neural model on heavily copied, patterned form letters risks teaching the model the pattern rather than authentic Ukrainian language and reasoning.

Issue #8339 establishes a mandatory, automated, fail-closed acceptance tool:
`scripts/projects/open_model_data/audit_dataset_acceptance.py`.

### Core Architectural Invariants

* **Fail Closed:** The tool exits non-zero (`exit 1`) whenever any acceptance threshold is breached. It exits `exit 2` if required dictionary dependencies (e.g. `vesum.db`) are missing or unreadable. It **never passes by default**.
* **Plain Numbers:** Output presents exact counts, ratios, and percentages; no vague qualitative hand-waving.
* **Reproduce Human Discoveries:** The tool must deterministically reproduce the exact findings recorded in `ROADMAP_250K_SOVEREIGN_UKRAINIAN.md` §2 on the baseline datasets.
* **Separation of Concerns:** Infrastructure audits check repeatability, concentration, contradictions, and source rules. Linguistic correctness is audited by human language reviewers using an un-cherry-picked sample drawn deterministically by this tool.
* **Enforceable Human Audit Lifecycle (M2):** Automated checks passing produces `PASSED_AUTOMATED_CHECKS`. Final dataset acceptance requires a signed human language review report bound to the dataset SHA-256.

---

## 2. Command Interface & Architecture

### 2.1. CLI Invocation

```bash
.venv/bin/python scripts/projects/open_model_data/audit_dataset_acceptance.py \
    <dataset_dir> \
    [--profile <name>] \
    [--sample-out <path>] \
    [--sample-size 300] \
    [--json-out <path>] \
    [--vesum-db <path>] \
    [--sources-db <path>] \
    [--verify-human-signoff <path>] \
    [--fail-fast]
```

### 2.2. Arguments & Configuration

* `dataset_dir` (positional, required): Path to dataset folder (e.g., `data/projects/open_model_data/export/uldr_v06_ulif_phraseology`). Scans all JSONL shards across `sft/`, `dpo/`, and evaluation splits (`eval/`, `*_eval.jsonl`).
* `--profile` (optional, default: `default`): Named, repository-committed acceptance profile from `scripts/projects/open_model_data/profiles/` (e.g., `grammar_8342`, `phraseology_8140`, `general_assistant_8341`). Arbitrary external YAML config paths are refused unless `--allow-uncommitted-config` is explicitly set, preventing authors from quietly loosening gates (M5).
* `--sample-out` (optional): Output path for the drawn reviewer sample package. Default: `<dataset_dir>/acceptance_review_sample.md` (and paired `.json`).
* `--sample-size` (optional, default: `300`): Number of records to draw for the human audit package ($n=300$ gives $>95\%$ detection power for a 1% defect rate; M3).
* `--json-out` (optional): Output path for machine-readable JSON acceptance scorecard.
* `--vesum-db` (optional): Path to `vesum.db`. Defaults to auto-resolved `data/vesum.db` or primary checkout copy via `VESUM_DB_PATH`. Fails closed (`exit 2`) if missing.
* `--sources-db` (optional): Path to `sources.db`. Fails closed (`exit 2`) if explicitly specified and missing.
* `--verify-human-signoff` (optional): Path to signed human reviewer report. If supplied, verifies signature, cross-family author identity, dataset SHA-256 binding, and rubric thresholds (M2).
* `--fail-fast` (optional): Abort immediately on first failing check rather than executing all 7 checks.

### 2.3. Exit Codes & Lifecycle States

* `0`: `ACCEPTED` (Automated checks passed AND valid human sign-off verified via `--verify-human-signoff`), OR `PASSED_AUTOMATED_CHECKS` (automated checks passed; human sample generated and pending review).
* `1`: `ACCEPTANCE_FAILED` (One or more threshold limits breached).
* `2`: `OPERATIONAL_ERROR` (Missing database files, unreadable inputs, or malformed JSONL records).
* `3`: `PENDING_HUMAN_REVIEW` (Automated checks passed, but `--require-human-signoff` was specified and sign-off is absent).

---

## 3. The Seven Acceptance Checks: Detailed Specification

### Check 1: Repeats (Exact Copies and Near-Copies)

#### 1.1. Ukrainian Text Normalization

To prevent false negatives from surface formatting tricks, all text comparison applies canonical normalization:
* Unicode NFKC normalization.
* Apostrophe unification: `’` (U+2019), `ʼ` (U+02BC), `` ` `` (U+0060) $\rightarrow$ `'` (U+0027).
* Stress mark stripping: remove combining acute accent `\u0301`.
* Whitespace collapse: strip leading/trailing whitespace and collapse internal whitespace runs.

#### 1.2. Exact Duplicates

* **Definition:**
  * For SFT / instruction rows: normalized tuple `(query, final_response)`.
  * For DPO rows: normalized tuple `(prompt, chosen, rejected)` (ensuring shared prompts with distinct rejected responses are not false-flagged).
  * For chat format: normalized sequence of `messages` `(role, content)`.
* **Metric:**
  $$\text{Exact Duplicate Count} = N_{\text{total}} - N_{\text{distinct\_QA}}$$
  $$\text{Exact Duplicate Rate} = \frac{\text{Exact Duplicate Count}}{N_{\text{total}}}$$
  $$\text{Max Single Multiplicity} = \max \text{count}(q, a)$$
* **Threshold:**
  * **Exact Duplicate Rate = 0.0%** (0 duplicates allowed).
  * **Max Single Multiplicity = 1**.
  * Every row in a released dataset must be unique. (In `uldr_v06`, 75,000 rows contained only 4,220 distinct QA pairs: Duplicate Rate = 94.4%!).

#### 1.3. Near-Duplicates (Template Clones & Clusters)

* **Measurement:**
  * MinHash with 128 permutation hashes over character 4-grams and token 2-grams.
  * LSH candidate clustering with exact token Jaccard verification on candidate pairs.
  * Cluster definition: A connected component of records where pairwise Jaccard $\ge 0.85$.
  * $\text{Near-Duplicate Count} = \sum_{\text{cluster } C} (|C| - 1)$.
  * $\text{Near-Duplicate Rate} = \frac{\text{Near-Duplicate Count}}{N_{\text{total}}}$.
* **Threshold:**
  * **Near-Duplicate Rate $\le 1.0\%$** of rows.

---

### Check 2: Form Letters (Pattern Concentration)

#### 2.1. Delexicalization Engine

To ensure unquoted variable slots or differing punctuation do not bypass detection:
1. **Extended Quote Masking:** Replace all Ukrainian and typographic quote pairs with `<QUOTED_SPAN>`:
   * `«[^»]*»`, `"[^"]*"`, `“[^”]*”`, `„[^“]*“`, `‘[^’]*’`.
2. **Numerical Runs:** Replace `\d+` with `#`.
3. **Step-Level Reasoning Decomposition:**
   * Multi-step reasoning chains are split into numbered steps (`1. ...`, `2. ...`). Skeletons are tracked both at the full-chain level and at the per-step level to detect single-step template reuse.

#### 2.2. Metrics per Field (`query`, `reasoning`, `answer`)

* $K$: Number of distinct delexicalized patterns.
* $\text{Top-1, Top-5, Top-10, Top-20 Share}$: Cumulative percentage of dataset covered.
* **Effective Pattern Perplexity:**
  $$H = -\sum_{i=1}^K p_i \ln p_i$$
  $$\text{Perplexity} = e^H$$
  $$\text{Normalized Entropy } H_{\text{norm}} = \frac{H}{\ln K} \quad (\text{for } K > 1)$$

#### 2.3. Thresholds & Scaling

* **For `reasoning` (Chain of Thought):**
  * Top-1 Share $\le 10.0\%$
  * Top-5 Share $\le 25.0\%$
  * Top-20 Share $\le 50.0\%$
  * Effective Pattern Perplexity $e^H \ge 25.0$
  * Unique Skeletons $K \ge \min(50, \lfloor N \times 0.05 \rfloor)$
  * Normalized Entropy $H_{\text{norm}} \ge 0.80$
* **For `answer` (`final_response`):**
  * Top-1 Share $\le 5.0\%$
  * Top-5 Share $\le 15.0\%$
  * Top-20 Share $\le 30.0\%$
  * Effective Pattern Perplexity $e^H \ge 35.0$
  * Unique Skeletons $K \ge \min(50, \lfloor N \times 0.05 \rfloor)$
  * Normalized Entropy $H_{\text{norm}} \ge 0.80$
* **For `query` (Prompt):**
  * Top-5 Share $\le 80.0\%$
  * Unique Skeletons $K \ge \min(20, \lfloor N \times 0.02 \rfloor)$
* **Missing Field Semantics:** If a dataset manifest declares a task type with no reasoning steps (e.g. `direct_qa`, `phraseology_gloss`), reasoning check reports `NOT_APPLICABLE` (neutral). If reasoning is declared or expected for that task type and absent, the check fails closed.

---

### Check 3: Real Content Share (for Correction & Normative Sets)

#### 3.1. Applicability & Manifest Declaration

* The dataset `manifest.json` must declare its `task_type`: `correction`, `classification`, `generation`, or `glossary`. If undeclared, the tool fails closed.
* Content share rules apply strictly to declared `correction` tasks.

#### 3.2. Substantive Diff Measurement

* `is_erroneous == True` requires a substantive lexical/grammatical edit:
  * Difference between `original_text` and `corrected_text` after whitespace and punctuation normalization must be non-empty ($\ge 1$ modified word token). Whitespace-only or punctuation-only edits do not count as substantive corrections.

#### 3.3. Thresholds

* **General Correction Datasets:** Substantive Real Corrections Share $\ge 50.0\%$.
* **Grammar Redo Specification (#8342 Calibration):**
  * Clean Controls: strictly **20.0% to 30.0%** of total examples.
  * Real Corrections: strictly **70.0% to 80.0%** of total examples.
  * Fail closed if controls $> 30.0\%$ (passivity) or $< 20.0\%$ (hyper-correction).
* **Taxonomy Balance & Thin Categories:**
  * Maximum share for any single error category $\le 40.0\%$ (preventing 1 trivial error swamping the dataset).
  * No declared error subtype may have $< 50$ examples, unless verified as an upstream corpus limit (in which case 100% of available instances are audited in Check 7).

---

### Check 4: Self-Contradiction Audit

#### 4.1. Failure Modes Audited

1. **Chronological / Period Contradiction:**
   * Evaluated strictly on designated date fields and the initial reasoning step (Step 1 paleographic/historical localization), avoiding false positives from incidental historical commentary.
   * If metadata declares `XI–XIII ст.` / `kyivan_rus`, but Step 1 dating extracts a range starting $\ge 1400$ (e.g. `(1585–1700 рр.)`), flag contradiction.
2. **Label vs Text Contradiction:**
   * `is_erroneous == True` with empty substantive diff.
   * `is_erroneous == False` with substantive diff.
   * `is_calque_or_russianism == False` while final response concludes the term is a Russianism or calque.
   * `is_calque_or_russianism == True` while final response concludes the term is authentic Ukrainian.
   * Declared error span is missing from `original_text`.
   * `corrected_text` still contains the flagged error span uncorrected.
3. **Target Term Alignment (Lemmatized):**
   * Declared `target_term` must match a token in `query`, `original_text`, or `reasoning_steps` using **VESUM lemma matching** (not exact substring), ensuring inflected word forms (*«вигляду»* for lemma *«вигляд»*) match cleanly.
4. **Linguistic Pre-Training Contamination Gate:**
   * Automated check on `corrected_text` and `final_response`: flag non-Ukrainian Russian-shadow contamination (`check_russian_shadow`) and VESUM out-of-vocabulary anomalies.

#### 4.2. Threshold

* **Allowed Self-Contradictions: 0 (0.0% tolerance).**

---

### Check 5: Source Rules (Epic Rules 3 & 4)

#### 5.1. Detection Design (Structured Provenance & Sourcing)

1. **Structured Source IDs:** Every record with a definition, normative claim, or error identification must carry structured provenance in `source_metadata` or `evidence_source` (e.g. `source_id: "sum20"`, `source_id: "antonenko_davydovych"`).
2. **Soviet Dictionary (СУМ-11) Distortion Boundary:**
   * **Aliases Tracked:** `sum11`, `sum_11`, `СУМ-11`, `Словник української мови (1970–1980)`, bare `СУМ` with date 1970-1980.
   * **Allowed Usage:** Strictly confined to contrastive Soviet colonization context fields: `soviet_colonization_context`, `historical_suppression_note`.
   * **Prohibited Usage:** Appearing as `primary_authority`, `normative_definition`, or `standard_source` $\rightarrow$ **FAIL (0 allowed)**.
   * **Negative Inference Prohibition:** Text asserting a word is wrong, rare, or dialectal because it is absent from СУМ-11 (`відсутн\w+ в СУМ-11`, `не зафіксован\w+ в СУМ-11.*тому.*помилк`) $\rightarrow$ **FAIL (0 allowed)**.
   * **Soviet Ideological Definitions:** Definition text matching СУМ-11 text flagged with `sovietization_risk` $\rightarrow$ **FAIL (0 allowed)**.
3. **Translation Dictionary Denylist:**
   * Definitions sourced from bilingual translation dictionaries (`r2u`, `e2u`, `balla_en_uk`, `dmklinger_uk_en`, `translate_en_uk`, or generic bilingual glosses) $\rightarrow$ **FAIL (0 allowed)**. Ukrainian is explained in Ukrainian.
4. **Approved Authority Grounding:**
   * Authorities cited must match approved scholarship per `ukrainian-linguistics.md` §4: VESUM, Український правопис (2019), СУМ-20, ВТС, Горох (goroh.pp.ua), Б. Антоненко-Давидович, С. Караванський, Б. Грінченко (1907–1909), ЕСУМ, ULIF.

#### 5.2. Threshold

* **Citing СУМ-11 as normative authority: 0 instances.**
* **Negative inference from СУМ-11 absence: 0 instances.**
* **Definitions from bilingual translation dictionaries: 0 instances.**
* **Unapproved/unverified authorities: 0 instances.**

---

### Check 6: Train/Test Overlap (Lemmatized & Aspect-Normalized)

#### 6.1. Curated Aspect Pair Linking & Lemma Disambiguation

Rather than lossy heuristic affix stripping, verbal aspect partners are normalized using:
1. **Curated Aspect Pair Dictionary:** A dedicated pairing table (`data/lexicon/aspect_pairs.json` and VESUM aspectual cross-references) linking imperfective and perfective verbs (*робити / зробити*, *брати / взяти*, *говорити / сказати*, *писати / написати*, *збирати / зібрати*).
2. **Homograph Multi-Lemma Sets:** For homographs (e.g. *«мала»* $\rightarrow$ noun or verb), all valid candidate lemmas are retained as a set.
3. Under this mapping, *«робити вигляд»* and *«зробити вигляд»* resolve to the identical aspect-unified lemma bigram: `("робити [aspect_pair: зробити]", "вигляд")`.

#### 6.2. Overlap Measurement & Per-Record Containment

* **Exact Query / Target Sentence Leakage:** 0 identical queries between train (`sft/`, `dpo/`) and eval splits.
* **Target Phenomenon Leakage:** 0 overlap between evaluation target terms and training target terms (for phenomenon splits).
* **Per-Eval-Record 4-Gram Containment:**
  * For each evaluation record $r_{\text{eval}}$, extract non-boilerplate 4-grams (excluding generic prompts occurring in $> 20\%$ of instances).
  * Compute maximum 4-gram containment against the training corpus:
    $$\text{Containment}(r) = \frac{|\text{4-grams}(r) \cap \text{Train 4-grams}|}{|\text{4-grams}(r)|}$$
  * Count share of eval records with high containment ($\ge 0.50$).

#### 6.3. Thresholds

* **Exact Train/Eval Sentence Overlap: 0 instances (0.0%).**
* **Eval Target Phenomenon Leakage: 0 instances (0.0%).**
* **Eval Records with 4-Gram Containment $\ge 0.50$: $\le 2.0\%$.**
* **Missing Split Policy:** If the dataset manifest specifies an evaluation split and the split is missing $\rightarrow$ **FAIL**. If the manifest explicitly designates a training-only dataset $\rightarrow$ Check 6 reports `NOT_APPLICABLE`.

---

### Check 7: Deterministic Random Sample Drawer & Review Lifecycle

#### 7.1. Un-Cherry-Pickable Sampling (M3)

* **Seed Derivation:** The sampling seed is computed deterministically from the SHA-256 of the dataset content:
  $$\text{Seed} = \text{int}(\text{SHA256}(\text{Dataset\_Manifest\_SHA256} + \text{Salt})[:8], 16)$$
* **Content Hash Ranking:** Records are sampled by hashing `SHA256(Seed + Record_Content)` and taking the top $n$ ranks, preventing manipulation via file reordering or UUID injection.
* **Sample Size & Power:**
  * Base sample: **$n = 300$ instances** (guaranteeing $> 95\%$ probability of detecting any defect with $\ge 1\%$ prevalence).
  * Stratified across splits (SFT, DPO) and categories.
  * Thin-category exhaustion: up to 20 instances per thin category ($< 50$ instances), capped at 100 extra instances total.
* **Artifacts Emitted:**
  * `acceptance_review_sample.md`: Rich Markdown file for human reading.
  * `acceptance_review_sample.json`: Machine-parseable sidecar for review tool integration.

#### 7.2. Reviewer Rubric & Evidence Schema

For each sampled record, the reviewer evaluates:
* [ ] **1. Чистота мови:** Відсутність русизмів, кальок, суржику.
* [ ] **2. Природність:** Автентичний український синтаксис та ідіоматика.
* [ ] **3. Джерела:** Тлумачення та норми підтверджені авторитетними джерелами.
* [ ] **4. Деколонізація:** Відсутність радянських/імперських ідеологічних кліше.
* [ ] **5. Точність:** Відсутність фактологічних або логічних помилок.
* **Severity Classification:** `BLOCKER` (defective language / hallucinated source / Soviet distortion) vs `MINOR` (stylistic nuance).
* **Evidence Citation:** Reviewer must cite specific tool/source evidence (e.g. СУМ-20, Правопис 2019).

#### 7.3. Sign-Off Verification (`--verify-human-signoff`) (M2)

To achieve final `ACCEPTED` state:
* Reviewer sign-off file (`acceptance_review_signoff.json`) must be present.
* Bound to the exact `dataset_sha256`.
* Signed by a reviewer from an independent cross-family team.
* Total `BLOCKER` defects: **0**.

---

## 4. Empirical Baseline Reproduction

Running the checker against the four earlier datasets reproduces the findings from `ROADMAP_250K_SOVEREIGN_UKRAINIAN.md` §2:

| Dataset | Metric / Phenomenon | Recorded in Roadmap §2 | Check Number | Acceptance Status |
| :--- | :--- | :--- | :--- | :--- |
| **`uldr_v06_general_assistant`** | Total Rows | 75,000 | Baseline | — |
| | Distinct QA Pairs | **4,220** | Check 1 (Repeats) | **FAIL** (94.4% dups) |
| | Top Repeated QA Multiplicity | **398 times** | Check 1 (Repeats) | **FAIL** (Max multi = 398) |
| **`uldr_v05_grammar_valency`** | Total Rows | 35,000 | Baseline | — |
| | Clean Controls ("nothing wrong") | **32,629 (93.2%)** | Check 3 (Content Share) | **FAIL** (Passive > 30%) |
| | Substantive Corrections | **2,371 (6.8%)** | Check 3 (Content Share) | **FAIL** (Corrections < 50%) |
| | Categories with < 50 examples | **8 of 20 categories** | Check 3 (Content Share) | **FAIL** (Thin categories) |
| | Distinct Question Patterns | **13 patterns (100%)** | Check 2 (Form Letters) | **FAIL** ($K = 13 < 50$) |
| **`uldr_v04a_kyivan_rus`** | Total Rows | 10,000 | Baseline | — |
| | Date Contradictions (XI–XIII vs 1585–1700) | **467 records** | Check 4 (Contradiction) | **FAIL** (467 contradictions) |
| | Top 5 Question Pattern Share | **9,412 (94.1%)** | Check 2 (Form Letters) | **FAIL** (Top 5 > 80%) |
| **`uldr_v04b_middle_ukrainian`** | Total Rows | 10,000 | Baseline | — |
| | Total Reasoning Patterns ($K$) | **142 patterns** | Check 2 (Form Letters) | Baseline |
| | Top 20 Reasoning Patterns Share | **9,877 (98.8%)** | Check 2 (Form Letters) | **FAIL** (Top 20 > 50%) |
| | Top 5 Question Patterns Share | **9,022 (90.2%)** | Check 2 (Form Letters) | **FAIL** (Top 5 > 80%) |
| **`uldr_v06_ulif_phraseology`** | Distinct Answer Patterns ($N=10,414$) | **9,710 (93.2%)** | Check 2 (Form Letters) | **PASS** (Diverse answers) |
| | Top 20 Answer Patterns Share | **3.8%** | Check 2 (Form Letters) | **PASS** (Top 20 < 30%) |

---

## 5. Configuration Profiles & Tamper Protection (M5)

To prevent arbitrary threshold weakening, configurations are strictly managed:
* Profiles reside in `scripts/projects/open_model_data/profiles/*.yaml`.
* The tool computes the SHA-256 hash of the effective profile.
* The emitted JSON scorecard embeds:
  * `dataset_sha256`
  * `profile_name` and `profile_sha256`
  * Complete threshold dictionary and measured values
  * Check outcome statuses (`PASS`, `FAIL`, `NOT_APPLICABLE`)
* Any edit to the dataset files after the audit automatically invalidates the scorecard.

---

## 6. Implementation & Test Suite Architecture

### 6.1. Script Architecture (`scripts/projects/open_model_data/audit_dataset_acceptance.py`)

```
audit_dataset_acceptance.py
├── Data Models (DatasetRecord, AcceptanceReport, CheckResult, ConfigProfile)
├── Text Normalization & Delexicalization (Quotes, Numbers, NFKC, Whitespace)
├── Aspect Pair Engine (Curated table + VESUM tag cross-referencing)
├── Check 1: RepeatsAuditor (Exact & LSH MinHash Near-Duplicates)
├── Check 2: PatternConcentrationAuditor (Query, Reasoning, Answer; Perplexity)
├── Check 3: ContentShareAuditor (Controls vs Substantive Corrections)
├── Check 4: ContradictionAuditor (Step 1 Dates, Label vs Text Diffs, Target Terms)
├── Check 5: SourceRuleAuditor (СУМ-11 aliases, Negative Inferences, Translation Dicts)
├── Check 6: SplitOverlapAuditor (Aspect-linked Lemmatized Containment)
├── Check 7: ReviewSampleDrawer (Content-hashed Seed, 300 instances, MD + JSON)
└── CLI Runner & Reporter (Console formatting, JSON scorecard emission, Exit codes)
```

### 6.2. Test Suite Architecture (`tests/projects/open_model_data/test_audit_dataset_acceptance.py`)

* **Seven Deliberately Bad Fixtures (Asserting Specific Metric Failures):**
  1. `test_check1_fails_on_duplicate_rows`: Asserts `duplicate_count > 0`, `duplicate_rate > 0.0%`.
  2. `test_check2_fails_on_form_letter_reasoning`: Asserts `reasoning_top20_share > 0.50`, `perplexity < 25.0`.
  3. `test_check3_fails_on_excessive_passive_controls`: Asserts `passive_control_share > 0.30`.
  4. `test_check4_fails_on_chronological_contradiction`: Asserts `contradiction_count > 0` on Step 1 date mismatch.
  5. `test_check5_fails_on_soviet_sum11_normative_use`: Asserts `sum11_normative_violations > 0`.
  6. `test_check6_fails_on_aspect_pair_leakage`: Asserts `high_containment_share > 0.02` when *«робити вигляд»* leaks into eval *«зробити вигляд»*.
  7. `test_check7_sample_generation_and_verification`: Asserts deterministic sampling, rubric integrity, and sign-off verification.
* **False-Positive Guard Fixtures:**
  * `test_check4_permits_incidental_date_mention`: Record mentioning *«переписано у XVI ст.»* in body does not false-fail.
  * `test_check4_permits_inflected_target_term`: Record with target *«вигляд»* appearing as *«вигляду»* does not false-fail.
* **Fail-Closed Dependency Fixtures:**
  * Missing `vesum.db` $\rightarrow$ exits with code 2.
  * Explicit missing `sources.db` $\rightarrow$ exits with code 2.
