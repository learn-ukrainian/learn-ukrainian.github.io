# Dispatch Brief — #1975 textbook_grounding matcher: add chunk_id lookup

**Date:** 2026-05-15
**Issue:** [#1975](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1975) — m20 build #5 RED on `textbook_grounding` (Karaman p.187)
**Target agent:** Codex
**Mode:** danger (commits + PR)
**Worktree:** mandatory

## Root cause (already diagnosed; just code the fix)

`scripts/build/linear_pipeline.py::_search_textbook_hits` (line 922) uses FTS5 full-text search via `wiki.sources_db.search_sources` with query `f"{title} {topic_query}"`. For a plan reference `title="Караман Grade 10, p.187"` against a `topic_query` like "ranok ranok routine morning":

- FTS5 has no metadata for "Grade 10" or page numbers — those become unmatched query tokens
- The chunk for p.187 (`10-klas-ukrmova-karaman-2018_s0187`) contains "§ 38 Розмовна, просторічна, емоційно забарвлена лексика..." — slang lexicon, NOT morning routines
- FTS5 cannot surface this chunk from a query containing morning-topic tokens
- Matcher reports `corpus_missing` even though the chunk exists

**Verified reproducer (run before coding):**
```bash
sqlite3 data/sources.db "SELECT chunk_id, substr(text,1,80) FROM textbooks WHERE source_file='10-klas-ukrmova-karaman-2018' AND chunk_id LIKE '%_s0187';"
```
Returns 1 row. So the chunk exists; the matcher just can't find it via FTS5.

## Fix shape (~40 LOC)

In `scripts/build/linear_pipeline.py`, add a metadata-first lookup BEFORE the FTS5 call inside `_search_textbook_hits` (or as a sibling helper that `_build_textbook_excerpt_context` calls first).

### 1. Parse the title

Add a parser that extracts `(author, grade, page)` from titles like:
- `"Караман Grade 10, p.187"` → `("Караман", 10, 187)`
- `"Захарійчук Grade 4, p.162"` → `("Захарійчук", 4, 162)`
- `"Кравцова Grade 4, p.113"` → `("Кравцова", 4, 113)`

Regex: `^(\S+)\s+Grade\s+(\d+),\s*p\.\s*(\d+)$` (case-insensitive on `Grade`/`p`).

### 2. Map author → corpus source_file prefix

The corpus naming convention is `{grade}-klas-{textbook_type}-{author-translit}-{year}`:
- Караман Grade 10 → `10-klas-ukrmova-karaman-2018`, `10-klas-ukrajinska-mova-karaman-...`, possibly multiple years
- Захарійчук Grade 4 → DOES NOT EXIST in corpus (Grade 1 is `1-klas-bukvar-zaharijchuk-2025`); the matcher should return a clear `corpus_missing` here, not a false `corpus_missing` from FTS5 failure
- Кравцова Grade 4 → check what's in corpus

Implement as a SQL pre-query:
```python
authors_translit = {
    "Караман": ["karaman"],
    "Захарійчук": ["zakhariychuk", "zaharijchuk", "zahariichuk"],  # transliteration variants
    "Кравцова": ["kravcova", "kravtsova"],
    "Авраменко": ["avramenko"],
    "Глазова": ["glazova", "hlazova"],
    "Заболотний": ["zabolotnyi", "zabolotnij"],
    "Захарчук": ["zakharchuk"],
    "Вашуленко": ["vashulenko"],
    "Большакова": ["bolshakova"],
    "Міщенко": ["mishhenko", "mishchenko"],
}
```

Build the candidate source_file list:
```python
SELECT DISTINCT source_file FROM textbooks
WHERE source_file LIKE '{grade}-klas-%'
  AND ({source_file LIKE '%-{translit1}-%' OR ...})
```

### 3. Direct chunk lookup

Given `source_file` candidates and a page number, fetch the chunk:
```python
SELECT chunk_id, text FROM textbooks
WHERE source_file = ?
  AND chunk_id LIKE '%_s{page:04d}'
```
Try zero-padded width 4, fall back to width 3 (`_s187`) if no match — different ingests used different padding conventions.

If exactly one row → use it as the textbook hit (skip FTS5).

If zero rows → set `corpus_missing=True` with reason `"page {page} not in corpus for {source_file}"` (deterministic — not a search miss).

If 1+ rows but ambiguous author (multiple matching source_files) → log warning, prefer the most-recent-year file.

### 4. Fall back to existing FTS5 path

If title doesn't match the `Author Grade N, p.M` regex (e.g. free-form title), use the existing FTS5 search as today.

## Tests required (add to `tests/test_textbook_grounding.py`, create if missing)

```python
def test_karaman_grade10_p187_resolves_to_chunk():
    """Reproducer from #1975: matcher must find the existing chunk."""
    hits = _search_textbook_hits("Караман Grade 10, p.187 ", level="a1", limit=1)
    assert len(hits) == 1
    assert hits[0]["chunk_id"] == "10-klas-ukrmova-karaman-2018_s0187"

def test_zakhariychuk_grade4_p162_reports_corpus_missing_deterministically():
    """Grade 4 Захарійчук doesn't exist in corpus; matcher should say so cleanly."""
    hits = _search_textbook_hits("Захарійчук Grade 4, p.162 ", level="a1", limit=1)
    assert len(hits) == 0  # or however corpus_missing is signaled

def test_free_form_title_falls_back_to_fts5():
    """Titles without 'Grade N, p.M' format use the existing FTS5 path."""
    # Use a title from a non-textbook reference type to confirm fallback
    ...
```

## Steps

1. **Worktree setup** — `git worktree add .worktrees/dispatch/codex/1975-matcher-fix -b fix/textbook-grounding-chunk-id-lookup main`
2. **Read** `scripts/build/linear_pipeline.py` lines 920-985 to see the current matcher.
3. **Implement** title parser + author→translit map + direct chunk lookup, with FTS5 fallback.
4. **Run reproducer** SQL to confirm the chunk exists.
5. **Add tests** as above.
6. **Verify**: `.venv/bin/pytest tests/test_textbook_grounding.py -v` — all pass.
7. **Lint**: `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/`.
8. **Commit** with conventional message (subject ≤72 chars).
9. **Push** and **open PR** (no auto-merge): `gh pr create --title "..."`.

## Verifiable-claims preamble (per #M-4)

| Claim | Tool | Evidence |
|---|---|---|
| Reproducer chunk exists | `sqlite3 data/sources.db "SELECT chunk_id FROM textbooks WHERE chunk_id='10-klas-ukrmova-karaman-2018_s0187';"` | raw row output |
| Tests pass | `pytest tests/test_textbook_grounding.py -v` | raw `N passed in M.MMs` |
| Ruff clean | `ruff check ...` | raw `All checks passed!` |
| PR opened | `gh pr view --json url` | raw URL |

No claim about an artifact without quoting tool output.

## Out of scope

- Fixing the plan_references for `a1/my-morning` themselves (they cite wrong-level textbooks: Караман Grade 10 p.187 = slang lexicon, not morning; Захарійчук Grade 4 isn't in corpus). That's a separate plan-review issue. THIS PR is matcher-only.
- The `vesum_verified` malformed forms (ди_юся, дивюся, користуювася) from the same #1975 — separate issue, writer-prompt scope.
- Rebuilding m20. Wait for the matcher fix to merge, then re-run.

## Branch + commit conventions

- Branch: `fix/textbook-grounding-chunk-id-lookup`
- Commit subject: `fix(pipeline): textbook_grounding does chunk_id lookup for 'Author Grade N, p.M' titles (#1975)`
- Co-authored-by trailer per AGENTS.md convention.
