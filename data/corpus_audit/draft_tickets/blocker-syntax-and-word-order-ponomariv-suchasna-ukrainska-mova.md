# Draft — Ingest Сучасна українська мова for синтаксис і порядок слів

## Why
`Синтаксис і порядок слів` affects 1 audited article(s) and 2 absent-from-corpus concept(s). This draft is for human review only and must not be auto-filed without approval.

## Source provenance
- Author: Олександр Пономарів
- Title: Сучасна українська мова
- Publisher / edition: Либідь; 4-те видання; 2008
- Provenance: Ukrainian university textbook with stable commercial metadata and broad grammar/phonetics coverage.
- License / access: commercial / purchasable

## Acquisition method
- Source URL: https://www.yakaboo.ua/ua/suchasna-ukrains-ka-mova-1229246.html
- Method: Purchase or library acquisition of the paper edition; scan with OCR and verify tables/examples manually.

## Estimated ingestion size
- Estimated chunk count: ~627 (≈ 448 page(s) × 1.4 chunks/page)

## Schema mapping
- Target table: `textbooks`
- Mapping: Store as a broad university grammar reference in `textbooks`; preserve the edition in metadata and keep `grade` blank.

## Suggested script reuse
- Starting point: `new print-PDF ingest path with OCR QA`

## Acceptance criteria
- The source is acquired from the listed Ukrainian-only provenance and stored with traceable metadata.
- Text extraction is reproducible and chunked without writing new ad hoc DB tables.
- A smoke query over the ingested chunks surfaces at least one currently missing concept from the target gap category.
- The resulting chunks are added through the existing source-ingest pipeline and appear in `data/sources.db` after rebuild.
