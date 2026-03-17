"""Cleanup poisoned ukrlib chunks from Qdrant literary_texts collection.

Identifies old ukrlib chunks (wrong author IDs) that coexist with correctly
re-scraped data. Deletes only the poisoned ones, preserving all valid data.

Strategy:
1. Build set of valid chunk_ids from current ukrlib-*.jsonl files
2. Scroll Qdrant for all points with source_url containing "ukrlib"
3. Delete any point whose chunk_id is NOT in the valid set

Related: issue #804
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "literary_texts"


def _chunk_id_to_point_id(identifier: str) -> int:
    """Deterministic Qdrant point ID from chunk_id string."""
    return int(hashlib.sha256(identifier.encode()).hexdigest()[:15], 16)


def load_valid_chunk_ids() -> set[str]:
    """Load all chunk_ids from current ukrlib JSONL files."""
    valid = set()
    for jf in sorted(DATA_DIR.glob("ukrlib-*.jsonl")):
        with open(jf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                chunk = json.loads(line)
                valid.add(chunk["chunk_id"])
    return valid


def main():
    from qdrant_client import QdrantClient
    from qdrant_client.models import FieldCondition, Filter, MatchText

    client = QdrantClient(host="localhost", port=6333, timeout=120)

    # Step 1: Load valid chunk_ids
    print("[cleanup] Loading valid chunk_ids from current ukrlib JSONL files...")
    valid_ids = load_valid_chunk_ids()
    print(f"[cleanup] Found {len(valid_ids):,} valid chunk_ids across {len(list(DATA_DIR.glob('ukrlib-*.jsonl')))} files")

    # Step 2: Scroll all ukrlib-sourced points
    print("[cleanup] Scrolling Qdrant for ukrlib-sourced points...")
    ukrlib_filter = Filter(
        must=[
            FieldCondition(
                key="source_url",
                match=MatchText(text="ukrlib.com.ua"),
            )
        ]
    )

    poisoned_point_ids = []
    poisoned_samples = []
    valid_count = 0
    offset = None
    batch_size = 1000

    while True:
        points, next_offset = client.scroll(
            collection_name="literary_texts",
            scroll_filter=ukrlib_filter,
            limit=batch_size,
            offset=offset,
            with_payload=["chunk_id", "work", "author"],
            with_vectors=False,
        )

        if not points:
            break

        for p in points:
            chunk_id = p.payload.get("chunk_id", "")
            if chunk_id not in valid_ids:
                poisoned_point_ids.append(p.id)
                if len(poisoned_samples) < 10:
                    poisoned_samples.append({
                        "chunk_id": chunk_id,
                        "work": p.payload.get("work", ""),
                        "author": p.payload.get("author", ""),
                    })
            else:
                valid_count += 1

        if next_offset is None:
            break
        offset = next_offset

        if (valid_count + len(poisoned_point_ids)) % 10000 < batch_size:
            print(f"  ... scanned {valid_count + len(poisoned_point_ids):,} points so far "
                  f"({len(poisoned_point_ids):,} poisoned, {valid_count:,} valid)")

    print("\n[cleanup] Scan complete:")
    print(f"  Total ukrlib points: {valid_count + len(poisoned_point_ids):,}")
    print(f"  Valid (in current JSONL): {valid_count:,}")
    print(f"  Poisoned (to delete): {len(poisoned_point_ids):,}")

    if poisoned_samples:
        print("\n[cleanup] Sample poisoned chunks:")
        for s in poisoned_samples:
            print(f"  - {s['chunk_id']}: {s['author']} — {s['work']}")

    if not poisoned_point_ids:
        print("\n[cleanup] No poisoned chunks found. Nothing to delete.")
        return

    # Step 3: Delete poisoned points
    print(f"\n[cleanup] Deleting {len(poisoned_point_ids):,} poisoned points...")

    # Delete in batches of 500
    deleted = 0
    for i in range(0, len(poisoned_point_ids), 500):
        batch = poisoned_point_ids[i:i + 500]
        client.delete(
            collection_name="literary_texts",
            points_selector=batch,
        )
        deleted += len(batch)
        if deleted % 5000 < 500:
            print(f"  ... deleted {deleted:,} / {len(poisoned_point_ids):,}")

    print(f"\n[cleanup] Done. Deleted {deleted:,} poisoned points.")

    # Verify
    info = client.get_collection("literary_texts")
    print(f"[cleanup] Collection now has {info.points_count:,} points")


if __name__ == "__main__":
    main()
