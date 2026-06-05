"""Path-traversal regression tests for the session API router.

Covers the ``py/path-injection`` HIGH alerts (CodeQL) on
``scripts/api/session_router.py``: the ``?agent=`` query param flows into a
filesystem read, so a resolved path must never escape ``PROJECT_ROOT``.

Hermetic — no network, no fixtures, no model downloads.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from scripts.api.config import PROJECT_ROOT
from scripts.api.session_router import _read_session_file, _safe_project_path


def test_safe_path_accepts_in_root():
    resolved = _safe_project_path("docs/session-state/current.md")
    assert str(resolved).startswith(str(PROJECT_ROOT.resolve()))


def test_safe_path_accepts_root_itself():
    # An empty/dot rel-path resolves to the root and must be allowed.
    assert _safe_project_path(".") == PROJECT_ROOT.resolve()


@pytest.mark.parametrize(
    "evil",
    [
        "../../../../etc/passwd",
        "docs/../../etc/passwd",
        "/etc/passwd",
        "docs/session-state/../../../../../etc/shadow",
        "../.ssh/id_rsa",
    ],
)
def test_safe_path_rejects_escape(evil):
    with pytest.raises(HTTPException) as exc:
        _safe_project_path(evil)
    assert exc.value.status_code == 400


def test_read_session_file_rejects_escape():
    # The escape must be caught by the containment barrier (400), never read.
    with pytest.raises(HTTPException) as exc:
        _read_session_file("../../../../etc/passwd")
    assert exc.value.status_code == 400


def test_safe_path_rejects_sibling_prefix():
    # A sibling directory that shares PROJECT_ROOT's name as a string prefix
    # (e.g. /…/learn-ukrainian-evil vs /…/learn-ukrainian) must be rejected.
    # Guards the trailing-os.sep in the containment check — a plain
    # startswith(root) without the separator would let this through.
    root = PROJECT_ROOT.resolve()
    sibling = f"../{root.name}-evil/secret"
    with pytest.raises(HTTPException) as exc:
        _safe_project_path(sibling)
    assert exc.value.status_code == 400
