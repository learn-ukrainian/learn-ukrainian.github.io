"""Slot to holder resolution helper for fleet taxonomy (step 4b).

Resolves a slot (e.g. claude-atlas, grok-infra, claude-folk) -> area -> live lease rows
in .agent/session-streams/v1/session-streams.sqlite3.

READ-ONLY: Never writes or mutates the session-streams database.

## Lane NAME vs AREA resolution — the load-bearing mismatch (r2 ruling, #5889)

A slot's NAME carries a lane/track hint, but resolution is **area-centric**,
not lane-centric. The slot name is an addressing convenience only; it does
NOT scope which lease the delivery binds to.

    slot name        area_assignments.yaml      fleet_taxonomy.yaml        lease matched
    -----------      ----------------------      ------------------        -------------
    claude-folk   -> seminars area            -> epics {2836,4431,4215, -> ANY active lease
                    (slots: folk AND bio)         3120,3079}              on ANY of those
                                                                         epics — folk OR bio

So ``claude-folk`` and ``claude-bio`` both resolve through the SAME
``seminars`` area epic union. A delivery addressed to ``claude-folk`` is
pickable by whichever driver holds an active ``seminars`` lease — including
a bio-track driver, because the area unions folk + bio + cross epics. The
``folk``/``bio`` suffix in the slot name is a naming hint, not a resolution
filter.

This is intentional per the r2 ruling and is NOT to be changed without an
operator/advisor GO. Per-lane epic scoping (resolving ``claude-folk`` ONLY
to the folk epic 2836) is a documented design decision, out of scope here;
see ``resolve_slot_holder`` below for the current algorithm.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.orchestration.fleet_taxonomy import (
    UnknownAreaError,
    resolve_area,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SESSION_DB_PATH = (
    PROJECT_ROOT / ".agent" / "session-streams" / "v1" / "session-streams.sqlite3"
)
DEFAULT_ASSIGNMENTS_PATH = PROJECT_ROOT / "scripts" / "config" / "area_assignments.yaml"


@dataclass(frozen=True, slots=True)
class SlotHolderResult:
    """Outcome of slot->holder resolution."""

    has_holder: bool
    slot: str
    area_id: str | None = None
    stream_id: str | None = None
    session_id: str | None = None
    holder_agent: str | None = None
    holder_harness: str | None = None
    generation: int | None = None
    expires_at: str | None = None
    queue_location: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to a dictionary representation."""
        return {
            "has_holder": self.has_holder,
            "slot": self.slot,
            "area_id": self.area_id,
            "stream_id": self.stream_id,
            "session_id": self.session_id,
            "holder_agent": self.holder_agent,
            "holder_harness": self.holder_harness,
            "generation": self.generation,
            "expires_at": self.expires_at,
            "queue_location": self.queue_location,
            "reason": self.reason,
        }


def _parse_iso(value: str) -> datetime:
    val = value.strip()
    if val.endswith("Z"):
        val = val[:-1] + "+00:00"
    return datetime.fromisoformat(val).astimezone(UTC)


def _find_area_for_slot(slot: str, assignments_path: Path) -> str | None:
    """Look up slot in area_assignments.yaml to find its area ID."""
    try:
        if not assignments_path.is_file():
            return None
        text = assignments_path.read_text(encoding="utf-8")
        import yaml
        raw_data = yaml.safe_load(text)
        if not isinstance(raw_data, dict):
            return None
        assignments = raw_data.get("assignments")
        if not isinstance(assignments, dict):
            return None
        for area_id, area_data in assignments.items():
            if isinstance(area_data, dict):
                slots = area_data.get("slots", [])
                if isinstance(slots, (list, tuple)) and slot in slots:
                    return str(area_id)
    except Exception:
        pass
    return None


def resolve_slot_holder(
    slot: str,
    *,
    taxonomy_path: Path | None = None,
    assignments_path: Path | None = None,
    session_db_path: Path | None = None,
    now: datetime | None = None,
) -> SlotHolderResult:
    """Resolve a slot identity to its live lease holder facts.

    Steps:
    1. Look up slot in area_assignments.yaml, or parse slot into provider prefix & area part.
    2. Resolve area via resolve_area() (canonical ID or alias).
    3. Query session-streams DB for active leases matching **the area's full
       epic union** — not a single lane epic.
    4. Return holder facts if an active, non-expired lease exists; else no-holder.

    For multi-epic areas with several live leases, the farthest-expiry lease wins.

    **Area-union resolution (r2 ruling, #5889):** the query matches the whole
    area's epic set, so a lane-named slot resolves to ANY active lease in its
    area. Concretely, ``claude-folk`` and ``claude-bio`` both resolve through
    the ``seminars`` area (epics 2836 folk + 4431/4215 bio + 3120/3079 cross):
    a delivery to ``claude-folk`` is pickable by a bio-track lease holder. The
    lane suffix in the name is an addressing hint, not a per-lane filter.
    Per-lane epic scoping is a future design decision — do not narrow this
    here without an operator/advisor GO.

    READ-ONLY — never writes that DB from this path.
    """
    clean_slot = slot.strip()
    queue_loc = f"channels DB delivery queue for '{clean_slot}'"

    assign_path = (assignments_path or DEFAULT_ASSIGNMENTS_PATH).resolve()
    area_candidate = _find_area_for_slot(clean_slot, assign_path)

    if area_candidate is None:
        if "-" not in clean_slot:
            return SlotHolderResult(
                has_holder=False,
                slot=clean_slot,
                queue_location=queue_loc,
                reason="invalid-slot-format",
            )
        provider, area_part = clean_slot.split("-", 1)
        if not provider or not area_part:
            return SlotHolderResult(
                has_holder=False,
                slot=clean_slot,
                queue_location=queue_loc,
                reason="invalid-slot-format",
            )
        area_candidate = area_part

    try:
        area = resolve_area(area_candidate, taxonomy_path=taxonomy_path)
    except UnknownAreaError:
        return SlotHolderResult(
            has_holder=False,
            slot=clean_slot,
            queue_location=queue_loc,
            reason="unknown-area",
        )

    db_path = (session_db_path or DEFAULT_SESSION_DB_PATH).resolve()
    if not db_path.is_file():
        return SlotHolderResult(
            has_holder=False,
            slot=clean_slot,
            area_id=area.id,
            queue_location=queue_loc,
            reason="no-live-holder",
        )

    epic_stream_ids = [f"epic:{epic.number}" for epic in area.epics]
    if not epic_stream_ids:
        return SlotHolderResult(
            has_holder=False,
            slot=clean_slot,
            area_id=area.id,
            queue_location=queue_loc,
            reason="no-live-holder",
        )

    placeholders = ", ".join("?" for _ in epic_stream_ids)
    query = f"""
        SELECT l.stream_id, l.session_id, l.holder_agent, l.holder_harness,
               l.generation, l.expires_at, l.state AS lease_state, s.state AS session_state
        FROM stream_leases AS l
        JOIN sessions AS s ON s.stream_id = l.stream_id AND s.session_id = l.session_id
        WHERE l.stream_id IN ({placeholders})
          AND l.state = 'active'
          AND s.state IN ('open', 'rolling')
        ORDER BY l.expires_at DESC
    """

    current_time = (now or datetime.now(UTC)).astimezone(UTC)

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(query, epic_stream_ids).fetchall()
        finally:
            conn.close()
    except (sqlite3.Error, OSError) as exc:
        return SlotHolderResult(
            has_holder=False,
            slot=clean_slot,
            area_id=area.id,
            queue_location=queue_loc,
            reason=f"db-error: {exc}",
        )

    if not rows:
        return SlotHolderResult(
            has_holder=False,
            slot=clean_slot,
            area_id=area.id,
            queue_location=queue_loc,
            reason="no-live-holder",
        )

    for row in rows:
        exp_str = str(row["expires_at"] or "")
        if exp_str:
            try:
                exp_dt = _parse_iso(exp_str)
                if exp_dt <= current_time:
                    # Expired lease treated as no-live-holder
                    continue
            except ValueError:
                continue

        return SlotHolderResult(
            has_holder=True,
            slot=clean_slot,
            area_id=area.id,
            stream_id=str(row["stream_id"]),
            session_id=str(row["session_id"]),
            holder_agent=str(row["holder_agent"]),
            holder_harness=str(row["holder_harness"]) if row["holder_harness"] else None,
            generation=int(row["generation"]) if row["generation"] is not None else None,
            expires_at=exp_str,
            queue_location=queue_loc,
        )

    return SlotHolderResult(
        has_holder=False,
        slot=clean_slot,
        area_id=area.id,
        queue_location=queue_loc,
        reason="no-live-holder",
    )
