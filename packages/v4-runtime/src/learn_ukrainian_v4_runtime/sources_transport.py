"""Attempt-authenticated Sources HTTP carriage and scoped stored-operation IO."""

from __future__ import annotations

import contextvars
import json
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from starlette.responses import Response

from learn_ukrainian_v4_runtime.operation_auth import OperationRefused, canonical_bytes, digest

ACTIVE_ATTEMPT = contextvars.ContextVar("v4_sources_active_attempt", default=None)


def credential_path() -> Path:
    return Path("/run/credentials/learn-ukrainian-sources.service/v4-sources-dsn")


@contextmanager
def sources_connection():
    path = credential_path()
    if not path.is_file() or path.is_symlink() or path.stat().st_mode & 0o077:
        raise OperationRefused("Sources scoped credential unavailable")
    with psycopg.connect(path.read_text().strip(), autocommit=True, row_factory=dict_row) as conn:
        if conn.execute("SELECT current_user AS principal").fetchone()["principal"] != "hramatka_v4_sources_writer":
            raise OperationRefused("Sources role required")
        yield conn


def resolve_attempt(token: str) -> dict | None:
    if not isinstance(token, str) or not token:
        return None
    try:
        with sources_connection() as conn:
            row = conn.execute(
                "SELECT hramatka_v4_record_sources_invocation_v1(%s,NULL,NULL,NULL) AS record",
                (digest(token.encode()),),
            ).fetchone()
            result = json.loads(row["record"])
            result["capability_token"] = token
            return result
    except (OSError, ValueError, psycopg.Error):
        return None


def record_typed_invocation(*, name: str, typed_outcome: dict) -> dict | None:
    attempt = ACTIVE_ATTEMPT.get()
    if attempt is None:
        return None
    from learn_ukrainian_v4_runtime.resources import read_bytes

    version = digest(read_bytes("sources_handlers.py"))
    with sources_connection() as conn:
        row = conn.execute(
            "SELECT hramatka_v4_record_sources_invocation_v1(%s,%s,%s,%s) AS record",
            (digest(attempt["capability_token"].encode()), name, version, canonical_bytes(typed_outcome).decode()),
        ).fetchone()
        return json.loads(row["record"])


class AttemptAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        attempt = None
        if scope.get("type") == "http" and scope.get("path") in {"/mcp", "/mcp/"}:
            values = [v.decode("latin1") for k, v in scope.get("headers", []) if k.lower() == b"authorization"]
            if values:
                if len(values) != 1 or not values[0].startswith("Bearer "):
                    await Response("V4 capability refused", status_code=401)(scope, receive, send)
                    return
                attempt = resolve_attempt(values[0][7:])
                if attempt is None:
                    await Response("V4 capability refused", status_code=401)(scope, receive, send)
                    return
        token = ACTIVE_ATTEMPT.set(attempt)
        try:
            await self.app(scope, receive, send)
        finally:
            ACTIVE_ATTEMPT.reset(token)


def create_sources_app():
    """Real MCP wire integration for the existing Sources unit and IO resources."""
    from mcp.server import Server
    from mcp.types import CallToolResult, ListToolsResult, Tool

    from learn_ukrainian_v4_runtime import sources_handlers

    names = ("verify_word", "verify_words", "verify_lemma", "verify_stress", "check_modern_form")

    async def list_tools(_ctx, _params):
        return ListToolsResult(
            tools=[
                Tool(name=name, description="Typed Sources verification", inputSchema={"type": "object"})
                for name in names
            ]
        )

    async def call_tool(_ctx, params):
        if params.name not in names:
            raise OperationRefused("non_Sources_tool")
        content, outcome = await getattr(sources_handlers, "handle_" + params.name)(dict(params.arguments or {}))
        record_typed_invocation(name=params.name, typed_outcome=outcome)
        return CallToolResult(content=content, structured_content=outcome, isError=False)

    server = Server("sources", on_list_tools=list_tools, on_call_tool=call_tool)
    return AttemptAuthMiddleware(
        server.streamable_http_app(streamable_http_path="/mcp", json_response=True, stateless_http=True)
    )
