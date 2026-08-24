"""Cache-only adapters that join live AI workers per opaque host."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agents_extensions.shared.session_streams.model import parse_timestamp
from scripts.api import delegate_router
from scripts.api.delegate_router import _derived_task_status
from scripts.api.fleet_workers_models import (
    _AGENT_RE,
    _EPIC_RE,
    _ID_RE,
    WorkerRow,
    worker_row_dict,
)
from scripts.api.fleet_workers_sanitize import validate_worker_row_dict
from scripts.api.observer_presence import list_live
from scripts.api.occupancy import DEFAULT_HOST_IDS, parse_host_id_map
from scripts.api.occupancy_local import (
    DEFAULT_MARKER_TTL_S,
    OccupancyRead,
    _iter_marker_payloads,
    markers_root,
    read_markers,
    read_session_streams,
    resolve_launcher_host_id,
    self_host_opaque_ids,
)
from scripts.api.occupancy_sanitize import CLOUD_OBSERVER_HOST_ID, opaque_host_id, safe_field
from scripts.api.project_state_store import (
    freshness_from_age,
    get_live_report,
    workers_status_from_document,
)
from scripts.api.session_streams_router import _db_path as session_streams_db_path
from scripts.lexicon.runner import atlas_job

WORKERS_SCHEMA = "monitor-fleet-workers.v1"
UNATTRIBUTED_HOST_ID = "unattributed"

MARKER_KIND_NORMALIZE = {
    "worker": "service",
    "service": "service",
    "job": "job",
    "driver": "driver",
    "foundry": "service",
    "evidence-compiler": "service",
    "other": "service",
}


@dataclass(frozen=True)
class WorkerIdentity:
    source: str
    kind: str
    id: str
    run_id: str | None = None
    marker_written_at: str | None = None


@dataclass
class CollectedWorker:
    source: str
    row: WorkerRow
    host_id: str | None
    identity: WorkerIdentity
    instance_id: str | None = None
    task_id: str | None = None
    related: list[dict[str, str]] = field(default_factory=list)


@dataclass
class SkipTally:
    count: int = 0

    def bump(self, amount: int = 1) -> None:
        self.count += amount


def compute_run_id(run_nonce: str | None) -> str | None:
    if not run_nonce or not str(run_nonce).strip():
        return None
    return hashlib.sha256(str(run_nonce).encode("utf-8")).hexdigest()[:8]


def _agent_token(value: Any) -> str | None:
    text = safe_field(value, role="agent")
    if text is None:
        return None
    return text if _AGENT_RE.fullmatch(text) else None


def _harness_token(value: Any) -> str | None:
    return _agent_token(value)


def _epic_token(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.isdigit():
        text = f"epic:{text}"
    return text if _EPIC_RE.fullmatch(text) else None


def _task_token(value: Any) -> str | None:
    return safe_field(value, role="task_id")


def _worker_id_token(value: Any, *, tally: SkipTally | None = None) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    text = safe_field(value, role="task_id")
    if text is None:
        if tally is not None:
            tally.bump()
        return None
    if _ID_RE.fullmatch(text):
        return text
    if tally is not None:
        tally.bump()
    return None


def _make_worker_row(tally: SkipTally | None, **kwargs: Any) -> WorkerRow | None:
    try:
        return WorkerRow(**kwargs)
    except Exception:
        if tally is not None:
            tally.bump()
        return None


def _age_seconds(started_at: str | None, *, now: datetime, fallback: float = 0.0) -> int:
    if not started_at:
        return int(max(0.0, fallback))
    try:
        stamp = parse_timestamp(str(started_at))
    except ValueError:
        return int(max(0.0, fallback))
    return int(min(604_800, max(0.0, (now - stamp).total_seconds())))


def _delegate_state(status: str, *, alive: bool, pid: Any) -> str | None:
    if status == "spawning":
        return "starting"
    if status == "running":
        if pid and alive:
            return "live"
        return "zombie"
    return None


def _job_state(state: str) -> str | None:
    if state == "running":
        return "live"
    if state in {"queued", "submitted"}:
        return "starting"
    if state == "needs_finalize":
        return "needs_attention"
    return None


def collect_delegate_workers(
    tasks_dir: Path,
    *,
    now: datetime | None = None,
    tally: SkipTally | None = None,
) -> list[CollectedWorker]:
    clock = now or datetime.now(UTC)
    rows: list[CollectedWorker] = []
    if not tasks_dir.is_dir():
        return rows
    for entry in sorted(tasks_dir.glob("*.json")):
        try:
            task = json.loads(entry.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(task, dict):
            continue
        status, alive = _derived_task_status(task)
        mapped = _delegate_state(str(task.get("status") or status), alive=alive, pid=task.get("pid"))
        if mapped is None:
            continue
        task_id = _worker_id_token(task.get("task_id") or entry.stem, tally=tally)
        agent = _agent_token(task.get("agent"))
        if task_id is None or agent is None:
            continue
        run_id = compute_run_id(task.get("run_nonce"))
        row = _make_worker_row(
            tally,
            kind="delegate",
            agent=agent,
            harness=_harness_token(task.get("harness")),
            id=task_id,
            run_id=run_id,
            epic=_epic_token(task.get("epic")),
            state=mapped,
            age_s=_age_seconds(task.get("started_at"), now=clock),
        )
        if row is None:
            continue
        rows.append(
            CollectedWorker(
                source="delegate",
                row=row,
                host_id=None,
                identity=WorkerIdentity("delegate", "delegate", task_id, run_id),
                task_id=task_id,
            )
        )
    return rows


def _read_driver_leases(
    *,
    db_path: Path | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    path = session_streams_db_path() if db_path is None else db_path
    clock = now or datetime.now(UTC)
    if not path.is_file():
        return []
    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        raw_rows = conn.execute(
            """
            SELECT l.stream_id, l.holder_agent, l.holder_harness, l.holder_instance_id,
                   l.holder_task_id, l.holder_host_id, l.heartbeat_at, l.expires_at, l.state
            FROM stream_leases AS l
            JOIN sessions AS s ON s.stream_id = l.stream_id AND s.session_id = l.session_id
            WHERE l.state = 'active' AND s.state IN ('open', 'rolling')
            """
        ).fetchall()
        conn.close()
    except Exception:
        return []
    leases: list[dict[str, Any]] = []
    for row in raw_rows:
        try:
            expires_at = parse_timestamp(str(row["expires_at"]))
        except (KeyError, TypeError, ValueError):
            continue
        if expires_at <= clock:
            continue
        leases.append(dict(row))
    return leases


def collect_driver_workers(
    *,
    db_path: Path | None = None,
    now: datetime | None = None,
    tally: SkipTally | None = None,
) -> tuple[list[CollectedWorker], list[CollectedWorker]]:
    clock = now or datetime.now(UTC)
    attributed: list[CollectedWorker] = []
    unattributed: list[CollectedWorker] = []
    for lease in _read_driver_leases(db_path=db_path, now=clock):
        instance_id = _worker_id_token(lease.get("holder_instance_id"), tally=tally)
        agent = _agent_token(lease.get("holder_agent"))
        if instance_id is None or agent is None:
            continue
        stream_id = str(lease.get("stream_id") or "")
        epic = None
        if stream_id.startswith("epic:"):
            epic = _epic_token(stream_id.removeprefix("epic:"))
        task_id = _worker_id_token(lease.get("holder_task_id"), tally=tally)
        row = _make_worker_row(
            tally,
            kind="driver",
            agent=agent,
            harness=_harness_token(lease.get("holder_harness")),
            id=instance_id,
            run_id=None,
            epic=epic,
            state="live",
            age_s=_age_seconds(str(lease.get("heartbeat_at")), now=clock),
        )
        if row is None:
            continue
        collected = CollectedWorker(
            source="driver",
            row=row,
            host_id=str(lease.get("holder_host_id") or "").strip().lower() or None,
            identity=WorkerIdentity("driver", "driver", instance_id),
            instance_id=instance_id,
            task_id=task_id,
        )
        if collected.host_id:
            attributed.append(collected)
        else:
            unattributed.append(collected)
    return attributed, unattributed


def collect_observer_workers(
    *,
    now_mono: float | None = None,
    tally: SkipTally | None = None,
) -> list[CollectedWorker]:
    rows: list[CollectedWorker] = []
    for presence in list_live(now_mono=now_mono):
        agent = _agent_token(presence.agent)
        if agent is None:
            continue
        task_id = _worker_id_token(presence.task_id, tally=tally)
        row = _make_worker_row(
            tally,
            kind="observer",
            agent=agent,
            harness=None,
            id=agent,
            run_id=None,
            epic=_epic_token(presence.epic),
            state="live",
            age_s=_age_seconds(presence.updated_at, now=datetime.now(UTC)),
            seat_model="single",
        )
        if row is None:
            continue
        rows.append(
            CollectedWorker(
                source="observer",
                row=row,
                host_id=CLOUD_OBSERVER_HOST_ID,
                identity=WorkerIdentity("observer", "observer", agent),
                task_id=task_id,
            )
        )
    return rows


def collect_job_workers(
    *,
    canonical_host: str | None,
    now: datetime | None = None,
    tally: SkipTally | None = None,
) -> tuple[list[CollectedWorker], dict[str, Any] | None]:
    clock = now or datetime.now(UTC)
    rows: list[CollectedWorker] = []
    burn: dict[str, Any] | None = None
    try:
        registry = atlas_job.list_registry()
    except Exception:
        return rows, {"source": "job", "state": "unknown", "count": 0, "reason": "registry unreadable"}
    for item in registry:
        if not isinstance(item, dict):
            continue
        if canonical_host is not None and atlas_job._canonical_host(item.get("host")) != canonical_host:
            continue
        state = str(item.get("state") or "")
        mapped = _job_state(state)
        if mapped is None:
            continue
        job_id = _worker_id_token(item.get("id"), tally=tally)
        plan = item.get("plan") if isinstance(item.get("plan"), dict) else {}
        agent = _agent_token(item.get("agent") or plan.get("agent"))
        if job_id is None or agent is None:
            continue
        row = _make_worker_row(
            tally,
            kind="job",
            agent=agent,
            harness=_harness_token(plan.get("harness")),
            id=job_id,
            run_id=None,
            epic=_epic_token(item.get("epic") or plan.get("epic")),
            state=mapped,
            age_s=_age_seconds(item.get("updated_at") or item.get("submitted_at"), now=clock),
        )
        if row is None:
            continue
        rows.append(
            CollectedWorker(
                source="job",
                row=row,
                host_id=None,
                identity=WorkerIdentity("job", "job", job_id),
                task_id=job_id,
            )
        )
    return rows, burn


def collect_marker_workers(
    *,
    host_id: str,
    root: Path | None = None,
    now: datetime | None = None,
    tally: SkipTally | None = None,
) -> list[CollectedWorker]:
    clock = now or datetime.now(UTC)
    read = read_markers(host_id=host_id, root=root, now=clock)
    rows: list[CollectedWorker] = []
    if not read.readable:
        return rows
    path = root
    if path is None:
        path = markers_root()
    payloads: list[dict[str, Any]] = []
    if path and path.exists():
        try:
            for payload in _iter_marker_payloads(path):
                payloads.append(payload)
        except OSError:
            return rows
    for occupant in read.occupants:
        raw_kind = str(occupant.get("kind") or "service")
        kind = MARKER_KIND_NORMALIZE.get(raw_kind, "service")
        task_id = _worker_id_token(occupant.get("task_id"), tally=tally)
        agent = _agent_token(occupant.get("agent"))
        if task_id is None or agent is None:
            continue
        written_at = ""
        for payload in payloads:
            if str(payload.get("task_id")) == task_id and str(payload.get("kind")) == raw_kind:
                written_at = str(payload.get("updated_at") or payload.get("expires_at") or "")
                break
        row = _make_worker_row(
            tally,
            kind=kind,
            agent=agent,
            harness=None,
            id=task_id,
            run_id=None,
            epic=_epic_token(occupant.get("epic")),
            state="live",
            age_s=min(DEFAULT_MARKER_TTL_S, int(read.observation_age_s)),
        )
        if row is None:
            continue
        rows.append(
            CollectedWorker(
                source="marker",
                row=row,
                host_id=host_id,
                identity=WorkerIdentity("marker", kind, task_id, marker_written_at=written_at or "0"),
                task_id=task_id,
            )
        )
    return rows


def _worker_from_report_row(row: dict[str, Any], *, tally: SkipTally | None = None) -> CollectedWorker | None:
    try:
        validated = validate_worker_row_dict(row)
    except Exception:
        if tally is not None:
            tally.bump()
        return None
    return CollectedWorker(
        source="project_state",
        row=validated,
        host_id=None,
        identity=WorkerIdentity("project_state", validated.kind, validated.id, validated.run_id),
        instance_id=validated.id if validated.kind == "driver" else None,
        task_id=validated.id if validated.kind in {"delegate", "job", "service"} else None,
    )


def _related_links(workers: list[CollectedWorker], *, host_id: str) -> None:
    by_instance: dict[str, list[CollectedWorker]] = {}
    by_task_host: dict[tuple[str, str], list[CollectedWorker]] = {}
    for worker in workers:
        if worker.instance_id:
            by_instance.setdefault(worker.instance_id, []).append(worker)
        if worker.task_id:
            by_task_host.setdefault((worker.task_id, host_id), []).append(worker)
    for group in by_instance.values():
        if len(group) < 2:
            continue
        for worker in group:
            for other in group:
                if other is worker:
                    continue
                link = {"source": other.source, "id": other.row.id}
                if link not in worker.related:
                    worker.related.append(link)
    for group in by_task_host.values():
        if len(group) < 2:
            continue
        for worker in group:
            for other in group:
                if other is worker:
                    continue
                link = {"source": other.source, "id": other.row.id}
                if link not in worker.related:
                    worker.related.append(link)


def _shape_worker(worker: CollectedWorker) -> dict[str, Any]:
    payload = worker_row_dict(worker.row)
    payload["source"] = worker.source
    payload["related"] = list(worker.related)
    return payload


def _selected_host_ids(host_id: str | None) -> list[str]:
    mapping = parse_host_id_map()
    reverse = {opaque: canonical for canonical, opaque in mapping.items()}
    if host_id is not None:
        if host_id in reverse or host_id in DEFAULT_HOST_IDS or host_id == CLOUD_OBSERVER_HOST_ID:
            return [host_id]
        return []
    selected: list[str] = []
    for default_id in DEFAULT_HOST_IDS:
        if default_id not in selected:
            selected.append(default_id)
    for opaque in sorted(reverse):
        if opaque not in selected:
            selected.append(opaque)
    if CLOUD_OBSERVER_HOST_ID not in selected:
        selected.append(CLOUD_OBSERVER_HOST_ID)
    return selected


def _self_host_ids() -> set[str]:
    self_id = resolve_launcher_host_id()
    ids: set[str] = set()
    if self_id and self_id != "local" and opaque_host_id(self_id):
        ids.add(self_id)
    ids.update(self_host_opaque_ids(parse_host_id_map()))
    return ids


def _host_freshness(host_id: str, *, now_mono: float) -> str:
    if host_id in _self_host_ids():
        return "fresh"
    if host_id == CLOUD_OBSERVER_HOST_ID:
        return "fresh" if list_live(now_mono=now_mono) else "unknown"
    stored = get_live_report(host_id, now_mono=now_mono)
    if stored is None:
        return "unknown"
    age_s = now_mono - stored.received_at_mono
    return freshness_from_age(age_s)


def _reported_workers(
    host_id: str,
    *,
    now_mono: float,
    tally: SkipTally | None = None,
) -> tuple[str, list[CollectedWorker]]:
    if host_id in _self_host_ids():
        return "reported", []
    stored = get_live_report(host_id, now_mono=now_mono)
    if stored is None:
        return "unreported", []
    status = workers_status_from_document(stored.document)
    if status != "reported":
        return "unreported", []
    rows: list[CollectedWorker] = []
    workers = stored.document.get("workers")
    if isinstance(workers, list):
        for item in workers:
            if not isinstance(item, dict):
                continue
            collected = _worker_from_report_row(item, tally=tally)
            if collected is not None:
                collected.host_id = host_id
                rows.append(collected)
    return status, rows


def collect_local_workers_for_reporter(
    *,
    tasks_dir: Path | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    clock = now or datetime.now(UTC)
    workers = collect_delegate_workers(tasks_dir or delegate_router.TASKS_DIR, now=clock)
    return [worker_row_dict(item.row) for item in workers[:200]]


def workers_payload(
    *,
    host_id: str | None = None,
    tasks_dir: Path | None = None,
    session_db: Path | None = None,
    markers_root: Path | None = None,
    now_mono: float | None = None,
) -> dict[str, Any]:
    stamp = time.monotonic() if now_mono is None else now_mono
    clock = datetime.now(UTC)
    mapping = parse_host_id_map()
    reverse = {opaque: canonical for canonical, opaque in mapping.items()}
    selected = _selected_host_ids(host_id)
    hosts: list[dict[str, Any]] = []
    attention: list[str] = []
    live_count = 0
    total_workers = 0
    unknown_hosts = 0
    tally = SkipTally()

    all_unattributed: list[CollectedWorker] = []
    driver_attributed, driver_unattributed = collect_driver_workers(
        db_path=session_db,
        now=clock,
        tally=tally,
    )
    all_unattributed.extend(driver_unattributed)

    for opaque in selected:
        if opaque == UNATTRIBUTED_HOST_ID:
            continue
        freshness = _host_freshness(opaque, now_mono=stamp)
        if freshness == "unknown":
            unknown_hosts += 1
        workers_status, reported = _reported_workers(opaque, now_mono=stamp, tally=tally)
        host_workers: list[CollectedWorker] = []
        unattributed_burn: dict[str, Any] = {}
        reason: str | None = None

        if opaque in _self_host_ids():
            workers_status = "reported"
            canonical = reverse.get(opaque)
            host_workers.extend(
                collect_delegate_workers(tasks_dir or delegate_router.TASKS_DIR, now=clock, tally=tally)
            )
            host_workers.extend(item for item in driver_attributed if item.host_id == opaque)
            if canonical is not None:
                job_rows, _ = collect_job_workers(canonical_host=canonical, now=clock, tally=tally)
                host_workers.extend(job_rows)
            host_workers.extend(
                collect_marker_workers(host_id=opaque, root=markers_root, now=clock, tally=tally)
            )
            selected_map = {item: reverse.get(item) for item in selected if item != CLOUD_OBSERVER_HOST_ID}
            driver_read: OccupancyRead = read_session_streams(
                host_id=opaque,
                mapping=mapping,
                selected=selected_map,
                db_path=session_db,
                now=clock,
            )
            if not driver_read.readable:
                unattributed_burn["driver"] = {
                    "state": "unknown",
                    "count": 0,
                    "reason": "session stream store unreadable",
                }
        elif opaque == CLOUD_OBSERVER_HOST_ID:
            workers_status = "reported"
            host_workers.extend(collect_observer_workers(now_mono=stamp, tally=tally))
        else:
            if workers_status == "unreported":
                attention.append(f"unreported:{opaque}")
                reason = "workers block unreported"
            host_workers.extend(reported)

        _related_links(host_workers, host_id=opaque)
        shaped = [_shape_worker(item) for item in host_workers]
        for item in shaped:
            total_workers += 1
            if item.get("state") == "live" and freshness == "fresh":
                live_count += 1
        hosts.append(
            {
                "host_id": opaque,
                "freshness": freshness,
                "workers_status": workers_status,
                "workers": shaped,
                "unattributed_burn": unattributed_burn,
                "reason": reason,
            }
        )

    if all_unattributed and (host_id is None or host_id == UNATTRIBUTED_HOST_ID):
        _related_links(all_unattributed, host_id=UNATTRIBUTED_HOST_ID)
        shaped = [_shape_worker(item) for item in all_unattributed]
        for item in shaped:
            total_workers += 1
            live_count += 1 if item.get("state") == "live" else 0
        hosts.append(
            {
                "host_id": UNATTRIBUTED_HOST_ID,
                "freshness": "fresh",
                "workers_status": "reported",
                "workers": shaped,
                "unattributed_burn": {},
                "reason": "lease has no host claim",
            }
        )

    return {
        "schema": WORKERS_SCHEMA,
        "observed_at": clock.isoformat().replace("+00:00", "Z"),
        "counts": {
            "live": live_count,
            "hosts_unknown": unknown_hosts,
            "workers_total": total_workers,
            "attention": len(attention),
            "skipped": tally.count,
        },
        "attention": attention,
        "hosts": hosts,
    }
