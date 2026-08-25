"""Guard: CI Ruff job must lint scripts/, tests/, and agents_extensions/ (#7262)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.repo_invariant

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

# Required trees for the PR-tier Ruff job (dashboards/ may be empty).
_REQUIRED_RUFF_PATHS = ("scripts/", "tests/", "agents_extensions/")


def _ruff_check_invocation(ci_text: str) -> str:
    """Return the `ruff check …` command line from the ruff job step."""
    match = re.search(
        r"(?m)^[ \t]*python -m ruff check[^\n]*$",
        ci_text,
    )
    assert match is not None, (
        f"{_CI.as_posix()} has no `python -m ruff check …` invocation — "
        "the Ruff job must run ruff check against the repo Python trees"
    )
    return match.group(0)


def test_ci_ruff_job_lints_required_python_trees() -> None:
    """Fail if the Ruff job reverts to scripts-only (or drops tests/)."""
    ci_text = _CI.read_text(encoding="utf-8")
    invocation = _ruff_check_invocation(ci_text)
    missing = [path for path in _REQUIRED_RUFF_PATHS if path not in invocation]
    assert not missing, (
        f"Ruff CI invocation is missing required path(s) {missing!r}: {invocation!r}. "
        "Expected `python -m ruff check` to include scripts/, tests/, and agents_extensions/ "
        "(see #7262)."
    )
