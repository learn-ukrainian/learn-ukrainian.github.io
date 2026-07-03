# Word Atlas Textbook Source Scope

This note defines the current textbook/headword source scope for Atlas intake.
It answers where the committed textbook words live and what is still missing
before broader textbook ingestion can be treated as resolved.

## Current Textbook Inventories

The committed textbook source-inventory lane currently has 114 rows:

- `data/lexicon/source-inventory/bolshakova-bukvar-keywords.yaml`
  - 40 headwords
  - source notes:
    `docs/l2-uk-direct/textbook-reading-notes/bolshakova-bukvar-mapping.md`
- `data/lexicon/source-inventory/vashulenko-grade3-headwords.yaml`
  - 40 headwords
  - source map: `docs/l2-uk-direct/textbook-map.yaml`
- `data/lexicon/source-inventory/vashulenko-grade3-family-numerals.yaml`
  - 34 headwords
  - source map: `docs/l2-uk-direct/textbook-map.yaml`

These inventory rows cite tracked notes/maps, not untracked source PDFs. The
source PDFs are not committed, so the reviewable repository evidence is the
tracked note/map locator plus each row's context.

## Current Vashulenko Subsets

The Vashulenko Grade 3 inventory is deliberately topic-bounded:

- school vocabulary: 7 rows
- interior vocabulary: 17 rows
- marine vocabulary: 6 rows
- bird vocabulary: 10 rows
- family vocabulary: 9 rows
- numerals: 25 rows

The row locators point into `docs/l2-uk-direct/textbook-map.yaml`, for example
`topic_index.vocabulary_school.words[0]`. Tests resolve those locators back to
the exact lemma so later edits cannot silently drift the inventory away from
the tracked source map.

## Not Yet Done

Issue #3934 remains open because the current 114 rows are only a reviewed seed, not a
complete textbook corpus. The missing work is:

- add more reviewed textbook/headword inventories with tracked source locators
- review held rows before publishing
- publish approved browse/search batches separately from source review
- make separate `surface_admission` decisions for Daily Word, Practice, and
  cloze

Do not infer new rows from private PDFs or broad textbook titles without a
tracked note/map row and reviewed source decision.
