"""Grok formal review uses ACP; unsupported native isolation stays closed."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.review.isolation import ReviewIsolationError, prepare_isolated_review_launch


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
