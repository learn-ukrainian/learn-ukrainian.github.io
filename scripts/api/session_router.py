"""Session API router — serves a condensed view of the current session state.

Mounted at /api/session in main.py.

Endpoints:
    GET /api/session/current              Markdown summary of current session
    GET /api/session/current?format=json  {hash, bytes, sections, markdown}

Why this exists (GH #1309): every agent cold-start was reading
``docs/session-state/current.md`` directly (plus a grep for the latest
dated handoff file, plus a grep for open decisions, etc.). Consolidating
into one endpoint lets agents check a single hash on
``/api/state/manifest`` and only refetch when something changed.

The payload is kept lean on purpose — if an agent needs the full
session state, the current.md file path is advertised in the JSON
response so the agent can fall back to a direct read. The endpoint is
designed for "what do I need to know RIGHT NOW to start working", not
for forensic archaeology.
"""

from __future__ import annotations

import hashlib
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from .config import PROJECT_ROOT
from .rules_router import _matches_etag  # shared ETag parser

router = APIRouter(tags=["session"])

SESSION_CURRENT_PATH = "docs/session-state/current.md"

# How many recent handoff files to include in the consolidated summary.
# Small on purpose — the manifest is the jump table; this endpoint is
# the "right now" view. If an agent needs more, they can read directly.
_RECENT_HANDOFFS_N = 3


def _read_current_session() -> str:
    path = PROJECT_ROOT / SESSION_CURRENT_PATH
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Session state file not found at {SESSION_CURRENT_PATH}. "
                "Create it with the current task's context."
            ),
        )
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read {SESSION_CURRENT_PATH}: {exc}",
        ) from exc


def _recent_handoff_paths() -> list[str]:
    """Return the N most-recent ``docs/session-state/*.md`` by filename.

    The convention is ``YYYY-MM-DD-<topic>.md``, which lexicographically
    sorts newest-last. We exclude ``current.md`` because it's returned
    as the main payload.
    """
    session_dir = PROJECT_ROOT / "docs" / "session-state"
    if not session_dir.is_dir():
        return []
    all_md = sorted(
        p for p in session_dir.glob("*.md")
        if p.name != "current.md"
    )
    latest = all_md[-_RECENT_HANDOFFS_N:] if all_md else []
    latest.reverse()  # newest first
    return [str(p.relative_to(PROJECT_ROOT)) for p in latest]


def _assemble_session() -> tuple[str, dict, str]:
    """Return (markdown, sections_dict, sha256_hex) for the session view."""
    current_md = _read_current_session().rstrip() + "\n"
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
        "current": SESSION_CURRENT_PATH,
        "recent_handoffs": handoffs,
    }
    return markdown, sections, digest


@router.get("/current")
def session_current(
    request: Request,
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
    markdown, sections, digest = _assemble_session()
    etag = f'"{digest}"'

    if _matches_etag(request.headers.get("If-None-Match"), digest):
        return Response(
            status_code=304,
            headers={"ETag": etag, "X-Session-Hash": digest},
        )

    if format == "json":
        return JSONResponse(
            content={
                "hash": digest,
                "bytes": len(markdown.encode("utf-8")),
                "sections": sections,
                "markdown": markdown,
            },
            headers={"ETag": etag, "X-Session-Hash": digest},
        )

    return PlainTextResponse(
        content=markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"ETag": etag, "X-Session-Hash": digest},
    )


def session_hash() -> str:
    """Hash-only helper for ``/api/state/manifest``. Returns empty on error."""
    try:
        _, _, digest = _assemble_session()
    except HTTPException:
        return ""
    return digest
