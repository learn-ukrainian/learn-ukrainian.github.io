# Task: #1339 — A1 grade filter bug, leaking Grade 5+10 chunks

**Status context**: verified 2026-04-19. `search_textbooks(keywords, track="a1")` and its successor `search_sources(track="a1", strategy="unified_dense")` both return chunks with `grade` in {"5", "10"} despite `_TRACK_GRADE_RANGES["a1"] == (1, 2, 3, 4)` in `scripts/wiki/sources_db.py:122-129`. Evidence: `wiki/.reviews/diagnostics/a1-sounds-letters-playback.json:24-30`.

Full spec: `gh issue view 1339`.

**Do NOT dispatch this until #1337 has landed** — stage-c's multi-corpus path now goes through `_search_sections_fts5`, which references `parent_section_id`. Running #1339 before #1337 means debugging against a non-functional code path.

## Scope — exactly this, no refactor

1. **Reproduce the bug first** — `tests/wiki/test_grade_filter.py` that calls `search_textbooks(keywords={"мама","тато","кіт"}, max_total=40, track="a1")` against the real `data/sources.db` and asserts every returned chunk has `grade` in {1, 2, 3, 4}. Write the test FIRST; it should fail.
2. **Root cause** — inspect the SQL at `sources_db.py:222-226` (or stage-c's equivalent in `_search_sections_fts5` after #1337 lands — both paths share the same grade filter idiom). Hypothesis from the original issue:
   - Schema column type mismatch — `grade` is stored as TEXT (check: `PRAGMA table_info(textbooks)` — yes, `grade TEXT`) but `_TRACK_GRADE_RANGES` returns integers. SQLite allows `TEXT IN (1,2,3,4)` which compares text "5" ≤ integer 5 via its loose-typing rules, but the IN operator with mixed types has well-known surprising behavior on some SQLite versions.
   - FTS5 JOIN edge — the `textbooks_fts JOIN textbooks s ON s.id = textbooks_fts.rowid` plus `WHERE textbooks_fts MATCH ?` may optimize the grade filter differently than expected.
3. **Fix** — minimal. Either cast the params to TEXT before binding (`[str(g) for g in grades]`) OR fix the schema to store `grade INTEGER` (broader, risks migration scope — avoid unless casting doesn't work). Test MUST pass after fix.
4. **Confirm fix holds under stage (c)** — rerun `_search_sections_fts5` path too if the SQL is shared, assert A1 results are grade-gated.
5. **Document root cause in the commit message** — one sentence explaining WHY the bug existed. Future debuggers need the breadcrumb.

## Ground rules

- Branch: `main`. No worktrees.
- `.venv/bin/python`, `.venv/bin/ruff`, `.venv/bin/pytest` — never bare.
- `git add` allow-list only — files named in the file scope below.
- Commit: `fix(sources): enforce A1-A4 grade filter in textbook retrieval (#1339)`
- Comment on #1339 with commit SHA + before/after test evidence (retrieval results showing Grade 5+10 presence before, absence after).

## File scope (allow-list)

Modify:
- `scripts/wiki/sources_db.py` — grade-filter fix (minimal, no refactor)

New:
- `tests/wiki/test_grade_filter.py` — regression test

**Do NOT modify**:
- Any other file in `scripts/wiki/` unless the bug is proven to originate there
- `scripts/wiki/build_sources_db.py` (schema changes out of scope unless casting fails)
- `curriculum/**`, `plans/**`, `orchestration/**`
- Any `text` column

## Acceptance criteria

- **AC1 reproduce**: `tests/wiki/test_grade_filter.py` fails on a clean checkout before the fix is applied
- **AC2 root-cause**: one-sentence explanation in the commit body
- **AC3 fix**: minimal change, test passes after
- **AC4 lint + full test green**: `.venv/bin/ruff check` + `.venv/bin/pytest tests/wiki/ -v` all green (including the stage-c multi-corpus tests that must survive)

## Out of scope

- Refactoring `search_textbooks` or `search_sources` beyond the grade filter
- Adding grade-filter logic to other corpora (literary, external, wikipedia use different routing; not this ticket)
- Schema migration of `grade` column to INTEGER (avoid unless casting doesn't fix; separate ticket)

## Done-when

- Single commit titled as above
- AC1-AC4 all green
- Comment on #1339 with evidence + commit SHA
