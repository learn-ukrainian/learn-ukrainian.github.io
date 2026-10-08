"""Rules API router — serves the condensed agent rule text.

Mounted at /api/rules in main.py.

Endpoints:
    GET /api/rules                  Default: binding core Markdown
    GET /api/rules?format=markdown  Binding core Markdown string
    GET /api/rules?format=json      {hash, bytes, sources[], markdown}
    GET /api/rules?scope=core       The rules core every seat loads
    GET /api/rules?scope=content    The core plus the curriculum addendum
    GET /api/rules?scope=full       Complete reference archive (explicit opt-in)
    GET /api/rules?scope=task:NAME  The reference sources task-scoped-reading.md selects

Without ``scope`` the binding core is served, identically to ``scope=core``.
The legacy full reference retains its sources, order, bytes and hash under
``scope=full``. A core/content/task response carries its own hash — sha256 over
``scope=<scope>\n`` plus the Markdown — so its ETag and cache identity never
collide with the full bundle or another scope. Scope sources and assembly come
from ``scripts/lib/rules_core.py``, the same loader launchers and workers use
offline.

Why this exists (GH #1309): every agent cold-start was reading three
rule files individually (``critical-rules.md`` +
``non-negotiable-rules.md`` + ``workflow.md``) plus ``CLAUDE.md`` plus
``memory/MEMORY.md``. That is 5+ tool calls / 15+ KB on every boot.
Consolidating them behind one endpoint lets agents check a single hash
on ``/api/state/manifest`` and only refetch when rules actually change.

Source of truth is the Claude extensions rule directory — `.claude/rules/`,
`.agent/rules/`, and `.gemini/rules/` are deployed copies
(``npm run agents:deploy``). We read the source so a fresh checkout
(or a worktree that hasn't deployed) still gets the current rules.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from scripts.lib import rules_core

from .monitor_context import MonitorContext, get_ctx
from .telemetry.response import (
    add_json_telemetry,
    append_telemetry_footer,
    session_id_from_request,
    telemetry_footer_enabled,
)

router = APIRouter(tags=["rules"])


def _matches_etag(if_none_match: str | None, digest: str) -> bool:
    """True if the client already has the bytes addressed by ``digest``.

    Honours both weak and strong ETags. The manifest exposes the raw
    hex digest so the client is permitted to send ``"<digest>"`` or
    ``W/"<digest>"``; both match. A literal ``*`` always matches.
    """
    if not if_none_match:
        return False
    tokens = [tok.strip() for tok in if_none_match.split(",")]
    for tok in tokens:
        if tok == "*":
            return True
        # Strip optional W/ prefix then the surrounding quotes.
        if tok.startswith("W/"):
            tok = tok[2:]
        tok = tok.strip('"')
        if tok == digest:
            return True
    return False


# Full-reference archive only; cold-start seats receive rules_core.CORE_REL.
# Order matters: operator contract first, then critical rules, non-negotiables,
# the mandatory workflow and remaining references. Changing
# this order is a user-visible contract change — agents that cache the
# concatenated blob by hash will see a new hash and refetch.
#
# Fleet doctrine + living role scorecard (#5529 / #5474) ship AFTER
# model-assignment so machine routing remains earlier in the blob while
# explicit full-reference readers still receive the scoreboard.
RULE_SOURCES: tuple[str, ...] = (
    "agents_extensions/shared/rules/operator-expectations.md",
    "agents_extensions/shared/rules/critical-rules.md",
    "agents_extensions/shared/rules/non-negotiable-rules.md",
    "agents_extensions/shared/rules/workflow.md",
    # Fleet-comms mid-cutover coordination (standalone TUI/UI SSOT; #5512 / #4707).
    "agents_extensions/shared/rules/fleet-comms-coordination.md",
    "agents_extensions/shared/rules/delegate-must-use-worktree.md",
    "agents_extensions/shared/rules/cli-help-standard.md",
    "agents_extensions/shared/rules/model-assignment.md",
    # Driver routing card + breadth floor (operator GO 2026-08-06).
    "agents_extensions/shared/rules/fleet-driver-routing.md",
    "docs/best-practices/fleet-shared-doctrine.md",
    "docs/best-practices/fleet-role-scorecard.md",
)

# Separator between files. Explicit so the concatenation is stable
# across machines (no locale-dependent newline handling) and so the
# assembled Markdown still renders cleanly.
_FILE_SEP = "\n\n---\n\n"


def _read_rule_files(project_root: Path) -> tuple[list[str], list[str]]:
    """Return (present_paths, file_contents) for every file that exists."""
    root = project_root
    present_paths: list[str] = []
    contents: list[str] = []
    for rel in RULE_SOURCES:
        path = root / rel
        if not path.exists() or not path.is_file():
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except OSError:
            # Unreadable file — skip rather than 500. The manifest hash
            # will change if the set of readable files changes, so
            # agents will notice the degraded state.
            continue
        present_paths.append(rel)
        contents.append(body.rstrip() + "\n")
    return present_paths, contents


def _assemble_rules(project_root: Path) -> tuple[str, list[str], str]:
    """Return (markdown, sources, sha256_hex) for the concatenated rules.

    Raises ``HTTPException(500)`` if not a single source file could be
    read — something is badly wrong with the checkout in that case.
    """
    sources, parts = _read_rule_files(project_root)
    if not parts:
        raise HTTPException(
            status_code=500,
            detail=(f"No rule sources readable under {', '.join(RULE_SOURCES)}. Is the repo checked out?"),
        )
    markdown = _FILE_SEP.join(parts).rstrip() + "\n"
    digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    return markdown, sources, digest


def scope_digest(scope: str, markdown: str) -> str:
    """Hash of a scoped response; the scope name is part of its identity."""
    return hashlib.sha256(f"scope={scope}\n{markdown}".encode()).hexdigest()


def _assemble_scope(project_root: Path, scope: str) -> tuple[str, list[str], str]:
    """Return (markdown, sources, digest) for a seat, task or full reference."""
    if scope == "full":
        return _assemble_rules(project_root)
    try:
        sources = list(rules_core.scope_sources(scope))
        markdown = rules_core.assemble(tuple(sources), project_root)
    except rules_core.RulesCoreMissing as exc:
        raise HTTPException(status_code=503, detail=f"{exc}; scope {scope!r} is unavailable in this checkout.") from exc
    except rules_core.RulesCoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return markdown, sources, scope_digest(scope, markdown)


@router.get("")
def get_rules(
    request: Request,
    format: Literal["markdown", "json"] = Query(
        "markdown",
        description="'markdown' returns the raw Markdown blob; 'json' wraps it with hash + metadata.",
    ),
    scope: str | None = Query(
        None,
        description="Omit for the binding core; 'content' adds curriculum rules; 'task:<name>' or 'full' selects references.",
    ),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Return the condensed agent rule text.

    ``format=markdown`` (default) returns the raw blob as
    ``text/markdown`` for direct drop-in into a system prompt.
    ``format=json`` returns ``{hash, bytes, sources, markdown}`` so an
    agent SDK can skip the payload entirely when the manifest hash
    matches its last-seen value.

    Supports ``If-None-Match: "<hash>"``. If the hash matches what the
    endpoint would return, responds ``304 Not Modified`` with an empty
    body — the client should reuse its cache. This makes the SDK's
    cache-hit path one small HTTP round-trip with zero payload.
    """
    effective_scope = "core" if scope is None else scope
    markdown, sources, digest = _assemble_scope(ctx.roots.project_root, effective_scope)
    etag = f'"{digest}"'
    session_id = session_id_from_request(request)
    scope_headers = {"X-Rules-Scope": effective_scope}

    if not telemetry_footer_enabled() and _matches_etag(request.headers.get("If-None-Match"), digest):
        return Response(
            status_code=304,
            headers={"ETag": etag, "X-Rules-Hash": digest, **scope_headers},
        )

    if format == "json":
        return _rules_json_response(markdown, sources, digest, etag, session_id, scope=effective_scope)

    # Raw Markdown path. FastAPI's default str response is
    # application/json, which would JSON-encode the whole blob — wrong
    # for an agent trying to drop it straight into a prompt.
    return PlainTextResponse(
        content=append_telemetry_footer(markdown, session_id),
        media_type="text/markdown; charset=utf-8",
        headers={**_cache_headers(etag, digest, "X-Rules-Hash"), **scope_headers},
    )


def _rules_json_response(
    markdown: str,
    sources,
    digest: str,
    etag: str,
    session_id: str | None,
    *,
    scope: str | None = None,
):
    payload = {
        "hash": digest,
        "bytes": len(markdown.encode("utf-8")),
        "sources": sources,
        "markdown": markdown,
    }
    headers = _cache_headers(etag, digest, "X-Rules-Hash")
    if scope is not None:
        payload["scope"] = scope
        headers["X-Rules-Scope"] = scope
    return JSONResponse(content=add_json_telemetry(payload, session_id=session_id), headers=headers)


def _cache_headers(etag: str, digest: str, hash_header: str) -> dict[str, str]:
    headers = {hash_header: digest}
    if not telemetry_footer_enabled():
        headers["ETag"] = etag
    return headers


def rules_hash(*, project_root: Path, scope: str | None = None) -> str:
    """Hash-only helper used by ``/api/state/manifest``.

    Defaults to the binding core, matching the unscoped endpoint.
    Returns empty string on unreadable state so the manifest
    stays 200-OK even if rules are momentarily missing.
    """
    try:
        _, _, digest = _assemble_scope(project_root, "core" if scope is None else scope)
    except HTTPException:
        return ""
    return digest


def rules_source_paths(*, project_root: Path, scope: str = "core") -> list[str]:
    """Resolve the set of rule sources that actually exist right now.

    Defaults to the binding core. Full and task references are explicit.
    """
    sources = RULE_SOURCES if scope == "full" else rules_core.scope_sources(scope)
    return [rel for rel in sources if rules_core.source_path(rel, project_root).is_file()]
