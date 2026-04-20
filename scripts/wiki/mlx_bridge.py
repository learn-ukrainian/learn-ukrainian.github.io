"""Subprocess bridge for the isolated MLX embedding worker."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import threading
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMBED_PYTHON = PROJECT_ROOT / "embed-venv" / "bin" / "python"
WORKER_SCRIPT = PROJECT_ROOT / "scripts" / "wiki" / "mlx_encoder.py"
EMBEDDING_DIMS = 1024
MAX_RETRIES = 3


class WorkerCrashedError(RuntimeError):
    """Raised when the MLX subprocess exits unexpectedly."""


class MLXEncoderBridge:
    """Encode text batches through an isolated MLX worker process."""

    def __init__(
        self,
        *,
        worker_python: Path = EMBED_PYTHON,
        worker_script: Path = WORKER_SCRIPT,
    ) -> None:
        self._worker_python = worker_python
        self._worker_script = worker_script
        self._process: subprocess.Popen[str] | None = None
        # Serialize encode() calls — stdin/stdout framing is NOT thread-safe.
        # search_sources fans out to 5 per-corpus workers via ThreadPoolExecutor,
        # each calling rerank_candidates → _get_encoder().encode(query). Without
        # this lock, interleaved writes deadlock or return garbled responses.
        self._io_lock = threading.Lock()

    def __enter__(self) -> MLXEncoderBridge:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def encode(
        self,
        texts: list[str],
        batch_size: int = 16,
        max_length: int = 512,
    ) -> NDArray[np.float16]:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if max_length <= 0:
            raise ValueError("max_length must be positive")
        if not texts:
            return np.zeros((0, EMBEDDING_DIMS), dtype=np.float16)

        chunks: list[NDArray[np.float16]] = []
        index = 0
        effective_batch_size = batch_size
        retries = 0

        # Serialize across callers: stdin/stdout framing is NOT thread-safe,
        # and search_sources fans out to 5 per-corpus threads that each call
        # rerank_candidates → _get_encoder().encode(query). Without this lock
        # the interleaved writes deadlock or return garbled responses.
        with self._io_lock:
            while index < len(texts):
                end = min(index + effective_batch_size, len(texts))
                batch = texts[index:end]
                try:
                    chunk = self._encode_batch(batch, max_length=max_length)
                except WorkerCrashedError as exc:
                    retries += 1
                    self._restart_worker()
                    effective_batch_size = max(1, effective_batch_size // 2)
                    if retries > MAX_RETRIES:
                        raise RuntimeError(
                            f"MLX worker crashed {retries} times while encoding batch at index {index}"
                        ) from exc
                    continue

                chunks.append(chunk)
                index = end
                retries = 0

        return np.concatenate(chunks, axis=0).astype(np.float16, copy=False)

    def close(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        if process.poll() is not None:
            return
        try:
            assert process.stdin is not None
            process.stdin.write(json.dumps({"op": "shutdown"}) + "\n")
            process.stdin.flush()
        except OSError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def _encode_batch(self, texts: list[str], *, max_length: int) -> NDArray[np.float16]:
        process = self._ensure_worker()
        request = {"op": "encode", "texts": texts, "max_length": max_length}

        try:
            assert process.stdin is not None
            process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
            process.stdin.flush()
        except OSError as exc:
            raise self._worker_crashed_error(process, "failed to write request") from exc

        response = self._read_response(process)
        if not response.get("ok", False):
            error = response.get("error", "unknown worker error")
            raise RuntimeError(f"MLX worker returned an error frame: {error}")

        return self._decode_array(response, expected_rows=len(texts))

    def _ensure_worker(self) -> subprocess.Popen[str]:
        process = self._process
        if process is not None and process.poll() is None:
            return process
        if process is not None and process.poll() is not None:
            self._process = None
        self._process = self._start_worker()
        return self._process

    def _start_worker(self) -> subprocess.Popen[str]:
        if not self._worker_python.exists():
            raise FileNotFoundError(f"embed worker python not found at {self._worker_python}")
        if not self._worker_script.exists():
            raise FileNotFoundError(f"embed worker script not found at {self._worker_script}")

        env = os.environ.copy()
        env.setdefault("TOKENIZERS_PARALLELISM", "false")

        return subprocess.Popen(
            [str(self._worker_python), str(self._worker_script)],
            cwd=str(PROJECT_ROOT),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def _read_response(self, process: subprocess.Popen[str]) -> dict[str, Any]:
        assert process.stdout is not None
        line = process.stdout.readline()
        if line:
            try:
                return json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"invalid JSON from MLX worker: {line!r}") from exc
        raise self._worker_crashed_error(process, "worker closed stdout before responding")

    def _decode_array(self, response: dict[str, Any], *, expected_rows: int) -> NDArray[np.float16]:
        dtype = response.get("dtype")
        shape = response.get("shape")
        payload = response.get("data_b64")

        if dtype != "float16":
            raise RuntimeError(f"unexpected worker dtype: {dtype!r}")
        if not isinstance(shape, list) or len(shape) != 2:
            raise RuntimeError(f"unexpected worker shape: {shape!r}")
        if shape[0] != expected_rows:
            raise RuntimeError(f"worker returned {shape[0]} rows for {expected_rows} texts")
        if not isinstance(payload, str):
            raise RuntimeError("worker response missing base64 payload")

        raw = base64.b64decode(payload.encode("ascii"))
        array = np.frombuffer(raw, dtype=np.float16)
        return array.reshape(shape).copy()

    def _restart_worker(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)

    @staticmethod
    def _worker_crashed_error(process: subprocess.Popen[str], context: str) -> WorkerCrashedError:
        returncode = process.poll()
        stderr_output = ""
        if process.stderr is not None and returncode is not None:
            stderr_output = process.stderr.read().strip()
        details = f"{context}; returncode={returncode}"
        if stderr_output:
            details = f"{details}; stderr={stderr_output}"
        return WorkerCrashedError(details)
