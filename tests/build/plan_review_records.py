"""Record a plan review the way a real bound attempt is recorded (#12114).

``plan-promote`` binds ``plan-review.yaml`` to the findings database row, the done
full-access dispatch record, its saved result and the Sources receipt ledger
(``scripts/build/fresh/review_binding.py``). A test world approves a plan by writing the
dispatch record and ledger where dispatch writes them (the task store, which the test
session isolates, and its sibling ``review-receipts``) and recording the return through
``scripts.review.record``, never by writing ``plan-review.yaml`` itself.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from scripts.build.fresh import plan_manifest
from scripts.common.task_store_paths import tasks_dir
from scripts.review import record
from scripts.review.receipts.ledger import create_empty_ledger
from tests.review.test_r1_schema_ledger import PLAN_CHECKS, _record, _review

SEAT = ("codex", "gpt-6.1-sol")


def record_plan_review(
    root: Path,
    level: str,
    slug: str,
    digest: str,
    *,
    verdict: str = "APPROVE",
    attempt_id: str = "attempt-1",
    review_id: str | None = None,
    seat: tuple[str, str] = SEAT,
    tasks: Path | None = None,
) -> record.Outcome:
    """Record one bound full-access plan attempt of manifest ``digest``; returns the recorder's outcome.

    ``tasks`` is the dispatch task store the attempt is recorded from (default: the session's).
    """
    root = Path(root)
    tasks = Path(tasks) if tasks is not None else tasks_dir()
    review_id = review_id or f"plan-{verdict.lower()}-{digest[:16]}"
    ledger = tasks.parent / "review-receipts" / review_id / f"{attempt_id}.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    create_empty_ledger(ledger)
    receipt = _record(ledger, manifest=digest, result="attested result", attempt_id=attempt_id, review_id=review_id)
    checks: dict = {name: "clean" for name in PLAN_CHECKS}
    findings: list = []
    if verdict == "REVISE":
        findings = [
            {
                "id": "F-01",
                "status": "active",
                "locations": [],
                "scope": {"lesson": 1},
                "dimension": "plan_defect",
                "severity": "MAJOR",
                "claim": "Placeholder claim.",
                "evidence": {"receipt": receipt},
            }
        ]
        checks["sequencing"] = ["F-01"]
    review = _review(
        kind="plan", manifest_hash=digest, checks=checks, findings=findings, attempt_id=attempt_id, review_id=review_id
    )
    data = yaml.safe_dump(review, sort_keys=False, allow_unicode=True).encode("utf-8")

    tasks.mkdir(parents=True, exist_ok=True)
    task_id = f"{review_id}-{attempt_id}"
    result = tasks / f"{task_id}.result"
    result.write_bytes(data)
    agent, model = seat
    task = {
        "task_id": task_id,
        "agent": agent,
        "model": model,
        "status": "done",
        "review_access": "full",
        "review_attempt": {"review_id": review_id, "attempt_id": attempt_id, "manifest_sha256": digest},
        "result_file": str(result),
        "result_sha256": hashlib.sha256(data).hexdigest(),
    }
    (tasks / f"{task_id}.json").write_text(json.dumps(task), encoding="utf-8")
    outcome = record.record_return(
        result,
        manifest_path=plan_manifest.history_path(root, level, slug, digest),
        ledger_path=ledger,
        task_id=task_id,
        repo_root=root,
        tasks_dir=tasks,
    )
    assert outcome.accepted and outcome.verdict == verdict, outcome.payload()
    return outcome
