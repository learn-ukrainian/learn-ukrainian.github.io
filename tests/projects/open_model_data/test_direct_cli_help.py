"""Direct project CLIs keep working after the read-only SQLite import (#9662)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

DIRECT_ENTRY_POINTS = (
    "scripts/projects/open_model_data/phase3_university_reconciliation.py",
    "scripts/projects/open_model_data/source_work_locator_index.py",
    "scripts/projects/open_model_data/typesafe_homonym_disambiguator.py",
    "scripts/projects/open_model_data/typesafe_word_qualifier.py",
)


def test_direct_entry_points_accept_help() -> None:
    """Running the file directly must reach argparse --help."""
    failures: list[str] = []
    for relative in DIRECT_ENTRY_POINTS:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / relative), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if result.returncode != 0:
            failures.append(f"{relative}: exit {result.returncode}\n{result.stderr}")
    assert not failures, "\n".join(failures)
