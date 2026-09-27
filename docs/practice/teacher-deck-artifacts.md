# Teacher-table deck artifacts (Dev's example deck)

**Status:** P1 data contract for #8843 (epic #4387). P2 (the practice page) builds against it.
**Generator:** `scripts/lexicon/teacher_deck_shard.py` · **Refresh:** `scripts/lexicon/teacher_deck.py`
**Independent checker:** `scripts/audit/check_teacher_deck.py` (never imports the generator)
**Related:** [curated membership and sources](curated-membership-and-sources.md), the CEFR practice shards (`scripts/audit/generate_practice_deck.py`)

The deck is the teacher's *Combined Master Vocabulary Table (#3)*. Every Ukrainian string in
these files comes from that table, the teacher's lesson texts, `data/atlas.db`, VESUM or a
textbook in `data/sources.db`; items are selected and assembled by rule, never written.

## Refresh

```bash
.venv/bin/python -m scripts.lexicon.teacher_deck refresh --docx "/path/to/master.docx"            # build + check locally
.venv/bin/python -m scripts.lexicon.teacher_deck refresh --docx "/path/to/master.docx" --publish  # after the scan
# or: make teacher-deck-refresh DOCX="/path/to/master.docx"   (runs with --publish)
```

The command ingests the dated lessons into `sources.db` (`private_teacher_lessons_ingest`,
source `private-teacher-lessons-a`; unchanged lessons are skipped, a changed source is replaced
as one unit), syncs the table, builds the deck and cloze, runs the generator gate and the
independent checker, and only then swaps the local published set directory
(`data/lexicon/teacher-deck/`, untracked) in one step and rewrites the committed
`site/src/data/lexicon-teacher-table-deck.json` and `site/src/data/lexicon-teacher-deck-frozen-keys.json`.
With `--publish` it packages the set as `lexicon-teacher-deck-<deckVersion>.json.gz` on the GitHub release
`atlas-teacher-deck` (an existing identical version is verified, not re-uploaded) and rewrites the committed
pointer `site/src/data/lexicon-teacher-deck.pointer.json`. The generated shard and cloze are never
committed: they exceed the repository's 2,000 KB file limit, and the lesson sentences must be scanned
by a person before anything is published. It prints the document and input versions,
added/removed/changed entries (including meaning changes), merges, every teacher-lesson sentence
that is public in the cloze file (`NEW` marks sentences not published before; scan them for
names and private details before committing), and the checker's matrix and residual lists.
Unchanged inputs give byte-identical files (`no-op: artifacts unchanged`).

## Published set (release package, pinned by the pointer)

| File | Schema (`schemaVersion` 1) | Served | Purpose |
| --- | --- | --- | --- |
| `manifest.json` | `atlas-practice-teacher-manifest` | no | deck version, DOCX SHA-256, input versions, per-file bytes/SHA-256/gzip size/budget |
| `frozen-keys.json` | `teacher-table-frozen-keys` | no | frozen denominator: every distinct Ukrainian cell of the table, with the DOCX SHA-256 |
| `practice-deck.teacher.json` | `atlas-practice-teacher-deck` | yes | entries, cards, choice items, grammar items |
| `practice-cloze.teacher.json` | `atlas-practice-teacher-cloze` | yes | cloze items (`cloze[]`, `PracticeClozeItem`-compatible) |
| `coverage.json` | `atlas-practice-teacher-coverage` | no | eligibility counts and residual lists with reasons |

The first sync assigns `firstSeen`; later refreshes read the previous deck from the local set or,
on a fresh machine, from the published asset. `npm run hydrate` runs
`site/scripts/hydrate-teacher-deck.mjs`, which downloads the pinned package, verifies the gzip and
package hashes and every served file (present, SHA-256, schema and version, `deckVersion`,
compressed-size budget), then writes it to `site/public/lexicon/`. A missing pointer, asset or file
fails the build.
Budgets (gzip, level 9): deck 600,000 B, cloze 560,000 B — `TEACHER_*_GZIP_LIMIT` next to the
CEFR budgets in `generate_practice_deck.py`, mirrored in the hydrate script (a test keeps them
equal). The files are fetched only when this deck is selected.

## Entries

One entry per **normalised Ukrainian key**: stress marks removed, apostrophe variants unified
to `'`, whitespace collapsed, case-folded. Capitalisation variants of one word are one entry
(the table's 1,134 distinct cells form 1,125 entries for DOCX `35da757f…`).

| Field | Meaning |
| --- | --- |
| `entryId` | `tt-` + first 12 hex of SHA-256(normalised key). Never depends on row position or English. |
| `key` | normalised key (also the Atlas join key) |
| `uk`, `en` | Ukrainian as written in the earliest row; the teacher's English — all distinct meanings of merged rows joined with `; ` |
| `firstSeen` | integer order key, newest = highest. Carried forward from the previous published deck; new keys get `max + 1, +2, …` in row order. First sync: the earliest row number. |
| `sourceRows`, `sourceKeys` | table rows (1-based data rows) and exact spellings merged into the entry |
| `multiword` | the Ukrainian contains whitespace |
| `atlas` | `null` (no public article or homograph) or `{slug, pos, senseRule, senseIndex, identityConflict}` |
| `conflicts` | ids of entries whose English overlaps (rule below); never grouped with this entry |
| `matching` | may take part in a matching round (group it only with entries not in `conflicts`) |
| `cards` | the card identity contract below |

## Card identity contract

Each entry has at most four FSRS cards, ids `<entryId>:recognition|production|cloze|grammar`.
Presentations are views of the same card and update that card's state.

| Card | Present when | Presentations |
| --- | --- | --- |
| `recognition` | always | UK→EN flashcard (`uk` → `en`); UK→EN meaning choice `cards.recognition.choice` (may be `null` = refused group) |
| `production` | the entry's English overlaps no other entry | EN→UK flashcard (attempt before reveal); EN→UK choice `cards.production.choice` |
| `cloze` | ≥1 cloze item | `cards.cloze.clozeIds` → items in the cloze file (≤3, teacher sentences first; rotate) |
| `grammar` | single-word, Atlas-joined, no identity conflict, and data present | `cards.grammar.items[] = {mode, id}`; `mode` ∈ `stress`, `paradigm`, `classify`, `synonym`, `antonym`; `id` resolves in the deck's `stress[]`, `paradigm[]`, `classify[]` or `synonym[]` array (`synonym[]` holds both polarities) |

Choice items: `{choiceId, direction: "uk-en"|"en-uk", prompt, options[4]: {entryId, label, kind}}`
with exactly one `kind: "answer"`. Options are unique, never equal the prompt, and never include
two entries whose meanings overlap. Matching never updates FSRS state.

Grammar items keep the CEFR shard shapes (`PracticeStressItem`, `PracticeParadigmItem`,
`PracticeClassifyItem`, `PracticeSynonymItem`) plus `entryId`, `cardId` and `atlas: {slug,
senseIndex}`. Level-gated classify sets open at B1 (the deck has no CEFR placement).

Cloze items are `PracticeClozeItem`-compatible (`sentence` with one `___`, `form`, four
`options` with one `answer`) plus `entryId`, `cardId`, `source` (`teacher-lesson` | `textbook`),
`attribution`, optional `clozeEn` (the teacher's English line for a lesson sentence) and
`atlasSense`. The existing Curated Deck (`virtual_teacher_lesson`) also reads this file.

## Rules

- **Overlapping English.** Split `en` on `;` and `,`; lower-case; drop parenthetical text, a
  leading `to ` and the articles a/an/the; collapse spaces. Two entries overlap when a part of one
  equals, or is contained as whole words in, a part of the other. Aspect partners marked only by
  `(impf)`/`(perf)` therefore overlap and get no EN→UK prompt.
- **Atlas senses** are the article's `enrichment.translation.en` glosses. One sense: usable. Several:
  usable only if exactly one shares a content word with the teacher's English. Otherwise synonym /
  antonym items and textbook cloze are withheld and the entry is listed in `senseReview`.
- **Identity conflict** (no grammar modes): more than one public article for the key, or, for a
  single-word entry, a teacher aspect marker that contradicts the Atlas POS or the VESUM aspect.
- **Cloze.** Teacher-lesson sentences are compatible by provenance; textbook sentences need a
  usable Atlas sense. A single word is blanked only where every VESUM reading of the token belongs
  to the entry's lemma; a multiword entry only where the whole phrase occurs verbatim. Distractors
  are other deck entries of the same class with a VESUM form that fills every grammatical slot of
  the answer form, never an entry with overlapping English or an Atlas synonym/antonym of the
  answer; the choice is seeded from the entry id.
- **Synonym/antonym** items come only from approved pairs in
  `registry/lexicon/synonym_pair_verdicts.yaml` whose other lemma is a public Atlas article.

## Checker

```bash
.venv/bin/python scripts/audit/check_teacher_deck.py --deck-dir data/lexicon/teacher-deck \
  --docx "/path/to/master.docx" --expect-keys 1134 --vesum-db data/vesum.db --sources-db data/sources.db
```

It re-extracts the table and re-implements normalisation, ids and the overlap rule, then
enforces the rules above and prints the eligibility matrix and the residual lists (no Atlas
entry, identity conflicts, overlap-omitted EN→UK prompts, refused groups, no-cloze entries).
