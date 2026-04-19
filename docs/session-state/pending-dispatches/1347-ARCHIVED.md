# Task: #1347 — literary metadata restoration

Full spec: `gh issue view 1347`. Read entirely before coding — every AC is there.

## Ground rules

- Work on `main` (no worktrees)
- `.venv/bin/python`, `.venv/bin/ruff`, `.venv/bin/pytest` — never bare `python`
- `git add` allow-list only (files named in AC1–AC7). No `-A`.
- Commit: `feat(sources): restore literary metadata (#1347)`
- Close #1347 with a comment containing: validation report output from AC5 (period distribution + work_id count), before/after SHA256 verification result, list of touched files

## Adversarial review notes (from 2026-04-19 review — apply these specifically)

1. AC1 is primary: update `scripts/wiki/build_sources_db.py` schema + INSERT FIRST. Then AC3 migration script for already-built DBs.
2. AC4: SHA256 text-immutability verification is Python-side (`hashlib.sha256` over `SELECT text ORDER BY id`). SQLite has no built-in `sha256()` function.
3. AC6: idempotency via unconditional UPDATE in a transaction, or `IS NOT` for null-safe compare. Never plain `!= NULL`.
4. Source JSONL has `work` not `work_id`. Derive `work_id` via slugify at build time, persist both columns.
5. Log output to `logs/literary_metadata_restore_YYYYMMDD.txt` — not `data/logs/` (which is not gitignored).
6. `language_period` canonical values: `modern`, `middle_ukrainian`, `old_east_slavic`. Verified from source JSONLs.

## Done when

- Builder schema has the new columns; fresh rebuild produces a populated DB
- Migration script handles already-built DBs idempotently
- SHA256 immutability check passes before/after
- Validation report shows three non-empty `language_period` rows summing to 137,688
- `ruff check` clean; `tests/wiki/test_literary_metadata.py` green
- Commit landed on `main`, #1347 closed with evidence
