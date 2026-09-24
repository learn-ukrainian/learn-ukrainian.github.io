"""Disposable-store recipes for every Monitor mutation route (#8542).

Each recipe seeds the isolated fixture tree (``MutationEnv.root``) or the
fixture ``MonitorContext`` stores, sends a valid minimal request, and proves
the route touched its disposable store.  The route sweep runs these requests
after the read pass, under a process-wide guard that fails any write outside
the fixture root and any subprocess or network attempt.

A recipe never names a real checkout path: every store it touches is resolved
from the fixture context or the fixture root.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

from agents_extensions.shared.session_streams.model import LeaseHolder
from scripts.api import agent_monitor_router, batch_router, project_state_router
from scripts.lexicon.runner import atlas_job

AGENT_MONITOR_TOKEN = "opsec-agent-monitor-token"
ATLAS_JOB_ID = "opsec-atlas-job"
ATLAS_CLOSE_JOB_ID = "opsec-atlas-close"
LOOPBACK_CLIENT = ("127.0.0.1", 50000)
LOOPBACK_BASE_URL = "http://127.0.0.1"
# Synthetic stream ids (scripts/lint/lint_test_assertions.py::_SYNTHETIC_EPIC_IDS):
# the fixture epics store is empty, so no id may name a real epic.
EPIC_CLAIM_STREAM = "epic:1001"
EPIC_HANDOFF_STREAM = "epic:1002"
EPIC_HEARTBEAT_STREAM = "epic:2001"
EPIC_RELEASE_STREAM = "epic:3001"
PROJECT_REPORTER_ID = "opsec-sweep-host"
UNLISTED_REPORTER_ID = "opsec-unlisted-host"


@dataclass(frozen=True)
class MutationEnv:
    """Handles a recipe may use; every one is fixture-scoped."""

    root: Path
    ctx: Any
    monkeypatch: Any
    scratch: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Prepared:
    """Request parts that only exist after a recipe seeded its store."""

    body: Any = None
    query: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MutationRecipe:
    """How the sweep exercises one mutation route against disposable stores."""

    store: str
    expected_statuses: tuple[int, ...]
    reason: str
    path_values: Mapping[str, str] = field(default_factory=dict)
    query: Mapping[str, Any] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    body_factory: Callable[[], Any] | None = None
    setup: Callable[[MutationEnv], Prepared | None] | None = None
    verify: Callable[[MutationEnv, Any], None] | None = None
    loopback: bool = False


# ── Shared seeding helpers ───────────────────────────────────────


def _agent_monitor_auth(env: MutationEnv) -> None:
    env.monkeypatch.setenv("AGENT_MONITOR_TOKEN", AGENT_MONITOR_TOKEN)


def _agent_monitor_db(env: MutationEnv) -> Path:
    return env.ctx.roots.batch_state_dir / "agent_monitor.sqlite3"


def _seed_agent_lease(env: MutationEnv, lease_token: str) -> None:
    now = time.time()
    connection = agent_monitor_router._get_db(_agent_monitor_db(env))
    try:
        connection.execute(
            "INSERT INTO agent_leases VALUES (?, ?, ?, ?, ?, ?, 'APPROVED', ?, ?)",
            (
                lease_token,
                "codex/opsec-sweep",
                "opsec_probe",
                os.getpid(),
                psutil.Process().create_time(),
                64,
                now,
                now,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def _agent_lease_status(env: MutationEnv, lease_token: str) -> str | None:
    connection = agent_monitor_router._get_db(_agent_monitor_db(env))
    try:
        row = connection.execute(
            "SELECT status FROM agent_leases WHERE lease_token = ?", (lease_token,)
        ).fetchone()
    finally:
        connection.close()
    return None if row is None else str(row[0])


def _atlas_plan(job_id: str) -> dict[str, Any]:
    return {
        "schema": atlas_job.SCHEMA,
        "id": job_id,
        "host": "atlas-runner",
        "kind": "reenrich",
        "pointer_write": False,
        "result_sink": "git",
        "denominator": 1,
        "success": {"circuit_breaker": False, "min_filled": 0},
        "args": [],
        "issue": 8542,
        "resume": "never",
        "timeout_seconds": 60,
    }


class _UnreachableAtlasHost:
    """Host adapter double: the fixture never reaches a real Atlas host."""

    def reachable(self, host: str) -> bool:
        del host
        return False

    def read_exit_status(self, host: str, workdir: str) -> dict[str, Any] | None:
        del host, workdir
        return None


def _isolate_atlas(env: MutationEnv) -> Path:
    registry = env.root / "batch_state" / "atlas-jobs"
    env.monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(registry))
    env.monkeypatch.setenv("ATLAS_RUN_ROOT", str(env.root / "atlas-run"))
    env.monkeypatch.setattr(atlas_job, "_HOST", _UnreachableAtlasHost())
    return registry


def _claim_epic(env: MutationEnv, stream_id: str, suffix: str) -> dict[str, Any]:
    holder = LeaseHolder(
        agent="codex",
        harness="codex-cli",
        instance_id=f"opsec-{suffix}-instance",
        process_id=1,
    )
    lease, _outcome = env.ctx.stores.epics_store.claim_remote_session(
        stream_id=stream_id,
        holder=holder,
        lineage_id=f"opsec-{suffix}-lineage",
        ttl_seconds=900,
        session_id=f"opsec-{suffix}-session",
        lease_id=f"opsec-{suffix}-lease",
    )
    return {
        "stream_id": lease.stream_id,
        "session_id": lease.session_id,
        "lease_id": lease.lease_id,
        "generation": lease.generation,
        "fencing_token": lease.fencing_token,
        "heartbeat_at": lease.heartbeat_at,
        "expires_at": lease.expires_at,
        "ttl_seconds": lease.ttl_seconds,
        "version": lease.version,
        "agent": holder.agent,
        "harness": holder.harness,
        "instance_id": holder.instance_id,
        "process_id": holder.process_id,
    }


def _epic_lease_state(env: MutationEnv, stream_id: str) -> str:
    return str(env.ctx.stores.epics_store.remote_stream_projection(stream_id)["lease"]["state"])


def _image_store(env: MutationEnv) -> Any:
    return env.ctx.stores.image_store


def _seed_images(env: MutationEnv) -> None:
    """Plant two structural image rows plus one PNG, then force a reload."""
    store = _image_store(env)
    book_dir = store.images_dir / "opsec-book"
    book_dir.mkdir(parents=True, exist_ok=True)
    (book_dir / "opsec-img-2.png").write_bytes(b"\x89PNG\r\n\x1a\nopsec")
    rows = [
        {"image_id": "opsec-img-1", "pdf_stem": "opsec-book", "page": 1},
        {
            "image_id": "opsec-img-2",
            "pdf_stem": "opsec-book",
            "page": 1,
            "image_path": "data/textbook_images/opsec-book/opsec-img-2.png",
        },
    ]
    (book_dir / "opsec-book-images.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    store.index.reload()


def _annotations_text(env: MutationEnv) -> str:
    path = _image_store(env).annotations_file
    return path.read_text(encoding="utf-8") if path.exists() else ""


# ── Admin ────────────────────────────────────────────────────────


def _setup_backup(env: MutationEnv) -> None:
    backup_dir = env.ctx.roots.backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / "opsec-backup.tar.gz").write_bytes(b"opsec-backup-bytes")


def _verify_backup(env: MutationEnv, response: Any) -> None:
    assert not (env.ctx.roots.backup_dir / "opsec-backup.tar.gz").exists()
    assert response.json()["freed_bytes"] == len(b"opsec-backup-bytes")


def _setup_clean_logs(env: MutationEnv) -> None:
    old_log = env.ctx.roots.logs_dir / "opsec-old.log"
    old_log.parent.mkdir(parents=True, exist_ok=True)
    old_log.write_text("opsec stale log\n", encoding="utf-8")
    stale = time.time() - 90 * 86400
    os.utime(old_log, (stale, stale))


def _verify_clean_logs(env: MutationEnv, response: Any) -> None:
    assert not (env.ctx.roots.logs_dir / "opsec-old.log").exists()
    assert response.json()["deleted_count"] == 1


def _setup_vacuum(env: MutationEnv) -> None:
    connection = env.ctx.stores.message_db.connect()
    try:
        connection.execute("CREATE TABLE IF NOT EXISTS opsec_vacuum_probe (value TEXT)")
        connection.commit()
    finally:
        connection.close()


def _verify_vacuum(env: MutationEnv, response: Any) -> None:
    del env
    assert response.json()["status"] == "ok"


# ── Agent monitor ────────────────────────────────────────────────


def _register_body() -> dict[str, Any]:
    return {
        "agent_id": "codex/opsec-sweep",
        "task_name": "opsec_register",
        "pid": os.getpid(),
        "process_create_time": psutil.Process().create_time(),
        "reserved_ram_mb": 64,
    }


def _verify_register(env: MutationEnv, response: Any) -> None:
    payload = response.json()
    if payload["verdict"] == "APPROVED":
        assert _agent_lease_status(env, payload["lease_token"]) == "APPROVED"


def _setup_heartbeat(env: MutationEnv) -> Prepared:
    _agent_monitor_auth(env)
    _seed_agent_lease(env, "lease_opsecbeat")
    return Prepared(body={"lease_token": "lease_opsecbeat", "pid": os.getpid()})


def _setup_release(env: MutationEnv) -> None:
    _agent_monitor_auth(env)
    _seed_agent_lease(env, "lease_opsecfree")


def _verify_release(env: MutationEnv, response: Any) -> None:
    del response
    assert _agent_lease_status(env, "lease_opsecfree") == "RELEASED"


# ── Atlas jobs ───────────────────────────────────────────────────


def _setup_atlas_submit(env: MutationEnv) -> None:
    _isolate_atlas(env)


def _verify_atlas_submit(env: MutationEnv, response: Any) -> None:
    del response
    row = atlas_job.load_registry(ATLAS_JOB_ID)
    assert row is not None and row["state"] == "rejected"
    assert atlas_job.registry_path(ATLAS_JOB_ID).is_relative_to(env.root)


def _setup_atlas_close(env: MutationEnv) -> None:
    _isolate_atlas(env)
    plan = _atlas_plan(ATLAS_CLOSE_JOB_ID)
    atlas_job.save_registry(
        {
            "id": ATLAS_CLOSE_JOB_ID,
            "state": "running",
            "host": "atlas-runner",
            "kind": "reenrich",
            "unit": atlas_job.unit_name(ATLAS_CLOSE_JOB_ID),
            "workdir": atlas_job.work_dir_for(ATLAS_CLOSE_JOB_ID, plan),
            "issue": 8542,
            "denominator": 1,
            "result_sink": "git",
            "pointer_write": False,
            "submitted_at": "2026-01-01T00:00:00+00:00",
            "plan": plan,
        }
    )


def _verify_atlas_close(env: MutationEnv, response: Any) -> None:
    del response
    assert atlas_job.result_path(ATLAS_CLOSE_JOB_ID).is_relative_to(env.root)
    assert atlas_job.result_path(ATLAS_CLOSE_JOB_ID).is_file()
    row = atlas_job.load_registry(ATLAS_CLOSE_JOB_ID)
    assert row is not None and row["state"] == "succeeded"


# ── Batch dispatcher ─────────────────────────────────────────────


def _setup_dispatcher_scan(env: MutationEnv) -> None:
    calls: list[tuple[list[str], Path]] = []

    def fixture_scan(cmd: list[str], cwd: Path) -> Any:
        calls.append((list(cmd), Path(cwd)))
        return subprocess.CompletedProcess(args=cmd, returncode=0)

    env.monkeypatch.setattr(batch_router, "_run_dispatcher_scan", fixture_scan)
    env.scratch["dispatcher_calls"] = calls


def _verify_dispatcher_scan(env: MutationEnv, response: Any) -> None:
    del response
    calls = env.scratch["dispatcher_calls"]
    assert len(calls) == 1
    cmd, cwd = calls[0]
    assert cwd == env.root
    assert all(Path(part).is_relative_to(env.root) for part in cmd[:2])


# ── Consultation queue ───────────────────────────────────────────


def _seed_consultation(env: MutationEnv, filename: str) -> None:
    template_dir = env.root / "agents_extensions" / "shared" / "phases" / "gemini"
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "opsec-template.md").write_text("opsec old guidance\n", encoding="utf-8")
    queue_dir = env.ctx.roots.queue_dir
    queue_dir.mkdir(parents=True, exist_ok=True)
    (queue_dir / filename).write_text(
        "source_module: a1/opsec-module\n"
        "consultation_num: 1\n"
        "confidence: high\n"
        "root_cause: synthetic opsec consultation\n"
        "queued_at: '2026-01-01T00:00:00Z'\n"
        "proposed_changes:\n"
        "  - file: opsec-template.md\n"
        "    find: opsec old guidance\n"
        "    replace: opsec new guidance\n"
        "    rationale: synthetic\n",
        encoding="utf-8",
    )


def _setup_consultation_approve(env: MutationEnv) -> None:
    _seed_consultation(env, "opsec-approve.yaml")


def _verify_consultation_approve(env: MutationEnv, response: Any) -> None:
    assert response.json()["changes_applied"] == 1
    assert (env.ctx.roots.queue_dir / "applied" / "opsec-approve.yaml").is_file()
    template = env.root / "agents_extensions" / "shared" / "phases" / "gemini" / "opsec-template.md"
    assert "opsec new guidance" in template.read_text(encoding="utf-8")


def _setup_consultation_reject(env: MutationEnv) -> None:
    _seed_consultation(env, "opsec-reject.yaml")


def _verify_consultation_reject(env: MutationEnv, response: Any) -> None:
    del response
    assert (env.ctx.roots.queue_dir / "rejected" / "opsec-reject.yaml").is_file()


# ── Epic leases (loopback-only mutations) ────────────────────────


def _claim_body() -> dict[str, Any]:
    return {
        "session_id": "opsec-claim-session",
        "lease_id": "opsec-claim-lease",
        "lineage_id": "opsec-claim-lineage",
        "agent": "codex",
        "harness": "codex-cli",
        "instance_id": "opsec-claim-instance",
        "process_id": 1,
        "ttl_seconds": 900,
    }


def _verify_claim(env: MutationEnv, response: Any) -> None:
    assert response.json()["outcome"]
    assert _epic_lease_state(env, EPIC_CLAIM_STREAM) == "active"


def _setup_epic_handoff(env: MutationEnv) -> Prepared:
    lease = _claim_epic(env, EPIC_HANDOFF_STREAM, "handoff")
    return Prepared(
        body={
            **lease,
            "type": "state",
            "body": "opsec synthetic handoff state",
            "idempotency_key": "opsec-handoff-key",
        }
    )


def _verify_epic_handoff(env: MutationEnv, response: Any) -> None:
    del env
    assert response.json()["entry"]["type"] == "state"


def _setup_epic_heartbeat(env: MutationEnv) -> Prepared:
    return Prepared(body=_claim_epic(env, EPIC_HEARTBEAT_STREAM, "heartbeat"))


def _verify_epic_heartbeat(env: MutationEnv, response: Any) -> None:
    del env
    assert response.json()["lease"]["state"] == "active"


def _setup_epic_release(env: MutationEnv) -> Prepared:
    return Prepared(body=_claim_epic(env, EPIC_RELEASE_STREAM, "release"))


def _verify_epic_release(env: MutationEnv, response: Any) -> None:
    assert response.json()["outcome"] == "released"
    assert _epic_lease_state(env, EPIC_RELEASE_STREAM) == "released"


# ── Fleet project-state report ───────────────────────────────────


def _project_report_body(host_id: str) -> dict[str, Any]:
    return {
        "host_id": host_id,
        "primary": {
            "head_sha": "0" * 40,
            "origin_main_sha": "0" * 40,
            "origin_main_age_s": 0,
            "ahead": 0,
            "behind": 0,
            "dirty_count": 0,
        },
        "worktrees": {"count": 0},
        "services": [],
        "collected_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def _setup_project_report(env: MutationEnv) -> None:
    """Allowlist one synthetic reporter for this fixture context only.

    A fixture context resolves no reporter ids by design (it must never read
    the real host-id environment), so the allowlist is the one seam replaced;
    peer, validation, and store-write logic stay real.
    """
    real_allowed = project_state_router.allowed_reporter_host_ids

    def fixture_allowed(ctx: Any = None) -> frozenset[str]:
        if ctx is env.ctx:
            return frozenset({PROJECT_REPORTER_ID})
        return real_allowed(ctx)

    env.monkeypatch.setattr(project_state_router, "allowed_reporter_host_ids", fixture_allowed)
    env.scratch["reports_before"] = dict(env.ctx.stores.report_store)


def _verify_project_report(env: MutationEnv, response: Any) -> None:
    payload = response.json()
    assert payload["host_id"] == PROJECT_REPORTER_ID and payload["received"] is True
    store = env.ctx.stores.report_store
    assert PROJECT_REPORTER_ID not in env.scratch["reports_before"]
    assert set(store) == {*env.scratch["reports_before"], PROJECT_REPORTER_ID}
    assert store[PROJECT_REPORTER_ID].document["host_id"] == PROJECT_REPORTER_ID


def _setup_project_report_refusal(env: MutationEnv) -> None:
    env.scratch["reports_before"] = dict(env.ctx.stores.report_store)


def _verify_project_report_refusal(env: MutationEnv, response: Any) -> None:
    assert response.json() == {"detail": "unknown host_id"}
    assert project_state_router.allowed_reporter_host_ids(env.ctx) == frozenset()
    assert env.ctx.stores.report_store == env.scratch["reports_before"]


# ── Images ───────────────────────────────────────────────────────


def _verify_annotation_put(env: MutationEnv, response: Any) -> None:
    assert response.json()["updated_fields"] == ["teaching_value"]
    assert '"opsec-img-1"' in _annotations_text(env)


def _verify_annotation_bulk(env: MutationEnv, response: Any) -> None:
    assert response.json()["updated_count"] == 2
    assert '"opsec-img-2"' in _annotations_text(env)


def _verify_image_cleanup(env: MutationEnv, response: Any) -> None:
    assert response.json()["deleted_count"] == 1
    store = _image_store(env)
    assert not (store.images_dir / "opsec-book" / "opsec-img-2.png").exists()
    assert "opsec-img-2" not in store.index.records


def _verify_image_reload(env: MutationEnv, response: Any) -> None:
    del env
    assert response.json()["total_records"] == 2


# ── Observer presence ────────────────────────────────────────────


def _verify_presence(env: MutationEnv, response: Any) -> None:
    del response
    rows = env.ctx.stores.presence_store
    assert any(key[1] == "codex" for key in rows)


# ── Telemetry ────────────────────────────────────────────────────


def _telemetry_rows(env: MutationEnv, filename: str, table: str) -> int:
    path = env.root / "data" / "telemetry" / filename
    with sqlite3.connect(path) as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _verify_tool_timing(env: MutationEnv, response: Any) -> None:
    assert response.json() == {"ok": True}
    assert _telemetry_rows(env, "tool_timings.db", "tool_timings") >= 1


def _verify_module_build(env: MutationEnv, response: Any) -> None:
    assert response.json()["run_id"] == "opsec-module-build"
    assert _telemetry_rows(env, "module_builds.db", "module_build_participants") == 1


_RETIRED = "retired legacy write; the 410 tombstone is the route's only response"

RECIPES: dict[str, MutationRecipe] = {
    "DELETE /api/admin/backup/{filename}": MutationRecipe(
        store="fixture backups dir (ctx.roots.backup_dir)",
        expected_statuses=(200,),
        reason="deletes a planted backup file",
        path_values={"filename": "opsec-backup.tar.gz"},
        setup=_setup_backup,
        verify=_verify_backup,
    ),
    "POST /api/admin/maintenance/clean-logs": MutationRecipe(
        store="fixture logs dir (ctx.roots.logs_dir)",
        expected_statuses=(200,),
        reason="deletes a planted 90-day-old log",
        query={"max_age_days": "30"},
        setup=_setup_clean_logs,
        verify=_verify_clean_logs,
    ),
    "POST /api/admin/maintenance/vacuum-broker": MutationRecipe(
        store="fixture broker DB (ctx.stores.message_db)",
        expected_statuses=(200,),
        reason="VACUUMs a planted broker database",
        setup=_setup_vacuum,
        verify=_verify_vacuum,
    ),
    "POST /api/agent-monitor/heartbeat": MutationRecipe(
        store="fixture batch_state/agent_monitor.sqlite3",
        expected_statuses=(200,),
        reason="renews a planted lease owned by the test process",
        headers={"X-Agent-Monitor-Token": AGENT_MONITOR_TOKEN},
        setup=_setup_heartbeat,
    ),
    "POST /api/agent-monitor/preflight": MutationRecipe(
        store="fixture batch_state/agent_monitor.sqlite3",
        expected_statuses=(200,),
        reason="capacity preflight reads the fixture lease table",
        body_factory=lambda: {
            "agent_id": "codex/opsec-sweep",
            "task_name": "opsec_probe",
            "required_ram_mb": 64,
        },
    ),
    "POST /api/agent-monitor/register": MutationRecipe(
        store="fixture batch_state/agent_monitor.sqlite3",
        expected_statuses=(200,),
        reason="registers the test process; host RAM decides APPROVED or REJECTED",
        headers={"X-Agent-Monitor-Token": AGENT_MONITOR_TOKEN},
        body_factory=_register_body,
        setup=_agent_monitor_auth,
        verify=_verify_register,
    ),
    "POST /api/agent-monitor/release": MutationRecipe(
        store="fixture batch_state/agent_monitor.sqlite3",
        expected_statuses=(200,),
        reason="releases a planted lease",
        headers={"X-Agent-Monitor-Token": AGENT_MONITOR_TOKEN},
        query={"lease_token": "lease_opsecfree"},
        setup=_setup_release,
        verify=_verify_release,
    ),
    "POST /api/atlas-jobs/submit": MutationRecipe(
        store="fixture batch_state/atlas-jobs registry (ATLAS_JOB_REGISTRY)",
        expected_statuses=(409,),
        reason="the fixture host adapter is unreachable, so submit journals a rejected row and refuses",
        body_factory=lambda: {"plan": _atlas_plan(ATLAS_JOB_ID), "dry_run": False},
        setup=_setup_atlas_submit,
        verify=_verify_atlas_submit,
    ),
    "POST /api/atlas-jobs/{job_id}/close": MutationRecipe(
        store="fixture batch_state/atlas-jobs registry (ATLAS_JOB_REGISTRY)",
        expected_statuses=(200,),
        reason="closes a planted running row with summary evidence and a local git receipt",
        path_values={"job_id": ATLAS_CLOSE_JOB_ID},
        body_factory=lambda: {
            "summary": {
                "targets": 1,
                "filled_translation": 1,
                "consecutive_misses": 0,
                "circuit_breaker_tripped": False,
            },
            "skip_pull": True,
            "skip_restic": True,
        },
        setup=_setup_atlas_close,
        verify=_verify_atlas_close,
    ),
    "POST /api/batch/dispatcher/scan": MutationRecipe(
        store="fixture live_repo_root dispatcher (subprocess seam replaced)",
        expected_statuses=(200,),
        reason="the dispatcher subprocess seam records its fixture-rooted argv instead of spawning",
        setup=_setup_dispatcher_scan,
        verify=_verify_dispatcher_scan,
    ),
    "POST /api/comms/acknowledge/{message_id}": MutationRecipe(
        store="none (retired)",
        expected_statuses=(410,),
        reason=_RETIRED,
    ),
    "POST /api/comms/channels/{name}/post": MutationRecipe(
        store="none (retired)",
        expected_statuses=(410,),
        reason=_RETIRED,
        body_factory=lambda: {"body": "opsec synthetic channel post"},
    ),
    "POST /api/comms/cleanup": MutationRecipe(
        store="none (retired)",
        expected_statuses=(410,),
        reason=_RETIRED,
    ),
    "POST /api/consultation/queue/{filename}/approve": MutationRecipe(
        store="fixture consultation queue + fixture gemini phase templates",
        expected_statuses=(200,),
        reason="approves a planted proposal and patches a planted template",
        path_values={"filename": "opsec-approve.yaml"},
        query={"confirm": "true"},
        setup=_setup_consultation_approve,
        verify=_verify_consultation_approve,
    ),
    "POST /api/consultation/queue/{filename}/reject": MutationRecipe(
        store="fixture consultation queue",
        expected_statuses=(200,),
        reason="rejects a planted proposal",
        path_values={"filename": "opsec-reject.yaml"},
        query={"confirm": "true", "reason": "opsec synthetic rejection"},
        setup=_setup_consultation_reject,
        verify=_verify_consultation_reject,
    ),
    "POST /api/epics/v1/{stream_id}/claim": MutationRecipe(
        store="fixture epics session-stream DB (ctx.stores.epics_store)",
        expected_statuses=(200,),
        reason="claims a fresh epic lease from a loopback peer",
        path_values={"stream_id": EPIC_CLAIM_STREAM},
        body_factory=_claim_body,
        verify=_verify_claim,
        loopback=True,
    ),
    "POST /api/epics/v1/{stream_id}/handoff": MutationRecipe(
        store="fixture epics session-stream DB (ctx.stores.epics_store)",
        expected_statuses=(200,),
        reason="appends a state entry under a planted lease from a loopback peer",
        path_values={"stream_id": EPIC_HANDOFF_STREAM},
        setup=_setup_epic_handoff,
        verify=_verify_epic_handoff,
        loopback=True,
    ),
    "POST /api/epics/v1/{stream_id}/heartbeat": MutationRecipe(
        store="fixture epics session-stream DB (ctx.stores.epics_store)",
        expected_statuses=(200,),
        reason="renews a planted lease from a loopback peer",
        path_values={"stream_id": EPIC_HEARTBEAT_STREAM},
        setup=_setup_epic_heartbeat,
        verify=_verify_epic_heartbeat,
        loopback=True,
    ),
    "POST /api/epics/v1/{stream_id}/release": MutationRecipe(
        store="fixture epics session-stream DB (ctx.stores.epics_store)",
        expected_statuses=(200,),
        reason="releases a planted lease from a loopback peer",
        path_values={"stream_id": EPIC_RELEASE_STREAM},
        setup=_setup_epic_release,
        verify=_verify_epic_release,
        loopback=True,
    ),
    "POST /api/fleet/projects/v1/report": MutationRecipe(
        store="fixture in-memory report store (ctx.stores.report_store)",
        expected_statuses=(200,),
        reason="upserts a loopback report from a synthetic reporter allowlisted for the fixture context",
        body_factory=lambda: _project_report_body(PROJECT_REPORTER_ID),
        setup=_setup_project_report,
        verify=_verify_project_report,
        loopback=True,
    ),
    "POST /api/images/annotations/bulk": MutationRecipe(
        store="fixture data/textbook_images annotations JSONL (ctx.stores.image_store)",
        expected_statuses=(200,),
        reason="bulk-annotates planted image rows",
        body_factory=lambda: {
            "image_ids": ["opsec-img-1", "opsec-img-2"],
            "updates": {"element_type": "photo"},
        },
        setup=_seed_images,
        verify=_verify_annotation_bulk,
    ),
    "POST /api/images/cleanup": MutationRecipe(
        store="fixture data/textbook_images (PNG + JSONLs)",
        expected_statuses=(200,),
        reason="deletes a planted image row and its PNG",
        body_factory=lambda: {"image_ids": ["opsec-img-2"]},
        setup=_seed_images,
        verify=_verify_image_cleanup,
    ),
    "POST /api/images/reload": MutationRecipe(
        store="fixture data/textbook_images index (ctx.stores.image_store)",
        expected_statuses=(200,),
        reason="reloads the planted image index from the fixture tree",
        setup=_seed_images,
        verify=_verify_image_reload,
    ),
    "POST /api/observer/presence": MutationRecipe(
        store="fixture in-memory presence store (ctx.stores.presence_store)",
        expected_statuses=(200,),
        reason="upserts an observer heartbeat from a loopback peer",
        body_factory=lambda: {"agent": "codex", "status": "working", "task_id": "opsec-presence"},
        verify=_verify_presence,
        loopback=True,
    ),
    "POST /api/telemetry/module-builds": MutationRecipe(
        store="fixture data/telemetry/module_builds.db",
        expected_statuses=(200,),
        reason="ingests one module-build run with one participant",
        body_factory=lambda: {
            "run_id": "opsec-module-build",
            "level": "a1",
            "slug": "opsec-module",
            "swarm_used": False,
            "swarm_note": "opsec synthetic run",
            "source": "opsec-sweep",
            "participants": [{"role": "writer", "agent": "codex"}],
        },
        verify=_verify_module_build,
    ),
    "POST /api/telemetry/tool-timings": MutationRecipe(
        store="fixture data/telemetry/tool_timings.db",
        expected_statuses=(200,),
        reason="ingests one tool timing row",
        body_factory=lambda: {
            "ts": "2026-01-01T00:00:00Z",
            "tool_name": "opsec_probe",
            "duration_ms": 1,
        },
        verify=_verify_tool_timing,
    ),
    "PUT /api/images/annotations/{image_id}": MutationRecipe(
        store="fixture data/textbook_images annotations JSONL (ctx.stores.image_store)",
        expected_statuses=(200,),
        reason="annotates one planted image row",
        path_values={"image_id": "opsec-img-1"},
        body_factory=lambda: {"teaching_value": "high"},
        setup=_seed_images,
        verify=_verify_annotation_put,
    ),
}


# Expected refusals exercised alongside a route's primary recipe. Each runs
# before the primary (so the fixture's own policy is still in force), is
# scanned like any response, and must leave its store unchanged.
REFUSAL_RECIPES: dict[str, tuple[MutationRecipe, ...]] = {
    "POST /api/fleet/projects/v1/report": (
        MutationRecipe(
            store="fixture in-memory report store (ctx.stores.report_store)",
            expected_statuses=(400,),
            reason=(
                "a fixture context allowlists no reporter host ids by design, so a well-formed "
                "loopback report is refused before the store"
            ),
            body_factory=lambda: _project_report_body(UNLISTED_REPORTER_ID),
            setup=_setup_project_report_refusal,
            verify=_verify_project_report_refusal,
            loopback=True,
        ),
    ),
}
