# Task: #1348 stage (c) — Multi-corpus retrieval rewire

**Stages (a) + (b) done**: `428be007b` (MLX bridge, parity 1.00000) and `59a419228` (embedding manifest + atomic shards). Stage (c) is the big one — wire the MLX encoder + manifest into the retrieval pipeline and switch `search_sources` to multi-corpus dispatch with per-track priors.

Full spec: `gh issue view 1348`. Stage (c) maps to AC3 (corpus coverage) + AC4 (mmap-preserving startup) + AC6 (multi-corpus retrieval with priors) + AC7 (incremental append).

## Stage (c) scope — exactly this, no more

- Rewrite `scripts/wiki/dense_rerank.py` — swap `TextEncoder` (FlagEmbedding path) for `MLXEncoderBridge`; write via `EmbeddingManifest`; matrix load preserves mmap (per-shard dict, NO `np.concatenate` on mmap arrays); token-budget batching with sort-BEFORE-batch; token-budget logic via tokenizer
- Rewrite `scripts/wiki/sources_db.py::search_sources` — multi-corpus dispatch, per-track priors, merged top-K
- Rewrite `scripts/wiki/enrichment.py` — wire `search_sources(strategy="unified_dense")`, respect `SOURCE_CHAR_CAPS[track]` (NOT `LEVEL_CHAR_BUDGETS` — that symbol does not exist)
- Rewrite `scripts/wiki/query_builder.py` IF needed — probably stays, but confirm it works cleanly with the new dispatch
- New: `scripts/wiki/track_priors.yaml` — per-track corpus weights, loaded at module init
- New: `scripts/wiki/cold_encode.py` — entry-point script for the full-corpus cold encode (used in stage e)
- Tests: multi-corpus retrieval returns merged + prior-weighted results; neighbor context expansion correct; incremental append smoke test

**Do NOT write the parity regression test or stress test** — those are stage (d). This stage is the integration; stage (d) is the exhaustive test suite + ADR revision.

## Ground rules

- Branch: `main`. No worktrees.
- `.venv/bin/python`, `.venv/bin/ruff`, `.venv/bin/pytest` — never bare.
- `git add` allow-list only — files named in AC1–AC8. No `-A`, no `-u`.
- Commit: `feat(wiki): multi-corpus retrieval + MLX integration (#1348 stage-c)`
- DO NOT close #1348.
- Comment on #1348 with stage-c evidence: commit SHA, test pass counts, synthetic 1K-unit retrieval demo output showing per-track prior scoring.

## Reading before coding

1. `gh issue view 1348` — full spec
2. Stage (a) commit `428be007b` — `scripts/wiki/mlx_bridge.py::MLXEncoderBridge` is the encoder to call
3. Stage (b) commit `59a419228` — `scripts/wiki/embedding_manifest.py::EmbeddingManifest` + `append_shard` + `filter_new_or_changed` are the storage entry points
4. Existing uncommitted v1 work: `scripts/wiki/dense_rerank.py`, `scripts/wiki/query_builder.py` — these are the files you'll be rewriting. The v1 versions were for textbook-only PyTorch MPS; stage (c) replaces them.
5. `scripts/wiki/enrichment.py:22` — **`SOURCE_CHAR_CAPS`** (verified; `LEVEL_CHAR_BUDGETS` does not exist anywhere)
6. The smoke-test evidence in `docs/session-state/current.md` — especially the CLS-pooling + sort-before-batch notes

## Acceptance criteria

### AC1 — `dense_rerank.py` rewrite

Replace the existing `scripts/wiki/dense_rerank.py` (the uncommitted v1 file with FlagEmbedding + fixed-batch logic) with a new implementation:

- Import `MLXEncoderBridge` from `scripts/wiki/mlx_bridge.py` (main venv — MLX is in a subprocess, not imported here)
- Import `EmbeddingManifest`, `append_shard`, `filter_new_or_changed` from `scripts/wiki/embedding_manifest.py`
- Fallback: if `EMBED_FRAMEWORK=pytorch_mps` env var is set, use `FlagEmbedding.BGEM3FlagModel` in-process. Default = MLX via subprocess.
- **Token-budget batching**: sort the FULL corpus by token count first, THEN form batches (each batch fills until `max_rows=16` OR `max_tokens=4096`, whichever binds). Preserve original `unit_key` → output-row mapping so the manifest records the right positions.
- **Matrix load at startup**: per-corpus, build a dict `{shard_id: np.memmap}` using `np.load(path, mmap_mode='r')`; build a second dict `{unit_key: (shard_id, row_idx)}` from the manifest. DO NOT `np.concatenate` mmap arrays — that defeats the lazy-load property.
- **Rerank query path**: given N candidate `unit_key`s (from FTS5 upstream or whoever), look up each `(shard_id, row_idx)` via the dict, fetch those specific rows from the shards (still mmap), stack into an `(N, 1024)` fp32 array on the fly, compute cosine with query vector, sort, return top-K.
- Query vector encoding: single-text `encode([query])` via the MLX bridge; cache the result keyed by query hash.
- `mx.metal.clear_cache()` + `gc.collect()` between batches during cold encode.

### AC2 — `sources_db.py::search_sources` multi-corpus dispatch

Replace or extend the existing `search_sources` function:

```python
def search_sources(
    query: str,
    *,
    track: str,
    strategy: str = "unified_dense",
    limit: int = 10,
    candidate_k_per_corpus: int = 30,   # pre-rerank candidate pool size per corpus
) -> list[SectionMatch]:
```

- `strategy="unified_dense"`: for each corpus (`textbook_sections`, `modern_literary`, `archaic_literary`, `external`, `wikipedia`):
  1. FTS5 (existing path) to get top-`candidate_k_per_corpus` candidates per corpus (grade-routed where applicable, e.g. textbooks use `_TRACK_GRADE_RANGES`)
  2. Dense rerank those candidates against the query via `dense_rerank.py`
  3. Apply per-track prior from `track_priors.yaml`: `final_score = cosine * prior[track][corpus]`
  4. Return top scorers per corpus
- Merge top-K across corpora by `final_score`, return top-`limit` overall
- For literary + wikipedia hits, expand to include ±1 neighbor chunks from same `parent_key` (work_id / source_file)
- Respect context cap `SOURCE_CHAR_CAPS[track]` when assembling the returned packet
- `strategy="archaic_metadata"`: legacy — keep for testing; calls FTS5 + period filter, no dense

Parallelize per-corpus sub-queries with `concurrent.futures.ThreadPoolExecutor(max_workers=5)`.

**`language_period` values in `literary_texts`**: `'modern'`, `'middle_ukrainian'`, `'old_east_slavic'` (confirmed from source JSONLs and restored by #1347). `modern_literary` corpus filter = `WHERE language_period = 'modern'`; `archaic_literary` = `WHERE language_period IN ('middle_ukrainian', 'old_east_slavic')`.

### AC3 — `track_priors.yaml`

`scripts/wiki/track_priors.yaml` — exactly this file, committed:

```yaml
# Per-track corpus priors. Multiplicative weights on cosine scores.
# Tune after #1340 validation. These are starting values.
a1:   {textbook: 1.0, modern_literary: 0.3, archaic_literary: 0.1, external: 0.5, wikipedia: 0.2}
a2:   {textbook: 1.0, modern_literary: 0.4, archaic_literary: 0.1, external: 0.6, wikipedia: 0.3}
b1:   {textbook: 0.9, modern_literary: 0.5, archaic_literary: 0.2, external: 0.7, wikipedia: 0.4}
b2:   {textbook: 0.8, modern_literary: 0.7, archaic_literary: 0.3, external: 0.6, wikipedia: 0.4}
c1:   {textbook: 0.5, modern_literary: 1.0, archaic_literary: 0.7, external: 0.4, wikipedia: 0.5}
c2:   {textbook: 0.3, modern_literary: 1.0, archaic_literary: 0.9, external: 0.3, wikipedia: 0.5}
hist: {textbook: 0.5, modern_literary: 0.8, archaic_literary: 1.0, external: 0.4, wikipedia: 0.6}
lit:  {textbook: 0.4, modern_literary: 1.0, archaic_literary: 1.0, external: 0.3, wikipedia: 0.4}
ruth: {textbook: 0.3, modern_literary: 0.7, archaic_literary: 1.0, external: 0.2, wikipedia: 0.5}
oes:  {textbook: 0.2, modern_literary: 0.5, archaic_literary: 1.0, external: 0.1, wikipedia: 0.4}
```

Loaded at `search_sources` module init; cached in memory.

### AC4 — `enrichment.py` rewire

Update `scripts/wiki/enrichment.py::enrich_sources` to call `search_sources(strategy="unified_dense")` for all non-archaic tracks. Archaic tracks (RUTH, OES) legitimately expect archaic-weighted retrieval; since priors handle that now, ALL tracks can use `unified_dense`. No special-casing.

Respect existing `SOURCE_CHAR_CAPS[track]` (line 22) when assembling the final per-section packet sent to the compile prompt. Each returned section's `full_text` becomes one source block; `parent_key` neighbors are grouped.

### AC5 — `query_builder.py` stays or minimal touch

The existing v1 `scripts/wiki/query_builder.py` already does bucket-A / bucket-B phrase extraction from discovery YAML. Stage (c) likely leaves it alone EXCEPT: if it was hard-coded for textbook-only, expand to accept the full corpus set. If it's already corpus-agnostic, leave it untouched.

### AC6 — `cold_encode.py` entry point

New `scripts/wiki/cold_encode.py`:

```bash
.venv/bin/python scripts/wiki/cold_encode.py --all-corpora [--resume] [--corpora textbook,modern_literary,...]
```

Behavior:
- For each requested corpus, iterate source rows from `data/sources.db`
- Compute `text_sha256` for each row
- Call `EmbeddingManifest.filter_new_or_changed` → get `new_keys` and `stale_keys`
- If no new/stale keys and `--resume` not passed → print "up to date" and skip corpus
- Otherwise: use `MLXEncoderBridge` to encode texts (batched via token-budget path), call `append_shard` per natural grouping (per `source_file` for textbooks/literary, per 1000 units for external/wikipedia)
- Mark stale keys via `mark_stale` before writing new shards
- Emit JSONL progress events to stdout: `{"event": "shard_written", "corpus": ..., "shard_id": ..., "units": ..., "elapsed_s": ...}`
- Final summary event: `{"event": "corpus_done", "corpus": ..., "total_units": ..., "total_shards": ..., "total_time_s": ...}`
- `--all-corpora` does all 5 (textbook_sections, modern_literary, archaic_literary, external, wikipedia) in sequence
- `--resume` picks up where a crash left off (manifest is the source of truth; already-encoded unit_keys are skipped)
- Respect `MEMORY_FRACTION_OVERRIDE` env var → passes through to MLX bridge

Wikipedia handling: before encoding, chunk each `wikipedia.text` to ~450 tokens with 50-token overlap, emit chunks as `wikipedia:{title}:chunk_{N}` unit_keys.

### AC7 — Integration tests

`tests/wiki/test_multi_corpus_retrieval.py`:
1. **Synthetic 5-corpus manifest**: build a fake manifest with 20 units across 5 corpora (4 per corpus), each with hand-crafted 1024-dim vectors where you KNOW which corpus wins a given query. Test `search_sources` returns them in the expected prior-weighted order for 3 tracks (a1, c2, lit).
2. **Neighbor expansion**: set up 3 literary chunks with same `parent_key` → query that's closest to the middle chunk → verify return packet includes `±1` neighbors.
3. **Char cap enforcement**: set `SOURCE_CHAR_CAPS[test_track] = 1000` → stuff enough candidates that raw return would exceed → assert returned packet is ≤1000 chars.
4. **Archaic legacy strategy**: `search_sources(strategy="archaic_metadata", track="ruth")` returns FTS5-only results filtered to `language_period IN ('middle_ukrainian','old_east_slavic')`.

`tests/wiki/test_cold_encode.py`:
5. **Incremental append smoke**: seed a manifest with 10 units in corpus `test_small`. Add 3 new rows to a synthetic source table. Run `cold_encode --corpora test_small` → assert 3 new units added, 10 existing untouched, new shard appended.
6. **Content-hash detection**: modify the text of 2 existing units. Rerun `cold_encode` → those 2 marked stale + re-encoded + new shard; other 8 untouched.

All tests run against synthetic data in `tmp_path`; no real `data/sources.db` or real `data/embeddings/manifest.db`.

### AC8 — Lint + test

- `.venv/bin/ruff check scripts/wiki/dense_rerank.py scripts/wiki/sources_db.py scripts/wiki/enrichment.py scripts/wiki/cold_encode.py scripts/wiki/track_priors.yaml tests/wiki/test_multi_corpus_retrieval.py tests/wiki/test_cold_encode.py` clean (yaml is parsed, not lint'd — skip ruff on it; just confirm it parses via `python -c "import yaml; yaml.safe_load(open(...))"`)
- `.venv/bin/pytest tests/wiki/test_multi_corpus_retrieval.py tests/wiki/test_cold_encode.py -v` green
- Backward-compat: existing tests in `tests/wiki/` that stage (a) and (b) added must still pass

## File scope (allow-list for stage c)

Modify:
- `scripts/wiki/dense_rerank.py` (complete rewrite of the v1 uncommitted file)
- `scripts/wiki/sources_db.py` (extend `search_sources` + add multi-corpus dispatch)
- `scripts/wiki/enrichment.py` (rewire to call new `search_sources`)
- `scripts/wiki/query_builder.py` IF needed (probably not)

New:
- `scripts/wiki/track_priors.yaml`
- `scripts/wiki/cold_encode.py`
- `tests/wiki/test_multi_corpus_retrieval.py`
- `tests/wiki/test_cold_encode.py`

**Do NOT modify**:
- `scripts/wiki/mlx_encoder.py`, `scripts/wiki/mlx_bridge.py` (stage a)
- `scripts/wiki/embedding_manifest.py`, `scripts/wiki/embedding_manifest_schema.py` (stage b)
- `scripts/wiki/build_sources_db.py` (precursor handled the schema; manifest DB is separate)
- `.gitignore` (stage a covered it)
- `docs/architecture/adr/adr-006-*.md` (stage d)
- `curriculum/`, `plans/`, `orchestration/`
- Any `text` column in any source table

## Out of scope for stage (c)

- Stress test (stage d)
- ADR-006 revision (stage d)
- Running the actual cold encode (stage e, user's Mac, user-supervised or overnight)
- Parity regression test (stage a already committed one)

## Done-when (stage c)

- Single commit on `main` titled `feat(wiki): multi-corpus retrieval + MLX integration (#1348 stage-c)`
- All 6 new tests green; existing stage (a)/(b) tests still green
- `ruff` clean
- `cold_encode.py --all-corpora --dry-run` (if you add that flag) or at minimum `cold_encode.py --help` runs without exception
- Comment on #1348 with: commit SHA, test pass counts, synthetic 1K-unit dispatch output showing per-track priors taking effect
