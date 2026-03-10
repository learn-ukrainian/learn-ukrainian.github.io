"""Benchmark BGE-M3 embedding configs on Apple Silicon MPS.

Tests different batch sizes, FP16 vs FP32, max_length settings.
Uses 100 chunks from a JSONL file as sample data.

Usage:
    .venv/bin/python scripts/rag/bench_ingest.py [--file data/literary_texts/ukrlib-shevchenko.jsonl] [--n 100]
"""

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def load_chunks(path: str, n: int) -> list[str]:
    """Load first N text chunks from JSONL."""
    texts = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if len(texts) >= n:
                break
            chunk = json.loads(line)
            texts.append(chunk["text"])
    return texts


def bench_config(texts: list[str], batch_size: int, use_fp16: bool, max_length: int) -> dict:
    """Benchmark a single config. Returns stats dict."""
    from FlagEmbedding import BGEM3FlagModel

    label = f"bs={batch_size}, fp16={use_fp16}, maxlen={max_length}"
    # Label may be extended by caller with sort info
    print(f"\n{'='*60}")
    print(f"Config: {label}")
    print(f"{'='*60}")

    # Load model
    t0 = time.time()
    model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=use_fp16)
    load_time = time.time() - t0
    print(f"  Model load: {load_time:.1f}s")

    # Warm up
    _ = model.encode(texts[:2], batch_size=2, max_length=max_length,
                     return_dense=True, return_sparse=True, return_colbert_vecs=False)
    torch.mps.synchronize()
    torch.mps.empty_cache()
    gc.collect()

    # Benchmark
    t0 = time.time()
    result = model.encode(texts, batch_size=batch_size, max_length=max_length,
                          return_dense=True, return_sparse=True, return_colbert_vecs=False)
    torch.mps.synchronize()
    encode_time = time.time() - t0

    dense = result["dense_vecs"]
    sparse_count = len(result.get("lexical_weights", []))

    # Quality check: compute norm stats
    import numpy as np
    norms = np.linalg.norm(dense, axis=1)

    stats = {
        "label": label,
        "batch_size": batch_size,
        "fp16": use_fp16,
        "max_length": max_length,
        "chunks": len(texts),
        "encode_time": encode_time,
        "chunks_per_sec": len(texts) / encode_time,
        "dense_shape": dense.shape,
        "sparse_count": sparse_count,
        "norm_mean": float(norms.mean()),
        "norm_std": float(norms.std()),
    }

    print(f"  Encode: {encode_time:.2f}s ({stats['chunks_per_sec']:.1f} chunks/s)")
    print(f"  Dense: {dense.shape}, Sparse: {sparse_count}")
    print(f"  Norm: mean={norms.mean():.4f} std={norms.std():.4f}")

    # Cleanup
    del model, result, dense
    torch.mps.empty_cache()
    gc.collect()
    time.sleep(1)  # let MPS settle

    return stats


def compare_quality(texts: list[str], max_length: int = 512):
    """Compare FP16 vs FP32 embedding quality on same texts."""
    from FlagEmbedding import BGEM3FlagModel
    import numpy as np

    print(f"\n{'='*60}")
    print(f"Quality comparison: FP16 vs FP32 (first 20 chunks)")
    print(f"{'='*60}")

    sample = texts[:20]

    # FP32
    model32 = BGEM3FlagModel("BAAI/bge-m3", use_fp16=False)
    r32 = model32.encode(sample, batch_size=8, max_length=max_length,
                         return_dense=True, return_sparse=False, return_colbert_vecs=False)
    d32 = r32["dense_vecs"]
    del model32
    torch.mps.empty_cache()
    gc.collect()

    # FP16
    model16 = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
    r16 = model16.encode(sample, batch_size=8, max_length=max_length,
                         return_dense=True, return_sparse=False, return_colbert_vecs=False)
    d16 = r16["dense_vecs"]
    del model16
    torch.mps.empty_cache()
    gc.collect()

    # Cosine similarity between FP16 and FP32 embeddings
    cosines = []
    for i in range(len(sample)):
        cos = np.dot(d32[i], d16[i]) / (np.linalg.norm(d32[i]) * np.linalg.norm(d16[i]))
        cosines.append(cos)

    cosines = np.array(cosines)
    print(f"  Cosine similarity (FP16 vs FP32):")
    print(f"    Mean:  {cosines.mean():.6f}")
    print(f"    Min:   {cosines.min():.6f}")
    print(f"    Max:   {cosines.max():.6f}")
    print(f"  Verdict: {'✅ Negligible difference' if cosines.mean() > 0.999 else '⚠️ Notable difference'}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark BGE-M3 embedding configs")
    parser.add_argument("--file", default="data/literary_texts/ukrlib-shevchenko.jsonl",
                        help="JSONL file to sample from")
    parser.add_argument("--n", type=int, default=100, help="Number of chunks to test")
    parser.add_argument("--quality", action="store_true", help="Run FP16 vs FP32 quality comparison")
    args = parser.parse_args()

    texts = load_chunks(args.file, args.n)
    print(f"Loaded {len(texts)} chunks (avg {sum(len(t) for t in texts)//len(texts)} chars)")

    if args.quality:
        compare_quality(texts)
        return

    configs = [
        # (batch_size, use_fp16, max_length, sorted)
        (16, True, 512, False),
        (16, True, 1024, False),
    ]

    results = []
    for bs, fp16, maxlen, do_sort in configs:
        try:
            test_texts = sorted(texts, key=len) if do_sort else texts
            stats = bench_config(test_texts, bs, fp16, maxlen)
            stats["sorted"] = do_sort
            stats["label"] += f", sort={'Y' if do_sort else 'N'}"
            results.append(stats)
        except RuntimeError as e:
            print(f"  ❌ OOM or error: {e}")
            torch.mps.empty_cache()
            gc.collect()

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"{'Config':<35} {'Time':>8} {'Speed':>12}")
    print(f"{'-'*35} {'-'*8} {'-'*12}")
    for r in sorted(results, key=lambda x: x["encode_time"]):
        print(f"{r['label']:<35} {r['encode_time']:>7.2f}s {r['chunks_per_sec']:>9.1f} c/s")


if __name__ == "__main__":
    main()
