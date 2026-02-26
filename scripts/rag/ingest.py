"""Ingest extracted chunks and images into Qdrant.

Creates collections with named vectors (dense + sparse for text,
SigLIP for images) and uploads in batches.

Usage:
    # Ingest text chunks from extracted JSONL
    .venv/bin/python scripts/rag/ingest.py --text data/textbook_chunks/grade-01/1-klas-bukvar-bolshakova-2025-1.jsonl

    # Ingest images from extracted metadata JSONL
    .venv/bin/python scripts/rag/ingest.py --images data/textbook_images/grade-01/1-klas-bukvar-bolshakova-2025-1-images.jsonl

    # Ingest all extracted data for specific grades
    .venv/bin/python scripts/rag/ingest.py --all --grade 1 3

    # Reset collections (delete and recreate)
    .venv/bin/python scripts/rag/ingest.py --reset
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import (
    BGE_M3_DENSE_DIM,
    CHUNKS_DIR,
    IMAGES_DIR,
    IMAGE_COLLECTION,
    QDRANT_GRPC_PORT,
    QDRANT_HOST,
    SIGLIP_DIM,
    TEXT_COLLECTION,
)


def get_client():
    """Get Qdrant client (gRPC for speed)."""
    from qdrant_client import QdrantClient
    return QdrantClient(
        host=QDRANT_HOST, grpc_port=QDRANT_GRPC_PORT,
        prefer_grpc=True, check_compatibility=False,
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


def ingest_text_chunks(client, jsonl_path: Path, batch_size: int = 64):
    """Embed and ingest text chunks from a JSONL file."""
    from qdrant_client.models import NamedSparseVector, NamedVector, PointStruct, SparseVector

    from rag.embed import TextEncoder

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

    encoder = TextEncoder()
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
            id=abs(hash(chunk["chunk_id"])) % (2**63),
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
    """Embed and ingest images from an image metadata JSONL file."""
    from qdrant_client.models import PointStruct

    from rag.embed import ImageEncoder

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
    image_paths = []
    valid_records = []
    for rec in records:
        img_path = project_root / rec["image_path"]
        if img_path.exists():
            image_paths.append(img_path)
            valid_records.append(rec)
        else:
            print(f"  Warning: image not found: {img_path}")

    if not valid_records:
        print("  No valid images found, skipping.")
        return 0

    print(f"  {len(valid_records)} images to embed...")

    encoder = ImageEncoder()
    vecs = encoder.encode_images(image_paths, batch_size=batch_size)

    print(f"  Uploading {len(valid_records)} image points to Qdrant...")

    points = []
    for i, rec in enumerate(valid_records):
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
            id=abs(hash(rec["image_id"])) % (2**63),
            vector=vecs[i].tolist(),
            payload=payload,
        )
        points.append(point)

    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=IMAGE_COLLECTION, points=batch)
        print(f"  Uploaded {min(i + batch_size, len(points))}/{len(points)}")

    print(f"  Done: {len(points)} images ingested.")
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
    parser = argparse.ArgumentParser(description="Ingest text/images into Qdrant")
    parser.add_argument("--text", type=str, help="Path to text chunks JSONL file")
    parser.add_argument("--images", type=str, help="Path to image metadata JSONL file")
    parser.add_argument("--all", action="store_true", help="Ingest all extracted data")
    parser.add_argument("--grade", type=int, nargs="+", help="Filter by grades")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate collections")
    parser.add_argument("--batch-size", type=int, default=64, help="Embedding batch size")
    args = parser.parse_args()

    client = get_client()

    if args.reset:
        create_text_collection(client, recreate=True)
        create_image_collection(client, recreate=True)
        if not (args.text or args.images or args.all):
            print("Collections reset. Done.")
            return

    # Ensure collections exist
    create_text_collection(client)
    create_image_collection(client)

    total_chunks = 0
    total_images = 0

    if args.text:
        total_chunks += ingest_text_chunks(client, Path(args.text), batch_size=args.batch_size)

    if args.images:
        total_images += ingest_images(client, Path(args.images), batch_size=min(args.batch_size, 16))

    if args.all:
        # Ingest all text chunks
        text_files = find_jsonl_files(CHUNKS_DIR, args.grade, suffix=".jsonl")
        # Exclude image metadata files
        text_files = [f for f in text_files if not f.name.endswith("-images.jsonl")]
        for tf in text_files:
            total_chunks += ingest_text_chunks(client, tf, batch_size=args.batch_size)

        # Ingest all images
        image_files = find_jsonl_files(IMAGES_DIR, args.grade, suffix="-images.jsonl")
        for imf in image_files:
            total_images += ingest_images(client, imf, batch_size=min(args.batch_size, 16))

    if total_chunks or total_images:
        print(f"\n=== Ingestion complete: {total_chunks} text chunks, {total_images} images ===")

        # Print collection stats
        for coll in [TEXT_COLLECTION, IMAGE_COLLECTION]:
            try:
                info = client.get_collection(coll)
                print(f"  {coll}: {info.points_count} points")
            except Exception:
                pass


if __name__ == "__main__":
    main()
