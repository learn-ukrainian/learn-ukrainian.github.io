"""Shared interpreter helpers for tests that spawn Python subprocesses.

Issue #8788: tests used to hard-code the repo-local ``.venv/bin/python`` and
fail in dispatch worktrees (which carry no ``.venv`` by design). The shared
interpreter contract is now: run pytest with the primary checkout's
``.venv/bin/python``, and let any test subprocess use the *same* interpreter
via ``sys.executable``. Never resolve a checkout-relative ``.venv`` path from a
test; a worktree has none.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]


def project_python() -> str:
    """The interpreter running pytest — the interpreter for test subprocesses.

    ``sys.executable`` is the primary checkout's ``.venv/bin/python`` when the
    suite runs via the shared-interpreter contract (``.venv/bin/python -m
    pytest``), so it carries every project dependency a spawned script needs.
    """
    return sys.executable


def require_repo_venv() -> Path:
    """Return ``<repo>/.venv/bin/python``, or skip when the repo venv is absent.

    Reserved for tests that deliberately exercise the checkout's own virtualenv
    (not merely "a Python with project deps"). Dispatch worktrees have no
    ``.venv``, so such a test skips there instead of failing on a missing file.
    """
    venv = _REPO_ROOT / ".venv" / "bin" / "python"
    if not venv.is_file():
        pytest.skip(f"repo virtualenv absent (dispatch worktree?): {venv}")
    return venv
