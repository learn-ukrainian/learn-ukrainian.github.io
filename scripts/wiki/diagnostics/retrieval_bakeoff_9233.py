#!/usr/bin/env python3
"""Run the reproducible hybrid Ukrainian retrieval bake-off for #9233.

The source database is opened read-only. All materialized rows, indexes, model
caches, judging pools, and keys are written below the caller-supplied work dir.
"""

from __future__ import annotations

import argparse
import ast
import fcntl
import hashlib
import inspect
import json
import math
import os
import random
import resource
import signal
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.common.repo_root import project_interpreter
from scripts.verification.vesum import get_vesum_connection
from scripts.wiki import sources_db
from scripts.wiki.diagnostics import retrieval_probe_9233 as phase1

G3_PATH = ROOT / "docs/research/retrieval-bakeoff-9233/g3-queries.yaml"
QUERY_PATH = ROOT / "docs/research/retrieval-bakeoff-9233/queries.yaml"
G3_SHA256 = "152391220a5db3fd7ad4b48795d47a844bd223ad912d87dcaf6e12f10764fa53"
SEED = 9233
RRF_K = 60
TOP_FIRST_STAGE = 100
TOP_RERANK = 20
POOL_DEPTH = 20
THREADS = 6
THREAD_ENV = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "ORT_NUM_THREADS")
MEMORY_BYTES = 10 * 1024**3
E5 = "intfloat/multilingual-e5-small"
GUARDRAILS = {"threads": THREADS, "memory_bytes": MEMORY_BYTES, "memory_enforcement": "systemd_scope_or_rss_watchdog", "cpu_nice": 19, "io_priority": "idle"}
PASSAGE_POLICIES = {"embedder": "model maximum; head only", "reranker": {"tokens": 512, "head": 128, "tail": 384, "overhead_excluded": True}}
TOKEN_RE = phase1.TOKEN_RE

# Repository IDs and retrieval prefixes are frozen from design v5 item 8 and
# the model-card contracts. Embedders truncate at their maximum; rerankers
# use the v6.1 passage-only first-128/last-384 policy.
EMBEDDERS: dict[str, dict[str, str]] = {
    "BAAI/bge-m3": {"kind": "flag", "query_prefix": "", "passage_prefix": ""},
    "Snowflake/snowflake-arctic-embed-l-v2.0": {
        "kind": "sentence", "query_prefix": "query: ", "passage_prefix": "",
    },
    "jinaai/jina-embeddings-v5-text-nano": {"kind": "jina", "query_prefix": "task=retrieval; prompt_name=query", "passage_prefix": "task=retrieval; prompt_name=document"},
    "intfloat/multilingual-e5-small": {"kind": "sentence", "query_prefix": "query: ", "passage_prefix": "passage: "},
    "hotchpotch/bekko-embedding-v1-a25m": {"kind": "sentence", "query_prefix": "", "passage_prefix": ""},
    "Qwen/Qwen3-Embedding-0.6B": {
        "kind": "sentence", "query_prefix": "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:", "passage_prefix": "",
    },
}
RERANKERS = {
    "BAAI/bge-reranker-v2-m3": "cross_encoder",
    "jinaai/jina-reranker-v3.5": "jina",
    "Qwen/Qwen3-Reranker-0.6B": "qwen",
}
EXTRA_SOURCES = (
    "antonenko-davydovych-yak-my-hovorymo",
    "anna-ohoiko-500-verbs",
    "anna-ohoiko-1000-words-2nd-ed",
    "pohribnyi-ukrainska-literaturna-vymova-1992",
)
EXPLICIT_FUNCTION_WORDS = frozenset([
    "а", "або", "але", "в", "від", "до", "з", "за", "і", "й", "на", "не", "у", "та", "що", "це", "як", "про", "для", "коли", "де", "чим", "хто", "чого", "я", "ми", "ти", "ви", "він", "вона", "воно", "вони", "мій", "моя", "моє", "мого", "цим", "цього",
])
TOPIC_FUNCTION_WORDS = frozenset({"з", "із", "зі", "і", "й", "у", "в"})
FUNCTION_POS = frozenset({"conj", "prep", "part"})


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def _freeze(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    result = {**payload, "sha256": _hash(payload)}
    if path.exists() and _read_frozen(path) != result:
        raise ValueError(f"Frozen {path.name} mismatch; use a fresh --work-dir")
    _write_json(path, result)
    return result


def _read_frozen(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    payload = {k: v for k, v in result.items() if k != "sha256"}
    if result.get("sha256") != _hash(payload):
        raise ValueError(f"Frozen {path.name} hash mismatch")
    return result


def _stratified_sample(rows: list[Any], size: int = 500) -> list[dict[str, Any]]:
    if len(rows) < size:
        raise ValueError(f"Encode sample requires {size} chunks, got {len(rows)}")
    # Source identity is the book/source_file, not subject. Terciles use stable
    # rank in the complete subset (character length, then chunk identity).
    ordered = sorted(rows, key=lambda r: (len(str(r["text"])), str(r["chunk_id"])))
    cells: dict[tuple[str, int], list[Any]] = defaultdict(list)
    for index, row in enumerate(ordered):
        cells[(str(row["source_file"]), min(2, 3 * index // len(rows)))].append(row)
    if len(cells) > size:
        raise ValueError("More source/length cells than sample slots")
    keys = sorted(cells)
    allocations = dict.fromkeys(keys, 1)
    # Proportional allocation with one chunk in every nonempty cell, bounded by
    # cell capacity; stable largest deficit apportionment fills all 500 slots.
    for _ in range(size - len(keys)):
        key = max((k for k in keys if allocations[k] < len(cells[k])),
                  key=lambda k: (size * len(cells[k]) / len(rows) - allocations[k], k))
        allocations[key] += 1
    rng = random.Random(SEED)
    sample_rows = []
    for key in keys:
        for row in rng.sample(cells[key], allocations[key]):
            sample_rows.append({"chunk_id": str(row["chunk_id"]), "source_identity": key[0], "length_tercile": key[1], "text_sha256": hashlib.sha256(str(row["text"]).encode()).hexdigest()})
    return sorted(sample_rows, key=lambda r: r["chunk_id"])


def sample(db_path: Path, work: Path) -> dict[str, Any]:
    rows = _subset_rows(db_path)
    chunks = _stratified_sample(rows)
    queries, _ = _load_queries()
    chosen = _pool_queries(queries)
    if Counter(q["family"] for q in chosen) != {"G1": 7, "G2": 24, "G3": 89} or len({q["id"] for q in chosen}) != 120:
        raise ValueError("Evaluation allocation must be 7 G1 + 24 G2 + 89 G3 unique queries")
    rng = random.Random(SEED)
    cost_ids = rng.sample([q["id"] for q in chosen], 50)
    timing_ids = rng.sample([q["id"] for q in chosen if q["family"] == "G3"], 25)
    return _freeze(work / "evaluation-manifest.json", {
        "schema": "retrieval-bakeoff-9233-evaluation.v6.1", "seed": SEED,
        "corpus_rows": len(rows), "corpus_row_digest": _digest_rows(rows),
        "g3_sha256": G3_SHA256, "query_file_sha256": hashlib.sha256(QUERY_PATH.read_bytes()).hexdigest(),
        "queries": chosen, "cost_query_ids": cost_ids, "encode_sample": chunks,
        "encode_sample_sha256": _hash(chunks), "timing_query_ids": timing_ids,
        "timing_recipe": {"hybrid": f"H:{E5}", "top": TOP_RERANK, "rrf_k": RRF_K, "first_stage_depth": TOP_FIRST_STAGE, "tie_break": "chunk_id ascending", "seed": SEED},
    })


def _evaluation(work: Path) -> dict[str, Any]:
    result = _read_frozen(work / "evaluation-manifest.json")
    if result["encode_sample_sha256"] != _hash(result["encode_sample"]):
        raise ValueError("Encode sample hash mismatch")
    queries, _ = _load_queries()
    if result["queries"] != _pool_queries(queries) or result["g3_sha256"] != G3_SHA256 or result["query_file_sha256"] != hashlib.sha256(QUERY_PATH.read_bytes()).hexdigest():
        raise ValueError("Evaluation query configuration mismatch")
    if len(result["cost_query_ids"]) != 50 or len(set(result["cost_query_ids"])) != 50 or not set(result["cost_query_ids"]) <= {q["id"] for q in result["queries"]}:
        raise ValueError("Invalid frozen cost batch")
    rng = random.Random(SEED)
    expected_cost = rng.sample([q["id"] for q in result["queries"]], 50)
    expected_timing = rng.sample([q["id"] for q in result["queries"] if q["family"] == "G3"], 25)
    recipe = {"hybrid": f"H:{E5}", "top": TOP_RERANK, "rrf_k": RRF_K, "first_stage_depth": TOP_FIRST_STAGE, "tie_break": "chunk_id ascending", "seed": SEED}
    if result["cost_query_ids"] != expected_cost or result["timing_query_ids"] != expected_timing or result["timing_recipe"] != recipe or len(result["encode_sample"]) != 500:
        raise ValueError("Frozen sample/timing recipe mismatch")
    return result


def run_manifest(db_path: Path, work: Path, configurations: dict[str, Any]) -> dict[str, Any]:
    evaluation = _evaluation(work)
    if set(configurations) != set(EMBEDDERS) | set(RERANKERS):
        raise ValueError("Run manifest requires configurations for all six embedders and three rerankers")
    for repo, config in configurations.items():
        for revision in (config.get("revision"), config.get("tokenizer", {}).get("revision")):
            if not isinstance(revision, str) or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
                raise ValueError(f"Resolved 40-hex repository/tokenizer revision required for {repo}")
        if config.get("tokenizer", {}).get("revision") != config["revision"] or config.get("tokenizer", {}).get("repository") != repo or not isinstance(config.get("max_tokens"), int) or config["max_tokens"] < 1:
            raise ValueError(f"Tokenizer repository and finite max_tokens required for {repo}")
        if repo in EMBEDDERS and config.get("prefixes") != {"query": EMBEDDERS[repo]["query_prefix"], "passage": EMBEDDERS[repo]["passage_prefix"]}:
            raise ValueError(f"Prefix configuration mismatch for {repo}")
        if repo in RERANKERS and config.get("scoring_template") != RERANKERS[repo]:
            raise ValueError(f"Scoring template configuration mismatch for {repo}")
    rows = _subset_rows(db_path)
    if _digest_rows(rows) != evaluation["corpus_row_digest"]:
        raise ValueError("Evaluation corpus digest mismatch")
    return _freeze(work / "run-manifest.json", {
        "schema": "retrieval-bakeoff-9233-run.v6.1", "corpus_row_digest": _digest_rows(rows),
        "evaluation_manifest_sha256": evaluation["sha256"], "models": configurations,
        "passage_policies": PASSAGE_POLICIES, "guardrails": GUARDRAILS,
        "memory_enforcement_receipt": "memory-enforcement.json (actual enforcement per step)",
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "retrieval_configuration": {"rrf_k": RRF_K, "first_stage_depth": TOP_FIRST_STAGE, "rerank_depth": TOP_RERANK},
    })


def _validate_run(db_path: Path, work: Path) -> dict[str, Any]:
    result = _read_frozen(work / "run-manifest.json")
    expected = run_manifest(db_path, work, result["models"])
    if result != expected:
        raise ValueError("Run manifest configuration mismatch")
    return result


def _model_options(repo: str, work: Path) -> dict[str, Any]:
    config = _read_frozen(work / "run-manifest.json")["models"][repo]
    return {"revision": config["revision"]}


def _check_runtime(repo: str, meta: dict[str, Any], work: Path) -> None:
    config = _read_frozen(work / "run-manifest.json")["models"][repo]
    if meta["max_tokens"] != config["max_tokens"] or (repo in EMBEDDERS and meta["prefixes"] != config["prefixes"]):
        raise ValueError(f"Loaded tokenizer/prefix configuration mismatch for {repo}")


def _measurement_binding(work: Path) -> dict[str, Any]:
    run = _read_frozen(work / "run-manifest.json")
    evaluation = _evaluation(work)
    return {"run_manifest_sha256": run["sha256"], "evaluation_manifest_sha256": evaluation["sha256"], "encode_sample_sha256": evaluation["encode_sample_sha256"], "guardrails": GUARDRAILS}


def _positive(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return float(value)


def _borderline(p50: float, mean: float, hybrid_count: int) -> bool:
    projection = mean * hybrid_count * 120
    return abs(p50 / 10 - 1) <= 0.1000000001 or abs(projection / (8 * 3600) - 1) <= 0.1000000001


def _measurement_preflight(work: Path, repo: str, variant: str, repeat: bool) -> None:
    if repo in EMBEDDERS:
        if variant != "fp32" or repeat:
            raise ValueError("Embedders use one frozen FP32 measurement")
        return
    if repo not in RERANKERS:
        raise ValueError("Unknown reranker")
    admitted = _admission(work)
    hybrid_count = len(admitted["admitted_embedders"])
    binding = _measurement_binding(work)
    def read(precision: str, second: bool) -> dict[str, Any]:
        path = work / "measurements" / (repo.replace("/", "--") + f"-{precision}-{int(second)}.json")
        result = json.loads(path.read_text())
        if any(result.get(key) != value for key, value in binding.items()):
            raise ValueError("Measurement configuration mismatch")
        return result
    if variant == "int8":
        first_fp32 = read("fp32", False)
        fp32 = read("fp32", True) if _borderline(first_fp32["p50_seconds"], first_fp32["mean_seconds"], hybrid_count) else first_fp32
        if fp32["p50_seconds"] <= 10 and fp32["mean_seconds"] * hybrid_count * 120 <= 8 * 3600:
            raise ValueError("INT8 fallback requires a failing FP32 measurement")
    if repeat:
        first = read(variant, False)
        if not _borderline(first["p50_seconds"], first["mean_seconds"], hybrid_count):
            raise ValueError("Remeasurement is only allowed within 10 percent of a threshold")


def admit(work: Path, measurements: dict[str, Any], *, persist: bool = True) -> dict[str, Any]:
    binding = _measurement_binding(work)
    if any(measurements.get(key) != value for key, value in binding.items()):
        raise ValueError("Measurements do not match frozen run/sample/guardrails")
    encoded = measurements.get("embedders", {})
    if set(encoded) != set(EMBEDDERS):
        raise ValueError("All six encode measurements required before admission")
    lexical = _read_frozen(work / "lexical-measurement.json")
    if any(lexical.get(key) != value for key, value in binding.items()):
        raise ValueError("Lexical measurement configuration mismatch")
    measurements = {**measurements, "lexical_query_seconds": _positive(lexical["lexical_query_seconds"], "Lexical query seconds")}
    for value in encoded.values():
        _positive(value.get("query_seconds"), "Dense query seconds")
        if not isinstance(value.get("batch_size"), int) or value["batch_size"] < 1:
            raise ValueError("Measured positive batch size required")
    total = 0.0
    admitted, excluded = [], []
    for repo in sorted(encoded, key=lambda r: (_positive(encoded[r]["projected_seconds"], r), r)):
        seconds = _positive(encoded[repo]["projected_seconds"], repo)
        if total + seconds <= 20 * 3600:
            admitted.append(repo)
            total += seconds
        else:
            excluded.append(repo)
    rerank_decisions = {}
    for repo, variants in measurements.get("rerankers", {}).items():
        if repo not in RERANKERS:
            raise ValueError(f"Unsupported reranker: {repo}")
        evaluations = []
        accepted = None
        for variant in ("fp32", "int8"):
            attempts = variants.get(variant)
            if not attempts:
                raise ValueError(f"Missing {variant} fallback measurement for failing {repo}")
            if len(attempts) > 2:
                raise ValueError("At most one borderline remeasurement is allowed")
            first = attempts[0]
            p50 = _positive(first["p50_seconds"], "p50")
            mean = _positive(first["mean_seconds"], "mean query latency")
            borderline = _borderline(p50, mean, len(admitted))
            if len(attempts) != (2 if borderline else 1):
                raise ValueError("Borderline measurement requires exactly one remeasurement")
            chosen = attempts[-1]
            p50 = _positive(chosen["p50_seconds"], "p50")
            p95 = _positive(chosen["p95_seconds"], "p95")
            if p95 < p50 or chosen.get("timing_pairs_sha256") != _read_frozen(work / "timing-pairs.json")["sha256"]:
                raise ValueError("Invalid latency distribution or realised timing-pair hash")
            projected = _positive(chosen["mean_seconds"], "mean query latency") * len(admitted) * 120
            passes = projected <= 8 * 3600 and p50 <= 10
            evaluations.append({"variant": variant, "attempts": attempts, "projected_seconds": projected, "admitted": passes})
            if passes:
                accepted = variant
                break
        rerank_decisions[repo] = {"variant": accepted, "measurements": evaluations}
    result = {"schema": "retrieval-bakeoff-9233-admission.v6.1", **binding,
              "admitted_embedders": admitted, "excluded_embedders": excluded,
              "encode_total_projected_seconds": total, "encode_budget_seconds": 20 * 3600,
              "rerankers": rerank_decisions, "measurements": measurements,
              "comparison_scope": "best among evaluated configurations"}
    if persist:
        _write_json(work / "admission.json", result)
    return result


def _admission(work: Path) -> dict[str, Any]:
    result = json.loads((work / "admission.json").read_text())
    binding = _measurement_binding(work)
    if any(result.get(key) != value for key, value in binding.items()):
        raise ValueError("Admission manifest mismatch")
    # Recompute the resource decisions rather than trusting edited admitted lists.
    computed = admit(work, result["measurements"], persist=False)
    if result != computed:
        raise ValueError("Admission decision mismatch")
    return result


def freeze_timing_pairs(work: Path, search_result: dict[str, Any]) -> dict[str, Any]:
    evaluation = _evaluation(work)
    hybrid = evaluation["timing_recipe"]["hybrid"]
    run_sha = _read_frozen(work / "run-manifest.json")["sha256"]
    if search_result.get("run_manifest_sha256") != run_sha or search_result.get("evaluation_manifest_sha256") != evaluation["sha256"] or hybrid not in search_result["arms"]:
        raise ValueError("Timing candidates require frozen E5 hybrid retrieval")
    pairs = []
    for qid in evaluation["timing_query_ids"]:
        ids = search_result["arms"][hybrid].get(qid, [])[:TOP_RERANK]
        if len(ids) != TOP_RERANK or len(set(ids)) != TOP_RERANK:
            raise ValueError("Each timing query requires 20 unique E5 hybrid candidates")
        pairs.append({"query_id": qid, "candidate_ids": ids})
    return _freeze(work / "timing-pairs.json", {"run_manifest_sha256": run_sha, "evaluation_manifest_sha256": evaluation["sha256"], "recipe": evaluation["timing_recipe"], "pairs": pairs})


def _passage(text: str, tokenizer: Any, *, budget: int, tail: bool) -> tuple[str, bool, int]:
    tokens = tokenizer.encode(text, add_special_tokens=False)
    if len(tokens) <= budget:
        return text, False, len(text)
    # Count retained original characters using token offsets, rather than the
    # length of decoded text (which may normalize whitespace or Unicode).
    try:
        encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
        offsets = encoded["offset_mapping"]
    except (TypeError, NotImplementedError, KeyError) as exc:
        raise ValueError("Tokenizer offsets required to measure retained original characters") from exc
    if list(encoded["input_ids"]) != list(tokens) or len(offsets) != len(tokens):
        raise ValueError("Tokenizer offset/token mismatch")
    head_end = int(offsets[127 if tail else budget - 1][1])
    tail_start = int(offsets[-384][0]) if tail else len(text)
    retained = min(len(text), head_end + len(text) - tail_start)
    if not 0 <= retained <= len(text):
        raise ValueError("Passage preview has invalid offsets")
    # Source offsets preserve original characters and keep the pieces apart.
    preview = text[:head_end] + " … " + text[tail_start:] if tail else text[:head_end]
    # Decoding pieces is not token-count preserving. Slice the re-encoded
    # preview at a token boundary and recheck, including normalizing tokenizers.
    while len(tokenizer.encode(preview, add_special_tokens=False)) > budget:
        encoded_preview = tokenizer(preview, add_special_tokens=False, return_offsets_mapping=True)
        cut = int(encoded_preview["offset_mapping"][budget - 1][1])
        if cut >= len(preview):
            cut = len(preview) - 1
        preview = preview[:max(0, cut)]
        retained = min(len(preview), head_end) + max(0, len(preview) - head_end - 3) if tail else len(preview)
    return preview, True, retained


def _passage_stats(rows: list[dict[str, Any]], tokenizer: Any, budget: int, *, tail: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    previews = []
    for row in rows:
        text = str(row["text"])
        preview, truncated, retained = _passage(text, tokenizer, budget=budget, tail=tail)
        previews.append({**row, "text": preview})
        counts = totals[str(row.get("source_file", "unknown"))]
        counts[0] += 1
        counts[1] += truncated
        counts[2] += len(text)
        counts[3] += retained
    return previews, {source: {"passages": c[0], "truncation_rate": c[1] / c[0], "retained_character_share": c[3] / c[2] if c[2] else 1.0} for source, c in sorted(totals.items())}


def _embedder_passage_stats(rows: list[dict[str, Any]], model: Any, meta: dict[str, Any], repo: str) -> dict[str, Any]:
    tokenizer = model.tokenizer
    prefix = meta.get("prefixes", {}).get("passage", EMBEDDERS[repo]["passage_prefix"])
    if EMBEDDERS[repo]["kind"] == "jina":
        prefix = model.prompts.get("document", "")
    overhead = len(tokenizer.encode(prefix, add_special_tokens=False))
    if hasattr(tokenizer, "num_special_tokens_to_add"):
        overhead += tokenizer.num_special_tokens_to_add(pair=False)
    budget = meta["max_tokens"] - overhead
    if budget < 1:
        raise ValueError("Embedding prompt leaves no passage token budget")
    return _passage_stats(rows, tokenizer, budget, tail=False)[1]


def _reranker_tokenizer(model: Any, meta: dict[str, Any]) -> Any:
    return model[1] if meta["kind"] == "qwen" else model._tokenizer if meta["kind"] == "jina" else model.tokenizer


def _quantize_reranker(model: Any, meta: dict[str, Any]) -> Any:
    import torch

    def quantize(module: Any) -> Any:
        return torch.ao.quantization.quantize_dynamic(module, {torch.nn.Linear}, dtype=torch.qint8, inplace=False)
    if meta["kind"] == "qwen":
        return quantize(model[0]), model[1]
    if meta["kind"] == "cross_encoder":
        model.model = quantize(model.model)
        return model
    return quantize(model)


def measure(db_path: Path, work: Path, repo: str, *, batch_size: int = 16, variant: str = "fp32", repeat: bool = False) -> dict[str, Any]:
    _validate_run(db_path, work)
    evaluation = _evaluation(work)
    _measurement_preflight(work, repo, variant, repeat)
    rows = [dict(row) for row in _subset_rows(db_path)]
    by_id = {row["chunk_id"]: row for row in rows}
    binding = _measurement_binding(work)
    lexical = _measure_lexical(db_path, work)
    checkpoint_path = work / "measurements" / (repo.replace("/", "--") + f"-{variant}-{int(repeat)}-progress.json")
    progress = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {"binding": binding, "units": []}
    if progress["binding"] != binding or progress.get("batch_size", batch_size) != batch_size:
        raise ValueError("Measurement checkpoint mismatch")
    progress["batch_size"] = batch_size
    if repo in EMBEDDERS:
        chosen = [by_id[r["chunk_id"]] for r in evaluation["encode_sample"]]
        load_started = time.perf_counter()
        model, meta = _new_encoder(repo, work)
        model_load_seconds = time.perf_counter() - load_started
        _check_runtime(repo, meta, work)
        stats = _embedder_passage_stats(chosen, model, meta, repo)
        # Warmup is outside the frozen 500-chunk steady-state measurement.
        _encode_batch(model, meta, [str(r["text"]) for r in chosen[:batch_size]], repo, batch_size)
        for offset in range(len(progress["units"]) * batch_size, len(chosen), batch_size):
            started = time.perf_counter()
            _encode_batch(model, meta, [str(r["text"]) for r in chosen[offset:offset + batch_size]], repo, batch_size)
            progress["units"].append(time.perf_counter() - started)
            _write_json(checkpoint_path, progress)
        seconds = sum(progress["units"])
        query_times = []
        query_by_id = {q["id"]: q for q in evaluation["queries"]}
        for qid in evaluation["cost_query_ids"]:
            before = time.perf_counter()
            _query_vector(model, meta, query_by_id[qid]["query"], repo)
            query_times.append(time.perf_counter() - before)
        result = {"model": repo, **binding, "sample_rows": len(chosen), "sample_seconds": seconds, "model_load_seconds": model_load_seconds, "batch_size": batch_size, "chunks_per_second": len(chosen) / seconds, "projected_seconds": seconds * len(rows) / len(chosen), "query_seconds": statistics.mean(query_times), "passage_stats": stats}
    else:
        if repo not in RERANKERS or variant not in {"fp32", "int8"}:
            raise ValueError("Unknown reranker or precision")
        frozen = _read_frozen(work / "timing-pairs.json")
        if frozen["run_manifest_sha256"] != binding["run_manifest_sha256"] or frozen["evaluation_manifest_sha256"] != evaluation["sha256"] or frozen["recipe"] != evaluation["timing_recipe"] or [p["query_id"] for p in frozen["pairs"]] != evaluation["timing_query_ids"]:
            raise ValueError("Timing manifest mismatch")
        if any(len(pair["candidate_ids"]) != 20 or len(set(pair["candidate_ids"])) != 20 or not set(pair["candidate_ids"]) <= set(by_id) for pair in frozen["pairs"]):
            raise ValueError("Timing manifest mismatch")
        load_started = time.perf_counter()
        model, meta = _new_reranker(repo, work)
        model_load_seconds = time.perf_counter() - load_started
        _check_runtime(repo, meta, work)
        if variant == "int8":
            model = _quantize_reranker(model, meta)
        queries = {q["id"]: q["query"] for q in evaluation["queries"]}
        times = progress["units"]
        stats = {}
        for index, pair in enumerate(frozen["pairs"]):
            candidates = [by_id[cid] for cid in pair["candidate_ids"]]
            _, stats[pair["query_id"]] = _passage_stats(candidates, _reranker_tokenizer(model, meta), 512, tail=True)
            if index < len(times):
                continue
            started = time.perf_counter()
            ranked = _rerank(model, meta, queries[pair["query_id"]], candidates)
            _assert_permutation(pair["candidate_ids"], ranked)
            times.append(time.perf_counter() - started)
            _write_json(checkpoint_path, progress)
        result = {"model": repo, "variant": variant, **binding, "timing_pairs_sha256": frozen["sha256"], "query_seconds": times, "model_load_seconds": model_load_seconds, "p50_seconds": statistics.median(times), "p95_seconds": _percentile(times, .95), "mean_seconds": statistics.mean(times), "passage_stats": stats}
    result["lexical_query_seconds"] = lexical["lexical_query_seconds"]
    _write_json(work / "measurements" / (repo.replace("/", "--") + f"-{variant}-{int(repeat)}.json"), result)
    return result


def _assert_permutation(before: list[str], after: list[str]) -> None:
    if len(before) != len(after) or len(set(before)) != len(before) or set(before) != set(after):
        raise ValueError("Reranker must permute the hybrid top 20; no pool additions allowed")


def _admission_probe() -> bool:
    from scripts.common.task_store_paths import tasks_dir
    from scripts.orchestration.dispatch_admission import evaluate

    decision = evaluate("danger", tasks_dir())
    probe = decision.probe
    return bool(decision.admitted and probe and probe.proc_available and probe.mem_available_bytes is not None and probe.load_per_cpu is not None)


def _enforce_host_limits() -> dict[str, Any]:
    # Memory is enforced by the launcher/supervisor, never virtual address space.
    os.nice(max(0, 19 - os.getpriority(os.PRIO_PROCESS, 0)))
    import psutil

    psutil.Process().ionice(psutil.IOPRIO_CLASS_IDLE)
    for key in THREAD_ENV:
        os.environ[key] = str(THREADS)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import torch

    torch.set_num_threads(THREADS)
    torch.set_num_interop_threads(THREADS)
    return {**GUARDRAILS, "memory_enforcement": os.environ.get("LU_BAKEOFF_MEMORY_ENFORCEMENT", "rss_watchdog")}


def _scope_environment() -> dict[str, str]:
    environment = dict(os.environ)
    runtime = f"/run/user/{os.getuid()}"
    if not environment.get("XDG_RUNTIME_DIR"):
        environment["XDG_RUNTIME_DIR"] = runtime
    if not environment.get("DBUS_SESSION_BUS_ADDRESS"):
        environment["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={runtime}/bus"
    for key in THREAD_ENV:
        environment[key] = str(THREADS)
    return environment


def _scope_command() -> list[str]:
    return ["systemd-run", "--user", "--scope", "--quiet", "-p", "MemoryMax=10G", "-p", "MemorySwapMax=0"]


class _HeavyProcess:
    def __init__(self, process: Any):
        self.process = process
        self.pid = process.pid

    def is_alive(self) -> bool:
        return self.process.poll() is None

    def terminate(self) -> None:
        self._signal(signal.SIGTERM)

    def kill(self) -> None:
        self._signal(signal.SIGKILL)

    def _signal(self, number: int) -> None:
        with suppress(ProcessLookupError):
            os.killpg(self.pid, number)

    def join(self, timeout: float) -> None:
        with suppress(subprocess.TimeoutExpired):
            self.process.wait(timeout=timeout)


class _ResultFile:
    def __init__(self, path: Path):
        self.path = path

    def poll(self, timeout: float) -> bool:
        if not self.path.exists():
            time.sleep(timeout)
        return self.path.exists()

    def recv(self) -> dict[str, Any]:
        return json.loads(self.path.read_text())

    def send(self, message: dict[str, Any]) -> None:
        _write_json(self.path, message)

    def close(self) -> None:
        pass


def _file_worker(payload_path: Path, result_path: Path) -> None:
    _write_json(result_path.with_suffix(".started"), {"started": True})
    payload = json.loads(payload_path.read_text())
    functions = {f.__name__: f for f in (measure, encode, _run_arm)}
    args = tuple(Path(a["path"]) if isinstance(a, dict) and set(a) == {"path"} else a for a in payload["args"])
    _heavy_worker(_ResultFile(result_path), functions[payload["function"]], args, payload["kwargs"])


def _launch_heavy(function: Any, args: tuple, kwargs: dict, work: Path) -> tuple[Any, Any, str]:
    environment = _scope_environment()
    try:
        scoped = subprocess.run([*_scope_command(), "true"], env=environment, capture_output=True, timeout=10, check=False).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        scoped = False
    enforcement = "systemd_scope" if scoped else "rss_watchdog"
    environment["LU_BAKEOFF_MEMORY_ENFORCEMENT"] = enforcement
    payload_path = work / "steps" / "worker-input.json"
    result_path = work / "steps" / "worker-result.json"
    # Unique output avoids consuming a prior result after an interrupted step.
    result_path = result_path.with_name(f"worker-result-{os.getpid()}-{time.time_ns()}.json")
    _write_json(payload_path, {"function": function.__name__, "args": [{"path": str(a)} if isinstance(a, Path) else a for a in args], "kwargs": kwargs})
    command = [str(project_interpreter(ROOT)), "-c", "from pathlib import Path; import sys; from scripts.wiki.diagnostics.retrieval_bakeoff_9233 import _file_worker; _file_worker(Path(sys.argv[1]), Path(sys.argv[2]))", str(payload_path), str(result_path)]
    if scoped:
        command = _scope_command() + command
    process = subprocess.Popen(command, env=environment, cwd=ROOT, start_new_session=True)
    if scoped:
        # A successful probe does not guarantee the subsequent scope starts.
        # Retry only a launcher failure before the worker's start receipt; an
        # OOM kill or any failure after entry must never restart compute.
        expires = time.monotonic() + 10
        while process.poll() is None and not result_path.with_suffix(".started").exists() and time.monotonic() < expires:
            time.sleep(.05)
        if process.poll() == 1 and not result_path.with_suffix(".started").exists():
            enforcement = "rss_watchdog"
            environment["LU_BAKEOFF_MEMORY_ENFORCEMENT"] = enforcement
            process = subprocess.Popen(command[len(_scope_command()):], env=environment, cwd=ROOT, start_new_session=True)
    return _HeavyProcess(process), _ResultFile(result_path), enforcement


def _resident_bytes(process: Any) -> int:
    import psutil

    try:
        parent = psutil.Process(process.pid)
        processes = [parent, *parent.children(recursive=True)]
    except psutil.NoSuchProcess:
        return 0
    total = 0
    for child in processes:
        try:
            total += child.memory_info().rss
        except psutil.NoSuchProcess:
            continue
    return total


@contextmanager
def _heavy_lock():
    # One host-wide lock across work directories and linked worktrees.
    path = Path(tempfile.gettempdir()) / f"retrieval-bakeoff-9233-heavy-{os.getuid()}.lock"
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another heavy bake-off job is running") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _stop_reason(running_seconds: float, projection: float, refused_since: float | None, now: float) -> str | None:
    if running_seconds > 1.5 * projection:
        return "DEADLINE"
    if refused_since is not None and now - refused_since >= 30 * 60:
        return "ADMISSION_REFUSED"
    return None


def _heavy_worker(connection: Any, function: Any, args: tuple, kwargs: dict) -> None:
    try:
        limits = _enforce_host_limits()
        connection.send({"ok": True, "result": function(*args, **kwargs), "guardrails": limits})
    except Exception as exc:
        connection.send({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        connection.close()


def _supervise(process: Any, pipe: Any, state: dict[str, Any], projection: float, *, clock: Any = time.monotonic, probe: Any = None, window_end: float | None = None, wall_clock: Any = time.time, rss: Any = None) -> dict[str, Any]:
    probe = probe or _admission_probe
    started = clock()
    previous_running = float(state.get("running_seconds", 0))
    refused_since = None
    next_probe = started + 300
    try:
        while True:
            now = clock()
            if now >= next_probe:
                try:
                    healthy = probe()
                except (OSError, ValueError):
                    healthy = False
                refused_since = None if healthy else now if refused_since is None else refused_since
                next_probe = now + 300
            reason = _stop_reason(previous_running + now - started, projection, refused_since, now)
            if state.get("memory_enforcement") == "rss_watchdog" and (rss or _resident_bytes)(process) > MEMORY_BYTES:
                reason = "MEMORY_LIMIT"
            if window_end is not None and wall_clock() >= window_end:
                reason = "QUIET_WINDOW_ENDED"
            if reason:
                process.terminate()
                process.join(timeout=10)
                if process.is_alive():
                    process.kill()
                    process.join(timeout=10)
                state["status"] = reason
                raise RuntimeError(f"Heavy step stopped: {reason}; resume in the next quiet window")
            if pipe.poll(min(1.0, max(0.01, 1.5 * projection - previous_running - (now - started)))):
                try:
                    message = pipe.recv()
                except EOFError as exc:
                    state["status"] = "failed"
                    raise RuntimeError("Heavy process exited without a measurement") from exc
                state["status"] = "done" if message["ok"] else "failed"
                if not message["ok"]:
                    raise RuntimeError(message["error"])
                return message
            if not process.is_alive():
                state["status"] = "failed"
                raise RuntimeError("Heavy process exited without a measurement")
    finally:
        state["running_seconds"] = previous_running + clock() - started


def _guarded_step(function: Any, args: tuple, kwargs: dict, work: Path, step: str, projection: float, *, window_end: float | None = None) -> dict[str, Any]:
    _positive(projection, "Measured step projection")
    path = work / "steps" / (hashlib.sha256(step.encode()).hexdigest() + ".json")
    binding = _measurement_binding(work)
    old = json.loads(path.read_text()) if path.exists() else {}
    if old and (old["binding"] != binding or old["projection_seconds"] != projection):
        raise ValueError("Resumable step configuration mismatch")
    if old.get("status") == "done":
        return old["result"]
    if old.get("running_seconds", 0) >= 1.5 * projection:
        raise RuntimeError("Heavy step stopped: DEADLINE; cumulative running-time budget exhausted")
    # Calendar duration persists across quiet windows; running duration does not
    # accrue while stopped. Deadline is never reset by a resume.
    state = {**old, "binding": binding, "projection_seconds": projection, "calendar_started": old.get("calendar_started", time.time())}
    with _heavy_lock():
        if window_end is not None and time.time() >= window_end:
            raise ValueError("Quiet window has ended; resume in the next quiet window")
        if not _admission_probe():
            raise ValueError("Dispatch admission unhealthy or unknown; heavy step not started")
        launch_started = time.monotonic()
        process, parent, enforcement = _launch_heavy(function, args, kwargs, work)
        try:
            state["memory_enforcement"] = enforcement
            receipt_path = work / "memory-enforcement.json"
            receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
            receipt[step] = {"memory_enforcement": enforcement, "memory_bytes": MEMORY_BYTES, "binding": binding}
            _write_json(receipt_path, receipt)
            state["running_seconds"] = float(state.get("running_seconds", 0)) + time.monotonic() - launch_started
            message = _supervise(process, parent, state, projection, window_end=window_end)
            result = message["result"]
            result["host_guardrails"] = message["guardrails"]
            result["host_running_seconds"] = state["running_seconds"]
            state["result"] = result
            return result
        finally:
            if process.is_alive():
                process.terminate()
            process.join(timeout=10)
            if process.is_alive():
                process.kill()
                process.join(timeout=10)
            parent.close()
            state["calendar_seconds"] = time.time() - state["calendar_started"]
            _write_json(path, state)


def _ro_connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def _work_dir(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == ROOT.resolve() or ROOT.resolve() in resolved.parents:
        raise ValueError("--work-dir must be outside the repository so data/ remains read-only")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _default_sources_db() -> Path:
    return Path(sources_db._read_db_path())


def _default_vesum_db() -> Path:
    return Path(__import__("scripts.verification.vesum", fromlist=["VESUM_DB_PATH"]).VESUM_DB_PATH)


def _subset_clause(alias: str = "t") -> str:
    placeholders = ",".join("?" for _ in EXTRA_SOURCES)
    return f"({alias}.subject IN ('ukrmova','bukvar') OR {alias}.source_file LIKE 'ulp-%' OR {alias}.source_file IN ({placeholders}))"


def _subset_args() -> tuple[str, ...]:
    return EXTRA_SOURCES


def _subset_rows(db_path: Path) -> list[sqlite3.Row]:
    with _ro_connect(db_path) as source:
        for identity in EXTRA_SOURCES:
            if not source.execute("SELECT 1 FROM textbooks WHERE source_file=? LIMIT 1", (identity,)).fetchone():
                raise ValueError(f"Listed source identity matches zero rows: {identity}")
        return source.execute(
            f"SELECT id,chunk_id,title,text,source_file,subject,parent_section_id FROM textbooks t WHERE {_subset_clause()} ORDER BY id",
            _subset_args(),
        ).fetchall()


def _copy_subset(db_path: Path, work: Path, *, vesum_path: Path | None = None) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    target = work / "corpus.sqlite3"
    rows = _subset_rows(db_path)
    digest = _digest_rows(rows)
    if target.exists():
        with _ro_connect(target) as cached:
            metadata = dict(cached.execute("SELECT key,value FROM metadata"))
            cached_rows = cached.execute("SELECT id,chunk_id,title,text,source_file,subject,parent_section_id FROM chunks ORDER BY id").fetchall()
            indexed = cached.execute("SELECT rowid,chunk_id,title,text FROM chunks_fts ORDER BY rowid").fetchall()
        if metadata.get("index_contract") != "A1-lemma-shared-v1" or metadata.get("row_digest") != digest or _digest_rows(cached_rows) != digest or _digest_rows(indexed) != metadata.get("index_digest"):
            raise ValueError("Cached corpus digest/lemma contract mismatch; use a fresh --work-dir")
        return target
    with get_vesum_connection(vesum_path or _default_vesum_db()) as vesum:
        expanded, _ = phase1.lemma_expanded_rows(rows, vesum)
    with sqlite3.connect(target) as conn:
        conn.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY, chunk_id TEXT UNIQUE, title TEXT, text TEXT, source_file TEXT, subject TEXT, parent_section_id INTEGER)")
        conn.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?)", [tuple(row) for row in rows])
        conn.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(chunk_id UNINDEXED, title, text, tokenize='unicode61')")
        conn.executemany("INSERT INTO chunks_fts(rowid,chunk_id,title,text) VALUES (?,?,?,?)", [row[:4] for row in expanded])
        conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
        conn.executemany("INSERT INTO metadata VALUES (?,?)", [("index_contract", "A1-lemma-shared-v1"), ("row_digest", digest), ("index_digest", _digest_rows([row[:4] for row in expanded]))])
    return target


def _digest_rows(rows: list[sqlite3.Row] | list[tuple[Any, ...]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        payload = [row[i] for i in range(len(row))]
        digest.update(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def corpus(db_path: Path, work: Path) -> dict[str, Any]:
    rows = _subset_rows(db_path)
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        identity = str(row["subject"] or "")
        if identity not in {"ukrmova", "bukvar"}:
            identity = str(row["source_file"] or "")
        counts[identity] += 1
    result = {"rows": len(rows), "row_digest_sha256": _digest_rows(rows), "identity_counts": dict(sorted(counts.items())), "subset": "ukrmova, bukvar, ULP source files, and v5 item 7 source identities"}
    _copy_subset(db_path, work)
    if (work / "run-manifest.json").exists():
        result["lexical_measurement"] = _measure_lexical(db_path, work)
    return result


def _measure_lexical(db_path: Path, work: Path) -> dict[str, Any]:
    path = work / "lexical-measurement.json"
    binding = _measurement_binding(work)
    if path.exists():
        result = _read_frozen(path)
        if any(result.get(key) != value for key, value in binding.items()):
            raise ValueError("Lexical measurement configuration mismatch")
        return result
    evaluation = _evaluation(work)
    queries = {q["id"]: q["query"] for q in evaluation["queries"]}
    times = []
    with _ro_connect(_copy_subset(db_path, work)) as index, get_vesum_connection(_default_vesum_db()) as vesum:
        for qid in evaluation["cost_query_ids"]:
            started = time.perf_counter()
            _fts_search(index, queries[qid], vesum, lemma=True, limit=TOP_FIRST_STAGE)
            times.append(time.perf_counter() - started)
    return _freeze(path, {**binding, "cost_query_ids": evaluation["cost_query_ids"], "query_seconds": times, "lexical_query_seconds": _positive(statistics.mean(times), "Lexical query seconds")})


def _vesum_analyses(conn: sqlite3.Connection, token: str) -> list[tuple[str, str]]:
    return [(str(row[0]), str(row[1])) for row in conn.execute(
        "SELECT DISTINCT pos,tags FROM forms_all WHERE word_form=?", (token,))]


def _is_function_analysis(pos: str, tags: str) -> bool:
    return pos in FUNCTION_POS or (pos in {"adv", "noun", "adj"} and "pron" in tags.split(":") and "int" in tags.split(":"))


def _topic_tokens(tokens: list[str], vesum: sqlite3.Connection) -> set[str]:
    """Keep metalinguistic alternatives and governed lists as topic terms."""
    topics: set[str] = set()
    markers = {"вибрати", "пишемо", "писати", "чергування", "прийменників", "сполучників", "після", "замість"}
    for index, token in enumerate(tokens):
        if token not in markers:
            continue
        tail = tokens[index + 1:]
        # A list contains two or more lexical function terms. The connector
        # itself is not enough to make an ordinary sentence metalinguistic.
        listed = {t for t in tail if t in TOPIC_FUNCTION_WORDS or any(pos == "prep" for pos, _ in _vesum_analyses(vesum, t))}
        if len(listed) >= 2:
            topics.update(listed)
    return topics


def filter_lemma_query(query: str, vesum: sqlite3.Connection) -> list[str]:
    """Use real VESUM POS/tags; keep topics and content/preposition homonyms."""
    tokens = list(dict.fromkeys(phase1.tokenize(query)))
    topics = _topic_tokens(tokens, vesum)
    content = []
    for token in tokens:
        analyses = _vesum_analyses(vesum, token)
        is_function = token in EXPLICIT_FUNCTION_WORDS or (bool(analyses) and all(_is_function_analysis(pos, tags) for pos, tags in analyses))
        if not is_function:
            content.append(token)
    if len(content) < 2:
        return tokens
    return [token for token in tokens if token in content or token in topics]


def _lemma_terms(query: str, vesum: sqlite3.Connection) -> list[str]:
    terms: list[str] = []
    for token in filter_lemma_query(query, vesum):
        rows = vesum.execute(
            "SELECT DISTINCT f.lemma FROM forms_all f WHERE f.word_form=? AND NOT EXISTS (SELECT 1 FROM form_markers m WHERE m.form_id=f.id AND m.marker IN ('bad','obsc','subst')) ORDER BY f.lemma",
            (token,),
        ).fetchall()
        terms.extend(phase1.normalize_token(str(row[0])) for row in rows)
        if not rows:
            terms.append(phase1.normalize_token(token))
    return list(dict.fromkeys(terms))


def _fts_search(conn: sqlite3.Connection, query: str, vesum: sqlite3.Connection, *, lemma: bool, limit: int) -> list[str]:
    terms = _lemma_terms(query, vesum) if lemma else list(dict.fromkeys(phase1.tokenize(query)))
    expression = sources_db._build_preserving_fts_query(terms)
    if not expression:
        return []
    return [str(row[0]) for row in conn.execute(
        "SELECT c.chunk_id FROM chunks_fts JOIN chunks c ON c.id=chunks_fts.rowid WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts,0,5.0,1.0),c.id LIMIT ?",
        (expression, limit),
    )]


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = RRF_K, limit: int = TOP_FIRST_STAGE) -> list[str]:
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] += 1.0 / (k + rank)
    return sorted(scores, key=lambda item: (-scores[item], item))[:limit]


def _load_rows(corpus_path: Path) -> list[dict[str, Any]]:
    with _ro_connect(corpus_path) as conn:
        return [dict(row) for row in conn.execute("SELECT id,chunk_id,title,text,source_file,subject,parent_section_id FROM chunks ORDER BY id")]


def _model_cache(work: Path) -> None:
    cache = work / "model-cache"
    cache.mkdir(parents=True, exist_ok=True)
    for key in ("HF_HOME", "HF_HUB_CACHE", "TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME"):
        os.environ[key] = str(cache)


def _new_encoder(repo: str, work: Path) -> tuple[Any, dict[str, Any]]:
    _model_cache(work)
    spec = EMBEDDERS[repo]
    options = _model_options(repo, work)
    if spec["kind"] == "flag":
        from FlagEmbedding import BGEM3FlagModel
        from huggingface_hub import snapshot_download

        snapshot = snapshot_download(repo, revision=options["revision"], cache_dir=str(work / "model-cache"))
        model = BGEM3FlagModel(snapshot, use_fp16=False, devices="cpu", cache_dir=str(work / "model-cache"))
        max_tokens = 8192
        model.tokenizer.truncation_side = "right"
        return model, {"kind": "flag", "max_tokens": max_tokens, "prefixes": {"query": "", "passage": ""}}
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(repo, device="cpu", cache_folder=str(work / "model-cache"), trust_remote_code=spec["kind"] == "jina", **options)
    max_tokens = int(model.max_seq_length)
    model.tokenizer.truncation_side = "right"
    prompts = model.prompts
    prefixes = {"query": prompts.get("query", spec["query_prefix"]), "passage": prompts.get("document", spec["passage_prefix"])}
    if spec["kind"] == "jina":
        prefixes = {"query": spec["query_prefix"], "passage": spec["passage_prefix"]}
    return model, {"kind": spec["kind"], "max_tokens": max_tokens, "prefixes": prefixes,
                   "prompt_names": {"query": "query" if "query" in prompts else None, "passage": "document" if "document" in prompts else None}}


def _encode_batch(model: Any, meta: dict[str, Any], texts: list[str], repo: str, batch_size: int) -> Any:
    spec = EMBEDDERS[repo]
    prefixes = meta.get("prefixes", {"passage": spec["passage_prefix"]})
    prompt_name = meta.get("prompt_names", {}).get("passage")
    passages = texts if prompt_name or spec["kind"] == "jina" else [prefixes["passage"] + text for text in texts]
    if meta["kind"] == "flag":
        result = model.encode(passages, batch_size=batch_size, max_length=meta["max_tokens"], return_dense=True, return_sparse=False, return_colbert_vecs=False)
        return result["dense_vecs"]
    options = {"task": "retrieval", "prompt_name": "document"} if spec["kind"] == "jina" else {"prompt_name": prompt_name} if prompt_name else {"prompt": ""}
    return model.encode(passages, batch_size=batch_size, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False, **options)


def encode(db_path: Path, work: Path, repo: str, *, limit: int | None, batch_size: int) -> dict[str, Any]:
    if repo not in EMBEDDERS:
        raise ValueError(f"Unsupported embedding repository: {repo}")
    if batch_size < 1:
        raise ValueError("Batch size must be positive")
    _validate_run(db_path, work)
    admission = _admission(work)
    if repo not in admission["admitted_embedders"]:
        raise ValueError("Embedder not admitted by the resource budget")
    corpus_path = _copy_subset(db_path, work)
    rows = _load_rows(corpus_path)
    if limit is not None:
        rows = rows[:limit]
    destination = work / "embeddings" / (repo.replace("/", "--") + ".sqlite3")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        with _ro_connect(destination) as cached:
            if not cached.execute("SELECT 1 FROM sqlite_master WHERE name='index_metadata'").fetchone():
                raise ValueError("Existing vectors lack frozen run manifest provenance")
    db = sqlite3.connect(destination)
    db.execute("CREATE TABLE IF NOT EXISTS index_metadata (key TEXT PRIMARY KEY, value TEXT)")
    index_binding = dict(db.execute("SELECT key,value FROM index_metadata"))
    run_sha = _measurement_binding(work)["run_manifest_sha256"]
    if index_binding and index_binding.get("run_manifest_sha256") != run_sha:
        db.close()
        raise ValueError("Vector index run manifest mismatch")
    db.execute("INSERT OR IGNORE INTO index_metadata VALUES ('run_manifest_sha256',?)", (run_sha,))
    db.execute("CREATE TABLE IF NOT EXISTS vectors (chunk_id TEXT PRIMARY KEY, text_sha256 TEXT NOT NULL, vector BLOB NOT NULL, dimensions INTEGER NOT NULL)")
    completed = {str(row[0]): str(row[1]) for row in db.execute("SELECT chunk_id,text_sha256 FROM vectors")}
    model, meta = _new_encoder(repo, work)
    _check_runtime(repo, meta, work)
    passage_stats = _embedder_passage_stats(rows, model, meta, repo)
    pending = [row for row in rows if completed.get(str(row["chunk_id"])) != hashlib.sha256(str(row["text"]).encode()).hexdigest()]
    previous_path = work / (repo.replace("/", "--") + "-encode.json")
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    if previous and previous.get("run_manifest_sha256") != _measurement_binding(work)["run_manifest_sha256"]:
        raise ValueError("Encode cost manifest mismatch")
    started = time.perf_counter()
    warmup_seconds = 0.0
    steady_chunks = 0
    steady_seconds = 0.0
    for offset in range(0, len(pending), batch_size):
        batch = pending[offset : offset + batch_size]
        before = time.perf_counter()
        vectors = _encode_batch(model, meta, [str(row["text"]) for row in batch], repo, batch_size)
        elapsed = time.perf_counter() - before
        if offset == 0:
            warmup_seconds = elapsed
        else:
            steady_chunks += len(batch)
            steady_seconds += elapsed
        for row, vector in zip(batch, vectors, strict=True):
            import numpy as np

            array = np.asarray(vector, dtype="float32")
            db.execute("INSERT OR REPLACE INTO vectors VALUES (?,?,?,?)", (row["chunk_id"], hashlib.sha256(str(row["text"]).encode()).hexdigest(), array.tobytes(), int(array.size)))
        db.commit()
        progress_cost = {**_measurement_binding(work), "wall_seconds": previous.get("wall_seconds", 0) + time.perf_counter() - started,
                         "steady_state_chunks": previous.get("steady_state_chunks", 0) + steady_chunks,
                         "steady_state_seconds": previous.get("steady_state_seconds", 0) + steady_seconds,
                         "peak_rss_bytes": max(_peak_rss_bytes(), previous.get("peak_rss_bytes", 0))}
        _write_json(previous_path, progress_cost)
    wall_seconds = previous.get("wall_seconds", 0) + time.perf_counter() - started
    steady_chunks += previous.get("steady_state_chunks", 0)
    steady_seconds += previous.get("steady_state_seconds", 0)
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak_rss *= 1024
    index_size = sum(p.stat().st_size for p in destination.parent.glob(destination.name + "*"))
    report = {
        "model": repo, "rows_requested": len(rows), "rows_encoded_this_run": len(pending),
        "rows_resumed": len(rows) - len(pending), "batch_size": batch_size,
        "warmup_batch_seconds": warmup_seconds,
        "steady_state_chunks_per_second": steady_chunks / steady_seconds if steady_seconds else None,
        "steady_state_chunks": steady_chunks, "steady_state_seconds": steady_seconds,
        "wall_seconds": wall_seconds, "peak_rss_bytes": max(peak_rss, previous.get("peak_rss_bytes", 0)), "index_size_bytes": index_size,
        "prefixes": meta.get("prefixes", {"query": EMBEDDERS[repo]["query_prefix"], "passage": EMBEDDERS[repo]["passage_prefix"]}),
        "truncation": f"head-only at model max sequence length ({meta['max_tokens']} tokens)",
        "index": str(destination), "passage_stats": passage_stats,
        **_measurement_binding(work),
    }
    db.close()
    (work / (repo.replace("/", "--") + "-encode.json")).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _query_vector(model: Any, meta: dict[str, Any], query: str, repo: str) -> Any:
    spec = EMBEDDERS[repo]
    prefix = meta.get("prefixes", {}).get("query", spec["query_prefix"])
    prompt_name = meta.get("prompt_names", {}).get("query")
    text = query if prompt_name or spec["kind"] == "jina" else prefix + query
    if meta["kind"] == "flag":
        return model.encode([text], batch_size=1, max_length=meta["max_tokens"], return_dense=True, return_sparse=False, return_colbert_vecs=False)["dense_vecs"][0]
    options = {"task": "retrieval", "prompt_name": "query"} if spec["kind"] == "jina" else {"prompt_name": prompt_name} if prompt_name else {"prompt": ""}
    return model.encode([text], batch_size=1, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False, **options)[0]


def _load_vectors(vectors_path: Path) -> tuple[Any, Any]:
    import numpy as np

    with _ro_connect(vectors_path) as conn:
        rows = conn.execute("SELECT chunk_id,vector,dimensions FROM vectors ORDER BY chunk_id").fetchall()
    ids = np.asarray([str(row[0]) for row in rows])
    if not rows:
        return ids, np.empty((0, 0), dtype="float32")
    matrix = np.stack([np.frombuffer(row[1], dtype="float32", count=int(row[2])) for row in rows])
    matrix /= np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)
    return ids, matrix


def _dense_rank(query_vector: Any, vectors: Any, limit: int = TOP_FIRST_STAGE) -> list[str]:
    import numpy as np

    ids, matrix = _load_vectors(vectors) if isinstance(vectors, Path) else vectors
    if not len(ids):
        return []
    q = np.asarray(query_vector, dtype="float32")
    q = q / max(float(np.linalg.norm(q)), 1e-12)
    scores = matrix @ q
    return ids[np.lexsort((ids, -scores))[:limit]].tolist()


def _model_token_limit(tokenizer: Any, config: Any) -> int:
    limits = [int(value) for value in (tokenizer.model_max_length, getattr(config, "max_position_embeddings", None)) if value is not None and 0 < int(value) < 10**9]
    if not limits:
        raise ValueError("Model has no finite token limit")
    return min(limits)


def _native_jina_limits(model: Any) -> dict[str, int]:
    # Read the loaded repository implementation's limits rather than inventing
    # a cap that differs from its native rerank preprocessing.
    import textwrap

    names = {"max_query_length", "max_doc_length"}
    limits = {name: getattr(model, name) for name in names if type(getattr(model, name, None)) is int and getattr(model, name) > 0}
    for name, parameter in inspect.signature(model.rerank).parameters.items():
        if name in names and type(parameter.default) is int and parameter.default > 0:
            limits[name] = parameter.default
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(model.rerank)))
    except (OSError, TypeError, SyntaxError) as exc:
        if set(limits) != names:
            raise ValueError("Jina native truncation limits unavailable; verify the pinned repository source locally (no download)") from exc
        return limits
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = node.value
            if isinstance(value, ast.Constant):
                value = value.value
            elif isinstance(value, ast.Attribute):
                attributes = []
                while isinstance(value, ast.Attribute):
                    attributes.append(value.attr)
                    value = value.value
                if isinstance(value, ast.Name) and value.id == "self":
                    value = model
                    for attribute in reversed(attributes):
                        value = getattr(value, attribute, None)
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names and type(value) is int and value > 0:
                    limits[target.id] = value
    if set(limits) != names:
        raise ValueError("Jina native truncation limits unavailable; verify the pinned repository source locally (no download)")
    return limits


def _new_reranker(repo: str, work: Path) -> tuple[Any, dict[str, Any]]:
    _model_cache(work)
    options = _model_options(repo, work)
    if RERANKERS[repo] == "jina":
        from transformers import AutoModel

        model = AutoModel.from_pretrained(repo, cache_dir=str(work / "model-cache"), trust_remote_code=True, **options).to("cpu").float().eval()
        model._ensure_tokenizer()
        model._tokenizer.truncation_side = "right"
        return model, {"kind": "jina", "max_tokens": _model_token_limit(model._tokenizer, model.config),
                       "truncation": "passage-only 512 tokens: first 128 + last 384; native query limits", **_native_jina_limits(model)}
    if RERANKERS[repo] == "qwen":
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(repo, cache_dir=str(work / "model-cache"), padding_side="left", truncation_side="right", **options)
        model = AutoModelForCausalLM.from_pretrained(repo, cache_dir=str(work / "model-cache"), **options).to("cpu").float().eval()
        return (model, tokenizer), {"kind": "qwen", "max_tokens": _model_token_limit(tokenizer, model.config), "truncation": "passage-only 512 tokens: first 128 + last 384; preserve scoring template"}
    from sentence_transformers import CrossEncoder

    model = CrossEncoder(repo, device="cpu", cache_folder=str(work / "model-cache"), **options)
    model.model.float()
    limit = _model_token_limit(model.tokenizer, model.model.config)
    model.max_seq_length = limit
    model.tokenizer.truncation_side = "right"
    return model, {"kind": "cross_encoder", "max_tokens": limit, "truncation": "passage-only 512 tokens: first 128 + last 384"}


def _qwen_scores(adapter: tuple[Any, Any], meta: dict[str, Any], query: str, documents: list[str]) -> list[float]:
    import torch

    model, tokenizer = adapter
    prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
    suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    prefix_ids = tokenizer.encode(prefix, add_special_tokens=False)
    suffix_ids = tokenizer.encode(suffix, add_special_tokens=False)
    budget = meta["max_tokens"] - len(prefix_ids) - len(suffix_ids)
    if budget < 1:
        raise ValueError("Qwen context too small for its scoring template")
    scores = []
    with torch.no_grad():
        for document in documents:
            text = f"<Instruct>: Given a web search query, retrieve relevant passages that answer the query\n<Query>: {query}\n<Document>: {document}"
            ids = tokenizer.encode(text, add_special_tokens=False)
            if len(ids) > budget:
                raise ValueError("Query/template leave insufficient context for the frozen passage preview")
            inputs = tokenizer.pad({"input_ids": [prefix_ids + ids + suffix_ids]}, padding=True, return_tensors="pt")
            logits = model(**inputs).logits[:, -1, :]
            selected = logits[:, [tokenizer.convert_tokens_to_ids("no"), tokenizer.convert_tokens_to_ids("yes")]]
            scores.append(float(torch.softmax(selected, dim=1)[0, 1]))
    return scores


def _rerank(model: Any, meta: dict[str, Any], query: str, candidates: list[dict[str, Any]]) -> list[str]:
    if not candidates:
        return []
    tokenizer = _reranker_tokenizer(model, meta)
    previews, _ = _passage_stats(candidates, tokenizer, 512, tail=True)
    pairs = [[query, str(item["text"])] for item in previews]
    if meta["kind"] != "qwen":
        overhead = tokenizer.num_special_tokens_to_add(pair=True) if hasattr(tokenizer, "num_special_tokens_to_add") else 4
        if any(len(tokenizer.encode(query, add_special_tokens=False)) + len(tokenizer.encode(pair[1], add_special_tokens=False)) + overhead > meta["max_tokens"] for pair in pairs):
            raise ValueError("Query/template leave insufficient context for the frozen passage preview")
    if meta["kind"] == "jina":
        result = model.rerank(query, [pair[1] for pair in pairs])
        return [str(candidates[int(row["index"])]["chunk_id"]) for row in result]
    if meta["kind"] == "qwen":
        scores = _qwen_scores(model, meta, query, [pair[1] for pair in pairs])
    else:
        import numpy as np

        scores = np.asarray(model.predict(pairs, batch_size=16, show_progress_bar=False)).reshape(-1).tolist()
    return [str(candidates[i]["chunk_id"]) for i in sorted(range(len(candidates)), key=lambda i: (-float(scores[i]), str(candidates[i]["chunk_id"]))) ]


def _load_queries() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    g3_raw = G3_PATH.read_bytes()
    actual = hashlib.sha256(g3_raw).hexdigest()
    if actual != G3_SHA256:
        raise ValueError(f"G3 query file SHA mismatch: expected {G3_SHA256}; got {actual}")
    g3 = yaml.safe_load(g3_raw)
    g1_g2 = yaml.safe_load(QUERY_PATH.read_text(encoding="utf-8"))
    queries: list[dict[str, Any]] = []
    for row in g1_g2.get("g1", []):
        if row.get("stratum") != "english":
            queries.append({**row, "family": "G1", "stratum": str(row.get("stratum", "G1")), "cluster": "G1:" + str(row["query"])})
    for row in g1_g2.get("g2", []):
        for form_index, form in enumerate(row.get("forms", [])):
            queries.append({"id": f"{row['id']}:{form}", "query": form, "family": "G2", "stratum": "G2-inflected" if form_index else "G2-base", "cluster": "G2:" + json.dumps(row["forms"], ensure_ascii=False, separators=(",", ":")), "pair_index": form_index, "area": row.get("category", "")})
    for row in g3:
        queries.append({**row, "family": "G3", "stratum": f"G3-{row.get('area','unknown')}-{row.get('kind','unknown')}", "cluster": row["id"]})
    return queries, g3


def _run_arm(corpus_path: Path, work: Path, queries: list[dict[str, Any]], arm: str, embedder: str | None, reranker: str | None, vesum_path: Path | None = None, *, timing_only: bool = False) -> dict[str, Any]:
    """One fresh process owns one complete pipeline, including its RSS peak."""
    pipeline_started = time.perf_counter()
    chunks = _load_rows(corpus_path)
    evaluation = _evaluation(work)
    by_id = {str(row["chunk_id"]): row for row in chunks}
    encoder, encoder_meta = _new_encoder(embedder, work) if embedder else (None, {})
    ranker, ranker_meta = _new_reranker(reranker.removesuffix("@int8"), work) if reranker else (None, {})
    if embedder:
        _check_runtime(embedder, encoder_meta, work)
    if reranker:
        base_ranker = reranker.removesuffix("@int8")
        _check_runtime(base_ranker, ranker_meta, work)
        if reranker.endswith("@int8"):
            ranker = _quantize_reranker(ranker, ranker_meta)
    vector_path = work / "embeddings" / (embedder.replace("/", "--") + ".sqlite3") if embedder else None
    vectors = _load_vectors(vector_path) if vector_path else None
    checkpoint_path = work / "search-progress" / (hashlib.sha256(arm.encode()).hexdigest() + ("-timing" if timing_only else "") + ".json")
    binding = _measurement_binding(work)
    progress = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {"binding": binding, "rankings": {}, "query_seconds": {}}
    if progress["binding"] != binding:
        raise ValueError("Search checkpoint mismatch")
    previous_pipeline_seconds = progress.get("pipeline_running_seconds", 0)
    hybrid_rankings = {}
    if reranker:
        hybrid_path = work / "search-progress" / (hashlib.sha256(f"H:{embedder}".encode()).hexdigest() + ".json")
        hybrid = json.loads(hybrid_path.read_text())
        if hybrid["binding"] != binding:
            raise ValueError("Hybrid checkpoint mismatch")
        hybrid_rankings = hybrid["rankings"]
    rankings = progress["rankings"]
    times = []
    passage_stats = {}
    with _ro_connect(corpus_path) as lexical, get_vesum_connection(vesum_path or _default_vesum_db()) as vesum:
        def retrieve(query: str, qid: str) -> list[str]:
            hits = []
            if not arm.startswith("D:"):
                hits = _fts_search(lexical, query, vesum, lemma=True, limit=TOP_FIRST_STAGE)
            if embedder:
                dense = _dense_rank(_query_vector(encoder, encoder_meta, query, embedder), vectors)
                hits = dense if arm.startswith("D:") else reciprocal_rank_fusion([hits, dense])
            if reranker:
                # Recompute first stages for end-to-end timing, but permutation
                # inputs come from the completed hybrid's exact checkpoint.
                hits = hybrid_rankings[qid]
                candidates = [by_id[cid] for cid in hits[:TOP_RERANK] if cid in by_id]
                original = hits[:TOP_RERANK]
                reordered = _rerank(ranker, ranker_meta, query, candidates)
                _assert_permutation(original, reordered)
                hits = reordered + hits[TOP_RERANK:]
            return hits

        measured = evaluation["cost_query_ids"]
        if measured:
            retrieve(str(next(q["query"] for q in queries if q["id"] == measured[0])), measured[0])
        for query in queries:
            if timing_only and query["id"] not in measured:
                continue
            if query["id"] not in rankings:
                started = time.perf_counter()
                rankings[query["id"]] = retrieve(str(query["query"]), query["id"])
                progress["query_seconds"][query["id"]] = time.perf_counter() - started
                progress["pipeline_running_seconds"] = previous_pipeline_seconds + time.perf_counter() - pipeline_started
                _write_json(checkpoint_path, progress)
            if query["id"] in measured:
                times.append(progress["query_seconds"][query["id"]])
    encode_path = work / (embedder.replace("/", "--") + "-encode.json") if embedder else None
    encode_cost = json.loads(encode_path.read_text()) if encode_path and encode_path.exists() else {}
    cost = {key: encode_cost[key] for key in ("wall_seconds", "steady_state_chunks_per_second", "peak_rss_bytes") if key in encode_cost}
    if encoder:
        passage_stats[embedder] = encode_cost.get("passage_stats", {})
    if ranker:
        rerank_rows = {cid: by_id[cid] for ranking in rankings.values() for cid in ranking[:TOP_RERANK]}
        _, passage_stats[reranker] = _passage_stats(list(rerank_rows.values()), _reranker_tokenizer(ranker, ranker_meta), 512, tail=True)
    cost.update({"passage_stats": passage_stats, "query_p50_seconds": statistics.median(times) if times else None,
                 "query_p95_seconds": _percentile(times, .95) if times else None,
                 "query_n": len(times), "query_peak_rss_bytes": _peak_rss_bytes(),
                 "index_size_bytes": (corpus_path.stat().st_size if not arm.startswith("D:") else 0) + (vector_path.stat().st_size if vector_path else 0),
                 "measurement": "fresh spawned process per arm; one full-pipeline warmup, then frozen 50-query cost batch; end-to-end lexical/dense/fusion/rerank as applicable; process-lifetime RSS including model setup",
                 "encoder": encoder_meta, "reranker": ranker_meta})
    cost["pipeline_seconds"] = previous_pipeline_seconds + time.perf_counter() - pipeline_started
    cost["pipeline_queries"] = len(rankings) + bool(measured)
    return {"rankings": rankings, "cost": cost}


def _isolated_arm(*args: Any) -> dict[str, Any]:
    _corpus_path, work, queries, arm, _embedder, _reranker, *_ = args
    _admission(work)
    # Initial timing probe has a bounded 30-minute projection. Its checkpoint
    # measures the entire pipeline, including setup, reporting and warmup.
    timing = _guarded_step(_run_arm, args, {"timing_only": True}, work, f"search-timing:{arm}", 30 * 60)
    cost = timing["cost"]
    # Scale the complete elapsed measurement conservatively: this also scales
    # setup rather than omitting any fixed costs from the real search step.
    projection = _positive(timing.get("host_running_seconds", cost["pipeline_seconds"]), "Full-pipeline timing") * (len(queries) + 1) / cost["pipeline_queries"]
    return _guarded_step(_run_arm, args, {}, work, f"search:{arm}", projection)


def search(db_path: Path, work: Path, *, models: list[str], rerankers: list[str], query_limit: int, families: list[str]) -> dict[str, Any]:
    run = _validate_run(db_path, work)
    evaluation = _evaluation(work)
    admission = _admission(work)
    queries = evaluation["queries"]
    if query_limit < len(queries) or set(families) != {"G1", "G2", "G3"}:
        raise ValueError("Search must run all and only the 120 frozen evaluation queries")
    if len(set(models)) != len(models) or len(set(rerankers)) != len(rerankers):
        raise ValueError("Duplicate models/rerankers requested")
    if not set(models) <= set(admission["admitted_embedders"]):
        raise ValueError("Search requested an excluded embedder")
    for ranker in rerankers:
        if not admission["rerankers"].get(ranker, {}).get("variant"):
            raise ValueError("Search requested an excluded or unmeasured reranker")
    corpus_path = _copy_subset(db_path, work)
    arm_specs = [("L", None, None)]
    coverage = {}
    for repo in models:
        if repo not in EMBEDDERS:
            raise ValueError(f"Unsupported embedding repository: {repo}")
        vector_path = work / "embeddings" / (repo.replace("/", "--") + ".sqlite3")
        if not vector_path.is_file():
            raise FileNotFoundError(f"Missing index for {repo}; run encode --model {repo} first")
        with _ro_connect(vector_path) as cached:
            index_binding = dict(cached.execute("SELECT key,value FROM index_metadata"))
        if index_binding.get("run_manifest_sha256") != run["sha256"]:
            raise ValueError("Vector index run manifest mismatch")
        coverage[repo] = {"indexed_vectors": _vector_count(vector_path), "corpus_rows": len(_load_rows(corpus_path))}
        if coverage[repo]["indexed_vectors"] != coverage[repo]["corpus_rows"]:
            raise ValueError("Search requires a fully encoded subset")
        arm_specs.extend([(f"D:{repo}", repo, None), (f"H:{repo}", repo, None)])
        for ranker in rerankers:
            if ranker not in RERANKERS:
                raise ValueError(f"Unsupported reranker repository: {ranker}")
            variant = admission["rerankers"][ranker]["variant"]
            name = ranker + ("@int8" if variant == "int8" else "")
            arm_specs.append((f"R:{name}|{repo}", repo, name))
    arms, costs = {}, {}
    for arm, embedder, reranker in arm_specs:
        measured = _isolated_arm(corpus_path, work, queries, arm, embedder, reranker)
        arms[arm], costs[arm] = measured["rankings"], measured["cost"]
    for arm, rankings in arms.items():
        if arm.startswith("R:"):
            hybrid = "H:" + arm.split("|", 1)[1]
            for qid, ranking in rankings.items():
                _assert_permutation(arms[hybrid][qid][:TOP_RERANK], ranking[:TOP_RERANK])
    result = {"schema": "retrieval-bakeoff-9233-search.v6.1", "evaluation_manifest_sha256": evaluation["sha256"], "run_manifest_sha256": run["sha256"], "g3_query_sha256": G3_SHA256, "queries": queries, "arms": arms, "costs": costs, "vector_coverage": coverage, "seed": SEED, "rrf_k": RRF_K, "top_first_stage": TOP_FIRST_STAGE, "top_rerank": TOP_RERANK}
    (work / "search-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value * (1024 if sys.platform != "darwin" else 1))


def _vector_count(path: Path) -> int:
    with _ro_connect(path) as conn:
        return int(conn.execute("SELECT count(*) FROM vectors").fetchone()[0])


def _percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(probability * len(ordered)) - 1)]


def _pool_queries(queries: list[dict[str, Any]], query_limit: int | None = None) -> list[dict[str, Any]]:
    # Deduplicate before budgeting, retaining G1 and then the registered G2 pair.
    required = [q for q in queries if q["family"] == "G1"]
    required.extend(q for q in queries if q["family"] == "G2" and q.get("pair_index") in {0, 1})
    seen: set[str] = set()
    unique = []
    for query in required:
        if query["query"] not in seen:
            unique.append(query)
            seen.add(query["query"])
    g3 = []
    for query in queries:
        if query["family"] == "G3" and query["query"] not in seen:
            g3.append(query)
            seen.add(query["query"])
    cap = 120 if query_limit is None else query_limit
    if cap < 1:
        raise ValueError("--query-limit must be positive")
    remaining = max(0, cap - len(unique))
    sampled = random.Random(SEED).sample(g3, min(remaining, len(g3)))
    return unique[:cap] + sorted(sampled, key=lambda row: row["id"])


def pool(work: Path, *, query_limit: int | None = None, overwrite: bool = False) -> dict[str, Any]:
    judge_dir = work / "judging"
    if not overwrite and (any((judge_dir / name).exists() for name in ("pool.json", "judge-a.jsonl", "judge-b.jsonl")) or (work / "sealed/pool-key.json").exists()):
        raise ValueError("Refusing to overwrite existing judging pool; pass --overwrite-pool explicitly")
    result = json.loads((work / "search-results.json").read_text(encoding="utf-8"))
    if "evaluation_manifest_sha256" in result:
        evaluation = _evaluation(work)
        if result["evaluation_manifest_sha256"] != evaluation["sha256"] or result["queries"] != evaluation["queries"] or query_limit not in (None, 120):
            raise ValueError("Pool must match the frozen evaluation manifest")
        admission = _admission(work)
        if set(admission["rerankers"]) != set(RERANKERS):
            raise ValueError("Final judging requires timing/admission decisions for all three rerankers")
        expected_arms = {"L"}
        for repo in admission["admitted_embedders"]:
            expected_arms.update({f"D:{repo}", f"H:{repo}"})
            for ranker, decision in admission["rerankers"].items():
                if decision["variant"]:
                    name = ranker + ("@int8" if decision["variant"] == "int8" else "")
                    expected_arms.add(f"R:{name}|{repo}")
        if set(result["arms"]) != expected_arms:
            raise ValueError("One judging pass requires all admitted configurations")
        queries = evaluation["queries"]
    else:
        queries = _pool_queries(result["queries"], query_limit)
    for arm, rankings in result["arms"].items():
        if arm.startswith("R:"):
            hybrid = "H:" + arm.split("|", 1)[1]
            for q in queries:
                _assert_permutation(result["arms"][hybrid][q["id"]][:20], rankings[q["id"]][:20])
    corpus_path = work / "corpus.sqlite3"
    chunks = {str(row["chunk_id"]): row for row in _load_rows(corpus_path)}
    # G1 known citations are always included even when only G3 is measured.
    query_set, _ = _load_queries()
    citations: dict[str, list[str]] = defaultdict(list)
    for q in query_set:
        if q["family"] == "G1":
            citations[str(q["query"])].append(str(q.get("gold_chunk_id", "")))
    generator = random.Random(SEED)
    judging: list[dict[str, Any]] = []
    key: list[dict[str, str]] = []
    for query in queries:
        qid = str(query["id"])
        candidates: set[str] = set(citations.get(str(query["query"]), []))
        for _arm, rankings in result["arms"].items():
            candidates.update(str(cid) for cid in rankings.get(qid, [])[:POOL_DEPTH])
        candidates.discard("")
        item_ids = [hashlib.sha256(f"{qid}\0{cid}".encode()).hexdigest()[:20] for cid in sorted(candidates)]
        shuffled = list(zip(item_ids, sorted(candidates), strict=True))
        generator.shuffle(shuffled)
        records: list[dict[str, Any]] = []
        for item_id, chunk_id in shuffled:
            row = chunks.get(chunk_id)
            if row is None:
                raise ValueError(f"Pool candidate missing from the frozen corpus: {chunk_id}")
            records.append({"item_id": item_id, "text": str(row["text"])})
            key.append({"item_id": item_id, "query_id": qid, "arm": "", "chunk_id": chunk_id, "source_identity": str(row["source_file"])})
            for arm, rankings in result["arms"].items():
                if chunk_id in rankings.get(qid, [])[:POOL_DEPTH]:
                    key.append({"item_id": item_id, "query_id": qid, "arm": arm, "chunk_id": chunk_id})
        judging.append({"query_id": qid, "query": str(query["query"]), "items": records})
    judge_dir.mkdir(parents=True, exist_ok=True)
    for judge in ("judge-a", "judge-b"):
        (judge_dir / f"{judge}.jsonl").write_text("", encoding="utf-8")
    (judge_dir / "pool.json").write_text(json.dumps(judging, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    key_path = work / "sealed" / "pool-key.json"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"family_counts": dict(Counter(q["family"] for q in queries)), "queries": len(judging), "items": sum(len(q["items"]) for q in judging), "pool": str(judge_dir / "pool.json"), "key": str(key_path), "seed": SEED}


def stricter_label(first: bool, second: bool) -> bool:
    return first and second


def lenient_label(first: bool, second: bool) -> bool:
    return first or second


def cohen_kappa(pairs: list[tuple[bool, bool]]) -> float:
    if not pairs:
        return 0.0
    observed = sum(left == right for left, right in pairs) / len(pairs)
    left_yes = sum(left for left, _ in pairs) / len(pairs)
    right_yes = sum(right for _, right in pairs) / len(pairs)
    expected = left_yes * right_yes + (1 - left_yes) * (1 - right_yes)
    return 1.0 if expected == 1 and observed == 1 else (observed - expected) / (1 - expected) if expected < 1 else 0.0


def paired_cluster_bootstrap(query_values: dict[str, tuple[float, float]], clusters: dict[str, str], *, iterations: int = 10000, seed: int = SEED) -> dict[str, float]:
    if iterations < 1:
        raise ValueError("Bootstrap iterations must be positive")
    grouped: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for query_id, pair in query_values.items():
        grouped[clusters[query_id]].append(pair)
    keys = sorted(grouped)
    if not keys:
        return {"estimate": 0.0, "lower_95": 0.0, "upper_95": 0.0}
    differences = {key: statistics.mean(a - b for a, b in pairs) for key, pairs in grouped.items()}
    estimate = statistics.mean(differences.values())
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(iterations):
        chosen = [keys[rng.randrange(len(keys))] for _ in keys]
        samples.append(statistics.mean(differences[cluster] for cluster in chosen))
    return {"estimate": estimate, "lower_95": _percentile(samples, .025), "upper_95": _percentile(samples, .975)}


def _read_labels(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    labels: dict[tuple[str, str], dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        required = {"usable_quotation", "usable_exercise", "usable_example", "reason"}
        if not required.issubset(row):
            raise ValueError(f"Missing required labels in {path}: {row.get('item_id')}")
        if any(type(row[label]) is not bool for label in ("usable_quotation", "usable_exercise", "usable_example")) or "\n" in str(row["reason"]):
            raise ValueError(f"Invalid label types or multiline reason in {path}: {row.get('item_id')}")
        identity = (str(row["query_id"]), str(row["item_id"]))
        if identity in labels:
            raise ValueError(f"Duplicate judging label id in {path}: {identity}")
        labels[identity] = row
    return labels


def _cluster_mean(values: dict[str, float], clusters: dict[str, str]) -> float:
    grouped: dict[str, list[float]] = defaultdict(list)
    for qid, value in values.items():
        grouped[clusters[qid]].append(value)
    return statistics.mean(statistics.mean(group) for group in grouped.values()) if grouped else 0.0


def _ranking_metrics(ranking: list[str], relevant: set[str]) -> tuple[float, float]:
    if len(set(ranking)) != len(ranking):
        raise ValueError("Duplicate chunk in arm ranking")
    dcg = sum(1 / math.log2(rank + 1) for rank, cid in enumerate(ranking[:10], 1) if cid in relevant)
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(10, len(relevant)) + 1))
    reciprocal = next((1 / rank for rank, cid in enumerate(ranking[:10], 1) if cid in relevant), 0.0)
    return dcg / ideal if ideal else 0.0, reciprocal


def decide(metrics: dict[str, dict[str, dict[str, float]]], queries: list[dict[str, Any]], costs: dict[str, Any], *, usable_queries: int, kappa_gate: bool, iterations: int) -> dict[str, Any]:
    clusters = {q["id"]: q["cluster"] for q in queries}
    coverage_arms = sorted(a for a in metrics if a == "L" or a.startswith(("D:", "H:")))
    ranking_arms = []
    comparisons: dict[str, Any] = {}
    ranking_comparisons: dict[str, Any] = {}
    recommendation = None
    outcome = "INCONCLUSIVE"

    def compare(arms: list[str], metric: str) -> dict[str, Any]:
        best = max(arms, key=lambda arm: _cluster_mean({q: v[metric] for q, v in metrics[arm].items()}, clusters))
        entries = {}
        for arm in arms:
            values = {q["id"]: (metrics[best][q["id"]][metric], metrics[arm][q["id"]][metric]) for q in queries}
            entries[arm] = {**paired_cluster_bootstrap(values, clusters, iterations=iterations), "reference_arm": best}
            entries[arm]["eligible_noninferior"] = entries[arm]["upper_95"] <= 0.05
        return entries

    if coverage_arms:
        comparisons = compare(coverage_arms, "recall_at_20_strict")
        hybrids = [a for a in coverage_arms if a.startswith("H:") and comparisons[a]["eligible_noninferior"]]
        if usable_queries >= 60 and kappa_gate:
            if not hybrids:
                outcome = "NO_ELIGIBLE_HYBRID"
            else:
                ranking_arms.extend(hybrids)
                # A reranker has to be non-inferior to its own eligible hybrid,
                # before it participates in the global ranking comparison.
                reranker_vs_hybrid = {}
                for arm in sorted(a for a in metrics if a.startswith("R:")):
                    hybrid = "H:" + arm.split("|", 1)[1]
                    if hybrid not in hybrids:
                        continue
                    values = {q["id"]: (metrics[hybrid][q["id"]]["ndcg_at_10_strict"], metrics[arm][q["id"]]["ndcg_at_10_strict"]) for q in queries}
                    bound = paired_cluster_bootstrap(values, clusters, iterations=iterations)
                    reranker_vs_hybrid[arm] = {**bound, "reference_arm": hybrid, "eligible_noninferior": bound["upper_95"] <= 0.05}
                    if bound["upper_95"] <= 0.05:
                        ranking_arms.append(arm)
                ranking_comparisons = compare(ranking_arms, "ndcg_at_10_strict")
                eligible = [a for a in ranking_arms if ranking_comparisons[a]["eligible_noninferior"]]
                def cost_order(arm: str) -> tuple[float, float, float, str]:
                    entry = costs.get(arm, {})
                    values = [entry.get(k) for k in ("query_p95_seconds", "index_size_bytes", "wall_seconds")]
                    return (*(float(v) if isinstance(v, (int, float)) and math.isfinite(v) and v >= 0 else float("inf") for v in values), arm)
                if eligible and all(all(math.isfinite(v) for v in cost_order(a)[:3]) for a in eligible):
                    recommendation = min(eligible, key=cost_order)
                    outcome = "RECOMMENDED" if recommendation.startswith("R:") else "NO_RERANKER"
                else:
                    outcome = "INCONCLUSIVE"
                return {"outcome": outcome, "recommended_configuration": recommendation, "coverage_comparisons": comparisons, "ranking_comparisons": ranking_comparisons, "reranker_vs_hybrid": reranker_vs_hybrid}
    return {"outcome": outcome, "recommended_configuration": recommendation, "coverage_comparisons": comparisons, "ranking_comparisons": ranking_comparisons, "reranker_vs_hybrid": {}}


def score(work: Path, labels_a: Path, labels_b: Path, *, iterations: int = 10000) -> dict[str, Any]:
    search_result = json.loads((work / "search-results.json").read_text(encoding="utf-8"))
    if "evaluation_manifest_sha256" in search_result:
        evaluation = _evaluation(work)
        run = _read_frozen(work / "run-manifest.json")
        if set(_admission(work)["rerankers"]) != set(RERANKERS):
            raise ValueError("Final scoring requires timing/admission decisions for all three rerankers")
        if search_result["evaluation_manifest_sha256"] != evaluation["sha256"] or search_result["run_manifest_sha256"] != run["sha256"] or search_result["queries"] != evaluation["queries"]:
            raise ValueError("Score manifest mismatch")
    key = json.loads((work / "sealed/pool-key.json").read_text(encoding="utf-8"))
    pool_rows = json.loads((work / "judging/pool.json").read_text(encoding="utf-8"))
    if "evaluation_manifest_sha256" in search_result and [q["query_id"] for q in pool_rows] != [q["id"] for q in search_result["queries"]]:
        raise ValueError("Score pool denominator mismatch")
    a, b = _read_labels(labels_a), _read_labels(labels_b)
    merged: dict[tuple[str, str], dict[str, bool]] = {}
    disagreements: dict[str, int] = defaultdict(int)
    kappa_pairs: dict[str, list[tuple[bool, bool]]] = defaultdict(list)
    expected = {(str(q["query_id"]), str(item["item_id"])) for q in pool_rows for item in q["items"]}
    if set(a) != expected or set(b) != expected:
        raise ValueError("Judging label ids do not exactly cover the blind pool")
    for identity in sorted(expected):
        if identity not in a or identity not in b:
            raise ValueError(f"Both judges must label every pooled item; missing {identity}")
        merged[identity] = {}
        for label in ("usable_quotation", "usable_exercise", "usable_example"):
            left, right = bool(a[identity][label]), bool(b[identity][label])
            disagreements[label] += left != right
            kappa_pairs[label].append((left, right))
            merged[identity][label] = stricter_label(left, right)
            merged[identity][label + "_lenient"] = lenient_label(left, right)
    if len(merged) != sum(len(query["items"]) for query in pool_rows):
        raise ValueError("Judging labels do not exactly cover the blind pool")
    query_by_id = {str(q["id"]): q for q in search_result["queries"]}
    query_ids = [str(query["query_id"]) for query in pool_rows]
    clusters = {qid: str(query_by_id[qid]["cluster"]) for qid in query_ids}
    relevant = {qid: (set(), set()) for qid in query_ids}
    item_chunks = {(row["query_id"], row["item_id"]): row["chunk_id"] for row in key}
    for (qid, item_id), label in merged.items():
        cid = item_chunks[(qid, item_id)]
        if label["usable_quotation"] or label["usable_exercise"]:
            relevant[qid][0].add(cid)
        if label["usable_quotation_lenient"] or label["usable_exercise_lenient"]:
            relevant[qid][1].add(cid)
    metrics = {}
    summaries = {}
    selected_queries = [query_by_id[qid] for qid in query_ids]
    for arm, rankings in search_result["arms"].items():
        if arm.startswith("R:"):
            hybrid = "H:" + arm.split("|", 1)[1]
            for qid in query_ids:
                _assert_permutation(search_result["arms"][hybrid][qid][:20], rankings[qid][:20])
        metrics[arm] = {}
        for qid in query_ids:
            ranking = rankings.get(qid, [])
            strict, lenient = relevant[qid]
            ndcg, mrr = _ranking_metrics(ranking, strict)
            lndcg, lmrr = _ranking_metrics(ranking, lenient)
            metrics[arm][qid] = {
                "recall_at_20_strict": len(set(ranking[:20]) & strict) / len(strict) if strict else 0.0,
                "recall_at_20_lenient": len(set(ranking[:20]) & lenient) / len(lenient) if lenient else 0.0,
                "ndcg_at_10_strict": ndcg, "ndcg_at_10_lenient": lndcg,
                "mrr_at_10_strict": mrr, "mrr_at_10_lenient": lmrr,
            }
        by_stratum: dict[str, list[str]] = defaultdict(list)
        for query in selected_queries:
            names = {str(query["stratum"]), str(query["family"]), "pooled"}
            if query["family"] == "G3":
                names.update({"G3-area:" + str(query.get("area", "unknown")), "G3-kind:" + str(query.get("kind", "unknown"))})
            for name in names:
                by_stratum[name].append(query["id"])
        summaries[arm] = {}
        for stratum, ids in sorted(by_stratum.items()):
            summaries[arm][stratum] = {
                "n": len(ids), "usable_n": sum(bool(relevant[qid][0]) for qid in ids),
                "lenient_n": sum(bool(relevant[qid][1]) for qid in ids),
                "queries_without_relevant_pool_item": sum(not relevant[qid][0] for qid in ids),
                **{metric: _cluster_mean({qid: metrics[arm][qid][metric] for qid in ids}, clusters) for metric in next(iter(metrics[arm].values()), {})},
            }
    kappas = {label: cohen_kappa(pairs) for label, pairs in kappa_pairs.items()}
    kappa_gate = bool(kappas) and all(kappas.get(label, 0.0) >= 0.6 for label in ("usable_quotation", "usable_exercise"))
    usable_queries = sum(bool(relevant[qid][0]) for qid in query_ids)
    decision = decide(metrics, selected_queries, search_result["costs"], usable_queries=usable_queries, kappa_gate=kappa_gate, iterations=iterations)
    # A partial or altered evaluation denominator never produces a winner.
    if len(query_ids) != 120:
        decision["outcome"] = "INCONCLUSIVE"
        decision["recommended_configuration"] = None
    report = {"schema": "retrieval-bakeoff-9233-score.v6.1", "g3_query_sha256": G3_SHA256,
              "query_count": len(query_ids), "usable_queries": usable_queries, "judged_items": len(merged),
              "judge_disagreements": dict(disagreements), "cohen_kappa": kappas, "kappa_gate": kappa_gate,
              "strata": summaries, "per_query_metrics": metrics,
              "per_query_usable_counts": {qid: {"strict": len(relevant[qid][0]), "lenient": len(relevant[qid][1])} for qid in query_ids},
              "topic_coverage": {name: entry["usable_n"] for name, entry in next(iter(summaries.values()), {}).items()},
              **decision, "paired_bootstrap_best_minus_arm": decision["coverage_comparisons"],
              "recommended_by_v5_cost_order": decision["recommended_configuration"], "costs": search_result["costs"],
              "comparison_scope": "best among evaluated configurations", "passage_policies": PASSAGE_POLICIES,
              "eligibility_rule": "Recall@20 coverage, then nDCG@10 ranking: upper 95% paired equal-cluster bootstrap(best - arm) <= 0.05; kappa >= 0.6; >=60/120 usable queries", "seed": SEED}
    (work / "score-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path = work / "phase2-results.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(report), encoding="utf-8")
    return report


def _render_report(report: dict[str, Any]) -> str:
    lines = ["# #9233 Phase 2 retrieval bake-off results", "", f"Outcome: **{report['outcome']}**; {report['usable_queries']}/120 queries have a strictly usable pool item. Best among evaluated configurations.", "", f"G3 query SHA-256: `{G3_SHA256}`; judged query denominator: {report['query_count']}; pooled items: {report['judged_items']}.", "", "Recall@20 uses the stricter label rule (both judges mark quotation or exercise usable); lenient sensitivity uses either judge. All 120 queries enter the primary contrast with equal weight per bootstrap cluster; G1/G2/G3 and G3 area/kind are diagnostics. English-derived queries are excluded.", "", "## Per arm and stratum", "", "| Arm | Stratum | n | Strict Recall@20 | Lenient Recall@20 |", "|---|---|---:|---:|---:|"]
    for arm, strata in sorted(report["strata"].items()):
        for stratum, metrics in sorted(strata.items()):
            lines.append(f"| {arm} | {stratum} | {metrics['n']} | {metrics['recall_at_20_strict']:.3f} | {metrics['recall_at_20_lenient']:.3f} |")
    lines.extend(["", "## Paired cluster bootstrap and eligibility", "", "Eligibility requires the upper 95% bound of Recall@20(best) − Recall@20(arm) to be at most 0.05. G2 variants resample as a base-query cluster.", "", "| Arm | Reference | Gain estimate | 95% lower | 95% upper | Eligible |", "|---|---|---:|---:|---:|---|"])
    for arm, metric in sorted(report["paired_bootstrap_best_minus_arm"].items()):
        lines.append(f"| {arm} | {metric['reference_arm']} | {metric['estimate']:.3f} | {metric['lower_95']:.3f} | {metric['upper_95']:.3f} | {metric['eligible_noninferior']} |")
    lines.extend(["", f"Recommended by v6.1 cost ordering: **{report['recommended_by_v5_cost_order'] or 'none eligible'}** (p95 latency, then index size, then subset encode wall time).", "", "## Measured costs", "", "| Arm/model | p50 s | p95 s | query RSS bytes | index bytes | encode s | chunks/s | peak encode RSS bytes |", "|---|---:|---:|---:|---:|---:|---:|---:|"])
    for name, cost in sorted(report["costs"].items()):
        lines.append(f"| {name} | {cost.get('query_p50_seconds','')} | {cost.get('query_p95_seconds','')} | {cost.get('query_peak_rss_bytes','')} | {cost.get('index_size_bytes','')} | {cost.get('wall_seconds','')} | {cost.get('steady_state_chunks_per_second','')} | {cost.get('peak_rss_bytes','')} |")
    lines.extend(["", "## nDCG@10 ranking eligibility (MRR@10 and lenient sensitivity in JSON)", ""])
    for arm, metric in sorted(report["ranking_comparisons"].items()):
        lines.append(f"{arm}: upper 95% best minus arm = {metric['upper_95']:.3f}; eligible = {metric['eligible_noninferior']}")
    lines.extend(["", f"Passage previews: `{json.dumps(PASSAGE_POLICIES, sort_keys=True)}`. Conclusions are conditional on these preview policies; per-model/source truncation and retained-character shares are in the measured costs."])
    lines.extend(["", f"Cohen's kappa by label: `{json.dumps(report['cohen_kappa'], sort_keys=True)}`; gate pass: {report['kappa_gate']}. Judge disagreements: `{json.dumps(report['judge_disagreements'], sort_keys=True)}`.", "", "Residual: no independent held-out set beyond the frozen G1/G2/G3 queries; owner: #9233 accountable driver.", ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure lexical, dense, hybrid, and reranked Ukrainian textbook retrieval for #9233.\nUse this for the frozen bake-off; do not use it for production indexing or changes to sources MCP.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/wiki/diagnostics/retrieval_bakeoff_9233.py corpus --work-dir /tmp/bakeoff-9233
  .venv/bin/python scripts/wiki/diagnostics/retrieval_bakeoff_9233.py sample --work-dir /tmp/bakeoff-9233
  .venv/bin/python scripts/wiki/diagnostics/retrieval_bakeoff_9233.py admit --measurements /tmp/measurements.json --work-dir /tmp/bakeoff-9233
Outputs: corpus/vector indexes, caches, search results, blind judging files, and sealed key below --work-dir; score writes phase2-results.md.
Exit codes: 0 means command completed; >=1 means invalid inputs, missing data/model index, or failed operation.
Related: docs/research/retrieval-bakeoff-9233/g3-queries.yaml; design #9233 v6.1 and amendments 9–12.
""",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--work-dir", type=Path, required=True, help="External directory for all generated indexes, caches and outputs; example /tmp/bakeoff-9233.")
    common.add_argument("--sources-db", type=Path, help="Read-only textbook SQLite database; defaults to the active project sources.db.")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("corpus", parents=[common], help="Materialize and digest the frozen Ukrainian subset.")
    commands.add_parser("sample", parents=[common], help="Freeze the 500 source/length-stratified chunks, 120 queries, cost batch and timing recipe; no models.")
    p = commands.add_parser("manifest", parents=[common], help="Freeze corpus, resolved model/tokenizer revisions and policies before compute; no models.")
    p.add_argument("--model-config", type=Path, required=True, help="JSON map of all nine repositories to revision (40-hex), tokenizer {repository, revision}, max_tokens, prefixes (embedders) or scoring_template (rerankers).")
    p = commands.add_parser("measure", parents=[common], help="Time the frozen encode sample or realised reranker pairs in a guarded CPU child.")
    p.add_argument("--model", choices=sorted(set(EMBEDDERS) | set(RERANKERS)), required=True, help="Exact repository to measure; example intfloat/multilingual-e5-small.")
    p.add_argument("--variant", choices=("fp32", "int8"), default="fp32", help="Reranker precision variant; default fp32; int8 is the one dynamic fallback.")
    p.add_argument("--batch-size", type=int, default=16, help="Frozen steady-state encode batch size; default 16.")
    p.add_argument("--projection-seconds", type=float, required=True, help="Measured step projection in running seconds, used for the 1.5x deadline; example 1200. Initial probe requires an explicit bounded estimate.")
    p.add_argument("--repeat", action="store_true", help="Perform the one required borderline remeasurement; default reuse a completed measurement.")
    p = commands.add_parser("admit", parents=[common], help="Apply ascending-cost 20h encode and 8h/10s reranker admission; no model compute.")
    p.add_argument("--measurements", type=Path, required=True, help="JSON with frozen binding, all six embedder projected_seconds/query_seconds, and optional reranker fp32/int8 attempt lists (p50_seconds, p95_seconds, mean_seconds, timing_pairs_sha256). Lexical timing is read from lexical-measurement.json, written by measure or corpus after manifest.")
    commands.add_parser("timing-pairs", parents=[common], help="Freeze E5 hybrid top-20 realised query/candidate pairs from search-results.json before reranker timing.")
    p = commands.add_parser("encode", parents=[common], help="CPU encode the subset resumably with the selected embedding model.")
    p.add_argument("--model", choices=sorted(EMBEDDERS), required=True, help="Exact embedding model repository; example intfloat/multilingual-e5-small.")
    p.add_argument("--quiet-window-end", type=float, help="Unix UTC end timestamp of the authorized quiet window; required for encodes projected above 2 hours. Interrupted steps resume in a later window.")
    p.add_argument("--limit", type=int, help="Encode the first N source-ordered chunks only; omit for full subset.")
    p.add_argument("--batch-size", type=int, default=16, help="CPU inference batch size (default 16); example 16.")
    p = commands.add_parser("search", parents=[common], help="Run L, dense D_i, RRF H_i, and every configured reranker over H_i.")
    p.add_argument("--models", nargs="+", choices=sorted(EMBEDDERS), default=None, help="Indexed embedder repositories to compare; default all admitted models.")
    p.add_argument("--rerankers", nargs="*", choices=sorted(RERANKERS), default=None, help="Reranker repositories; default all admitted rerankers; pass --rerankers with no values for the first E5 timing retrieval.")
    p.add_argument("--query-limit", type=int, default=10000, help="Must include the complete frozen 120-query manifest; default 10000 (does not add queries).")
    p.add_argument("--families", nargs="+", choices=("G1", "G2", "G3"), default=["G1", "G2", "G3"], help="Query families to execute; default all Ukrainian G1, G2 and G3.")
    p = commands.add_parser("pool", parents=[common], help="Create arm-blind judging files and a separately sealed arm key.")
    p.add_argument("--query-limit", type=int, help="Cap unique pooled query strings at N; default 120: all unique G1/G2 pairs, then seeded G3 sample.")
    p.add_argument("--overwrite-pool", action="store_true", help="Explicitly replace the pool and reset judge files; default refuse any existing pool or labels.")
    p = commands.add_parser("score", parents=[common], help="Score two judge JSONL files with strict/lenient labels and paired cluster bootstrap.")
    p.add_argument("--judge-a", type=Path, required=True, help="First judge JSONL with one item label per pooled item.")
    p.add_argument("--judge-b", type=Path, required=True, help="Second judge JSONL with the same item labels.")
    p.add_argument("--bootstrap-iterations", type=int, default=10000, help="Paired cluster bootstrap replicates (default 10000).")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        work = _work_dir(args.work_dir)
        db_path = args.sources_db.resolve() if args.sources_db else _default_sources_db()
        if args.command == "corpus":
            result = corpus(db_path, work)
        elif args.command == "sample":
            result = sample(db_path, work)
        elif args.command == "manifest":
            result = run_manifest(db_path, work, json.loads(args.model_config.read_text()))
        elif args.command == "admit":
            _validate_run(db_path, work)
            result = admit(work, json.loads(args.measurements.read_text()))
        elif args.command == "timing-pairs":
            _validate_run(db_path, work)
            result = freeze_timing_pairs(work, json.loads((work / "search-results.json").read_text()))
        elif args.command == "measure":
            _validate_run(db_path, work)
            if args.batch_size < 1 or (args.model in EMBEDDERS and args.variant != "fp32"):
                raise ValueError("Positive batch size and fp32 embedder measurement required")
            _measurement_preflight(work, args.model, args.variant, args.repeat)
            result = _guarded_step(measure, (db_path, work, args.model), {"batch_size": args.batch_size, "variant": args.variant, "repeat": args.repeat}, work, f"measure:{args.model}:{args.variant}:{args.batch_size}:{int(args.repeat)}", args.projection_seconds)
        elif args.command == "encode":
            if args.limit is not None and args.limit < 1:
                raise ValueError("--limit must be positive")
            _validate_run(db_path, work)
            admission = _admission(work)
            if args.model not in admission["admitted_embedders"] or args.batch_size != admission["measurements"]["embedders"][args.model]["batch_size"]:
                raise ValueError("Encode requires admission and the measured batch size")
            if args.batch_size < 1:
                raise ValueError("--batch-size must be positive")
            projection = admission["measurements"]["embedders"][args.model]["projected_seconds"]
            if projection > 2 * 3600 and args.quiet_window_end is None:
                raise ValueError("Large encode requires --quiet-window-end")
            result = _guarded_step(encode, (db_path, work, args.model), {"limit": args.limit, "batch_size": args.batch_size}, work, f"encode:{args.model}:{args.limit}:{args.batch_size}", projection, window_end=args.quiet_window_end)
        elif args.command == "search":
            admission = _admission(work)
            models = args.models if args.models is not None else admission["admitted_embedders"]
            rankers = args.rerankers if args.rerankers is not None else [r for r, d in admission["rerankers"].items() if d["variant"]]
            result = search(db_path, work, models=models, rerankers=rankers, query_limit=args.query_limit, families=args.families)
        elif args.command == "pool":
            _validate_run(db_path, work)
            result = pool(work, query_limit=args.query_limit, overwrite=args.overwrite_pool)
        else:
            _validate_run(db_path, work)
            result = score(work, args.judge_a, args.judge_b, iterations=args.bootstrap_iterations)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, sqlite3.Error, ValueError, KeyError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
