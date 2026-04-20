from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAIN_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
EMBED_PYTHON = PROJECT_ROOT / "embed-venv" / "bin" / "python"
RSS_LIMIT_BYTES = 4 * 1024**3


def _slow_selected(request: pytest.FixtureRequest) -> bool:
    markexpr = request.config.getoption("-m")
    return isinstance(markexpr, str) and "slow" in markexpr


def _require_slow(request: pytest.FixtureRequest) -> None:
    if not _slow_selected(request):
        pytest.skip("slow test; run with `pytest -m slow`")


def _ensure_mlx_available() -> None:
    if not EMBED_PYTHON.exists():
        pytest.skip("embed-venv not installed")
    probe = subprocess.run(
        [str(EMBED_PYTHON), "-c", "import mlx.core, mlx_embeddings"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        details = (probe.stderr or probe.stdout).strip() or "unknown import failure"
        pytest.skip(f"MLX not importable in embed-venv: {details}")


def _synth_text(char_count: int, *, index: int) -> str:
    prefix = (
        f"Розділ {index}. Синтетичний навчальний уривок для навантажувального тесту. "
        "Тут немає справжнього підручникового тексту, лише штучний наповнювач. "
    )
    filler = (
        "вправа склад наголос приголосний голосний абзац приклад правило завдання "
        "текст сторінка учень учитель пояснення речення словник читання письмо "
    )
    parts = [prefix]
    while len("".join(parts)) < char_count:
        parts.append(filler)
    return "".join(parts)[:char_count]


def _char_counts() -> list[int]:
    start = 200
    stop = 50_000
    steps = 19
    return [round(start + (stop - start) * index / steps) for index in range(steps + 1)]


@pytest.mark.slow
def test_mlx_memory_safety_peak_child_rss_stays_below_4gb(
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> None:
    _require_slow(request)
    _ensure_mlx_available()

    texts_path = tmp_path / "stress_texts.json"
    helper_path = tmp_path / "measure_memory.py"
    texts = [_synth_text(char_count, index=index) for index, char_count in enumerate(_char_counts(), start=1)]
    texts_path.write_text(json.dumps(texts, ensure_ascii=False), encoding="utf-8")
    helper_path.write_text(
        """
from __future__ import annotations

import json
import resource
import sys
from pathlib import Path

root = Path(sys.argv[1])
texts_path = Path(sys.argv[2])
sys.path.insert(0, str(root / "scripts"))

from wiki import dense_rerank
from wiki.mlx_bridge import MLXEncoderBridge

texts = json.loads(texts_path.read_text(encoding="utf-8"))
with MLXEncoderBridge() as bridge:
    vectors = dense_rerank.encode_texts(
        texts,
        encoder=bridge,
        max_length=512,
        max_rows=16,
        max_tokens=4096,
    )

usage = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
rss_bytes = usage if sys.platform == "darwin" else usage * 1024
payload = {
    "shape": list(vectors.shape),
    "dtype": str(vectors.dtype),
    "peak_child_rss_raw": usage,
    "peak_child_rss_bytes": rss_bytes,
}
print(json.dumps(payload), flush=True)
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(MAIN_PYTHON), str(helper_path), str(PROJECT_ROOT), str(texts_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            "memory helper failed\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["shape"] == [20, 1024]
    assert payload["dtype"] == "float16"
    assert payload["peak_child_rss_bytes"] <= RSS_LIMIT_BYTES, payload
