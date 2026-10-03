# Ingest Scripts

- `esum_ingest.py`: parse the deployed ЕСУМ DjVu plain-text OCR (`data/raw/esum/vol*.txt`).
- `esum_abbyy_parser.py`: parse Internet Archive ABBYY FineReader XML for ЕСУМ vols. 1, 2, 3, and 6 (`data/raw/esum/ia-abbyy-xml/vol*-abbyy.xml` or `.gz`).
- `verify_stem_coverage.py`: read-only live SQLite census for #4593. Reports all-grade STEM source/chunk counts, each source's grade, observed grade 5–11 absences, and both corpus-wide and STEM grade 5–11 FTS hits. Run from the repository root with an explicit live database path (replace `/path/to/sources.db` below). In a dispatch worktree, use the shared interpreter specified by your worktree contract:

  ```bash
  .venv/bin/python -m scripts.ingest.verify_stem_coverage --db /path/to/sources.db
  ```

  Exit 0 means the census was read, including any gaps; it does not certify curriculum completeness, current editions, or extraction quality. Interpret absent cells against `registry/textbook_curriculum_denominator.yaml` (including integrated alternatives and subject start grades). Use `incremental_textbook_ingest.py` with verified retained chunks for ingestion, then rerun this census. A selected book or retained PDF is not evidence of live SQLite ingestion.

- `pohribnyi_tooling.py` (#9604): render the held, SHA-verified 28-page PDF with
  PyMuPDF at 300 dpi into `.cache/pohribnyi/` (Git-ignored). The manifest records
  page numbers, image dimensions, DPI, renderer and SHA-256 hashes. No OCR or
  transcription is performed. Use the worktree contract's shared interpreter.

  ```bash
  .venv/bin/python -m scripts.ingest.pohribnyi_tooling render --pdf /path/to/held.pdf
  .venv/bin/python -m scripts.ingest.pohribnyi_tooling validate --input .cache/seat-a.json
  .venv/bin/python -m scripts.ingest.pohribnyi_tooling diff \
    --left .cache/seat-a.json --right .cache/seat-b.json --output .cache/diff.json
  ```

  `pohribnyi_notation.schema.json` defines the notation-table schema;
  `pohribnyi_notation.json` is **frozen** under the #9604 comment headed
  “E3c step 2: notation inventory reconciled”. The inventory records the
  GPT-6.1 Sol and Claude Opus 5.5 freeze seats and driver reconciliation,
  short Ukrainian source quotations, page locators, codepoints and Unicode
  properties. The key is on pp. 4–5; additions come from pp. 7–24. Symbols
  without an individual key definition have null quotations and explicit
  separator/encoding provenance. Freeze metadata records the inventory review;
  it does not replace independent exact-head implementation review.

  The approximation letters above a vowel are U+A675 (и), U+2DF7 (е),
  U+A677 (у), U+2DEA (о), and U+1E08F (і). Degree parentheses are U+1ABB
  or U+1ABC; acute/grave stress is U+0301/U+0300. Devoicing uses U+032D,
  slight softening U+0358, the affricate tie U+0361, softness U+02B9,
  half-softness U+02BC, and length U+02D0. Raised off-glides use the seven
  observed Cyrillic Extended-D modifier letters (д, з, ц, ж, ш, ч, т), with
  their own tie and softness. Dialect ы remains a base letter. Space, comma,
  semicolon, compound hyphen U+2010 and separating dash U+2013 are preserved.
  Line-end breaks belong to layout metadata, never a lexical hyphen.

  Require Unicode 15.0 or later and **NFC only**. NFKC/NFKD erase raised-letter
  distinctions and must never be used. Accepted modifier-letter strings may
  differ from their NFKC forms; those forms represent different transcriptions,
  and the diff must retain the disagreement. The canonical order is:
  precomposed base → class 220 devoicing → class 230 approximation, degree,
  stress → class 232 slight softening → class 234 tie → spacing softness,
  length, raised letters (each with its own softness). Intrinsic breve in ў/й
  belongs to the base. NFC does not reorder equal-class marks, so the validator
  enforces the class-230 order separately. See
  [UAX #15](https://www.unicode.org/reports/tr15/).

  `parse_transcription()` derives base, approximation letter, degree, stress,
  devoicing, slight softening, tie, softness, length and raised-group fields;
  separators are separate items. `serialize_transcription()` regenerates the
  identical NFC string, including ў, й, ѐ, ѝ and canonical marked-base
  compositions. The string stays authoritative; the structured view is derived.
  Orphan/duplicate marks, misplaced spacing marks, Latin and unlisted symbols
  inside brackets, and unassigned codepoints are refused. U+02C8, U+00B7,
  U+003A, Latin superscript U+2071 and approximation ї U+A676 are rejected
  alternatives. Underlining is metadata, never inline markup.

  The diff normalizes copies before comparison and remaps underlining offsets;
  boundaries splitting a combining sequence are refused. Ingest never silently
  normalizes text after offsets are assigned. Uncertain source glyphs listed in
  the reconciliation remain withheld; the inventory does not adjudicate tokens.

  Independent transcription files are JSON arrays of paragraph objects with
  `page` (1-based PDF page, 1–28), `paragraph` (1-based within page), `text`, and
  `underlining` (an explicit list, empty when absent). Each underlining interval
  has `start` and `end`, zero-based Unicode-codepoint offsets into the paragraph,
  with the end excluded. Offset ranges must be ordered and non-overlapping.
  The diff lists changed prose, underlining, missing paragraphs and every changed,
  inserted or removed bracketed span with page/paragraph and span offsets.
  Repeated spans are aligned deterministically; alignment is not adjudication.
  Every disagreement starts with null `resolution` and `resolved_by` fields.
  Keep inputs and diff reports in ignored private storage: they contain source text.

- `pohribnyi_pronunciation_ingest.py --adjudicated` appends new paragraph chunks
  to an **existing local** SQLite database. The packet is an object with `rows`
  (the paragraph array) and `paragraph_counts` (string page keys mapped to the
  complete declared paragraph count for each supplied page). Every row must also
  have `status: "adjudicated"` and a nonempty `adjudicated_by` identity. Ingest
  rejects provisional notation overrides, incomplete declared pages, invalid
  text/underlining and conflicting existing clean rows. It is idempotent for an
  identical active packet and never overwrites a conflicting adjudicated row.
  A separate `--census` JSON file maps page strings to independently counted
  paragraph totals from the page images. Every supplied page must match this
  independent count; the packet's own declaration cannot authorize supersession.
  Library callers must likewise pass independent `census_counts`.

  ```bash
  .venv/bin/python -m scripts.ingest.pohribnyi_pronunciation_ingest \
    --adjudicated .cache/final.json \
    --census .cache/page-image-census.json --db /path/to/schema-copy.db --dry-run
  ```

  Replace `--dry-run` with `--apply` to ingest. Both an explicit `--db` and
  `--apply` are required for writes, including legacy OCR mode. Dry-run checks
  the existing target database read-only and requires a retained OCR row for
  each adjudicated page. Tests use
  temporary schema copies, never the live corpus. The new chunks retain source,
  page/paragraph locators, underlining, adjudicator and notation SHA-256. Each
  links to a section with page bounds and paragraph locator. The matching OCR
  page and section, and all prior rows outside the current complete packet on
  that page, remain intact with `transcription_status: "superseded"`. This also
  retires extra paragraphs from an earlier longer packet. Untouched pages remain
  unchanged. Default chunk/section searches and MCP chunk context exclude
  superseded rows; `search_textbooks`, MCP `search_text` and MCP
  `get_chunk_context` accept `include_superseded=True` for explicit historical
  retrieval. Inserts, metadata additions and supersession
  roll back together on failure. Callers of `ingest_adjudicated` own commit/rollback.
  `--force` is refused in adjudicated mode; it belongs to the legacy OCR path.
  Live ingest, page-image census, transcriptions, adjudication and
  custody/register updates belong to later #9604
  steps. These tools and synthetic tests do not establish those acceptance criteria.
