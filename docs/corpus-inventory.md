# Corpus Inventory — what's actually in our data

> **Read this when you need to know what source material we have** (for writing, review,
> verify_quote, RAG grounding, or deciding whether to scrape something new). Sessions
> kept re-discovering the corpus from scratch — this doc is the durable, current answer.
>
> **Last refreshed: 2026-07-10** (by querying `data/sources.db` directly — see
> [§ Refreshing this doc](#refreshing-this-doc)). When the corpus grows, update this file
> AND `docs/best-practices/v7-design-and-corpus.md` §2 (the #M-11 SSOT cross-links here).

---

## TL;DR

- The live store is **`data/sources.db`** — a **1.6 GB SQLite + FTS5** database. The MCP
  `sources` server (port 8766) reads it; every `mcp__sources__*` tool, `verify_quote`,
  `search_literary`, etc. hit this file.
- It holds **~137.7K literary chunks + 50.9K textbook chunks + ~1M dictionary rows +
  22.4K wiki + Wikipedia** across ~27 content/dictionary tables.
- It is **BUILT from a Google Drive mount**, not local `data/`. That split is the #1
  gotcha — see [§ Architecture](#architecture).
- **What we have a LOT of:** chronicles (litopys/izbornyk), Грушевський, encyclopedias,
  authored literature (Франко/Нечуй/Гончар/Шевченко…), and dictionaries (СУМ-11, Грінченко,
  ЕСУМ, ukrajinet WordNet, Балла).
- **What's thin:** anonymous **folk genre primaries** (думи/колядки/щедрівки as verbatim
  texts) — only ~35 `narod` chunks (added 2026-06-15, #3193); the rich folk material is
  *embedded inside* scholarly works (Грушевський, Драгоманов, Костомаров, ЕУ), not standalone.

---

## Architecture — where the data lives (the #1 gotcha)

```
  scrapers (scrape_ukrlib.py, scrape_litopys.py, …)
        │ write jsonl →  data/literary_texts/        ← LOCAL repo (data/ is gitignored)
        │
        ▼
  build_sources_db.py  (scripts/wiki/)
        │ reads literary + textbooks ← GDRIVE_DATA  ←  Google Drive mount, NOT local data/!
        │ reads external             ← data/external_articles/  (local)
        ▼
  data/sources.db  (1.6 GB SQLite + FTS5)  ←  what the MCP `sources` server serves
```

- **`GDRIVE_DATA`** = `~/Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com/My Drive/Projects/learn-ukrainian-data`
  (228 `literary_texts/*.jsonl` ≈ 137.7K chunks + `textbook_chunks/grade-*/`). This is the
  rebuild source of record.
- **⚠️ DIR MISMATCH:** scrapers write to LOCAL `data/literary_texts/`, but `build_sources_db.py`
  reads literary from **`GDRIVE_DATA/literary_texts/`**. A freshly-scraped jsonl in `data/`
  is **invisible** to a `--force` rebuild until it's also placed on the GDrive mount.
- **`build_sources_db.py --force`** does a **FULL destroy + rebuild** of `sources.db` from
  GDrive. It is **destructive**; only safe when the GDrive mount is fully present (it is, as of
  2026-06-15: 137,688 literary + 11 textbook grades). **`--dry-run` does NOT preview** on a
  populated DB — it short-circuits to the same "refuse without --force" message.
- The FTS tables (`literary_fts`, `textbooks_fts`, …) are **external-content FTS5** with only
  an `AFTER INSERT` trigger — no delete/update trigger. After any delete/bulk change, resync with
  `INSERT INTO <name>_fts(<name>_fts) VALUES('rebuild')`.

### Safe recipe to ADD literary content (no destructive rebuild)
Used 2026-06-15 to land the expanded folk corpus (#3193) without a `--force`:
1. Scrape → `data/literary_texts/<source>.jsonl`.
2. **Copy the jsonl to `GDRIVE_DATA/literary_texts/`** (so a future `--force` keeps it).
3. **Incremental-insert** into the live `data/sources.db` in one transaction: back up the DB,
   `DELETE FROM literary_texts WHERE source_file=<src>`, insert rows via
   `scripts/wiki/sources.py::build_literary_row`, then `literary_fts('rebuild')`, commit.
4. Verify via the MCP: `mcp__sources__search_literary` / `verify_quote`.

### Reclaiming local disk — symlink a Drive-duplicated file (no data loss)
Much of `data/` is **already copied to the Drive mount but never deleted locally**, so the local
copy is pure duplication (~2.4 GB as of 2026-07-16: `ubertext-freq` 1.2 GB, `embeddings` 597 MB,
`raw` 305 MB, `native-reviewer-lessons` 254 MB, `literary_texts` 36 MB — all confirmed present on
`GDRIVE_DATA`). To reclaim the space without breaking builds that read the **local** path (the
dir-mismatch gotcha above), replace the local file with a **symlink to the streamed Drive copy** —
it takes 0 local bytes when idle and materializes on demand. Recipe (used 2026-07-16 for
`ubertext-freq/frequency.db`, 1.2 GB):
1. **Confirm identical:** `ls -la` byte-size of `data/<x>` == `GDRIVE_DATA/<x>` (same size + mtime).
2. **Confirm valid + mount healthy:** e.g. `head -c 16` of a SQLite file reads `SQLite format 3`.
3. **Confirm nothing has it open:** `lsof data/<x>` is empty.
4. `rm data/<x>` then `ln -s "$GDRIVE_DATA/<x>" data/<x>`.
5. **Functional test (mandatory):** actually open/read it through the symlink (e.g.
   `sqlite3` a `SELECT`), proving the reader still works before declaring done.

**Caveats:** (a) do NOT symlink files a **runtime server** reads hot — `embeddings/` may back the
MCP dense reranker; confirm it is not runtime-critical first. (b) A regenerating writer (e.g.
`convert_phase2.py` rebuilds `frequency.db` from `ubertext_freq.csv.xz`) will write **through** the
symlink to Drive; delete the symlink first if you want a fresh local rebuild.

**Never symlink these — runtime-essential, must stay local:** `sources.db` (MCP `sources` server),
`vesum.db`, `mphdict/`, `lexicon/`.

---

## Table inventory (`data/sources.db`, 2026-07-10)

### Content corpora
| Table | Rows | MCP tool | What it is |
|---|---:|---|---|
| `literary_texts` / `literary_fts` | **137,723** | `search_literary` | Primary sources: chronicles, encyclopedias, authored literature, scholarly works, **folk primaries (35)**. See [breakdown](#literary_texts-breakdown). |
| `textbooks` / `textbooks_fts` | **50,933** (168 `source_file`s) | `search_text` | School textbooks, grades 1–11 (Заболотний, Авраменко, Большакова, Вашуленко…), plus **8 private ULP/Ohoiko refs** — see [§ Private reference sources](#private-reference-sources-textbooks). |
| `textbook_sections` | 7,250 | (internal) | Section hierarchy for textbook chunks. |
| `zno_documents` | **33** | (direct SQL) | ZNO/NMT booklet metadata (2010–2025, Ukrainian language). Ingest: `scripts/ingest/zno_ingest.py`. |
| `zno_tasks` / `zno_tasks_fts` | **366** | (direct SQL) | Parsed ZNO tasks from zno.osvita.ua; FTS on `stem`, `options_json`, `topic_tag`. **2019–2021** task coverage: 116 / 116 / 134. Consumer: #4506 paronym/stress worksheets. |
| `ukrainian_wiki` / `_fts` | 22,385 | `search_sources` | Our OWN compiled wiki pedagogy (`wiki/**`), keyed by article slug + track. |
| `external_articles` / `external_fts` | 1,205 | `search_external` | Curated external articles + YouTube/blog transcripts (register/decolonization tagged). |
| `wikipedia` / `_fts` | 1,026 | `query_wikipedia` | Cached Ukrainian Wikipedia articles (+ `wikipedia_negative_cache` 243). |

### Dictionaries & lexical resources
| Table | Rows | MCP tool | What it is |
|---|---:|---|---|
| `sum11` | 127,069 | `search_definitions` | СУМ-11 explanatory dict. ⚠ partly Sovietized (~5.6% flagged; each row carries `sovietization_risk`). |
| `esum_cognate_forms` | 134,836 | `search_esum` | ЕСУМ cognate/related forms. |
| `esum_etymology` | 36,177 | `search_esum` | ЕСУМ etymology (vols 1–6, А–Я). |
| `ukrajinet` | 122,441 | `search_synonyms` | Ukrajinet WordNet synsets (⚠ largely auto-translated from English WordNet). |
| `balla_en_uk` | 78,704 | `translate_en_uk` | Балла EN→UK translations. |
| `grinchenko` | 67,275 | `search_grinchenko_1907` | Грінченко 1907 historical dict (pre-Soviet attestation). |
| `wiktionary` | 50,278 | (via `search_sources`) | Wiktionary entries (+ `wiktionary_etymology` 4). |
| `dmklinger_uk_en` | 30,111 | (UK→EN) | dmklinger UK→EN dictionary. |
| `frazeolohichnyi` | 24,683 | `search_idioms` | Фразеологічний — idioms & set expressions. |
| `ua_gec_errors` / `_fts` | 8,937 | `search_ua_gec_errors` | UA-GEC human-annotated error→correction pairs (calques/cases/gender). |
| `puls_cefr` | 5,939 | `query_cefr_level` | PULS CEFR vocabulary (A1–C1). |
| `style_guide` | 342 | `search_style_guide` | Антоненко-Давидович structured entries (Russianism/calque authority). |
| `grinchenko`/`goroh_etymology` | 41 | — | Горох etymology stubs (small). |
| `paronyms_cache` | 6 | — | Paronym pair cache. |

### Private reference sources (`textbooks`)

Eight ingested sources live in the `textbooks` table but are **not** redistributable
school textbooks. Source `.txt` files are gitignored under `docs/references/private/`;
they are local-only references for RAG grounding and must **never** be quoted verbatim
in pipeline outputs.

| `source_file` | `author` | Chunks | What it is |
|---|---|---:|---|
| `ulp-1-00-lesson-notes` … `ulp-6-00-lesson-notes` | Ukrainian Lessons Podcast | 40 each (240 total) | ULP Seasons 1–6 lesson-note books. Ingest: `scripts/ingest/ulp_lesson_notes_ingest.py`. |
| `anna-ohoiko-1000-words-2nd-ed` | Anna Ohoiko | 1,000 | «1000 Most Useful Ukrainian Words» (2nd ed.). Ingest: `scripts/ingest/ohoiko_books_ingest.py`. |
| `anna-ohoiko-500-verbs` | Anna Ohoiko | 500 | «500+ Ukrainian Verbs». Ingest: `scripts/ingest/ohoiko_verbs_ingest.py`. |

> Also available separately (not in `sources.db`): **VESUM** morphological dict at `data/vesum.db`
> (409K lemmas / 6.7M forms) via `verify_word`/`verify_words`/`verify_lemma`; **stress dict** (2.7M
> forms) via `ukrainian-word-stress`. Full Antonenko PROSE (169 chunks) lives in `textbooks`
> under `source_file='antonenko-davydovych-yak-my-hovorymo'` — pair with `style_guide` for any
> Russianism check (the structured 342 misses the prose discussion).

---

## `literary_texts` breakdown

### By genre (137,723 chunks)
| Genre | Chunks | | Genre | Chunks |
|---|---:|---|---|---:|
| scholarly | 40,480 | | drama | 1,183 |
| prose | 33,186 | | letters | 1,175 |
| chronicle | 18,777 | | legal | 1,022 |
| poetry | 14,184 | | diary | 939 |
| encyclopedia | 11,459 | | fable | 832 |
| philosophy | 2,954 | | documents | 635 |
| polemic | 2,844 | | hagiography | 425 |
| biography | 2,446 | | religious | 379 |
| anthology | 1,624 | | travelogue | 335 |
| memoir | 1,442 | | rhetoric / reference / grammar | ~855 |
| | | | **folk** (carol/duma/spring/harvest/historical_song) | **35** |

### Key sources (by `source_file` / `work`)
- **Chronicles (litopys.org.ua / izbornyk):** Іпатіївський (1,865), Величко (1,678+1,676), Новгородський
  (1,120), Лаврентіївський (1,033), Київський, Самовидець, ПВЛ, Литовсько-білоруські літописи.
  Scraped by `scrape_litopys.py` / `batch_scrape_izbornyk.py`. (litopys.org.ua = izbornyk.org.ua,
  HTTP only, confirmed live 2026-06-15.)
- **Грушевський** «Історія України-Руси» — all volumes (~14K chunks).
- **Encyclopedias:** Українська літературна енциклопедія (5,555), Енциклопедія українознавства (3,242),
  Шевченківський словник (2,420).
- **Authored literature (ukrlib бібліотека):** Франко (4,466), Нечуй-Левицький (4,370), Гончар (3,975),
  Самчук (3,804), Лепкий (2,236), Багряний (1,877), Кобилянська (1,750), Шевченко (1,166), Хвильовий,
  Мирний, Йогансен, Довженко, Сковорода, Прокопович, Вишня, Грінченко… (`source_file=ukrlib-<author>`).
- **Folk scholarship:** Костомаров «Слов'янська міфологія» (958), + folk attestations embedded in
  Грушевський / Драгоманов / ЕУ (this is where most folk *verbatims* actually live).
- **Folk primaries (standalone):** `ukrlib-narod-dumy` — 35 chunks / 29 works (думи, колядки, щедрівки,
  веснянки, жниварські, історичні пісні). Added 2026-06-15 (#3193). Scraper: `scrape_ukrlib.py --narod`.

---

## How to query the corpus

- **Prefer the MCP tools** (see table above). Start with `mcp__sources__search_sources` (unified) or
  scope with `search_literary` / `search_text` / `search_definitions` / `search_esum` / etc.
- **Verify a quote is real:** `mcp__sources__verify_quote` (returns confidence + chunk_id).
- **Direct SQL** (forensics / counts):
  ```bash
  .venv/bin/python -c "import sqlite3; d=sqlite3.connect('data/sources.db'); \
    print(d.execute(\"SELECT COUNT(*) FROM literary_fts WHERE literary_fts MATCH 'щедрівочка'\").fetchone())"
  ```

## Known gaps & caveats
- **#4594 — deterministic gap audit:** see
  [docs/corpus-gap-audit.md](corpus-gap-audit.md) for the 2026-07-06 register × domain ×
  CEFR/track evidence table and DRAFT consumer-driven acquisition queue.
- **#2901 — `source_url` dropped:** ~92% of `literary_texts` rows have NULL `source_url`, so we can't
  always link a chunk back to its public web page (only izbornyk + new narod carry URLs).
- **Folk genre primaries are thin** — standalone folk texts are only the 35 narod chunks; the rest of
  folk is embedded in scholarly works. Expanding the narod scrape further (more genres: байки, вертеп)
  or ingesting Грушевський/Драгоманов folk anthologies as tagged primaries would deepen #3162.
- **СУМ-11 Sovietization** (~5.6% flagged) and **ukrajinet auto-translation** — see the
  `mcp-sources-and-dictionaries` rule for the per-tool caveats.
- **Dir mismatch** (scraper-local vs builder-GDrive) — see [§ Architecture](#architecture).

## Refreshing this doc
```bash
# row counts per table:
.venv/bin/python -c "import sqlite3; d=sqlite3.connect('data/sources.db'); \
  print([(t,d.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]) for (t,) in \
  d.execute(\"SELECT name FROM sqlite_master WHERE type='table'\") if not t.endswith(('_fts','_config','_data','_docsize','_idx','_meta'))])"
# curated view: mcp__sources__collection_stats
# literary by genre: SELECT genre,COUNT(*) FROM literary_texts GROUP BY genre ORDER BY 2 DESC;
```
After refreshing, bump the "Last refreshed" date at the top and re-sync `v7-design-and-corpus.md` §2.
