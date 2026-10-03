"""Schema-only Pohribnyi fixtures copied from the live read-only DDL."""

import sqlite3
from pathlib import Path


def open_schema_copy(path: Path) -> sqlite3.Connection:
    """Replay textbook/section/FTS DDL and triggers without copying corpus rows."""
    # The checked-in schema-only fixture is extracted from the live DDL,
    # including FTS and source triggers. It keeps these tests portable in CI.
    ddl = Path(__file__).with_name("fixtures") / "pohribnyi_sources_schema.sql"
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.executescript(ddl.read_text(encoding="utf-8"))
    assert conn.execute("SELECT count(*) FROM sqlite_master WHERE name='textbooks_fts'").fetchone()[0] == 1
    assert conn.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger' AND tbl_name='textbooks'").fetchone()[0]
    return conn
