"""MLX BGE-M3 encoder worker. Runs inside embed-venv. Communicates via JSON frames on stdin/stdout.

Protocol:
  stdin  : one JSON object per line, e.g. {"op": "encode", "texts": [...], "max_length": 512}
  stdout : one JSON object per line, e.g. {"ok": true, "dtype": "float16", "shape": [N, 1024], "data_b64": "..."}
  stderr : log messages (main bridge doesn't parse)
  exit on {"op": "shutdown"} or EOF
"""

from __future__ import annotations

import base64
import gc
import json
import os
import sys
import traceback
from typing import Any

import mlx.core as mx
import numpy as np
from mlx_embeddings import load

MODEL_NAME = "mlx-community/bge-m3-mlx-fp16"
EMBEDDING_DIMS = 1024

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def _log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _emit(frame: dict[str, Any]) -> None:
    print(json.dumps(frame, ensure_ascii=False), flush=True)


def _configure_memory_limit() -> None:
    info = mx.metal.device_info()
    recommended = info.get("max_recommended_working_set_size")
    if recommended is None:
        return
    mx.metal.set_memory_limit(int(recommended * 0.7))


class MLXEncoderWorker:
    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None

    def _ensure_model(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return
        self._model, self._tokenizer = load(MODEL_NAME)

    def encode(self, texts: list[str], max_length: int) -> dict[str, Any]:
        if not texts:
            empty = np.zeros((0, EMBEDDING_DIMS), dtype=np.float16)
            return self._serialize(empty)

        self._ensure_model()
        assert self._tokenizer is not None
        assert self._model is not None

        inputs = self._tokenizer.batch_encode_plus(
            texts,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="np",
        )
        model_inputs = {
            "input_ids": mx.array(inputs["input_ids"]),
            "attention_mask": mx.array(inputs["attention_mask"]),
        }
        if "token_type_ids" in inputs:
            model_inputs["token_type_ids"] = mx.array(inputs["token_type_ids"])

        output = self._model(**model_inputs)
        cls = output.last_hidden_state[:, 0, :]
        norms = mx.sqrt(mx.sum(cls * cls, axis=1, keepdims=True))
        vectors = (cls / mx.maximum(norms, 1e-12)).astype(mx.float16)
        mx.eval(vectors)
        array = np.ascontiguousarray(np.asarray(vectors))
        return self._serialize(array)

    @staticmethod
    def _serialize(array: np.ndarray) -> dict[str, Any]:
        return {
            "ok": True,
            "dtype": str(array.dtype),
            "shape": list(array.shape),
            "data_b64": base64.b64encode(array.tobytes()).decode("ascii"),
        }


def main() -> int:
    try:
        _configure_memory_limit()
    except Exception as exc:  # pragma: no cover - startup diagnostics only
        _log(f"failed to configure MLX memory limit: {exc}")

    worker = MLXEncoderWorker()
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            op = request.get("op")
            if op == "shutdown":
                return 0
            if op != "encode":
                raise ValueError(f"unsupported op: {op!r}")

            texts = request.get("texts")
            if not isinstance(texts, list) or any(not isinstance(text, str) for text in texts):
                raise TypeError("'texts' must be a list[str]")

            max_length = int(request.get("max_length", 512))
            if max_length <= 0:
                raise ValueError("'max_length' must be positive")

            _emit(worker.encode(texts, max_length))
        except Exception as exc:
            _log(f"worker error: {exc}")
            traceback.print_exc(file=sys.stderr)
            _emit({"ok": False, "error": str(exc)})
        finally:
            mx.metal.clear_cache()
            gc.collect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
