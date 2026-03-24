# Dictionary Pipeline Status

> What we have, what needs converting to JSONL, what needs RAG ingestion.
> Updated: 2026-03-24

## Phase 1: HAVE JSONL — Need RAG ingestion

Run: `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 .venv/bin/python scripts/rag/ingest_style_dictionaries.py --<flag>`

| Dictionary | JSONL file | Entries | Ingest flag | RAG status |
|-----------|-----------|---------|-------------|------------|
| СУМ-11 | `data/sum11/chunks.jsonl` | 127,069 | `--sum11` | ❌ Not ingested |
| Балла EN→UK | `data/balla-en-uk/chunks.jsonl` | 78,704 | `--balla` | ❌ Not ingested |
| Фразеологічний | `data/frazeolohichnyi/chunks.jsonl` | 24,683 | `--frazeolohichnyi` | ❌ Not ingested |
| Вікісловник | `data/wiktionary/chunks.jsonl` | 50,278 | `--wiktionary` | ❌ Not ingested |

## Phase 2: HAVE raw data — Need JSONL conversion

| Dictionary | Raw file | Entries | Conversion needed |
|-----------|---------|---------|-------------------|
| dmklinger UK→EN | `data/dmklinger-uk-en/words.json` | 30,111 | Parse JSON → JSONL |
| Ukrajinet WordNet | `data/ukrajinet/ukrajinet.xml` | 3,360 synsets | Parse XML → JSONL |
| UberText frequency | `data/ubertext-freq/ubertext_freq.csv.xz` | 12.4M rows | Decompress, import to SQLite |
| PULS CEFR vocab | puls.peremova.org (119 pages) | ~10,000 | **Scrape → JSONL** |
| Ukrainian Formality | HuggingFace `ukr-detect/ukr-formality-dataset-translated-gyafc` | ? | **Download → process** |
| СУМ-11 register labels | `data/sum11/chunks.jsonl` (already have) | 127K | **Extract розм./книжн./заст. tags** |

## Phase 3: Already in RAG ✅

| Dictionary | Collection | Points |
|-----------|-----------|--------|
| Грінченко | `grinchenko_dict` | 67,275 ✅ |
| Антоненко-Давидович | `style_guide` | 279 ✅ |
| Textbooks | `textbook_chunks` | 23,398 ✅ |
| Literary texts | `literary_texts` | 125,316 ✅ |
| Textbook images | `textbook_images` | 14,119 ✅ |

## Phase 4: Already local (no RAG needed)

| Resource | Location | Size |
|---------|----------|------|
| VESUM | `data/vesum.db` (SQLite) | 409K lemmas, 6.7M forms |
| Stress dictionary | `ukrainian-word-stress` lib | 2.7M forms |
| Heteronyms | `ukrainian-heteronyms-dictionary` lib | ~1K |
| Wikipedia cache | `data/wiki_cache.db` | Full UK Wiki |

## Phase 5: GAPS — Need research/acquisition

| Gap | Size needed | Blocking? | Best lead |
|-----|------------|-----------|-----------|
| **Synonyms (large-scale)** | 50K+ groups | B1+ distractors | No open source found. Derive from UberText corpus? |
| **C2 vocabulary list** | ~5K words | C2 track (last priority) | Derive from UberText freq + literary chunks |
| **Collocations** | 50K+ pairs | C1+ naturalness | Derive from UberText corpus (PMI extraction) |
| **Native formality corpus** | 10K+ labeled | C1+ register | Only translated version exists (HuggingFace) |

## Quick commands

```bash
# Ingest all Phase 1 dictionaries (~90 min total)
PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 .venv/bin/python scripts/rag/ingest_style_dictionaries.py --all

# Scrape PULS (Phase 2)
.venv/bin/python scripts/rag/scrape_puls.py

# Scrape Грушевський тт. 4-6 (already have т.4-10 in one file)
# Already done — check data/literary_texts/грушевський-історія-україни-руси-т4.jsonl

# Backup everything to Google Drive
./scripts/backup-data.sh
```
