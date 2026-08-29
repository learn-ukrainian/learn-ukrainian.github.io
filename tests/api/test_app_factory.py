"""Step-0 structural and context tests for the Monitor API app factory."""

from __future__ import annotations

import json
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
# silently shrink when the exemptions below are changed. #7269 step 5 removed
# scripts/api/comms_router.py deliberately (20 -> 19); step 2 removed
# scripts/api/state_helpers.py direct access via MonitorContext (19 -> 18);
# step 8 removed scripts/api/admin_router.py (18 -> 17);
# step 9 removed scripts/api/dashboard_comms.py (17 -> 16).
DB_ACCESS_ALLOWLIST = frozenset(
    {
        "scripts/api/agent_monitor_router.py",
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

    assert context.roots.plans_root == context.roots.curriculum_root / "plans"
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


def test_step1_session_streams_cluster_isolation(tmp_path: Path) -> None:
    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    # Set up first isolated instance
    first_root = tmp_path / "first"
    first_ctx = fixture_context(first_root)
    first_conn = first_ctx.stores.session_streams_database.connect()
    first_conn.close()

    (first_root / "docs" / "session-state").mkdir(parents=True)
    (first_root / "docs" / "session-state" / "current.md").write_text(
        "# First Instance Session\nAgent-Handoff:\n- orchestrator: docs/session-state/current.orchestrator.md\n",
        encoding="utf-8",
    )
    (first_root / "docs" / "session-state" / "current.orchestrator.md").write_text(
        "First instance orchestrator state\n",
        encoding="utf-8",
    )
    (first_root / "agents_extensions" / "shared" / "rules").mkdir(parents=True)
    (first_root / "agents_extensions" / "shared" / "rules" / "operator-expectations.md").write_text(
        "# First Rules\nFirst rule body\n",
        encoding="utf-8",
    )
    (first_root / "scripts" / "config").mkdir(parents=True)
    (first_root / "scripts" / "config" / "issue_streams.yaml").write_text(
        "schema_version: issue-streams.v1\nstreams: {}\n",
        encoding="utf-8",
    )

    # Set up second isolated instance
    second_root = tmp_path / "second"
    second_ctx = fixture_context(second_root)
    second_conn = second_ctx.stores.session_streams_database.connect()
    second_conn.close()

    (second_root / "docs" / "session-state").mkdir(parents=True)
    (second_root / "docs" / "session-state" / "current.md").write_text(
        "# Second Instance Session\nAgent-Handoff:\n- orchestrator: docs/session-state/current.orchestrator.md\n",
        encoding="utf-8",
    )
    (second_root / "docs" / "session-state" / "current.orchestrator.md").write_text(
        "Second instance orchestrator state\n",
        encoding="utf-8",
    )
    (second_root / "agents_extensions" / "shared" / "rules").mkdir(parents=True)
    (second_root / "agents_extensions" / "shared" / "rules" / "operator-expectations.md").write_text(
        "# Second Rules\nSecond rule body\n",
        encoding="utf-8",
    )
    (second_root / "scripts" / "config").mkdir(parents=True)
    (second_root / "scripts" / "config" / "issue_streams.yaml").write_text(
        "schema_version: issue-streams.v1\nstreams: {}\n",
        encoding="utf-8",
    )

    first_app = api_main.create_app(first_ctx, lifespan=no_lifespan)
    second_app = api_main.create_app(second_ctx, lifespan=no_lifespan)

    with TestClient(first_app) as first_client, TestClient(second_app) as second_client:
        # Session streams health
        first_health = first_client.get("/api/session-streams/v1/health").json()
        assert first_health["ok"] is True
        assert first_health["store"]["reachable"] is True
        assert "path" not in first_health["repo"]

        # Session current endpoint isolation
        first_session = first_client.get("/api/session/current")
        assert first_session.status_code == 200
        assert "First instance orchestrator state" in first_session.text
        assert "Second instance" not in first_session.text

        second_session = second_client.get("/api/session/current")
        assert second_session.status_code == 200
        assert "Second instance orchestrator state" in second_session.text
        assert "First instance" not in second_session.text

        # Rules endpoint isolation
        first_rules = first_client.get("/api/rules")
        assert first_rules.status_code == 200
        assert "First rule body" in first_rules.text
        assert "Second rule body" not in first_rules.text

        second_rules = second_client.get("/api/rules")
        assert second_rules.status_code == 200
        assert "Second rule body" in second_rules.text
        assert "First rule body" not in second_rules.text

        # Rollovers endpoint
        assert first_client.get("/api/rollovers").status_code == 200
        assert second_client.get("/api/rollovers").status_code == 200

    # Third uninitialized instance: missing DB must return 404 for status, digest, and drift
    third_root = tmp_path / "third"
    third_ctx = fixture_context(third_root)
    third_app = api_main.create_app(third_ctx, lifespan=no_lifespan)
    with TestClient(third_app) as third_client:
        assert (
            third_client.get("/api/session-streams/v1/status/epic:4707").status_code == 404
        )  # allow-hardcoded-epic: synthetic epic id for missing-DB 404 regression probe
        assert (
            third_client.get("/api/session-streams/v1/digest/epic:4707").status_code == 404
        )  # allow-hardcoded-epic: synthetic epic id for missing-DB 404 regression probe
        assert third_client.get("/api/session-streams/v1/drift").status_code == 404


def test_step2_state_router_cluster_isolation(tmp_path: Path) -> None:
    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    # Set up first isolated instance
    first_root = tmp_path / "first"
    first_ctx = fixture_context(first_root)
    (first_root / "curriculum" / "l2-uk-en" / "a1").mkdir(parents=True)
    (first_root / "curriculum" / "l2-uk-en" / "curriculum.yaml").write_text(
        "levels:\n  a1:\n    path: a1\n    modules:\n      - id: 01-first-slug\n        title: First Module\n",
        encoding="utf-8",
    )
    (first_root / "curriculum" / "l2-uk-en" / "a1" / "01-first-slug.md").write_text(
        "# First Content\n", encoding="utf-8"
    )

    # Set up second isolated instance
    second_root = tmp_path / "second"
    second_ctx = fixture_context(second_root)
    (second_root / "curriculum" / "l2-uk-en" / "a1").mkdir(parents=True)
    (second_root / "curriculum" / "l2-uk-en" / "curriculum.yaml").write_text(
        "levels:\n  a1:\n    path: a1\n    modules:\n      - id: 01-second-slug\n        title: Second Module\n",
        encoding="utf-8",
    )
    (second_root / "curriculum" / "l2-uk-en" / "a1" / "01-second-slug.md").write_text(
        "# Second Content\n", encoding="utf-8"
    )

    (first_root / "curriculum" / "l2-uk-en" / "plans" / "a1").mkdir(parents=True)
    (first_root / "curriculum" / "l2-uk-en" / "plans" / "a1" / "first-slug.yaml").write_text(
        "title: First Plan\nplan_fixes:\n  - fix 1\n", encoding="utf-8"
    )

    first_app = api_main.create_app(first_ctx, lifespan=no_lifespan)
    second_app = api_main.create_app(second_ctx, lifespan=no_lifespan)

    with TestClient(first_app) as first_client, TestClient(second_app) as second_client:
        # No fresh=true / no manual cache_invalidate: proves ctx-scoped keys.
        first_summary = first_client.get("/api/state/summary").json()
        second_summary = second_client.get("/api/state/summary").json()
        assert first_summary["tracks"]["a1"]["total"] == 1
        assert second_summary["tracks"]["a1"]["total"] == 1
        assert first_summary.get("meta", {}).get("cache") == "miss"
        assert second_summary.get("meta", {}).get("cache") == "miss"

        first_pipeline = first_client.get("/api/state/pipeline/a1").json()
        second_pipeline = second_client.get("/api/state/pipeline/a1").json()
        assert first_pipeline["modules"][0]["slug"] == "first-slug"
        assert second_pipeline["modules"][0]["slug"] == "second-slug"

        first_enrichment = first_client.get("/api/state/enrichment-status?track=a1").json()
        assert first_enrichment["tracks"]["a1"]["enriched"] == 1

        second_enrichment = second_client.get("/api/state/enrichment-status?track=a1").json()
        assert second_enrichment["tracks"]["a1"]["enriched"] == 0

        first_summary_hit = first_client.get("/api/state/summary").json()
        assert first_summary_hit.get("meta", {}).get("cache") == "hit"
        assert first_summary_hit["tracks"]["a1"]["total"] == 1

        first_manifest = first_client.get("/api/state/manifest").json()
        second_manifest = second_client.get("/api/state/manifest").json()
        assert "rules" in first_manifest
        assert "session" in second_manifest


def test_step8_admin_ops_git_cluster_isolation(tmp_path: Path) -> None:
    """Admin / ops / git-hygiene routes read only the app's MonitorContext."""

    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_ctx = fixture_context(first_root)
    second_ctx = fixture_context(second_root)

    first_backups = first_root / "data" / "backups"
    second_backups = second_root / "data" / "backups"
    first_backups.mkdir(parents=True)
    second_backups.mkdir(parents=True)
    (first_backups / "first.tar").write_bytes(b"first")
    (second_backups / "second.tar").write_bytes(b"second")

    first_plan = first_root / "batch_state" / "fleet-comms" / "retention"
    second_plan = second_root / "batch_state" / "fleet-comms" / "retention"
    first_plan.mkdir(parents=True)
    second_plan.mkdir(parents=True)
    (first_plan / "latest.json").write_text(
        json.dumps({"schema": "fleet-comms.retention.plan.v1", "marker": "first-plan"}),
        encoding="utf-8",
    )
    (second_plan / "latest.json").write_text(
        json.dumps({"schema": "fleet-comms.retention.plan.v1", "marker": "second-plan"}),
        encoding="utf-8",
    )

    first_app = api_main.create_app(first_ctx, lifespan=no_lifespan)
    second_app = api_main.create_app(second_ctx, lifespan=no_lifespan)

    with TestClient(first_app) as first_client, TestClient(second_app) as second_client:
        first_backups_body = first_client.get("/api/admin/backup/list").json()
        second_backups_body = second_client.get("/api/admin/backup/list").json()
        assert {item["filename"] for item in first_backups_body["backups"]} == {"first.tar"}
        assert {item["filename"] for item in second_backups_body["backups"]} == {"second.tar"}
        assert "first.tar" not in json.dumps(second_backups_body)
        assert "second.tar" not in json.dumps(first_backups_body)

        first_retention = first_client.get("/api/ops/v1/retention/latest").json()
        second_retention = second_client.get("/api/ops/v1/retention/latest").json()
        assert first_retention["marker"] == "first-plan"
        assert second_retention["marker"] == "second-plan"
        assert first_retention["missing"] is False
        assert second_retention["missing"] is False

        first_status = first_client.get("/api/ops/entire-context/status").json()
        second_status = second_client.get("/api/ops/entire-context/status").json()
        assert first_status["schema"] == "entire-context-monitor.v1"
        assert second_status["schema"] == "entire-context-monitor.v1"
        assert first_status["recall"]["available"] is False
        assert second_status["recall"]["available"] is False

        first_hygiene = first_client.get("/api/git/hygiene").json()
        second_hygiene = second_client.get("/api/git/hygiene").json()
        assert first_hygiene["dirty_total"] == 0
        assert second_hygiene["dirty_total"] == 0
        assert "error" in first_hygiene
        assert "error" in second_hygiene


def test_db_access_patterns_have_the_step_two_allowlist() -> None:
    assert len(DB_ACCESS_ALLOWLIST) == 16
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
