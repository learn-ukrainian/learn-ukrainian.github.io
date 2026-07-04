# Word Atlas Source Entry Count

- workflow: `atlas_source_entry_count.v1`
- generated_at: `2026-07-04T14:14:57+00:00`
- production_outputs_updated: []
- raw_text_included: false
- candidate_lemmas_included: false
- private_paths_included: false
- private_filenames_included: false

## Exact Reviewed Atlas Baseline

- manifest_loaded: true
- manifest_sha256: `f585ea69643154028e1d467162144a3f40fa758fa75a25610c19acc4686e8929`
- manifest_records: 5502
- total_reviewed_entries: 5156

| entry bucket | exact reviewed entries |
| --- | ---: |
| `lemma` | 3847 |
| `expression` | 5 |
| `phraseologism` | 0 |
| `proverb` | 0 |
| `multiword_term` | 1266 |
| `proper_name` | 38 |

### Exact Non-Entry Manifest Records

| bucket | records |
| --- | ---: |
| `form_alias` | 336 |
| `grammar_term` | 10 |
| `noise_rejected` | 0 |
| `invalid` | 0 |

## Estimated Source-Corpus Backlog By Lane

| source lane | source units | unique forms | explicit headwords | candidate entries | reviewed overlap | estimated backlog | lemma | expression | phraseologism | proverb | multiword term | proper name | needs review | unknown | noise rejected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `module_activity` | 518 | 32511 | 0 | 14765 | 3191 | 11574 | 8959 | 0 | 0 | 0 | 0 | 0 | 2615 | 0 | 0 |
| `module_all` | 1549 | 56853 | 7222 | 30269 | 7981 | 22288 | 16963 | 0 | 0 | 0 | 0 | 0 | 5325 | 0 | 0 |
| `module_content` | 518 | 48556 | 0 | 19786 | 3372 | 16414 | 13591 | 0 | 0 | 0 | 0 | 0 | 2823 | 0 | 0 |
| `module_vocabulary` | 513 | 16646 | 7222 | 15949 | 7844 | 8105 | 6790 | 0 | 0 | 0 | 0 | 0 | 1315 | 0 | 0 |
| `ohoiko_private_text` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `textbook_extracted_text` | 24 | 125294 | 0 | 70040 | 3161 | 66879 | 34736 | 0 | 0 | 0 | 0 | 0 | 32143 | 0 | 0 |
| `textbook_jsonl_chunks` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `textbook_sqlite_db` | 25714 | 277142 | 0 | 148329 | 3407 | 144922 | 60422 | 0 | 0 | 0 | 0 | 0 | 84500 | 0 | 0 |
| `committed_source_inventory` | 31 | 0 | 377 | 377 | 358 | 18 | 14 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| `committed_inventory_curriculum` | 10 | 0 | 20 | 20 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `committed_inventory_ohoiko` | 4 | 0 | 33 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `committed_inventory_teacher_lesson` | 10 | 0 | 224 | 224 | 207 | 17 | 13 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| `committed_inventory_textbook` | 7 | 0 | 111 | 111 | 110 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Classification Methods By Lane

| source lane | method | candidates |
| --- | --- | ---: |
| `module_activity` | `manifest_entry_type` | 3191 |
| `module_activity` | `unknown_needs_review` | 2615 |
| `module_activity` | `vesum_backed_lemma` | 8959 |
| `module_all` | `heuristic_multiword_needs_review` | 861 |
| `module_all` | `manifest_entry_type` | 7981 |
| `module_all` | `module_explicit_headword` | 1800 |
| `module_all` | `unknown_needs_review` | 4464 |
| `module_all` | `vesum_backed_lemma` | 15163 |
| `module_content` | `manifest_entry_type` | 3372 |
| `module_content` | `unknown_needs_review` | 2823 |
| `module_content` | `vesum_backed_lemma` | 13591 |
| `module_vocabulary` | `heuristic_multiword_needs_review` | 861 |
| `module_vocabulary` | `manifest_entry_type` | 7844 |
| `module_vocabulary` | `module_explicit_headword` | 1800 |
| `module_vocabulary` | `unknown_needs_review` | 454 |
| `module_vocabulary` | `vesum_backed_lemma` | 4990 |
| `ohoiko_private_text` | `none` | 0 |
| `textbook_extracted_text` | `manifest_entry_type` | 3161 |
| `textbook_extracted_text` | `unknown_needs_review` | 32143 |
| `textbook_extracted_text` | `vesum_backed_lemma` | 34736 |
| `textbook_jsonl_chunks` | `none` | 0 |
| `textbook_sqlite_db` | `manifest_entry_type` | 3407 |
| `textbook_sqlite_db` | `unknown_needs_review` | 84500 |
| `textbook_sqlite_db` | `vesum_backed_lemma` | 60422 |
| `committed_source_inventory` | `heuristic_multiword_needs_review` | 4 |
| `committed_source_inventory` | `manifest_entry_type` | 358 |
| `committed_source_inventory` | `noise_filter` | 1 |
| `committed_source_inventory` | `source_inventory_headword` | 14 |
| `committed_inventory_curriculum` | `manifest_entry_type` | 19 |
| `committed_inventory_curriculum` | `noise_filter` | 1 |
| `committed_inventory_ohoiko` | `manifest_entry_type` | 33 |
| `committed_inventory_teacher_lesson` | `heuristic_multiword_needs_review` | 4 |
| `committed_inventory_teacher_lesson` | `manifest_entry_type` | 207 |
| `committed_inventory_teacher_lesson` | `source_inventory_headword` | 13 |
| `committed_inventory_textbook` | `manifest_entry_type` | 110 |
| `committed_inventory_textbook` | `source_inventory_headword` | 1 |

## Textbook Grades By Lane

| source lane | grade | source units | unique forms | candidate entries | reviewed overlap | estimated backlog | lemma | needs review | unknown |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `textbook_extracted_text` | `grade-02` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `textbook_extracted_text` | `grade-03` | 2 | 14398 | 9252 | 1739 | 7513 | 6035 | 1478 | 0 |
| `textbook_extracted_text` | `grade-04` | 1 | 7180 | 5062 | 1156 | 3906 | 3002 | 904 | 0 |
| `textbook_extracted_text` | `grade-05` | 2 | 25532 | 16614 | 2145 | 14469 | 10073 | 4396 | 0 |
| `textbook_extracted_text` | `grade-06` | 2 | 25254 | 16515 | 2212 | 14303 | 10320 | 3983 | 0 |
| `textbook_extracted_text` | `grade-07` | 2 | 20841 | 13315 | 2057 | 11258 | 8058 | 3200 | 0 |
| `textbook_extracted_text` | `grade-08` | 3 | 16636 | 10103 | 1559 | 8544 | 6261 | 2283 | 0 |
| `textbook_extracted_text` | `grade-09` | 3 | 36774 | 25183 | 2254 | 22929 | 12229 | 10700 | 0 |
| `textbook_extracted_text` | `grade-10` | 3 | 40334 | 23924 | 2317 | 21607 | 14304 | 7303 | 0 |
| `textbook_extracted_text` | `grade-11` | 3 | 52101 | 30298 | 2670 | 27628 | 17937 | 9691 | 0 |
| `textbook_extracted_text` | `unknown` | 1 | 4895 | 3716 | 903 | 2813 | 2074 | 739 | 0 |
| `textbook_sqlite_db` | `grade-01` | 394 | 8588 | 6474 | 1194 | 5280 | 3064 | 2216 | 0 |
| `textbook_sqlite_db` | `grade-02` | 746 | 20198 | 12377 | 1932 | 10445 | 7663 | 2782 | 0 |
| `textbook_sqlite_db` | `grade-03` | 939 | 29508 | 17501 | 2240 | 15261 | 10874 | 4387 | 0 |
| `textbook_sqlite_db` | `grade-04` | 986 | 28898 | 17592 | 2222 | 15370 | 10168 | 5202 | 0 |
| `textbook_sqlite_db` | `grade-05` | 1820 | 53501 | 31802 | 2758 | 29044 | 18409 | 10635 | 0 |
| `textbook_sqlite_db` | `grade-06` | 2467 | 70456 | 40827 | 2933 | 37894 | 23316 | 14578 | 0 |
| `textbook_sqlite_db` | `grade-07` | 2834 | 78339 | 43796 | 2971 | 40825 | 25829 | 14996 | 0 |
| `textbook_sqlite_db` | `grade-08` | 3290 | 79301 | 44861 | 2927 | 41934 | 24618 | 17316 | 0 |
| `textbook_sqlite_db` | `grade-09` | 3257 | 81256 | 47822 | 2872 | 44950 | 24748 | 20202 | 0 |
| `textbook_sqlite_db` | `grade-10` | 3066 | 78770 | 47382 | 2991 | 44391 | 25104 | 19287 | 0 |
| `textbook_sqlite_db` | `grade-11` | 3978 | 91502 | 51991 | 3060 | 48931 | 27498 | 21433 | 0 |
| `textbook_sqlite_db` | `unknown` | 1937 | 62069 | 26481 | 2849 | 23632 | 17194 | 6438 | 0 |

## Input Availability

```json
{
  "committed_source_inventories": {
    "by_family": {
      "curriculum": {
        "deduped_candidates": 20,
        "records": 20,
        "source_units": 10
      },
      "ohoiko": {
        "deduped_candidates": 33,
        "records": 33,
        "source_units": 4
      },
      "teacher_lesson": {
        "deduped_candidates": 224,
        "records": 228,
        "source_units": 10
      },
      "textbook": {
        "deduped_candidates": 111,
        "records": 114,
        "source_units": 7
      }
    },
    "deduped_candidates": 377,
    "included": true,
    "inventory_files": 15,
    "public_boundary": "aggregate counts only; no inventory filenames, source titles, paths, text, or candidate lists",
    "records": 395
  },
  "modules": {
    "l2_uk_direct_module_yaml": 180,
    "l2_uk_en_activity_yaml": 338,
    "l2_uk_en_module_md": 338,
    "l2_uk_en_vocabulary_yaml": 338
  },
  "ohoiko_private_text": {
    "private_roots_available": 0,
    "public_boundary": "aggregate counts only; no private paths, filenames, text, or lemmas",
    "text_files_scanned": 0
  },
  "textbook_extracted_text": {
    "public_boundary": "aggregate counts by grade only; no textbook filenames or raw text",
    "text_files_scanned": 24,
    "text_root_available": true
  },
  "textbook_jsonl_chunks": {
    "chunks_scanned": 0,
    "jsonl_files_scanned": 0,
    "jsonl_root_available": false,
    "malformed_rows": 0,
    "public_boundary": "aggregate counts by grade only; no JSONL chunk ids, filenames, or raw text"
  },
  "textbook_sqlite_db": {
    "char_count": 16933213,
    "chunks_scanned": 25714,
    "public_boundary": "aggregate counts by grade only; no DB chunk ids, source files, titles, or raw text",
    "source_files": 91,
    "sources_db_available": true
  }
}
```

## Caveats

- Reviewed Atlas counts are exact manifest article-entry counts; source-corpus counts are planning estimates.
- VESUM-backed lanes count unique candidate lemmas inferred from unique surface forms; ambiguous forms may contribute more than one possible lemma.
- Unrecognized forms, unreviewed multiword headwords, and unavailable lemmatizer lanes are counted as needs_review or unknown, not as approved entries.
- Current Atlas reviewed entries, source-corpus candidates, and backlog counts are separate numbers and should not be added together.
- Module content/activity/vocabulary lanes overlap; module_all is a convenience union for module surfaces.
- SQLite, JSONL, and extracted-TXT textbook lanes can overlap; use SQLite as the primary local corpus lane when available and JSONL/TXT as availability or drift checks.
- Committed source-inventory lanes are explicit reviewed/headword-style evidence, but they still require the normal Atlas review/publish gate for missing entries.
- No Phase 2 design or POC drift was found beyond the entry-model drift already documented in PR #4245.
