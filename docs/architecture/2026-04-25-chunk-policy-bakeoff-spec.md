# Chunk-policy bakeoff spec (#1553 step 5)

Date: 2026-04-25
Issue: #1553
Predecessor: `docs/architecture/research/2026-04-embedder-survey.md` (#1345)

## Why this exists

The 2026-04 embedder survey settled the model question (BGE-M3 wins).
What it did NOT settle is the chunking policy — every cell ran at
whatever ingest-time chunk size each corpus happened to have, which
for `textbook_sections` and `external_articles` was "no chunking,
silently truncated to 512 tokens by the encoder."

Step 1 of #1553 added a centralized boundary-aware chunker. Step 5
(this spec) measures whether the new chunker actually improves
retrieval quality, and at what target token size, before committing
to a full re-encode (step 6).

## Cells

Three configurations on the same 1000-sample gold set used in #1345.
Hold model = BGE-M3-mlx-fp16, pooling = CLS, query_max_length = 512
constant across cells.

| Cell | INDEX_MAX_LENGTH | target_tokens | overlap_tokens | Notes |
|------|---:|---:|---:|---|
| **A** (baseline) | 512 | 0 (NO_CHUNK on textbook/external; 450 on wikipedia) | 0/50 | The current shipped #1348 behavior. Reference. |
| **B** (recommended) | 2048 | 1500 | 150 | BAAI's recommended sweet spot; chunks fit fully in window. |
| **C** (max recall) | 8192 | 4000 | 400 | Pushes BGE-M3's 8192 context fully; trades intra-doc granularity for recall. |

## Implementation

The harness must:

1. **For each cell, override runtime config without permanent change.**
   - Cells A: use the current `CHUNKING_POLICIES`, `INDEX_MAX_LENGTH=512`
   - Cell B: temporarily monkey-patch
     ```python
     dense_rerank.INDEX_MAX_LENGTH = 2048
     chunking.CHUNKING_POLICIES["wikipedia"] = ChunkingPolicy(
         version_id="wikipedia:bakeoff-cell-B-1500t-o150-v1",
         target_tokens=1500, overlap_tokens=150)
     # Same for external, textbook_sections.
     ```
   - Cell C: target=4000, overlap=400, INDEX_MAX_LENGTH=8192. Same pattern.

2. **Re-encode the gold set's source pool** under each cell's config.
   The gold set is at `scripts/rag/benchmark_queries.yaml`; its
   `relevant_chunks` reference passages by chunk_id. Cell-specific
   manifest stored at `data/embeddings/bakeoff-cell-{A,B,C}/manifest.db`
   to avoid contaminating the production manifest.

   Use a separate `manifest_db` argument to `cold_encode_corpus` so
   the production state is untouched until the winner is committed:
   ```python
   cold_encode_corpus(
       "textbook_sections",
       db_path=DEFAULT_DB_PATH,
       manifest_db=Path(f"data/embeddings/bakeoff-cell-{cell_id}/manifest.db"),
   )
   ```

3. **Run the existing benchmark** at `scripts/rag/benchmark_embeddings.py`
   pointing at the cell-specific manifest. The benchmark already computes
   Recall@5, Recall@10, nDCG@10 per period (modern / middle_ukrainian /
   old_east_slavic).

4. **Compare cells**: write `docs/architecture/research/2026-04-25-chunk-policy-bakeoff-results.md`
   with the result matrix. Pick the cell with the best `modern Recall@10`
   that doesn't regress the archaic tiers below #1345's recorded
   baseline (BGE-M3 dense modern=1.00, middle=0.50, oes=0.30).

5. **Commit the winner** to `scripts/wiki/chunking.py` and `dense_rerank.py`:
   - Update `CHUNKING_POLICIES` to use the winner's params.
   - Bump `INDEX_MAX_LENGTH` to the winner's value.
   - Bump `_STEP1_TARGET_TOKENS` / `_STEP1_OVERLAP_TOKENS` accordingly.
   - The auto-derived `version_id` will mechanically force re-encode
     of textbook/external/wikipedia (step 6).

## Suggested CLI surface

```
.venv/bin/python scripts/wiki/run_chunk_policy_bakeoff.py \
    --cells A,B,C \
    --output-dir docs/architecture/research/ \
    --sample-size 1000

# Resume after a crash
.venv/bin/python scripts/wiki/run_chunk_policy_bakeoff.py \
    --cells B,C \
    --resume

# Just one cell for debugging
.venv/bin/python scripts/wiki/run_chunk_policy_bakeoff.py --cells B
```

## Cost estimate

- Encoding a 1000-sample subset per cell at 4000-token chunks: ~30 min
  on M-series Mac.
- Three cells: ~90 min total encode.
- Benchmark scoring: ~5 min per cell.
- Write-up: human time.

Total: ~2 hours wall-clock for a clean winner decision.

## Risk + recovery

- Cell-specific manifests live in `data/embeddings/bakeoff-cell-{A,B,C}/`.
  Delete that subtree to roll back; production manifest is untouched.
- The benchmark gold set in `scripts/rag/benchmark_queries.yaml` is
  read-only. No risk of corrupting the regression-test baseline.

## Stop conditions

Bakeoff fails if:

- Cell B regresses any of the #1345 baselines on modern (1.00
  Recall@10, 0.997 nDCG@10) by >5%.
- Cell C catches up on modern but tanks middle_ukrainian below 0.40
  Recall@10 (#1345 baseline 0.50).

In either case, document the result and stay on Cell A (current
behavior). The chunker stays in main but the bakeoff doesn't
trigger an encoder ceiling bump.

## Followup-only

After step 5 lands a winner:

- **Step 6**: full re-encode of textbook/external/wikipedia with
  winner config. Manifest auto-detects stale rows via the
  `chunk_policy_version` change.
- **Step 7**: rebuild the **754** wikis that touch a re-chunked
  corpus (per `scripts/wiki/list_rebuild_targets.py`). Skip the
  387 NO_CHUNK-only wikis — their embeddings are bit-identical.
- **Step 8**: `scripts/wiki/cleanup_post_rebuild.py` to drop orphan
  shards and VACUUM.
