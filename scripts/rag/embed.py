"""Embedding encoders for BGE-M3 (text) and SigLIP 2 (images).

Lazy-loads models on first use to avoid startup cost.

Usage as library:
    from rag.embed import TextEncoder, ImageEncoder

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
            return_colbert_vecs=False,
            **kwargs,
        )
        print("[embed] BGE-M3 loaded.")

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
        import torch

        print(f"[embed] Loading SigLIP 2 ({SIGLIP_MODEL})...")
        self._model, _, self._preprocess = open_clip.create_model_and_transforms(
            SIGLIP_MODEL,
            pretrained=SIGLIP_PRETRAINED,
            device=self._device,
        )
        self._tokenizer = open_clip.get_tokenizer(SIGLIP_MODEL)
        self._model.eval()

        if self._device == "cpu" and torch.backends.mps.is_available():
            self._device = "mps"
            self._model = self._model.to("mps")
            print("[embed] SigLIP 2 moved to MPS (Apple Silicon).")
        print("[embed] SigLIP 2 loaded.")

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

            batch_tensor = torch.stack(images).to(self._device)
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
