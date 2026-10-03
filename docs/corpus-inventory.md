# Corpus Inventory — what's actually in our data

> **Read this when you need to know what source material we have** (for writing, review,
> verify_quote, RAG grounding, or deciding whether to scrape something new). Sessions
> kept re-discovering the corpus from scratch — this doc is the durable, current answer.
>
> **Last refreshed: 2026-07-31** (by querying `data/sources.db` directly and
> reconciling retained raw-source identities — see
> [§ Refreshing this doc](#refreshing-this-doc)). When the corpus grows, update this file
> AND `docs/best-practices/v7-design-and-corpus.md` §2 (the #M-11 SSOT cross-links here).

---

## TL;DR

- The live store is **`data/sources.db`** — a **9.4 GB SQLite + FTS5** database in
  **WAL journal mode** (grown from 1.8 GB by the ULIF DictUA walk's cached entries and
  raw responses, 2026-09). The MCP `sources` server (port 8766) reads it; every
  `mcp__sources__*` tool, `verify_quote`, `search_literary`, etc. hit this file.
- **Journal mode is WAL and is declared by the writers** (`build_sources_db.py` right after
  its atomic swap, `fetch_ulif_homonyms.py prepare_database` on every walk start; each
  asserts the PRAGMA returns `wal`). Evidence readers (`build-words`, `words-verify`,
  `build-pack`, `pack-verify`) **pin one snapshot per session**: a long read transaction
  that in WAL costs a concurrent writer nothing. In DELETE mode the same pinned read holds
  a SHARED lock and blocks the walk's commits — see `docs/runbooks/storage-topology.md`
  § Journal mode.
- It holds **137.7K literary chunks + 55.0K textbook chunks + ~1M dictionary rows +
  22.4K wiki + Wikipedia** across ~27 content/dictionary tables.
- It is **BUILT from the bulk raw-source root** (SMB mirror preferred, Google Drive
  fallback), not from local scraper output under `data/`. That split is the #1
  gotcha — see
  [§ Architecture](#architecture--where-the-data-lives-the-1-gotcha).
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
        │ reads literary + textbooks ← GDRIVE_DATA  ←  bulk raw-source root (see below)
        │ reads external             ← data/external_articles/  (local)
        ▼
  data/sources.db  (9.4 GB SQLite + FTS5, WAL)  ←  what the MCP `sources` server serves
                                                    (ALWAYS local — never open from SMB)
```

### Storage topology v1 (bulk root + local DB)

- **Active DB:** `data/sources.db` stays on the Mac repository volume. Sources MCP
  and ordinary tests depend on this local file; an SMB outage must not break them.
  `.venv/bin/python -m scripts.storage status` reports its size, `journal_mode` (read from
  the SQLite header, no connection opened) and the `-wal` sidecar size.
- **Readers pin one snapshot per session.** `scripts/curriculum/evidence/sources.py` opens
  `sources.db` read-only with an explicit deferred `BEGIN` and keeps that read transaction
  for the whole build/verify; the identity a lock records is the digest of the rows it
  cites (`built_with.sources_db_scheme: rows-v2`), never a digest of the file. While a
  session is open the WAL cannot be checkpointed past its read mark, so the reader stops
  itself (`snapshot_limit`) if `sources.db-wal` exceeds 4 GiB or free disk on the data
  volume drops below 10 GiB (`scripts/curriculum/evidence/config.py`; env overrides
  `LU_EVIDENCE_WAL_CEILING_BYTES` / `LU_EVIDENCE_FREE_DISK_FLOOR_BYTES`).
- **Bulk raw-source root** (legacy name `GDRIVE_DATA` in `scripts/wiki/config.py`)
  is resolved by `scripts.storage.topology.resolve_bulk_root`:
  1. `LU_BULK_ROOT` when marker-valid
  2. Windows **UkrainianData** SMB mirror
     (`…/raw-sources/learn-ukrainian-data`) when mounted and marker-valid
  3. Google Drive File Provider
     (`My Drive/Projects/learn-ukrainian-data` or `LU_GDRIVE_DATA`) when marker-valid
  4. Structured **unavailable** (no path guessing)
- **Markers:** both `literary_texts/` and `textbook_chunks/` must exist.
- **Status CLI (read-only):** `.venv/bin/python -m scripts.storage status`
- **Windows mirror maintenance:** `scripts/storage/windows/` (`rclone copy` only;
  verify before receipt). Full contract: [`docs/runbooks/storage-topology.md`](runbooks/storage-topology.md).

- **`GDRIVE_DATA`** is the bulk-root alias above (SMB preferred, Drive fallback).
  It contains 229 `literary_texts/*.jsonl` files and 158 public
  `textbook_chunks/grade-*/*.jsonl` files on the full mirror. Never commit an
  operator-specific mount path. This is the rebuild source of record.
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

For the #4593 STEM books, follow the
[incremental textbook recipe](runbooks/stem-textbook-incremental-ingest.md),
including guarded acquisition, explicit database selection, and native-text
admission. A worktree database copy is not the live Sources MCP database.

### Safe recipe to ADD literary content (no destructive rebuild)

Used 2026-06-15 to land the expanded folk corpus (#3193) without a `--force`:
1. Scrape → `data/literary_texts/<source>.jsonl`.
2. **Copy the jsonl to `GDRIVE_DATA/literary_texts/`** (so a future `--force` keeps it).
3. **Incremental-insert** into the live `data/sources.db` in one transaction: back up the DB,
   `DELETE FROM literary_texts WHERE source_file=<src>`, insert rows via
   `scripts/wiki/sources.py::build_literary_row`, then `literary_fts('rebuild')`, commit.
4. Verify via the MCP: `mcp__sources__search_literary` / `verify_quote`.

### Reclaiming local disk — symlink a Drive-duplicated FILE (verify identity per file)

Some files in `data/` are byte-identical copies of what already sits on the Drive mount but were
never deleted locally. For a file **proven identical** to its Drive copy, replace the local file
with a **symlink to the streamed Drive copy** — it takes 0 local bytes when idle and materializes
on demand, so builds that read the **local** path (the dir-mismatch gotcha above) still work. This
is **per-file**, not per-directory: prove identity for each file; do NOT blanket-symlink a directory
(most `data/` subdirs are NOT pure duplicates — see caveat b).

Resolve the mount path the way the runbooks do — the env override is **`LU_GDRIVE_DATA`** (see
`scripts/wiki/config.py`), NOT `GDRIVE_DATA`:
```bash
GDRIVE="${LU_GDRIVE_DATA:-$(ls -d "$HOME/Library/CloudStorage/"GoogleDrive-*/"My Drive/Projects/learn-ukrainian-data" 2>/dev/null | head -1)}"
```
Recipe (used 2026-07-16 for `ubertext-freq/frequency.db`, 1.2 GB reclaimed):
1. **Prove byte-identical** (not just "exists on Drive"): `cmp -s data/<x> "$GDRIVE/<x>"` — or, for a
   very large file you trust, matching size **and** mtime via `ls -la`.
2. **Confirm valid + mount healthy:** e.g. `head -c 16` of a SQLite file reads `SQLite format 3`.
3. **Confirm nothing has it open:** `lsof data/<x>` is empty.
4. **Swap, keeping the local copy until verified:**
   ```bash
   mv "data/<x>" "data/<x>.localbak"
   ln -s "$GDRIVE/<x>" "data/<x>"
   ```
5. **Functional test (mandatory):** actually open/read it through the symlink (e.g. a `sqlite3
   SELECT`) — the reader must work. THEN `rm -rf "data/<x>.localbak"`. If it fails, `mv` the bak back.

**Caveats:** (a) A regenerating writer (e.g. `convert_phase2.py` DROP/CREATE/INSERTs `frequency.db`
from `ubertext_freq.csv.xz`) writes **through** the symlink to Drive; unlink first for a fresh local
rebuild. (b) **Directories are usually NOT pure duplicates.** As of 2026-07-16 only
`ubertext-freq/frequency.db` was proven identical; `literary_texts/` local (~27 files) is a partial
subset of Drive's source-of-truth (~232), and `native-reviewer-lessons/` + `raw/` diverge
(different tree/mtime). Verify each file — never trust the directory.

**Never symlink these — runtime-hot / build-essential, keep local:** `sources.db` (MCP `sources`
server), `vesum.db` (VESUM `verify_*`), **`embeddings/`** (dense reranker — `search_sources` defaults
to `unified_dense` → `rerank_candidates` → `data/embeddings/manifest.db` + shards), `mphdict/`,
`lexicon/` (offline Atlas/enrich/build deps).

---

## Table inventory (`data/sources.db`, 2026-07-31)

### Content corpora

| Table | Rows | MCP tool | What it is |
| --- | ---: | --- | --- |
| `literary_texts` / `literary_fts` | **137,723** | `search_literary` | Primary sources: chronicles, encyclopedias, authored literature, scholarly works, **folk primaries (35)**. See [breakdown](#literary_texts-breakdown). |
| `textbooks` / `textbooks_fts` | **54,979** (168 `source_file`s) | `search_text` | 49,193 public/external school-textbook rows across grades 1–11 plus 5,786 rows from **8 private ULP/Ohoiko refs** — see [§ Private reference sources](#private-reference-sources-textbooks). |
| `textbook_sections` | 7,250 | (internal) | Section hierarchy for textbook chunks. |
| `zno_documents` | **33** | (direct SQL) | ZNO/NMT booklet metadata (2010–2025, Ukrainian language). Ingest: `scripts/ingest/zno_ingest.py`. |
| `zno_tasks` / `zno_tasks_fts` | **1,646** | (direct SQL) | Parsed ZNO tasks from zno.osvita.ua; FTS on `stem`, `options_json`, `topic_tag`. Consumer: #4506 paronym/stress worksheets. |
| `ukrainian_wiki` / `_fts` | 22,385 | `search_sources` | Our OWN compiled wiki pedagogy (`wiki/**`), keyed by article slug + track. |
| `external_articles` / `external_fts` | 1,205 | `search_external` | Curated external articles + YouTube/blog transcripts (register/decolonization tagged). |
| `wikipedia` / `_fts` | 1,029 | `query_wikipedia` | Cached Ukrainian Wikipedia articles (+ a separate negative cache). |

### Curated listening and reading catalogues (#9409)

`resource_catalogue` / `resource_catalogue_fts` indexes metadata from every entry
in these files under `docs/resources/`: `podcasts/podcast_db.json`, all three
`podcasts/raw_lists/*.txt` lists, `podcasts/ulp_mapping.yaml`,
`external_resources.yaml`, `ulp-resources.yaml`, `ulp-alphabet.yaml`, `ulp-articles-index.yaml`,
`ulp-article-mappings.yaml`, `trusted_sources.yaml`, and the `dobraforma`,
`talkukrainian` and `verba` article catalogues. Internal trusted-source collections
use `sources://collection/...` locators; they have no HTTP link check.

Run the incremental metadata ingestion with an explicit **local** database:

```bash
<shared-project-python> -m scripts.ingest.resource_catalogue_ingest \
  --ingest --db data/sources-copy.db
```

For rehearsals, first create a consistent SQLite backup of the active database;
do not copy a running WAL database's main file alone. `--no-network` skips new
HTTP requests and retains previous checks. The script creates the table and FTS
idempotently, replaces only catalogue rows in one transaction, and reports each
file's input entries and distinct output URLs. Every original locator, title and
module mapping survives URL deduplication. `rows_out` per file overlaps other
files; only the global count represents distinct resources. After a full corpus
rebuild, rerun this incremental ingest as for the separately ingested ZNO tables.
Activation of the live database remains a separate driver operation after merge.

Use **`mcp__sources__search_resources`** with `query`, `kind`, `level`, `module`,
`free_only` and optionally `live_only` and `mode`. The default `mode: text`
searches full text even for one-letter words; empty text queries browse using filters.
Only explicit `mode: letter` uses the evidenced letter index, accepting a single
letter. Curriculum curation selects letter mode only for letter requirements.
The `letters` and `letter_evidence` columns preserve publisher-evidenced pairings
from `ulp-alphabet.yaml`; `access_evidence` records the evidence required for
`access: free`. Databases missing these columns require re-ingestion before any
resource search; the driver backs up and re-ingests the live database immediately
after merge.
Levels reflect explicit catalogue levels and module prefixes; absence stays
unknown. Module IDs preserve existing catalogue mappings rather than claiming
they match a current lesson plan. Results use `sources.tool-result.v1` and carry
source-entry provenance, HTTP status and UTC check date. `free_only` requires
an explicit free resource or free audio fact; missing access stays `unknown`.
It does not prove present availability or include premium notes. `live_only`
requires a recorded successful HTTP check, whose date remains visible.

ULP/FMU rows have `access: mixed`, `audio_access: free` and `notes_access: premium`.
Podcast page aliases (`/lesson/2/`, `/episode2/`) share a canonical URL.
Existing `external_articles` text is linked by normalized URL (including
catalogue-related URLs) or ULP/FMU series and episode identity. Its text joins the
FTS index; `discovery_evidence` records the chunk, source file, URL and relation.
Ukrainian queries therefore match stored source text rather than keyword aliases.
The ingest reports `linked_resources`; it downloads no media, article bodies or
premium material. Linked text is discovery evidence, not independent audio or
word-level timestamp verification.

Responses return at most 20 hits with a short prose summary and structured hits.
Each row is bounded to 24 KiB; provenance list budgets total 3,584 UTF-8 JSON bytes.
Other metadata lists have 512-byte budgets and scalar strings have 256-byte
budgets. Lists retain complete-record prefixes with total counts and truncation
flags; full provenance remains in the database. Before catalogue ingestion the
tool returns `status: error`, `error_code: resource_catalogue_missing`.

### Dictionaries & lexical resources

| Table | Rows | MCP tool | What it is |
| --- | ---: | --- | --- |
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

Owned books and premium notes are private references for grounding and pedagogy
research. Their raw files, extracted JSONL and digest receipts stay outside the
repository. The committed `registry/sources/owned-rights.yaml` is a mandatory
publication overlay: `owned_cite_only` permits a Resources credit but refuses any
printed quote; `private_permission` refuses both quotes and citations, with typed
errors. Pack claims and injected textbook-selection registries cannot override it.
An unreadable or malformed rights record also fails publication closed.

The private inventory is the denominator (23 work rows at the #9581 intake).
Existing Ohoiko word/verb books and the pronunciation reference retain their
`source_file`; ULP Seasons 1–6 retain `ulp-N-00-lesson-notes`. New sources use
`owned-<inventory-id>`. The inventory also covers workbooks and transcripts,
premium text packs and charts, readers and children's books, and two private
teacher-material sets, used with permission. Teacher identities are absent from
public records and corpus metadata. Audio, decks, derived study files and an
intentional missing source have explicit skip states.

Regenerate against a local backup before applying to the active corpus:

```bash
<shared-project-python> -m scripts.ingest.owned_books_ingest \
  --inventory <private>/INVENTORY.yaml --out-dir <private>/jsonl \
  --db <local>/sources-copy.db
<shared-project-python> -m scripts.ingest.owned_books_ingest \
  --inventory <private>/INVENTORY.yaml --out-dir <private>/jsonl \
  --db <local>/sources-copy.db --check
```

The sibling `drive-ukrainian/` directory holds inventory-matched inputs. Extraction
supports PDF, DOCX, EPUB spine order, PPTX presentation order and UTF-8 CSV text,
including ZIP
members and one nested archive level. Oversized members, unreadable documents,
missing expected files and PDF pages without text remain accounted for; predominantly
scanned PDFs and validated JPEG image pages require OCR. Available text is ingested even when another file is
missing, but the row remains an error and `--check` fails. PDF pages with more than
20% letters outside Ukrainian and ASCII English are reported as `garbled_text_layer`
and withheld for OCR; clean pages remain ingestable. The same classifier filters
extracted slides and other text units. Zero-letter pages count as
`page_no_text`. Garbled pages are excluded from the scanned-PDF threshold.
An `already_ingested` row supplies either `source_file` or a nonempty, unique
`source_files` list. Every identity must exist in the corpus and rights record.
Before extraction or cached-artifact reuse, each new identity must have a rights
record matching the inventory's class; missing or mismatched records fail closed.
ULP premium packs map to the six existing season identities without new extraction.
Unknown ingest modes fail with `unknown_ingest`. Terminal `/**` globs select all
regular files recursively; `.DS_Store` and AppleDouble (`._*`) metadata are ignored
on disk and in archives. Owner-only password PDFs remain extractable and carry
`owner_restricted: true` accounting; user-password PDFs are refused as `encrypted`.
Within each work, NFC-normalised, whitespace-collapsed file text is hashed with
SHA-256 before chunking. Identical files and files wholly contained in an earlier
retained file add no chunks and point to the earliest donor as `duplicate_of:f<index>`
(including archive-member indexes). The same applies when every non-empty
normalised page or slide equals a unit in one earlier retained file, regardless
of order. A file with even one new unit stays fully retained; individual units
are never removed. Empty text retains its no-text accounting;
partially overlapping files remain ingestable. CSV
text retains serialized rows, separators and quotes without guessing its dialect.

Unchanged reruns make no writes. A changed input digest is `stale_input` until
`--force` explicitly replaces that work's JSONL, corpus rows, FTS entries and
section links. `--dry-run` extracts and accounts without writes; `--only ID`
selects one work. Accounting exposes only inventory ids, numeric file/page
locators, counts and statuses. The driver owns backup, live application, Sources
restart and MCP verification; rehearsal on a copy does not establish live delivery.

> Also available separately (not in `sources.db`): **VESUM** morphological dict at `data/vesum.db`
> (409K lemmas / 6.7M forms) via `verify_word`/`verify_words`/`verify_lemma`; **stress dict** (2.7M
> forms) via `ukrainian-word-stress`. Full Antonenko PROSE (169 chunks) lives in `textbooks`
> under `source_file='antonenko-davydovych-yak-my-hovorymo'` — pair with `style_guide` for any
> Russianism check (the structured 342 misses the prose discussion).

---

## `literary_texts` breakdown

### By genre (137,723 chunks)

| Genre | Chunks | | Genre | Chunks |
| --- | ---: | --- | --- | ---: |
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

- **#6107 — recovery and lineage baseline:** the
  [existing-corpus audit](research/EXISTING_CORPUS_ASSET_RECOVERY_AND_LINEAGE_AUDIT.md)
  and machine-readable ledger reconcile all 229 literary JSONL source stems to
  the 229 database groups, separate 49,193 public textbook rows from 5,786
  private rows, and identify two database textbook sources whose raw chunk was
  unresolved at that snapshot. The later
  [training-usability decision](research/UKRAINIAN_CORPUS_TRAINING_USABILITY_DECISION.md)
  found source locators on all 137,723 literary raw rows and verified retained
  textbook chunks, PDFs, selection metadata, and URL mappings. The operator
  approved local research and model learning after required preprocessing;
  raw-source redistribution and publication remain separate decisions.
- **#4594 — deterministic gap audit:** see
  [docs/corpus-gap-audit.md](corpus-gap-audit.md) for the 2026-07-06 register × domain ×
  CEFR/track evidence table and DRAFT consumer-driven acquisition queue.
- **#2901 — `source_url` dropped during ingestion:** ~92% of
  `literary_texts` database rows have NULL `source_url`, but all 137,723 raw
  literary JSONL rows retain `source_url` or `source`. Restore links from the
  raw records; do not classify these rows as source-unknown.
- **Folk genre primaries are thin** — standalone folk texts are only the 35 narod chunks; the rest of
  folk is embedded in scholarly works. Expanding the narod scrape further (more genres: байки, вертеп)
  or ingesting Грушевський/Драгоманов folk anthologies as tagged primaries would deepen #3162.
- **СУМ-11 Sovietization** (~5.6% flagged) and **ukrajinet auto-translation** — see the
  `mcp-sources-and-dictionaries` rule for the per-tool caveats.
- **Dir mismatch** (scraper-local vs builder-GDrive) — see
  [§ Architecture](#architecture--where-the-data-lives-the-1-gotcha).

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
