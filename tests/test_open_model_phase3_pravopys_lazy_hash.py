"""Lazy pinned-receipt hash: thread-safe first use, raise on missing (#8581).

These tests monkeypatch the receipt path into tmp_path, so they need no
sparse-excluded tree and run identically in full and sparse worktrees.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_evaluation_context_manifest as eval_manifest
from scripts.projects.open_model_data import phase3_pravopys_evaluation_context as prav_context

_PINNED_NAME = "PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_FILE_SHA256"


@pytest.fixture
def _cleared_pinned_cache():
    prav_context.__dict__.pop(_PINNED_NAME, None)
    try:
        yield
    finally:
        prav_context.__dict__.pop(_PINNED_NAME, None)


def test_first_use_is_thread_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _cleared_pinned_cache: None
) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_bytes(b'{"ok": true}\n')
    monkeypatch.setattr(prav_context, "_PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_PATH", receipt)
    real_sha256_file = eval_manifest.sha256_file
    calls: list[Path] = []
    calls_lock = threading.Lock()

    def counting_sha256_file(path: Path) -> str:
        with calls_lock:
            calls.append(path)
        # Widen the race window: without the lock in the helper, both threads
        # observe the empty cache and hash concurrently.
        time.sleep(0.2)
        return real_sha256_file(path)

    monkeypatch.setattr(eval_manifest, "sha256_file", counting_sha256_file)

    start = threading.Barrier(2)
    results: list[str] = []
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            start.wait(timeout=10)
            results.append(prav_context._pinned_evaluation_context_manifest_receipt_file_sha256())
        except BaseException as exc:  # surfaced by the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert not errors
    assert results == [real_sha256_file(receipt)] * 2
    assert len(calls) == 1


def test_missing_receipt_raises_on_first_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _cleared_pinned_cache: None
) -> None:
    missing = tmp_path / "absent-receipt.json"
    monkeypatch.setattr(prav_context, "_PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_PATH", missing)
    with pytest.raises(eval_manifest.EvaluationContextManifestError, match="cannot read artifact"):
        prav_context._pinned_evaluation_context_manifest_receipt_file_sha256()
    # The module attribute must raise the same way — never return "".
    with pytest.raises(eval_manifest.EvaluationContextManifestError, match="cannot read artifact"):
        getattr(prav_context, _PINNED_NAME)
