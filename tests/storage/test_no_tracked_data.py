"""Protect the tracked-data allowlist during the data/ split."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = REPO_ROOT / "registry/artifacts/tracked-data-allowlist.txt"


@pytest.mark.repo_wide
def test_tracked_data_paths_are_all_allowlisted() -> None:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "data"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        timeout=30,
    )
    tracked = {path.decode("utf-8") for path in result.stdout.split(b"\0") if path}
    allowed = {line for line in ALLOWLIST.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")}
    unauthorized = sorted(tracked - allowed)
    assert not unauthorized, (
        "tracked data paths absent from registry/artifacts/tracked-data-allowlist.txt:\n" + "\n".join(unauthorized)
    )
