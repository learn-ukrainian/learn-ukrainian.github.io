# Dictionary Pipeline Status

> What we have, what needs RAG ingestion, what gaps remain.
> Updated: 2026-03-24 (after Phase 2 conversions)

## Ready to ingest (have JSONL + ingestion flag in script)

Run: `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 .venv/bin/python scripts/rag/ingest_style_dictionaries.py --all`

Skips already-ingested collections automatically.

| Dictionary | JSONL file | Entries | Flag | RAG status |
|-----------|-----------|---------|------|------------|
| Антоненко-Давидович | `data/antonenko-davydovych/chunks.jsonl` | 279 | `--antonenko` | ✅ Done (279 pts) |
| Грінченко | `data/grinchenko/chunks.jsonl` | 67,275 | `--grinchenko` | ✅ Done (67,275 pts) |
| СУМ-11 | `data/sum11/chunks.jsonl` | 127,069 | `--sum11` | ❌ Need ingestion |
| Балла EN→UK | `data/balla-en-uk/chunks.jsonl` | 78,704 | `--balla` | ❌ Need ingestion |
| Фразеологічний | `data/frazeolohichnyi/chunks.jsonl` | 24,683 | `--frazeolohichnyi` | ❌ Need ingestion |
| Вікісловник | `data/wiktionary/chunks.jsonl` | 50,278 | `--wiktionary` | ❌ Need ingestion |
| dmklinger UK→EN | `data/dmklinger-uk-en/chunks.jsonl` | 30,111 | `--dmklinger` | ❌ Need ingestion |
| Ukrajinet WordNet | `data/ukrajinet/chunks.jsonl` | 122,441 | `--ukrajinet` | ❌ Need ingestion |

## Local databases (no RAG needed)

| Resource | File | Size | Status |
|---------|------|------|--------|
| VESUM | `data/vesum.db` | 409K lemmas, 6.7M forms | ✅ |
| UberText frequency | `data/ubertext-freq/frequency.db` | 12.4M rows (SQLite) | ✅ |
| PULS CEFR vocab | `data/puls/entries.jsonl` | ~10K words (A1-C1) | ✅ Scraped |
| СУМ-11 registers | `data/sum11/registers.jsonl` | 25,565 labeled words | ✅ |
| Stress dictionary | `ukrainian-word-stress` lib | 2.7M forms | ✅ |
| Heteronyms | `ukrainian-heteronyms-dictionary` lib | ~1K | ✅ |
| Wikipedia cache | `data/wiki_cache.db` | Full UK Wiki | ✅ |

## Already in RAG

| Collection | Points |
|-----------|--------|
| literary_texts | 125,316 |
| textbook_chunks | 23,398 |
| textbook_images | 14,119 |
| grinchenko_dict | 67,275 |
| style_guide | 279 |

## Remaining gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| **Collocations** | Medium (C1+) | No open source exists. Derive from UberText corpus later (PMI extraction). |
| **C2 vocabulary** | Low (last priority) | Derive from UberText freq + literary chunks when we reach C2. |
| **Native formality corpus** | Low | Only translated version on HuggingFace. СУМ-11 registers cover most needs. |

## Ingestion command

```bash
# Ingest all 8 dictionaries (skips already-done ones)
PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 .venv/bin/python scripts/rag/ingest_style_dictionaries.py --all

# Backup to Google Drive
./scripts/backup-data.sh
```

## Literary sources

See `docs/RAG-LITERARY-CATALOG.md` for full inventory (125K chunks, 3257 works).
See `docs/RAG-CONTENT-GAPS.md` for missing primary sources.

Грушевський тт. 4-10 scraped. Конституція Орлика scraped.
