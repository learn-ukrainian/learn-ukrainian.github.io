"""Session API router — serves a condensed view of the current session state.

Mounted at /api/session in main.py.

Endpoints:
    GET /api/session/current              Markdown summary of orchestrator session
    GET /api/session/current?agent=codex  Markdown summary of Codex session
    GET /api/session/current?format=json  {hash, bytes, sections, markdown}

Why this exists (GH #1309): every agent cold-start was reading
``docs/session-state/current.md`` directly (plus a grep for the latest
dated handoff file, plus a grep for open decisions, etc.). Consolidating
into one endpoint lets agents check a single hash on
``/api/state/manifest`` and only refetch when something changed.

The payload is kept lean on purpose — if an agent needs the full
session state, the selected mapped agent handoff path is advertised
in the JSON response so the agent can fall back to a direct read. The
endpoint is designed for "what do I need to know RIGHT NOW to start
working", not for forensic archaeology.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from .config import PROJECT_ROOT
from .rules_router import _matches_etag  # shared ETag parser
from .telemetry.response import (
    add_json_telemetry,
    append_telemetry_footer,
    telemetry_footer_enabled,
)

router = APIRouter(tags=["session"])

SESSION_ROUTER_PATH = "docs/session-state/current.md"
ORCHESTRATOR_HANDOFF_PATH = "docs/session-state/codex-orchestrator-handoff.md"
LEGACY_ORCHESTRATOR_HANDOFF_PATH = "docs/session-state/current.orchestrator.md"
DEFAULT_SESSION_AGENT = "orchestrator"
AGENT_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")

# How many recent handoff files to include in the consolidated summary.
# Small on purpose — the manifest is the jump table; this endpoint is
# the "right now" view. If an agent needs more, they can read directly.
_RECENT_HANDOFFS_N = 3


def _safe_project_path(rel_path: str) -> Path:
    """Resolve ``rel_path`` under ``PROJECT_ROOT`` and reject any escape.

    The ``agent`` query param is already regex-validated and Agent-Handoff
    paths are filtered for ``..``/absolute in ``_parse_agent_handoffs``. This
    is an explicit second containment barrier: resolve the candidate and
    confirm it stays inside the project root. Defense-in-depth against path
    traversal (CWE-22).

    The containment guard normalizes with ``os.path.realpath`` and checks a
    ``startswith(root + os.sep)`` prefix. This specific ``os.path`` idiom is
    the form CodeQL's ``py/path-injection`` query recognizes as a sanitizing
    barrier. Earlier attempts did NOT clear the alerts: ``root in
    candidate.parents`` (#2706) and the pathlib ``str(Path.resolve())
    .startswith(...)`` form (#2727) are both correct at runtime but invisible
    to the static analyzer (confirmed: the post-#2727 scan still flagged this
    function). The trailing ``os.sep`` prevents a sibling-prefix bypass
    (``/rootX`` is not inside ``/root``); ``candidate == root`` is allowed.
    """
    root = os.path.realpath(PROJECT_ROOT)
    candidate = os.path.realpath(os.path.join(root, rel_path))
    if candidate != root and not candidate.startswith(root + os.sep):
        raise HTTPException(
            status_code=400,
            detail="Resolved session path escapes the project root.",
        )
    return Path(candidate)


def _read_session_file(session_path: str) -> str:
    path = _safe_project_path(session_path)
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Session state file not found at {session_path}. "
                "Create it with the current task's context."
            ),
        )
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read {session_path}: {exc}",
        ) from exc


def _normalize_agent(agent: str | None) -> str:
    normalized = (agent or DEFAULT_SESSION_AGENT).strip().lower()
    if normalized == "router":
        return normalized
    if not AGENT_NAME_RE.fullmatch(normalized):
        raise HTTPException(
            status_code=400,
            detail="agent names must match [a-z][a-z0-9-]*",
        )
    return normalized


def _parse_agent_handoffs(router_markdown: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    in_mapping = False
    for raw_line in router_markdown.splitlines():
        line = raw_line.strip()
        if line == "Agent-Handoff:":
            in_mapping = True
            continue
        if not in_mapping:
            continue
        if not line:
            break
        if line.startswith("- "):
            line = line[2:].strip()
        if ":" not in line:
            continue
        agent, path = [part.strip() for part in line.split(":", 1)]
        if not AGENT_NAME_RE.fullmatch(agent):
            continue
        rel_path = Path(path)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            continue
        mapping[agent] = rel_path.as_posix()
    return mapping


def _resolve_session_path(agent: str) -> str:
    if agent == "router":
        return SESSION_ROUTER_PATH

    router_path = PROJECT_ROOT / SESSION_ROUTER_PATH
    agent_default = (
        # If the small compatibility router is absent, the API should still
        # serve Codex UI the durable orchestrator state directly. Thread
        # bootstrap prompts separately name the current.orchestrator.md pointer
        # because that is the stable local file agents should read first.
        ORCHESTRATOR_HANDOFF_PATH
        if agent == "codex"
        else f"docs/session-state/current.{agent}.md"
    )
    if not router_path.is_file():
        return agent_default

    router_markdown = router_path.read_text(encoding="utf-8", errors="replace")
    handoffs = _parse_agent_handoffs(router_markdown)
    if agent in handoffs:
        handoff_path = handoffs[agent]
        if (
            agent in {DEFAULT_SESSION_AGENT, "codex"}
            and handoff_path == LEGACY_ORCHESTRATOR_HANDOFF_PATH
            and (PROJECT_ROOT / ORCHESTRATOR_HANDOFF_PATH).is_file()
        ):
            return ORCHESTRATOR_HANDOFF_PATH
        return handoff_path

    # Backward compatibility for older current.md files that still contained
    # the detailed orchestrator handoff rather than an Agent-Handoff router.
    if agent in {DEFAULT_SESSION_AGENT, "codex"} and not handoffs:
        return SESSION_ROUTER_PATH
    return agent_default


def _recent_handoff_paths() -> list[str]:
    """Return the N most-recent ``docs/session-state/*.{md,html}`` by filename.

    The convention is ``YYYY-MM-DD-<topic>.{md,html}``, which lexicographically
    sorts newest-last. We exclude ``current.md`` because it's returned
    as the main payload. Both extensions are indexed because the #M-2 rule
    (2026-05-09) shifted handoff bodies to HTML for ai → human consumption,
    while keeping the same filename convention for machine discovery.
    """
    session_dir = PROJECT_ROOT / "docs" / "session-state"
    if not session_dir.is_dir():
        return []
    excluded_names = {"current.md", Path(ORCHESTRATOR_HANDOFF_PATH).name}
    candidates: list[Path] = []
    for pattern in ("*.md", "*.html"):
        candidates.extend(session_dir.glob(pattern))
    all_handoffs = sorted(
        p
        for p in candidates
        if p.name not in excluded_names and not (p.name.startswith("current.") and p.suffix == ".md")
    )
    latest = all_handoffs[-_RECENT_HANDOFFS_N:] if all_handoffs else []
    latest.reverse()  # newest first
    return [str(p.relative_to(PROJECT_ROOT)) for p in latest]


def _assemble_session(agent: str = DEFAULT_SESSION_AGENT) -> tuple[str, dict, str]:
    """Return (markdown, sections_dict, sha256_hex) for the session view."""
    normalized_agent = _normalize_agent(agent)
    current_path = _resolve_session_path(normalized_agent)
    current_md = _read_session_file(current_path).rstrip() + "\n"
    handoffs = _recent_handoff_paths()

    if handoffs:
        handoff_block = "\n".join(
            f"- `{rel}`" for rel in handoffs
        )
        markdown = (
            current_md
            + "\n---\n\n"
            + "## Recent session-state files (for deeper context)\n\n"
            + handoff_block
            + "\n"
        )
    else:
        markdown = current_md

    digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    sections = {
        "agent": normalized_agent,
        "current": current_path,
        "router": SESSION_ROUTER_PATH,
        "recent_handoffs": handoffs,
    }
    return markdown, sections, digest


@router.get("/current")
def session_current(
    request: Request,
    agent: str = Query(
        DEFAULT_SESSION_AGENT,
        description="Agent-specific handoff to serve; use 'router' for docs/session-state/current.md.",
    ),
    format: Literal["markdown", "json"] = Query(
        "markdown",
        description="'markdown' returns text/markdown; 'json' wraps with hash + section map.",
    ),
):
    """Condensed session summary for agent cold-start.

    Supports ``If-None-Match: "<hash>"`` — a matching hash responds
    ``304 Not Modified`` with no body, so an SDK with a valid local
    cache pays only the TCP round-trip.
    """
    markdown, sections, digest = _assemble_session(agent)
    etag = f'"{digest}"'

    if not telemetry_footer_enabled() and _matches_etag(request.headers.get("If-None-Match"), digest):
        return Response(
            status_code=304,
            headers={"ETag": etag, "X-Session-Hash": digest},
        )

    if format == "json":
        return JSONResponse(
            content=add_json_telemetry({
                "hash": digest,
                "bytes": len(markdown.encode("utf-8")),
                "sections": sections,
                "markdown": markdown,
            }),
            headers=_cache_headers(etag, digest),
        )

    return PlainTextResponse(
        content=append_telemetry_footer(markdown),
        media_type="text/markdown; charset=utf-8",
        headers=_cache_headers(etag, digest),
    )


def _cache_headers(etag: str, digest: str) -> dict[str, str]:
    headers = {"X-Session-Hash": digest}
    if not telemetry_footer_enabled():
        headers["ETag"] = etag
    return headers


def session_hash(agent: str = DEFAULT_SESSION_AGENT) -> str:
    """Hash-only helper for ``/api/state/manifest``. Returns empty on error."""
    try:
        _, _, digest = _assemble_session(agent)
    except HTTPException:
        return ""
    return digest
