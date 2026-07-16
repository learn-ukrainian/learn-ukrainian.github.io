#!/usr/bin/env python3
"""Fleet rollover registry, exact selection, reconciliation, and maintenance CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.orchestration import thread_handoff
from scripts.orchestration.task_family import rollover_registry as registry
from scripts.orchestration.task_family.storage import advisory_lock


def _roots(repo_root: Path | None) -> tuple[Path, Path]:
    return thread_handoff.resolve_roots(repo_root)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON evidence {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON evidence must be an object: {path}")
    return value


def _selectors(args: argparse.Namespace) -> dict[str, str | None]:
    return {
        "agent": getattr(args, "agent", None),
        "source_thread_id": getattr(args, "source_thread_id", None),
        "replacement_thread_id": getattr(args, "selector_replacement_thread_id", None)
        or getattr(args, "replacement_thread_id", None),
        "lineage_id": getattr(args, "lineage_id", None),
        "rollover_id": getattr(args, "rollover_id", None),
    }


def _select_one(state_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    records, errors = registry.scan_records(state_root)
    selected = registry.select_exact(records, **_selectors(args))
    if len(selected) != 1:
        payload = {
            "error": "exact rollover selector did not resolve uniquely",
            "mutation_allowed": False,
            "selectors": {key: value for key, value in _selectors(args).items() if value},
            "matches": [registry.candidate_summary(record) for record in selected],
            "registry_errors": errors,
        }
        raise SelectionError(payload)
    record = selected[0]
    selected_errors = registry.record_source_errors(state_root, record, errors)
    if selected_errors:
        raise SelectionError(
            {
                "error": "exact rollover selector matched a corrupt durable source",
                "mutation_allowed": False,
                "selectors": {key: value for key, value in _selectors(args).items() if value},
                "candidate": registry.candidate_summary(record),
                "registry_errors": selected_errors,
            }
        )
    return record


class SelectionError(ValueError):
    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(str(payload.get("error")))
        self.payload = payload


def _print_error(exc: Exception, *, action: str) -> int:
    payload = exc.payload if isinstance(exc, SelectionError) else {"error": str(exc), "action": action}
    print(json.dumps(payload, indent=2))
    return 2


def cmd_detect(args: argparse.Namespace) -> int:
    try:
        _, state_root = _roots(args.repo_root)
        records, errors = registry.scan_records(state_root)
        agent_records = [record for record in records if record["key"]["agent"] == args.agent]
        has_exact = any(value for key, value in _selectors(args).items() if key != "agent")
        if has_exact:
            record = _select_one(state_root, args)
            print(
                json.dumps(
                    {
                        "status": "selected",
                        "mutation_allowed": registry.allows_exact_progress(record),
                        "candidate": registry.candidate_summary(record),
                        "packet_paths": record.get("packet_paths"),
                        "lease_path": record.get("lease_path"),
                        "unrelated_live_pending": sum(
                            registry.is_live_pending(item) and item["key"] != record["key"] for item in agent_records
                        ),
                        "registry_errors": errors,
                    },
                    indent=2,
                )
            )
            return 0
        live = [record for record in agent_records if registry.is_live_pending(record)]
        if errors:
            print(
                json.dumps(
                    {
                        "error": "inconsistent_or_corrupt_rollover_sources",
                        "agent": args.agent,
                        "mutation_allowed": False,
                        "candidates": [registry.candidate_summary(record) for record in live],
                        "registry_errors": errors,
                    },
                    indent=2,
                )
            )
            return 2
        if len(live) > 1:
            print(
                json.dumps(
                    {
                        "error": "multiple_live_pending_rollovers",
                        "agent": args.agent,
                        "mutation_allowed": False,
                        "candidates": [registry.candidate_summary(record) for record in live],
                        "registry_errors": errors,
                    },
                    indent=2,
                )
            )
            return 2
        if not live:
            print(json.dumps({"agent": args.agent, "status": "none", "registry_errors": errors}, indent=2))
            return 2 if errors else 0
        record = live[0]
        print(
            json.dumps(
                {
                    "agent": args.agent,
                    "status": "selected",
                    "mutation_allowed": registry.allows_exact_progress(record),
                    "candidate": registry.candidate_summary(record),
                    "packet_paths": record.get("packet_paths"),
                    "lease_path": record.get("lease_path"),
                },
                indent=2,
            )
        )
        return 0
    except (OSError, ValueError) as exc:
        return _print_error(exc, action="detect")


def cmd_audit(args: argparse.Namespace) -> int:
    try:
        _, state_root = _roots(args.repo_root)
        if args.stale_hours <= 0:
            raise ValueError("--stale-hours must be positive")
        result = registry.audit_fleet(state_root, stale_hours=args.stale_hours)
    except (OSError, ValueError) as exc:
        return _print_error(exc, action="audit")
    print(json.dumps(result, indent=2))
    return 2 if result["errors"] else 0


def cmd_migrate(args: argparse.Namespace) -> int:
    try:
        _, state_root = _roots(args.repo_root)
        result = registry.migrate_existing(
            state_root,
            apply=args.apply,
            evidence=args.evidence or "",
        )
    except (OSError, ValueError) as exc:
        return _print_error(exc, action="migrate")
    print(json.dumps(result, indent=2))
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    try:
        _, state_root = _roots(args.repo_root)
        record = _select_one(state_root, args)
        snapshot = _load_json(args.snapshot)
        if args.apply:
            result = registry.apply_reconciliation(state_root, record=record, snapshot=snapshot)
        else:
            result = {
                "mode": "read-only",
                "mutation_allowed": False,
                "candidate": registry.candidate_summary(record),
                "reconciliation": registry.reconcile_snapshot(record, snapshot),
            }
    except (OSError, ValueError) as exc:
        return _print_error(exc, action="reconcile-exact")
    print(json.dumps(result, indent=2))
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    try:
        repo_root, state_root = _roots(args.repo_root)
        record = _select_one(state_root, args)
        if not registry.allows_exact_progress(record):
            raise ValueError(
                f"selected rollover state {record['state']} requires reconciliation or maintenance before resume"
            )
        selected_replacement_id = args.replacement_thread_id.strip()
        if not selected_replacement_id:
            raise ValueError("--replacement-thread-id is required")
        if record["task_identity"].get("replacement_task_id") != selected_replacement_id:
            raise ValueError("--replacement-thread-id does not match the authoritative registry binding")
        lease_relative = record.get("lease_path")
        if not isinstance(lease_relative, str) or not lease_relative:
            raise ValueError("selected registry record has no live lease to resume")
        lease_path = thread_handoff.repo_local_path(state_root, Path(lease_relative))
        key = record["key"]
        with advisory_lock(registry.lineage_lock_path(state_root, agent=key["agent"], lineage_id=key["lineage_id"])):
            lease = thread_handoff.load_state(lease_path)
            thread_handoff.require_checkout_continuity(lease.get("replacement") or {}, repo_root)
            resumed = thread_handoff.resume_state(
                lease,
                rollover_id=key["rollover_id"],
                replacement_thread_id=selected_replacement_id,
                now=thread_handoff.utc_now(),
            )
            thread_handoff.write_rollover_state(
                lease_path,
                state_root,
                resumed,
                already_locked=True,
            )
            current = registry.load_record(state_root, **key)
    except (OSError, ValueError) as exc:
        return _print_error(exc, action="resume-exact")
    print(
        json.dumps(
            {
                "status": "resumed",
                "candidate": registry.candidate_summary(current),
                "lease_path": current["lease_path"],
            },
            indent=2,
        )
    )
    return 0


def cmd_maintenance(args: argparse.Namespace) -> int:
    try:
        _, state_root = _roots(args.repo_root)
        record = _select_one(state_root, args)
        action = registry.MaintenanceAction(args.maintenance_action)
        if args.plan:
            if args.proof_file is None:
                raise ValueError("maintenance planning requires --proof-file")
            result = registry.create_maintenance_plan(
                state_root,
                record=record,
                action=action,
                proof=_load_json(args.proof_file),
            )
        else:
            if args.plan_file is None:
                raise ValueError("maintenance apply requires --plan-file")
            _, plan = registry.load_maintenance_plan(state_root, plan_path=args.plan_file)
            if plan.get("key") != record.get("key"):
                raise ValueError("maintenance plan exact IDs do not match the selected registry record")
            if plan.get("action") != action.value:
                raise ValueError("maintenance plan action does not match the selected command")
            result = registry.apply_maintenance_plan(state_root, plan_path=args.plan_file)
    except (OSError, ValueError) as exc:
        return _print_error(exc, action=args.maintenance_action)
    print(json.dumps(result, indent=2))
    return 0


def _add_exact_selectors(
    parser: argparse.ArgumentParser,
    *,
    require_pair: bool = False,
    include_replacement: bool = True,
) -> None:
    parser.add_argument("--agent", type=registry.normalize_agent, default="codex")
    parser.add_argument("--source-thread-id")
    if include_replacement:
        parser.add_argument("--replacement-thread-id", dest="selector_replacement_thread_id")
    parser.add_argument("--lineage-id", required=require_pair)
    parser.add_argument("--rollover-id", required=require_pair)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect = subparsers.add_parser("detect", help="Read-only generic or exact rollover detection.")
    _add_exact_selectors(detect)
    detect.set_defaults(func=cmd_detect)

    audit = subparsers.add_parser("audit", help="Classify every fleet rollover packet without mutation.")
    audit.add_argument("--stale-hours", type=float, default=registry.DEFAULT_STALE_HOURS)
    audit.set_defaults(func=cmd_audit)

    migrate = subparsers.add_parser("migrate", help="Plan or apply non-destructive legacy registry migration.")
    migration_mode = migrate.add_mutually_exclusive_group(required=True)
    migration_mode.add_argument("--plan", action="store_true")
    migration_mode.add_argument("--apply", action="store_true")
    migrate.add_argument("--evidence")
    migrate.set_defaults(func=cmd_migrate)

    reconcile = subparsers.add_parser(
        "reconcile-exact",
        help="Compare one exact registry entry with an authoritative native/app snapshot.",
    )
    _add_exact_selectors(reconcile)
    reconcile.add_argument("--snapshot", type=Path, required=True)
    reconcile.add_argument("--apply", action="store_true")
    reconcile.set_defaults(func=cmd_reconcile)

    resume = subparsers.add_parser("resume-exact", help="Resume one uniquely selected exact packet.")
    _add_exact_selectors(resume, include_replacement=False)
    resume.add_argument("--replacement-thread-id", required=True)
    resume.set_defaults(func=cmd_resume)

    for name, action in (
        ("finish-cleanup-exact", registry.MaintenanceAction.FINISH_CLEANUP),
        ("supersede-exact", registry.MaintenanceAction.SUPERSEDE),
        ("abandon-exact", registry.MaintenanceAction.ABANDON),
    ):
        maintenance = subparsers.add_parser(name, help=f"Plan or apply exact {action.value} maintenance.")
        _add_exact_selectors(maintenance, require_pair=True)
        mode = maintenance.add_mutually_exclusive_group(required=True)
        mode.add_argument("--plan", action="store_true")
        mode.add_argument("--apply", action="store_true")
        maintenance.add_argument("--proof-file", type=Path)
        maintenance.add_argument("--plan-file", type=Path)
        maintenance.set_defaults(func=cmd_maintenance, maintenance_action=action.value)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
