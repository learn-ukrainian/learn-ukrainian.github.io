"""Tests for process-wide playground API resilience controls."""

from __future__ import annotations

import asyncio
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.main import app as playground_app
from scripts.api.resilience import (
    connect_sqlite,
    get_resilience_snapshot,
    reset_resilience_stats_for_tests,
    resilience_middleware,
)

ROOT = Path(__file__).resolve().parents[1]


def _test_app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(resilience_middleware)
    return app


def test_request_timeout_returns_504(monkeypatch):
    reset_resilience_stats_for_tests()
    monkeypatch.setenv("API_REQUEST_TIMEOUT_S", "0.05")
    monkeypatch.setenv("API_MAX_CONCURRENCY", "4")

    app = _test_app()

    @app.get("/slow")
    async def slow():
        await asyncio.sleep(0.2)
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/slow")

    assert response.status_code == 504
    assert response.json()["error"] == "request_timeout"
    assert get_resilience_snapshot()["timeout_count"] == 1


def test_concurrency_limiter_returns_503_with_retry_after(monkeypatch):
    reset_resilience_stats_for_tests()
    monkeypatch.setenv("API_REQUEST_TIMEOUT_S", "2")
    monkeypatch.setenv("API_MAX_CONCURRENCY", "1")

    entered = threading.Event()
    release = threading.Event()
    app = _test_app()

    @app.get("/hold")
    async def hold():
        entered.set()
        await asyncio.to_thread(release.wait, 1)
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=False)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(client.get, "/hold")
        assert entered.wait(1)
        saturated = client.get("/hold")
        release.set()
        assert first.result(timeout=2).status_code == 200

    assert saturated.status_code == 503
    assert saturated.headers["Retry-After"] == "1"
    assert saturated.json()["error"] == "server_saturated"
    assert get_resilience_snapshot()["saturated_count"] == 1


def test_slow_request_and_sql_events_surface_in_health(monkeypatch, tmp_path):
    reset_resilience_stats_for_tests()
    monkeypatch.setenv("API_SLOW_REQUEST_MS", "0")
    monkeypatch.setenv("API_SLOW_SQL_MS", "0")

    db_path = tmp_path / "timed.db"
    conn = connect_sqlite(str(db_path))
    conn.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO sample DEFAULT VALUES")
    conn.commit()
    conn.close()

    client = TestClient(playground_app, raise_server_exceptions=False)
    assert client.get("/api/health").status_code == 200
    response = client.get("/api/health")
    assert response.status_code == 200

    resilience = response.json()["resilience"]
    assert resilience["recent_slow_requests"]
    assert resilience["recent_slow_sql"]
    assert "CREATE TABLE sample" in resilience["recent_slow_sql"][0]["query"]


def test_slow_sql_caller_never_exposes_absolute_filesystem_root(monkeypatch, tmp_path):
    """``recent_slow_sql[*].caller`` is published on /api/health, so it must
    be repo-relative (or a bare basename) — never an absolute host path."""
    reset_resilience_stats_for_tests()
    monkeypatch.setenv("API_SLOW_SQL_MS", "0")

    db_path = tmp_path / "timed.db"
    conn = connect_sqlite(str(db_path))
    conn.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
    conn.close()

    snapshot = get_resilience_snapshot()
    callers = [event["caller"] for event in snapshot["recent_slow_sql"]]
    assert callers
    for caller in callers:
        assert not caller.startswith("/"), caller
        assert "/home/" not in caller
        assert "/Users/" not in caller
    assert any(caller.startswith("tests/test_api_resilience.py:") for caller in callers)


def test_normal_api_launch_uses_uvicorn_with_reload():
    """package.json scripts.api / scripts.api:bg launch uvicorn in dev-reload mode.

    Pinned 2026-05-10 after commit 6d81e694b1 ("api auto-reload"). The previous
    contract (--workers 2 --limit-concurrency 32 --timeout-keep-alive 5) was a
    production-style launcher; the project does not run a production API and
    has standardized on --reload for the localhost:8765 dev server.
    """
    scripts = json.loads((ROOT / "package.json").read_text())["scripts"]

    for name in ("api", "api:bg"):
        command = scripts[name]
        assert ".venv/bin/python -m uvicorn" in command
        assert "scripts.api.main:app" in command
        assert "--host 127.0.0.1" in command
        assert "--port 8765" in command
        assert "--reload" in command
        assert "--log-config scripts/api/logging.json" in command

    # api:reload is now an alias of api (legacy name preserved for muscle memory).
    assert scripts["api:reload"] == "npm run api"


def test_services_sh_loopback_bind_and_match_contract():
    """services.sh api/sources must bind loopback and keep SVC_MATCH aligned with argv."""
    content = (ROOT / "services.sh").read_text(encoding="utf-8")

    def _field(name: str) -> str:
        escaped = re.escape(name)
        match = re.search(rf'{escaped}="([^"]+)"', content)
        assert match is not None, f"missing {name} in services.sh"
        return match.group(1)

    api_cmd = _field("SVC_CMD[api]")
    api_match = _field("SVC_MATCH[api]")
    sources_cmd = _field("SVC_CMD[sources]")
    sources_match = _field("SVC_MATCH[sources]")

    assert "SVC_HOST[api]=127.0.0.1" in content
    assert "SVC_HOST[sources]=127.0.0.1" in content
    assert "--host 127.0.0.1" in api_cmd
    assert "--host 127.0.0.1 --port 8766" in sources_cmd
    assert "0.0.0.0" not in api_cmd
    assert "0.0.0.0" not in sources_cmd
    assert api_match in api_cmd
    assert sources_match in sources_cmd
