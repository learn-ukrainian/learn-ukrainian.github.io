# Session Handoff — 2026-04-20 ~00:45 (user-requested stop mid-overnight work)

User stopped me mid-way through the #1348 stage dispatch sequence. Nothing is running. Pick up here cleanly.

## TL;DR

- **#1347 literary metadata restoration — DONE** (commit `2824b3b70`)
- **#1348 stage (a) MLX encoder + subprocess bridge — DONE** (commit `428be007b`, parity cosine 1.000)
- **#1348 stage (b) embedding manifest + storage — DONE** (commit `59a419228`, 7 tests green, atomic append verified)
- **#1348 stage (c) retrieval rewire — NOT DISPATCHED.** Prompt is ready at `docs/session-state/pending-dispatches/1348-stage-c.md`. This is the next action.
- **Stages (d) + (e) not yet drafted.** Wait until (c) lands to know what the integrated shape looks like, then write them.

**No Codex task is running.** No Monitor is armed. Working tree has the same dirty state as earlier (pre-existing L1-UK brief + Phase 0 smoke artifacts — both unrelated, untouched by all of today's work).

## Commit chain (oldest → newest)

```
e26cab97a docs(session-state): corrigendum — L1-UK pivot IS real
2824b3b70 feat(sources): restore literary metadata (#1347)
f380357ca docs(session-state): overnight handoff (STALE — written before stage b landed)
428be007b feat(wiki): MLX encoder + subprocess bridge for BGE-M3 (#1348 stage-a)
59a419228 feat(wiki): embedding manifest + storage layer (#1348 stage-b)
```

The `f380357ca` handoff doc is pre-stage-b; this current handoff supersedes it.

## Evidence summary (what's been proven on this Mac)

### #1347 validation (from `batch_state/tasks/issue-1347.result`)
- `language_period` distribution: modern 107,436 + middle_ukrainian 20,050 + old_east_slavic 10,202 = **137,688 total** ✓
- Distinct `work_id`: 3,278 (legitimate — poetry anthologies create many singleton works)
- SHA256 text immutability: PASS (text column unchanged by migration)
- Idempotent rerun: 0 UPDATEs on second run ✓

### #1348 stage (a) — MLX bridge parity
- Test: 20 texts (mix modern + archaic)
- Per-text cosine(MLX fp16 + CLS pooling, FlagEmbedding fp16): **min 0.999998, mean 0.999999**
- Top-5 retrieval overlap: **20 / 20 (100%)**
- `embed-venv/` 719 MB, gitignored
- Subprocess bridge: lazy worker startup, auto-respawn + halved-batch retry on child OOM (max 3 retries)

### #1348 stage (b) — manifest atomic append
- `data/embeddings/manifest.db` schema: `embedding_shards` + `embedding_units` + 3 indexes
- 7 tests passed (schema init, atomic append happy path, fault injection, incremental classification, active units query, shard map, vacuum)
- Init DB size: 36 KB; 10K-row synthetic manifest: 1.8 MB
- Fault injection: SQLite commit crashed mid-way → `.npy` file auto-cleaned, `embedding_shards` empty → atomic guarantee holds

## What's still pending (in order)

### Stage (c) — Multi-corpus retrieval rewire (NEXT)

**Prompt**: `docs/session-state/pending-dispatches/1348-stage-c.md`

Scope: rewrite `dense_rerank.py` to use the stage-(a) MLX bridge + stage-(b) manifest; rewrite `sources_db.py::search_sources` for multi-corpus dispatch with per-track priors; rewire `enrichment.py`; add `track_priors.yaml` + `cold_encode.py` entry-point; integration tests. See file for full ACs.

**Resume command**:
```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent codex \
  --task-id issue-1348-c \
  --prompt-file docs/session-state/pending-dispatches/1348-stage-c.md \
  --mode danger \
  --hard-timeout 3600
```

Estimated runtime: 30–60 min Codex time. Will commit as `feat(wiki): multi-corpus retrieval + MLX integration (#1348 stage-c)`.

### Stage (d) — Tests + ADR revision (NOT DRAFTED)

Depends on stage (c) so we know what landed. Will cover:
- Exhaustive stress test (AC8 from #1348 issue body): 20 random textbook sections with varying char_count 200–50K, encode under `max_tokens=4096`, assert peak RSS ≤ 4 GB
- Fault-injection test: force MLX worker OOM, verify parent retries with halved batch
- Full `tests/wiki/` pytest green
- ADR-006 revision: replace the "T3-T4 metadata only" clause with full dense indexing decision, cite smoke-test evidence
- `.gitignore` verification (already added in stage a, just confirm no orphan rules needed)

Draft the prompt only after stage (c) merges.

### Stage (e) — Cold encode of 157K units (NOT DRAFTED)

**Runs on the user's Mac, NOT via Codex.** This is the ~2-hour local MLX inference pass that builds the actual `.npy` shards.

Script to call: `scripts/wiki/cold_encode.py --all-corpora` (created in stage c).

Memory safety stack verified by smoke tests:
- MLX fp16 + manual CLS-pooling (peak RSS 1,760 MB measured on 100-text sample)
- `mx.metal.set_memory_limit(0.7 × recommended)` hard cap
- Token-budget batching (max 16 rows OR 4096 tokens)
- `mx.metal.clear_cache()` between batches
- Child-process encoder isolation
- Shard checkpointing per source_file / per 5K-unit group

**Running this overnight is safe now** — original crash was PyTorch MPS + batch=128 + variable-length inputs; none of those conditions hold anymore. If it does fail, shards already written survive and `--resume` picks up where it stopped.

## Key design decisions (don't re-litigate)

1. **Framework: MLX fp16** — measured 43% less RAM than PyTorch MPS, bit-equivalent output with manual CLS-pooling
2. **Storage: `.npy` shards + separate SQLite manifest DB** at `data/embeddings/manifest.db` (NOT in `sources.db`, which gets wiped on rebuild)
3. **Corpus scope: ~157K units** — textbooks + modern literary + archaic literary (verbatim, no normalization) + external articles + chunked wikipedia
4. **Archaic text is sacred.** Encoded as-is; no ѣ→е, no abbreviation expansion, no character substitution. Any query-side normalization is a separate layer if ever needed.
5. **`language_period` canonical values**: `'modern'`, `'middle_ukrainian'`, `'old_east_slavic'` (verified from source JSONLs)
6. **`SOURCE_CHAR_CAPS`** (in `scripts/wiki/enrichment.py:22`) is the correct symbol for context capping — NOT `LEVEL_CHAR_BUDGETS` (does not exist)
7. **MLX community port needs manual CLS pooling** — the shipped checkpoint is missing `1_Pooling/config.json`; library defaults to mean-pooling which produces wrong vectors (cosine 0.68). Workaround is 7 lines and fully tested in stage (a)'s parity test.
8. **Dependency isolation**: MLX needs `transformers≥5.0.0`; main venv has 4.57.6. MLX lives in `embed-venv/` at project root, gitignored.
9. **Smoke-test evidence**: memory cap + child process + shard checkpointing reduce overnight-crash risk to near-zero. Running cold encode while user sleeps is viable.

## Files NOT touched (left as they were)

- `docs/session-state/2026-04-19-l1-uk-evidence-brief.md` — L1-UK pivot roadmap, orthogonal
- `wiki/.reviews/pedagogy/a1/sounds-letters-and-hello.json`, `wiki/pedagogy/a1/*` — Phase 0 smoke artifacts known-REJECT under old retrieval; will be rebuilt after #1348 lands
- Uncommitted v1 files in working tree: `scripts/wiki/dense_rerank.py`, `scripts/wiki/query_builder.py`, `tests/wiki/test_*.py` — stage (c) either overwrites `dense_rerank.py` entirely or consumes `query_builder.py` as-is

## Adversarial review archive (pre-file)

Gemini + Codex adversarial review of the #1347 + #1348 dispatch prompts caught **13 real bugs** before anything was filed. All 13 applied. Most material:

- Codex: schema migration must start in the builder (ALTER on already-built DB would get wiped on rebuild)
- Codex: `language_period` canonical value is `'modern'` not `'modern_literary'`
- Codex: embedding manifest must live in separate DB file (sources.db gets wiped on rebuild)
- Gemini: `np.concatenate(mmap arrays)` defeats mmap → use per-shard dict routing
- Gemini: `gc.collect()` doesn't free MLX Metal cache → `mx.metal.clear_cache()` mandatory
- Gemini: sort-WITHIN-batch is useless → sort full corpus BEFORE batching
- Gemini: dtype contradiction → fp16 end-to-end

Archived:
- `batch_state/tasks/review-1338v2.result` (Codex review)
- `/tmp/review-gemini.md` (Gemini review — not committed; copy somewhere durable if needed)

## Dispatch prompt archive (for forensics / reuse)

All prompts moved from `/tmp/` to `docs/session-state/pending-dispatches/`:

- `1347-ARCHIVED.md` — precursor dispatch used for #1347
- `1347-issue-body-ARCHIVED.md` — the GH issue body
- `1348-issue-body-ARCHIVED.md` — the #1348 GH issue body (full spec)
- `1348-stage-a-ARCHIVED.md` — stage (a) dispatch
- `1348-stage-b-ARCHIVED.md` — stage (b) dispatch
- `1348-stage-c.md` — **pending**, ready to dispatch

## Bridge bug

`ab discuss` still fails for Claude because pinned context gets passed as CLI flags. Worked around in this session by using `ask-gemini` + `ab post --to codex`. Worth a small follow-up issue if it becomes recurring.

## Open issues snapshot

| # | Title | Owner | Blocks on |
|---|---|---|---|
| #1346 | Qwen3 embedding benchmark follow-up | — | (parked) |
| #1344 | Replace Phase A canary wiki articles | claude | #1340 |
| #1342 | ADR-005 cross-ref + docs | claude | rolled into #1348 stage d |
| #1340 | Re-validate #1330 against new pipeline | claude | #1348 complete |
| #1339 | A1 grade filter bug | codex | — |
| #1335 | EPIC tracker | — | #1348 + #1340 + #1344 |
| #1334 | [PARKED] Reviewer incentive inversion | claude | — |
| #1333 | Corpus gap analysis + ingestion roadmap | codex | — |
| #1347 | Literary metadata restoration | codex | **CLOSED** |
| #1348 | Full-corpus dense retrieval | codex | **IN PROGRESS** — stage (c) next |
