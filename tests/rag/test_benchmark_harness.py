from __future__ import annotations

import os
import subprocess
import time
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
    with patch("transformers.AutoModel.from_pretrained") as mock_from_pretrained:
        exit_code = benchmark_embeddings.main(
            ["--dry-run", "--model", "gemma", "--lock-file", str(lock_path)]
        )
    assert exit_code == 0
    assert mock_from_pretrained.call_count == 0
    output = capsys.readouterr().out
    assert "would benchmark" in output
    assert "gemma" in output


def test_reranker_dry_run_skips_model_loading(tmp_path, capsys):
    lock_path = tmp_path / "reranker.lock"
    with patch("sentence_transformers.CrossEncoder.__init__", return_value=None) as mock_init:
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
    assert mock_init.call_count == 0
    output = capsys.readouterr().out
    assert "would load model bge-reranker-v2-m3" in output
    assert "50 candidates" in output
