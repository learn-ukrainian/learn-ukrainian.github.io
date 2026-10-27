"""Read-only dispatches that look up the local databases (#9122).

The stray ``data/vesum.db`` and ``data/sources.db`` that failed AGY read-only
reviews were created by the reviewer's own ad-hoc shell commands, which ran
``sqlite3.connect('data/vesum.db')`` relative to the sparse dispatch worktree.
That is a real checkout write, and the read-only guard must keep flagging it
without the primary database changing. A lookup through the ``sources`` MCP
resolves the primary's databases through the one resolver per database, opens
them read-only, and leaves the worktree untouched; with no database present it
fails typed and creates nothing.

These tests drive the real worktree creation, sparse profile, read-only guard
and MCP wire handler in a throwaway repository; they need no network, no
``origin`` and no host database.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import mcp  # noqa: F401  # Declares the Sources wire dependency to the CI fastlane.
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


_DATABASES = ("vesum.db", "sources.db")

# What dispatch records for a read-only Gemini Flash Ukrainian review (#9275).


# The commands the AGY reviewers ran in review-8843-sent-1 and -5: ad-hoc
# Python opening the database relative to the worktree cwd.


# A worker that looks words and chunks up through the real sources MCP wire
# handler. The server code lives in this test checkout, so its resolvers are
# anchored at the fixture dispatch worktree (cwd) the way they are anchored at
# the server's own checkout in production; resolution itself is unpatched.


@pytest.mark.parametrize("name", _DATABASES)
def test_read_only_database_openers_never_create_a_missing_file(tmp_path: Path, name: str) -> None:
    """With no database present, the repository openers fail typed and create nothing."""
    from scripts.verification.vesum import get_vesum_connection
    from scripts.wiki.sources_db import _open_conn

    missing = tmp_path / "data" / name
    missing.parent.mkdir()

    if name == "vesum.db":
        with pytest.raises(FileNotFoundError, match="VESUM database not found"), get_vesum_connection(missing):
            pass
    else:
        with pytest.raises(sqlite3.OperationalError, match="unable to open database file"):
            _open_conn(missing, read_only=True)

    assert not missing.exists()
    assert list(missing.parent.iterdir()) == []
