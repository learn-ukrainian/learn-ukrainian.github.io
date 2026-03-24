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
SUM11_CHUNKS = PROJECT_ROOT / "data" / "sum11" / "chunks.jsonl"
SUM11_COLLECTION = "sum11"
BALLA_CHUNKS = PROJECT_ROOT / "data" / "balla-en-uk" / "chunks.jsonl"
BALLA_COLLECTION = "balla_en_uk"
FRAZ_CHUNKS = PROJECT_ROOT / "data" / "frazeolohichnyi" / "chunks.jsonl"
FRAZ_COLLECTION = "frazeolohichnyi"
WIKT_CHUNKS = PROJECT_ROOT / "data" / "wiktionary" / "chunks.jsonl"
WIKT_COLLECTION = "wiktionary_uk"
DMK_CHUNKS = PROJECT_ROOT / "data" / "dmklinger-uk-en" / "chunks.jsonl"
DMK_COLLECTION = "dmklinger_uk_en"
UKRNET_CHUNKS = PROJECT_ROOT / "data" / "ukrajinet" / "chunks.jsonl"
UKRNET_COLLECTION = "ukrajinet"

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
        print(f"  ⚠️  Collection has {existing}/{total} points — resuming from chunk {existing}")
        chunks = chunks[existing:]
        total_remaining = len(chunks)
        if total_remaining == 0:
            print(f"  ✅ Nothing to resume — all {total} points already ingested.")
            return
        print(f"  Resuming: {total_remaining} entries remaining")
    else:
        total_remaining = total

    print(f"  Ingesting {total_remaining} entries into '{collection_name}'...")

    # Process in mega-batches to allow resume on interruption
    EMBED_BATCH = BATCH_SIZE
    for batch_start in range(0, total_remaining, EMBED_BATCH):
        batch_chunks = chunks[batch_start:batch_start + EMBED_BATCH]
        batch_num = batch_start // EMBED_BATCH + 1
        total_batches = (total_remaining + EMBED_BATCH - 1) // EMBED_BATCH
        print(f"  Batch {batch_num}/{total_batches}: embedding {len(batch_chunks)} entries...", flush=True)

        texts = [c.get(text_field, c.get("text", "")) for c in batch_chunks]
        embeddings = encoder.encode(texts, batch_size=16)
        dense_vecs = embeddings["dense_vecs"]

        points = []
        for i, (chunk, vec) in enumerate(zip(batch_chunks, dense_vecs, strict=True)):
            global_idx = existing + batch_start + i
            chunk_id = chunk.get("id", f"chunk-{global_idx}")
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

        # Upload this batch immediately
        client.upsert(collection_name=collection_name, points=points)
        done = existing + batch_start + len(batch_chunks)
        print(f"    ✅ Uploaded — {done}/{total} total points")

    count = client.count(collection_name=collection_name).count
    print(f"  ✅ Collection '{collection_name}': {count} points total")


def main():
    parser = argparse.ArgumentParser(description="Ingest dictionaries into Qdrant")
    parser.add_argument("--antonenko", action="store_true", help="Ingest Антоненко-Давидович (279)")
    parser.add_argument("--grinchenko", action="store_true", help="Ingest Грінченко (67K)")
    parser.add_argument("--sum11", action="store_true", help="Ingest СУМ-11 (127K)")
    parser.add_argument("--balla", action="store_true", help="Ingest Балла EN→UK (79K)")
    parser.add_argument("--frazeolohichnyi", action="store_true", help="Ingest Фразеологічний (25K)")
    parser.add_argument("--wiktionary", action="store_true", help="Ingest Вікісловник (50K)")
    parser.add_argument("--dmklinger", action="store_true", help="Ingest dmklinger UK→EN (30K)")
    parser.add_argument("--ukrajinet", action="store_true", help="Ingest Ukrajinet WordNet (122K)")
    parser.add_argument("--all", action="store_true", help="Ingest all dictionaries")
    args = parser.parse_args()

    any_selected = any([args.antonenko, args.grinchenko, args.sum11, args.balla, args.frazeolohichnyi, args.wiktionary, args.dmklinger, args.ukrajinet, args.all])
    if not any_selected:
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

    if args.sum11 or args.all:
        print("\n📖 СУМ-11 «Словник української мови в 11 томах»")
        chunks = load_chunks(SUM11_CHUNKS)
        ingest_collection(client, SUM11_COLLECTION, chunks, text_field="text", encoder=encoder)

    if args.balla or args.all:
        print("\n📖 Балла «Англо-український словник»")
        chunks = load_chunks(BALLA_CHUNKS)
        ingest_collection(client, BALLA_COLLECTION, chunks, text_field="text", encoder=encoder)

    if args.frazeolohichnyi or args.all:
        print("\n📖 Фразеологічний словник")
        chunks = load_chunks(FRAZ_CHUNKS)
        ingest_collection(client, FRAZ_COLLECTION, chunks, text_field="text", encoder=encoder)

    if args.wiktionary or args.all:
        print("\n📖 Вікісловник (Ukrainian Wiktionary)")
        chunks = load_chunks(WIKT_CHUNKS)
        ingest_collection(client, WIKT_COLLECTION, chunks, text_field="text", encoder=encoder)

    if args.dmklinger or args.all:
        print("\n📖 dmklinger UK→EN dictionary")
        chunks = load_chunks(DMK_CHUNKS)
        ingest_collection(client, DMK_COLLECTION, chunks, text_field="text", encoder=encoder)

    if args.ukrajinet or args.all:
        print("\n📖 Ukrajinet WordNet (synonyms)")
        chunks = load_chunks(UKRNET_CHUNKS)
        ingest_collection(client, UKRNET_COLLECTION, chunks, text_field="text", encoder=encoder)


if __name__ == "__main__":
    main()
