# Task: #1348 stage (a) — MLX encoder + subprocess bridge

Full spec: `gh issue view 1348`. This is the FIRST of 4 stages; do not attempt the whole ticket in one pass. Scope of stage (a) is defined below. Subsequent stages (b), (c), (d) will be dispatched separately after this one lands.

## Stage (a) scope — exactly this, no more

Set up the MLX encoder path: isolated venv, subprocess-based bridge from main venv, `.gitignore` updates, parity test against FlagEmbedding. Nothing else.

## Ground rules

- Branch: `main` (no worktrees)
- `.venv/bin/python`, `.venv/bin/ruff`, `.venv/bin/pytest` — never bare `python`
- `git add` allow-list only: files named in AC1–AC5 below. No `-A`, no `-u`.
- Commit: `feat(wiki): MLX encoder + subprocess bridge for BGE-M3 (#1348 stage-a)`
- DO NOT close #1348 — this is only stage (a) of 4.
- Leave a comment on #1348 with stage-a evidence (commit SHA, parity test output, embed-venv size).

## Reading before coding

1. `gh issue view 1348` — full spec; stage (a) maps to AC1 + AC2 + AC9 of the issue body
2. `docs/session-state/current.md` — smoke-test evidence baseline
3. Existing uncommitted files in working tree: `scripts/wiki/dense_rerank.py`, `scripts/wiki/query_builder.py`. **Do NOT modify these in stage (a)** — they'll be reworked in stage (c). Leave them alone.

## Key measured facts

- MLX community checkpoint `mlx-community/bge-m3-mlx-fp16` ships **without** `1_Pooling/config.json`. The `mlx_embeddings` library defaults to mean-pooling which produces WRONG vectors (cosine 0.68 vs FlagEmbedding). Manual CLS-pooling is REQUIRED — cosine becomes 1.00000 bit-equivalent.
- Canonical BGE-M3 pooling: `cls = out.last_hidden_state[:, 0, :]; norms = sqrt(sum(cls²)); vectors = cls / norms`
- Main venv has `transformers 4.57.6`; `mlx-embeddings` requires `transformers>=5.0.0` — incompatible. Use isolated `embed-venv`.

## Acceptance criteria

### AC1 — Isolated `embed-venv/` at project root

Create via: `~/.pyenv/versions/3.12.8/bin/python -m venv embed-venv`

Install: `embed-venv/bin/pip install mlx mlx-embeddings sentencepiece protobuf filelock`

Verify after install:
```bash
embed-venv/bin/python -c "import mlx.core as mx; import mlx_embeddings; print('device:', mx.default_device())"
```
Expected: `device: Device(gpu, 0)`

### AC2 — `.gitignore` entries for generated artifacts

Add to `.gitignore` (group with existing `data/` entries starting line 157 if present, else append):
```
embed-venv/
data/embeddings/
```

Verify `git status` does NOT show `embed-venv/` after it's created.

### AC3 — `scripts/wiki/mlx_encoder.py` (runs inside embed-venv)

Worker script, stdin/stdout JSON protocol. This file is EXECUTED by `embed-venv/bin/python`, not the main venv.

```python
# scripts/wiki/mlx_encoder.py
"""MLX BGE-M3 encoder worker. Runs inside embed-venv. Communicates via JSON frames on stdin/stdout.

Protocol:
  stdin  : one JSON object per line, e.g. {"op": "encode", "texts": [...], "max_length": 512}
  stdout : one JSON object per line, e.g. {"ok": true, "dtype": "float16", "shape": [N, 1024], "data_b64": "..."}
  stderr : log messages (main bridge doesn't parse)
  exit on {"op": "shutdown"} or EOF
"""
```

Requirements:
- Manual CLS-pooling (not library default — library is broken, see Key measured facts)
- fp16 output, L2-normalized
- Batch-by-batch response (echo one JSON frame per encode op)
- `mx.metal.clear_cache()` + `gc.collect()` after each batch
- Memory ceiling: `mx.metal.set_memory_limit(int(info['max_recommended_working_set_size'] * 0.7))` at startup

### AC4 — `scripts/wiki/mlx_bridge.py` (main venv side)

Wrapper class `MLXEncoderBridge` in main venv. Launches worker via `embed-venv/bin/python scripts/wiki/mlx_encoder.py`. Feeds batches via stdin pipe, parses stdout frames back to numpy arrays.

Requirements:
- Public API: `encode(texts: list[str], batch_size: int = 16, max_length: int = 512) -> np.ndarray[fp16]`
- Auto-respawn on worker crash (non-zero exit): halve `batch_size`, retry the failed batch, track retries (max 3 before giving up)
- Lazy worker startup (don't spawn until first `encode` call)
- Explicit `close()` / context-manager support
- Base64 decode + numpy reconstruction from worker's JSON response

### AC5 — Parity regression test

`tests/wiki/test_mlx_flagembedding_parity.py`:

1. Load fixture: 20 short Ukrainian texts (committed at `tests/wiki/fixtures/parity_texts.json`) — mix of modern + archaic per the smoke-test sample pattern
2. Run `MLXEncoderBridge` → save to `/tmp/mlx_parity.npy`
3. Run FlagEmbedding (main venv, `use_fp16=True`) → save to `/tmp/fe_parity.npy`
4. Assert:
   - Per-text `cosine(MLX, FlagEmbedding) ≥ 0.9999` for every text in the fixture
   - Top-5 retrieval overlap ≥ 18/20 (90%)

The test is mock-friendly: if `embed-venv` doesn't exist, skip with `pytest.skip("embed-venv not installed")`.

Fixture seed: draw 10 from `textbook_sections` + 10 from `literary_texts` where `language_period IN ('modern', 'middle_ukrainian', 'old_east_slavic')` with deterministic `ORDER BY chunk_id LIMIT 10`. Commit the fixture JSON (not the DB queries — the fixture must be reproducible).

### AC6 — Lint + test

- `.venv/bin/ruff check scripts/wiki/mlx_bridge.py tests/wiki/test_mlx_flagembedding_parity.py` clean
- `embed-venv/bin/python -m py_compile scripts/wiki/mlx_encoder.py` clean (we lint it in the subprocess env since it imports MLX)
- `.venv/bin/pytest tests/wiki/test_mlx_flagembedding_parity.py -v` green

## File scope (allow-list for stage (a))

New files:
- `scripts/wiki/mlx_encoder.py`
- `scripts/wiki/mlx_bridge.py`
- `tests/wiki/test_mlx_flagembedding_parity.py`
- `tests/wiki/fixtures/parity_texts.json`

Modify:
- `.gitignore` (add 2 lines per AC2)

Generated (NOT committed):
- `embed-venv/` — ignored via AC2
- `tests/wiki/fixtures/parity_texts.json` IS committed (the fixture texts themselves, not a cache)

**Do NOT modify:**
- `scripts/wiki/sources_db.py`, `scripts/wiki/enrichment.py`, `scripts/wiki/dense_rerank.py`, `scripts/wiki/query_builder.py` — those are stage (c)
- `docs/architecture/adr/adr-006-compile-layer-retrieval.md` — stage (d)
- `scripts/wiki/embedding_manifest.py` — stage (b)
- Anything in `curriculum/`, `plans/`, `orchestration/`

## Out of scope for stage (a)

- Cold-encoding anything from the real corpus (that's stage e, user-supervised)
- Multi-corpus retrieval logic (stage c)
- Storage/manifest layer (stage b)
- ADR revision (stage d)
- Integration with `dense_rerank.py` (stage c — the bridge will be wired in later)

## Done-when (stage a)

- Single commit on `main` titled `feat(wiki): MLX encoder + subprocess bridge for BGE-M3 (#1348 stage-a)`
- Parity test green: 20 texts, cosine ≥0.9999 each, top-5 overlap ≥90%
- `embed-venv/` exists at project root, gitignored
- Comment on #1348 with: commit SHA, parity test output (actual cosine min/mean, overlap number), embed-venv size on disk
- `ruff` + `pytest` green
