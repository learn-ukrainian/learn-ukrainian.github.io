"""Benchmark reranker models for Ukrainian retrieval using FTS5 candidates.

This harness evaluates exactly one reranker model per process. It first fetches
the top-50 SQLite FTS5 candidates for each benchmark query, reranks them in
batches of at most eight query/document pairs, and then computes Recall@10 and
nDCG@10 against the benchmark ground truth.
"""

from __future__ import annotations

import argparse
import gc
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.benchmark_embeddings import (
    PERIOD_LABELS,
    SAMPLE_SEED,
    acquire_benchmark_lock,
    build_result_row,
    get_db_connection,
    get_hf_token,
    get_peak_memory_mb,
    get_period_sql,
    is_hf_unauthorized,
    load_queries,
    maybe_hold_dry_run_lock_for_tests,
    ndcg_at_k,
    recall_at_k,
    save_benchmark_results,
)

SCRIPT_DIR = Path(__file__).resolve().parent
RERANKER_LOCK_FILE = "/tmp/benchmark-reranker.lock"
RERANKER_METRICS = ("recall@10", "ndcg@10")
FTS_TOP_K = 50
RERANK_TOP_K = 10
RERANK_BATCH_SIZE = 8
DEFAULT_SAMPLE_SIZE = None


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for the reranker harness."""
    parser = argparse.ArgumentParser(
        description="Benchmark Ukrainian rerankers over FTS5 candidate pools",
    )
    parser.add_argument(
        "--model",
        choices=[
            "bge-reranker-v2-m3",
            "jina-reranker-v2-base-multilingual",
        ],
        required=True,
        help="Single reranker model to benchmark",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of benchmark queries to evaluate (default: all with ground truth)",
    )
    parser.add_argument(
        "--lock-file",
        default=RERANKER_LOCK_FILE,
        help=f"Lock file for mutual exclusion (default: {RERANKER_LOCK_FILE})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the reranker plan and exit without loading any model",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    return build_parser().parse_args(argv)


def load_benchmark_queries(sample_size: int | None) -> list[dict]:
    """Load ground-truth benchmark queries, optionally down-sampled."""
    queries = [query for query in load_queries() if query.get("relevant_chunks")]
    if sample_size is None or sample_size >= len(queries):
        return queries
    rng = random.Random(SAMPLE_SEED)
    return rng.sample(queries, sample_size)


def build_fts_query(query_text: str) -> str | None:
    """Build an FTS5 MATCH query from the benchmark text."""
    terms: list[str] = []
    for raw_term in query_text.split():
        cleaned = raw_term.replace('"', "").replace("'", "").replace("/", " ").strip()
        for token in cleaned.split():
            if token:
                terms.append(f'"{token}"')
    return " OR ".join(terms) if terms else None


def get_fts_tables(period: str) -> tuple[str, str, str, tuple]:
    """Map a benchmark period to its FTS5/data-table pair and filters."""
    data_table, where_sql, params = get_period_sql(period)
    if data_table == "textbooks":
        return "textbooks_fts", data_table, where_sql, params
    if data_table == "literary_texts":
        return "literary_fts", data_table, where_sql, params
    raise ValueError(f"Unsupported benchmark table for reranking: {data_table}")


def load_fts_candidates(conn, query: dict, limit: int = FTS_TOP_K) -> list[dict]:
    """Fetch the top SQLite FTS5 candidates for one benchmark query."""
    fts_query = build_fts_query(query["query"])
    if not fts_query:
        return []

    fts_table, data_table, where_sql, params = get_fts_tables(query["period"])
    where_clauses = [f"{fts_table} MATCH ?"]
    query_params: list[object] = [fts_query]
    if where_sql:
        where_clauses.append(where_sql.removeprefix("WHERE ").strip())
        query_params.extend(params)

    rows = conn.execute(
        f"""
        SELECT s.chunk_id, s.text, bm25({fts_table}, 5.0, 1.0) AS rank
        FROM {fts_table}
        JOIN {data_table} s ON s.id = {fts_table}.rowid
        WHERE {' AND '.join(where_clauses)}
        ORDER BY rank
        LIMIT ?
        """,
        (*query_params, limit),
    ).fetchall()
    return [dict(row) for row in rows]


class RerankerModel:
    """Thin wrapper around a SentenceTransformers CrossEncoder."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    def load(self):
        if self._model is not None:
            return
        from sentence_transformers import CrossEncoder

        try:
            self._model = CrossEncoder(
                self.model_name,
                trust_remote_code=True,
                token=get_hf_token(),
            )
        except Exception as exc:
            if is_hf_unauthorized(exc):
                raise SystemExit(
                    f"ERROR: unauthorized loading {self.model_name}. "
                    "Check HF_TOKEN and model access."
                ) from exc
            raise

    def score_pairs(self, query_text: str, candidates: list[dict]) -> list[float]:
        """Score query/document pairs in batches no larger than eight."""
        self.load()
        assert self._model is not None
        pairs = [(query_text, candidate["text"]) for candidate in candidates]
        scores: list[float] = []
        for index in range(0, len(pairs), RERANK_BATCH_SIZE):
            batch = pairs[index:index + RERANK_BATCH_SIZE]
            batch_scores = self._model.predict(
                batch,
                batch_size=RERANK_BATCH_SIZE,
                show_progress_bar=False,
            )
            scores.extend(float(score) for score in np.asarray(batch_scores).reshape(-1))
        return scores

    def unload(self):
        del self._model
        self._model = None
        gc.collect()
        try:
            import torch

            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception:
            pass


def evaluate_reranker(queries: list[dict], ranked_results: list[list[str]]) -> dict:
    """Aggregate reranker quality metrics with the embedder-style schema."""
    per_period = defaultdict(lambda: defaultdict(list))
    overall = defaultdict(list)
    human_curated = defaultdict(list)
    auto_populated_count = 0

    for query, ranked in zip(queries, ranked_results, strict=True):
        relevant = query["relevant_chunks"]
        period = query["period"]
        recall_10 = recall_at_k(ranked, relevant, RERANK_TOP_K)
        ndcg_10 = ndcg_at_k(ranked, relevant, RERANK_TOP_K)

        per_period[period]["recall@10"].append(recall_10)
        per_period[period]["ndcg@10"].append(ndcg_10)
        overall["recall@10"].append(recall_10)
        overall["ndcg@10"].append(ndcg_10)

        if query.get("auto_populated", False):
            auto_populated_count += 1
        else:
            human_curated["recall@10"].append(recall_10)
            human_curated["ndcg@10"].append(ndcg_10)

    result = {"overall": {}, "by_period": {}, "human_curated_only": {}}
    for metric in RERANKER_METRICS:
        result["overall"][metric] = float(np.mean(overall[metric])) if overall[metric] else 0.0
        result["human_curated_only"][metric] = (
            float(np.mean(human_curated[metric])) if human_curated[metric] else 0.0
        )

    for period, metrics in per_period.items():
        result["by_period"][period] = {}
        for metric in RERANKER_METRICS:
            result["by_period"][period][metric] = float(np.mean(metrics[metric])) if metrics[metric] else 0.0

    result["auto_populated_count"] = auto_populated_count
    result["human_curated_count"] = len(queries) - auto_populated_count
    return result


def print_summary(model_name: str, metrics: dict):
    """Print a compact reranker summary."""
    print(f"\nReranker benchmark complete: {model_name}")
    print(
        "  Overall:"
        f" Recall@10={metrics['overall'].get('recall@10', 0.0):.3f},"
        f" nDCG@10={metrics['overall'].get('ndcg@10', 0.0):.3f}"
    )
    for period, label in PERIOD_LABELS.items():
        period_metrics = metrics["by_period"].get(period, {})
        print(
            f"  {label}:"
            f" Recall@10={period_metrics.get('recall@10', 0.0):.3f},"
            f" nDCG@10={period_metrics.get('ndcg@10', 0.0):.3f}"
        )


def save_reranker_result(model_name: str, row: dict):
    """Write the reranker row beneath the dedicated _rerankers key."""
    results_path = SCRIPT_DIR / "benchmark_results.json"
    existing_results = {}
    if results_path.exists():
        with open(results_path) as f:
            existing_results = json.load(f)
    rerankers = existing_results.setdefault("_rerankers", {})
    rerankers[model_name] = row
    save_benchmark_results(existing_results)


def print_dry_run_plan(args: argparse.Namespace):
    """Print the dry-run plan without touching any model loader."""
    queries = load_benchmark_queries(args.sample_size)
    pair_count = len(queries) * FTS_TOP_K
    print(
        f"DRY RUN: would load model {args.model}, would score "
        f"{len(queries)} queries × {FTS_TOP_K} candidates = {pair_count} pairs"
    )
    maybe_hold_dry_run_lock_for_tests()


def run_benchmark(model_name: str, sample_size: int | None):
    """Run the reranker benchmark for one model."""
    queries = load_benchmark_queries(sample_size)
    if not queries:
        raise SystemExit("ERROR: No benchmark queries with ground truth were found.")

    conn = get_db_connection()
    reranker = RerankerModel(model_name)
    ranked_results: list[list[str]] = []

    try:
        start_time = time.time()
        for query in queries:
            candidates = load_fts_candidates(conn, query, limit=FTS_TOP_K)
            if not candidates:
                ranked_results.append([])
                continue

            scores = reranker.score_pairs(query["query"], candidates)
            rescored = [
                (candidate["chunk_id"], score)
                for candidate, score in zip(candidates, scores, strict=True)
            ]
            rescored.sort(key=lambda item: item[1], reverse=True)
            ranked_results.append([chunk_id for chunk_id, _ in rescored[:RERANK_TOP_K]])

        metrics = evaluate_reranker(queries, ranked_results)
        elapsed = time.time() - start_time
        row = build_result_row(
            metrics,
            len(queries),
            get_peak_memory_mb(),
            elapsed,
        )
    finally:
        conn.close()
        reranker.unload()

    print_summary(model_name, metrics)
    save_reranker_result(model_name, row)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    lock_fd = acquire_benchmark_lock(args.lock_file, "reranker")
    try:
        if args.dry_run:
            print_dry_run_plan(args)
            return 0
        run_benchmark(args.model, args.sample_size)
        return 0
    finally:
        lock_fd.close()


if __name__ == "__main__":
    raise SystemExit(main())
