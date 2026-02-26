"""CLI query tool for the RAG pipeline.

Usage:
    # Hybrid text search
    .venv/bin/python scripts/rag/query.py text "як утворюється минулий час"
    .venv/bin/python scripts/rag/query.py text "загадка про тварин" --grade 3 --limit 3

    # Image search (text-to-image via SigLIP)
    .venv/bin/python scripts/rag/query.py images "яблуко"
    .venv/bin/python scripts/rag/query.py images "ілюстрація до букви А" --grade 1

    # Get surrounding context for a chunk
    .venv/bin/python scripts/rag/query.py context <chunk_id> --window 2

    # Collection stats
    .venv/bin/python scripts/rag/query.py stats
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import (
    BGE_M3_DENSE_DIM,
    IMAGE_COLLECTION,
    QDRANT_GRPC_PORT,
    QDRANT_HOST,
    SIGLIP_DIM,
    TEXT_COLLECTION,
)

# Module-level singletons (lazy-loaded)
_qdrant_client = None
_text_encoder = None
_image_encoder = None


def get_client():
    global _qdrant_client
    if _qdrant_client is None:
        from qdrant_client import QdrantClient
        _qdrant_client = QdrantClient(
            host=QDRANT_HOST, grpc_port=QDRANT_GRPC_PORT,
            prefer_grpc=True, check_compatibility=False,
        )
    return _qdrant_client


def get_text_encoder():
    global _text_encoder
    if _text_encoder is None:
        from rag.embed import TextEncoder
        _text_encoder = TextEncoder()
    return _text_encoder


def get_image_encoder():
    global _image_encoder
    if _image_encoder is None:
        from rag.embed import ImageEncoder
        _image_encoder = ImageEncoder()
    return _image_encoder


def build_filter(grade: int | None = None, subject: str | None = None,
                 trust_tier: int | None = None, author: str | None = None):
    """Build Qdrant filter from optional parameters."""
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    conditions = []
    if grade is not None:
        conditions.append(FieldCondition(key="grade", match=MatchValue(value=grade)))
    if subject:
        conditions.append(FieldCondition(key="subject", match=MatchValue(value=subject)))
    if trust_tier is not None:
        conditions.append(FieldCondition(key="trust_tier", match=MatchValue(value=trust_tier)))
    if author:
        conditions.append(FieldCondition(key="author", match=MatchValue(value=author)))

    return Filter(must=conditions) if conditions else None


def search_text(query: str, grade: int | None = None, subject: str | None = None,
                trust_tier: int | None = None, limit: int = 5) -> list[dict]:
    """Hybrid text search combining dense + sparse scores."""
    from qdrant_client.models import (
        FusionQuery,
        Prefetch,
        QueryRequest,
        SparseVector,
    )

    client = get_client()
    encoder = get_text_encoder()

    # Encode query
    result = encoder.encode([query])
    dense_vec = result["dense_vecs"][0].tolist()
    sparse_w = result["lexical_weights"][0]

    if isinstance(sparse_w, dict):
        sparse_indices = [int(k) if isinstance(k, (int, float)) else hash(k) % (2**31) for k in sparse_w.keys()]
        sparse_values = list(sparse_w.values())
    else:
        sparse_indices, sparse_values = [], []

    qfilter = build_filter(grade, subject, trust_tier)

    # Hybrid search via Reciprocal Rank Fusion
    results = client.query_points(
        collection_name=TEXT_COLLECTION,
        prefetch=[
            Prefetch(
                query=dense_vec,
                using="dense",
                limit=limit * 3,
                filter=qfilter,
            ),
            Prefetch(
                query=SparseVector(indices=sparse_indices, values=sparse_values),
                using="sparse",
                limit=limit * 3,
                filter=qfilter,
            ),
        ],
        query=FusionQuery(fusion="rrf"),
        limit=limit,
        with_payload=True,
    )

    hits = []
    for point in results.points:
        payload = point.payload or {}
        hits.append({
            "score": point.score if hasattr(point, 'score') else 0,
            "chunk_id": payload.get("chunk_id", ""),
            "text": payload.get("text", "")[:500],
            "section_title": payload.get("section_title", ""),
            "grade": payload.get("grade", 0),
            "author": payload.get("author", ""),
            "page": payload.get("page_start", ""),
            "trust_tier": payload.get("trust_tier", 0),
        })
    return hits


def search_images(query: str, grade: int | None = None, limit: int = 5) -> list[dict]:
    """Image search via Ukrainian text query (SigLIP text-to-image)."""
    client = get_client()
    encoder = get_image_encoder()

    query_vec = encoder.encode_text([query])[0].tolist()
    qfilter = build_filter(grade)

    results = client.query_points(
        collection_name=IMAGE_COLLECTION,
        query=query_vec,
        limit=limit,
        query_filter=qfilter,
        with_payload=True,
    )

    hits = []
    for point in results.points:
        payload = point.payload or {}
        hits.append({
            "score": point.score if hasattr(point, 'score') else 0,
            "image_id": payload.get("image_id", ""),
            "image_path": payload.get("image_path", ""),
            "page": payload.get("page", 0),
            "grade": payload.get("grade", 0),
            "author": payload.get("author", ""),
            "width": payload.get("width", 0),
            "height": payload.get("height", 0),
        })
    return hits


def get_chunk_context(chunk_id: str, window: int = 2) -> list[dict]:
    """Get surrounding chunks for context.

    Finds the chunk by ID, then retrieves nearby chunks from the same PDF
    based on sequential chunk numbering.
    """
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    client = get_client()

    # Parse chunk_id to find pdf_stem and sequence number
    # Format: {pdf_stem}_s{NNNN}
    parts = chunk_id.rsplit("_s", 1)
    if len(parts) != 2:
        return [{"error": f"Invalid chunk_id format: {chunk_id}"}]

    pdf_stem = parts[0]
    try:
        seq_num = int(parts[1])
    except ValueError:
        return [{"error": f"Invalid sequence number in chunk_id: {chunk_id}"}]

    # Search for chunks from same PDF with nearby sequence numbers
    nearby_ids = []
    for offset in range(-window, window + 1):
        nearby_id = f"{pdf_stem}_s{seq_num + offset:04d}"
        nearby_ids.append(nearby_id)

    # Search by chunk_id in payload
    results = client.scroll(
        collection_name=TEXT_COLLECTION,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="pdf_stem", match=MatchValue(value=pdf_stem)),
            ]
        ),
        limit=100,
        with_payload=True,
    )

    # Filter to nearby chunks and sort
    context_chunks = []
    for point in results[0]:
        payload = point.payload or {}
        cid = payload.get("chunk_id", "")
        if cid in nearby_ids:
            context_chunks.append({
                "chunk_id": cid,
                "text": payload.get("text", ""),
                "section_title": payload.get("section_title", ""),
                "is_target": cid == chunk_id,
            })

    # Sort by chunk_id (which is sequential)
    context_chunks.sort(key=lambda x: x["chunk_id"])
    return context_chunks


def collection_stats() -> dict:
    """Get stats for all RAG collections."""
    client = get_client()
    stats = {}
    for coll_name in [TEXT_COLLECTION, IMAGE_COLLECTION]:
        try:
            info = client.get_collection(coll_name)
            stats[coll_name] = {
                "points_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": str(info.status),
            }
        except Exception as e:
            stats[coll_name] = {"error": str(e)}
    return stats


def main():
    parser = argparse.ArgumentParser(description="Query the RAG pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Text search
    text_parser = subparsers.add_parser("text", help="Hybrid text search")
    text_parser.add_argument("query", help="Search query in Ukrainian")
    text_parser.add_argument("--grade", type=int, help="Filter by grade")
    text_parser.add_argument("--subject", type=str, help="Filter by subject")
    text_parser.add_argument("--trust-tier", type=int, help="Filter by trust tier (1 or 2)")
    text_parser.add_argument("--limit", type=int, default=5, help="Number of results")

    # Image search
    img_parser = subparsers.add_parser("images", help="Text-to-image search")
    img_parser.add_argument("query", help="Search query in Ukrainian")
    img_parser.add_argument("--grade", type=int, help="Filter by grade")
    img_parser.add_argument("--limit", type=int, default=5, help="Number of results")

    # Context
    ctx_parser = subparsers.add_parser("context", help="Get surrounding chunks")
    ctx_parser.add_argument("chunk_id", help="Chunk ID")
    ctx_parser.add_argument("--window", type=int, default=2, help="Number of chunks before/after")

    # Stats
    subparsers.add_parser("stats", help="Collection statistics")

    args = parser.parse_args()

    if args.command == "text":
        hits = search_text(
            args.query,
            grade=args.grade,
            subject=args.subject,
            trust_tier=args.trust_tier,
            limit=args.limit,
        )
        for i, hit in enumerate(hits, 1):
            print(f"\n--- Result {i} (score: {hit['score']:.4f}) ---")
            print(f"  Section: {hit['section_title']}")
            print(f"  Grade {hit['grade']}, {hit['author']}, tier {hit['trust_tier']}")
            print(f"  Chunk: {hit['chunk_id']}")
            print(f"  Text: {hit['text'][:300]}...")

    elif args.command == "images":
        hits = search_images(args.query, grade=args.grade, limit=args.limit)
        for i, hit in enumerate(hits, 1):
            print(f"\n--- Image {i} (score: {hit['score']:.4f}) ---")
            print(f"  Path: {hit['image_path']}")
            print(f"  Grade {hit['grade']}, {hit['author']}, page {hit['page']}")
            print(f"  Size: {hit['width']}x{hit['height']}")

    elif args.command == "context":
        chunks = get_chunk_context(args.chunk_id, window=args.window)
        for chunk in chunks:
            marker = ">>>" if chunk.get("is_target") else "   "
            print(f"{marker} [{chunk['chunk_id']}] {chunk['section_title']}")
            print(f"    {chunk['text'][:200]}...")
            print()

    elif args.command == "stats":
        stats = collection_stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
