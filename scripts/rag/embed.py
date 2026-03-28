"""Embedding encoders for BGE-M3 (text), SigLIP 2 (images), and cross-encoder reranker.

Lazy-loads models on first use to avoid startup cost.

Usage as library:
    from rag.embed import TextEncoder, ImageEncoder, CrossEncoderReranker

    text_enc = TextEncoder()
    results = text_enc.encode(["Привіт, світе!"])
    # results["dense_vecs"]  → np.ndarray (N, 1024)
    # results["lexical_weights"] → list of {token_id: weight} dicts

    img_enc = ImageEncoder()
    vecs = img_enc.encode_images(["/path/to/image.png"])
    # vecs → np.ndarray (N, 1152)

    # Text-to-image search (encode query text in SigLIP space)
    qvecs = img_enc.encode_text(["яблуко"])
    # qvecs → np.ndarray (N, 1152)
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import BGE_M3_MODEL, SIGLIP_DIM, SIGLIP_MODEL, SIGLIP_PRETRAINED


class TextEncoder:
    """BGE-M3 encoder producing dense + sparse vectors in one pass."""

    def __init__(self, device: str | None = None):
        self._model = None
        self._device = device

    def _load(self):
        if self._model is not None:
            return
        from FlagEmbedding import BGEM3FlagModel

        kwargs = {"use_fp16": True}
        if self._device:
            kwargs["devices"] = [self._device]

        print(f"[embed] Loading BGE-M3 from {BGE_M3_MODEL}...")
        self._model = BGEM3FlagModel(
            BGE_M3_MODEL,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=True,  # Enable ColBERT for reranking (#1099)
            **kwargs,
        )
        print("[embed] BGE-M3 loaded (dense + sparse + ColBERT).")

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        max_length: int = 512,
    ) -> dict:
        """Encode texts into dense + sparse vectors.

        Returns:
            {
                "dense_vecs": np.ndarray (N, 1024),
                "lexical_weights": list[dict[str, float]] (N sparse vectors)
            }
        """
        self._load()
        result = self._model.encode(
            texts,
            batch_size=batch_size,
            max_length=max_length,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )
        return {
            "dense_vecs": result["dense_vecs"],
            "lexical_weights": result["lexical_weights"],
        }

    def colbert_rerank(
        self,
        query: str,
        candidates: list[dict],
        text_key: str = "text",
        limit: int = 5,
    ) -> list[dict]:
        """Rerank candidates using ColBERT MaxSim scoring (#1099).

        ColBERT computes token-level similarity: for each query token,
        find the max similarity across all document tokens, then sum.
        This captures fine-grained term interactions that dense vectors miss.

        Args:
            query: Search query text
            candidates: List of dicts with text_key field
            text_key: Key in candidate dicts containing the text to score
            limit: Number of top results to return

        Returns:
            Reranked candidates (top `limit`), each with added 'colbert_score' key.
        """
        import numpy as np

        self._load()
        if not candidates:
            return []

        # Encode query and all candidate texts in one batch
        texts = [query] + [c.get(text_key, "")[:512] for c in candidates]
        result = self._model.encode(
            texts,
            batch_size=len(texts),
            max_length=512,
            return_dense=False,
            return_sparse=False,
            return_colbert_vecs=True,
        )

        colbert_vecs = result["colbert_vecs"]
        query_vecs = colbert_vecs[0]  # (num_query_tokens, 1024)

        scored = []
        for i, candidate in enumerate(candidates):
            doc_vecs = colbert_vecs[i + 1]  # (num_doc_tokens, 1024)

            # MaxSim: for each query token, find max cosine similarity with any doc token
            # Normalize vectors for cosine similarity
            q_norm = query_vecs / (np.linalg.norm(query_vecs, axis=1, keepdims=True) + 1e-8)
            d_norm = doc_vecs / (np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-8)

            # (num_query_tokens, num_doc_tokens) similarity matrix
            sim_matrix = q_norm @ d_norm.T

            # MaxSim: max over doc tokens for each query token, then sum
            max_sim_score = float(sim_matrix.max(axis=1).sum())

            scored.append((max_sim_score, candidate))

        # Sort by ColBERT score descending
        scored.sort(key=lambda x: -x[0])

        # Add colbert_score to results
        results = []
        for score, candidate in scored[:limit]:
            candidate = dict(candidate)  # Don't mutate original
            candidate["colbert_score"] = round(score, 4)
            results.append(candidate)

        return results


# Cross-encoder reranker model
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"


class CrossEncoderReranker:
    """BGE cross-encoder reranker for precise (query, document) scoring (#1097).

    Scores query-document pairs jointly with full cross-attention.
    More precise than ColBERT for short passages. Use for MCP tool calls
    where latency matters (~50-100ms for 15 candidates).

    ColBERT (TextEncoder.colbert_rerank) is better for batch operations
    like knowledge packet building where more candidates are processed.
    """

    def __init__(self):
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        from FlagEmbedding import FlagReranker

        print(f"[reranker] Loading cross-encoder from {RERANKER_MODEL}...")
        self._model = FlagReranker(RERANKER_MODEL, use_fp16=True)
        print("[reranker] Cross-encoder loaded.")

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        text_key: str = "text",
        limit: int = 5,
    ) -> list[dict]:
        """Rerank candidates using cross-encoder scoring.

        Args:
            query: Search query text
            candidates: List of dicts with text_key field
            text_key: Key in candidate dicts containing the text
            limit: Number of top results to return

        Returns:
            Reranked candidates with added 'rerank_score' key.
        """
        self._load()
        if not candidates:
            return []

        pairs = [[query, c.get(text_key, "")[:512]] for c in candidates]
        scores = self._model.compute_score(pairs, normalize=True)

        # compute_score returns a single float for 1 pair, list for multiple
        if isinstance(scores, (int, float)):
            scores = [scores]

        scored = list(zip(scores, candidates, strict=False))
        scored.sort(key=lambda x: -x[0])

        results = []
        for score, candidate in scored[:limit]:
            candidate = dict(candidate)
            candidate["rerank_score"] = round(float(score), 4)
            results.append(candidate)

        return results


class ImageEncoder:
    """SigLIP 2 encoder for images and text-to-image queries."""

    def __init__(self, device: str | None = None):
        self._model = None
        self._preprocess = None
        self._tokenizer = None
        self._device = device or "cpu"

    def _load(self):
        if self._model is not None:
            return
        import open_clip

        print(f"[embed] Loading SigLIP 2 ({SIGLIP_MODEL})...")
        self._model, _, self._preprocess = open_clip.create_model_and_transforms(
            SIGLIP_MODEL,
            pretrained=SIGLIP_PRETRAINED,
            device=self._device,
        )
        self._tokenizer = open_clip.get_tokenizer(SIGLIP_MODEL)
        self._model.eval()
        self._model = self._model.half()  # fp16 — halves memory footprint
        print(f"[embed] SigLIP 2 loaded on {self._device} (fp16).")

    def encode_images(self, image_paths: list[str | Path], batch_size: int = 16) -> np.ndarray:
        """Encode images into vectors.

        Returns: np.ndarray (N, 1152)
        """
        self._load()
        import torch
        from PIL import Image

        all_vecs = []
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i : i + batch_size]
            images = []
            for p in batch_paths:
                try:
                    img = Image.open(p).convert("RGB")
                    images.append(self._preprocess(img))
                except Exception as e:
                    print(f"  Warning: skipping {p}: {e}")
                    # Use zero vector as placeholder
                    images.append(torch.zeros(3, 224, 224))

            batch_tensor = torch.stack(images).to(self._device).half()
            with torch.no_grad():
                vecs = self._model.encode_image(batch_tensor)
                vecs = vecs / vecs.norm(dim=-1, keepdim=True)
            all_vecs.append(vecs.cpu().numpy())

        return np.concatenate(all_vecs, axis=0) if all_vecs else np.empty((0, SIGLIP_DIM))

    def encode_text(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Encode text queries into SigLIP space (for text-to-image search).

        Returns: np.ndarray (N, 1152)
        """
        self._load()
        import torch

        all_vecs = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            tokens = self._tokenizer(batch).to(self._device)
            with torch.no_grad():
                vecs = self._model.encode_text(tokens)
                vecs = vecs / vecs.norm(dim=-1, keepdim=True)
            all_vecs.append(vecs.cpu().numpy())

        return np.concatenate(all_vecs, axis=0) if all_vecs else np.empty((0, SIGLIP_DIM))
