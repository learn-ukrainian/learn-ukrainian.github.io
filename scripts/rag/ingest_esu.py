"""Ingest ESU encyclopedia chunks into Qdrant for RAG search.

Reads the chunked JSONL produced by crawl_esu.py, embeds with BGE-M3
(dense + sparse), and upserts into the esu_encyclopedia collection.

Usage:
    # Full ingest (embed + upsert)
    .venv/bin/python scripts/rag/ingest_esu.py

    # Recreate collection from scratch
    .venv/bin/python scripts/rag/ingest_esu.py --recreate

    # Dry run (count chunks, don't embed or ingest)
    .venv/bin/python scripts/rag/ingest_esu.py --dry-run

    # Custom batch size (lower if running out of memory)
    .venv/bin/python scripts/rag/ingest_esu.py --batch-size 16

Requires: crawl_esu.py to have produced data/esu/chunks.jsonl
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import BGE_M3_DENSE_DIM, DATA_DIR, ESU_COLLECTION, QDRANT_HOST, QDRANT_REST_PORT

ESU_DIR = DATA_DIR / "esu"
CHUNKS_PATH = ESU_DIR / "chunks.jsonl"


def ensure_collection(client, recreate: bool = False):
    """Create or verify the esu_encyclopedia Qdrant collection."""
    from qdrant_client.models import (
        Distance,
        PayloadSchemaType,
        SparseIndexParams,
        SparseVectorParams,
        VectorParams,
    )

    exists = client.collection_exists(ESU_COLLECTION)
    if exists and not recreate:
        info = client.get_collection(ESU_COLLECTION)
        print(f"[ingest] Collection '{ESU_COLLECTION}' exists with {info.points_count} points")
        return
    if exists and recreate:
        print(f"[ingest] Recreating collection '{ESU_COLLECTION}'...")
        client.delete_collection(ESU_COLLECTION)

    print(f"[ingest] Creating collection '{ESU_COLLECTION}'...")
    client.create_collection(
        collection_name=ESU_COLLECTION,
        vectors_config={
            "dense": VectorParams(size=BGE_M3_DENSE_DIM, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False)),
        },
    )
    for field, schema_type in [
        ("title", PayloadSchemaType.KEYWORD),
        ("letter", PayloadSchemaType.KEYWORD),
        ("author", PayloadSchemaType.KEYWORD),
        ("article_id", PayloadSchemaType.INTEGER),
    ]:
        client.create_payload_index(
            collection_name=ESU_COLLECTION,
            field_name=field,
            field_schema=schema_type,
        )
    # Full-text index on keywords for filtered search
    client.create_payload_index(
        collection_name=ESU_COLLECTION,
        field_name="keywords",
        field_schema=PayloadSchemaType.TEXT,
    )
    print("[ingest] Collection created with indexes.")


def load_chunks() -> list[dict]:
    """Load chunks from JSONL file."""
    if not CHUNKS_PATH.exists():
        print(f"[error] Chunks file not found: {CHUNKS_PATH}")
        print("  Run crawl_esu.py first to crawl and chunk articles.")
        sys.exit(1)

    chunks = []
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return chunks


def chunk_id_to_point_id(chunk_id: str) -> int:
    """Deterministic point ID from chunk_id (same scheme as literary ingest)."""
    return int(hashlib.sha256(chunk_id.encode()).hexdigest()[:15], 16)


def get_existing_point_ids(client) -> set[int]:
    """Get all point IDs already in the collection (for resume support)."""
    existing = set()
    if not client.collection_exists(ESU_COLLECTION):
        return existing
    info = client.get_collection(ESU_COLLECTION)
    if info.points_count == 0:
        return existing

    # Scroll through all points, fetching only IDs (no vectors/payload)
    offset = None
    while True:
        results, offset = client.scroll(
            collection_name=ESU_COLLECTION,
            limit=1000,
            offset=offset,
            with_payload=False,
            with_vectors=False,
        )
        for point in results:
            existing.add(point.id)
        if offset is None:
            break

    return existing


def ingest(client, chunks: list[dict], batch_size: int = 32, resume: bool = True,
           device: str | None = None):
    """Embed chunks with BGE-M3 and upsert into Qdrant."""
    from qdrant_client.models import PointStruct, SparseVector

    from rag.embed import TextEncoder

    # Resume support: skip chunks already in Qdrant
    if resume:
        existing_ids = get_existing_point_ids(client)
        if existing_ids:
            before = len(chunks)
            chunks = [c for c in chunks if chunk_id_to_point_id(c["chunk_id"]) not in existing_ids]
            print(f"[resume] {before - len(chunks)} chunks already ingested, {len(chunks)} remaining")
            if not chunks:
                print("[resume] Nothing to do — all chunks already ingested.")
                return 0

    encoder = TextEncoder(device=device)
    total_ingested = 0

    # Sort by text length to minimize padding waste within batches.
    # Short chunks get batched together and pad to ~100 tokens, not 512.
    chunks.sort(key=lambda c: len(c["text"]))

    # Process in batches to manage memory
    for start in range(0, len(chunks), batch_size):
        batch_chunks = chunks[start : start + batch_size]
        texts = [c["text"] for c in batch_chunks]

        # Embed
        embeddings = encoder.encode(texts, batch_size=batch_size)
        dense_vecs = embeddings["dense_vecs"]
        sparse_weights = embeddings["lexical_weights"]

        # Build points
        points = []
        for i, chunk in enumerate(batch_chunks):
            # Sparse vector handling (same as literary ingest)
            sw = sparse_weights[i]
            if isinstance(sw, dict):
                idx_map: dict[int, float] = {}
                for k, v in sw.items():
                    idx = int(k) if isinstance(k, (int, float)) else hash(k) % (2**31)
                    idx_map[idx] = idx_map.get(idx, 0.0) + v
                indices = list(idx_map.keys())
                values = list(idx_map.values())
            else:
                indices, values = [], []

            payload = {
                "text": chunk["text"],
                "chunk_id": chunk["chunk_id"],
                "title": chunk.get("title", ""),
                "article_id": chunk.get("article_id", 0),
                "url": chunk.get("url", ""),
                "letter": chunk.get("letter", ""),
                "author": chunk.get("author", ""),
                "keywords": chunk.get("keywords", ""),
                "token_count": chunk.get("token_count", 0),
            }

            point = PointStruct(
                id=chunk_id_to_point_id(chunk["chunk_id"]),
                vector={
                    "dense": dense_vecs[i].tolist(),
                    "sparse": SparseVector(indices=indices, values=values),
                },
                payload=payload,
            )
            points.append(point)

        # Upsert with retry
        for attempt in range(3):
            try:
                client.upsert(collection_name=ESU_COLLECTION, points=points)
                break
            except Exception as e:
                if attempt < 2 and ("408" in str(e) or "timeout" in str(e).lower()):
                    print(f"  [retry] Upsert timeout, attempt {attempt + 2}/3...")
                    time.sleep(2)
                else:
                    raise

        total_ingested += len(points)
        if (start + batch_size) % (batch_size * 10) == 0 or start + batch_size >= len(chunks):
            print(f"  [{start + len(batch_chunks)}/{len(chunks)}] ingested {total_ingested} chunks")

    return total_ingested


def main():
    parser = argparse.ArgumentParser(description="Ingest ESU encyclopedia into Qdrant")
    parser.add_argument("--recreate", action="store_true",
                       help="Recreate Qdrant collection from scratch")
    parser.add_argument("--dry-run", action="store_true",
                       help="Count chunks without embedding or ingesting")
    parser.add_argument("--batch-size", type=int, default=32,
                       help="Embedding batch size (default 32)")
    parser.add_argument("--no-resume", action="store_true",
                       help="Don't skip already-ingested chunks (re-embed everything)")
    parser.add_argument("--device", type=str, default=None,
                       help="Torch device for embedding (e.g., 'mps', 'cpu', 'cuda')")
    args = parser.parse_args()

    # Load chunks
    chunks = load_chunks()
    print(f"[ingest] Loaded {len(chunks)} chunks from {CHUNKS_PATH}")

    if args.dry_run:
        # Stats only
        titles = set(c["title"] for c in chunks)
        letters = set(c["letter"] for c in chunks)
        tokens = [c["token_count"] for c in chunks]
        print(f"  Articles: {len(titles)}")
        print(f"  Letters: {sorted(letters)}")
        print(f"  Tokens: min={min(tokens)}, median={sorted(tokens)[len(tokens)//2]}, max={max(tokens)}")
        return

    # Connect to Qdrant
    from qdrant_client import QdrantClient
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_REST_PORT,
                         prefer_grpc=False, timeout=300)

    ensure_collection(client, recreate=args.recreate)

    # Ingest (resumable by default — safe to Ctrl+C and restart)
    print(f"[ingest] Embedding and ingesting {len(chunks)} chunks...")
    ingest(client, chunks, batch_size=args.batch_size, resume=not args.no_resume,
                   device=args.device)

    # Verify
    info = client.get_collection(ESU_COLLECTION)
    print(f"\n[ingest] Done. {ESU_COLLECTION}: {info.points_count} points, status: {info.status}")


if __name__ == "__main__":
    main()
