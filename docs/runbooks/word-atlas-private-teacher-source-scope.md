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

Current approval-ledger coverage is 228 reviewed headwords from rows 1-218.
After PR #4208, live Atlas manifest coverage is 208 neutral `teacher_lesson`
provenance refs across 204 Atlas entries from rows 1-198; public browse/search
is regenerated from that manifest. Rows 199-218 are approved for later
controlled browse/search publish; they are not live Atlas output yet. Missing
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

## Full-Source Census Lane

Issue #4160 is now normalized under the full-corpus Atlas intake epic. The next
private teacher-lesson step is a local-only full-source census and candidate
extraction pass, not a public row-window seed. First bind the local source
shape before using an ignored tab/unit. This emits a safe checksum only: no
lemmas, source text, filenames, paths, tab names, or teacher-identifying labels.

```bash
.venv/bin/python -m scripts.audit.private_teacher_lesson_intake \
  /absolute/path/to/local/private-source.docx \
  --print-source-shape
```

Then run the census with the recorded checksum. If the source unit structure
changed, the script aborts before candidate extraction:

```bash
.venv/bin/python -m scripts.audit.private_teacher_lesson_intake \
  /absolute/path/to/local/private-source.docx \
  --ignore-tab-index 3 \
  --expect-source-shape-sha256 <sha256-from-preflight> \
  --format markdown
```

The census output is safe to summarize publicly because it emits counts,
neutral source refs, neutral locators, gate totals, and existing-vs-missing
Atlas counts only. It does not emit lemmas, raw text, filenames, tab names,
document paths, contexts, glosses, or notes. The ignored tab/unit is excluded
before text-block candidate extraction, so it contributes no candidate rows or
gate classifications.

When a local reviewer needs the derived candidate queue, write it outside the
repository:

```bash
.venv/bin/python -m scripts.audit.private_teacher_lesson_intake \
  /absolute/path/to/local/private-source.docx \
  --ignore-tab-index 3 \
  --expect-source-shape-sha256 <sha256-from-preflight> \
  --candidates-out /tmp/atlas-private-teacher-lesson-candidates.json \
  --format markdown
```

The candidate payload contains derived headword metadata and neutral locators
for local review only. Do not commit it, copy it into `docs/`, or paste raw rows
into public issue/PR text. Candidate rows from this lane still need review and a
separate controlled publish step before any live Atlas browse/search movement.

## Bulk Triage Lane

For a large private-source queue, use deterministic bulk triage instead of
manual public row windows. The triage buckets are disjoint and exhaustive:

- `atlas_existing`
- `committed_teacher_inventory`
- `low_signal_hold`
- `post_boundary_table_missing`
- `high_frequency_missing`
- `needs_review_bulk`

Only the bucket counts are safe for public issue/PR updates. Detailed JSON or
Markdown includes derived lemmas and must be written outside the repository:

```bash
.venv/bin/python -m scripts.audit.private_teacher_lesson_intake \
  /absolute/path/to/local/private-source.docx \
  --ignore-tab-index 3 \
  --expect-source-shape-sha256 <sha256-from-preflight> \
  --manifest site/src/data/lexicon-manifest.json \
  --bulk-triage \
  --triage-out /tmp/atlas-private-teacher-lesson-bulk-triage.json \
  --triage-report-out /tmp/atlas-private-teacher-lesson-bulk-triage.md \
  --format markdown
```

The script rejects repository paths for detailed outputs, `.gitignore` ignores
the standard local export filenames, and pre-commit blocks staged JSON/Markdown
that contains the private-source review workflow markers.

## Next Valid #4160 PR Shapes

A safe follow-up PR may do one of these:

- add or harden the full-source local census/extraction tooling
- add reviewed decision-ledger rows from a locally reviewed derived candidate
  queue
- publish already-approved teacher-lesson rows to Atlas browse/search only

Do not mix private-source intake, live Atlas publish, and Daily/Practice/cloze
admission in one PR.
