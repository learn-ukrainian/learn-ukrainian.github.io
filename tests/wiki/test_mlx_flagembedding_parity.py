from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from FlagEmbedding import BGEM3FlagModel

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki.mlx_bridge import EMBED_PYTHON, MLXEncoderBridge

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "parity_texts.json"
MLX_OUTPUT_PATH = Path("/tmp/mlx_parity.npy")
FLAGEMBEDDING_OUTPUT_PATH = Path("/tmp/fe_parity.npy")
MODEL_NAME = "BAAI/bge-m3"


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.clip(norms, 1e-12, None)


def _top_k_neighbors(vectors: np.ndarray, k: int = 5) -> np.ndarray:
    similarity = vectors @ vectors.T
    np.fill_diagonal(similarity, -np.inf)
    return np.argsort(-similarity, axis=1)[:, :k]


def test_mlx_matches_flagembedding_bge_m3() -> None:
    if not EMBED_PYTHON.exists():
        pytest.skip("embed-venv not installed")

    texts = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    with MLXEncoderBridge() as bridge:
        mlx_vectors = bridge.encode(texts, batch_size=16, max_length=512)
    np.save(MLX_OUTPUT_PATH, mlx_vectors)

    flag_model = BGEM3FlagModel(MODEL_NAME, use_fp16=True, pooling_method="cls")
    flag_vectors = flag_model.encode(
        texts,
        batch_size=16,
        max_length=512,
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False,
    )["dense_vecs"]
    np.save(FLAGEMBEDDING_OUTPUT_PATH, flag_vectors)

    mlx_norm = _normalize(mlx_vectors.astype(np.float32))
    flag_norm = _normalize(flag_vectors.astype(np.float32))
    cosine = np.sum(mlx_norm * flag_norm, axis=1)

    min_cosine = float(np.min(cosine))
    mean_cosine = float(np.mean(cosine))
    assert np.all(cosine >= 0.9999), f"cosine min={min_cosine:.6f} mean={mean_cosine:.6f}"

    mlx_top5 = _top_k_neighbors(mlx_norm, k=5)
    flag_top5 = _top_k_neighbors(flag_norm, k=5)
    overlap = sum(
        set(mlx_row.tolist()) == set(flag_row.tolist())
        for mlx_row, flag_row in zip(mlx_top5, flag_top5, strict=True)
    )
    assert overlap >= 18, f"top-5 overlap={overlap}/20"
