"""Step-0 structural and context tests for the Monitor API app factory."""

from __future__ import annotations

import sqlite3
import subprocess
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.exception_handlers import websocket_request_validation_exception_handler
from fastapi.exceptions import RequestValidationError, WebSocketRequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from scripts.api import dashboard_comms
from scripts.api import main as api_main
from scripts.api.monitor_context import fixture_context, production_context
from scripts.api.opsec_sanitize import REDACTED_ABSOLUTE_PATH, opsec_path_sanitizer_middleware
from scripts.api.resilience import TimedSQLiteConnection, resilience_middleware

pytestmark = [pytest.mark.repo_invariant, pytest.mark.reads_content]

REPO_ROOT = Path(__file__).resolve().parents[2]
def test_factory_snapshot_preserves_middleware_and_exception_handlers() -> None:
    app = api_main.create_app(production_context())

    assert [(entry.cls, entry.args) for entry in app.user_middleware] == [
        (BaseHTTPMiddleware, ()),
        (BaseHTTPMiddleware, ()),
        (CORSMiddleware, ()),
    ]
    assert app.user_middleware[0].kwargs["dispatch"] is opsec_path_sanitizer_middleware
    assert app.user_middleware[1].kwargs["dispatch"] is resilience_middleware
    assert app.user_middleware[2].kwargs == {
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
    assert context.stores.work_in_flight == {}
    assert context.stores.work_in_flight is not production_context().stores.work_in_flight

    outside = tmp_path.parent / "monitor-context-outside"
    outside.mkdir()
    escaped = tmp_path / "escaped"
    escaped.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes"):
        context._open_db(escaped / "messages.sqlite3")


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
    (first_root / "agents_extensions" / "shared" / "rules" / "core.md").write_text(
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
    (second_root / "agents_extensions" / "shared" / "rules" / "core.md").write_text(
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


def _seed_sources_db(path: Path, *, rows: int) -> None:
    import sqlite3

    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, text TEXT)")
    connection.executemany("INSERT INTO textbooks (text) VALUES (?)", [("chunk",)] * rows)
    connection.commit()
    connection.close()


def _write_textbook_png(root: Path, *, grade: str, name: str) -> None:
    directory = root / "data" / "textbook_images" / grade
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(b"\x89PNG" + b"\x00" * 8)


def test_step10_sources_router_cluster_isolation(tmp_path: Path) -> None:
    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_ctx = fixture_context(first_root)
    second_ctx = fixture_context(second_root)

    _write_textbook_png(first_root, grade="grade-01", name="first.png")
    _write_textbook_png(second_root, grade="grade-02", name="second.png")
    _seed_sources_db(first_ctx.roots.sources_db_path, rows=3)
    _seed_sources_db(second_ctx.roots.sources_db_path, rows=7)

    first_app = api_main.create_app(first_ctx, lifespan=no_lifespan)
    second_app = api_main.create_app(second_ctx, lifespan=no_lifespan)

    with TestClient(first_app) as first_client, TestClient(second_app) as second_client:
        first_browse = first_client.get("/api/sources/browse_images").json()
        second_browse = second_client.get("/api/sources/browse_images").json()
        assert first_browse["total"] == 1
        assert first_browse["images"][0]["name"] == "first.png"
        assert first_browse["images"][0]["grade"] == "grade-01"
        assert second_browse["total"] == 1
        assert second_browse["images"][0]["name"] == "second.png"
        assert second_browse["images"][0]["grade"] == "grade-02"
        assert first_browse["images"][0]["name"] not in {
            image["name"] for image in second_browse["images"]
        }

        first_stats = first_client.get("/api/sources/stats").json()
        second_stats = second_client.get("/api/sources/stats").json()
        assert first_stats["sources_db"]["status"] == "ok"
        assert second_stats["sources_db"]["status"] == "ok"
        assert first_stats["sources_db"]["points_count"] == 3
        assert second_stats["sources_db"]["points_count"] == 7
        assert first_stats["sources_db"]["tables"]["textbooks"] == 3
        assert second_stats["sources_db"]["tables"]["textbooks"] == 7

        assert first_client.get("/api/rag/stats").status_code == 404


def test_step12d_site_wiki_worktrees_telemetry_isolation(tmp_path: Path) -> None:
    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_ctx = fixture_context(first_root)
    second_ctx = fixture_context(second_root)

    first_dist = first_root / "site" / "dist"
    second_dist = second_root / "site" / "dist"
    first_dist.mkdir(parents=True)
    second_dist.mkdir(parents=True)
    (first_dist / "sitemap-index.xml").write_text("<first/>", encoding="utf-8")
    (second_dist / "sitemap-index.xml").write_text("<second/>", encoding="utf-8")

    for root, ctx in ((first_root, first_ctx), (second_root, second_ctx)):
        ctx.roots.sources_db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(ctx.roots.sources_db_path)) as conn:
            conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY)")
            count = 1 if root is first_root else 2
            conn.executemany("INSERT INTO textbooks DEFAULT VALUES", [()] * count)
            conn.commit()
        subprocess.run(
            ["git", "init", "--quiet", "-b", "main"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )

    first_app = api_main.create_app(first_ctx, lifespan=no_lifespan)
    second_app = api_main.create_app(second_ctx, lifespan=no_lifespan)

    with TestClient(first_app) as first_client, TestClient(second_app) as second_client:
        first_site = first_client.get("/api/site/health").json()
        second_site = second_client.get("/api/site/health").json()
        assert first_site["last_astro_build"]["built"] is True
        assert second_site["last_astro_build"]["built"] is True
        assert first_site["sitemap"]["path"] == "site/dist/sitemap-index.xml"
        assert second_site["sitemap"]["path"] == "site/dist/sitemap-index.xml"
        assert first_site["sitemap"]["path"] == second_site["sitemap"]["path"]

        first_sources = first_client.get("/api/wiki/sources").json()
        second_sources = second_client.get("/api/wiki/sources").json()
        assert first_sources["total_entries"] == 1
        assert second_sources["total_entries"] == 2

        first_timing = first_client.post(
            "/api/telemetry/tool-timings",
            json={
                "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "tool_name": "Bash",
                "duration_ms": 10,
            },
        )
        assert first_timing.status_code == 200
        assert first_client.get("/api/telemetry/tool-timings?window=24h").json()[0]["count"] == 1
        assert second_client.get("/api/telemetry/tool-timings?window=24h").json() == []

        first_worktrees = first_client.get("/api/worktrees").json()
        second_worktrees = second_client.get("/api/worktrees").json()
        assert first_worktrees["count"] == 1
        assert second_worktrees["count"] == 1
        assert first_worktrees["worktrees"][0]["is_primary"] is True
        assert second_worktrees["worktrees"][0]["is_primary"] is True
        assert first_worktrees["worktrees"][0]["path"] == REDACTED_ABSOLUTE_PATH
        assert second_worktrees["worktrees"][0]["path"] == REDACTED_ABSOLUTE_PATH


def test_step12e_work_epics_cluster_isolation(tmp_path: Path) -> None:
    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    def _plant(root: Path, stream_id: str, epic: int, title: str) -> None:
        config = root / "scripts" / "config"
        config.mkdir(parents=True)
        (config / "issue_streams.yaml").write_text(
            "schema_version: 1\n"
            "streams:\n"
            f"  {stream_id}:\n"
            f"    title: {title}\n"
            f"    epics: [{epic}]\n",
            encoding="utf-8",
        )

    first_stream, first_epic = "first-area", 1001
    second_stream, second_epic = "second-area", 2002
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    _plant(first_root, first_stream, first_epic, "First Area")
    _plant(second_root, second_stream, second_epic, "Second Area")

    first_ctx = fixture_context(first_root)
    second_ctx = fixture_context(second_root)
    api_main.seed_manifest_inventory(
        first_root, store=first_ctx.stores.epics_store, handoff_root=first_root
    )
    api_main.seed_manifest_inventory(
        second_root, store=second_ctx.stores.epics_store, handoff_root=second_root
    )
    assert first_ctx.stores.work_in_flight is not None
    assert second_ctx.stores.work_in_flight is not None
    first_ctx.stores.work_in_flight["first-only"] = "sentinel"
    assert "first-only" not in second_ctx.stores.work_in_flight

    first_app = api_main.create_app(first_ctx, lifespan=no_lifespan)
    second_app = api_main.create_app(second_ctx, lifespan=no_lifespan)

    with TestClient(first_app) as first_client, TestClient(second_app) as second_client:
        first_health = first_client.get("/api/epics/v1/health").json()
        second_health = second_client.get("/api/epics/v1/health").json()
        assert first_health["ok"] is True
        assert second_health["ok"] is True
        assert "path" not in first_health
        assert "path" not in second_health

        first_ids = {row["stream_id"] for row in first_client.get("/api/epics/v1").json()["streams"]}
        second_ids = {row["stream_id"] for row in second_client.get("/api/epics/v1").json()["streams"]}
        assert f"epic:{first_epic}" in first_ids  # allow-hardcoded-epic: isolated fixture stream
        assert f"epic:{second_epic}" not in first_ids  # allow-hardcoded-epic: isolated fixture stream
        assert f"epic:{second_epic}" in second_ids  # allow-hardcoded-epic: isolated fixture stream
        assert f"epic:{first_epic}" not in second_ids  # allow-hardcoded-epic: isolated fixture stream

        first_areas = {area["id"] for area in first_client.get("/api/epics/graph/v1").json()["nodes"]["areas"]}
        second_areas = {area["id"] for area in second_client.get("/api/epics/graph/v1").json()["nodes"]["areas"]}
        assert f"area:{first_stream}" in first_areas
        assert f"area:{second_stream}" not in first_areas
        assert f"area:{second_stream}" in second_areas
        assert f"area:{first_stream}" not in second_areas

        assert first_client.get("/api/work/v1/health").json()["ok"] is True
        assert second_client.get("/api/work/v1/health").json()["ok"] is True
        assert first_client.get("/api/work/v1/capabilities").json()["mutation"] is False


def test_broker_reads_use_guarded_timed_readonly_context(tmp_path: Path) -> None:
    context = fixture_context(tmp_path / "fixture")
    handle = context.stores.message_db
    assert handle is not None
    handle.path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(handle.path) as conn:
        conn.execute("CREATE TABLE messages (body TEXT)")
        conn.execute("INSERT INTO messages VALUES ('fixture message')")
    conn = dashboard_comms.get_broker_db(context)
    try:
        assert isinstance(conn, TimedSQLiteConnection)
        assert conn.row_factory is sqlite3.Row
        assert conn.execute("SELECT body FROM messages").fetchone()["body"] == "fixture message"
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("INSERT INTO messages VALUES ('forbidden')")
    finally:
        conn.close()

    outside = tmp_path / "outside.sqlite"
    with sqlite3.connect(outside) as conn:
        conn.execute("CREATE TABLE messages (body TEXT)")
    context = replace(context, stores=replace(context.stores, message_db=replace(handle, path=outside)))
    with pytest.raises(ValueError, match="escapes"):
        dashboard_comms.get_broker_db(context)
