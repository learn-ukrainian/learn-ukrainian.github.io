"""Fleet board v1 routes: an endpoint index, a JSON Schema document, and the PR pipeline."""

from __future__ import annotations

import re
from typing import Annotated, Any

from fastapi import APIRouter, Path, Query, Request

from . import prs as prs_api
from .envelope import endpoint_schema, envelope, utc_timestamp
from .sources import SourceReport, collect_source_reports, report

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


def respond(name: str, data: Any) -> dict[str, Any]:
    """Envelope ``data``. A source failure stays inside ``sources``."""
    try:
        return envelope(name, data, _sources())
    except Exception:
        try:
            generated_at = utc_timestamp()
        except Exception:
            generated_at = "1970-01-01T00:00:00Z"
        safe_data = data if isinstance(data, dict) else {}
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


@router.get("/prs", name="prs")
def read_prs(
    epic: Annotated[str | None, Query(max_length=80)] = None,
    state: Annotated[str | None, Query(max_length=40)] = None,
) -> dict[str, Any]:
    return prs_api.read_prs(epic=epic, state=state)


@router.get("/prs/{number}", name="pr")
def read_pr(number: Annotated[int, Path(ge=1)]) -> dict[str, Any]:
    return prs_api.read_pr(number)
