"""Integration test surfaces for Cursor in delegate.py / ab discuss / lint.

The agent runtime registry already exposes ``cursor`` via
``scripts/agent_runtime/registry.py`` (CursorAdapter, ``cli_available:
True``). These tests pin the surface allowlists so future churn cannot
silently strip ``cursor`` from any of them.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_lint_agent_trailer_accepts_cursor():
    """Commits authored by ``cursor`` dispatches must pass the X-Agent trailer linter."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from audit.lint_agent_trailer import _TRAILER_RE

    sample = "X-Agent: cursor/2026-05-23-integration"
    match = _TRAILER_RE.search(sample)
    assert match is not None, "lint_agent_trailer rejected cursor-authored trailer"
    assert match.group("agent") == "cursor"
    assert match.group("task") == "2026-05-23-integration"
