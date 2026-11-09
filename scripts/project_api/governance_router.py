"""Unified governance state endpoint for decisions and ADRs (#1523)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends

from scripts.api.monitor_context import MonitorContext, get_ctx, resolve_context

from .curriculum_state import monitor_surface

router = APIRouter(tags=["governance"])

APPROACHING_EXPIRY_DAYS = 30

_EMPTY_ADR_GOVERNANCE: dict[str, Any] = {
    "total": 0,
    "stale_proposed_count": 0,
    "error_count": 0,
    "warning_count": 0,
    "broken_chains": [],
    "orphaned_refs": [],
    "promotion_candidates": [],
    "index": [],
}




def _decisions_file(ctx: MonitorContext | None = None) -> Path:
    return resolve_context(ctx).roots.project_root / "docs" / "decisions" / "decisions.yaml"


def _isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _load_decisions(
    path: Path | None = None, ctx: MonitorContext | None = None
) -> list[dict[str, Any]]:
    path = path or _decisions_file(ctx)
    if not path.exists():
        return []
    payload = yaml.safe_load(path.read_text("utf-8")) or {}
    decisions = payload.get("decisions") or []
    return decisions if isinstance(decisions, list) else []


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip('"'))
    except ValueError:
        return None


def _is_stale_decision(decision: dict[str, Any], today: date) -> bool:
    if decision.get("status") != "active":
        return False
    expires = _parse_date(decision.get("expires"))
    return bool(expires and expires <= today)


def _is_approaching_expiry(decision: dict[str, Any], today: date) -> bool:
    if decision.get("status") != "active":
        return False
    expires = _parse_date(decision.get("expires"))
    if expires is None or expires <= today:
        return False
    return expires <= today + timedelta(days=APPROACHING_EXPIRY_DAYS)


def collect_decision_governance(
    *,
    decisions_file: Path | None = None,
    today: date | None = None,
    ctx: MonitorContext | None = None,
) -> dict[str, Any]:
    today = today or date.today()
    decisions = _load_decisions(decisions_file, ctx=ctx)
    stale = [decision for decision in decisions if _is_stale_decision(decision, today)]
    approaching = [
        decision for decision in decisions
        if _is_approaching_expiry(decision, today)
    ]
    return {
        "total": len(decisions),
        "stale_count": len(stale),
        "approaching_expiry_count": len(approaching),
        "stale": stale,
        "approaching": approaching,
        "all": decisions,
    }


def collect_adr_governance(ctx: MonitorContext | None = None) -> dict[str, Any]:
    """Scan product ADRs unless the context owns an isolated fixture tree."""
    if resolve_context(ctx).root is not None:
        return dict(_EMPTY_ADR_GOVERNANCE)
    data: dict[str, Any] = monitor_surface.collect_adr_governance()
    return data


def _collect_adr_governance_summary(ctx: MonitorContext | None = None) -> dict[str, int]:
    if resolve_context(ctx).root is not None:
        return {"adrs_total": 0, "adrs_warnings": 0, "adrs_errors": 0}
    summary: dict[str, int] = monitor_surface.collect_adr_governance_summary()
    return summary


def collect_governance_state(ctx: MonitorContext | None = None) -> dict[str, Any]:
    return {
        "decisions": collect_decision_governance(ctx=ctx),
        "adrs": collect_adr_governance(ctx=ctx),
        "generated_at": _isoformat_z(datetime.now(UTC)),
    }


def collect_governance_summary(ctx: MonitorContext) -> dict[str, int]:
    decisions = collect_decision_governance(ctx=ctx)
    adrs = _collect_adr_governance_summary(ctx=ctx)
    return {
        "decisions_total": int(decisions["total"]),
        "decisions_stale": int(decisions["stale_count"]),
        "decisions_approaching_expiry": int(decisions["approaching_expiry_count"]),
        "adrs_total": int(adrs["adrs_total"]),
        "adrs_warnings": int(adrs["adrs_warnings"]),
        "adrs_errors": int(adrs["adrs_errors"]),
    }


@router.get("")
async def governance_state(ctx: MonitorContext = Depends(get_ctx)) -> dict[str, Any]:
    return collect_governance_state(ctx)
