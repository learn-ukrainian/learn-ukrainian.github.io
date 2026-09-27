"""Fixture-only speedups for review tests that do not exercise crash durability."""

import os
from pathlib import Path

import pytest


@pytest.fixture
def without_disk_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep atomic replacements and integrity checks, but skip physical flushes."""
    monkeypatch.setattr(os, "fsync", lambda _fd: None)


@pytest.fixture(scope="session")
def review_world_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Immutable starting files shared by the record and fix-loop cases."""
    from tests.review.test_record import World

    root = tmp_path_factory.mktemp("review-world-template")
    patcher = pytest.MonkeyPatch()
    try:
        World(root, patcher)
    finally:
        patcher.undo()
    return root
