# Task: #1338 v2 — full-corpus dense retrieval (MLX + hybrid storage)

**Supersedes** original #1338 (textbook-only scope, crashed during live validation 2026-04-19). The code from the original attempt is preserved in the working tree and will be integrated; scope is expanded based on measured evidence.

**Depends on:** `#1347` (literary metadata restoration) — must land first.

## Measured evidence (2026-04-19 smoke test, user's M-series Mac)

| Framework | Warm load | Encode 100 × batch=8 | Peak RSS | Parity vs canonical BGE-M3 |
|---|---|---|---|---|
| **MLX fp16 + manual CLS-pooling** | 2.62s | 19.88s | 1,760 MB | cosine=1.00000, 100% top-5 overlap |
| PyTorch MPS + FlagEmbedding fp16 | 9.81s | 20.77s | 3,098 MB | reference |

Additional measurements (see `docs/session-state/current.md`):
- fp16 vs fp32 cosine on modern: 1.00000, top-5 overlap 100% → fp16 is sufficient
- fp16 vs fp32 cosine on archaic: 1.00000 (min 0.99998), top-5 overlap 100% → fp16 sufficient for archaic too
- 8bit vs fp16: cosine 0.99964, top-5 99% → 12% RAM saving not worth 1% quality loss → stay fp16
- MLX community port `mlx-community/bge-m3-mlx-fp16` ships without `1_Pooling/config.json`; library defaults to mean-pooling producing WRONG vectors. **Manual CLS pooling is required**: `cls = out.last_hidden_state[:, 0, :]; vectors = cls / ||cls||`

## Ground truth (read in full)

1. `gh issue view 1338` — original scope
2. `gh issue view 1347` — metadata restoration
3. `docs/architecture/adr/adr-006-compile-layer-retrieval.md` — to be revised
4. `docs/session-state/current.md` — 2026-04-19 handoff with smoke-test numbers
5. Uncommitted v1 work in tree: `scripts/wiki/dense_rerank.py`, `scripts/wiki/query_builder.py`, `scripts/wiki/sources_db.py`, `scripts/wiki/enrichment.py`
6. `scripts/wiki/enrichment.py:22` — **`SOURCE_CHAR_CAPS`** (not `LEVEL_CHAR_BUDGETS` — that symbol does not exist)

## File scope (allow-list)

**Modify:**
- `scripts/wiki/sources_db.py` — expand `search_sources` to multi-corpus dispatch
- `scripts/wiki/query_builder.py` — multi-corpus query construction
- `scripts/wiki/dense_rerank.py` — swap to MLX + CLS pooling + token-budget batching + child-process encoder + shard checkpointing + manifest-based append
- `scripts/wiki/enrichment.py` — wire multi-corpus retrieval, respect `SOURCE_CHAR_CAPS`
- `docs/architecture/adr/adr-006-compile-layer-retrieval.md` — revision encoded as part of this ticket
- `.gitignore` — add entries for `data/embeddings/` and `embed-venv/`
- `pyproject.toml` — add `mlx` and `mlx-embeddings` to an optional `embed` extras group if/when we consolidate to main venv (otherwise leave alone and use isolated venv)

**New:**
- `scripts/wiki/mlx_encoder.py` — MLX fp16 encoder (runs inside `embed-venv` via subprocess bridge)
- `scripts/wiki/mlx_bridge.py` — subprocess bridge: spawns `embed-venv/bin/python scripts/wiki/mlx_encoder.py`, pipes batches via stdin/stdout JSON frames, gets back fp16 numpy arrays serialized as bytes
- `scripts/wiki/embedding_manifest.py` — manifest DB (new SQLite file at `data/embeddings/manifest.db`, NOT a table in `sources.db`) with `EmbeddingManifest` class
- `scripts/wiki/track_priors.yaml` — per-track corpus priors, tunable without code change
- `tests/wiki/test_mlx_encoder_bridge.py` — shells out to `embed-venv`, compares serialized vectors
- `tests/wiki/test_embedding_manifest.py`
- `tests/wiki/test_multi_corpus_retrieval.py`
- `tests/wiki/test_flagembedding_parity.py` — freezes 100-text parity check as regression test
- `embed-venv/` — isolated MLX environment (generated; must be in `.gitignore`)
- `data/embeddings/{corpus}/shard-NNNNNN.npy` (generated; must be in `.gitignore`)
- `data/embeddings/manifest.db` (generated — see AC3 about rebuild preservation)

**Do NOT modify:**
- Any `text`/`title` column of any source table — `literary_texts.text`, `textbook_sections.full_text`, `external_articles.text`, `wikipedia.text` — verbatim
- `curriculum/**`, `plans/**`, `orchestration/**`
- Archaic normalization — encoded verbatim

## Dependencies

- `mlx ≥ 0.31.0`
- `mlx-embeddings ≥ 0.1.0` (note: pulls `transformers ≥ 5.0.0`, incompatible with main venv's `transformers 4.57.6` which FlagEmbedding/peft/sentence-transformers/marker-pdf/surya-ocr depend on)

**Therefore isolate MLX in `embed-venv/`** in the project root. Main `.venv` stays unchanged. Encoder runs as a subprocess, communicating via a JSON-framed stdin/stdout protocol.

## Architectural design

### 1. Framework: MLX fp16 with manual CLS-pooling, subprocess-isolated

`scripts/wiki/mlx_encoder.py` runs inside `embed-venv` as a long-lived worker process. Protocol:

- **stdin** accepts JSON-framed requests: `{"op": "encode", "texts": [...], "max_length": 512}`
- **stdout** emits JSON responses: `{"ok": true, "dtype": "float16", "shape": [N, 1024], "data_b64": "..."}` where `data_b64` is base64-encoded fp16 bytes
- **stderr** is for logs; parent doesn't parse it
- Worker exits on `{"op": "shutdown"}` or EOF

Encoder loop:
```python
out = model(input_ids, attention_mask)
cls = out.last_hidden_state[:, 0, :]
norms = mx.sqrt(mx.sum(cls * cls, axis=1, keepdims=True))
vectors = np.asarray((cls / norms).astype(mx.float16))
```

Output dtype = **fp16** end-to-end. Shards store fp16. Startup and rerank paths treat them as fp16.

`scripts/wiki/mlx_bridge.py` in main venv wraps this: `MLXEncoderBridge.encode(texts) -> np.ndarray[fp16]`. Parent manages process lifecycle, restarts on OOM (child exit non-zero), halves batch and retries.

Fallback path `EMBED_FRAMEWORK=pytorch_mps` uses existing FlagEmbedding directly (no subprocess). Default = MLX.

### 2. Corpus scope (dense-indexable, verbatim)

| Corpus | Unit | Count | Filter |
|---|---|---|---|
| textbook_sections | section | 5,389 | all |
| literary_texts (modern) | chunk | ~105,500 | `language_period = 'modern'` |
| literary_texts (archaic) | chunk | ~32,100 | `language_period IN ('middle_ukrainian','old_east_slavic')` |
| external_articles | row | 1,199 | all |
| wikipedia (chunked) | chunk | ~12,800 | after 450-token chunking, 50-token overlap |
| **Total** | | **~157,000** | |

**Confirmed values** for `language_period`: `modern`, `middle_ukrainian`, `old_east_slavic`. (Not `modern_literary` — that string does not exist in the source data.)

All text encoded verbatim. No orthographic normalization. No abbreviation expansion. Archaic text (ѣ, ѳ, ъ-endings) stays as ingested.

### 3. Storage: `.npy` shards + separate manifest DB

Manifest DB = **`data/embeddings/manifest.db`** (separate SQLite file, NOT tables in `sources.db`).

Reason: `scripts/wiki/build_sources_db.py:382` deletes `sources.db` on rebuild, preserving only Wikipedia (`:345`). Putting embedding manifest tables in `sources.db` would cause every rebuild to orphan all shards. Since the dispatch forbids modifying `build_sources_db.py`, a separate manifest DB is the correct architectural choice.

**Directory layout:**
```
data/embeddings/
  manifest.db                        # SQLite, survives sources.db rebuilds
  textbook_sections/shard-000001.npy
  modern_literary/shard-000001.npy
  modern_literary/shard-000002.npy   # one shard per source_file group, capped at 5K units
  archaic_literary/shard-000001.npy
  external/shard-000001.npy
  wikipedia/shard-000001.npy
```

**Manifest schema:**
```sql
CREATE TABLE embedding_shards (
    shard_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    corpus       TEXT NOT NULL,
    path         TEXT NOT NULL,        -- relative to data/embeddings/
    rows         INTEGER NOT NULL,
    dims         INTEGER NOT NULL DEFAULT 1024,
    dtype        TEXT NOT NULL DEFAULT 'float16',
    committed_at TEXT NOT NULL
);
CREATE INDEX idx_embshards_corpus ON embedding_shards(corpus);

CREATE TABLE embedding_units (
    unit_key     TEXT PRIMARY KEY,     -- "textbook_section:1234", "literary:5cbffa78_c0000", ...
    corpus       TEXT NOT NULL,
    parent_key   TEXT,                 -- source_file / work_id for neighbor context expansion
    text_sha256  TEXT NOT NULL,
    model        TEXT NOT NULL,        -- e.g. "bge-m3-mlx-fp16"
    shard_id     INTEGER NOT NULL REFERENCES embedding_shards(shard_id),
    row_idx      INTEGER NOT NULL,
    deleted      INTEGER NOT NULL DEFAULT 0,
    updated_at   TEXT NOT NULL
);
CREATE INDEX idx_embunits_corpus ON embedding_units(corpus, deleted);
CREATE INDEX idx_embunits_parent ON embedding_units(corpus, parent_key);
CREATE INDEX idx_embunits_shard ON embedding_units(shard_id);
```

**Startup load — do NOT concatenate mmap arrays:**

```python
# WRONG — np.concatenate eagerly copies data into RAM, defeating mmap
# matrix = np.concatenate([np.load(p, mmap_mode="r") for p in shards])

# CORRECT — keep shards as a list, maintain (shard_id → mmap_array), look up per-unit
shards = {row["shard_id"]: np.load(row["path"], mmap_mode="r")
          for row in db.execute("SELECT shard_id, path FROM embedding_shards WHERE corpus = ?")}
unit_index = {
    row["unit_key"]: (row["shard_id"], row["row_idx"])
    for row in db.execute("SELECT unit_key, shard_id, row_idx FROM embedding_units WHERE corpus = ? AND deleted = 0")
}
# Rerank: given N candidate unit_keys
candidate_vecs = np.stack([shards[sid][ridx] for sid, ridx in (unit_index[k] for k in candidate_keys)])
# candidate_vecs is now a small materialized array (N × 1024 × 2 bytes = trivial)
```

This preserves mmap's lazy-load behavior — RAM cost is (paged-in bytes for accessed rows), not full-corpus size.

**Atomic append:**
1. Encode batch → numpy fp16 array
2. Write to `shard-NNNNNN.npy.tmp` → `fsync` → rename to `shard-NNNNNN.npy`
3. SQLite transaction: INSERT INTO embedding_shards + embedding_units, commit
4. Orphan tmp files are cleaned on next startup

**Edit (same unit_key, new text_sha256):** encode into new shard, update `embedding_units.shard_id, row_idx`; old row orphaned (vacuum later).

**Delete:** `UPDATE embedding_units SET deleted=1 WHERE unit_key=?`. Shard untouched.

### 4. Memory-safe cold encoding

**Token-budget batching — sort BEFORE batching, not within:**

```python
# WRONG — sorting inside an already-formed batch doesn't reduce max length
# for batch in chunks(texts, 16):
#     batch.sort(key=len)

# CORRECT — sort the full corpus by token length first
token_lengths = [len(tokenizer.encode(t, max_length=512, truncation=True)) for t in texts]
order = sorted(range(len(texts)), key=lambda i: token_lengths[i])
# Consume in sorted order; batches now have similar lengths → minimum padding waste
for batch_indices in chunks(order, max_rows):
    # or: accumulate until sum(token_lengths) hits max_tokens
```

Use `max_rows=16` OR `max_tokens≈4096`, whichever binds first. Preserve the mapping back to original `unit_key` order when writing shards (write in original order, not sorted).

**MLX memory discipline — `mx.metal.clear_cache()` is mandatory, not optional:**

```python
# WRONG — Python's gc does NOT free Metal device memory cache
# gc.collect()

# CORRECT — clear Metal cache explicitly, gc as belt-and-braces
mx.metal.clear_cache()
gc.collect()
```

Call `mx.metal.clear_cache()` after every batch. `gc.collect()` every 8 batches.

**Memory ceiling:**
```python
info = mx.metal.device_info()
mx.metal.set_memory_limit(int(info['max_recommended_working_set_size'] * 0.7))
```

**Child-process isolation:** the worker process is the ONLY place MLX is imported. Parent runs main venv, has no MLX dependency. On worker crash (non-zero exit), parent halves batch size and respawns.

**Shard checkpointing:** one shard per natural grouping:
- textbook_sections: all in a single shard (5,389 units fits easily)
- modern_literary: per `source_file`, capped at 5,000 units per shard; `ukrlib-shevchenko-tvory-t1` may need 2 shards
- archaic_literary: per `source_file`
- external: per 1,000 units
- wikipedia: per 1,000 units

After each shard writes successfully, commit manifest rows. Interruption loses ≤1 shard (≤5,000 units, ~1 min re-encode).

### 5. Multi-corpus retrieval with per-track priors

`search_sources(query, *, track, strategy="unified_dense", limit=10)`:
- Parallel (`concurrent.futures.ThreadPoolExecutor`) sub-queries to each corpus retriever
- Each corpus returns its top-K vectors with cosine scores
- Score merge: `final_score = cosine × prior[track][corpus]`
- Sort merged list by `final_score`, take top-`limit`
- For `literary` and `wikipedia` hits, expand to include ±1 neighbor `chunk_id` with matching `parent_key`
- Context cap via **`SOURCE_CHAR_CAPS[track]`** from `scripts/wiki/enrichment.py:22` (not `LEVEL_CHAR_BUDGETS` — does not exist)

Priors in `scripts/wiki/track_priors.yaml` (start values; tune after #1340):

```yaml
# Per-track corpus priors. Values are multiplicative weights on cosine scores.
a1: {textbook: 1.0, modern_literary: 0.3, archaic_literary: 0.1, external: 0.5, wikipedia: 0.2}
a2: {textbook: 1.0, modern_literary: 0.4, archaic_literary: 0.1, external: 0.6, wikipedia: 0.3}
b1: {textbook: 0.9, modern_literary: 0.5, archaic_literary: 0.2, external: 0.7, wikipedia: 0.4}
b2: {textbook: 0.8, modern_literary: 0.7, archaic_literary: 0.3, external: 0.6, wikipedia: 0.4}
c1: {textbook: 0.5, modern_literary: 1.0, archaic_literary: 0.7, external: 0.4, wikipedia: 0.5}
c2: {textbook: 0.3, modern_literary: 1.0, archaic_literary: 0.9, external: 0.3, wikipedia: 0.5}
hist: {textbook: 0.5, modern_literary: 0.8, archaic_literary: 1.0, external: 0.4, wikipedia: 0.6}
lit:  {textbook: 0.4, modern_literary: 1.0, archaic_literary: 1.0, external: 0.3, wikipedia: 0.4}
ruth: {textbook: 0.3, modern_literary: 0.7, archaic_literary: 1.0, external: 0.2, wikipedia: 0.5}
oes:  {textbook: 0.2, modern_literary: 0.5, archaic_literary: 1.0, external: 0.1, wikipedia: 0.4}
```

### 6. Incremental append

```python
for row in iterate_corpus_rows(corpus):
    unit_key = f"{corpus}:{row['id']}"
    text = row[text_column]
    h = hashlib.sha256(text.encode()).hexdigest()
    existing = manifest.get_unit(unit_key)
    if existing and existing.text_sha256 == h:
        continue                   # skip — already correct
    if existing:
        manifest.mark_stale(unit_key)  # edit detected
    shard_buffer.add(unit_key, text, h)
shard_buffer.flush()
```

Adding 50 new literary works → encodes only those 50. No 2-hour rebuild.

### 7. ADR-006 revision

Update `docs/architecture/adr/adr-006-compile-layer-retrieval.md`:
- Replace the T3-T4 "metadata only" clause with full dense indexing across all periods, text-untouched, verbatim encoding
- Add framework decision (MLX fp16 + manual CLS-pooling) with smoke-test citation
- Add per-track priors as the routing mechanism (replaces tier-based source exclusion)
- Add hybrid storage decision (`.npy` shards + separate manifest DB at `data/embeddings/manifest.db`)
- Reference the precursor ticket and this v2 dispatch

## Acceptance criteria

### AC1 — MLX encoder + subprocess bridge

- `scripts/wiki/mlx_encoder.py` runs inside `embed-venv`; exposes stdin/stdout JSON protocol with `encode` and `shutdown` ops
- `scripts/wiki/mlx_bridge.py::MLXEncoderBridge` manages worker lifecycle from main venv, exposes `encode(texts, batch_size, max_length) -> np.ndarray[fp16]`
- Output dtype = fp16, shape (N, 1024), L2-normalized, CLS-pooled
- Fallback: `EMBED_FRAMEWORK=pytorch_mps` env var uses FlagEmbedding path directly

### AC2 — Parity test (bit-equivalence vs FlagEmbedding)

`tests/wiki/test_flagembedding_parity.py`:
- 100-text fixture (mix of modern + archaic samples; committed under `tests/wiki/fixtures/`)
- Shells out to `embed-venv/bin/python scripts/wiki/mlx_encoder.py`, saves output to `/tmp/mlx_test_vecs.npy`
- Runs FlagEmbedding on same texts in main venv, saves to `/tmp/fe_test_vecs.npy`
- Asserts: `cosine(MLX, FlagEmbedding) ≥ 0.9999` per text; top-5 retrieval overlap ≥ 95%; top-10 ≥ 93%

### AC3 — Manifest DB in separate file

- `scripts/wiki/embedding_manifest.py::EmbeddingManifest` class
- DB path = `data/embeddings/manifest.db`, NOT in `sources.db`
- All CRUD operations: `add_shard`, `add_units`, `get_unit`, `mark_stale`, `mark_deleted`, `active_units_for_corpus`, `shard_map_for_corpus`
- Atomic append (tmp + rename + transaction), verified by a fault-injection test

### AC4 — Startup load preserves mmap

Unit test: load a 10K-unit fixture corpus with 3 shards, assert:
- Startup RSS grows by ≤ 50 MB (not 50+ MB, since mmap is lazy)
- Specific row lookup returns correct vector
- No `np.concatenate` in the startup path (verified via static scan of `dense_rerank.py`)

### AC5 — Full-corpus cold encode

Successfully encode all 157K units on the user's Mac without OOM or crash:
- textbook_sections (5,389)
- modern literary (~105,500)
- archaic literary (~32,100) — encoded verbatim, text column untouched (verified by SHA256 before/after)
- external_articles (1,199)
- wikipedia chunked (~12,800)

Runtime ≤ 3 hours at `max_rows=16`, `max_tokens=4096`. Peak RSS ≤ 4 GB. Shard-checkpointed so interruption loses ≤ 1 min.

### AC6 — Multi-corpus retrieval with priors

- `search_sources(query, track="b1", strategy="unified_dense")` returns merged results from all 5 corpora, scored by cosine × track prior
- Priors loaded from `scripts/wiki/track_priors.yaml` at module init
- Neighbor context (±1 in same `parent_key`) included for literary/wikipedia hits
- Context cap enforced via `SOURCE_CHAR_CAPS[track]` — test asserts the returned packet is ≤ cap

### AC7 — Incremental append works

Smoke test:
1. Encode a 100-unit corpus → manifest has 100 rows
2. Change the `text` column of 3 units in the DB
3. Run `ensure_corpus_indexed` → only those 3 get re-encoded; one new shard appended; 3 old rows marked stale
4. Verify cosine of the 3 new vectors differs from their stale versions; unchanged units untouched

### AC8 — Memory safety verified

- Stress test: 20 textbook_sections with `char_count` varying 200–50,000, encoded under `max_tokens=4096` → peak RSS stays under 4 GB
- Fault-injection test: force MLX worker OOM by setting `mx.metal.set_memory_limit(100 * 1024 * 1024)`; confirm parent halves batch and retries

### AC9 — `.gitignore` updated

Add these entries (grouped with existing `data/` ignores starting at line 157):
```
data/embeddings/
embed-venv/
```

### AC10 — ADR-006 revised

Revision merged with evidence links.

### AC11 — Lint + tests

- `.venv/bin/ruff check` clean on all touched files
- `.venv/bin/pytest tests/wiki/ -v` green (tests shell out to `embed-venv/` where needed, per AC2)

## Out of scope

- Modifying any `text` column (archaic or modern)
- Normalizing archaic orthography
- Fine-tuning BGE-M3 (separate project if ever)
- Switching embedder
- sqlite-vec / ANN index (exhaustive cosine at 157K is sub-ms)
- 4/6/8-bit quantization (tested, rejected — 1% quality hit not worth 12% RAM saving)
- Modifying `build_sources_db.py` (precursor handles the schema for literary; manifest lives separately so it's untouched by rebuilds)
- Touching `curriculum/`, `plans/`, `orchestration/`

## Owner / dispatch

Codex. Reference `#1338` in commits. **Blocks on `#1347`.**

## Closing criteria

All 11 ACs met. Full 157K-corpus cold encode completes on user's Mac without crash. #1340 re-validation passes against the new retrieval pipeline. ADR-006 revision merged.
