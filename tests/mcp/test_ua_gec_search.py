import asyncio
import sqlite3
import sys
from pathlib import Path

import pytest

# Add the server directory to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / ".mcp" / "servers" / "sources"))

# CI's sources.db doesn't ship the ua_gec_errors_fts table (the ingest is
# run locally + the table is committed in the canonical sources.db via
# GDrive sync, not regenerated in CI). Skip data-dependent tests when
# the table is absent rather than fail; structural tests (list/schema)
# still run and catch tool-registration regressions.
_DB_PATH = PROJECT_ROOT / "data" / "sources.db"


def _ua_gec_table_present() -> bool:
    if not _DB_PATH.exists():
        return False
    try:
        conn = sqlite3.connect(_DB_PATH)
        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type IN ('table', 'view') AND name = 'ua_gec_errors_fts'",
            ).fetchone()
        finally:
            conn.close()
        return row is not None
    except sqlite3.Error:
        return False


requires_ua_gec_data = pytest.mark.skipif(
    not _ua_gec_table_present(),
    reason="ua_gec_errors_fts not present in sources.db (CI / fresh checkout)",
)

@pytest.fixture
def server_module():
    if "server" in sys.modules:
        del sys.modules["server"]
    import server as srv
    return srv

def _run(coro):
    return asyncio.run(coro)

def test_search_ua_gec_errors_listed(server_module):
    tools = _run(server_module.list_tools())
    tool_names = {t.name for t in tools}
    assert "search_ua_gec_errors" in tool_names

def test_search_ua_gec_errors_schema(server_module):
    tools = _run(server_module.list_tools())
    tool = next(t for t in tools if t.name == "search_ua_gec_errors")
    assert "query" in tool.inputSchema["required"]
    assert "tag_filter" in tool.inputSchema["properties"]
    assert "require_native_author" in tool.inputSchema["properties"]

@requires_ua_gec_data
def test_search_ua_gec_errors_execution(server_module):
    # Test execution against the real database.
    # Project pytest config has no pytest-asyncio plugin, so use the
    # _run() helper above (already used by the sibling list/schema tests)
    # rather than `async def` + @pytest.mark.asyncio (which silently no-ops
    # without the plugin — the CI failure that blocked this PR).
    arguments = {"query": "коментарій", "limit": 5}
    result = _run(server_module.call_tool("search_ua_gec_errors", arguments))

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Found" in result[0].text
    assert "коментарій" in result[0].text
    assert "### Result 1" in result[0].text
    assert "Correction" in result[0].text
