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

Issue #8342 cited approximately ~8,900 human corrections across the UA-GEC database. This section documents the exact, authoritative funnel reconciling that gross annotation count with the delivered dataset of 995 substantive corrections and 380 authentic clean controls (1,375 total records):

### 1. Corpus-Level Counts (UA-GEC 2.0 `gec-fluency`)
- **Total raw train sentences:** 31,028 sentences (plus 2,690 test sentences).
- **Sentences with any annotator edits:** 17,023 train sentences.
- **Total edits across all error types:** 37,164 train edits + 8,247 test edits = 45,411 edits.
- **In-scope grammatical edits (`G/*` + `F/Calque`):** **9,874 total edits** (8,266 train edits + 1,608 test edits quarantined by the held-out firewall).
  - This authoritative count of 9,874 in-scope edits across train and test directly explains the "~8,900" human correction estimate cited in issue #8342.
- **Train sentences containing $\ge 1$ in-scope edit:** 5,138 sentences.
- **Total in-scope train candidate annotator edit sets:** 5,252 candidate edit sets.

### 2. Systematic Exclusions & Quality Gates (per SPEC §2.2 & §3)
To ensure zero training corruption, zero benchmark leakage, and high grammatical density, all 5,252 candidate edit sets (4,802 in train-partition documents, 450 in eval-partition documents) were subjected to strict, fail-closed filtering. Full itemized accounting per candidate is recorded in [`candidate_exclusion_accounting.json`](./candidate_exclusion_accounting.json):
1. **Document-Level 90:10 Partition Holdout:**
   - 10% of documents (partitioned by SHA-256 hash of `doc_id`) are held out for the evaluation split (`grammar_eval_shard_01_of_02.jsonl`, `grammar_eval_shard_02_of_02.jsonl`), preserving document isolation with zero cross-split leakage.
2. **Official Held-Out Test Firewall:**
   - Strict firewall matching against `gec-fluency.test.m2` (0 doc overlap, 0 exact text overlap, and 0 near-duplicate sentences with Jaccard $\ge 0.80$; **13** candidate matches excluded: 10 quarantined targets [`test_firewall_target`], 3 quarantined sources [`test_firewall_source`]).
3. **Cross-Split Eval Partition Isolation:**
   - Sentences appearing in the evaluation partition are strictly quarantined from the training partition: **10** candidate matches excluded (9 sources [`eval_partition_firewall_source`], 1 target [`eval_partition_firewall_target`]).
4. **Syntactic, Semantic & Valency Quality Filters:**
   - Unwarranted valid-to-valid lexical swap (`unwarranted_valid_to_valid_lexical_swap`): **861** candidates excluded.
   - Sentence length floor (< 5 words) (`sentence_length_floor_under_5_words`): **287** candidates excluded.
   - Ungrammatical gold correction (`ungrammatical_gold_correction`): **275** candidates excluded.
   - Wholesale essay rewrite exceeding 30% of tokens (`wholesale_essay_rewrite_token_share_over_30_pct`): **196** candidates excluded.
   - Repeated word with intervening tokens (`repeated_word_intervening_words`): **187** candidates excluded.
   - Russianism in corrected text (`russianism_in_corrected_text`): **150** candidates excluded.
   - VESUM-unverified vocabulary form in corrected text (`vesum_unverified_vocabulary_form`): **123** candidates excluded.
   - Missing finite verb or copula (`missing_finite_verb_or_copula`): **113** candidates excluded.
   - Semantic meaning change or invented content (`semantic_meaning_change_or_invented_content`): **97** candidates excluded.
   - Contextless pronoun or gender flip (`contextless_pronoun_or_gender_flip`): **71** candidates excluded.
   - Polarity flips / negation changes (`polarity_flips_negation`): **64** candidates excluded.
   - Russianism in original text unrelated to edit (`russianism_in_original_text_unrelated_to_edit`): **63** candidates excluded.
   - Grammatical aspect, tense, or mood change (`grammatical_aspect_tense_or_mood_change`): **50** candidates excluded.
   - Morphology or agreement defect (`morphology_or_agreement_defect`): **31** candidates excluded.
   - Sentence-splitting edits (`sentence_splitting_edit`): **30** candidates excluded.
   - Gender agreement mismatch (`gender_agreement_mismatch`): **11** candidates excluded.
   - Euphony defect (`euphony_defect`): **11** candidates excluded.
   - Run-on sentences / dropped periods (`run_on_sentence_dropped_period`): **4** candidates excluded.
   - Comma between subject and reporting verb (`comma_subject_reporting_verb`): **3** candidates excluded.
   - Truncated sentence ending in preposition (`truncated_sentence_ends_in_preposition`): **1** candidate excluded.
   - Dangling subordinate clause (`dangling_subordinate_clause`): **1** candidate excluded.
   - Adjacent doubled words (`adjacent_doubled_words`): **1** candidate excluded.
   - Unpaired comma after relative pronoun (`unpaired_comma_after_relative_pronoun`): **1** candidate excluded.
5. **Orthographic & Typographic Standard Filters:**
   - Uncapitalized sentence fragments (`uncapitalized_or_fragment`): **503** candidates excluded.
   - Non-Cyrillic characters, Latin scripts, and control characters (`latin_characters`): **224** candidates excluded.
   - Missing or invalid terminal punctuation (`missing_or_invalid_terminal_punctuation`): **222** candidates excluded.
   - Stray floating quotation marks (`stray_floating_quotes`): **118** candidates excluded.
   - Straight ASCII quotation marks (`"` instead of standard Ukrainian `«...»`) (`straight_ascii_quotes`): **66** candidates excluded.
   - Unbalanced quotation marks (`unbalanced_quotes`): **61** candidates excluded.
   - Missing punctuation before direct speech quote (`missing_punct_before_direct_speech_quote`): **46** candidates excluded.
   - Mathematical symbols and special characters (`math_special_symbols`): **22** candidates excluded.
   - Bracket editorial artifacts (`bracket_editorial_artifacts`): **15** candidates excluded.
   - Malformed quote spacing (`malformed_quote_spacing`): **13** candidates excluded.
   - Colloquial Russian suffix *-то* (`colloquial_russian_suffix_to`): **13** candidates excluded.
   - Unbalanced parentheses (`unbalanced_parentheses`): **13** candidates excluded.
   - Mixed dashes (`mixed_dashes`): **7** candidates excluded.
   - Emojis (`emojis`): **6** candidates excluded.
   - Triple repeated letters (`triple_repeated_letters`): **4** candidates excluded.
   - Spaced dashes in compounds (`spaced_dashes_in_compounds`): **4** candidates excluded.
   - URLs in sentence (`url_in_sentence`): **3** candidates excluded.
   - Spaced dash in initials (`spaced_dash_in_initials`): **2** candidates excluded.
   - Capitalization after comma-dash (`capitalization_after_comma_dash`): **2** candidates excluded.
6. **Pedagogical Grounding, Safety & Semantic Fidelity:**
   - Pure word insertions (`start == end`) (`pure_word_insertions`): **216** candidates excluded. Pure insertions lack an authentic corrupted grammatical surface form in the source text and risk teaching ungrounded generative insertion rather than grammatical correction.
   - Safety filters (violent / morbid / vulgar content) (`safety_violent_morbid_vulgar`): **26** candidates excluded.
   - Defamatory or personal claims about named individuals (`claim_about_named_person`): **1** candidate excluded.
   - Unsubstantiated political assertions (`unsubstantiated_political_assertion`): **1** candidate excluded.
7. **Cross-Document Pair Deduplication:**
   - Duplicate `(original_text, corrected_text)` pairs across multiple annotators or documents were deduplicated (`duplicate_sentence_pair`): **15** candidates excluded.
8. **Funnel Summary & Zero Reserve:**
   - Total exclusions: **4,257** candidate edit sets excluded across **51** measured criteria (3,893 train, 364 eval).
   - **Zero Catch-Alls:** Every single rejected candidate is mapped directly to its specific validator gate or firewall check; generic catch-all buckets (`adversarial_review_round_findings`) have a count of **0**.
   - Retained candidate edit sets in pipeline: **995** (909 train candidates + 86 eval candidates).
   - Delivered in final balanced component: **995** substantive corrections (909 train, 86 eval) — 100% of retained candidate edit sets delivered, with zero withheld and zero in reserve.
   - Complete itemized candidate-level audit trail: 4,257 exclusion records in `candidate_exclusion_accounting.json`, each recording `candidate_id`, `doc_id`, `sent_idx`, `ann_id`, `split`, `primary_tag`, `rejection_gate`, and `original_snippet`.
   - *Reserve disposition:* The earlier reported figure of 1,096 retained / 99 in reserve was an unmeasured legacy placeholder prior to completing the structural, safety, and orthographic filter suite. Every single candidate is now tracked and measured in `candidate_exclusion_accounting.json`.

### 3. Delivered Dataset Composition
- **Substantive Corrections:** **995 records** (909 train across 8 shards, 86 eval across 2 shards).
- **Protective Clean Controls:** **380 records** (330 train from Brown-UK and gold UA-GEC, 50 eval from Brown-UK).
- **Total Records:** **1,375 records** (1,239 train records, 136 eval records).
- **Mixture Ratio:** **72.4% substantive corrections / 27.6% clean controls**, strictly adhering to the 70%–80% corrections and 20%–30% controls required by SPEC §2.2.

## Licensing & Upstream Attribution
All dataset records carry explicit per-row licensing and provenance:
- **UA-GEC 2.0:** Licensed under CC BY 4.0. Annotated human error corrections from the official Grammarly UA-GEC release.
- **Brown-UK (БрУК):** Licensed under CC BY-NC-SA 4.0. Pristine literary and journalistic negative controls. Full per-document catalog, rights architecture, and verification records are documented in [`BROWN_UK_ATTRIBUTION.md`](./BROWN_UK_ATTRIBUTION.md).

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
