# Restore + formalize `literary_texts` metadata in `build_sources_db.py` + migration path

## Why

The `scripts/rag/ingest_literary.py:459-469` pipeline originally indexed these payload fields on each literary chunk:

- `work` (KEYWORD) — e.g. `"Повість временних літ"`, `"Кобзар"`
- `author` (KEYWORD) — already kept
- `year` (INTEGER) — publication / composition year
- `genre` (KEYWORD) — chronicle, religious, legal, poetry, prose, drama
- `language_period` (KEYWORD) — values: `modern`, `middle_ukrainian`, `old_east_slavic`

When the project migrated from Qdrant to SQLite at `scripts/wiki/build_sources_db.py:103-118` (schema) and `:474` (INSERT), the new `literary_texts` schema dropped `language_period`, `work`, `year`, and left `genre` empty. Source JSONLs still contain these fields (verified: all 23+ literary JSONL files carry `language_period` ∈ {modern, middle_ukrainian, old_east_slavic}).

Downstream work (#1338-v2 — full-corpus dense retrieval) requires these fields in SQL, not reconstructed in Python. This ticket restores them **at the builder, not as an ALTER patch** — because the rebuild path (`build_sources_db.py:382`) deletes `sources.db` and any post-hoc ALTER would be wiped on next rebuild.

## Scope — in order

1. Update the **builder** (`scripts/wiki/build_sources_db.py`) schema + INSERT so new DB rebuilds have the columns
2. Update the **ingest upstream** (`scripts/wiki/sources.py` and whatever passes payloads) to carry the fields through
3. Run the builder once to produce the new schema on the current DB
4. Provide a **migration script** (`scripts/wiki/restore_literary_metadata.py`) for any external / already-built DB instances, as a fallback path — not the primary fix

Do NOT touch the `text` or `title` columns — primary source text stays verbatim.

## JSONL field shape (verified)

The source JSONLs have `work` (human title, e.g. `"Літопис Грабянки"`), **not** `work_id`. Decision: **derive `work_id` by slugify at build time**, keep `work` as display name:

```python
def work_to_id(work: str) -> str:
    # "Літопис Грабянки" → "litopys_hrabyanky"
    return unidecode(work).lower().replace(" ", "_").replace("'", "").strip("_")
```

Persist both: `work` (display) and `work_id` (stable key).

## Acceptance criteria

### AC1 — Builder schema update (primary)

In `scripts/wiki/build_sources_db.py`:
- Extend the `CREATE TABLE literary_texts` block (currently line 103-118) to include `work` TEXT, `work_id` TEXT, `year` INTEGER, `language_period` TEXT. `genre` column already exists; it stays but gets populated.
- Extend the INSERT statement (currently line 474) to include the new fields
- Add indexes: `idx_literary_period`, `idx_literary_work_id`, `idx_literary_period_genre`
- Preserve the existing rebuild-deletes-db behavior; callers stay compatible

### AC2 — Ingest passthrough

In `scripts/wiki/sources.py` (the `LiteraryEntry` / `build_rows()` path, around line 20 based on review): read `work`, `year`, `genre`, `language_period` from the JSONL payload; compute `work_id` via `work_to_id()`; pass all of them to the INSERT.

If the JSONL is missing a field: `language_period` → fail loud (not optional). `year` → NULL. `genre` → empty string. `work` → use `source_file` as a fallback display name + log a warning.

### AC3 — Migration script for already-built DBs

`scripts/wiki/restore_literary_metadata.py`:
- Detect: if `literary_texts` lacks the new columns, ALTER them in
- Backfill: read every `data/literary_texts/*.jsonl`, JOIN to DB rows by `chunk_id`, UPDATE the new columns
- Idempotent: re-running should produce zero UPDATEs if data is already current
- Text-immutability check (AC4) runs before/after

### AC4 — Text-immutability verification (Python-side, not SQL)

SQLite has **no built-in `sha256()` function**. Compute in Python:

```python
before = [
    hashlib.sha256(row[0].encode("utf-8")).hexdigest()
    for row in conn.execute("SELECT text FROM literary_texts ORDER BY id")
]
# ... run migration ...
after = [
    hashlib.sha256(row[0].encode("utf-8")).hexdigest()
    for row in conn.execute("SELECT text FROM literary_texts ORDER BY id")
]
assert before == after, "migration modified text column"
```

### AC5 — Validation report

After AC1+AC2 build completes (fresh DB) OR AC3 migration completes (existing DB):

```
SELECT language_period, COUNT(*) FROM literary_texts GROUP BY language_period
```
Expected: three non-empty rows for `modern`, `middle_ukrainian`, `old_east_slavic`, summing to 137,688.

```
SELECT COUNT(DISTINCT work_id) FROM literary_texts
```
Expected: 30–60 distinct works.

Print the report to stdout and write a copy to `logs/literary_metadata_restore_YYYYMMDD.txt`. **Not** to `data/logs/` — `logs/` is already in `.gitignore`; `data/logs/` is not.

### AC6 — Idempotency without null-unsafe comparison

Do NOT use `WHERE x != new_value` patterns. SQLite's `!=` returns NULL when comparing against NULL, which evaluates as FALSE in a WHERE and silently skips rows.

Use either `IS NOT` (null-safe) or unconditional UPDATE (same-value UPDATEs are cheap, 137K rows is trivial). Prefer the unconditional form for simplicity. Wrap in a transaction to make it atomic.

### AC7 — Lint + tests

- `.venv/bin/ruff check scripts/wiki/build_sources_db.py scripts/wiki/sources.py scripts/wiki/restore_literary_metadata.py` clean
- `tests/wiki/test_literary_metadata.py` — new test file covering: builder schema has new columns, ingest passes them through, migration is idempotent, text immutability holds
- `tests/test_build_sources_db_safety.py` (existing, line 243 referenced by review) must still pass after schema change

## Out of scope

- Re-ingesting from source PDFs
- Modifying `text` or `title` content
- Filling gaps in JSONL payloads (separate project if needed)
- Adding new works to the corpus
- Changing the rebuild-deletes-db behavior (that's orthogonal, handled by #1338-v2)

## Owner / dispatch

Codex. Reference `#1338-precursor` in commits.

## Closing criteria

Builder produces DBs with the new fields populated. Migration script works on existing DBs. Validation report shows expected distribution (three period values summing to 137,688). Tests green. Text immutability verified via Python-side SHA256 comparison.
