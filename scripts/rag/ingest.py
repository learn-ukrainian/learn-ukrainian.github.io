"""Ingest extracted chunks, images, and literary texts into Qdrant.

Creates collections with named vectors (dense + sparse for text,
SigLIP for images) and uploads in batches.

Usage:
    # Ingest text chunks from extracted JSONL
    .venv/bin/python scripts/rag/ingest.py --text data/textbook_chunks/grade-01/1-klas-bukvar-bolshakova-2025-1.jsonl

    # Ingest images from extracted metadata JSONL
    .venv/bin/python scripts/rag/ingest.py --images data/textbook_images/grade-01/1-klas-bukvar-bolshakova-2025-1-images.jsonl

    # Ingest literary text chunks
    .venv/bin/python scripts/rag/ingest.py --literary data/literary_texts/wave0-slovo-o-polku.jsonl

    # Ingest all literary texts at once
    .venv/bin/python scripts/rag/ingest.py --all-literary

    # Ingest all extracted data for specific grades
    .venv/bin/python scripts/rag/ingest.py --all --grade 1 3

    # Reset collections (delete and recreate)
    .venv/bin/python scripts/rag/ingest.py --reset
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import (
    BGE_M3_DENSE_DIM,
    CHUNKS_DIR,
    IMAGES_DIR,
    IMAGE_COLLECTION,
    LITERARY_COLLECTION,
    LITERARY_DIR,
    QDRANT_GRPC_PORT,
    QDRANT_HOST,
    QDRANT_REST_PORT,
    SIGLIP_DIM,
    TEXT_COLLECTION,
)


def get_client():
    """Get Qdrant client (REST for reliability — encoding is the bottleneck, not upload)."""
    from qdrant_client import QdrantClient
    return QdrantClient(
        host=QDRANT_HOST, port=QDRANT_REST_PORT,
        prefer_grpc=False, timeout=300,
    )


def create_text_collection(client, recreate: bool = False):
    """Create or verify the textbook_chunks collection."""
    from qdrant_client.models import (
        Distance,
        NamedSparseVector,
        PayloadSchemaType,
        SparseIndexParams,
        SparseVectorParams,
        VectorParams,
    )

    exists = client.collection_exists(TEXT_COLLECTION)
    if exists and not recreate:
        info = client.get_collection(TEXT_COLLECTION)
        print(f"[ingest] Collection '{TEXT_COLLECTION}' exists with {info.points_count} points")
        return
    if exists and recreate:
        print(f"[ingest] Deleting collection '{TEXT_COLLECTION}'...")
        client.delete_collection(TEXT_COLLECTION)

    print(f"[ingest] Creating collection '{TEXT_COLLECTION}'...")
    client.create_collection(
        collection_name=TEXT_COLLECTION,
        vectors_config={
            "dense": VectorParams(
                size=BGE_M3_DENSE_DIM,
                distance=Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(
                index=SparseIndexParams(on_disk=False),
            ),
        },
    )

    # Create payload indexes for filtering
    for field, schema_type in [
        ("grade", PayloadSchemaType.INTEGER),
        ("subject", PayloadSchemaType.KEYWORD),
        ("trust_tier", PayloadSchemaType.INTEGER),
        ("author", PayloadSchemaType.KEYWORD),
        ("section_title", PayloadSchemaType.KEYWORD),
    ]:
        client.create_payload_index(
            collection_name=TEXT_COLLECTION,
            field_name=field,
            field_schema=schema_type,
        )
    print(f"[ingest] Collection '{TEXT_COLLECTION}' created with indexes.")


def create_image_collection(client, recreate: bool = False):
    """Create or verify the textbook_images collection."""
    from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

    exists = client.collection_exists(IMAGE_COLLECTION)
    if exists and not recreate:
        info = client.get_collection(IMAGE_COLLECTION)
        print(f"[ingest] Collection '{IMAGE_COLLECTION}' exists with {info.points_count} points")
        return
    if exists and recreate:
        print(f"[ingest] Deleting collection '{IMAGE_COLLECTION}'...")
        client.delete_collection(IMAGE_COLLECTION)

    print(f"[ingest] Creating collection '{IMAGE_COLLECTION}'...")
    client.create_collection(
        collection_name=IMAGE_COLLECTION,
        vectors_config=VectorParams(
            size=SIGLIP_DIM,
            distance=Distance.COSINE,
        ),
    )

    for field, schema_type in [
        ("grade", PayloadSchemaType.INTEGER),
        ("subject", PayloadSchemaType.KEYWORD),
        ("author", PayloadSchemaType.KEYWORD),
    ]:
        client.create_payload_index(
            collection_name=IMAGE_COLLECTION,
            field_name=field,
            field_schema=schema_type,
        )
    print(f"[ingest] Collection '{IMAGE_COLLECTION}' created with indexes.")


_text_encoder = None
_image_encoder = None


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


def ingest_text_chunks(client, jsonl_path: Path, batch_size: int = 64):
    """Embed and ingest text chunks from a JSONL file."""
    from qdrant_client.models import NamedSparseVector, NamedVector, PointStruct, SparseVector

    jsonl_path = Path(jsonl_path)
    print(f"\n[ingest] Loading chunks from {jsonl_path.name}...")

    chunks = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            chunk = json.loads(line)
            # Only ingest clean chunks
            if chunk.get("quality", {}).get("is_clean", True):
                chunks.append(chunk)

    if not chunks:
        print("  No clean chunks found, skipping.")
        return 0

    print(f"  {len(chunks)} clean chunks to embed...")

    encoder = get_text_encoder()
    texts = [c["text"] for c in chunks]
    embeddings = encoder.encode(texts, batch_size=batch_size)

    dense_vecs = embeddings["dense_vecs"]
    sparse_weights = embeddings["lexical_weights"]

    print(f"  Uploading {len(chunks)} points to Qdrant...")

    points = []
    for i, chunk in enumerate(chunks):
        # Convert sparse weights: {token_str: weight} → SparseVector
        sw = sparse_weights[i]
        if isinstance(sw, dict):
            indices = list(int(k) if isinstance(k, (int, float)) else hash(k) % (2**31) for k in sw.keys())
            values = list(sw.values())
        else:
            indices, values = [], []

        payload = {
            "text": chunk["text"],
            "chunk_id": chunk["chunk_id"],
            "grade": chunk.get("grade", 0),
            "subject": chunk.get("subject", ""),
            "author": chunk.get("author", ""),
            "year": chunk.get("year", 0),
            "trust_tier": chunk.get("trust_tier", 2),
            "section_title": chunk.get("section_title", ""),
            "pdf_stem": chunk.get("pdf_stem", ""),
            "token_count": chunk.get("token_count", 0),
        }

        point = PointStruct(
            id=int(hashlib.sha256(chunk["chunk_id"].encode()).hexdigest()[:15], 16),
            vector={
                "dense": dense_vecs[i].tolist(),
                "sparse": SparseVector(indices=indices, values=values),
            },
            payload=payload,
        )
        points.append(point)

    # Upload in batches
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=TEXT_COLLECTION, points=batch)
        print(f"  Uploaded {min(i + batch_size, len(points))}/{len(points)}")

    print(f"  Done: {len(points)} text chunks ingested.")
    return len(points)


def ingest_images(client, jsonl_path: Path, batch_size: int = 16):
    """Embed and ingest images from an image metadata JSONL file.

    Streams in batches: encode batch_size images → upload → free memory → next batch.
    This avoids OOM on large JSONL files (300+ images).
    """
    from qdrant_client.models import PointStruct

    jsonl_path = Path(jsonl_path)
    print(f"\n[ingest] Loading image metadata from {jsonl_path.name}...")

    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    if not records:
        print("  No images found, skipping.")
        return 0

    # Resolve image paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    valid_records = []
    valid_paths = []
    for rec in records:
        img_path = project_root / rec["image_path"]
        if img_path.exists():
            valid_records.append(rec)
            valid_paths.append(img_path)
        else:
            print(f"  Warning: image not found: {img_path}")

    if not valid_records:
        print("  No valid images found, skipping.")
        return 0

    total = len(valid_records)
    print(f"  {total} images to embed+upload (streaming, batch={batch_size})...")

    encoder = get_image_encoder()
    uploaded = 0

    # Stream: encode batch → build points → upload → free memory
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch_paths = valid_paths[start:end]
        batch_records = valid_records[start:end]

        vecs = encoder.encode_images(batch_paths, batch_size=batch_size)

        points = []
        for i, rec in enumerate(batch_records):
            payload = {
                "image_id": rec["image_id"],
                "image_path": rec["image_path"],
                "filename": rec["filename"],
                "page": rec.get("page", 0),
                "grade": rec.get("grade", 0),
                "subject": rec.get("subject", ""),
                "author": rec.get("author", ""),
                "year": rec.get("year", 0),
                "width": rec.get("width", 0),
                "height": rec.get("height", 0),
                "pdf_stem": rec.get("pdf_stem", ""),
            }
            point = PointStruct(
                id=int(hashlib.sha256(rec["image_id"].encode()).hexdigest()[:15], 16),
                vector=vecs[i].tolist(),
                payload=payload,
            )
            points.append(point)

        client.upsert(collection_name=IMAGE_COLLECTION, points=points)
        uploaded += len(points)
        print(f"  Uploaded {uploaded}/{total}")

        del vecs, points  # Free memory immediately

    print(f"  Done: {uploaded} images ingested.")
    return uploaded


def create_literary_collection(client, recreate: bool = False):
    """Create or verify the literary_texts collection."""
    from qdrant_client.models import (
        Distance,
        PayloadSchemaType,
        SparseIndexParams,
        SparseVectorParams,
        VectorParams,
    )

    exists = client.collection_exists(LITERARY_COLLECTION)
    if exists and not recreate:
        info = client.get_collection(LITERARY_COLLECTION)
        print(f"[ingest] Collection '{LITERARY_COLLECTION}' exists with {info.points_count} points")
        return
    if exists and recreate:
        print(f"[ingest] Deleting collection '{LITERARY_COLLECTION}'...")
        client.delete_collection(LITERARY_COLLECTION)

    print(f"[ingest] Creating collection '{LITERARY_COLLECTION}'...")
    client.create_collection(
        collection_name=LITERARY_COLLECTION,
        vectors_config={
            "dense": VectorParams(
                size=BGE_M3_DENSE_DIM,
                distance=Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(
                index=SparseIndexParams(on_disk=False),
            ),
        },
    )

    for field, schema_type in [
        ("work", PayloadSchemaType.KEYWORD),
        ("author", PayloadSchemaType.KEYWORD),
        ("year", PayloadSchemaType.INTEGER),
        ("genre", PayloadSchemaType.KEYWORD),
        ("language_period", PayloadSchemaType.KEYWORD),
    ]:
        client.create_payload_index(
            collection_name=LITERARY_COLLECTION,
            field_name=field,
            field_schema=schema_type,
        )
    print(f"[ingest] Collection '{LITERARY_COLLECTION}' created with indexes.")


def ingest_literary_chunks(client, jsonl_path: Path, batch_size: int = 32):
    """Embed and ingest literary text chunks into Qdrant."""
    from qdrant_client.models import PointStruct, SparseVector

    jsonl_path = Path(jsonl_path)
    print(f"\n[ingest] Ingesting literary chunks from {jsonl_path.name}...")

    chunks = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    if not chunks:
        print("  No chunks found, skipping.")
        return 0

    print(f"  {len(chunks)} chunks to embed...")

    encoder = get_text_encoder()
    texts = [c["text"] for c in chunks]
    embeddings = encoder.encode(texts, batch_size=batch_size)

    dense_vecs = embeddings["dense_vecs"]
    sparse_weights = embeddings["lexical_weights"]

    points = []
    for i, chunk in enumerate(chunks):
        sw = sparse_weights[i]
        if isinstance(sw, dict):
            indices = list(
                int(k) if isinstance(k, (int, float)) else hash(k) % (2**31)
                for k in sw.keys()
            )
            values = list(sw.values())
        else:
            indices, values = [], []

        payload = {
            "text": chunk["text"],
            "chunk_id": chunk["chunk_id"],
            "work": chunk.get("work", ""),
            "author": chunk.get("author", ""),
            "year": chunk.get("year", 0),
            "genre": chunk.get("genre", ""),
            "language_period": chunk.get("language_period", ""),
            "source_url": chunk.get("source_url", ""),
            "token_count": chunk.get("token_count", 0),
        }
        if "original_text" in chunk:
            payload["original_text"] = chunk["original_text"]

        point = PointStruct(
            id=int(hashlib.sha256(chunk["chunk_id"].encode()).hexdigest()[:15], 16),
            vector={
                "dense": dense_vecs[i].tolist(),
                "sparse": SparseVector(indices=indices, values=values),
            },
            payload=payload,
        )
        points.append(point)

    print(f"  Uploading {len(points)} points to Qdrant...")
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=LITERARY_COLLECTION, points=batch)
        print(f"  Uploaded {min(i + batch_size, len(points))}/{len(points)}")

    print(f"  Done: {len(points)} literary chunks ingested.")
    return len(points)


def find_jsonl_files(base_dir: Path, grades: list[int] | None = None, suffix: str = ".jsonl") -> list[Path]:
    """Find JSONL files, optionally filtered by grade."""
    files = []
    for grade_dir in sorted(base_dir.iterdir()):
        if not grade_dir.is_dir() or not grade_dir.name.startswith("grade-"):
            continue
        grade_num = int(grade_dir.name.split("-")[1])
        if grades and grade_num not in grades:
            continue
        for f in sorted(grade_dir.glob(f"*{suffix}")):
            files.append(f)
    return files


def main():
    parser = argparse.ArgumentParser(description="Ingest text/images/literary texts into Qdrant")
    parser.add_argument("--text", type=str, action="append", help="Path to text chunks JSONL (repeatable)")
    parser.add_argument("--images", type=str, action="append", help="Path to image metadata JSONL (repeatable)")
    parser.add_argument("--literary", type=str, action="append", help="Path to literary text JSONL (repeatable)")
    parser.add_argument("--all", action="store_true", help="Ingest all extracted data")
    parser.add_argument("--all-literary", action="store_true", help="Ingest all literary JSONL files in data/literary_texts/")
    parser.add_argument("--grade", type=int, nargs="+", help="Filter by grades (textbook only)")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate collections")
    parser.add_argument("--batch-size", type=int, default=64, help="Embedding batch size")
    args = parser.parse_args()

    client = get_client()

    has_literary = args.literary or args.all_literary
    has_textbook = args.text or args.images or args.all

    if args.reset:
        create_text_collection(client, recreate=True)
        create_image_collection(client, recreate=True)
        create_literary_collection(client, recreate=True)
        if not (has_textbook or has_literary):
            print("Collections reset. Done.")
            return

    total_chunks = 0
    total_images = 0
    total_literary = 0

    # Textbook ingestion
    if args.text or args.images or args.all:
        create_text_collection(client)
        create_image_collection(client)

    if args.text:
        for text_path in args.text:
            total_chunks += ingest_text_chunks(client, Path(text_path), batch_size=args.batch_size)

    if args.images:
        for img_path in args.images:
            total_images += ingest_images(client, Path(img_path), batch_size=min(args.batch_size, 16))

    if args.all:
        text_files = find_jsonl_files(CHUNKS_DIR, args.grade, suffix=".jsonl")
        text_files = [f for f in text_files if not f.name.endswith("-images.jsonl")]
        for tf in text_files:
            total_chunks += ingest_text_chunks(client, tf, batch_size=args.batch_size)

        image_files = find_jsonl_files(IMAGES_DIR, args.grade, suffix="-images.jsonl")
        for imf in image_files:
            total_images += ingest_images(client, imf, batch_size=min(args.batch_size, 16))

    # Literary ingestion
    if has_literary:
        create_literary_collection(client)

    if args.literary:
        for lit_path in args.literary:
            total_literary += ingest_literary_chunks(client, Path(lit_path), batch_size=min(args.batch_size, 32))

    if args.all_literary:
        if LITERARY_DIR.exists():
            for jsonl_file in sorted(LITERARY_DIR.glob("*.jsonl")):
                total_literary += ingest_literary_chunks(client, jsonl_file, batch_size=min(args.batch_size, 32))
        else:
            print(f"[ingest] Literary dir not found: {LITERARY_DIR}")

    # Summary
    totals = []
    if total_chunks:
        totals.append(f"{total_chunks} text chunks")
    if total_images:
        totals.append(f"{total_images} images")
    if total_literary:
        totals.append(f"{total_literary} literary chunks")

    if totals:
        print(f"\n=== Ingestion complete: {', '.join(totals)} ===")
        for coll in [TEXT_COLLECTION, IMAGE_COLLECTION, LITERARY_COLLECTION]:
            try:
                info = client.get_collection(coll)
                print(f"  {coll}: {info.points_count} points")
            except Exception:
                pass


if __name__ == "__main__":
    main()
