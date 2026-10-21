"""Response and containment regressions for artifact path handling (#9648)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from scripts.api import docs_router


def test_docs_resolved_containment_rejects_escape(tmp_path: Path) -> None:
    root = tmp_path / "approved"
    root.mkdir()
    outside = tmp_path / "approved-sibling"
    outside.mkdir()
    target = outside / "outside.md"
    target.write_text("outside", encoding="utf-8")
    link = root / "escape.md"
    link.symlink_to(target)
    for path in (link, target, root / ".." / "approved-sibling" / "outside.md"):
        with pytest.raises(HTTPException) as error:
            docs_router._assert_under_root(path, root)
        assert error.value.status_code == 403

    inside = root / "inside.md"
    inside.write_text("inside", encoding="utf-8")
    link.unlink()
    link.symlink_to(inside)
    docs_router._assert_under_root(link, root)
    logical_root = tmp_path / "logical"
    logical_root.symlink_to(root, target_is_directory=True)
    docs_router._assert_under_root(logical_root / "inside.md", logical_root)
    assert docs_router._relative_to_root(logical_root / "inside.md", logical_root) == "inside.md"
