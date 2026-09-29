"""Backward-compatible ``project_python`` shim.

Prefer ``tests.helpers.python.project_python`` for new code. This module is
kept so the ~20 existing importers keep working while the canonical helper
lives in one place. It returns the interpreter running pytest (``sys.executable``),
never a checkout-relative ``.venv`` (issue #8788).
"""

from __future__ import annotations

from pathlib import Path

from tests.helpers.python import project_python as _project_python


def project_python() -> Path:
    """The interpreter running pytest, as a ``Path`` (see tests.helpers.python)."""
    return Path(_project_python())
