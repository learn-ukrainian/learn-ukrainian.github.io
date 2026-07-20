"""DB-first legacy projection receipts + file drift detection (Sol PR-H / #5512).

After inventory registration, each epic can record a ``legacy_projection_receipts``
row describing what a dual-write compatibility projection would do. This module
does **not** rewrite handoff files, open leases, or advance migration mode past
``inventory`` / shadow structure — cutover remains blocked.

Drift means the on-disk handoff no longer matches the last inventory/import
receipt, or (when DB content exists) diverges from the DB-first projection body.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .inventory import load_stream_epic_inventory, resolve_streams_yaml
from .model import canonical_json, sha256_text
from .receipts import record_projection_receipt, register_manifest_inventory
from .store import SessionStreamStore

PROJECTION_KIND = "session_stream_file_projection.v1"
CUTOVER_BLOCKED = "blocked — dual-write only; file handoffs remain authoritative"


@dataclass(frozen=True, slots=True)
class StreamProjectionResult:
    """One stream's projection observation."""

    stream_id: str
    target_path: str
    status: str
    projection_id: int
    target_sha256: str
    high_water_entry_id: int | None
    projection_hash: str
    error: str
    file_exists: bool
    unrecorded_mutation: bool
    source: str  # db_mirror | db_digest | file_shadow | missing
    mode: str


@dataclass(frozen=True, slots=True)
class ProjectionBatchResult:
    """Outcome of ``project_inventory_streams``."""

    epic_count: int
    receipts_written: int
    ok: int
    drift: int
    failed: int
    streams: tuple[StreamProjectionResult, ...]
    cutover: str = CUTOVER_BLOCKED

    def as_dict(self) -> dict[str, Any]:
        return {
            "epic_count": self.epic_count,
            "receipts_written": self.receipts_written,
            "ok": self.ok,
            "drift": self.drift,
            "failed": self.failed,
            "cutover": self.cutover,
            "streams": [
                {
                    "stream_id": s.stream_id,
                    "target_path": s.target_path,
                    "status": s.status,
                    "projection_id": s.projection_id,
                    "target_sha256": s.target_sha256,
                    "high_water_entry_id": s.high_water_entry_id,
                    "projection_hash": s.projection_hash,
                    "error": s.error,
                    "file_exists": s.file_exists,
                    "unrecorded_mutation": s.unrecorded_mutation,
                    "source": s.source,
                    "mode": s.mode,
                }
                for s in self.streams
            ],
        }


def _read_target(root: Path, rel: str) -> tuple[bool, str, str]:
    """Return (exists, sha256_or_empty, utf8_body_or_empty)."""
    path = root / rel
    if not path.is_file():
        return False, "", ""
    raw = path.read_bytes()
    try:
        body = raw.decode("utf-8")
    except UnicodeDecodeError:
        body = ""
    return True, hashlib.sha256(raw).hexdigest(), body


def _latest_import_for_path(
    store: SessionStreamStore,
    *,
    stream_id: str,
    source_path: str,
) -> dict[str, Any] | None:
    with store._read_snapshot() as connection:
        row = connection.execute(
            "SELECT * FROM legacy_import_receipts "
            "WHERE stream_id = ? AND source_path = ? "
            "ORDER BY import_id DESC LIMIT 1",
            (stream_id, source_path),
        ).fetchone()
        return dict(row) if row is not None else None


def _baseline_import_for_path(
    store: SessionStreamStore,
    *,
    stream_id: str,
    source_path: str,
) -> dict[str, Any] | None:
    """Return the drift baseline import for a path.

    Prefer the earliest ``inventoried``/``imported`` receipt so later
    re-inventory of a mutated file cannot mask unrecorded mutations. Fall back
    to the earliest receipt of any status, then the latest if needed.
    """
    with store._read_snapshot() as connection:
        row = connection.execute(
            "SELECT * FROM legacy_import_receipts "
            "WHERE stream_id = ? AND source_path = ? "
            "AND status IN ('inventoried', 'imported') "
            "ORDER BY import_id ASC LIMIT 1",
            (stream_id, source_path),
        ).fetchone()
        if row is not None:
            return dict(row)
        row = connection.execute(
            "SELECT * FROM legacy_import_receipts "
            "WHERE stream_id = ? AND source_path = ? "
            "ORDER BY import_id ASC LIMIT 1",
            (stream_id, source_path),
        ).fetchone()
        return dict(row) if row is not None else None


def _latest_projection_for_path(
    store: SessionStreamStore,
    *,
    stream_id: str,
    target_path: str,
) -> dict[str, Any] | None:
    with store._read_snapshot() as connection:
        row = connection.execute(
            "SELECT * FROM legacy_projection_receipts "
            "WHERE stream_id = ? AND target_path = ? "
            "ORDER BY projection_id DESC LIMIT 1",
            (stream_id, target_path),
        ).fetchone()
        return dict(row) if row is not None else None


def _last_ok_projection_sha(
    store: SessionStreamStore,
    *,
    stream_id: str,
    target_path: str,
) -> str:
    with store._read_snapshot() as connection:
        row = connection.execute(
            "SELECT target_sha256 FROM legacy_projection_receipts "
            "WHERE stream_id = ? AND target_path = ? AND status = 'ok' "
            "ORDER BY projection_id DESC LIMIT 1",
            (stream_id, target_path),
        ).fetchone()
        return str(row["target_sha256"]) if row is not None else ""


def _db_mirror_payload(
    store: SessionStreamStore,
    *,
    stream_id: str,
    target_path: str,
) -> tuple[str | None, int | None, int | None]:
    """Return (entry_body, entry_id, high_water) when a legacy mirror exists for path."""
    with store._read_snapshot() as connection:
        high_water_row = connection.execute(
            "SELECT COALESCE(MAX(entry_id), 0) AS n FROM entries WHERE stream_id = ?",
            (stream_id,),
        ).fetchone()
        high_water = int(high_water_row["n"]) if high_water_row else 0
        mirror = connection.execute(
            "SELECT m.entry_id, e.body FROM legacy_mirrors m "
            "JOIN entries e ON e.entry_id = m.entry_id "
            "WHERE m.stream_id = ? AND m.source_path = ? "
            "ORDER BY m.mirror_id DESC LIMIT 1",
            (stream_id, target_path),
        ).fetchone()
        if mirror is None:
            return None, None, high_water if high_water else None
        return str(mirror["body"]), int(mirror["entry_id"]), high_water if high_water else None


def _migration_mode(store: SessionStreamStore, stream_id: str) -> str:
    with store._read_snapshot() as connection:
        row = connection.execute(
            "SELECT mode FROM stream_migration_state WHERE stream_id = ?",
            (stream_id,),
        ).fetchone()
        if row is None:
            return "inventory"
        return str(row["mode"])


def _choose_target_path(root: Path, candidates: Sequence[str]) -> str:
    """Prefer first existing candidate; otherwise first declared path."""
    for rel in candidates:
        if (root / rel).is_file():
            return rel
    return candidates[0] if candidates else ""


def _build_projection_body(
    *,
    stream_id: str,
    target_path: str,
    mode: str,
    source: str,
    target_sha256: str,
    high_water_entry_id: int | None,
    content: str,
    inventoried_sha256: str,
    unrecorded_mutation: bool,
) -> str:
    payload = {
        "kind": PROJECTION_KIND,
        "stream_id": stream_id,
        "target_path": target_path,
        "mode": mode,
        "source": source,
        "target_sha256": target_sha256,
        "high_water_entry_id": high_water_entry_id,
        "inventoried_sha256": inventoried_sha256,
        "unrecorded_mutation": unrecorded_mutation,
        "content_sha256": sha256_text(content) if content else "",
        "content": content,
        "cutover": CUTOVER_BLOCKED,
    }
    return canonical_json(payload)


def classify_file_projection(
    *,
    file_exists: bool,
    file_sha256: str,
    inventoried_sha256: str,
    invent_status: str | None,
    db_body: str | None,
    file_body: str,
) -> tuple[str, str, bool, str]:
    """Return (status, error, unrecorded_mutation, source).

    Status vocabulary matches ``legacy_projection_receipts.status``.
    """
    if db_body is not None:
        source = "db_mirror"
        db_sha = hashlib.sha256(db_body.encode("utf-8")).hexdigest()
        if not file_exists:
            return (
                "failed",
                "dual-write projection target missing; DB mirror cannot land on disk",
                False,
                source,
            )
        if file_sha256 != db_sha:
            mutation = bool(inventoried_sha256) and file_sha256 != inventoried_sha256
            return (
                "drift",
                "file diverges from DB-first projection body",
                mutation or (bool(inventoried_sha256) and file_sha256 != inventoried_sha256),
                source,
            )
        if inventoried_sha256 and file_sha256 != inventoried_sha256:
            # File matches DB but not last inventory — still unrecorded mutation
            # relative to import receipts; surface as drift for operator review.
            return (
                "drift",
                "unrecorded file mutation since last import receipt",
                True,
                source,
            )
        return "ok", "", False, source

    # No DB mirror yet — inventory/shadow observation only.
    if not file_exists:
        if invent_status == "missing" or invent_status is None:
            return "ok", "", False, "missing"
        return (
            "failed",
            "inventoried handoff file is now missing",
            True,
            "missing",
        )

    source = "file_shadow"
    if invent_status is None:
        return (
            "failed",
            "stream path has no import receipt; register inventory first",
            False,
            source,
        )
    if invent_status == "missing":
        # Was missing at inventory; now present → unrecorded creation.
        return (
            "drift",
            "handoff file appeared after inventory recorded missing",
            True,
            source,
        )
    if inventoried_sha256 and file_sha256 != inventoried_sha256:
        return (
            "drift",
            "unrecorded file mutation since last import receipt",
            True,
            source,
        )
    return "ok", "", False, source


def project_inventory_streams(
    store: SessionStreamStore,
    repo_root: Path,
    *,
    streams_yaml: Path | None = None,
    stream_ids: Sequence[str] | None = None,
    ensure_inventory: bool = True,
    agent: str = "system",
    now: datetime | None = None,
) -> ProjectionBatchResult:
    """Write projection receipts for each inventoried epic (no file rewrite).

    When ``ensure_inventory`` is true, registers the manifest first so every epic
    has import receipts to compare against. Never advances mode past inventory
    and never opens leases.
    """
    root = repo_root.resolve()
    path = resolve_streams_yaml(root, streams_yaml)
    if ensure_inventory:
        register_manifest_inventory(
            store, root, streams_yaml=path, agent=agent, now=now
        )
    else:
        # Materialize schema so read-only baseline probes work on a fresh DB.
        with store._transaction(now=now):
            pass
    records = load_stream_epic_inventory(root, streams_yaml=path)
    wanted = set(stream_ids) if stream_ids is not None else None
    results: list[StreamProjectionResult] = []
    new_receipts = 0

    for rec in records:
        if wanted is not None and rec.stream_id not in wanted:
            continue
        if not rec.handoff_candidates:
            continue
        target_path = _choose_target_path(root, rec.handoff_candidates)
        file_exists, file_sha, file_body = _read_target(root, target_path)
        # Drift baseline: last ok projection wins, else earliest inventory import.
        # Do not use the latest import alone — re-inventory after mutation would
        # silently re-hash the new file and hide unrecorded edits.
        ok_proj_sha = _last_ok_projection_sha(
            store, stream_id=rec.stream_id, target_path=target_path
        )
        baseline = _baseline_import_for_path(
            store, stream_id=rec.stream_id, source_path=target_path
        )
        latest_import = _latest_import_for_path(
            store, stream_id=rec.stream_id, source_path=target_path
        )
        invent_status = (
            str(baseline["status"])
            if baseline is not None
            else (str(latest_import["status"]) if latest_import else None)
        )
        inventoried_sha = ok_proj_sha or (
            str(baseline["source_sha256"]) if baseline is not None else ""
        )
        db_body, entry_id, high_water = _db_mirror_payload(
            store, stream_id=rec.stream_id, target_path=target_path
        )
        mode = _migration_mode(store, rec.stream_id)
        if mode not in {"inventory", "shadow", "dual_write"}:
            # Structure-only slice: refuse to pretend cutover modes are active.
            mode = "inventory"

        status, error, unrecorded_mutation, source = classify_file_projection(
            file_exists=file_exists,
            file_sha256=file_sha,
            inventoried_sha256=inventoried_sha,
            invent_status=invent_status,
            db_body=db_body,
            file_body=file_body,
        )

        content = db_body if db_body is not None else file_body
        high_water_entry_id = entry_id if entry_id is not None else high_water
        body = _build_projection_body(
            stream_id=rec.stream_id,
            target_path=target_path,
            mode=mode,
            source=source,
            target_sha256=file_sha,
            high_water_entry_id=high_water_entry_id,
            content=content,
            inventoried_sha256=inventoried_sha,
            unrecorded_mutation=unrecorded_mutation,
        )
        projection_hash = sha256_text(body)
        before = _latest_projection_for_path(
            store, stream_id=rec.stream_id, target_path=target_path
        )
        was_new = (
            before is None
            or str(before.get("projection_hash")) != projection_hash
            or str(before.get("status")) != status
        )
        projection_id = record_projection_receipt(
            store,
            stream_id=rec.stream_id,
            target_path=target_path,
            target_sha256=file_sha,
            projection_body=body,
            status=status,
            high_water_entry_id=high_water_entry_id,
            error=error,
            agent=agent,
            now=now,
        )
        if was_new:
            new_receipts += 1

        results.append(
            StreamProjectionResult(
                stream_id=rec.stream_id,
                target_path=target_path,
                status=status,
                projection_id=projection_id,
                target_sha256=file_sha,
                high_water_entry_id=high_water_entry_id,
                projection_hash=projection_hash,
                error=error,
                file_exists=file_exists,
                unrecorded_mutation=unrecorded_mutation,
                source=source,
                mode=mode,
            )
        )

    ok = sum(1 for s in results if s.status == "ok")
    drift = sum(1 for s in results if s.status == "drift")
    failed = sum(1 for s in results if s.status == "failed")
    return ProjectionBatchResult(
        epic_count=len(results),
        receipts_written=new_receipts,
        ok=ok,
        drift=drift,
        failed=failed,
        streams=tuple(results),
    )


def detect_projection_drift(
    store: SessionStreamStore,
    repo_root: Path,
    *,
    streams_yaml: Path | None = None,
    stream_ids: Sequence[str] | None = None,
    ensure_inventory: bool = False,
    agent: str = "system",
    now: datetime | None = None,
) -> ProjectionBatchResult:
    """Record projection receipts and return drift-focused batch result.

    Same path as :func:`project_inventory_streams`; named for the drift-detection
    hook surface (structure only — no SessionStart / launcher wiring).
    """
    return project_inventory_streams(
        store,
        repo_root,
        streams_yaml=streams_yaml,
        stream_ids=stream_ids,
        ensure_inventory=ensure_inventory,
        agent=agent,
        now=now,
    )


def list_projection_receipts(
    store: SessionStreamStore,
    *,
    stream_id: str | None = None,
) -> list[dict[str, Any]]:
    """Return projection receipts ordered by projection_id."""
    with store._read_snapshot() as connection:
        if stream_id is None:
            rows = connection.execute(
                "SELECT * FROM legacy_projection_receipts ORDER BY projection_id"
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM legacy_projection_receipts WHERE stream_id = ? "
                "ORDER BY projection_id",
                (stream_id,),
            ).fetchall()
        return [dict(row) for row in rows]
