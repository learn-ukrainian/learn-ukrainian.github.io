# Component: Grammar, Valency & Morphosyntax

**Governing Issue:** [#8342](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8342)
**Parent Epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
**Specification:** `docs/projects/open-model-data/GRAMMAR_DATASET_SPEC_8342.md`
**Status:** Complete / Approved

## Purpose
Focuses specifically on prepositional government, case valency, aspectual pairs, and morphosyntactic patterns where Slavic interference is most prevalent:
1. Prepositional constructions (e.g. *по* vs *за/через/для*, *згідно з*, *відповідно до*).
2. Verb valency and direct/indirect object government (e.g. *дякувати комусь*, *запобігати чомусь*, *вчитися чогось*).
3. Aspect pair usage in modal and negative contexts.
4. Agreement and concord in gender, number, and case.
5. De-calquing of Russian grammatical calques (`F/Calque`).

## Source Denominator Reconciliation (#8342)

Issue #8342 cited approximately ~8,900 human corrections across the UA-GEC database. This section documents the exact, authoritative funnel reconciling that gross annotation count with the delivered dataset of 997 substantive corrections and 380 authentic clean controls (1,377 total records):

### 1. Corpus-Level Counts (UA-GEC 2.0 `gec-fluency`)
- **Total raw train sentences:** 31,028 sentences (plus 2,690 test sentences).
- **Sentences with any annotator edits:** 17,023 train sentences.
- **Total edits across all error types:** 37,164 train edits + 8,247 test edits = 45,411 edits.
- **In-scope grammatical edits (`G/*` + `F/Calque`):** **9,874 total edits** (8,266 train edits + 1,608 test edits quarantined by the held-out firewall).
  - This authoritative count of 9,874 in-scope edits across train and test directly explains the "~8,900" human correction estimate cited in issue #8342.
- **Train sentences containing $\ge 1$ in-scope edit:** 5,138 sentences.
- **Total in-scope train candidate annotator edit sets:** 5,252 candidate edit sets.

### 2. Systematic Exclusions & Quality Gates (per SPEC §2.2 & §3)
To ensure zero training corruption, zero benchmark leakage, and high grammatical density, all 5,252 candidate edit sets were subjected to strict, fail-closed filtering:
1. **Document-Level 90:10 Partition Holdout:**
   - 10% of documents (partitioned by SHA-256 hash of `doc_id`) are held out for the evaluation split (`grammar_eval_shard_01_of_02.jsonl`, `grammar_eval_shard_02_of_02.jsonl`), preserving document isolation with zero cross-split leakage.
2. **Official Held-Out Test Firewall:**
   - Strict firewall matching against `gec-fluency.test.m2` (0 doc overlap, 0 exact text overlap, and 0 near-duplicate sentences with Jaccard $\ge 0.80$; **13** candidate matches excluded).
3. **Syntactic & Structural Integrity Filters:**
   - Structural and syntactic quality filters (complex run-ons, dropped copula/subjects): **2,464** candidates excluded.
   - Uncapitalized sentence fragments: **508** candidates excluded.
   - Sentence length floor (< 5 words): **287** candidates excluded.
   - Missing or malformed terminal punctuation: **193** candidates excluded.
   - Unbalanced quotation marks: **30** candidates excluded.
4. **Orthographic & Typographic Standard Filters:**
   - Non-Cyrillic characters, Latin scripts, URLs, emojis, and unprintable symbols: **236** candidates excluded.
   - Straight ASCII quotation marks (`"` instead of standard Ukrainian `«...»`): **79** candidates excluded.
   - Mathematical symbols and special characters: **22** candidates excluded.
   - Bracket editorial artifacts: **16** candidates excluded.
5. **Pedagogical Grounding & Scope Filters:**
   - Pure word insertions (`start == end`): **217** candidates excluded. Pure insertions lack an authentic corrupted grammatical surface form in the source text and risk teaching ungrounded generative insertion rather than grammatical correction.
   - Polarity flips (adding or dropping negation particle *не*): **70** candidates excluded to preserve source semantics.
6. **Cross-Document Pair Deduplication:**
   - Duplicate `(original_text, corrected_text)` pairs across multiple annotators or documents were deduplicated: **21** candidates excluded.
7. **Funnel Summary:**
   - Total exclusions: **4,156** candidate edit sets excluded.
   - Retained candidate edit sets in pipeline: **1,096** (1,009 train candidates + 87 eval candidates).
   - Delivered in final balanced component: **997** substantive corrections (911 train, 86 eval), leaving 99 verified candidates in pipeline reserve.

### 3. Delivered Dataset Composition
- **Substantive Corrections:** **997 records** (911 train across 8 shards, 86 eval across 2 shards).
- **Protective Clean Controls:** **380 records** (330 train from Brown-UK and gold UA-GEC, 50 eval from Brown-UK).
- **Total Records:** **1,377 records** (1,241 train records, 136 eval records).
- **Mixture Ratio:** **72.4% substantive corrections / 27.6% clean controls**, strictly adhering to the 70%–80% corrections and 20%–30% controls required by SPEC §2.2.

## Query Prompt Punctuation Standards
Prompt templates follow Ukrainian orthographic standards (Правопис 2019, § 162–164):
- When a sentence is cited inside quotation marks (`«...»`) within an interrogative or instructional carrier prompt, trailing terminal periods are stripped from the quoted sentence so that carrier punctuation does not generate duplicated punctuation (such as `«... .».` or `«... ?».`).
- Sentences that are already quoted have outer quotes stripped, and internal quotes are converted to curved double quotes (`“...”`) to prevent nested guillemets (`««...»»`).
- Interrogative (`?`) and exclamatory (`!`) source punctuation is fully preserved.
- Zero records contain duplicated quotation-terminal punctuation or nested guillemets.

## Verified Linguistic Authorities
Every substantive correction and clean control is grounded in approved Ukrainian authorities:
- **VESUM** (Morphological dictionary of Ukrainian)
- **Український правопис (2019)**
- **Борис Антоненко-Давидович**, *«Як ми говоримо»*
- **Олександр Пономарів**, *«Культура слова»*
- **Катерина Городенська**, *«Словник дієслівного керування»*
- **Академічний «Словник української мови» (СУМ-20)**
