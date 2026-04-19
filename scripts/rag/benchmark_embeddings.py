"""Benchmark embedding models for Ukrainian retrieval.

Compares embedding quality across three language periods:
- Old East Slavic (X-XIII c.)
- Middle Ukrainian (XIV-XVIII c.)
- Modern Ukrainian (textbooks)

Models: BGE-M3 (current), EmbeddingGemma-300M, Qwen3-Embedding-0.6B
        jina-embeddings-v3

Approach:
  1. Load ground-truth queries from benchmark_queries.yaml
  2. Sample chunks from sources.db tier pools
  3. Embed queries + chunks with each model (+ BGE-M3 dense-only)
  4. Compute Recall@K and nDCG@K via numpy
  5. Profile peak memory for each model

Usage:
    # Full benchmark (loads models sequentially to fit in 16GB)
    .venv/bin/python scripts/rag/benchmark_embeddings.py

    # Only run one model (useful for debugging)
    .venv/bin/python scripts/rag/benchmark_embeddings.py --model bge-m3
    .venv/bin/python scripts/rag/benchmark_embeddings.py --model gemma
    .venv/bin/python scripts/rag/benchmark_embeddings.py --model qwen3
    .venv/bin/python scripts/rag/benchmark_embeddings.py --model jina

    # Adjust sample size
    .venv/bin/python scripts/rag/benchmark_embeddings.py --sample-size 500

    # Populate ground truth for queries with empty relevant_chunks
    .venv/bin/python scripts/rag/benchmark_embeddings.py --populate-ground-truth
"""

import argparse
import gc
import json
import random
import resource
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
QUERIES_PATH = SCRIPT_DIR / "benchmark_queries.yaml"
SOURCES_DB_PATH = PROJECT_ROOT / "data" / "sources.db"

# EmbeddingGemma config
GEMMA_MODEL_NAME = "google/embeddinggemma-300m"
GEMMA_DIM = 768

# Qwen3 Embedding config
QWEN3_EMB_MODEL = "Qwen/Qwen3-Embedding-0.6B"
JINA_V3_MODEL = "jinaai/jina-embeddings-v3"

# Evaluation constants
METRICS = ("recall@5", "recall@10", "ndcg@10")
PERIODS = ("old_east_slavic", "middle_ukrainian", "modern")
PERIOD_LABELS = {
    "old_east_slavic": "OES (X-XIII)",
    "middle_ukrainian": "Middle (XIV-XVIII)",
    "modern": "Modern (textbooks)",
}
SAMPLE_SEED = 42

# `sources.db` no longer stores `language_period`, so benchmark tiering uses
# source_file allowlists derived from the literary JSONL metadata that built the DB.
LITERARY_SOURCE_FILES = {
    "old_east_slavic": (
        "wave0-pvl-yaremenko",
        "wave0-slovo-o-polku",
        "wave1-galytsko-volynskyi",
        "wave1-kyivskyi-litopys",
        "wave1-pateryk-pechersky",
        "wave1-pvl-ipatskyi",
        "wave1-pvl-lavrentiyivskyi",
        "wave1-pvl-lavrentiyivskyi-rozshyfrovka",
        "wave1-slovo-poetic-translations",
        "wave11-izbornyk-svyatoslava-uryvky",
        "wave12-ipatskyj-litopys",
        "wave12-lavrentiivskyj-litopys",
        "wave12-novgorodskyj-litopys-1",
        "wave12-paterikon-pecherskyi",
        "wave12-pvl-lavrentiivska",
        "wave12-slovo-o-polku-ihorevim",
        "wave5-buhoslavsky-borys-hlib",
        "wave5-oldukr-xi-xiii",
        "wave5-oldukr-xi-xiii-galvol",
        "wave5-yushkov-ruska-pravda",
        "wave6-galvol-kostruba",
        "wave9-rech-zhydovskoho-1282",
        "wave9-tlkovaniye-1431",
    ),
    "middle_ukrainian": (
        "wave0-samovydets",
        "wave12-bajky-xvii-xviii",
        "wave12-chernihivsky-litopys",
        "wave12-grabianka-litopys",
        "wave12-samovyd-litopys",
        "wave12-ukrainska-poeziia-xvi-xvii",
        "wave12-ukrainski-intermediyi",
        "wave12-velychko-litopys",
        "wave2-berynda-leksykon",
        "wave2-chernihivskyi-litopys",
        "wave2-fedorovych-bukvar",
        "wave2-hrabianka",
        "wave2-istoriya-rusiv",
        "wave2-smotrytsky-gramatyka",
        "wave2-velychko",
        "wave2-zyzaniy-leksys",
        "wave3-bajky-xvii-xviii",
        "wave3-hramoty-xiv",
        "wave3-intermedii-xvii-xviii",
        "wave3-likarski-poradnyky",
        "wave3-poeziya-baroko",
        "wave3-pysovnyk-lystuvannia",
        "wave5-dovhalevsky-poetyka",
        "wave5-hramoty-volyn-xvi",
        "wave5-hramoty-xv",
        "wave5-humanisty-vidrodzennia",
        "wave5-klementiy-zinoviiv",
        "wave5-oldukr-xiv-xvi",
        "wave5-oldukr-xvii",
        "wave5-oldukr-xviii",
        "wave5-poradnyky-xviii",
        "wave5-prokopovych-filosofski",
        "wave5-skovoroda-tvory",
        "wave5-suspilna-dumka-xvi-xvii",
        "wave5-velychkovsky",
        "wave6-bilozersky-pivdennoruski",
        "wave6-boplan-opys-ukrainy",
        "wave6-chevalier-istoriia-viiny",
        "wave6-gustmon-litopys",
        "wave6-huklyvsky-litopys",
        "wave6-khaenko-shchodennyk-rizne",
        "wave6-khanenko-shchodennyk",
        "wave6-keresturska-khronika",
        "wave6-krman-shchodennyk",
        "wave6-kyivskyi-litopys-xvii",
        "wave6-litopys-binvilsky",
        "wave6-litopys-krekhiv",
        "wave6-litopysni-zamitky-1783",
        "wave6-litopysni-zamitky-novorosiia",
        "wave6-litopystsi-krokovskyi",
        "wave6-litovsko-biloruski",
        "wave6-ostrozky-litopys",
        "wave6-povist-ukraina-lytva",
        "wave6-rihelman-litopysna-opovid",
        "wave6-sborlet-zbirnyk",
        "wave6-scherer-litopys-malorosiyi",
        "wave6-sofonovych-khronika",
        "wave6-symonovskyi-korotky-opys",
        "wave6-synopsis-1674",
        "wave7-statut-1566",
        "wave9-fedorovych-azbuka-1578",
        "wave9-synonima-slavenoroskaia",
        "wave9-uzhevych-hramatyka",
        "wave9-uzhevych-paryzky",
        "wave9-verbytsky-bukvar-1627",
        "wikisource-орлик",
    ),
}


# ── Metrics ───────────────────────────────────────────────────────

def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """Fraction of relevant docs found in top-K retrieved."""
    if not relevant_ids:
        return 0.0
    retrieved_set = set(retrieved_ids[:k])
    found = len(retrieved_set & set(relevant_ids))
    return found / len(relevant_ids)


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """Normalized Discounted Cumulative Gain at K."""
    if not relevant_ids:
        return 0.0
    relevant_set = set(relevant_ids)

    # DCG
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        if doc_id in relevant_set:
            dcg += 1.0 / np.log2(i + 2)  # i+2 because rank starts at 1

    # Ideal DCG
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_hits))

    return dcg / idcg if idcg > 0 else 0.0


# ── Data loading ──────────────────────────────────────────────────

def load_queries() -> list[dict]:
    """Load benchmark queries from YAML."""
    with open(QUERIES_PATH) as f:
        data = yaml.safe_load(f)
    return data["queries"]


def get_db_connection() -> sqlite3.Connection:
    """Open the benchmark source DB."""
    if not SOURCES_DB_PATH.exists():
        raise FileNotFoundError(
            f"Sources database not found at {SOURCES_DB_PATH}. "
            "Run: .venv/bin/python scripts/wiki/build_sources_db.py"
        )
    conn = sqlite3.connect(str(SOURCES_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_period_sql(period: str) -> tuple[str, str, tuple]:
    """Return (table, where_sql, params) for a benchmark period.

    Modern uses all textbook grades to preserve comparability with the
    existing ground truth, which includes grades 3-11.
    """
    if period == "modern":
        return "textbooks", "", ()
    if period in LITERARY_SOURCE_FILES:
        source_files = LITERARY_SOURCE_FILES[period]
        placeholders = ", ".join("?" * len(source_files))
        return "literary_texts", f"WHERE source_file IN ({placeholders})", tuple(source_files)
    raise ValueError(f"Unsupported benchmark period: {period}")


def load_period_chunks(period: str, chunk_ids: set[str] | None = None) -> list[dict]:
    """Load all SQLite chunks for a benchmark period or a specific chunk subset."""
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


def sample_chunks_from_sqlite(period: str, sample_size: int) -> list[dict]:
    """Randomly sample benchmark chunks from sources.db for one period."""
    all_chunks = load_period_chunks(period)
    total_chunks = len(all_chunks)
    if total_chunks > sample_size:
        rng = random.Random(SAMPLE_SEED)
        all_chunks = rng.sample(all_chunks, sample_size)
    print(f"  Sampled {len(all_chunks)} chunks for {period} from sources.db (total: {total_chunks})")
    return all_chunks


# ── Encoders ──────────────────────────────────────────────────────

class BGEEncoder:
    """Wraps BGE-M3 for benchmark: returns dense vectors and optionally sparse."""

    def __init__(self):
        self._model = None

    def load(self):
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

    def encode(self, texts: list[str], batch_size: int = 32) -> dict:
        """Returns {dense: np.ndarray, sparse_weights: list[dict]}."""
        self.load()
        result = self._model.encode(
            texts, batch_size=batch_size, max_length=512,
            return_dense=True, return_sparse=True, return_colbert_vecs=False,
        )
        return {
            "dense": result["dense_vecs"],
            "sparse_weights": result["lexical_weights"],
        }

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
        print("[bench] BGE-M3 unloaded.")


class GemmaEncoder:
    """Wraps EmbeddingGemma-300M for benchmark."""

    def __init__(self):
        self._model = None
        self._tokenizer = None

    def load(self):
        if self._model is not None:
            return
        import torch
        from transformers import AutoModel, AutoTokenizer

        # Determine device: prefer MPS on Apple Silicon, fallback to CPU
        if torch.backends.mps.is_available():
            self._device = "mps"
        else:
            self._device = "cpu"

        print(f"[bench] Loading EmbeddingGemma-300M from {GEMMA_MODEL_NAME} on {self._device}...")
        self._tokenizer = AutoTokenizer.from_pretrained(GEMMA_MODEL_NAME)
        # Gemma tokenizer may lack a pad_token — set to EOS
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        self._model = AutoModel.from_pretrained(
            GEMMA_MODEL_NAME,
            torch_dtype=torch.float16,
        ).to(self._device)
        self._model.eval()
        print("[bench] EmbeddingGemma-300M loaded.")

    def encode(self, texts: list[str], batch_size: int = 32) -> dict:
        """Returns {dense: np.ndarray}."""
        import torch

        self.load()
        all_vecs = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            inputs = self._tokenizer(
                batch, padding=True, truncation=True,
                max_length=512, return_tensors="pt",  # Match BGE-M3's max_length for fair comparison
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self._model(**inputs)
                # EmbeddingGemma uses last_hidden_state mean pooling
                attention_mask = inputs["attention_mask"]
                hidden = outputs.last_hidden_state
                mask_expanded = attention_mask.unsqueeze(-1).float()
                summed = (hidden * mask_expanded).sum(dim=1)
                counts = mask_expanded.sum(dim=1).clamp(min=1e-9)
                embeddings = summed / counts
                # Normalize
                embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)

            all_vecs.append(embeddings.cpu().float().numpy())

        return {"dense": np.concatenate(all_vecs, axis=0)}

    def unload(self):
        del self._model
        del self._tokenizer
        self._model = None
        self._tokenizer = None
        gc.collect()
        try:
            import torch
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception:
            pass
        print("[bench] EmbeddingGemma-300M unloaded.")


class Qwen3Encoder:
    """Wraps Qwen3-Embedding-0.6B for benchmark. Same size class as BGE-M3."""

    def __init__(self):
        self._model = None

    def load(self):
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer

        print(f"[bench] Loading {QWEN3_EMB_MODEL}...")
        self._model = SentenceTransformer(
            QWEN3_EMB_MODEL,
            trust_remote_code=True,
        )
        dim = self._model.get_sentence_embedding_dimension()
        print(f"[bench] Qwen3-Embedding-0.6B loaded (dim={dim}).")

    def encode(self, texts: list[str], batch_size: int = 2, *,
               prompt_name: str | None = None) -> dict:
        """Returns {dense: np.ndarray}. Qwen3 is dense-only (no sparse).

        Qwen3-Embedding-0.6B is a decoder model (not BERT-like), so it uses
        significantly more memory per token. We truncate to 512 tokens to match
        BGE-M3's max_length for a fair comparison, and use very small batches
        to reduce MPS pressure on Apple Silicon.
        """
        self.load()
        # Truncate texts to ~512 tokens (~2000 chars) to match BGE-M3
        truncated = [t[:2000] for t in texts]
        vecs = self._model.encode(
            truncated,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
            prompt_name=prompt_name,
        )
        return {"dense": np.array(vecs)}

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
        print("[bench] Qwen3-Embedding-0.6B unloaded.")


class JinaV3Encoder:
    """Wraps jina-embeddings-v3 with retrieval task adapters."""

    def __init__(self):
        self._model = None

    def load(self):
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer

        print(f"[bench] Loading {JINA_V3_MODEL}...")
        self._model = SentenceTransformer(
            JINA_V3_MODEL,
            trust_remote_code=True,
        )
        dim = self._model.get_sentence_embedding_dimension()
        print(f"[bench] jina-embeddings-v3 loaded (dim={dim}).")

    def encode(self, texts: list[str], batch_size: int = 8, *,
               task: str = "retrieval.passage") -> dict:
        """Returns {dense: np.ndarray} using jina-v3 task adapters."""
        self.load()
        vecs = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
            task=task,
        )
        return {"dense": np.array(vecs)}

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
        print("[bench] jina-embeddings-v3 unloaded.")


# ── Sparse scoring ────────────────────────────────────────────────

def sparse_score(query_weights: dict, doc_weights: dict) -> float:
    """Compute sparse dot product between query and document lexical weights."""
    score = 0.0
    for token, qw in query_weights.items():
        if token in doc_weights:
            score += qw * doc_weights[token]
    return score


def rrf_combine(dense_ranks: list[str], sparse_ranks: list[str], k: int = 60) -> list[str]:
    """Reciprocal Rank Fusion of two ranked lists."""
    scores = defaultdict(float)
    for rank, doc_id in enumerate(dense_ranks):
        scores[doc_id] += 1.0 / (k + rank + 1)
    for rank, doc_id in enumerate(sparse_ranks):
        scores[doc_id] += 1.0 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)


# ── Retrieval ─────────────────────────────────────────────────────

def retrieve_dense(query_vec: np.ndarray, chunk_vecs: np.ndarray,
                   chunk_ids: list[str], top_k: int) -> list[str]:
    """Retrieve top-K by cosine similarity (vectors assumed normalized)."""
    scores = chunk_vecs @ query_vec
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [chunk_ids[i] for i in top_indices]


def retrieve_hybrid(query_vec: np.ndarray, query_sparse: dict,
                    chunk_vecs: np.ndarray, chunk_sparse_list: list[dict],
                    chunk_ids: list[str], top_k: int) -> list[str]:
    """Hybrid retrieval: dense + sparse via RRF.

    Uses full corpus ranking for both dense and sparse to avoid
    RRF truncation artifacts. This is O(N) for sparse scoring and
    O(N log N) for sorting — fine for benchmark sample sizes (1-5K chunks)
    but would need top-M pre-filtering for production-scale corpora.
    """
    # Dense ranking — full corpus
    dense_scores = chunk_vecs @ query_vec
    dense_order = np.argsort(dense_scores)[::-1]
    dense_ranked = [chunk_ids[i] for i in dense_order]

    # Sparse ranking — full corpus
    sparse_scores = []
    for i, doc_sparse in enumerate(chunk_sparse_list):
        sparse_scores.append((chunk_ids[i], sparse_score(query_sparse, doc_sparse)))
    sparse_scores.sort(key=lambda x: x[1], reverse=True)
    sparse_ranked = [cid for cid, _ in sparse_scores]

    return rrf_combine(dense_ranked, sparse_ranked)[:top_k]


# ── Memory profiling ──────────────────────────────────────────────

def get_peak_memory_mb() -> float:
    """Get peak RSS in MB (macOS/Linux)."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # On macOS, ru_maxrss is in bytes; on Linux, in KB
    if sys.platform == "darwin":
        return usage.ru_maxrss / (1024 * 1024)
    return usage.ru_maxrss / 1024


def get_mps_memory_mb() -> float:
    """Get current MPS (Apple Silicon GPU) memory allocation in MB. Returns 0 if unavailable."""
    try:
        import torch
        if torch.backends.mps.is_available():
            return torch.mps.current_allocated_memory() / (1024 * 1024)
    except Exception:
        pass
    return 0.0


# ── Ground truth population ───────────────────────────────────────

def populate_ground_truth():
    """Use existing BGE-M3 against SQLite tier pools to find candidate chunks for empty queries.

    WARNING: Auto-populated ground truth is biased toward BGE-M3. These queries
    are tagged with 'auto_populated: true' and reported separately in the benchmark
    to avoid circular evaluation (BGE-M3 evaluated against its own predictions).
    Human review of auto-populated chunks is strongly recommended.
    """
    with open(QUERIES_PATH) as f:
        data = yaml.safe_load(f)

    all_queries = data["queries"]
    empty_queries = [q for q in all_queries if not q.get("relevant_chunks")]

    if not empty_queries:
        print("All queries already have ground truth. Nothing to populate.")
        return

    print(f"Populating ground truth for {len(empty_queries)} queries...")
    print("  WARNING: Auto-populated chunks are BGE-M3-biased. Review manually!")

    encoder = BGEEncoder()
    encoder.load()
    period_chunks: dict[str, list[dict]] = {}
    period_dense: dict[str, np.ndarray] = {}
    period_sparse: dict[str, list[dict]] = {}
    period_ids: dict[str, list[str]] = {}

    for q in empty_queries:
        period = q["period"]
        if period not in period_chunks:
            period_chunks[period] = load_period_chunks(period)
            texts = [chunk["text"] for chunk in period_chunks[period]]
            chunk_result = encoder.encode(texts, batch_size=64)
            period_dense[period] = chunk_result["dense"]
            period_sparse[period] = chunk_result["sparse_weights"]
            period_ids[period] = [chunk["chunk_id"] for chunk in period_chunks[period]]

        result = encoder.encode([q["query"]])
        retrieved = retrieve_hybrid(
            result["dense"][0],
            result["sparse_weights"][0],
            period_dense[period],
            period_sparse[period],
            period_ids[period],
            top_k=3,
        )

        chunk_ids = []
        print(f"\n  Query: {q['query']}")
        text_lookup = {chunk["chunk_id"]: chunk["text"] for chunk in period_chunks[period]}
        for cid in retrieved:
            text_preview = text_lookup.get(cid, "")[:100]
            chunk_ids.append(cid)
            print(f"    [{cid}] {text_preview}...")

        q["relevant_chunks"] = chunk_ids
        q["auto_populated"] = True  # Mark as BGE-M3-sourced ground truth

    # Write back (data was loaded once at the top — no re-read needed)
    with open(QUERIES_PATH, "w") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, width=120)

    print(f"\nUpdated {len(empty_queries)} queries in {QUERIES_PATH}")
    encoder.unload()


# ── Main benchmark ────────────────────────────────────────────────

def run_benchmark(model_filter: str | None = None, sample_size: int = 1000):
    """Run the full benchmark."""
    queries = load_queries()

    # Filter to queries with ground truth
    queries_with_gt = [q for q in queries if q.get("relevant_chunks")]
    queries_without_gt = [q for q in queries if not q.get("relevant_chunks")]

    if queries_without_gt:
        print(f"WARNING: {len(queries_without_gt)} queries have no ground truth.")
        print("  Run with --populate-ground-truth first to fill them in.")
        print()

    if not queries_with_gt:
        print("ERROR: No queries with ground truth. Run --populate-ground-truth first.")
        sys.exit(1)

    print(f"Benchmark: {len(queries_with_gt)} queries with ground truth")
    print(f"Sample size per period: {sample_size}")
    print()

    # Group queries by benchmark period
    by_period = defaultdict(list)
    for q in queries_with_gt:
        by_period[q["period"]].append(q)

    # Sample chunks from each period-specific SQLite pool
    print("Sampling chunks from sources.db...")
    collection_chunks = {}
    for period in by_period:
        collection_chunks[period] = sample_chunks_from_sqlite(period, sample_size)

    # Ensure ground-truth chunks are included in samples
    for period, period_queries in by_period.items():
        sample_ids = {c["chunk_id"] for c in collection_chunks[period]}
        missing_ids = set()
        for q in period_queries:
            for cid in q["relevant_chunks"]:
                if cid not in sample_ids:
                    missing_ids.add(cid)

        if missing_ids:
            print(f"  Fetching {len(missing_ids)} ground-truth chunks missing from sample ({period})")
            collection_chunks[period].extend(load_period_chunks(period, missing_ids))

    # Prepare texts for encoding
    collection_texts = {}
    collection_ids = {}
    for period, chunks in collection_chunks.items():
        collection_texts[period] = [c["text"] for c in chunks]
        collection_ids[period] = [c["chunk_id"] for c in chunks]

    query_texts = [q["query"] for q in queries_with_gt]

    results = {}

    # ── BGE-M3 ────────────────────────────────────────────────────
    if model_filter in (None, "bge-m3"):
        print("\n" + "=" * 60)
        print("MODEL: BGE-M3 (hybrid: dense + sparse)")
        print("=" * 60)

        encoder = BGEEncoder()
        encoder.load()

        t0 = time.time()

        # Encode queries
        print("  Encoding queries...")
        q_result = encoder.encode(query_texts)
        q_dense = q_result["dense"]
        q_sparse = q_result["sparse_weights"]

        # Encode chunks per collection
        c_dense = {}
        c_sparse = {}
        for coll, texts in collection_texts.items():
            print(f"  Encoding {len(texts)} chunks from {coll}...")
            c_result = encoder.encode(texts, batch_size=64)
            c_dense[coll] = c_result["dense"]
            c_sparse[coll] = c_result["sparse_weights"]

        encode_time = time.time() - t0
        peak_rss = get_peak_memory_mb()

        # Evaluate: dense-only
        print("\n  Evaluating BGE-M3 dense-only...")
        bge_dense_metrics = evaluate_model(
            queries_with_gt, q_dense, None,
            collection_ids, c_dense, None, mode="dense"
        )

        # Evaluate: hybrid (dense + sparse)
        print("  Evaluating BGE-M3 hybrid (dense + sparse)...")
        bge_hybrid_metrics = evaluate_model(
            queries_with_gt, q_dense, q_sparse,
            collection_ids, c_dense, c_sparse, mode="hybrid"
        )

        mps_mem = get_mps_memory_mb()
        results["bge-m3-dense"] = {
            "metrics": bge_dense_metrics,
            "peak_rss_mb": peak_rss,
            "mps_memory_mb": mps_mem,
            "encode_time_s": encode_time,
        }
        results["bge-m3-hybrid"] = {
            "metrics": bge_hybrid_metrics,
            "peak_rss_mb": peak_rss,
            "mps_memory_mb": mps_mem,
            "encode_time_s": encode_time,
        }

        encoder.unload()

    # ── EmbeddingGemma-300M ───────────────────────────────────────
    if model_filter in (None, "gemma"):
        print("\n" + "=" * 60)
        print("MODEL: EmbeddingGemma-300M (dense only)")
        print("=" * 60)

        encoder = GemmaEncoder()
        encoder.load()

        t0 = time.time()

        print("  Encoding queries...")
        q_result = encoder.encode(query_texts)
        q_dense = q_result["dense"]

        # Encode chunks per collection
        c_dense = {}
        for coll, texts in collection_texts.items():
            print(f"  Encoding {len(texts)} chunks from {coll}...")
            c_result = encoder.encode(texts, batch_size=32)
            c_dense[coll] = c_result["dense"]

        encode_time = time.time() - t0
        peak_rss = get_peak_memory_mb()

        # Evaluate
        print("\n  Evaluating EmbeddingGemma-300M...")
        gemma_metrics = evaluate_model(
            queries_with_gt, q_dense, None,
            collection_ids, c_dense, None, mode="dense"
        )

        mps_mem = get_mps_memory_mb()
        results["gemma-300m"] = {
            "metrics": gemma_metrics,
            "peak_rss_mb": peak_rss,
            "mps_memory_mb": mps_mem,
            "encode_time_s": encode_time,
        }

        encoder.unload()

    # ── Qwen3-Embedding-0.6B ─────────────────────────────────────
    if model_filter in (None, "qwen3"):
        print("\n" + "=" * 60)
        print("MODEL: Qwen3-Embedding-0.6B (dense only)")
        print("=" * 60)

        encoder = Qwen3Encoder()
        encoder.load()

        t0 = time.time()

        # Encode queries with the model-card query prompt.
        print("  Encoding queries...")
        q_result = encoder.encode(query_texts, prompt_name="query")
        q_dense = q_result["dense"]

        # Encode chunks per collection (very small batches for Apple Silicon memory)
        c_dense = {}
        for coll, texts in collection_texts.items():
            print(f"  Encoding {len(texts)} chunks from {coll}...")
            c_result = encoder.encode(texts, batch_size=2)
            c_dense[coll] = c_result["dense"]

        encode_time = time.time() - t0
        peak_rss = get_peak_memory_mb()

        # Evaluate
        print("\n  Evaluating Qwen3-Embedding-0.6B...")
        qwen3_metrics = evaluate_model(
            queries_with_gt, q_dense, None,
            collection_ids, c_dense, None, mode="dense"
        )

        mps_mem = get_mps_memory_mb()
        results["qwen3-0.6b"] = {
            "metrics": qwen3_metrics,
            "peak_rss_mb": peak_rss,
            "mps_memory_mb": mps_mem,
            "encode_time_s": encode_time,
        }

        encoder.unload()

    # ── jina-embeddings-v3 ──────────────────────────────────────
    if model_filter in (None, "jina"):
        print("\n" + "=" * 60)
        print("MODEL: jina-embeddings-v3 (dense only)")
        print("=" * 60)

        encoder = JinaV3Encoder()
        encoder.load()

        t0 = time.time()

        # Encode queries with the asymmetric retrieval query adapter
        print("  Encoding queries...")
        q_result = encoder.encode(query_texts, task="retrieval.query")
        q_dense = q_result["dense"]

        # Encode chunks per collection with the passage adapter
        c_dense = {}
        for coll, texts in collection_texts.items():
            print(f"  Encoding {len(texts)} chunks from {coll}...")
            c_result = encoder.encode(texts, task="retrieval.passage")
            c_dense[coll] = c_result["dense"]

        encode_time = time.time() - t0
        peak_rss = get_peak_memory_mb()

        print("\n  Evaluating jina-embeddings-v3...")
        jina_metrics = evaluate_model(
            queries_with_gt, q_dense, None,
            collection_ids, c_dense, None, mode="dense"
        )

        mps_mem = get_mps_memory_mb()
        results["jina-v3"] = {
            "metrics": jina_metrics,
            "peak_rss_mb": peak_rss,
            "mps_memory_mb": mps_mem,
            "encode_time_s": encode_time,
        }

        encoder.unload()

    # ── Report ────────────────────────────────────────────────────
    print_report(results)

    # Save results, preserving prior model runs when benchmarking incrementally
    results_path = SCRIPT_DIR / "benchmark_results.json"
    existing_results = {}
    if results_path.exists():
        with open(results_path) as f:
            existing_results = json.load(f)
    existing_results.update(results)
    # Convert numpy types for JSON serialization
    serializable = json.loads(json.dumps(existing_results, default=lambda x: float(x) if isinstance(x, (np.floating,)) else x))
    with open(results_path, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"\nResults saved to {results_path}")


def evaluate_model(queries: list[dict], q_dense: np.ndarray,
                   q_sparse: list[dict] | None,
                   collection_ids: dict[str, list[str]],
                   c_dense: dict[str, np.ndarray],
                   c_sparse: dict[str, list[dict]] | None,
                   mode: str = "dense") -> dict:
    """Evaluate retrieval quality for a model configuration.

    Separates results from human-curated vs auto-populated ground truth
    to avoid circular evaluation bias.
    """
    def empty_metrics():
        return {m: [] for m in METRICS}

    per_period = defaultdict(empty_metrics)
    overall = empty_metrics()
    # Track human-curated queries separately (unbiased subset)
    human_curated = empty_metrics()
    auto_populated_count = 0

    for i, q in enumerate(queries):
        coll = q["period"]
        relevant = q["relevant_chunks"]
        period = q["period"]
        is_auto = q.get("auto_populated", False)

        if coll not in collection_ids:
            continue

        chunk_ids = collection_ids[coll]
        chunk_dense = c_dense[coll]

        if mode == "hybrid" and q_sparse and c_sparse and coll in c_sparse:
            retrieved = retrieve_hybrid(
                q_dense[i], q_sparse[i],
                chunk_dense, c_sparse[coll],
                chunk_ids, top_k=10,
            )
        else:
            retrieved = retrieve_dense(q_dense[i], chunk_dense, chunk_ids, top_k=10)

        r5 = recall_at_k(retrieved, relevant, 5)
        r10 = recall_at_k(retrieved, relevant, 10)
        n10 = ndcg_at_k(retrieved, relevant, 10)

        per_period[period]["recall@5"].append(r5)
        per_period[period]["recall@10"].append(r10)
        per_period[period]["ndcg@10"].append(n10)

        overall["recall@5"].append(r5)
        overall["recall@10"].append(r10)
        overall["ndcg@10"].append(n10)

        if is_auto:
            auto_populated_count += 1
        else:
            human_curated["recall@5"].append(r5)
            human_curated["recall@10"].append(r10)
            human_curated["ndcg@10"].append(n10)

    # Aggregate
    result = {"overall": {}, "by_period": {}, "human_curated_only": {}}
    for metric in METRICS:
        result["overall"][metric] = float(np.mean(overall[metric])) if overall[metric] else 0.0
        result["human_curated_only"][metric] = float(np.mean(human_curated[metric])) if human_curated[metric] else 0.0

    for period, metrics in per_period.items():
        result["by_period"][period] = {}
        for metric in METRICS:
            result["by_period"][period][metric] = float(np.mean(metrics[metric])) if metrics[metric] else 0.0

    result["auto_populated_count"] = auto_populated_count
    result["human_curated_count"] = len(overall["recall@5"]) - auto_populated_count
    return result


def print_report(results: dict):
    """Print a formatted comparison report."""
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    models = list(results.keys())

    # Header
    header = f"{'Metric':<25}"
    for model in models:
        header += f"{model:>18}"
    print(header)
    print("-" * 70)

    # Overall
    for metric in METRICS:
        row = f"{'Overall ' + metric:<25}"
        for model in models:
            val = results[model]["metrics"]["overall"].get(metric, 0)
            row += f"{val:>17.3f}"
        print(row)

    print("-" * 70)

    # Human-curated only (unbiased)
    print("\n  Human-curated ground truth only (unbiased):")
    for metric in METRICS:
        row = f"    {metric:<21}"
        for model in models:
            val = results[model]["metrics"].get("human_curated_only", {}).get(metric, 0)
            row += f"{val:>18.3f}"
        print(row)

    # Show query counts
    for model in models:
        m = results[model]["metrics"]
        human = m.get("human_curated_count", "?")
        auto = m.get("auto_populated_count", "?")
        print(f"    {model}: {human} human-curated, {auto} auto-populated")

    print("-" * 70)

    # Per period
    for period in PERIODS:
        label = PERIOD_LABELS.get(period, period)
        print(f"\n  {label}:")
        for metric in METRICS:
            row = f"    {metric:<21}"
            for model in models:
                val = results[model]["metrics"]["by_period"].get(period, {}).get(metric, 0)
                row += f"{val:>18.3f}"
            print(row)

    print("-" * 70)

    # Memory and speed
    print(f"\n{'Peak RSS (MB)':<25}", end="")
    for model in models:
        print(f"{results[model]['peak_rss_mb']:>17.0f}", end="")
    print()

    print(f"{'MPS/GPU mem (MB)':<25}", end="")
    for model in models:
        print(f"{results[model].get('mps_memory_mb', 0):>17.0f}", end="")
    print()

    print(f"{'Encode time (s)':<25}", end="")
    for model in models:
        print(f"{results[model]['encode_time_s']:>17.1f}", end="")
    print()

    # Sparse contribution analysis
    if "bge-m3-dense" in results and "bge-m3-hybrid" in results:
        print("\n" + "-" * 70)
        print("SPARSE SEARCH CONTRIBUTION (BGE-M3 hybrid - dense):")
        for period in PERIODS:
            label = PERIOD_LABELS.get(period, period)
            dense_r10 = results["bge-m3-dense"]["metrics"]["by_period"].get(period, {}).get("recall@10", 0)
            hybrid_r10 = results["bge-m3-hybrid"]["metrics"]["by_period"].get(period, {}).get("recall@10", 0)
            delta = hybrid_r10 - dense_r10
            sign = "+" if delta >= 0 else ""
            print(f"  {label:<25} Recall@10: {sign}{delta:.3f}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Benchmark Ukrainian embedding models from sources.db")
    parser.add_argument("--model", choices=["bge-m3", "gemma", "qwen3", "jina"], default=None,
                        help="Run only one model (default: all four)")
    parser.add_argument("--sample-size", type=int, default=1000,
                        help="Number of chunks to sample per collection (default: 1000)")
    parser.add_argument("--populate-ground-truth", action="store_true",
                        help="Use BGE-M3 + SQLite tier pools to fill empty relevant_chunks in queries")
    args = parser.parse_args()

    if args.populate_ground_truth:
        populate_ground_truth()
    else:
        run_benchmark(model_filter=args.model, sample_size=args.sample_size)


if __name__ == "__main__":
    main()
