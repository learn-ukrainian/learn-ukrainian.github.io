from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from tests.helpers.python import project_python

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = project_python()
EMBED_SCRIPT = PROJECT_ROOT / "scripts" / "rag" / "benchmark_embeddings.py"


def _wait_for_lock(lock_path: Path, timeout_s: float = 60.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if lock_path.exists() and lock_path.read_text().strip():
            return
        time.sleep(0.05)
    raise AssertionError(f"Lock file {lock_path} was not populated in time")


def test_lockfile_conflict_uses_clear_message(tmp_path):
    lock_path = tmp_path / "benchmark.lock"
    env = os.environ.copy()
    env["BENCHMARK_DRY_RUN_HOLD_SECS"] = "120"

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
            timeout=30
        )
        assert second.returncode != 0
        combined_output = f"{second.stdout}\n{second.stderr}"
        assert "another embedder benchmark is running" in combined_output
        assert "Refusing to start" in combined_output
    finally:
        if first.poll() is None:
            first.terminate()
        first.wait(timeout=10)
