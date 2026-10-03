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
  `pohribnyi_notation.json` is **provisional**, with only the plan's starting
  codepoints and a provisional U+02BC softness mark. Secondary stress, length,
  devoicing and the complete softening inventory remain pending. It is not an
  image-verified inventory. Two independent seats must freeze the full table
  from pp. 4–5 before transcription or ingest. Freezing requires clearing all
  provisional flags and pending classes and recording both reviewer identities;
  those fields record a review, and do not prove that the review happened.
  NFC input is required, never silently normalized after offsets are assigned.
  Latin and unlisted symbols inside brackets are refused. NFC composes
  U+045E from Cyrillic U+0443 + U+0306; both the combining starter and its
  NFC letter are represented. Underlining is metadata, never inline markup.

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
  rejects the bundled provisional notation, incomplete declared pages, invalid
  text/underlining and conflicting existing clean rows. It is idempotent for an
  identical packet and never overwrites a conflicting adjudicated row.

  ```bash
  .venv/bin/python -m scripts.ingest.pohribnyi_pronunciation_ingest \
    --adjudicated .cache/final.json --notation .cache/frozen-notation.json \
    --db /path/to/schema-copy.db --dry-run
  ```

  Remove `--dry-run` to ingest into the explicitly selected database. Tests use
  temporary schema copies, never the live corpus. The new chunks retain source,
  page/paragraph locators, underlining, adjudicator and notation SHA-256. Each
  links to a section with page bounds and paragraph locator. The matching OCR
  page and section remain intact with `transcription_status: "superseded"`;
  untouched pages remain unchanged. Inserts, metadata additions and supersession
  roll back together on failure. Callers of `ingest_adjudicated` own commit/rollback.
  `--force` is refused in adjudicated mode; it belongs to the legacy OCR path.
  Retrieval filtering, live ingest, page-image census, inventory freeze,
  transcriptions, adjudication and custody/register updates belong to later #9604
  steps. These tools and synthetic tests do not establish those acceptance criteria.
