# Session Handoff — 2026-04-19 night → 2026-04-20 morning

You went to sleep. Here's where things stand and what's running.

## TL;DR — the single plan

- Staged dispatch of #1348 to Codex overnight: **(a) MLX bridge done → (b) manifest storage IN PROGRESS → (c) retrieval rewire → (d) tests + ADR + cold-encode script → (e) actual cold encode of 157K units on your Mac**
- **Stage (e) runs tonight if and only if (a)–(d) all land clean.** Revised from an earlier draft of the plan which wrongly postponed the cold encode.
- If anything crashes: shards already written survive, manifest up to date, clear resume command in this file.
- You wake up to either: fully indexed 157K-unit dense corpus, OR a clean partial state with exact resume instructions. Not to a frozen machine.

## Why running the cold encode overnight is safe now (vs. why the first attempt crashed)

First attempt (pre-smoke-test): `SECTION_BATCH_SIZE=128` + variable-length inputs up to 484K chars + PyTorch MPS + FlagEmbedding autocast fp16 → 8–12 GB memory spike per batch → machine hang.

Now:
- MLX fp16 end-to-end (no autocast parallel-path overhead) — measured peak 1,760 MB vs PyTorch MPS 3,098 MB on the same 100-text smoke sample
- Token-budget batching: `max_rows=16` OR `max_tokens=4096`, whichever binds first (not fixed 128 rows)
- `mx.metal.set_memory_limit(int(recommended_max_working_set * 0.7))` hard cap — prevents the allocator from reaching system-wide memory pressure
- `mx.metal.clear_cache()` + `gc.collect()` between every batch
- Child-process encoder isolation: parent kills child on OOM, halves batch, retries (max 3 before giving up)
- Shard checkpointing per source_file / per 5K-unit group: each shard atomically committed (tmp → fsync → rename → SQLite transaction) so crash at unit 80,000 loses at most the one in-flight shard (~1 min of work)
- Fallback: `EMBED_FRAMEWORK=pytorch_mps` env var reverts to FlagEmbedding path if MLX path has issues

Risk is bounded. If the encode crashes, you wake up to a partial state, NOT a frozen Mac.

## Chain state (what's in git right now)

| # | Title | State | Commit / evidence |
|---|---|---|---|
| #1338 | original textbook-only scope | ✅ closed as superseded | — |
| #1347 | literary metadata restoration | ✅ done | `2824b3b70` — 137,688 rows, period distribution correct, SHA256 text immutability verified |
| #1348 | full-corpus dense retrieval (MLX + hybrid) | 🔄 in progress | stages below |
| #1348 stage (a) — MLX encoder + subprocess bridge | ✅ done | `428be007b` — parity min cosine 0.999998, mean 0.999999, top-5 overlap 20/20; `embed-venv/` 719 MB gitignored |
| #1348 stage (b) — embedding manifest + storage | 🔄 running | dispatched 22:32 (Codex PID 47802) |
| #1348 stage (c) — retrieval rewire | ⏸ queued | blocks on (b) |
| #1348 stage (d) — tests + cold-encode script + ADR-006 revision | ⏸ queued | blocks on (c) |
| #1348 stage (e) — cold encode of full 157K corpus | ⏸ queued | blocks on (d); runs on user's Mac |

## What's happening while you sleep

Tonight, sequentially:

1. **Monitor fires when stage (b) finishes.** I verify the commit + tests green, then dispatch stage (c).
2. **Stage (c)** (estimated 30–60 min Codex time): rewire `scripts/wiki/dense_rerank.py` + `scripts/wiki/enrichment.py` + `scripts/wiki/sources_db.py::search_sources` for multi-corpus dispatch, per-track priors via `scripts/wiki/track_priors.yaml`.
3. **Stage (d)** (estimated 30–60 min Codex time): write the `scripts/wiki/cold_encode.py` entry-point script, full test suite, ADR-006 revision.
4. **Stage (e) — run cold encode on your Mac.** This is the one local-execution step. Logged to `logs/cold_encode_2026-04-20_HHMMSS.jsonl`. Expected runtime ~2 hours. I watch for OOM / timeout / error via Monitor on the JSONL event stream.

Estimated completion: stages (a)–(d) done by ~01:00, cold encode done by ~03:00. If Codex stages take longer than estimated, cold encode gets pushed back or postponed.

## What I will NOT do tonight

- Touch any `text` column in any source table (archaic text stays verbatim)
- Modify `curriculum/`, `plans/`, `orchestration/`
- Dispatch stage (e) cold encode if ANY prior stage failed validation
- Retry a failed stage more than once
- Run content builds (`v6_build.py`) — not in scope
- Decide any new architectural trade-offs without measured evidence

## Hard constraints the Codex dispatches respect (baked into each stage prompt)

- `.venv/bin/python` / `.venv/bin/ruff` / `.venv/bin/pytest` — never bare `python`
- `git add` allow-list only — no `-A` / `-u`
- Each stage is one commit on `main`, with the issue number in the message
- Do not close #1348 until stage (d) completes
- Verify with ruff + pytest before commit
- Never touch files outside the explicit allow-list for the stage

## Resume commands (if you wake up to a partial state)

**If stages (a)–(d) completed but (e) did not run or crashed mid-run:**
```bash
# Verify the manifest is consistent
.venv/bin/python -c "from scripts.wiki.embedding_manifest import EmbeddingManifest; print(EmbeddingManifest().stats())"

# Resume cold encode — picks up from the last checkpoint
.venv/bin/python scripts/wiki/cold_encode.py --all-corpora --resume
```

**If stages (a)–(b) done and (c) or (d) failed:**
```bash
# See which stages landed
git log --oneline main -10 | grep "#1348 stage"

# For each missing stage, the dispatch prompts are at:
ls /tmp/codex-1348-stage-*.md
```

**If you need to start the cold encode yourself** (e.g. I was unable to get stages through by wake-up):
```bash
EMBED_FRAMEWORK=mlx .venv/bin/python scripts/wiki/cold_encode.py --all-corpora 2>&1 | tee logs/cold_encode_$(date +%Y-%m-%d_%H%M%S).jsonl
```

## Key measured evidence (from 2026-04-19 smoke test on your Mac)

| Framework | Warm load | Encode 100 texts × batch=8 | Peak RSS | Parity vs canonical BGE-M3 |
|---|---|---|---|---|
| MLX fp16 + manual CLS-pooling | 2.62s | 19.88s | 1,760 MB | cosine=1.00000, 100% top-5 overlap |
| PyTorch MPS + FlagEmbedding fp16 | 9.81s | 20.77s | 3,098 MB | reference |
| MLX 8bit | — | 20.61s | 1,516 MB (−12%) | cosine=0.99964, 99% top-5 overlap — rejected, too much quality loss |

fp16 vs fp32 on modern AND archaic: cosine ≥ 0.99998, 100% top-5 overlap → fp16 is sufficient everywhere.

## Infra + process notes

- **MLX community port quirk**: `mlx-community/bge-m3-mlx-fp16` is missing `1_Pooling/config.json`. The library defaults to mean-pooling → wrong vectors (cosine 0.68). Manual CLS-pooling is mandatory, baked into the stage (a) encoder script.
- **Dependency isolation**: MLX requires `transformers≥5.0.0`; main venv has 4.57.6 (FlagEmbedding/peft/sentence-transformers/marker-pdf/surya-ocr depend on 4.x). MLX lives in `embed-venv/` (project root, gitignored) and is called via subprocess bridge.
- **Manifest DB location**: `data/embeddings/manifest.db` — separate SQLite file, NOT a table in `sources.db`. Reason: `scripts/wiki/build_sources_db.py:382` deletes sources.db on rebuild; putting embedding tables there would orphan all shards on next rebuild.
- **Archaic text is encoded verbatim**. No orthographic normalization. `ѣ`, `ѳ`, `ъ`-endings stay as-is. Primary-source integrity is non-negotiable.

## Adversarial review archive

Full 2026-04-19 discussion: `architecture` channel thread `dacd16a8b81b4d09`. Gemini + Codex caught 13 real bugs in the initial ticket drafts before they were filed. All 13 applied. Specific wins:

- Codex: schema migration must start in the builder (ALTER on already-built DB gets wiped on rebuild)
- Codex: `language_period` canonical value is `'modern'` not `'modern_literary'` (source JSONLs verified)
- Gemini: `np.concatenate(mmap'd arrays)` defeats mmap — use per-shard dict routing instead
- Gemini: `gc.collect()` doesn't free MLX Metal cache — `mx.metal.clear_cache()` is mandatory
- Both agreed: keep archaic text untouched at encoding time; normalize only at QUERY time if needed at all

Saved: `batch_state/tasks/review-1338v2.result` (Codex), `/tmp/review-gemini.md` (Gemini).

## Files left untouched (by design)

- `docs/session-state/2026-04-19-l1-uk-evidence-brief.md` — L1-UK pivot roadmap, orthogonal to this thread
- `docs/session-state/2026-04-19-evening.md` — previous handoff, archived
- `wiki/.reviews/pedagogy/a1/sounds-letters-and-hello.json`, `wiki/pedagogy/a1/*` — Phase 0 smoke artifacts known-REJECT under old retrieval; will be rebuilt after #1348 lands
- Pre-existing uncommitted work from earlier sessions (`scripts/wiki/dense_rerank.py`, `scripts/wiki/query_builder.py`, `tests/wiki/test_*.py`) — integrated by stage (c)

## Bridge bug still open

`ab discuss` fails for Claude because pinned context gets passed as CLI flags. Worked around this session by using `ask-gemini` + `ab post --to codex`. Worth a small follow-up issue if it becomes recurring.
