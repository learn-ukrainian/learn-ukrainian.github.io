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

### 1. Corpus-Level Counts (UA-GEC 2.0 `gec-fluency.train.m2`)
- **Total raw sentences:** 31,028 sentences.
- **Sentences with any annotator edits:** 17,023 sentences.
- **Total edits across all error types:** 37,164 edits (including spelling, punctuation, fluency, styling, and typography).
- **In-scope grammatical edits (`G/*` + `F/Calque`):** **8,266 edits**.
  - This count of 8,266 in-scope edits in the training split (plus corresponding edits in the held-out test split) constitutes the "~8,900" rough estimate cited in issue #8342.
- **Sentences containing $\ge 1$ in-scope edit:** 5,138 sentences.
- **Total in-scope candidate annotator edit sets:** 5,252 candidate edit sets.

### 2. Systematic Exclusions & Quality Gates (per SPEC §2.2 & §3)
To ensure zero training corruption, zero benchmark leakage, and high grammatical density, candidates were subjected to fail-closed filtering:
1. **Document-Level 90:10 Partition Holdout:**
   - 10% of documents (partitioned by SHA-256 hash of `doc_id`) are held out for the evaluation split (`grammar_eval_shard_01_of_02.jsonl`, `grammar_eval_shard_02_of_02.jsonl`), preserving document isolation with zero cross-split leakage.
2. **Official Held-Out Test Firewall:**
   - Strict firewall matching against `gec-fluency.test.m2` (0 doc overlap, 0 exact text overlap, and 0 near-duplicate sentences with Jaccard $\ge 0.80$).
3. **Syntactic & Structural Integrity Filters:**
   - Uncapitalized sentence fragments: **547** candidates excluded.
   - Sentence length floor (< 5 words): **293** candidates excluded.
   - Missing or malformed terminal punctuation: **193** candidates excluded.
   - Unbalanced quotation marks: **33** candidates excluded.
4. **Orthographic & Typographic Standard Filters:**
   - Non-Cyrillic characters, Latin scripts, URLs, emojis, and unprintable symbols: **242** candidates excluded.
   - ASCII straight quotation marks (`"` instead of standard Ukrainian `«...»`): **67** candidates excluded.
   - Mathematical symbols and bracket artifacts: **35** candidates excluded.
5. **Pedagogical Grounding & Scope Filters:**
   - Pure word insertions (`start == end`): **218** candidates excluded. Pure insertions lack an authentic corrupted grammatical surface form in the source text and risk teaching ungrounded generative insertion rather than grammatical correction.
   - Polarity flips (adding or dropping negation particle *не*): **68** candidates excluded to preserve source semantics.
6. **Cross-Document Pair Deduplication:**
   - Duplicate `(original_text, corrected_text)` pairs across multiple annotators or documents were deduplicated, leaving only distinct correction pairs.

### 3. Delivered Dataset Composition
- **Substantive Corrections:** **997 records** (891 train across 8 shards, 106 eval across 2 shards).
- **Protective Clean Controls:** **380 records** (350 train from Brown-UK and gold UA-GEC, 30 eval from Brown-UK).
- **Total Records:** **1,377 records**.
- **Mixture Ratio:** **72.4% substantive corrections / 27.6% clean controls**, strictly adhering to the 70%–80% corrections and 20%–30% controls required by SPEC §2.2.

## Query Prompt Punctuation Standards
Prompt templates follow Ukrainian orthographic standards (Правопис 2019, § 162):
- When a sentence is cited inside quotation marks (`«...»`) within an interrogative or instructional carrier prompt, trailing terminal periods are stripped from the quoted sentence so that carrier punctuation does not generate duplicated punctuation (such as `«... .».` or `«... ?».`).
- Zero records contain duplicated quotation-terminal punctuation.

## Verified Linguistic Authorities
Every substantive correction and clean control is grounded in approved Ukrainian authorities:
- **VESUM** (Morphological dictionary of Ukrainian)
- **Український правопис (2019)**
- **Борис Антоненко-Давидович**, *«Як ми говоримо»*
- **Олександр Пономарів**, *«Культура слова»*
- **Катерина Городенська**, *«Словник дієслівного керування»*
- **Академічний «Словник української мови» (СУМ-20)**
