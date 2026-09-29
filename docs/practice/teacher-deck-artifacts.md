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
.venv/bin/python -m scripts.lexicon.teacher_deck refresh --docx "/path/to/master.docx" --publish  # after the review queue is empty
# or: make teacher-deck-refresh DOCX="/path/to/master.docx"   (runs with --publish)
```

The command ingests the dated lessons into `sources.db` (`private_teacher_lessons_ingest`,
source `private-teacher-lessons-a`; unchanged lessons are skipped, a changed source is replaced
as one unit), syncs the table, builds the deck and cloze, runs the generator gate and the
independent checker. `--publish` is refused (exit 1, nothing replaced or uploaded) while any served
teacher-lesson sentence has no record in the review ledger; run without it to write the review queue.
With `--publish` the independent checker also runs in publication mode (`--publication`): it derives
every served lesson sentence from the built cloze file itself and fails on any without a `kept` record.
With `--publish` it then creates the GitHub release `atlas-teacher-deck` if it
does not exist yet and uploads the set as `lexicon-teacher-deck-<deckVersion>.json.gz` (an existing
identical version is verified, not re-uploaded). Only when every step succeeded does it write its
outputs as one generation, all together or not at all: the local published set directory
(`data/lexicon/teacher-deck/`, untracked), the committed `site/src/data/lexicon-teacher-table-deck.json`,
`site/src/data/lexicon-teacher-deck-frozen-keys.json` and, with `--publish`, the pointer
`site/src/data/lexicon-teacher-deck.pointer.json`. A journal (`data/lexicon/.teacher-deck.journal`,
`pending`) naming every target is written first; the new files are staged, the old ones kept as
`.<name>.previous`, the directory is swapped and each file replaced; marking the journal `committed`
is the single commit point, after which the backups and the journal are removed. A raised error rolls
back through the journal at once; a killed process leaves the journal behind, and the next refresh
starts by restoring the complete previous generation (`pending`) or finishing the cleanup
(`committed`) — never a new deck with an old pointer. The review ledger is written only by
`record-review`. A failed checker, build or upload leaves every output untouched (a versioned asset
uploaded before a later failure is harmless: nothing points to it). The generated shard and cloze are never
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

The refresh also writes `lesson-sentence-review.json` (`teacher-lesson-sentence-review`) next to these
files: the **language-review queue**. It is a local artifact only — never in the manifest, the package
or the release. It lists every *served* teacher-lesson cloze item whose sentence has no record in the
review ledger yet (below), one row per item (cloze id, entry, sentence, `sentenceSha256`, lesson date),
with its counts against all served lesson items and deterministic flags —
`proper_noun_tokens` (capitalised tokens not at the sentence start, and tokens VESUM tags
`prop`/`fname`/`lname`/`pname`), `vesum_unknown_tokens` (tokens unknown to VESUM's normative `forms`
view, so forms marked `bad`/`obsc`/`subst` count as unknown) and `digits_or_contact` (digits, emails,
phone- or URL-like strings). Lesson logs can hold the learner's own attempts; the language review and
the privacy scan decide. `--publish` refuses while the queue is not empty.

### Lesson-sentence screening and the review ledger

Lesson sentences pass two gates **before** up to three are selected per entry, so a screened-out
sentence can be replaced by the next candidate:

1. **Fragment rules** (deterministic, re-implemented by the checker) reject worksheet debris: the
   outline arrow `→`; slash alternatives between words (`слово/слово`); a parenthesis holding a
   number or an all-lowercase gloss/hint, or left unclosed (`(11)`, `(365) триста`, `(ходити)`,
   `(хронічна втома)`; capitalised or punctuated asides stay); a copied citation marker (`[5]`); a leading section label of up to three
   words ending in `:` (`Версія СБУ:`); a worksheet task verb at the start (`Визначте`, `Поясніть`,
   `Запишіть`, `Використайте`, …); a truncated abbreviation at the end (`ім.`, `м.`, `чол.`, …).
   The rules are deliberately conservative: a few natural `X: …` sentences are dropped too.
2. **Review ledger** `site/src/data/lexicon-teacher-deck-withheld.json`
   (`atlas-practice-teacher-withheld`, committed): `withheld[]` records
   `{sentenceSha256, code, reviewer, reviewedAt}` with `code` `ERR` (incorrect Ukrainian), `AMBIG`
   (more than one option fits), `FRAG` (not a usable sentence) or `PRIV` (private detail), and
   `kept[]` records `{sentenceSha256, reviewer, reviewedAt}` for sentences reviewed and accepted.
   `sentenceSha256` is the SHA-256 of the NFC-normalised sentence with whitespace collapsed; the file
   never holds sentence text. Withheld sentences are never served (from lessons or textbooks); kept
   ones leave the review queue. Record a review result with:

```bash
.venv/bin/python -m scripts.lexicon.teacher_deck record-review --queue data/lexicon/teacher-deck/lesson-sentence-review.json \
  --cloze data/lexicon/teacher-deck/practice-cloze.teacher.json --results /tmp/withheld.tsv \
  --reviewer "<model> (<task id>)" --reviewed-at YYYY-MM-DD [--positions 0-774]
```

`--results` is `clozeId<TAB>code` per withheld item; every queue item in `--positions` that is not
listed is recorded as kept. One sentence withheld under several codes keeps the gravest
(`PRIV` > `ERR` > `AMBIG` > `FRAG`); a withheld record is never downgraded to kept. The refresh prints
how many lesson sentences each fragment rule and each withheld code screened out.

The first sync assigns `firstSeen`; later refreshes read the previous deck from the local set or,
on a fresh machine, from the published asset. `npm run hydrate` runs
`site/scripts/hydrate-teacher-deck.mjs`, which downloads the pinned package, verifies the gzip and
package hashes and every served file (present, SHA-256, schema and version, `deckVersion`,
compressed-size budget), then writes it to `site/public/lexicon/`. The pointer is required: without
it `npm run hydrate` and `npm run verify:artifacts` fail with `teacher deck pointer missing: …` and the
publish command, so the site never builds without the teacher deck. Both fail closed:
`verify:artifacts` checks the pointer itself (asset URL
= the pinned release asset for its `deck_version`, SHA-256 digests, served-file schemas and versions,
the cloze file record, recorded gzip size within budget) and hydrate additionally re-verifies the
downloaded package and every served file.
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
| `uk` | Ukrainian as written in the earliest row |
| `teacherEn` | the teacher's English verbatim — all distinct meanings of merged rows joined with `; ` |
| `en` | learner-facing English: `teacherEn` with the teacher's aspect markers removed (a meaning that becomes a duplicate is dropped) and, for a verb with a known aspect, the source label appended: `(impf.)`, `(pf.)` or `(impf./pf.)` |
| `aspect` | `null` for non-verb entries, else `{value, basis, lemma, vesum, ulif, teacherMarker, markerAgrees}` (rule below) |
| `firstSeen` | integer order key, newest = highest. Carried forward from the previous published deck; new keys get `max + 1, +2, …` in row order. First sync: the earliest row number. |
| `sourceRows`, `sourceKeys` | table rows (1-based data rows) and exact spellings merged into the entry |
| `multiword` | the Ukrainian contains whitespace |
| `atlas` | `null` (no public article or homograph) or `{slug, pos, senseRule, senseIndex, identityConflict}` |
| `conflicts` | ids of entries whose English overlaps (rule below); never grouped with this entry |
| `aspectPartners` | ids of entries with otherwise identical English and the opposite source aspect; not an overlap, but never a cloze or synonym distractor (both forms can fit one sentence) |
| `matching` | may take part in a matching round (group it only with entries not in `conflicts`) |
| `cards` | the card identity contract below |

## Card identity contract

Each entry has at most four FSRS cards, ids `<entryId>:recognition|production|cloze|grammar`.
Presentations are views of the same card and update that card's state.

| Card | Present when | Presentations |
| --- | --- | --- |
| `recognition` | always | UK→EN flashcard (`uk` → `en`); UK→EN meaning choice `cards.recognition.choice` (may be `null` = refused group) |
| `production` | the entry's English overlaps no other entry (aspect partners are not overlaps) | EN→UK flashcard (attempt before reveal, prompt `en` with its aspect label); EN→UK choice `cards.production.choice` |
| `cloze` | ≥1 cloze item | `cards.cloze.clozeIds` → items in the cloze file (≤3, teacher sentences first; rotate) |
| `grammar` | single-word, Atlas-joined, no identity conflict, and data present; a `classify` aspect set only when it equals the source aspect | `cards.grammar.items[] = {mode, id}`; `mode` ∈ `stress`, `paradigm`, `classify`, `synonym`, `antonym`; `id` resolves in the deck's `stress[]`, `paradigm[]`, `classify[]` or `synonym[]` array (`synonym[]` holds both polarities) |

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

## Practice page (P2)

`site/src/components/practice/TeacherDeckPractice.tsx` renders the deck when it is selected on
`/practice/`; `LexiconPractice.tsx` switches to it because the special set carries a `practice`
config (`getArtifactPracticeDeck` in `site/src/lib/lexicon/custom-decks.ts`: file names, default
10 new words and 100 reviews per day). It fetches the two served files only then
(`site/src/lib/lexicon/teacher-deck.ts` validates schema, deck id and matching `deckVersion`);
a failed fetch shows an error with retry — there is no CEFR-shard fallback. Scheduling lives in
`site/src/lib/lexicon/teacher-deck-srs.ts`:

- **Store** `localStorage["lu-deck-progress:<deckId>"]` (never the CEFR store): settings, the
  introduced set by entry id, FSRS state by card id, the review log (last 3,000 records; today's
  are never dropped) and today's queue. FSRS parameters are the learner's practice settings.
- **Day plan** (local midnight): due cards first, capped by the review cap (distinct cards
  reviewed today as scheduled reviews count against it), then unseen entries by highest
  `firstSeen`, up to new words per day (distinct entries first introduced today). A failed card
  in a learning step comes back later the same day as a repeat, outside both limits.
- **Unlock**: the first recognition rating other than *again* creates the entry's production,
  cloze and grammar cards (those the loaded deck can serve), due the next local midnight.
- **Presentations** rotate with the card's review count: recognition/production alternate
  flashcard and choice (a first exposure is the flashcard; EN→UK needs a typed attempt or
  "I don't know" before the answer shows); cloze rotates its sentences; grammar rotates its modes,
  then items and classify sets. Objective items rate *good* when right, *again* when wrong.
  Matching rounds use introduced entries, never group `conflicts`, and never touch FSRS.
- **Continuity**: each answer is read-apply-written at once and applied at most once (the queue
  slot id is the review id). The saved queue is restored only on the same local day; its pending
  slots are dropped when the entry, card or shown content changed (a fingerprint per slot) or the
  card is no longer due, then the plan is topped up. A new day rebuilds the queue.
- **Migration** (once): an entry whose Atlas slug, key or table spelling has state in the CEFR
  store (`lu-lexicon-srs`) counts as introduced (not against today's allowance); its most recent
  flashcards/choice/matching state becomes the recognition card. The CEFR store is only read.

## Rules

- **Verb aspect comes from the sources, never from the teacher's markers** (operator 2026-09-27).
  Lookups: VESUM `forms_all` rows whose `lemma` is the word (verb rows give `imperf`/`perf` tags) and
  `sources.db` `ulif_dictua_entries` rows with `homonym_checked = 1` (`дієслово недоконаного виду` =
  imperf, `дієслово доконаного виду` = perf, `дієслово недоконаного і доконаного виду` = dual). A
  single-word entry looks up its key; a phrase looks up its first token the sources know as a verb
  lemma (its governing verb, `aspect.lemma`). A spelling that is also a non-verb lemma counts as the
  verb only when the teacher's English is a verb meaning (all meanings start with `to ` or carry a
  marker); a verb meaning no source knows as a verb (an unknown spelling, or one attested only as a
  non-verb) gets `unknown` (basis `none`). Resolution (`basis`): both
  sources name the same aspect → `agree`; only one source knows the lemma → `vesum-only` /
  `ulif-only`; they disagree → `unknown` (`conflict`). VESUM lists a biaspectual verb as two lemmas
  (imperf + perf), exactly like two homograph verbs, so VESUM imperf+perf with ULIF dual → `dual`
  (`agree`); with ULIF naming both aspects on separate homonyms → `unknown` (`homograph`); VESUM
  imperf+perf alone → `unknown`. `markerAgrees` compares the teacher's `(impf)`/`(perf)` with the
  result (`null` when there is no marker or the aspect is unknown); a disagreement is only reported
  (`aspectMarkerDisagreements`), it never stops the entry or drops its grammar modes.
- **Overlapping English.** Split `en` on `;` and `,`; lower-case; drop parenthetical text (so the
  aspect label), a leading `to ` and the articles a/an/the; collapse spaces. Two entries overlap when
  a part of one equals, or is contained as whole words in, a part of the other — except when their
  normalised parts are identical and their source aspects are imperf vs perf: those are aspect
  partners, and each gets an EN→UK card whose prompt shows its label. Pairs with a `dual`/`unknown`
  aspect or a merely contained meaning still overlap.
- **Atlas senses** are the article's `enrichment.translation.en` glosses. One sense: usable. Several:
  usable only if exactly one shares a content word with the teacher's English. Otherwise synonym /
  antonym items and textbook cloze are withheld and the entry is listed in `senseReview`.
- **Identity conflict** (no grammar modes): more than one public article for the key, or a single
  word the sources know as a verb whose Atlas article is not a verb.
- **Cloze.** Teacher-lesson sentences are compatible by provenance; textbook sentences need a
  usable Atlas sense. A single word is blanked only where every VESUM reading of the token belongs
  to the entry's lemma; a multiword entry only where the whole phrase occurs verbatim. Distractors
  are other deck entries of the same class with a VESUM form that fills every grammatical slot of
  the answer form, never an entry with overlapping English, an aspect partner or an Atlas
  synonym/antonym of the answer; the choice is seeded from the entry id.
- **Synonym/antonym** items come only from approved pairs in
  `registry/lexicon/synonym_pair_verdicts.yaml` whose other lemma is a public Atlas article.

## Checker

```bash
.venv/bin/python scripts/audit/check_teacher_deck.py --deck-dir data/lexicon/teacher-deck \
  --docx "/path/to/master.docx" --expect-keys 1134 --vesum-db data/vesum.db --sources-db data/sources.db \
  --atlas-db data/atlas.db --withheld site/src/data/lexicon-teacher-deck-withheld.json --publication
```

It re-extracts the table and re-implements normalisation, ids, the VESUM/ULIF aspect lookup (with
`--vesum-db` and `--sources-db`; otherwise the declared aspect is used and the output says so), the
learner-facing English and the overlap rule; with `--atlas-db` (read-only) the Atlas join, the
mechanical sense rule (including "textbook sentences only with a usable sense") and the identity
conflicts; with `--vesum-db` the same-slot distractor rule (every single-word distractor is a VESUM
form of its own entry filling every slot of the blank's form, never a form of the answer); the
lesson-sentence fragment rules; and with `--withheld` that no withheld sentence is served and that the
ledger carries hashes only; with `--publication` (needs `--withheld`; `refresh --publish` passes it)
also that every served teacher-lesson sentence has a `kept` record. It then enforces the rules above and prints the aspect
counts, the number of entries without an EN→UK card, the eligibility matrix and the residual lists
(no Atlas entry, identity conflicts, overlap-omitted EN→UK prompts, refused groups, no-cloze
entries, unknown aspects, teacher markers that disagree with the sources).
