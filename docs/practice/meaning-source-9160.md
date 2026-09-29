# #9160 — reduced meaning-containment candidate after final round 5

This is an **unpublished candidate**, not a delivered learner outcome. Independent Google/AGY evaluation found material failures in the 177-row `dmklinger_row` admission mechanism. The approved stop rule withdraws that entire mechanism, rather than tuning examples. On the same frozen denominator of 6,217 lexemes, the reduced artifact retains 22 English meanings and withholds 6,195. Its remaining mechanism still requires one fresh independent verification with per-item source evidence. A further material failure or unsupported retained meaning disables the affected meaning surfaces and dependent exercises.

Withheld rows lose flashcards, matching, choice and synonym eligibility while independent modes remain unchanged. No Ukrainian definition becomes an English substitute. Coverage restoration belongs to #8977 (owner: atlas); the over-withholding ceiling is nonblocking. #9160 closes only after exact-head independent code approval, semantic success, same-head CI, publication, old-deck replacement/invalidation and live delivery checks, as `contamination contained; coverage not restored`.

## Frozen inputs, code and artifacts

The reproducer verifies every frozen input hash and opens the source databases read-only. Do not alter inputs or hashes to make reproduction pass.

| Input or code | SHA-256 |
| --- | --- |
| `Frozen release gzip` | `d01ed4b4cf10d8f587de214d0e3dd7f4039f4bafe5549d6bed7145bc34e55b19` |
| `atlas.db` | `fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca` |
| `sources.db` | `7868ce16f3cc8280676f08f436b94563ba20e3e7909ad236f06c2bdce19baa7b` |
| `scripts/audit/generate_practice_deck.py` | `6c7d8ca7cd854ebfdba499ff93c52b0f2198269c44617b0f93804fd5576fc7a6` |
| `scripts/practice/meaning_containment.py` | `9899bb742da4104c7a14871e6de832fc70fe0ea7209b1310b493ada5122bc615` |
| `scripts/audit/reproduce_meaning_9160.py` | `0c0c67510f8e7661442353b962fc978fdcaf60f865baf12fda307653ee1cbdc1` |

```bash
/home/ops/learn-ukrainian/.venv/bin/python -m scripts.audit.reproduce_meaning_9160 \
  --package /tmp/codex-atlas-20260929/frozen/lexicon-practice-deck-atlas-practice-v1-f1e1cf95470ce319.json.gz \
  --atlas-db /home/ops/learn-ukrainian/data/atlas.db \
  --sources-db /home/ops/learn-ukrainian/data/sources.db \
  --output batch_state/meaning-9160-reduced/shards
```

The ignored output directory contains 55 shards and the following three manifests. Shard hashes and all level × mode × withholding-reason tables are in the summary. These artifacts stay outside Git and are not published.

| Manifest | SHA-256 |
| --- | --- |
| `meaning-9160-summary.json` | `9c9c1747516962de8db758caf1306deab7823b7f2a0033e9fcdd3d9887f8e47b` |
| `meaning-9160-admissions.json` | `a5ec55bdf755db37c0cab41ac65d6ccc8a2d0a3e2bcaf10798cc1bbd1de0ef8f` |
| `meaning-9160-history.json` | `f24a4d7ae99f9e4ca7d10ece0ee90fc56c68efc14c3dbec0adfe4f784243d2e9` |

## Admission boundary and independent evaluation

Each retained candidate is tied to one **specific** `dmklinger_uk_en` row ID and candidate in the frozen `sources.db`. The source headword must equal the Atlas lemma with only stress marks removed, preserving case; its POS must equal the Atlas article POS; exactly **one** source row may share that case-preserving headword and POS; and the displayed candidate must be a complete alternative in the Atlas English head, the Atlas attributed field, and that row's **first** candidate. A learner-English list must also put it in its first candidate. The first-candidate constraint is a conservative ambiguity stop: row 735 for `вплива́ти` mixes “to exert an influence” with “to swim in”; the latter is not an independently resolved sense of the displayed Atlas word. Balla can veto a conflicting reverse mapping but does not manufacture forward support. Qualifier-bearing source alternatives must remain intact; only a trailing `(proper noun)` metadata tag can be omitted. Matching case/POS alone never admits an unresolved homonym: when several rows share the headword and POS once stress is removed (`по́ра` “pore” / `пора́` “time”, `ті́кати` “to tick” / `тіка́ти` “to flee”), the row is `unresolved_source_homograph` even if only one row matches the display. Atlas's own stress field cannot pick the row, because it is a Kaikki copy (for `тікати` it points at the “tick” homograph while the paradigm is the “flee” verb).

`dmklinger_row` is now withheld as `withdrawn_dmklinger_mechanism`, even when its row binding passes. The remaining frozen artifact contains only `learner_dmklinger_corrob|learner_english_gloss|unique_case_pos_primary_candidate_row`: A1 11, A2 4, B1 7, B2 0, C1 0. Kaikki, slovnyk.me, curation, Горох, Wikidata and base-form paths retain zero rows; separately accessible source gaps remain #8977 residuals.

The first semantic evaluation reproduced all artifacts and found the raw Dmklinger mechanism unsafe. Its reported clean 22-row path does not waive the final gate: independent Google/AGY must reproduce the reduced exact-head artifact, rebuild its admission partition and inspect **all remaining 22 meanings** with fresh positive lexeme/POS/sense evidence. Record source table/row, unmodified source text, VESUM evidence and the assessment per item. Author provenance or a copied sample list alone is insufficient. Check every historical regression and known error outside samples. Missing or inconclusive evidence is unsupported.

Retained seed 20261101 and withholding seed 20261102 were registered before sampling. Each path/level seed is the big-endian integer from the first eight bytes of SHA-256 of `base_seed|mechanism|level`; proportional quotas use Hamilton largest remainder, ties in A1–C1 order. The 60-row withholding audit is nonblocking for coverage. This is the **one final verification of the reduced artifact**, not another tuning round.

## Denominator, modes and withholding reasons

| Level | Frozen rows | Retained EN | Retained UK | Withheld | Frozen display changed |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 1,496 | 11 | 0 | 1,485 | 1,487 |
| A2 | 1,511 | 4 | 0 | 1,507 | 1,510 |
| B1 | 1,505 | 7 | 0 | 1,498 | 1,501 |
| B2 | 1,040 | 0 | 0 | 1,040 | 1,040 |
| C1 | 665 | 0 | 0 | 665 | 665 |
| **Total** | **6,217** | **22** | **0** | **6,195** | **6,203** |

| Level | Flashcards before → after | Matching before → after | Choice before → after | Synonym before → after |
| --- | ---: | ---: | ---: | ---: |
| A1 | 1,496 → 11 | 1,362 → 10 | 1,362 → 10 | 0 → 0 |
| A2 | 1,511 → 4 | 1,340 → 3 | 1,340 → 3 | 0 → 0 |
| B1 | 1,505 → 7 | 652 → 4 | 652 → 4 | 0 → 0 |
| B2 | 1,040 → 0 | 779 → 0 | 779 → 0 | 0 → 0 |
| C1 | 665 → 0 | 511 → 0 | 511 → 0 | 0 → 0 |

Every frozen row had flashcards. Reasons below are first-failing rules, not marginal effects; the summary contains separate dependent-mode cross-tabs.

| Withholding reason | A1 | A2 | B1 | B2 | C1 | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `dated_citation` | 0 | 0 | 408 | 13 | 3 | 424 |
| `dictionary_fragment` | 4 | 8 | 112 | 33 | 15 | 172 |
| `example_quotation` | 0 | 0 | 26 | 1 | 2 | 29 |
| `parenthesized_citation` | 2 | 2 | 104 | 27 | 53 | 188 |
| `reverse_source_conflict` | 11 | 17 | 13 | 14 | 5 | 60 |
| `reviewed_wrong_sense` | 1 | 26 | 18 | 12 | 8 | 65 |
| `same_word_sum11` | 0 | 0 | 27 | 23 | 11 | 61 |
| `unattributed_english` | 579 | 646 | 284 | 431 | 223 | 2,163 |
| `unbound_english_sense` | 27 | 46 | 27 | 31 | 10 | 141 |
| `unbound_independent_row` | 587 | 449 | 347 | 234 | 98 | 1,715 |
| `unbound_original_sense` | 129 | 150 | 0 | 0 | 0 | 279 |
| `unbound_primary_learner_sense` | 46 | 61 | 33 | 24 | 6 | 170 |
| `unresolved_source_homograph` | 11 | 9 | 5 | 3 | 1 | 29 |
| `unsafe_display_fields` | 0 | 1 | 47 | 41 | 13 | 102 |
| `unsupported_english_source` | 54 | 60 | 10 | 100 | 196 | 420 |
| `withdrawn_dmklinger_mechanism` | 34 | 32 | 37 | 53 | 21 | 177 |

Whole-artifact gates check both display fields and equality; no fragment/citation/SUM-11, Cyrillic, digit or cross-reference leak; complete load-bearing qualifiers; row-specific provenance; no dependent meaning mode on withheld rows; and preservation of independent modes. **All 11 retained A2+ displays were already English in the frozen package.** Passing these mechanical checks is not semantic approval.

## Historical regression denominator

The unchanged denominator is **367 lexeme × failure-condition cases**: 65 reviewed wrong senses, 38 named forbidden displays and 264 source-binding conditions. It is the deduplicated union of copied fixtures, inline tests and named round-1–4 failures. The reduced artifact retains only one source-binding historical case, the already corroborated learner-gloss row; all other historical rows remain withheld or absent. One named phrase outside the frozen release remains a direct fixture. The historical list is never an admission bypass.

## Delivery and residuals

The original OpenAI work and Claude Opus recovery are followed by this Codex class withdrawal. Actual authorship is mixed. Independent code review comes from outside OpenAI and Anthropic; Google/AGY owns only source-grounded Ukrainian semantics. Both must assess the final exact head before PR/CI landing.

B2 and C1 have no meaning sessions in this reduced artifact. Live surfaces must show explicit unavailability rather than revive withdrawn or cached meanings. The driver owns integrated regeneration/publication/pointer landing/deployment under prior authorization and desktop/390px regular/daily cards, meaning, Mixed, direct-entry, resume, cache and teacher-deck checks. Those delivery paths remain unverified. A pushed branch alone cannot close #9160. All coverage restoration and source alignment gaps remain owned by Atlas under #8977.
