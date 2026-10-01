---
date: 2026-10-01T11:45:11Z
task: revise-a1-p1-p3-r2
issue: 8425
status: worker-package-pending-driver-acceptance
base_sha: 72dabe24945bd8a220d58a6d8518ca01b68cc5cb
owner: accountable curriculum driver for issue 8425
---

# A1 positions 1–3: round-2 plan and evidence package

Three version-2 plans cover 20 lessons and 136 planned activities (35 / 48 / 53), including all nine authorized audio-to-print conversions. This is an authoring deliverable, **not an accepted, reviewed or build-certified package**. Exact-head integration, publication rights, independent playback, held-out semantic review and stale manifests belong to the driver. No writer, lesson build, plan review, promotion, PR or merge was run.

Smallest change: use existing dialogue/quote comprehension and word-record orthography fields, retain native letter models, and replace unsupported exact-word audio scoring with explicit offline teacher practice plus scored print discrimination. Core vocabulary, grammar, letters, lesson counts and word targets are preserved. All 153 inherited word records remain unchanged as parsed records. The 22 new records are W-154–W-175; source-reading additions are incidental, not new core CEFR objectives. `_grammar.yaml`, `_arc.yaml`, `_decisions.yaml`, approvals and `_state/` remain unchanged.

## Recap hosts and source limits

Printed page and corpus/PDF-title page differ. Lengths count locked excerpt characters, including spaces/newlines. Each selected excerpt is below 800 characters; attribution accompanies every displayed public-textbook quote. ULP premium notes remain **explains only**, never displayed quotes.

| Position | Scored host / order | Source / printed page / corpus page | Chunk / record | Length |
| --- | --- | --- | --- | --- |
| 1 L6 a2 | Planned dialogue in s1 before a2 | Захарійчук, Буквар 2025 part 1, 74 / 76 | `1-klas-bukvar-zaharijchuk-2025-1_s0072`, T-036 grounding | 103-character grounding excerpt; future dialogue length unmeasured |
| 2 L6 a2 | Quote in s2 before a2 | Захарійчук, Буквар 2025 part 2, 111 / 113 | `1-klas-bukvar-zaharijchuk-2025-2_s0110`, T-034 | 31 characters, two complete connected sentences |
| 3 L8 a2 | Quote in s2 before a2 | Захарійчук, Буквар 2025 part 2, 73 / 75 | `1-klas-bukvar-zaharijchuk-2025-2_s0072`, T-035 | 81 characters, two complete connected sentences |

P1 uses complete mother/Pavlik turns from the plum scene, ending with the mother's negative reply. The syllable-hyphenated excerpt grounds a genuinely planned dialogue, not a relabelled bilingual story or an invented blank completion. Its read targets and elliptical Ukrainian questions use taught letters; no хто before Х. Module recycling and offline copying remain. P2's passage supplies different substantive answers about spring and arriving birds. ULP 1-10 stays unscored listening in s1; T-016/T-017 ground it through explains. EX-001/EX-002 whole-sentence reading and notebook production remain. P3's passage supplies different substantive answers about rain and the travelling snail. Its other model/production tasks retain all eight letters, soft sign, digraphs and apostrophe; the passage alone is not claimed to contain every sign. Optional writer bilingual stories remain unscored support only.

## Search and verification record

Live `sources.get_chunk_context` read whole pages at all supplied pointers: part-1 s0072 and part-2 s0028/s0029/s0068/s0072. Additional full pages: part-1 s0027/s0073/s0074/s0075/s0081 and part-2 s0110. P2 s0028 contains an untaught apostrophe. P2 s0029 has two decodable complete utterances but no connected story, while the other utterances contain untaught signs. P3 s0068 contains unresolved-stress малюче and OCR artifacts; its poem was withheld. P2's following sentence with березі was excluded after `verify_stress` reported ambiguity unresolvable by tags. P1's hyphenated excerpt is grounding, not a verbatim machine word stream.

Current `search_text` queries: `"мама" "слива"` (bukvar, exact part-1; s0091/s0087/s0031), `"ми" "прилетіли"` (bukvar; s0029/s0110), `"сім" "я"` (ukrmova; unrelated higher-grade material), `"равлики" "дощ"` (bukvar exact part-2; s0072/s0073/s0071), `"сливка"` (exact part-1; empty FTS despite successful direct retrieval), and `"весна" "птахи"` (ukrmova, Bolshakova part-2; empty). A compound plum FTS call failed and was retried; direct page access still worked. Empty FTS is not absence from the corpus.

Audio discovery read the tracked `docs/resources/` catalogue locators and queried `search_external`, channel `ulp_youtube`: `"тин" OR "тінь" OR "джміль" OR "дзиґа"` (108 broken ASR; 163 band-name hit), `"рука" OR "ріка" OR "letter names" OR "апостроф"`, and `"ґрати" OR "прилетіли" OR "пюре"` (including food episode 292). These hits do not prove exact primer contrasts or all letter names. The inherited exhaustive catalogue/corpus search remains in `listening-sources.md`; it is not claimed as a new exhaustive scan. `search_resources` is not exposed in this seat: driver condition is #9409 ingestion/tool integration and current MCP exposure, then the requested catalogue search.

MCP `verify_words`, `verify_stress`/`verify_stresses` and `vet_vocabulary` checked newly selected forms. Unresolved candidate stress was withheld. Word generation and verification supply stress and glosses; no model stress was added. Shadow screening returned no flags for the queried additions; that is suspicion screening, not a universal Russianism verdict. Grammar remains inherited, not established by dictionary gloss or shadow screening.

Entire Context was announced and loaded. Status was available; bounded search `8425 --limit 5` yielded an unrelated Git locator, not consumed. No recall adoption or independent review is claimed. Read-only issue lookup found #8425 OPEN; the authoring worker has no stream lease or merge authority.

## Family contracts and structural witnesses

Fixtures below are **structural stimuli**, not written lesson artifacts, held-out semantic proof or permission to build. Ordinary families use the base activity-array schema. Listening uses only the inspected proposed schema at fc02b4af5f0ad54fbd88f2411a60bd2fb524d501; base schema rejects that kind. The proposed model_target/choice_error functions are executed read-only without importing or merging that branch. Current A1 choice checks use actual VESUM lookups and the locked word store. Current host-order probes include negative activity-before-host cases. Public rights, resolver roles, rendering and independent text-question uniqueness remain integrated-driver checks.

| Family | Required fields / binding / order |
| --- | --- |
| quiz / comprehension / dialogue | Correct key, aligned option_why, feedback, host kind dialogue; actual planned dialogue block before every item |
| quiz or odd-one-out / comprehension / quote | Correct key, aligned option_why, feedback, exact T-ref; attributed displayed quote before item |
| quiz / listening / video | Correct key, aligned option_why, V-ref, single T-ref glyph model, marker-free taught glyph options; video precedes item. Segment/target playback confirmation pending |
| fill-in / orthography | Mode and kind orthography, printed word-local blank, target_record W-ref, valid learner completion, no other VESUM-word completion; no semantic form demand |
| letter-grid / observe | Upper/lower models; at least two sourced examples plus prompt; display only taught units |
| watch-and-repeat | Actual V URL and explanation; offline production, no machine accuracy claim |
| match-up | Explicit side roles, W-ref for each form side, sourced gloss, pair why |
| anagram / unjumble | Exact model character/word multiset, answer and feedback; whole source sentence retained |
| divide / count / pick syllables | Model, segmentation/count/index key and feedback; sourced CV units and taught letters |
| order | Source alphabet glyphs, complete permutation and feedback |


## Final deterministic gate tails

Commands ran from the assigned dispatch worktree using the prescribed shared interpreter and source/vesum databases. Public command text substitutes environment variables for private absolute paths. No offline weakening, promotion, write-report or full suite.

```bash
"$PROJECT_PYTHON" -m scripts.curriculum.evidence words-verify a1 --sources-db "$SOURCES_DB" --vesum-db "$VESUM_DB"
```

Exit 0:

```text
Word Store Verification: level=a1 status=OK
Verified: 175 records, 2125 forms
Open records / reports:
  pending forms: 211
  override forms: 4
  unresolved un-cited records: 0

```

```bash
"$PROJECT_PYTHON" -m scripts.curriculum.evidence pack-verify a1 sounds-letters-and-hello --strict --sources-db "$SOURCES_DB" --vesum-db "$VESUM_DB"
```

Exit 0:

```text
Evidence Pack Verification: module=a1/sounds-letters-and-hello status=OK
Verified: texts=37, exercises=5, examples=0, errors=0, notes=0, videos=16, standard=3
Unsupported: 0 open, 1 resolved

```

```bash
"$PROJECT_PYTHON" -m scripts.curriculum.validate a1 sounds-letters-and-hello --provisional-pack --write-scope
```

Exit 0:

```text
plan-validate: the §6 gate of docs/epics/fresh-build-plan-schema.md — §2 rules 1–7 with the semantics of §2a (single-plan and cross-plan). not_checked items are reported, never passed silently.
plan: a1/sounds-letters-and-hello
status: pass
mode: provisional
NOTE core_cefr_above_module: lesson 2: core lemma 'звук' (W-077) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 2: core lemma 'літера' (W-078) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 3: core lemma 'голосний' (W-079) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 3: core lemma 'приголосний' (W-080) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 4: core lemma 'малина' (W-082) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 4: core lemma 'слива' (W-083) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOT_CHECKED minutes_constants_undefined: not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)
NOT_CHECKED word_target_not_calibrated: not_checked: word_target presence and type are checked; the per-level minimum is not calibrated (§2a)
NOT_CHECKED lesson_activity_minimums_not_calibrated: not_checked: per-lesson inline/workbook activity minimums are not calibrated (§2a)
NOT_CHECKED arc_has_no_structured_grammar_or_vocabulary: not_checked: the arc carries letters only; it has no structured grammar or vocabulary to compare against (§2a)
NOT_CHECKED title_quantities_not_parsed: subtitle digits: 1, 3; digit quantities are not parsed — the plan review checks stated quantities against the scope sidecar (§2a)
NOT_CHECKED mechanical_rule_not_checked: gate M5 was not checked: core word records carry no CEFR level: W-074
activity_report (plan stage) module: workbook_activities=9 inline_activities=26 workbook_presence_complete=True largest_workbook_type_share=0.3333333333333333 longest_same_type_workbook_run=2
activity_report (plan stage) lesson 1: kind=teach inline=4 workbook=1 distinct_types=quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 2: kind=teach inline=4 workbook=2 distinct_types=letter-grid,observe,odd-one-out,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 3: kind=teach inline=6 workbook=2 distinct_types=letter-grid,odd-one-out,pick-syllables,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 4: kind=teach inline=4 workbook=2 distinct_types=divide-words,letter-grid,pick-syllables,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 5: kind=teach inline=5 workbook=2 distinct_types=letter-grid,match-up,pick-syllables,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 6: kind=recap inline=3 workbook=0 distinct_types=letter-grid,observe,quiz has_workbook=False

```

```bash
"$PROJECT_PYTHON" -m scripts.curriculum.evidence pack-verify a1 reading-ukrainian --strict --sources-db "$SOURCES_DB" --vesum-db "$VESUM_DB"
```

Exit 0:

```text
Evidence Pack Verification: module=a1/reading-ukrainian status=OK
Verified: texts=37, exercises=5, examples=4, errors=0, notes=0, videos=15, standard=0
Unsupported: 0 open, 4 resolved

```

```bash
"$PROJECT_PYTHON" -m scripts.curriculum.validate a1 reading-ukrainian --provisional-pack --write-scope
```

Exit 0:

```text
plan-validate: the §6 gate of docs/epics/fresh-build-plan-schema.md — §2 rules 1–7 with the semantics of §2a (single-plan and cross-plan). not_checked items are reported, never passed silently.
plan: a1/reading-ukrainian
status: pass
mode: provisional
NOT_CHECKED minutes_constants_undefined: not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)
NOT_CHECKED word_target_not_calibrated: not_checked: word_target presence and type are checked; the per-level minimum is not calibrated (§2a)
NOT_CHECKED lesson_activity_minimums_not_calibrated: not_checked: per-lesson inline/workbook activity minimums are not calibrated (§2a)
NOT_CHECKED arc_has_no_structured_grammar_or_vocabulary: not_checked: the arc carries letters only; it has no structured grammar or vocabulary to compare against (§2a)
NOT_CHECKED title_quantities_not_parsed: no ASCII digits in the title or subtitle; digit quantities are not parsed — the plan review checks stated quantities against the scope sidecar (§2a)
activity_report (plan stage) module: workbook_activities=13 inline_activities=35 workbook_presence_complete=True largest_workbook_type_share=0.23076923076923078 longest_same_type_workbook_run=1
activity_report (plan stage) lesson 1: kind=teach inline=5 workbook=3 distinct_types=fill-in,letter-grid,match-up,pick-syllables,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 2: kind=teach inline=7 workbook=2 distinct_types=divide-words,letter-grid,observe,quiz has_workbook=True
activity_report (plan stage) lesson 3: kind=teach inline=5 workbook=2 distinct_types=fill-in,letter-grid,odd-one-out,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 4: kind=teach inline=7 workbook=3 distinct_types=anagram,fill-in,letter-grid,match-up,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 5: kind=teach inline=7 workbook=3 distinct_types=letter-grid,observe,pick-syllables,quiz,unjumble has_workbook=True
activity_report (plan stage) lesson 6: kind=recap inline=4 workbook=0 distinct_types=letter-grid,observe,quiz has_workbook=False

```

```bash
"$PROJECT_PYTHON" -m scripts.curriculum.evidence pack-verify a1 special-signs --strict --sources-db "$SOURCES_DB" --vesum-db "$VESUM_DB"
```

Exit 0:

```text
Evidence Pack Verification: module=a1/special-signs status=OK
Verified: texts=36, exercises=5, examples=1, errors=0, notes=0, videos=12, standard=1
Unsupported: 0 open, 7 resolved

```

```bash
"$PROJECT_PYTHON" -m scripts.curriculum.validate a1 special-signs --provisional-pack --write-scope
```

Exit 0:

```text
plan-validate: the §6 gate of docs/epics/fresh-build-plan-schema.md — §2 rules 1–7 with the semantics of §2a (single-plan and cross-plan). not_checked items are reported, never passed silently.
plan: a1/special-signs
status: pass
mode: provisional
NOT_CHECKED minutes_constants_undefined: not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)
NOT_CHECKED word_target_not_calibrated: not_checked: word_target presence and type are checked; the per-level minimum is not calibrated (§2a)
NOT_CHECKED lesson_activity_minimums_not_calibrated: not_checked: per-lesson inline/workbook activity minimums are not calibrated (§2a)
NOT_CHECKED arc_has_no_structured_grammar_or_vocabulary: not_checked: the arc carries letters only; it has no structured grammar or vocabulary to compare against (§2a)
NOT_CHECKED title_quantities_not_parsed: no ASCII digits in the title or subtitle; digit quantities are not parsed — the plan review checks stated quantities against the scope sidecar (§2a)
activity_report (plan stage) module: workbook_activities=20 inline_activities=33 workbook_presence_complete=True largest_workbook_type_share=0.35 longest_same_type_workbook_run=2
activity_report (plan stage) lesson 1: kind=teach inline=4 workbook=2 distinct_types=fill-in,letter-grid,match-up,observe,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 2: kind=teach inline=4 workbook=3 distinct_types=anagram,fill-in,letter-grid,pick-syllables,quiz has_workbook=True
activity_report (plan stage) lesson 3: kind=teach inline=4 workbook=3 distinct_types=count-syllables,fill-in,letter-grid has_workbook=True
activity_report (plan stage) lesson 4: kind=teach inline=6 workbook=3 distinct_types=divide-words,fill-in,letter-grid,match-up,quiz has_workbook=True
activity_report (plan stage) lesson 5: kind=teach inline=4 workbook=3 distinct_types=anagram,fill-in,observe,pick-syllables has_workbook=True
activity_report (plan stage) lesson 6: kind=teach inline=4 workbook=3 distinct_types=fill-in,letter-grid,observe,odd-one-out,unjumble has_workbook=True
activity_report (plan stage) lesson 7: kind=teach inline=3 workbook=3 distinct_types=letter-grid,odd-one-out,order,quiz has_workbook=True
activity_report (plan stage) lesson 8: kind=recap inline=4 workbook=0 distinct_types=letter-grid,observe,quiz has_workbook=False

```

Mechanical notes are not silently cleared: inherited P1 core literacy/source terms звук, літера, голосний, приголосний, малина, слива are A2 in the word store; their planned literacy role is retained for review. P1 greeting CEFR absence and calibration gaps (minutes, word targets, per-lesson activity minimums, unstructured arc grammar/vocabulary, title quantity parsing) remain not_checked. Scope sidecars are generated, not approvals. Pending stress/ULIF forms in the shared store are not blanket learner admission; actual source forms are restricted below.

Affected tests already ran in the foreground: `$PROJECT_PYTHON -m pytest tests/curriculum/test_plan_validate.py tests/curriculum/evidence/test_schemas.py -q`: **111 passed in 27.97s**, exit 0. Ruff: `$PROJECT_PYTHON -m ruff check scripts/curriculum/evidence scripts/curriculum/validate`: **All checks passed!**, exit 0. These check contracts, not held-out pedagogy or integrated rendering.

## Current-base preflight (20 real lessons)

Actual `preflight_lesson(lesson, pack=pack, word_store=words)` results; no lesson-lock or gap-report writes, no writer invocation. Publication-right failures remain driver integration work and do not confer permission.

```json
[
  {
    "module": "sounds-letters-and-hello",
    "lesson": 1,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 2,
    "status": "evidence_gap",
    "passed": false,
    "gaps": [
      {
        "step": "s1-print",
        "need": "publication_right",
        "detail": "source for quote T-022 in step s1-print lacks verified publication right (WP 21 pending)"
      }
    ]
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 3,
    "status": "evidence_gap",
    "passed": false,
    "gaps": [
      {
        "step": "s1-print",
        "need": "publication_right",
        "detail": "source for quote T-026 in step s1-print lacks verified publication right (WP 21 pending)"
      },
      {
        "step": "s-print-workbook",
        "need": "publication_right",
        "detail": "source for quote T-037 in step s-print-workbook lacks verified publication right (WP 21 pending)"
      }
    ]
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 4,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 5,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 6,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "reading-ukrainian",
    "lesson": 1,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "reading-ukrainian",
    "lesson": 3,
    "status": "evidence_gap",
    "passed": false,
    "gaps": [
      {
        "step": "s2-print",
        "need": "publication_right",
        "detail": "source for quote T-035 in step s2-print lacks verified publication right (WP 21 pending)"
      }
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 4,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "status": "evidence_gap",
    "passed": false,
    "gaps": [
      {
        "step": "s3-print",
        "need": "publication_right",
        "detail": "source for quote T-036 in step s3-print lacks verified publication right (WP 21 pending)"
      },
      {
        "step": "s3-print",
        "need": "publication_right",
        "detail": "source for quote T-037 in step s3-print lacks verified publication right (WP 21 pending)"
      },
      {
        "step": "s3-print",
        "need": "publication_right",
        "detail": "source for quote T-032 in step s3-print lacks verified publication right (WP 21 pending)"
      },
      {
        "step": "s3-print",
        "need": "publication_right",
        "detail": "source for quote T-033 in step s3-print lacks verified publication right (WP 21 pending)"
      },
      {
        "step": "s3-print",
        "need": "publication_right",
        "detail": "source for quote T-029 in step s3-print lacks verified publication right (WP 21 pending)"
      },
      {
        "step": "s3-print",
        "need": "publication_right",
        "detail": "source for quote T-031 in step s3-print lacks verified publication right (WP 21 pending)"
      }
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 6,
    "status": "evidence_gap",
    "passed": false,
    "gaps": [
      {
        "step": "s2",
        "need": "publication_right",
        "detail": "source for quote T-034 in step s2 lacks verified publication right (WP 21 pending)"
      }
    ]
  },
  {
    "module": "special-signs",
    "lesson": 1,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "special-signs",
    "lesson": 2,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "special-signs",
    "lesson": 3,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "special-signs",
    "lesson": 4,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "special-signs",
    "lesson": 5,
    "status": "ok",
    "passed": true,
    "gaps": []
  },
  {
    "module": "special-signs",
    "lesson": 6,
    "status": "evidence_gap",
    "passed": false,
    "gaps": [
      {
        "step": "s-print-workbook",
        "need": "publication_right",
        "detail": "source for quote T-036 in step s-print-workbook lacks verified publication right (WP 21 pending)"
      }
    ]
  },
  {
    "module": "special-signs",
    "lesson": 7,
    "status": "evidence_gap",
    "passed": false,
    "gaps": [
      {
        "step": "s1-print",
        "need": "publication_right",
        "detail": "source for quote T-012 in step s1-print lacks verified publication right (WP 21 pending)"
      }
    ]
  },
  {
    "module": "special-signs",
    "lesson": 8,
    "status": "evidence_gap",
    "passed": false,
    "gaps": [
      {
        "step": "s2",
        "need": "publication_right",
        "detail": "source for quote T-035 in step s2 lacks verified publication right (WP 21 pending)"
      }
    ]
  }
]
```

## Complete teaching-job and all-activity coverage

All 20 original lessons and 136 activities are accounted for. Original IDs and placements remain. Quoted source displays are named separately from explains-only grounding. Notebook and voice tasks are offline. The following operations and bindings are copied from the actual plan instructions, not invented report-only permissions.

### Position 1: sounds-letters-and-hello

| Lesson | Original teaching job | Revised coverage / source proof | Unchanged minimum |
| --- | --- | --- | --- |
| L1 | Hear an informal or formal first greeting and say the appropriate memorised response aloud. | Hear an informal or formal first greeting and say the appropriate memorised response aloud. Steps s1, s2; records S-003, T-002, T-003, T-020, T-021, T-035, V-001, V-002, X-001; activities a1, a2, a3, a4, a5. | 210 words; letters recycling; grammar/core unchanged. |
| L2 | Tell an audible sound from a visible letter and recognise and copy А, О, У, И in primer order. | Tell an audible sound from a visible letter and recognise and copy А, О, У, И in primer order. Steps s1, s2, s1-print; records S-002, T-001, T-006, T-007, T-008, T-009, T-022, T-023, T-024, T-025, V-004, V-005, V-006, V-007; activities a1, a2, a3, a4, a5, a6. | 240 words; letters А, О, У, И; grammar/core unchanged. |
| L3 | Hear the vowel/consonant contrast, keep И distinct from І, and read first CV and VC syllables with М and Н. | Hear the vowel/consonant contrast, keep И distinct from І, and read first CV and VC syllables with М and Н. Steps s1, s1-print, s2, s3, s-print-workbook; records T-001, T-004, T-009, T-010, T-011, T-012, T-019, T-025, T-026, T-027, T-028, T-037, V-003, V-007, V-008, V-009, V-010, X-002, X-003; activities a1, a2, a3, a4, a5, a6, a7, a8. | 290 words; letters М, І, Н; grammar/core unchanged. |
| L4 | Read and copy syllables and short words after adding В, Л, С, checking Latin-shaped letters by their Ukrainian sounds. | Read and copy syllables and short words after adding В, Л, С, checking Latin-shaped letters by their Ukrainian sounds. Steps s1, s2; records S-002, T-006, T-007, T-010, T-013, T-014, T-015, T-019, T-029, T-030, T-031, V-011, V-012, V-013, X-003, X-005; activities a1, a2, a3, a4, a5, a6. | 250 words; letters В, Л, С; grammar/core unchanged. |
| L5 | Read and copy the final three letters and short words, then copy a sourced model name from a written model into a notebook. | Read and copy the final three letters and short words, then copy a sourced model name from a written model into a notebook. Steps s1, s2; records S-001, S-002, T-016, T-017, T-018, T-034, V-014, V-015, V-016, X-003, X-004, X-005; activities a1, a2, a3, a4, a5, a6, a7. | 290 words; letters К, П, Р; grammar/core unchanged. |
| L6 | Use a short first-person bilingual story to recognise the greetings and taught words, answer Ukrainian-only questions, and copy decodable model lines written with taught letters and a model personal name offline. | Recycle the module letters and words in a connected planned dialogue, answer Ukrainian-only questions about that exchange, and copy decodable source-model lines and a model personal name offline; any bilingual story is unscored support. Steps s1; records S-001, S-002, T-002, T-005, T-036, X-005; activities a1, a2, a3. | 170 words; letters recycling; grammar/core unchanged. |

All-activity buildability ledger:

| Lesson / activity | Type / placement / supported family | Required operation and record bindings | Host order / representative witness |
| --- | --- | --- | --- |
| L1 a1 | watch-and-repeat / inline / watch-and-repeat | Hear and say the informal greeting aloud; practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `watch-and-repeat` (same family field shape). |
| L1 a2 | quiz / inline / quiz/dialogue | Answer about the intact informal or formal greeting in the planned classroom exchange, retaining whole D3 chunks. Required item kind: comprehension; host: {kind: dialogue}. The actual dialogue block in s1 precedes a2, a4 and workbook a5; paired English support accompanies every stem, option and explanation. No spelling, name decoding, lexical paradigm or heard-phrase binding is scored. | s1; planned preceding dialogue; witness `quiz/dialogue` (same family field shape). |
| L1 a3 | watch-and-repeat / inline / watch-and-repeat | Hear and say the formal greeting aloud in a new situation; practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `watch-and-repeat` (same family field shape). |
| L1 a4 | quiz / inline / quiz/dialogue | Answer about the intact informal or formal greeting in the planned classroom exchange, retaining whole D3 chunks. Required item kind: comprehension; host: {kind: dialogue}. The actual dialogue block in s1 precedes a2, a4 and workbook a5; paired English support accompanies every stem, option and explanation. No spelling, name decoding, lexical paradigm or heard-phrase binding is scored. | s2; planned preceding dialogue; witness `quiz/dialogue` (same family field shape). |
| L1 a5 | quiz / workbook / quiz/dialogue | Answer about the intact informal or formal greeting in the planned classroom exchange, retaining whole D3 chunks. Required item kind: comprehension; host: {kind: dialogue}. The actual dialogue block in s1 precedes a2, a4 and workbook a5; paired English support accompanies every stem, option and explanation. No spelling, name decoding, lexical paradigm or heard-phrase binding is scored. | workbook consolidation after all steps; planned preceding dialogue; witness `quiz/dialogue` (same family field shape). |
| L2 a1 | observe / inline / observe | Notice the primer contrast between heard sound and visible letter. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L2 a2 | quiz / inline / quiz/quote | Choose whether a presented unit is heard or seen, from the primer model. Required item kind: comprehension; quote host refs T-022 must be displayed before this activity, with attribution. Stem/options depend on the displayed print; no new source prose or premium-note quote. | s1-print; exact attributed T-quote before item; witness `quiz/quote` (same family field shape). |
| L2 a3 | watch-and-repeat / inline / watch-and-repeat | Hear and repeat the four vowel sounds in primer order. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `watch-and-repeat` (same family field shape). |
| L2 a4 | letter-grid / inline / letter-grid | Find А, О, У, И and copy each shape into a notebook; copying practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L2 a5 | quiz / workbook / quiz/listening | Select the letter matching a replayed sound, with each choice grounded in its primer record. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-004/T-022, V-005/T-023, V-006/T-024, V-007/T-025. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. | workbook consolidation after all steps; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L2 a6 | odd-one-out / workbook / odd-one-out/quote | Select the taught vowel glyph that differs from the displayed T-022 capital/small pair. kind: comprehension; host: {kind: quote, ref: T-022}. Quote appears after vowel introduction and before workbook consolidation. This scores visible correspondence, while the native vowel videos model the heard sounds separately. | workbook consolidation after all steps; exact attributed T-quote before item; witness `odd-one-out/quote` (same family field shape). |
| L3 a1 | quiz / inline / quiz/quote | Choose the consonant represented by the displayed T-026 heading among the known vowel glyphs; kind: comprehension; host: {kind: quote, ref: T-026}. Show the source before a1. Hear and classify its native V-008 sound offline in s1; the scored item classifies the visible representation. | s1-print; exact attributed T-quote before item; witness `quiz/quote` (same family field shape). |
| L3 a2 | letter-grid / inline / letter-grid | Read first М+vowel and vowel+М rows, then copy the grid and model word into a notebook; copying practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L3 a3 | watch-and-repeat / inline / watch-and-repeat | Hear and repeat distinct И and І sounds before reading their symbols. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `watch-and-repeat` (same family field shape). |
| L3 a4 | quiz / inline / quiz/listening | Select И or І after a source-modeled contrast, without unsupported spelling distractors. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-007/T-025, V-009/T-027. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. | s2; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L3 a5 | letter-grid / inline / letter-grid | Read Н+vowel and vowel+Н rows on the primer syllable pattern, then copy the grid and model names into a notebook; copying practised offline — not machine-verified. | s3; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L3 a6 | quiz / inline / quiz/listening | Choose the Ukrainian sound for Н from the primer model, rejecting the Latin-shape guess. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-010/T-028. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s3; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L3 a7 | pick-syllables / workbook / pick-syllables | Choose syllables built from the taught letters to complete the decodable word мама and model names Ніна and Нонна. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `pick-syllables` (same family field shape). |
| L3 a8 | odd-one-out / workbook / odd-one-out/quote | Identify the odd printed syllable among taught М CV/VC combinations from T-037; kind: comprehension; host: {kind: quote, ref: T-037}. Display the complete row before workbook consolidation. Read the row aloud with a teacher offline; no missing syllable recording is claimed. | workbook consolidation after all steps; exact attributed T-quote before item; witness `odd-one-out/quote` (same family field shape). |
| L4 a1 | watch-and-repeat / inline / watch-and-repeat | Hear and repeat the В sound before trusting its Latin-looking shape. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `watch-and-repeat` (same family field shape). |
| L4 a2 | quiz / inline / quiz/listening | Choose the Ukrainian reading for the displayed В, with primer sound as the host, and classify the sound as a consonant. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-011/T-029. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s1; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L4 a3 | letter-grid / inline / letter-grid | Read Л and С rows and copy their letter shapes and model short words in a notebook; copying practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L4 a4 | pick-syllables / inline / pick-syllables | Select a missing syllable in a newly decodable short word. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `pick-syllables` (same family field shape). |
| L4 a5 | quiz / workbook / quiz/listening | Select the consonant letter (В, Л, or С) matching a replayed sound, modeled on the sound-to-letter choice of lesson 2 a5. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-011/T-029, V-012/T-030, V-013/T-031. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | workbook consolidation after all steps; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L4 a6 | divide-words / workbook / divide-words | Split taught short words and decodable names (малина, слива, Іван, Вова) into sounded syllables, with source-backed word forms. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `divide-words` (same family field shape). |
| L5 a1 | letter-grid / inline / letter-grid | Read and copy К and П syllable rows into a notebook; copying practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L5 a2 | pick-syllables / inline / pick-syllables | Pick CV or VC syllables for the new letter group to complete decodable words and names (коса, Павлик, Поліна). | s1; sourced model or offline teacher/media practice; no comprehension host; witness `pick-syllables` (same family field shape). |
| L5 a3 | watch-and-repeat / inline / watch-and-repeat | Hear and repeat Р before reading its Latin P-looking shape. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `watch-and-repeat` (same family field shape). |
| L5 a4 | quiz / inline / quiz/listening | Choose the Ukrainian sound for Р from the primer model, not the Latin-shape guess, and classify the sound as a consonant. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-016/T-034. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s2; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L5 a5 | letter-grid / inline / letter-grid | Display model words and a sourced personal-name copying frame; copy both by hand, not into a keyboard; practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L5 a6 | pick-syllables / workbook / pick-syllables | Complete newly readable short words and names by selecting missing syllables formed with К, П, and Р (коса, Павлик, Поліна, рука); progresses from syllable division to active word completion. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `pick-syllables` (same family field shape). |
| L5 a7 | match-up / workbook / match-up | Match taught core decodable word forms (мама, малина, слива, рука) to English glosses using bound W records; drills only core decodable vocabulary. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `match-up` (same family field shape). |
| L6 a1 | observe / inline / observe | Read the new planned dialogue after its Ukrainian-first/English-supported presentation; optionally retain the writer’s bilingual literacy story as separate unscored support. Recycle sound/letter and vowel/consonant distinctions in English-supported recall. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L6 a2 | quiz / inline / quiz/dialogue | kind: comprehension; host: {kind: dialogue}. Dialogue block precedes a2 in s1. Ukrainian-only decodable selection questions about the mother, the plum and the source answer, with different substantive keys; no question about the optional bilingual story. | s1; planned preceding dialogue; witness `quiz/dialogue` (same family field shape). |
| L6 a3 | letter-grid / inline / letter-grid | Display the decodable recap lines written only with the 13 taught letters and the model name frame for one notebook production task: copy the lines and model name; practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |

Changed-activity before/after:

| Id | Before type / host / action | After type / host / action | Why the job is retained |
| --- | --- | --- | --- |
| L1 a2 | quiz: Select the greeting just heard in an informal exchange, using a source-hosted comprehension choice. | quiz: Answer about the intact informal or formal greeting in the planned classroom exchange, retaining whole D3 chunks. Required item kind: comprehension; host: {kind: dialogue}. The actual dialogue block in s1 precedes a2, a4 and workbook a5; paired English support accompanies every stem, option and explanation. No spelling, name decoding, lexical paradigm or heard-phrase binding is scored. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L1 a4 | quiz: Select the greeting appropriate for a formal setting; keep the full phrase intact. | quiz: Answer about the intact informal or formal greeting in the planned classroom exchange, retaining whole D3 chunks. Required item kind: comprehension; host: {kind: dialogue}. The actual dialogue block in s1 precedes a2, a4 and workbook a5; paired English support accompanies every stem, option and explanation. No spelling, name decoding, lexical paradigm or heard-phrase binding is scored. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L1 a5 | quiz: Choose the appropriate whole greeting chunk across distinct sourced situations (meeting a friend or close family from T-002, speaking with a boss or a cashier from T-002, a receptionist from T-020, or a teacher from T-021); requires independent communicative decisions without spelling. | quiz: Answer about the intact informal or formal greeting in the planned classroom exchange, retaining whole D3 chunks. Required item kind: comprehension; host: {kind: dialogue}. The actual dialogue block in s1 precedes a2, a4 and workbook a5; paired English support accompanies every stem, option and explanation. No spelling, name decoding, lexical paradigm or heard-phrase binding is scored. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L2 a2 | quiz: Choose whether a presented unit is heard or seen, from the primer model. | quiz: Choose whether a presented unit is heard or seen, from the primer model. Required item kind: comprehension; quote host refs T-022 must be displayed before this activity, with attribution. Stem/options depend on the displayed print; no new source prose or premium-note quote. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L2 a5 | quiz: Select the letter matching a replayed sound, with each choice grounded in its primer record. | quiz: Select the letter matching a replayed sound, with each choice grounded in its primer record. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-004/T-022, V-005/T-023, V-006/T-024, V-007/T-025. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L2 a6 | odd-one-out: Select the visible letter that does not match a repeated heard-vowel model; source-hosted comprehension, not free typing. | odd-one-out: Select the taught vowel glyph that differs from the displayed T-022 capital/small pair. kind: comprehension; host: {kind: quote, ref: T-022}. Quote appears after vowel introduction and before workbook consolidation. This scores visible correspondence, while the native vowel videos model the heard sounds separately. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L3 a1 | quiz: Select vowel or consonant for a sound heard in the primer model. | quiz: Choose the consonant represented by the displayed T-026 heading among the known vowel glyphs; kind: comprehension; host: {kind: quote, ref: T-026}. Show the source before a1. Hear and classify its native V-008 sound offline in s1; the scored item classifies the visible representation. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L3 a4 | quiz: Select И or І after a source-modeled contrast, without unsupported spelling distractors. | quiz: Select И or І after a source-modeled contrast, without unsupported spelling distractors. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-007/T-025, V-009/T-027. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L3 a6 | quiz: Choose the Ukrainian sound for Н from the primer model, rejecting the Latin-shape guess. | quiz: Choose the Ukrainian sound for Н from the primer model, rejecting the Latin-shape guess. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-010/T-028. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L3 a8 | odd-one-out: Select the odd sound or syllable in grouped taught items (contrasting consonant sounds with vowels, or syllables containing И versus І); source-hosted contrast. | odd-one-out: Identify the odd printed syllable among taught М CV/VC combinations from T-037; kind: comprehension; host: {kind: quote, ref: T-037}. Display the complete row before workbook consolidation. Read the row aloud with a teacher offline; no missing syllable recording is claimed. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L4 a2 | quiz: Choose the Ukrainian reading for the displayed В, with primer sound as the host, and classify the sound as a consonant. | quiz: Choose the Ukrainian reading for the displayed В, with primer sound as the host, and classify the sound as a consonant. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-011/T-029. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L4 a5 | quiz: Select the consonant letter (В, Л, or С) matching a replayed sound, modeled on the sound-to-letter choice of lesson 2 a5. | quiz: Select the consonant letter (В, Л, or С) matching a replayed sound, modeled on the sound-to-letter choice of lesson 2 a5. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-011/T-029, V-012/T-030, V-013/T-031. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L5 a4 | quiz: Choose the Ukrainian sound for Р from the primer model, not the Latin-shape guess, and classify the sound as a consonant. | quiz: Choose the Ukrainian sound for Р from the primer model, not the Latin-shape guess, and classify the sound as a consonant. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-016/T-034. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L6 a1 | observe: Display the short Ukrainian-left and English-right first-person story; unscored reading support. | observe: Read the new planned dialogue after its Ukrainian-first/English-supported presentation; optionally retain the writer’s bilingual literacy story as separate unscored support. Recycle sound/letter and vowel/consonant distinctions in English-supported recall. | The authorized recap decision preserves connected reading, Ukrainian answers and module recycling; writer stories and ULP narrative audio are unscored support. |
| L6 a2 | quiz: Ask Ukrainian-only comprehension questions about the story using selection choices between story words or letters, or polar intonation questions (including answers with так or ні); score recognition only. | quiz: kind: comprehension; host: {kind: dialogue}. Dialogue block precedes a2 in s1. Ukrainian-only decodable selection questions about the mother, the plum and the source answer, with different substantive keys; no question about the optional bilingual story. | The authorized recap decision preserves connected reading, Ukrainian answers and module recycling; writer stories and ULP narrative audio are unscored support. |

U-record ledger: original claims and all inherited searches are preserved; conversion is not proof that an exact recording exists.

| Record | Original requirement | Explicit conversion / source and ownership |
| --- | --- | --- |
| U-001 | No confirmed free recording models the exact primer CV/VC/CVC combinations required to be heard in lesson 3 s1 and lesson 5 s1, or the W-084/W-085 and before-І contrasts in lessons 4 s2 and 5 s2. The letter videos establish their named sounds, not those complete primer combinations or word pairs. | authorization: Issue 8425 frozen round-1 revision brief plus round-2 recap-host decision; explicitly permitted print conversion, not evidence that an audio recording exists.<br>mode: audio-to-print<br>lessons: [3, 4, 5]<br>records: ['T-010', 'T-012', 'T-014', 'T-015', 'T-016', 'T-017', 'T-018', 'T-037', 'X-003', 'X-005']<br>words: ['W-081', 'W-084', 'W-085']<br>replacement: Exact plan steps and scored activity ids are in the coverage/conversion ledger in _requests/revise-a1-p1-p3.md; print discrimination plus offline read-aloud/copying, retaining the native letter video in the same teaching step.<br>teacher_dependency: Teacher models the exact syllable/word/contrast or letter name and listens to learner production offline; no machine speaking or acoustic equivalence claim.<br>remaining_audio_evidence: Original missing-recording claim remains historical; no existence or independent playback proof inferred from resolved status.<br> |

v1 placement/response-opportunity denominator (v2 item counts are unbuilt, so not estimated):

```json
{
  "inline": {
    "activities": {
      "total": 10,
      "by_type": {
        "error-correction": 1,
        "fill-in": 1,
        "group-sort": 1,
        "match-up": 1,
        "quiz": 3,
        "translate": 1,
        "true-false": 1,
        "watch-and-repeat": 1
      }
    },
    "response_opportunities": {
      "total": 62,
      "by_type": {
        "error-correction": 5,
        "fill-in": 6,
        "group-sort": 14,
        "match-up": 9,
        "quiz": 15,
        "translate": 7,
        "true-false": 6,
        "watch-and-repeat": 0
      }
    },
    "uncounted_activities": {
      "total": 0,
      "by_type": {}
    }
  },
  "workbook": {
    "activities": {
      "total": 0,
      "by_type": {}
    },
    "response_opportunities": {
      "total": 0,
      "by_type": {}
    },
    "uncounted_activities": {
      "total": 0,
      "by_type": {}
    }
  },
  "all": {
    "activities": {
      "total": 10,
      "by_type": {
        "error-correction": 1,
        "fill-in": 1,
        "group-sort": 1,
        "match-up": 1,
        "quiz": 3,
        "translate": 1,
        "true-false": 1,
        "watch-and-repeat": 1
      }
    },
    "response_opportunities": {
      "total": 62,
      "by_type": {
        "error-correction": 5,
        "fill-in": 6,
        "group-sort": 14,
        "match-up": 9,
        "quiz": 15,
        "translate": 7,
        "true-false": 6,
        "watch-and-repeat": 0
      }
    },
    "uncounted_activities": {
      "total": 0,
      "by_type": {}
    }
  }
}
```

### Position 2: reading-ukrainian

| Lesson | Original teaching job | Revised coverage / source proof | Unchanged minimum |
| --- | --- | --- | --- |
| L1 | Read and copy Т and Е, their sound rows, and newly decodable whole words including the informal greeting. | Read and copy Т and Е, their sound rows, and newly decodable whole words including the informal greeting. Steps s1, s2, s3; records T-001, T-002, T-003, T-021, T-022, T-023, V-001, V-005, X-001, X-004; activities a1, a2, a3, a4, a5, a6, a7, a8. | 260 words; letters Т, Е; grammar/core unchanged. |
| L2 | Read and copy Д, З and Б in primer order and move from short word parts to whole decodable words. | Read and copy Д, З and Б in primer order and move from short word parts to whole decodable words. Steps s1, s2, s3, s4; records EX-003, T-004, T-005, T-006, T-018, T-024, T-025, T-026, V-006, V-007, V-008, X-001, X-004; activities a1, a2, a3, a4, a5, a6, a7, a8, a9. | 300 words; letters Д, З, Б; grammar/core unchanged. |
| L3 | Hear, read and copy Г and Ґ as different sounds, then decode one source-backed word with each. | Hear, read and copy Г and Ґ as different sounds, then decode one source-backed word with each. Steps s1, s2, s2-print, s3; records EX-004, T-007, T-008, T-009, T-020, T-027, T-035, V-002, V-009, X-001, X-002, X-004; activities a1, a2, a3, a4, a5, a6, a7. | 260 words; letters Г, Ґ; grammar/core unchanged. |
| L4 | Read and copy Ч, Й and Х, then read new words without inserting an untaught sign or digraph. | Read and copy Ч, Й and Х, then read new words without inserting an untaught sign or digraph. Steps s1, s2, s3, s4; records T-004, T-010, T-011, T-012, T-019, T-021, T-029, T-030, T-031, V-003, V-010, V-011, X-001, X-004; activities a1, a2, a3, a4, a5, a6, a7, a8, a9, a10. | 300 words; letters Ч, Й, Х; grammar/core unchanged. |
| L5 | Read and copy Ж and Ш words, then read two whole sourced short sentences aloud. | Read and copy Ж and Ш words, then read two whole sourced short sentences aloud. Steps s1, s2, s3, s3-print; records EX-001, EX-002, T-013, T-014, T-015, T-029, T-031, T-032, T-033, T-036, T-037, V-010, V-011, V-012, V-013, X-001, X-003, X-004; activities a1, a2, a3, a4, a5, a6, a7, a8, a9, a10. | 320 words; letters Ж, Ш; grammar/core unchanged. |
| L6 | Hear a short first-person bilingual source story, answer Ukrainian-only questions about it by ear, read the two whole sourced sentences aloud, and copy decodable models plus an own-name model offline. | Listen to ULP 1-10 as an unscored model, read the connected primer passage and answer Ukrainian-only questions about it, then read EX-001/EX-002 whole and copy decodable source and own-name models offline. Steps s1, s2; records EX-001, EX-002, T-016, T-017, T-034, V-004, V-014, X-003, X-004; activities a1, a2, a3, a4. | 190 words; letters recycling; grammar/core unchanged. |

All-activity buildability ledger:

| Lesson / activity | Type / placement / supported family | Required operation and record bindings | Host order / representative witness |
| --- | --- | --- | --- |
| L1 a1 | letter-grid / inline / letter-grid | Read the Т CV and VC row from T-001 aloud, then copy the letter and the decodable W-101 and W-074 by hand; practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L1 a2 | quiz / inline / quiz/listening | Choose the Т letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-001/T-022. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s1; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L1 a3 | letter-grid / inline / letter-grid | Read the Е CV and VC rows from T-002 aloud, then copy the letter and the decodable W-117 by hand; practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L1 a4 | quiz / inline / quiz/listening | Choose the Е letter after hearing its primer sound; contrast it with earlier taught vowels and consonants, and include the Latin-shape check against the English letter name. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-005/T-023. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s2; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L1 a5 | watch-and-repeat / inline / watch-and-repeat | Hear the Т and Е models in V-001 and V-005, then read W-074, W-101, W-117 and W-102 whole aloud from print; practised offline — not machine-verified. | s3; sourced model or offline teacher/media practice; no comprehension host; witness `watch-and-repeat` (same family field shape). |
| L1 a6 | pick-syllables / workbook / pick-syllables | Select the missing taught syllable in three distinct core decodable records W-081, W-082 and W-101; spelling assembly after sound reading. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `pick-syllables` (same family field shape). |
| L1 a7 | match-up / workbook / match-up | Match three independent core form–gloss pairs W-081, W-082 and W-101; no greeting option because W-074 has no gloss. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `match-up` (same family field shape). |
| L1 a8 | fill-in / workbook / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-074, W-081, W-082, W-101, W-117. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print a whole word and choose its printed form among the decodable W-074, W-081, W-082, W-101 and W-117; the correct answer differs from item to item, and the check is word decoding, not meaning. | workbook consolidation after all steps; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L2 a1 | letter-grid / inline / letter-grid | Read the Д CV and VC row from T-004 aloud, then copy the letter and decodable W-116 by hand; practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L2 a2 | quiz / inline / quiz/listening | Choose the Д letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-006/T-024. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s1; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L2 a3 | letter-grid / inline / letter-grid | Read the З CV and VC row from T-005 aloud, then copy the letter and decodable W-104 by hand; practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L2 a4 | quiz / inline / quiz/listening | Choose the З letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-007/T-025. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s2; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L2 a5 | letter-grid / inline / letter-grid | Read the Б word list from T-018 aloud, then copy the letter and decodable W-118 and W-105 by hand; practised offline — not machine-verified. | s3; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L2 a6 | quiz / inline / quiz/listening | Choose the Б letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-008/T-026. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s3; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L2 a7 | observe / inline / observe | Read the new decodable words W-116, W-104, W-118 and W-105 aloud from print after sound-row practice; practised offline — not machine-verified. | s4; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L2 a8 | divide-words / workbook / divide-words | Divide three previously taught core decodable words W-081, W-101 and W-104 by their visible vowels; contrast the three word shapes rather than glosses. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `divide-words` (same family field shape). |
| L2 a9 | quiz / workbook / quiz/listening | Choose the letter for a heard Д, З or Б sound across a balanced mixed set; the answer is not the same for every item, and the contrast differs from syllable division. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-006/T-024, V-007/T-025, V-008/T-026. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. | workbook consolidation after all steps; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L3 a1 | letter-grid / inline / letter-grid | Read the Г CV and VC row from T-007 aloud, then copy the letter and decodable W-106 by hand; practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L3 a2 | quiz / inline / quiz/listening | Choose the Г letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-009/T-027. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s1; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L3 a3 | letter-grid / inline / letter-grid | Read the Ґ CV and VC row from T-009 aloud, then copy the letter and decodable W-107 by hand; practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L3 a4 | quiz / inline / quiz/quote | Distinguish the displayed Г/Ґ spellings across the complete six-word T-035 / EX-004 row; choose the requested printed member of a pair. kind: comprehension; host: {kind: quote, ref: T-035}. Source quote precedes the activity. Read every pair aloud with teacher modeling offline; V-009/V-002 model individual letters only. | s2-print; exact attributed T-quote before item; witness `quiz/quote` (same family field shape). |
| L3 a5 | watch-and-repeat / inline / watch-and-repeat | Hear the Г and Ґ models in V-009 and V-002, then read W-106 and W-107 whole aloud from print; practised offline — not machine-verified. | s3; sourced model or offline teacher/media practice; no comprehension host; witness `watch-and-repeat` (same family field shape). |
| L3 a6 | odd-one-out / workbook / odd-one-out/quote | Distinguish the displayed Г/Ґ spellings across the complete six-word T-035 / EX-004 row; choose the word whose initial glyph differs in a mixed printed set. kind: comprehension; host: {kind: quote, ref: T-035}. Source quote precedes the activity. Read every pair aloud with teacher modeling offline; V-009/V-002 model individual letters only. | workbook consolidation after all steps; exact attributed T-quote before item; witness `odd-one-out/quote` (same family field shape). |
| L3 a7 | fill-in / workbook / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-106, W-107, W-081, W-101, W-104. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print a taught decodable word (W-106, W-107, W-081, W-101 or W-104) and choose the letter it begins with among Г, Ґ and earlier consonants; the answer changes from item to item, progressing from the lesson-2 sound-to-letter quiz to the new Г/Ґ contrast. | workbook consolidation after all steps; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L4 a1 | letter-grid / inline / letter-grid | Read the Ч CV and VC row from T-010 aloud, then copy the letter and decodable W-108 by hand; practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L4 a2 | quiz / inline / quiz/listening | Choose the Ч letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-010/T-029. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s1; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L4 a3 | letter-grid / inline / letter-grid | Read the vowel-plus-Й row from T-011 aloud, then copy the letter and decodable W-109 by hand; practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L4 a4 | quiz / inline / quiz/listening | Choose the Й letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-003/T-030. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s2; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L4 a5 | letter-grid / inline / letter-grid | Read the Х syllables and word list from T-019 aloud, then copy the letter and decodable W-110 by hand; practised offline — not machine-verified. | s3; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L4 a6 | quiz / inline / quiz/listening | Choose the Ukrainian sound for the displayed Х from the primer model, rejecting the Latin-shape guess, and classify it as a consonant. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-011/T-031. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s3; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L4 a7 | watch-and-repeat / inline / watch-and-repeat | Hear the Ч, Й and Х models in V-010, V-003 and V-011, then read W-108, W-109, W-110 and W-103 whole aloud from print; practised offline — not machine-verified. | s4; sourced model or offline teacher/media practice; no comprehension host; witness `watch-and-repeat` (same family field shape). |
| L4 a8 | match-up / workbook / match-up | Match four distinct core form–gloss pairs W-104, W-109, W-110 and W-118; each pair has a separate meaning decision, and none repeats a lesson-1 pair. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `match-up` (same family field shape). |
| L4 a9 | anagram / workbook / anagram | Assemble the letters of three taught core decodable words W-101, W-104 and W-109; a whole-word construction decision after the previous lesson’s sound selection. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `anagram` (same family field shape). |
| L4 a10 | fill-in / workbook / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-101, W-103, W-108, W-109, W-110. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print a whole word and choose its printed form among the decodable W-101, W-103, W-108, W-109 and W-110; distractors differ in one of the new letters, and the answer changes from item to item. | workbook consolidation after all steps; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L5 a1 | letter-grid / inline / letter-grid | Read the Ж CV and VC row from T-013 aloud, then copy the letter and decodable W-111 by hand; practised offline — not machine-verified. W-111 remains incidental: decode its letters without testing its meaning. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L5 a2 | quiz / inline / quiz/listening | Choose the Ж letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-012/T-032. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s1; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L5 a3 | letter-grid / inline / letter-grid | Read the Ш CV and VC row from T-014 aloud, then copy the letter and decodable W-112 by hand; practised offline — not machine-verified. W-112 remains incidental: decode its letters without testing its meaning. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L5 a4 | quiz / inline / quiz/listening | Choose the Ш letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-013/T-033. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s2; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L5 a5 | observe / inline / observe | Display EX-001 and EX-002 whole with their source context and English support; unscored preparation for reading aloud. | s3; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L5 a6 | observe / inline / observe | Read EX-001 and EX-002 whole aloud from print, preserving every word and punctuation; practised offline — not machine-verified. | s3; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L5 a7 | quiz / inline / quiz/quote | Read EX-001/EX-002 whole and answer source-text questions about arrival versus the frog enquiry. kind: comprehension; each item uses its exact host {kind: quote, ref: T-036} or {kind: quote, ref: T-037}; show both unchanged sentence quotes before a7. No sentence or multiword listening key. | s3-print; exact attributed T-quote before item; witness `quiz/quote` (same family field shape). |
| L5 a8 | unjumble / workbook / unjumble | Reorder each whole sourced sentence EX-001 and EX-002 from its original word set; never compose, shorten or add a sentence. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `unjumble` (same family field shape). |
| L5 a9 | quiz / workbook / quiz/listening | Choose the letter for a heard Ж, Ш, Ч or Х sound across a balanced mixed set, keeping the vowel/consonant classification; it extends the lesson-2 and lesson-3 sound-to-letter quizzes to the last four consonants. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-012/T-032, V-013/T-033, V-010/T-029, V-011/T-031. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | workbook consolidation after all steps; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L5 a10 | pick-syllables / workbook / pick-syllables | Complete the decodable W-111, W-112 and W-104 by selecting the missing syllable; the check is spelling with the new letters, not meaning, and it differs from the whole-sentence reordering task. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `pick-syllables` (same family field shape). |
| L6 a1 | observe / inline / observe | Listen to V-004 as an unscored public ULP 1-10 model after the intact V-014 greeting; then read the public-primer quote in s2. T-016/T-017 are explains-only grounding, never displayed note text. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L6 a2 | quiz / inline / quiz/quote | kind: comprehension; host: {kind: quote, ref: T-034}. Present the attributed quote before a2 in s2. Ukrainian-only questions about the season and the arriving birds; keys must depend on the text. Printed decodable options only, not premium-note questions or spoken sentence bindings. Required item kind: comprehension; quote host refs T-034 must be displayed before this activity, with attribution. Stem/options depend on the displayed print; no new source prose or premium-note quote. | s2; exact attributed T-quote before item; witness `quiz/quote` (same family field shape). |
| L6 a3 | observe / inline / observe | Read EX-001 and EX-002 whole aloud from print; practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L6 a4 | letter-grid / inline / letter-grid | Copy EX-001 and EX-002 whole, the decodable core words W-101, W-104, W-109, W-110 and W-118, the sourced W-093 name model, and one’s own name from an existing personal model into a notebook; practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |

Changed-activity before/after:

| Id | Before type / host / action | After type / host / action | Why the job is retained |
| --- | --- | --- | --- |
| L1 a2 | quiz: Choose the Т letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. | quiz: Choose the Т letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-001/T-022. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L1 a4 | quiz: Choose the Е letter after hearing its primer sound; contrast it with earlier taught vowels and consonants, and include the Latin-shape check against the English letter name. | quiz: Choose the Е letter after hearing its primer sound; contrast it with earlier taught vowels and consonants, and include the Latin-shape check against the English letter name. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-005/T-023. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L1 a8 | quiz: Hear a whole word and choose its printed form among the decodable W-074, W-081, W-082, W-101 and W-117; the correct answer differs from item to item, and the check is word decoding, not meaning. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-074, W-081, W-082, W-101, W-117. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print a whole word and choose its printed form among the decodable W-074, W-081, W-082, W-101 and W-117; the correct answer differs from item to item, and the check is word decoding, not meaning. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L2 a2 | quiz: Choose the Д letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. | quiz: Choose the Д letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-006/T-024. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L2 a4 | quiz: Choose the З letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. | quiz: Choose the З letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-007/T-025. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L2 a6 | quiz: Choose the Б letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. | quiz: Choose the Б letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-008/T-026. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L2 a9 | quiz: Choose the letter for a heard Д, З or Б sound across a balanced mixed set; the answer is not the same for every item, and the contrast differs from syllable division. | quiz: Choose the letter for a heard Д, З or Б sound across a balanced mixed set; the answer is not the same for every item, and the contrast differs from syllable division. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-006/T-024, V-007/T-025, V-008/T-026. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L3 a2 | quiz: Choose the Г letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. | quiz: Choose the Г letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-009/T-027. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L3 a4 | quiz: Choose Г or Ґ after hearing a primer syllable, with answers alternating between the two sounds. | quiz: Distinguish the displayed Г/Ґ spellings across the complete six-word T-035 / EX-004 row; choose the requested printed member of a pair. kind: comprehension; host: {kind: quote, ref: T-035}. Source quote precedes the activity. Read every pair aloud with teacher modeling offline; V-009/V-002 model individual letters only. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L3 a6 | odd-one-out: Select the different heard consonant among mixed Г and Ґ audio models; answers alternate across both sounds and cite the primer contrast. | odd-one-out: Distinguish the displayed Г/Ґ spellings across the complete six-word T-035 / EX-004 row; choose the word whose initial glyph differs in a mixed printed set. kind: comprehension; host: {kind: quote, ref: T-035}. Source quote precedes the activity. Read every pair aloud with teacher modeling offline; V-009/V-002 model individual letters only. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L3 a7 | quiz: Hear a taught decodable word (W-106, W-107, W-081, W-101 or W-104) and choose the letter it begins with among Г, Ґ and earlier consonants; the answer changes from item to item, progressing from the lesson-2 sound-to-letter quiz to the new Г/Ґ contrast. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-106, W-107, W-081, W-101, W-104. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print a taught decodable word (W-106, W-107, W-081, W-101 or W-104) and choose the letter it begins with among Г, Ґ and earlier consonants; the answer changes from item to item, progressing from the lesson-2 sound-to-letter quiz to the new Г/Ґ contrast. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L4 a2 | quiz: Choose the Ч letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. | quiz: Choose the Ч letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-010/T-029. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L4 a4 | quiz: Choose the Й letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. | quiz: Choose the Й letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-003/T-030. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L4 a6 | quiz: Choose the Ukrainian sound for the displayed Х from the primer model, rejecting the Latin-shape guess, and classify it as a consonant. | quiz: Choose the Ukrainian sound for the displayed Х from the primer model, rejecting the Latin-shape guess, and classify it as a consonant. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-011/T-031. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L4 a10 | quiz: Hear a whole word and choose its printed form among the decodable W-101, W-103, W-108, W-109 and W-110; distractors differ in one of the new letters, and the answer changes from item to item. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-101, W-103, W-108, W-109, W-110. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print a whole word and choose its printed form among the decodable W-101, W-103, W-108, W-109 and W-110; distractors differ in one of the new letters, and the answer changes from item to item. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L5 a2 | quiz: Choose the Ж letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. | quiz: Choose the Ж letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-012/T-032. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L5 a4 | quiz: Choose the Ш letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. | quiz: Choose the Ш letter after hearing its primer sound; contrast it with earlier taught sounds, with both vowel and consonant answers represented. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-013/T-033. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L5 a7 | quiz: Hear one of the two whole sentences EX-001 and EX-002, or one word from them, and choose the matching printed item; every option is decodable, and the answers vary across the set. | quiz: Read EX-001/EX-002 whole and answer source-text questions about arrival versus the frog enquiry. kind: comprehension; each item uses its exact host {kind: quote, ref: T-036} or {kind: quote, ref: T-037}; show both unchanged sentence quotes before a7. No sentence or multiword listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L5 a9 | quiz: Choose the letter for a heard Ж, Ш, Ч or Х sound across a balanced mixed set, keeping the vowel/consonant classification; it extends the lesson-2 and lesson-3 sound-to-letter quizzes to the last four consonants. | quiz: Choose the letter for a heard Ж, Ш, Ч or Х sound across a balanced mixed set, keeping the vowel/consonant classification; it extends the lesson-2 and lesson-3 sound-to-letter quizzes to the last four consonants. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-012/T-032, V-013/T-033, V-010/T-029, V-011/T-031. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L6 a1 | observe: Hear the complete first-person source sentences in V-004 while seeing their T-016 Ukrainian-left and English-right alignment; the story is by-ear only. | observe: Listen to V-004 as an unscored public ULP 1-10 model after the intact V-014 greeting; then read the public-primer quote in s2. T-016/T-017 are explains-only grounding, never displayed note text. | The authorized recap decision preserves connected reading, Ukrainian answers and module recycling; writer stories and ULP narrative audio are unscored support. |
| L6 a2 | quiz: Ask the first three Ukrainian-only T-017 questions about the heard story by ear, with heard answer options from T-017; each question has a different correct answer, and no item is a decoding task. | quiz: kind: comprehension; host: {kind: quote, ref: T-034}. Present the attributed quote before a2 in s2. Ukrainian-only questions about the season and the arriving birds; keys must depend on the text. Printed decodable options only, not premium-note questions or spoken sentence bindings. Required item kind: comprehension; quote host refs T-034 must be displayed before this activity, with attribution. Stem/options depend on the displayed print; no new source prose or premium-note quote. | The authorized recap decision preserves connected reading, Ukrainian answers and module recycling; writer stories and ULP narrative audio are unscored support. |

U-record ledger: original claims and all inherited searches are preserved; conversion is not proof that an exact recording exists.

| Record | Original requirement | Explicit conversion / source and ownership |
| --- | --- | --- |
| U-002 | No confirmed free recording covers all exact whole-word choices required by lessons 1 s3/a8, 3 s3/a7 and 4 a10. Public letter videos use different example words. V-014 supports W-074, V-004 supports W-081/W-101, and V-015 supports W-118/W-109/W-110; these do not establish the remaining word sets. Lesson 3 a4 also needs exact primer Г/Ґ syllable recordings. Each remaining required word or syllable needs an exact-form recording before a by-ear item can be written. | authorization: Issue 8425 frozen round-1 revision brief plus round-2 recap-host decision; explicitly permitted print conversion, not evidence that an audio recording exists.<br>mode: audio-to-print<br>lessons: [1, 3, 4]<br>records: ['T-001', 'T-002', 'T-007', 'T-009', 'T-019', 'T-035', 'EX-004']<br>words: ['W-074', 'W-081', 'W-082', 'W-101', 'W-102', 'W-103', 'W-106', 'W-107', 'W-108', 'W-109', 'W-110', 'W-117']<br>replacement: Exact plan steps and scored activity ids are in the coverage/conversion ledger in _requests/revise-a1-p1-p3.md; print discrimination plus offline read-aloud/copying, retaining the native letter video in the same teaching step.<br>teacher_dependency: Teacher models the exact syllable/word/contrast or letter name and listens to learner production offline; no machine speaking or acoustic equivalence claim.<br>remaining_audio_evidence: Original missing-recording claim remains historical; no existence or independent playback proof inferred from resolved status.<br> |
| U-003 | No confirmed free recording says either whole primer sentence EX-001 or EX-002 required by lesson 5 s3/a7. Printed T-015 and X-003 establish reading material, not recorded speech. V-004 supplies the recap story and questions only. | authorization: Issue 8425 frozen round-1 revision brief plus round-2 recap-host decision; explicitly permitted print conversion, not evidence that an audio recording exists.<br>mode: audio-to-print<br>lessons: [5]<br>records: ['T-036', 'T-037', 'EX-001', 'EX-002']<br>words: ['W-006', 'W-007', 'W-061', 'W-087', 'W-113', 'W-114', 'W-115']<br>replacement: Exact plan steps and scored activity ids are in the coverage/conversion ledger in _requests/revise-a1-p1-p3.md; print discrimination plus offline read-aloud/copying, retaining the native letter video in the same teaching step.<br>teacher_dependency: Teacher models the exact syllable/word/contrast or letter name and listens to learner production offline; no machine speaking or acoustic equivalence claim.<br>remaining_audio_evidence: Original missing-recording claim remains historical; no existence or independent playback proof inferred from resolved status.<br> |
| U-004 | The complete T-018 and X-002 rows are bound to word records by EX-003 and EX-004. Lesson 2 s3/a5 still lacks W-145/W-146/W-147/W-148 in its core/incidental/recycled allowlist, and lesson 3 s2 lacks W-149/W-150/W-151/W-152/W-153. W-035 is the existing base preposition. The pack and word store cannot change the frozen plan allowlists; the plan author must admit all nine new incidental decoding records before the complete rows can pass inventory checks. | authorization: Issue 8425 frozen round-1 revision brief plus round-2 recap-host decision; explicitly permitted print conversion, not evidence that an audio recording exists.<br>mode: complete-row word admission<br>lessons: [2, 3]<br>records: ['T-018', 'X-002', 'EX-003', 'EX-004']<br>words: ['W-145', 'W-146', 'W-147', 'W-148', 'W-149', 'W-150', 'W-151', 'W-152', 'W-153', 'W-035', 'W-107', 'W-118']<br>replacement: Exact plan steps and scored activity ids are in the coverage/conversion ledger in _requests/revise-a1-p1-p3.md; print discrimination plus offline read-aloud/copying, retaining the native letter video in the same teaching step.<br>teacher_dependency: Teacher models the exact syllable/word/contrast or letter name and listens to learner production offline; no machine speaking or acoustic equivalence claim.<br>remaining_audio_evidence: Original missing-recording claim remains historical; no existence or independent playback proof inferred from resolved status.<br> |

v1 placement/response-opportunity denominator (v2 item counts are unbuilt, so not estimated):

```json
{
  "inline": {
    "activities": {
      "total": 4,
      "by_type": {
        "count-syllables": 1,
        "divide-words": 1,
        "error-correction": 1,
        "match-up": 1
      }
    },
    "response_opportunities": {
      "total": 22,
      "by_type": {
        "count-syllables": 6,
        "divide-words": 6,
        "error-correction": 4,
        "match-up": 6
      }
    },
    "uncounted_activities": {
      "total": 0,
      "by_type": {}
    }
  },
  "workbook": {
    "activities": {
      "total": 6,
      "by_type": {
        "group-sort": 1,
        "match-up": 1,
        "odd-one-out": 1,
        "quiz": 1,
        "true-false": 1,
        "watch-and-repeat": 1
      }
    },
    "response_opportunities": {
      "total": 24,
      "by_type": {
        "group-sort": 8,
        "match-up": 5,
        "odd-one-out": 4,
        "quiz": 3,
        "true-false": 4,
        "watch-and-repeat": 0
      }
    },
    "uncounted_activities": {
      "total": 0,
      "by_type": {}
    }
  },
  "all": {
    "activities": {
      "total": 10,
      "by_type": {
        "count-syllables": 1,
        "divide-words": 1,
        "error-correction": 1,
        "group-sort": 1,
        "match-up": 2,
        "odd-one-out": 1,
        "quiz": 1,
        "true-false": 1,
        "watch-and-repeat": 1
      }
    },
    "response_opportunities": {
      "total": 46,
      "by_type": {
        "count-syllables": 6,
        "divide-words": 6,
        "error-correction": 4,
        "group-sort": 8,
        "match-up": 11,
        "odd-one-out": 4,
        "quiz": 3,
        "true-false": 4,
        "watch-and-repeat": 0
      }
    },
    "uncounted_activities": {
      "total": 0,
      "by_type": {}
    }
  }
}
```

### Position 3: special-signs

| Lesson | Original teaching job | Revised coverage / source proof | Unchanged minimum |
| --- | --- | --- | --- |
| L1 | Hear hard and soft consonants, read and copy the soft sign and its sourced word pair, and read the whole formal greeting. | Hear hard and soft consonants, read and copy the soft sign and its sourced word pair, and read the whole formal greeting. Steps s1, s2; records T-001, T-013, T-014, T-019, V-001, V-006, V-007, X-001, X-003; activities a1, a2, a3, a4, a5, a6. | 260 words; letters ь; grammar/core unchanged. |
| L2 | Read and copy Ї as two sounds and Я in its two values, including word-start, post-vowel and post-soft-sign models. | Read and copy Ї as two sounds and Я in its two values, including word-start, post-vowel and post-soft-sign models. Steps s1, s2; records T-002, T-003, T-013, T-030, V-002, V-008, X-003; activities a1, a2, a3, a4, a5, a6, a7. | 340 words; letters Ї, Я; grammar/core unchanged. |
| L3 | Read and copy Ю and Є in their two values after consonants, at word start and after vowels. | Read and copy Ю and Є in their two values after consonants, at word start and after vowels. Steps s1, s2; records T-004, T-005, T-013, T-022, T-025, V-002, V-003, X-003; activities a1, a2, a3, a4, a5, a6, a7. | 320 words; letters Ю, Є; grammar/core unchanged. |
| L4 | Read and copy Ц, Щ and Ф words and distinguish the two sounds represented by Щ from a single-consonant letter. | Read and copy Ц, Щ and Ф words and distinguish the two sounds represented by Щ from a single-consonant letter. Steps s1, s2, s3; records T-006, T-007, T-008, T-012, T-013, T-018, T-023, T-028, T-029, T-033, T-034, V-002, V-004, V-005, V-011, V-012, X-002, X-003; activities a1, a2, a3, a4, a5, a6, a7, a8, a9. | 360 words; letters Ц, Щ, Ф; grammar/core unchanged. |
| L5 | Read and copy words with joined дж and дз sounds and hear the hard/soft contrast for дз. | Read and copy words with joined дж and дз sounds and hear the hard/soft contrast for дз. Steps s1, s2; records T-009, T-010, T-013, T-016, T-017, V-002, X-002, X-003; activities a1, a2, a3, a4, a5, a6, a7. | 300 words; letters recycling; grammar/core unchanged. |
| L6 | Read and copy apostrophe-bearing words with separate pronunciation, then read a whole sourced sentence containing the apostrophe. | Read and copy apostrophe-bearing words with separate pronunciation, then read a whole sourced sentence containing the apostrophe. Steps s1, s2, s-print-workbook; records EX-001, T-011, T-013, T-015, T-017, T-024, T-026, T-036, V-002, X-003, X-005; activities a1, a2, a3, a4, a5, a6, a7. | 340 words; letters recycling; grammar/core unchanged. |
| L7 | Use the complete alphabet in dictionary order, say the sourced letter names and connect capital to small letters. | Use the complete alphabet in dictionary order, say the sourced letter names and connect capital to small letters. Steps s1, s1-print, s2; records S-001, T-003, T-012, T-013, V-002, X-003; activities a1, a2, a3, a4, a5, a6. | 260 words; letters recycling; grammar/core unchanged. |
| L8 | Hear and read a short first-person bilingual review, answer Ukrainian-only story questions and copy source models plus one’s own name offline. | Recycle all module letters, signs and word models, read the connected primer passage and answer Ukrainian-only questions about it, and copy source models plus an own-name model offline; any bilingual story is unscored support. Steps s1, s2; records EX-001, T-020, T-021, T-035, X-001, X-003, X-005; activities a1, a2, a3, a4. | 200 words; letters recycling; grammar/core unchanged. |

All-activity buildability ledger:

| Lesson / activity | Type / placement / supported family | Required operation and record bindings | Host order / representative witness |
| --- | --- | --- | --- |
| L1 a1 | watch-and-repeat / inline / watch-and-repeat | Watch the V-001 soft-sign model and V-007 general softness trainer, then read W-119/W-120 aloud from print with teacher modeling; neither recording is claimed to contain the complete source pair. Speaking is offline, unscored. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `watch-and-repeat` (same family field shape). |
| L1 a2 | letter-grid / inline / letter-grid | Read aloud and copy ь, W-119/W-120 and the intact W-075+W-076 greeting; do not add a vowel for the silent sign. Practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L1 a3 | fill-in / inline / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-119, W-120. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print either member of the X-001 pair and choose its printed word; alternate hard and soft answers, not a same-key run. | s1; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L1 a4 | observe / inline / observe | Read W-074, W-075+W-076, W-081 and W-101 aloud from print after the listening contrast. Practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L1 a5 | fill-in / workbook / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-119, W-120. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Distinguish the printed X-001 hard/soft pair among W-119/W-120, then select the printed W-076, W-081 and W-101 for printed whole words; different correct answers. | workbook consolidation after all steps; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L1 a6 | match-up / workbook / match-up | Match three independent form–gloss pairs W-076, W-081 and W-101; each form bound to its own word record; never match the unglossed W-074. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `match-up` (same family field shape). |
| L2 a1 | letter-grid / inline / letter-grid | Read aloud and copy Ї, W-121 and the T-002 plural form of W-010; both Ї contexts keep two sounds. Practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L2 a2 | quiz / inline / quiz/listening | Hear the Ї model and select its letter among taught vowels; include earlier single-vowel sounds so answers vary. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-008/T-030. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. | s1; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L2 a3 | letter-grid / inline / letter-grid | Read aloud and copy Я with W-122, W-123, W-141 and W-142, distinguishing one vowel plus softness from two sounds. Practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L2 a4 | fill-in / inline / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-122, W-123, W-141, W-142. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Select the T-013 sound model for each of W-122, W-123, W-141 and W-142; both values must occur in the scored set. | s2; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L2 a5 | pick-syllables / workbook / pick-syllables | Complete the W-121 decoding puzzle using taught syllables; keep one puzzle per activity and do not require typing. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `pick-syllables` (same family field shape). |
| L2 a6 | fill-in / workbook / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-121, W-122, W-123, W-141. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print W-121, W-122, W-123 or W-141 and choose the matching printed whole word, testing Ї/Я decoding rather than incidental meanings. | workbook consolidation after all steps; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L2 a7 | anagram / workbook / anagram | Reconstruct W-121, W-081 and W-101 from taught letters; whole-word assembly differs from the single syllable puzzle. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `anagram` (same family field shape). |
| L3 a1 | letter-grid / inline / letter-grid | Read aloud and copy Ю, W-124/W-125 and the T-025 form of W-140; keep the two values separate. Practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L3 a2 | fill-in / inline / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-124, W-125, W-140. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Choose the sourced Ю sound model for W-124, W-125 and the T-025 form of W-140; both one-vowel and two-sound answers occur. | s1; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L3 a3 | letter-grid / inline / letter-grid | Read aloud and copy Є with the T-022, T-005 and T-013 forms of W-127, W-126 and W-010. Practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L3 a4 | fill-in / inline / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-127, W-126, W-010. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Choose the sourced Є sound model for the word-start, post-consonant and post-vowel examples; do not score adjective agreement. | s2; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L3 a5 | fill-in / workbook / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-124, W-125, W-126, W-127, W-010. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print mixed sourced Ю/Є models and choose the word whose reading value differs, rotating the odd position; use W-124/W-125, W-126, W-127 and W-010, not a grammatical group-sort. | workbook consolidation after all steps; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L3 a6 | fill-in / workbook / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-124, W-125, W-127. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print three distinct whole words among W-124, W-125 and W-127 and choose their printed forms; pronunciation decoding, not a gloss test for the unglossed W-125. | workbook consolidation after all steps; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L3 a7 | count-syllables / workbook / count-syllables | Count vowel nuclei in the taught W-121 and the source forms of W-124/W-125; two sounds represented by one letter do not create two syllables. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `count-syllables` (same family field shape). |
| L4 a1 | letter-grid / inline / letter-grid | Read the Ц CV/VC rows and W-128 aloud, then copy Ц and the whole word. Practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L4 a2 | quiz / inline / quiz/listening | Choose Ц for its heard sound among earlier sounds, then distinguish the hard and soft Ц source models; rotate correct answers. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-004/T-028. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s1; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L4 a3 | letter-grid / inline / letter-grid | Read the Щ row, W-129 and W-130 aloud, then copy the letter and both words. Practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L4 a4 | quiz / inline / quiz/listening | Choose Щ or the earlier Ш after hearing the native models; include both so the two-consonant Щ reading is actually tested. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-011/T-033, V-012/T-034. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s2; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L4 a5 | letter-grid / inline / letter-grid | Read the Ф CV/VC rows and W-131 aloud, then copy the letter and word. Practised offline — not machine-verified. | s3; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L4 a6 | quiz / inline / quiz/listening | Choose Ф or another taught consonant after hearing its native sound; no English visual-comparison option. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-005/T-029. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | s3; lesson-listed V before item, glyph T target; independent segment playback pending; witness `quiz/listening` (same family field shape). |
| L4 a7 | divide-words / workbook / divide-words | Divide W-128, W-129 and W-131 into sounded syllables using their written vowels; specialist meanings remain incidental. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `divide-words` (same family field shape). |
| L4 a8 | match-up / workbook / match-up | Match three independent form–gloss pairs W-121, W-130 and W-101, adding rain to the earlier food/father set without repeating lesson-1 decisions. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `match-up` (same family field shape). |
| L4 a9 | fill-in / workbook / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-128, W-129, W-130, W-131. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print W-128, W-129, W-130 or W-131 and select the printed whole word; extend the two-value work to Ц, Щ and Ф word decoding. | workbook consolidation after all steps; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L5 a1 | observe / inline / observe | Hear and read W-132 and W-133 whole aloud, then copy both; join дж into one source sound. Practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L5 a2 | fill-in / inline / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-132, W-133. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print a T-009 word and select its printed form among W-132/W-133 and earlier W-130; do not use prefixed exception words. | s1; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L5 a3 | observe / inline / observe | Hear the two дз source values, read W-134 and the T-010 present form of W-135 aloud and copy both whole. Practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L5 a4 | fill-in / inline / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-134, W-135. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Choose the hard or soft T-010 sound model for W-134 versus the present source form of W-135; both answer classes occur. | s2; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L5 a5 | anagram / workbook / anagram | Assemble W-132, W-133 and W-134 from taught letters, keeping each adjacent digraph intact when reading the result. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `anagram` (same family field shape). |
| L5 a6 | fill-in / workbook / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-132, W-133, W-134, W-135. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print one of W-132/W-133/W-134 or the T-010 present form of W-135 and select the matching printed whole word; the new decision is digraph joining, not a gloss. | workbook consolidation after all steps; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L5 a7 | pick-syllables / workbook / pick-syllables | Complete the W-134 spinning-top decoding puzzle on the primer word-building pattern; one puzzle, no typing. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `pick-syllables` (same family field shape). |
| L6 a1 | letter-grid / inline / letter-grid | Read aloud and copy the sourced apostrophe forms of W-136, W-137, W-139 and W-144, plus the no-apostrophe W-143 contrast. Practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L6 a2 | fill-in / inline / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-143, W-137. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Select the printed word for the printed source model, mixing apostrophe and no-apostrophe W-143/W-137 examples; reading separate pronunciation is the target, no invented misspellings. | s1; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L6 a3 | observe / inline / observe | Read EX-001 whole aloud from print with its attribution and English support. Practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L6 a4 | letter-grid / inline / letter-grid | Copy EX-001 whole and its apostrophe-bearing family word by hand; preserve every word and punctuation. Practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L6 a5 | unjumble / workbook / unjumble | Reorder the complete original word set of EX-001; preserve its entire sentence and punctuation rather than creating an unsourced sentence. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `unjumble` (same family field shape). |
| L6 a6 | fill-in / workbook / fill-in/orthography | Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-136, W-139, W-144. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print W-136, W-139 or W-144 and choose its sourced printed form, then select the full EX-001 for its printed sentence; no all-identical answer set. | workbook consolidation after all steps; word-local W completion; no comprehension host; witness `fill-in/orthography` (same family field shape). |
| L6 a7 | odd-one-out / workbook / odd-one-out/quote | Inspect the complete printed contrast пюре — п’ю in T-036 and identify presence versus absence of the apostrophe. Required item kind: comprehension; host: {kind: quote, ref: T-036}. Display the attributed public-textbook quote in s-print-workbook before workbook consolidation. Rotate the key position; meaning and acoustic discrimination are not scored. Read the contrast aloud offline after the teacher models its pronunciation. | workbook consolidation after all steps; exact attributed T-quote before item; witness `odd-one-out/quote` (same family field shape). |
| L7 a1 | letter-grid / inline / letter-grid | Say all sourced names in dictionary order, then copy each capital/small pair from T-012. Practised offline — not machine-verified. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L7 a2 | quiz / inline / quiz/quote | Select the capital/small glyph corresponding to a printed T-012 letter name; kind: comprehension; host: {kind: quote, ref: T-012}. Show the attributed alphabet table before a2. Say each name aloud with teacher modeling offline; V-002 supplies sound support only, never letter-name evidence. | s1-print; exact attributed T-quote before item; witness `quiz/quote` (same family field shape). |
| L7 a3 | letter-grid / inline / letter-grid | Read and copy the five taught word models plus W-141, then write one’s own name from an already-written model into a notebook. Practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |
| L7 a4 | order / workbook / order | Put short mixed groups of taught letter glyphs in the T-012 dictionary order; use different parts of the full alphabet, not the primer teaching order. | workbook consolidation after all steps; sourced model or offline teacher/media practice; no comprehension host; witness `order` (same family field shape). |
| L7 a5 | odd-one-out / workbook / odd-one-out/quote | From T-012, choose the small glyph that does not correspond to a displayed capital, and reverse the direction in other items; different target letters, no lexical form matching. Required item kind: comprehension; quote host refs T-012 must be displayed before this activity, with attribution. Stem/options depend on the displayed print; no new source prose or premium-note quote. | workbook consolidation after all steps; exact attributed T-quote before item; witness `odd-one-out/quote` (same family field shape). |
| L7 a6 | quiz / workbook / quiz/quote | Select the T-012 predecessor or successor of a shown letter among taught glyphs; mixed positions give different answers and progress from name recall to alphabet navigation. Required item kind: comprehension; quote host refs T-012 must be displayed before this activity, with attribution. Stem/options depend on the displayed print; no new source prose or premium-note quote. | workbook consolidation after all steps; exact attributed T-quote before item; witness `quiz/quote` (same family field shape). |
| L8 a1 | observe / inline / observe | Show one short first-person review story in Ukrainian-left/English-right alignment, using only allowed records and the T-020 methodology; no reference-author persona. | s1; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L8 a2 | quiz / inline / quiz/quote | kind: comprehension; host: {kind: quote, ref: T-035}. Attributed quote precedes a2 in s2. Ask Ukrainian-only questions whose answers come from the rain/snail text, with printed options and substantive varied answers; the optional bilingual story never hosts scored items. Required item kind: comprehension; quote host refs T-035 must be displayed before this activity, with attribution. Stem/options depend on the displayed print; no new source prose or premium-note quote. | s2; exact attributed T-quote before item; witness `quiz/quote` (same family field shape). |
| L8 a3 | observe / inline / observe | Read EX-001 whole and the sourced X-001 pair aloud from print; recognition scores do not stand for speaking. Practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `observe` (same family field shape). |
| L8 a4 | letter-grid / inline / letter-grid | One notebook production task: copy EX-001, W-120, W-121, W-122, W-124, the T-005 neuter W-126, W-128, W-129, W-131, W-132, W-134, W-136, sourced W-141 and capital/small pairs; write own name from an existing model. Practised offline — not machine-verified. | s2; sourced model or offline teacher/media practice; no comprehension host; witness `letter-grid` (same family field shape). |

Changed-activity before/after:

| Id | Before type / host / action | After type / host / action | Why the job is retained |
| --- | --- | --- | --- |
| L1 a1 | watch-and-repeat: Hear the soft-sign model and repeat the source pair W-119/W-120 before reading. Practised offline — not machine-verified. | watch-and-repeat: Watch the V-001 soft-sign model and V-007 general softness trainer, then read W-119/W-120 aloud from print with teacher modeling; neither recording is claimed to contain the complete source pair. Speaking is offline, unscored. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L1 a3 | quiz: Hear either member of the X-001 pair and choose its printed word; alternate hard and soft answers, not a same-key run. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-119, W-120. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print either member of the X-001 pair and choose its printed word; alternate hard and soft answers, not a same-key run. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L1 a5 | quiz: Distinguish the heard X-001 hard/soft pair among W-119/W-120, then select the printed W-076, W-081 and W-101 for heard whole words; different correct answers. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-119, W-120. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Distinguish the printed X-001 hard/soft pair among W-119/W-120, then select the printed W-076, W-081 and W-101 for printed whole words; different correct answers. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L2 a2 | quiz: Hear the Ї model and select its letter among taught vowels; include earlier single-vowel sounds so answers vary. | quiz: Hear the Ї model and select its letter among taught vowels; include earlier single-vowel sounds so answers vary. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-008/T-030. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L2 a4 | quiz: Select the T-013 sound model for each of W-122, W-123, W-141 and W-142; both values must occur in the scored set. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-122, W-123, W-141, W-142. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Select the T-013 sound model for each of W-122, W-123, W-141 and W-142; both values must occur in the scored set. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L2 a6 | quiz: Hear W-121, W-122, W-123 or W-141 and choose the matching printed whole word, testing Ї/Я decoding rather than incidental meanings. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-121, W-122, W-123, W-141. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print W-121, W-122, W-123 or W-141 and choose the matching printed whole word, testing Ї/Я decoding rather than incidental meanings. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L3 a2 | quiz: Choose the sourced Ю sound model for W-124, W-125 and the T-025 form of W-140; both one-vowel and two-sound answers occur. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-124, W-125, W-140. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Choose the sourced Ю sound model for W-124, W-125 and the T-025 form of W-140; both one-vowel and two-sound answers occur. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L3 a4 | quiz: Choose the sourced Є sound model for the word-start, post-consonant and post-vowel examples; do not score adjective agreement. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-127, W-126, W-010. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Choose the sourced Є sound model for the word-start, post-consonant and post-vowel examples; do not score adjective agreement. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L3 a5 | odd-one-out: Hear mixed sourced Ю/Є models and choose the word whose reading value differs, rotating the odd position; use W-124/W-125, W-126, W-127 and W-010, not a grammatical group-sort. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-124, W-125, W-126, W-127, W-010. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print mixed sourced Ю/Є models and choose the word whose reading value differs, rotating the odd position; use W-124/W-125, W-126, W-127 and W-010, not a grammatical group-sort. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L3 a6 | quiz: Hear three distinct whole words among W-124, W-125 and W-127 and choose their printed forms; pronunciation decoding, not a gloss test for the unglossed W-125. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-124, W-125, W-127. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print three distinct whole words among W-124, W-125 and W-127 and choose their printed forms; pronunciation decoding, not a gloss test for the unglossed W-125. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L4 a2 | quiz: Choose Ц for its heard sound among earlier sounds, then distinguish the hard and soft Ц source models; rotate correct answers. | quiz: Choose Ц for its heard sound among earlier sounds, then distinguish the hard and soft Ц source models; rotate correct answers. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-004/T-028. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L4 a4 | quiz: Choose Щ or the earlier Ш after hearing the native models; include both so the two-consonant Щ reading is actually tested. | quiz: Choose Щ or the earlier Ш after hearing the native models; include both so the two-consonant Щ reading is actually tested. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-011/T-033, V-012/T-034. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L4 a6 | quiz: Choose Ф or another taught consonant after hearing its native sound; no English visual-comparison option. | quiz: Choose Ф or another taught consonant after hearing its native sound; no English visual-comparison option. Required item kind: listening; each item binds host {kind: video, ref: V-id} and one T-id target_record using these aligned pairs: V-005/T-029. Present its video block before the item; choices are taught single glyphs, never words, sound-class labels, letter names or a whole greeting. Independent segment playback remains driver-owned. Classification/hard-soft/shape commentary is English-supported offline practice from the primer, not a second unsupported listening key. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L4 a9 | quiz: Hear W-128, W-129, W-130 or W-131 and select the printed whole word; extend the two-value work to Ц, Щ and Ф word decoding. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-128, W-129, W-130, W-131. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print W-128, W-129, W-130 or W-131 and select the printed whole word; extend the two-value work to Ц, Щ and Ф word decoding. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L5 a2 | quiz: Hear a T-009 word and select its printed form among W-132/W-133 and earlier W-130; do not use prefixed exception words. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-132, W-133. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print a T-009 word and select its printed form among W-132/W-133 and earlier W-130; do not use prefixed exception words. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L5 a4 | quiz: Choose the hard or soft T-010 sound model for W-134 versus the present source form of W-135; both answer classes occur. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-134, W-135. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Choose the hard or soft T-010 sound model for W-134 versus the present source form of W-135; both answer classes occur. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L5 a6 | quiz: Hear one of W-132/W-133/W-134 or the T-010 present form of W-135 and select the matching printed whole word; the new decision is digraph joining, not a gloss. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-132, W-133, W-134, W-135. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print one of W-132/W-133/W-134 or the T-010 present form of W-135 and select the matching printed whole word; the new decision is digraph joining, not a gloss. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L6 a2 | quiz: Select the printed word for the heard source model, mixing apostrophe and no-apostrophe W-143/W-137 examples; hearing separate pronunciation is the target, no invented misspellings. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-143, W-137. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Select the printed word for the printed source model, mixing apostrophe and no-apostrophe W-143/W-137 examples; reading separate pronunciation is the target, no invented misspellings. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L6 a6 | quiz: Hear W-136, W-139 or W-144 and choose its sourced printed form, then select the full EX-001 for its heard sentence; no all-identical answer set. | fill-in: Read aloud from print with teacher modeling offline, then complete the sourced printed word in fill-in mode orthography (kind: orthography). Target records: W-136, W-139, W-144. Each item has a printed word-local blank, target_record and marker-free learner key; every wrong completion must be verified as a nonword. Keep all taught positional/sign/digraph contrasts across the listed targets; spoken discrimination and word meaning are not machine-scored. Original teaching job retained as print decoding plus teacher-supported pronunciation: Read aloud from print W-136, W-139 or W-144 and choose its sourced printed form, then select the full EX-001 for its printed sentence; no all-identical answer set. | Retains sourced literacy discrimination and exact word/letter models; unsupported acoustic scoring is explicitly replaced by authorized print choice and offline teacher read-aloud. |
| L6 a7 | odd-one-out: Choose the one source model with different separate-pronunciation behavior among no-apostrophe W-143/W-125 and apostrophe forms of W-137/W-136; vary which class is odd and rotate its position. This tests the source sound contrast, never word meaning. | odd-one-out: Inspect the complete printed contrast пюре — п’ю in T-036 and identify presence versus absence of the apostrophe. Required item kind: comprehension; host: {kind: quote, ref: T-036}. Display the attributed public-textbook quote in s-print-workbook before workbook consolidation. Rotate the key position; meaning and acoustic discrimination are not scored. Read the contrast aloud offline after the teacher models its pronunciation. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L7 a2 | quiz: Hear a T-012 letter name and select its glyph; mix new and earlier letters and distinguish the name task from a sound-to-letter task. | quiz: Select the capital/small glyph corresponding to a printed T-012 letter name; kind: comprehension; host: {kind: quote, ref: T-012}. Show the attributed alphabet table before a2. Say each name aloud with teacher modeling offline; V-002 supplies sound support only, never letter-name evidence. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L7 a5 | odd-one-out: From T-012, choose the small glyph that does not correspond to a displayed capital, and reverse the direction in other items; different target letters, no lexical form matching. | odd-one-out: From T-012, choose the small glyph that does not correspond to a displayed capital, and reverse the direction in other items; different target letters, no lexical form matching. Required item kind: comprehension; quote host refs T-012 must be displayed before this activity, with attribution. Stem/options depend on the displayed print; no new source prose or premium-note quote. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L7 a6 | quiz: Select the T-012 predecessor or successor of a shown letter among taught glyphs; mixed positions give different answers and progress from name recall to alphabet navigation. | quiz: Select the T-012 predecessor or successor of a shown letter among taught glyphs; mixed positions give different answers and progress from name recall to alphabet navigation. Required item kind: comprehension; quote host refs T-012 must be displayed before this activity, with attribution. Stem/options depend on the displayed print; no new source prose or premium-note quote. | Retains the source-text or letter discrimination objective, with an explicit accepted host field and source-before-item order; exact acoustic production remains offline where converted. |
| L8 a2 | quiz: Ask Ukrainian-only questions about this story and its shown models, with heard or printed options that the story supports; mixed substantive answers, not all yes/no. | quiz: kind: comprehension; host: {kind: quote, ref: T-035}. Attributed quote precedes a2 in s2. Ask Ukrainian-only questions whose answers come from the rain/snail text, with printed options and substantive varied answers; the optional bilingual story never hosts scored items. Required item kind: comprehension; quote host refs T-035 must be displayed before this activity, with attribution. Stem/options depend on the displayed print; no new source prose or premium-note quote. | The authorized recap decision preserves connected reading, Ukrainian answers and module recycling; writer stories and ULP narrative audio are unscored support. |

U-record ledger: original claims and all inherited searches are preserved; conversion is not proof that an exact recording exists.

| Record | Original requirement | Explicit conversion / source and ownership |
| --- | --- | --- |
| U-003 | No confirmed free recording models both W-119 and W-120 as the intact T-001/X-001 hard/soft pair required by lesson 1 s1/a1/a3/a5. V-001 has other example words and V-007 is generic hard/soft support; the corpus occurrence resembling W-119 is a broken ASR boundary, not the intended noun. | authorization: Issue 8425 frozen round-1 revision brief plus round-2 recap-host decision; explicitly permitted print conversion, not evidence that an audio recording exists.<br>mode: audio-to-print<br>lessons: [1]<br>records: ['T-001', 'X-001']<br>words: ['W-119', 'W-120']<br>replacement: Exact plan steps and scored activity ids are in the coverage/conversion ledger in _requests/revise-a1-p1-p3.md; print discrimination plus offline read-aloud/copying, retaining the native letter video in the same teaching step.<br>teacher_dependency: Teacher models the exact syllable/word/contrast or letter name and listens to learner production offline; no machine speaking or acoustic equivalence claim.<br>remaining_audio_evidence: Original missing-recording claim remains historical; no existence or independent playback proof inferred from resolved status.<br> |
| U-004 | No confirmed free recording covers all exact Ї/Я and Ю/Є primer word values and whole-word choices in lessons 2 a4/a6 and 3 a2/a4/a5/a6, or all Ц/Щ/Ф word choices in lesson 4 a9. V-002/V-003/V-004/V-005 establish the named sounds, not the complete required word sets or positional contrasts. | authorization: Issue 8425 frozen round-1 revision brief plus round-2 recap-host decision; explicitly permitted print conversion, not evidence that an audio recording exists.<br>mode: audio-to-print<br>lessons: [2, 3, 4]<br>records: ['T-002', 'T-003', 'T-004', 'T-005', 'T-006', 'T-007', 'T-008', 'T-013', 'T-022', 'T-023', 'T-025']<br>words: ['W-121', 'W-122', 'W-123', 'W-124', 'W-125', 'W-126', 'W-127', 'W-128', 'W-129', 'W-130', 'W-131', 'W-010', 'W-140', 'W-141', 'W-142']<br>replacement: Exact plan steps and scored activity ids are in the coverage/conversion ledger in _requests/revise-a1-p1-p3.md; print discrimination plus offline read-aloud/copying, retaining the native letter video in the same teaching step.<br>teacher_dependency: Teacher models the exact syllable/word/contrast or letter name and listens to learner production offline; no machine speaking or acoustic equivalence claim.<br>remaining_audio_evidence: Original missing-recording claim remains historical; no existence or independent playback proof inferred from resolved status.<br> |
| U-005 | No confirmed free recording models the T-009/T-010 joined дж/дз words and hard/soft дз contrast required by lesson 5 s1/s2/a1/a2/a3/a4/a6. V-002 recalls letter sounds only; it cannot establish the joined digraph words or rule. | authorization: Issue 8425 frozen round-1 revision brief plus round-2 recap-host decision; explicitly permitted print conversion, not evidence that an audio recording exists.<br>mode: audio-to-print<br>lessons: [5]<br>records: ['T-009', 'T-010', 'T-013', 'T-016', 'T-017']<br>words: ['W-132', 'W-133', 'W-134', 'W-135']<br>replacement: Exact plan steps and scored activity ids are in the coverage/conversion ledger in _requests/revise-a1-p1-p3.md; print discrimination plus offline read-aloud/copying, retaining the native letter video in the same teaching step.<br>teacher_dependency: Teacher models the exact syllable/word/contrast or letter name and listens to learner production offline; no machine speaking or acoustic equivalence claim.<br>remaining_audio_evidence: Original missing-recording claim remains historical; no existence or independent playback proof inferred from resolved status.<br> |
| U-006 | No confirmed free recording covers the exact T-015 W-143/W-137 apostrophe contrast, T-011/T-026 word forms and EX-001 whole sentence required by lesson 6 s1/a2/a6. Printed source forms are not audio; V-002 supplies vowel sounds only. | authorization: Issue 8425 frozen round-1 revision brief plus round-2 recap-host decision; explicitly permitted print conversion, not evidence that an audio recording exists.<br>mode: audio-to-print<br>lessons: [6]<br>records: ['T-011', 'T-015', 'T-017', 'T-026', 'EX-001', 'T-036']<br>words: ['W-125', 'W-136', 'W-137', 'W-139', 'W-143', 'W-144']<br>replacement: Exact plan steps and scored activity ids are in the coverage/conversion ledger in _requests/revise-a1-p1-p3.md; print discrimination plus offline read-aloud/copying, retaining the native letter video in the same teaching step.<br>teacher_dependency: Teacher models the exact syllable/word/contrast or letter name and listens to learner production offline; no machine speaking or acoustic equivalence claim.<br>remaining_audio_evidence: Original missing-recording claim remains historical; no existence or independent playback proof inferred from resolved status.<br> |
| U-007 | No confirmed free recording models all T-012 letter names required by lesson 7 a2. V-002 models letter sounds and example words, not the complete letter-name inventory; sounds cannot substitute for names. | authorization: Issue 8425 frozen round-1 revision brief plus round-2 recap-host decision; explicitly permitted print conversion, not evidence that an audio recording exists.<br>mode: audio-to-print<br>lessons: [7]<br>records: ['T-012']<br>words: []<br>replacement: Exact plan steps and scored activity ids are in the coverage/conversion ledger in _requests/revise-a1-p1-p3.md; print discrimination plus offline read-aloud/copying, retaining the native letter video in the same teaching step.<br>teacher_dependency: Teacher models the exact syllable/word/contrast or letter name and listens to learner production offline; no machine speaking or acoustic equivalence claim.<br>remaining_audio_evidence: Original missing-recording claim remains historical; no existence or independent playback proof inferred from resolved status.<br> |

v1 placement/response-opportunity denominator (v2 item counts are unbuilt, so not estimated):

```json
{
  "inline": {
    "activities": {
      "total": 5,
      "by_type": {
        "divide-words": 1,
        "error-correction": 1,
        "fill-in": 1,
        "match-up": 1,
        "quiz": 1
      }
    },
    "response_opportunities": {
      "total": 20,
      "by_type": {
        "divide-words": 4,
        "error-correction": 4,
        "fill-in": 4,
        "match-up": 5,
        "quiz": 3
      }
    },
    "uncounted_activities": {
      "total": 0,
      "by_type": {}
    }
  },
  "workbook": {
    "activities": {
      "total": 7,
      "by_type": {
        "error-correction": 1,
        "fill-in": 1,
        "group-sort": 1,
        "match-up": 1,
        "odd-one-out": 1,
        "quiz": 1,
        "true-false": 1
      }
    },
    "response_opportunities": {
      "total": 39,
      "by_type": {
        "error-correction": 6,
        "fill-in": 5,
        "group-sort": 14,
        "match-up": 4,
        "odd-one-out": 3,
        "quiz": 3,
        "true-false": 4
      }
    },
    "uncounted_activities": {
      "total": 0,
      "by_type": {}
    }
  },
  "all": {
    "activities": {
      "total": 12,
      "by_type": {
        "divide-words": 1,
        "error-correction": 2,
        "fill-in": 2,
        "group-sort": 1,
        "match-up": 2,
        "odd-one-out": 1,
        "quiz": 2,
        "true-false": 1
      }
    },
    "response_opportunities": {
      "total": 59,
      "by_type": {
        "divide-words": 4,
        "error-correction": 10,
        "fill-in": 9,
        "group-sort": 14,
        "match-up": 9,
        "odd-one-out": 3,
        "quiz": 6,
        "true-false": 4
      }
    },
    "uncounted_activities": {
      "total": 0,
      "by_type": {}
    }
  }
}
```

Activity denominator: 136; changed activity instruction/type records: 61. Original lesson targets, grammar, core vocabulary, introduced-letter sequence, activity IDs and placements compare equal except the explicitly authorized recap jobs.

18 structural fixtures (15 distinct family shapes plus three recap bindings). All schema and structural checks pass, 16 current choice checks pass, the order check crashes as shown, and the proposed listening model/choice functions return no error. This is not an integrated listening check-7 pass.

```json
{
  "letter-grid": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    }
  },
  "observe": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    }
  },
  "watch-and-repeat": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    }
  },
  "match-up": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    }
  },
  "anagram": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    }
  },
  "count-syllables": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    }
  },
  "divide-words": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    }
  },
  "pick-syllables": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    }
  },
  "order": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "status": "crashed",
      "error": "'str' object has no attribute 'get'",
      "owner": "driver engine lane"
    }
  },
  "unjumble": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    }
  },
  "odd-one-out/quote": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    },
    "wrong_order_eligible": false
  },
  "fill-in/orthography": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    }
  },
  "quiz/quote": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    },
    "wrong_order_eligible": false
  },
  "quiz/dialogue": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    },
    "wrong_order_eligible": false
  },
  "quiz/listening": {
    "schema_errors": [],
    "structural_error": null,
    "model_target": [
      "А",
      null
    ],
    "choice_error": null,
    "base_schema_valid": false,
    "base_check7": "unsupported listening; integrated rerun required"
  },
  "recap-P1/dialogue": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    },
    "wrong_order_eligible": false
  },
  "recap-P2/quote": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    },
    "wrong_order_eligible": false
  },
  "recap-P3/quote": {
    "schema_errors": [],
    "structural_error": null,
    "check7": {
      "check": 7,
      "status": "passed",
      "details": {
        "requirement_receipts": []
      }
    },
    "wrong_order_eligible": false
  }
}
```

Exact fixture payloads (English structural scaffolding is not shipped lesson prose):

```json
{
  "letter-grid": {
    "type": "letter-grid",
    "letters": [
      {
        "upper": "М",
        "lower": "м"
      }
    ],
    "id": "w1"
  },
  "observe": {
    "type": "observe",
    "examples": [
      "тин",
      "тінь"
    ],
    "prompt": "Compare the printed soft sign.",
    "id": "w2"
  },
  "watch-and-repeat": {
    "type": "watch-and-repeat",
    "items": [
      {
        "video": "https://www.ukrainianlessons.com/episode5/",
        "explanation": "Repeat the native letter model offline."
      }
    ],
    "id": "w3"
  },
  "match-up": {
    "type": "match-up",
    "instruction": "Match sourced words and glosses.",
    "left_role": "form",
    "right_role": "gloss",
    "pairs": [
      {
        "left": "мама",
        "left_record": "W-081",
        "right": "mama, mummy, mom, ma",
        "why": "Locked dictionary gloss."
      },
      {
        "left": "малина",
        "left_record": "W-082",
        "right": "raspberries (fruit); raspberry (plant)",
        "why": "Locked dictionary gloss."
      }
    ],
    "id": "w4"
  },
  "anagram": {
    "type": "anagram",
    "instruction": "Reassemble the source word.",
    "items": [
      {
        "letters": [
          "м",
          "а",
          "а",
          "м"
        ],
        "answer": "мама",
        "explanation": "Source model."
      }
    ],
    "id": "w5"
  },
  "count-syllables": {
    "type": "count-syllables",
    "items": [
      {
        "word": "мама",
        "correct": 2,
        "explanation": "Two vowel positions."
      }
    ],
    "id": "w6"
  },
  "divide-words": {
    "type": "divide-words",
    "items": [
      {
        "word": "мама",
        "answer": "ма-ма",
        "explanation": "Repeated source CV unit."
      }
    ],
    "id": "w7"
  },
  "pick-syllables": {
    "type": "pick-syllables",
    "syllables": [
      "ма",
      "ма",
      "мо"
    ],
    "correctIndices": [
      0,
      1
    ],
    "category": "мама",
    "explanation": "Two model CV units.",
    "id": "w8"
  },
  "order": {
    "type": "order",
    "instruction": "Use the alphabet table.",
    "items": [
      "Б",
      "А"
    ],
    "correct_order": [
      1,
      0
    ],
    "explanation": "T-012 places А before Б.",
    "id": "w9"
  },
  "unjumble": {
    "type": "unjumble",
    "instruction": "Restore the whole source sentence.",
    "items": [
      {
        "words": [
          "додому!",
          "Ми",
          "прилетіли"
        ],
        "answer": "Ми прилетіли додому!",
        "explanation": "Exact EX-001 model."
      }
    ],
    "id": "w10"
  },
  "odd-one-out/quote": {
    "type": "odd-one-out",
    "items": [
      {
        "words": [
          "грати",
          "ґрати",
          "грім"
        ],
        "correct": 1,
        "explanation": "Only the second begins with Ґ.",
        "kind": "comprehension",
        "option_why": [
          "Starts with Г.",
          "Starts with Ґ.",
          "Starts with Г."
        ],
        "host": {
          "kind": "quote",
          "ref": "T-035"
        }
      }
    ],
    "id": "w11"
  },
  "fill-in/orthography": {
    "type": "fill-in",
    "instruction": "Restore the letter in the sourced word.",
    "items": [
      {
        "sentence": "т___нь",
        "options": [
          "і",
          "у"
        ],
        "answer": "і",
        "explanation": "The model is тінь.",
        "kind": "orthography",
        "mode": "orthography",
        "target_record": "W-120",
        "option_why": [
          "Completes W-120.",
          "Does not complete a VESUM word."
        ]
      }
    ],
    "id": "w12"
  },
  "quiz/quote": {
    "type": "quiz",
    "instruction": "Use the presented model.",
    "items": [
      {
        "question": "Select the source target.",
        "options": [
          "А",
          "О"
        ],
        "correct": 0,
        "explanation": "The preceding source supplies the target.",
        "kind": "comprehension",
        "option_why": [
          "Matches the source target.",
          "Different source target."
        ],
        "host": {
          "kind": "quote",
          "ref": "T-022"
        }
      }
    ],
    "id": "w13"
  },
  "quiz/dialogue": {
    "type": "quiz",
    "instruction": "Use the presented model.",
    "items": [
      {
        "question": "Select the source target.",
        "options": [
          "Привіт!",
          "Добрий день!"
        ],
        "correct": 0,
        "explanation": "The preceding source supplies the target.",
        "kind": "comprehension",
        "option_why": [
          "Matches the source target.",
          "Different source target."
        ],
        "host": {
          "kind": "dialogue"
        }
      }
    ],
    "id": "w14"
  },
  "quiz/listening": {
    "type": "quiz",
    "instruction": "Use the presented model.",
    "items": [
      {
        "question": "Select the source target.",
        "options": [
          "А",
          "О"
        ],
        "correct": 0,
        "explanation": "The preceding source supplies the target.",
        "kind": "listening",
        "option_why": [
          "Matches the source target.",
          "Different source target."
        ],
        "host": {
          "kind": "video",
          "ref": "V-004"
        },
        "target_record": "T-022"
      }
    ],
    "id": "w15"
  },
  "recap-P1/dialogue": {
    "type": "quiz",
    "instruction": "Use the presented model.",
    "items": [
      {
        "question": "Select the source target.",
        "options": [
          "сливка",
          "мама"
        ],
        "correct": 0,
        "explanation": "The preceding source supplies the target.",
        "kind": "comprehension",
        "option_why": [
          "Matches the source target.",
          "Different source target."
        ],
        "host": {
          "kind": "dialogue"
        }
      }
    ],
    "id": "w16"
  },
  "recap-P2/quote": {
    "type": "quiz",
    "instruction": "Use the presented model.",
    "items": [
      {
        "question": "Select the source target.",
        "options": [
          "весна",
          "зима"
        ],
        "correct": 0,
        "explanation": "The preceding source supplies the target.",
        "kind": "comprehension",
        "option_why": [
          "Matches the source target.",
          "Different source target."
        ],
        "host": {
          "kind": "quote",
          "ref": "T-034"
        }
      }
    ],
    "id": "w17"
  },
  "recap-P3/quote": {
    "type": "quiz",
    "instruction": "Use the presented model.",
    "items": [
      {
        "question": "Select the source target.",
        "options": [
          "дощ",
          "зима"
        ],
        "correct": 0,
        "explanation": "The preceding source supplies the target.",
        "kind": "comprehension",
        "option_why": [
          "Matches the source target.",
          "Different source target."
        ],
        "host": {
          "kind": "quote",
          "ref": "T-035"
        }
      }
    ],
    "id": "w18"
  }
}
```

## Plan-order and decodability audit

Actual step-order reconstruction exercised 17 comprehension hosts; all are eligible before their actual planned activities. All 14 explicitly displayed T-records contain only letters already introduced at their presenting step, no early apostrophe or digraph. Letter names/syllables remain sourced phonetic units, not lexical dictionary claims; integrated resolver-role proof is still required.

```json
{
  "hosts": [
    {
      "module": "sounds-letters-and-hello",
      "lesson": 1,
      "activity": "a2",
      "host": {
        "kind": "dialogue"
      },
      "eligible": true
    },
    {
      "module": "sounds-letters-and-hello",
      "lesson": 1,
      "activity": "a4",
      "host": {
        "kind": "dialogue"
      },
      "eligible": true
    },
    {
      "module": "sounds-letters-and-hello",
      "lesson": 1,
      "activity": "a5",
      "host": {
        "kind": "dialogue"
      },
      "eligible": true
    },
    {
      "module": "sounds-letters-and-hello",
      "lesson": 2,
      "activity": "a2",
      "host": {
        "kind": "quote",
        "ref": "T-022"
      },
      "eligible": true
    },
    {
      "module": "sounds-letters-and-hello",
      "lesson": 2,
      "activity": "a6",
      "host": {
        "kind": "quote",
        "ref": "T-022"
      },
      "eligible": true
    },
    {
      "module": "sounds-letters-and-hello",
      "lesson": 3,
      "activity": "a1",
      "host": {
        "kind": "quote",
        "ref": "T-026"
      },
      "eligible": true
    },
    {
      "module": "sounds-letters-and-hello",
      "lesson": 3,
      "activity": "a8",
      "host": {
        "kind": "quote",
        "ref": "T-037"
      },
      "eligible": true
    },
    {
      "module": "sounds-letters-and-hello",
      "lesson": 6,
      "activity": "a2",
      "host": {
        "kind": "dialogue"
      },
      "eligible": true
    },
    {
      "module": "reading-ukrainian",
      "lesson": 3,
      "activity": "a4",
      "host": {
        "kind": "quote",
        "ref": "T-035"
      },
      "eligible": true
    },
    {
      "module": "reading-ukrainian",
      "lesson": 3,
      "activity": "a6",
      "host": {
        "kind": "quote",
        "ref": "T-035"
      },
      "eligible": true
    },
    {
      "module": "reading-ukrainian",
      "lesson": 5,
      "activity": "a7",
      "host": {
        "kind": "quote",
        "ref": "T-036"
      },
      "eligible": true
    },
    {
      "module": "reading-ukrainian",
      "lesson": 6,
      "activity": "a2",
      "host": {
        "kind": "quote",
        "ref": "T-034"
      },
      "eligible": true
    },
    {
      "module": "special-signs",
      "lesson": 6,
      "activity": "a7",
      "host": {
        "kind": "quote",
        "ref": "T-036"
      },
      "eligible": true
    },
    {
      "module": "special-signs",
      "lesson": 7,
      "activity": "a2",
      "host": {
        "kind": "quote",
        "ref": "T-012"
      },
      "eligible": true
    },
    {
      "module": "special-signs",
      "lesson": 7,
      "activity": "a5",
      "host": {
        "kind": "quote",
        "ref": "T-012"
      },
      "eligible": true
    },
    {
      "module": "special-signs",
      "lesson": 7,
      "activity": "a6",
      "host": {
        "kind": "quote",
        "ref": "T-012"
      },
      "eligible": true
    },
    {
      "module": "special-signs",
      "lesson": 8,
      "activity": "a2",
      "host": {
        "kind": "quote",
        "ref": "T-035"
      },
      "eligible": true
    }
  ],
  "quote_decodability": [
    {
      "module": "sounds-letters-and-hello",
      "lesson": 2,
      "step": "s1-print",
      "quote": "T-022",
      "length": 3,
      "missing_letters": []
    },
    {
      "module": "sounds-letters-and-hello",
      "lesson": 3,
      "step": "s1-print",
      "quote": "T-026",
      "length": 3,
      "missing_letters": []
    },
    {
      "module": "sounds-letters-and-hello",
      "lesson": 3,
      "step": "s-print-workbook",
      "quote": "T-037",
      "length": 33,
      "missing_letters": []
    },
    {
      "module": "reading-ukrainian",
      "lesson": 3,
      "step": "s2-print",
      "quote": "T-035",
      "length": 32,
      "missing_letters": []
    },
    {
      "module": "reading-ukrainian",
      "lesson": 5,
      "step": "s3-print",
      "quote": "T-036",
      "length": 20,
      "missing_letters": []
    },
    {
      "module": "reading-ukrainian",
      "lesson": 5,
      "step": "s3-print",
      "quote": "T-037",
      "length": 19,
      "missing_letters": []
    },
    {
      "module": "reading-ukrainian",
      "lesson": 5,
      "step": "s3-print",
      "quote": "T-032",
      "length": 3,
      "missing_letters": []
    },
    {
      "module": "reading-ukrainian",
      "lesson": 5,
      "step": "s3-print",
      "quote": "T-033",
      "length": 3,
      "missing_letters": []
    },
    {
      "module": "reading-ukrainian",
      "lesson": 5,
      "step": "s3-print",
      "quote": "T-029",
      "length": 3,
      "missing_letters": []
    },
    {
      "module": "reading-ukrainian",
      "lesson": 5,
      "step": "s3-print",
      "quote": "T-031",
      "length": 3,
      "missing_letters": []
    },
    {
      "module": "reading-ukrainian",
      "lesson": 6,
      "step": "s2",
      "quote": "T-034",
      "length": 31,
      "missing_letters": []
    },
    {
      "module": "special-signs",
      "lesson": 6,
      "step": "s-print-workbook",
      "quote": "T-036",
      "length": 10,
      "missing_letters": []
    },
    {
      "module": "special-signs",
      "lesson": 7,
      "step": "s1-print",
      "quote": "T-012",
      "length": 295,
      "missing_letters": []
    },
    {
      "module": "special-signs",
      "lesson": 8,
      "step": "s2",
      "quote": "T-035",
      "length": 81,
      "missing_letters": []
    }
  ],
  "exact_recap_forms": [
    {
      "module": "sounds-letters-and-hello",
      "text": "коло",
      "admitted": [
        {
          "id": "W-154",
          "form": "коло",
          "tags": "prep",
          "stress_source": "trie",
          "stressed": "ко́ло"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "сливи",
      "admitted": [
        {
          "id": "W-083",
          "form": "сливи",
          "tags": "noun:inanim:f:v_rod",
          "stress_source": "ulif",
          "stressed": "сли́ви"
        },
        {
          "id": "W-083",
          "form": "сливи",
          "tags": "noun:inanim:p:v_kly",
          "stress_source": "ulif",
          "stressed": "сли́ви"
        },
        {
          "id": "W-083",
          "form": "сливи",
          "tags": "noun:inanim:p:v_naz",
          "stress_source": "ulif",
          "stressed": "сли́ви"
        },
        {
          "id": "W-083",
          "form": "сливи",
          "tags": "noun:inanim:p:v_zna",
          "stress_source": "ulif",
          "stressed": "сли́ви"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "мама",
      "admitted": [
        {
          "id": "W-081",
          "form": "мама",
          "tags": "noun:anim:f:v_naz",
          "stress_source": "trie",
          "stressed": "ма́ма"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "Павлик",
      "admitted": [
        {
          "id": "W-098",
          "form": "Павлик",
          "tags": "noun:anim:m:v_naz:prop:fname",
          "stress_source": "trie",
          "stressed": "Па́влик"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "і",
      "admitted": [
        {
          "id": "W-050",
          "form": "і",
          "tags": "conj:coord",
          "stress_source": "none",
          "stressed": "і"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "Поліна",
      "admitted": [
        {
          "id": "W-099",
          "form": "Поліна",
          "tags": "noun:anim:f:v_naz:prop:fname",
          "stress_source": "trie",
          "stressed": "Полі́на"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "мамо",
      "admitted": [
        {
          "id": "W-081",
          "form": "мамо",
          "tags": "noun:anim:f:v_kly",
          "stress_source": "trie",
          "stressed": "ма́мо"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "он",
      "admitted": [
        {
          "id": "W-155",
          "form": "он",
          "tags": "part",
          "stress_source": "none",
          "stressed": "он"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "сливка",
      "admitted": [
        {
          "id": "W-156",
          "form": "сливка",
          "tags": "noun:inanim:f:v_naz",
          "stress_source": "trie",
          "stressed": "сли́вка"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "вона",
      "admitted": [
        {
          "id": "W-004",
          "form": "вона",
          "tags": "noun:unanim:f:v_naz:pron:pers:3",
          "stress_source": "trie",
          "stressed": "вона́"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "кисла",
      "admitted": [
        {
          "id": "W-157",
          "form": "кисла",
          "tags": "adj:f:v_kly:compb",
          "stress_source": "trie",
          "stressed": "ки́сла"
        },
        {
          "id": "W-157",
          "form": "кисла",
          "tags": "adj:f:v_naz:compb",
          "stress_source": "trie",
          "stressed": "ки́сла"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "ні",
      "admitted": [
        {
          "id": "W-062",
          "form": "ні",
          "tags": "part",
          "stress_source": "none",
          "stressed": "ні"
        }
      ]
    },
    {
      "module": "sounds-letters-and-hello",
      "text": "сину",
      "admitted": [
        {
          "id": "W-158",
          "form": "сину",
          "tags": "noun:anim:m:v_dav",
          "stress_source": "ulif",
          "stressed": "си́ну"
        },
        {
          "id": "W-158",
          "form": "сину",
          "tags": "noun:anim:m:v_kly",
          "stress_source": "ulif",
          "stressed": "си́ну"
        },
        {
          "id": "W-158",
          "form": "сину",
          "tags": "noun:anim:m:v_mis",
          "stress_source": "ulif",
          "stressed": "си́ну"
        }
      ]
    },
    {
      "module": "reading-ukrainian",
      "text": "настала",
      "admitted": [
        {
          "id": "W-159",
          "form": "настала",
          "tags": "verb:perf:past:f",
          "stress_source": "ulif",
          "stressed": "наста́ла"
        }
      ]
    },
    {
      "module": "reading-ukrainian",
      "text": "весна",
      "admitted": [
        {
          "id": "W-160",
          "form": "весна",
          "tags": "noun:inanim:f:v_naz",
          "stress_source": "ulif",
          "stressed": "весна́"
        }
      ]
    },
    {
      "module": "reading-ukrainian",
      "text": "прилетіли",
      "admitted": [
        {
          "id": "W-113",
          "form": "прилетіли",
          "tags": "verb:perf:past:p",
          "stress_source": "ulif",
          "stressed": "прилеті́ли"
        }
      ]
    },
    {
      "module": "reading-ukrainian",
      "text": "птахи",
      "admitted": [
        {
          "id": "W-161",
          "form": "птахи",
          "tags": "noun:anim:p:v_kly",
          "stress_source": "ulif",
          "stressed": "птахи́"
        },
        {
          "id": "W-161",
          "form": "птахи",
          "tags": "noun:anim:p:v_naz",
          "stress_source": "ulif",
          "stressed": "птахи́"
        },
        {
          "id": "W-161",
          "form": "птахи",
          "tags": "noun:anim:p:v_zna",
          "stress_source": "ulif",
          "stressed": "птахи́"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "весною",
      "admitted": [
        {
          "id": "W-160",
          "form": "весною",
          "tags": "noun:inanim:f:v_oru",
          "stress_source": "ulif",
          "stressed": "весно́ю"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "равлики",
      "admitted": [
        {
          "id": "W-166",
          "form": "равлики",
          "tags": "noun:anim:p:v_kly",
          "stress_source": "ulif",
          "stressed": "ра́влики"
        },
        {
          "id": "W-166",
          "form": "равлики",
          "tags": "noun:anim:p:v_naz",
          "stress_source": "ulif",
          "stressed": "ра́влики"
        },
        {
          "id": "W-166",
          "form": "равлики",
          "tags": "noun:anim:p:v_zna",
          "stress_source": "ulif",
          "stressed": "ра́влики"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "люблять",
      "admitted": [
        {
          "id": "W-165",
          "form": "люблять",
          "tags": "verb:imperf:pres:p:3",
          "stress_source": "ulif",
          "stressed": "лю́блять"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "дощ",
      "admitted": [
        {
          "id": "W-130",
          "form": "дощ",
          "tags": "noun:inanim:m:v_naz",
          "stress_source": "none",
          "stressed": "дощ"
        },
        {
          "id": "W-130",
          "form": "дощ",
          "tags": "noun:inanim:m:v_zna",
          "stress_source": "none",
          "stressed": "дощ"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "один",
      "admitted": [
        {
          "id": "W-167",
          "form": "один",
          "tags": "numr:m:v_naz",
          "stress_source": "ulif",
          "stressed": "оди́н"
        },
        {
          "id": "W-167",
          "form": "один",
          "tags": "numr:m:v_zna:rinanim",
          "stress_source": "ulif",
          "stressed": "оди́н"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "старенький",
      "admitted": [
        {
          "id": "W-168",
          "form": "старенький",
          "tags": "adj:m:v_kly",
          "stress_source": "trie",
          "stressed": "старе́нький"
        },
        {
          "id": "W-168",
          "form": "старенький",
          "tags": "adj:m:v_naz",
          "stress_source": "trie",
          "stressed": "старе́нький"
        },
        {
          "id": "W-168",
          "form": "старенький",
          "tags": "adj:m:v_zna:rinanim",
          "stress_source": "trie",
          "stressed": "старе́нький"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "равлик",
      "admitted": [
        {
          "id": "W-166",
          "form": "равлик",
          "tags": "noun:anim:m:v_naz",
          "stress_source": "ulif",
          "stressed": "ра́влик"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "любив",
      "admitted": [
        {
          "id": "W-165",
          "form": "любив",
          "tags": "verb:imperf:past:m",
          "stress_source": "ulif",
          "stressed": "люби́в"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "мандрувати",
      "admitted": [
        {
          "id": "W-169",
          "form": "мандрувати",
          "tags": "verb:imperf:inf",
          "stress_source": "ulif",
          "stressed": "мандрува́ти"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "під",
      "admitted": [
        {
          "id": "W-032",
          "form": "під",
          "tags": "prep",
          "stress_source": "none",
          "stressed": "під"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "час",
      "admitted": [
        {
          "id": "W-170",
          "form": "час",
          "tags": "noun:inanim:m:v_naz:predic",
          "stress_source": "none",
          "stressed": "час"
        },
        {
          "id": "W-170",
          "form": "час",
          "tags": "noun:inanim:m:v_zna",
          "stress_source": "none",
          "stressed": "час"
        }
      ]
    },
    {
      "module": "special-signs",
      "text": "дощу",
      "admitted": [
        {
          "id": "W-130",
          "form": "дощу",
          "tags": "noun:inanim:m:v_dav",
          "stress_source": "ulif",
          "stressed": "дощу́"
        },
        {
          "id": "W-130",
          "form": "дощу",
          "tags": "noun:inanim:m:v_kly",
          "stress_source": "ulif",
          "stressed": "дощу́"
        },
        {
          "id": "W-130",
          "form": "дощу",
          "tags": "noun:inanim:m:v_mis",
          "stress_source": "ulif",
          "stressed": "дощу́"
        },
        {
          "id": "W-130",
          "form": "дощу",
          "tags": "noun:inanim:m:v_rod",
          "stress_source": "ulif",
          "stressed": "дощу́"
        }
      ]
    }
  ]
}
```

Every activity read/copy boundary follows. Candidate models list verified lemma forms already decodable at that exact position, not every licensed source inflection. Exact recap inflections are bound above. Other whole sentences remain the exact EX-001/EX-002 and source copy models; no shortened rows. All explicit W-targets must use the exact displayed source form, with non-pending stress. Core oral metalanguage and initial D3 greeting chunks are not printed decoding targets before their letters are introduced. Initial name labels are paired with English role labels, never read/copy tests. Actual writer outputs, question stems/options/feedback, extra name forms and resolver roles require a renewed audit; no unbuilt item is claimed decoded.

| Module / lesson / activity | Family / position | Letters available | Verified decodable model candidates / source restriction |
| --- | --- | --- | --- |
| sounds-letters-and-hello L1 a1 | watch-and-repeat / s1 | D3 oral only | T/EX glyph or syllable model; D3 oral exception where applicable; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L1 a2 | quiz / s1 | D3 oral only | T/EX glyph or syllable model; D3 oral exception where applicable; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L1 a3 | watch-and-repeat / s2 | D3 oral only | T/EX glyph or syllable model; D3 oral exception where applicable; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L1 a4 | quiz / s2 | D3 oral only | T/EX glyph or syllable model; D3 oral exception where applicable; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L1 a5 | quiz / consolidation | D3 oral only | T/EX glyph or syllable model; D3 oral exception where applicable; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L2 a1 | observe / s1 | D3 oral only | T/EX glyph or syllable model; D3 oral exception where applicable; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L2 a2 | quiz / s1-print | аиоу | T/EX glyph or syllable model; D3 oral exception where applicable; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L2 a3 | watch-and-repeat / s2 | аиоу | T/EX glyph or syllable model; D3 oral exception where applicable; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L2 a4 | letter-grid / s2 | аиоу | T/EX glyph or syllable model; D3 oral exception where applicable; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L2 a5 | quiz / consolidation | аиоу | T/EX glyph or syllable model; D3 oral exception where applicable; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L2 a6 | odd-one-out / consolidation | аиоу | T/EX glyph or syllable model; D3 oral exception where applicable; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L3 a1 | quiz / s1-print | аимоу | W-081:мама; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L3 a2 | letter-grid / s1 | аимоу | W-081:мама; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L3 a3 | watch-and-repeat / s2 | аимоуі | W-081:мама; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L3 a4 | quiz / s2 | аимоуі | W-081:мама; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L3 a5 | letter-grid / s3 | аимноуі | W-081:мама, W-091:Ніна, W-092:Нонна; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L3 a6 | quiz / s3 | аимноуі | W-081:мама, W-091:Ніна, W-092:Нонна; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L3 a7 | pick-syllables / consolidation | аимноуі | W-081:мама, W-091:Ніна, W-092:Нонна; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L3 a8 | odd-one-out / consolidation | аимноуі | W-081:мама, W-091:Ніна, W-092:Нонна; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L4 a1 | watch-and-repeat / s1 | авимноуі | W-081:мама, W-093:Іван, W-094:Вова; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L4 a2 | quiz / s1 | авимноуі | W-081:мама, W-093:Іван, W-094:Вова; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L4 a3 | letter-grid / s2 | авилмносуі | W-081:мама, W-082:малина, W-083:слива, W-093:Іван, W-094:Вова; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L4 a4 | pick-syllables / s2 | авилмносуі | W-081:мама, W-082:малина, W-083:слива, W-093:Іван, W-094:Вова; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L4 a5 | quiz / consolidation | авилмносуі | W-081:мама, W-082:малина, W-083:слива, W-093:Іван, W-094:Вова; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L4 a6 | divide-words / consolidation | авилмносуі | W-081:мама, W-082:малина, W-083:слива, W-093:Іван, W-094:Вова; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L5 a1 | letter-grid / s1 | авиклмнопсуі | W-081:мама, W-082:малина, W-083:слива, W-098:Павлик, W-099:Поліна, W-100:Панас; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L5 a2 | pick-syllables / s1 | авиклмнопсуі | W-081:мама, W-082:малина, W-083:слива, W-098:Павлик, W-099:Поліна, W-100:Панас; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L5 a3 | watch-and-repeat / s2 | авиклмнопрсуі | W-081:мама, W-082:малина, W-083:слива, W-084:рука, W-085:ріка, W-098:Павлик, W-099:Поліна, W-100:Панас; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L5 a4 | quiz / s2 | авиклмнопрсуі | W-081:мама, W-082:малина, W-083:слива, W-084:рука, W-085:ріка, W-098:Павлик, W-099:Поліна, W-100:Панас; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L5 a5 | letter-grid / s2 | авиклмнопрсуі | W-081:мама, W-082:малина, W-083:слива, W-084:рука, W-085:ріка, W-098:Павлик, W-099:Поліна, W-100:Панас; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L5 a6 | pick-syllables / consolidation | авиклмнопрсуі | W-081:мама, W-082:малина, W-083:слива, W-084:рука, W-085:ріка, W-098:Павлик, W-099:Поліна, W-100:Панас; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L5 a7 | match-up / consolidation | авиклмнопрсуі | W-081:мама, W-082:малина, W-083:слива, W-084:рука, W-085:ріка, W-098:Павлик, W-099:Поліна, W-100:Панас; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L6 a1 | observe / s1 | авиклмнопрсуі | W-004:вона, W-050:і, W-062:ні, W-081:мама, W-082:малина, W-083:слива, W-084:рука, W-093:Іван, W-098:Павлик, W-099:Поліна, W-154:коло, W-155:он, W-156:сливка, W-158:син; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L6 a2 | quiz / s1 | авиклмнопрсуі | W-004:вона, W-050:і, W-062:ні, W-081:мама, W-082:малина, W-083:слива, W-084:рука, W-093:Іван, W-098:Павлик, W-099:Поліна, W-154:коло, W-155:он, W-156:сливка, W-158:син; select only exact source models, not arbitrary candidate combinations. |
| sounds-letters-and-hello L6 a3 | letter-grid / s1 | авиклмнопрсуі | W-004:вона, W-050:і, W-062:ні, W-081:мама, W-082:малина, W-083:слива, W-084:рука, W-093:Іван, W-098:Павлик, W-099:Поліна, W-154:коло, W-155:он, W-156:сливка, W-158:син; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L1 a1 | letter-grid / s1 | авиклмнопрстуі | W-074:привіт, W-101:тато; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L1 a2 | quiz / s1 | авиклмнопрстуі | W-074:привіт, W-081:мама, W-082:малина, W-101:тато; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L1 a3 | letter-grid / s2 | авеиклмнопрстуі | W-117:клен; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L1 a4 | quiz / s2 | авеиклмнопрстуі | W-074:привіт, W-081:мама, W-082:малина, W-101:тато, W-102:Евеліна, W-117:клен; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L1 a5 | watch-and-repeat / s3 | авеиклмнопрстуі | W-074:привіт, W-101:тато, W-102:Евеліна, W-117:клен; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L1 a6 | pick-syllables / consolidation | авеиклмнопрстуі | W-081:мама, W-082:малина, W-101:тато; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L1 a7 | match-up / consolidation | авеиклмнопрстуі | W-074:привіт, W-081:мама, W-082:малина, W-101:тато; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L1 a8 | fill-in / consolidation | авеиклмнопрстуі | W-074:привіт, W-081:мама, W-082:малина, W-101:тато, W-117:клен; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L2 a1 | letter-grid / s1 | авдеиклмнопрстуі | W-116:дрова; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L2 a2 | quiz / s1 | авдеиклмнопрстуі | W-035:над, W-074:привіт, W-081:мама, W-101:тато, W-116:дрова, W-147:лід; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L2 a3 | letter-grid / s2 | авдезиклмнопрстуі | W-104:зима; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L2 a4 | quiz / s2 | авдезиклмнопрстуі | W-035:над, W-074:привіт, W-081:мама, W-101:тато, W-104:зима, W-116:дрова, W-147:лід; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L2 a5 | letter-grid / s3 | абвдезиклмнопрстуі | W-105:білка, W-118:зуб; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L2 a6 | quiz / s3 | абвдезиклмнопрстуі | W-035:над, W-074:привіт, W-081:мама, W-101:тато, W-104:зима, W-105:білка, W-116:дрова, W-118:зуб, W-145:бак, W-146:біб, W-147:лід, W-148:бук; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L2 a7 | observe / s4 | абвдезиклмнопрстуі | W-104:зима, W-105:білка, W-116:дрова, W-118:зуб; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L2 a8 | divide-words / consolidation | абвдезиклмнопрстуі | W-081:мама, W-101:тато, W-104:зима; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L2 a9 | quiz / consolidation | абвдезиклмнопрстуі | W-035:над, W-074:привіт, W-081:мама, W-101:тато, W-104:зима, W-105:білка, W-116:дрова, W-118:зуб, W-145:бак, W-146:біб, W-147:лід, W-148:бук; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L3 a1 | letter-grid / s1 | абвгдезиклмнопрстуі | W-106:гарбуз; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L3 a2 | quiz / s1 | абвгдезиклмнопрстуі | W-074:привіт, W-081:мама, W-101:тато, W-104:зима, W-106:гарбуз, W-149:грати, W-151:кава, W-152:грім; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L3 a3 | letter-grid / s2 | абвгдезиклмнопрстуіґ | W-107:ґава; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L3 a4 | quiz / s2-print | абвгдезиклмнопрстуіґ | W-074:привіт, W-081:мама, W-101:тато, W-104:зима, W-106:гарбуз, W-107:ґава, W-149:грати, W-150:ґрати, W-151:кава, W-152:грім, W-153:ґрунт; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L3 a5 | watch-and-repeat / s3 | абвгдезиклмнопрстуіґ | W-106:гарбуз, W-107:ґава; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L3 a6 | odd-one-out / consolidation | абвгдезиклмнопрстуіґ | W-074:привіт, W-081:мама, W-101:тато, W-104:зима, W-106:гарбуз, W-107:ґава, W-149:грати, W-150:ґрати, W-151:кава, W-152:грім, W-153:ґрунт; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L3 a7 | fill-in / consolidation | абвгдезиклмнопрстуіґ | W-081:мама, W-101:тато, W-104:зима, W-106:гарбуз, W-107:ґава; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L4 a1 | letter-grid / s1 | абвгдезиклмнопрстучіґ | W-108:чобіт; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L4 a2 | quiz / s1 | абвгдезиклмнопрстучіґ | W-074:привіт, W-101:тато, W-104:зима, W-108:чобіт, W-118:зуб; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L4 a3 | letter-grid / s2 | абвгдезийклмнопрстучіґ | W-109:чай; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L4 a4 | quiz / s2 | абвгдезийклмнопрстучіґ | W-074:привіт, W-079:голосний, W-080:приголосний, W-101:тато, W-104:зима, W-108:чобіт, W-109:чай, W-118:зуб; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L4 a5 | letter-grid / s3 | абвгдезийклмнопрстухчіґ | W-110:хліб; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L4 a6 | quiz / s3 | абвгдезийклмнопрстухчіґ | W-074:привіт, W-079:голосний, W-080:приголосний, W-101:тато, W-103:дах, W-104:зима, W-108:чобіт, W-109:чай, W-110:хліб, W-118:зуб; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L4 a7 | watch-and-repeat / s4 | абвгдезийклмнопрстухчіґ | W-103:дах, W-108:чобіт, W-109:чай, W-110:хліб; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L4 a8 | match-up / consolidation | абвгдезийклмнопрстухчіґ | W-104:зима, W-109:чай, W-110:хліб, W-118:зуб; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L4 a9 | anagram / consolidation | абвгдезийклмнопрстухчіґ | W-101:тато, W-104:зима, W-109:чай; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L4 a10 | fill-in / consolidation | абвгдезийклмнопрстухчіґ | W-101:тато, W-103:дах, W-108:чобіт, W-109:чай, W-110:хліб; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L5 a1 | letter-grid / s1 | абвгдежзийклмнопрстухчіґ | W-111:жито; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L5 a2 | quiz / s1 | абвгдежзийклмнопрстухчіґ | W-006:ми, W-007:ви, W-061:не, W-074:привіт, W-079:голосний, W-080:приголосний, W-087:бачити, W-104:зима, W-111:жито, W-113:прилетіти, W-114:додому, W-115:жабка; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L5 a3 | letter-grid / s2 | абвгдежзийклмнопрстухчшіґ | W-112:комиш; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L5 a4 | quiz / s2 | абвгдежзийклмнопрстухчшіґ | W-006:ми, W-007:ви, W-061:не, W-074:привіт, W-079:голосний, W-080:приголосний, W-087:бачити, W-104:зима, W-111:жито, W-112:комиш, W-113:прилетіти, W-114:додому, W-115:жабка; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L5 a5 | observe / s3 | абвгдежзийклмнопрстухчшіґ | W-006:ми, W-007:ви, W-061:не, W-074:привіт, W-079:голосний, W-080:приголосний, W-087:бачити, W-104:зима, W-111:жито, W-112:комиш, W-113:прилетіти, W-114:додому, W-115:жабка; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L5 a6 | observe / s3 | абвгдежзийклмнопрстухчшіґ | W-006:ми, W-007:ви, W-061:не, W-074:привіт, W-079:голосний, W-080:приголосний, W-087:бачити, W-104:зима, W-111:жито, W-112:комиш, W-113:прилетіти, W-114:додому, W-115:жабка; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L5 a7 | quiz / s3-print | абвгдежзийклмнопрстухчшіґ | W-006:ми, W-007:ви, W-061:не, W-074:привіт, W-079:голосний, W-080:приголосний, W-087:бачити, W-104:зима, W-111:жито, W-112:комиш, W-113:прилетіти, W-114:додому, W-115:жабка; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L5 a8 | unjumble / consolidation | абвгдежзийклмнопрстухчшіґ | W-006:ми, W-007:ви, W-061:не, W-074:привіт, W-079:голосний, W-080:приголосний, W-087:бачити, W-104:зима, W-111:жито, W-112:комиш, W-113:прилетіти, W-114:додому, W-115:жабка; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L5 a9 | quiz / consolidation | абвгдежзийклмнопрстухчшіґ | W-006:ми, W-007:ви, W-061:не, W-074:привіт, W-079:голосний, W-080:приголосний, W-087:бачити, W-104:зима, W-111:жито, W-112:комиш, W-113:прилетіти, W-114:додому, W-115:жабка; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L5 a10 | pick-syllables / consolidation | абвгдежзийклмнопрстухчшіґ | W-104:зима, W-111:жито, W-112:комиш; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L6 a1 | observe / s1 | абвгдежзийклмнопрстухчшіґ | W-006:ми, W-007:ви, W-026:до, W-061:не, W-074:привіт, W-075:добрий, W-081:мама, W-087:бачити, W-093:Іван, W-101:тато, W-104:зима, W-109:чай, W-110:хліб, W-113:прилетіти, W-114:додому, W-115:жабка, W-118:зуб, W-159:настати, W-160:весна, W-161:птах, W-162:хто, W-163:де; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L6 a2 | quiz / s2 | абвгдежзийклмнопрстухчшіґ | W-006:ми, W-007:ви, W-026:до, W-061:не, W-074:привіт, W-075:добрий, W-081:мама, W-087:бачити, W-093:Іван, W-101:тато, W-104:зима, W-109:чай, W-110:хліб, W-113:прилетіти, W-114:додому, W-115:жабка, W-118:зуб, W-159:настати, W-160:весна, W-161:птах, W-162:хто, W-163:де; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L6 a3 | observe / s2 | абвгдежзийклмнопрстухчшіґ | W-006:ми, W-007:ви, W-026:до, W-061:не, W-074:привіт, W-075:добрий, W-081:мама, W-087:бачити, W-093:Іван, W-101:тато, W-104:зима, W-109:чай, W-110:хліб, W-113:прилетіти, W-114:додому, W-115:жабка, W-118:зуб, W-159:настати, W-160:весна, W-161:птах, W-162:хто, W-163:де; select only exact source models, not arbitrary candidate combinations. |
| reading-ukrainian L6 a4 | letter-grid / s2 | абвгдежзийклмнопрстухчшіґ | W-093:Іван, W-101:тато, W-104:зима, W-109:чай, W-110:хліб, W-118:зуб; select only exact source models, not arbitrary candidate combinations. |
| special-signs L1 a1 | watch-and-repeat / s1 | абвгдежзийклмнопрстухчшьіґ | W-119:тин, W-120:тінь; select only exact source models, not arbitrary candidate combinations. |
| special-signs L1 a2 | letter-grid / s1 | абвгдежзийклмнопрстухчшьіґ | W-075:добрий, W-076:день, W-119:тин, W-120:тінь; select only exact source models, not arbitrary candidate combinations. |
| special-signs L1 a3 | fill-in / s1 | абвгдежзийклмнопрстухчшьіґ | W-119:тин, W-120:тінь; select only exact source models, not arbitrary candidate combinations. |
| special-signs L1 a4 | observe / s2 | абвгдежзийклмнопрстухчшьіґ | W-074:привіт, W-075:добрий, W-076:день, W-081:мама, W-101:тато; select only exact source models, not arbitrary candidate combinations. |
| special-signs L1 a5 | fill-in / consolidation | абвгдежзийклмнопрстухчшьіґ | W-076:день, W-081:мама, W-101:тато, W-119:тин, W-120:тінь; select only exact source models, not arbitrary candidate combinations. |
| special-signs L1 a6 | match-up / consolidation | абвгдежзийклмнопрстухчшьіґ | W-074:привіт, W-076:день, W-081:мама, W-101:тато; select only exact source models, not arbitrary candidate combinations. |
| special-signs L2 a1 | letter-grid / s1 | абвгдежзийклмнопрстухчшьіїґ | W-010:мій, W-121:їжа; select only exact source models, not arbitrary candidate combinations. |
| special-signs L2 a2 | quiz / s1 | абвгдежзийклмнопрстухчшьіїґ | W-010:мій, W-074:привіт, W-075:добрий, W-076:день, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа; select only exact source models, not arbitrary candidate combinations. |
| special-signs L2 a3 | letter-grid / s2 | абвгдежзийклмнопрстухчшьяіїґ | W-122:яма, W-123:маля, W-141:Марія, W-142:мільярд; select only exact source models, not arbitrary candidate combinations. |
| special-signs L2 a4 | fill-in / s2 | абвгдежзийклмнопрстухчшьяіїґ | W-122:яма, W-123:маля, W-141:Марія, W-142:мільярд; select only exact source models, not arbitrary candidate combinations. |
| special-signs L2 a5 | pick-syllables / consolidation | абвгдежзийклмнопрстухчшьяіїґ | W-121:їжа; select only exact source models, not arbitrary candidate combinations. |
| special-signs L2 a6 | fill-in / consolidation | абвгдежзийклмнопрстухчшьяіїґ | W-121:їжа, W-122:яма, W-123:маля, W-141:Марія; select only exact source models, not arbitrary candidate combinations. |
| special-signs L2 a7 | anagram / consolidation | абвгдежзийклмнопрстухчшьяіїґ | W-081:мама, W-101:тато, W-121:їжа; select only exact source models, not arbitrary candidate combinations. |
| special-signs L3 a1 | letter-grid / s1 | абвгдежзийклмнопрстухчшьюяіїґ | W-124:юрта, W-125:люпин, W-140:радіти; select only exact source models, not arbitrary candidate combinations. |
| special-signs L3 a2 | fill-in / s1 | абвгдежзийклмнопрстухчшьюяіїґ | W-124:юрта, W-125:люпин, W-140:радіти; select only exact source models, not arbitrary candidate combinations. |
| special-signs L3 a3 | letter-grid / s2 | абвгдежзийклмнопрстухчшьюяєіїґ | W-010:мій, W-126:синій, W-127:єнот; select only exact source models, not arbitrary candidate combinations. |
| special-signs L3 a4 | fill-in / s2 | абвгдежзийклмнопрстухчшьюяєіїґ | W-010:мій, W-126:синій, W-127:єнот; select only exact source models, not arbitrary candidate combinations. |
| special-signs L3 a5 | fill-in / consolidation | абвгдежзийклмнопрстухчшьюяєіїґ | W-010:мій, W-124:юрта, W-125:люпин, W-126:синій, W-127:єнот; select only exact source models, not arbitrary candidate combinations. |
| special-signs L3 a6 | fill-in / consolidation | абвгдежзийклмнопрстухчшьюяєіїґ | W-124:юрта, W-125:люпин, W-127:єнот; select only exact source models, not arbitrary candidate combinations. |
| special-signs L3 a7 | count-syllables / consolidation | абвгдежзийклмнопрстухчшьюяєіїґ | W-121:їжа, W-124:юрта, W-125:люпин; select only exact source models, not arbitrary candidate combinations. |
| special-signs L4 a1 | letter-grid / s1 | абвгдежзийклмнопрстухцчшьюяєіїґ | W-128:цимбали; select only exact source models, not arbitrary candidate combinations. |
| special-signs L4 a2 | quiz / s1 | абвгдежзийклмнопрстухцчшьюяєіїґ | W-074:привіт, W-075:добрий, W-076:день, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-128:цимбали; select only exact source models, not arbitrary candidate combinations. |
| special-signs L4 a3 | letter-grid / s2 | абвгдежзийклмнопрстухцчшщьюяєіїґ | W-129:щука, W-130:дощ; select only exact source models, not arbitrary candidate combinations. |
| special-signs L4 a4 | quiz / s2 | абвгдежзийклмнопрстухцчшщьюяєіїґ | W-074:привіт, W-075:добрий, W-076:день, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-128:цимбали, W-129:щука, W-130:дощ; select only exact source models, not arbitrary candidate combinations. |
| special-signs L4 a5 | letter-grid / s3 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-131:ферма; select only exact source models, not arbitrary candidate combinations. |
| special-signs L4 a6 | quiz / s3 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-074:привіт, W-075:добрий, W-076:день, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-128:цимбали, W-129:щука, W-130:дощ, W-131:ферма; select only exact source models, not arbitrary candidate combinations. |
| special-signs L4 a7 | divide-words / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-128:цимбали, W-129:щука, W-131:ферма; select only exact source models, not arbitrary candidate combinations. |
| special-signs L4 a8 | match-up / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-101:тато, W-121:їжа, W-130:дощ; select only exact source models, not arbitrary candidate combinations. |
| special-signs L4 a9 | fill-in / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-128:цимбали, W-129:щука, W-130:дощ, W-131:ферма; select only exact source models, not arbitrary candidate combinations. |
| special-signs L5 a1 | observe / s1 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-132:джміль, W-133:джем; select only exact source models, not arbitrary candidate combinations. |
| special-signs L5 a2 | fill-in / s1 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-130:дощ, W-132:джміль, W-133:джем; select only exact source models, not arbitrary candidate combinations. |
| special-signs L5 a3 | observe / s2 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-134:дзиґа, W-135:дзюрчати; select only exact source models, not arbitrary candidate combinations. |
| special-signs L5 a4 | fill-in / s2 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-134:дзиґа, W-135:дзюрчати; select only exact source models, not arbitrary candidate combinations. |
| special-signs L5 a5 | anagram / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-132:джміль, W-133:джем, W-134:дзиґа; select only exact source models, not arbitrary candidate combinations. |
| special-signs L5 a6 | fill-in / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-132:джміль, W-133:джем, W-134:дзиґа, W-135:дзюрчати; select only exact source models, not arbitrary candidate combinations. |
| special-signs L5 a7 | pick-syllables / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-134:дзиґа; select only exact source models, not arbitrary candidate combinations. |
| special-signs L6 a1 | letter-grid / s1 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-136:пір'я, W-137:пити, W-139:м'яч, W-143:пюре, W-144:пір'їна; select only exact source models, not arbitrary candidate combinations. |
| special-signs L6 a2 | fill-in / s1 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-137:пити, W-143:пюре; select only exact source models, not arbitrary candidate combinations. |
| special-signs L6 a3 | observe / s2 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-004:вона, W-010:мій, W-011:твій, W-065:ось, W-074:привіт, W-075:добрий, W-076:день, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-125:люпин, W-130:дощ, W-136:пір'я, W-137:пити, W-138:сім'я, W-139:м'яч, W-142:мільярд, W-143:пюре, W-144:пір'їна; select only exact source models, not arbitrary candidate combinations. |
| special-signs L6 a4 | letter-grid / s2 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-004:вона, W-010:мій, W-011:твій, W-065:ось, W-074:привіт, W-075:добрий, W-076:день, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-125:люпин, W-130:дощ, W-136:пір'я, W-137:пити, W-138:сім'я, W-139:м'яч, W-142:мільярд, W-143:пюре, W-144:пір'їна; select only exact source models, not arbitrary candidate combinations. |
| special-signs L6 a5 | unjumble / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-004:вона, W-010:мій, W-011:твій, W-065:ось, W-074:привіт, W-075:добрий, W-076:день, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-125:люпин, W-130:дощ, W-136:пір'я, W-137:пити, W-138:сім'я, W-139:м'яч, W-142:мільярд, W-143:пюре, W-144:пір'їна; select only exact source models, not arbitrary candidate combinations. |
| special-signs L6 a6 | fill-in / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-136:пір'я, W-139:м'яч, W-144:пір'їна; select only exact source models, not arbitrary candidate combinations. |
| special-signs L6 a7 | odd-one-out / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-004:вона, W-010:мій, W-011:твій, W-065:ось, W-074:привіт, W-075:добрий, W-076:день, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-125:люпин, W-130:дощ, W-136:пір'я, W-137:пити, W-138:сім'я, W-139:м'яч, W-142:мільярд, W-143:пюре, W-144:пір'їна; select only exact source models, not arbitrary candidate combinations. |
| special-signs L7 a1 | letter-grid / s1 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-074:привіт, W-075:добрий, W-076:день, W-078:літера, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-130:дощ, W-141:Марія, W-171:буква, W-172:назва, W-173:алфавіт, W-174:знак, W-175:м'якшення; select only exact source models, not arbitrary candidate combinations. |
| special-signs L7 a2 | quiz / s1-print | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-074:привіт, W-075:добрий, W-076:день, W-078:літера, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-130:дощ, W-141:Марія, W-171:буква, W-172:назва, W-173:алфавіт, W-174:знак, W-175:м'якшення; select only exact source models, not arbitrary candidate combinations. |
| special-signs L7 a3 | letter-grid / s2 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-141:Марія; select only exact source models, not arbitrary candidate combinations. |
| special-signs L7 a4 | order / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-074:привіт, W-075:добрий, W-076:день, W-078:літера, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-130:дощ, W-141:Марія, W-171:буква, W-172:назва, W-173:алфавіт, W-174:знак, W-175:м'якшення; select only exact source models, not arbitrary candidate combinations. |
| special-signs L7 a5 | odd-one-out / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-074:привіт, W-075:добрий, W-076:день, W-078:літера, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-130:дощ, W-141:Марія, W-171:буква, W-172:назва, W-173:алфавіт, W-174:знак, W-175:м'якшення; select only exact source models, not arbitrary candidate combinations. |
| special-signs L7 a6 | quiz / consolidation | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-074:привіт, W-075:добрий, W-076:день, W-078:літера, W-079:голосний, W-080:приголосний, W-081:мама, W-101:тато, W-121:їжа, W-130:дощ, W-141:Марія, W-171:буква, W-172:назва, W-173:алфавіт, W-174:знак, W-175:м'якшення; select only exact source models, not arbitrary candidate combinations. |
| special-signs L8 a1 | observe / s1 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-001:я, W-004:вона, W-011:твій, W-032:під, W-065:ось, W-074:привіт, W-075:добрий, W-076:день, W-078:літера, W-079:голосний, W-080:приголосний, W-081:мама, W-087:бачити, W-088:читати, W-089:писати, W-090:повторення, W-101:тато, W-119:тин, W-120:тінь, W-121:їжа, W-122:яма, W-123:маля, W-124:юрта, W-125:люпин, W-126:синій, W-127:єнот, W-128:цимбали, W-129:щука, W-130:дощ, W-131:ферма, W-132:джміль, W-133:джем, W-134:дзиґа, W-135:дзюрчати, W-136:пір'я, W-137:пити, W-138:сім'я, W-139:м'яч, W-140:радіти, W-141:Марія, W-142:мільярд, W-143:пюре, W-144:пір'їна, W-160:весна, W-162:хто, W-163:де, W-164:що, W-165:любити, W-166:равлик, W-167:один, W-168:старенький, W-169:мандрувати, W-170:час, W-171:буква, W-172:назва, W-173:алфавіт, W-174:знак, W-175:м'якшення; select only exact source models, not arbitrary candidate combinations. |
| special-signs L8 a2 | quiz / s2 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-001:я, W-004:вона, W-011:твій, W-032:під, W-065:ось, W-074:привіт, W-075:добрий, W-076:день, W-078:літера, W-079:голосний, W-080:приголосний, W-081:мама, W-087:бачити, W-088:читати, W-089:писати, W-090:повторення, W-101:тато, W-119:тин, W-120:тінь, W-121:їжа, W-122:яма, W-123:маля, W-124:юрта, W-125:люпин, W-126:синій, W-127:єнот, W-128:цимбали, W-129:щука, W-130:дощ, W-131:ферма, W-132:джміль, W-133:джем, W-134:дзиґа, W-135:дзюрчати, W-136:пір'я, W-137:пити, W-138:сім'я, W-139:м'яч, W-140:радіти, W-141:Марія, W-142:мільярд, W-143:пюре, W-144:пір'їна, W-160:весна, W-162:хто, W-163:де, W-164:що, W-165:любити, W-166:равлик, W-167:один, W-168:старенький, W-169:мандрувати, W-170:час, W-171:буква, W-172:назва, W-173:алфавіт, W-174:знак, W-175:м'якшення; select only exact source models, not arbitrary candidate combinations. |
| special-signs L8 a3 | observe / s2 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-001:я, W-004:вона, W-011:твій, W-032:під, W-065:ось, W-074:привіт, W-075:добрий, W-076:день, W-078:літера, W-079:голосний, W-080:приголосний, W-081:мама, W-087:бачити, W-088:читати, W-089:писати, W-090:повторення, W-101:тато, W-119:тин, W-120:тінь, W-121:їжа, W-122:яма, W-123:маля, W-124:юрта, W-125:люпин, W-126:синій, W-127:єнот, W-128:цимбали, W-129:щука, W-130:дощ, W-131:ферма, W-132:джміль, W-133:джем, W-134:дзиґа, W-135:дзюрчати, W-136:пір'я, W-137:пити, W-138:сім'я, W-139:м'яч, W-140:радіти, W-141:Марія, W-142:мільярд, W-143:пюре, W-144:пір'їна, W-160:весна, W-162:хто, W-163:де, W-164:що, W-165:любити, W-166:равлик, W-167:один, W-168:старенький, W-169:мандрувати, W-170:час, W-171:буква, W-172:назва, W-173:алфавіт, W-174:знак, W-175:м'якшення; select only exact source models, not arbitrary candidate combinations. |
| special-signs L8 a4 | letter-grid / s2 | абвгдежзийклмнопрстуфхцчшщьюяєіїґ | W-120:тінь, W-121:їжа, W-122:яма, W-124:юрта, W-126:синій, W-128:цимбали, W-129:щука, W-131:ферма, W-132:джміль, W-134:дзиґа, W-136:пір'я, W-141:Марія; select only exact source models, not arbitrary candidate combinations. |

## Scored letter-model bindings

All 35 activity/model bindings below pass the proposed exact model declaration/heading lookup, taught-glyph choice and actual video-before-item order. This is author-supplied source-label correspondence, not independent playback. Locator descriptions are recording sections, not invented timestamps; the driver must confirm each distinct section/target independently and record exact playback boundaries before acceptance. Generic letter models are not reused as primer word, syllable, digraph, apostrophe, sentence or letter-name audio.

```json
[
  {
    "module": "sounds-letters-and-hello",
    "lesson": 2,
    "activity": "a5",
    "V": "V-004",
    "T": "T-022",
    "target": "А",
    "segment_locator": "Pronunciation model for А. Pronunciation model for letter А. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 2,
    "activity": "a5",
    "V": "V-005",
    "T": "T-023",
    "target": "О",
    "segment_locator": "Pronunciation model for О. Pronunciation model for letter О. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 2,
    "activity": "a5",
    "V": "V-006",
    "T": "T-024",
    "target": "У",
    "segment_locator": "Pronunciation model for У. Pronunciation model for letter У. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 2,
    "activity": "a5",
    "V": "V-007",
    "T": "T-025",
    "target": "И",
    "segment_locator": "Pronunciation model for И. Pronunciation model for letter И. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 3,
    "activity": "a4",
    "V": "V-007",
    "T": "T-025",
    "target": "И",
    "segment_locator": "Pronunciation model for И. Pronunciation model for letter И. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 3,
    "activity": "a4",
    "V": "V-009",
    "T": "T-027",
    "target": "І",
    "segment_locator": "Pronunciation model for І. Pronunciation model for vowel І. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 3,
    "activity": "a6",
    "V": "V-010",
    "T": "T-028",
    "target": "Н",
    "segment_locator": "Pronunciation model for Н. Pronunciation model for consonant Н. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 4,
    "activity": "a2",
    "V": "V-011",
    "T": "T-029",
    "target": "В",
    "segment_locator": "Pronunciation model for В. Pronunciation model for consonant В. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 4,
    "activity": "a5",
    "V": "V-011",
    "T": "T-029",
    "target": "В",
    "segment_locator": "Pronunciation model for В. Pronunciation model for consonant В. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 4,
    "activity": "a5",
    "V": "V-012",
    "T": "T-030",
    "target": "Л",
    "segment_locator": "Pronunciation model for Л. Pronunciation model for consonant Л. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 4,
    "activity": "a5",
    "V": "V-013",
    "T": "T-031",
    "target": "С",
    "segment_locator": "Pronunciation model for С. Pronunciation model for consonant С. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "sounds-letters-and-hello",
    "lesson": 5,
    "activity": "a4",
    "V": "V-016",
    "T": "T-034",
    "target": "Р",
    "segment_locator": "Pronunciation model for Р. Pronunciation model for consonant Р. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 1,
    "activity": "a2",
    "V": "V-001",
    "T": "T-022",
    "target": "Т",
    "segment_locator": "Pronunciation model for Т. Pronunciation model for Т before CV and VC reading. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 1,
    "activity": "a4",
    "V": "V-005",
    "T": "T-023",
    "target": "Е",
    "segment_locator": "Pronunciation model for Е. Pronunciation model for Е before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "activity": "a2",
    "V": "V-006",
    "T": "T-024",
    "target": "Д",
    "segment_locator": "Pronunciation model for Д. Pronunciation model for Д before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "activity": "a4",
    "V": "V-007",
    "T": "T-025",
    "target": "З",
    "segment_locator": "Pronunciation model for З. Pronunciation model for З before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "activity": "a6",
    "V": "V-008",
    "T": "T-026",
    "target": "Б",
    "segment_locator": "Pronunciation model for Б. Pronunciation model for Б before its word row. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "activity": "a9",
    "V": "V-006",
    "T": "T-024",
    "target": "Д",
    "segment_locator": "Pronunciation model for Д. Pronunciation model for Д before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "activity": "a9",
    "V": "V-007",
    "T": "T-025",
    "target": "З",
    "segment_locator": "Pronunciation model for З. Pronunciation model for З before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "activity": "a9",
    "V": "V-008",
    "T": "T-026",
    "target": "Б",
    "segment_locator": "Pronunciation model for Б. Pronunciation model for Б before its word row. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 3,
    "activity": "a2",
    "V": "V-009",
    "T": "T-027",
    "target": "Г",
    "segment_locator": "Pronunciation model for Г. Pronunciation model for Г before the Г/Ґ contrast. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 4,
    "activity": "a2",
    "V": "V-010",
    "T": "T-029",
    "target": "Ч",
    "segment_locator": "Pronunciation model for Ч. Pronunciation model for Ч before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 4,
    "activity": "a4",
    "V": "V-003",
    "T": "T-030",
    "target": "Й",
    "segment_locator": "Pronunciation model for Й. Pronunciation model for Й in short final-letter reading. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 4,
    "activity": "a6",
    "V": "V-011",
    "T": "T-031",
    "target": "Х",
    "segment_locator": "Pronunciation model for Х. Pronunciation model for Х before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "activity": "a2",
    "V": "V-012",
    "T": "T-032",
    "target": "Ж",
    "segment_locator": "Pronunciation model for Ж. Pronunciation model for Ж before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "activity": "a4",
    "V": "V-013",
    "T": "T-033",
    "target": "Ш",
    "segment_locator": "Pronunciation model for Ш. Pronunciation model for Ш before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "activity": "a9",
    "V": "V-012",
    "T": "T-032",
    "target": "Ж",
    "segment_locator": "Pronunciation model for Ж. Pronunciation model for Ж before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "activity": "a9",
    "V": "V-013",
    "T": "T-033",
    "target": "Ш",
    "segment_locator": "Pronunciation model for Ш. Pronunciation model for Ш before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "activity": "a9",
    "V": "V-010",
    "T": "T-029",
    "target": "Ч",
    "segment_locator": "Pronunciation model for Ч. Pronunciation model for Ч before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "activity": "a9",
    "V": "V-011",
    "T": "T-031",
    "target": "Х",
    "segment_locator": "Pronunciation model for Х. Pronunciation model for Х before its sound rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "special-signs",
    "lesson": 2,
    "activity": "a2",
    "V": "V-008",
    "T": "T-030",
    "target": "Ї",
    "segment_locator": "Pronunciation model for Ї. Full-alphabet video, publisher-labelled Ї sound demonstration only; not its letter name or a complete primer word. Driver must confirm segment playback and exact timecode independently.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "special-signs",
    "lesson": 4,
    "activity": "a2",
    "V": "V-004",
    "T": "T-028",
    "target": "Ц",
    "segment_locator": "Pronunciation model for Ц. Native Ц sound model before primer reading rows. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "special-signs",
    "lesson": 4,
    "activity": "a4",
    "V": "V-011",
    "T": "T-033",
    "target": "Щ",
    "segment_locator": "Pronunciation model for Щ. Full-alphabet video, publisher-labelled Щ sound demonstration only; not its letter name or a complete primer word. Driver must confirm segment playback and exact timecode independently.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "special-signs",
    "lesson": 4,
    "activity": "a4",
    "V": "V-012",
    "T": "T-034",
    "target": "Ш",
    "segment_locator": "Pronunciation model for Ш. Full-alphabet video, publisher-labelled Ш sound demonstration only; not its letter name or a complete primer word. Driver must confirm segment playback and exact timecode independently.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  },
  {
    "module": "special-signs",
    "lesson": 4,
    "activity": "a6",
    "V": "V-005",
    "T": "T-029",
    "target": "Ф",
    "segment_locator": "Pronunciation model for Ф. Native Ф sound model; no visual look-alike claim. Scored segment is the publisher-labelled native letter-sound demonstration; exact playback/timecode confirmation remains driver-owned.",
    "model_target_error": null,
    "choice_error": null,
    "prior_video": true,
    "independent_playback": "pending driver"
  }
]
```

Complete EX-model word admission: all selected whole-row and whole-sentence forms below match lesson-allowed W-record learner forms with non-pending stress; curly source apostrophes are normalized only for dictionary lookup, source display is unchanged.

```json
[
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "example": "EX-003",
    "form": "зуб",
    "matches": [
      [
        "W-118",
        "зуб",
        "noun:inanim:m:v_naz",
        "зуб"
      ],
      [
        "W-118",
        "зуб",
        "noun:inanim:m:v_zna",
        "зуб"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "example": "EX-003",
    "form": "бак",
    "matches": [
      [
        "W-145",
        "бак",
        "noun:inanim:m:v_naz",
        "бак"
      ],
      [
        "W-145",
        "бак",
        "noun:inanim:m:v_zna",
        "бак"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "example": "EX-003",
    "form": "біб",
    "matches": [
      [
        "W-146",
        "біб",
        "noun:inanim:m:v_naz",
        "біб"
      ],
      [
        "W-146",
        "біб",
        "noun:inanim:m:v_zna",
        "біб"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "example": "EX-003",
    "form": "лід",
    "matches": [
      [
        "W-147",
        "лід",
        "noun:inanim:m:v_naz",
        "лід"
      ],
      [
        "W-147",
        "лід",
        "noun:inanim:m:v_zna",
        "лід"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "example": "EX-003",
    "form": "бук",
    "matches": [
      [
        "W-148",
        "бук",
        "noun:inanim:m:v_naz",
        "бук"
      ],
      [
        "W-148",
        "бук",
        "noun:inanim:m:v_zna",
        "бук"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 2,
    "example": "EX-003",
    "form": "над",
    "matches": [
      [
        "W-035",
        "над",
        "prep",
        "над"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 3,
    "example": "EX-004",
    "form": "грати",
    "matches": [
      [
        "W-149",
        "грати",
        "verb:imperf:inf",
        "гра́ти"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 3,
    "example": "EX-004",
    "form": "кава",
    "matches": [
      [
        "W-151",
        "кава",
        "noun:inanim:f:v_naz",
        "ка́ва"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 3,
    "example": "EX-004",
    "form": "грім",
    "matches": [
      [
        "W-152",
        "грім",
        "noun:inanim:m:v_naz",
        "грім"
      ],
      [
        "W-152",
        "грім",
        "noun:inanim:m:v_zna",
        "грім"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 3,
    "example": "EX-004",
    "form": "ґрати",
    "matches": [
      [
        "W-150",
        "ґрати",
        "noun:inanim:p:v_kly:ns",
        "ґра́ти"
      ],
      [
        "W-150",
        "ґрати",
        "noun:inanim:p:v_naz:ns",
        "ґра́ти"
      ],
      [
        "W-150",
        "ґрати",
        "noun:inanim:p:v_zna:ns",
        "ґра́ти"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 3,
    "example": "EX-004",
    "form": "ґава",
    "matches": [
      [
        "W-107",
        "ґава",
        "noun:anim:f:v_naz",
        "ґа́ва"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 3,
    "example": "EX-004",
    "form": "ґрунт",
    "matches": [
      [
        "W-153",
        "ґрунт",
        "noun:inanim:m:v_naz",
        "ґрунт"
      ],
      [
        "W-153",
        "ґрунт",
        "noun:inanim:m:v_zna",
        "ґрунт"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "example": "EX-001",
    "form": "Ми",
    "matches": [
      [
        "W-006",
        "ми",
        "noun:anim:p:v_naz:pron:pers:1",
        "ми"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "example": "EX-001",
    "form": "прилетіли",
    "matches": [
      [
        "W-113",
        "прилетіли",
        "verb:perf:past:p",
        "прилеті́ли"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "example": "EX-001",
    "form": "додому",
    "matches": [
      [
        "W-114",
        "додому",
        "adv",
        "додо́му"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "example": "EX-002",
    "form": "Ви",
    "matches": [
      [
        "W-007",
        "ви",
        "noun:anim:p:v_kly:pron:pers:2",
        "ви"
      ],
      [
        "W-007",
        "ви",
        "noun:anim:p:v_naz:pron:pers:2",
        "ви"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "example": "EX-002",
    "form": "не",
    "matches": [
      [
        "W-061",
        "не",
        "part",
        "не"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "example": "EX-002",
    "form": "бачили",
    "matches": [
      [
        "W-087",
        "бачили",
        "verb:imperf:past:p",
        "ба́чили"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 5,
    "example": "EX-002",
    "form": "жабок",
    "matches": [
      [
        "W-115",
        "жабок",
        "noun:anim:p:v_rod",
        "жа́бок"
      ],
      [
        "W-115",
        "жабок",
        "noun:anim:p:v_zna",
        "жа́бок"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 6,
    "example": "EX-001",
    "form": "Ми",
    "matches": [
      [
        "W-006",
        "ми",
        "noun:anim:p:v_naz:pron:pers:1",
        "ми"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 6,
    "example": "EX-001",
    "form": "прилетіли",
    "matches": [
      [
        "W-113",
        "прилетіли",
        "verb:perf:past:p",
        "прилеті́ли"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 6,
    "example": "EX-001",
    "form": "додому",
    "matches": [
      [
        "W-114",
        "додому",
        "adv",
        "додо́му"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 6,
    "example": "EX-002",
    "form": "Ви",
    "matches": [
      [
        "W-007",
        "ви",
        "noun:anim:p:v_kly:pron:pers:2",
        "ви"
      ],
      [
        "W-007",
        "ви",
        "noun:anim:p:v_naz:pron:pers:2",
        "ви"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 6,
    "example": "EX-002",
    "form": "не",
    "matches": [
      [
        "W-061",
        "не",
        "part",
        "не"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 6,
    "example": "EX-002",
    "form": "бачили",
    "matches": [
      [
        "W-087",
        "бачили",
        "verb:imperf:past:p",
        "ба́чили"
      ]
    ]
  },
  {
    "module": "reading-ukrainian",
    "lesson": 6,
    "example": "EX-002",
    "form": "жабок",
    "matches": [
      [
        "W-115",
        "жабок",
        "noun:anim:p:v_rod",
        "жа́бок"
      ],
      [
        "W-115",
        "жабок",
        "noun:anim:p:v_zna",
        "жа́бок"
      ]
    ]
  },
  {
    "module": "special-signs",
    "lesson": 6,
    "example": "EX-001",
    "form": "Ось",
    "matches": [
      [
        "W-065",
        "ось",
        "part",
        "ось"
      ]
    ]
  },
  {
    "module": "special-signs",
    "lesson": 6,
    "example": "EX-001",
    "form": "вона",
    "matches": [
      [
        "W-004",
        "вона",
        "noun:unanim:f:v_naz:pron:pers:3",
        "вона́"
      ]
    ]
  },
  {
    "module": "special-signs",
    "lesson": 6,
    "example": "EX-001",
    "form": "твоя",
    "matches": [
      [
        "W-011",
        "твоя",
        "adj:f:v_kly:pron:pos",
        "твоя́"
      ],
      [
        "W-011",
        "твоя",
        "adj:f:v_naz:pron:pos",
        "твоя́"
      ]
    ]
  },
  {
    "module": "special-signs",
    "lesson": 6,
    "example": "EX-001",
    "form": "сім’я",
    "matches": [
      [
        "W-138",
        "сім'я",
        "noun:inanim:f:v_naz:xp1",
        "сім'я́"
      ]
    ]
  },
  {
    "module": "special-signs",
    "lesson": 8,
    "example": "EX-001",
    "form": "Ось",
    "matches": [
      [
        "W-065",
        "ось",
        "part",
        "ось"
      ]
    ]
  },
  {
    "module": "special-signs",
    "lesson": 8,
    "example": "EX-001",
    "form": "вона",
    "matches": [
      [
        "W-004",
        "вона",
        "noun:unanim:f:v_naz:pron:pers:3",
        "вона́"
      ]
    ]
  },
  {
    "module": "special-signs",
    "lesson": 8,
    "example": "EX-001",
    "form": "твоя",
    "matches": [
      [
        "W-011",
        "твоя",
        "adj:f:v_kly:pron:pos",
        "твоя́"
      ],
      [
        "W-011",
        "твоя",
        "adj:f:v_naz:pron:pos",
        "твоя́"
      ]
    ]
  },
  {
    "module": "special-signs",
    "lesson": 8,
    "example": "EX-001",
    "form": "сім’я",
    "matches": [
      [
        "W-138",
        "сім'я",
        "noun:inanim:f:v_naz:xp1",
        "сім'я́"
      ]
    ]
  }
]
```

## Exact nine-group conversion map

| Position / U | Replacement lesson / step / activity | Source-model and scored binding | Offline dependency |
| --- | --- | --- | --- |
| P1 U-001 | L3 s1/a2, s3/a5, s-print-workbook/a8; L4 s1/s2 a1/a3/a4; L5 s1/s2 a1/a2/a3/a5, workbook a6 | T-010/T-012/T-014/T-015/T-016/T-017/T-018, X-003/X-005; full T-037 row hosts L3 a8. W-084/W-085 are read only after Р in L5. Retained single-letter quizzes have separate V/T bindings. | Teacher models exact CV/VC/CVC, before-І and рука/ріка forms; learner reads aloud/copies; no exact combination audio asserted. |
| P2 U-002 | L1 s3/a8; L3 s2-print/a4, workbook a6/a7; L4 s4/a10 | Orthography targets W-074/W-081/W-082/W-101/W-117; W-106/W-107; W-101/W-103/W-108/W-109/W-110. Complete T-035/EX-004 six-word Г/Ґ row hosts a4/a6. | Exact word/contrast read-aloud from print, teacher models; native letter videos retained. |
| P2 U-003 | L5 s3-print/a7; L6 s2/a3/a4 | T-036/T-037 quote comprehension; EX-001/EX-002 retained whole for reading/copying. | Teacher models complete sentences, no recorded-sentence binding. |
| P2 U-004 | L2 s3/s4 a5/a6/a7/a8/a9; L3 s2-print/s3 a4/a5/a6 | Full EX-003 row admits W-145–W-148 plus W-118/W-035. Full EX-004/T-035 row admits W-149–W-153 plus W-107; no shortened row. | Teacher models complete printed word rows; hearing isolated letter sounds is separate. |
| P3 U-003 | L1 s1/a1/a2/a3, workbook a5 | T-001/X-001 tin/tin-soft-sign pair; fill-in orthography W-119/W-120. V-001/V-007 general hard/soft support is unscored. | Teacher models both intact source words, learner reads/copies; no generic-model equivalence. |
| P3 U-004 | L2 s1/s2 a4/a6; L3 s1/s2 a2/a4/a5/a6; L4 s3/workbook a9 | Orthography W-121–W-131, W-010/W-140/W-141/W-142 exact sourced forms; T-002–T-008/T-013/T-022/T-023/T-025. Named-letter listening retained separately. | Teacher models each positional word value before offline read-aloud. |
| P3 U-005 | L5 s1/s2 a1/a2/a3/a4/a6 | T-009/T-010/T-013/T-016/T-017; orthography W-132–W-135. V-002 is individual-letter recall only. | Teacher models joined дж/дз and hard/soft дз in source words; offline production. |
| P3 U-006 | L6 s1/s2 a1/a2/a3/a4/a5/a6; s-print-workbook/a7 | T-011/T-015/T-017/T-026, W-136/W-137/W-139/W-143/W-144; printed T-036 contrast hosts a7. Complete EX-001 retained for reading, copy and unjumble. | Teacher models apostrophe contrast and complete sentence; print presence/absence is scored, acoustics are not. |
| P3 U-007 | L7 s1/a1, s1-print/a2, s2/a3/a4, workbook a5/a6 | Full sourced T-012 alphabet-name table as attributed quote; a2/a5/a6 comprehension depends on its printed names/order/glyphs. | Teacher models all names; V-002 letter sounds never stand in for names. |

Resolved status records an authorized modality conversion, not independent playback or absence from all possible future recordings. Every inherited U-id/claim/search entry remains. The other three already-resolved U-records are preserved.

## STOP and driver-owned acceptance residuals

STOP: the actual current A1 choice checker crashes on a schema-valid `order` family (P3 L7 a4). Its item loop assumes dictionaries although the schema mandates strings. Engine edits exceed this packet's ownership. The source/plan/evidence package is valid partial work; Acceptance 2's integrated compatibility proof is unmet and owned by the accountable #8425 driver/engine lane.

BLOCKED: `$PROJECT_PYTHON` stdin probe calling `check_7_a1_choices` with the exact `order` witness above, a real planned lesson, locked words and source client.
ERROR: `AttributeError: 'str' object has no attribute 'get'` at `scripts/build/fresh/runner.py:653` (`kind = item.get("kind")`).
STILL WORKS: the order fixture passes the current JSON Schema and `_structural_activity_error`; 16 other current family/recap choice probes pass, the proposed listening model/choice probes return no error, and all three deterministic package gates pass.
ASK / next owner action: driver assigns the bounded engine fix and regression proof, obtains its required review, integrates the exact reviewed listening/publication-right implementations with this deliverable, then reruns every fixture through actual schema/preflight/check 7. No bypass or worker engine edit is authorized here.

Five acceptance work classes remain, all driver-owned: (1) order/check-7 engine fix plus integrated head/registry identity and reruns; (2) independent playback for the 26 distinct scored section/target bindings and independent semantic/plan reviews; (3) #9409 search_resources exposure/search; (4) regeneration of seven inherited stale plan-review manifests in position order; (5) writer-output source-form/decodability/resolver-role/rendering and held-out learner proof when builds are authorized. No independent held-out proof was produced here. Pending package is not final curriculum DoD. Stop policy preserves all valid edits and returns the complete reproducer instead of weakening an operation.

Scope sidecars were regenerated and remain byte-identical because introduced letters, grammar and core counts are unchanged. No approvals/receipts/manifests are renewed by these gates. The rebuilt S-001 actual text cites the alphabet requirement; retained historical U-002 text is provenance, not a current failure assertion.


Final provisional plan reruns after glyph-key and teacher-dependency clarifications:

```bash
"$PROJECT_PYTHON" -m scripts.curriculum.validate a1 sounds-letters-and-hello --provisional-pack --write-scope
```
Exit 0:
```text
plan-validate: the §6 gate of docs/epics/fresh-build-plan-schema.md — §2 rules 1–7 with the semantics of §2a (single-plan and cross-plan). not_checked items are reported, never passed silently.
plan: a1/sounds-letters-and-hello
status: pass
mode: provisional
NOTE core_cefr_above_module: lesson 2: core lemma 'звук' (W-077) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 2: core lemma 'літера' (W-078) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 3: core lemma 'голосний' (W-079) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 3: core lemma 'приголосний' (W-080) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 4: core lemma 'малина' (W-082) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 4: core lemma 'слива' (W-083) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOT_CHECKED minutes_constants_undefined: not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)
NOT_CHECKED word_target_not_calibrated: not_checked: word_target presence and type are checked; the per-level minimum is not calibrated (§2a)
NOT_CHECKED lesson_activity_minimums_not_calibrated: not_checked: per-lesson inline/workbook activity minimums are not calibrated (§2a)
NOT_CHECKED arc_has_no_structured_grammar_or_vocabulary: not_checked: the arc carries letters only; it has no structured grammar or vocabulary to compare against (§2a)
NOT_CHECKED title_quantities_not_parsed: subtitle digits: 1, 3; digit quantities are not parsed — the plan review checks stated quantities against the scope sidecar (§2a)
NOT_CHECKED mechanical_rule_not_checked: gate M5 was not checked: core word records carry no CEFR level: W-074
activity_report (plan stage) module: workbook_activities=9 inline_activities=26 workbook_presence_complete=True largest_workbook_type_share=0.3333333333333333 longest_same_type_workbook_run=2
activity_report (plan stage) lesson 1: kind=teach inline=4 workbook=1 distinct_types=quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 2: kind=teach inline=4 workbook=2 distinct_types=letter-grid,observe,odd-one-out,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 3: kind=teach inline=6 workbook=2 distinct_types=letter-grid,odd-one-out,pick-syllables,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 4: kind=teach inline=4 workbook=2 distinct_types=divide-words,letter-grid,pick-syllables,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 5: kind=teach inline=5 workbook=2 distinct_types=letter-grid,match-up,pick-syllables,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 6: kind=recap inline=3 workbook=0 distinct_types=letter-grid,observe,quiz has_workbook=False

```

```bash
"$PROJECT_PYTHON" -m scripts.curriculum.validate a1 reading-ukrainian --provisional-pack --write-scope
```
Exit 0:
```text
plan-validate: the §6 gate of docs/epics/fresh-build-plan-schema.md — §2 rules 1–7 with the semantics of §2a (single-plan and cross-plan). not_checked items are reported, never passed silently.
plan: a1/reading-ukrainian
status: pass
mode: provisional
NOT_CHECKED minutes_constants_undefined: not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)
NOT_CHECKED word_target_not_calibrated: not_checked: word_target presence and type are checked; the per-level minimum is not calibrated (§2a)
NOT_CHECKED lesson_activity_minimums_not_calibrated: not_checked: per-lesson inline/workbook activity minimums are not calibrated (§2a)
NOT_CHECKED arc_has_no_structured_grammar_or_vocabulary: not_checked: the arc carries letters only; it has no structured grammar or vocabulary to compare against (§2a)
NOT_CHECKED title_quantities_not_parsed: no ASCII digits in the title or subtitle; digit quantities are not parsed — the plan review checks stated quantities against the scope sidecar (§2a)
activity_report (plan stage) module: workbook_activities=13 inline_activities=35 workbook_presence_complete=True largest_workbook_type_share=0.23076923076923078 longest_same_type_workbook_run=1
activity_report (plan stage) lesson 1: kind=teach inline=5 workbook=3 distinct_types=fill-in,letter-grid,match-up,pick-syllables,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 2: kind=teach inline=7 workbook=2 distinct_types=divide-words,letter-grid,observe,quiz has_workbook=True
activity_report (plan stage) lesson 3: kind=teach inline=5 workbook=2 distinct_types=fill-in,letter-grid,odd-one-out,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 4: kind=teach inline=7 workbook=3 distinct_types=anagram,fill-in,letter-grid,match-up,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 5: kind=teach inline=7 workbook=3 distinct_types=letter-grid,observe,pick-syllables,quiz,unjumble has_workbook=True
activity_report (plan stage) lesson 6: kind=recap inline=4 workbook=0 distinct_types=letter-grid,observe,quiz has_workbook=False

```

```bash
"$PROJECT_PYTHON" -m scripts.curriculum.validate a1 special-signs --provisional-pack --write-scope
```
Exit 0:
```text
plan-validate: the §6 gate of docs/epics/fresh-build-plan-schema.md — §2 rules 1–7 with the semantics of §2a (single-plan and cross-plan). not_checked items are reported, never passed silently.
plan: a1/special-signs
status: pass
mode: provisional
NOT_CHECKED minutes_constants_undefined: not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)
NOT_CHECKED word_target_not_calibrated: not_checked: word_target presence and type are checked; the per-level minimum is not calibrated (§2a)
NOT_CHECKED lesson_activity_minimums_not_calibrated: not_checked: per-lesson inline/workbook activity minimums are not calibrated (§2a)
NOT_CHECKED arc_has_no_structured_grammar_or_vocabulary: not_checked: the arc carries letters only; it has no structured grammar or vocabulary to compare against (§2a)
NOT_CHECKED title_quantities_not_parsed: no ASCII digits in the title or subtitle; digit quantities are not parsed — the plan review checks stated quantities against the scope sidecar (§2a)
activity_report (plan stage) module: workbook_activities=20 inline_activities=33 workbook_presence_complete=True largest_workbook_type_share=0.35 longest_same_type_workbook_run=2
activity_report (plan stage) lesson 1: kind=teach inline=4 workbook=2 distinct_types=fill-in,letter-grid,match-up,observe,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 2: kind=teach inline=4 workbook=3 distinct_types=anagram,fill-in,letter-grid,pick-syllables,quiz has_workbook=True
activity_report (plan stage) lesson 3: kind=teach inline=4 workbook=3 distinct_types=count-syllables,fill-in,letter-grid has_workbook=True
activity_report (plan stage) lesson 4: kind=teach inline=6 workbook=3 distinct_types=divide-words,fill-in,letter-grid,match-up,quiz has_workbook=True
activity_report (plan stage) lesson 5: kind=teach inline=4 workbook=3 distinct_types=anagram,fill-in,observe,pick-syllables has_workbook=True
activity_report (plan stage) lesson 6: kind=teach inline=4 workbook=3 distinct_types=fill-in,letter-grid,observe,odd-one-out,unjumble has_workbook=True
activity_report (plan stage) lesson 7: kind=teach inline=3 workbook=3 distinct_types=letter-grid,odd-one-out,order,quiz has_workbook=True
activity_report (plan stage) lesson 8: kind=recap inline=4 workbook=0 distinct_types=letter-grid,observe,quiz has_workbook=False

```

Delivery file list (exact staged paths are checked against ownership before commit):

```text
curriculum/l2-uk-en/evidence/a1/_requests/reading-ukrainian.pack.yaml
curriculum/l2-uk-en/evidence/a1/_requests/reading-ukrainian.words.yaml
curriculum/l2-uk-en/evidence/a1/_requests/revise-a1-p1-p3.md
curriculum/l2-uk-en/evidence/a1/_requests/sounds-letters-and-hello.pack.yaml
curriculum/l2-uk-en/evidence/a1/_requests/sounds-letters-and-hello.words.yaml
curriculum/l2-uk-en/evidence/a1/_requests/special-signs.pack.yaml
curriculum/l2-uk-en/evidence/a1/_requests/special-signs.words.yaml
curriculum/l2-uk-en/evidence/a1/_words.registry.yaml
curriculum/l2-uk-en/evidence/a1/_words.registry.yaml.lock
curriculum/l2-uk-en/evidence/a1/_words.yaml
curriculum/l2-uk-en/evidence/a1/_words.yaml.lock
curriculum/l2-uk-en/evidence/a1/reading-ukrainian.yaml
curriculum/l2-uk-en/evidence/a1/reading-ukrainian.yaml.lock
curriculum/l2-uk-en/evidence/a1/sounds-letters-and-hello.yaml
curriculum/l2-uk-en/evidence/a1/sounds-letters-and-hello.yaml.lock
curriculum/l2-uk-en/evidence/a1/special-signs.yaml
curriculum/l2-uk-en/evidence/a1/special-signs.yaml.lock
curriculum/l2-uk-en/lesson-plans/a1/reading-ukrainian.yaml
curriculum/l2-uk-en/lesson-plans/a1/sounds-letters-and-hello.yaml
curriculum/l2-uk-en/lesson-plans/a1/special-signs.yaml
```

Final P1 U-001 print-discrimination clarification: L5 workbook a6 includes the intact W-084/W-085 pair with different printed syllable units, retaining the teacher model and offline read-aloud. This is the 61st changed activity record. Its complete before/after row is:

| Id | Before type / host / action | After type / host / action | Continuity |
| --- | --- | --- | --- |
| P1 L5 a6 | pick-syllables / no host: Complete newly readable short words and names by selecting missing syllables formed with К, П, and Р (коса, Павлик, Поліна, рука); progresses from syllable division to active word completion. | pick-syllables / no comprehension host: Complete newly readable short words and names by selecting missing syllables formed with К, П, and Р (коса, Павлик, Поліна, рука). Include the complete printed W-084 рука and W-085 ріка models after Р is introduced, and select their distinguishing ру / рі unit plus the common ка to reproduce each intact word. This is scored print/syllable discrimination, not word meaning or recorded-word recognition; the teacher models both words before offline read-aloud. Keep the exact verified source forms and progress from syllable division to active assembly. | Exact minimal-pair print discrimination now has an explicit scored endpoint; native letter audio remains distinct. |

Final P1 validation after the minimal-pair assembly clarification: exit 0, status pass, provisional; mechanical notes unchanged.

```text
plan-validate: the §6 gate of docs/epics/fresh-build-plan-schema.md — §2 rules 1–7 with the semantics of §2a (single-plan and cross-plan). not_checked items are reported, never passed silently.
plan: a1/sounds-letters-and-hello
status: pass
mode: provisional
NOTE core_cefr_above_module: lesson 2: core lemma 'звук' (W-077) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 2: core lemma 'літера' (W-078) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 3: core lemma 'голосний' (W-079) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 3: core lemma 'приголосний' (W-080) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 4: core lemma 'малина' (W-082) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 4: core lemma 'слива' (W-083) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOT_CHECKED minutes_constants_undefined: not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)
NOT_CHECKED word_target_not_calibrated: not_checked: word_target presence and type are checked; the per-level minimum is not calibrated (§2a)
NOT_CHECKED lesson_activity_minimums_not_calibrated: not_checked: per-lesson inline/workbook activity minimums are not calibrated (§2a)
NOT_CHECKED arc_has_no_structured_grammar_or_vocabulary: not_checked: the arc carries letters only; it has no structured grammar or vocabulary to compare against (§2a)
NOT_CHECKED title_quantities_not_parsed: subtitle digits: 1, 3; digit quantities are not parsed — the plan review checks stated quantities against the scope sidecar (§2a)
NOT_CHECKED mechanical_rule_not_checked: gate M5 was not checked: core word records carry no CEFR level: W-074
activity_report (plan stage) module: workbook_activities=9 inline_activities=26 workbook_presence_complete=True largest_workbook_type_share=0.3333333333333333 longest_same_type_workbook_run=2
activity_report (plan stage) lesson 1: kind=teach inline=4 workbook=1 distinct_types=quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 2: kind=teach inline=4 workbook=2 distinct_types=letter-grid,observe,odd-one-out,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 3: kind=teach inline=6 workbook=2 distinct_types=letter-grid,odd-one-out,pick-syllables,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 4: kind=teach inline=4 workbook=2 distinct_types=divide-words,letter-grid,pick-syllables,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 5: kind=teach inline=5 workbook=2 distinct_types=letter-grid,match-up,pick-syllables,quiz,watch-and-repeat has_workbook=True
activity_report (plan stage) lesson 6: kind=recap inline=3 workbook=0 distinct_types=letter-grid,observe,quiz has_workbook=False

```

Order reproducer bound to the actual P3 L7 plan entry and planned a4 id (schema-valid source alphabet ordering):

```json
{
  "module": "special-signs",
  "lesson": 7,
  "activity": "a4",
  "schema_valid": true,
  "structural_error": null,
  "check7": {
    "status": "crashed",
    "error": "'str' object has no attribute 'get'"
  }
}
```

Closeout live state: read-only `gh issue view 8425 --json number,state,title` returned OPEN. `delegate.py status revise-a1-p1-p3-r2` returned running, author model gpt-6.1-sol/high, allow_merge false. No terminal worker success or review approval is inferred. Seven inherited manifest locators are present and preserved; their prior approvals do not apply to version-2 plans / refreshed input digests.

```json
[
  {
    "path": "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.manifest.yaml",
    "present": true,
    "keys": [
      "inputs",
      "kind",
      "learner_state",
      "level",
      "manifest_schema",
      "position",
      "slug"
    ],
    "file_sha256": "8591d48151704f4cf6443b52df56e47b4cc295f0975cd69ec69fedf83c3ccce8"
  },
  {
    "path": "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/8591d48151704f4cf6443b52df56e47b4cc295f0975cd69ec69fedf83c3ccce8.yaml",
    "present": true,
    "keys": [
      "inputs",
      "kind",
      "learner_state",
      "level",
      "manifest_schema",
      "position",
      "slug"
    ],
    "file_sha256": "8591d48151704f4cf6443b52df56e47b4cc295f0975cd69ec69fedf83c3ccce8"
  },
  {
    "path": "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.manifest.yaml",
    "present": true,
    "keys": [
      "inputs",
      "kind",
      "learner_state",
      "level",
      "manifest_schema",
      "position",
      "slug"
    ],
    "file_sha256": "217c19ca26cde45cf340e624d8b422df5b92d029d29ffbc706e6f5f9a2da94d9"
  },
  {
    "path": "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/217c19ca26cde45cf340e624d8b422df5b92d029d29ffbc706e6f5f9a2da94d9.yaml",
    "present": true,
    "keys": [
      "inputs",
      "kind",
      "learner_state",
      "level",
      "manifest_schema",
      "position",
      "slug"
    ],
    "file_sha256": "217c19ca26cde45cf340e624d8b422df5b92d029d29ffbc706e6f5f9a2da94d9"
  },
  {
    "path": "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/360b2f2eb4728efb7df6b287cd3028065685031a138860800af6e62fd745bd4c.yaml",
    "present": true,
    "keys": [
      "inputs",
      "kind",
      "learner_state",
      "level",
      "manifest_schema",
      "position",
      "slug"
    ],
    "file_sha256": "360b2f2eb4728efb7df6b287cd3028065685031a138860800af6e62fd745bd4c"
  },
  {
    "path": "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.manifest.yaml",
    "present": true,
    "keys": [
      "inputs",
      "kind",
      "learner_state",
      "level",
      "manifest_schema",
      "position",
      "slug"
    ],
    "file_sha256": "db619776b2c86847e583410a68780f4ed57c20810013a29a9cb9ecd25c9a9e78"
  },
  {
    "path": "curriculum/l2-uk-en/evidence/a1/_state/special-signs/manifests/plan/db619776b2c86847e583410a68780f4ed57c20810013a29a9cb9ecd25c9a9e78.yaml",
    "present": true,
    "keys": [
      "inputs",
      "kind",
      "learner_state",
      "level",
      "manifest_schema",
      "position",
      "slug"
    ],
    "file_sha256": "db619776b2c86847e583410a68780f4ed57c20810013a29a9cb9ecd25c9a9e78"
  }
]
```

Acceptance residual count: five driver-owned work classes, listed above; open U count from the strict pack tools is zero. This authoring worker has no authority to dispatch the residual engine/review/build work.

Final integration handoff at 2026-10-01T12:05:48Z: ownership check passes for the exact 20 changed paths, lock bytes match all three final packs and plan references, inherited 153 word records compare unchanged, and `git diff --check` is empty. Branch is codex/revise-a1-p1-p3. This report and all valid partial edits are committed and pushed together; final response supplies the resulting head SHA. No independent approval or shipped curriculum outcome is claimed.
