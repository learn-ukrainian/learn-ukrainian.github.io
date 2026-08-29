"""Tests for per-host project state routes and drift semantics (#7188)."""

from __future__ import annotations

import json
import re
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from scripts.api import project_state_router as router_mod
from scripts.api.main import app
from scripts.api.project_state_store import REPORT_TTL_SECONDS, reset_project_state_store, upsert_report
from tests.api.test_project_state_collect import _init_repo

loop_client = TestClient(
    app,
    base_url="http://127.0.0.1",
    client=("127.0.0.1", 50000),
    raise_server_exceptions=False,
)
client = TestClient(app, raise_server_exceptions=False)

_PLACEHOLDER_MAP = "teach-box=host-teacher,job-box=host-job"
_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_ALIAS_LEAKS = ("atlas-runner", "hramatka", "vps")

SHA_MAIN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SHA_OLD = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
SHA_HEAD = "cccccccccccccccccccccccccccccccccccccccc"


def _primary(
    *,
    origin_main_sha: str = SHA_MAIN,
    head_sha: str = SHA_HEAD,
    origin_main_age_s: float = 120.0,
    dirty_count: int = 0,
) -> dict[str, Any]:
    return {
        "head_sha": head_sha,
        "origin_main_sha": origin_main_sha,
        "origin_main_age_s": origin_main_age_s,
        "ahead": 1,
        "behind": 0,
        "dirty_count": dirty_count,
    }


def _service(
    name: str,
    *,
    state: str = "running",
    repo: str = "learn-ukrainian",
    serving_mode: str = "release",
    serving_sha: str | None = SHA_MAIN,
    checkout_sha: str | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "state": state,
        "repo": repo,
        "serving_mode": serving_mode,
        "serving_sha": serving_sha,
        "checkout_sha": checkout_sha,
    }


def _document(
    host_id: str = "host-job",
    *,
    primary: dict[str, Any] | None = None,
    services: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "host_id": host_id,
        "primary": primary or _primary(),
        "worktrees": {"count": 2},
        "services": services or [_service("api")],
        "collected_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


@pytest.fixture(autouse=True)
def _clear_store() -> None:
    reset_project_state_store()
    router_mod.reset_local_document_cache()
    yield
    reset_project_state_store()
    router_mod.reset_local_document_cache()


def _post_report(document: dict[str, Any]) -> Any:
    return loop_client.post("/api/fleet/projects/v1/report", json=document)


def test_get_projects_schema_and_unknown_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MONITOR_OCCUPANCY_HOST_IDS", raising=False)
    monkeypatch.setattr(router_mod, "_self_host_ids", lambda: set())
    response = client.get("/api/fleet/projects/v1?host_id=host-job")
    assert response.status_code == 200
    data = response.json()
    assert data["schema"] == "monitor-project-state.v1"
    host = data["hosts"]["host-job"]
    assert host["freshness"] == "unknown"
    assert host["primary"] is None
    assert host["services"] == []


def test_post_report_loopback_and_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    posted = _post_report(_document())
    assert posted.status_code == 200
    remote = client.post("/api/fleet/projects/v1/report", json=_document())
    assert remote.status_code == 403

    monkeypatch.setattr(router_mod, "_self_host_ids", lambda: set())
    live = client.get("/api/fleet/projects/v1?host_id=host-job").json()["hosts"]["host-job"]
    assert live["freshness"] == "fresh"
    assert live["services"][0]["drift"] is False

    upsert_report(
        _document(),
        now_mono=time.monotonic() - REPORT_TTL_SECONDS - 1,
    )
    expired = client.get("/api/fleet/projects/v1?host_id=host-job").json()["hosts"]["host-job"]
    assert expired["freshness"] == "unknown"


def test_drift_matrix_release_behind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setattr(router_mod, "_self_host_ids", lambda: set())
    doc = _document(services=[_service("api", serving_sha=SHA_OLD)])
    _post_report(doc)
    host = client.get("/api/fleet/projects/v1?host_id=host-job").json()["hosts"]["host-job"]
    assert host["services"][0]["drift"] is True
    assert "drift:api" in host["attention"]


def test_drift_matrix_checkout_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setattr(router_mod, "_self_host_ids", lambda: set())
    doc = _document(
        services=[
            _service(
                "sources",
                serving_mode="checkout",
                serving_sha=None,
                checkout_sha=SHA_OLD,
            )
        ]
    )
    _post_report(doc)
    service = client.get("/api/fleet/projects/v1?host_id=host-job").json()["hosts"]["host-job"]["services"][0]
    assert service["serving_mode"] == "checkout"
    assert service["drift"] is True


def test_drift_matrix_stopped_and_sibling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setattr(router_mod, "_self_host_ids", lambda: set())
    doc = _document(
        services=[
            _service("api", state="stopped", serving_sha=None),
            _service("work", repo="sibling", serving_mode="checkout", checkout_sha=SHA_OLD),
        ]
    )
    _post_report(doc)
    services = client.get("/api/fleet/projects/v1?host_id=host-job").json()["hosts"]["host-job"]["services"]
    assert services[0]["drift"] == "unknown"
    assert services[1]["drift"] == "not_applicable"


def test_drift_matrix_stale_upstream(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setattr(router_mod, "_self_host_ids", lambda: set())
    doc = _document(
        primary=_primary(origin_main_age_s=4000.0),
        services=[_service("api", serving_sha=SHA_OLD)],
    )
    _post_report(doc)
    host = client.get("/api/fleet/projects/v1?host_id=host-job").json()["hosts"]["host-job"]
    assert host["services"][0]["drift"] == "unknown"
    assert "stale_upstream" in host["attention"]


def test_report_validation_rejects_forbidden_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    assert _post_report({**_document(), "host_id": "10.0.0.1"}).status_code == 400
    assert _post_report({**_document(), "host_id": "atlas-runner"}).status_code == 400
    bad_doc = _document()
    bad_doc["services"] = [
        {
            "name": "api",
            "state": "running",
            "repo": "learn-ukrainian",
            "serving_mode": "release",
            "serving_sha": "/Users/foo/aaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "checkout_sha": None,
        }
    ]
    assert _post_report(bad_doc).status_code == 400


def test_projects_opsec_no_paths_or_hostnames(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setattr(router_mod, "_self_host_ids", lambda: set())
    _post_report(_document())
    text = json.dumps(client.get("/api/fleet/projects/v1").json()).lower()
    assert _IP.findall(text) == []
    for alias in _ALIAS_LEAKS:
        assert alias not in text
    assert "/users/" not in text


def test_health_serving_fields_and_opaque_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LU_MONITOR_HOST_ID", "host-job")
    data = client.get("/api/health").json()["instance"]
    assert data["host"] == "host-job"
    assert data["checkout_sha"] == data["git_sha"]
    assert data["serving_mode"] in {"release", "checkout"}
    hostname = __import__("socket").gethostname()
    assert data["host"] != hostname


def test_health_release_fixture(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    from dataclasses import replace
    release_sha = SHA_MAIN
    release_dir = tmp_path / ".runtime" / "api" / "releases" / release_sha
    release_dir.mkdir(parents=True)
    (release_dir / ".release-manifest.json").write_text(
        json.dumps({"sha": release_sha, "tree_sha256": "a" * 64}),
        encoding="utf-8",
    )
    base_ctx = app.state.ctx
    patched_ctx = replace(
        base_ctx,
        roots=replace(base_ctx.roots, project_root=release_dir),
    )
    monkeypatch.setattr(app.state, "ctx", patched_ctx)
    monkeypatch.setenv("LU_MONITOR_HOST_ID", "host-job")
    instance = client.get("/api/health").json()["instance"]
    assert instance["serving_mode"] == "release"
    assert instance["serving_sha"] == release_sha


def test_in_process_self_host_is_fresh(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setenv("LU_MONITOR_HOST_ID", "host-job")
    monkeypatch.setattr(router_mod, "_live_local_document", lambda host_id: _document(host_id))
    host = client.get("/api/fleet/projects/v1?host_id=host-job").json()["hosts"]["host-job"]
    assert host["freshness"] == "fresh"
    assert host["age_s"] == 0.0


def test_self_report_cache_is_shared_by_project_and_worker_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setenv("LU_MONITOR_HOST_ID", "host-job")
    document = _document("host-job")
    calls = 0

    def collect(host_id: str) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        assert host_id == "host-job"
        return document

    monkeypatch.setattr(router_mod, "collect_local_document", collect)
    monkeypatch.setattr("scripts.api.fleet_workers_collect._self_host_ids", lambda: {"host-job"})
    monkeypatch.setattr("scripts.api.fleet_workers_collect.collect_driver_workers", lambda **_: ([], []))
    monkeypatch.setattr("scripts.api.fleet_workers_collect.collect_delegate_workers", lambda *_, **__: [])
    monkeypatch.setattr("scripts.api.fleet_workers_collect.collect_job_workers", lambda **_: ([], None))
    monkeypatch.setattr("scripts.api.fleet_workers_collect.collect_marker_workers", lambda **_: [])

    project = client.get("/api/fleet/projects/v1?host_id=host-job")
    workers = client.get("/api/fleet/workers/v1?host_id=host-job")

    assert project.status_code == 200
    assert workers.status_code == 200
    assert calls == 1
    project_host = project.json()["hosts"]["host-job"]
    worker_host = workers.json()["hosts"][0]
    assert project_host["freshness"] == "fresh"
    assert project_host["age_s"] <= 1.0
    assert worker_host["freshness"] == "fresh"
    assert worker_host["age_s"] <= 1.0


def test_self_report_cache_serves_stale_while_refreshing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setenv("LU_MONITOR_HOST_ID", "host-job")
    document = _document("host-job")
    calls = 0
    refresh_started = threading.Event()
    release_refresh = threading.Event()

    def collect(_host_id: str) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return document
        refresh_started.set()
        release_refresh.wait(timeout=2.0)
        return {**document, "collected_at": datetime.now(UTC).isoformat().replace("+00:00", "Z")}

    monkeypatch.setattr(router_mod, "collect_local_document", collect)
    first = router_mod.get_cached_local_document("host-job")
    assert first.document is document
    cached_entry = router_mod._LOCAL_DOCUMENT_CACHE["host-job"]
    router_mod._LOCAL_DOCUMENT_CACHE["host-job"] = router_mod._LocalDocumentCacheEntry(
        document,
        cached_entry.stored_at_mono - router_mod.LOCAL_DOCUMENT_FRESH_S - 1.0,
    )

    try:
        stale = router_mod.get_cached_local_document("host-job")
        assert refresh_started.wait(timeout=1.0)
        assert stale.document is document
        assert stale.freshness == "stale"
        assert stale.age_s is not None and stale.age_s > router_mod.LOCAL_DOCUMENT_FRESH_S
        assert calls == 2
    finally:
        release_refresh.set()


def test_self_host_live_collection_unmocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_repo = _init_repo(tmp_path)
    monkeypatch.chdir(fixture_repo)
    monkeypatch.setenv("LU_MONITOR_HOST_ID", "mac-operator")
    monkeypatch.delenv("MONITOR_OCCUPANCY_HOST_IDS", raising=False)

    response = client.get("/api/fleet/projects/v1?host_id=mac-operator")
    assert response.status_code == 200
    data = response.json()
    assert data["schema"] == "monitor-project-state.v1"
    host = data["hosts"]["mac-operator"]
    assert host["freshness"] == "fresh"
    assert host["age_s"] == 0.0
    assert host["primary"] is not None
    assert len(host["primary"]["head_sha"]) == 40
    assert host["worktrees"]["count"] >= 1
    assert len(host["services"]) == 4
    assert {service["name"] for service in host["services"]} == {"sources", "api", "astro", "work"}


def test_projects_route_contract_registered() -> None:
    from scripts.api.route_contracts import contract_for_route

    get_contract = contract_for_route("/api/fleet/projects/v1", "http")
    post_contract = contract_for_route("/api/fleet/projects/v1/report", "http")
    assert get_contract is not None
    assert post_contract is not None
    assert post_contract.mutates is True
