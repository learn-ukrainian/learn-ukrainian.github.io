"""The native candidate sees and can call only reference tools in its condition."""

import pytest

from scripts.eval.zno_nmt.mcp_proxy import Bridge, decode_response


def test_tool_surface_and_forbidden_execution(monkeypatch):
    bridge = Bridge("http://example.invalid/mcp", ["verify_word"])
    requested = []

    def upstream(method, params, ident=1):
        requested.append(method)
        return {"result": {"tools": [{"name": "verify_word"}, {"name": "search_external"}]}}

    monkeypatch.setattr(bridge, "request", upstream)
    result = bridge.handle({"id": 1, "method": "tools/list"})
    assert result["result"]["tools"] == [{"name": "verify_word"}]
    for method, params in [("tools/call", {"name": "search_external"}), ("resources/read", {"uri": "key"})]:
        assert "error" in bridge.handle({"id": 2, "method": method, "params": params})
    assert requested == ["tools/list"]


def test_call_budget_blocks_before_upstream(monkeypatch):
    bridge = Bridge("http://example.invalid/mcp", ["verify_word"], max_tool_calls=1)
    calls = []

    def upstream(*args):
        calls.append(args)
        return {"result": {"content": []}}

    monkeypatch.setattr(bridge, "request", upstream)
    message = {"id": 1, "method": "tools/call", "params": {"name": "verify_word", "arguments": {"word": "x"}}}
    assert "result" in bridge.handle(message)
    assert "error" in bridge.handle(message)
    assert len(calls) == 1


def test_unavailable_tool_refuses_instead_of_weakening(monkeypatch):
    bridge = Bridge("http://example.invalid/mcp", ["verify_word"])
    monkeypatch.setattr(bridge, "request", lambda *args: {"result": {"tools": []}})
    with pytest.raises(ValueError, match="unavailable"):
        bridge.handle({"id": 1, "method": "tools/list"})


def test_cannot_allow_arbitrary_tools():
    with pytest.raises(ValueError, match="allowlist"):
        Bridge("http://example.invalid/mcp", ["search_external"])


def test_mcp_json_and_sse():
    expected = {"jsonrpc": "2.0", "id": 1, "result": {}}
    assert decode_response(b'{"jsonrpc":"2.0","id":1,"result":{}}') == expected
    assert decode_response(b'event: message\r\ndata: {"jsonrpc":"2.0","id":1,"result":{}}\r\n\r\n') == expected
