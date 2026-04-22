# Codex Brief — #1373 A.6 Ingest 55 A1 wikis into sources.db

**Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1373
**Parent EPIC:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1365 (Two-track build rollout)
**Task ID:** `codex-1373-wiki-ingest`
**Worktree:** `.worktrees/codex-1373-wiki-ingest`
**Branch:** `codex/codex-1373-wiki-ingest`
**Effort:** xhigh (substantial pipeline work; tests required; integration with existing sources.db schema)
**Hard timeout:** 5400s (90 min) — this is a real chunk of work

## Why this matters

A.5 (#1372) landed 55 Ukrainian-canonical A1 pedagogy wikis at `wiki/pedagogy/a1/*.md`. They're not yet ingested into `sources.db` so downstream retrieval can't find them. A.6 closes that loop — wikis become a primary retrieval surface for A1/A2 module builds.

This is the **immediate next blocker for Track A** in the EPIC roadmap. Once A.6 lands, A.7 (build a canary A1 module against the enriched corpus) is unblocked.

## Read the issue body in full before coding

The issue at #1373 has 5 detailed ACs (AC1 through AC5) covering segmentation, FTS5 indexing, source-weighting, admission gates, and tests. **Read it.** This brief adds dispatch-specific instructions; the issue body is the primary spec.

## Worktree instructions (mandatory)

    git worktree add -b codex/codex-1373-wiki-ingest .worktrees/codex-1373-wiki-ingest
    cd .worktrees/codex-1373-wiki-ingest

## Hard prohibitions

1. **DO NOT MERGE the PR yourself.** Open it only.
2. **DO NOT use `gh pr merge` / `--admin` / `gh pr review --approve`.**
3. **DO NOT touch the existing `textbooks` or `external_articles` tables in `sources.db`.** A.6 adds a NEW corpus (`ukrainian_wiki`) — segregation is non-negotiable per EPIC.
4. **DO NOT branch in the main checkout.**
5. **DO NOT skip AC4 admission gates.** Empty/non-Cyrillic chunks will pollute retrieval — the gate exists for a reason.
6. **DO NOT skip AC5 tests.** Ingestion correctness is verifiable; verify it.
7. **DO NOT modify the 55 wiki source files** at `wiki/pedagogy/a1/*.md` — they're the input, not your output.

## Read before coding (mandatory)

- `wiki/pedagogy/a1/` — sample 3-5 of the source files to understand the input shape (markdown body + `[S1]` / `[S2]` citation markers + sidecar `*.sources.yaml`)
- `scripts/wiki_corpus/` — Codex's #1368 corpus scaffolding (existing patterns)
- The schema for `sources.db` — find via `sqlite3 data/sources.db ".schema"` or wherever the schema lives. Look for the existing `ukrainian_wiki` table created by #1368.
- `scripts/retrieval/` (or wherever post-#1348 retrieval lives) — to understand how to add a new retrieval branch
- Any existing tests for `wiki_corpus/` or retrieval

## Acceptance criteria

Read the full text in #1373. Summary of what must land:

### AC-1 — 55 wikis segmented + ingested into `ukrainian_wiki` table
### AC-2 — FTS5 index + BM25 retrieval branch
### AC-3 — Source-weighting policy (HIGH for A1/A2, supplementary for B1+)
### AC-4 — Admission gate (non-empty, ≥50 chars, Cyrillic content, valid UTF-8)
### AC-5 — Tests (unit + integration on 5-sample subset)

### AC-6 (this brief) — Adversarial review

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
  "Adversarial review of #1373 A.6 wiki ingest. Read the diff. Look for: (1) segmentation strategy mismatch with existing textbooks corpus (chunk size/overlap inconsistencies create retrieval surprises), (2) FTS5 weighting that overweights wiki and starves textbook retrieval, (3) admission gate too lax (admits whitespace-only chunks) or too strict (rejects valid short paragraphs), (4) source-weighting policy applied at ingest time vs query time — should be query time (weights are policy, not data), (5) sidecar sources.yaml citation markers lost during chunk segmentation." \
  --task-id 1373-review
```

## Workflow

1. Create worktree per worktree instructions
2. Read source files (3-5 sample wikis + their sidecars), existing wiki_corpus code, sources.db schema, retrieval code
3. Implement AC-1 → AC-5 in order; commit per AC (or per logical chunk if AC is large)
4. Run AC-6 adversarial review; address findings; log them in PR body
5. Push, open PR with title `feat(retrieval): ingest 55 A1 Ukrainian wikis into sources.db.ukrainian_wiki (#1373)`
6. STOP. Do not merge. Do not run any subsequent A.7 / canary build.

## PR body template

```
## Summary
- AC-1: 55 wikis from `wiki/pedagogy/a1/*.md` segmented and ingested into `ukrainian_wiki` table (idempotent upsert)
- AC-2: FTS5 index `ukrainian_wiki_fts` + new retrieval branch in `scripts/retrieval/`
- AC-3: Source weighting — HIGH for A1/A2, supplementary for B1+ (configurable, defaults documented)
- AC-4: Admission gate (Cyrillic + ≥50 chars + UTF-8 valid)
- AC-5: Unit tests + 5-wiki integration test
- AC-6: Adversarial review (Claude) — N findings addressed, M rejected with rationale

## Test plan
- [ ] `.venv/bin/pytest tests/test_wiki_corpus_ingest.py -v` — all green
- [ ] Spot-check: `sqlite3 data/sources.db "SELECT COUNT(*) FROM ukrainian_wiki"` — confirm 55+ chunks
- [ ] Spot-check retrieval: `python -c "from scripts.retrieval import ...; print(query('special signs'))"` — returns ukrainian_wiki chunks
- [ ] Re-run ingestion script — confirm idempotent (no duplicates)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Done when

PR opened, all ACs documented, adversarial review noted, dispatch reports `done`. User reviews + merges. Then A.7 (canary A1 module against enriched corpus) becomes the next dispatch.
