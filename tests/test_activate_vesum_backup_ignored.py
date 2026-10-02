"""The VESUM activation backup must be gitignored.

An activation leaves a timestamped copy of the previous store next to
``data/vesum.db``. If ``.gitignore`` does not cover that name, the primary
checkout turns dirty and ``delegate.py`` refuses every write-capable dispatch
(seen 2026-09-30 after the #9349 activation). The name comes from the tool's own
helper, so a rename on either side fails this test.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.rag.activate_vesum_db import backup_path_for

REPO_ROOT = Path(__file__).resolve().parents[1]


def _ignored(relative: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "--no-index", "-q", relative],
        capture_output=True,
        check=False,
        timeout=30,
    )
    return result.returncode == 0


def test_backup_name_is_timestamped_beside_target() -> None:
    target = Path("data/vesum.db")
    backup = backup_path_for(target, datetime(2026, 9, 30, 23, 53, 46, tzinfo=UTC))
    assert backup == Path("data/vesum.db.bak.20260930_235346")


@pytest.mark.parametrize(
    "now",
    [
        datetime(2026, 9, 30, 23, 53, 46, tzinfo=UTC),
        datetime(2027, 1, 2, 3, 4, 5, tzinfo=UTC),
    ],
)
def test_activation_backup_is_gitignored(now: datetime) -> None:
    backup = backup_path_for(Path("data/vesum.db"), now)
    assert _ignored(backup.as_posix()), f"{backup} is not gitignored; the primary checkout would turn dirty"


def test_latest_backup_pointer_is_gitignored() -> None:
    assert _ignored("data/vesum.db.bak")


def test_live_store_stays_ignored_and_tracked_data_is_not_swept() -> None:
    assert _ignored("data/vesum.db")
    # The new pattern is scoped to database backups, not to other data files.
    assert not _ignored("data/vesum_notes.md")
