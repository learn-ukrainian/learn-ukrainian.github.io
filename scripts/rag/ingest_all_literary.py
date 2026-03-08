"""Ingest all literary JSONL files into Qdrant with embedding cache.

First run:  encodes with BGE-M3, saves cache, uploads (~4-5h for 78K chunks).
Subsequent: loads from cache, uploads only (~5 min).

Cache files: data/literary_texts/.embed_cache/{stem}.npz
Delete a cache file to force re-encoding of that JSONL.

Usage:
    .venv/bin/python scripts/rag/ingest_all_literary.py           # Normal (use cache)
    .venv/bin/python scripts/rag/ingest_all_literary.py --no-cache  # Force re-encode all
    .venv/bin/python scripts/rag/ingest_all_literary.py --cache-only # Encode + cache, skip Qdrant
    .venv/bin/python scripts/rag/ingest_all_literary.py --stats      # Show cache status
"""

import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import LITERARY_DIR

CACHE_DIR = LITERARY_DIR / ".embed_cache"


def cache_path_for(jsonl_path: Path) -> Path:
    """Get the cache file path for a JSONL file."""
    return CACHE_DIR / f"{jsonl_path.stem}.pkl"


def has_cache(jsonl_path: Path) -> bool:
    """Check if a valid cache exists for a JSONL file."""
    cp = cache_path_for(jsonl_path)
    if not cp.exists():
        return False
    # Cache is stale if JSONL is newer
    return cp.stat().st_mtime >= jsonl_path.stat().st_mtime


def save_cache(jsonl_path: Path, embeddings: dict):
    """Save embeddings to cache (dense as fp16 to halve size)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cp = cache_path_for(jsonl_path)
    cache_data = {
        "dense_vecs": embeddings["dense_vecs"].astype(np.float16),
        "lexical_weights": embeddings["lexical_weights"],
    }
    with open(cp, "wb") as f:
        pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_cache(jsonl_path: Path) -> dict:
    """Load embeddings from cache (upcast dense back to fp32)."""
    cp = cache_path_for(jsonl_path)
    with open(cp, "rb") as f:
        data = pickle.load(f)  # nosec B301 — loading our own embedding cache
    data["dense_vecs"] = data["dense_vecs"].astype(np.float32)
    return data


def encode_file(encoder, jsonl_path: Path, batch_size: int = 32) -> dict:
    """Encode all texts in a JSONL file and return embeddings dict."""
    texts = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            texts.append(json.loads(line)["text"])
    return encoder.encode(texts, batch_size=batch_size)


def _count_lines(path):
    """Count lines in a file."""
    with open(path) as _fh:
        return sum(1 for _ in _fh)


def show_stats(jsonl_files: list[Path]):
    """Show cache status for all files."""
    cached = 0
    uncached = 0
    cache_bytes = 0
    total_chunks = 0

    for jf in jsonl_files:
        n_chunks = _count_lines(jf)
        total_chunks += n_chunks
        if has_cache(jf):
            cached += 1
            cache_bytes += cache_path_for(jf).stat().st_size
        else:
            uncached += 1

    print(f"JSONL files:    {len(jsonl_files)}")
    print(f"Total chunks:   {total_chunks:,}")
    print(f"Cached:         {cached} ({cached / len(jsonl_files) * 100:.0f}%)")
    print(f"Uncached:       {uncached}")
    print(f"Cache size:     {cache_bytes / 1024 / 1024:.0f} MB")

    if uncached > 0:
        uncached_chunks = sum(
            _count_lines(jf)
            for jf in jsonl_files
            if not has_cache(jf)
        )
        est_min = uncached_chunks / 5 / 60  # ~5 ch/s on M4
        print(f"Uncached chunks: {uncached_chunks:,} (est. {est_min:.0f} min to encode)")


def main():
    parser = argparse.ArgumentParser(description="Ingest all literary texts with embedding cache")
    parser.add_argument("--no-cache", action="store_true", help="Force re-encode (ignore cache)")
    parser.add_argument("--cache-only", action="store_true", help="Encode and cache, skip Qdrant upload")
    parser.add_argument("--stats", action="store_true", help="Show cache status and exit")
    parser.add_argument("--batch-size", type=int, default=32, help="BGE-M3 batch size (default: 32)")
    args = parser.parse_args()

    jsonl_files = sorted(LITERARY_DIR.glob("*.jsonl"))
    if not jsonl_files:
        print("No JSONL files found in", LITERARY_DIR)
        return

    if args.stats:
        show_stats(jsonl_files)
        return

    total_chunks = sum(_count_lines(f) for f in jsonl_files)
    to_encode = [jf for jf in jsonl_files if args.no_cache or not has_cache(jf)]
    cached_count = len(jsonl_files) - len(to_encode)

    print(f"Found {len(jsonl_files)} JSONL files, {total_chunks:,} total chunks")
    print(f"  Cached: {cached_count}  |  To encode: {len(to_encode)}")

    if to_encode:
        encode_chunks = sum(_count_lines(f) for f in to_encode)
        est_min = encode_chunks / 5 / 60
        print(f"  Chunks to encode: {encode_chunks:,} (est. {est_min:.0f} min)")

    # Phase 1: Encode uncached files
    if to_encode:
        from rag.embed import TextEncoder
        encoder = TextEncoder()
        print(f"\n{'='*60}")
        print("Phase 1: Encoding uncached files with BGE-M3...")
        print(f"{'='*60}")
        t0 = time.time()

        for i, jf in enumerate(to_encode, 1):
            n_chunks = _count_lines(jf)
            print(f"\n[{i}/{len(to_encode)}] {jf.name} ({n_chunks} chunks)...", flush=True)
            t1 = time.time()
            embeddings = encode_file(encoder, jf, batch_size=args.batch_size)
            save_cache(jf, embeddings)
            elapsed = time.time() - t1
            speed = n_chunks / elapsed if elapsed > 0 else 0
            print(f"  Encoded + cached in {elapsed:.1f}s ({speed:.1f} ch/s)")

        total_encode_time = time.time() - t0
        print(f"\nEncoding complete: {total_encode_time / 60:.1f} min")

    if args.cache_only:
        print("\n--cache-only: skipping Qdrant upload.")
        show_stats(jsonl_files)
        return

    # Phase 2: Upload to Qdrant from cache
    from rag.ingest import create_literary_collection, get_client, ingest_literary_chunks

    client = get_client()
    create_literary_collection(client)

    print(f"\n{'='*60}")
    print("Phase 2: Uploading to Qdrant from cache...")
    print(f"{'='*60}")
    t0 = time.time()
    total = 0

    for i, jf in enumerate(jsonl_files, 1):
        embeddings = load_cache(jf)
        n = ingest_literary_chunks(client, jf, batch_size=64, embeddings=embeddings)
        total += n
        if i % 10 == 0:
            elapsed = time.time() - t0
            print(f"  Progress: {i}/{len(jsonl_files)} files, {total:,} chunks, {elapsed:.0f}s")

    upload_time = time.time() - t0
    print(f"\n{'='*60}")
    print(f"Total: {total:,} literary chunks ingested in {upload_time:.0f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
