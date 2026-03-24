# Dictionary Pipeline Status

> Updated: 2026-03-24 (all dictionaries ingested)

## In RAG ✅

| Collection | Points | Source |
|-----------|--------|--------|
| sum11 | 127,069 | СУМ-11 — Ukrainian explanatory dictionary (11 volumes) |
| ukrajinet | 122,441 | Ukrajinet WordNet — 48K+ synonym groups |
| literary_texts | 125,316 | Literary texts — 3,257 works, 127 authors |
| balla_en_uk | 78,704 | Балла — English→Ukrainian dictionary |
| grinchenko_dict | 67,275 | Грінченко — Historical dictionary (1907) |
| wiktionary_uk | 50,278 | Вікісловник — definitions, synonyms, antonyms |
| dmklinger_uk_en | 30,111 | dmklinger — Ukrainian→English dictionary |
| frazeolohichnyi | 24,683 | Фразеологічний — Ukrainian idioms |
| textbook_chunks | 23,398 | Textbooks — Grades 1-11 |
| textbook_images | 14,119 | Textbook images |
| style_guide | 279 | Антоненко-Давидович — style guide |
| **TOTAL** | **663,673** | |

## Need ingestion

| Dictionary | JSONL | Entries | Command |
|-----------|-------|---------|---------|
| PULS CEFR | `data/puls/entries.jsonl` | ~10K | `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 .venv/bin/python scripts/rag/ingest_style_dictionaries.py --puls` |
| Literary (new) | Грушевський тт.4-10 + Орлика | ~610 chunks | `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 .venv/bin/python scripts/rag/ingest.py --all-literary --batch-size 16` |

## Local databases (no RAG needed)

| Resource | File | Size |
|---------|------|------|
| VESUM | `data/vesum.db` | 409K lemmas, 6.7M forms |
| UberText frequency | `data/ubertext-freq/frequency.db` | 12.4M rows (SQLite) |
| PULS CEFR | `data/puls/entries.jsonl` + `puls_cefr.csv` | ~10K words (A1-C1) |
| СУМ-11 registers | `data/sum11/registers.jsonl` | 25,565 labeled words |
| Stress dictionary | `ukrainian-word-stress` lib | 2.7M forms |
| Wikipedia cache | `data/wiki_cache.db` | Full UK Wiki |

## Remaining gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| Collocations | Medium (C1+) | Derive from UberText corpus later |
| C2 vocabulary | Low (last priority) | Derive from freq + literary chunks |

## Backup

```bash
./scripts/backup-data.sh
```
