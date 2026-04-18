# Draft — Ingest Методика навчання української мови в загальноосвітніх закладах for побутові сценарії та лексичні формули

## Why
`Побутові сценарії та лексичні формули` affects 3 audited article(s) and 7 absent-from-corpus concept(s). This draft is for human review only and must not be auto-filed without approval.

## Source provenance
- Author: Вікторія Дороз
- Title: Методика навчання української мови в загальноосвітніх закладах
- Publisher / edition: Центр учбової літератури; навчальний посібник; 2008
- Provenance: Ukrainian pedagogical manual surfaced via current book metadata and library references.
- License / access: commercial / purchasable

## Acquisition method
- Source URL: https://www.yakaboo.ua/ua/metodika-navchannja-ukrains-koi-movi-v-zagal-noosvitnih-zakladah-3350949.html
- Method: Purchase the print edition or source from a library, then scan/OCR with manual cleanup for tabular course outlines.

## Estimated ingestion size
- Estimated chunk count: ~540 (≈ 386 page(s) × 1.4 chunks/page)

## Schema mapping
- Target table: `textbooks`
- Mapping: Store as a pedagogy-methodology book in `textbooks`; use author/title metadata and keep `grade` blank.

## Suggested script reuse
- Starting point: `new print-PDF ingest path with OCR QA`

## Acceptance criteria
- The source is acquired from the listed Ukrainian-only provenance and stored with traceable metadata.
- Text extraction is reproducible and chunked without writing new ad hoc DB tables.
- A smoke query over the ingested chunks surfaces at least one currently missing concept from the target gap category.
- The resulting chunks are added through the existing source-ingest pipeline and appear in `data/sources.db` after rebuild.
