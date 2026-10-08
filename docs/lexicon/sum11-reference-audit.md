# СУМ-11 references in lexicon scripts (#8990)

## Not covered by this change

[#8964](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8964) owns `site/src/lib/lexicon/curated-heteronyms.ts`, which has 569 `soviet_colonization_context` blocks without a `red_flag` and cites СУМ-11 as an example and synonym source outside any context. The site bundles that file directly, so the Atlas migration and runtime export gate do not check this path. #8964 also owns `scripts/lexicon/enrich_heteronyms.py:751`, which still runs `SELECT word, definition FROM sum11`. Readers outside `scripts/lexicon` belong to [#9147](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9147). The operator rule allowing СУМ-11 only as red-flagged contrast is not fully met until #8964 and #9147 land. This change does not close #8990.

Denominator: `git grep -I -i -n -E '(СУМ|SUM)[-‐‑‒–— ]?11|search_definitions|sum11' -- scripts/lexicon`, excluding the exact #8964 heteronym files and `sum20_lookup.py`. Audited after the WIP removal. The classified matches within this denominator are contrast/exclusion code or documentation; they do not verify a lemma, sense, relation, stress, or gloss.

Counts: verification **0**, contrast **77**, dead **0**. The WIP removed verification consumers including `anchor_curation_evidence.py` and the `sum11` headword fallback, plus uncalled `_synonyms_from_sum11`. The three added contrast lines below are exact diagnostic errors, not verification inputs.

Readers outside `scripts/lexicon/**` have their own classification and remediation follow-up in [#9147](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9147).

## Stored public relation audit

The denominator is every stored `article_payloads` route in the read-only `atlas.db` snapshot, including ten public form routes without an `articles` row. The older `enrichment JOIN articles` query counted 4,111 synonym rows; the route denominator has 4,121. The audit also counts homonym sections and cited strings in `enrichment.sources[]`. The source list is metadata, so its citations are counted separately from relation items.

Re-run from this worktree with `.venv/bin/python -m scripts.lexicon.audit_sum11_relations`. The command opens the primary `data/atlas.db` and `data/sources.db` with SQLite `mode=ro`, sets `query_only=ON` on the production VESUM reader for `data/vesum.db`, and regenerates this count block, [confirmed items](sum11-confirmed-relations.tsv), [held relation items](sum11-held-relations.tsv), and [held source-list strings](sum11-held-sources.tsv). For cited synonym and antonym sections it calls the production ULIF extractor and VESUM lemma gate, then compares each stored item. A row is **fully confirmed** only when every stored item is emitted by ULIF; all other items are held. Homonym items are held because this audit does not run an independent replacement-source gate. A top-level `enrichment.sources[]` match is held metadata requiring removal on rebuild. These classifications do not certify any other allowed source or byte-identical rebuilt sections.

<!-- audit-counts:start -->
| Section | Cited rows | Fully confirmed rows | Held rows | Confirmed items | Held items |
| --- | ---: | ---: | ---: | ---: | ---: |
| synonyms | 4,121 | 2,023 | 2,098 | 14,526 | 4,778 |
| antonyms | 297 | 79 | 218 | 117 | 262 |
| homonyms | 567 | 0 | 567 | 0 | 655 |
| **Relation total** | **4,985** | **2,102** | **2,883** | **14,643** | **5,695** |
| top-level sources | 4,324 | 0 | 4,324 | 0 | 4,453 |

Source SHA-256: `atlas.db` `fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca`, `sources.db` `7868ce16f3cc8280676f08f436b94563ba20e3e7909ad236f06c2bdce19baa7b`, `vesum.db` `3e3a3c211f27c3f338abdfe47b2a5e3e8d6f38b9cfc31a65ca467677145e4dd5`
<!-- audit-counts:end -->

A next build recomputes cited sections from allowed sources and withholds unsupported items. Atlas migration and runtime export reject a learner citation outside the direct `soviet_colonization_context` section or without that citation's explicit `red_flag: true` marker. A withdrawal without a replacement-source check remains `source-withdrawn-unverified` in gate provenance.

Round 8 projection of the pinned 27,472-entry manifest touched 4,638 relation sections, including note-only cleanups, and withheld citations in 4,333 entries. It withheld 8,571 cited clauses and 1,775 unsupported relation items while retaining 18,197 items in touched sections; 1,813 diagnostic `[gate: …]` notes were stripped separately. No entry failed the projection. The migrate-stage report counts withdrawals from the source manifest; the export-stage report counts only residual withdrawals from its input database, so a zero export count after migration is expected.

Residual: the pinned manifest (`json_sha256` `81c695cdd5a5fdbd09fe2062884f663f891368b52a8de9f18340c2100a998801`) has **30 items in 28 relation sections** where only a СУМ-11 clause names the item, but another permitted bare source label supports the entire section. The review called these “30 sections”; recomputing at the section level gives 28. They remain kept under the documented bare-label rule, without a target-specific source check. The sections are:

| Section | Lemmas |
| --- | --- |
| synonyms | бурштин, генератор, гладити, глей, гуд, доповнити, дурницею, жартом, зайнятися (2 items), закінчити, закінчувати, зволити, зелена, знову, зрізати (2 items), коза, козак, лис, насіння, плавання, право, ризик, свиня |
| antonyms | лад, начало, схід, тяжкий, імпорт |

This is an evidence residual for #8990: a source lookup was unavailable during review, so the bare labels have not been independently checked for those 30 item relations. The `тлумачний` literary attestation quotes a 2004 encyclopedia mentioning the 11-volume dictionary. Its `text` is a corpus quotation, while its `source` metadata identifies the work; the citation guard still rejects that wording when it appears as a source attribution.

| Match | Class | Reason |
| --- | --- | --- |
| `scripts/lexicon/admit_fmu_boosters.py:8` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/admit_textbook_book_glossary.py:10` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/admit_textbook_book_glossary.py:420` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/audit_sum11_relations.py:2` | contrast | Read-only audit of stored citations against allowed sources. |
| `scripts/lexicon/audit_sum11_relations.py:78` | contrast | Read-only audit of stored citations against allowed sources. |
| `scripts/lexicon/audit_sum11_relations.py:107` | contrast | Read-only audit of stored citations against allowed sources. |
| `scripts/lexicon/audit_sum11_relations.py:118` | contrast | Read-only audit of stored citations against allowed sources. |
| `scripts/lexicon/audit_sum11_relations.py:119` | contrast | Read-only audit of stored citations against allowed sources. |
| `scripts/lexicon/audit_sum11_relations.py:120` | contrast | Read-only audit of stored citations against allowed sources. |
| `scripts/lexicon/audit_sum11_relations.py:154` | contrast | Read-only audit of stored citations against allowed sources. |
| `scripts/lexicon/census_atlas_6371_textbook_leftover.py:9` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/census_atlas_6371_textbook_leftover.py:554` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/census_atlas_6371_textbook_leftover.py:637` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/curated_ohoiko_ulp_repromote.py:10` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/curated_ohoiko_ulp_repromote.py:110` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/curated_ohoiko_ulp_repromote.py:112` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/curated_textbook_jsonl_repromote.py:8` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/curated_textbook_jsonl_repromote.py:121` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/curated_textbook_jsonl_repromote.py:123` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/curated_textbook_jsonl_repromote.py:200` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/enrich_manifest.py:13` | contrast | States the source exclusion or contrasts it with allowed dictionary sources. |
| `scripts/lexicon/enrich_manifest.py:3984` | contrast | States the source exclusion or contrasts it with allowed dictionary sources. |
| `scripts/lexicon/enrich_manifest.py:4384` | contrast | States the source exclusion or contrasts it with allowed dictionary sources. |
| `scripts/lexicon/enrich_manifest.py:4508` | contrast | States the source exclusion or contrasts it with allowed dictionary sources. |
| `scripts/lexicon/enrich_manifest.py:4549` | contrast | States the source exclusion or contrasts it with allowed dictionary sources. |
| `scripts/lexicon/heritage_classifier.py:200` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1104` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1105` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1110` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1118` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1123` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1127` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1136` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1141` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1147` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1157` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1163` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1304` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/heritage_classifier.py:1306` | contrast | Reads or computes only the occupation-risk flag; classification authority remains separate. |
| `scripts/lexicon/load_relation_candidates.py:102` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/migrate_sum11_sovietization.py:2` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:5` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:6` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:11` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:24` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:29` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:30` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:32` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:36` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:41` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:45` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:51` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:59` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:65` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:66` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:67` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:84` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:85` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/migrate_sum11_sovietization.py:113` | contrast | Maintains the occupation-risk scan and its database columns; no modern verification. |
| `scripts/lexicon/ohoiko_paired_headword_split.py:342` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/ohoiko_paired_headword_split.py:537` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/promote_grow_candidates.py:838` | contrast | Rejects a contaminated learner-English gloss or names that rejection. |
| `scripts/lexicon/promote_grow_candidates.py:839` | contrast | Rejects a contaminated learner-English gloss or names that rejection. |
| `scripts/lexicon/promote_grow_candidates.py:853` | contrast | Rejects a contaminated learner-English gloss or names that rejection. |
| `scripts/lexicon/promote_grow_candidates.py:864` | contrast | Rejects a contaminated learner-English gloss or names that rejection. |
| `scripts/lexicon/promote_grow_candidates.py:865` | contrast | Rejects a contaminated learner-English gloss or names that rejection. |
| `scripts/lexicon/promote_grow_candidates.py:866` | contrast | Rejects a contaminated learner-English gloss or names that rejection. |
| `scripts/lexicon/promote_grow_candidates.py:896` | contrast | Rejects a contaminated learner-English gloss or names that rejection. |
| `scripts/lexicon/promote_grow_candidates.py:898` | contrast | Rejects a contaminated learner-English gloss or names that rejection. |
| `scripts/lexicon/promote_grow_candidates.py:919` | contrast | Rejects a contaminated learner-English gloss or names that rejection. |
| `scripts/lexicon/source_attribution.py:29` | contrast | Defines the citation quarantine, not a source lookup. |
| `scripts/lexicon/source_attribution.py:168` | contrast | Fails closed if a withheld citation cannot be counted. |
| `scripts/lexicon/source_attribution.py:245` | contrast | Fails closed if an unsafe citation survives the projection. |
| `scripts/lexicon/enrich_manifest.py:8315` | contrast | Fails closed on an unflagged citation in newly enriched output. |
| `scripts/lexicon/thin_page_report.py:29` | contrast | Excludes historical definition cards from modern coverage counts. |
| `scripts/lexicon/thin_page_report.py:35` | contrast | Excludes historical definition cards from modern coverage counts. |
| `scripts/lexicon/triage_needs_review.py:43` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
