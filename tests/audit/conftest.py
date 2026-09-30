"""Shared fixtures for the post-build-review test modules."""

from __future__ import annotations

import subprocess

import pytest


@pytest.fixture(scope="session")
def bilash_packet() -> dict:
    """The real Bilash packet, built once per process for both review modules.

    This is the end-to-end packet: it runs the real deterministic audit
    subprocesses and proves that preparation leaves the checkout untouched.
    Tests treat it as read-only and deep-copy before changing it.
    """
    from scripts.audit import post_build_review as pbr
    from tests.audit.test_post_build_review import ROOT, _artifact_snapshot, _reviewer

    def status() -> str:
        return subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            timeout=30,
        ).stdout

    before_status = status()
    before_artifacts = _artifact_snapshot()
    packet = pbr.prepare_review("bio/oleksandr-bilash", _reviewer())
    assert status() == before_status
    assert _artifact_snapshot() == before_artifacts
    return packet
