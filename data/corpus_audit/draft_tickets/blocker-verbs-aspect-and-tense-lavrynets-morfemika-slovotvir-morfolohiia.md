# Draft — Ingest Сучасна українська літературна мова. Морфеміка. Словотвір. Морфологія for дієслово: вид, час, спосіб

## Why
`Дієслово: вид, час, спосіб` affects 2 audited article(s) and 2 absent-from-corpus concept(s). This draft is for human review only and must not be auto-filed without approval.

## Source provenance
- Author: Олена Лавринець, Катерина Симонова, І. Ярошевич
- Title: Сучасна українська літературна мова. Морфеміка. Словотвір. Морфологія
- Publisher / edition: Києво-Могилянська академія; серія «Могилянський підручник»; 2019
- Provenance: Ukrainian university press textbook with stable commercial acquisition page and full bibliography.
- License / access: commercial / purchasable

## Acquisition method
- Source URL: https://www.yakaboo.ua/ua/suchasna-ukrains-ka-literaturna-mova-morfemika-slovotvir-morfologija.html
- Method: Purchase or library acquisition of the paper textbook, then scan/OCR with manual QA for grammatical paradigms.

## Estimated ingestion size
- Estimated chunk count: ~734 (≈ 524 page(s) × 1.4 chunks/page)

## Schema mapping
- Target table: `textbooks`
- Mapping: Store as a university grammar textbook in `textbooks`; keep the publisher and author metadata, blank `grade`.

## Suggested script reuse
- Starting point: `new print-PDF ingest path with OCR QA`

## Acceptance criteria
- The source is acquired from the listed Ukrainian-only provenance and stored with traceable metadata.
- Text extraction is reproducible and chunked without writing new ad hoc DB tables.
- A smoke query over the ingested chunks surfaces at least one currently missing concept from the target gap category.
- The resulting chunks are added through the existing source-ingest pipeline and appear in `data/sources.db` after rebuild.
