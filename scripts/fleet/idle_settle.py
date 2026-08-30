#!/usr/bin/env python3
"""Conditional settle-event reminder + eligibility-aware idle telemetry (#6976/#6998).

This module never gates a settle on raw idle time. Invalid disposition codes
are rejected as vocabulary errors. A missing dispatch-or-disposition is
recorded as MISSING; a valid code that does not match eligibility is
DISHONEST. ``driver_breadth_report --enforce`` fails those two codes only —
never an idle-seconds threshold. Guardrail-authorized idle (honest
disposition) is not a failure.

Admission control lives here as first-class state (same plane, not a second
controller): explicit WIP limits for authoring / review / CI / worktrees /
disk / integration, plus queue readiness and reason codes.

Eligibility (issue #6976): healthy available lane AND compatible / ready /
valuable / independent item AND quota/capacity AND no WIP / dependency
constraint.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.common.repo_root import main_checkout_root

ROOT = Path(__file__).resolve().parents[2]

EVENT_SCHEMA = "fleet-idle-settle-event.v1"
REPORT_SCHEMA = "fleet-idle-settle.v1"
SNAPSHOT_SCHEMA = "fleet-idle-settle-snapshot.v1"
ADMISSION_SCHEMA = "fleet-admission.v1"

WIP_DIMENSIONS: tuple[str, ...] = (
    "authoring",
    "review",
    "ci",
    "worktrees",
    "disk",
    "integration",
)
WIP_REASON_CODES: dict[str, str] = {
    "authoring": "authoring_wip_cap",
    "review": "review_wip_cap",
    "ci": "ci_capacity",
    "worktrees": "worktree_wip_cap",
    "disk": "disk_capacity",
    "integration": "integration_wip_cap",
}

DISPOSITION_CODES: frozenset[str] = frozenset(
    {
        "dependency_blocked",
        "human_decision",
        "no_ready_work",
        *WIP_REASON_CODES.values(),
    }
)

SETTLE_KINDS: frozenset[str] = frozenset({"dispatch", "review"})
_HEALTHY_STATUSES: frozenset[str] = frozenset({"cool", "warm", "idle"})
_CONSTRAINT_CODES: tuple[str, ...] = tuple(WIP_REASON_CODES.values())
ENFORCE_MISSING = "MISSING"
ENFORCE_DISHONEST = "DISHONEST"


def default_store_path(repo_root: Path | None = None) -> Path:
    root = main_checkout_root(repo_root or ROOT)
    return root / "batch_state" / "idle_settle" / "events.jsonl"


def infer_settle_kind(task_id: str | None) -> str:
    ident = (task_id or "").strip().lower()
    return "review" if ident.startswith("review-") else "dispatch"


def normalize_disposition(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def disposition_accepted(code: str | None) -> bool:
    return code in DISPOSITION_CODES


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def utc_now(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now(UTC)
    if now.tzinfo is None:
        return now.replace(tzinfo=UTC)
    return now.astimezone(UTC)


def format_iso(now: datetime | None = None) -> str:
    return utc_now(now).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class ReadyItem:
    item_id: str
    kind: str = "issue"
    ready: bool = True
    valuable: bool = True
    independent: bool = True
    compatible_lanes: tuple[str, ...] | None = None
    dependency_blocked: bool = False

    def is_fillable(self) -> bool:
        return (
            self.ready
            and self.valuable
            and self.independent
            and not self.dependency_blocked
        )


@dataclass(frozen=True)
class LaneState:
    lane: str
    status: str = "unknown"
    in_flight: int = 0
    will_last: bool | None = None
    quota_ok: bool | None = None

    def is_healthy_available(self) -> bool:
        if self.status not in _HEALTHY_STATUSES:
            return False
        if int(self.in_flight or 0) != 0:
            return False
        if self.quota_ok is False:
            return False
        return self.will_last is not False


def _optional_int(raw: Any) -> int | None:
    if raw is None or raw == "":
        return None
    return int(raw)


@dataclass(frozen=True)
class ResourceCaps:
    authoring_in_flight: int = 0
    authoring_wip_limit: int | None = None
    review_in_flight: int = 0
    review_wip_limit: int | None = None
    ci_in_flight: int = 0
    ci_wip_limit: int | None = None
    ci_capacity_ok: bool = True
    worktrees_in_flight: int = 0
    worktrees_wip_limit: int | None = None
    disk_in_flight: int = 0
    disk_wip_limit: int | None = None
    disk_ok: bool = True
    integration_in_flight: int = 0
    integration_wip_limit: int | None = None

    def dimension_ok(self, name: str) -> bool:
        in_flight = int(getattr(self, f"{name}_in_flight") or 0)
        limit = getattr(self, f"{name}_wip_limit")
        if limit is not None and in_flight >= int(limit):
            return False
        if name == "ci" and self.ci_capacity_ok is False:
            return False
        return not (name == "disk" and self.disk_ok is False)

    def dimension_status(self) -> dict[str, dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}
        for name in WIP_DIMENSIONS:
            ok = self.dimension_ok(name)
            rows[name] = {
                "in_flight": int(getattr(self, f"{name}_in_flight") or 0),
                "limit": getattr(self, f"{name}_wip_limit"),
                "ok": ok,
                "reason_code": None if ok else WIP_REASON_CODES[name],
            }
        return rows

    def active_constraints(self) -> tuple[str, ...]:
        return tuple(
            WIP_REASON_CODES[name] for name in WIP_DIMENSIONS if not self.dimension_ok(name)
        )


@dataclass(frozen=True)
class EligibilitySnapshot:
    lanes: tuple[LaneState, ...] = ()
    items: tuple[ReadyItem, ...] = ()
    caps: ResourceCaps = field(default_factory=ResourceCaps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SNAPSHOT_SCHEMA,
            "lanes": [asdict(lane) for lane in self.lanes],
            "items": [
                {
                    **asdict(item),
                    "compatible_lanes": (
                        None if item.compatible_lanes is None else list(item.compatible_lanes)
                    ),
                }
                for item in self.items
            ],
            "caps": asdict(self.caps),
        }


@dataclass(frozen=True)
class EligiblePair:
    lane: str
    item_id: str


@dataclass(frozen=True)
class AdmissionState:
    """First-class WIP + queue admission (same plane as settle eligibility)."""

    admitted: bool
    queue_ready: bool
    ready_item_count: int
    fillable_item_ids: tuple[str, ...]
    wip: dict[str, dict[str, Any]]
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": ADMISSION_SCHEMA,
            "admitted": self.admitted,
            "queue_ready": self.queue_ready,
            "ready_item_count": self.ready_item_count,
            "fillable_item_ids": list(self.fillable_item_ids),
            "wip": self.wip,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class SettleDecision:
    reminder_required: bool
    reminder_fired: bool
    eligible: bool
    outcome: str
    accepted: bool
    disposition: str | None
    disposition_valid: bool | None
    disposition_honest: bool | None
    dispatched: bool
    eligible_pairs: tuple[EligiblePair, ...]
    eligible_lanes: tuple[str, ...]
    eligible_item_ids: tuple[str, ...]
    active_constraints: tuple[str, ...]
    caps: ResourceCaps
    settle_kind: str
    task_id: str | None
    admission: AdmissionState

    def to_dict(self) -> dict[str, Any]:
        return {
            "reminder_required": self.reminder_required,
            "reminder_fired": self.reminder_fired,
            "eligible": self.eligible,
            "outcome": self.outcome,
            "accepted": self.accepted,
            "disposition": self.disposition,
            "disposition_valid": self.disposition_valid,
            "disposition_honest": self.disposition_honest,
            "dispatched": self.dispatched,
            "eligible_pairs": [asdict(pair) for pair in self.eligible_pairs],
            "eligible_lanes": list(self.eligible_lanes),
            "eligible_item_ids": list(self.eligible_item_ids),
            "active_constraints": list(self.active_constraints),
            "caps": asdict(self.caps),
            "settle_kind": self.settle_kind,
            "task_id": self.task_id,
            "admission": self.admission.to_dict(),
            "report_only": True,
        }


def empty_snapshot() -> EligibilitySnapshot:
    return EligibilitySnapshot()


def parse_snapshot(payload: dict[str, Any] | None) -> EligibilitySnapshot:
    data = payload if isinstance(payload, dict) else {}
    lanes_raw = data.get("lanes") or []
    items_raw = data.get("items") or []
    caps_raw = data.get("caps") if isinstance(data.get("caps"), dict) else {}

    lanes: list[LaneState] = []
    for row in lanes_raw:
        if not isinstance(row, dict):
            continue
        lane = str(row.get("lane") or "").strip()
        if not lane:
            continue
        will_last = row.get("will_last")
        quota_ok = row.get("quota_ok")
        lanes.append(
            LaneState(
                lane=lane,
                status=str(row.get("status") or "unknown"),
                in_flight=int(row.get("in_flight") or 0),
                will_last=None if will_last is None else bool(will_last),
                quota_ok=None if quota_ok is None else bool(quota_ok),
            )
        )

    items: list[ReadyItem] = []
    for row in items_raw:
        if not isinstance(row, dict):
            continue
        item_id = str(row.get("item_id") or "").strip()
        if not item_id:
            continue
        compat = row.get("compatible_lanes")
        compatible: tuple[str, ...] | None
        if compat is None:
            compatible = None
        elif isinstance(compat, (list, tuple)):
            compatible = tuple(str(name).strip() for name in compat if str(name).strip())
        else:
            compatible = None
        items.append(
            ReadyItem(
                item_id=item_id,
                kind=str(row.get("kind") or "issue"),
                ready=bool(row.get("ready", True)),
                valuable=bool(row.get("valuable", True)),
                independent=bool(row.get("independent", True)),
                compatible_lanes=compatible,
                dependency_blocked=bool(row.get("dependency_blocked", False)),
            )
        )

    caps = ResourceCaps(
        authoring_in_flight=int(caps_raw.get("authoring_in_flight") or 0),
        authoring_wip_limit=_optional_int(caps_raw.get("authoring_wip_limit")),
        review_in_flight=int(caps_raw.get("review_in_flight") or 0),
        review_wip_limit=_optional_int(caps_raw.get("review_wip_limit")),
        ci_in_flight=int(caps_raw.get("ci_in_flight") or 0),
        ci_wip_limit=_optional_int(caps_raw.get("ci_wip_limit")),
        ci_capacity_ok=bool(caps_raw.get("ci_capacity_ok", True)),
        worktrees_in_flight=int(caps_raw.get("worktrees_in_flight") or 0),
        worktrees_wip_limit=_optional_int(caps_raw.get("worktrees_wip_limit")),
        disk_in_flight=int(caps_raw.get("disk_in_flight") or 0),
        disk_wip_limit=_optional_int(caps_raw.get("disk_wip_limit")),
        disk_ok=bool(caps_raw.get("disk_ok", True)),
        integration_in_flight=int(caps_raw.get("integration_in_flight") or 0),
        integration_wip_limit=_optional_int(caps_raw.get("integration_wip_limit")),
    )
    return EligibilitySnapshot(lanes=tuple(lanes), items=tuple(items), caps=caps)


def lanes_from_capacity_rows(rows: list[dict[str, Any]] | None) -> tuple[LaneState, ...]:
    lanes: list[LaneState] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        lane = str(row.get("lane") or "").strip()
        if not lane:
            continue
        will_last = row.get("will_last")
        avoid = bool(row.get("avoid"))
        quota_ok = False if avoid else None
        lanes.append(
            LaneState(
                lane=lane,
                status=str(row.get("status") or "unknown"),
                in_flight=int(row.get("in_flight") or 0),
                will_last=None if will_last is None else bool(will_last),
                quota_ok=quota_ok,
            )
        )
    return tuple(lanes)


def items_from_work_next_queue(queue: list[dict[str, Any]] | None) -> tuple[ReadyItem, ...]:
    items: list[ReadyItem] = []
    for row in queue or []:
        if not isinstance(row, dict):
            continue
        item_id = str(row.get("work_id") or row.get("item_id") or "").strip()
        if not item_id:
            continue
        action = row.get("safe_next_action") if isinstance(row.get("safe_next_action"), dict) else {}
        code = str(action.get("code") or "")
        reasons = action.get("reason_codes") or []
        dep_blocked = code == "RESOLVE_BLOCKER" or "blocked_by" in reasons or "dependency_cycle" in reasons
        items.append(
            ReadyItem(
                item_id=item_id,
                kind=str(row.get("resource_kind") or row.get("kind") or "issue"),
                ready=True,
                valuable=True,
                independent=True,
                compatible_lanes=None,
                dependency_blocked=dep_blocked,
            )
        )
    return tuple(items)


def assemble_snapshot(
    *,
    capacity_rows: list[dict[str, Any]] | None = None,
    work_next_queue: list[dict[str, Any]] | None = None,
    authoring_in_flight: int = 0,
    authoring_wip_limit: int | None = None,
    review_in_flight: int = 0,
    review_wip_limit: int | None = None,
    ci_in_flight: int = 0,
    ci_wip_limit: int | None = None,
    ci_capacity_ok: bool = True,
    worktrees_in_flight: int = 0,
    worktrees_wip_limit: int | None = None,
    disk_in_flight: int = 0,
    disk_wip_limit: int | None = None,
    disk_ok: bool = True,
    integration_in_flight: int = 0,
    integration_wip_limit: int | None = None,
) -> EligibilitySnapshot:
    return EligibilitySnapshot(
        lanes=lanes_from_capacity_rows(capacity_rows),
        items=items_from_work_next_queue(work_next_queue),
        caps=ResourceCaps(
            authoring_in_flight=authoring_in_flight,
            authoring_wip_limit=authoring_wip_limit,
            review_in_flight=review_in_flight,
            review_wip_limit=review_wip_limit,
            ci_in_flight=ci_in_flight,
            ci_wip_limit=ci_wip_limit,
            ci_capacity_ok=ci_capacity_ok,
            worktrees_in_flight=worktrees_in_flight,
            worktrees_wip_limit=worktrees_wip_limit,
            disk_in_flight=disk_in_flight,
            disk_wip_limit=disk_wip_limit,
            disk_ok=disk_ok,
            integration_in_flight=integration_in_flight,
            integration_wip_limit=integration_wip_limit,
        ),
    )


def evaluate_admission(snapshot: EligibilitySnapshot) -> AdmissionState:
    fillable = tuple(item.item_id for item in snapshot.items if item.is_fillable())
    queue_ready = bool(fillable)
    wip = snapshot.caps.dimension_status()
    reasons: list[str] = []
    for name in WIP_DIMENSIONS:
        code = wip[name]["reason_code"]
        if code:
            reasons.append(str(code))
    if not queue_ready:
        reasons.append("no_ready_work")
    reason_codes = tuple(dict.fromkeys(reasons))
    admitted = all(wip[name]["ok"] for name in WIP_DIMENSIONS) and queue_ready
    return AdmissionState(
        admitted=admitted,
        queue_ready=queue_ready,
        ready_item_count=len(fillable),
        fillable_item_ids=fillable,
        wip=wip,
        reason_codes=reason_codes,
    )


def enforce_fail_codes(report: dict[str, Any] | None) -> tuple[str, ...]:
    """MISSING/DISHONEST only. Never uses eligible idle opportunity-seconds."""
    if not report:
        return ()
    codes: list[str] = []
    if int(report.get("settle_events_missing_action") or 0) > 0:
        codes.append(ENFORCE_MISSING)
    if int(report.get("settle_events_dishonest") or 0) > 0:
        codes.append(ENFORCE_DISHONEST)
    return tuple(codes)


def eligible_pairs(snapshot: EligibilitySnapshot) -> tuple[EligiblePair, ...]:
    constraints = snapshot.caps.active_constraints()
    if constraints:
        return ()
    pairs: list[EligiblePair] = []
    healthy = [lane for lane in snapshot.lanes if lane.is_healthy_available()]
    for item in snapshot.items:
        if not item.is_fillable():
            continue
        for lane in healthy:
            if item.compatible_lanes is not None and lane.lane not in item.compatible_lanes:
                continue
            pairs.append(EligiblePair(lane=lane.lane, item_id=item.item_id))
    return tuple(pairs)


def disposition_is_honest(snapshot: EligibilitySnapshot, code: str | None, *, eligible: bool) -> bool | None:
    if code is None:
        return None
    if code not in DISPOSITION_CODES:
        return None
    if code == "human_decision":
        return True
    constraints = set(snapshot.caps.active_constraints())
    if code == "no_ready_work":
        return not eligible
    if code in _CONSTRAINT_CODES:
        return code in constraints
    if code == "dependency_blocked":
        return (not eligible) and any(item.dependency_blocked for item in snapshot.items)
    return False


def evaluate_settle(
    snapshot: EligibilitySnapshot,
    *,
    dispatched: bool = False,
    disposition: str | None = None,
    settle_kind: str = "dispatch",
    task_id: str | None = None,
) -> SettleDecision:
    kind = settle_kind if settle_kind in SETTLE_KINDS else infer_settle_kind(task_id)
    code = normalize_disposition(disposition)
    pairs = eligible_pairs(snapshot)
    eligible = bool(pairs)
    lanes = tuple(dict.fromkeys(pair.lane for pair in pairs))
    item_ids = tuple(dict.fromkeys(pair.item_id for pair in pairs))
    constraints = snapshot.caps.active_constraints()
    admission = evaluate_admission(snapshot)

    if code is not None and not disposition_accepted(code):
        return SettleDecision(
            reminder_required=eligible,
            reminder_fired=eligible,
            eligible=eligible,
            outcome="invalid_disposition",
            accepted=False,
            disposition=code,
            disposition_valid=False,
            disposition_honest=None,
            dispatched=bool(dispatched),
            eligible_pairs=pairs,
            eligible_lanes=lanes,
            eligible_item_ids=item_ids,
            active_constraints=constraints,
            caps=snapshot.caps,
            settle_kind=kind,
            task_id=task_id,
            admission=admission,
        )

    honest = disposition_is_honest(snapshot, code, eligible=eligible)
    if not eligible:
        return SettleDecision(
            reminder_required=False,
            reminder_fired=False,
            eligible=False,
            outcome="silent" if code is None else "disposed",
            accepted=True,
            disposition=code,
            disposition_valid=None if code is None else True,
            disposition_honest=honest,
            dispatched=bool(dispatched),
            eligible_pairs=(),
            eligible_lanes=(),
            eligible_item_ids=(),
            active_constraints=constraints,
            caps=snapshot.caps,
            settle_kind=kind,
            task_id=task_id,
            admission=admission,
        )

    if dispatched:
        outcome = "dispatched"
        accepted = True
        reminder_required = False
        reminder_fired = False
    elif code is not None:
        outcome = "disposed"
        accepted = True
        reminder_required = False
        reminder_fired = False
    else:
        outcome = "missing_action"
        accepted = False
        reminder_required = True
        reminder_fired = True

    return SettleDecision(
        reminder_required=reminder_required,
        reminder_fired=reminder_fired,
        eligible=True,
        outcome=outcome,
        accepted=accepted,
        disposition=code,
        disposition_valid=None if code is None else True,
        disposition_honest=honest,
        dispatched=bool(dispatched),
        eligible_pairs=pairs,
        eligible_lanes=lanes,
        eligible_item_ids=item_ids,
        active_constraints=constraints,
        caps=snapshot.caps,
        settle_kind=kind,
        task_id=task_id,
        admission=admission,
    )


def format_reminder(decision: SettleDecision, snapshot: EligibilitySnapshot) -> str | None:
    if not decision.eligible:
        return None
    lines = [
        "SETTLE REMINDER: eligible ready work exists.",
        f"  kind={decision.settle_kind} task_id={decision.task_id or '-'}",
        f"  eligible_items={len(decision.eligible_item_ids)} eligible_lanes={','.join(decision.eligible_lanes) or '-'}",
    ]
    by_item: dict[str, list[str]] = {}
    for pair in decision.eligible_pairs:
        by_item.setdefault(pair.item_id, []).append(pair.lane)
    item_meta = {item.item_id: item for item in snapshot.items}
    for item_id, lanes in by_item.items():
        meta = item_meta.get(item_id)
        kind = meta.kind if meta is not None else "item"
        lines.append(f"  - {item_id} ({kind}) lanes={','.join(lanes)}")
    caps = decision.caps
    limit = "-" if caps.review_wip_limit is None else str(caps.review_wip_limit)
    wip = caps.dimension_status()
    extra = []
    for name in ("authoring", "worktrees", "integration"):
        row = wip[name]
        dim_limit = "-" if row["limit"] is None else str(row["limit"])
        extra.append(f"{name}={row['in_flight']}/{dim_limit}")
    lines.append(
        "  caps: "
        f"review_wip={caps.review_in_flight}/{limit} "
        f"ci_in_flight={caps.ci_in_flight} ci_ok={caps.ci_capacity_ok} "
        f"disk_ok={caps.disk_ok} " + " ".join(extra)
    )
    admission = decision.admission
    lines.append(
        "  admission: "
        f"admitted={admission.admitted} queue_ready={admission.queue_ready} "
        f"ready={admission.ready_item_count} "
        f"reasons={','.join(admission.reason_codes) or '-'}"
    )
    if decision.reminder_required:
        lines.append(
            "  ACTION REQUIRED: dispatch a compatible ready item, or pass "
            "--disposition with one of: " + " | ".join(sorted(DISPOSITION_CODES))
        )
    else:
        lines.append(f"  satisfied via {decision.outcome}")
    return "\n".join(lines)


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return []
    for line in raw.splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def opportunity_seconds_since(previous: dict[str, Any] | None, now: datetime) -> float:
    if not previous or not previous.get("eligible"):
        return 0.0
    prev_at = parse_iso(str(previous.get("recorded_at") or "") or None)
    if prev_at is None:
        return 0.0
    delta = (utc_now(now) - prev_at).total_seconds()
    return max(0.0, float(delta))


def build_event(
    decision: SettleDecision,
    *,
    previous: dict[str, Any] | None = None,
    now: datetime | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    stamp = utc_now(now)
    return {
        "schema": EVENT_SCHEMA,
        "event_id": event_id or uuid.uuid4().hex,
        "recorded_at": format_iso(stamp),
        "settle_kind": decision.settle_kind,
        "task_id": decision.task_id,
        "eligible": decision.eligible,
        "eligible_item_ids": list(decision.eligible_item_ids),
        "eligible_lanes": list(decision.eligible_lanes),
        "active_constraints": list(decision.active_constraints),
        "dispatched": decision.dispatched,
        "disposition": decision.disposition,
        "disposition_valid": decision.disposition_valid,
        "disposition_honest": decision.disposition_honest,
        "reminder_fired": decision.reminder_fired,
        "outcome": decision.outcome,
        "opportunity_seconds_since_prev": opportunity_seconds_since(previous, stamp),
        "report_only": True,
    }


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def record_settle(
    path: Path,
    decision: SettleDecision,
    *,
    now: datetime | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    events = load_events(path)
    previous = events[-1] if events else None
    event = build_event(decision, previous=previous, now=now, event_id=event_id)
    append_event(path, event)
    return event


def build_report(events: list[dict[str, Any]], *, enforce: bool = False) -> dict[str, Any]:
    opportunity = 0.0
    missing = 0
    invalid = 0
    dishonest = 0
    dispatched = 0
    disposed = 0
    silent = 0
    reminders = 0
    for event in events:
        opportunity += float(event.get("opportunity_seconds_since_prev") or 0.0)
        outcome = str(event.get("outcome") or "")
        if outcome == "missing_action":
            missing += 1
        elif outcome == "invalid_disposition":
            invalid += 1
        elif outcome == "dispatched":
            dispatched += 1
        elif outcome == "disposed":
            disposed += 1
        elif outcome == "silent":
            silent += 1
        if event.get("reminder_fired"):
            reminders += 1
        if event.get("disposition_honest") is False:
            dishonest += 1
    counts = {
        "settle_events_missing_action": missing,
        "settle_events_dishonest": dishonest,
    }
    fail_codes = enforce_fail_codes(counts)
    return {
        "schema": REPORT_SCHEMA,
        "report_only": not enforce,
        "enforce_disposition": enforce,
        "enforce_fail_codes": list(fail_codes),
        "idle_seconds_never_enforce": True,
        "event_count": len(events),
        "eligible_idle_opportunity_seconds": opportunity,
        "settle_events_missing_action": missing,
        "settle_events_invalid_disposition": invalid,
        "settle_events_dishonest": dishonest,
        "settle_events_dispatched": dispatched,
        "settle_events_disposed": disposed,
        "settle_events_silent": silent,
        "reminder_fired_count": reminders,
    }


def format_report(report: dict[str, Any]) -> str:
    fail = report.get("enforce_fail_codes") or []
    return (
        f"fleet-idle-settle report_only={report.get('report_only')} "
        f"events={report.get('event_count')} "
        f"eligible_idle_opportunity_seconds={report.get('eligible_idle_opportunity_seconds')} "
        f"missing_action={report.get('settle_events_missing_action')} "
        f"invalid_disposition={report.get('settle_events_invalid_disposition')} "
        f"dishonest={report.get('settle_events_dishonest')} "
        f"enforce_fail_codes={','.join(fail) or '-'}"
    )


def format_admission(state: AdmissionState) -> str:
    wip_bits = []
    for name in WIP_DIMENSIONS:
        row = state.wip[name]
        limit = "-" if row["limit"] is None else str(row["limit"])
        flag = "ok" if row["ok"] else str(row["reason_code"])
        wip_bits.append(f"{name}={row['in_flight']}/{limit}:{flag}")
    return (
        f"fleet-admission admitted={state.admitted} "
        f"queue_ready={state.queue_ready} ready={state.ready_item_count} "
        f"reasons={','.join(state.reason_codes) or '-'} "
        f"wip[{' '.join(wip_bits)}]"
    )


def _load_json_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def run_evaluate(
    *,
    snapshot: EligibilitySnapshot,
    dispatched: bool = False,
    disposition: str | None = None,
    settle_kind: str = "dispatch",
    task_id: str | None = None,
    store: Path | None = None,
    record: bool = True,
    now: datetime | None = None,
    as_json: bool = False,
    out=None,
    err=None,
) -> tuple[int, SettleDecision, dict[str, Any] | None]:
    stdout = out if out is not None else sys.stdout
    stderr = err if err is not None else sys.stderr
    decision = evaluate_settle(
        snapshot,
        dispatched=dispatched,
        disposition=disposition,
        settle_kind=settle_kind,
        task_id=task_id,
    )
    event: dict[str, Any] | None = None
    if record and store is not None:
        event = record_settle(store, decision, now=now)
    payload = decision.to_dict()
    if event is not None:
        payload["event"] = event
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), file=stdout)
    else:
        text = format_reminder(decision, snapshot)
        if text:
            print(text, file=stdout)
        elif decision.outcome == "invalid_disposition":
            print(
                f"idle_settle: rejected disposition {decision.disposition!r}; "
                f"accepted: {' | '.join(sorted(DISPOSITION_CODES))}",
                file=stderr,
            )
    rc = 2 if decision.outcome == "invalid_disposition" else 0
    return rc, decision, event


def _cmd_evaluate(args: argparse.Namespace) -> int:
    if args.snapshot_json is not None:
        snapshot = parse_snapshot(_load_json_file(args.snapshot_json))
    else:
        snapshot = empty_snapshot()
    kind = args.kind or infer_settle_kind(args.task_id)
    store = args.store if not args.no_record else None
    rc, _decision, _event = run_evaluate(
        snapshot=snapshot,
        dispatched=bool(args.dispatched),
        disposition=args.disposition,
        settle_kind=kind,
        task_id=args.task_id,
        store=store,
        record=not args.no_record,
        as_json=bool(args.json),
    )
    return rc


def _cmd_report(args: argparse.Namespace) -> int:
    report = build_report(load_events(args.store))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_report(report))
    return 0


def _cmd_admission(args: argparse.Namespace) -> int:
    if args.snapshot_json is not None:
        snapshot = parse_snapshot(_load_json_file(args.snapshot_json))
    else:
        snapshot = empty_snapshot()
    state = evaluate_admission(snapshot)
    if args.json:
        print(json.dumps(state.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_admission(state))
    return 0 if state.admitted else 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    evaluate = sub.add_parser(
        "evaluate",
        help="Evaluate one dispatch/review settle: reminder + optional JSONL record",
    )
    evaluate.add_argument("--snapshot-json", type=Path, help="Eligibility snapshot JSON")
    evaluate.add_argument("--task-id", default=None)
    evaluate.add_argument("--kind", choices=sorted(SETTLE_KINDS), default=None)
    evaluate.add_argument("--dispatched", action="store_true")
    evaluate.add_argument(
        "--disposition",
        default=None,
        help="One of: " + " | ".join(sorted(DISPOSITION_CODES)),
    )
    evaluate.add_argument(
        "--store",
        type=Path,
        default=default_store_path(),
        help="Append-only events JSONL (default: batch_state/idle_settle/events.jsonl)",
    )
    evaluate.add_argument("--no-record", action="store_true")
    evaluate.add_argument("--json", action="store_true")
    evaluate.set_defaults(func=_cmd_evaluate)

    report = sub.add_parser("report", help="Print report-only idle/disposition telemetry")
    report.add_argument("--store", type=Path, default=default_store_path())
    report.add_argument("--json", action="store_true")
    report.set_defaults(func=_cmd_report)

    admission = sub.add_parser(
        "admission",
        help="Evaluate first-class WIP admission (authoring/review/CI/worktrees/disk/integration)",
    )
    admission.add_argument("--snapshot-json", type=Path, help="Eligibility snapshot JSON")
    admission.add_argument("--json", action="store_true")
    admission.set_defaults(func=_cmd_admission)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
