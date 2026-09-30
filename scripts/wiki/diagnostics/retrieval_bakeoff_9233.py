#!/usr/bin/env python3
"""Run the reproducible hybrid Ukrainian retrieval bake-off for #9233.

The source database is opened read-only. All materialized rows, indexes, model
caches, judging pools, and keys are written below the caller-supplied work dir.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import resource
import sqlite3
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.vesum import get_vesum_connection
from scripts.wiki import sources_db
from scripts.wiki.diagnostics import retrieval_probe_9233 as phase1

G3_PATH = ROOT / "docs/research/retrieval-bakeoff-9233/g3-queries.yaml"
QUERY_PATH = ROOT / "docs/research/retrieval-bakeoff-9233/queries.yaml"
G3_SHA256 = "8d5c4b34857d7abe85c1943bb69f39a454547a1176bea1b996c304ca7c8d03d4"
SEED = 9233
RRF_K = 60
TOP_FIRST_STAGE = 100
TOP_RERANK = 50
POOL_DEPTH = 20
TOKEN_RE = phase1.TOKEN_RE

# Repository IDs and retrieval prefixes are frozen from design v5 item 8 and
# the v3 item 8 model-card contracts. Truncation is head-only at model limit.
EMBEDDERS: dict[str, dict[str, str]] = {
    "BAAI/bge-m3": {"kind": "flag", "query_prefix": "", "passage_prefix": ""},
    "Snowflake/snowflake-arctic-embed-l-v2.0": {
        "kind": "sentence", "query_prefix": "Represent this sentence for searching relevant passages: ", "passage_prefix": "",
    },
    "jinaai/jina-embeddings-v5-text-nano": {"kind": "jina", "query_prefix": "task=retrieval; prompt_name=query", "passage_prefix": "task=retrieval; prompt_name=document"},
    "intfloat/multilingual-e5-small": {"kind": "sentence", "query_prefix": "query: ", "passage_prefix": "passage: "},
    "hotchpotch/bekko-embedding-v1-a25m": {"kind": "sentence", "query_prefix": "", "passage_prefix": ""},
    "Qwen/Qwen3-Embedding-0.6B": {
        "kind": "sentence", "query_prefix": "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: ", "passage_prefix": "",
    },
}
RERANKERS = {
    "BAAI/bge-reranker-v2-m3": "cross_encoder",
    "jinaai/jina-reranker-v3.5": "jina",
    "Qwen/Qwen3-Reranker-0.6B": "cross_encoder",
}
EXTRA_SOURCES = (
    "antonenko-davydovych-yak-my-hovorymo",
    "anna-ohoiko-500-verbs",
    "anna-ohoiko-1000-words-2nd-ed",
    "pohribnyi",
)
EXPLICIT_FUNCTION_WORDS = frozenset([
    "а", "або", "але", "в", "від", "до", "з", "за", "і", "й", "на", "не", "у", "та", "що", "це", "як", "про", "для", "коли", "де", "чим", "хто", "чого", "я", "ми", "ти", "ви", "він", "вона", "воно", "вони", "мій", "моя", "моє", "мого", "цим", "цього",
])
TOPIC_FUNCTION_WORDS = frozenset({"з", "із", "зі", "і", "й", "у", "в"})
POS_FUNCTION_MARKERS = ("conj", "conjunction", "prep", "preposition", "part", "particle", "adv.int", "pron.int")


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


def _copy_subset(db_path: Path, work: Path) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    target = work / "corpus.sqlite3"
    if target.exists():
        with _ro_connect(target) as cached:
            ok = cached.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='chunks'").fetchone()
        if ok:
            return target
    source = _ro_connect(db_path)
    try:
        rows = source.execute(
            f"SELECT id,chunk_id,title,text,source_file,subject,parent_section_id FROM textbooks t WHERE {_subset_clause()} ORDER BY id",
            _subset_args(),
        ).fetchall()
    finally:
        source.close()
    conn = sqlite3.connect(target)
    conn.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY, chunk_id TEXT UNIQUE, title TEXT, text TEXT, source_file TEXT, subject TEXT, parent_section_id INTEGER)")
    conn.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?)", [tuple(row) for row in rows])
    conn.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(chunk_id UNINDEXED, title, text, tokenize='unicode61')")
    conn.execute("INSERT INTO chunks_fts(rowid,chunk_id,title,text) SELECT id,chunk_id,title,text FROM chunks")
    conn.commit()
    conn.close()
    return target


def _digest_rows(rows: list[sqlite3.Row] | list[tuple[Any, ...]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        payload = [row[i] for i in range(len(row))]
        digest.update(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def corpus(db_path: Path, work: Path) -> dict[str, Any]:
    source = _ro_connect(db_path)
    try:
        rows = source.execute(
            f"SELECT id,chunk_id,title,text,source_file,subject,parent_section_id FROM textbooks t WHERE {_subset_clause()} ORDER BY id",
            _subset_args(),
        ).fetchall()
    finally:
        source.close()
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        identity = str(row["subject"] or "")
        if identity not in {"ukrmova", "bukvar"}:
            identity = str(row["source_file"] or "")
        counts[identity] += 1
    result = {"rows": len(rows), "row_digest_sha256": _digest_rows(rows), "identity_counts": dict(sorted(counts.items())), "subset": "ukrmova, bukvar, ULP source files, and v5 item 7 source identities"}
    _copy_subset(db_path, work)
    return result


def _vesum_pos(conn: sqlite3.Connection, token: str) -> set[str]:
    rows = conn.execute("SELECT DISTINCT pos FROM forms_all WHERE word_form=?", (token,)).fetchall()
    return {str(row[0]).casefold() for row in rows}


def filter_lemma_query(query: str, vesum: sqlite3.Connection) -> list[str]:
    """Drop VESUM function words unless fewer than two content terms remain or topic."""
    tokens = list(dict.fromkeys(phase1.tokenize(query)))
    if len(tokens) == 1 and tokens[0] in TOPIC_FUNCTION_WORDS:
        return tokens
    content: list[str] = []
    function: list[str] = []
    for token in tokens:
        pos = _vesum_pos(vesum, token)
        is_function = token in EXPLICIT_FUNCTION_WORDS or any(marker in p for p in pos for marker in POS_FUNCTION_MARKERS)
        (function if is_function else content).append(token)
    if len(content) < 2:
        return tokens
    return list(dict.fromkeys(content))


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
        "SELECT c.chunk_id FROM chunks_fts JOIN chunks c ON c.id=chunks_fts.rowid WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts,5.0,1.0),c.id LIMIT ?",
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
    if spec["kind"] == "flag":
        from FlagEmbedding import BGEM3FlagModel

        model = BGEM3FlagModel(repo, use_fp16=False, devices="cpu", cache_dir=str(work / "model-cache"))
        max_tokens = 8192
        return model, {"kind": "flag", "max_tokens": max_tokens}
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(repo, device="cpu", cache_folder=str(work / "model-cache"), trust_remote_code=spec["kind"] == "jina")
    max_tokens = int(model.max_seq_length)
    return model, {"kind": spec["kind"], "max_tokens": max_tokens}


def _encode_batch(model: Any, meta: dict[str, Any], texts: list[str], repo: str, batch_size: int) -> Any:
    spec = EMBEDDERS[repo]
    passages = [text if spec["kind"] == "jina" else spec["passage_prefix"] + text for text in texts]
    if meta["kind"] == "flag":
        result = model.encode(passages, batch_size=batch_size, max_length=meta["max_tokens"], return_dense=True, return_sparse=False, return_colbert_vecs=False)
        return result["dense_vecs"]
    options = {"task": "retrieval", "prompt_name": "document"} if spec["kind"] == "jina" else {}
    return model.encode(passages, batch_size=batch_size, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False, **options)


def encode(db_path: Path, work: Path, repo: str, *, limit: int | None, batch_size: int) -> dict[str, Any]:
    if repo not in EMBEDDERS:
        raise ValueError(f"Unsupported embedding repository: {repo}")
    corpus_path = _copy_subset(db_path, work)
    rows = _load_rows(corpus_path)
    if limit is not None:
        rows = rows[:limit]
    destination = work / "embeddings" / (repo.replace("/", "--") + ".sqlite3")
    destination.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(destination)
    db.execute("CREATE TABLE IF NOT EXISTS vectors (chunk_id TEXT PRIMARY KEY, text_sha256 TEXT NOT NULL, vector BLOB NOT NULL, dimensions INTEGER NOT NULL)")
    completed = {str(row[0]): str(row[1]) for row in db.execute("SELECT chunk_id,text_sha256 FROM vectors")}
    model, meta = _new_encoder(repo, work)
    pending = [row for row in rows if completed.get(str(row["chunk_id"])) != hashlib.sha256(str(row["text"]).encode()).hexdigest()]
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
    wall_seconds = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if os.name != "darwin":
        peak_rss *= 1024
    index_size = sum(p.stat().st_size for p in destination.parent.glob(destination.name + "*"))
    report = {
        "model": repo, "rows_requested": len(rows), "rows_encoded_this_run": len(pending),
        "rows_resumed": len(rows) - len(pending), "batch_size": batch_size,
        "warmup_batch_seconds": warmup_seconds,
        "steady_state_chunks_per_second": steady_chunks / steady_seconds if steady_seconds else None,
        "steady_state_chunks": steady_chunks, "steady_state_seconds": steady_seconds,
        "wall_seconds": wall_seconds, "peak_rss_bytes": peak_rss, "index_size_bytes": index_size,
        "prefixes": {"query": EMBEDDERS[repo]["query_prefix"], "passage": EMBEDDERS[repo]["passage_prefix"]},
        "truncation": f"head-only at model max sequence length ({meta['max_tokens']} tokens)",
        "index": str(destination),
    }
    db.close()
    (work / (repo.replace("/", "--") + "-encode.json")).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _query_vector(model: Any, meta: dict[str, Any], query: str, repo: str) -> Any:
    spec = EMBEDDERS[repo]
    text = query if spec["kind"] == "jina" else spec["query_prefix"] + query
    if meta["kind"] == "flag":
        return model.encode([text], batch_size=1, max_length=meta["max_tokens"], return_dense=True, return_sparse=False, return_colbert_vecs=False)["dense_vecs"][0]
    options = {"task": "retrieval", "prompt_name": "query"} if spec["kind"] == "jina" else {}
    return model.encode([text], batch_size=1, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False, **options)[0]


def _dense_rank(query_vector: Any, vectors_path: Path, limit: int = TOP_FIRST_STAGE) -> list[str]:
    import numpy as np

    conn = _ro_connect(vectors_path)
    try:
        best: list[tuple[float, str]] = []
        q = np.asarray(query_vector, dtype="float32")
        q /= max(float(np.linalg.norm(q)), 1e-12)
        for chunk_id, blob, dimensions in conn.execute("SELECT chunk_id,vector,dimensions FROM vectors"):
            vector = np.frombuffer(blob, dtype="float32", count=int(dimensions))
            score = float(np.dot(q, vector) / max(float(np.linalg.norm(vector)), 1e-12))
            best.append((score, str(chunk_id)))
        return [chunk for _, chunk in sorted(best, key=lambda item: (-item[0], item[1]))[:limit]]
    finally:
        conn.close()


def _new_reranker(repo: str, work: Path) -> tuple[Any, dict[str, Any]]:
    _model_cache(work)
    if RERANKERS[repo] == "flag":
        from FlagEmbedding import FlagReranker

        model = FlagReranker(repo, use_fp16=False, devices="cpu", cache_dir=str(work / "model-cache"))
        return model, {"kind": "flag", "max_tokens": int(model.tokenizer.model_max_length)}
    if RERANKERS[repo] == "jina":
        from transformers import AutoModel

        model = AutoModel.from_pretrained(repo, cache_dir=str(work / "model-cache"), trust_remote_code=True).to("cpu").eval()
        return model, {"kind": "jina", "max_tokens": int(model.config.max_position_embeddings)}
    from sentence_transformers import CrossEncoder

    model = CrossEncoder(repo, device="cpu", cache_folder=str(work / "model-cache"), max_length=512)
    return model, {"kind": "cross_encoder", "max_tokens": 512}


def _rerank(model: Any, meta: dict[str, Any], query: str, candidates: list[dict[str, Any]]) -> list[str]:
    pairs = [[query, str(item["text"])] for item in candidates]
    if meta["kind"] == "flag":
        scores = model.compute_score(pairs, normalize=True)
        if not isinstance(scores, list):
            scores = [scores]
    elif meta["kind"] == "jina":
        result = model.rerank(query, [str(item["text"]) for item in candidates])
        return [str(candidates[int(row["index"])]["chunk_id"]) for row in result]
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
            queries.append({**row, "family": "G1", "stratum": str(row.get("stratum", "G1")), "cluster": row["id"]})
    for row in g1_g2.get("g2", []):
        for form_index, form in enumerate(row.get("forms", [])):
            queries.append({"id": f"{row['id']}:{form}", "query": form, "family": "G2", "stratum": "G2-inflected" if form_index else "G2-base", "cluster": row["id"], "pair_index": form_index, "area": row.get("category", "")})
    for row in g3:
        queries.append({**row, "family": "G3", "stratum": f"G3-{row.get('area','unknown')}-{row.get('kind','unknown')}", "cluster": row["id"]})
    return queries, g3


def search(db_path: Path, work: Path, *, models: list[str], rerankers: list[str], query_limit: int, batch_size: int, families: list[str]) -> dict[str, Any]:
    corpus_path = _copy_subset(db_path, work)
    queries, _ = _load_queries()
    queries = [q for q in queries if q["family"] in families][:query_limit]
    chunks = _load_rows(corpus_path)
    by_id = {str(row["chunk_id"]): row for row in chunks}
    lexical = sqlite3.connect(f"file:{corpus_path.as_posix()}?mode=ro", uri=True)
    lexical.row_factory = sqlite3.Row
    lexical.execute("PRAGMA query_only=ON")
    lexical_rankings: dict[str, list[str]] = {}
    query_times: dict[str, list[float]] = defaultdict(list)
    g3_seen = 0
    with get_vesum_connection(_default_vesum_db()) as vesum:
        for query in queries:
            started = time.perf_counter()
            lexical_rankings[query["id"]] = _fts_search(lexical, str(query["query"]), vesum, lemma=True, limit=TOP_FIRST_STAGE)
            if query["family"] == "G3" and g3_seen < 50:
                g3_seen += 1
                query_times["L"].append(time.perf_counter() - started)
    arms: dict[str, dict[str, list[str]]] = {"L": lexical_rankings}
    costs: dict[str, dict[str, Any]] = {}
    encoders: dict[str, Path] = {}
    for repo in models:
        if repo not in EMBEDDERS:
            raise ValueError(f"Unsupported embedding repository: {repo}")
        vector_path = work / "embeddings" / (repo.replace("/", "--") + ".sqlite3")
        if not vector_path.is_file():
            raise FileNotFoundError(f"Missing index for {repo}; run encode --model {repo} first")
        model, meta = _new_encoder(repo, work)
        encoders[repo] = vector_path
        d_rankings: dict[str, list[str]] = {}
        h_rankings: dict[str, list[str]] = {}
        warmup_query = next((q for q in queries if q["family"] == "G3"), None)
        if warmup_query is not None:
            warmup_vector = _query_vector(model, meta, str(warmup_query["query"]), repo)
            _dense_rank(warmup_vector, vector_path)
        g3_seen = 0
        for q in queries:
            started = time.perf_counter()
            qvec = _query_vector(model, meta, str(q["query"]), repo)
            dense = _dense_rank(qvec, vector_path)
            dense_elapsed = time.perf_counter() - started
            rrf_started = time.perf_counter()
            h_rankings[q["id"]] = reciprocal_rank_fusion([lexical_rankings[q["id"]], dense])
            hybrid_elapsed = time.perf_counter() - rrf_started
            d_rankings[q["id"]] = dense
            if q["family"] == "G3" and g3_seen < 50:
                g3_seen += 1
                query_times[f"D:{repo}"].append(dense_elapsed)
                query_times[f"H:{repo}"].append(dense_elapsed + hybrid_elapsed)
        arms[f"D:{repo}"] = d_rankings
        arms[f"H:{repo}"] = h_rankings
        costs[repo] = json.loads((work / (repo.replace("/", "--") + "-encode.json")).read_text(encoding="utf-8")) if (work / (repo.replace("/", "--") + "-encode.json")).exists() else {}
        del model
    rerank_models: dict[str, tuple[Any, dict[str, Any]]] = {}
    for repo in rerankers:
        if repo not in RERANKERS:
            raise ValueError(f"Unsupported reranker repository: {repo}")
        rerank_models[repo] = _new_reranker(repo, work)
        for embedder in models:
            hybrid_name = f"H:{embedder}"
            arm_name = f"R:{repo}|{embedder}"
            rankings: dict[str, list[str]] = {}
            warmup_query = next((q for q in queries if q["family"] == "G3"), None)
            if warmup_query is not None:
                warmup_candidates = [by_id[cid] for cid in arms[hybrid_name][warmup_query["id"]][:TOP_RERANK] if cid in by_id]
                _rerank(*rerank_models[repo], str(warmup_query["query"]), warmup_candidates)
            g3_seen = 0
            for query in queries:
                candidates = [by_id[cid] for cid in arms[hybrid_name][query["id"]][:TOP_RERANK] if cid in by_id]
                started = time.perf_counter()
                rankings[query["id"]] = _rerank(*rerank_models[repo], str(query["query"]), candidates)
                if query["family"] == "G3" and g3_seen < 50:
                    g3_seen += 1
                    query_times[arm_name].append(time.perf_counter() - started)
            arms[arm_name] = rankings
    for arm, times in query_times.items():
        costs.setdefault(arm, {})["query_p50_seconds"] = statistics.median(times)
        costs[arm]["query_p95_seconds"] = _percentile(times, .95)
        costs[arm]["query_n"] = len(times)
        costs[arm]["query_peak_rss_bytes"] = _peak_rss_bytes()
    costs.setdefault("L", {})["index_size_bytes"] = (work / "corpus.sqlite3").stat().st_size
    for arm in list(query_times):
        if arm == "L":
            continue
        embedder = arm.split("|", maxsplit=1)[1] if arm.startswith("R:") else arm.split(":", maxsplit=1)[1]
        encode_cost = costs.get(embedder, {})
        costs[arm].update({key: encode_cost[key] for key in ("index_size_bytes", "wall_seconds", "steady_state_chunks_per_second", "peak_rss_bytes") if key in encode_cost})
    vector_coverage = {repo: {"indexed_vectors": _vector_count(path), "corpus_rows": len(chunks)} for repo, path in encoders.items()}
    result = {"schema": "retrieval-bakeoff-9233-search.v1", "g3_query_sha256": G3_SHA256, "queries": queries, "arms": arms, "costs": costs, "vector_coverage": vector_coverage, "seed": SEED, "rrf_k": RRF_K, "top_first_stage": TOP_FIRST_STAGE, "top_rerank": TOP_RERANK}
    (work / "search-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lexical.close()
    return result


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value * (1024 if os.name != "darwin" else 1))


def _vector_count(path: Path) -> int:
    with _ro_connect(path) as conn:
        return int(conn.execute("SELECT count(*) FROM vectors").fetchone()[0])


def _percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(probability * len(ordered)) - 1)]


def pool(work: Path, *, query_limit: int | None = None) -> dict[str, Any]:
    path = work / "search-results.json"
    result = json.loads(path.read_text(encoding="utf-8"))
    if query_limit is not None:
        queries = result["queries"][:query_limit]
    else:
        # All G1 and base/first-inflected G2 pairs, then a fixed G3 sample up to 120.
        required = [q for q in result["queries"] if q["family"] == "G1"]
        required.extend(q for q in result["queries"] if q["family"] == "G2" and q.get("pair_index") in {0, 1})
        remaining = max(0, 120 - len(required))
        g3 = [q for q in result["queries"] if q["family"] == "G3"]
        generator = random.Random(SEED)
        required.extend(sorted(generator.sample(g3, min(remaining, len(g3))), key=lambda row: row["id"]))
        queries = required
    corpus_path = work / "corpus.sqlite3"
    chunks = {str(row["chunk_id"]): row for row in _load_rows(corpus_path)}
    # G1 known citations are always included even when only G3 is measured.
    query_set, _ = _load_queries()
    citations: dict[str, list[str]] = defaultdict(list)
    for q in query_set:
        if q["family"] == "G1":
            citations[str(q["id"])].append(str(q.get("gold_chunk_id", "")))
    generator = random.Random(SEED)
    judging: list[dict[str, Any]] = []
    key: list[dict[str, str]] = []
    for query in queries:
        qid = str(query["id"])
        candidates: set[str] = set(citations.get(qid, []))
        for _arm, rankings in result["arms"].items():
            candidates.update(str(cid) for cid in rankings.get(qid, [])[:POOL_DEPTH])
        candidates.discard("")
        item_ids = [hashlib.sha256(f"{qid}\0{cid}".encode()).hexdigest()[:20] for cid in candidates]
        shuffled = list(zip(item_ids, sorted(candidates), strict=True))
        generator.shuffle(shuffled)
        records: list[dict[str, Any]] = []
        for item_id, chunk_id in shuffled:
            row = chunks.get(chunk_id)
            if row is None:
                continue
            records.append({"item_id": item_id, "chunk_id": chunk_id, "source_identity": str(row["source_file"]), "text": str(row["text"])})
            for arm, rankings in result["arms"].items():
                if chunk_id in rankings.get(qid, [])[:POOL_DEPTH]:
                    key.append({"item_id": item_id, "query_id": qid, "arm": arm, "chunk_id": chunk_id})
        judging.append({"query_id": qid, "query": str(query["query"]), "items": records})
    judge_dir = work / "judging"
    judge_dir.mkdir(parents=True, exist_ok=True)
    for judge in ("judge-a", "judge-b"):
        (judge_dir / f"{judge}.jsonl").write_text("", encoding="utf-8")
    (judge_dir / "pool.json").write_text(json.dumps(judging, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    key_path = work / "sealed" / "pool-key.json"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"queries": len(judging), "items": sum(len(q["items"]) for q in judging), "pool": str(judge_dir / "pool.json"), "key": str(key_path), "seed": SEED}


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
    grouped: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for query_id, pair in query_values.items():
        grouped[clusters[query_id]].append(pair)
    keys = sorted(grouped)
    if not keys:
        return {"estimate": 0.0, "lower_95": 0.0, "upper_95": 0.0}
    estimate = statistics.mean(a - b for a, b in query_values.values())
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(iterations):
        chosen = [keys[rng.randrange(len(keys))] for _ in keys]
        pairs = [pair for cluster in chosen for pair in grouped[cluster]]
        samples.append(statistics.mean(a - b for a, b in pairs))
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
        labels[(str(row["query_id"]), str(row["item_id"]))] = row
    return labels


def score(work: Path, labels_a: Path, labels_b: Path, *, iterations: int = 10000) -> dict[str, Any]:
    search_result = json.loads((work / "search-results.json").read_text(encoding="utf-8"))
    key = json.loads((work / "sealed/pool-key.json").read_text(encoding="utf-8"))
    pool_rows = json.loads((work / "judging/pool.json").read_text(encoding="utf-8"))
    a, b = _read_labels(labels_a), _read_labels(labels_b)
    merged: dict[tuple[str, str], dict[str, bool]] = {}
    disagreements: dict[str, int] = defaultdict(int)
    kappa_pairs: dict[str, list[tuple[bool, bool]]] = defaultdict(list)
    for identity in set(a) | set(b):
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
    pool_query_ids = [str(query["query_id"]) for query in pool_rows]
    relevant_by_query: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
    for query in pool_rows:
        qid = str(query["query_id"])
        for item in query["items"]:
            label = merged[(qid, str(item["item_id"]))]
            strict_total, lenient_total = relevant_by_query[qid]
            relevant_by_query[qid] = (
                strict_total + int(label["usable_quotation"] or label["usable_exercise"]),
                lenient_total + int(label["usable_quotation_lenient"] or label["usable_exercise_lenient"]),
            )
    arm_query_hits: dict[str, dict[str, tuple[float, float]]] = defaultdict(dict)
    arm_retrieved: dict[str, dict[str, tuple[int, int]]] = defaultdict(lambda: defaultdict(lambda: (0, 0)))
    for item in key:
        label = merged[(item["query_id"], item["item_id"])]
        current = arm_retrieved[item["arm"]][item["query_id"]]
        quotation = label["usable_quotation"]
        exercise = label["usable_exercise"]
        lq = label["usable_quotation_lenient"]
        le = label["usable_exercise_lenient"]
        arm_retrieved[item["arm"]][item["query_id"]] = (current[0] + int(quotation or exercise), current[1] + int(lq or le))
    query_ids = pool_query_ids
    for arm, retrieved in arm_retrieved.items():
        for qid in query_ids:
            strict_total, lenient_total = relevant_by_query[qid]
            strict_found, lenient_found = retrieved.get(qid, (0, 0))
            arm_query_hits[arm][qid] = (strict_found / strict_total if strict_total else 0.0, lenient_found / lenient_total if lenient_total else 0.0)
    summaries: dict[str, Any] = {}
    for arm, hits in arm_query_hits.items():
        by_stratum: dict[str, list[str]] = defaultdict(list)
        for qid in query_ids:
            by_stratum[str(query_by_id[qid]["stratum"])].append(qid)
        summaries[arm] = {}
        for stratum, ids in by_stratum.items():
            strict_ids = [qid for qid in ids if relevant_by_query[qid][0] > 0]
            lenient_ids = [qid for qid in ids if relevant_by_query[qid][1] > 0]
            summaries[arm][stratum] = {
                "n": len(strict_ids),
                "queries_without_relevant_pool_item": len(ids) - len(strict_ids),
                "recall_at_20_strict": statistics.mean(hits[qid][0] for qid in strict_ids) if strict_ids else 0.0,
                "recall_at_20_lenient": statistics.mean(hits[qid][1] for qid in lenient_ids) if lenient_ids else 0.0,
                "lenient_n": len(lenient_ids),
            }
    g3_g2_ids = [qid for qid in query_ids if query_by_id[qid]["family"] in {"G2", "G3"} and relevant_by_query[qid][0] > 0]
    if not g3_g2_ids:
        raise ValueError("No strictly usable quotation/exercise labels in G2 ∪ G3; Recall@20 comparison is undefined")
    best = max(summaries, key=lambda arm: statistics.mean(arm_query_hits[arm].get(qid, (0.0, 0.0))[0] for qid in g3_g2_ids))
    clusters = {qid: str(query_by_id[qid]["cluster"]) for qid in query_ids}
    paired: dict[str, Any] = {}
    best_hits = arm_query_hits[best]
    for arm, hits in arm_query_hits.items():
        values = {qid: (best_hits.get(qid, (0.0, 0.0))[0], hits.get(qid, (0.0, 0.0))[0]) for qid in g3_g2_ids}
        paired[arm] = paired_cluster_bootstrap(values, clusters, iterations=iterations)
        paired[arm]["eligible_noninferior"] = paired[arm]["upper_95"] <= 0.05
        paired[arm]["reference_arm"] = best
    costs = search_result["costs"]
    eligible = [arm for arm, entry in paired.items() if entry["eligible_noninferior"]]
    eligible.sort(key=lambda arm: (costs.get(arm, {}).get("query_p95_seconds", float("inf")), costs.get(arm, {}).get("index_size_bytes", float("inf")), costs.get(arm, {}).get("wall_seconds", float("inf"))))
    kappas = {label: cohen_kappa(pairs) for label, pairs in kappa_pairs.items()}
    kappa_gate = bool(kappas) and all(value >= 0.6 for value in kappas.values())
    if not kappa_gate:
        for entry in paired.values():
            entry["eligible_noninferior"] = False
    eligible = [arm for arm, entry in paired.items() if entry["eligible_noninferior"]]
    eligible.sort(key=lambda arm: (costs.get(arm, {}).get("query_p95_seconds", float("inf")), costs.get(arm, {}).get("index_size_bytes", float("inf")), costs.get(arm, {}).get("wall_seconds", float("inf"))))
    report = {"schema": "retrieval-bakeoff-9233-score.v1", "g3_query_sha256": G3_SHA256, "query_count": len(query_ids), "judged_items": len(merged), "judge_disagreements": dict(disagreements), "cohen_kappa": kappas, "kappa_gate": kappa_gate, "strata": summaries, "paired_bootstrap_best_minus_arm": paired, "recommended_by_v5_cost_order": eligible[0] if eligible else None, "costs": costs, "eligibility_rule": "upper 95% bound of paired cluster bootstrap(best Recall@20 - arm Recall@20) <= 0.05, conditional on kappa >= 0.6", "seed": SEED}
    (work / "score-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path = ROOT / "docs/research/retrieval-bakeoff-9233/phase2-results.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(report), encoding="utf-8")
    return report


def _render_report(report: dict[str, Any]) -> str:
    lines = ["# #9233 Phase 2 retrieval bake-off results", "", f"G3 query SHA-256: `{G3_SHA256}`; judged query denominator: {report['query_count']}; pooled items: {report['judged_items']}.", "", "Recall@20 uses the stricter label rule (both judges mark quotation or exercise usable); lenient sensitivity uses either judge. G3 and G2 are the primary contrast. English-derived queries are excluded.", "", "## Per arm and stratum", "", "| Arm | Stratum | n | Strict Recall@20 | Lenient Recall@20 |", "|---|---|---:|---:|---:|"]
    for arm, strata in sorted(report["strata"].items()):
        for stratum, metrics in sorted(strata.items()):
            lines.append(f"| {arm} | {stratum} | {metrics['n']} | {metrics['recall_at_20_strict']:.3f} | {metrics['recall_at_20_lenient']:.3f} |")
    lines.extend(["", "## Paired cluster bootstrap and eligibility", "", "Eligibility requires the upper 95% bound of Recall@20(best) − Recall@20(arm) to be at most 0.05. G2 variants resample as a base-query cluster.", "", "| Arm | Reference | Gain estimate | 95% lower | 95% upper | Eligible |", "|---|---|---:|---:|---:|---|"])
    for arm, metric in sorted(report["paired_bootstrap_best_minus_arm"].items()):
        lines.append(f"| {arm} | {metric['reference_arm']} | {metric['estimate']:.3f} | {metric['lower_95']:.3f} | {metric['upper_95']:.3f} | {metric['eligible_noninferior']} |")
    lines.extend(["", f"Recommended by v5 cost ordering: **{report['recommended_by_v5_cost_order'] or 'none eligible'}** (p95 latency, then index size, then subset encode wall time).", "", "## Measured costs", "", "| Arm/model | p50 s | p95 s | query RSS bytes | index bytes | encode s | chunks/s | peak encode RSS bytes |", "|---|---:|---:|---:|---:|---:|---:|---:|"])
    for name, cost in sorted(report["costs"].items()):
        lines.append(f"| {name} | {cost.get('query_p50_seconds','')} | {cost.get('query_p95_seconds','')} | {cost.get('query_peak_rss_bytes','')} | {cost.get('index_size_bytes','')} | {cost.get('wall_seconds','')} | {cost.get('steady_state_chunks_per_second','')} | {cost.get('peak_rss_bytes','')} |")
    lines.extend(["", f"Cohen's kappa by label: `{json.dumps(report['cohen_kappa'], sort_keys=True)}`; gate pass: {report['kappa_gate']}. Judge disagreements: `{json.dumps(report['judge_disagreements'], sort_keys=True)}`.", "", "Residual: no independent held-out set beyond the frozen G1/G2/G3 queries; owner: #9233 accountable driver.", ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure lexical, dense, hybrid, and reranked Ukrainian textbook retrieval for #9233.\nUse this for the frozen bake-off; do not use it for production indexing or changes to sources MCP.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/wiki/diagnostics/retrieval_bakeoff_9233.py corpus --work-dir /tmp/bakeoff-9233
  .venv/bin/python scripts/wiki/diagnostics/retrieval_bakeoff_9233.py encode --model intfloat/multilingual-e5-small --limit 500 --work-dir /tmp/bakeoff-9233
  .venv/bin/python scripts/wiki/diagnostics/retrieval_bakeoff_9233.py search --query-limit 10 --models intfloat/multilingual-e5-small BAAI/bge-m3 --work-dir /tmp/bakeoff-9233
Outputs: corpus/vector indexes, caches, search results, blind judging files, and sealed key below --work-dir; score writes phase2-results.md.
Exit codes: 0 means command completed; >=1 means invalid inputs, missing data/model index, or failed operation.
Related: docs/research/retrieval-bakeoff-9233/g3-queries.yaml; design #9233 v5.
""",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--work-dir", type=Path, required=True, help="External directory for all generated indexes, caches and outputs; example /tmp/bakeoff-9233.")
    common.add_argument("--sources-db", type=Path, help="Read-only textbook SQLite database; defaults to the active project sources.db.")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("corpus", parents=[common], help="Materialize and digest the frozen Ukrainian subset.")
    p = commands.add_parser("encode", parents=[common], help="CPU encode the subset resumably with the selected embedding model.")
    p.add_argument("--model", choices=sorted(EMBEDDERS), required=True, help="Exact embedding model repository; example intfloat/multilingual-e5-small.")
    p.add_argument("--limit", type=int, help="Encode the first N source-ordered chunks only; omit for full subset.")
    p.add_argument("--batch-size", type=int, default=16, help="CPU inference batch size (default 16); example 16.")
    p = commands.add_parser("search", parents=[common], help="Run L, dense D_i, RRF H_i, and every configured reranker over H_i.")
    p.add_argument("--models", nargs="+", choices=sorted(EMBEDDERS), default=sorted(EMBEDDERS), help="Indexed embedder repositories to compare; default all six v5 models.")
    p.add_argument("--rerankers", nargs="+", choices=sorted(RERANKERS), default=sorted(RERANKERS), help="Reranker repositories; default all three v5 rerankers.")
    p.add_argument("--query-limit", type=int, default=10000, help="Maximum frozen queries after family filtering; default all queries.")
    p.add_argument("--families", nargs="+", choices=("G1", "G2", "G3"), default=["G1", "G2", "G3"], help="Query families to execute; default all Ukrainian G1, G2 and G3.")
    p.add_argument("--batch-size", type=int, default=16, help="CPU batch size for model setup/runtime metadata; default 16.")
    p = commands.add_parser("pool", parents=[common], help="Create arm-blind judging files and a separately sealed arm key.")
    p.add_argument("--query-limit", type=int, help="Pool first N search queries; default all search queries.")
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
        elif args.command == "encode":
            if args.limit is not None and args.limit < 1:
                raise ValueError("--limit must be positive")
            result = encode(db_path, work, args.model, limit=args.limit, batch_size=args.batch_size)
        elif args.command == "search":
            result = search(db_path, work, models=args.models, rerankers=args.rerankers, query_limit=args.query_limit, batch_size=args.batch_size, families=args.families)
        elif args.command == "pool":
            result = pool(work, query_limit=args.query_limit)
        else:
            result = score(work, args.judge_a, args.judge_b, iterations=args.bootstrap_iterations)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, sqlite3.Error, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
