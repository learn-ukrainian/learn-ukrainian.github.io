# #1434 — Fix compiler.py source attribution (BLOCKER for B2 compile)

Read `gh issue view 1434` for full context + ACs.

## One-line problem

`scripts/wiki/compiler.py:_build_sources_registry` stores raw chunk_id
as the `file:` field in sources.yaml. When chunk_id isn't filename-
shaped (literary_texts, external_articles, ukrainian_wiki, wikipedia,
textbooks chunk-level), type falls through to `unknown` and the citation
is unverifiable.

## Fix scope

1. **New helper** `scripts/wiki/source_attribution.py`:
   `resolve_chunk_attribution(chunk_id: str, corpus: str) -> dict`.
   Hits `data/sources.db` per corpus. Returns at minimum `file`, `type`,
   `title`; plus `url`, `domain`, `video_id`, `ts_start`, `ts_end`,
   `page`, `grade`, `author`, `section_path` where applicable. See
   #1434 body for the per-corpus table.

2. **Update** `WikiSourceEntry` in `scripts/wiki/sources_schema.py` to
   carry optional fields without breaking existing YAML parsing (use
   dataclass with defaults; `to_dict` omits None).

3. **Update** `compiler.py:_build_sources_registry` to pass corpus
   hint into the helper and populate rich attribution. The `sources`
   list already carries `corpus` per row (set in
   `sources_db.py:_dispatch_corpus_search` ~line 644) — use it.

4. **Dedupe** the `generated_by_model` line in wiki-meta. Currently
   appears twice in every compiled wiki (see `wiki/grammar/b2/academic-
   writing.md:8-9`). Root cause likely in how compiler.py builds the
   wiki-meta comment block — find + fix.

5. **Tests**:
   - `resolve_chunk_attribution` per corpus (textbook_sections, textbooks,
     literary_texts, external_articles with/without video_id, wikipedia,
     ukrainian_wiki)
   - Integration: fresh compile of a single slug produces 0 entries
     with `type: unknown` (assuming all chunks resolvable)
   - Regression: existing wikis with proper S1-S5 textbook attribution
     continue to work

## Acceptance — CANONICAL SMOKE TEST (user, 2026-04-23)

The PR is not done until this exact command, run from repo root on
a clean main checkout after your branch is merged, produces a
`.sources.yaml` with ZERO `type: unknown` entries and proper
attribution for every `[S*]`:

```bash
.venv/bin/python scripts/wiki/compile.py --track b2 --slug academic-writing --force
```

Inspect `wiki/grammar/b2/academic-writing.sources.yaml` after the run.
Every entry must have:
- `file:` that is NOT a bare chunk ID (no more `file: S2318`)
- `type:` that is one of the real corpus types (textbook / literary /
  external / ukrainian_wiki / wikipedia / dictionary), NEVER `unknown`
  unless the chunk is genuinely unresolvable
- For external articles with video_id: `url:` with `?t=<ts_start>s`

Also required:
- Zero bare chunk IDs in any newly-compiled sources.yaml (not just
  academic-writing — sanity-check one other slug on a different corpus)
- wiki-meta `generated_by_model` appears exactly once
- Full `pytest` suite green

## Worktree

```
git worktree add -b codex/1434-compiler-attribution .worktrees/codex-1434-compiler-attribution
cd .worktrees/codex-1434-compiler-attribution
# work, commit, push, PR. Do NOT auto-merge.
```

## Sibling issue

#1435 is the backfill for already-generated wikis. DEPENDS on this PR
merging first (needs the helper). Don't touch that in this PR.

## Hard timeout

5400s (90m). Medium complexity.
