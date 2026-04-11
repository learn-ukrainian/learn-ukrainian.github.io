# RAG Gap — Issue #1026 Status

Last updated: 2026-04-11

## Verified state on disk

| Work | `data/sources.db` | Google Drive `literary_texts/` | `izbornyk/litopys` |
|------|---|---|---|
| Hrushevsky ІУР т.4 | ✅ 606 chunks | ✅ `грушевський-історія-україни-руси-т4.jsonl` | ✅ `/hrushrus/iur4*.htm` |
| Hrushevsky ІУР т.5 | ✅ 683 chunks | ✅ `грушевський-історія-україни-руси-т5.jsonl` | ✅ `/hrushrus/iur5*.htm` |
| **Hrushevsky ІУР т.6** | ❌ | ❌ | ✅ **`/hrushrus/iur601.htm` → Next chain** |
| Orlyk Constitution (Ukrainian) | ❌ | ⚠️ 4 lines — Latin/Russian editorial preface only | ❌ Site has only Latin + letters |
| Izbornyk Svyatoslava | ⚠️ via mentions | ❌ | ⚠️ Excerpts at `/oldukr2/oldukr58.htm` |
| Ostromir Gospel | ❌ | ❌ | ❌ Not on site |
| Peresopnytske Gospel | ❌ | ❌ | ❌ Not on site |
| Perestoroha (1605) | ❌ | ❌ | ❌ Not as standalone page |
| Doroshenko «Нарис історії» | ❌ | ❌ | ❌ Not on site |
| Polonska-Vasilenko «Історія України» | ❌ | ❌ | ❌ Not on site |

Verification done by:
- Grep of `sources.db.literary_texts.source_file` and `.author`
- `find` over Google Drive literary_texts/ (208 subdirs, 205 JSONL files scanned)
- HTTP HEAD + size probe of izbornyk.org.ua index pages (inoldlit, inistor, inlex, inliter, inpolit, inlitop, inmovozn)
- HTTP body inspection of `/hrushrus/iur.htm`, `/rizne/orl.htm`, `/oldukr2/oldukr2.htm`, `/oldukr/oldukr.htm`
- Single-page extraction test of `/hrushrus/iur601.htm` and `/oldukr2/oldukr58.htm` through `scrape_litopys.HTMLTextExtractor` — real Ukrainian text confirmed

## Three groups of missing work

### Group A — covered by existing `batch_scrape_izbornyk.py`

These are now in `WAVE_11_GAP_FILLS`:

1. **Hrushevsky ІУР т.6** — starts at `http://izbornyk.org.ua/hrushrus/iur601.htm`, follows Next chain. Expect ~600-800 chunks based on т4/т5 sizes. Note: start from `iur601.htm`, NOT `iur6.htm` (the latter is just a volume index with no Next link).

2. **Ізборник Святослава 1076 (уривки)** — single page at `http://izbornyk.org.ua/oldukr2/oldukr58.htm`, ~28K chars, no multi-page follow. The site explicitly labels this "уривки" (excerpts) — the full Izbornyk is not digitized here.

Both verified end-to-end: HTML fetch → windows-1251 decode → dop3 div extraction → real Ukrainian text output.

### Group B — needs a different source entirely

| Work | Possible source | Notes |
|------|---|---|
| Orlyk Constitution (Ukrainian) | `uk.wikisource.org` | The Latin original on litopys is historically correct but not useful for Ukrainian learners. Wikisource has modern Ukrainian translations. Use `scripts/rag/scrape_wikisource.py`. |
| Ostromir Gospel | `uk.wikisource.org` / diasporiana facsimile | Probably only ceremonial / museum digitizations exist. May be better to skip for language learning — Old Church Slavonic liturgical text, low pedagogical value outside religious history. |
| Peresopnytske Gospel | `uk.wikisource.org` | Famous 1556-1561 translation. Check Wikisource first. |
| Пересторога (1605) | `uk.wikisource.org` / `biletsky-khrestomatiia` excerpt | We already have excerpts in `wave5-biletsky-khrestomatiia.jsonl`. Full text: try Wikisource. |
| Doroshenko «Нарис історії України» | `diasporiana.org.ua` (PDF) | Diaspora library, PDF-only. Needs PDF→text extraction. |
| Polonska-Vasilenko «Історія України» | `diasporiana.org.ua` (PDF) or `chtyvo.org.ua` | Same. |

### Group C — binary conversion needed

- **Orlyk Diary (Діаріуш)** at `http://izbornyk.org.ua/djvu/orlyk_diariusz.htm` — 2.2MB DJVU file. Would require DJVU→text conversion (e.g. `djvutxt` from djvulibre). Not in scope of the current scraper.

## Action plan for the user

### Step 1 — run Wave 11 scrape (what you can do today)

```bash
# Dry run first to verify URLs
.venv/bin/python scripts/rag/batch_scrape_izbornyk.py --wave 11 --dry-run

# Real run — writes to data/literary_texts/wave11-*.jsonl
.venv/bin/python scripts/rag/batch_scrape_izbornyk.py --wave 11
```

Expected output:
- `data/literary_texts/wave11-hrushevsky-iur-t6.jsonl` (~600-800 chunks)
- `data/literary_texts/wave11-izbornyk-svyatoslava-uryvky.jsonl` (1-5 chunks, single page ~28K chars)

### Step 2 — sync to Google Drive

```bash
GDRIVE="/Users/krisztiankoos/Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com/My Drive/Projects/learn-ukrainian-data"
rsync -av --include='wave11-*.jsonl' --exclude='*' data/literary_texts/ "$GDRIVE/literary_texts/"
```

### Step 3 — rebuild `sources.db` from Google Drive

```bash
.venv/bin/python scripts/wiki/build_sources_db.py
```

This reads every JSONL under `$GDRIVE/literary_texts/` and reingests into the `literary_texts` FTS5 table.

### Step 4 — verify ingestion

```bash
.venv/bin/python -c "
import sqlite3
c = sqlite3.connect('data/sources.db')
for sf in ('wave11-hrushevsky-iur-t6', 'wave11-izbornyk-svyatoslava-uryvky'):
    n = c.execute('SELECT COUNT(*) FROM literary_texts WHERE source_file = ?', (sf,)).fetchone()[0]
    print(f'{sf}: {n} chunks')
"
```

### Step 5 — cleanup the bad Orlyk ingestion

```bash
# Drop the 4-line Latin/Russian garbage ingestion of konstytutsiya-pylypa-orlyka-1710
.venv/bin/python -c "
import sqlite3
c = sqlite3.connect('data/sources.db')
c.execute(\"DELETE FROM literary_texts WHERE source_file = 'конституція-пилипа-орлика-1710'\")
c.commit()
print(f'Deleted {c.total_changes} rows')
"
# Also delete the JSONL on Drive (it's just 4 lines of non-Ukrainian editorial preface)
rm "$GDRIVE/literary_texts/конституція-пилипа-орлика-1710.jsonl"
```

This prevents any agent from citing non-Ukrainian content as a "Ukrainian primary source". The real Orlyk Constitution in Ukrainian needs to come from Wikisource or a translation (follow-up).

### Step 6 — (optional) rename convention

Proposal (see user request): strip the `wave{N}-` prefix from all literary_texts JSONL so filenames self-identify when cited in wiki builds.

**Before:** `wave4-hrushevsky-iur-t1.jsonl`
**After:** `hrushevsky-iur-t1.jsonl`

This requires:
1. Rename files on Google Drive literary_texts/
2. Update any hardcoded filename references in `scripts/wiki/build_sources_db.py` or `scripts/wiki/sources_db.py` (none found in grep, but double-check)
3. Rebuild sources.db so the `source_file` column reflects the new names
4. Update any wiki articles that cite `wave4-...` paths (grep `wiki/` for stale references)

**Not doing this unilaterally** — proposing the rule, user approves, then execute. See "Rename proposal" at bottom.

## Follow-up work for Group B / Group C

Separate tickets or scoped as addenda to #1026:

1. **Wikisource sweep** — run `scripts/rag/scrape_wikisource.py` for: Orlyk Constitution (Ukrainian), Ostromir Gospel, Peresopnytske Gospel, Перестoрога 1605. Needs the existing Wikisource scraper, possibly with per-work `--pages` targets.

2. **Diasporiana PDF pipeline** — write a new `scripts/rag/scrape_diasporiana.py` that:
   - Downloads PDFs from diasporiana.org.ua / chtyvo.org.ua
   - Extracts text via pdftotext / pdfminer
   - Chunks + writes JSONL
   - Targets: Doroshenko «Нарис історії України», Polonska-Vasilenko «Історія України»

3. **DJVU converter** (low priority) — if Orlyk Diary becomes needed for a specific seminar module, add DJVU→text conversion via `djvutxt`. Not otherwise worth the infra.

## Rename proposal (needs user approval)

Current state is inconsistent:
- `wave4-hrushevsky-iur-t1.jsonl` (wave prefix, Latin slug)
- `грушевський-історія-україни-руси-т4.jsonl` (no wave prefix, Ukrainian slug)
- `ukrlib-franko.jsonl` (source prefix, single-word slug)

**Proposal:** unify on `{author-surname-latin}-{work-slug}-{year}.jsonl`

Examples:
- `hrushevsky-iur-t1-1898.jsonl` (from `wave4-hrushevsky-iur-t1.jsonl`)
- `hrushevsky-iur-t4-1905.jsonl` (from `грушевський-історія-україни-руси-т4.jsonl`)
- `izbornyk-svyatoslava-uryvky-1076.jsonl` (from `wave11-izbornyk-svyatoslava-uryvky.jsonl`)
- `franko-collected.jsonl` (from `ukrlib-franko.jsonl`)

Pros: chronological sort by year, consistent Latin slug, no internal "wave" noise exposed to wiki agents.
Cons: changes source_file identifiers in existing sources.db — all existing wiki article citations to old names break and need a migration pass.

Alternative (safer): keep existing filenames, add a `display_name` field to the JSONL metadata that wiki build uses for citations. No rename, no breakage.

**Recommendation:** go with the alternative (add `display_name` metadata) unless there's a strong reason to change filenames.
