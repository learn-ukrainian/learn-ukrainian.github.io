# Dispatch: literary corpus ingest drops source_url — add column + propagate + backfill (#2901)

The literary RAG scrapers record `source_url` per chunk in the JSONL, but `ingest_literary.py` → the
`literary_texts` table has NO url column, so provenance is silently dropped at ingest → modules can't link
students to readable originals. Read it: `gh issue view 2901`. (External-article + Wikipedia tables DO keep URLs.)

## Fix
1. **Schema:** add a `source_url TEXT` column to `literary_texts` (idempotent migration — `ALTER TABLE ... ADD
   COLUMN` guarded by a column-exists check; do NOT drop/recreate the table or lose rows).
2. **Ingest:** in `scripts/rag/ingest_literary.py`, read `source_url` from each JSONL record and write it to
   the new column. Default NULL when the JSONL lacks it (do not invent URLs).
3. **Backfill:** existing rows from the on-disk JSONL in `data/literary_texts/*.jsonl` keyed by `chunk_id`.
   For waves whose JSONL is absent locally, leave NULL + log the wave (do NOT fabricate a URL). Public-domain
   izbornyk/litopys work-level URLs may be re-derived ONLY if a deterministic manifest maps work→URL; else NULL.
4. **Audit note:** check whether `textbooks` (and other corpus tables) have the same gap; note it in the PR
   (fix textbooks only if trivial — otherwise file a follow-up). Do NOT expand scope blindly.

## Constraints
- `data/sources.db` is local (1.6 GB, gitignored) — migration + backfill run LOCALLY; CI can't. Provide a
  one-shot migration script (`scripts/rag/migrate_add_literary_source_url.py`) + a unit test on a TEMP sqlite
  fixture DB (NOT the real 1.6 GB db). Do NOT commit any `.db`.
- Verify backfill count: report rows updated / rows left NULL with reasons.

## Numbered steps
1. `cd /Users/krisztiankoos/projects/learn-ukrainian && git fetch origin` (`--worktree` from origin/main).
2. Implement schema migration + ingest propagation + backfill script + tests (temp-db fixture).
3. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest -k "literary or ingest or source_url" -q` → paste summary.
4. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/ tests/` → paste final line.
5. Confirm no DB staged: `git status --short` shows NO `*.db`.
6. Commit `fix(corpus): propagate source_url into literary_texts (column + ingest + backfill) (#2901)`.
7. `git push -u origin <branch>`; `gh pr create` referencing #2901. NO auto-merge.

## Evidence (#M-4 — command + cwd + raw output per claim)
- pytest summary (temp-db fixture); the `PRAGMA table_info(literary_texts)` before/after showing the new
  column; backfill counts (updated / NULL-with-reason); `git status --short` (no .db); ruff final line;
  `git log -1 --oneline`; `gh pr view --json url`.
