"""PR-tier route-wide OPSEC invariant for the Monitor API and dashboards."""

from __future__ import annotations

import asyncio
import fnmatch
import importlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.requests import Request

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api import (
    docs_router,
    entire_context_router,
    epics_router,
    fleet_router,
    git_hygiene_router,
    governance_router,
    images_router,
    issues_router,
    opsec_scan,
    project_state_collect,
    project_state_router,
    repository_authority,
    route_contracts,
    site_router,
    state_helpers,
    work_router,
    worktrees_router,
)
from scripts.api import main as api_main
from scripts.api.monitor_context import fixture_context
from scripts.fleet_comms import cold_start_board, message_plane
from scripts.guardrails import worktree_containment
from scripts.lexicon.runner import atlas_job
from scripts.orchestration import reap_worktrees
from scripts.wiki import sources_db

from . import registry

pytestmark = pytest.mark.repo_invariant

KNOWN_LEAKS_PATH = Path(__file__).with_name("known_leaks.toml")
FROZEN_IDS = frozenset(
    {
        "admin-backup-dir",
        "fleet-workers-host-id",
        "occupancy-host-id",
        "retention-plan-dir",
        "retention-archive-root",
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


def _sqlite_database_path(database: Any, *, uri: bool) -> Path | None:
    """Resolve a sqlite database argument to a filesystem path when it has one."""
    if isinstance(database, os.PathLike):
        database = os.fspath(database)
    if isinstance(database, bytes):
        database = os.fsdecode(database)
    if not isinstance(database, str):
        return None
    if database == ":memory:":
        return None
    if uri and database.startswith("file:"):
        parsed = urlparse(database)
        if parsed.path == ":memory:" or "memory" in parse_qs(parsed.query).get("mode", []):
            return None
        if parsed.path:
            database = unquote(parsed.path)
    return Path(database).expanduser().resolve()


def _deny_real_database_connect(root: Path, original_connect: Any) -> Any:
    def connect(database: Any, *args: Any, **kwargs: Any) -> Any:
        uri = kwargs.get("uri", args[6] if len(args) > 6 else False)
        database_path = _sqlite_database_path(database, uri=bool(uri))
        if database_path is not None and root not in (database_path, *database_path.parents):
            raise AssertionError("OPSEC sweep fixture forbids real database access")
        return original_connect(database, *args, **kwargs)

    return connect


def _fixture_completed_process(
    args: Any,
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=args,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _fixture_run_command(args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Return bounded, non-sensitive results for route-local command seams."""
    argv = [str(value) for value in args]
    if argv[:3] == ["git", "rev-parse", "HEAD"]:
        return _fixture_completed_process(args, stdout=("0" * 40) + "\n")
    if argv[:2] == ["git", "rev-parse"] and any("short" in value for value in argv):
        return _fixture_completed_process(args, stdout=("0" * 9) + "\n")
    if argv[:3] == ["git", "branch", "--show-current"]:
        return _fixture_completed_process(args, stdout="opsec-fixture\n")
    if argv[:1] == ["ps"]:
        return _fixture_completed_process(args, stdout="PID STATE COMMAND\n")
    return _fixture_completed_process(args)


def _fixture_authority_git(_cwd: Path, *args: str) -> str:
    if args == ("remote", "get-url", "origin"):
        return "https://example.invalid/opsec/repository.git"
    if args == ("branch", "--show-current"):
        return "opsec-fixture"
    if args == ("rev-parse", "HEAD"):
        return "0" * 40
    return ""


def _fixture_missing_sources_db() -> Any:
    raise FileNotFoundError("isolated OPSEC fixture has no source database")


def _fixture_reap_run(
    args: list[str],
    *,
    cwd: Path,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    del cwd, timeout
    return _fixture_completed_process(args, returncode=127, stderr="fixture git unavailable")


def _fixture_health_identity() -> dict[str, str | None]:
    return {
        "host": "fixture-host",
        "git_sha": None,
        "checkout_sha": None,
        "serving_sha": None,
        "serving_mode": "checkout",
    }


REAL_BOARD_PROBE_KEYS = frozenset(
    {
        "capsule_session_env",
        "plane_status",
        "backlog_and_dead_letters",
        "bottleneck_slice",
        "orient_lean",
        "issues_streams_membership",
        "session_streams_and_handoff",
        "inbox_check",
        "gh_pr_list",
        "needle_search",
    }
)


def _assert_real_cold_start_board_producer() -> None:
    from scripts.fleet_comms.cold_start_board import build_cold_start_board as real_build

    assert fleet_router.build_cold_start_board is real_build


def _assert_board_payload_is_real_shape(payload: dict[str, Any]) -> None:
    probes = payload.get("probes") or {}
    assert REAL_BOARD_PROBE_KEYS.issubset(probes.keys())
    assert "db_path" not in json.dumps(payload)


def _fixture_cold_start_board(
    *,
    stream_id: str | None = None,
    agent: str | None = None,
    needle: str | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    return {
        "timestamp": "2026-01-01T00:00:00Z",
        "board_status": "ok",
        "stream_id": stream_id,
        "agent": agent,
        "needle": needle,
        "probes": {},
    }


@pytest.fixture
def isolated_fixture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> IsolatedFixture:
    """Redirect existing API seams into a canary-planted disposable tree."""
    # pytest may expose a symlinked tmp_path on macOS and a worker-specific
    # ``/tmp/.../popen-gwN`` path on Linux. Resolve once, then use this same
    # canonical root for every fixture seam.
    root = (tmp_path / PATH_CANARY).resolve()
    root.mkdir()
    for relative in ("batch_state", "stores", "curriculum", "dashboards", "data", "logs"):
        (root / relative).mkdir(parents=True, exist_ok=True)

    # The API cache is process-global, while pytest-xdist gives each worker a
    # different fixture root. Replace the mutable stores rather than allowing
    # a prior test (or a background projection build) to replay another root's
    # logical work ids into this sweep.
    monkeypatch.setattr(state_helpers, "_ttl_cache", {})
    monkeypatch.setattr(state_helpers, "_content_file_index_cache", {})
    monkeypatch.setattr(state_helpers, "_curriculum_cache", None)
    monkeypatch.setattr(state_helpers, "_curriculum_mtime", 0.0)
    monkeypatch.setattr(work_router, "_IN_FLIGHT_BUILDS", {})
    fixture_ctx = fixture_context(root)
    monkeypatch.setattr(api_main.app.state, "ctx", fixture_ctx)
    session_connection = fixture_ctx.stores.session_streams_database.connect()
    session_connection.close()
    epics_store = SessionStreamStore(SessionStreamDatabase(root / "stores" / "epics.sqlite3"))
    monkeypatch.setattr(epics_router, "_store", lambda: epics_store)
    session_database = SessionStreamDatabase(root / "stores" / "session-streams.sqlite3")
    legacy_connection = session_database.connect()
    legacy_connection.close()
    handoff_path = root / "batch_state" / "session-handoff.md"
    handoff_path.write_text("fixture handoff\n", encoding="utf-8")
    (root / "scripts" / "config").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "config" / "issue_streams.yaml").write_text(
        "schema_version: issue-streams.v1\nstreams: {}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(api_main, "_health_instance_identity", _fixture_health_identity)
    monkeypatch.setattr(project_state_router, "allowed_reporter_host_ids", lambda: frozenset())
    monkeypatch.setattr(atlas_job, "registry_dir", lambda: Path("atlas-jobs-fixture"))

    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", f"{HOST_ALIAS_CANARY}={HOST_ID_CANARY}")
    monkeypatch.setenv("LU_MONITOR_HOST_ID", HOST_ID_CANARY)
    monkeypatch.setenv("AGENT_NO_TELEMETRY_FOOTER", "1")
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(root / "batch_state" / "atlas-jobs"))

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
            monkeypatch.setattr(module, "_run_command", _fixture_run_command)

    monkeypatch.setattr(subprocess, "run", _deny_subprocess)
    monkeypatch.setattr(subprocess, "Popen", _deny_subprocess)
    monkeypatch.setattr(socket, "create_connection", _deny_network)

    # These routes intentionally expose read-only local diagnostics, but the
    # sweep must not execute their git/gh/process seams. Return bounded fixture
    # values at the seam so the route exercises its normal response shaping.
    monkeypatch.setattr(project_state_collect, "_git", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(repository_authority, "_git", _fixture_authority_git)
    monkeypatch.setattr(repository_authority, "classify_repo_path", lambda *_args, **_kwargs: "primary_checkout")
    monkeypatch.setattr(
        git_hygiene_router,
        "_run_git",
        lambda *_args, **_kwargs: (127, "", "fixture git unavailable"),
    )
    monkeypatch.setattr(
        worktrees_router,
        "_run",
        lambda *_args, **_kwargs: (127, "", "fixture git unavailable"),
    )
    monkeypatch.setattr(
        issues_router,
        "_run_gh",
        lambda *_args, **_kwargs: (127, "", "fixture gh unavailable"),
    )
    monkeypatch.setattr(
        site_router,
        "_run",
        lambda args, **_kwargs: _fixture_completed_process(
            args,
            returncode=127,
            stderr="fixture command unavailable",
        ),
    )
    monkeypatch.setattr(
        governance_router,
        "collect_adr_governance",
        lambda: {
            "total": 0,
            "stale_proposed_count": 0,
            "error_count": 0,
            "warning_count": 0,
            "broken_chains": [],
            "orphaned_refs": [],
            "promotion_candidates": [],
            "index": [],
        },
    )
    monkeypatch.setattr(
        entire_context_router,
        "projection_path",
        lambda cwd: Path(cwd) / "batch_state" / "entire-context" / "v1" / "context-links.sqlite3",
    )
    monkeypatch.setattr(entire_context_router, "load_provider_status", lambda _root: {})
    monkeypatch.setattr(entire_context_router, "load_provider_capabilities", lambda _root: {})
    monkeypatch.setattr(reap_worktrees, "_run", _fixture_reap_run)
    monkeypatch.setattr(atlas_job, "primary_checkout_root", lambda: root)
    monkeypatch.setattr(
        worktree_containment,
        "primary_checkout_dirty_status",
        lambda _start: {
            "role": "primary",
            "head_sha": "0" * 40,
            "branch": "opsec-fixture",
            "protected_branch": False,
            "dirty": False,
            "dirty_count": 0,
            "tracked_dirty_count": 0,
            "untracked_dirty_count": 0,
            "entries": [],
            "checked_command": "git status --porcelain=v1 -z --untracked-files=all",
            "bare_primary": False,
            "bare_healed": False,
            "bare_heal_message": None,
        },
    )

    monkeypatch.setattr(
        cold_start_board,
        "_get_local_git_info",
        lambda: {
            "branch": "opsec-fixture",
            "head": "000000000",
        },
    )
    monkeypatch.setattr(
        cold_start_board,
        "_resolve_session_streams_db",
        lambda _repo_root: root / "stores" / "session-streams.sqlite3",
    )
    monkeypatch.setattr(
        cold_start_board,
        "_probe_gh_pr_list",
        lambda: cold_start_board.ProbeResult(
            status="skipped",
            elapsed_ms=0.0,
            data={"gh_available": False, "reason": "isolated_fixture"},
        ),
    )

    # RAG imports its source DB lazily outside the scripts.api namespace. The
    # top-level ``rag.query`` import resolves ``wiki.sources_db`` while this
    # fixture imports ``scripts.wiki.sources_db``; both module identities must
    # point at the same nonexistent worker-local path. The missing-corpus
    # behavior then stays on the documented empty-response path.
    fixture_sources_db = root / "stores" / "sources.db"
    rag_query = importlib.import_module("rag.query")
    search_db_modules = {
        sources_db,
        rag_query.sources_db,
    }
    for search_db_module in search_db_modules:
        monkeypatch.setattr(search_db_module, "SOURCES_DB_PATH", fixture_sources_db)
        monkeypatch.setattr(search_db_module, "_conn", None)
    monkeypatch.setattr(sources_db, "_get_conn", _fixture_missing_sources_db)

    # The route sweep also traverses diagnostics that import their own local
    # stores outside ``scripts.api``. Repoint those module-level paths before
    # installing the global guard, so missing fixture state is handled by each
    # route's documented empty/read-only envelope instead of as a 500.
    # ``scripts.ai_agent_bridge`` is deliberately absent here (#7269 step 5):
    # comms routes now hand the bridge the MonitorContext's broker DB
    # explicitly, so the bridge's import-time default DB_PATH globals are no
    # longer seams this sweep must repoint.
    importlib.import_module("scripts.fleet_comms.legacy_broker_report")
    importlib.import_module("scripts.telemetry.legacy_bridge")
    importlib.import_module("wiki.state")
    for module_name, module in tuple(sys.modules.items()):
        if module is None or not module_name.startswith(("scripts.telemetry", "wiki")):
            continue
        for name, value in tuple(vars(module).items()):
            if not isinstance(value, Path) or not value.is_absolute():
                continue
            if not any(token in name.upper() for token in ("DB", "PROGRESS", "STATE")):
                continue
            replacement = root / "stores" / module_name.replace(".", "_") / name.lower()
            replacement.parent.mkdir(parents=True, exist_ok=True)
            if value.is_dir() or value.suffix == "":
                replacement.mkdir(parents=True, exist_ok=True)
            monkeypatch.setattr(module, name, replacement)

    # Image discovery is also lazy, but its index and page caches are module
    # singletons. Repoint its file roots and recreate the singletons so a prior
    # test cannot leak real checkout data into this isolated route sweep.
    monkeypatch.setattr(images_router, "IMAGES_DIR", root / "stores" / "images")
    monkeypatch.setattr(images_router, "TEXTBOOKS_DIR", root / "stores" / "textbooks")
    monkeypatch.setattr(
        images_router,
        "ANNOTATIONS_FILE",
        root / "stores" / "image_text_pairs.jsonl",
    )
    monkeypatch.setattr(images_router, "_index", images_router._ImageIndex())
    monkeypatch.setattr(images_router, "_pdf_pool", images_router._PDFPool())
    monkeypatch.setattr(images_router, "_page_cache", images_router.OrderedDict())
    monkeypatch.setattr(images_router, "_pdf_page_count_cache", {})

    # NOTE (#7269 step 5): the step-5 inventory row originally attributed
    # this seam to comms_router, but its only sweep consumer is the
    # still-unmigrated fleet facade route (fleet_router.py:598 ->
    # build_legacy_broker_report -> default_routes_db()). Deleting it here
    # was verified to fail the sweep with "GET /api/fleet/facade/broker-report
    # status=500" on any machine whose primary checkout has a live
    # data/telemetry/legacy_comms_routes.db (the deny-connect backstop
    # correctly rejects the real-DB open). It migrates with step 4
    # (fleet_router), not step 5.
    broker_report = importlib.import_module("scripts.fleet_comms.legacy_broker_report")
    monkeypatch.setattr(broker_report, "main_checkout_root", lambda _repo_root: root)

    # This is the fixture-level backstop for any future search entry point that
    # misses a module-local path seam. Connections inside the disposable root
    # remain valid for the other isolated stores.
    monkeypatch.setattr(
        sqlite3,
        "connect",
        _deny_real_database_connect(root, sqlite3.connect),
    )

    # These docs roots are derived once at import time rather than exposed as
    # individual Path globals. Rebuild the lookup tables so docs requests
    # cannot traverse back into the checkout.
    monkeypatch.setattr(docs_router, "PROJECT_ROOT", root)
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
    # Dashboard paths are imported from PROJECT_ROOT at module import time;
    # bind both consumers to the same resolved fixture root as the docs roots.
    dashboards_root = root / "dashboards"
    monkeypatch.setattr(api_main, "DASHBOARDS_DIR", dashboards_root)
    monkeypatch.setattr(docs_router, "DASHBOARDS_DIR", dashboards_root)

    # Facade/status readers retain imported references to the resolver;
    # redirect every such reference into the disposable tree instead of
    # consulting the retired local plane. The resolver's own module global
    # no longer needs a setattr seam (#7269 step 5): default_plane_root
    # honors the documented FLEET_COMMS_ROOT operator override, which the
    # migrated comms routes and every still-unmigrated internal caller
    # (read_plane_status in fleet/runtime routers) resolve through.
    isolated_plane_root = root / "stores" / "fleet-comms"
    isolated_plane_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(isolated_plane_root))

    def isolated_plane_resolver(repo_root: Path | None = None) -> Path:
        del repo_root
        return isolated_plane_root

    monkeypatch.setattr(cold_start_board, "default_plane_root", isolated_plane_resolver)
    for module_name, module in tuple(sys.modules.items()):
        if not module_name.startswith("scripts.api") or module is None:
            continue
        if "default_plane_root" in vars(module):
            monkeypatch.setattr(module, "default_plane_root", isolated_plane_resolver)

    for dashboards_dir in {api_main.DASHBOARDS_DIR, docs_router.DASHBOARDS_DIR}:
        dashboards_dir.mkdir(parents=True, exist_ok=True)
        for filename in ("index.html", "artifacts.html"):
            (dashboards_dir / filename).write_text("<html><body>synthetic artifacts</body></html>\n", encoding="utf-8")
    shutil.copytree(
        Path(__file__).resolve().parents[3] / "dashboards",
        dashboards_root,
        dirs_exist_ok=True,
    )

    # The source and the injected seams must both carry the planted canary
    # before any response is considered safe to scan.
    assert root / "seams" / "scripts_api_main" / "project_root" == api_main.PROJECT_ROOT
    assert HOST_ALIAS_CANARY in os.environ["MONITOR_OCCUPANCY_HOST_IDS"]
    assert os.environ["LU_MONITOR_HOST_ID"] == HOST_ID_CANARY
    assert PATH_CANARY in str(api_main.PROJECT_ROOT.parent.parent.parent)
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


def _scan_response(
    record: registry.ExerciseRecord, response: Any, canaries: tuple[str, ...]
) -> list[opsec_scan.Finding]:
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
    assert {
        "GET /api/images/textbooks",
        "GET /api/rag/search_literary",
        "GET /api/rag/search_text",
        "GET /api/sources/search_literary",
        "GET /api/sources/search_text",
    } == registry.FIXTURE_EMPTY_ROUTE_KEYS
    for key in registry.FIXTURE_EMPTY_ROUTE_KEYS:
        assert by_key[key].fixture == "isolated"
        assert by_key[key].expected_statuses == (200,)
    assert by_key["GET /api/session-streams/v1/drift"].query["dry_run"] == "true"
    assert by_key["POST /api/comms/send"].expected_statuses == (410,)
    assert by_key["POST /api/comms/send"].body() is not None
    assert by_key["POST /api/epics/v1/{stream_id}/bundles"].classification == "mutation"
    assert by_key["POST /api/epics/v1/{stream_id}/bundles"].body() is not None
    assert by_key["POST /api/epics/v1/{stream_id}/bundles"].expected_statuses == (403,)
    assert by_key["GET /api/epics/v1/{stream_id}/bundles"].classification == "read"
    assert by_key["GET /api/epics/v1/{stream_id}/bundles/latest"].classification == "read"
    assert by_key["GET /api/epics/v1/{stream_id}/bundles/{upload_seq}"].classification == "read"
    assert (
        route_contracts.contract_for_route("/api/session-streams/v1/health").response_schema_version
        == "session-streams.v2"
    )
    assert route_contracts.contract_for_route("/api/state/preparation").response_schema_version == "authority.v2"
    assert route_contracts.contract_for_route("/api/orient").response_schema_version == "orient.v2"
    for record in records:
        if record.fixture == "skip":
            assert record.owner and record.reason and record.expiry


def test_exercised_read_registry_refuses_unexplained_5xx() -> None:
    records = registry.build_registry(api_main.app)
    unexplained = [
        record.key
        for record in records
        if record.fixture != "skip"
        and record.classification in {"read", "read-side-effect"}
        and any(500 <= status < 600 for status in record.expected_statuses)
        and not record.reason
    ]
    assert unexplained == []


def test_family_one_fixture_reaches_dual_write_and_orient_git_happy_paths(
    isolated_fixture: IsolatedFixture,
) -> None:
    client = TestClient(api_main.app, raise_server_exceptions=False)

    dual = client.get("/api/session-streams/v1/dual-write-status")
    assert dual.status_code == 200
    dual_payload = dual.json()
    assert dual_payload["total"] >= 0
    assert "candidates" in dual_payload
    assert all("path" not in candidate for candidate in dual_payload["candidates"])
    assert "repo_root" not in json.dumps(dual_payload)
    assert "db_path" not in json.dumps(dual_payload)

    orient = client.get("/api/orient", params={"sections": "git"})
    assert orient.status_code == 200
    git_payload = orient.json()["git"]
    assert git_payload["primary_checkout"] == {
        "role": "primary",
        "head_sha": "0" * 40,
        "dirty_count": 0,
    }
    assert git_payload["cwd_role"] in {"primary", "worktree", "other"}
    encoded = json.dumps(git_payload)
    assert "main_root" not in encoded
    assert "checked_cwd" not in encoded
    assert "data_checkout" not in encoded
    assert isolated_fixture.root.name == PATH_CANARY


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


def test_sweep_seam_honesty_requires_real_cold_start_board_producer(
    isolated_fixture: IsolatedFixture,
) -> None:
    del isolated_fixture
    _assert_real_cold_start_board_producer()
    client = TestClient(api_main.app, raise_server_exceptions=False)
    response = client.get("/api/fleet/facade/board")
    assert response.status_code == 200
    _assert_board_payload_is_real_shape(response.json())


def test_sweep_cold_start_board_stub_restoration_fails_seam_honesty(
    isolated_fixture: IsolatedFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del isolated_fixture
    monkeypatch.setattr(fleet_router, "build_cold_start_board", _fixture_cold_start_board)
    with pytest.raises(AssertionError):
        _assert_real_cold_start_board_producer()


def test_isolated_fixture_denies_network_and_subprocess(isolated_fixture: IsolatedFixture) -> None:
    del isolated_fixture
    with pytest.raises(AssertionError, match="forbids subprocess"):
        subprocess.run(["git", "status"], timeout=1)
    with pytest.raises(AssertionError, match="forbids subprocess"):
        subprocess.Popen(["git", "status"])
    with pytest.raises(AssertionError, match="forbids network"):
        socket.create_connection(("127.0.0.1", 8765))


def test_isolated_fixture_denies_real_database_access(isolated_fixture: IsolatedFixture) -> None:
    real_db_path = Path(__file__).resolve().parents[3] / "data" / "sources.db"
    assert real_db_path.resolve() not in (
        isolated_fixture.root,
        *isolated_fixture.root.parents,
    )
    connection: sqlite3.Connection | None = None
    try:
        with pytest.raises(AssertionError, match="forbids real database access"):
            connection = sources_db._open_conn(real_db_path)
    finally:
        if connection is not None:
            connection.close()

    class _BytesPath:
        def __fspath__(self) -> bytes:
            return os.fsencode(real_db_path)

    outside_databases = (
        (real_db_path.as_uri() + "?mode=ro", {"uri": True}),
        (os.fsencode(real_db_path), {}),
        (_BytesPath(), {}),
        ("file::memory:outside.db", {"uri": True}),
    )
    for database, kwargs in outside_databases:
        with pytest.raises(AssertionError, match="forbids real database access"):
            sqlite3.connect(database, **kwargs)

    with sqlite3.connect(":memory:") as connection:
        connection.execute("SELECT 1")
    with sqlite3.connect("file:fixture-memory?mode=memory&cache=shared", uri=True) as connection:
        connection.execute("SELECT 1")


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
        if record.key in registry.FIXTURE_EMPTY_ROUTE_KEYS and response.status_code >= 500:
            failures.append(f"{record.key} real-database failure status={response.status_code}")
        if record.key in registry.FIXTURE_EMPTY_ROUTE_KEYS and response.status_code == 200:
            assert _response_payload(response) == [], f"{record.key} did not return its empty fixture envelope"
        findings.extend(_scan_response(record, response, isolated_fixture.canaries))

    dashboard_root = isolated_fixture.root / "dashboards"
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
