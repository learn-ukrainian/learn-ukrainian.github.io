#!/usr/bin/env python3
"""Ingest Антоненко-Давидович and Грінченко into Qdrant.

Creates two new collections:
- style_guide: Антоненко-Давидович «Як ми говоримо» (279 entries)
- grinchenko: Грінченко «Словарь» (67K entries)

Usage:
    .venv/bin/python scripts/rag/ingest_style_dictionaries.py --antonenko
    .venv/bin/python scripts/rag/ingest_style_dictionaries.py --grinchenko
    .venv/bin/python scripts/rag/ingest_style_dictionaries.py --all

Issue: #1022
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import BGE_M3_DENSE_DIM, QDRANT_HOST, QDRANT_REST_PORT

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANTONENKO_CHUNKS = PROJECT_ROOT / "data" / "antonenko-davydovych" / "chunks.jsonl"
GRINCHENKO_CHUNKS = PROJECT_ROOT / "data" / "grinchenko" / "chunks.jsonl"

STYLE_COLLECTION = "style_guide"
GRINCHENKO_COLLECTION = "grinchenko_dict"

BATCH_SIZE = 500  # Larger batches — model loaded once, embedding is the bottleneck


def get_client():
    from qdrant_client import QdrantClient
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_REST_PORT, timeout=60)


def ensure_collection(client, name: str):
    """Create collection if it doesn't exist."""
    from qdrant_client.models import Distance, VectorParams
    collections = [c.name for c in client.get_collections().collections]
    if name in collections:
        print(f"  Collection '{name}' already exists")
        return
    client.create_collection(
        collection_name=name,
        vectors_config={
            "dense": VectorParams(size=BGE_M3_DENSE_DIM, distance=Distance.COSINE),
        },
    )
    print(f"  ✅ Created collection '{name}'")


def load_chunks(path: Path) -> list[dict]:
    chunks = []
    for line in path.read_text("utf-8").splitlines():
        if line.strip():
            chunks.append(json.loads(line))
    return chunks


def get_text_encoder():
    """Get the shared TextEncoder from the RAG module."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from rag.embed import TextEncoder
    print("  Loading TextEncoder (same as ingest.py)...")
    return TextEncoder()


def ingest_collection(client, collection_name: str, chunks: list[dict], text_field: str, encoder):
    """Ingest chunks into a Qdrant collection using the shared TextEncoder."""
    from qdrant_client.models import PointStruct

    ensure_collection(client, collection_name)

    # Check for resume — skip if already fully ingested
    existing = client.count(collection_name=collection_name).count
    total = len(chunks)
    if existing >= total:
        print(f"  ✅ Collection '{collection_name}' already has {existing} points (>= {total}). Skipping.")
        return

    if existing > 0:
        print(f"  ⚠️  Collection has {existing}/{total} points — re-ingesting all (upsert is safe)")

    print(f"  Ingesting {total} entries into '{collection_name}'...")

    # Encode ALL texts at once (encoder handles internal batching efficiently)
    texts = [c.get(text_field, c.get("text", "")) for c in chunks]
    print(f"  Embedding {len(texts)} texts (this may take a few minutes)...")
    embeddings = encoder.encode(texts, batch_size=64)
    dense_vecs = embeddings["dense_vecs"]
    print(f"  ✅ Embedding complete ({len(dense_vecs)} vectors)")

    # Build all points
    points = []
    for i, (chunk, vec) in enumerate(zip(chunks, dense_vecs, strict=True)):
        chunk_id = chunk.get("id", f"chunk-{i}")
        point_id = int(hashlib.md5(chunk_id.encode()).hexdigest()[:15], 16)
        payload = {
            "chunk_id": chunk_id,
            "word": chunk.get("word", ""),
            "text": chunk.get(text_field, chunk.get("text", "")),
            "source": chunk.get("source", collection_name),
        }
        if "section" in chunk:
            payload["section"] = chunk["section"]
        if "definition" in chunk:
            payload["definition"] = chunk["definition"]
        points.append(PointStruct(id=point_id, vector={"dense": vec.tolist()}, payload=payload))

    # Upload in batches
    print(f"  Uploading {len(points)} points to Qdrant...")
    for batch_start in range(0, len(points), BATCH_SIZE):
        batch = points[batch_start:batch_start + BATCH_SIZE]
        client.upsert(collection_name=collection_name, points=batch)
        uploaded = min(batch_start + BATCH_SIZE, len(points))
        print(f"    Uploaded {uploaded}/{len(points)}")

    count = client.count(collection_name=collection_name).count
    print(f"  ✅ Collection '{collection_name}': {count} points total")


def main():
    parser = argparse.ArgumentParser(description="Ingest style/dictionary data into Qdrant")
    parser.add_argument("--antonenko", action="store_true", help="Ingest Антоненко-Давидович")
    parser.add_argument("--grinchenko", action="store_true", help="Ingest Грінченко")
    parser.add_argument("--all", action="store_true", help="Ingest both")
    args = parser.parse_args()

    if not (args.antonenko or args.grinchenko or args.all):
        parser.print_help()
        sys.exit(1)

    client = get_client()
    encoder = get_text_encoder()

    if args.antonenko or args.all:
        print("\n📚 Антоненко-Давидович «Як ми говоримо»")
        chunks = load_chunks(ANTONENKO_CHUNKS)
        ingest_collection(client, STYLE_COLLECTION, chunks, text_field="text", encoder=encoder)

    if args.grinchenko or args.all:
        print("\n📖 Грінченко «Словарь української мови»")
        chunks = load_chunks(GRINCHENKO_CHUNKS)
        ingest_collection(client, GRINCHENKO_COLLECTION, chunks, text_field="definition", encoder=encoder)


if __name__ == "__main__":
    main()
