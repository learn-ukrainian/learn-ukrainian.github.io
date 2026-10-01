"""Knowledge API router — ADR-011 P2/P3 bounded research discovery.

Mounted at ``/api/knowledge`` in ``main.py``. The discovery endpoints are gated
behind the default-off ``research_registry`` kill switch (``scripts/research/
registry.py``); the P4 monitor is deliberately **ungated** so governance survives a
serving disable:

    GET /api/knowledge/manifest             Filtered, task-scoped pointer list with
                                            its own strong ETag (no digest bodies).
                                            Pure AND matcher over role/task_family/
                                            track/owned_path. [gated]
    GET /api/knowledge/cold-start           Role-only pointer list from the opt-in
                                            ``cold_start_roles`` announce list —
                                            NEVER the AND matcher (P3). [gated]
    GET /api/knowledge/monitor              ADR-011 P4 observability: lifecycle rot,
                                            adoption, distinct-task consumption, dead
                                            consumers. Deterministic, no ETag. [ungated]
    GET /api/knowledge/record/{record_id}   One compact digest body as text/markdown
                                            with an honest per-record ETag. [gated]
    GET /api/knowledge/find?q=&limit=&family=
                                            Document and data catalogue locator
                                            (#9412): one query over the catalogue,
                                            tracked names and readable tracked text.
                                            [ungated; never behind the kill switch]

The registry endpoints are deterministic and fail-open: disabled or a failed registry
load yields an empty/disabled projection (or a degraded monitor section), never a 500.
``/find`` shares only the URL prefix with the registry, not its schema or kill switch:
it reports an invalid catalogue or a cut-off search inside its result, a bad request as
a typed 422 and an unreadable repository as a typed 503.
The runtime/observability layers do all the loading, matching, projection, and
budgeting; this module only maps them to HTTP, including the shared ``_matches_etag``
304 semantics.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from scripts.docs import find as docs_find
from scripts.research import consumption, observability
from scripts.research import registry as reg

from .monitor_context import MonitorContext, get_ctx
from .rules_router import _matches_etag

router = APIRouter(tags=["knowledge"])

_JSON_MEDIA = "application/json"
_MARKDOWN_MEDIA = "text/markdown; charset=utf-8"
_NOT_FOUND = "Not Found"


def _json_response(body: bytes, etag_hex: str | None = None, status_code: int = 200) -> Response:
    headers = {"ETag": f'"{etag_hex}"'} if etag_hex is not None else None
    return Response(content=body, media_type=_JSON_MEDIA, status_code=status_code, headers=headers)


@router.get("/manifest")
def knowledge_manifest(
    request: Request,
    role: str | None = Query(default=None, max_length=reg.MAX_QUERY_VALUE_LEN),
    task_family: str | None = Query(default=None, max_length=reg.MAX_QUERY_VALUE_LEN),
    track: str | None = Query(default=None, max_length=reg.MAX_QUERY_VALUE_LEN),
    owned_path: list[str] = Query(default=[]),
    monitor_ctx: MonitorContext = Depends(get_ctx),
):
    """Filtered, task-scoped research pointers for the given context.

    Disabled → HTTP 200 ``{"enabled":false,"records":[]}`` (loader never invoked).
    Enabled → the pure AND matcher over ``{role, task_family, track, owned_path}``,
    top-5 / ≤1.5 KB pointers, sorted by record id, with a strong ETag over the exact
    response bytes. No task context yields zero records. Supports ``If-None-Match``
    for a bodyless 304.
    """
    root = monitor_ctx.roots.live_repo_root
    if not reg.is_enabled(root=root):
        return _json_response(reg.disabled_manifest_bytes())

    if len(owned_path) > reg.MAX_OWNED_PATHS:
        raise HTTPException(status_code=422, detail="too many owned_path values")
    if any(len(path) > reg.MAX_OWNED_PATH_LEN for path in owned_path):
        raise HTTPException(status_code=422, detail="owned_path value too long")

    runtime = reg.load_runtime_safe(root=root)
    if runtime is None:
        result = reg.empty_manifest_response()
    else:
        ctx = reg.normalize_context(role, task_family, track, owned_path)
        result = reg.filtered_manifest(runtime, ctx)

    if _matches_etag(request.headers.get("If-None-Match"), result.etag_hex):
        return Response(status_code=304, headers={"ETag": f'"{result.etag_hex}"'})
    return _json_response(result.body, result.etag_hex)


@router.get("/cold-start")
def knowledge_cold_start(
    request: Request,
    role: str | None = Query(default=None, max_length=reg.MAX_QUERY_VALUE_LEN),
    monitor_ctx: MonitorContext = Depends(get_ctx),
):
    """Role-only cold-start research pointers (ADR-011 P3 ``cold_start_roles``).

    Distinct from ``/manifest``: this NEVER runs the AND matcher over
    role/task_family/track/owned_path — a missing family/track/path context would
    fail that matcher closed even for a record that explicitly opted in via
    ``cold_start_roles``. Disabled → HTTP 200 ``{"enabled":false,"records":[]}``.
    Enabled → pointers from ``cold_start_roles`` only, top-5 / ≤1.5 KB, sorted by
    record id, strong ETag over the exact response bytes, ``If-None-Match`` gives a
    bodyless 304.
    """
    root = monitor_ctx.roots.live_repo_root
    if not reg.is_enabled(root=root):
        return _json_response(reg.disabled_manifest_bytes())

    runtime = reg.load_runtime_safe(root=root)
    result = reg.empty_manifest_response() if runtime is None else reg.filtered_cold_start(runtime, role)

    if _matches_etag(request.headers.get("If-None-Match"), result.etag_hex):
        return Response(status_code=304, headers={"ETag": f'"{result.etag_hex}"'})
    return _json_response(result.body, result.etag_hex)


@router.get("/monitor")
def knowledge_monitor(
    window_days: int = Query(default=30, ge=1, le=365),
    monitor_ctx: MonitorContext = Depends(get_ctx),
):
    """ADR-011 P4 registry observability — lifecycle rot, adoption, distinct-task
    consumption, and dead consumers.

    **Ungated by the discovery kill switch**: governance must not disappear when
    serving is disabled — the payload reports ``discovery_enabled`` so the caller
    knows the serving state. Deterministic (identical registry/telemetry/cache/now
    → identical metrics), no ETag/conditional caching. Built from the RAW registry
    and P1 per-record helpers plus the P3 telemetry JSONL, so semantic-invalid
    records stay visible instead of being hidden by the runtime loader. Fail-soft:
    a broken registry, cache, or event line degrades a section, never 500s.

    Privacy: only registry ids and counts are returned — never task ids, run/
    session/source, role, track, owned paths, titles, summaries, source urls,
    prompts, or digest bodies. Unknown research ids are aggregated without echoing
    their id strings.
    """
    return observability.build_monitor(
        window_days=window_days,
        root=monitor_ctx.roots.live_repo_root,
    )


@router.get("/record/{record_id}")
def knowledge_record(
    request: Request,
    record_id: str,
    task: str | None = Query(default=None),
    monitor_ctx: MonitorContext = Depends(get_ctx),
):
    """One validated compact digest body as ``text/markdown`` with an honest ETag.

    Returns a generic 404 for a disabled feature, an unknown/malformed/traversal
    id, an invalid/drifted/``private-local`` record, an unsafe digest path, or an
    over-budget body — never a leaking status. ``content_hash`` is the ETag for the
    exact normalized body; ``If-None-Match`` gives a bodyless 304.

    ADR-011 P3 consumption telemetry: an optional ``task`` id attributes an actual
    on-demand fetch (a served 200 or a cache-backed 304) to a validated, still-active
    delegate task. Attribution is best-effort and **response-invariant** — a missing,
    malformed, unknown, or finished task changes nothing an unattributed caller sees
    and never reveals whether a task exists; it just emits no consumption event. A
    404 (no record served) is never a consumption. A `304` only counts as
    consumption when the same task already has evidence of a matching prior `200`
    (see ``consumption.record_consumption``) — replaying the record's public
    ``content_hash`` as ``If-None-Match`` without ever fetching the body does not
    manufacture a consumption event.
    """
    root = monitor_ctx.roots.live_repo_root
    if not reg.is_enabled(root=root):
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    runtime = reg.load_runtime_safe(root=root)
    if runtime is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    result = reg.record_body(runtime, record_id)
    if result is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    body, etag_hex = result
    etag = f'"{etag_hex}"'
    if _matches_etag(request.headers.get("If-None-Match"), etag_hex):
        consumption.record_consumption(task, record_id, status=304, etag=etag_hex)
        return Response(status_code=304, headers={"ETag": etag})
    consumption.record_consumption(task, record_id, status=200, etag=etag_hex)
    return Response(content=body, media_type=_MARKDOWN_MEDIA, headers={"ETag": etag})


@router.get("/find")
def knowledge_find(
    request: Request,
    q: str = Query(min_length=1, max_length=docs_find.MAX_QUERY_CHARS),
    limit: str = Query(
        default=str(docs_find.DEFAULT_LIMIT),
        description=f"Maximum hits, ASCII digits only, 1..{docs_find.MAX_LIMIT}.",
    ),
    family: str | None = Query(default=None, max_length=64, pattern=docs_find.FAMILY_ID_PATTERN),
    monitor_ctx: MonitorContext = Depends(get_ctx),
):
    """Locate a document, data store or resource in one query (#9412).

    The same search as ``python -m scripts.docs.find``: catalogue entries
    (``docs/knowledge/catalogue.yaml``), tracked path names and the text of
    content-searchable families in Git's index of the live repository root. Each
    hit carries its path, line, excerpt, family, status, replacement and the
    family's query hint; ``coverage`` lists the families searched and skipped and
    says ``incomplete`` (with reasons) when a budget cut the search short, so a
    cut-off search is never reported as "no source".

    **Ungated**: a locator that a kill switch can turn off fails its purpose, so this
    route never consults ``research_registry``. Read-only; nothing is persisted.
    An empty query, a bad limit or an unknown family is a typed 422; an unreadable
    repository is a typed 503; neither is a 500. ``limit`` is read as raw text and
    checked by the library's own validator (digits only) before any search starts, so
    ``5.0``, ``5e0`` or ``+5`` is rejected here exactly as the CLI rejects it; every
    repeated ``limit`` value is checked, not only the one used.
    """
    try:
        for raw in request.query_params.getlist("limit"):
            docs_find.limit_from_text(raw)
        checked = docs_find.limit_from_text(limit)
        return docs_find.find(q, checked, family=family, repo=monitor_ctx.roots.live_repo_root)
    except docs_find.FindError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": str(exc)}) from None
    except docs_find.UNREADABLE as exc:
        detail = {"code": getattr(exc, "code", type(exc).__name__), "message": docs_find.escape_excerpt(str(exc)[:300])}
        raise HTTPException(status_code=503, detail=detail) from None
