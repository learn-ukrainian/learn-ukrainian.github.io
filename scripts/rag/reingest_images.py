"""Re-ingest images into Qdrant with annotations from image_text_pairs.jsonl.

Images-only — skips text chunk re-embedding. Upserts (same IDs, enriched payloads).

Usage:
    .venv/bin/python scripts/rag/reingest_images.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import IMAGES_DIR
from rag.ingest import create_image_collection, get_client, ingest_images

image_files = sorted(IMAGES_DIR.rglob("*-images.jsonl"))
non_empty = [f for f in image_files if f.stat().st_size > 0]
print(f"Found {len(non_empty)} non-empty image JSONLs\n")

client = get_client()
create_image_collection(client)

total = 0
for i, imf in enumerate(non_empty, 1):
    print(f"[{i}/{len(non_empty)}] ", end="", flush=True)
    n = ingest_images(client, imf, batch_size=16)
    total += n

print(f"\n=== Total: {total} images ingested with annotations ===")
