# Draft — Ingest Крок 1. Українська мова як іноземна. Книга для студента for побутові сценарії та лексичні формули

## Why
`Побутові сценарії та лексичні формули` affects 3 audited article(s) and 7 absent-from-corpus concept(s). This draft is for human review only and must not be auto-filed without approval.

## Source provenance
- Author: Олеся Палінська, Оксана Туркевич
- Title: Крок 1. Українська мова як іноземна. Книга для студента
- Publisher / edition: Видавництво Львівської політехніки / МІОК; 2-ге видання, рівень A1-A2; 2014
- Provenance: Ukrainian-for-foreigners textbook series from МІОК / Львівська політехніка with stable current acquisition pages.
- License / access: commercial / purchasable

## Acquisition method
- Source URL: https://www.yakaboo.ua/ua/krok-1-ukrains-ka-mova-jak-inozemna-kniga-dlja-studenta-cd-rom.html
- Method: Purchase the current student book or source it from a university library; scan/OCR the print pages and preserve lesson/dialogue metadata.

## Estimated ingestion size
- Estimated chunk count: ~146 (≈ 104 page(s) × 1.4 chunks/page)

## Schema mapping
- Target table: `textbooks`
- Mapping: Store as a Ukrainian-as-a-foreign-language coursebook in `textbooks`; preserve lesson titles in `source_file` and leave `grade` blank.

## Suggested script reuse
- Starting point: `new print-PDF ingest path with OCR QA`

## Acceptance criteria
- The source is acquired from the listed Ukrainian-only provenance and stored with traceable metadata.
- Text extraction is reproducible and chunked without writing new ad hoc DB tables.
- A smoke query over the ingested chunks surfaces at least one currently missing concept from the target gap category.
- The resulting chunks are added through the existing source-ingest pipeline and appear in `data/sources.db` after rebuild.
