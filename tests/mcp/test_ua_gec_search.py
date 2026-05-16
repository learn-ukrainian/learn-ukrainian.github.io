import asyncio
import sys
from pathlib import Path

import pytest

# Add the server directory to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / ".mcp" / "servers" / "sources"))

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

@pytest.mark.asyncio
async def test_search_ua_gec_errors_execution(server_module):
    # Test execution against the real database
    arguments = {"query": "коментарій", "limit": 5}
    result = await server_module.call_tool("search_ua_gec_errors", arguments)

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Found" in result[0].text
    assert "коментарій" in result[0].text
    assert "### Result 1" in result[0].text
    assert "Correction" in result[0].text
