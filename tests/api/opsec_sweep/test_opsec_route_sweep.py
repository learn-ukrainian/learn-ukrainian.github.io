"""PR-tier route-wide OPSEC invariant for the Monitor API and dashboards."""

from __future__ import annotations

import asyncio
import fnmatch
import json
import os
import socket
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.requests import Request

from scripts.api import docs_router, opsec_scan, session_streams_router
from scripts.api import main as api_main
from scripts.fleet_comms import message_plane

from . import registry

pytestmark = pytest.mark.repo_invariant

KNOWN_LEAKS_PATH = Path(__file__).with_name("known_leaks.toml")
FROZEN_IDS = frozenset(
    {
        "admin-backup-dir",
        "comms-plane-status",
        "comms-plane-schema-db-path",
        "comms-plane-telemetry-path",
        "fleet-facade-db-paths",
        "fleet-facade-status",
        "fleet-facade-status-schema-db-path",
        "fleet-facade-status-telemetry-path",
        "fleet-broker-report-store-0",
        "fleet-broker-report-store-1",
        "fleet-workers-host-id",
        "occupancy-host-id",
        "retention-plan-dir",
        "retention-archive-root",
        "session-digest-detail",
        "session-health-repo-root",
        "session-health-db-path",
        "session-status-detail",
        "dashboard-index-localhost",
        "dashboard-work-loopback",
    }
)
PATH_CANARY = "opsec-fixture-canary"
HOST_ALIAS_CANARY = "opsec-host-alias"
HOST_ID_CANARY = "opsec-host-id"
MAX_SWEEP_SECONDS = 60.0


@dataclass(frozen=True)
class IsolatedFixture:
    root: Path
    canaries: tuple[str, ...]


def _request_scope(path: str = "/") -> dict[str, Any]:
    return {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": [],
        "server": ("testserver", 80),
        "client": ("testclient", 123),
        "root_path": "",
        "state": {},
    }


def _deny_subprocess(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("OPSEC sweep fixture forbids subprocess execution")


def _deny_network(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("OPSEC sweep fixture forbids network execution")


@pytest.fixture
def isolated_fixture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> IsolatedFixture:
    """Redirect existing API seams into a canary-planted disposable tree."""
    root = tmp_path / PATH_CANARY
    root.mkdir()
    for relative in ("batch_state", "stores", "curriculum", "dashboards", "data", "logs"):
        (root / relative).mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", f"{HOST_ALIAS_CANARY}={HOST_ID_CANARY}")
    monkeypatch.setenv("LU_MONITOR_HOST_ID", HOST_ID_CANARY)
    monkeypatch.setenv("AGENT_NO_TELEMETRY_FOOTER", "1")

    # All imported API modules use module-level Path seams. Repoint each
    # absolute path while retaining a recognizable canary in its parent.
    for module_name, module in tuple(sys.modules.items()):
        if not module_name.startswith("scripts.api") or module is None:
            continue
        for name, value in tuple(vars(module).items()):
            if not isinstance(value, Path) or not value.is_absolute():
                continue
            replacement = root / "seams" / module_name.replace(".", "_") / name.lower()
            replacement.parent.mkdir(parents=True, exist_ok=True)
            if value.is_dir() or value.suffix == "":
                replacement.mkdir(parents=True, exist_ok=True)
            monkeypatch.setattr(module, name, replacement)

        if "_run_command" in vars(module):
            monkeypatch.setattr(module, "_run_command", _deny_subprocess)

    monkeypatch.setattr(subprocess, "run", _deny_subprocess)
    monkeypatch.setattr(subprocess, "Popen", _deny_subprocess)
    monkeypatch.setattr(socket, "create_connection", _deny_network)
    monkeypatch.setattr(session_streams_router, "_repo_root", lambda: root)
    monkeypatch.setattr(
        session_streams_router,
        "_db_path",
        lambda: root / "stores" / "session-streams.sqlite3",
    )

    # These docs roots are derived once at import time rather than exposed as
    # individual Path globals. Rebuild the lookup tables so docs requests
    # cannot traverse back into the checkout.
    docs_root = root / "docs"
    audit_root = root / "audit"
    allowed_roots = {
        "audit": audit_root,
        "session-state": docs_root / "session-state",
        "handoffs": docs_root / "handoffs",
        "reports": docs_root / "reports",
        "architecture": docs_root / "architecture",
        "best-practices": docs_root / "best-practices",
        "decisions": docs_root / "decisions",
        "references": docs_root / "references" / "external",
        "proposals": docs_root / "proposals",
        "poc": docs_root / "poc",
    }
    for path in [*allowed_roots.values(), docs_root, audit_root]:
        path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(docs_router, "ALLOWED_ROOTS", allowed_roots)
    monkeypatch.setattr(docs_router, "DISCOVERY_ROOTS", (docs_root, audit_root))
    monkeypatch.setattr(docs_router, "EFFECTIVE_ROOTS", dict(allowed_roots))

    # Facade/status readers retain imported references to the resolver;
    # redirect every such reference and the resolver's own global into the
    # disposable tree instead of consulting the retired local plane.
    isolated_plane_root = root / "stores" / "fleet-comms"
    isolated_plane_root.mkdir(parents=True, exist_ok=True)
    def isolated_plane_resolver(repo_root: Path | None = None) -> Path:
        del repo_root
        return isolated_plane_root

    monkeypatch.setattr(message_plane, "default_plane_root", isolated_plane_resolver)
    for module_name, module in tuple(sys.modules.items()):
        if not module_name.startswith("scripts.api") or module is None:
            continue
        if "default_plane_root" in vars(module):
            monkeypatch.setattr(module, "default_plane_root", isolated_plane_resolver)

    for dashboards_dir in {api_main.DASHBOARDS_DIR, docs_router.DASHBOARDS_DIR}:
        dashboards_dir.mkdir(parents=True, exist_ok=True)
        for filename in ("index.html", "artifacts.html"):
            (dashboards_dir / filename).write_text(
                "<html><body>synthetic artifacts</body></html>\n", encoding="utf-8"
            )

    # The source and the injected seams must both carry the planted canary
    # before any response is considered safe to scan.
    assert root / "seams" / "scripts_api_main" / "project_root" == api_main.PROJECT_ROOT
    assert HOST_ALIAS_CANARY in os.environ["MONITOR_OCCUPANCY_HOST_IDS"]
    assert os.environ["LU_MONITOR_HOST_ID"] == HOST_ID_CANARY
    assert PATH_CANARY in str(api_main.PROJECT_ROOT.parent.parent.parent)
    assert PATH_CANARY in str(session_streams_router._repo_root())
    assert PATH_CANARY in str(session_streams_router._db_path())
    assert PATH_CANARY in str(docs_router.EFFECTIVE_ROOTS["audit"])
    assert PATH_CANARY in str(message_plane.default_plane_root())

    return IsolatedFixture(
        root=root,
        canaries=(PATH_CANARY, HOST_ALIAS_CANARY, HOST_ID_CANARY),
    )


def _load_known_leaks() -> list[dict[str, str]]:
    payload = tomllib.loads(KNOWN_LEAKS_PATH.read_text(encoding="utf-8"))
    rows = payload.get("known_leaks", [])
    assert isinstance(rows, list), "known_leaks.toml must contain [[known_leaks]] rows"
    return rows


def _matches(value: str, pattern: str) -> bool:
    """Match glob rows while preserving literal JSON path brackets."""
    return value == pattern or fnmatch.fnmatchcase(value, pattern)


def _validate_known_leaks(rows: list[dict[str, str]], findings: list[opsec_scan.Finding]) -> None:
    ids = [row.get("id") for row in rows]
    assert all(isinstance(row_id, str) and row_id for row_id in ids), "every known leak needs a non-empty id"
    assert len(ids) == len(set(ids)), "known leak ids must be unique"
    assert set(ids) <= FROZEN_IDS, "adding a known leak requires editing FROZEN_IDS in the same diff"

    matches: dict[str, list[opsec_scan.Finding]] = {row_id: [] for row_id in ids if row_id is not None}
    unmatched: list[opsec_scan.Finding] = []
    for finding in findings:
        row_matches = [
            row
            for row in rows
            if _matches(finding.operation, row.get("operation", ""))
            and _matches(finding.field_path, row.get("field", ""))
        ]
        if not row_matches:
            unmatched.append(finding)
            continue
        for row in row_matches:
            matches[row["id"]].append(finding)

    assert not unmatched, "unhandled OPSEC findings: " + json.dumps(
        [finding.as_dict() for finding in unmatched], sort_keys=True
    )
    dead = [row_id for row_id, row_findings in matches.items() if not row_findings]
    assert not dead, f"known leak rows no longer match findings: {sorted(dead)}"

    today = date.today()
    latest_allowed = today + timedelta(days=30)
    for row in rows:
        expiry = date.fromisoformat(row["expiry"])
        assert expiry > today, f"known leak row expired: {row['id']}"
        assert expiry <= latest_allowed, f"known leak expiry exceeds 30 days: {row['id']}"
        assert row.get("owner"), f"known leak row has no owner: {row['id']}"
        assert row.get("operation"), f"known leak row has no operation: {row['id']}"
        assert row.get("field"), f"known leak row has no field: {row['id']}"


def _path_for_record(record: registry.ExerciseRecord) -> str:
    path = record.path_template
    for name, value in record.path_params().items():
        path = path.replace("{" + name + "}", value)
    return path


def _response_payload(response: Any) -> Any:
    content_type = response.headers.get("content-type", "")
    if "json" in content_type:
        try:
            return response.json()
        except ValueError:
            pass
    try:
        return response.text
    except UnicodeDecodeError:
        return response.content


def _scan_response(record: registry.ExerciseRecord, response: Any, canaries: tuple[str, ...]) -> list[opsec_scan.Finding]:
    payload = _response_payload(response)
    return opsec_scan.scan_response(
        record.key,
        body=payload,
        headers=dict(response.headers),
        canaries=canaries,
    )


def test_route_registry_matches_openapi_and_classifies_every_operation() -> None:
    records = registry.build_registry(api_main.app)
    assert len(records) == registry.FROZEN_HTTP_OPERATION_COUNT + registry.FROZEN_WEBSOCKET_ROUTE_COUNT
    assert registry.unrecorded_operations(api_main.app, records) == []
    assert {record.classification for record in records} >= {"read", "mutation", "stream"}
    by_key = {record.key: record for record in records}
    assert by_key["GET /api/session-streams/v1/drift"].query["dry_run"] == "true"
    assert by_key["POST /api/comms/send"].expected_statuses == (410,)
    assert by_key["POST /api/comms/send"].body() is not None
    for record in records:
        if record.fixture == "skip":
            assert record.owner and record.reason and record.expiry


def test_registry_reports_a_removed_operation() -> None:
    records = registry.build_registry(api_main.app)
    missing = registry.unrecorded_operations(api_main.app, records[:-1])
    assert missing == [records[-1].key]


def test_known_leak_table_rejects_unmatched_dead_and_expired_rows() -> None:
    row = {
        "id": "admin-backup-dir",
        "operation": "GET /synthetic",
        "field": "body.value",
        "owner": "test-owner",
        "expiry": "2026-09-23",
    }
    finding = opsec_scan.Finding(
        operation="GET /other",
        field_path="body.value",
        kind="canary",
        token="synthetic",
        start=0,
        end=9,
    )
    with pytest.raises(AssertionError, match="unhandled OPSEC findings"):
        _validate_known_leaks([row], [finding])
    with pytest.raises(AssertionError, match="no longer match"):
        _validate_known_leaks([row], [])

    expired = dict(row)
    expired.update(
        operation="GET /api/admin/backup/list",
        field="body.backup_dir",
        expiry=(date.today() - timedelta(days=1)).isoformat(),
    )
    matching = opsec_scan.Finding(
        operation="GET /api/admin/backup/list",
        field_path="body.backup_dir",
        kind="canary",
        token="synthetic",
        start=0,
        end=9,
    )
    with pytest.raises(AssertionError, match="expired"):
        _validate_known_leaks([expired], [matching])


def test_isolated_fixture_denies_network_and_subprocess(isolated_fixture: IsolatedFixture) -> None:
    del isolated_fixture
    with pytest.raises(AssertionError, match="forbids subprocess"):
        subprocess.run(["git", "status"], timeout=1)
    with pytest.raises(AssertionError, match="forbids subprocess"):
        subprocess.Popen(["git", "status"])
    with pytest.raises(AssertionError, match="forbids network"):
        socket.create_connection(("127.0.0.1", 8765))


def test_opsec_route_sweep_isolated_and_bounded(isolated_fixture: IsolatedFixture) -> None:
    started = time.perf_counter()
    records = registry.build_registry(api_main.app)
    client = TestClient(api_main.app, raise_server_exceptions=False)
    findings: list[opsec_scan.Finding] = []
    failures: list[str] = []

    for record in records:
        if record.fixture == "skip":
            continue
        if record.method == "WEBSOCKET":
            try:
                with client.websocket_connect(_path_for_record(record)) as websocket:
                    payload = websocket.receive_json()
                    findings.extend(
                        opsec_scan.scan_response(
                            record.key,
                            body=payload,
                            headers=dict(websocket.extra_headers),
                            canaries=isolated_fixture.canaries,
                        )
                    )
            except Exception as exc:
                failures.append(f"{record.key} error={type(exc).__name__}")
            continue

        path = _path_for_record(record)
        body = record.body()
        response = client.request(
            record.method,
            path,
            params=dict(record.query),
            headers=dict(record.headers),
            json=body if record.body_factory is not None else None,
        )
        if record.expected_statuses and response.status_code not in record.expected_statuses:
            failures.append(f"{record.key} status={response.status_code}")
        findings.extend(_scan_response(record, response, isolated_fixture.canaries))

    dashboard_root = Path(__file__).resolve().parents[3] / "dashboards"
    for dashboard in sorted(path for path in dashboard_root.rglob("*") if path.is_file()):
        relative = dashboard.relative_to(dashboard_root).as_posix()
        findings.extend(
            opsec_scan.scan_response(
                f"dashboard:{relative}",
                body=dashboard.read_text(encoding="utf-8"),
                headers={},
                canaries=isolated_fixture.canaries,
            )
        )

    elapsed = time.perf_counter() - started
    assert elapsed < MAX_SWEEP_SECONDS, f"OPSEC route sweep exceeded {MAX_SWEEP_SECONDS:.0f}s: {elapsed:.2f}s"
    assert not failures, "exercised route failures: " + ", ".join(sorted(failures))
    _validate_known_leaks(_load_known_leaks(), findings)

    print(
        "opsec sweep: "
        f"records={len(records)} dashboards={len(list(dashboard_root.rglob('*')))} "
        f"findings={len(findings)} known_leaks={len(_load_known_leaks())} elapsed_s={elapsed:.2f}"
    )


def test_error_handlers_do_not_echo_raw_exception_text() -> None:
    raw = "/Users/private/opsec-secret/traceback-value"
    request = Request(_request_scope("/api/opsec-error"))
    server_error = asyncio.run(api_main.global_exception_handler(request, RuntimeError(raw)))
    body = json.loads(server_error.body)
    assert server_error.status_code == 500
    assert body["error"] == "internal_server_error"
    assert body["detail"] == "internal server error"
    assert body["error_id"]
    assert raw not in server_error.body.decode()

    client_error = asyncio.run(
        api_main.http_exception_handler(
            request,
            HTTPException(status_code=400, detail="safe validation message"),
        )
    )
    body = json.loads(client_error.body)
    assert client_error.status_code == 400
    assert body == {
        "error": "http_error",
        "error_id": body["error_id"],
        "detail": "safe validation message",
    }


def test_error_handler_redacts_exception_shaped_http_details() -> None:
    request = Request(_request_scope("/api/opsec-error"))
    response = asyncio.run(
        api_main.http_exception_handler(
            request,
            HTTPException(status_code=500, detail="status_failed: /tmp/opsec-fixture-canary"),
        )
    )
    body = json.loads(response.body)
    assert response.status_code == 500
    assert body["detail"] == "request rejected"
    assert "opsec-fixture-canary" not in response.body.decode()


def test_validation_handler_drops_submitted_values_and_context() -> None:
    request = Request(_request_scope("/api/opsec-validation"))
    error = RequestValidationError(
        [
            {
                "type": "value_error",
                "loc": ("body", "path"),
                "msg": "Value error, /tmp/opsec-fixture-canary",
                "input": "/Users/private/submitted-value",
                "ctx": {"error": ValueError("/Users/private/raw-error")},
            }
        ]
    )
    response = asyncio.run(api_main.request_validation_exception_handler(request, error))
    body = json.loads(response.body)
    assert response.status_code == 422
    assert body["error"] == "validation_error"
    assert body["detail"][0]["msg"] == "request rejected"
    assert "input" not in body["detail"][0]
    assert "ctx" not in body["detail"][0]
    assert "opsec-fixture-canary" not in response.body.decode()
