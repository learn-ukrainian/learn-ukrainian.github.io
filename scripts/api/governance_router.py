"""Unified governance state endpoint for decisions and ADRs (#1523)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter

from scripts.audit import check_adrs

from .config import PROJECT_ROOT

router = APIRouter(tags=["governance"])

DECISIONS_FILE = PROJECT_ROOT / "docs" / "decisions" / "decisions.yaml"
APPROACHING_EXPIRY_DAYS = 30


def _isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _load_decisions(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or DECISIONS_FILE
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
) -> dict[str, Any]:
    today = today or date.today()
    decisions = _load_decisions(decisions_file)
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


def _matching_findings(findings: list[str], markers: tuple[str, ...]) -> list[str]:
    return [
        finding for finding in findings
        if any(marker in finding for marker in markers)
    ]


def collect_adr_governance() -> dict[str, Any]:
    result = check_adrs.run_check(check_promotions_flag=True)
    broken_chains = _matching_findings(
        result.errors,
        ("claims supersede by ADR-", "supersedes ADR-"),
    )
    orphaned_refs = _matching_findings(
        result.warnings,
        ("Orphaned reference to ADR-",),
    )
    stale_proposed = _matching_findings(
        result.warnings,
        ("in Proposed/DRAFT status",),
    )
    return {
        "total": len(result.adrs),
        "stale_proposed_count": len(stale_proposed),
        "error_count": len(result.errors),
        "warning_count": len(result.warnings),
        "broken_chains": broken_chains,
        "orphaned_refs": orphaned_refs,
        "promotion_candidates": result.promotion_candidates,
        "index": [record.as_dict() for record in result.adrs],
    }


def _collect_adr_governance_summary() -> dict[str, int]:
    result = check_adrs.CheckResult()
    result.adrs = check_adrs._load_adrs()
    if not result.adrs:
        result.warnings.append("No ADRs found")
    else:
        check_adrs._check_numbering(result.adrs, result)
        check_adrs._check_required_fields(result.adrs, result)
        check_adrs._check_stale_proposed(
            result.adrs,
            result,
            check_adrs.STALE_PROPOSED_DAYS_DEFAULT,
        )
        check_adrs._check_supersede_chains(result.adrs, result)
        check_adrs._check_index_drift(result.adrs, result)
    return {
        "adrs_total": len(result.adrs),
        "adrs_warnings": len(result.warnings),
        "adrs_errors": len(result.errors),
    }


def collect_governance_state() -> dict[str, Any]:
    return {
        "decisions": collect_decision_governance(),
        "adrs": collect_adr_governance(),
        "generated_at": _isoformat_z(datetime.now(UTC)),
    }


def collect_governance_summary() -> dict[str, int]:
    decisions = collect_decision_governance()
    adrs = _collect_adr_governance_summary()
    return {
        "decisions_total": int(decisions["total"]),
        "decisions_stale": int(decisions["stale_count"]),
        "decisions_approaching_expiry": int(decisions["approaching_expiry_count"]),
        "adrs_total": int(adrs["adrs_total"]),
        "adrs_warnings": int(adrs["adrs_warnings"]),
        "adrs_errors": int(adrs["adrs_errors"]),
    }


@router.get("")
async def governance_state() -> dict[str, Any]:
    return collect_governance_state()
