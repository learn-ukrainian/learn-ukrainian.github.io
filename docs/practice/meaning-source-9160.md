# #9160 — final local meaning-containment candidate (round 5)

This is an **unpublished candidate**, not a delivered learner outcome. On the pinned 6,217-lexeme release package, the transform retains 199 English meanings and withholds 6,018. A withheld row loses flashcards, matching, choice and synonym eligibility while its independent modes remain unchanged. No Ukrainian definition is rewritten into English. Coverage restoration belongs to #8977 (owner: atlas); the 10% over-withholding ceiling is non-blocking for this removal-only round. The accountable driver must still obtain exact-head independent cross-family semantic approval, same-head CI, publication and old-deck replacement/invalidation, and live checks before #9160 can close as `contamination contained; coverage not restored`.

## Frozen inputs, code and artifacts

Run from this dispatch worktree with the shared project interpreter. The reproducer rejects any input hash mismatch. Source databases are opened read-only. These inputs are not changed to make the transform pass.

| Input | SHA-256 |
| --- | --- |
| Frozen release gzip, `/tmp/codex-atlas-20260929/frozen/lexicon-practice-deck-atlas-practice-v1-f1e1cf95470ce319.json.gz` | `d01ed4b4cf10d8f587de214d0e3dd7f4039f4bafe5549d6bed7145bc34e55b19` |
| `/home/ops/learn-ukrainian/data/atlas.db` | `fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca` |
| `/home/ops/learn-ukrainian/data/sources.db` | `7868ce16f3cc8280676f08f436b94563ba20e3e7909ad236f06c2bdce19baa7b` |
| `scripts/audit/generate_practice_deck.py` | `6c7d8ca7cd854ebfdba499ff93c52b0f2198269c44617b0f93804fd5576fc7a6` |
| `scripts/practice/meaning_containment.py` | `6577779b8ceb85be3e54ca25199c599409ac4cd10b3514bbb2e2d8d40adef0d1` |
| `scripts/audit/reproduce_meaning_9160.py` | `0c0c67510f8e7661442353b962fc978fdcaf60f865baf12fda307653ee1cbdc1` |

```bash
/home/ops/learn-ukrainian/.venv/bin/python -m scripts.audit.reproduce_meaning_9160 \
  --package /tmp/codex-atlas-20260929/frozen/lexicon-practice-deck-atlas-practice-v1-f1e1cf95470ce319.json.gz \
  --atlas-db /home/ops/learn-ukrainian/data/atlas.db \
  --sources-db /home/ops/learn-ukrainian/data/sources.db \
  --output batch_state/meaning-9160-r5/shards
```

The ignored `batch_state/meaning-9160-r5/shards/` directory contains all 55 output shards, `meaning-9160-summary.json` (SHA-256 `644d7ebe93f530f656862412b7f670334621cb38130fc14440d6952fb21a81c9`, including SHA-256 for every shard and the level × mode × withholding-reason cross-tabs), `meaning-9160-admissions.json` (SHA-256 `79d487d113095b0208b046ad75e70141b30d0b8572f8fca05471c9c2eba3e614`), and `meaning-9160-history.json` (SHA-256 `4091d8c626e0e8e6afdebb9568955b4ee9d52ddbc7d64819e37288efb77e5eb7`). Generated artifacts stay outside Git. They are local evaluation artifacts, not published shards.

## Admission boundary and evaluator denominator

Each retained candidate is tied to one **specific** `dmklinger_uk_en` row ID and candidate in the frozen `sources.db`. The source headword must equal the Atlas lemma with only stress marks removed, preserving case; its POS must equal the Atlas article POS; exactly **one** source row may share that case-preserving headword and POS; and the displayed candidate must be a complete alternative in the Atlas English head, the Atlas attributed field, and that row's **first** candidate. A learner-English list must also put it in its first candidate. The first-candidate constraint is a conservative ambiguity stop: row 735 for `вплива́ти` mixes “to exert an influence” with “to swim in”; the latter is not an independently resolved sense of the displayed Atlas word. Balla can veto a conflicting reverse mapping but does not manufacture forward support. Qualifier-bearing source alternatives must remain intact; only a trailing `(proper noun)` metadata tag can be omitted. Matching case/POS alone never admits an unresolved homonym: when several rows share the headword and POS once stress is removed (`по́ра` “pore” / `пора́` “time”, `ті́кати` “to tick” / `тіка́ти` “to flee”), the row is `unresolved_source_homograph` even if only one row matches the display. Atlas's own stress field cannot pick the row, because it is a Kaikki copy (for `тікати` it points at the “tick” homograph while the paradigm is the “flee” verb).

Atlas copies of Kaikki and slovnyk.me are not counted as independent witnesses. They and curation, Горох, Wikidata and base-form variants produced **zero retained paths** under this rule; missing separately accessible source records are a #8977 tooling/coverage gap. No row is admitted by a prefix-derived aspect partner, substring or word-bag match. This stops the lowercase `покуття` from receiving the region's capitalized `Поку́ття` source row 22035 and stops the noun `лікарняний` from receiving adjective row 4327; source noun row 18067 instead says “sick day.” Source strings and row IDs were copied from read-only `sources.db` into focused fixtures.

The mutually exclusive retained admission partition, to be rebuilt independently by the evaluator, is:

| Actual mechanism / support rule | A1 | A2 | B1 | B2 | C1 | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `dmklinger_row` / unique case + POS + primary candidate row | 34 | 32 | 37 | 53 | 21 | 177 |
| `learner_dmklinger_corrob` / same rule | 11 | 4 | 7 | 0 | 0 | 22 |
| **All retained** | **45** | **36** | **44** | **53** | **21** | **199** |

The independent Claude Opus 5.5 phase must rebuild those paths and inspect 150 fresh retained rows from the 177-row path, all 22 from the small path, and every historical case. It must use source/VESUM/ULIF evidence, proportional level coverage within each path, pre-registered retained seed 20261101 and withholding seed 20261102, with per-path seeds derived deterministically from the path name. A clean author gate or pooled sample is not semantic approval. Missing or inconclusive evidence fails. The fresh 60-row withholding audit is reported without a coverage ceiling. If a path fails, withdraw it or a source-justified failing subclass and perform at most one fresh verification of the reduced artifact; a second failure disables affected meaning surfaces and their dependent exercises.

## Denominator, modes and withholding reasons

| Level | Frozen rows | Retained EN | Retained UK | Withheld | Frozen display changed |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 1,496 | 45 | 0 | 1,451 | 1,460 |
| A2 | 1,511 | 36 | 0 | 1,475 | 1,497 |
| B1 | 1,505 | 44 | 0 | 1,461 | 1,476 |
| B2 | 1,040 | 53 | 0 | 987 | 1,018 |
| C1 | 665 | 21 | 0 | 644 | 652 |
| **Total** | **6,217** | **199** | **0** | **6,018** | **6,103** |

| Level | Flashcards before → after | Matching before → after | Choice before → after | Synonym before → after |
| --- | ---: | ---: | ---: | ---: |
| A1 | 1,496 → 45 | 1,362 → 40 | 1,362 → 40 | 0 → 0 |
| A2 | 1,511 → 36 | 1,340 → 28 | 1,340 → 28 | 0 → 0 |
| B1 | 1,505 → 44 | 652 → 29 | 652 → 29 | 0 → 0 |
| B2 | 1,040 → 53 | 779 → 47 | 779 → 47 | 0 → 0 |
| C1 | 665 → 21 | 511 → 18 | 511 → 18 | 0 → 0 |

Every frozen row had flashcards, so this reason table is the level × flashcard-withholding table. The machine summary additionally gives `modes.<mode>.withheld_reasons` for matching, choice and synonym at each level. Reasons are first-failing rules, not marginal effects.

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

The reproducibility gate checks both display fields on every retained row, their equality, fragment/citation/SUM-11 rejection, Cyrillic and digit exclusion, cross-reference stubs, non-qualifier parentheses, row-specific provenance, no meaning mode or MC eligibility on withheld rows, and preservation of independent modes. It also checks that **all 154 retained A2+ meanings** had English display text in the frozen package. A Cyrillic valency note cannot pass the English-display gate by being stripped. The local run passed these mechanical gates; the semantic gate remains independent.

## Frozen historical denominator

`meaning-9160-history.json` freezes **367 lexeme × failure-condition cases** after deduplication: 65 `reviewed_wrong_sense` cases must remain withheld; 38 named wrong displays must be absent; and 264 source-binding cases must be retained only with row-specific evidence or withheld. The source-binding set is the union of the 26 copied evaluation fixtures, inline containment examples, and named round-1–4 failures and withholding cases. One named phrase is outside the 6,217-row release and remains a direct regression fixture rather than a release-row claim. The manifest records the expected behavior, presence in the frozen package, and observed display for each condition. Only two source-binding cases are retained, each with its row: `зазначати` “to note” (row 1164) and `сірий` “grey” (row 4243). `пора` is now withheld as an unresolved stress homograph, so its historical wrong “pore” display is absent. The case and POS errors, source strings and row IDs are in the committed fixtures; the list is not an admission bypass.

## Round-5 recovery record and named gaps

Authorship is mixed. An OpenAI worker wrote the round-5 row-binding contract, provenance, reproducer gates and case/POS fixtures, and was cancelled before test integration. Claude Opus 5.5 finished the round without adding any admission path. It added the stress-homograph withholding rule above, which withdrew 7 previously retained rows (`пора`, `провідний`, `також`, `іноді`, `ненавидіти`, `хаос`, `послуга`). It rebuilt the focused tests on Atlas fields and `dmklinger_uk_en`/`balla_en_uk` rows copied by script from the frozen databases, corrected the `лікарняний` fixture to carry both of Atlas's translation candidates, and regenerated this artifact. Tests that pinned the retired Balla-bridge, aspect-partner, qualifier-stripping and Ukrainian-gloss admissions now assert the specific fail-closed reason instead.

Named gaps, all assigned to #8977 and none admitted here:

- Atlas POS values such as `noun:m`, `infinitive` and `preposition` do not equal Dmklinger's `noun`, `verb` and `particle`, so those rows cannot bind.
- Stress variants of one lexeme (`водно́час`/`водно́ча́с`, `та́кож`/`тако́ж`) are withheld together with true homographs. An independent stress-to-sense source would be needed to separate them.
- A row whose primary candidate keeps a qualifier or register label (`lion (big cat Panthera leo)`, `(colloquial) to donate`) cannot support a bare Atlas head.
- There is still no separately accessible source for Kaikki, slovnyk.me, curation, Горох, Wikidata or base-form rows.

## Changed shard SHA-256 values

All 55 shard hashes are in `meaning-9160-summary.json`. The 10 changed lexeme/index shards and five copied synonym shards most relevant to meaning exercise eligibility are:

| Shard | SHA-256 |
| --- | --- |
| `practice-index.A1.json` | `8e5bcfd131ccb3e6088c920c6eee6bbf3dc5e118bb84c94ca18da38714ec4b68` |
| `practice-index.A2.json` | `1dcd1cddfd4df1340a592e85db92f41ca75c1c4254998e4aa00d2853a277e255` |
| `practice-index.B1.json` | `86318d266c5ee1aec3be4666d9550f9b765be0491a2f123de63f00c51f3bfaf0` |
| `practice-index.B2.json` | `716acd0cfb6eba91eb7dd6b6aca7b3e8e30e571325fdbfb9ac98eed883269453` |
| `practice-index.C1.json` | `c912f9edce02d1ec9f303b7a553803d68b3efd596d16a126947b491698c43ae2` |
| `practice-lexemes.A1.json` | `822ead6ad2fa49e851aaeacb58217b930587f4c88594dbd05a0e0a6fb4e7d885` |
| `practice-lexemes.A2.json` | `c12cf2368490d478cc7471536061dbfa55cb6588e70e6efea2231f4dd18e8204` |
| `practice-lexemes.B1.json` | `ee16d7c07fc86a71b22853fe9c4fb12c9d53964a91330c7f52d00c64e55b2137` |
| `practice-lexemes.B2.json` | `d1f3b50b4861d44317a97fd6c16dab07e675ffcc7d12a7bd645af7f3388e21f7` |
| `practice-lexemes.C1.json` | `a1922c9f03c2b3653e8dbac0e62b4877b24b4099392bc4ac413c1bf48023926f` |
| `practice-synonym.A1.json` | `a941e7dafa1a0f136ed0f97bd98548a4e3786b34cb727c68cec4bdb092462d7c` |
| `practice-synonym.A2.json` | `9701ccb57d7a20e327ebae341776499883cc3b33cfcf389d9535b24ded5cabad` |
| `practice-synonym.B1.json` | `4745abff6ca1f318c6ea37161f1120ba14134e4b0db0a0a463663701da38494b` |
| `practice-synonym.B2.json` | `e56430a67078cb765380c3e0409e8a29314b2078980306da0e156608e7c55ee5` |
| `practice-synonym.C1.json` | `7beb5a2f9db4445e111fb7bae03579b6532aacd49ed208405b61601a6d30735d` |

This packet stops before PR, release, pointer, production and Pages actions. The driver owns cross-family judgment, same-head CI run IDs, merge/cleanup, regeneration and publication, old-deck invalidation, and live regular/daily flashcard, meaning, Mixed, direct-entry, resume and cache checks. Those delivery paths are **unverified**, so this pushed branch alone does not close #9160. If reduced coverage yields no usable session, the live surface must show explicit unavailability rather than revive a withdrawn meaning.
