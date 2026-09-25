# Draft — Ingest Український правопис for фонетика й орфоепія

## Why
`Фонетика й орфоепія` affects 1 audited article(s) and 1 absent-from-corpus concept(s). This draft is for human review only and must not be auto-filed without approval.

## Source provenance
- Author: Українська національна комісія з питань правопису
- Title: Український правопис
- Publisher / edition: Наукова думка / МОН України; нова редакція, офіційний PDF; 2019
- Provenance: Офіційне державне видання, затверджене Кабміном і поширене МОН України.
- License / access: official public PDF

## Acquisition method
- Source URL: https://mon.gov.ua/npa/pro-vprovadzhennya-novoyi-redakciyi-ukrayinskogo-pravopisu
- Method: Direct PDF download from the official MON page; no OCR expected.

## Estimated ingestion size
- Estimated chunk count: ~420 (≈ 300 page(s) × 1.4 chunks/page)

## Schema mapping
- Target table: `textbooks`
- Mapping: Map as a reference grammar volume in `textbooks` with blank grade and author/publisher metadata preserved in `source_file`.

## Suggested script reuse
- Starting point: `new PDF ingest wrapper or adapted `scripts/rag/scrape_diasporiana.py` text-layer path`

## Acceptance criteria
- The source is acquired from the listed Ukrainian-only provenance and stored with traceable metadata.
- Text extraction is reproducible and chunked without writing new ad hoc DB tables.
- A smoke query over the ingested chunks surfaces at least one currently missing concept from the target gap category.
- The resulting chunks are added through the existing source-ingest pipeline and appear in `data/sources.db` after rebuild.
