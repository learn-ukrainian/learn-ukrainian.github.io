"""Bind the plan review of record to the dispatch that produced it (#12114 AC-02).

``plan-review.yaml`` is a projection the recorder (``scripts.review.record``) writes
from the findings database after it has checked the bound dispatch record. Its three
fields alone prove nothing: anyone can write the file. Before a plan is promoted, or a
promoted plan passes strict validation, this module re-establishes the chain from
host-local state, read-only:

1. the findings database holds an accepted plan attempt, and ``plan-review.yaml`` is
   exactly its projection;
2. that attempt's dispatch record is a ``done`` full-access task bound to the same
   review id, attempt id and manifest hash, its saved result hashes to its recorded
   ``result_sha256``, and its reviewer identity is the attempt's;
3. the saved return ``plan-review.<attempt_id>.yaml`` hashes to the attempt's
   ``return_sha256``;
4. the attempt's Sources receipt ledger verifies against its sidecar and holds at
   least one ``ok`` receipt of this review attempt.

Each failure names what is missing. The database, task records and receipt ledger are
host-local state (the primary checkout's ``batch_state``) and never in the repository, so
a checkout without them (CI) cannot run this check: ``ReviewStateUnavailable`` says so,
and the caller decides whether that is declared.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any

from scripts.build.fresh import plan_manifest as pm

REVIEW_UNBOUND = "review_unbound"
REVIEW_STATE_UNAVAILABLE = "review_state_unavailable"


class ReviewStateUnavailable(pm.PlanReviewError):
    """The host-local review state (findings database) is absent: the binding cannot be checked here."""


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def check_review_binding(
    root: Path, level: str, slug: str, *, db_path: Path | None = None, tasks_dir: Path | None = None
) -> dict[str, Any]:
    """Raise ``PlanReviewError(review_unbound)`` naming what is missing, else return the binding.

    The findings database defaults to the one the recorder writes for ``root``; dispatch
    records to the dispatcher's task store (``task_store_paths.tasks_dir``), whose sibling
    ``review-receipts`` holds the attempt ledger dispatch claimed. Raises
    ``ReviewStateUnavailable`` when this host has no findings database for the level.
    """
    from scripts.common.task_store_paths import tasks_dir as dispatch_tasks_dir
    from scripts.lib.readonly_sqlite import open_readonly
    from scripts.orchestration.task_record_store import relocated_result_file
    from scripts.review import findings_db, fixloop
    from scripts.review import record as recorder
    from scripts.review.receipts import ledger

    root = Path(root).resolve()
    database = Path(db_path) if db_path is not None else findings_db.db_path(level, root)
    tasks = Path(tasks_dir) if tasks_dir is not None else dispatch_tasks_dir()
    if not database.is_file():
        raise ReviewStateUnavailable(
            REVIEW_STATE_UNAVAILABLE,
            f"no findings database for {level} on this host; the plan review's dispatch binding cannot be checked",
        )

    def unbound(message: str) -> pm.PlanReviewError:
        return pm.PlanReviewError(
            REVIEW_UNBOUND, f"the plan review of {level}/{slug} is not bound to a dispatch: {message}"
        )

    directory = pm.state_dir(root, level, slug)
    conn = open_readonly(database)
    conn.row_factory = sqlite3.Row
    try:
        latest = findings_db.latest_accepted(conn, level, slug, "plan", None)
    except sqlite3.Error as error:
        raise unbound(f"the findings database cannot be read ({error})") from error
    finally:
        conn.close()
    problem = fixloop.projection_problem(directory, "plan", None, latest)
    if problem is not None or latest is None:
        raise unbound(problem or f"no {pm.REVIEW_NAME}")
    attempt = dict(latest)
    binding = {key: attempt[key] for key in ("review_id", "attempt_id", "manifest_sha256")}

    task_id = attempt["task_id"]
    try:
        task, task_path = recorder._read_dispatch_record(task_id, tasks)
        identity = recorder.identity_from_record(task, task_id, record_path=task_path)
    except recorder.RecordError as error:
        raise unbound(f"no usable dispatch record {task_id}: {error}") from error
    if task.get("status") != "done":
        raise unbound(f"dispatch record {task_id} is {task.get('status')!r}, not done")
    if task.get("review_attempt") != binding:
        raise unbound(
            f"dispatch record {task_id} is not bound to review {binding['review_id']} attempt "
            f"{binding['attempt_id']} of manifest {binding['manifest_sha256']}"
        )
    if task.get("review_access") != "full" or attempt["access"] != "full":
        raise unbound(f"dispatch record {task_id} is not a full-access review")
    if identity != {
        "model": attempt["reviewer_model"],
        "harness": attempt["harness"],
        "family": attempt["reviewer_family"],
    }:
        raise unbound(f"dispatch record {task_id} names another reviewer than the recorded attempt")
    canonical = tasks / f"{task_id}.result"
    declared = task.get("result_file")
    result = Path(relocated_result_file(task_path, str(canonical)))
    if (
        not isinstance(declared, str)
        or Path(declared).resolve() != canonical.resolve()
        or (_sha256(result) is None or _sha256(result) != task.get("result_sha256"))
    ):
        raise unbound(f"the saved result of dispatch {task_id} is missing or does not hash to its result_sha256")

    saved = directory / f"plan-review.{binding['attempt_id']}.yaml"
    if _sha256(saved) != attempt["return_sha256"]:
        raise unbound(f"the saved return {saved.name} is missing or does not hash to the recorded return_sha256")

    receipts_path = tasks.parent / "review-receipts" / binding["review_id"] / f"{binding['attempt_id']}.jsonl"
    try:
        receipts = ledger.records(receipts_path)
    except (ledger.LedgerError, OSError, ValueError) as error:
        raise unbound(f"the Sources receipt ledger does not verify ({error})") from error
    bound = [
        receipt
        for receipt in receipts
        if receipt.get("status") == "ok" and all(receipt.get(key) == value for key, value in binding.items())
    ]
    if not bound:
        raise unbound(f"0 ok Sources receipts of this attempt in its ledger ({len(receipts)} rows)")
    return {**binding, "task_id": task_id, "sources_receipts": len(bound)}
