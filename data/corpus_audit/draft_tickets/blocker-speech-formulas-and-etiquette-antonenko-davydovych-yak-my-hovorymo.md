# Draft — Ingest Як ми говоримо for мовленнєві формули й етикет

## Why
`Мовленнєві формули й етикет` affects 2 audited article(s) and 5 absent-from-corpus concept(s). This draft is for human review only and must not be auto-filed without approval.

## Source provenance
- Author: Борис Антоненко-Давидович
- Title: Як ми говоримо
- Publisher / edition: Об’єднання Українських Письменників «Слово» / Українське видавництво «Смолоскип» ім. В. Симоненка; Балтиморське видання Diasporiana; 1979
- Provenance: Diasporiana preservation page for a Ukrainian usage and style classic.
- License / access: preservation scan / archive PDF

## Acquisition method
- Source URL: https://diasporiana.org.ua/movoznavstvo/17347-antonenko-davidovich-b-yak-mi-govorimo/
- Method: Download the preserved PDF from Diasporiana; ingest as a style/usage book with OCR fallback only if needed.

## Estimated ingestion size
- Estimated chunk count: ~379 (≈ 271 page(s) × 1.4 chunks/page)

## Schema mapping
- Target table: `textbooks`
- Mapping: Store as a reference usage book in `textbooks`; preserve publisher/author metadata and leave `grade` empty.

## Suggested script reuse
- Starting point: `scripts/rag/scrape_diasporiana.py`

## Acceptance criteria
- The source is acquired from the listed Ukrainian-only provenance and stored with traceable metadata.
- Text extraction is reproducible and chunked without writing new ad hoc DB tables.
- A smoke query over the ingested chunks surfaces at least one currently missing concept from the target gap category.
- The resulting chunks are added through the existing source-ingest pipeline and appear in `data/sources.db` after rebuild.
