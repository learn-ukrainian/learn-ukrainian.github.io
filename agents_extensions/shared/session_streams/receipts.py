"""Import / projection / inventory receipt registration (Sol PR-H / #5512).

Registers every epic from ``issue_streams.yaml`` into the session-stream DB at
migration mode ``inventory``. Does not open leases, flip cutover defaults, or
touch launchers.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .inventory import (
    DEFAULT_STREAMS_YAML,
    resolve_streams_yaml,
    scan_stream_epic_inventory,
    streams_yaml_sha256,
)
from .model import isoformat_z, sha256_text, utc_now
from .store import SessionStreamStore


@dataclass(frozen=True, slots=True)
class InventoryRegistrationResult:
    """Outcome of one ``register_manifest_inventory`` call."""

    source: str
    source_sha256: str
    epic_count: int
    registered_stream_ids: tuple[str, ...]
    new_inventory_receipts: int
    import_receipts_written: int
    modes: dict[str, str]
    records: int = 0
    skipped: int = 0
    no_op: bool = False


MAX_HANDOFF_BYTES = 1_048_576


def _source_label(root: Path, path: Path) -> str:
    """Return a stable non-absolute source label for receipts and CLI output."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name or str(DEFAULT_STREAMS_YAML)


def _prepare_handoff_imports(
    records: tuple[Any, ...],
    handoff_root: Path,
) -> list[tuple[str, str, str, int, str]]:
    """Read bounded handoff candidates before the lease-critical transaction."""
    prepared: list[tuple[str, str, str, int, str]] = []
    root = handoff_root.resolve()
    for record in records:
        for relative in record.handoff_candidates:
            candidate = Path(relative)
            try:
                resolved = (root / candidate).resolve()
                resolved.relative_to(root)
            except (OSError, ValueError):
                continue
            try:
                if not resolved.is_file():
                    prepared.append((record.stream_id, relative, "", 0, "missing"))
                    continue
                size = resolved.stat().st_size
                if size > MAX_HANDOFF_BYTES:
                    prepared.append((record.stream_id, relative, "", 0, "review_required"))
                    continue
                raw = resolved.read_bytes()
            except OSError:
                prepared.append((record.stream_id, relative, "", 0, "review_required"))
                continue
            prepared.append(
                (
                    record.stream_id,
                    relative,
                    hashlib.sha256(raw).hexdigest(),
                    len(raw),
                    "inventoried",
                )
            )
    return prepared


def _modes_for(store: SessionStreamStore, stream_ids: set[str]) -> dict[str, str]:
    try:
        return store.inventory_modes(stream_ids)
    except Exception:
        return {}


def register_manifest_inventory(
    store: SessionStreamStore,
    repo_root: Path,
    *,
    streams_yaml: Path | None = None,
    agent: str = "system",
    now: datetime | None = None,
    handoff_root: Path | None = None,
    read_handoff_files: bool = True,
) -> InventoryRegistrationResult:
    """Ensure every manifest epic is registered with inventory receipts.

    ``repo_root`` is the immutable registry root. ``handoff_root`` is the
    optional live-data root used only by the manual CLI path. Startup passes
    ``read_handoff_files=False`` so no filesystem-heavy work occurs while the
    store's write transaction is held. Never advances mode past ``inventory``.
    """
    root = repo_root.resolve()
    path = resolve_streams_yaml(root, streams_yaml)
    source_sha = streams_yaml_sha256(root, streams_yaml=path)
    source_rel = _source_label(root, path)
    handoff_base = (handoff_root or root).resolve()
    scan = scan_stream_epic_inventory(root, streams_yaml=path, handoff_root=handoff_base)
    records = scan.records
    timestamp = isoformat_z(now or utc_now())

    # This read-only comparison is deliberately before BEGIN IMMEDIATE. A
    # repeat startup against the same snapshot is a true database no-op.
    try:
        previous_source_sha = store.latest_inventory_source_sha()
    except Exception:
        previous_source_sha = None
    if previous_source_sha == source_sha and not read_handoff_files:
        stream_ids = {record.stream_id for record in records}
        return InventoryRegistrationResult(
            source=source_rel,
            source_sha256=source_sha,
            epic_count=len(records),
            registered_stream_ids=tuple(record.stream_id for record in records),
            new_inventory_receipts=0,
            import_receipts_written=0,
            modes=_modes_for(store, stream_ids),
            records=len(records),
            skipped=scan.skipped,
            no_op=True,
        )

    prepared_imports = (
        _prepare_handoff_imports(records, handoff_base) if read_handoff_files else []
    )
    new_inventory = 0
    import_written = 0
    modes: dict[str, str] = {}
    registered: list[str] = []

    with store._transaction(now=now) as connection:
        for rec in records:
            store._ensure_stream(
                connection, stream_id=rec.stream_id, created_at=timestamp
            )
            registered.append(rec.stream_id)
            handoff_json = json.dumps(list(rec.handoff_candidates), ensure_ascii=False, sort_keys=True)
            cursor = connection.execute(
                "INSERT OR IGNORE INTO stream_inventory_receipts("
                "stream_id, stream_name, epic_number, title, source_path, "
                "source_sha256, handoff_candidates_json, recorded_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    rec.stream_id,
                    rec.stream_name,
                    rec.epic_number,
                    rec.title,
                    source_rel,
                    source_sha,
                    handoff_json,
                    timestamp,
                ),
            )
            if cursor.rowcount:
                new_inventory += 1
                connection.execute(
                    "INSERT INTO stream_control_events("
                    "stream_id, event_type, from_mode, to_mode, proof_json, "
                    "recorded_at, agent, reason"
                    ") VALUES (?, 'inventory_registered', NULL, 'inventory', ?, ?, ?, ?)",
                    (
                        rec.stream_id,
                        json.dumps(
                            {
                                "source": source_rel,
                                "source_sha256": source_sha,
                                "stream_name": rec.stream_name,
                                "epic_number": rec.epic_number,
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                        timestamp,
                        agent,
                        f"registered {rec.stream_id} from issue_streams.yaml",
                    ),
                )

            existing = connection.execute(
                "SELECT mode, version FROM stream_migration_state WHERE stream_id = ?",
                (rec.stream_id,),
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO stream_migration_state("
                    "stream_id, mode, stream_name, title, inventoried_at, updated_at, "
                    "inventory_source, version"
                    ") VALUES (?, 'inventory', ?, ?, ?, ?, ?, 1)",
                    (
                        rec.stream_id,
                        rec.stream_name,
                        rec.title,
                        timestamp,
                        timestamp,
                        source_rel,
                    ),
                )
                modes[rec.stream_id] = "inventory"
            else:
                modes[rec.stream_id] = str(existing["mode"])
                connection.execute(
                    "UPDATE stream_migration_state SET stream_name = ?, title = ?, "
                    "updated_at = ?, inventory_source = ?, version = version + 1 "
                    "WHERE stream_id = ?",
                    (rec.stream_name, rec.title, timestamp, source_rel, rec.stream_id),
                )

        for stream_id, rel, file_sha, source_bytes, status in prepared_imports:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO legacy_import_receipts("
                "stream_id, source_path, source_sha256, source_bytes, status, "
                "recorded_at, entry_id"
                ") VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (stream_id, rel, file_sha, source_bytes, status, timestamp),
            )
            if cursor.rowcount:
                import_written += 1

    return InventoryRegistrationResult(
        source=source_rel,
        source_sha256=source_sha,
        epic_count=len(records),
        registered_stream_ids=tuple(registered),
        new_inventory_receipts=new_inventory,
        import_receipts_written=import_written,
        modes=modes,
        records=len(records),
        skipped=scan.skipped,
        no_op=False,
    )


def record_projection_receipt(
    store: SessionStreamStore,
    *,
    stream_id: str,
    target_path: str,
    target_sha256: str,
    projection_body: str,
    status: str,
    high_water_entry_id: int | None = None,
    error: str = "",
    agent: str = "system",
    now: datetime | None = None,
) -> int:
    """Append one legacy projection receipt (ok / failed / drift).

    Idempotent for the unique key
    ``(stream_id, target_path, projection_hash, status)``. Drift/failed control
    events are only inserted when a new receipt row is written.
    """
    if status not in {"ok", "failed", "drift"}:
        raise ValueError(f"invalid projection status: {status}")
    if target_sha256 and len(target_sha256) != 64:
        raise ValueError("target_sha256 must be empty or a SHA-256 hex digest")
    projection_hash = sha256_text(projection_body)
    timestamp = isoformat_z(now or utc_now())
    with store._transaction(now=now) as connection:
        store._ensure_stream(connection, stream_id=stream_id, created_at=timestamp)
        cursor = connection.execute(
            "INSERT OR IGNORE INTO legacy_projection_receipts("
            "stream_id, target_path, target_sha256, high_water_entry_id, "
            "projection_hash, status, recorded_at, error"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                stream_id,
                target_path,
                target_sha256,
                high_water_entry_id,
                projection_hash,
                status,
                timestamp,
                error,
            ),
        )
        inserted = bool(cursor.rowcount)
        row = connection.execute(
            "SELECT projection_id FROM legacy_projection_receipts "
            "WHERE stream_id = ? AND target_path = ? AND projection_hash = ? AND status = ? "
            "ORDER BY projection_id DESC LIMIT 1",
            (stream_id, target_path, projection_hash, status),
        ).fetchone()
        assert row is not None
        if inserted and status in {"failed", "drift"}:
            connection.execute(
                "INSERT INTO stream_control_events("
                "stream_id, event_type, from_mode, to_mode, proof_json, "
                "recorded_at, agent, reason"
                ") VALUES (?, 'drift_detected', NULL, NULL, ?, ?, ?, ?)",
                (
                    stream_id,
                    json.dumps(
                        {
                            "target_path": target_path,
                            "status": status,
                            "projection_hash": projection_hash,
                            "error": error,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    timestamp,
                    agent,
                    f"projection {status} for {target_path}",
                ),
            )
        return int(row["projection_id"])


def list_migration_state(store: SessionStreamStore) -> list[dict[str, Any]]:
    """Return current migration mode rows for all registered streams."""
    with store._read_snapshot() as connection:
        rows = connection.execute(
            "SELECT stream_id, mode, stream_name, title, inventoried_at, "
            "updated_at, inventory_source, version "
            "FROM stream_migration_state ORDER BY stream_id"
        ).fetchall()
        return [dict(row) for row in rows]


def inventory_registration_summary(store: SessionStreamStore) -> dict[str, Any]:
    """Counts of inventory / import / projection receipts and modes."""
    with store._read_snapshot() as connection:
        inv = connection.execute("SELECT COUNT(*) AS n FROM stream_inventory_receipts").fetchone()
        imp = connection.execute("SELECT COUNT(*) AS n FROM legacy_import_receipts").fetchone()
        proj = connection.execute("SELECT COUNT(*) AS n FROM legacy_projection_receipts").fetchone()
        modes = connection.execute(
            "SELECT mode, COUNT(*) AS n FROM stream_migration_state GROUP BY mode ORDER BY mode"
        ).fetchall()
        return {
            "inventory_receipts": int(inv["n"]) if inv else 0,
            "import_receipts": int(imp["n"]) if imp else 0,
            "projection_receipts": int(proj["n"]) if proj else 0,
            "modes": {str(row["mode"]): int(row["n"]) for row in modes},
            "default_source": str(DEFAULT_STREAMS_YAML),
            "cutover": "blocked — dual-write only; file handoffs remain authoritative",
        }
