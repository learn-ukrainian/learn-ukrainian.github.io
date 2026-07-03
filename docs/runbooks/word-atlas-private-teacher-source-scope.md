# Word Atlas Private Teacher-Lesson Source Scope

This note defines how private teacher-lesson vocabulary can enter the Word
Atlas source-inventory lane without publishing private lesson material.

## Current Safe Source

The committed inventory seeds are:

- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-seed.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-39-58.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-59-78.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-79-98.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-99-118.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-119-138.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-139-158.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-159-178.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-179-198.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-199-218.yaml`

Current committed coverage is 228 source-inventory headwords from explicit
local vocabulary table rows 1-218. The source family is `teacher_lesson`, and the
source titles, source ids, locators, and context are intentionally privacy-safe.
The inventories do not commit raw notes, transcripts, prompts, document paths,
or teacher-identifying names.

Current approval-ledger coverage is 208 reviewed headwords from rows 1-198.
After PR #4208, live Atlas manifest coverage is 208 neutral `teacher_lesson`
provenance refs across 204 Atlas entries from rows 1-198; public browse/search
is regenerated from that manifest. Rows 199-218 are committed as review-only
source inventory; they are not approved or live Atlas output yet. Missing
`surface_admission` keeps Daily Word, Practice, and cloze frozen.

## Source Handling Rule

Use the ignored local lesson material only as private evidence for deriving
reviewed headword metadata. Committed rows may contain:

- a normalized Ukrainian headword or phrase
- a POS tag
- a short learner-facing English gloss
- a neutral source id and locator such as `explicit vocabulary table row 12`
- a generic context sentence that does not quote private lesson prose

Do not commit raw private source files, private file paths, lesson transcripts,
prompt dumps, screenshots, or teacher-identifying labels.

## Current Boundary

New private teacher-lesson inventory and ledger PRs are review-only until a
separate controlled publish PR updates Atlas browse/search. A review-only seed
or ledger PR does not update:

- live Atlas manifest, search, or browse output
- Daily Word
- Practice decks
- cloze decks
- manifest pointer or fingerprint

Daily Word, Practice, and cloze admission must remain separate
`surface_admission` decisions. Missing `surface_admission` means Atlas
browse/search only after a later publish PR, and no learner-facing activity
admission.

## Next Valid #4160 PR Shapes

A safe follow-up PR may do one of these:

- add the next bounded reviewed private teacher-lesson inventory batch
- add reviewed decision-ledger rows for already committed teacher-lesson
  candidates
- publish an already-approved teacher-lesson batch to Atlas browse/search only

Do not mix private-source intake, live Atlas publish, and Daily/Practice/cloze
admission in one PR.
