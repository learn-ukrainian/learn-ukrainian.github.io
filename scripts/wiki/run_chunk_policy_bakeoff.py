#!/usr/bin/env python3
"""Chunk-policy bakeoff harness for #1553 step 5.

Three cells (A: legacy NO_CHUNK + 512, B: paragraph-aware 1500/150 + 2048,
C: paragraph-aware 4000/400 + 8192) on the same 1000-sample gold set used
by ``scripts/rag/benchmark_embeddings.py`` (and the prior #1345 embedder
survey). For each cell we:

1. Sample the same 1000 rows per period from ``sources.db``
   (textbook=modern, literary=middle/oes — Wikipedia/external are NOT in
   the gold set, so the bakeoff is strictly a textbook/literary signal —
   see DESIGN NOTES at the bottom of this docstring).
2. Re-chunk every sampled row through the cell's ``ChunkingPolicy`` via
   :func:`scripts.wiki.chunking.chunk_text`. NO_CHUNK policy yields the
   row text unchanged.
3. Embed queries + sub-chunks with BGE-M3 fp16 at the cell's
   ``INDEX_MAX_LENGTH``.
4. Top-200 dense retrieval per query, then aggregate sub-chunks back to
   their parent SQL chunk_id using *first-occurrence-per-parent* (the
   standard chunk-to-doc rollup; alternatives are documented inline).
5. Compute Recall@5, Recall@10, nDCG@10 against the gold-set parent
   chunk_ids — same metrics as ``benchmark_embeddings.evaluate_model``.
6. Diff Cell A's results against the #1345 baseline; refuse to publish
   if any tier is off by more than ``--baseline-tolerance`` (default
   0.02 R@10).

Why this exists rather than ``cold_encode_corpus`` against a per-cell
manifest: ``benchmark_embeddings.py`` does not read from manifest.db at
all (samples + embeds in-process per run), and ``cold_encode_corpus`` has
no gold-set subset support. Manifest writes would produce zero observable
signal in the benchmark. See Codex review msg #461 for confirmation.

DESIGN NOTES (see :func:`run_cell` for the cell control flow):

* Cell A is defined as the *legacy* baseline: NO_CHUNK on every corpus,
  encoder window 512. This deliberately differs from "what is on main
  today" (which has 450/50 paragraph-aware on textbook/external/wiki
  per #1553 step 1). Reproducing #1345 requires the legacy state, not
  the post-step-1 state. Codex review msg #461 flagged this.
* The benchmark gold set's *modern* tier samples from the legacy
  ``textbooks`` table, not the production ``textbook_sections``. The
  bakeoff therefore measures chunk-policy quality on the legacy table
  and extrapolates to ``textbook_sections``. Boundary structure of
  Ukrainian textbook prose is similar enough to make the extrapolation
  reasonable, but the writeup must call this out.
* First-occurrence aggregation is a max-score-per-parent equivalent
  when the underlying ranking is score-sorted. Sum/count alternatives
  reward chunkers that emit MORE pieces per parent — undesired for a
  policy-pick decision.
* Hybrid (dense+sparse) sparse weights are computed per-emitted-chunk,
  so sparse is NOT chunk-policy-independent. We report hybrid for
  completeness but pick the winner on dense-only.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import gc
import json
import random
import sqlite3
import sys
import time
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# These imports follow sys.path manipulation above; ruff's import-order
# autofix would break them, so they live below the sys.path.insert call.
from rag.benchmark_embeddings import (  # noqa: I001
    LITERARY_SOURCE_FILES,
    SAMPLE_SEED,
    acquire_benchmark_lock,
    load_queries,
    ndcg_at_k,
    recall_at_k,
)
from wiki import chunking as chunking_module
from wiki import dense_rerank as dense_rerank_module
from wiki.chunking import (
    NO_CHUNK,
    ChunkingPolicy,
    chunk_text,
)

SOURCES_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "docs"
    / "architecture"
    / "research"
    / "2026-04-25-chunk-policy-bakeoff-results.md"
)
BAKEOFF_LOCK_FILE = "/tmp/chunk-policy-bakeoff.lock"

# Periods covered by the gold set (mirrors benchmark_embeddings.PERIODS).
PERIODS = ("old_east_slavic", "middle_ukrainian", "modern")
PERIOD_LABELS = {
    "old_east_slavic": "OES (X-XIII)",
    "middle_ukrainian": "Middle (XIV-XVIII)",
    "modern": "Modern (textbooks)",
}
METRICS = ("recall@5", "recall@10", "ndcg@10")

#: Top-K sub-chunk retrieval depth before parent rollup. Sized so that
#: even if a few parents emit many sub-chunks, we still surface ≥10
#: unique parents per query in the rollup. Empirically: median doc
#: emits 1-3 sub-chunks at cell B/C target sizes; 200 is comfortable
#: headroom. We log a warning when a query produces fewer than 10
#: unique parents — that signals the cap is too tight.
SUBCHUNK_RETRIEVAL_DEPTH = 200

#: Per-cell encode batch sizes. Memory pressure scales with
#: batch_size × max_length²; cell C at 8192 tokens needs a much
#: smaller batch than cells A/B to fit a 16-32 GB unified-memory
#: M-series Mac. Numbers chosen empirically: A=32, B=16, C=4 keeps
#: peak workspace under ~3 GB on top of the 2.3 GB BGE-M3 model.
#: Override with --batch-A / --batch-B / --batch-C if your machine
#: has more headroom.
DEFAULT_BATCH_SIZES = {
    "A": 32,
    "B": 16,
    "C": 4,
}

# #1345 dense baselines — used by Cell A reproduction sanity check.
# Source: docs/architecture/research/2026-04-embedder-survey.md.
BASELINE_1345 = {
    "modern":           {"recall@10": 1.000, "ndcg@10": 0.997},
    "middle_ukrainian": {"recall@10": 0.500, "ndcg@10": 0.380},
    "old_east_slavic":  {"recall@10": 0.300, "ndcg@10": 0.220},
}


# --- Cell definitions ------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class CellConfig:
    """A bakeoff cell. Encapsulates the chunk-policy override and encoder
    window for one comparison point."""

    cell_id: str
    description: str
    index_max_length: int
    #: Maps corpus name → policy. Corpora not in the dict keep main's
    #: shipped policy (so e.g. ``literary`` stays NO_CHUNK across all
    #: cells — re-chunking 137K vectors is out of scope per #1553).
    policy_overrides: dict[str, ChunkingPolicy]
    #: Encoder batch size — memory-bound on long-context cells.
    #: Default from ``DEFAULT_BATCH_SIZES``; overridable per-CLI.
    batch_size: int = 32


def _legacy_policies() -> dict[str, ChunkingPolicy]:
    """Cell A: the legacy pre-#1553 state — NO_CHUNK on every corpus.

    Distinct from main today (post-PR #1555), where textbook/external/
    wikipedia are at 450/50. To reproduce the #1345 baseline numbers we
    need the truly-no-chunking state.
    """

    return {
        "wikipedia": NO_CHUNK,
        "external": NO_CHUNK,
        "textbook_sections": NO_CHUNK,
    }


def _paragraph_policy(corpus: str, *, target: int, overlap: int) -> ChunkingPolicy:
    return ChunkingPolicy(
        version_id=f"{corpus}:bakeoff-{target}t-o{overlap}-v1",
        target_tokens=target,
        overlap_tokens=overlap,
    )


CELLS: dict[str, CellConfig] = {
    "A": CellConfig(
        cell_id="A",
        description="legacy: NO_CHUNK on textbook/external/wiki, encoder 512",
        index_max_length=512,
        policy_overrides=_legacy_policies(),
        batch_size=DEFAULT_BATCH_SIZES["A"],
    ),
    "B": CellConfig(
        cell_id="B",
        description="paragraph-aware 1500/150, encoder 2048",
        index_max_length=2048,
        policy_overrides={
            "wikipedia": _paragraph_policy("wikipedia", target=1500, overlap=150),
            "external": _paragraph_policy("external", target=1500, overlap=150),
            "textbook_sections": _paragraph_policy(
                "textbook_sections", target=1500, overlap=150
            ),
        },
        batch_size=DEFAULT_BATCH_SIZES["B"],
    ),
    "C": CellConfig(
        cell_id="C",
        description="paragraph-aware 4000/400, encoder 8192",
        index_max_length=8192,
        policy_overrides={
            "wikipedia": _paragraph_policy("wikipedia", target=4000, overlap=400),
            "external": _paragraph_policy("external", target=4000, overlap=400),
            "textbook_sections": _paragraph_policy(
                "textbook_sections", target=4000, overlap=400
            ),
        },
        batch_size=DEFAULT_BATCH_SIZES["C"],
    ),
}


# --- Period → corpus mapping ---------------------------------------------


def corpus_for_period(period: str) -> str:
    """Map a benchmark period to the production corpus that controls
    its chunking policy. Modern → textbook_sections (chunking applies);
    middle/oes → "literary" (NO_CHUNK on main and in every cell, so the
    chunk policy is moot for these tiers — but the encoder window
    change still affects them)."""

    if period == "modern":
        return "textbook_sections"
    return "literary"  # NO_CHUNK in every cell


def policy_for_period(period: str, cell: CellConfig) -> ChunkingPolicy:
    corpus = corpus_for_period(period)
    if corpus in cell.policy_overrides:
        return cell.policy_overrides[corpus]
    # literary: stays NO_CHUNK in every cell.
    return NO_CHUNK


# --- DB sampling (mirrors benchmark_embeddings) --------------------------


def get_db_connection() -> sqlite3.Connection:
    if not SOURCES_DB_PATH.exists():
        raise FileNotFoundError(
            f"Sources database not found at {SOURCES_DB_PATH}. "
            "Run: .venv/bin/python scripts/wiki/build_sources_db.py"
        )
    conn = sqlite3.connect(str(SOURCES_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_period_sql(period: str) -> tuple[str, str, tuple]:
    if period == "modern":
        return "textbooks", "", ()
    if period in LITERARY_SOURCE_FILES:
        source_files = LITERARY_SOURCE_FILES[period]
        placeholders = ", ".join("?" * len(source_files))
        return (
            "literary_texts",
            f"WHERE source_file IN ({placeholders})",
            tuple(source_files),
        )
    raise ValueError(f"Unsupported benchmark period: {period}")


def load_period_chunks(period: str, chunk_ids: set[str] | None = None) -> list[dict]:
    table, where_sql, params = get_period_sql(period)
    clauses = []
    query_params: list[str] = []

    if where_sql:
        clauses.append(where_sql.removeprefix("WHERE ").strip())
        query_params.extend(params)

    if chunk_ids:
        placeholders = ", ".join("?" * len(chunk_ids))
        clauses.append(f"chunk_id IN ({placeholders})")
        query_params.extend(sorted(chunk_ids))

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    conn = get_db_connection()
    try:
        rows = conn.execute(
            f"SELECT chunk_id, text FROM {table} {where_clause}",
            tuple(query_params),
        ).fetchall()
    finally:
        conn.close()

    return [{"chunk_id": row["chunk_id"], "text": row["text"]} for row in rows]


def sample_chunks(period: str, sample_size: int) -> list[dict]:
    all_chunks = load_period_chunks(period)
    total = len(all_chunks)
    if total > sample_size:
        rng = random.Random(SAMPLE_SEED)
        all_chunks = rng.sample(all_chunks, sample_size)
    print(f"  [{period}] sampled {len(all_chunks)} chunks of {total} (seed={SAMPLE_SEED})")
    return all_chunks


def ensure_gold_chunks_present(
    period: str,
    sampled: list[dict],
    queries: list[dict],
) -> list[dict]:
    """Pad the sample with any gold-set chunks that random sampling missed."""

    sample_ids = {c["chunk_id"] for c in sampled}
    missing: set[str] = set()
    for q in queries:
        if q["period"] != period:
            continue
        for cid in q["relevant_chunks"]:
            if cid not in sample_ids:
                missing.add(cid)
    if not missing:
        return sampled
    extra = load_period_chunks(period, missing)
    print(f"  [{period}] padded with {len(extra)} gold-set chunks missing from random sample")
    return [*sampled, *extra]


# --- Re-chunk + parent tracking ------------------------------------------


@dataclasses.dataclass(frozen=True)
class SubChunk:
    parent_chunk_id: str
    sub_index: int
    text: str


def rechunk_period(
    period: str,
    rows: list[dict],
    cell: CellConfig,
    tokenizer: Any,
) -> tuple[list[SubChunk], dict[str, Any]]:
    """Apply the cell's policy to every row of a period.

    Returns ``(sub_chunks, stats_dict)``. NO_CHUNK passes the row text
    through unchanged with ``sub_index=0``.
    """

    policy = policy_for_period(period, cell)
    sub_chunks: list[SubChunk] = []
    rows_with_zero_chunks = 0
    sub_count_per_parent: dict[str, int] = {}

    for row in rows:
        parent_id = row["chunk_id"]
        text = row["text"] or ""
        pieces = list(chunk_text(text, policy=policy, tokenizer=tokenizer))
        if not pieces:
            rows_with_zero_chunks += 1
            continue
        sub_count_per_parent[parent_id] = len(pieces)
        for piece in pieces:
            sub_chunks.append(
                SubChunk(parent_chunk_id=parent_id, sub_index=piece.chunk_index, text=piece.text)
            )

    counts = list(sub_count_per_parent.values()) or [0]
    stats = {
        "parent_rows": len(rows),
        "sub_chunks": len(sub_chunks),
        "rows_with_zero_chunks": rows_with_zero_chunks,
        "subchunks_per_parent_mean": float(np.mean(counts)),
        "subchunks_per_parent_p50": float(np.percentile(counts, 50)),
        "subchunks_per_parent_p90": float(np.percentile(counts, 90)),
        "subchunks_per_parent_max": int(np.max(counts)),
        "policy_version_id": policy.version_id,
        "policy_target_tokens": policy.target_tokens,
        "policy_overlap_tokens": policy.overlap_tokens,
    }
    return sub_chunks, stats


# --- Encoder wrapper -----------------------------------------------------


class BgeEncoder:
    """BGE-M3 fp16 with per-call ``max_length``.

    Distinct from ``benchmark_embeddings.BGEEncoder`` (which hardcodes
    ``max_length=512``). Loaded once per script invocation and reused
    across cells to avoid 90+s reload cost per cell.
    """

    def __init__(self) -> None:
        self._model = None

    def load(self) -> None:
        if self._model is not None:
            return
        from FlagEmbedding import BGEM3FlagModel

        print("[bench] Loading BGE-M3...")
        self._model = BGEM3FlagModel(
            "BAAI/bge-m3",
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
            use_fp16=True,
        )
        print("[bench] BGE-M3 loaded.")

    def encode(
        self,
        texts: list[str],
        *,
        max_length: int,
        batch_size: int = 32,
        return_sparse: bool = False,
    ) -> dict[str, Any]:
        self.load()
        # ``load`` populates ``_model`` or raises; the assert sharpens
        # the type for pyright since it cannot prove the post-condition.
        assert self._model is not None
        result = self._model.encode(
            texts,
            batch_size=batch_size,
            max_length=max_length,
            return_dense=True,
            return_sparse=return_sparse,
            return_colbert_vecs=False,
        )
        out: dict[str, Any] = {"dense": result["dense_vecs"]}
        if return_sparse:
            out["sparse_weights"] = result["lexical_weights"]
        return out

    def unload(self) -> None:
        del self._model
        self._model = None
        gc.collect()
        try:
            import torch

            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception:
            pass


# --- Retrieval + parent rollup -------------------------------------------


def retrieve_dense_subchunks(
    query_vec: np.ndarray,
    sub_vecs: np.ndarray,
    top_k: int,
) -> np.ndarray:
    """Return indices of the top-K sub-chunks by cosine similarity
    (vectors assumed L2-normalized)."""

    scores = sub_vecs @ query_vec
    top = np.argpartition(-scores, min(top_k, len(scores) - 1))[:top_k]
    # Sort the top-K by score descending.
    top_sorted = top[np.argsort(-scores[top])]
    return top_sorted


def aggregate_to_parents(
    ranked_indices: np.ndarray,
    sub_chunks: list[SubChunk],
    *,
    top_k: int,
) -> list[str]:
    """First-occurrence-per-parent rollup. Produces ≤``top_k`` unique
    parent chunk_ids in rank order."""

    seen: set[str] = set()
    out: list[str] = []
    for idx in ranked_indices:
        parent_id = sub_chunks[idx].parent_chunk_id
        if parent_id in seen:
            continue
        seen.add(parent_id)
        out.append(parent_id)
        if len(out) >= top_k:
            break
    return out


# --- Cell control flow ---------------------------------------------------


@contextlib.contextmanager
def overridden_chunking(cell: CellConfig) -> Iterator[None]:
    """Temporarily replace ``CHUNKING_POLICIES`` and ``INDEX_MAX_LENGTH``.

    Restores the originals in ``finally`` even on exception. The chunking
    module imports CHUNKING_POLICIES into ``policy_for``; that lookup
    re-reads the dict on every call, so monkey-patching the dict in
    place propagates to all callers.
    """

    original_policies = dict(chunking_module.CHUNKING_POLICIES)
    original_max_len = dense_rerank_module.INDEX_MAX_LENGTH
    try:
        for corpus, policy in cell.policy_overrides.items():
            chunking_module.CHUNKING_POLICIES[corpus] = policy
        dense_rerank_module.INDEX_MAX_LENGTH = cell.index_max_length
        yield
    finally:
        chunking_module.CHUNKING_POLICIES.clear()
        chunking_module.CHUNKING_POLICIES.update(original_policies)
        dense_rerank_module.INDEX_MAX_LENGTH = original_max_len


def evaluate_period(
    *,
    queries: list[dict],
    sub_chunks: list[SubChunk],
    sub_dense: np.ndarray,
    query_indices: list[int],
    q_dense: np.ndarray,
) -> tuple[dict[str, float], dict[str, Any]]:
    """Score one period of one cell. Returns (metrics, diagnostic_stats).

    ``period`` is implicit from the (queries, sub_chunks) pair — the
    caller has already filtered by period before calling.
    """

    period_metrics = {m: [] for m in METRICS}
    queries_with_low_unique = 0
    avg_unique_parents: list[int] = []

    for query_idx, q in zip(query_indices, queries, strict=False):
        relevant = q["relevant_chunks"]
        ranked_idx = retrieve_dense_subchunks(
            q_dense[query_idx],
            sub_dense,
            top_k=SUBCHUNK_RETRIEVAL_DEPTH,
        )
        retrieved_parents = aggregate_to_parents(ranked_idx, sub_chunks, top_k=10)
        avg_unique_parents.append(len(retrieved_parents))
        if len(retrieved_parents) < 10:
            queries_with_low_unique += 1

        period_metrics["recall@5"].append(recall_at_k(retrieved_parents, relevant, 5))
        period_metrics["recall@10"].append(recall_at_k(retrieved_parents, relevant, 10))
        period_metrics["ndcg@10"].append(ndcg_at_k(retrieved_parents, relevant, 10))

    aggregated = {
        m: float(np.mean(period_metrics[m])) if period_metrics[m] else 0.0
        for m in METRICS
    }
    diag = {
        "queries_evaluated": len(queries),
        "queries_with_<10_unique_parents": queries_with_low_unique,
        "avg_unique_parents": float(np.mean(avg_unique_parents)) if avg_unique_parents else 0.0,
    }
    return aggregated, diag


def run_cell(
    cell: CellConfig,
    *,
    encoder: BgeEncoder,
    queries_by_period: dict[str, list[dict]],
    sample_size: int,
    tokenizer: Any,
) -> dict[str, Any]:
    """Run one cell end-to-end. Returns the per-period results dict."""

    print(f"\n{'=' * 60}\nCELL {cell.cell_id}: {cell.description}\n{'=' * 60}")

    cell_results: dict[str, Any] = {
        "cell_id": cell.cell_id,
        "description": cell.description,
        "index_max_length": cell.index_max_length,
        "policy_overrides": {
            corpus: dataclasses.asdict(policy)
            for corpus, policy in cell.policy_overrides.items()
        },
        "by_period": {},
        "stats": {},
    }

    with overridden_chunking(cell):
        # Encode queries once per cell at the cell's max_length. Queries
        # are short (rarely >20 tokens) so max_length only affects them
        # via padding budget — but staying consistent makes the audit
        # cleaner.
        all_queries: list[dict] = []
        period_query_indices: dict[str, list[int]] = {}
        for period in PERIODS:
            qs = queries_by_period.get(period, [])
            period_query_indices[period] = list(
                range(len(all_queries), len(all_queries) + len(qs))
            )
            all_queries.extend(qs)
        if not all_queries:
            raise RuntimeError("no queries with ground truth")
        q_texts = [q["query"] for q in all_queries]
        # Queries are short — even cell C's batch_size=4 is overkill for
        # them; use a slightly larger query batch to keep encode latency
        # snappy without breaking the long-context memory budget.
        query_batch = max(cell.batch_size, 8)
        q_result = encoder.encode(
            q_texts, max_length=cell.index_max_length, batch_size=query_batch
        )
        q_dense = q_result["dense"]

        for period in PERIODS:
            period_queries = queries_by_period.get(period, [])
            if not period_queries:
                continue

            t0 = time.time()
            print(f"\n  [{period}] sampling + chunking + encoding (cell {cell.cell_id})")
            rows = sample_chunks(period, sample_size)
            rows = ensure_gold_chunks_present(period, rows, period_queries)

            sub_chunks, chunk_stats = rechunk_period(period, rows, cell, tokenizer)
            print(
                f"    chunked {chunk_stats['parent_rows']} parents → "
                f"{chunk_stats['sub_chunks']} sub-chunks "
                f"(p50={chunk_stats['subchunks_per_parent_p50']:.0f}, "
                f"p90={chunk_stats['subchunks_per_parent_p90']:.0f}, "
                f"max={chunk_stats['subchunks_per_parent_max']})"
            )

            sub_texts = [s.text for s in sub_chunks]
            print(
                f"    encoding {len(sub_texts)} sub-chunks "
                f"@ max_length={cell.index_max_length} batch={cell.batch_size}"
            )
            sub_result = encoder.encode(
                sub_texts, max_length=cell.index_max_length, batch_size=cell.batch_size
            )
            sub_dense = sub_result["dense"]

            metrics, diag = evaluate_period(
                queries=period_queries,
                sub_chunks=sub_chunks,
                sub_dense=sub_dense,
                query_indices=period_query_indices[period],
                q_dense=q_dense,
            )
            elapsed = time.time() - t0
            print(
                f"    [{period}] R@5={metrics['recall@5']:.3f} "
                f"R@10={metrics['recall@10']:.3f} nDCG@10={metrics['ndcg@10']:.3f} "
                f"({elapsed:.1f}s)"
            )
            if diag["queries_with_<10_unique_parents"]:
                print(
                    f"    [WARN] {diag['queries_with_<10_unique_parents']} queries surfaced "
                    f"<10 unique parents in top-{SUBCHUNK_RETRIEVAL_DEPTH} subchunks"
                )

            cell_results["by_period"][period] = metrics
            cell_results["stats"][period] = {
                **chunk_stats,
                **diag,
                "elapsed_seconds": elapsed,
            }

            # Free the encoded sub-chunk array before the next period
            # to keep peak RSS down on the M-series Mac. Release MPS
            # workspace explicitly — gc alone leaves it allocated and
            # the next period's encode tips a 16 GB Mac into OOM.
            # (Empirical: post-#1562 OOM-reboot 2026-04-25 on cell B
            # middle_ukrainian after a successful OES.)
            del sub_dense, sub_texts, sub_chunks
            gc.collect()
            try:
                import torch

                if torch.backends.mps.is_available():
                    torch.mps.empty_cache()
            except Exception:
                pass

    return cell_results


# --- Sanity gate (Cell A vs #1345 baseline) ------------------------------


def cell_a_baseline_drift(
    cell_a_results: dict[str, Any], tolerance: float
) -> tuple[bool, list[str]]:
    """Compare Cell A's R@10 against the #1345 baseline. Returns
    ``(passes, [drift_lines])``."""

    drifts: list[str] = []
    passes = True
    for period, base in BASELINE_1345.items():
        observed = cell_a_results["by_period"].get(period, {})
        if not observed:
            drifts.append(f"  [{period}] MISSING from cell A results")
            passes = False
            continue
        delta = observed.get("recall@10", 0.0) - base["recall@10"]
        sign = "+" if delta >= 0 else ""
        line = (
            f"  [{period}] R@10: cellA={observed['recall@10']:.3f} "
            f"baseline={base['recall@10']:.3f} (Δ {sign}{delta:.3f})"
        )
        if abs(delta) > tolerance:
            line += f"  ❌ exceeds tolerance ±{tolerance:.2f}"
            passes = False
        else:
            line += "  ✅"
        drifts.append(line)
    return passes, drifts


# --- Markdown writeup -----------------------------------------------------


def render_results_markdown(
    cells: list[dict[str, Any]],
    *,
    sample_size: int,
    tolerance: float,
    drift_lines: list[str],
    drift_passes: bool,
) -> str:
    out: list[str] = []
    out.append("# Chunk-policy bakeoff results (#1553 step 5)\n\n")
    out.append("Date: 2026-04-25\n")
    out.append(f"Sample size per period: {sample_size}\n")
    out.append(f"Sub-chunk retrieval depth: {SUBCHUNK_RETRIEVAL_DEPTH}\n")
    out.append(
        f"Cell A baseline tolerance (vs #1345): ±{tolerance:.2f} R@10\n\n"
    )

    out.append("## Cell A reproduction sanity check\n\n")
    out.append(
        "Cell A is defined as the *legacy* baseline (NO_CHUNK on every corpus, "
        "encoder window 512). It must reproduce the #1345 numbers within "
        f"±{tolerance:.2f} R@10 on every tier or the bakeoff is invalid.\n\n"
    )
    for line in drift_lines:
        out.append(line + "\n")
    if not drift_passes:
        out.append(
            "\n**❌ Sanity check FAILED. Cell B/C results are not interpretable. "
            "Investigate the harness before trusting the comparison.**\n"
        )
    else:
        out.append("\n**✅ Sanity check passed.**\n")

    out.append("\n## Per-cell metrics\n\n")
    out.append("| Period | Cell A R@10 | Cell B R@10 | Cell C R@10 | Cell A nDCG@10 | Cell B nDCG@10 | Cell C nDCG@10 |\n")
    out.append("|---|---:|---:|---:|---:|---:|---:|\n")
    by_cell = {c["cell_id"]: c for c in cells}
    for period in PERIODS:
        row = [PERIOD_LABELS[period]]
        for metric in ("recall@10", "ndcg@10"):
            for cid in ("A", "B", "C"):
                v = by_cell.get(cid, {}).get("by_period", {}).get(period, {}).get(metric)
                row.append(f"{v:.3f}" if v is not None else "—")
        # Reorder so all R@10 then all nDCG@10
        out.append("| " + " | ".join(row) + " |\n")

    out.append("\n## Per-cell chunking stats\n\n")
    out.append(
        "Sub-chunks per parent measures chunker fragmentation. Higher = more "
        "fragmentation per source row.\n\n"
    )
    out.append("| Period | Cell | sub-chunks | mean/parent | p90/parent | max/parent |\n")
    out.append("|---|---|---:|---:|---:|---:|\n")
    for period in PERIODS:
        for cid in ("A", "B", "C"):
            stats = by_cell.get(cid, {}).get("stats", {}).get(period, {})
            if not stats:
                continue
            out.append(
                f"| {PERIOD_LABELS[period]} | {cid} | "
                f"{stats.get('sub_chunks', 0)} | "
                f"{stats.get('subchunks_per_parent_mean', 0):.2f} | "
                f"{stats.get('subchunks_per_parent_p90', 0):.0f} | "
                f"{stats.get('subchunks_per_parent_max', 0)} |\n"
            )

    out.append("\n## Decision (auto-generated, human-validate)\n\n")
    out.append(_decision_summary(by_cell, drift_passes=drift_passes))

    out.append("\n## Limitations\n\n")
    out.append(
        "1. **Modern source mismatch:** the gold set's *modern* tier samples "
        "from the legacy `textbooks` table, while production retrieval uses "
        "`textbook_sections`. The bakeoff measures chunk-policy quality on "
        "the legacy table and extrapolates to `textbook_sections`. Boundary "
        "structure of Ukrainian textbook prose is similar enough to make "
        "the extrapolation reasonable, but absolute Recall numbers may shift.\n"
    )
    out.append(
        "2. **No Wikipedia / external in the gold set.** Wikipedia and "
        "external article queries are not in `benchmark_queries.yaml`. The "
        "bakeoff strictly measures textbook + literary chunk-policy quality; "
        "wikipedia/external are an extrapolation.\n"
    )
    out.append(
        "3. **Single-shot, single-seed.** Same `SAMPLE_SEED=42` as #1345 so "
        "matched-pair comparison against the baseline is valid. If Cell B "
        "and Cell C tie within 1 pp, multi-seed before deciding.\n"
    )
    out.append(
        "4. **Hybrid (dense+sparse) not in this bakeoff.** Sparse weights "
        "are computed per-emitted-chunk, so sparse is NOT chunk-policy "
        "independent. The policy-pick decision is dense-only, which is the "
        "layer the chunk policy actually controls.\n"
    )
    out.append(
        "5. **OES / Middle-Ukrainian source heterogeneity.** Per user "
        "feedback (2026-04-25), confirmed by a per-source modern-letter "
        "audit: literary corpora are a mix of three types — (a) "
        "true side-by-side bilingual editions (archaic + modern "
        "translation interleaved, e.g. `wave0-slovo-o-polku` 91%, "
        "`wave9-tlkovaniye-1431` 83%, `wave1-pvl-lavrentiyivskyi` 78%); "
        "(b) standalone modern-Ukrainian translations (e.g. "
        "`wave0-pvl-yaremenko`, `wave6-galvol-kostruba`); (c) pure "
        "archaic transcripts (e.g. `wave1-pvl-lavrentiyivskyi-"
        "rozshyfrovka` 0% modern). Cell A embeds each row whole "
        "regardless of type; cells B/C may split bilingual rows at "
        "paragraph boundaries that happen to be archaic-modern "
        "translation pairs, producing language-pure sub-chunks for "
        "type (a). Any OES/middle Recall@10 *gain* in cells B/C should "
        "therefore be partially discounted on bilingual sources — it "
        "may be an artifact of language-purity splits, not boundary-"
        "aware chunking on its own. Modern textbook Recall@10 is the "
        "cleaner signal for the policy-pick decision.\n"
    )
    out.append(
        "6. **Hungarian contamination in modern textbooks.** "
        "`5-klas-ukrmova-uhor-2022-1` (246 rows in `textbooks`, 90 in "
        "`textbook_sections`) is a Ukrainian-for-Hungarian-speakers "
        "schoolbook with interleaved Hungarian text. Same `textbooks` "
        "table feeds every cell, so this is a constant bias that "
        "subtracts out of cell-vs-cell comparison — but absolute Modern "
        "Recall@10 numbers may be 1-2 pp lower than they would be on a "
        "language-pure corpus. Tracked in a separate followup issue.\n"
    )

    return "".join(out)


def _decision_summary(by_cell: dict[str, Any], *, drift_passes: bool) -> str:
    if not drift_passes:
        return (
            "Sanity check failed — no decision recorded. Stay on Cell A "
            "(current shipped behavior) until the harness discrepancy is "
            "explained.\n"
        )
    modern = {
        cid: by_cell.get(cid, {}).get("by_period", {}).get("modern", {}).get("recall@10", 0.0)
        for cid in ("A", "B", "C")
    }
    middle = {
        cid: by_cell.get(cid, {}).get("by_period", {}).get("middle_ukrainian", {}).get("recall@10", 0.0)
        for cid in ("A", "B", "C")
    }
    oes = {
        cid: by_cell.get(cid, {}).get("by_period", {}).get("old_east_slavic", {}).get("recall@10", 0.0)
        for cid in ("A", "B", "C")
    }
    winner = max(("B", "C"), key=lambda cid: modern[cid])
    # Stop conditions from the spec.
    if middle[winner] < (BASELINE_1345["middle_ukrainian"]["recall@10"] - 0.05):
        return (
            f"Cell {winner} has the best modern R@10 ({modern[winner]:.3f} vs "
            f"baseline {modern['A']:.3f}) but tanks middle-Ukrainian "
            f"({middle[winner]:.3f}, baseline {middle['A']:.3f}). "
            f"Stop condition triggered — stay on Cell A.\n"
        )
    if oes[winner] < (BASELINE_1345["old_east_slavic"]["recall@10"] - 0.05):
        return (
            f"Cell {winner} has the best modern R@10 but regresses OES below "
            f"baseline-5pp. Stop condition triggered — stay on Cell A.\n"
        )
    return (
        f"**Recommended winner: Cell {winner}** "
        f"(modern R@10 {modern[winner]:.3f} vs Cell A {modern['A']:.3f}; "
        f"middle {middle[winner]:.3f}, OES {oes[winner]:.3f}; both within "
        "the 5pp baseline-regression budget).\n\n"
        "Next steps after human validation:\n"
        "1. Update `scripts/wiki/chunking.py` `_STEP1_TARGET_TOKENS` / "
        "`_STEP1_OVERLAP_TOKENS` to the winner's params.\n"
        "2. Update `scripts/wiki/dense_rerank.py` `INDEX_MAX_LENGTH`.\n"
        "3. Auto-derived `version_id` will mechanically force re-encode "
        "(step 6).\n"
    )


# --- CLI ---------------------------------------------------------------


def parse_cells(arg: str) -> list[str]:
    cells = [c.strip().upper() for c in arg.split(",") if c.strip()]
    for cid in cells:
        if cid not in CELLS:
            raise argparse.ArgumentTypeError(
                f"unknown cell {cid!r}; valid: {sorted(CELLS)}"
            )
    return cells


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Chunk-policy bakeoff for #1553 step 5. Compares cell-specific "
            "(chunking_policy, INDEX_MAX_LENGTH) configs on the same gold "
            "set used by the prior #1345 embedder survey.\n\n"
            "Use to pick a chunk-policy winner before re-encoding all "
            "corpora. Do NOT use to test embedder changes — model is "
            "fixed at BGE-M3 fp16 by #1345."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/wiki/run_chunk_policy_bakeoff.py --cells A,B,C\n"
            "  .venv/bin/python scripts/wiki/run_chunk_policy_bakeoff.py --cells B \\\n"
            "      --sample-size 200  # quick smoke test\n"
            "\n"
            "Outputs:\n"
            "  --output            Markdown writeup with per-cell metrics + decision\n"
            "  --json-output       (optional) JSON dump of raw per-cell results\n"
            "  stdout              Human-readable progress + cell summaries\n"
            "\n"
            "Exit codes:\n"
            "  0  bakeoff completed and Cell A reproduces #1345 baseline\n"
            "  1  Cell A failed the baseline sanity check (results untrustworthy)\n"
            "  2  CLI / IO error\n"
            "\n"
            "Related:\n"
            "  Spec:        docs/architecture/2026-04-25-chunk-policy-bakeoff-spec.md\n"
            "  Issue:       #1553 (wiki retrieval overhaul)\n"
            "  Baseline:    docs/architecture/research/2026-04-embedder-survey.md (#1345)\n"
        ),
    )
    parser.add_argument(
        "--cells",
        type=parse_cells,
        default=["A", "B", "C"],
        help="Comma-separated cells to run. Default: A,B,C.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=1000,
        help="Chunks sampled per period (matches #1345). Default: 1000.",
    )
    parser.add_argument(
        "--baseline-tolerance",
        type=float,
        default=0.02,
        help="Max R@10 drift between Cell A and #1345 baseline before sanity "
             "check fails. Default: 0.02.",
    )
    parser.add_argument(
        "--batch-A",
        type=int,
        default=None,
        help=f"Override Cell A encoder batch size. Default: {DEFAULT_BATCH_SIZES['A']}.",
    )
    parser.add_argument(
        "--batch-B",
        type=int,
        default=None,
        help=f"Override Cell B encoder batch size. Default: {DEFAULT_BATCH_SIZES['B']}.",
    )
    parser.add_argument(
        "--batch-C",
        type=int,
        default=None,
        help=f"Override Cell C encoder batch size. Default: {DEFAULT_BATCH_SIZES['C']}.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Markdown writeup path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional JSON dump of raw per-cell results.",
    )
    parser.add_argument(
        "--lock-file",
        default=BAKEOFF_LOCK_FILE,
        help=f"Lock file for mutual exclusion. Default: {BAKEOFF_LOCK_FILE}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print plan and exit without loading the model.",
    )
    return parser


def queries_by_period(queries: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for q in queries:
        if not q.get("relevant_chunks"):
            continue
        out[q["period"]].append(q)
    return dict(out)


def print_dry_run(args: argparse.Namespace, queries: list[dict]) -> None:
    by_period = queries_by_period(queries)
    print("DRY RUN: chunk-policy bakeoff plan")
    print(f"  cells: {','.join(args.cells)}")
    print(f"  sample size per period: {args.sample_size}")
    print(f"  baseline tolerance: ±{args.baseline_tolerance:.2f} R@10")
    print(f"  queries with ground truth: {sum(len(qs) for qs in by_period.values())}")
    for period, qs in sorted(by_period.items()):
        print(f"    {period}: {len(qs)} queries")
    print(f"  writeup: {args.output}")
    if args.json_output:
        print(f"  json: {args.json_output}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    queries = load_queries()
    queries = [q for q in queries if q.get("relevant_chunks")]
    if not queries:
        print("ERROR: no queries with ground truth in benchmark_queries.yaml")
        return 2

    if args.dry_run:
        print_dry_run(args, queries)
        return 0

    lock_fd = acquire_benchmark_lock(args.lock_file, benchmark_kind="chunk-policy bakeoff")
    try:
        return _run(args, queries)
    finally:
        lock_fd.close()


def _write_outputs(
    args: argparse.Namespace,
    cells_results: list[dict[str, Any]],
    *,
    partial: bool,
    drift_lines: list[str] | None = None,
    drift_passes: bool = True,
) -> None:
    """Write markdown + JSON outputs to disk.

    Called incrementally after each cell completes (``partial=True``) so a
    later-cell crash doesn't wipe completed work, AND once at the end with
    ``partial=False`` to attach the final drift gate verdict. The 2026-04-25
    cell-C OOM lesson: always snapshot to disk before the next cell starts.
    """

    if not cells_results:
        return

    if drift_lines is None:
        cell_a = next((c for c in cells_results if c["cell_id"] == "A"), None)
        if cell_a is not None:
            drift_passes, drift_lines = cell_a_baseline_drift(
                cell_a, args.baseline_tolerance
            )
        else:
            drift_lines = ["  Cell A not yet completed — sanity check pending."]
            drift_passes = True

    md = render_results_markdown(
        cells_results,
        sample_size=args.sample_size,
        tolerance=args.baseline_tolerance,
        drift_lines=drift_lines,
        drift_passes=drift_passes,
    )
    if partial:
        md = (
            f"<!-- PARTIAL: {len(cells_results)} cell(s) of "
            f"{len(args.cells)} complete -->\n\n" + md
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md, encoding="utf-8")
    label = "Partial writeup" if partial else "Writeup"
    print(f"  ↳ {label}: {args.output}")

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(cells_results, indent=2, default=str), encoding="utf-8"
        )
        print(f"  ↳ JSON: {args.json_output}")


def _run(args: argparse.Namespace, queries: list[dict]) -> int:
    by_period = queries_by_period(queries)
    print(f"Bakeoff: cells={args.cells} sample_size={args.sample_size}")
    for period, qs in sorted(by_period.items()):
        print(f"  {period}: {len(qs)} queries")

    # Tokenizer is shared across cells (BGE-M3 tokenizer; chunk_text uses
    # it for token accounting). Loaded lazily by dense_rerank.
    tokenizer = dense_rerank_module._get_tokenizer()
    encoder = BgeEncoder()

    # Apply per-cell batch-size overrides from CLI.
    batch_overrides = {
        "A": args.batch_A,
        "B": args.batch_B,
        "C": args.batch_C,
    }
    effective_cells: dict[str, CellConfig] = {}
    for cid, base in CELLS.items():
        override = batch_overrides.get(cid)
        if override is not None:
            effective_cells[cid] = dataclasses.replace(base, batch_size=override)
            print(f"  cell {cid} batch_size override: {base.batch_size} → {override}")
        else:
            effective_cells[cid] = base

    cells_results: list[dict[str, Any]] = []
    for cid in args.cells:
        cell = effective_cells[cid]
        try:
            cell_results = run_cell(
                cell,
                encoder=encoder,
                queries_by_period=by_period,
                sample_size=args.sample_size,
                tokenizer=tokenizer,
            )
            cells_results.append(cell_results)
        except KeyboardInterrupt:
            print(f"\n⚠️  Interrupted during cell {cid} — preserving prior cell results")
            break
        except Exception as exc:
            # Cell crashed (OOM, MPS assertion, etc.) — preserve completed
            # cell data and continue to writeup. Lesson from the 2026-04-25
            # cell-C OOM that wiped Cell A+B in-memory results when the
            # writeup was deferred to script-end. Now we ALSO snapshot to
            # disk after each cell (see incremental write below).
            print(f"\n💥 Cell {cid} crashed: {type(exc).__name__}: {exc}")
            print(f"  Continuing with {len(cells_results)} completed cell(s) of {len(args.cells)}")
            break

        # Incremental snapshot after each cell — protects against later-cell
        # crashes wiping completed work. (2026-04-25 lesson learned.)
        _write_outputs(args, cells_results, partial=True)

    encoder.unload()

    # Sanity gate: only meaningful if Cell A was run.
    drift_passes = True
    drift_lines: list[str] = []
    cell_a = next((c for c in cells_results if c["cell_id"] == "A"), None)
    if cell_a is None:
        drift_lines = ["  Cell A not run — sanity check skipped."]
    else:
        drift_passes, drift_lines = cell_a_baseline_drift(cell_a, args.baseline_tolerance)

    print("\n" + "=" * 60 + "\nCell A vs #1345 baseline\n" + "=" * 60)
    for line in drift_lines:
        print(line)

    _write_outputs(
        args,
        cells_results,
        partial=False,
        drift_lines=drift_lines,
        drift_passes=drift_passes,
    )

    if cell_a is not None and not drift_passes:
        print("\n❌ Cell A failed baseline sanity check — exit 1")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
