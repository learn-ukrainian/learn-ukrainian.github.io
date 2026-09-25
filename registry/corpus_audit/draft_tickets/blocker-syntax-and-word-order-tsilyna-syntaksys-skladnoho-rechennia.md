# Draft — Ingest Сучасна українська літературна мова. Синтаксис складного речення for синтаксис і порядок слів

## Why
`Синтаксис і порядок слів` affects 1 audited article(s) and 2 absent-from-corpus concept(s). This draft is for human review only and must not be auto-filed without approval.

## Source provenance
- Author: Марина Цілина
- Title: Сучасна українська літературна мова. Синтаксис складного речення
- Publisher / edition: Університет "Україна"; навчальний посібник; n.d.
- Provenance: Ukrainian syntax workbook with stable current metadata and focus on complex sentence structures.
- License / access: commercial / purchasable

## Acquisition method
- Source URL: https://www.yakaboo.ua/ua/suchasna-ukrains-ka-literaturna-mova-sintaksis-skladnogo-rechennja.html
- Method: Purchase the print edition or source from a university library; scan/OCR and keep module headings for conjunction and clause types.

## Estimated ingestion size
- Estimated chunk count: ~319 (≈ 228 page(s) × 1.4 chunks/page)

## Schema mapping
- Target table: `textbooks`
- Mapping: Store as a syntax-focused higher-ed manual in `textbooks`; preserve chapter names in `source_file` and leave `grade` blank.

## Suggested script reuse
- Starting point: `new print-PDF ingest path with OCR QA`

## Acceptance criteria
- The source is acquired from the listed Ukrainian-only provenance and stored with traceable metadata.
- Text extraction is reproducible and chunked without writing new ad hoc DB tables.
- A smoke query over the ingested chunks surfaces at least one currently missing concept from the target gap category.
- The resulting chunks are added through the existing source-ingest pipeline and appear in `data/sources.db` after rebuild.
