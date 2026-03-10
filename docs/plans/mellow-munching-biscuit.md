# Plan: Re-attribute quarantined ukrlib JSONL files

## Context

ukrlib.com.ua has broken author-to-works database mappings for 8 author IDs. The scraper correctly downloaded the texts but stamped them with wrong author metadata. We quarantined 8 JSONL files and deleted 14,843 poisoned chunks from Qdrant (collection now at 117,844 points).

The quarantined files contain **correct literary text with wrong author/work metadata**. We know the real authors from the literary canon (e.g., "Кобзар" = Шевченко, "Енеїда" = Котляревський, "Fata Morgana" = Коцюбинський).

## File disposition

| Quarantined file | Real author | Action | Reason |
|---|---|---|---|
| `ukrlib-kotlyarevsky.jsonl` (1,141) | Шевченко | **DELETE** | Duplicate of `ukrlib-shevchenko.jsonl` |
| `ukrlib-kotsyubynsky.jsonl` (402) | Сковорода | **DELETE** | Duplicate of `ukrlib-skovoroda.jsonl` |
| `ukrlib-vynnychenko.jsonl` (551) | Карпенко-Карий | **DELETE** | Duplicate of `ukrlib-karpenko_karyi.jsonl` |
| `ukrlib-kvitka.jsonl` (1,157) | **Коцюбинський** | REATTRIBUTE | No correct file exists |
| `ukrlib-myrny.jsonl` (313) | **Котляревський** | REATTRIBUTE | No correct file exists |
| `ukrlib-tychyna.jsonl` (1,281) | **Мирний** | REATTRIBUTE | No correct file exists |
| `ukrlib-nechuy.jsonl` (351) | **Тичина** | REATTRIBUTE | No correct file exists |
| `ukrlib-rylsky.jsonl` (4,370) | **Нечуй-Левицький** | REATTRIBUTE | No correct file exists |

**5 files to reattribute, 3 to delete. ~7,472 chunks to fix.**

## Reattribution mapping

```python
REATTRIBUTE = {
    "ukrlib-kvitka.jsonl": {
        "old_author": "Квітка-Основ'яненко Г.",
        "new_author": "Коцюбинський М.",
        "old_prefix": "Григорій Квітка-Основ'яненко",
        "new_prefix": "Михайло Коцюбинський",
        "new_filename": "ukrlib-kotsyubynsky.jsonl",
        "year": 1864,
    },
    "ukrlib-myrny.jsonl": {
        "old_author": "Мирний П.",
        "new_author": "Котляревський І.",
        "old_prefix": "Панас Мирний",
        "new_prefix": "Іван Котляревський",
        "new_filename": "ukrlib-kotlyarevsky.jsonl",
        "year": 1769,
    },
    "ukrlib-tychyna.jsonl": {
        "old_author": "Тичина П.",
        "new_author": "Мирний П.",
        "old_prefix": "Павло Тичина",
        "new_prefix": "Панас Мирний",
        "new_filename": "ukrlib-myrny.jsonl",
        "year": 1849,
    },
    "ukrlib-nechuy.jsonl": {
        "old_author": "Нечуй-Левицький І.",
        "new_author": "Тичина П.",
        "old_prefix": "Іван Нечуй-Левицький",
        "new_prefix": "Павло Тичина",
        "new_filename": "ukrlib-tychyna.jsonl",
        "year": 1891,
    },
    "ukrlib-rylsky.jsonl": {
        "old_author": "Рильський М.",
        "new_author": "Нечуй-Левицький І.",
        "old_prefix": "Максим Рильський",
        "new_prefix": "Іван Нечуй-Левицький",
        "new_filename": "ukrlib-nechuy.jsonl",
        "year": 1838,
    },
}
```

## Implementation

### Step 1: Write `scripts/rag/reattribute_ukrlib.py`

Script that:
1. Reads each quarantined JSONL
2. For each chunk:
   - Replaces `author` field
   - Replaces author prefix in `work` field (e.g., "Панас Мирний. Енеїда" → "Іван Котляревський. Енеїда")
   - Regenerates `chunk_id` (MD5 of new work title) — required because chunk_id includes author name
   - Updates `year` field
3. Writes corrected JSONL to `data/literary_texts/{new_filename}`
4. Does NOT touch Qdrant — ingestion is a separate step

### Step 2: Write `tests/test_reattribute_ukrlib.py`

**Pre-execution tests** (run BEFORE the script, verify the plan is correct):
- `test_quarantined_files_exist` — all 8 files present in `_quarantine/`
- `test_known_works_match_real_author` — spot-check canonical works against expected real authors:
  - "Енеїда" in ukrlib-myrny.jsonl → real author is Котляревський
  - "Fata Morgana" in ukrlib-kvitka.jsonl → real author is Коцюбинський
  - "Хіба ревуть воли" in ukrlib-tychyna.jsonl → real author is Мирний
  - "Арфами, арфами..." in ukrlib-nechuy.jsonl → real author is Тичина
  - "Кайдашева сім'я" in ukrlib-rylsky.jsonl → real author is Нечуй-Левицький
  - "Мартин Боруля" in ukrlib-vynnychenko.jsonl → real author is Карпенко-Карий
  - "Кобзар" in ukrlib-kotlyarevsky.jsonl → real author is Шевченко
  - "Байки Харківські" in ukrlib-kotsyubynsky.jsonl → real author is Сковорода
- `test_duplicates_already_exist` — verify correct files exist for the 3 duplicates
- `test_no_target_file_collision` — the 5 new filenames don't already exist in `data/literary_texts/`

**Post-execution tests** (run AFTER reattribution + ingestion):
- `test_reattributed_files_valid` — each new JSONL has correct author/work fields, valid chunk_ids
- `test_no_cross_contamination` — run `audit_cross_contamination()` on new files
- `test_search_quality` — query Qdrant for known works and verify correct attribution:
  - Search "Коцюбинський Fata Morgana" → result author should be "Коцюбинський М."
  - Search "Котляревський Енеїда" → result should include actual Енеїда text (not just scholarly refs)
  - Search "Мирний Хіба ревуть воли" → result author should be "Мирний П."
  - Search "Тичина Арфами арфами" → result author should be "Тичина П."
  - Search "Нечуй-Левицький Кайдашева сім'я" → result author should be "Нечуй-Левицький І."

### Step 3: Run pre-execution tests

```bash
.venv/bin/python -m pytest tests/test_reattribute_ukrlib.py -k "pre" -v
```

All must pass before proceeding.

### Step 4: Run reattribution script

```bash
.venv/bin/python scripts/rag/reattribute_ukrlib.py
```

Creates 5 new JSONL files in `data/literary_texts/`.

### Step 5: Ingest into Qdrant (~15-20 min)

```bash
.venv/bin/python scripts/rag/ingest.py --literary data/literary_texts/ukrlib-kotsyubynsky.jsonl
.venv/bin/python scripts/rag/ingest.py --literary data/literary_texts/ukrlib-kotlyarevsky.jsonl
.venv/bin/python scripts/rag/ingest.py --literary data/literary_texts/ukrlib-myrny.jsonl
.venv/bin/python scripts/rag/ingest.py --literary data/literary_texts/ukrlib-tychyna.jsonl
.venv/bin/python scripts/rag/ingest.py --literary data/literary_texts/ukrlib-nechuy.jsonl
```

Handles embedding (BGE-M3) automatically during ingestion.

### Step 6: Run post-execution tests

```bash
.venv/bin/python -m pytest tests/test_reattribute_ukrlib.py -k "post" -v
```

### Step 7: Fix scraper config

Blacklist the 8 broken ukrlib IDs in `scripts/rag/scrape_ukrlib.py` so they're never re-scraped:

```python
# BLACKLISTED IDs — ukrlib database serves wrong works for these author pages
BLACKLISTED_IDS = {8, 9, 10, 13, 15, 16, 38, 65}
```

Remove the 8 authors from `P1_AUTHORS` / `P2_AUTHORS` configs. The correct data now comes from reattributed files, not from scraping.

### Step 8: Clean up

- Delete 3 duplicate files from `_quarantine/`
- Delete 5 reattributed source files from `_quarantine/` (originals no longer needed)
- Remove `_quarantine/` directory
- Delete progress markers for the 8 authors from `.ukrlib_progress/`

## Files to create/modify

| File | Action |
|---|---|
| `scripts/rag/reattribute_ukrlib.py` | CREATE — reattribution script |
| `tests/test_reattribute_ukrlib.py` | CREATE — pre/post verification tests |
| `scripts/rag/scrape_ukrlib.py` | MODIFY — blacklist 8 broken IDs |
| `data/literary_texts/ukrlib-kotsyubynsky.jsonl` | CREATE (by script) |
| `data/literary_texts/ukrlib-kotlyarevsky.jsonl` | CREATE (by script) |
| `data/literary_texts/ukrlib-myrny.jsonl` | CREATE (by script) |
| `data/literary_texts/ukrlib-tychyna.jsonl` | CREATE (by script) |
| `data/literary_texts/ukrlib-nechuy.jsonl` | CREATE (by script) |

## Risks

1. **Wrong reattribution mapping** — mitigated by pre-execution tests that verify canonical works (Енеїда = Котляревський, Кобзар = Шевченко, etc.)
2. **Embedding time** — ~15-20 min for 7,472 chunks on MPS (Apple Silicon). Not a risk, just time.
3. **Missing works for Квітка, Рильський, Винниченко** — these 3 authors will still have NO primary text in Qdrant after this fix. Their correct works aren't in any of the quarantined files. This is a known gap, not a regression.
