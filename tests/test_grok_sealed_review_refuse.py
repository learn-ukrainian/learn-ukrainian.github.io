"""Grok sealed formal review is fail-closed (#5557)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.review.isolation import ReviewIsolationError, prepare_isolated_review_launch


def test_grok_endpoint_not_formal_review_eligible() -> None:
    from scripts.fleet_comms.endpoints import load_endpoint_registry

    registry = load_endpoint_registry()
    endpoint, _ = registry.resolve("grok")
    assert endpoint.formal_review_eligible is False


def test_grok_isolated_review_refuses_explicitly(tmp_path: Path) -> None:
    with pytest.raises(ReviewIsolationError, match="grok_isolated_review_unsupported"):
        prepare_isolated_review_launch(
            engine="grok",
            argv=["grok", "-p", "review"],
            snapshot_root=tmp_path / "snap",
            reject_root=tmp_path / "reject",
            write_root=tmp_path / "write",
            exec_root=tmp_path / "exec",
        )
