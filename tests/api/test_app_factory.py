"""Step-0 structural and context tests for the Monitor API app factory."""

from __future__ import annotations

import re
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.exception_handlers import websocket_request_validation_exception_handler
from fastapi.exceptions import RequestValidationError, WebSocketRequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from scripts.api import main as api_main
from scripts.api.monitor_context import fixture_context, production_context
from scripts.api.resilience import resilience_middleware
from tests.api.opsec_sweep import registry

pytestmark = pytest.mark.repo_invariant

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_ACCESS_PATTERNS = (
    re.compile(r"\bsqlite3\.connect\("),
    re.compile(r"\bconnect_sqlite\("),
    re.compile(r"\bSessionStreamDatabase\("),
)

# The exact pre-migration inventory from design §4.1: 22 access sites in 21
# unique files. Infrastructure files are listed too so the denominator cannot
# silently shrink when the exemptions below are changed.
DB_ACCESS_ALLOWLIST = frozenset(
    {
        "scripts/api/admin_router.py",
        "scripts/api/agent_monitor_router.py",
        "scripts/api/comms_router.py",
        "scripts/api/dashboard_comms.py",
        "scripts/api/delegate_router.py",
        "scripts/api/discussions_router.py",
        "scripts/api/epics_router.py",
        "scripts/api/fleet_router.py",
        "scripts/api/fleet_workers_collect.py",
        "scripts/api/hramatka_cache.py",
        "scripts/api/hramatka_router.py",
        "scripts/api/occupancy_local.py",
        "scripts/api/resilience.py",
        "scripts/api/runtime_router.py",
        "scripts/api/session_streams_router.py",
        "scripts/api/state_helpers.py",
        "scripts/api/telemetry/legacy_comms.py",
        "scripts/api/telemetry_router.py",
        "scripts/api/wiki_router.py",
        "scripts/api/gold_router.py",
        "agents_extensions/shared/session_streams/db.py",
    }
)
DB_ACCESS_INFRASTRUCTURE = frozenset(
    {
        "scripts/api/monitor_context.py",
        "scripts/api/resilience.py",
        "agents_extensions/shared/session_streams/db.py",
    }
)


def test_factory_route_table_keeps_frozen_denominator() -> None:
    factory_app = api_main.create_app(production_context())

    registry.assert_frozen_denominator(factory_app)
    assert factory_app.routes[-1].original_router is api_main.core_router
    core_contexts = list(factory_app.routes[-1].effective_route_contexts())
    assert core_contexts[-1].path == "/{path:path}"
    assert core_contexts[-2].path == "/images/{path:path}"


def test_factory_snapshot_preserves_middleware_and_exception_handlers() -> None:
    app = api_main.create_app(production_context())

    assert [(entry.cls, entry.args) for entry in app.user_middleware] == [
        (BaseHTTPMiddleware, ()),
        (CORSMiddleware, ()),
    ]
    assert app.user_middleware[0].kwargs["dispatch"] is resilience_middleware
    assert app.user_middleware[1].kwargs == {
        "allow_origins": ["*"],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }

    assert set(app.exception_handlers) == {
        api_main.StarletteHTTPException,
        RequestValidationError,
        WebSocketRequestValidationError,
        Exception,
    }
    assert app.exception_handlers[api_main.StarletteHTTPException] is api_main.http_exception_handler
    assert app.exception_handlers[RequestValidationError] is api_main.request_validation_exception_handler
    assert app.exception_handlers[WebSocketRequestValidationError] is websocket_request_validation_exception_handler
    assert app.exception_handlers[Exception] is api_main.global_exception_handler


def test_factory_lifespan_is_wired_and_runs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    start_periodic_refresh = Mock()
    stop_periodic_refresh = Mock()
    monkeypatch.setattr(api_main, "preload_all", Mock())
    monkeypatch.setattr(api_main, "install_signal_logging", Mock())
    monkeypatch.setattr(api_main, "ensure_broker_db_ready", Mock())
    monkeypatch.setattr(api_main, "seed_manifest_inventory", Mock())
    monkeypatch.setattr(api_main.isa, "schedule_refresh", Mock())
    monkeypatch.setattr(api_main, "warm_projection_cache", Mock())
    monkeypatch.setattr(api_main, "start_periodic_refresh", start_periodic_refresh)
    monkeypatch.setattr(api_main, "stop_periodic_refresh", stop_periodic_refresh)

    factory_app = api_main.create_app(fixture_context(tmp_path))
    with TestClient(factory_app):
        pass

    start_periodic_refresh.assert_called_once_with()
    stop_periodic_refresh.assert_called_once_with()


def test_fixture_context_resolves_roots_and_rejects_symlink_escape(tmp_path: Path) -> None:
    context = fixture_context(tmp_path)

    for field_name, value in context.roots.__dict__.items():
        if field_name == "effective_roots":
            values = value.values()
        elif value is None:
            continue
        else:
            values = (value,)
        for path in values:
            assert Path(path).resolve().is_relative_to(tmp_path.resolve())

    assert context.stores.sources_db.path.resolve().is_relative_to(tmp_path.resolve())
    assert context.stores.message_db.path.resolve().is_relative_to(tmp_path.resolve())
    assert context.stores.session_streams_database.path.resolve().is_relative_to(tmp_path.resolve())
    assert context.stores.epics_database.path.resolve().is_relative_to(tmp_path.resolve())

    outside = tmp_path.parent / "monitor-context-outside"
    outside.mkdir()
    escaped = tmp_path / "escaped"
    escaped.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes"):
        context._open_db(escaped / "messages.sqlite3")


def test_core_routes_read_the_serving_app_version(tmp_path: Path) -> None:
    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    first = api_main.create_app(fixture_context(tmp_path / "first"), lifespan=no_lifespan)
    second = api_main.create_app(fixture_context(tmp_path / "second"), lifespan=no_lifespan)
    first.version = "first-version"
    second.version = "second-version"

    with TestClient(first) as first_client, TestClient(second) as second_client:
        assert first_client.get("/api/health").json()["version"] == "first-version"
        assert second_client.get("/api/health").json()["version"] == "second-version"
        assert first_client.get("/api/config").json()["api_version"] == "first-version"
        assert second_client.get("/api/config").json()["api_version"] == "second-version"


def test_db_access_patterns_have_the_step_zero_allowlist() -> None:
    assert len(DB_ACCESS_ALLOWLIST) == 21
    files = sorted((REPO_ROOT / "scripts/api").rglob("*.py"))
    files.append(REPO_ROOT / "agents_extensions/shared/session_streams/db.py")
    findings: list[str] = []
    for path in files:
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative in DB_ACCESS_INFRASTRUCTURE:
            continue
        source = path.read_text(encoding="utf-8")
        if any(pattern.search(source) for pattern in DB_ACCESS_PATTERNS):
            findings.append(relative)

    expected_non_infrastructure = DB_ACCESS_ALLOWLIST - DB_ACCESS_INFRASTRUCTURE
    assert set(findings) == expected_non_infrastructure, {
        "missing": sorted(expected_non_infrastructure - set(findings)),
        "unexpected": sorted(set(findings) - expected_non_infrastructure),
    }
