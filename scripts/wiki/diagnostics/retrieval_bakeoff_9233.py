#!/usr/bin/env python3
"""Run the reproducible hybrid Ukrainian retrieval bake-off for #9233.

The source database is opened read-only. All materialized rows, indexes, model
caches, judging pools, and keys are written below the caller-supplied work dir.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import math
import multiprocessing
import os
import random
import resource
import sqlite3
import statistics
import sys
import time
from collections import Counter, defaultdict
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
TOP_RERANK = 50
POOL_DEPTH = 20
TOKEN_RE = phase1.TOKEN_RE

# Repository IDs and retrieval prefixes are frozen from design v5 item 8 and
# the v3 item 8 model-card contracts. Truncation is head-only at model limit.
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
    return result


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
    if spec["kind"] == "flag":
        from FlagEmbedding import BGEM3FlagModel

        model = BGEM3FlagModel(repo, use_fp16=False, devices="cpu", cache_dir=str(work / "model-cache"))
        max_tokens = 8192
        model.tokenizer.truncation_side = "right"
        return model, {"kind": "flag", "max_tokens": max_tokens, "prefixes": {"query": "", "passage": ""}}
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(repo, device="cpu", cache_folder=str(work / "model-cache"), trust_remote_code=spec["kind"] == "jina")
    max_tokens = int(model.max_seq_length)
    model.tokenizer.truncation_side = "right"
    prompts = model.prompts
    prefixes = {"query": prompts.get("query", spec["query_prefix"]), "passage": prompts.get("document", spec["passage_prefix"])}
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
    if sys.platform != "darwin":
        peak_rss *= 1024
    index_size = sum(p.stat().st_size for p in destination.parent.glob(destination.name + "*"))
    report = {
        "model": repo, "rows_requested": len(rows), "rows_encoded_this_run": len(pending),
        "rows_resumed": len(rows) - len(pending), "batch_size": batch_size,
        "warmup_batch_seconds": warmup_seconds,
        "steady_state_chunks_per_second": steady_chunks / steady_seconds if steady_seconds else None,
        "steady_state_chunks": steady_chunks, "steady_state_seconds": steady_seconds,
        "wall_seconds": wall_seconds, "peak_rss_bytes": peak_rss, "index_size_bytes": index_size,
        "prefixes": meta.get("prefixes", {"query": EMBEDDERS[repo]["query_prefix"], "passage": EMBEDDERS[repo]["passage_prefix"]}),
        "truncation": f"head-only at model max sequence length ({meta['max_tokens']} tokens)",
        "index": str(destination),
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


def _model_token_limit(tokenizer: Any, config: Any) -> int:
    limits = [int(value) for value in (tokenizer.model_max_length, getattr(config, "max_position_embeddings", None)) if value is not None and 0 < int(value) < 10**9]
    if not limits:
        raise ValueError("Model has no finite token limit")
    return min(limits)


def _native_jina_limits(model: Any) -> dict[str, int]:
    # Read the loaded repository implementation's limits rather than inventing
    # a cap that differs from its native rerank preprocessing.
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(model.rerank)))
    limits = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and type(node.value.value) is int:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"max_query_length", "max_doc_length"}:
                    limits[target.id] = node.value.value
    if set(limits) != {"max_query_length", "max_doc_length"}:
        raise ValueError("Jina native truncation limits changed; verify its repository implementation")
    return limits


def _new_reranker(repo: str, work: Path) -> tuple[Any, dict[str, Any]]:
    _model_cache(work)
    if RERANKERS[repo] == "jina":
        from transformers import AutoModel

        model = AutoModel.from_pretrained(repo, cache_dir=str(work / "model-cache"), trust_remote_code=True).to("cpu").eval()
        model._ensure_tokenizer()
        model._tokenizer.truncation_side = "right"
        return model, {"kind": "jina", "max_tokens": _model_token_limit(model._tokenizer, model.config),
                       "truncation": "head-only; native query/document limits", **_native_jina_limits(model)}
    if RERANKERS[repo] == "qwen":
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(repo, cache_dir=str(work / "model-cache"), padding_side="left", truncation_side="right")
        model = AutoModelForCausalLM.from_pretrained(repo, cache_dir=str(work / "model-cache")).to("cpu").eval()
        return (model, tokenizer), {"kind": "qwen", "max_tokens": _model_token_limit(tokenizer, model.config), "truncation": "head-only, preserving system prefix and yes/no suffix"}
    from sentence_transformers import CrossEncoder

    model = CrossEncoder(repo, device="cpu", cache_folder=str(work / "model-cache"))
    limit = _model_token_limit(model.tokenizer, model.model.config)
    model.max_seq_length = limit
    model.tokenizer.truncation_side = "right"
    return model, {"kind": "cross_encoder", "max_tokens": limit, "truncation": "head-only at model maximum, longest-first pair truncation"}


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
            ids = tokenizer.encode(text, add_special_tokens=False, truncation=True, max_length=budget)
            inputs = tokenizer.pad({"input_ids": [prefix_ids + ids + suffix_ids]}, padding=True, return_tensors="pt")
            logits = model(**inputs).logits[:, -1, :]
            selected = logits[:, [tokenizer.convert_tokens_to_ids("no"), tokenizer.convert_tokens_to_ids("yes")]]
            scores.append(float(torch.softmax(selected, dim=1)[0, 1]))
    return scores


def _rerank(model: Any, meta: dict[str, Any], query: str, candidates: list[dict[str, Any]]) -> list[str]:
    if not candidates:
        return []
    pairs = [[query, str(item["text"])] for item in candidates]
    if meta["kind"] == "jina":
        result = model.rerank(query, [str(item["text"]) for item in candidates])
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


def _run_arm(corpus_path: Path, work: Path, queries: list[dict[str, Any]], arm: str, embedder: str | None, reranker: str | None, vesum_path: Path | None = None) -> dict[str, Any]:
    """One fresh process owns one complete pipeline, including its RSS peak."""
    chunks = _load_rows(corpus_path)
    by_id = {str(row["chunk_id"]): row for row in chunks}
    encoder, encoder_meta = _new_encoder(embedder, work) if embedder else (None, {})
    ranker, ranker_meta = _new_reranker(reranker, work) if reranker else (None, {})
    vector_path = work / "embeddings" / (embedder.replace("/", "--") + ".sqlite3") if embedder else None
    rankings = {}
    times = []
    with _ro_connect(corpus_path) as lexical, get_vesum_connection(vesum_path or _default_vesum_db()) as vesum:
        def retrieve(query: str) -> list[str]:
            hits = []
            if not arm.startswith("D:"):
                hits = _fts_search(lexical, query, vesum, lemma=True, limit=TOP_FIRST_STAGE)
            if embedder:
                dense = _dense_rank(_query_vector(encoder, encoder_meta, query, embedder), vector_path)
                hits = dense if arm.startswith("D:") else reciprocal_rank_fusion([hits, dense])
            if reranker:
                candidates = [by_id[cid] for cid in hits[:TOP_RERANK] if cid in by_id]
                hits = _rerank(ranker, ranker_meta, query, candidates)
            return hits

        measured = [q["id"] for q in queries if q["family"] == "G3"][:50]
        if measured:
            retrieve(str(next(q["query"] for q in queries if q["id"] == measured[0])))
        for query in queries:
            started = time.perf_counter()
            rankings[query["id"]] = retrieve(str(query["query"]))
            elapsed = time.perf_counter() - started
            if query["id"] in measured:
                times.append(elapsed)
    encode_path = work / (embedder.replace("/", "--") + "-encode.json") if embedder else None
    encode_cost = json.loads(encode_path.read_text()) if encode_path and encode_path.exists() else {}
    cost = {key: encode_cost[key] for key in ("wall_seconds", "steady_state_chunks_per_second", "peak_rss_bytes") if key in encode_cost}
    cost.update({"query_p50_seconds": statistics.median(times) if times else None,
                 "query_p95_seconds": _percentile(times, .95) if times else None,
                 "query_n": len(times), "query_peak_rss_bytes": _peak_rss_bytes(),
                 "index_size_bytes": (corpus_path.stat().st_size if not arm.startswith("D:") else 0) + (vector_path.stat().st_size if vector_path else 0),
                 "measurement": "fresh spawned process per arm; one full-pipeline warmup, then first 50 G3 queries; end-to-end lexical/dense/fusion/rerank as applicable; process-lifetime RSS including model setup",
                 "encoder": encoder_meta, "reranker": ranker_meta})
    return {"rankings": rankings, "cost": cost}


def _arm_worker(connection: Any, *args: Any) -> None:
    try:
        connection.send({"ok": True, "result": _run_arm(*args)})
    except Exception as exc:
        connection.send({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        connection.close()


def _isolated_arm(*args: Any) -> dict[str, Any]:
    # Use the prescribed shared interpreter, never a worktree venv.
    multiprocessing.set_executable(str(project_interpreter(ROOT)))
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=_arm_worker, args=(child, *args))
    process.start()
    child.close()
    try:
        message = parent.recv()
    except EOFError as exc:
        raise RuntimeError("Arm process exited without a measurement") from exc
    finally:
        parent.close()
        process.join()
    if process.exitcode != 0 or not message["ok"]:
        raise RuntimeError(message.get("error", f"Arm process exit {process.exitcode}"))
    return message["result"]


def search(db_path: Path, work: Path, *, models: list[str], rerankers: list[str], query_limit: int, families: list[str]) -> dict[str, Any]:
    corpus_path = _copy_subset(db_path, work)
    queries, _ = _load_queries()
    queries = [q for q in queries if q["family"] in families][:query_limit]
    arm_specs = [("L", None, None)]
    coverage = {}
    for repo in models:
        if repo not in EMBEDDERS:
            raise ValueError(f"Unsupported embedding repository: {repo}")
        vector_path = work / "embeddings" / (repo.replace("/", "--") + ".sqlite3")
        if not vector_path.is_file():
            raise FileNotFoundError(f"Missing index for {repo}; run encode --model {repo} first")
        coverage[repo] = {"indexed_vectors": _vector_count(vector_path), "corpus_rows": len(_load_rows(corpus_path))}
        arm_specs.extend([(f"D:{repo}", repo, None), (f"H:{repo}", repo, None)])
        for ranker in rerankers:
            if ranker not in RERANKERS:
                raise ValueError(f"Unsupported reranker repository: {ranker}")
            arm_specs.append((f"R:{ranker}|{repo}", repo, ranker))
    arms, costs = {}, {}
    for arm, embedder, reranker in arm_specs:
        measured = _isolated_arm(corpus_path, work, queries, arm, embedder, reranker)
        arms[arm], costs[arm] = measured["rankings"], measured["cost"]
    result = {"schema": "retrieval-bakeoff-9233-search.v1", "g3_query_sha256": G3_SHA256, "queries": queries, "arms": arms, "costs": costs, "vector_coverage": coverage, "seed": SEED, "rrf_k": RRF_K, "top_first_stage": TOP_FIRST_STAGE, "top_rerank": TOP_RERANK}
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
    queries = _pool_queries(result["queries"], query_limit)
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
                continue
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
        identity = (str(row["query_id"]), str(row["item_id"]))
        if identity in labels:
            raise ValueError(f"Duplicate judging label id in {path}: {identity}")
        labels[identity] = row
    return labels


def score(work: Path, labels_a: Path, labels_b: Path, *, iterations: int = 10000) -> dict[str, Any]:
    search_result = json.loads((work / "search-results.json").read_text(encoding="utf-8"))
    key = json.loads((work / "sealed/pool-key.json").read_text(encoding="utf-8"))
    pool_rows = json.loads((work / "judging/pool.json").read_text(encoding="utf-8"))
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
        if not item["arm"]:
            continue
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
    kappa_gate = bool(kappas) and all(kappas.get(label, 0.0) >= 0.6 for label in ("usable_quotation", "usable_exercise"))
    if not kappa_gate:
        for entry in paired.values():
            entry["eligible_noninferior"] = False
    eligible = [arm for arm, entry in paired.items() if entry["eligible_noninferior"]]
    eligible.sort(key=lambda arm: (costs.get(arm, {}).get("query_p95_seconds", float("inf")), costs.get(arm, {}).get("index_size_bytes", float("inf")), costs.get(arm, {}).get("wall_seconds", float("inf"))))
    report = {"schema": "retrieval-bakeoff-9233-score.v1", "g3_query_sha256": G3_SHA256, "query_count": len(query_ids), "judged_items": len(merged), "judge_disagreements": dict(disagreements), "cohen_kappa": kappas, "kappa_gate": kappa_gate, "strata": summaries, "paired_bootstrap_best_minus_arm": paired, "recommended_by_v5_cost_order": eligible[0] if eligible else None, "costs": costs, "eligibility_rule": "upper 95% bound of paired cluster bootstrap(best Recall@20 - arm Recall@20) <= 0.05, conditional on kappa >= 0.6", "seed": SEED}
    (work / "score-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path = work / "phase2-results.md"
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
        elif args.command == "encode":
            if args.limit is not None and args.limit < 1:
                raise ValueError("--limit must be positive")
            result = encode(db_path, work, args.model, limit=args.limit, batch_size=args.batch_size)
        elif args.command == "search":
            result = search(db_path, work, models=args.models, rerankers=args.rerankers, query_limit=args.query_limit, families=args.families)
        elif args.command == "pool":
            result = pool(work, query_limit=args.query_limit, overwrite=args.overwrite_pool)
        else:
            result = score(work, args.judge_a, args.judge_b, iterations=args.bootstrap_iterations)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, sqlite3.Error, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
