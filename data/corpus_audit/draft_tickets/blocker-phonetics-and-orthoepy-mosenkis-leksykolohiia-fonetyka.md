# Draft — Ingest Сучасна українська літературна мова: Лексикологія. Фонетика for фонетика й орфоепія

## Why
`Фонетика й орфоепія` affects 1 audited article(s) and 1 absent-from-corpus concept(s). This draft is for human review only and must not be auto-filed without approval.

## Source provenance
- Author: Анатолій Мойсієнко та ін.
- Title: Сучасна українська літературна мова: Лексикологія. Фонетика
- Publisher / edition: Знання; підручник; 2010
- Provenance: Chtyvo preservation page with full bibliographic description and downloadable PDF.
- License / access: preservation copy / educational PDF

## Acquisition method
- Source URL: https://chtyvo.org.ua/authors/Mosenkis_Yurii/Suchasna_ukrainska_literaturna_mova_Leksykolohiia_Fonetyka/
- Method: Download the PDF from Chtyvo; ingest directly if the text layer is intact.

## Estimated ingestion size
- Estimated chunk count: ~378 (≈ 270 page(s) × 1.4 chunks/page)

## Schema mapping
- Target table: `textbooks`
- Mapping: Store as a phonetics/lexicology textbook in `textbooks`; keep multi-author metadata in title/author fields.

## Suggested script reuse
- Starting point: `new PDF ingest wrapper or adapted `scripts/rag/scrape_diasporiana.py` text-layer path`

## Acceptance criteria
- The source is acquired from the listed Ukrainian-only provenance and stored with traceable metadata.
- Text extraction is reproducible and chunked without writing new ad hoc DB tables.
- A smoke query over the ingested chunks surfaces at least one currently missing concept from the target gap category.
- The resulting chunks are added through the existing source-ingest pipeline and appear in `data/sources.db` after rebuild.
