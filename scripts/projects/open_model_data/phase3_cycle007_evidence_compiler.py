#!/usr/bin/env python3
"""Phase 3 Cycle 007 evidence-sidecar compiler.

Builds one immutable, text-free-in-public evidence sidecar per packet by
running the frozen query plan from
``batch_state/phase3-cycle007-source-grounded-amendment-v1.md`` (step "Frozen
Sources MCP evidence layer") against every row's source-bearing text, using
the project's ``sources`` MCP at the reviewed local endpoint.

Every production evidence result comes through an actual MCP tool call —
``LocalMcpSourcesClient`` talks to the real local server over the streamable
HTTP transport (``mcp.ClientSession`` + ``mcp.client.streamable_http``), not
a direct library/database import. It never makes an external network call:
anything that would require a live HTTP fetch (ULIF, slovnyk.me, GRAC) is
answered by the server's cache-only tool options; a cache miss is reported
``unavailable``, never fetched. Tests inject a ``McpToolTransport`` double
that never touches a socket either.

Only counts, hashes, tool names, source versions, and pass/fail facts belong
in a printed or logged receipt (``public_manifest``/``compile_receipt``);
row text, extracted forms, and raw tool output belong only in the private
per-packet sidecar file.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import stat
import tempfile
import threading
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Any, Protocol

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

ROOT = Path(__file__).resolve().parents[3]
SIDECAR_SCHEMA_VERSION = "phase3_cycle007_evidence_sidecar_v1"
MANIFEST_SCHEMA_VERSION = "phase3_cycle007_evidence_manifest_v1"
EVALUATION_CYCLE_ID = "phase3-v2-1-evaluation-cycle-007"

PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600

DEFAULT_SOURCES_DB = ROOT / "data" / "sources.db"
DEFAULT_VESUM_DB = ROOT / "data" / "vesum.db"
DEFAULT_SERVER_CODE = ROOT / ".mcp" / "servers" / "sources" / "server.py"

ANTONENKO_SOURCE_FILE = "antonenko-davydovych-yak-my-hovorymo"

# The reviewed local Sources MCP streamable-HTTP endpoint (.mcp.json
# "sources" server). Never a remote host — loopback only.
DEFAULT_MCP_ENDPOINT = "http://127.0.0.1:8766/mcp"
DEFAULT_MCP_TIMEOUT_S = 30.0

# Amendment step 3-6 plus step 7: the exact named tools the frozen query plan
# is allowed to use. Preflight requires every one of these to be present in
# the server's tools/list result; anything else is drift and fails closed.
REQUIRED_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "verify_words",
        "check_modern_form",
        "search_style_guide",
        "search_text",
        "search_ua_gec_errors",
        "search_heritage",
        "check_russian_shadow",
        "query_pravopys",
        "query_ulif",
        "search_slovnyk_me",
        "query_grac",
    }
)

# --------------------------------------------------------------------------
# Frozen, versioned tokenizer (amendment step 2).
# --------------------------------------------------------------------------

TOKENIZER_ID = "phase3-cycle007-cyrillic-tokenizer-v1"
TOKENIZER_VERSION = "1"
COMPOUND_PARSER_ID = "phase3-cycle007-compound-splitter-v1"
COMPOUND_PARSER_VERSION = "2"
MCP_RESPONSE_PARSER_ID = "phase3-cycle007-mcp-response-parser-v1"
MCP_RESPONSE_PARSER_VERSION = "1"
QUERY_PLAN_ID = "phase3-cycle007-query-plan-v1"
QUERY_PLAN_VERSION = "1"

# Amendment step 10 ("Freeze compiler, tokenizer, compound parser, MCP
# response parser, and query-plan code SHA-256 values in each sidecar and
# the text-free manifest"). The tokenizer, compound splitter, MCP response
# parsing, and query plan are all defined in this one module/commit, so a
# per-component hash of a sub-region would be false precision; instead every
# named component is bound to the exact same whole-module SHA-256 — a
# hand-edit to any of them changes this hash and fails the drift check.
COMPILER_MODULE_SHA256 = contract.sha256_file(Path(__file__))
CODE_HASHES: dict[str, str] = {
    "compiler_id": "phase3-cycle007-evidence-compiler-v2",
    "compiler_sha256": COMPILER_MODULE_SHA256,
    "tokenizer_id": TOKENIZER_ID,
    "tokenizer_version": TOKENIZER_VERSION,
    "tokenizer_sha256": COMPILER_MODULE_SHA256,
    "compound_parser_id": COMPOUND_PARSER_ID,
    "compound_parser_version": COMPOUND_PARSER_VERSION,
    "compound_parser_sha256": COMPILER_MODULE_SHA256,
    "mcp_response_parser_id": MCP_RESPONSE_PARSER_ID,
    "mcp_response_parser_version": MCP_RESPONSE_PARSER_VERSION,
    "mcp_response_parser_sha256": COMPILER_MODULE_SHA256,
    "query_plan_id": QUERY_PLAN_ID,
    "query_plan_version": QUERY_PLAN_VERSION,
    "query_plan_sha256": COMPILER_MODULE_SHA256,
}

_UKRAINIAN_LETTERS = "А-ЩЬЮЯЄІЇҐа-щьюяєіїґ"
_TOKEN_RE = re.compile(
    rf"[{_UKRAINIAN_LETTERS}]+(?:['’ʼ-][{_UKRAINIAN_LETTERS}]+)*",
    re.UNICODE,
)


def extract_forms(text: str) -> list[str]:
    """Extract, lowercase, and deduplicate Cyrillic surface forms from text.

    Frozen tokenizer: ``TOKENIZER_ID``/``TOKENIZER_VERSION``. Never silently
    drops candidate forms — every match is returned; ambiguous decomposition
    is a separate, explicit compound-splitting step, not a tokenizer
    responsibility.
    """
    return sorted({match.group(0).lower() for match in _TOKEN_RE.finditer(text)})


def split_compound(form: str) -> tuple[str, list[str] | None]:
    """Split a hyphenated compound into parts (versioned parser operation).

    Returns ``(status, parts)`` where ``status`` is one of:

    - ``"not_compound"`` — the form has no hyphen; ``parts`` is ``None``.
    - ``"resolved"`` — a single unambiguous full split at every hyphen was
      found; ``parts`` is the list of components.
    - ``"ambiguous"`` — the form contains a hyphen but the split cannot be
      resolved deterministically (amendment step 2: "Ambiguous tokenization
      or decomposition is recorded as unresolved and never silently drops or
      invents evidence"); ``parts`` is ``None``. This is explicit and
      versioned (``COMPOUND_PARSER_VERSION``), not a silent guess: a
      component shorter than 2 characters cannot be reliably distinguished
      from a stray hyphen/prefix fragment, so a split containing one is
      unresolved rather than asserted.
    """
    if "-" not in form:
        return "not_compound", None
    parts = [part for part in form.split("-") if part]
    if len(parts) < 2 or any(not _TOKEN_RE.fullmatch(part) for part in parts):
        return "ambiguous", None
    if any(len(part) < 2 for part in parts):
        return "ambiguous", None
    return "resolved", parts


# --------------------------------------------------------------------------
# Injectable MCP tool transport.
# --------------------------------------------------------------------------


class McpTransportError(RuntimeError):
    """A real MCP round trip failed closed: timeout, protocol error, drift, or tool error."""


class McpToolTransport(Protocol):
    """The exact low-level surface the compiler is allowed to use.

    A production transport performs a real MCP initialize/list-tools
    preflight and every subsequent call as an actual ``tools/call`` request.
    A test transport never touches a socket but exercises the identical
    interface, so ``LocalMcpSourcesClient``'s parsing/fail-closed logic runs
    unchanged in synthetic tests.
    """

    def preflight(self) -> frozenset[str]:
        """Resolve the server's tool set; raise ``McpTransportError`` on drift."""
        ...

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> str:
        """Return the tool's concatenated text content; never a live network fetch."""
        ...

    def close(self) -> None: ...


class FakeMcpToolTransport:
    """Injectable in-process fake transport for tests — never touches a socket.

    ``responses`` maps tool name -> either a fixed string or a callable
    ``(arguments) -> str`` returning the exact text an MCP ``TextContent``
    block would carry. ``tool_names`` fixes the ``tools/list`` preflight
    result, so drift/missing-tool tests are exact and deterministic.
    """

    def __init__(self, *, tool_names: Sequence[str], responses: Mapping[str, Any]) -> None:
        self._tool_names = frozenset(tool_names)
        self._responses = dict(responses)
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.closed = False

    def preflight(self) -> frozenset[str]:
        missing = REQUIRED_TOOL_NAMES - self._tool_names
        if missing:
            raise McpTransportError(f"mcp_tool_set_drift:missing={sorted(missing)}")
        return self._tool_names

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> str:
        self.calls.append((name, dict(arguments)))
        if name not in self._tool_names:
            raise McpTransportError(f"mcp_tool_set_drift:unknown_tool={name}")
        handler = self._responses.get(name)
        if handler is None:
            raise McpTransportError(f"mcp_tool_error:{name}:no_fixture_response")
        result = handler(dict(arguments)) if callable(handler) else handler
        if not isinstance(result, str):
            raise McpTransportError(f"mcp_malformed_content:{name}")
        return result

    def close(self) -> None:
        self.closed = True


class RealMcpToolTransport:
    """The real local MCP streamable-HTTP transport.

    Owns a background thread running one persistent asyncio event loop and
    one ``mcp.ClientSession``, opened once (on first use) and reused for
    every call in this process — an actual MCP tool-call round trip for
    every evidence result, never a direct library import. Fails closed on:

    - timeout (``McpTransportError`` wrapping a future timeout);
    - a JSON-RPC / MCP protocol error surfaced by the client library;
    - malformed or truncated content (no text block, or a non-string body);
    - tool-set drift (a required tool missing from ``tools/list``, or a call
      to a tool never advertised by the server);
    - a tool error envelope (``CallToolResult.isError``).
    """

    def __init__(
        self,
        endpoint_url: str = DEFAULT_MCP_ENDPOINT,
        *,
        timeout_s: float = DEFAULT_MCP_TIMEOUT_S,
        required_tools: frozenset[str] = REQUIRED_TOOL_NAMES,
    ) -> None:
        self._endpoint_url = endpoint_url
        self._timeout_s = timeout_s
        self._required_tools = required_tools
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._session: Any = None
        self._session_cm: Any = None
        self._transport_cm: Any = None
        self._tool_names: frozenset[str] | None = None
        self._lock = threading.Lock()

    def _ensure_loop(self) -> None:
        if self._loop is not None:
            return
        ready = threading.Event()

        def _run() -> None:
            loop = asyncio.new_event_loop()
            self._loop = loop
            asyncio.set_event_loop(loop)
            ready.set()
            loop.run_forever()

        thread = threading.Thread(target=_run, name="cycle007-mcp-transport", daemon=True)
        thread.start()
        if not ready.wait(timeout=self._timeout_s):
            raise McpTransportError("mcp_transport_start_timeout")
        self._thread = thread

    def _submit(self, coro: Any) -> Any:
        self._ensure_loop()
        assert self._loop is not None
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return future.result(timeout=self._timeout_s)
        except FuturesTimeoutError:
            raise McpTransportError("mcp_call_timeout") from None
        except McpTransportError:
            raise
        except Exception as exc:
            raise McpTransportError(f"mcp_call_failed:{type(exc).__name__}") from exc

    async def _open(self) -> frozenset[str]:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        self._transport_cm = streamable_http_client(self._endpoint_url)
        read_stream, write_stream, *_rest = await self._transport_cm.__aenter__()
        self._session_cm = ClientSession(read_stream, write_stream)
        self._session = await self._session_cm.__aenter__()
        await self._session.initialize()
        tools_result = await self._session.list_tools()
        return frozenset(tool.name for tool in tools_result.tools)

    def preflight(self) -> frozenset[str]:
        with self._lock:
            if self._tool_names is not None:
                return self._tool_names
            tool_names = self._submit(self._open())
            missing = self._required_tools - tool_names
            if missing:
                self.close()
                raise McpTransportError(f"mcp_tool_set_drift:missing={sorted(missing)}")
            self._tool_names = tool_names
            return tool_names

    async def _call(self, name: str, arguments: Mapping[str, Any]) -> Any:
        # Amendment step 3: every private call carries the server's internal
        # hash-only privacy-logging mode (.mcp/servers/sources/server.py
        # ``call_tool``'s reserved ``_privacy_mode`` argument). The server
        # strips it before dispatch — no tool handler or schema ever sees it.
        privacy_arguments = dict(arguments)
        privacy_arguments["_privacy_mode"] = True
        return await self._session.call_tool(name, privacy_arguments)

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> str:
        tool_names = self.preflight()
        if name not in tool_names:
            raise McpTransportError(f"mcp_tool_set_drift:unknown_tool={name}")
        result = self._submit(self._call(name, arguments))
        if getattr(result, "isError", False):
            raise McpTransportError(f"mcp_tool_error:{name}")
        content = getattr(result, "content", None) or []
        texts = [
            block.text
            for block in content
            if getattr(block, "type", None) == "text" and isinstance(getattr(block, "text", None), str)
        ]
        if not texts:
            raise McpTransportError(f"mcp_malformed_content:{name}")
        return "\n".join(texts)

    def close(self) -> None:
        loop = self._loop
        if loop is None:
            return

        async def _shutdown() -> None:
            if self._session_cm is not None:
                await self._session_cm.__aexit__(None, None, None)
            if self._transport_cm is not None:
                await self._transport_cm.__aexit__(None, None, None)

        try:
            self._submit(_shutdown())
        except McpTransportError:
            pass
        finally:
            loop.call_soon_threadsafe(loop.stop)
            if self._thread is not None:
                self._thread.join(timeout=self._timeout_s)
            self._loop = None
            self._session = None
            self._session_cm = None
            self._transport_cm = None
            self._tool_names = None


# --------------------------------------------------------------------------
# Injectable Sources client protocol.
# --------------------------------------------------------------------------


class SourcesClient(Protocol):
    """The exact frozen query surface the compiler is allowed to use.

    Every method is synchronous and returns a plain, JSON-serializable
    structure so the compiler can hash and interpret it uniformly whether it
    came from the real MCP adapter or a synthetic test double.
    """

    def server_identity(self) -> Mapping[str, Any]:
        """Return the frozen server/source-database identity for the manifest."""
        ...

    def verify_words(self, words: Sequence[str]) -> Mapping[str, list[Mapping[str, str]]]:
        """Batch VESUM check. Word -> list of ``{lemma}``; ``[]`` = miss."""
        ...

    def check_modern_form(self, word: str) -> Mapping[str, Any]:
        """``{found, is_modern_codified, has_archaic_form, has_only_archaic_form}``."""
        ...

    def ulif_cached(self, word: str) -> Mapping[str, Any]:
        """Cache-only ULIF escalation lookup via MCP. ``{status, payload}``, never live HTTP."""
        ...

    def slovnyk_me_cached(self, word: str) -> Mapping[str, Any]:
        """Cache-only slovnyk.me escalation lookup via MCP. ``{status, payload}``."""
        ...

    def grac_cached(self, word: str) -> Mapping[str, Any]:
        """Cache-only GRAC corpus-occurrence lookup via MCP. ``{status, payload}``."""
        ...

    def search_style_guide(self, query: str) -> Mapping[str, Any]:
        """Антоненко-Давидович structured index lookup. ``{status, hits}``."""
        ...

    def search_antonenko_text(self, query: str) -> Mapping[str, Any]:
        """``search_text`` scoped to ``source_file=antonenko-davydovych-yak-my-hovorymo``."""
        ...

    def search_ua_gec_errors(self, query: str) -> Mapping[str, Any]:
        """UA-GEC human error/correction pair search. ``{status, hits}``."""
        ...

    def search_heritage_cached(self, query: str) -> Mapping[str, Any]:
        """Cache-only heritage search (no live slovnyk.me escalation). ``{status, hits}``."""
        ...

    def check_russian_shadow(self, word: str) -> Mapping[str, Any]:
        """``{matches_russian, russian_lemma, confidence}`` — suspicion only."""
        ...

    def query_pravopys(self, topic: str) -> Mapping[str, Any]:
        """2019 Pravopys comparison-only lookup. ``{status, hits}``."""
        ...


# --------------------------------------------------------------------------
# Production local-MCP adapter.
# --------------------------------------------------------------------------


class LocalMcpSourcesClientError(RuntimeError):
    """The local Sources MCP endpoint is unavailable or drifted."""


_NOT_FOUND_PREFIXES: tuple[str, ...] = (
    "No results found.",
    "No UA-GEC results found",
    "No heritage evidence found",
    "No slovnyk.me results",
    "No pravopys section found",
)


def _prose_status(text: str, *, not_found_prefixes: tuple[str, ...] = _NOT_FOUND_PREFIXES) -> str:
    """Classify a prose MCP tool response as attested/not_found (amendment step 8).

    The exact "no results" sentinels are frozen per tool
    (``MCP_RESPONSE_PARSER_ID``/``VERSION``) from the reviewed server's own
    handler text, never guessed. Anything else non-empty is attested.
    """
    stripped = text.strip()
    if not stripped:
        return "not_found"
    for prefix in not_found_prefixes:
        if stripped.startswith(prefix):
            return "not_found"
    if stripped.startswith("No results in"):  # handle_dict_search family (style guide)
        return "not_found"
    return "attested"


_VERIFY_WORDS_LINE_RE = re.compile(r"^- \*\*(?P<word>.+?)\*\* — (?P<verdict>FOUND|NOT FOUND)", re.MULTILINE)


class LocalMcpSourcesClient:
    """Calls the reviewed local Sources MCP server over a real transport.

    Every method that answers a "does this exist" question issues an actual
    ``tools/call`` request through ``transport`` (a ``RealMcpToolTransport``
    by default) and parses the server's own response text/JSON — it never
    imports ``scripts.verification.vesum`` or ``wiki.sources_db`` directly.
    Every method that would otherwise require a live HTTP fetch (ULIF,
    slovnyk.me, GRAC) instead asks the server's cache-only tool option; a
    cache miss is reported ``unavailable``, never fetched.

    ``server_identity()`` is the one exception: it hashes the local
    ``server.py``/``sources.db``/``vesum.db`` files directly. That is not an
    evidence retrieval — it is the frozen code/database identity binding the
    amendment requires ("records the exact public Sources server code hash
    plus the local sources.db and vesum.db hashes"), computed independently
    of the transport so a canary can prove the endpoint is backed by the
    same reviewed code/data this process is looking at.
    """

    def __init__(
        self,
        *,
        transport: McpToolTransport | None = None,
        endpoint_url: str = DEFAULT_MCP_ENDPOINT,
        sources_db: Path = DEFAULT_SOURCES_DB,
        vesum_db: Path = DEFAULT_VESUM_DB,
        server_code: Path = DEFAULT_SERVER_CODE,
    ) -> None:
        self._sources_db = sources_db
        self._vesum_db = vesum_db
        self._server_code = server_code
        for path, label in ((sources_db, "sources.db"), (vesum_db, "vesum.db"), (server_code, "server.py")):
            if not path.is_file():
                raise LocalMcpSourcesClientError(f"local sources endpoint unavailable: missing {label} at {path}")
        self._transport: McpToolTransport = transport if transport is not None else RealMcpToolTransport(endpoint_url)
        # Fail closed immediately on drift/unavailability rather than at the
        # first evidence call.
        self._transport.preflight()

    def server_identity(self) -> Mapping[str, Any]:
        return {
            "server_code_sha256": contract.sha256_file(self._server_code),
            "sources_db_sha256": contract.sha256_file(self._sources_db),
            "sources_db_bytes": self._sources_db.stat().st_size,
            "vesum_db_sha256": contract.sha256_file(self._vesum_db),
            "vesum_db_bytes": self._vesum_db.stat().st_size,
        }

    def _call_text(self, tool: str, arguments: Mapping[str, Any]) -> str:
        return self._transport.call_tool(tool, arguments)

    def _call_json(self, tool: str, arguments: Mapping[str, Any]) -> Any:
        text = self._call_text(tool, arguments)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LocalMcpSourcesClientError(f"malformed_json_response:{tool}") from exc

    def verify_words(self, words: Sequence[str]) -> Mapping[str, list[Mapping[str, str]]]:
        if not words:
            return {}
        text = self._call_text("verify_words", {"words": list(words)})
        found_words = {match.group("word") for match in _VERIFY_WORDS_LINE_RE.finditer(text) if match.group("verdict") == "FOUND"}
        # The batch response is prose and does not carry per-match tags —
        # check_modern_form (run unconditionally for every extracted form,
        # amendment step 3) is the archaic-detail source of truth. This
        # method only needs to answer found/not-found for the VESUM batch
        # channel; a non-empty placeholder list is enough to signal "found".
        return {word: ([{"lemma": word}] if word in found_words else []) for word in words}

    def check_modern_form(self, word: str) -> Mapping[str, Any]:
        payload = self._call_json("check_modern_form", {"word": word})
        if not isinstance(payload, Mapping):
            raise LocalMcpSourcesClientError("malformed_json_response:check_modern_form")
        found = "error" not in payload
        return {
            "found": found,
            "is_modern_codified": bool(payload.get("is_modern_codified")),
            "has_archaic_form": bool(payload.get("has_archaic_form")),
            "has_only_archaic_form": bool(payload.get("has_only_archaic_form")),
        }

    def ulif_cached(self, word: str) -> Mapping[str, Any]:
        payload = self._call_json("query_ulif", {"word": word, "cache_only": True})
        if not isinstance(payload, Mapping) or payload.get("status") not in {"attested", "not_found", "unavailable"}:
            raise LocalMcpSourcesClientError("malformed_cache_only_response:query_ulif")
        return {"status": str(payload["status"]), "payload": payload.get("entry")}

    def slovnyk_me_cached(self, word: str) -> Mapping[str, Any]:
        text = self._call_text("search_slovnyk_me", {"query": word, "live": False})
        status = _prose_status(text)
        return {"status": status, "payload": text if status == "attested" else None}

    def grac_cached(self, word: str) -> Mapping[str, Any]:
        payload = self._call_json("query_grac", {"query": word, "cache_only": True})
        if not isinstance(payload, Mapping) or payload.get("status") not in {"attested", "not_found", "unavailable"}:
            raise LocalMcpSourcesClientError("malformed_cache_only_response:query_grac")
        return {"status": str(payload["status"]), "payload": payload.get("entry")}

    def search_style_guide(self, query: str) -> Mapping[str, Any]:
        text = self._call_text("search_style_guide", {"query": query})
        status = _prose_status(text)
        return {"status": status, "hits": text}

    def search_antonenko_text(self, query: str) -> Mapping[str, Any]:
        text = self._call_text("search_text", {"query": query, "source_file": ANTONENKO_SOURCE_FILE})
        status = _prose_status(text)
        return {"status": status, "hits": text}

    def search_ua_gec_errors(self, query: str) -> Mapping[str, Any]:
        text = self._call_text("search_ua_gec_errors", {"query": query})
        status = _prose_status(text)
        return {"status": status, "hits": text}

    def search_heritage_cached(self, query: str) -> Mapping[str, Any]:
        # include_live_slovnyk explicit False; cache-only, never a live fallback.
        text = self._call_text("search_heritage", {"query": query, "include_live_slovnyk": False})
        status = _prose_status(text)
        return {"status": status, "hits": text}

    def check_russian_shadow(self, word: str) -> Mapping[str, Any]:
        payload = self._call_json("check_russian_shadow", {"word": word})
        if not isinstance(payload, Mapping):
            raise LocalMcpSourcesClientError("malformed_json_response:check_russian_shadow")
        return payload

    def query_pravopys(self, topic: str) -> Mapping[str, Any]:
        text = self._call_text("query_pravopys", {"topic": topic})
        status = _prose_status(text)
        return {"status": status, "hits": text}

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> LocalMcpSourcesClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


# --------------------------------------------------------------------------
# Per-row evidence compilation.
# --------------------------------------------------------------------------


def _evidence(
    *,
    client_result_status: str,
    channel: str,
    positive_supports: str,
    source_identity: str,
    source_version: str,
    locator: str,
    query: str,
    retrieval_payload: Any,
    parser_id: str,
    parser_version: str,
    row: Mapping[str, Any],
    phenomenon_id: str | None,
    negative_reason: str | None,
) -> dict[str, Any]:
    status = client_result_status
    supports = positive_supports if status == "attested" else "no_conclusion"
    return contract.build_evidence_record(
        channel=channel,
        source_identity=source_identity,
        source_version=source_version,
        locator=locator,
        query=query,
        status=status,
        supports=supports,
        retrieval_sha256=contract.sha256_value(retrieval_payload),
        parser_id=parser_id,
        parser_version=parser_version,
        row=row,
        phenomenon_id=phenomenon_id,
        negative_reason=None if status == "attested" else (negative_reason or status),
    ), retrieval_payload


def _vesum_form_evidence(
    form: str,
    *,
    verify_result: list[Mapping[str, str]] | None,
    modern_result: Mapping[str, Any],
    row: Mapping[str, Any],
    source_version: str,
) -> tuple[dict[str, Any], Any]:
    found = bool(verify_result) or bool(modern_result.get("found"))
    retrieval_payload = {"verify_words": verify_result, "check_modern_form": modern_result}
    if not found:
        return _evidence(
            client_result_status="not_found",
            channel="vesum_attestation",
            positive_supports="attestation",
            source_identity="vesum",
            source_version=source_version,
            locator="data/vesum.db#forms",
            query=form,
            retrieval_payload=retrieval_payload,
            parser_id="vesum-forms-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="vesum_miss",
        )
    has_only_archaic = bool(modern_result.get("has_only_archaic_form"))
    return _evidence(
        client_result_status="attested",
        channel="vesum_attestation",
        positive_supports="archaic_attestation" if has_only_archaic else "attestation",
        source_identity="vesum",
        source_version=source_version,
        locator="data/vesum.db#forms",
        query=form,
        retrieval_payload=retrieval_payload,
        parser_id="vesum-forms-v1",
        parser_version="1",
        row=row,
        phenomenon_id=None,
        negative_reason=None,
    )


def _escalation_evidence(
    form: str,
    *,
    client: SourcesClient,
    row: Mapping[str, Any],
    source_version: str,
) -> list[tuple[dict[str, Any], Any]]:
    """VESUM-miss escalation: ULIF, cached slovnyk.me, cached GRAC corpus attestation.

    A miss here is never condemnation — every result stays a distinct,
    explicit, negative-or-positive evidence record. Amendment step 11: this
    is run for the original form AND (by the caller) for every valid split
    part of an ambiguity-free compound.
    """
    records = []
    ulif = client.ulif_cached(form)
    records.append(
        _evidence(
            client_result_status=ulif["status"],
            channel="vesum_attestation",
            positive_supports="attestation",
            source_identity="ulif",
            source_version=source_version,
            locator="https://lcorp.ulif.org.ua/dictua",
            query=form,
            retrieval_payload=ulif,
            parser_id="ulif-mcp-cache-only-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="ulif_cache_" + ulif["status"],
        )
    )
    slovnyk = client.slovnyk_me_cached(form)
    records.append(
        _evidence(
            client_result_status=slovnyk["status"],
            channel="vesum_attestation",
            positive_supports="attestation",
            source_identity="slovnyk_me",
            source_version=source_version,
            locator="https://slovnyk.me",
            query=form,
            retrieval_payload=slovnyk,
            parser_id="slovnyk-me-mcp-cache-only-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="slovnyk_me_cache_" + slovnyk["status"],
        )
    )
    grac = client.grac_cached(form)
    records.append(
        _evidence(
            client_result_status=grac["status"],
            channel="ukrainian_corpus_occurrence",
            positive_supports="occurrence",
            source_identity="grac",
            source_version=source_version,
            locator="https://sketch.uacorpus.org/bonito/run.cgi",
            query=form,
            retrieval_payload=grac,
            parser_id="grac-mcp-cache-only-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="grac_cache_" + grac["status"],
        )
    )
    return records


# Channels eligible for phenomenon-scoped rebinding (amendment step re:
# residual evidence). source_metadata never phenomenon-scopes (it is row
# identity/provenance only); pravopys_2026_normative/pravopys_2019_comparison
# are already explicitly bound per-phenomenon by their own bind_* functions.
_PHENOMENON_SCOPABLE_CHANNELS: frozenset[str] = frozenset(
    {
        "vesum_attestation",
        "antonenko_style",
        "ua_gec_calque",
        "heritage_attestation",
        "ukrainian_corpus_occurrence",
        "russian_shadow_suspicion",
    }
)


def bind_phenomenon_scoped_evidence(
    row_level_records: Sequence[Mapping[str, Any]],
    phenomenon_id: str,
    row: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Re-bind already-compiled row-level evidence into one residual phenomenon.

    Amendment: "every residual phenomenon a label may emit must have exact
    same-row/same-phenomenon IDs available. Do not let row-level IDs satisfy
    a residual phenomenon." Each output record keeps the identical
    ``retrieval_sha256`` as its row-level source (the underlying retrieval
    fact is shared/deduplicated — see the sidecar's ``retrieval_payloads``
    table) but gets a fresh, phenomenon-bound ``evidence_id`` since
    ``phenomenon_id`` is part of the identity hash.
    """
    contract.require(phenomenon_id in contract.RESIDUAL_PHENOMENON_TAXONOMY, f"unknown phenomenon_id: {phenomenon_id!r}")
    bound: list[dict[str, Any]] = []
    for record in row_level_records:
        if record["channel"] not in _PHENOMENON_SCOPABLE_CHANNELS:
            continue
        if record.get("phenomenon_id") is not None:
            continue  # already phenomenon-bound; never re-bind onto a different phenomenon
        bound.append(
            contract.build_evidence_record(
                channel=record["channel"],
                source_identity=record["source_identity"],
                source_version=record["source_version"],
                locator=record["locator"],
                query=record["query"],
                status=record["status"],
                supports=record["supports"],
                retrieval_sha256=record["retrieval_sha256"],
                parser_id=record["parser_id"],
                parser_version=record["parser_version"],
                row=row,
                phenomenon_id=phenomenon_id,
                negative_reason=record.get("negative_reason"),
            )
        )
    return bound


def compile_row_evidence(
    row: Mapping[str, Any],
    client: SourcesClient,
    *,
    identity: Mapping[str, Any],
    residual_phenomena: Sequence[str] = (),
) -> dict[str, Any]:
    """Compile the complete evidence set for one row.

    Runs the always-on per-row channels (Antonenko style/text, UA-GEC,
    heritage, Russian-shadow) plus the per-extracted-form VESUM batch/
    escalation channels, and a single source_metadata record preserving the
    row's existing provenance without printing it. ``identity`` is the
    compiler-bound ``server_identity()`` mapping used to derive per-source
    version bindings (amendment step 10) instead of one blanket version
    string. ``residual_phenomena`` — when the row belongs to the
    residual-label lane — additionally binds phenomenon-scoped evidence for
    every listed phenomenon (amendment: "make residual evidence actually
    phenomenon-scoped before model calls").
    """
    vesum_source_version = str(identity["vesum_db_sha256"])
    sources_db_source_version = str(identity["sources_db_sha256"])
    russian_shadow_source_version = "check-ru-morph-heuristic-v1"

    source_text = str(row.get("source_text", ""))
    forms = extract_forms(source_text)
    evidence: list[dict[str, Any]] = []
    retrieval_payloads: dict[str, Any] = {}

    def _add(record_and_payload: tuple[dict[str, Any], Any]) -> dict[str, Any]:
        record, payload = record_and_payload
        retrieval_payloads[str(record["retrieval_sha256"])] = payload
        evidence.append(record)
        return record

    # source_metadata: preserve existing provenance, hashed, never printed.
    # The row's own frozen-locator hash is folded into the locator field
    # (part of the identity hash) rather than into query_sha256, so
    # query_sha256 can follow the uniform no-query domain-separated rule
    # (amendment step 9) even for this metadata-only record.
    frozen_locator_sha256 = str(row.get("frozen_locator_sha256") or contract.sha256_text(""))
    source_text_sha256 = str(row.get("source_text_sha256") or contract.sha256_text(source_text))
    metadata_record = contract.build_evidence_record(
        channel="source_metadata",
        source_identity=str(row.get("family_id") or "unknown"),
        source_version=sources_db_source_version,
        locator=f"phase3-cycle007-row:{row.get('unit_id')}:{frozen_locator_sha256}",
        query=None,
        status="attested",
        supports="metadata_only",
        retrieval_sha256=source_text_sha256,
        parser_id="phase3-cycle007-row-provenance-v1",
        parser_version="1",
        row=row,
        phenomenon_id=None,
    )
    retrieval_payloads[source_text_sha256] = {"source_text_sha256": source_text_sha256}
    evidence.append(metadata_record)

    # VESUM batch + check_modern_form for every extracted form, regardless of
    # the batch result (amendment step 3).
    verify_batch = client.verify_words(forms) if forms else {}
    for form in forms:
        modern = client.check_modern_form(form)
        _add(
            _vesum_form_evidence(
                form,
                verify_result=verify_batch.get(form, []),
                modern_result=modern,
                row=row,
                source_version=vesum_source_version,
            )
        )
        miss = not (verify_batch.get(form) or modern.get("found"))
        if miss:
            # Split supported compounds first; ambiguous/unresolved
            # decomposition never silently drops or invents evidence — it is
            # recorded on the row output, and escalation still runs for the
            # whole (unsplit) form either way.
            split_status, parts = split_compound(form)
            if split_status == "resolved" and parts:
                part_batch = client.verify_words(parts)
                for part in parts:
                    part_modern = client.check_modern_form(part)
                    _add(
                        _vesum_form_evidence(
                            part,
                            verify_result=part_batch.get(part, []),
                            modern_result=part_modern,
                            row=row,
                            source_version=vesum_source_version,
                        )
                    )
                    # Amendment step 11: cache-only escalation for each valid
                    # split part as well as the original form.
                    for record_and_payload in _escalation_evidence(
                        part, client=client, row=row, source_version=sources_db_source_version
                    ):
                        _add(record_and_payload)
            for record_and_payload in _escalation_evidence(
                form, client=client, row=row, source_version=sources_db_source_version
            ):
                _add(record_and_payload)

    # Always-on per-row parallel path (amendment step 5): style guide, the
    # structured Антоненко-Давидович index, its prose surface, UA-GEC, and
    # heritage. Runs even when the row has no extractable Cyrillic forms so
    # every row carries these channels.
    row_query = source_text if source_text.strip() else str(row.get("unit_id", ""))
    style = client.search_style_guide(row_query)
    _add(
        _evidence(
            client_result_status=style["status"],
            channel="antonenko_style",
            positive_supports="style_guidance",
            source_identity="antonenko-davydovych-style-guide-index",
            source_version=sources_db_source_version,
            locator="repo:data/sources.db#style_guide",
            query=row_query,
            retrieval_payload=style,
            parser_id="antonenko-style-index-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="style_guide_" + style["status"],
        )
    )
    antonenko_text = client.search_antonenko_text(row_query)
    _add(
        _evidence(
            client_result_status=antonenko_text["status"],
            channel="antonenko_style",
            positive_supports="style_guidance",
            source_identity=ANTONENKO_SOURCE_FILE,
            source_version=sources_db_source_version,
            locator=f"repo:data/sources.db#textbooks:{ANTONENKO_SOURCE_FILE}",
            query=row_query,
            retrieval_payload=antonenko_text,
            parser_id="antonenko-prose-search-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="antonenko_text_" + antonenko_text["status"],
        )
    )
    ua_gec = client.search_ua_gec_errors(row_query)
    _add(
        _evidence(
            client_result_status=ua_gec["status"],
            channel="ua_gec_calque",
            positive_supports="calque_flag",
            source_identity="ua-gec",
            source_version=sources_db_source_version,
            locator="repo:data/sources.db#ua_gec",
            query=row_query,
            retrieval_payload=ua_gec,
            parser_id="ua-gec-search-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="ua_gec_" + ua_gec["status"],
        )
    )
    heritage = client.search_heritage_cached(row_query)
    _add(
        _evidence(
            client_result_status=heritage["status"],
            channel="heritage_attestation",
            positive_supports="attestation",
            source_identity="heritage-cache",
            source_version=sources_db_source_version,
            locator="repo:data/sources.db#heritage",
            query=row_query,
            retrieval_payload=heritage,
            parser_id="heritage-cache-search-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="heritage_" + heritage["status"],
        )
    )

    # Russian-shadow suspicion: per extracted form (or the row identity when
    # there is nothing to tokenize), suspicion-only, never authoritative.
    shadow_targets = forms or [row_query]
    for target in shadow_targets:
        shadow = client.check_russian_shadow(target)
        matches = bool(shadow.get("matches_russian"))
        _add(
            _evidence(
                client_result_status="attested" if matches else "not_found",
                channel="russian_shadow_suspicion",
                positive_supports="suspicion",
                source_identity="check_ru_morph",
                source_version=russian_shadow_source_version,
                locator="repo:scripts/verification/check_ru_morph.py",
                query=target,
                retrieval_payload=shadow,
                parser_id="russian-shadow-heuristic-v1",
                parser_version="1",
                row=row,
                phenomenon_id=None,
                negative_reason="russian_shadow_not_suspected" if not matches else None,
            )
        )

    # Amendment: phenomenon-scoped evidence, produced before any model call.
    row_level_records = list(evidence)
    for phenomenon_id in residual_phenomena:
        for bound_record in bind_phenomenon_scoped_evidence(row_level_records, phenomenon_id, row):
            evidence.append(bound_record)
            # Deliberately no new retrieval_payloads entry: the payload is
            # already present under this shared retrieval_sha256.

    evidence_ids = sorted({str(record["evidence_id"]) for record in evidence})
    phenomenon_evidence_ids: dict[str, list[str]] = {}
    for record in evidence:
        phenomenon_id = record.get("phenomenon_id")
        if phenomenon_id:
            phenomenon_evidence_ids.setdefault(str(phenomenon_id), []).append(str(record["evidence_id"]))
    phenomenon_evidence_ids = {key: sorted(set(value)) for key, value in phenomenon_evidence_ids.items()}

    return {
        "unit_id": row["unit_id"],
        "unit_sha256": row["unit_sha256"],
        "tokenizer_id": TOKENIZER_ID,
        "tokenizer_version": TOKENIZER_VERSION,
        "extracted_forms": forms,
        "evidence": evidence,
        "evidence_ids": evidence_ids,
        "phenomenon_evidence_ids": phenomenon_evidence_ids,
        "retrieval_payloads": retrieval_payloads,
        "sufficient_support": any(contract.is_sufficient_positive(record) for record in evidence),
        "archaic_only_risk": contract.is_archaic_only_risk(evidence),
        "russian_shadow_suspected": any(
            record["channel"] == "russian_shadow_suspicion" and record["status"] == "attested" for record in evidence
        ),
    }


# --------------------------------------------------------------------------
# Pravopys 2026/2019 binding — explicit, phenomenon-scoped, never blanket.
# --------------------------------------------------------------------------

PRAVOPYS_2026_PDF_SHA256 = "e593956bfba6737d991a76fa86970db9c10a5cd7fd8895bae67f2b9a950c3a92"
PRAVOPYS_2026_CONTEXT_RECEIPT_SHA256 = "5da6f60e1cf5527fd98e44b4396472d871d359cd6b9dc76e3806c73a15c2b827"
DEFAULT_PRAVOPYS_CONTEXT_RECEIPT = (
    ROOT / "data/projects/open_model_data/inventory/phase3_pravopys_evaluation_context_receipt_v1.json"
)


def bind_pravopys_2026_evidence(
    row: Mapping[str, Any],
    phenomenon_id: str,
    *,
    context_receipt_path: Path = DEFAULT_PRAVOPYS_CONTEXT_RECEIPT,
) -> dict[str, Any]:
    """Bind the frozen Pravopys 2026 normative fact to one residual phenomenon.

    This is deliberately not a per-row/per-form query: within this frozen
    Phase 3 evaluation the 2026 edition is bound by explicit task-specific
    identity (PDF + context-receipt SHA-256), not fetched live — the general
    Sources MCP ``query_pravopys`` tool only exposes 2019 and is
    comparison-only here.
    """
    contract.require(bool(phenomenon_id), "pravopys_2026_normative evidence requires a phenomenon_id")
    receipt_sha256 = contract.sha256_file(context_receipt_path) if context_receipt_path.is_file() else None
    status = "attested" if receipt_sha256 == PRAVOPYS_2026_CONTEXT_RECEIPT_SHA256 else "unavailable"
    return contract.build_evidence_record(
        channel="pravopys_2026_normative",
        source_identity="pravopys-2026-official-edition",
        source_version=PRAVOPYS_2026_PDF_SHA256,
        locator=(
            str(context_receipt_path.relative_to(ROOT))
            if context_receipt_path.is_absolute() and context_receipt_path.is_relative_to(ROOT)
            else str(context_receipt_path)
        ),
        query=None,
        status=status,
        supports="normative_rule" if status == "attested" else "no_conclusion",
        retrieval_sha256=receipt_sha256 or contract.sha256_text("unavailable"),
        parser_id="pravopys-2026-frozen-binding-v1",
        parser_version="1",
        row=row,
        phenomenon_id=phenomenon_id,
        negative_reason=None if status == "attested" else "pravopys_2026_context_receipt_hash_mismatch",
    )


def bind_pravopys_2019_comparison_evidence(
    row: Mapping[str, Any],
    phenomenon_id: str,
    client: SourcesClient,
    *,
    query: str,
) -> dict[str, Any]:
    """Bind a comparison-only 2019 Pravopys result to one residual phenomenon.

    Amendment step 8: this calls the ``query_pravopys`` MCP tool — never
    ``search_style_guide``, which is a distinct Антоненко-Давидович channel.
    ``query_pravopys`` is explicitly comparison-only in this evaluation: its
    result can never carry ``normative_rule`` support (enforced by the
    closed per-channel claim boundary in the contract module).
    """
    contract.require(bool(phenomenon_id), "pravopys_2019_comparison evidence requires a phenomenon_id")
    result = client.query_pravopys(query)
    return contract.build_evidence_record(
        channel="pravopys_2019_comparison",
        source_identity="pravopys-2019-comparison",
        source_version="2019.pravopys.net",
        locator="https://2019.pravopys.net",
        query=query,
        status=result["status"],
        supports="comparison_only" if result["status"] == "attested" else "no_conclusion",
        retrieval_sha256=contract.sha256_value(result),
        parser_id="pravopys-2019-comparison-v1",
        parser_version="1",
        row=row,
        phenomenon_id=phenomenon_id,
        negative_reason=None if result["status"] == "attested" else "pravopys_2019_" + result["status"],
    )


# --------------------------------------------------------------------------
# Packet-level sidecar assembly and atomic private write.
# --------------------------------------------------------------------------


def compile_packet_sidecar(
    packet_index: int,
    rows: Sequence[Mapping[str, Any]],
    client: SourcesClient,
    *,
    residual_lane: bool = False,
) -> dict[str, Any]:
    identity = client.server_identity()
    residual_phenomena = contract.RESIDUAL_PHENOMENON_TAXONOMY if residual_lane else ()
    row_records = []
    retrieval_payloads: dict[str, Any] = {}
    for row in rows:
        row_record = compile_row_evidence(row, client, identity=identity, residual_phenomena=residual_phenomena)
        retrieval_payloads.update(row_record.pop("retrieval_payloads"))
        row_records.append(row_record)
    body = {
        "schema_version": SIDECAR_SCHEMA_VERSION,
        "evaluation_cycle_id": EVALUATION_CYCLE_ID,
        "packet_index": packet_index,
        "row_count": len(rows),
        "tokenizer_id": TOKENIZER_ID,
        "tokenizer_version": TOKENIZER_VERSION,
        "code_hashes": CODE_HASHES,
        "server_code_sha256": identity["server_code_sha256"],
        "sources_db_sha256": identity["sources_db_sha256"],
        "vesum_db_sha256": identity["vesum_db_sha256"],
        "network_lookups_performed": 0,
        "rows": row_records,
        # Amendment step 5: the full normalized private MCP result payload,
        # deduplicated by retrieval SHA-256. The public manifest projection
        # never includes this table.
        "retrieval_payloads": {key: retrieval_payloads[key] for key in sorted(retrieval_payloads)},
    }
    body["sidecar_id"] = "cycle007_sidecar:" + contract.sha256_value(body)
    return body


def _atomic_write_private(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    os.chmod(path.parent, PRIVATE_DIR_MODE)
    if path.exists() or path.is_symlink():
        raise contract.EvidenceContractError(f"refusing to overwrite existing sidecar: {path}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), PRIVATE_FILE_MODE)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return contract.sha256_bytes(payload)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _walk_private_modes(root: Path) -> None:
    contract.require(stat.S_IMODE(root.stat().st_mode) == PRIVATE_DIR_MODE, f"staging permission drift: {root}")
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise contract.EvidenceContractError(f"symlink not permitted in sidecar output: {path}")
        mode = stat.S_IMODE(path.stat().st_mode)
        expected = PRIVATE_DIR_MODE if path.is_dir() else PRIVATE_FILE_MODE
        contract.require(mode == expected, f"sidecar output permission drift: {path}")


def compile_sidecar_bundle(
    packets: Sequence[Sequence[Mapping[str, Any]]],
    client: SourcesClient,
    output_dir: Path,
    *,
    residual_lane_packets: Sequence[bool] | None = None,
) -> dict[str, Any]:
    """Compile every packet's sidecar into a fresh staging directory, then atomically install.

    Amendment step 14: the whole bundle is built and fully validated in a
    fresh mode-0700 staging directory before anything is installed at
    ``output_dir``; the destination is refused up front if it already
    exists (including as a nonempty directory or a symlink), and on any
    failure only the staging directory this call created is removed —
    ``output_dir`` is never touched unless every packet validated.
    """
    if output_dir.exists() or output_dir.is_symlink():
        raise contract.EvidenceContractError(f"refusing to compile into an existing destination: {output_dir}")
    residual_flags = list(residual_lane_packets) if residual_lane_packets is not None else [False] * len(packets)
    contract.require(len(residual_flags) == len(packets), "residual_lane_packets length must match packets")

    output_dir.parent.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent))
    os.chmod(staging, PRIVATE_DIR_MODE)
    committed = False
    try:
        identity = client.server_identity()
        channel_counts: Counter[str] = Counter()
        status_counts: Counter[str] = Counter()
        supports_counts: Counter[str] = Counter()
        sufficient_support_rows = 0
        archaic_only_risk_rows = 0
        russian_shadow_suspected_rows = 0
        row_count = 0
        sidecar_index: list[dict[str, Any]] = []
        for packet_index, (rows, residual_lane) in enumerate(zip(packets, residual_flags, strict=True), start=1):
            sidecar = compile_packet_sidecar(packet_index, rows, client, residual_lane=residual_lane)
            payload = (contract.canonical_json(sidecar) + "\n").encode("utf-8")
            sidecar_path = staging / f"sidecar-{packet_index:04d}.json"
            sidecar_sha256 = _atomic_write_private(sidecar_path, payload)
            for row_record in sidecar["rows"]:
                row_count += 1
                sufficient_support_rows += int(row_record["sufficient_support"])
                archaic_only_risk_rows += int(row_record["archaic_only_risk"])
                russian_shadow_suspected_rows += int(row_record["russian_shadow_suspected"])
                for evidence_record in row_record["evidence"]:
                    channel_counts[evidence_record["channel"]] += 1
                    status_counts[evidence_record["status"]] += 1
                    supports_counts[evidence_record["supports"]] += 1
            sidecar_index.append(
                {
                    "packet_index": packet_index,
                    "row_count": len(rows),
                    "sidecar_sha256": sidecar_sha256,
                    "sidecar_id": sidecar["sidecar_id"],
                }
            )
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "text_free": True,
            "evaluation_cycle_id": EVALUATION_CYCLE_ID,
            "tokenizer_id": TOKENIZER_ID,
            "tokenizer_version": TOKENIZER_VERSION,
            "code_hashes": CODE_HASHES,
            "server_code_sha256": identity["server_code_sha256"],
            "sources_db_sha256": identity["sources_db_sha256"],
            "vesum_db_sha256": identity["vesum_db_sha256"],
            "packet_count": len(packets),
            "row_count": row_count,
            "network_lookups_performed": 0,
            "counts_by_channel": dict(sorted(channel_counts.items())),
            "counts_by_status": dict(sorted(status_counts.items())),
            "counts_by_supports": dict(sorted(supports_counts.items())),
            "sufficient_support_rows": sufficient_support_rows,
            "archaic_only_risk_rows": archaic_only_risk_rows,
            "russian_shadow_suspected_rows": russian_shadow_suspected_rows,
            "sidecars": sidecar_index,
        }
        manifest["manifest_sha256"] = contract.sha256_value(manifest)
        manifest_bytes = (contract.canonical_json(manifest) + "\n").encode("utf-8")
        _atomic_write_private(staging / "manifest.json", manifest_bytes)
        _walk_private_modes(staging)
        for child in staging.iterdir():
            _fsync_directory(child.parent)
        os.replace(staging, output_dir)
        _fsync_directory(output_dir.parent)
        _walk_private_modes(output_dir)
        committed = True
        return manifest
    finally:
        if not committed:
            import shutil

            shutil.rmtree(staging, ignore_errors=True)


# --------------------------------------------------------------------------
# Package-bound production entrypoint (amendment step 13).
# --------------------------------------------------------------------------

REAL_PACKET_COUNT = 204
REAL_ROW_COUNT = 10_159
_RESIDUAL_LANE_NAME = "residual_label"


def _materializer_module():
    from scripts.projects.open_model_data import phase3_cycle007_materializer as materializer

    return materializer


def compile_cycle007_package(
    package_dir: Path,
    client: SourcesClient,
    output_dir: Path,
    *,
    fixture: bool = False,
) -> dict[str, Any]:
    """Compile a full evidence bundle bound to one materialized Cycle 007 package.

    Reads exactly the frozen Cycle 007 materialization manifest and packets
    written by ``phase3_cycle007_materializer.materialize`` — never an
    arbitrary caller-assembled packet sequence. Every sidecar's
    ``packet_index`` is bound to its source packet's own ``lane``,
    ``packet_index``, and ``canonical_basename``; every packet's ``raw_sha256``
    and ``packet_identity_set_sha256`` are re-verified against the manifest
    before compilation. Real mode enforces the exact 204-packet/10,159-row
    denominator; a smaller synthetic run requires ``fixture=True``.
    """
    materializer = _materializer_module()
    manifest_path = package_dir / "manifest.json"
    manifest = materializer.strict_json(manifest_path, "source_binding_drift")
    contract.require(isinstance(manifest, Mapping), "source_binding_drift")
    contract.require(manifest.get("schema_version") == "phase3_cycle007_materialization_manifest_v1", "manifest_binding_drift")
    contract.require(manifest.get("evaluation_cycle_id") == EVALUATION_CYCLE_ID, "manifest_binding_drift")
    contract.require(manifest.get("receipt_sha256") == materializer._hash_receipt(manifest), "manifest_binding_drift")
    records = manifest.get("packets")
    contract.require(isinstance(records, list) and bool(records), "manifest_binding_drift")
    contract.require(manifest.get("packet_count") == len(records), "manifest_binding_drift")
    if not fixture:
        contract.require(manifest.get("packet_count") == REAL_PACKET_COUNT, "manifest_binding_drift")
        contract.require(manifest.get("row_count") == REAL_ROW_COUNT, "manifest_binding_drift")

    packets: list[list[Mapping[str, Any]]] = []
    residual_flags: list[bool] = []
    for record in records:
        contract.require(isinstance(record, Mapping), "packet_binding_drift")
        lane = record.get("lane")
        basename = record.get("canonical_basename")
        contract.require(isinstance(lane, str) and isinstance(basename, str), "packet_binding_drift")
        contract.require(Path(basename).name == basename, "packet_binding_drift")
        packet_path = package_dir / lane / basename
        raw = materializer._read_regular(packet_path, "packet_binding_drift")
        contract.require(materializer.digest(raw) == record.get("raw_sha256"), "packet_binding_drift")
        packet = materializer.strict_json(packet_path, "packet_binding_drift")
        contract.require(isinstance(packet, Mapping), "packet_binding_drift")
        rows = packet.get("rows")
        contract.require(isinstance(rows, list) and len(rows) == record.get("row_count"), "packet_binding_drift")
        contract.require(
            packet.get("packet_identity_set_sha256") == materializer.identity_set(rows), "packet_binding_drift"
        )
        contract.require(
            packet.get("packet_identity_set_sha256") == record.get("packet_identity_set_sha256"), "packet_binding_drift"
        )
        packets.append(list(rows))
        residual_flags.append(lane == _RESIDUAL_LANE_NAME)

    return compile_sidecar_bundle(packets, client, output_dir, residual_lane_packets=residual_flags)
