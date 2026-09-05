# Incremental STEM textbook ingestion (#4593)

Use the existing downloader, native extractor, and incremental ingester for
the remaining STEM cells. Resolve source pages from
`data/pidruchnyk_urls.yaml` and `docs/l2-uk-direct/textbook-selection.yaml`;
never construct a guessed publisher URL.

## Source choices

| Cell | Selected source_file |
| --- | --- |
| Informatics, grade 5 | `5-klas-informatyka-morze-2022` |
| Informatics, grade 6 | `6-klas-informatyka-bondarenko-2023` |
| Mathematics, grade 6 | `6-klas-matematyka-tarasenkova-2023-1` and `-2` |
| Informatics, grade 7 | `7-klas-informatyka-bondarenko-2024` |
| Biology, grade 7 | `7-klas-biolohiya-sobol-2024` |

The Ryvkind informatics PDFs for grades 5–7 and Zadorozhnyi biology PDF for
grade 7 are downloadable, but their native text fails the existing extraction
coverage floor. Download success alone does not make them ingestible. The
Bondarenko grade 7 pidruchnyk fallback page is already recorded in the selection
file. Both Tarasenkova volumes are required.

Grades 5–6 use integrated natural science in
`data/textbook_curriculum_denominator.yaml` (`g05.natural_5_6_one_of` and
`g06.natural_5_6_one_of`). Preserve those books' `pryroda` subject; do not
relabel them `biolohiya` to fill a census grid. Likewise, separate algebra,
physics, and chemistry begin at grade 7; mathematics is represented by
algebra/geometry in grades 7–9. Census absence is not itself a curriculum gap.

## Acquisition and admission

1. Create a local PDF destination under ignored `data/textbook_chunks/` when
   the operator authorizes local acquisition without the retained store.
2. Use `scripts.crawl.download_textbooks.extract_pdf_links` for pidruchnyk
   pages or `extract_shkola_pdf_links` for Shkola pages. Both require the
   expected author and grade in the fetched title. Download only the returned
   links with `download_pdf` or `download_from_gdrive`. A registry Drive ID
   by itself does not establish the required title guard.
3. Extract each PDF with `scripts/rag/extract_text.py --native-only
   --native-backend pymupdf --output-dir <chunks-root>/grade-NN`. Use the
   project interpreter specified by the dispatch contract. Keep receipts and
   PDFs outside Git.
4. Inspect title/publication pages and held-out content pages. In particular,
   the grade 6 Bondarenko file is watermarked as a publisher project; report
   that provenance limitation. Native formula/table extraction is explicitly
   lossy and must not be presented as faithful mathematical notation.
5. Run `scripts/ingest/incremental_textbook_ingest.py` with explicit `--db`,
   `--chunks-root`, the six source slugs above, and `--dry-run --receipt
   <ignored-receipt-path>`. Admission must retain the author, subject, grade,
   and exactness gates. Do not mark uncertain chunks verified without exact
   page-image evidence.
6. Once the target database is authorized, repeat without `--dry-run`.
   This replaces only the named sources in a transaction, maintains section
   links, and resynchronizes FTS. Never force-rebuild the database.
7. Run `-m scripts.ingest.verify_stem_coverage --db <same-database>` and post
   its full output on #4593, identifying whether it is a live database or a
   worktree copy. Report native-page losses and unresolved cells separately;
   the census proves presence and FTS hits, not full-book fidelity.

Local PDFs and JSONL remain staging material while the bulk root is
unavailable. The corpus owner must preserve them in the canonical retained
store before any future rebuild or dispatch-worktree cleanup. Do not call
local staging durable corpus delivery.
