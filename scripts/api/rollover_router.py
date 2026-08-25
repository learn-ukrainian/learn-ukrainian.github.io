"""Read-only fleet rollover registry and reconciliation API."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from scripts.orchestration import thread_handoff
from scripts.orchestration.task_family import rollover_registry as registry

from . import config
from .monitor_context import MonitorContext, get_ctx

router = APIRouter(tags=["rollovers"])


def _client_registry_errors(errors: list | None) -> list[dict[str, str]]:
    """Return path-only registry errors for HTTP clients (no exception text)."""
    out: list[dict[str, str]] = []
    for err in errors or []:
        if not isinstance(err, dict):
            continue
        path = err.get("path")
        if path is None:
            continue
        out.append({"path": str(path), "error": "invalid or unreadable durable source"})
    return out


def collect_rollover_orient_data(live_repo_root: Path | None = None) -> dict:
    """Compact cold-start projection; full evidence remains on this router."""
    root = live_repo_root if live_repo_root is not None else Path(config.LIVE_REPO_ROOT)
    audit = registry.audit_fleet(root)
    identity_snapshot = thread_handoff.rollover_identity_snapshot(root)
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
        "errors": _client_registry_errors(audit["errors"]),
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
    ctx: MonitorContext = Depends(get_ctx),
) -> dict:
    """Classify the fleet or return one exact read-only selector projection."""
    selectors = {
        "source_thread_id": source_thread_id,
        "replacement_thread_id": replacement_thread_id,
        "lineage_id": lineage_id,
        "rollover_id": rollover_id,
    }
    if any(selectors.values()):
        records, errors = registry.scan_records(ctx.roots.live_repo_root)
        try:
            selected = registry.select_exact(records, agent=agent, **selectors)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not selected:
            raise HTTPException(
                status_code=404,
                detail={"error": "exact rollover selector matched no registry entry", "registry_errors": _client_registry_errors(errors)},
            )
        if len(selected) > 1:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "exact rollover selector remains ambiguous",
                    "matches": [registry.candidate_summary(record) for record in selected],
                    "registry_errors": _client_registry_errors(errors),
                },
            )
        record = selected[0]
        selected_errors = registry.record_source_errors(ctx.roots.live_repo_root, record, errors)
        if selected_errors:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "exact rollover selector matched a corrupt durable source",
                    "candidate": registry.candidate_summary(record),
                    "registry_errors": _client_registry_errors(selected_errors),
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
            "registry_errors": _client_registry_errors(errors),
        }
    audit = registry.audit_fleet(ctx.roots.live_repo_root, stale_hours=stale_hours)
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
    audit = {**audit, "errors": _client_registry_errors(audit.get("errors"))}
    return audit
