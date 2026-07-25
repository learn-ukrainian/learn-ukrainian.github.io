from __future__ import annotations

import os
import subprocess
import sys
import time
import types
from pathlib import Path
from unittest.mock import patch

from scripts.rag import benchmark_embeddings, benchmark_rerankers

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = PROJECT_ROOT / ".venv" / "bin" / "python"
EMBED_SCRIPT = PROJECT_ROOT / "scripts" / "rag" / "benchmark_embeddings.py"


def _wait_for_lock(lock_path: Path, timeout_s: float = 5.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if lock_path.exists() and lock_path.read_text().strip():
            return
        time.sleep(0.05)
    raise AssertionError(f"Lock file {lock_path} was not populated in time")


def test_lockfile_conflict_uses_clear_message(tmp_path):
    lock_path = tmp_path / "benchmark.lock"
    env = os.environ.copy()
    env["BENCHMARK_DRY_RUN_HOLD_SECS"] = "2"

    first = subprocess.Popen(
        [
            str(PYTHON_BIN),
            str(EMBED_SCRIPT),
            "--dry-run",
            "--model",
            "jina",
            "--lock-file",
            str(lock_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )

    try:
        _wait_for_lock(lock_path)
        second = subprocess.run(
            [
                str(PYTHON_BIN),
                str(EMBED_SCRIPT),
                "--dry-run",
                "--model",
                "jina",
                "--lock-file",
                str(lock_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert second.returncode != 0
        combined_output = f"{second.stdout}\n{second.stderr}"
        assert "another embedder benchmark is running" in combined_output
        assert "Refusing to start" in combined_output
    finally:
        first.wait(timeout=10)


def test_cli_flag_parsing():
    embed_args = benchmark_embeddings.parse_args(
        ["--model", "jina", "--sample-size", "123", "--lock-file", "/tmp/embed.lock", "--dry-run"]
    )
    assert embed_args.model == "jina"
    assert embed_args.sample_size == 123
    assert embed_args.lock_file == "/tmp/embed.lock"
    assert embed_args.dry_run is True

    rerank_args = benchmark_rerankers.parse_args(
        [
            "--model",
            "bge-reranker-v2-m3",
            "--sample-size",
            "7",
            "--lock-file",
            "/tmp/reranker.lock",
            "--dry-run",
        ]
    )
    assert rerank_args.model == "bge-reranker-v2-m3"
    assert rerank_args.sample_size == 7
    assert rerank_args.lock_file == "/tmp/reranker.lock"
    assert rerank_args.dry_run is True


def test_embedder_dry_run_skips_model_loading(tmp_path, capsys):
    lock_path = tmp_path / "embed.lock"

    # Same treatment as the reranker case below: patching `transformers.AutoModel`
    # forced an import of the real `transformers`, and therefore torch, which CI
    # deliberately does not install. `scripts/rag/benchmark_embeddings.py` imports
    # `AutoModel`/`AutoTokenizer` lazily inside the encoder (line ~448), so a
    # `sys.modules` stand-in is sufficient and works with or without the ML stack.
    from_pretrained_calls: list[tuple] = []
    fake_transformers = types.ModuleType("transformers")

    class _StandInAutoModel:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            from_pretrained_calls.append((args, kwargs))
            return None

    class _StandInAutoTokenizer:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            from_pretrained_calls.append((args, kwargs))
            return None

    fake_transformers.AutoModel = _StandInAutoModel
    fake_transformers.AutoTokenizer = _StandInAutoTokenizer

    with patch.dict(sys.modules, {"transformers": fake_transformers}):
        exit_code = benchmark_embeddings.main(
            ["--dry-run", "--model", "gemma", "--lock-file", str(lock_path)]
        )
    assert exit_code == 0
    assert from_pretrained_calls == [], (
        f"dry run must not load a model, got {from_pretrained_calls}"
    )
    output = capsys.readouterr().out
    assert "would benchmark" in output
    assert "gemma" in output


def test_reranker_dry_run_skips_model_loading(tmp_path, capsys):
    lock_path = tmp_path / "reranker.lock"

    # This test asserts the dry-run path never constructs the model. It used to
    # prove that by patching `sentence_transformers.CrossEncoder.__init__`, which
    # forced an import of the real package — and therefore of torch (~2.5GB),
    # which CI deliberately does not install.
    #
    # Inject a stand-in module instead. `scripts/rag/benchmark_rerankers.py`
    # imports CrossEncoder LAZILY inside the wrapper, and `--dry-run` returns via
    # `print_dry_run_plan` without touching it, so replacing the module in
    # `sys.modules` is sufficient.
    #
    # This is a STRICTLY STRONGER check than the old patch: it holds whether or not
    # the ML stack is installed, and if the dry run ever regressed into loading a
    # model it would fail here even on a machine with no torch at all.
    instantiations: list[tuple] = []
    fake_sentence_transformers = types.ModuleType("sentence_transformers")

    class _StandInCrossEncoder:
        def __init__(self, *args, **kwargs):
            instantiations.append((args, kwargs))

    fake_sentence_transformers.CrossEncoder = _StandInCrossEncoder

    with patch.dict(sys.modules, {"sentence_transformers": fake_sentence_transformers}):
        exit_code = benchmark_rerankers.main(
            [
                "--dry-run",
                "--model",
                "bge-reranker-v2-m3",
                "--lock-file",
                str(lock_path),
            ]
        )
    assert exit_code == 0
    assert instantiations == [], f"dry run must not construct a model, got {instantiations}"
    output = capsys.readouterr().out
    assert "would load model bge-reranker-v2-m3" in output
    assert "50 candidates" in output
