"""Builders for the seeded-measurement tests (#8430 R3-A): records on disk, attempts and adjudications in a database.

No Ukrainian anywhere: dimensions and families are the taxonomy's and the resolver's, texts are English placeholders.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.review import findings_db
from scripts.review.seeds import manifest as sm

LEVEL = "a1"
WRITER_FAMILY = "anthropic"
# concrete models the closeout resolver maps to a family (checked by tests/review/seeds/test_manifest.py)
PLANTER_MODEL, PLANTER_FAMILY = "gemini-3.1-pro-preview", "google"
GOLD_MODEL, GOLD_FAMILY = "grok-4.3", "xai"
SEATS = {  # harness -> (model, family)
    "codex": ("gpt-6-astra", "openai"),
    "agy": ("gemini-3.1-pro-preview", "google"),
    "grok": ("grok-4.3", "xai"),
}


def mechanical_seed(
    seed_id: str, dimension: str = "job", *, source: str = "real_built", n: int = 1, **over: Any
) -> sm.Seed:
    fields: dict[str, Any] = {
        "seed_id": seed_id,
        "seed_kind": "mechanical",
        "source_kind": source,
        "level": LEVEL,
        "slug": f"{seed_id}-module",
        "lesson_n": n,
        "dimension": dimension,
        "sub_dimension": "calque" if dimension == "language" else None,
        "target_spans": [{"tab": "urok", "quote": "a placeholder span"}],
        "semantic_defect": "a placeholder defect",
        "detection_criterion": "the finding names the placeholder defect",
        "writer_family": WRITER_FAMILY,
        "planter_model": None,
        "planter_family": None,
        "gold_checker_model": None,
        "gold_checker_family": None,
        "gold_verdict": "not_applicable",
    }
    fields.update(over)
    return sm.Seed(**fields)


def linguistic_seed(seed_id: str, dimension: str = "language", **over: Any) -> sm.Seed:
    fields = {
        "seed_kind": "linguistic",
        "planter_model": PLANTER_MODEL,
        "planter_family": PLANTER_FAMILY,
        "gold_checker_model": GOLD_MODEL,
        "gold_checker_family": GOLD_FAMILY,
        "gold_verdict": "pass",
    }
    fields.update(over)
    return mechanical_seed(seed_id, dimension, **fields)


def clean_lesson(clean_id: str, *, source: str = "real_built", n: int = 1, **over: Any) -> sm.Clean:
    fields: dict[str, Any] = {
        "clean_id": clean_id,
        "source_kind": source,
        "level": LEVEL,
        "slug": f"{clean_id}-module",
        "lesson_n": n,
        "writer_family": WRITER_FAMILY,
    }
    fields.update(over)
    return sm.Clean(**fields)


def finding(
    fid: str = "F-01", severity: str = "MAJOR", status: str = "active", dimension: str = "job"
) -> dict[str, Any]:
    return {
        "id": fid,
        "status": status,
        "locations": [{"tab": "urok", "quote": "a placeholder span"}],
        "dimension": dimension,
        "severity": severity,
        "claim": f"claim {fid}",
        "evidence": {"receipt": f"r-{fid}"},
    }


class Env:
    """A tmp repository root with a findings database and a directory of dispatch records."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.db = root / "batch_state" / "review-findings" / f"{LEVEL}.sqlite"
        self.tasks = root / "batch_state" / "tasks"
        self.tasks.mkdir(parents=True)
        self.counter = 0

    # --- records ------------------------------------------------------------------------
    def add(self, unit: sm.Seed | sm.Clean, assign: str | None = None) -> str:
        if isinstance(unit, sm.Seed):
            sm.write_scoring_manifest(unit, self.root)
            unit_id = unit.seed_id
        else:
            sm.write_clean_record(unit, self.root)
            unit_id = unit.clean_id
        if assign:
            sm.assign_set(unit_id, assign, self.root)
        return unit_id

    def dispatch_record(self, task_id: str, agent: str, model: str) -> str:
        (self.tasks / f"{task_id}.json").write_text(
            json.dumps({"task_id": task_id, "agent": agent, "model": model, "status": "done"}), encoding="utf-8"
        )
        return task_id

    # --- the database -------------------------------------------------------------------
    def connect(self):
        return findings_db.connect(self.db)

    def attempt(
        self,
        unit: sm.Seed | sm.Clean,
        seat: str = "codex",
        verdict: str = "REVISE",
        findings: list[dict[str, Any]] | None = None,
        *,
        review_id: str | None = None,
    ) -> tuple[str, str]:
        """Insert one first-seat attempt on a unit (with its findings); returns ``(review_id, attempt_id)``."""
        self.counter += 1
        model, family = SEATS[seat]
        unit_id = unit.seed_id if isinstance(unit, sm.Seed) else unit.clean_id
        review_id = review_id or f"review-{self.counter}"
        attempt_id = f"attempt-{self.counter}"
        conn = self.connect()
        try:
            with findings_db.transaction(conn):
                findings_db.insert_attempt(
                    conn,
                    {
                        "review_id": review_id,
                        "attempt_id": attempt_id,
                        "kind": "lesson",
                        "level": unit.level,
                        "slug": unit.slug,
                        "lesson_n": unit.lesson_n,
                        "manifest_sha256": f"{self.counter:064x}",
                        "reviewer_model": model,
                        "reviewer_family": family,
                        "harness": seat,
                        "verdict": verdict,
                        "validated_at": "2026-09-25T00:00:00+00:00",
                        "task_id": f"task-{self.counter}",
                        "role": "first",
                        "seed_id": unit_id,
                        "writer_family": unit.writer_family,
                    },
                )
                for item in findings or []:
                    findings_db.insert_finding(conn, review_id, attempt_id, item, layer=None, seed_id=unit_id)
        finally:
            conn.close()
        return review_id, attempt_id

    def seed_result(
        self, unit_id: str, ids: tuple[str, str], found: bool, blocking: bool, classes: dict[str, str]
    ) -> None:
        conn = self.connect()
        try:
            with findings_db.transaction(conn):
                findings_db.insert_seed_result(
                    conn,
                    seed_id=unit_id,
                    review_id=ids[0],
                    attempt_id=ids[1],
                    planted_found=found,
                    planted_blocking=blocking,
                    mapping=[{"finding_id": k, "class": v, "reason": "checked"} for k, v in sorted(classes.items())],
                    adjudicator_model="claude-sonnet-5",
                    adjudicator_family="anthropic-adjudicator",
                )
        finally:
            conn.close()

    def clean_result(self, unit_id: str, ids: tuple[str, str], classes: dict[str, str], blocked: bool) -> None:
        conn = self.connect()
        try:
            with findings_db.transaction(conn):
                findings_db.insert_clean_result(
                    conn,
                    clean_id=unit_id,
                    review_id=ids[0],
                    attempt_id=ids[1],
                    false_findings=sum(1 for value in classes.values() if value == "false"),
                    falsely_blocked=blocked,
                    mapping=[{"finding_id": k, "class": v, "reason": "checked"} for k, v in sorted(classes.items())],
                    adjudicator_model="claude-sonnet-5",
                    adjudicator_family="anthropic-adjudicator",
                )
        finally:
            conn.close()

    def path_for(self, level: str) -> Path:
        return self.db
