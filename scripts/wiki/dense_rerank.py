"""Dense reranking and cold-encode helpers for manifest-backed wiki retrieval."""

from __future__ import annotations

import atexit
import gc
import hashlib
import os
import sqlite3
import threading
import time
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .chunking import chunk_text, policy_for
from .config import PROJECT_ROOT
from .embedding_manifest import (
    EmbeddingManifest,
    EncoderConfig,
    UnitSpecInput,
    append_shard,
    filter_new_or_changed,
)
from .mlx_bridge import EMBEDDING_DIMS, MLXEncoderBridge
from .thermal import nsprocessinfo_thermal_state

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_MANIFEST_DB = PROJECT_ROOT / "data" / "embeddings" / "manifest.db"
DEFAULT_MODEL_ID = "bge-m3-mlx-fp16"
DEFAULT_POOLING_MODE = "cls"
QUERY_MAX_LENGTH = 512
INDEX_MAX_LENGTH = 512


def current_encoder_config(corpus: str) -> EncoderConfig:
    """Build the ``EncoderConfig`` that the runtime is currently using
    for ``corpus``.

    The ``chunk_policy_version`` is pulled from the chunking registry
    (``wiki.chunking.CHUNKING_POLICIES``), so per-corpus chunker
    changes invalidate that corpus's manifest entries automatically.
    Unknown corpora raise ``KeyError`` — registration is required.

    Until #1553 step 5 bumps ``INDEX_MAX_LENGTH`` past 512, the
    model + max-length + pooling tuple stays at the #1348 shipped
    values and only the chunk_policy_version field shifts when the
    chunker changes (paragraph-aware policies replace the legacy
    "no chunking" stamp on textbook / external / wikipedia).
    """

    return EncoderConfig(
        model=DEFAULT_MODEL_ID,
        index_max_length=INDEX_MAX_LENGTH,
        chunk_policy_version=policy_for(corpus).version_id,
        pooling_mode=DEFAULT_POOLING_MODE,
    )
MAX_BATCH_ROWS = 16
MAX_BATCH_TOKENS = 4096
LITERARY_SHARD_LIMIT = 5000
SEQUENTIAL_SHARD_LIMIT = 1000
EPOCH_BATCH_LIMIT = 8
EPOCH_TOKEN_LIMIT = 32_000
SUPPORTED_CORPORA = (
    "textbook_sections",
    "modern_literary",
    "archaic_literary",
    "external",
    "wikipedia",
    "ukrainian_wiki",
)

_TOKENIZER = None
_TOKENIZER_LOCK = threading.Lock()
_ENCODER = None
#: Re-entrant because encode_query() acquires this lock then calls _get_encoder()
#: which also acquires it. With a plain Lock() that's an instant self-deadlock
#: the first time a query comes in without a cached encoder.
_ENCODER_LOCK = threading.RLock()
_QUERY_CACHE: dict[tuple[str, int, str], NDArray[np.float32]] = {}
_INDEX_CACHE: dict[tuple[Path, str], CorpusEmbeddingIndex] = {}
_INDEX_CACHE_LOCK = threading.Lock()


@dataclass(frozen=True)
class CorpusUnit:
    """A single dense-indexable retrieval unit."""

    unit_key: str
    corpus: str
    parent_key: str | None
    text: str
    text_sha256: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CorpusEmbeddingIndex:
    """Per-corpus shard map + unit row routing table."""

    corpus: str
    shards: dict[int, np.memmap]
    unit_rows: dict[str, tuple[int, int]]


@dataclass
class _ThermalEpochController:
    tier: str = "cool"
    consecutive_nominal_epochs: int = 0
    ms_per_token_ewma: float | None = None
    consecutive_regressed_epochs: int = 0


_EPOCH_SLEEP_BY_TIER = {"cool": 0.0, "warm": 1.5, "hot": 5.0}
_THERMAL_NOMINAL = 0
_THERMAL_FAIR = 1
_THERMAL_SERIOUS = 2
_THERMAL_CRITICAL = 3
_MS_PER_TOKEN_REGRESSION_RATIO = 1.15
_THERMAL_EWMA_ALPHA = 0.2
_THERMAL_DEMOTION_NOMINAL_EPOCHS = 5
_THERMAL_REGRESSION_EPOCHS = 3


def _advance_thermal_epoch(
    controller: _ThermalEpochController,
    *,
    ms_per_token: float,
    thermal_state: int,
) -> tuple[str, float]:
    regressed = (
        controller.ms_per_token_ewma is not None
        and ms_per_token > controller.ms_per_token_ewma * _MS_PER_TOKEN_REGRESSION_RATIO
    )

    if thermal_state >= _THERMAL_CRITICAL:
        controller.tier = "hot"
        controller.consecutive_nominal_epochs = 0
        controller.consecutive_regressed_epochs = 0
    else:
        if thermal_state >= _THERMAL_SERIOUS:
            # Escalate: cool → warm → warm (don't jump to hot on SERIOUS; CRITICAL does that)
            if controller.tier == "cool":
                controller.tier = "warm"
            # warm and hot stay as-is; SERIOUS doesn't escalate from warm/hot
            controller.consecutive_nominal_epochs = 0
            controller.consecutive_regressed_epochs = 0
        elif regressed:
            controller.consecutive_regressed_epochs += 1
            controller.consecutive_nominal_epochs = 0
            if controller.consecutive_regressed_epochs >= _THERMAL_REGRESSION_EPOCHS:
                if controller.tier == "cool":
                    controller.tier = "warm"
                elif controller.tier == "warm":
                    controller.tier = "hot"
                # if already "hot", stay at "hot"
        else:
            controller.consecutive_regressed_epochs = 0
            if thermal_state == _THERMAL_NOMINAL:
                controller.consecutive_nominal_epochs += 1
                if controller.consecutive_nominal_epochs >= _THERMAL_DEMOTION_NOMINAL_EPOCHS:
                    if controller.tier == "hot":
                        controller.tier = "warm"
                    elif controller.tier == "warm":
                        controller.tier = "cool"
                    controller.consecutive_nominal_epochs = 0
            else:
                controller.consecutive_nominal_epochs = 0

    if controller.ms_per_token_ewma is None:
        controller.ms_per_token_ewma = ms_per_token
    elif not regressed and thermal_state <= _THERMAL_FAIR:
        controller.ms_per_token_ewma += _THERMAL_EWMA_ALPHA * (
            ms_per_token - controller.ms_per_token_ewma
        )

    return controller.tier, _EPOCH_SLEEP_BY_TIER[controller.tier]


def _now_utc_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _suppress_misleading_tokenizer_warning() -> None:
    """Filter HuggingFace's "sequence length is longer than the
    specified maximum" warning at the logger level (#1553 step 4).

    The warning is emitted from
    ``transformers.tokenization_utils_base`` BEFORE truncation
    actually runs. Every code path that calls the tokenizer
    explicitly passes ``truncation=True, max_length=...``, so the
    warning is a false alarm — but it still scares future readers
    of build logs into thinking the encoder will crash.

    Filter only the one specific warning at the transformers
    tokenization logger; do not suppress real warnings.
    """

    import logging

    class _SilenceLengthWarning(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return "Token indices sequence length is longer" not in record.getMessage()

    logger = logging.getLogger("transformers.tokenization_utils_base")
    # Idempotent: don't add the filter twice on re-import.
    if not any(isinstance(f, _SilenceLengthWarning) for f in logger.filters):
        logger.addFilter(_SilenceLengthWarning())


def _get_tokenizer():
    global _TOKENIZER
    if _TOKENIZER is not None:
        return _TOKENIZER

    with _TOKENIZER_LOCK:
        if _TOKENIZER is None:
            from transformers import AutoTokenizer

            _suppress_misleading_tokenizer_warning()
            _TOKENIZER = AutoTokenizer.from_pretrained("BAAI/bge-m3", use_fast=True)
    return _TOKENIZER


def _extract_dense_vectors(encoded: Any) -> NDArray[np.float16]:
    dense = encoded.get("dense_vecs") if isinstance(encoded, dict) else encoded
    if dense is None:
        raise ValueError("encoder output did not include dense vectors")
    array = np.asarray(dense)
    if array.ndim != 2 or array.shape[1] != EMBEDDING_DIMS:
        raise ValueError(f"unexpected embedding shape {array.shape!r}")
    return array.astype(np.float16, copy=False)


class _FlagEmbeddingEncoder:
    """In-process fallback for environments that still want PyTorch MPS."""

    def __init__(self) -> None:
        from FlagEmbedding import BGEM3FlagModel

        self._model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True, pooling_method="cls")

    def encode(
        self,
        texts: list[str],
        batch_size: int = MAX_BATCH_ROWS,
        max_length: int = INDEX_MAX_LENGTH,
    ) -> NDArray[np.float16]:
        encoded = self._model.encode(
            texts,
            batch_size=batch_size,
            max_length=max_length,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        return _extract_dense_vectors(encoded)


def _get_encoder():
    global _ENCODER
    if _ENCODER is not None:
        return _ENCODER

    with _ENCODER_LOCK:
        if _ENCODER is None:
            if os.environ.get("EMBED_FRAMEWORK") == "pytorch_mps":
                _ENCODER = _FlagEmbeddingEncoder()
            else:
                _ENCODER = MLXEncoderBridge()
    return _ENCODER


def _close_encoder() -> None:
    global _ENCODER
    encoder = _ENCODER
    _ENCODER = None
    if encoder is not None and hasattr(encoder, "close"):
        encoder.close()


atexit.register(_close_encoder)


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_matrix(matrix: NDArray[np.float32]) -> NDArray[np.float32]:
    if matrix.size == 0:
        return matrix.astype(np.float32, copy=False)
    matrix = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.clip(norms, 1e-12, None)


def _token_count(text: str, *, max_length: int) -> int:
    tokenizer = _get_tokenizer()
    token_ids = tokenizer.encode(
        text,
        add_special_tokens=True,
        truncation=True,
        max_length=max_length,
    )
    return max(1, len(token_ids))


def _sorted_token_batches(
    texts: Sequence[str],
    *,
    max_length: int,
    max_rows: int = MAX_BATCH_ROWS,
    max_tokens: int = MAX_BATCH_TOKENS,
    token_lengths: Sequence[int] | None = None,
) -> list[list[int]]:
    token_lengths = list(token_lengths) if token_lengths is not None else [
        _token_count(text, max_length=max_length) for text in texts
    ]
    order = sorted(range(len(texts)), key=token_lengths.__getitem__)
    batches: list[list[int]] = []
    current: list[int] = []
    current_tokens = 0

    for index in order:
        token_count = min(token_lengths[index], max_tokens)
        would_overflow = current and (
            len(current) >= max_rows or current_tokens + token_count > max_tokens
        )
        if would_overflow:
            batches.append(current)
            current = []
            current_tokens = 0

        current.append(index)
        current_tokens += token_count

        if len(current) >= max_rows or current_tokens >= max_tokens:
            batches.append(current)
            current = []
            current_tokens = 0

    if current:
        batches.append(current)
    return batches


def encode_texts(
    texts: Sequence[str],
    *,
    encoder=None,
    max_length: int = INDEX_MAX_LENGTH,
    max_rows: int = MAX_BATCH_ROWS,
    max_tokens: int = MAX_BATCH_TOKENS,
    corpus: str | None = None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> NDArray[np.float16]:
    """Encode texts with token-budget batching while preserving input order."""

    if not texts:
        return np.zeros((0, EMBEDDING_DIMS), dtype=np.float16)

    encoder = encoder or _get_encoder()
    result = np.zeros((len(texts), EMBEDDING_DIMS), dtype=np.float16)
    token_lengths = [_token_count(text, max_length=max_length) for text in texts]
    batches = _sorted_token_batches(
        texts,
        max_length=max_length,
        max_rows=max_rows,
        max_tokens=max_tokens,
        token_lengths=token_lengths,
    )
    controller = _ThermalEpochController()
    epoch_rows = 0
    epoch_tokens = 0
    epoch_encode_s = 0.0
    epoch_batches = 0

    for batch_number, batch_indices in enumerate(batches, start=1):
        batch_texts = [texts[index] for index in batch_indices]
        batch_tokens = sum(min(token_lengths[index], max_tokens) for index in batch_indices)
        batch_started = time.perf_counter()
        with _ENCODER_LOCK:
            batch_vectors = _extract_dense_vectors(
                encoder.encode(
                    batch_texts,
                    batch_size=min(max_rows, len(batch_texts)),
                    max_length=max_length,
                )
            )
        batch_encode_s = time.perf_counter() - batch_started
        for row_index, original_index in enumerate(batch_indices):
            result[original_index] = batch_vectors[row_index]
        epoch_rows += len(batch_indices)
        epoch_tokens += batch_tokens
        epoch_encode_s += batch_encode_s
        epoch_batches += 1

        epoch_boundary = (
            epoch_batches >= EPOCH_BATCH_LIMIT
            or epoch_tokens >= EPOCH_TOKEN_LIMIT
            or batch_number == len(batches)
        )
        if epoch_boundary:
            thermal_state = nsprocessinfo_thermal_state()
            ms_per_token = (epoch_encode_s * 1000.0) / max(epoch_tokens, 1)
            tier, sleep_s = _advance_thermal_epoch(
                controller,
                ms_per_token=ms_per_token,
                thermal_state=thermal_state,
            )
            actual_sleep_s = sleep_s if batch_number < len(batches) else 0.0
            if progress_callback is not None and corpus is not None:
                progress_callback(
                    {
                        "event": "epoch_done",
                        "ts": _now_utc_iso(),
                        "corpus": corpus,
                        "rows": epoch_rows,
                        "tokens": epoch_tokens,
                        "encode_s": round(epoch_encode_s, 3),
                        "ms_per_token": round(ms_per_token, 6),
                        "tier": tier,
                        "thermal_state": thermal_state,
                        "sleep_s": actual_sleep_s,
                    }
                )
            if actual_sleep_s:
                time.sleep(actual_sleep_s)
            epoch_rows = 0
            epoch_tokens = 0
            epoch_encode_s = 0.0
            epoch_batches = 0
        gc.collect()

    return result


def _query_cache_key(query: str, *, max_length: int) -> tuple[str, int, str]:
    framework = os.environ.get("EMBED_FRAMEWORK", "mlx")
    digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
    return digest, max_length, framework


def encode_query(query: str, *, encoder=None, max_length: int = QUERY_MAX_LENGTH) -> NDArray[np.float32]:
    cache_key = _query_cache_key(query, max_length=max_length)
    cached = _QUERY_CACHE.get(cache_key)
    if cached is not None:
        return cached

    with _ENCODER_LOCK:
        cached = _QUERY_CACHE.get(cache_key)
        if cached is not None:
            return cached
        encoder = encoder or _get_encoder()
        vector = _extract_dense_vectors(
            encoder.encode([query], batch_size=1, max_length=max_length)
        ).astype(np.float32, copy=False)
        normalized = _normalize_matrix(vector)[0]
        _QUERY_CACHE[cache_key] = normalized
        return normalized


def load_corpus_index(
    corpus: str,
    *,
    manifest_db: Path = DEFAULT_MANIFEST_DB,
    refresh: bool = False,
) -> CorpusEmbeddingIndex:
    cache_key = (Path(manifest_db), corpus)
    with _INDEX_CACHE_LOCK:
        if refresh:
            _INDEX_CACHE.pop(cache_key, None)
        cached = _INDEX_CACHE.get(cache_key)
        if cached is not None:
            return cached

    manifest_path = Path(manifest_db)
    if not manifest_path.exists():
        index = CorpusEmbeddingIndex(corpus=corpus, shards={}, unit_rows={})
        with _INDEX_CACHE_LOCK:
            _INDEX_CACHE[cache_key] = index
        return index

    manifest = EmbeddingManifest(manifest_path)
    try:
        shard_map = manifest.shard_map_for_corpus(corpus)
        unit_rows = {
            row.unit_key: (row.shard_id, row.row_idx)
            for row in manifest.active_units_for_corpus(corpus)
        }
    finally:
        manifest.close()

    index = CorpusEmbeddingIndex(
        corpus=corpus,
        shards={
            shard_id: np.load(path, mmap_mode="r")
            for shard_id, path in shard_map.items()
        },
        unit_rows=unit_rows,
    )
    with _INDEX_CACHE_LOCK:
        _INDEX_CACHE[cache_key] = index
    return index


def invalidate_corpus_index(corpus: str, *, manifest_db: Path = DEFAULT_MANIFEST_DB) -> None:
    with _INDEX_CACHE_LOCK:
        _INDEX_CACHE.pop((Path(manifest_db), corpus), None)


def rerank_candidates(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    corpus: str,
    limit: int = 10,
    manifest_db: Path = DEFAULT_MANIFEST_DB,
    encoder=None,
) -> list[dict[str, Any]]:
    """Rerank prefiltered candidates against the manifest-backed dense index."""

    if not candidates:
        return []

    index = load_corpus_index(corpus, manifest_db=manifest_db)
    if not index.unit_rows:
        return [{**candidate, "dense_score": 0.0, "cosine_score": 0.0} for candidate in candidates[:limit]]

    vectors: list[NDArray[np.float32]] = []
    present: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for candidate in candidates:
        unit_key = str(candidate.get("unit_key", "")).strip()
        location = index.unit_rows.get(unit_key)
        if location is None:
            missing.append({**candidate, "dense_score": 0.0, "cosine_score": 0.0})
            continue
        shard_id, row_idx = location
        vectors.append(np.asarray(index.shards[shard_id][row_idx], dtype=np.float32))
        present.append(candidate)

    if not present:
        return missing[:limit]

    candidate_matrix = _normalize_matrix(np.stack(vectors, axis=0))
    query_vector = encode_query(query, encoder=encoder)
    scores = candidate_matrix @ query_vector

    scored = [
        {
            **candidate,
            "dense_score": float(score),
            "cosine_score": float(score),
        }
        for candidate, score in zip(present, scores, strict=True)
    ]
    scored.extend(missing)
    scored.sort(
        key=lambda row: (
            -float(row.get("dense_score", 0.0)),
            float(row.get("fts_score", row.get("rank", 0.0)) or 0.0),
            str(row.get("unit_key", "")),
        )
    )
    return scored[:limit]


def rerank_sections(
    query: str,
    sections: list[dict[str, Any]],
    *,
    limit: int = 10,
    manifest_db: Path = DEFAULT_MANIFEST_DB,
    encoder=None,
    **_: Any,
) -> list[dict[str, Any]]:
    """Backward-compatible textbook-section wrapper used by earlier callers."""

    enriched = [
        {
            **section,
            "unit_key": section.get("unit_key") or f"textbook_sections:{int(section['section_id'])}",
        }
        for section in sections
    ]
    return rerank_candidates(
        query,
        enriched,
        corpus="textbook_sections",
        limit=limit,
        manifest_db=manifest_db,
        encoder=encoder,
    )


def _literary_query(conn: sqlite3.Connection, where_sql: str, params: tuple[Any, ...]) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(
        f"""
        SELECT
            id,
            chunk_id,
            text,
            source_file,
            work_id
        FROM literary_texts
        WHERE {where_sql}
        ORDER BY source_file, id
        """,
        params,
    ).fetchall()


def _iter_textbook_units(conn: sqlite3.Connection) -> Iterator[CorpusUnit]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT section_id, source_file, section_title, full_text
        FROM textbook_sections
        ORDER BY section_id
        """
    ).fetchall()
    for row in rows:
        text = str(row["full_text"] or "")
        yield CorpusUnit(
            unit_key=f"textbook_sections:{int(row['section_id'])}",
            corpus="textbook_sections",
            parent_key=str(row["source_file"] or ""),
            text=text,
            text_sha256=text_sha256(text),
            metadata={
                "section_id": int(row["section_id"]),
                "source_file": str(row["source_file"] or ""),
                "title": str(row["section_title"] or ""),
            },
        )


def _iter_modern_literary_units(conn: sqlite3.Connection) -> Iterator[CorpusUnit]:
    for row in _literary_query(conn, "language_period = ?", ("modern",)):
        text = str(row["text"] or "")
        yield CorpusUnit(
            unit_key=f"modern_literary:{row['chunk_id']}",
            corpus="modern_literary",
            parent_key=str(row["work_id"] or row["source_file"] or ""),
            text=text,
            text_sha256=text_sha256(text),
            metadata={
                "chunk_id": str(row["chunk_id"] or ""),
                "source_file": str(row["source_file"] or ""),
                "row_id": int(row["id"]),
            },
        )


def _iter_archaic_literary_units(conn: sqlite3.Connection) -> Iterator[CorpusUnit]:
    for row in _literary_query(
        conn,
        "language_period IN (?, ?)",
        ("middle_ukrainian", "old_east_slavic"),
    ):
        text = str(row["text"] or "")
        yield CorpusUnit(
            unit_key=f"archaic_literary:{row['chunk_id']}",
            corpus="archaic_literary",
            parent_key=str(row["work_id"] or row["source_file"] or ""),
            text=text,
            text_sha256=text_sha256(text),
            metadata={
                "chunk_id": str(row["chunk_id"] or ""),
                "source_file": str(row["source_file"] or ""),
                "row_id": int(row["id"]),
            },
        )


def _iter_external_units(conn: sqlite3.Connection) -> Iterator[CorpusUnit]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT id, chunk_id, source_file, title, text, url
        FROM external_articles
        ORDER BY id
        """
    ).fetchall()
    for row in rows:
        text = str(row["text"] or "")
        chunk_id = str(row["chunk_id"] or row["id"])
        yield CorpusUnit(
            unit_key=f"external:{chunk_id}",
            corpus="external",
            parent_key=str(row["source_file"] or ""),
            text=text,
            text_sha256=text_sha256(text),
            metadata={
                "chunk_id": chunk_id,
                "source_file": str(row["source_file"] or ""),
                "title": str(row["title"] or ""),
                "url": str(row["url"] or ""),
            },
        )


def _iter_wikipedia_units(conn: sqlite3.Connection) -> Iterator[CorpusUnit]:
    """Yield one ``CorpusUnit`` per Wikipedia article.

    Pre-#1553 this iterator inlined a token-window chunker
    (``chunk_wikipedia_article``, 450t/50t). Step 1 of #1553 moves
    chunking out to ``wiki.chunking`` so the policy is uniform across
    all corpora and applied centrally inside ``load_corpus_units``.
    The iterator now yields whole articles; the chunker splits them.
    """

    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT id, title, text, url
        FROM wikipedia
        ORDER BY id
        """
    ).fetchall()
    for row in rows:
        title = str(row["title"] or "")
        text = str(row["text"] or "")
        yield CorpusUnit(
            unit_key=f"wikipedia:{title}",
            corpus="wikipedia",
            parent_key=title,
            text=text,
            text_sha256=text_sha256(text),
            metadata={
                "title": title,
                "url": str(row["url"] or ""),
            },
        )


def _iter_ukrainian_wiki_units(conn: sqlite3.Connection) -> Iterator[CorpusUnit]:
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                passage_id,
                article_slug,
                article_title,
                article_path,
                section_path,
                paragraph_start,
                paragraph_end,
                text
            FROM ukrainian_wiki
            ORDER BY article_slug, paragraph_start, id
            """
        ).fetchall()
    except sqlite3.OperationalError:
        return

    for row in rows:
        text = str(row["text"] or "")
        yield CorpusUnit(
            unit_key=f"ukrainian_wiki:{row['passage_id']}",
            corpus="ukrainian_wiki",
            parent_key=str(row["article_slug"] or ""),
            text=text,
            text_sha256=text_sha256(text),
            metadata={
                "passage_id": str(row["passage_id"] or ""),
                "article_slug": str(row["article_slug"] or ""),
                "article_title": str(row["article_title"] or ""),
                "article_path": str(row["article_path"] or ""),
                "section_path": str(row["section_path"] or ""),
                "paragraph_start": int(row["paragraph_start"] or 0),
                "paragraph_end": int(row["paragraph_end"] or 0),
            },
        )


CORPUS_UNIT_LOADERS: dict[str, Callable[[sqlite3.Connection], Iterator[CorpusUnit]]] = {
    "textbook_sections": _iter_textbook_units,
    "modern_literary": _iter_modern_literary_units,
    "archaic_literary": _iter_archaic_literary_units,
    "external": _iter_external_units,
    "wikipedia": _iter_wikipedia_units,
    "ukrainian_wiki": _iter_ukrainian_wiki_units,
}


def load_corpus_units(corpus: str, *, db_path: Path = DEFAULT_DB_PATH) -> list[CorpusUnit]:
    """Load all units for ``corpus``, applying the central chunking
    policy from ``wiki.chunking``.

    Pre-#1553 this returned whatever the iterator yielded. Step 1
    centralizes chunking: each raw unit is fed to ``chunk_text``,
    which respects the ``ChunkingPolicy`` for ``corpus``. NO_CHUNK
    policies pass units through unchanged (preserves the existing
    ingest-chunked behavior of literary / ukrainian_wiki). Active
    policies emit ``unit_key:chunk_N`` sub-units with
    ``chunk_index`` / ``chunk_count`` / ``parent_unit_key`` metadata
    so post-rerank parent expansion can group siblings back together.
    """

    loader = CORPUS_UNIT_LOADERS.get(corpus)
    if loader is None:
        raise ValueError(f"unsupported corpus: {corpus}")

    policy = policy_for(corpus)
    tokenizer = _get_tokenizer()

    conn = sqlite3.connect(str(db_path))
    try:
        units: list[CorpusUnit] = []
        for raw_unit in loader(conn):
            for piece in chunk_text(raw_unit.text, policy=policy, tokenizer=tokenizer):
                if not piece.text:
                    continue
                # NO_CHUNK / single-chunk: yield original unit
                # unchanged (one-piece-with-chunk_index-0 contract).
                if not piece.extra_metadata:
                    if piece.text == raw_unit.text:
                        units.append(raw_unit)
                    else:
                        units.append(_with_text(raw_unit, piece.text))
                    continue
                # Active policy: synthesize a sub-unit.
                metadata = {
                    **raw_unit.metadata,
                    "parent_unit_key": raw_unit.unit_key,
                    **piece.extra_metadata,
                }
                units.append(
                    CorpusUnit(
                        unit_key=f"{raw_unit.unit_key}:chunk_{piece.chunk_index}",
                        corpus=raw_unit.corpus,
                        parent_key=raw_unit.parent_key or raw_unit.unit_key,
                        text=piece.text,
                        text_sha256=text_sha256(piece.text),
                        metadata=metadata,
                    )
                )
        return units
    finally:
        conn.close()


def _assert_units_fit_index_window(
    units: list[CorpusUnit],
    *,
    corpus: str,
    max_length: int | None = None,
) -> None:
    """Validator gate (#1553 step 3): no post-chunk unit may exceed
    ``INDEX_MAX_LENGTH`` tokens.

    Pre-#1553 the tokenizer emitted a 22,174 > 8192 warning during
    a live build because un-chunked textbook sections fed straight
    into a 512-token encoder window. The chunker added in step 1
    is supposed to prevent that, but a misconfigured policy (e.g.
    ``target_tokens=2000`` while ``INDEX_MAX_LENGTH=512``) would
    silently re-introduce the bug. This gate makes the failure
    loud at encode time instead of buried in tokenizer stderr.

    Skipped silently if a corpus has units > max_length AND its
    chunking policy says ``target_tokens == 0`` (no-chunk policy
    intentionally accepts whatever the source row length is — that
    behavior is preserved for the literary corpora where re-chunking
    would invalidate 137K vectors for marginal gain).
    """

    cap = INDEX_MAX_LENGTH if max_length is None else max_length
    policy = policy_for(corpus)
    if policy.target_tokens == 0:
        # NO_CHUNK policy: tolerate >cap units. The encoder will
        # truncate per its own ``truncation=True`` setting, which is
        # the intended behavior for these pre-chunked corpora.
        return

    tokenizer = _get_tokenizer()
    over = []
    for unit in units:
        token_count = len(
            tokenizer.encode(unit.text, add_special_tokens=False, truncation=False)
        )
        if token_count > cap:
            over.append((unit.unit_key, token_count))
            if len(over) >= 5:
                break

    if over:
        examples = ", ".join(f"{key} ({count}t)" for key, count in over)
        raise ValueError(
            f"chunking policy {policy.version_id!r} for corpus {corpus!r} "
            f"emitted {len(over)}+ units exceeding INDEX_MAX_LENGTH={cap}. "
            f"Examples: {examples}. Either bump INDEX_MAX_LENGTH or lower "
            f"the policy's target_tokens (and its version_id)."
        )


def _with_text(unit: CorpusUnit, text: str) -> CorpusUnit:
    """Return a copy of ``unit`` with replaced ``text`` and recomputed
    ``text_sha256``. Used when a NO_CHUNK policy emits stripped text
    that differs from the original by whitespace only."""

    return CorpusUnit(
        unit_key=unit.unit_key,
        corpus=unit.corpus,
        parent_key=unit.parent_key,
        text=text,
        text_sha256=text_sha256(text),
        metadata=unit.metadata,
    )


def _chunked(items: Sequence[CorpusUnit], size: int) -> Iterator[list[CorpusUnit]]:
    for start in range(0, len(items), size):
        yield list(items[start:start + size])


def plan_shard_groups(corpus: str, units: Sequence[CorpusUnit]) -> list[list[CorpusUnit]]:
    if not units:
        return []

    if corpus == "textbook_sections":
        return [list(units)]

    if corpus in {"modern_literary", "archaic_literary"}:
        grouped: dict[str, list[CorpusUnit]] = defaultdict(list)
        for unit in units:
            grouped[str(unit.metadata.get("source_file") or unit.parent_key or "unknown")].append(unit)
        planned: list[list[CorpusUnit]] = []
        for source_file in sorted(grouped):
            for batch in _chunked(grouped[source_file], LITERARY_SHARD_LIMIT):
                planned.append(batch)
        return planned

    return [batch for batch in _chunked(units, SEQUENTIAL_SHARD_LIMIT)]


def cold_encode_corpus(
    corpus: str,
    *,
    db_path: Path = DEFAULT_DB_PATH,
    manifest_db: Path = DEFAULT_MANIFEST_DB,
    resume: bool = False,
    encoder=None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Incrementally encode a corpus and append new shards to the manifest."""

    started = time.perf_counter()
    units = load_corpus_units(corpus, db_path=db_path)
    _assert_units_fit_index_window(units, corpus=corpus)
    manifest = EmbeddingManifest(manifest_db)
    encoder_config = current_encoder_config(corpus)
    try:
        new_keys, stale_keys = filter_new_or_changed(
            manifest,
            corpus=corpus,
            candidates=[(unit.unit_key, unit.text_sha256) for unit in units],
            expected_config=encoder_config,
        )
        pending_keys = set(new_keys) | set(stale_keys)

        if not pending_keys:
            return {
                "corpus": corpus,
                "resume": resume,
                "status": "up_to_date",
                "total_units": len(units),
                "encoded_units": 0,
                "new_units": 0,
                "stale_units": 0,
                "total_shards": len(manifest.shard_map_for_corpus(corpus)),
                "total_time_s": round(time.perf_counter() - started, 3),
            }

        for unit_key in stale_keys:
            manifest.mark_stale(unit_key)

        encoder = encoder or _get_encoder()
        groups = plan_shard_groups(
            corpus,
            [unit for unit in units if unit.unit_key in pending_keys],
        )
        written = 0
        for group in groups:
            if not group:
                continue
            vectors = encode_texts(
                [unit.text for unit in group],
                encoder=encoder,
                max_length=INDEX_MAX_LENGTH,
                corpus=corpus,
                progress_callback=progress_callback,
            )
            shard_id = append_shard(
                manifest,
                corpus=corpus,
                vectors=vectors,
                unit_specs=[
                    UnitSpecInput(
                        unit_key=unit.unit_key,
                        parent_key=unit.parent_key,
                        text_sha256=unit.text_sha256,
                    )
                    for unit in group
                ],
                encoder_config=encoder_config,
            )
            invalidate_corpus_index(corpus, manifest_db=manifest_db)
            written += 1
            if progress_callback is not None:
                progress_callback(
                    {
                        "event": "shard_written",
                        "corpus": corpus,
                        "shard_id": shard_id,
                        "units": len(group),
                        "elapsed_s": round(time.perf_counter() - started, 3),
                    }
                )

        summary = {
            "corpus": corpus,
            "resume": resume,
            "status": "encoded",
            "total_units": len(units),
            "encoded_units": len(pending_keys),
            "new_units": len(new_keys),
            "stale_units": len(stale_keys),
            "total_shards": len(manifest.shard_map_for_corpus(corpus)),
            "total_time_s": round(time.perf_counter() - started, 3),
            "shards_written": written,
        }
        if progress_callback is not None:
            progress_callback(
                {
                    "event": "corpus_done",
                    "corpus": corpus,
                    "total_units": summary["total_units"],
                    "total_shards": summary["total_shards"],
                    "total_time_s": summary["total_time_s"],
                }
            )
        return summary
    finally:
        manifest.close()
