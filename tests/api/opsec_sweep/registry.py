"""Explicit exercise records for the Monitor API OPSEC sweep.

The live FastAPI tree is the denominator.  ``FROZEN_DENOMINATOR_SHA256`` is
the reviewed snapshot guard: adding an HTTP or WebSocket route changes the
fingerprint and fails the sweep until a record is deliberately reviewed.
Included routers and mounts are walked through their public ``routes`` and
``original_router``/``include_context`` attributes; no private FastAPI route
class is part of the walker contract.
"""

from __future__ import annotations

import base64
import hashlib
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Literal

from fastapi.routing import APIRoute
from starlette.routing import Mount, WebSocketRoute

from scripts.orchestration import thread_handoff

HTTP_METHODS = frozenset({"DELETE", "GET", "PATCH", "POST", "PUT"})
RouteClass = Literal["read", "read-side-effect", "mutation", "stream"]
FixtureKind = Literal["isolated", "skip"]

# Filled from the current exact route tree after the implementation is
# assembled.  The count and digest are intentionally independent checks.
FROZEN_HTTP_OPERATION_COUNT = 280
FROZEN_WEBSOCKET_ROUTE_COUNT = 1
FROZEN_DENOMINATOR_SHA256 = "4876620305f8035f30103fc6f2d0f0d4f22e43dfb00247f1a7aa32604cbccd20"

# The OpenAPI document records the successful response for most operations,
# while the isolated fixture deliberately exercises empty stores, denied
# subprocess seams, and invalid synthetic identifiers. Read records must not
# silently bless a server error: an exercised 5xx needs a route-specific
# record reason and explicit expected status.
DOCUMENTED_EXERCISE_STATUSES = frozenset(
    {200, 400, 401, 403, 404, 409, 410, 422, 500, 503}
)

EXERCISED_READ_5XX_REASONS: dict[str, str] = {
    "GET /api/comms/by-module/{track}/{slug}": "isolated fixture has no broker module rows",
    "GET /api/comms/channels/{name}": "isolated fixture has no broker channel store",
    "GET /api/comms/channels/{name}/deliveries": "isolated fixture has no broker delivery store",
    "GET /api/comms/channels/{name}/messages": "isolated fixture has no broker message store",
    "GET /api/comms/channels/{name}/threads/{thread_id}": "isolated fixture has no broker thread store",
    "GET /api/dashboard/comms/conversation/{task_id}": "isolated fixture has no dashboard comms store",
    "GET /api/dashboard/comms/message/{message_id}": "isolated fixture has no dashboard comms store",
    "GET /api/dashboard/comms/messages": "isolated fixture has no dashboard comms store",
    "GET /api/epics/v1": "isolated fixture has no seeded epic registry snapshot",
    "GET /api/rules": "isolated fixture has no deployed rule files",
    "GET /api/state/preparation": "sparse isolated fixture omits the curriculum tree",
    "GET /api/state/preparation/{track}/{slug}": "sparse isolated fixture omits the curriculum tree",
    "GET /api/work/v1/next": "isolated fixture has no warm work projection",
}

_CONVERTER_RE = re.compile(r"\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::[^}]+)?\}")
_PATH_PARAM_RE = re.compile(r"\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::[^}]+)?\}")


@dataclass(frozen=True, order=True)
class Operation:
    """One HTTP method/template pair or one WebSocket template."""

    method: str
    path_template: str

    @property
    def key(self) -> str:
        return f"{self.method} {self.path_template}"


@dataclass(frozen=True)
class ExerciseRecord:
    """Bounded request recipe for one denominator operation."""

    method: str
    path_template: str
    classification: RouteClass
    fixture: FixtureKind
    path_values: Mapping[str, str] = field(default_factory=dict)
    query: Mapping[str, Any] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    body_factory: Callable[[], Any] | None = None
    ws_script: tuple[Mapping[str, Any], ...] = ()
    owner: str | None = None
    reason: str | None = None
    expiry: str | None = None
    expected_statuses: tuple[int, ...] = ()

    @property
    def key(self) -> str:
        return f"{self.method} {self.path_template}"

    def path_params(self) -> Mapping[str, str]:
        return self.path_values

    def body(self) -> Any:
        """Build the bounded request body, if this operation has one."""
        return self.body_factory() if self.body_factory is not None else None

    @property
    def class_name(self) -> str:
        """Compatibility alias for callers that avoid the Python keyword."""
        return self.classification

    def as_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "path_template": self.path_template,
            "class": self.classification,
            "fixture": self.fixture,
            "path_params": dict(self.path_values),
            "query": dict(self.query),
            "headers": dict(self.headers),
            "body": self.body_factory,
            "ws_script": list(self.ws_script),
            "skip": (
                {"owner": self.owner, "reason": self.reason, "expiry": self.expiry}
                if self.fixture == "skip"
                else None
            ),
        }


def _join_path(prefix: str, path: str) -> str:
    if path == "/":
        return prefix.rstrip("/") + "/" if prefix else "/"
    if not prefix:
        return path or "/"
    return prefix.rstrip("/") + "/" + path.lstrip("/")


def normalize_path_template(path: str) -> str:
    """Normalize Starlette converters to OpenAPI-style ``{name}`` tokens."""
    normalized = _CONVERTER_RE.sub(lambda match: "{" + match.group("name") + "}", path)
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    return normalized


def _walk_routes(node: Any, prefix: str = "") -> Iterable[tuple[str, Operation]]:
    """Yield routes from an app/router/mount using public route attributes."""
    effective_contexts = getattr(node, "effective_route_contexts", None)
    if callable(effective_contexts):
        for context in effective_contexts():
            original_route = getattr(context, "original_route", context)
            path = normalize_path_template(getattr(context, "path", getattr(original_route, "path", "/")))
            if isinstance(original_route, WebSocketRoute):
                yield "websocket", Operation("WEBSOCKET", path)
            elif isinstance(original_route, APIRoute) and getattr(context, "include_in_schema", True):
                for method in sorted(getattr(context, "methods", ()) & HTTP_METHODS):
                    yield "http", Operation(method, path)
        return

    original_router = getattr(node, "original_router", None)
    if original_router is not None:
        context = getattr(node, "include_context", None)
        included_prefix = getattr(context, "prefix", "") if context is not None else ""
        yield from _walk_routes(original_router, _join_path(prefix, included_prefix))
        return

    if isinstance(node, Mount):
        mount_prefix = _join_path(prefix, getattr(node, "path", ""))
        for child in getattr(node, "routes", ()):
            yield from _walk_routes(child, mount_prefix)
        return

    if isinstance(node, WebSocketRoute):
        path = normalize_path_template(_join_path(prefix, node.path))
        yield "websocket", Operation("WEBSOCKET", path)
        return

    if isinstance(node, APIRoute):
        if not getattr(node, "include_in_schema", True):
            return
        path = normalize_path_template(_join_path(prefix, node.path))
        for method in sorted(getattr(node, "methods", ()) & HTTP_METHODS):
            yield "http", Operation(method, path)
        return

    routes = getattr(node, "routes", None)
    if routes is not None:
        node_prefix = prefix
        if node_prefix == "" and node is not None and not hasattr(node, "openapi"):
            node_prefix = _join_path(prefix, getattr(node, "prefix", ""))
        for child in routes:
            yield from _walk_routes(child, node_prefix)


def enumerate_http_operations(app: Any) -> tuple[Operation, ...]:
    """Enumerate the HTTP denominator from the app's route tree."""
    operations = {operation for kind, operation in _walk_routes(app) if kind == "http"}
    return tuple(sorted(operations))


def enumerate_websocket_routes(app: Any) -> tuple[Operation, ...]:
    """Enumerate WebSocket templates separately from OpenAPI operations."""
    operations = {operation for kind, operation in _walk_routes(app) if kind == "websocket"}
    return tuple(sorted(operations))


def openapi_operations(app: Any) -> tuple[Operation, ...]:
    """Return OpenAPI's method/template denominator for the cross-check."""
    operations: set[Operation] = set()
    for path, item in app.openapi().get("paths", {}).items():
        for method in item:
            if method.upper() in HTTP_METHODS:
                operations.add(Operation(method.upper(), normalize_path_template(path)))
    return tuple(sorted(operations))


def denominator_digest(
    http_operations: Iterable[Operation], websocket_routes: Iterable[Operation]
) -> str:
    lines = [operation.key for operation in sorted(http_operations)]
    lines.extend(f"WS {operation.path_template}" for operation in sorted(websocket_routes))
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def denominator_diff(app: Any) -> dict[str, list[str]]:
    """Return route-tree/OpenAPI differences for a useful failure message."""
    walked = {operation.key for operation in enumerate_http_operations(app)}
    openapi = {operation.key for operation in openapi_operations(app)}
    websockets = {operation.path_template for operation in enumerate_websocket_routes(app)}
    return {
        "missing_from_openapi": sorted(walked - openapi),
        "missing_from_route_tree": sorted(openapi - walked),
        "websockets": sorted(websockets),
    }


def assert_frozen_denominator(app: Any) -> None:
    """Fail closed when a new route has not received a reviewed record."""
    http_operations = enumerate_http_operations(app)
    openapi = openapi_operations(app)
    websockets = enumerate_websocket_routes(app)
    differences = denominator_diff(app)
    assert len(http_operations) == len(openapi) == FROZEN_HTTP_OPERATION_COUNT, (
        "Monitor API HTTP denominator changed: "
        f"route_tree={len(http_operations)} openapi={len(openapi)} "
        f"expected={FROZEN_HTTP_OPERATION_COUNT} diff={differences}"
    )
    assert len(websockets) == FROZEN_WEBSOCKET_ROUTE_COUNT, (
        f"Monitor API WebSocket denominator changed: got {len(websockets)}, "
        f"expected {FROZEN_WEBSOCKET_ROUTE_COUNT}; routes={differences['websockets']}"
    )
    assert not differences["missing_from_openapi"] and not differences["missing_from_route_tree"], (
        f"route tree/OpenAPI operation diff: {differences}"
    )
    digest = denominator_digest(http_operations, websockets)
    assert digest == FROZEN_DENOMINATOR_SHA256, (
        "Monitor API route denominator changed without a registry review: "
        f"sha256={digest} expected={FROZEN_DENOMINATOR_SHA256}"
    )


def _path_value(name: str) -> str:
    if name in {"stream_id", "epic"}:
        return "epic:9999"
    if name in {"page_num", "num", "message_id", "image_id", "start", "end", "upload_seq"}:
        return "1"
    if name in {"filename"}:
        return "missing-opsec-fixture.json"
    if name in {"path", "pdf_stem", "record_id", "conversation_id", "task_id", "job_id", "dec_id"}:
        return "opsec-synthetic-missing"
    if name in {"track", "track_id", "level"}:
        return "a1"
    if name in {"slug"}:
        return "opsec-synthetic-missing"
    if name in {"name", "scope"}:
        return "opsec-synthetic"
    return "opsec-synthetic"


def _body_factory(path_template: str) -> Callable[[], Any] | None:
    if path_template == "/api/comms/send":
        return lambda: {
            "from_llm": "codex",
            "to_llm": "gemini",
            "content": "opsec synthetic deprecated-route probe",
            "task_id": "opsec-synthetic-task",
        }
    if path_template == "/api/epics/v1/{stream_id}/bundles":
        member_name = "handoff.md"
        member_body = b"opsec fixture handoff\n"
        members = {member_name: member_body}
        manifest = {
            "schema": "rollover-bundle.v1",
            "agent": "codex",
            "stream_id": "epic:9999",
            "lineage_id": "opsec-lineage",
            "rollover_id": "rollover-opsec",
            "generation": 1,
            "status": "pending_start",
            "prepared_at": "2026-01-01T00:00:00Z",
            "source_root": "{{REPO_ROOT}}",
            "exported_at": "2026-01-01T00:00:00Z",
            "files": [
                {
                    "path": member_name,
                    "sha256": hashlib.sha256(member_body).hexdigest(),
                    "bytes": len(member_body),
                    "tokenized": True,
                }
            ],
            "tokenized_members": [member_name],
            "upload_seq": 0,
            "bundle_sha256": "",
        }
        manifest["bundle_sha256"] = thread_handoff._bundle_digest(members, manifest)
        blob = thread_handoff._bundle_archive(members, manifest)
        return lambda: {
            "stream_id": "epic:9999",
            "session_id": "opsec-bundle-session",
            "lease_id": "opsec-bundle-lease",
            "generation": 1,
            "fencing_token": 1,
            "agent": "codex",
            "harness": "codex-cli",
            "instance_id": "opsec-bundle-instance",
            "process_id": 1,
            "host_id": "opsec-host-id",
            "heartbeat_at": "2026-01-01T00:00:00Z",
            "expires_at": "2026-01-01T00:15:00Z",
            "ttl_seconds": 900,
            "version": 1,
            "manifest": manifest,
            "blob": base64.b64encode(blob).decode("ascii"),
        }
    return None


def _query_for(path_template: str) -> dict[str, Any]:
    # Explicitly force side-effect-shaped flags to their read-only values.
    if path_template == "/api/orient":
        return {"lean": "true", "sections": "health"}
    if path_template == "/api/session-streams/v1/drift":
        return {"dry_run": "true"}
    if path_template == "/api/work/v1/next":
        return {"stream": "infra-harness", "limit": "1"}
    if path_template == "/api/ops/entire-context/search":
        return {"q": "opsec synthetic", "limit": "1"}
    if path_template in {"/api/sources/search_text", "/api/rag/search_text", "/api/sources/search_images", "/api/rag/search_images", "/api/sources/search_literary", "/api/rag/search_literary"}:
        return {"q": "opsec synthetic", "limit": "1"}
    if path_template == "/api/comms/inbox":
        return {"agent": "codex", "limit": "1"}
    if path_template == "/api/epics/v1/{stream_id}/bundles":
        return {"agent": "opsec-synthetic", "lineage_id": "opsec-lineage", "limit": "1"}
    if path_template == "/api/epics/v1/{stream_id}/bundles/latest":
        return {"agent": "opsec-synthetic", "lineage_id": "opsec-lineage"}
    return {}


def _record_for(operation: Operation, openapi_by_key: Mapping[str, Any]) -> ExerciseRecord:
    if operation.method == "WEBSOCKET":
        return ExerciseRecord(
            method=operation.method,
            path_template=operation.path_template,
            classification="stream",
            fixture="isolated",
            ws_script=({"expect": "heartbeat"},),
            expected_statuses=(),
        )

    path_values = {match.group("name"): _path_value(match.group("name")) for match in _PATH_PARAM_RE.finditer(operation.path_template)}
    operation_spec = openapi_by_key.get(operation.key, {})
    statuses = tuple(
        int(status)
        for status in operation_spec.get("responses", {})
        if str(status).isdigit()
    )
    statuses = tuple(sorted(set(statuses) | DOCUMENTED_EXERCISE_STATUSES))
    explicit_5xx_reason = EXERCISED_READ_5XX_REASONS.get(operation.key)
    if explicit_5xx_reason is None:
        statuses = tuple(status for status in statuses if not 500 <= status < 600)

    if operation.path_template in {
        "/api/epics/v1/{stream_id}/bundles",
        "/api/epics/v1/{stream_id}/bundles/latest",
        "/api/epics/v1/{stream_id}/bundles/{upload_seq}",
    }:
        if operation.method == "POST":
            return ExerciseRecord(
                method=operation.method,
                path_template=operation.path_template,
                classification="mutation",
                fixture="isolated",
                path_values=path_values,
                body_factory=_body_factory(operation.path_template),
                reason="the isolated TestClient is a non-loopback peer, so the upload must refuse before store access",
                expected_statuses=(403,),
            )
        return ExerciseRecord(
            method=operation.method,
            path_template=operation.path_template,
            classification="read",
            fixture="isolated",
            path_values=path_values,
            query=_query_for(operation.path_template),
            reason="the synthetic epic is absent from the disposable fixture store, so the read returns 404",
            expected_statuses=(404,),
        )

    if operation.method == "POST" and operation.path_template == "/api/comms/send":
        return ExerciseRecord(
            method=operation.method,
            path_template=operation.path_template,
            classification="read",
            fixture="isolated",
            body_factory=_body_factory(operation.path_template),
            expected_statuses=(410,),
        )

    if operation.method in {"POST", "PUT", "DELETE", "PATCH"}:
        return ExerciseRecord(
            method=operation.method,
            path_template=operation.path_template,
            classification="mutation",
            fixture="skip",
            path_values=path_values,
            owner="monitor-infra",
            reason="mutation has no approved disposable-store recipe in PR-A",
            expiry="2026-09-23",
            expected_statuses=statuses,
        )

    classification: RouteClass = "read-side-effect" if operation.path_template == "/api/session-streams/v1/drift" else "read"
    return ExerciseRecord(
        method=operation.method,
        path_template=operation.path_template,
        classification=classification,
        fixture="isolated",
        path_values=path_values,
        query=_query_for(operation.path_template),
        body_factory=_body_factory(operation.path_template),
        reason=explicit_5xx_reason,
        expected_statuses=statuses,
    )


def build_registry(app: Any) -> tuple[ExerciseRecord, ...]:
    """Build one record per frozen operation after the denominator checks."""
    assert_frozen_denominator(app)
    openapi_by_key = {
        f"{method.upper()} {path}": operation
        for path, item in app.openapi().get("paths", {}).items()
        for method, operation in item.items()
        if method.upper() in HTTP_METHODS
    }
    operations = [*enumerate_http_operations(app), *enumerate_websocket_routes(app)]
    records = tuple(_record_for(operation, openapi_by_key) for operation in operations)
    assert len(records) == len(set(record.key for record in records)), "duplicate OPSEC exercise records"
    assert {record.key for record in records} == {operation.key for operation in operations}, (
        "an app operation has no OPSEC exercise record"
    )
    today = date.today()
    latest_allowed = today + timedelta(days=30)
    for record in records:
        if record.fixture != "skip":
            continue
        assert record.owner and record.reason and record.expiry, f"skip metadata missing: {record.key}"
        expiry = date.fromisoformat(record.expiry)
        assert today < expiry <= latest_allowed, f"skip expiry outside 30-day window: {record.key}"
    return tuple(sorted(records, key=lambda record: record.key))


def unrecorded_operations(app: Any, records: Iterable[ExerciseRecord]) -> list[str]:
    """Return operations absent from a supplied registry for focused tests."""
    known = {record.key for record in records}
    current = {operation.key for operation in enumerate_http_operations(app)}
    current.update(operation.key for operation in enumerate_websocket_routes(app))
    return sorted(current - known)
