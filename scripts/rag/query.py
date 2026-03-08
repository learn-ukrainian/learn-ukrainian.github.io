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
    ESU_COLLECTION,
    IMAGE_COLLECTION,
    LITERARY_COLLECTION,
    QDRANT_GRPC_PORT,
    QDRANT_HOST,
    TEXT_COLLECTION,
    VESUM_DB_PATH,
)

# Module-level singletons (lazy-loaded)
_qdrant_client = None
_text_encoder = None
_image_encoder = None
_vesum_conn = None


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
        SparseVector,
    )

    client = get_client()
    encoder = get_text_encoder()

    # Encode query
    result = encoder.encode([query])
    dense_vec = result["dense_vecs"][0].tolist()
    sparse_w = result["lexical_weights"][0]

    if isinstance(sparse_w, dict):
        sparse_indices = [int(k) if isinstance(k, (int, float)) else hash(k) % (2**31) for k in sparse_w]
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


def search_literary(query: str, work: str | None = None, genre: str | None = None,
                    period: str | None = None, limit: int = 5) -> list[dict]:
    """Search literary texts (Slovo, PVL, chronicles, etc.) via dense vectors."""
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    client = get_client()
    encoder = get_text_encoder()

    result = encoder.encode([query])
    dense_vec = result["dense_vecs"][0].tolist()

    conditions = []
    if work:
        conditions.append(FieldCondition(key="work", match=MatchValue(value=work)))
    if genre:
        conditions.append(FieldCondition(key="genre", match=MatchValue(value=genre)))
    if period:
        conditions.append(FieldCondition(key="language_period", match=MatchValue(value=period)))
    qfilter = Filter(must=conditions) if conditions else None

    results = client.query_points(
        collection_name=LITERARY_COLLECTION,
        query=dense_vec,
        using="dense",
        limit=limit,
        query_filter=qfilter,
        with_payload=True,
    )

    hits = []
    for point in results.points:
        payload = point.payload or {}
        hit = {
            "score": point.score if hasattr(point, "score") else 0,
            "chunk_id": payload.get("chunk_id", ""),
            "text": payload.get("text", "")[:500],
            "work": payload.get("work", ""),
            "author": payload.get("author", ""),
            "year": payload.get("year", 0),
            "genre": payload.get("genre", ""),
            "language_period": payload.get("language_period", ""),
            "source_url": payload.get("source_url", ""),
        }
        if payload.get("original_text"):
            hit["original_text"] = payload["original_text"][:300]
        hits.append(hit)
    return hits


def search_esu(query: str, letter: str | None = None, limit: int = 5) -> list[dict]:
    """Search ESU encyclopedia articles via hybrid dense+sparse vectors."""
    from qdrant_client.models import (
        FieldCondition,
        Filter,
        FusionQuery,
        MatchValue,
        Prefetch,
        SparseVector,
    )

    client = get_client()
    encoder = get_text_encoder()

    result = encoder.encode([query])
    dense_vec = result["dense_vecs"][0].tolist()
    sparse_w = result["lexical_weights"][0]

    if isinstance(sparse_w, dict):
        sparse_indices = [int(k) if isinstance(k, (int, float)) else hash(k) % (2**31) for k in sparse_w]
        sparse_values = list(sparse_w.values())
    else:
        sparse_indices, sparse_values = [], []

    conditions = []
    if letter:
        conditions.append(FieldCondition(key="letter", match=MatchValue(value=letter)))
    qfilter = Filter(must=conditions) if conditions else None

    results = client.query_points(
        collection_name=ESU_COLLECTION,
        prefetch=[
            Prefetch(query=dense_vec, using="dense", limit=limit * 3, filter=qfilter),
            Prefetch(
                query=SparseVector(indices=sparse_indices, values=sparse_values),
                using="sparse", limit=limit * 3, filter=qfilter,
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
            "score": point.score if hasattr(point, "score") else 0,
            "chunk_id": payload.get("chunk_id", ""),
            "text": payload.get("text", "")[:500],
            "title": payload.get("title", ""),
            "article_id": payload.get("article_id", 0),
            "url": payload.get("url", ""),
            "letter": payload.get("letter", ""),
            "author": payload.get("author", ""),
            "keywords": payload.get("keywords", ""),
        })
    return hits


def get_full_text(work: str, max_chars: int = 50_000) -> dict:
    """Load all chunks for a literary work, concatenated into full text.

    For short works (<20 pages / ~8000 tokens), returns the complete text.
    Caps at max_chars for safety.

    Returns dict with keys: work, author, year, genre, language_period, text, chunk_count, truncated.
    """
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    client = get_client()

    # Scroll all chunks for this work
    all_points = []
    offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name=LITERARY_COLLECTION,
            scroll_filter=Filter(
                must=[FieldCondition(key="work", match=MatchValue(value=work))]
            ),
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        all_points.extend(points)
        if next_offset is None:
            break
        offset = next_offset

    if not all_points:
        return {"error": f"No chunks found for work: {work}"}

    # Sort by chunk_id for correct ordering
    all_points.sort(key=lambda p: p.payload.get("chunk_id", ""))

    # Extract metadata from first chunk
    first = all_points[0].payload
    metadata = {
        "work": first.get("work", ""),
        "author": first.get("author", ""),
        "year": first.get("year", 0),
        "genre": first.get("genre", ""),
        "language_period": first.get("language_period", ""),
        "chunk_count": len(all_points),
    }

    # Concatenate text
    texts = [p.payload.get("text", "") for p in all_points]
    full_text = "\n\n".join(texts)

    truncated = len(full_text) > max_chars
    if truncated:
        full_text = full_text[:max_chars] + "\n\n[... truncated at character limit ...]"

    metadata["text"] = full_text
    metadata["truncated"] = truncated
    return metadata


def search_images(query: str, grade: int | None = None,
                   teaching_value: str | None = None,
                   subject: str | None = None,
                   limit: int = 5) -> list[dict]:
    """Image search via Ukrainian text query (SigLIP text-to-image).

    Args:
        teaching_value: Filter by annotation quality — "high", "medium", "low", or "none".
        subject: Filter by textbook subject (e.g., "bukvar").
    """
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    client = get_client()
    encoder = get_image_encoder()

    query_vec = encoder.encode_text([query])[0].tolist()

    conditions = []
    if grade is not None:
        conditions.append(FieldCondition(key="grade", match=MatchValue(value=grade)))
    if subject:
        conditions.append(FieldCondition(key="subject", match=MatchValue(value=subject)))
    if teaching_value:
        conditions.append(FieldCondition(key="teaching_value", match=MatchValue(value=teaching_value)))
    qfilter = Filter(must=conditions) if conditions else None

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
        hit = {
            "score": point.score if hasattr(point, 'score') else 0,
            "image_id": payload.get("image_id", ""),
            "image_path": payload.get("image_path", ""),
            "page": payload.get("page", 0),
            "grade": payload.get("grade", 0),
            "author": payload.get("author", ""),
            "width": payload.get("width", 0),
            "height": payload.get("height", 0),
        }
        # Include annotation fields when present
        if payload.get("description_uk"):
            hit["description_uk"] = payload["description_uk"]
        if payload.get("associated_text_uk"):
            hit["associated_text_uk"] = payload["associated_text_uk"]
        if payload.get("teaching_value"):
            hit["teaching_value"] = payload["teaching_value"]
        hits.append(hit)
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
    for coll_name in [TEXT_COLLECTION, IMAGE_COLLECTION, LITERARY_COLLECTION, ESU_COLLECTION]:
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


def get_vesum_conn():
    """Lazy-load SQLite connection to VESUM dictionary."""
    global _vesum_conn
    if _vesum_conn is None:
        import sqlite3
        if not VESUM_DB_PATH.exists():
            raise FileNotFoundError(
                f"VESUM database not found at {VESUM_DB_PATH}. "
                "Run: .venv/bin/python scripts/rag/import_vesum.py"
            )
        _vesum_conn = sqlite3.connect(str(VESUM_DB_PATH), check_same_thread=False)
        _vesum_conn.row_factory = sqlite3.Row
    return _vesum_conn


def verify_word(word: str, pos_filter: str | None = None) -> list[dict]:
    """Check if a word form exists in VESUM.

    Returns list of {lemma, pos, tags} matches. Empty list = not found.
    """
    conn = get_vesum_conn()
    if pos_filter:
        rows = conn.execute(
            "SELECT lemma, pos, tags FROM forms WHERE word_form = ? AND pos = ?",
            (word, pos_filter),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT lemma, pos, tags FROM forms WHERE word_form = ?",
            (word,),
        ).fetchall()
    return [{"lemma": r["lemma"], "pos": r["pos"], "tags": r["tags"]} for r in rows]


def verify_words(words: list[str], pos_filter: str | None = None) -> dict[str, list[dict]]:
    """Batch-verify multiple word forms against VESUM in a single query.

    Returns dict mapping each word to its list of matches.
    Words not found map to an empty list.
    """
    if not words:
        return {}
    conn = get_vesum_conn()
    placeholders = ",".join("?" * len(words))
    if pos_filter:
        rows = conn.execute(
            f"SELECT word_form, lemma, pos, tags FROM forms WHERE word_form IN ({placeholders}) AND pos = ?",
            (*words, pos_filter),
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT word_form, lemma, pos, tags FROM forms WHERE word_form IN ({placeholders})",
            words,
        ).fetchall()
    result: dict[str, list[dict]] = {w: [] for w in words}
    for r in rows:
        result[r["word_form"]].append({"lemma": r["lemma"], "pos": r["pos"], "tags": r["tags"]})
    return result


def verify_lemma(lemma: str) -> list[dict]:
    """Get all inflected forms of a lemma.

    Returns list of {word_form, pos, tags} for every form.
    """
    conn = get_vesum_conn()
    rows = conn.execute(
        "SELECT word_form, pos, tags FROM forms WHERE lemma = ? ORDER BY pos, tags",
        (lemma,),
    ).fetchall()
    return [{"word_form": r["word_form"], "pos": r["pos"], "tags": r["tags"]} for r in rows]


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

    # Literary text search
    lit_parser = subparsers.add_parser("literary", help="Literary text search (Slovo, PVL, chronicles)")
    lit_parser.add_argument("query", help="Search query in Ukrainian")
    lit_parser.add_argument("--work", type=str, help="Filter by work title")
    lit_parser.add_argument("--genre", type=str, help="Filter by genre")
    lit_parser.add_argument("--period", type=str, help="Filter by language period")
    lit_parser.add_argument("--limit", type=int, default=5, help="Number of results")

    # Image search
    img_parser = subparsers.add_parser("images", help="Text-to-image search")
    img_parser.add_argument("query", help="Search query in Ukrainian")
    img_parser.add_argument("--grade", type=int, help="Filter by grade")
    img_parser.add_argument("--limit", type=int, default=5, help="Number of results")

    # Full text
    full_parser = subparsers.add_parser("full-text", help="Get full text of a literary work")
    full_parser.add_argument("work", help="Work title (e.g., 'Слово о полку Ігоревім')")
    full_parser.add_argument("--max-chars", type=int, default=50000, help="Max characters")

    # Context
    ctx_parser = subparsers.add_parser("context", help="Get surrounding chunks")
    ctx_parser.add_argument("chunk_id", help="Chunk ID")
    ctx_parser.add_argument("--window", type=int, default=2, help="Number of chunks before/after")

    # Stats
    subparsers.add_parser("stats", help="Collection statistics")

    # VESUM word verification
    word_parser = subparsers.add_parser("word", help="Verify a Ukrainian word form (VESUM)")
    word_parser.add_argument("query", help="Word form to check")
    word_parser.add_argument("--pos", type=str, help="Filter by POS (e.g., noun, verb, adj)")

    # VESUM lemma lookup
    lemma_parser = subparsers.add_parser("lemma", help="Get all forms of a lemma (VESUM)")
    lemma_parser.add_argument("query", help="Lemma to look up")

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

    elif args.command == "literary":
        hits = search_literary(
            args.query,
            work=args.work,
            genre=args.genre,
            period=args.period,
            limit=args.limit,
        )
        for i, hit in enumerate(hits, 1):
            print(f"\n--- Result {i} (score: {hit['score']:.4f}) ---")
            print(f"  Work: {hit['work']} ({hit['year']})")
            print(f"  Genre: {hit['genre']}, Period: {hit['language_period']}")
            print(f"  Chunk: {hit['chunk_id']}")
            print(f"  Text: {hit['text'][:300]}...")
            if hit.get("original_text"):
                print(f"  Original: {hit['original_text'][:200]}...")

    elif args.command == "full-text":
        result = get_full_text(args.work, max_chars=args.max_chars)
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Work: {result['work']} ({result['year']})")
            print(f"Author: {result['author']}")
            print(f"Genre: {result['genre']}, Period: {result['language_period']}")
            print(f"Chunks: {result['chunk_count']}, Truncated: {result['truncated']}")
            print(f"\n{'─' * 60}\n")
            print(result["text"])

    elif args.command == "images":
        hits = search_images(args.query, grade=args.grade, limit=args.limit)
        for i, hit in enumerate(hits, 1):
            print(f"\n--- Image {i} (score: {hit['score']:.4f}) ---")
            print(f"  Path: {hit['image_path']}")
            print(f"  Grade {hit['grade']}, {hit['author']}, page {hit['page']}")
            print(f"  Size: {hit['width']}x{hit['height']}")
            if hit.get("description_uk"):
                print(f"  Description: {hit['description_uk']}")
            if hit.get("associated_text_uk"):
                print(f"  Associated text: {hit['associated_text_uk']}")
            if hit.get("teaching_value"):
                print(f"  Teaching value: {hit['teaching_value']}")

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

    elif args.command == "word":
        matches = verify_word(args.query, pos_filter=args.pos)
        if not matches:
            print(f"❌ '{args.query}' not found in VESUM")
        else:
            print(f"✅ '{args.query}' — {len(matches)} match(es):")
            for m in matches:
                print(f"  lemma={m['lemma']}  pos={m['pos']}  tags={m['tags']}")

    elif args.command == "lemma":
        forms = verify_lemma(args.query)
        if not forms:
            print(f"❌ Lemma '{args.query}' not found in VESUM")
        else:
            print(f"✅ '{args.query}' — {len(forms)} form(s):")
            for f in forms:
                print(f"  {f['word_form']:20s}  {f['tags']}")


if __name__ == "__main__":
    main()
