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
import contextlib
import copy
import functools
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
from urllib.parse import urlparse

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract
from scripts.projects.open_model_data import phase3_cycle007_evidence_validator as validator

ROOT = Path(__file__).resolve().parents[3]
SIDECAR_SCHEMA_VERSION = "phase3_cycle007_evidence_sidecar_v1"
MANIFEST_SCHEMA_VERSION = "phase3_cycle007_evidence_manifest_v1"
EVALUATION_CYCLE_ID = "phase3-v2-1-evaluation-cycle-007"

PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600

DEFAULT_SOURCES_DB = ROOT / "data" / "sources.db"
DEFAULT_VESUM_DB = ROOT / "data" / "vesum.db"
DEFAULT_SERVER_CODE = ROOT / ".mcp" / "servers" / "sources" / "server.py"
DEFAULT_CHECK_RU_MORPH = ROOT / "scripts" / "verification" / "check_ru_morph.py"


@functools.lru_cache(maxsize=1)
def _russian_shadow_source_version(check_ru_morph_path: Path = DEFAULT_CHECK_RU_MORPH) -> str:
    """The actual current SHA-256 of check_ru_morph.py (amendment fixes v3, item 6).

    Never a literal version string — memoized so the file is hashed once
    per process, not once per row.
    """
    return contract.sha256_file(check_ru_morph_path)

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
        # Amendment (fixes v3, item 1): endpoint identity attestation. A
        # server that does not advertise this tool is drift and fails
        # preflight closed the same as a missing evidence-retrieval tool.
        "mcp_server_identity",
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
        # MCP's wire field is ``isError`` but the Python SDK exposes the
        # validated model attribute as ``is_error``. Check both so an SDK
        # model cannot silently turn a real tool failure into ordinary text.
        if getattr(result, "is_error", getattr(result, "isError", False)):
            raise McpTransportError(f"mcp_tool_error:{name}")
        content = getattr(result, "content", None) or []
        texts = [
            block.text
            for block in content
            if getattr(block, "type", None) == "text" and isinstance(getattr(block, "text", None), str)
        ]
        if not texts:
            raise McpTransportError(f"mcp_malformed_content:{name}")
        # Defense in depth (fixes v3, item 2): a real MCP error is signaled
        # by ``isError`` above, but a legacy/downgraded server could still
        # put the old raw-exception prose marker on the wire without it.
        # Never trust that text as a positive result either way.
        if any(text.strip().startswith(("Error in ", "Unknown tool:")) for text in texts):
            raise McpTransportError(f"mcp_tool_error_prose_marker:{name}")
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
    "No results in",  # handle_dict_search family (style guide)
)

# Fail-closed error/unknown-tool markers a server response can never
# legitimately carry as a positive result — a real MCP error is signaled by
# ``isError``, but a downgraded/legacy server (or ``call_tool``'s own legacy
# text path) could still put this exact prose on the wire. Recognized here so
# it is never accidentally classified "attested".
_ERROR_PROSE_PREFIXES: tuple[str, ...] = ("Error in ", "Unknown tool:")

# Amendment (fixes v3, item 2): "Prose parsers must recognize only exact
# reviewed success envelopes; unknown nonempty prose is incomplete/parse_error
# or terminal, never attested." Each handler's reviewed success text always
# starts with one of these exact prefixes (see .mcp/servers/sources/server.py
# handle_search_text / handle_dict_search / handle_search_ua_gec_errors /
# handle_search_heritage / handle_search_slovnyk_me / handle_query_pravopys).
# A tool name absent from this table has no prose success path in the
# compiler (its only call sites use the JSON parsers instead).
_SUCCESS_ENVELOPES_BY_TOOL: dict[str, re.Pattern[str]] = {
    "search_style_guide": re.compile(
        r'^Found (?P<count>[1-9][0-9]*) results in \*\*Антоненко-Давидович\*\* for: "(?P<query>.+)"$'
    ),
    "search_text": re.compile(r'^Found (?P<count>[1-9][0-9]*) results for: "(?P<query>.+)"$'),
    "search_ua_gec_errors": re.compile(
        r'^Found (?P<count>[1-9][0-9]*) human-annotated error pairs for: "(?P<query>.+)"$'
    ),
    "search_heritage": re.compile(
        r'^Found (?P<count>[1-9][0-9]*) heritage evidence row\(s\) for: "(?P<query>.+)"$'
    ),
    "search_slovnyk_me": re.compile(
        r'^Found (?P<count>[1-9][0-9]*) slovnyk\.me result\(s\) for: "(?P<query>.+)"$'
    ),
    "query_pravopys": re.compile(r"^\*\*Pravopys section [1-9][0-9]*\*\*$"),
}

_SUCCESS_ITEM_PREFIX_BY_TOOL: dict[str, str] = {
    "search_style_guide": "### Result ",
    "search_text": "### Result ",
    "search_ua_gec_errors": "### Result ",
    "search_heritage": "### Evidence ",
    "search_slovnyk_me": "### Result ",
}

# ``handle_query_pravopys`` is backed only by ``scripts.rag.source_query``.
# That reviewed adapter exposes sections 1--61 at this exact origin and path;
# accepting a generic HTTPS URL or an unrelated body would turn untrusted MCP
# prose into an attestation.
_PRAVOPYS_2019_RESPONSE_RE = re.compile(
    r"^\*\*Pravopys section (?P<section>[1-9]|[1-5][0-9]|6[0-1])\*\*\n"
    r"\*\*URL\*\*: https://2019\.pravopys\.net/sections/(?P<url_section>[1-9]|[1-5][0-9]|6[0-1])/\n\n"
    r"(?P<body>.+)$",
    re.DOTALL,
)


def _prose_status(
    text: str,
    *,
    tool: str,
    expected_query: str | None = None,
    not_found_prefixes: tuple[str, ...] = _NOT_FOUND_PREFIXES,
) -> str:
    """Classify a prose MCP tool response (amendment step 8; fixes v3 item 2).

    The exact "no results" and "found" envelope sentinels are frozen per
    tool (``MCP_RESPONSE_PARSER_ID``/``VERSION``) from the reviewed server's
    own handler text, never guessed. Only an exact reviewed success prefix
    for ``tool`` is ever classified ``attested``; a known "no results"
    sentinel is ``not_found``; the legacy error/unknown-tool prose marker is
    ``parse_error`` (defensively — a real MCP error should already have
    ``isError`` set and never reach this parser); anything else nonempty and
    unrecognized is ``incomplete`` — it is never silently promoted to
    ``attested`` just because it is nonempty.
    """
    stripped = text.strip()
    if not stripped:
        return "not_found"
    if stripped.startswith(_ERROR_PROSE_PREFIXES):
        return "parse_error"
    for prefix in not_found_prefixes:
        if stripped.startswith(prefix):
            return "not_found"
    lines = stripped.splitlines()
    success_envelope = _SUCCESS_ENVELOPES_BY_TOOL.get(tool)
    match = success_envelope.fullmatch(lines[0]) if success_envelope is not None else None
    if match is None:
        return "incomplete"
    if tool == "query_pravopys":
        pravopys_match = _PRAVOPYS_2019_RESPONSE_RE.fullmatch(stripped)
        if pravopys_match is None:
            return "incomplete"
        section = pravopys_match.group("section")
        if pravopys_match.group("url_section") != section:
            return "incomplete"
        # ``_extract_pravopys_text`` preserves the authoritative section
        # marker.  Requiring that marker binds the returned prose to the same
        # reviewed section instead of accepting arbitrary nonblank text.
        if re.search(rf"(?:^|\n)§\s*{re.escape(section)}(?:\D|$)", pravopys_match.group("body")) is None:
            return "incomplete"
        return "attested"
    if expected_query is not None and match.groupdict().get("query") != expected_query:
        return "incomplete"
    expected_count = int(match.group("count"))
    marker_prefix = _SUCCESS_ITEM_PREFIX_BY_TOOL[tool]
    markers = [line for line in lines[1:] if line.startswith(marker_prefix)]
    if markers != [f"{marker_prefix}{index}" for index in range(1, expected_count + 1)]:
        return "incomplete"
    marker_positions = [lines.index(marker) for marker in markers]
    for position, next_position in zip(marker_positions, [*marker_positions[1:], len(lines)], strict=True):
        if not any(line.startswith("- **") for line in lines[position + 1 : next_position]):
            return "incomplete"
    return "attested"


_VERIFY_WORDS_HEADER_RE = re.compile(r"^Batch verification: (?P<count>[0-9]+) words$")
_VERIFY_WORDS_SUMMARY_RE = re.compile(r"^Found: (?P<found>[0-9]+)/(?P<count>[0-9]+)$")
_VERIFY_WORDS_LINE_RE = re.compile(
    r"^- \*\*(?P<word>[^*\n]+)\*\* — "
    r"(?:(?P<found>FOUND) \((?P<matches>[1-9][0-9]*) match\): (?P<details>[^\n]+)|(?P<not_found>NOT FOUND))$"
)


_SERVER_IDENTITY_TOOL = "mcp_server_identity"
_SERVER_IDENTITY_KEYS: frozenset[str] = frozenset(
    {"server_code_sha256", "sources_db_sha256", "sources_db_bytes", "vesum_db_sha256", "vesum_db_bytes"}
)


def _is_loopback_host(host: str) -> bool:
    if host == "localhost":
        return True
    import ipaddress

    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class LocalMcpSourcesClient:
    """Calls the reviewed local Sources MCP server over a real transport.

    Every method that answers a "does this exist" question issues an actual
    ``tools/call`` request through ``transport`` (a ``RealMcpToolTransport``
    by default) and parses the server's own response text/JSON — it never
    imports ``scripts.verification.vesum`` or ``wiki.sources_db`` directly.
    Every method that would otherwise require a live HTTP fetch (ULIF,
    slovnyk.me, GRAC) instead asks the server's cache-only tool option; a
    cache miss is reported ``unavailable``, never fetched.

    ``server_identity()`` (fixes v3, item 1) never trusts a locally computed
    hash on its own. It hashes the exact local ``server.py``/``sources.db``/
    ``vesum.db`` files this process reviewed (what it *expects*), calls the
    endpoint's own ``mcp_server_identity`` tool through the real MCP
    transport, and requires an exact match on every field — a mismatch,
    missing tool, or malformed response is terminal. This is what proves the
    endpoint is actually backed by the same reviewed code/data, not merely
    files that happen to exist on the caller's own filesystem.
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
        host = urlparse(endpoint_url).hostname
        if not host or not _is_loopback_host(host):
            raise LocalMcpSourcesClientError(f"non_loopback_mcp_endpoint: {endpoint_url!r}")
        self._endpoint_url = endpoint_url
        self._sources_db = sources_db
        self._vesum_db = vesum_db
        self._server_code = server_code
        for path, label in ((sources_db, "sources.db"), (vesum_db, "vesum.db"), (server_code, "server.py")):
            if not path.is_file():
                raise LocalMcpSourcesClientError(f"local sources endpoint unavailable: missing {label} at {path}")
        self._transport: McpToolTransport = transport if transport is not None else RealMcpToolTransport(endpoint_url)
        self._tool_call_count = 0
        self._tool_call_counts: Counter[str] = Counter()
        self._tool_call_commitment = contract.sha256_text("phase3-cycle007-mcp-tool-call-chain-v1")
        self._tool_call_records: list[dict[str, Any]] = []
        # Fail closed immediately on drift/unavailability rather than at the
        # first evidence call.
        self._transport.preflight()
        self._identity: Mapping[str, Any] = self._attest_server_identity()

    def _attest_server_identity(self) -> Mapping[str, Any]:
        expected = {
            "server_code_sha256": contract.sha256_file(self._server_code),
            "sources_db_sha256": contract.sha256_file(self._sources_db),
            "sources_db_bytes": self._sources_db.stat().st_size,
            "vesum_db_sha256": contract.sha256_file(self._vesum_db),
            "vesum_db_bytes": self._vesum_db.stat().st_size,
        }
        payload = self._call_json(_SERVER_IDENTITY_TOOL, {})
        if not isinstance(payload, Mapping) or set(payload) != _SERVER_IDENTITY_KEYS:
            raise LocalMcpSourcesClientError(f"malformed_json_response:{_SERVER_IDENTITY_TOOL}")
        for key in ("server_code_sha256", "sources_db_sha256", "vesum_db_sha256"):
            if not (isinstance(payload.get(key), str) and len(payload[key]) == 64):
                raise LocalMcpSourcesClientError(f"malformed_json_response:{_SERVER_IDENTITY_TOOL}")
        for key in ("sources_db_bytes", "vesum_db_bytes"):
            if not isinstance(payload.get(key), int) or isinstance(payload.get(key), bool):
                raise LocalMcpSourcesClientError(f"malformed_json_response:{_SERVER_IDENTITY_TOOL}")
        for key in _SERVER_IDENTITY_KEYS:
            if payload[key] != expected[key]:
                raise LocalMcpSourcesClientError(f"endpoint_identity_mismatch:{key}")
        return expected

    def server_identity(self) -> Mapping[str, Any]:
        return self._identity

    def _call_text(self, tool: str, arguments: Mapping[str, Any]) -> str:
        response = self._transport.call_tool(tool, arguments)
        self._record_tool_call(
            tool=tool,
            arguments_sha256=contract.sha256_value(arguments),
            response_sha256=contract.sha256_text(response),
        )
        return response

    def _record_tool_call(
        self,
        *,
        tool: str,
        arguments_sha256: str,
        response_sha256: str,
    ) -> None:
        self._tool_call_count += 1
        self._tool_call_counts[tool] += 1
        call = {
            "ordinal": self._tool_call_count,
            "tool": tool,
            "arguments_sha256": arguments_sha256,
            "response_sha256": response_sha256,
        }
        self._tool_call_commitment = contract.sha256_text(
            self._tool_call_commitment + "\n" + contract.canonical_json(call)
        )
        self._tool_call_records.append(call)

    def transport_call_records(self) -> list[dict[str, Any]]:
        """Return the private text-free ledger behind the public commitment.

        Records contain only ordinals, fixed tool names, and SHA-256 values;
        arguments, responses, row text, and locators are never persisted here.
        """
        return copy.deepcopy(self._tool_call_records)

    def resume_transport_state(
        self,
        prior_attestation: Mapping[str, Any],
        prior_call_records: Sequence[Mapping[str, Any]],
    ) -> None:
        """Restore a verified sealed-prefix call chain and append this process's identity call.

        The caller must first validate the durable receipt and recompute the
        prior commitment from ``prior_call_records``. This method repeats the
        transport-shape checks and can run only immediately after construction,
        when the sole current-process call is ``mcp_server_identity``.
        """
        from scripts.projects.open_model_data import phase3_cycle007_evidence_compile_throughput as throughput

        if self._tool_call_count != 1 or len(self._tool_call_records) != 1:
            raise LocalMcpSourcesClientError("resume_transport_state_too_late")
        current_identity_call = dict(self._tool_call_records[0])
        if current_identity_call.get("tool") != _SERVER_IDENTITY_TOOL:
            raise LocalMcpSourcesClientError("resume_transport_identity_missing")
        current_attestation = self.transport_attestation()
        throughput.validate_transport_state(
            prior_attestation,
            prior_call_records,
            expected_transport=str(current_attestation["transport"]),
            expected_endpoint_sha256=str(current_attestation["endpoint_sha256"]),
            expected_tool_set_sha256=str(current_attestation["required_tool_set_sha256"]),
        )
        self._tool_call_count = int(prior_attestation["tool_call_count"])
        self._tool_call_counts = Counter(
            {str(name): int(count) for name, count in prior_attestation["counts_by_tool"].items()}
        )
        self._tool_call_commitment = str(prior_attestation["ordered_call_commitment_sha256"])
        self._tool_call_records = [dict(record) for record in prior_call_records]
        self._record_tool_call(
            tool=str(current_identity_call["tool"]),
            arguments_sha256=str(current_identity_call["arguments_sha256"]),
            response_sha256=str(current_identity_call["response_sha256"]),
        )

    def transport_attestation(self) -> Mapping[str, Any]:
        """Return a text-free commitment to the actual ordered MCP calls."""
        return {
            "schema_version": "phase3_cycle007_mcp_transport_attestation_v1",
            "transport": (
                "streamable_http" if isinstance(self._transport, RealMcpToolTransport) else "synthetic"
            ),
            "endpoint_sha256": contract.sha256_text(self._endpoint_url),
            "required_tool_set_sha256": contract.sha256_value(sorted(REQUIRED_TOOL_NAMES)),
            "tool_call_count": self._tool_call_count,
            "counts_by_tool": dict(sorted(self._tool_call_counts.items())),
            "server_identity_call_count": self._tool_call_counts.get(_SERVER_IDENTITY_TOOL, 0),
            "ordered_call_commitment_sha256": self._tool_call_commitment,
        }

    def _call_json(self, tool: str, arguments: Mapping[str, Any]) -> Any:
        text = self._call_text(tool, arguments)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LocalMcpSourcesClientError(f"malformed_json_response:{tool}") from exc

    def verify_words(self, words: Sequence[str]) -> Mapping[str, list[Mapping[str, str]]]:
        if not words:
            return {}
        if any(not isinstance(word, str) or not word for word in words) or len(set(words)) != len(words):
            raise LocalMcpSourcesClientError("malformed_verify_words_request")
        text = self._call_text("verify_words", {"words": list(words)})
        lines = [line for line in text.strip().splitlines() if line.strip()]
        if len(lines) != len(words) + 2:
            raise LocalMcpSourcesClientError("malformed_response:verify_words")
        header = _VERIFY_WORDS_HEADER_RE.fullmatch(lines[0])
        summary = _VERIFY_WORDS_SUMMARY_RE.fullmatch(lines[1])
        if header is None or summary is None or int(header["count"]) != len(words) or int(summary["count"]) != len(words):
            raise LocalMcpSourcesClientError("malformed_response:verify_words")
        found_words: set[str] = set()
        for expected_word, line in zip(words, lines[2:], strict=True):
            match = _VERIFY_WORDS_LINE_RE.fullmatch(line)
            if match is None or match["word"] != expected_word:
                raise LocalMcpSourcesClientError("malformed_response:verify_words")
            if match["found"] is not None:
                found_words.add(expected_word)
        if int(summary["found"]) != len(found_words):
            raise LocalMcpSourcesClientError("malformed_response:verify_words")
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
        # Amendment (fixes v3, item 2): an empty/malformed payload (``{}``)
        # must never be treated as "found". A genuine hit always carries the
        # three reviewed boolean keys and never an "error" key; anything
        # else — including a payload missing keys entirely — is not found.
        required_keys = ("is_modern_codified", "has_archaic_form", "has_only_archaic_form")
        has_required_keys = all(isinstance(payload.get(key), bool) for key in required_keys)
        found = "error" not in payload and has_required_keys
        return {
            "found": found,
            "is_modern_codified": bool(payload.get("is_modern_codified")) if found else False,
            "has_archaic_form": bool(payload.get("has_archaic_form")) if found else False,
            "has_only_archaic_form": bool(payload.get("has_only_archaic_form")) if found else False,
        }

    def ulif_cached(self, word: str) -> Mapping[str, Any]:
        payload = self._call_json("query_ulif", {"word": word, "cache_only": True})
        if not isinstance(payload, Mapping) or payload.get("status") not in {"attested", "not_found", "unavailable"}:
            raise LocalMcpSourcesClientError("malformed_cache_only_response:query_ulif")
        return {"status": str(payload["status"]), "payload": payload.get("entry")}

    def slovnyk_me_cached(self, word: str) -> Mapping[str, Any]:
        text = self._call_text("search_slovnyk_me", {"query": word, "live": False})
        status = _prose_status(text, tool="search_slovnyk_me", expected_query=word)
        return {"status": status, "payload": text if status == "attested" else None}

    def grac_cached(self, word: str) -> Mapping[str, Any]:
        payload = self._call_json("query_grac", {"query": word, "cache_only": True})
        if not isinstance(payload, Mapping) or payload.get("status") not in {"attested", "not_found", "unavailable"}:
            raise LocalMcpSourcesClientError("malformed_cache_only_response:query_grac")
        return {"status": str(payload["status"]), "payload": payload.get("entry")}

    def search_style_guide(self, query: str) -> Mapping[str, Any]:
        text = self._call_text("search_style_guide", {"query": query})
        status = _prose_status(text, tool="search_style_guide", expected_query=query)
        return {"status": status, "hits": text}

    def search_antonenko_text(self, query: str) -> Mapping[str, Any]:
        text = self._call_text("search_text", {"query": query, "source_file": ANTONENKO_SOURCE_FILE})
        status = _prose_status(text, tool="search_text", expected_query=query)
        return {"status": status, "hits": text}

    def search_ua_gec_errors(self, query: str) -> Mapping[str, Any]:
        text = self._call_text("search_ua_gec_errors", {"query": query})
        status = _prose_status(text, tool="search_ua_gec_errors", expected_query=query)
        return {"status": status, "hits": text}

    def search_heritage_cached(self, query: str) -> Mapping[str, Any]:
        # include_live_slovnyk explicit False; cache-only, never a live fallback.
        text = self._call_text("search_heritage", {"query": query, "include_live_slovnyk": False})
        status = _prose_status(text, tool="search_heritage", expected_query=query)
        return {"status": status, "hits": text}

    def check_russian_shadow(self, word: str) -> Mapping[str, Any]:
        payload = self._call_json("check_russian_shadow", {"word": word})
        # Amendment (fixes v3, item 2): require the exact reviewed keys/types
        # — an empty or partial payload (``{}``) must never be accepted as a
        # suspicion result.
        if (
            not isinstance(payload, Mapping)
            or not isinstance(payload.get("matches_russian"), bool)
            or "russian_lemma" not in payload
            or not isinstance(payload.get("confidence"), (int, float))
            or isinstance(payload.get("confidence"), bool)
        ):
            raise LocalMcpSourcesClientError("malformed_json_response:check_russian_shadow")
        return payload

    def query_pravopys(self, topic: str) -> Mapping[str, Any]:
        text = self._call_text("query_pravopys", {"topic": topic})
        status = _prose_status(text, tool="query_pravopys")
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
    russian_shadow_source_version = _russian_shadow_source_version()

    source_text = str(row.get("source_text", ""))
    forms = extract_forms(source_text)
    evidence: list[dict[str, Any]] = []
    seen_evidence_ids: set[str] = set()
    retrieval_payloads: dict[str, Any] = {}

    def _append_unique(record: dict[str, Any]) -> None:
        """Keep one canonical copy when query planning reaches the same fact twice.

        A surface form can also occur as a repeated compound component (or as
        both a standalone form and a component).  Those routes intentionally
        produce the same evidence identity; the sidecar contract requires the
        resulting record set to contain that identity exactly once.
        """
        record_id = str(record["evidence_id"])
        if record_id in seen_evidence_ids:
            return
        seen_evidence_ids.add(record_id)
        evidence.append(record)

    def _add(record_and_payload: tuple[dict[str, Any], Any]) -> dict[str, Any]:
        record, payload = record_and_payload
        retrieval_payloads[str(record["retrieval_sha256"])] = payload
        _append_unique(record)
        return record

    # source_metadata: preserve existing provenance, hashed, never printed.
    # The row's own frozen-locator hash is folded into the locator field
    # (part of the identity hash) rather than into query_sha256, so
    # query_sha256 can follow the uniform no-query domain-separated rule
    # (amendment step 9) even for this metadata-only record.
    frozen_locator_sha256 = str(row.get("frozen_locator_sha256") or contract.sha256_text(""))
    source_text_sha256 = str(row.get("source_text_sha256") or contract.sha256_text(source_text))
    # Amendment (fixes v3, item 5): retrieval_sha256 must equal
    # sha256_value(payload) for the exact payload stored under it — never a
    # raw file/text hash computed independently of what retrieval_payloads
    # actually holds.
    metadata_payload = {"source_text_sha256": source_text_sha256}
    metadata_retrieval_sha256 = contract.sha256_value(metadata_payload)
    metadata_record = contract.build_evidence_record(
        channel="source_metadata",
        source_identity=str(row.get("family_id") or "unknown"),
        source_version=sources_db_source_version,
        locator=f"phase3-cycle007-row:{row.get('unit_id')}:{frozen_locator_sha256}",
        query=None,
        status="attested",
        supports="metadata_only",
        retrieval_sha256=metadata_retrieval_sha256,
        parser_id="phase3-cycle007-row-provenance-v1",
        parser_version="1",
        row=row,
        phenomenon_id=None,
    )
    retrieval_payloads[metadata_retrieval_sha256] = metadata_payload
    _append_unique(metadata_record)

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
                # Repeated compounds legitimately yield the same component
                # more than once, while the reviewed MCP batch contract
                # rejects duplicate words. Query each distinct component once
                # in first-occurrence order; its evidence identity is the same
                # for every route that reached it.
                unique_parts = list(dict.fromkeys(parts))
                part_batch = client.verify_words(unique_parts)
                for part in unique_parts:
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

    # Amendment (fixes v3, item 3): frozen Cycle005 Pravopys provenance,
    # bound before any model call. pravopys_2026_normative only ever binds
    # for a row whose frozen family is Pravopys 2026; pravopys_2019_comparison
    # is queried once per row and rebound (never re-queried) to every
    # phenomenon. Both channels are already explicitly phenomenon-scoped by
    # construction — never routed through the generic row-level rebinder.
    for record_and_payload in _bind_pravopys_2026_for_row(row, residual_phenomena):
        _add(record_and_payload)
    for record_and_payload in _bind_pravopys_2019_comparison_for_row(
        row, client, residual_phenomena, source_version=PRAVOPYS_2019_PDF_SHA256
    ):
        _add(record_and_payload)

    # Amendment: phenomenon-scoped evidence, produced before any model call.
    row_level_records = list(evidence)
    for phenomenon_id in residual_phenomena:
        for bound_record in bind_phenomenon_scoped_evidence(row_level_records, phenomenon_id, row):
            _append_unique(bound_record)
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
PRAVOPYS_2019_PDF_SHA256 = "9adcb3e7e6b68db62719a4e8b0c34d7b1f4abde2986c694ab77662f2791ad24c"
PRAVOPYS_2026_CONTEXT_RECEIPT_SHA256 = "5da6f60e1cf5527fd98e44b4396472d871d359cd6b9dc76e3806c73a15c2b827"
PRAVOPYS_2026_DECISION_LOCATOR = (
    "https://mova.gov.ua/rozyasnennya/rishennia-2026/berezen-2026/"
    "rishennia-47-vid-1-bereznia"
)
PRAVOPYS_2026_DOWNLOAD_LOCATOR = (
    "https://mova.gov.ua/storage/app/sites/19/2026/rishennja-komisiji/01-03/"
    "sdm-ukrayinskii-pravopis-vidannia.pdf"
)
PRAVOPYS_2019_DOWNLOAD_LOCATOR = (
    "https://mon.gov.ua/storage/app/media/zagalna%20serednya/05062019-onovl-pravo.pdf"
)
DEFAULT_PRAVOPYS_CONTEXT_RECEIPT = (
    ROOT / "data/projects/open_model_data/inventory/phase3_pravopys_evaluation_context_receipt_v1.json"
)

# The one frozen family/source provenance value (phase3_source_universe.py
# ``stage_family("pravopys_2026_complete", ...)``) that ever grants a row
# 2026 normative_rule support. An unrelated family's row must never receive
# it, no matter how its text looks.
PRAVOPYS_2026_FAMILY_ID = "pravopys_2026_complete"


def _pravopys_2026_locator(context_receipt_path: Path) -> str:
    del context_receipt_path
    return PRAVOPYS_2026_DOWNLOAD_LOCATOR


def _pravopys_2026_payload(context_receipt_path: Path) -> tuple[str, dict[str, Any]]:
    """The frozen 2026 binding fact as a hashable retrieval payload.

    Amendment (fixes v3, item 3/5): ``retrieval_sha256`` must be
    ``sha256_value`` of the *payload actually stored* under it (the same
    invariant every other channel holds), never a raw file hash computed
    independently of what the sidecar's ``retrieval_payloads`` table holds.
    """
    receipt_sha256 = contract.sha256_file(context_receipt_path) if context_receipt_path.is_file() else None
    receipt: Mapping[str, Any] = {}
    if receipt_sha256 == PRAVOPYS_2026_CONTEXT_RECEIPT_SHA256:
        try:
            loaded = json.loads(context_receipt_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            loaded = None
        if isinstance(loaded, Mapping):
            receipt = loaded
    bindings = receipt.get("bindings") if isinstance(receipt.get("bindings"), Mapping) else {}
    status = (
        "attested"
        if receipt_sha256 == PRAVOPYS_2026_CONTEXT_RECEIPT_SHA256
        and bindings.get("pravopys_2026_pdf_sha256") == PRAVOPYS_2026_PDF_SHA256
        and bindings.get("pravopys_2019_pdf_sha256") == PRAVOPYS_2019_PDF_SHA256
        and receipt.get("text_free") is True
        and receipt.get("provider_calls") is False
        else "unavailable"
    )
    payload = {
        "pdf_sha256": PRAVOPYS_2026_PDF_SHA256,
        "context_receipt_sha256": receipt_sha256,
        "official_decision_locator": PRAVOPYS_2026_DECISION_LOCATOR,
        "official_download_locator": PRAVOPYS_2026_DOWNLOAD_LOCATOR,
        "status": status,
    }
    return status, payload


def bind_pravopys_2026_evidence(
    row: Mapping[str, Any],
    phenomenon_id: str,
    *,
    context_receipt_path: Path | None = None,
) -> dict[str, Any]:
    """Bind the frozen Pravopys 2026 normative fact to one residual phenomenon.

    This is deliberately not a per-row/per-form query: within this frozen
    Phase 3 evaluation the 2026 edition is bound by explicit task-specific
    identity (PDF + context-receipt SHA-256), not fetched live — the general
    Sources MCP ``query_pravopys`` tool only exposes 2019 and is
    comparison-only here. Standalone/manual entry point; ``compile_row_evidence``
    uses ``_bind_pravopys_2026_for_row`` instead so the receipt is only
    hashed once per row, not once per phenomenon.

    ``context_receipt_path`` defaults to the current module-level
    ``DEFAULT_PRAVOPYS_CONTEXT_RECEIPT`` (resolved at call time, not frozen
    into the function signature) so tests can monkeypatch that constant.
    """
    contract.require(bool(phenomenon_id), "pravopys_2026_normative evidence requires a phenomenon_id")
    context_receipt_path = context_receipt_path or DEFAULT_PRAVOPYS_CONTEXT_RECEIPT
    status, payload = _pravopys_2026_payload(context_receipt_path)
    return contract.build_evidence_record(
        channel="pravopys_2026_normative",
        source_identity="pravopys-2026-official-edition",
        source_version=PRAVOPYS_2026_PDF_SHA256,
        locator=_pravopys_2026_locator(context_receipt_path),
        query=None,
        status=status,
        supports="normative_rule" if status == "attested" else "no_conclusion",
        retrieval_sha256=contract.sha256_value(payload),
        parser_id="pravopys-2026-frozen-binding-v1",
        parser_version="1",
        row=row,
        phenomenon_id=phenomenon_id,
        negative_reason=None if status == "attested" else "pravopys_2026_context_receipt_hash_mismatch",
    )


def _bind_pravopys_2026_for_row(
    row: Mapping[str, Any],
    residual_phenomena: Sequence[str],
    *,
    context_receipt_path: Path | None = None,
) -> list[tuple[dict[str, Any], Any]]:
    """Bind the frozen 2026 normative fact to every residual phenomenon of a Pravopys-2026-family row.

    Amendment (fixes v3, item 3): only rows whose frozen family/source
    provenance is Pravopys 2026 (``row["family_id"] == PRAVOPYS_2026_FAMILY_ID``)
    ever receive 2026 normative_rule support; every other family gets none —
    ``bind_phenomenon_scoped_evidence`` never grants it either (this channel
    is not in ``_PHENOMENON_SCOPABLE_CHANNELS``). The receipt is hashed once
    per row and the identical retrieval payload is reused (same
    ``retrieval_sha256``) across all 23 phenomena.

    ``context_receipt_path`` defaults to the current module-level
    ``DEFAULT_PRAVOPYS_CONTEXT_RECEIPT`` (resolved at call time).
    """
    if not residual_phenomena or row.get("family_id") != PRAVOPYS_2026_FAMILY_ID:
        return []
    context_receipt_path = context_receipt_path or DEFAULT_PRAVOPYS_CONTEXT_RECEIPT
    status, payload = _pravopys_2026_payload(context_receipt_path)
    locator = _pravopys_2026_locator(context_receipt_path)
    retrieval_sha256 = contract.sha256_value(payload)
    records: list[tuple[dict[str, Any], Any]] = []
    for phenomenon_id in residual_phenomena:
        record = contract.build_evidence_record(
            channel="pravopys_2026_normative",
            source_identity="pravopys-2026-official-edition",
            source_version=PRAVOPYS_2026_PDF_SHA256,
            locator=locator,
            query=None,
            status=status,
            supports="normative_rule" if status == "attested" else "no_conclusion",
            retrieval_sha256=retrieval_sha256,
            parser_id="pravopys-2026-frozen-binding-v1",
            parser_version="1",
            row=row,
            phenomenon_id=phenomenon_id,
            negative_reason=None if status == "attested" else "pravopys_2026_context_receipt_hash_mismatch",
        )
        records.append((record, payload))
    return records


def _pravopys_2019_comparison_record(
    row: Mapping[str, Any],
    phenomenon_id: str,
    result: Mapping[str, Any],
    *,
    query: str,
    source_version: str,
) -> dict[str, Any]:
    contract.require(bool(phenomenon_id), "pravopys_2019_comparison evidence requires a phenomenon_id")
    return contract.build_evidence_record(
        channel="pravopys_2019_comparison",
        source_identity="pravopys-2019-comparison",
        source_version=source_version,
        locator=PRAVOPYS_2019_DOWNLOAD_LOCATOR,
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


def bind_pravopys_2019_comparison_evidence(
    row: Mapping[str, Any],
    phenomenon_id: str,
    client: SourcesClient,
    *,
    query: str,
    source_version: str,
) -> dict[str, Any]:
    """Bind a comparison-only 2019 Pravopys result to one residual phenomenon.

    Amendment step 8: this calls the ``query_pravopys`` MCP tool — never
    ``search_style_guide``, which is a distinct Антоненко-Давидович channel.
    ``query_pravopys`` is explicitly comparison-only in this evaluation: its
    result can never carry ``normative_rule`` support (enforced by the
    closed per-channel claim boundary in the contract module).
    ``source_version`` must be an exact source/database hash (never a
    URL-like literal) — callers pass the compiler's own
    ``identity["sources_db_sha256"]``. Standalone/manual entry point;
    ``compile_row_evidence`` uses ``_bind_pravopys_2019_comparison_for_row``
    instead so ``query_pravopys`` is only called once per row, not once per
    phenomenon.
    """
    result = client.query_pravopys(query)
    return _pravopys_2019_comparison_record(row, phenomenon_id, result, query=query, source_version=source_version)


def _bind_pravopys_2019_comparison_for_row(
    row: Mapping[str, Any],
    client: SourcesClient,
    residual_phenomena: Sequence[str],
    *,
    source_version: str,
) -> list[tuple[dict[str, Any], Any]]:
    """One ``query_pravopys`` call per row, rebound to every residual phenomenon.

    Amendment (fixes v3, item 3): "Query the MCP query_pravopys 2019
    comparison path once per residual row (not once per phenomenon), store/
    deduplicate its normalized private payload, then rebind that one
    comparison-only result to all 23 potential phenomena."
    """
    if not residual_phenomena:
        return []
    query = str(row.get("source_text", "")).strip() or str(row.get("unit_id", ""))
    result = client.query_pravopys(query)
    return [
        (
            _pravopys_2019_comparison_record(row, phenomenon_id, result, query=query, source_version=source_version),
            result,
        )
        for phenomenon_id in residual_phenomena
    ]


# --------------------------------------------------------------------------
# Packet-level sidecar assembly and atomic private write.
# --------------------------------------------------------------------------


_PACKET_BINDING_KEYS: frozenset[str] = frozenset({"canonical_basename", "raw_sha256", "packet_identity_set_sha256"})


def _default_packet_binding(packet_index: int, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """A self-derived packet binding for a bare (non-package-bound) compile.

    Always internally recomputable from this exact sidecar's own rows —
    ``packet_identity_set_sha256`` is the same materializer identity-set
    hash a real source package carries, and ``raw_sha256`` is a canonical
    hash of the exact row list this sidecar was built from (not a real
    packet file's bytes, since a bare ``compile_sidecar_bundle`` call has
    none — ``compile_cycle007_package`` supplies the real verified
    materializer binding instead via ``packet_binding``/``packet_bindings``).
    """
    materializer = _materializer_module()
    return {
        "canonical_basename": f"packet-{packet_index:04d}.json",
        "raw_sha256": contract.sha256_value({"rows": list(rows)}),
        "packet_identity_set_sha256": materializer.identity_set(list(rows)),
    }


def compile_packet_sidecar(
    packet_index: int,
    rows: Sequence[Mapping[str, Any]],
    client: SourcesClient,
    *,
    residual_lane: bool = False,
    packet_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile one packet's sidecar.

    Amendment (fixes v3, item 4): every sidecar persists its source packet's
    lane, canonical basename, raw packet SHA-256, and packet identity-set
    SHA-256 — ``packet_binding`` (when given by ``compile_cycle007_package``,
    already verified against the materialized source package) or, for a bare
    compile with no source package, a self-derived binding computed directly
    from ``rows``.
    """
    identity = client.server_identity()
    residual_phenomena = contract.RESIDUAL_PHENOMENON_TAXONOMY if residual_lane else ()
    row_records = []
    retrieval_payloads: dict[str, Any] = {}
    for row in rows:
        row_record = compile_row_evidence(row, client, identity=identity, residual_phenomena=residual_phenomena)
        retrieval_payloads.update(row_record.pop("retrieval_payloads"))
        row_records.append(row_record)
    if packet_binding is None:
        packet_binding = _default_packet_binding(packet_index, rows)
    else:
        contract.require(set(packet_binding) == _PACKET_BINDING_KEYS, "malformed packet_binding")
    body = {
        "schema_version": SIDECAR_SCHEMA_VERSION,
        "evaluation_cycle_id": EVALUATION_CYCLE_ID,
        # Amendment (fixes v3, item 5): sidecars must carry their lane so a
        # validator can require a clean-lane row to carry no
        # phenomenon-scoped evidence and a residual-lane row to carry
        # exactly the frozen 23-phenomenon keys.
        "lane": "residual_label" if residual_lane else "clean_label",
        "packet_binding": dict(packet_binding),
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
    packet_bindings: Sequence[Mapping[str, Any] | None] | None = None,
    source_package_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile every packet's sidecar into a fresh staging directory, then atomically install.

    Amendment step 14: the whole bundle is built and fully validated in a
    fresh mode-0700 staging directory before anything is installed at
    ``output_dir``; the destination is refused up front if it already
    exists (including as a nonempty directory or a symlink), and on any
    failure only the staging directory this call created is removed —
    ``output_dir`` is never touched unless every packet validated.

    Amendment (fixes v3, item 4): every sidecar and the public manifest
    index persist their source packet's lane/canonical-basename/raw-SHA-256/
    identity-set-SHA-256 binding (``packet_bindings`` — real verified
    materializer values from ``compile_cycle007_package``, or a self-derived
    binding per packet when omitted). ``source_package_binding`` — the
    materialization custody/manifest hashes and ordered identity commitment
    — is persisted in the text-free manifest whenever a real source package
    backs this compile; ``None`` for a bare, package-free compile.
    """
    if output_dir.exists() or output_dir.is_symlink():
        raise contract.EvidenceContractError(f"refusing to compile into an existing destination: {output_dir}")
    residual_flags = list(residual_lane_packets) if residual_lane_packets is not None else [False] * len(packets)
    contract.require(len(residual_flags) == len(packets), "residual_lane_packets length must match packets")
    bindings = list(packet_bindings) if packet_bindings is not None else [None] * len(packets)
    contract.require(len(bindings) == len(packets), "packet_bindings length must match packets")

    output_dir.parent.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent))
    os.chmod(staging, PRIVATE_DIR_MODE)
    committed = False
    try:
        identity = client.server_identity()
        # Amendment (fixes v3, item 5/6): the compiler's own freshly derived
        # current code/source identity — never taken from a sidecar being
        # validated — so ``validate_sidecar``/``validate_manifest`` reject a
        # rehashed sidecar that self-consistently substitutes arbitrary
        # code/source hashes.
        expected_identity = {
            "tokenizer_id": TOKENIZER_ID,
            "tokenizer_version": TOKENIZER_VERSION,
            "code_hashes": CODE_HASHES,
            "server_code_sha256": identity["server_code_sha256"],
            "sources_db_sha256": identity["sources_db_sha256"],
            "vesum_db_sha256": identity["vesum_db_sha256"],
        }
        channel_counts: Counter[str] = Counter()
        status_counts: Counter[str] = Counter()
        supports_counts: Counter[str] = Counter()
        sufficient_support_rows = 0
        archaic_only_risk_rows = 0
        russian_shadow_suspected_rows = 0
        row_count = 0
        sidecar_index: list[dict[str, Any]] = []
        for packet_index, (rows, residual_lane, packet_binding) in enumerate(
            zip(packets, residual_flags, bindings, strict=True), start=1
        ):
            sidecar = compile_packet_sidecar(
                packet_index, rows, client, residual_lane=residual_lane, packet_binding=packet_binding
            )
            # Amendment (fixes v3, item 5): validate every sidecar before it
            # is ever written to disk.
            validator.validate_sidecar(sidecar, expected_identity=expected_identity)
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
                    "lane": sidecar["lane"],
                    "packet_binding": sidecar["packet_binding"],
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
            # Amendment (fixes v3, item 4): materialization custody/manifest
            # hashes and ordered identity commitment, when this compile is
            # backed by a real materialized source package.
            "source_package_binding": dict(source_package_binding) if source_package_binding is not None else None,
            "mcp_transport_attestation": (
                dict(client.transport_attestation()) if isinstance(client, LocalMcpSourcesClient) else None
            ),
        }
        manifest["manifest_sha256"] = contract.sha256_value(manifest)
        # Amendment (fixes v3, item 5): validate the manifest before installation.
        validator.validate_manifest(manifest, expected_identity=expected_identity)
        manifest_bytes = (contract.canonical_json(manifest) + "\n").encode("utf-8")
        _atomic_write_private(staging / "manifest.json", manifest_bytes)
        _walk_private_modes(staging)
        for child in staging.iterdir():
            _fsync_directory(child.parent)
        _install_staged_bundle(staging, output_dir)
        _fsync_directory(output_dir.parent)
        _walk_private_modes(output_dir)
        committed = True
        return manifest
    finally:
        if not committed:
            import shutil

            shutil.rmtree(staging, ignore_errors=True)


def _empty_bundle_aggregate() -> dict[str, Any]:
    return {
        "channel_counts": Counter(),
        "status_counts": Counter(),
        "supports_counts": Counter(),
        "sufficient_support_rows": 0,
        "archaic_only_risk_rows": 0,
        "russian_shadow_suspected_rows": 0,
        "row_count": 0,
        "sidecar_index": [],
    }


def _accumulate_validated_sidecar(
    aggregate: dict[str, Any],
    sidecar: Mapping[str, Any],
    sidecar_sha256: str,
) -> None:
    for row_record in sidecar["rows"]:
        aggregate["row_count"] += 1
        aggregate["sufficient_support_rows"] += int(row_record["sufficient_support"])
        aggregate["archaic_only_risk_rows"] += int(row_record["archaic_only_risk"])
        aggregate["russian_shadow_suspected_rows"] += int(row_record["russian_shadow_suspected"])
        for evidence_record in row_record["evidence"]:
            aggregate["channel_counts"][evidence_record["channel"]] += 1
            aggregate["status_counts"][evidence_record["status"]] += 1
            aggregate["supports_counts"][evidence_record["supports"]] += 1
    aggregate["sidecar_index"].append(
        {
            "packet_index": sidecar["packet_index"],
            "row_count": sidecar["row_count"],
            "sidecar_sha256": sidecar_sha256,
            "sidecar_id": sidecar["sidecar_id"],
            "lane": sidecar["lane"],
            "packet_binding": sidecar["packet_binding"],
        }
    )


def _build_bundle_manifest(
    *,
    aggregate: Mapping[str, Any],
    packet_count: int,
    identity: Mapping[str, Any],
    source_package_binding: Mapping[str, Any] | None,
    transport_attestation: Mapping[str, Any],
) -> dict[str, Any]:
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
        "packet_count": packet_count,
        "row_count": aggregate["row_count"],
        "network_lookups_performed": 0,
        "counts_by_channel": dict(sorted(aggregate["channel_counts"].items())),
        "counts_by_status": dict(sorted(aggregate["status_counts"].items())),
        "counts_by_supports": dict(sorted(aggregate["supports_counts"].items())),
        "sufficient_support_rows": aggregate["sufficient_support_rows"],
        "archaic_only_risk_rows": aggregate["archaic_only_risk_rows"],
        "russian_shadow_suspected_rows": aggregate["russian_shadow_suspected_rows"],
        "sidecars": aggregate["sidecar_index"],
        "source_package_binding": dict(source_package_binding) if source_package_binding is not None else None,
        "mcp_transport_attestation": dict(transport_attestation),
    }
    manifest["manifest_sha256"] = contract.sha256_value(manifest)
    return manifest


def compile_sidecar_bundle_resumable(
    packets: Sequence[Sequence[Mapping[str, Any]]],
    client: LocalMcpSourcesClient,
    output_dir: Path,
    *,
    residual_lane_packets: Sequence[bool],
    packet_bindings: Sequence[Mapping[str, Any] | None],
    source_package_binding: Mapping[str, Any] | None,
    _interrupt_after_packet: int | None = None,
    _interrupt_after_install: bool = False,
) -> dict[str, Any]:
    """Compile serially with a validated, durable sealed-packet prefix.

    Resume changes custody only. Every reused sidecar is re-read, checked
    against the current frozen identity and packet binding, and passed through
    the production validator before it contributes to the final manifest.
    """
    from scripts.projects.open_model_data import phase3_cycle007_evidence_compile_throughput as throughput

    if not isinstance(client, LocalMcpSourcesClient):
        raise contract.EvidenceContractError("resumable compile requires LocalMcpSourcesClient")
    residual_flags = list(residual_lane_packets)
    bindings = list(packet_bindings)
    contract.require(len(residual_flags) == len(packets), "residual_lane_packets length must match packets")
    contract.require(len(bindings) == len(packets), "packet_bindings length must match packets")
    identity = client.server_identity()
    expected_identity = {
        "tokenizer_id": TOKENIZER_ID,
        "tokenizer_version": TOKENIZER_VERSION,
        "code_hashes": CODE_HASHES,
        "server_code_sha256": identity["server_code_sha256"],
        "sources_db_sha256": identity["sources_db_sha256"],
        "vesum_db_sha256": identity["vesum_db_sha256"],
    }
    target_row_count = sum(len(packet) for packet in packets)
    resume_identity = throughput.build_resume_identity(
        expected_identity,
        source_package_binding=source_package_binding,
        packet_bindings=bindings,
        residual_lane_packets=residual_flags,
        target_packet_count=len(packets),
        target_row_count=target_row_count,
    )
    root = throughput.resume_root_for(output_dir)

    # A crash after the single atomic install but before metadata cleanup is
    # repaired by validating the installed bundle and removing only metadata.
    if os.path.lexists(output_dir):
        if os.path.lexists(root) and (not root.is_dir() or root.is_symlink()):
            raise contract.EvidenceContractError("invalid resume metadata root")
        root_is_live = root.is_dir()
        lock_context = throughput.exclusive_resume_lock(root) if root_is_live else contextlib.nullcontext()
        with lock_context:
            if root_is_live:
                throughput.inspect_resume_root(root)
            throughput.assert_private_tree(output_dir)
            actual_names = {path.name for path in output_dir.iterdir()}
            expected_names = {"manifest.json"} | {
                throughput.sidecar_filename(index) for index in range(1, len(packets) + 1)
            }
            contract.require(actual_names == expected_names, "installed bundle shape drift")
            manifest_path = output_dir / "manifest.json"
            manifest = throughput.load_sidecar(manifest_path)
            validator.validate_manifest(manifest, expected_identity=expected_identity)
            contract.require(manifest["packet_count"] == len(packets), "installed packet count drift")
            contract.require(manifest["row_count"] == target_row_count, "installed row count drift")
            contract.require(
                manifest["source_package_binding"] == source_package_binding,
                "installed source package binding drift",
            )
            progress: Mapping[str, Any] | None = None
            if root_is_live and os.path.lexists(root / throughput.PROGRESS_NAME):
                current_attestation = client.transport_attestation()
                progress = throughput.read_progress(root / throughput.PROGRESS_NAME)
                throughput.validate_progress_receipt(
                    progress,
                    resume_identity,
                    expected_transport=str(current_attestation["transport"]),
                    expected_endpoint_sha256=str(current_attestation["endpoint_sha256"]),
                    expected_tool_set_sha256=str(current_attestation["required_tool_set_sha256"]),
                    sealed_packet_count=len(packets),
                )
            aggregate = _empty_bundle_aggregate()
            last_sha256: str | None = None
            for packet_index, expected_binding in enumerate(bindings, start=1):
                sidecar_path = output_dir / throughput.sidecar_filename(packet_index)
                sidecar = throughput.load_sidecar(sidecar_path)
                validator.validate_sidecar(sidecar, expected_identity=expected_identity)
                contract.require(sidecar["packet_binding"] == expected_binding, "installed packet binding drift")
                expected_lane = "residual_label" if residual_flags[packet_index - 1] else "clean_label"
                contract.require(sidecar["lane"] == expected_lane, "installed lane drift")
                contract.require(sidecar["row_count"] == len(packets[packet_index - 1]), "installed row count drift")
                last_sha256 = contract.sha256_file(sidecar_path)
                _accumulate_validated_sidecar(aggregate, sidecar, last_sha256)
            if progress is not None:
                contract.require(
                    progress["last_sealed_sidecar_sha256"] == last_sha256,
                    "installed last sidecar drift",
                )
            rebuilt = _build_bundle_manifest(
                aggregate=aggregate,
                packet_count=len(packets),
                identity=identity,
                source_package_binding=source_package_binding,
                transport_attestation=manifest["mcp_transport_attestation"],
            )
            contract.require(rebuilt == manifest, "installed manifest/file drift")
            if root_is_live:
                throughput.cleanup_resume_metadata(root)
            else:
                throughput.reap_cleanup_tombstone(root)
        return manifest

    root, bundle = throughput.prepare_resume_root(output_dir)
    with throughput.exclusive_resume_lock(root):
        throughput.inspect_resume_root(root)
        indexes, sealed = throughput.inspect_sealed_prefix(bundle)
        progress_path = root / throughput.PROGRESS_NAME
        progress: Mapping[str, Any] | None = None
        if os.path.lexists(progress_path):
            progress = throughput.read_progress(progress_path)
            progress_sealed = progress.get("sealed_packet_count")
            contract.require(
                isinstance(progress_sealed, int) and not isinstance(progress_sealed, bool),
                "resume progress count invalid",
            )
            if sealed == progress_sealed + 1:
                trailing = bundle / throughput.sidecar_filename(sealed)
                trailing.unlink()
                _fsync_directory(bundle)
                indexes.pop()
                sealed -= 1
            contract.require(sealed == progress_sealed, "resume prefix/progress mismatch")
        elif sealed:
            raise contract.EvidenceContractError("resume progress missing")

        aggregate = _empty_bundle_aggregate()
        last_sha256: str | None = None
        last_sidecar_id: str | None = None
        for packet_index in indexes:
            sidecar_path = bundle / throughput.sidecar_filename(packet_index)
            sidecar = throughput.load_sidecar(sidecar_path)
            validator.validate_sidecar(sidecar, expected_identity=expected_identity)
            contract.require(sidecar["packet_index"] == packet_index, "resume packet index drift")
            contract.require(sidecar["packet_binding"] == bindings[packet_index - 1], "resume packet binding drift")
            expected_lane = "residual_label" if residual_flags[packet_index - 1] else "clean_label"
            contract.require(sidecar["lane"] == expected_lane, "resume lane drift")
            contract.require(sidecar["row_count"] == len(packets[packet_index - 1]), "resume row count drift")
            last_sha256 = contract.sha256_file(sidecar_path)
            last_sidecar_id = str(sidecar["sidecar_id"])
            _accumulate_validated_sidecar(aggregate, sidecar, last_sha256)

        current_attestation = client.transport_attestation()
        if progress is not None:
            throughput.validate_progress_receipt(
                progress,
                resume_identity,
                expected_transport=str(current_attestation["transport"]),
                expected_endpoint_sha256=str(current_attestation["endpoint_sha256"]),
                expected_tool_set_sha256=str(current_attestation["required_tool_set_sha256"]),
                sealed_packet_count=sealed,
                last_sealed_sidecar_sha256=last_sha256,
            )
            contract.require(progress["target_packet_count"] == len(packets), "resume packet target drift")
            contract.require(progress["target_row_count"] == target_row_count, "resume row target drift")
            if sealed:
                contract.require(progress["last_sealed_sidecar_id"] == last_sidecar_id, "resume sidecar id drift")
            client.resume_transport_state(
                progress["mcp_transport_attestation"],
                progress["mcp_call_records"],
            )
        else:
            throughput.write_progress(
                root,
                throughput.build_progress_receipt(
                    sealed_packet_count=0,
                    target_packet_count=len(packets),
                    target_row_count=target_row_count,
                    last_sealed_sidecar_sha256=None,
                    last_sealed_sidecar_id=None,
                    resume_identity=resume_identity,
                    mcp_transport_attestation=client.transport_attestation(),
                    mcp_call_records=client.transport_call_records(),
                ),
            )

        manifest_path = bundle / "manifest.json"
        if os.path.lexists(manifest_path):
            manifest_path.unlink()
            _fsync_directory(bundle)
        for packet_index in range(sealed + 1, len(packets) + 1):
            sidecar = compile_packet_sidecar(
                packet_index,
                packets[packet_index - 1],
                client,
                residual_lane=residual_flags[packet_index - 1],
                packet_binding=bindings[packet_index - 1],
            )
            validator.validate_sidecar(sidecar, expected_identity=expected_identity)
            payload = (contract.canonical_json(sidecar) + "\n").encode("utf-8")
            sidecar_path = bundle / throughput.sidecar_filename(packet_index)
            last_sha256 = _atomic_write_private(sidecar_path, payload)
            _fsync_directory(bundle)
            last_sidecar_id = str(sidecar["sidecar_id"])
            _accumulate_validated_sidecar(aggregate, sidecar, last_sha256)
            throughput.write_progress(
                root,
                throughput.build_progress_receipt(
                    sealed_packet_count=packet_index,
                    target_packet_count=len(packets),
                    target_row_count=target_row_count,
                    last_sealed_sidecar_sha256=last_sha256,
                    last_sealed_sidecar_id=last_sidecar_id,
                    resume_identity=resume_identity,
                    mcp_transport_attestation=client.transport_attestation(),
                    mcp_call_records=client.transport_call_records(),
                ),
            )
            if _interrupt_after_packet == packet_index:
                raise RuntimeError("synthetic_interrupt_after_seal")

        manifest = _build_bundle_manifest(
            aggregate=aggregate,
            packet_count=len(packets),
            identity=identity,
            source_package_binding=source_package_binding,
            transport_attestation=client.transport_attestation(),
        )
        validator.validate_manifest(manifest, expected_identity=expected_identity)
        _atomic_write_private(
            manifest_path,
            (contract.canonical_json(manifest) + "\n").encode("utf-8"),
        )
        _fsync_directory(bundle)
        throughput.assert_private_tree(root)
        throughput.atomic_install_bundle(bundle, output_dir)
        if _interrupt_after_install:
            raise RuntimeError("synthetic_interrupt_after_install")
        throughput.cleanup_resume_metadata(root)
    throughput.assert_private_tree(output_dir)
    return manifest


def _install_staged_bundle(staging: Path, output_dir: Path) -> None:
    """Atomically claim ``output_dir`` and move the staged bundle into it.

    ``os.mkdir`` is a single atomic kernel syscall: it fails closed with
    ``FileExistsError`` if anything — including a directory a concurrent
    actor created after this call's earlier existence check — now occupies
    ``output_dir``. This closes the TOCTOU window a plain ``os.replace``
    onto ``output_dir`` would leave open (POSIX rename silently succeeds
    when the destination is an existing *empty* directory).
    """
    try:
        os.mkdir(output_dir)
    except FileExistsError:
        raise contract.EvidenceContractError(f"destination created concurrently: {output_dir}") from None
    # See the materializer's equivalent installer.  Claiming the destination
    # preserves no-overwrite semantics; restoring entries already moved makes
    # a later rename failure atomic from callers' perspective.  Use ``rmdir``
    # only, so a concurrently written destination is never recursively
    # deleted during error handling.
    moved: list[Path] = []
    try:
        os.chmod(output_dir, PRIVATE_DIR_MODE)
        for child in sorted(staging.iterdir()):
            os.rename(child, output_dir / child.name)
            moved.append(child)
    except BaseException:
        for child in reversed(moved):
            installed = output_dir / child.name
            if not installed.exists() and not installed.is_symlink():
                break
            try:
                os.rename(installed, staging / child.name)
            except OSError:
                break
        # Do not recursively remove a destination after an install error.
        with contextlib.suppress(OSError):
            os.rmdir(output_dir)
        raise


# --------------------------------------------------------------------------
# Package-bound production entrypoint (amendment step 13).
# --------------------------------------------------------------------------

REAL_PACKET_COUNT = 204
REAL_ROW_COUNT = 10_159
_RESIDUAL_LANE_NAME = "residual_label"

_MATERIALIZATION_PACKET_RECORD_FIELDS: frozenset[str] = frozenset(
    {
        "lane",
        "packet_index",
        "canonical_basename",
        "row_count",
        "raw_sha256",
        "packet_identity_set_sha256",
    }
)
_MATERIALIZATION_PACKET_FIELDS: frozenset[str] = frozenset(
    {
        "schema_version",
        "evaluation_cycle_id",
        "lane",
        "packet_index",
        "row_count",
        "rows",
        "packet_identity_set_sha256",
    }
)
_MATERIALIZATION_MANIFEST_FIELDS: frozenset[str] = frozenset(
    {
        "schema_version",
        "evaluation_cycle_id",
        "source_evaluation_cycle_id",
        "text_free",
        "custody_receipt_raw_sha256",
        "ordered_identity_commitment_sha256",
        "identity_union_commitment_sha256",
        "ordered_packet_commitment_sha256",
        "packet_count",
        "row_count",
        "lane_row_counts",
        "packets",
        "receipt_sha256",
    }
)
_MATERIALIZATION_CUSTODY_FIELDS: frozenset[str] = frozenset(
    {
        "schema_version",
        "evaluation_cycle_id",
        "source_evaluation_cycle_id",
        "amendment_reference",
        "source_custody_receipt_raw_sha256",
        "source_label_manifest_raw_sha256",
        "ordered_identity_commitment_sha256",
        "identity_union_commitment_sha256",
        "ordered_packet_commitment_sha256",
        "packet_count",
        "row_count",
        "lane_row_counts",
        "packet_size",
        "provider_artifacts_copied",
        "labels_copied",
        "responses_copied",
        "prompts_generated",
        "evidence_sidecars_generated",
        "text_free",
        "receipt_sha256",
    }
)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _materializer_module():
    from scripts.projects.open_model_data import phase3_cycle007_materializer as materializer

    return materializer


def _validate_cycle007_materialization(
    package_dir: Path,
    source_manifest_path: Path,
    *,
    fixture: bool,
    allowed_top_level_entries: Sequence[str] = (),
) -> tuple[
    list[list[Mapping[str, Any]]],
    list[bool],
    list[dict[str, Any]],
    dict[str, Any],
]:
    """Read and bind every public package byte before compiling any evidence.

    The materializer already validates these invariants while it creates a
    package.  The compiler must repeat the checks from the package on disk:
    compilation is a separate trust boundary, and a changed packet,
    manifest, or custody receipt must never become a self-consistent evidence
    bundle merely because a caller supplied matching metadata.
    """
    materializer = _materializer_module()
    manifest_path = package_dir / "manifest.json"
    manifest = materializer.strict_json(manifest_path, "source_binding_drift")
    contract.require(isinstance(manifest, Mapping), "source_binding_drift")
    materializer._verify_source_package_modes(package_dir, manifest, fixture)
    contract.require(
        all(
            isinstance(name, str)
            and bool(name)
            and Path(name).name == name
            for name in allowed_top_level_entries
        ),
        "manifest_binding_drift",
    )
    contract.require(
        {path.name for path in package_dir.iterdir()}
        == materializer.OUTPUT_TOP_LEVEL | set(allowed_top_level_entries),
        "manifest_binding_drift",
    )
    contract.require(set(manifest) == _MATERIALIZATION_MANIFEST_FIELDS, "manifest_binding_drift")
    contract.require(
        manifest.get("schema_version") == "phase3_cycle007_materialization_manifest_v1",
        "manifest_binding_drift",
    )
    contract.require(manifest.get("evaluation_cycle_id") == EVALUATION_CYCLE_ID, "manifest_binding_drift")
    contract.require(
        manifest.get("source_evaluation_cycle_id") == materializer.CYCLE005,
        "manifest_binding_drift",
    )
    contract.require(manifest.get("text_free") is True, "manifest_binding_drift")
    contract.require(_is_sha256(manifest.get("receipt_sha256")), "manifest_binding_drift")
    contract.require(
        manifest.get("receipt_sha256") == materializer._hash_receipt(manifest),
        "manifest_binding_drift",
    )

    records = manifest.get("packets")
    contract.require(isinstance(records, list) and bool(records), "manifest_binding_drift")
    packet_count = manifest.get("packet_count")
    row_count = manifest.get("row_count")
    contract.require(
        isinstance(packet_count, int)
        and not isinstance(packet_count, bool)
        and packet_count == len(records)
        and packet_count > 0,
        "manifest_binding_drift",
    )
    contract.require(
        isinstance(row_count, int) and not isinstance(row_count, bool) and row_count > 0,
        "manifest_binding_drift",
    )

    reported_lane_counts = manifest.get("lane_row_counts")
    contract.require(
        isinstance(reported_lane_counts, Mapping)
        and set(reported_lane_counts) == set(materializer.LANE_ORDER)
        and all(
            isinstance(reported_lane_counts[lane], int)
            and not isinstance(reported_lane_counts[lane], bool)
            and reported_lane_counts[lane] >= 0
            for lane in materializer.LANE_ORDER
        ),
        "manifest_binding_drift",
    )
    for field in (
        "custody_receipt_raw_sha256",
        "ordered_identity_commitment_sha256",
        "identity_union_commitment_sha256",
        "ordered_packet_commitment_sha256",
    ):
        contract.require(_is_sha256(manifest.get(field)), "manifest_binding_drift")

    custody_path = package_dir / "custody-receipt.json"
    custody_raw = materializer._read_regular(custody_path, "source_binding_drift")
    contract.require(
        manifest.get("custody_receipt_raw_sha256") == materializer.digest(custody_raw),
        "custody_binding_drift",
    )
    custody = materializer.strict_json(custody_path, "source_binding_drift")
    contract.require(isinstance(custody, Mapping), "source_binding_drift")
    contract.require(set(custody) == _MATERIALIZATION_CUSTODY_FIELDS, "custody_binding_drift")
    contract.require(
        custody.get("schema_version") == "phase3_cycle007_custody_receipt_v1"
        and custody.get("evaluation_cycle_id") == EVALUATION_CYCLE_ID
        and custody.get("source_evaluation_cycle_id") == materializer.CYCLE005
        and custody.get("text_free") is True,
        "custody_binding_drift",
    )
    contract.require(
        isinstance(custody.get("amendment_reference"), str) and bool(custody["amendment_reference"]),
        "custody_binding_drift",
    )
    for field in (
        "source_custody_receipt_raw_sha256",
        "source_label_manifest_raw_sha256",
        "ordered_identity_commitment_sha256",
        "identity_union_commitment_sha256",
        "ordered_packet_commitment_sha256",
        "receipt_sha256",
    ):
        contract.require(_is_sha256(custody.get(field)), "custody_binding_drift")
    contract.require(
        custody.get("receipt_sha256") == materializer._hash_receipt(custody),
        "custody_binding_drift",
    )
    contract.require(custody.get("packet_size") == materializer.PACKET_SIZE, "custody_binding_drift")
    contract.require(
        all(custody.get(field) is False for field in (
            "provider_artifacts_copied",
            "labels_copied",
            "responses_copied",
            "prompts_generated",
            "evidence_sidecars_generated",
        )),
        "custody_binding_drift",
    )

    source_manifest_raw = materializer._read_regular(source_manifest_path, "source_binding_drift")
    expected_source_manifest_sha256 = (
        materializer.digest(source_manifest_raw)
        if fixture
        else materializer.SOURCE_MANIFEST_SHA256
    )
    contract.require(
        materializer.digest(source_manifest_raw) == expected_source_manifest_sha256
        and custody.get("source_label_manifest_raw_sha256") == expected_source_manifest_sha256,
        "source_binding_drift",
    )
    source_manifest = materializer.strict_json(source_manifest_path, "source_binding_drift")
    contract.require(isinstance(source_manifest, Mapping), "source_binding_drift")
    contract.require(
        source_manifest.get("schema_version") == "phase3_cycle005_label_manifest_v1"
        and source_manifest.get("evaluation_cycle_id") == materializer.CYCLE005
        and source_manifest.get("receipt_sha256") == materializer._hash_receipt(source_manifest),
        "source_binding_drift",
    )
    source_records = materializer._expected_order(source_manifest, fixture)
    source_records_by_key = {
        (record["lane"], record["packet_index"]): record for record in source_records
    }
    if not fixture:
        contract.require(
            custody.get("source_custody_receipt_raw_sha256") == materializer.SOURCE_CUSTODY_SHA256
            and custody.get("source_label_manifest_raw_sha256") == materializer.SOURCE_MANIFEST_SHA256
            and custody.get("amendment_reference")
            == "batch_state/phase3-cycle007-source-grounded-amendment-v1.md",
            "custody_binding_drift",
        )

    packets: list[list[Mapping[str, Any]]] = []
    residual_flags: list[bool] = []
    packet_bindings: list[dict[str, Any]] = []
    seen_identities: set[tuple[str, str]] = set()
    ordered_identity_stream: list[list[Any]] = []
    lane_row_counts = {lane: 0 for lane in materializer.LANE_ORDER}
    next_index = {lane: 1 for lane in materializer.LANE_ORDER}
    last_lane_position = -1

    for record in records:
        contract.require(
            isinstance(record, Mapping) and set(record) == _MATERIALIZATION_PACKET_RECORD_FIELDS,
            "packet_order_failure",
        )
        lane = record.get("lane")
        packet_index = record.get("packet_index")
        basename = record.get("canonical_basename")
        contract.require(lane in materializer.LANE_ORDER, "packet_order_failure")
        contract.require(
            isinstance(packet_index, int) and not isinstance(packet_index, bool) and packet_index >= 1,
            "packet_order_failure",
        )
        lane_position = materializer.LANE_ORDER.index(lane)
        contract.require(lane_position >= last_lane_position, "packet_order_failure")
        expected_index = next_index[lane]
        contract.require(packet_index == expected_index, "packet_order_failure")
        if lane_position > last_lane_position:
            contract.require(packet_index == 1, "packet_order_failure")
        last_lane_position = lane_position
        next_index[lane] += 1

        contract.require(
            isinstance(basename, str)
            and Path(basename).name == basename
            and basename == f"packet-{packet_index:04d}.json",
            "packet_binding_drift",
        )
        row_count_for_packet = record.get("row_count")
        contract.require(
            isinstance(row_count_for_packet, int)
            and not isinstance(row_count_for_packet, bool)
            and 1 <= row_count_for_packet <= materializer.PACKET_SIZE,
            "packet_binding_drift",
        )
        if not fixture:
            expected_row_count = (
                9
                if lane == _RESIDUAL_LANE_NAME and packet_index == materializer.REAL_PACKET_COUNTS[lane]
                else materializer.PACKET_SIZE
            )
            contract.require(row_count_for_packet == expected_row_count, "packet_binding_drift")
        raw_sha256 = record.get("raw_sha256")
        identity_set_sha256 = record.get("packet_identity_set_sha256")
        contract.require(_is_sha256(raw_sha256) and _is_sha256(identity_set_sha256), "packet_binding_drift")

        packet_path = package_dir / lane / basename
        raw = materializer._read_regular(packet_path, "packet_binding_drift")
        contract.require(materializer.digest(raw) == raw_sha256, "packet_binding_drift")
        packet = materializer.strict_json(packet_path, "packet_binding_drift")
        contract.require(isinstance(packet, Mapping), "packet_binding_drift")
        contract.require(set(packet) == _MATERIALIZATION_PACKET_FIELDS, "packet_binding_drift")
        contract.require(
            packet.get("schema_version") == "phase3_cycle007_evidence_packet_v1"
            and packet.get("evaluation_cycle_id") == EVALUATION_CYCLE_ID
            and packet.get("lane") == lane
            and packet.get("packet_index") == packet_index
            and packet.get("row_count") == row_count_for_packet,
            "packet_binding_drift",
        )
        rows = packet.get("rows")
        contract.require(
            isinstance(rows, list) and len(rows) == row_count_for_packet,
            "packet_binding_drift",
        )

        source_record = source_records_by_key.get((lane, packet_index))
        contract.require(
            isinstance(source_record, Mapping)
            and source_record.get("canonical_basename") == basename
            and source_record.get("row_count") == row_count_for_packet
            and source_record.get("packet_identity_set_sha256") == identity_set_sha256,
            "source_binding_drift",
        )
        reconstructed_source_packet = copy.deepcopy(packet)
        reconstructed_source_packet["schema_version"] = "phase3_cycle005_private_packet_v1"
        reconstructed_source_packet["evaluation_cycle_id"] = materializer.CYCLE005
        for reconstructed_row in reconstructed_source_packet["rows"]:
            if "evaluation_cycle_id" in reconstructed_row:
                reconstructed_row["evaluation_cycle_id"] = materializer.CYCLE005
        source_digest_candidates = {
            materializer.digest(materializer.canonical(reconstructed_source_packet))
        }
        legacy_source_packet = copy.deepcopy(reconstructed_source_packet)
        for legacy_row in legacy_source_packet["rows"]:
            legacy_row.pop("source_text_sha256", None)
        source_digest_candidates.add(materializer.digest(materializer.canonical(legacy_source_packet)))
        contract.require(
            source_record.get("raw_sha256") in source_digest_candidates,
            "source_content_binding_drift",
        )

        packet_identities: list[tuple[str, str]] = []
        for row_index, row in enumerate(rows):
            contract.require(isinstance(row, Mapping), "packet_binding_drift")
            contract.require(not (materializer.FORBIDDEN_ROW_KEYS & set(row)), "label_leak_detected")
            if "evaluation_cycle_id" in row:
                contract.require(row.get("evaluation_cycle_id") == EVALUATION_CYCLE_ID, "packet_binding_drift")
            source_text = row.get("source_text")
            source_text_sha256 = row.get("source_text_sha256")
            contract.require(
                isinstance(source_text, str)
                and _is_sha256(source_text_sha256)
                and contract.sha256_text(source_text) == source_text_sha256,
                "packet_binding_drift",
            )
            unit_id = row.get("unit_id")
            unit_sha256 = row.get("unit_sha256")
            contract.require(
                isinstance(unit_id, str)
                and bool(unit_id)
                and _is_sha256(unit_sha256),
                "packet_binding_drift",
            )
            identity = (unit_id, unit_sha256)
            contract.require(identity not in packet_identities, "identity_uniqueness_failure")
            contract.require(identity not in seen_identities, "identity_uniqueness_failure")
            packet_identities.append(identity)
            seen_identities.add(identity)
            ordered_identity_stream.append([lane, packet_index, row_index, unit_id, unit_sha256])

        recomputed_packet_identity_set = materializer.digest(materializer.canonical(sorted(packet_identities)))
        contract.require(
            packet.get("packet_identity_set_sha256") == recomputed_packet_identity_set
            and packet.get("packet_identity_set_sha256") == identity_set_sha256,
            "packet_binding_drift",
        )
        packets.append(list(rows))
        residual_flags.append(lane == _RESIDUAL_LANE_NAME)
        packet_bindings.append(
            {
                "canonical_basename": basename,
                "raw_sha256": raw_sha256,
                "packet_identity_set_sha256": identity_set_sha256,
            }
        )
        lane_row_counts[lane] += row_count_for_packet

    contract.require(all(next_index[lane] > 1 for lane in materializer.LANE_ORDER), "packet_order_failure")
    if not fixture:
        contract.require(
            {lane: next_index[lane] - 1 for lane in materializer.LANE_ORDER}
            == materializer.REAL_PACKET_COUNTS,
            "packet_order_failure",
        )
        contract.require(
            manifest.get("packet_count") == REAL_PACKET_COUNT and manifest.get("row_count") == REAL_ROW_COUNT,
            "manifest_binding_drift",
        )
        contract.require(lane_row_counts == materializer.REAL_ROW_COUNTS, "manifest_binding_drift")
    recomputed_row_count = sum(lane_row_counts.values())
    contract.require(recomputed_row_count == manifest.get("row_count"), "manifest_binding_drift")
    contract.require(dict(reported_lane_counts) == lane_row_counts, "manifest_binding_drift")
    contract.require(len(packets) == manifest.get("packet_count"), "manifest_binding_drift")

    ordered_identity_commitment = materializer.digest(materializer.canonical(ordered_identity_stream))
    identity_union_commitment = materializer.digest(materializer.canonical(sorted(seen_identities)))
    ordered_packet_commitment = materializer.digest(materializer.canonical(records))
    contract.require(
        manifest.get("ordered_identity_commitment_sha256") == ordered_identity_commitment
        and manifest.get("identity_union_commitment_sha256") == identity_union_commitment
        and manifest.get("ordered_packet_commitment_sha256") == ordered_packet_commitment,
        "manifest_binding_drift",
    )
    if not fixture:
        contract.require(
            ordered_identity_commitment == materializer.ORDERED_IDENTITY_COMMITMENT_SHA256,
            "ordered_identity_commitment_failure",
        )

    for field in (
        "ordered_identity_commitment_sha256",
        "identity_union_commitment_sha256",
        "ordered_packet_commitment_sha256",
        "packet_count",
        "row_count",
        "lane_row_counts",
    ):
        contract.require(custody.get(field) == manifest.get(field), "custody_binding_drift")

    source_package_binding = {
        "source_evaluation_cycle_id": manifest["source_evaluation_cycle_id"],
        "custody_receipt_raw_sha256": manifest["custody_receipt_raw_sha256"],
        "materialization_manifest_sha256": manifest["receipt_sha256"],
        "ordered_identity_commitment_sha256": manifest["ordered_identity_commitment_sha256"],
        "identity_union_commitment_sha256": manifest["identity_union_commitment_sha256"],
        "ordered_packet_commitment_sha256": manifest["ordered_packet_commitment_sha256"],
        "packet_count": manifest["packet_count"],
        "row_count": manifest["row_count"],
    }
    return packets, residual_flags, packet_bindings, source_package_binding


def compile_cycle007_package(
    package_dir: Path,
    source_manifest_path: Path,
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
    if not fixture and (
        not isinstance(client, LocalMcpSourcesClient)
        or not isinstance(client._transport, RealMcpToolTransport)
    ):
        raise contract.EvidenceContractError(
            "real package compile requires the reviewed streamable-HTTP MCP transport"
        )

    allowed_top_level_entries: tuple[str, ...] = ()
    if not fixture:
        from scripts.projects.open_model_data import phase3_cycle007_evidence_compile_throughput as throughput

        resume_root = throughput.resume_root_for(output_dir)
        contract.require(resume_root.parent == package_dir, "manifest_binding_drift")
        if os.path.lexists(resume_root):
            allowed_top_level_entries = (resume_root.name,)

    packets, residual_flags, packet_bindings, source_package_binding = _validate_cycle007_materialization(
        package_dir,
        source_manifest_path,
        fixture=fixture,
        allowed_top_level_entries=allowed_top_level_entries,
    )

    if fixture:
        return compile_sidecar_bundle(
            packets,
            client,
            output_dir,
            residual_lane_packets=residual_flags,
            packet_bindings=packet_bindings,
            source_package_binding=source_package_binding,
        )
    return compile_sidecar_bundle_resumable(
        packets,
        client,
        output_dir,
        residual_lane_packets=residual_flags,
        packet_bindings=packet_bindings,
        source_package_binding=source_package_binding,
    )
