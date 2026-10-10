"""Fleet board v1 routes."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import JSONResponse

from ..monitor_context import MonitorContext, get_ctx
from . import prs as prs_api
from .budget import load_budget, unknown_budget
from .envelope import endpoint_schema, envelope, utc_timestamp
from .file_sources import load_backups, load_downloads, load_harness, load_harness_driver
from .http_sources import empty_stats, load_alerts, load_links, load_stats
from .roster import empty_roster, load_roster
from .sources import SourceReport, collect_source_reports, overlay_source, read_location, report
from .view import load_board

router = APIRouter()

PUBLIC_PREFIX = "/api/fleet/v1"
_SKIP_METHODS = frozenset({"HEAD", "OPTIONS"})
_KNOWN_SCHEMA_IDS = {
    PUBLIC_PREFIX: "fleet.v1.index",
    f"{PUBLIC_PREFIX}/schema": "fleet.v1.schema",
}


def _schema_id(path: str, route_name: str) -> str:
    known = _KNOWN_SCHEMA_IDS.get(path)
    if known:
        return known
    token = re.sub(r"[^a-z0-9_]+", "_", route_name.lower()).strip("_")
    return f"fleet.v1.{token or 'endpoint'}"


def _is_v1(path: str) -> bool:
    return path == PUBLIC_PREFIX or path.startswith(f"{PUBLIC_PREFIX}/")


def _iter_mounted_routes(app: Any):
    """Yield route objects that carry a path and methods.

    Included routers expose their handlers through ``effective_route_contexts``
    rather than a flat ``path`` on the top-level route.
    """
    for route in getattr(app, "routes", ()):
        contexts = getattr(route, "effective_route_contexts", None)
        if callable(contexts):
            yield from contexts()
            continue
        if getattr(route, "path", None) and getattr(route, "methods", None):
            yield route


def endpoint_index(app: Any) -> list[dict[str, str]]:
    """Every HTTP route mounted under the v1 prefix, except HEAD and OPTIONS."""
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for route in _iter_mounted_routes(app):
        path = getattr(route, "path", "")
        if not isinstance(path, str) or not _is_v1(path):
            continue
        methods = getattr(route, "methods", None) or ()
        route_name = str(getattr(route, "name", "") or "")
        for method in sorted(methods):
            if method in _SKIP_METHODS:
                continue
            key = (method, path)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"method": method, "path": path, "schema": _schema_id(path, route_name)})
    rows.sort(key=lambda item: (item["path"], item["method"]))
    return rows


def _sources() -> tuple[SourceReport, ...]:
    try:
        return collect_source_reports()
    except Exception:
        return (report("sources", "unavailable"),)


def _publish(
    schema_name: str,
    source_name: str,
    empty: Callable[[], dict[str, Any]],
    loader: Callable[[], tuple[dict[str, Any], tuple[SourceReport, ...]]],
) -> dict[str, Any]:
    """Run one loader. A bug becomes ``unavailable`` and HTTP 200."""
    try:
        data, reports = loader()
        return envelope(schema_name, data, reports)
    except Exception:
        return envelope(schema_name, empty(), (report(source_name, "unavailable"),))


def respond(
    name: str,
    data: Any,
    sources: Sequence[SourceReport] | None = None,
) -> dict[str, Any]:
    """Envelope ``data``. A source failure stays inside ``sources``."""
    try:
        chosen = _sources() if sources is None else tuple(sources)
        return envelope(name, data, chosen)


        return envelope(name, data, _sources() if sources is None else sources)
    except Exception:
        try:
            generated_at = utc_timestamp()
        except Exception:
            generated_at = "1970-01-01T00:00:00Z"
        safe_data = data if data is None or isinstance(data, dict) else {}
        return {
            "schema": f"fleet.v1.{name}" if re.fullmatch(r"[a-z0-9_]+", name) else "fleet.v1.unknown",
            "generated_at": generated_at,
            "sources": [report("response", "unavailable").as_dict()],
            "data": safe_data,
        }


@router.get("", name="index")
def read_index(request: Request) -> dict[str, Any]:
    try:
        data: dict[str, Any] = {"endpoints": endpoint_index(request.app)}
    except Exception:
        data = {"endpoints": []}
    return respond("index", data)


@router.get("/schema", name="schema")
def read_schema(request: Request) -> dict[str, Any]:
    try:
        identifiers = [item["schema"] for item in endpoint_index(request.app)]
        for required in ("fleet.v1.index", "fleet.v1.schema"):
            if required not in identifiers:
                identifiers.append(required)
        data: dict[str, Any] = {"endpoints": {schema_id: endpoint_schema(schema_id) for schema_id in identifiers}}
    except Exception:
        data = {
            "endpoints": {
                "fleet.v1.index": endpoint_schema("fleet.v1.index"),
                "fleet.v1.schema": endpoint_schema("fleet.v1.schema"),
            }
        }
    return respond("schema", data)


@router.get("/roster", name="roster")
def read_roster() -> dict[str, Any]:
    try:
        loaded = load_roster(read_location("FLEET_ROSTER_SNAPSHOT"))
        data: dict[str, Any] = loaded.data
        source = loaded.source
    except Exception:
        data = empty_roster()
        source = report("roster_snapshot", "unavailable")
    return respond("roster", data, overlay_source(source))


@router.get("/budget", name="budget")
def read_budget(ctx: MonitorContext = Depends(get_ctx)) -> dict[str, Any]:
    try:
        data, source = load_budget(ctx)
    except Exception:
        data = unknown_budget()
        source = report("routing_budget", "unavailable")
    return respond("budget", data, overlay_source(source))


_ROLES = frozenset({"driver", "worker", "bot"})


def _loaded(name: str, data: dict[str, Any] | None):
    try:
        board = load_board()
    except Exception:
        return None, respond(name, data, (report("board", "unavailable"),))
    return board, None


def _json(body: dict[str, Any], status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=body)


@router.get("/now", name="now", response_model=None)
def read_now() -> JSONResponse:
    board, failed = _loaded("now", {"attention": [], "epics": []})
    if failed is not None or board is None:
        return _json(failed or respond("now", {"attention": [], "epics": []}))
    return _json(respond("now", {"attention": board.attention, "epics": board.epics}, board.sources))


@router.get("/epics", name="epics", response_model=None)
def read_epics() -> JSONResponse:
    board, failed = _loaded("epics", {"epics": []})
    if failed is not None or board is None:
        return _json(failed or respond("epics", {"epics": []}))
    return _json(respond("epics", {"epics": board.epics}, board.sources))


@router.get("/epics/{epic}", name="epic", response_model=None)
def read_epic(epic: str) -> JSONResponse:
    board, failed = _loaded("epic", None)
    if failed is not None or board is None:
        return _json(failed or respond("epic", None))
    match = next((item for item in board.epics if item["epic"] == epic), None)
    if match is None:
        return _json(respond("epic", None, board.sources), 404)
    return _json(respond("epic", match, board.sources))


@router.get("/agents", name="agents", response_model=None)
def read_agents(role: str | None = Query(default=None)) -> JSONResponse:
    board, failed = _loaded("agents", {"agents": []})
    if failed is not None or board is None:
        return _json(failed or respond("agents", {"agents": []}))
    if role is not None and role not in _ROLES:
        return _json(respond("agents", {"agents": []}, board.sources), 400)
    agents = board.agents if role is None else [item for item in board.agents if item["role"] == role]
    return _json(respond("agents", {"agents": agents}, board.sources))


@router.get("/agents/{agent_id}", name="agent", response_model=None)
def read_agent(agent_id: str) -> JSONResponse:
    board, failed = _loaded("agent", None)
    if failed is not None or board is None:
        return _json(failed or respond("agent", None))
    match = next((item for item in board.agents if item["agent_id"] == agent_id), None)
    if match is None:
        return _json(respond("agent", None, board.sources), 404)
    return _json(respond("agent", match, board.sources))


@router.get("/alerts", name="alerts")
def read_alerts() -> dict[str, Any]:
    return _publish("alerts", "alerts", lambda: {"alerts": []}, load_alerts)


@router.get("/stats", name="stats")
def read_stats() -> dict[str, Any]:
    return _publish("stats", "stats", empty_stats, load_stats)


@router.get("/links", name="links")
def read_links() -> dict[str, Any]:
    return _publish("links", "links", lambda: {"links": []}, load_links)


@router.get("/prs", name="prs")
def read_prs(
    epic: Annotated[str | None, Query(max_length=80)] = None,
    state: Annotated[str | None, Query(max_length=40)] = None,
) -> dict[str, Any]:
    return prs_api.read_prs(epic=epic, state=state)


@router.get("/prs/{number}", name="pr")
def read_pr(number: Annotated[int, Path(ge=1)]) -> dict[str, Any]:
    return prs_api.read_pr(number)


@router.get("/backups", name="backups")
def read_backups() -> dict[str, Any]:
    return _publish(
        "backups",
        "backups",
        lambda: {"age_h": None, "stale": None, "last_result": None, "restore_test": None},
        load_backups,
    )


@router.get("/downloads", name="downloads")
def read_downloads() -> dict[str, Any]:
    return _publish("downloads", "downloads", lambda: {"state": None, "items": []}, load_downloads)


@router.get("/harness", name="harness")
def read_harness() -> dict[str, Any]:
    return _publish("harness", "harness_snapshot", lambda: {"drivers": []}, load_harness)


@router.get("/harness/{agent_id}", name="harness_driver")
def read_harness_driver(agent_id: str) -> dict[str, Any]:
    return _publish(
        "harness_driver",
        "harness_snapshot",
        lambda: {"driver": None},
        lambda: load_harness_driver(agent_id),
    )
