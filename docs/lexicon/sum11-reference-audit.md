# СУМ-11 references in lexicon scripts (#8990)

Denominator: `git grep -I -i -n -E '(СУМ|SUM)[-‐‑‒–— ]?11|search_definitions|sum11' -- scripts/lexicon`, excluding `*heteronym*` and `sum20_lookup.py` owned by #8964. Audited after the WIP removal. Every remaining match is contrast/exclusion code or documentation; none verifies a lemma, sense, relation, stress, or gloss.

Counts: verification **0**, contrast **67**, dead **0**. The WIP removed verification consumers including `anchor_curation_evidence.py` and the `sum11` headword fallback, plus uncalled `_synonyms_from_sum11`.

## Stored public relation audit

The read-only 2026-09-11 `atlas.db` snapshot has **4,111** public synonym sections and **297** public antonym sections citing СУМ-11. These are the live database counts from `sqlite3 -readonly /home/ops/learn-ukrainian/data/atlas.db "SELECT e.section,count(*) FROM enrichment e JOIN articles a USING(slug) WHERE a.visibility='public' AND e.section IN ('synonyms','antonyms') AND e.payload_json LIKE '%СУМ-11%' GROUP BY e.section;"`, whose output was `antonyms|297` and `synonyms|4111`. The issue comment's earlier count of 3,583 synonym rows used a different query/snapshot; this report uses the query above as its denominator.

For every cited section, the audit queried the exact `ulif_dictua_entries.normalized_query` and matching `ulif_dictua_sections` relation kind in read-only `sources.db`. It ran the production `_synonyms_ulif` or `_antonyms_ulif` extractor with the read-only VESUM lemma gate pointed at the primary `vesum.db`, and compared each emitted item to the stored item. A row is **confirmed** only if every stored item was emitted by that allowed source. A row with any other item is **held**; [the held-item list](sum11-held-relations.tsv) records every unresolved item and the source search run. This is a conservative ULIF-only confirmation, not a claim that another allowed source lacks the item or that the full rebuilt section is byte-identical.

| Section | Cited rows | Fully confirmed rows | Held rows | Confirmed items | Held items |
| --- | ---: | ---: | ---: | ---: | ---: |
| Synonyms | 4,111 | 1,945 | 2,166 | 14,133 | 5,154 |
| Antonyms | 297 | 79 | 218 | 117 | 262 |
| **Total** | **4,408** | **2,024** | **2,384** | **14,250** | **5,416** |

The extraction command printed `{"antonyms": {"confirmed_items": 117, "fully_confirmed_rows": 79, "held_items": 262, "held_rows": 218, "rows": 297}, "synonyms": {"confirmed_items": 14133, "fully_confirmed_rows": 1945, "held_items": 5154, "held_rows": 2166, "rows": 4111}}`. A next build recomputes cited sections from allowed sources and withholds unsupported items. Atlas migration and runtime export reject a learner citation outside `soviet_colonization_context`, and they also reject a citation that stays inside that context without a russification marker (`russif`, `русиф`, `русизм`, `sovietiz`, or `red_flag` on the same card).

| Match | Class | Reason |
| --- | --- | --- |
| `scripts/lexicon/admit_fmu_boosters.py:8` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/admit_textbook_book_glossary.py:10` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
| `scripts/lexicon/admit_textbook_book_glossary.py:420` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
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
| `scripts/lexicon/enrich_manifest.py:3983` | contrast | States the source exclusion or contrasts it with allowed dictionary sources. |
| `scripts/lexicon/enrich_manifest.py:4383` | contrast | States the source exclusion or contrasts it with allowed dictionary sources. |
| `scripts/lexicon/enrich_manifest.py:4507` | contrast | States the source exclusion or contrasts it with allowed dictionary sources. |
| `scripts/lexicon/enrich_manifest.py:4548` | contrast | States the source exclusion or contrasts it with allowed dictionary sources. |
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
| `scripts/lexicon/source_attribution.py:28` | contrast | Defines the citation quarantine, not a source lookup. |
| `scripts/lexicon/thin_page_report.py:29` | contrast | Excludes historical definition cards from modern coverage counts. |
| `scripts/lexicon/thin_page_report.py:35` | contrast | Excludes historical definition cards from modern coverage counts. |
| `scripts/lexicon/triage_needs_review.py:43` | contrast | Documents or enforces the exclusion of Soviet dictionary evidence. |
