# Session State: Wiki retrieval overhaul (#1553)

**Date**: 2026-04-25
**Owner**: Claude (autonomous; user signed off "make me proud")
**Issue**: #1553 — extends closed #1348
**Worktree**: `.worktrees/claude-1553-wiki-retrieval-overhaul`
**Branch**: `claude-1553-wiki-retrieval-overhaul`

## Why this exists

`oes/adjectives-agreement` build surfaced a tokenizer warning:
`(22174 > 8192)`. Investigation traced to two un-chunked corpora
(`textbook_sections`, `external_articles`) being silently truncated
to 512 tokens during dense reranking. BGE-M3 supports 8192 native
context but #1348 shipped at `INDEX_MAX_LENGTH=512` as a defensive
default. Wikipedia got chunked at 450/50 in #1348; other corpora
didn't. Result: retrieval ranking is degraded for the long-tail
corpora, but downstream LLM compilation still receives full text up
to the per-track char cap, so existing wikis aren't broken — just
suboptimally grounded.

Codex review (msg #449, #451) confirmed:
- BGE-M3 stays (the 2026-04 bakeoff already settled embedder choice)
- Two BLOCKERS before any re-encode:
  1. Manifest must version `(model_id, index_max_length, chunk_policy_version, pooling_mode)`
  2. Runtime candidate builders must align with chunk-level `unit_key`s
- Boundary-aware chunking (paragraph -> sentence -> token-window)
- Skip ColBERT this round (different architecture, defer)

User accepted: full re-encode + 1259-wiki rebuild. GDrive backup of
`wiki/` exists as recovery path.

## Plan (issue #1553)

0. Schema migration: version `embedding_units` config columns
1. Centralized + boundary-aware chunker; per-corpus policies
2. Align `sources_db.py` candidate builders with chunk-level keys
3. Validator + pytest gate (no unit > INDEX_MAX_LENGTH)
4. HF warning suppression (cosmetic, parallelizable)
5. Chunk-policy bakeoff (A: 512/no-chunk, B: 2048/1500t, C: 8192/4000t)
6. Re-encode all 6 corpora with bakeoff winner
7. Rebuild 1,259 wikis
8. Cleanup (drop old shards, VACUUM, archive intermediates)
9. **(Followup, separate issue)**: hierarchical summary tier

## Current state

- Issue #1553 filed
- Worktree created at `.worktrees/claude-1553-wiki-retrieval-overhaul`
- **STEP 0 SHIPPED (commit `d081e6a682`, PR #1555 draft)**
  - Schema v2: `EncoderConfig` dataclass, `LEGACY_SHIPPED_CONFIG`
  - In-place migration of `embedding_units` via `_ensure_schema_v2()`
  - `filter_new_or_changed` compares full config tuple
  - `append_shard` takes `encoder_config` once per shard
  - 5 new tests + parameterized stale-on-any-field test
  - 74/74 wiki tests pass, lint clean
- Codex review of step-0 implementation dispatched (msg #454)

## Next actions

1. Wait for Codex review of step 0 (PR #1555). Iterate if pushback.
2. Step 1: centralized boundary-aware chunker in `dense_rerank.py`
   - Per-corpus policies (`textbook_sections`, `external_articles`,
     others)
   - Paragraph -> sentence -> token-window fallback
   - Apply uniformly inside `load_corpus_units()`
   - Delete old `chunk_wikipedia_article`
3. Step 2: align `sources_db.py` candidate builders with chunk-level
   `unit_key`s + post-rerank parent/neighbor expansion
4. Step 3: validator gate (no unit > INDEX_MAX_LENGTH)
5. Step 4: HF warning suppression (parallelizable; can dispatch
   to Codex headless)
6. Step 5: chunk-policy bakeoff (A: 512/no-chunk, B: 2048/1500t,
   C: 8192/4000t)
7. Step 6: full re-encode under winner config
8. Step 7: rebuild 1259 wikis
9. Step 8: cleanup pass

## Codex collaboration model

Per user directive 2026-04-25: keep Codex involved on each design
decision; confrontation welcome if it drives forward. Workflow:
draft design -> ask-codex -> iterate to agreement -> implement.
Don't fire-and-forget. Don't agree silently.

## Bridge messages so far

- #448 -> #449: initial architecture review (model + chunking plan)
- #450 -> #451: prior-bakeoff context, revised plan
- #452 -> #453: step 0 schema design review (confirmed row-level
  + use centralized LEGACY constant + add model-only stale test)
- #454 -> #455: step 0 implementation review (BLOCKER: PRAGMA+ALTER
  is concurrency-racy, fix with BEGIN IMMEDIATE; add drift-guard
  test current_encoder_config == LEGACY_SHIPPED_CONFIG)
- #456 (in flight): step 1 centralized chunker design

## PRs

- **#1555 (open, ready for review)**: step 0 schema migration. Two
  commits (`d081e6a682`, `62b6314ca9`). 18 new tests. Lint clean.

## Steps 0-4 shipped checklist

### Step 0 (schema migration)
- [x] EncoderConfig dataclass + LEGACY_SHIPPED_CONFIG constant
- [x] embedding_units schema migrated in place via _ensure_schema_v2
- [x] Concurrency-safe migration (BEGIN IMMEDIATE + fast-path)
- [x] filter_new_or_changed compares full config tuple
- [x] append_shard takes encoder_config once per shard
- [x] Migration tests: legacy stamp, partial-v2, concurrent
- [x] Drift-guard test (current_encoder_config == LEGACY_SHIPPED_CONFIG)
- [x] Parameterized stale-on-any-field test (incl model-only)

### Step 1 (centralized boundary-aware chunker)
- [x] New `scripts/wiki/chunking.py` module
- [x] ChunkingPolicy dataclass + CHUNKING_POLICIES registry
- [x] Auto-derived version_id encoding params (no silent reuse)
- [x] policy_for() raises on unregistered corpora
- [x] Boundary-aware splitter: paragraph -> sentence -> token-window
- [x] Ukrainian abbreviation guard (вул., р., ст., проф., акад., …)
- [x] Sentence-aligned overlap (not raw token windows)
- [x] load_corpus_units() applies registry uniformly
- [x] Old chunk_wikipedia_article deleted
- [x] _iter_wikipedia_units simplified
- [x] 22 chunker unit tests
- [x] Drift-guard split: no-chunk vs actively-chunked corpora

### Step 2 (sources_db candidate alignment)
- [x] _search_wikipedia_candidates uses chunk_text(policy_for("wikipedia"))
- [x] _expand_wikipedia_neighbors aligned with chunk-level keys
- [x] _search_external_candidates emits chunk-level keys (commit ca68517a68)
- [x] textbook dispatcher uses _expand_to_chunk_candidates helper (ca68517a68)
- [x] All chunk candidates carry parent_unit_key for parent expansion
- [ ] Post-rerank parent expansion for textbook/external is mechanically
      possible via parent_unit_key but not yet wired in sources_db
      result aggregation. Deferred — will be needed if cold-encode
      tests during step 6 reveal a gap. Wikipedia precedent at
      _expand_wikipedia_neighbors shows the pattern.

### Step 3 (validator gate)
- [x] _assert_units_fit_index_window() runs in cold_encode_corpus
- [x] NO_CHUNK corpora exempt
- [x] Tests: validator raises on oversize, silent on NO_CHUNK

### Step 4 (HF warning suppression)
- [x] Logging filter on transformers.tokenization_utils_base
- [x] Only the specific "Token indices sequence length" message
- [x] Other warnings still surface

## Rebuild scope decision (2026-04-25 PM, post-merge)

User asked: "would the /tmp wiki logs help decide selective vs full rebuild?"

Logs aren't useful for that — HuggingFace emits the warning ONCE per
session (silenced after first), so logs only confirm the chunking
issue was active in every recent batch but not which specific wikis
were affected.

The `.sources.yaml` files DO answer the question. New script
`scripts/wiki/list_rebuild_targets.py` enumerates rebuild candidates:

```
.venv/bin/python scripts/wiki/list_rebuild_targets.py --summary
# Total wikis with sources.yaml: 1141
# Rebuild candidates: 754
#   of which high-priority (>=50% rechunked): 512
# Skipped (NO_CHUNK only): 387
```

**Recommendation**: rebuild 754 wikis (66%). Skip the 387 (34%) using
only literary/ukrainian_wiki/folk — their embeddings are bit-identical
post step-1 since those corpora keep NO_CHUNK policy. Rebuilding them
produces the same retrieval and same output modulo Gemini stochasticity.

The 512-wiki "high priority" subset (>=50% re-chunked sources) is for
incremental rebuilds when budget is tight.

## New tooling shipped on main (post-merge)

- `scripts/wiki/list_rebuild_targets.py` — enumerate step-7 rebuild
  candidates with `--summary` / `--high-priority` / `--skipped` flags.
- `scripts/wiki/cleanup_post_rebuild.py` — step 8 vacuum + orphan drop
  with `--dry-run` for safety.
- `docs/architecture/2026-04-25-chunk-policy-bakeoff-spec.md` —
  concrete spec for step 5 implementation, including monkey-patch
  pattern for cell config overrides and CLI surface.

## Steps 5-7 (REQUIRE USER'S MAC, deferred to user when back)

### Step 5: chunk-policy bakeoff
Cells to compare on the same 1000-sample gold set used in #1345
(`scripts/rag/benchmark_*`):
- Cell A: INDEX_MAX_LENGTH=512, no chunking (current shipped #1348)
- Cell B: INDEX_MAX_LENGTH=2048, paragraph-aware target=1500t / overlap=150t
- Cell C: INDEX_MAX_LENGTH=8192, paragraph-aware target=4000t / overlap=400t

Implementation sketch for the next agent:
1. Add a CLI flag to `scripts/wiki/cold_encode.py` accepting an
   override `EncoderConfig` (model / max_length / policy_version).
   For each cell, override CHUNKING_POLICIES, INDEX_MAX_LENGTH, then
   re-encode the gold-set subset (1000 random sample per corpus).
2. Run `scripts/rag/benchmark_embeddings.py` with the resulting
   manifest, capturing Recall@5, Recall@10, nDCG@10 per cell.
3. Write `docs/architecture/research/2026-04-25-chunk-policy-bakeoff.md`
   tabling results and naming the winner.
4. Update CHUNKING_POLICIES + INDEX_MAX_LENGTH in main code to the
   winner.

### Step 6: full re-encode
Once the winner config is in main:
- `cold_encode_corpus` for each of textbook / external / wikipedia
  with the new policy. Existing legacy units get marked stale,
  new units get encoded.
- ukrainian_wiki / literary stay NO_CHUNK so they aren't re-encoded.
- Estimated 4-8 hours on M-series Mac.

### Step 7: rebuild 1,259 wikis
- Iterate over all `wiki/**/*.md` slugs, call the wiki compile
  pipeline. New retrieval picks better top-K candidates.
- Estimated several days of Gemini compilation time. GDrive backups
  cover the recovery path.

### Step 8: cleanup pass
- Drop orphan shards via `manifest.vacuum_orphaned_shards()`.
- VACUUM the manifest.db to reclaim space.
- Archive the bakeoff intermediates.
- Verify no remaining references to `chunk_wikipedia_article` or
  the old `UnitSpecInput.model` field in any docs / fixtures.

## Followup issues to file (after this lands)

- Hierarchical summary tier (doc-level + chunk-level two-stage) —
  Codex confirmed this is the right next-architecture upgrade
  AFTER chunking is in. Tracks against the user's intuition that
  "summaries help" without compromising the chunking work.
- Cross-encoder reranker over top-100 dense candidates as a
  precision layer — Codex's recommended next-quality lever beyond
  the chunker.
- Qwen3-0.6B re-attempt if/when CPU or smaller-batch funding
  arrives (per the 2026-04 embedder survey).

## Recovery path (if I need to resume from a fresh session)

1. `gh issue view 1553` for plan + ACs
2. `cat docs/session-state/2026-04-25-wiki-retrieval-overhaul-1553.md` (this file)
3. `cd .worktrees/claude-1553-wiki-retrieval-overhaul && git log --oneline` for progress
4. `.venv/bin/python scripts/ai_agent_bridge/__main__.py conversation wiki-embedder-review` for Codex thread
5. Continue from "Next actions" section

## Files I expect to touch

- `scripts/wiki/embedding_manifest_schema.py` — schema additions
- `scripts/wiki/embedding_manifest.py` — `EncoderConfig`, filter update, migration
- `scripts/wiki/dense_rerank.py` — `_chunk_unit()`, INDEX_MAX_LENGTH bump, validator
- `scripts/wiki/sources_db.py` — candidate builder chunk-level keys
- `scripts/wiki/mlx_encoder.py` — HF warning filter (parallelizable)
- `tests/wiki/test_embedding_manifest.py` — schema migration tests
- `tests/wiki/test_chunking_policy.py` — new (boundary-aware chunker)
- `tests/wiki/test_chunk_size_validator.py` — new (validator gate)
- `docs/architecture/research/2026-04-25-chunk-policy-bakeoff.md` — new
- `docs/architecture/adr/adr-006-compile-layer-retrieval.md` — revision
