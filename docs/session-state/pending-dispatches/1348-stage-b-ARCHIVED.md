# Task: #1348 stage (b) — Embedding manifest + storage layer

**Stage (a) is done**: commit `428be007b` landed MLX encoder + subprocess bridge with parity mean cosine 0.999999. That's the foundation; stage (b) builds the storage layer on top of it but does not yet wire into retrieval (that's stage c).

Full spec: `gh issue view 1348`. Stage (b) maps to AC3 + parts of AC4/AC7.

## Stage (b) scope — exactly this, no more

Build the embedding storage layer: a separate SQLite manifest DB at `data/embeddings/manifest.db`, the `EmbeddingManifest` class with CRUD + atomic append semantics, and supporting tests. **Do not yet use this from `dense_rerank.py` or `search_sources` — that's stage (c).**

## Ground rules

- Branch: `main`. No worktrees.
- `.venv/bin/python`, `.venv/bin/ruff`, `.venv/bin/pytest` — never bare.
- `git add` allow-list only — files named in AC1–AC5. No `-A`, no `-u`.
- Commit: `feat(wiki): embedding manifest + storage layer (#1348 stage-b)`
- DO NOT close #1348.
- Comment on #1348 with stage-b evidence: commit SHA, manifest DB size after a synthetic 10K-row test, fault-injection test output showing atomic append survives mid-write kill.

## Why separate manifest DB (design rationale)

`scripts/wiki/build_sources_db.py:382` deletes `data/sources.db` on rebuild. Putting embedding tables inside `sources.db` would orphan every `.npy` shard on each rebuild. Separate file at `data/embeddings/manifest.db` survives rebuilds cleanly and is gitignored alongside the shards.

## Reading before coding

1. `gh issue view 1348` — full spec (stage b maps to AC3 + the incremental append flow)
2. Stage (a) commit `428be007b` — especially the new `scripts/wiki/mlx_bridge.py` (not called from stage b directly, but it's the consumer of stage b's output later)
3. `scripts/wiki/sources_db.py` — for conventions on SQLite connection patterns in this project

## Acceptance criteria

### AC1 — Schema module

`scripts/wiki/embedding_manifest_schema.py` — defines DDL as a constant, executed on first open:

```sql
CREATE TABLE IF NOT EXISTS embedding_shards (
    shard_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    corpus       TEXT NOT NULL,
    path         TEXT NOT NULL,          -- relative to data/embeddings/
    rows         INTEGER NOT NULL,
    dims         INTEGER NOT NULL DEFAULT 1024,
    dtype        TEXT NOT NULL DEFAULT 'float16',
    committed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_embshards_corpus ON embedding_shards(corpus);

CREATE TABLE IF NOT EXISTS embedding_units (
    unit_key     TEXT PRIMARY KEY,       -- "textbook_section:1234", "literary:5cbffa78_c0000", ...
    corpus       TEXT NOT NULL,
    parent_key   TEXT,                   -- source_file / work_id for neighbor context expansion
    text_sha256  TEXT NOT NULL,
    model        TEXT NOT NULL,          -- e.g. "bge-m3-mlx-fp16"
    shard_id     INTEGER NOT NULL REFERENCES embedding_shards(shard_id),
    row_idx      INTEGER NOT NULL,
    deleted      INTEGER NOT NULL DEFAULT 0,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_embunits_corpus ON embedding_units(corpus, deleted);
CREATE INDEX IF NOT EXISTS idx_embunits_parent ON embedding_units(corpus, parent_key);
CREATE INDEX IF NOT EXISTS idx_embunits_shard ON embedding_units(shard_id);
```

DB path: `data/embeddings/manifest.db` (create parent dir if missing, gitignored via `data/embeddings/` entry from stage a).

### AC2 — `EmbeddingManifest` class

`scripts/wiki/embedding_manifest.py` — class-based API:

```python
class EmbeddingManifest:
    def __init__(self, db_path: Path = DEFAULT_MANIFEST_DB): ...
    def add_shard(self, *, corpus: str, path: Path, rows: int, dims: int = 1024, dtype: str = "float16") -> int: ...
    def add_units(self, rows: list[UnitSpec]) -> None: ...  # bulk insert in one transaction
    def get_unit(self, unit_key: str) -> UnitRow | None: ...
    def get_units(self, unit_keys: list[str]) -> dict[str, UnitRow]: ...
    def mark_stale(self, unit_key: str) -> None: ...  # same meaning as delete here; a re-encode writes a fresh row
    def mark_deleted(self, unit_key: str) -> None: ...
    def active_units_for_corpus(self, corpus: str) -> list[UnitRow]: ...
    def shard_map_for_corpus(self, corpus: str) -> dict[int, Path]: ...  # {shard_id: absolute_path}
    def vacuum_orphaned_shards(self) -> int: ...  # returns count of shards removed (rows==0 or no active units point to it)
    def stats(self) -> dict: ...  # totals per corpus for diagnostics
    def close(self) -> None: ...

@dataclass
class UnitSpec:
    unit_key: str
    corpus: str
    parent_key: str | None
    text_sha256: str
    model: str
    shard_id: int
    row_idx: int

@dataclass
class UnitRow(UnitSpec):
    deleted: bool
    updated_at: str
```

Conventions:
- All paths stored in the DB are **relative to `data/embeddings/`**; absolute paths materialized only in `shard_map_for_corpus()` return.
- All writes wrapped in `BEGIN IMMEDIATE ... COMMIT` transactions.
- `mark_stale` and `mark_deleted` both set `deleted=1` + update `updated_at`. Semantically: stale = "a new vector will replace this"; deleted = "no longer in the source corpus." Same column, different intent; treat them as aliases in SQL; keep them distinct in API for future telemetry.

### AC3 — Atomic shard append helper

`scripts/wiki/embedding_manifest.py::append_shard(manifest, corpus, vectors, unit_specs)`:

```python
def append_shard(
    manifest: EmbeddingManifest,
    *,
    corpus: str,
    vectors: np.ndarray,      # shape (N, 1024), dtype fp16
    unit_specs: list[UnitSpecInput],  # (unit_key, parent_key, text_sha256, model), N entries
) -> int:  # returns new shard_id
    """Atomic append: write shard to tmp, fsync, rename, commit manifest rows in one transaction.
    On any error, cleans up tmp file; manifest never has a shard_row pointing at a file that doesn't exist."""
```

Sequence:
1. Validate: `vectors.dtype == np.float16`, `vectors.shape[1] == 1024`, `len(unit_specs) == vectors.shape[0]`
2. Compute next shard number for corpus: `max(existing shard numbers for corpus) + 1`, zero-padded to 6 digits
3. Path: `data/embeddings/{corpus}/shard-NNNNNN.npy`
4. Write to `{path}.tmp` via `np.save`, then `os.fsync` the FD
5. `os.rename({path}.tmp, {path})` — atomic on POSIX
6. SQLite `BEGIN IMMEDIATE` → `INSERT INTO embedding_shards` (get shard_id from AUTOINCREMENT) → `INSERT INTO embedding_units` (bulk) → `COMMIT`
7. On any exception: unlink `.tmp` if present; if SQLite fails after `.npy` rename, unlink the `.npy` too (so manifest never references a missing file, and vice versa)
8. Return shard_id

### AC4 — Incremental-append helper

`scripts/wiki/embedding_manifest.py::filter_new_or_changed(manifest, corpus, candidates)`:

```python
def filter_new_or_changed(
    manifest: EmbeddingManifest,
    *,
    corpus: str,
    candidates: Iterable[tuple[str, str]],  # (unit_key, text_sha256)
) -> tuple[list[str], list[str]]:  # (new_keys, stale_keys)
    """Classify candidates against the manifest.
    - new_keys: unit_key not in manifest at all (or deleted=1) → to encode and add
    - stale_keys: unit_key present with deleted=0 but different text_sha256 → to encode, mark old stale, add new
    Returns keys (for the caller to resolve into texts); does not read text.
    """
```

### AC5 — Tests

`tests/wiki/test_embedding_manifest.py`:

1. **Schema init**: fresh DB has both tables + all 3 indexes; reopening is idempotent.
2. **Atomic append happy path**: 100 synthetic fp16 vectors → append_shard → 1 shard row, 100 unit rows, `.npy` file exists on disk with correct shape/dtype.
3. **Atomic append fault injection**: mock `sqlite3.Connection.commit` to raise `OperationalError` after the shard row INSERT → verify the `.npy` file is removed, and `embedding_shards` is empty.
4. **Incremental classification**: seed manifest with 50 units → feed 75 candidates (30 unchanged sha, 15 changed sha, 30 new) → assert `new_keys == 30`, `stale_keys == 15`.
5. **Active units query**: mark 10 of 50 units deleted → `active_units_for_corpus` returns 40.
6. **Shard map**: seed 3 shards with 10/20/30 units → `shard_map_for_corpus` returns dict of shard_id → absolute path, all 3 entries.
7. **Vacuum**: seed 2 shards, mark all units in shard 1 deleted → `vacuum_orphaned_shards()` returns 1 and removes both the row and the `.npy` file.

All tests run against a temp DB + temp embeddings dir (use `tmp_path` fixture); no shared state with real `data/embeddings/manifest.db`.

### AC6 — Lint + test

- `.venv/bin/ruff check scripts/wiki/embedding_manifest.py scripts/wiki/embedding_manifest_schema.py tests/wiki/test_embedding_manifest.py` clean
- `.venv/bin/pytest tests/wiki/test_embedding_manifest.py -v` green

## File scope (allow-list for stage b)

New:
- `scripts/wiki/embedding_manifest.py`
- `scripts/wiki/embedding_manifest_schema.py`
- `tests/wiki/test_embedding_manifest.py`

**Do NOT modify**:
- Any file that stage (a) created (`mlx_encoder.py`, `mlx_bridge.py`) — they'll be consumed in stage (c)
- `scripts/wiki/dense_rerank.py`, `scripts/wiki/sources_db.py`, `scripts/wiki/enrichment.py`, `scripts/wiki/query_builder.py` — stage (c)
- `docs/architecture/adr/adr-006-*.md` — stage (d)
- `curriculum/**`, `plans/**`, `orchestration/**`
- `data/sources.db` schema (this is literally why we have a separate manifest DB)

## Out of scope for stage (b)

- Integrating the manifest with `dense_rerank.py` or `search_sources` (stage c)
- Cold-encoding anything from the real corpus (stage e, user-supervised)
- Full-matrix-load-at-startup optimization (stage c — the mmap dict strategy goes there)
- ADR revision (stage d)

## Done-when (stage b)

- Single commit on `main` titled `feat(wiki): embedding manifest + storage layer (#1348 stage-b)`
- All 7 tests green
- `ruff` clean
- Manifest DB can be opened and initialized from an empty state; schema check passes
- Fault-injection test proves atomic append survives mid-commit failure without leaving orphans
- Comment on #1348 with: commit SHA, manifest DB init size, 7-test green confirmation, fault-injection test output (showing the `.npy` got cleaned when SQLite failed)
