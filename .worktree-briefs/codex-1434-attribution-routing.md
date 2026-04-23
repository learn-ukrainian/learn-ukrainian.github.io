# Fix #1434 — `_search_sections_fts5` missing `corpus` key (#1450 Fix 1)

## Context

The #1450 Opus diagnostic (`docs/reports/2026-04-23-gemini-wiki-writer-diagnosis.md`) root-caused 1,538 phantom-citation sidecar entries across 215 of 220 compiled wikis to a single missing dict key. Not Gemini invention — a contract-break in the pipeline between retrieval and attribution.

Full diagnostic in section §2 Pattern A + §4 Fix 1 of that report.

## Scope

Inline code-only change in `scripts/wiki/sources_db.py`. No prompt edits, no backfill (that's #1445 scope, blocked on this landing).

## Root cause

`scripts/wiki/sources_db.py::_search_sections_fts5` lines 315-322 constructs result dicts that are missing `"corpus": "textbook_sections"`. Every sibling `_search_*_candidates` function sets `corpus`. Downstream `compiler._build_sources_registry` reads `source.get("corpus") or source.get("source_type")` and falls back to `"textbook"` — routes to the wrong attribution table, silently degrades to `type: unknown + file: S####`.

## Fix

In `scripts/wiki/sources_db.py::_search_sections_fts5` result-dict construction, add:
```python
"corpus": "textbook_sections",
"unit_key": f"textbook_sections:S{meta['section_id']}",
```

## Test

Extend `tests/test_wiki_sources_db.py` (create if missing) with:
- Assert `results[0].get("corpus") == "textbook_sections"`
- Given a known `section_id` in fixture, assert `resolve_chunk_attribution(chunk_id, corpus)` returns `type="textbook"` + a filename matching `r"^\d+-klas-.+_s\d+$"`

## Verify

1. `.venv/bin/pytest tests/test_wiki_sources_db.py` green
2. `.venv/bin/pytest` full suite green (no regressions)
3. Live: compile one wiki with `scripts/wiki/compile.py --track b1 --slug adjectives-comparative --force`; inspect resulting `.sources.yaml` — expect `type: textbook`, `file: {grade}-klas-...`. No `type: unknown + file: S####` entries.

## Out of scope

- No prompt template edits (those are #1447, already merged).
- No backfill of historical yamls (#1445).
- No changes in `source_attribution.py` — `_resolve_textbook_section` already parses `S####` correctly; this fix gets the right corpus value feeding it.

## PR

Title: `fix(wiki): route textbook_sections through attribution — close #1434 (#1450 Fix 1)`

Body: reference this brief, summarize the 1-line fix + test additions. Do NOT auto-merge. Push + open PR; human or Claude merges after review.

## Worktree

Work in `.worktrees/codex-1434-attribution-routing` on branch `codex/1434-attribution-routing` (already created from origin/main). Commit + push + open PR. Do NOT attempt to merge — merging is blocked for dispatched agents per #1403 safety shim.

## References

- `docs/reports/2026-04-23-gemini-wiki-writer-diagnosis.md` (on main as of merge of #1450) — full diagnostic
- GH #1434 — issue with supplementary context
- EPIC #1451 Phase 3
