from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki.mlx_bridge import EMBED_PYTHON, EMBEDDING_DIMS, MAX_RETRIES, MLXEncoderBridge

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FAULT_LIMIT_BYTES = 104_857_600


def _fault_text(index: int, *, char_count: int = 2_000) -> str:
    prefix = f"Синтетичний fault-injection текст {index}. "
    filler = (
        "память обмеження пакет повторення місток кодування перевірка порядок рядок "
        "симуляція аварія навантаження обчислення "
    )
    parts = [prefix]
    while len("".join(parts)) < char_count:
        parts.append(filler)
    return "".join(parts)[:char_count]


def _expected_vectors(texts: list[str]) -> np.ndarray:
    rows: list[np.ndarray] = []
    for text in texts:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        row = np.frombuffer(digest * 64, dtype=np.uint8)[:EMBEDDING_DIMS].astype(np.float16)
        rows.append(row)
    return np.stack(rows, axis=0)


def test_mlx_fault_injection_halves_batch_and_preserves_row_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "worker-state.json"
    worker_path = tmp_path / "fault_worker.py"
    state_path.write_text(
        json.dumps({"memory_limit": None, "pids": [], "calls": [], "crashes": 0}),
        encoding="utf-8",
    )
    worker_path.write_text(
        """
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

root = Path(os.environ["MLX_TEST_PROJECT_ROOT"])
state_path = Path(os.environ["MLX_TEST_STATE_PATH"])
sys.path.insert(0, str(root / "scripts"))

from wiki import mlx_encoder

serialize = mlx_encoder.MLXEncoderWorker._serialize


def load_state() -> dict:
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    state_path.write_text(json.dumps(state), encoding="utf-8")


state = load_state()
state["pids"].append(os.getpid())
save_state(state)


def fake_set_memory_limit(limit: int) -> int:
    state = load_state()
    state["memory_limit"] = limit
    save_state(state)
    return 0


mlx_encoder.mx.metal.set_memory_limit = fake_set_memory_limit
mlx_encoder.mx.metal.device_info = lambda: {"max_recommended_working_set_size": 2 * 1024**3}
mlx_encoder.mx.metal.clear_cache = lambda: None


class FakeWorker:
    def encode(self, texts: list[str], max_length: int) -> dict:
        state = load_state()
        state["calls"].append({"batch_size": len(texts), "max_length": max_length})
        save_state(state)
        if len(texts) > 8:
            state = load_state()
            state["crashes"] += 1
            save_state(state)
            os._exit(137)

        vectors = np.zeros((len(texts), mlx_encoder.EMBEDDING_DIMS), dtype=np.float16)
        for row_index, text in enumerate(texts):
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vectors[row_index] = np.frombuffer(
                digest * 64,
                dtype=np.uint8,
            )[: mlx_encoder.EMBEDDING_DIMS].astype(np.float16)
        return serialize(vectors)


mlx_encoder.MLXEncoderWorker = FakeWorker

raise SystemExit(mlx_encoder.main())
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("MLX_MEMORY_LIMIT_BYTES", str(FAULT_LIMIT_BYTES))
    monkeypatch.setenv("MLX_TEST_PROJECT_ROOT", str(PROJECT_ROOT))
    monkeypatch.setenv("MLX_TEST_STATE_PATH", str(state_path))

    texts = [_fault_text(index) for index in range(16)]
    with MLXEncoderBridge(worker_python=EMBED_PYTHON, worker_script=worker_path) as bridge:
        vectors = bridge.encode(texts, batch_size=16, max_length=512)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    batch_sizes = [call["batch_size"] for call in state["calls"]]

    assert state["memory_limit"] == FAULT_LIMIT_BYTES
    assert 1 <= state["crashes"] <= MAX_RETRIES
    assert batch_sizes[:3] == [16, 8, 8], state
    assert len(set(state["pids"])) >= 2, state
    assert vectors.shape == (len(texts), EMBEDDING_DIMS)
    assert np.array_equal(vectors, _expected_vectors(texts))
