"""Filtered stdio MCP bridge; no corpus material is written to disk.

Invoked by a trusted native candidate harness, never by the candidate itself.
The endpoint is read from an environment variable and never advertised as a tool.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

REFERENCE_TOOLS = frozenset({
    "verify_word", "verify_words", "verify_lemma", "verify_stress", "search_text",
    "get_chunk_context", "query_pravopys", "search_style_guide", "search_definitions",
    "search_idioms", "search_synonyms", "check_modern_form", "search_literary",
})
MAX_BYTES = 2_000_000


def decode_response(raw: bytes) -> dict:
    text = raw.decode("utf-8")
    if text.lstrip().startswith("{"):
        return json.loads(text)
    for event in text.replace("\r\n", "\n").split("\n\n"):
        payload = "\n".join(line[5:].lstrip() for line in event.splitlines() if line.startswith("data:"))
        if payload:
            result = json.loads(payload)
            if isinstance(result, dict) and ("result" in result or "error" in result):
                return result
    raise ValueError("missing MCP result")


class Bridge:
    def __init__(self, url: str, allowed: list[str], timeout: float = 20, max_tool_calls: int = 20):
        if not allowed or len(set(allowed)) != len(allowed) or not set(allowed) <= REFERENCE_TOOLS:
            raise ValueError("invalid reference tool allowlist")
        self.url = url
        self.allowed = allowed
        self.timeout = timeout
        self.max_tool_calls = max_tool_calls
        self.calls = 0
        self.headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        self.schemas: dict = {}

    def request(self, method: str, params: dict, ident: int | str | None = 1) -> dict:
        data = {"jsonrpc": "2.0", "method": method, "params": params}
        if ident is not None:
            data["id"] = ident
        request = urllib.request.Request(self.url, data=json.dumps(data).encode(), headers=self.headers)
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            session = response.headers.get("Mcp-Session-Id")
            if session:
                self.headers["Mcp-Session-Id"] = session
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("MCP response exceeds limit")
            if ident is None or not raw:
                return {}
            return decode_response(raw)

    def handle(self, message: dict) -> dict | None:
        ident = message.get("id")
        method = message.get("method")
        params = message.get("params", {})
        if ident is None:
            if method == "notifications/initialized":
                self.request(method, {}, None)
            return None
        if method == "initialize":
            result = self.request("initialize", params, ident)
            if "error" in result:
                raise ValueError("upstream MCP initialization failed")
            version = result["result"]["protocolVersion"]
            self.headers["MCP-Protocol-Version"] = version
            body = {"protocolVersion": version, "capabilities": {"tools": {}},
                    "serverInfo": {"name": "exam-reference-filter", "version": "1"}}
        elif method == "ping":
            body = {}
        elif method == "tools/list":
            upstream = self.request("tools/list", {})
            tools = upstream.get("result", {}).get("tools", [])
            by_name = {tool["name"]: tool for tool in tools}
            if not set(self.allowed) <= by_name.keys():
                raise ValueError("requested reference tools unavailable")
            self.schemas = by_name
            body = {"tools": [by_name[name] for name in self.allowed]}
        elif method == "tools/call":
            if params.get("name") not in self.allowed:
                return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32602, "message": "Tool not permitted"}}
            if not isinstance(params.get("arguments", {}), dict):
                raise ValueError("tool arguments must be an object")
            if self.calls >= self.max_tool_calls:
                return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32602, "message": "Reference call limit reached"}}
            self.calls += 1
            upstream = self.request(method, params, ident)
            if "error" in upstream:
                # Do not forward transport diagnostics containing private endpoints.
                body = {"isError": True, "content": [{"type": "text", "text": "Reference lookup failed"}]}
            else:
                body = upstream["result"]
        else:
            return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32601, "message": "Method not permitted"}}
        return {"jsonrpc": "2.0", "id": ident, "result": body}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url-env", required=True)
    parser.add_argument("--tools", required=True, help="JSON array of reference tool names")
    parser.add_argument("--max-tool-calls", type=int, default=20)
    args = parser.parse_args()
    try:
        if args.max_tool_calls < 1:
            raise ValueError("positive call budget required")
        bridge = Bridge(os.environ[args.url_env], json.loads(args.tools), max_tool_calls=args.max_tool_calls)
    except (KeyError, ValueError, TypeError):
        print("Invalid reference bridge configuration", file=sys.stderr)
        return 2
    for line in sys.stdin:
        message = {}
        try:
            if len(line.encode()) > MAX_BYTES:
                raise ValueError("request exceeds limit")
            message = json.loads(line)
            if not isinstance(message, dict):
                raise ValueError("request must be an object")
            response = bridge.handle(message)
        except Exception:
            response = {"jsonrpc": "2.0", "id": message.get("id") if isinstance(message, dict) else None,
                        "error": {"code": -32603, "message": "Reference bridge request failed"}}
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
