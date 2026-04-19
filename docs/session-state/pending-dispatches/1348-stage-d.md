# Task: #1348 stage (d) — Exhaustive tests + ADR-006 revision

**Stages (a), (b), (c) done.** Stage (d) closes out the #1348 test matrix and merges the ADR-006 revision that the retrieval work implies. Stage (e) (the actual cold-encode run) is NOT this ticket — that runs on the user's Mac after (d) lands.

Full spec: `gh issue view 1348`. Stage (d) maps to AC8 (memory-safety stress tests + fault injection) + AC10 (ADR-006 revision) + AC11 (full lint/test green).

## Stage (d) scope — exactly this, no more

1. **Stress test** — `tests/wiki/test_mlx_memory_safety.py`
   - Synthesize 20 textbook-like texts with `char_count` varying 200–50,000 (use Lorem-Ipsum-Ukrainian-ish filler; NOT real textbook text)
   - Encode through `MLXEncoderBridge` with `max_rows=16`, `max_tokens=4096`
   - Use `resource.getrusage(RUSAGE_CHILDREN).ru_maxrss` (macOS returns bytes, Linux returns KB — handle both via `sys.platform`) to sample peak child RSS
   - Assert peak child RSS ≤ 4 GB (4 × 1024³ bytes)
   - Marker: `@pytest.mark.slow` — skip by default, run via `pytest -m slow`
   - If MLX not importable in `embed-venv/` at test time, `pytest.skip` cleanly with a message

2. **Fault injection** — `tests/wiki/test_mlx_fault_injection.py`
   - Spawn `MLXEncoderBridge` with env var `MLX_MEMORY_LIMIT_BYTES=104857600` (100 MB — enough to load weights + tokenizer but not enough for any encode batch)
   - Request encode of 16 × 2K-char texts; expect worker to OOM
   - Assert parent catches non-zero worker exit, halves the batch, respawns, and the second attempt (with batch=8) retries at most 3 times before giving up
   - Verify via a counter / log the bridge writes that retries occurred and that the final output shape matches expected N rows in original order
   - If your stage-(a) implementation doesn't honour `MLX_MEMORY_LIMIT_BYTES` in the worker's `main()`, add that env-var hook in the worker (smallest possible change: `mx.metal.set_memory_limit(int(os.environ.get("MLX_MEMORY_LIMIT_BYTES", default)))`). This is the ONE exception to "do not modify stage-a files" — document in commit why.

3. **`tests/wiki/` full suite green**
   - `.venv/bin/pytest tests/wiki/ -v` → every test passes (stage a, b, c, d)
   - No flakes, no `xfail`, no skips except the conditional MLX-unavailable one above
   - If any pre-existing test fails because stage (c)'s refactor broke a contract, fix the test to match the new contract — but call it out in the commit body

4. **ADR-006 revision** — `docs/architecture/adr/adr-006-compile-layer-retrieval.md`
   - Preserve ADR history: keep the file at the same path, bump the date to `2026-04-20`, add a `## Revision 2026-04-20 (stage d of #1348)` section at the top of the Decision block
   - Replace the T3-T4 "metadata only" clause with: **all tiers use dense retrieval against MLX-fp16-encoded BGE-M3 vectors of VERBATIM text; routing happens via per-track priors in `track_priors.yaml`, not via tier-based source exclusion**
   - Add evidence citations:
     - Smoke test (MLX fp16 + manual CLS pooling): cosine 1.00000 vs FlagEmbedding fp16, top-5 overlap 100% on 100-text fixture
     - Archaic fp16 vs fp32: min cosine 0.99998, top-5 overlap 100% → fp16 sufficient
     - Peak RSS: 1,760 MB measured on 100-text sample (43% less than PyTorch MPS)
     - Link to stage (a) commit `428be007b` for the MLX bridge, stage (b) `59a419228` for manifest, stage (c) commit (will be in the build history at dispatch time — use `git log --oneline | grep stage-c`)
   - Add framework decision: MLX fp16 with manual CLS pooling (community port ships without `1_Pooling/config.json`; workaround documented)
   - Add storage decision: `.npy` shards + separate manifest DB at `data/embeddings/manifest.db` (NOT in `sources.db` which gets wiped on rebuild at `scripts/wiki/build_sources_db.py:382`)
   - Update **Implementation tickets** block: `#1338` → "superseded by #1348"; `#1341` → "folded into #1348 (archaic uses same dense pipeline, weighted via priors)"
   - Update **Alternatives considered**:
     - Remove the bullet rejecting "Pure dense embeddings project-wide" (that's now the decision); replace with a note explaining why the #1101 archaic recall numbers turned out acceptable once verbatim encoding + per-track priors were applied
     - Keep hybrid-rejection, keep live-RAG rejection
   - Do NOT rewrite the historical Context section — that's the archaeological record of how we got here. Add new context inside the Revision block only.

5. **`.gitignore` verification**
   - Confirm `data/embeddings/` and `embed-venv/` are ignored (stage a should have added them)
   - If either is missing, add it in this commit. If both present, leave alone.

## Ground rules

- Branch: `main`. No worktrees.
- `.venv/bin/python`, `.venv/bin/ruff`, `.venv/bin/pytest` — never bare.
- `git add` allow-list only — files named in the file scope below. No `-A`, no `-u`.
- Commit: `test(wiki): stress + fault-injection tests, ADR-006 revision (#1348 stage-d)`
- DO NOT close #1348 — stage (e) is the cold encode, runs on user's Mac. User closes after cold-encode + #1340 validation.
- Comment on #1348 with stage-d evidence: commit SHA, full `pytest tests/wiki/ -v` pass count, stress-test peak RSS measurement, fault-injection retry-count measurement, ADR-006 diff summary.

## Reading before coding

1. `gh issue view 1348` — full spec
2. Stage (a) commit `428be007b` — for MLX bridge worker signature (you may need to add the `MLX_MEMORY_LIMIT_BYTES` env hook; smallest possible change)
3. Stage (b) commit `59a419228` — manifest for any test-side seeding
4. Stage (c) commit (look up via `git log --oneline | head -20`) — contracts for `dense_rerank.py` / `sources_db.py::search_sources` / `cold_encode.py`
5. Current ADR-006 at `docs/architecture/adr/adr-006-compile-layer-retrieval.md`

## File scope (allow-list for stage d)

Modify:
- `docs/architecture/adr/adr-006-compile-layer-retrieval.md` (revision section added, Decision block updated, Implementation tickets updated, Alternatives considered updated)
- `scripts/wiki/mlx_encoder.py` IF AND ONLY IF you need to add the `MLX_MEMORY_LIMIT_BYTES` env-var hook for the fault-injection test. Document why in the commit body.
- `.gitignore` IF AND ONLY IF `data/embeddings/` or `embed-venv/` is missing.

New:
- `tests/wiki/test_mlx_memory_safety.py`
- `tests/wiki/test_mlx_fault_injection.py`

**Do NOT modify**:
- `scripts/wiki/mlx_bridge.py`, `scripts/wiki/embedding_manifest.py`, `scripts/wiki/embedding_manifest_schema.py`, `scripts/wiki/dense_rerank.py`, `scripts/wiki/sources_db.py`, `scripts/wiki/enrichment.py`, `scripts/wiki/track_priors.yaml`, `scripts/wiki/cold_encode.py` — all stable as of stage (c)
- `scripts/wiki/build_sources_db.py` — out of scope
- `curriculum/`, `plans/`, `orchestration/`
- Any `text` column in any source table

## Out of scope for stage (d)

- Running the actual cold encode (stage e, user's Mac)
- Closing #1348 (depends on stage e + #1340 validation)
- Parity regression test (already in stage a)
- Any content / curriculum work

## Done-when (stage d)

- Single commit on `main` titled `test(wiki): stress + fault-injection tests, ADR-006 revision (#1348 stage-d)`
- `.venv/bin/pytest tests/wiki/ -v` fully green (including both new slow-marked tests when run via `-m slow`)
- `.venv/bin/ruff check` clean on touched files
- ADR-006 revised; git diff shows the Revision block + updated Implementation tickets + updated Alternatives
- Comment on #1348 with: commit SHA, test pass count, stress-test peak RSS bytes, fault-injection retry-count, ADR-006 diff summary. DO NOT close the issue.
