"""Read-only fleet rollover registry and reconciliation API."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query

from scripts.orchestration import thread_handoff
from scripts.orchestration.task_family import rollover_registry as registry

from .config import LIVE_REPO_ROOT

router = APIRouter(tags=["rollovers"])


def collect_rollover_orient_data() -> dict:
    """Compact cold-start projection; full evidence remains on this router."""
    audit = registry.audit_fleet(LIVE_REPO_ROOT)
    identity_snapshot = thread_handoff.rollover_identity_snapshot(LIVE_REPO_ROOT)
    actionable = [
        entry
        for entry in audit["entries"]
        if entry["live_pending"] or entry["classification"] == "confirmed but incompletely cleaned"
    ]
    return {
        "schema_version": "rollover-orient.v1",
        "generated_at": audit["generated_at"],
        "counts": audit["counts"],
        "actionable": actionable,
        "errors": audit["errors"],
        "task_identity": {
            "schema_version": identity_snapshot["schema_version"],
            "candidate_count": identity_snapshot["candidate_count"],
            "errors": identity_snapshot["errors"],
        },
    }


@router.get("")
def rollover_audit(
    agent: str | None = Query(None),
    source_thread_id: str | None = Query(None),
    replacement_thread_id: str | None = Query(None),
    lineage_id: str | None = Query(None),
    rollover_id: str | None = Query(None),
    stale_hours: float = Query(registry.DEFAULT_STALE_HOURS, gt=0),
) -> dict:
    """Classify the fleet or return one exact read-only selector projection."""
    selectors = {
        "source_thread_id": source_thread_id,
        "replacement_thread_id": replacement_thread_id,
        "lineage_id": lineage_id,
        "rollover_id": rollover_id,
    }
    if any(selectors.values()):
        records, errors = registry.scan_records(LIVE_REPO_ROOT)
        try:
            selected = registry.select_exact(records, agent=agent, **selectors)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not selected:
            raise HTTPException(
                status_code=404,
                detail={"error": "exact rollover selector matched no registry entry", "registry_errors": errors},
            )
        if len(selected) > 1:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "exact rollover selector remains ambiguous",
                    "matches": [registry.candidate_summary(record) for record in selected],
                    "registry_errors": errors,
                },
            )
        record = selected[0]
        selected_errors = registry.record_source_errors(LIVE_REPO_ROOT, record, errors)
        if selected_errors:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "exact rollover selector matched a corrupt durable source",
                    "candidate": registry.candidate_summary(record),
                    "registry_errors": selected_errors,
                },
            )
        return {
            "schema_version": registry.REGISTRY_SCHEMA_VERSION,
            "mutation_allowed": False,
            "entry": registry.candidate_summary(record),
            "classification": registry.classify(
                record,
                now=registry.utc_now(),
                stale_after=timedelta(hours=stale_hours),
            ).value,
            "reconciliation": record.get("last_reconciliation"),
            "receipts": record.get("receipts", []),
            "evidence_paths": record.get("evidence_paths", []),
            "blocking_reason": record.get("blocking_reason"),
            "terminal_reason": record.get("terminal_reason"),
            "registry_errors": errors,
        }
    audit = registry.audit_fleet(LIVE_REPO_ROOT, stale_hours=stale_hours)
    if agent is not None:
        try:
            agent = registry.normalize_agent(agent)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        audit["entries"] = [entry for entry in audit["entries"] if entry["agent"] == agent]
        audit["counts"] = {
            "total": len(audit["entries"]),
            "live_pending": sum(entry["live_pending"] for entry in audit["entries"]),
            "corrupt": sum(
                entry["classification"] == registry.AuditClassification.INCONSISTENT_CORRUPT.value
                for entry in audit["entries"]
            ),
        }
    return audit
