"""Typed loader for the generated level arc YAML.

Reads curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml, validates it
against schemas/arc.schema.json, and re-verifies source.sha256 against the
current arc document so a stale generated file fails loudly instead of
feeding old data to the gates that consume the arc.

Scoping rule (docs/epics/fresh-build-plan-schema.md §1): load_arc resolves
only curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml. It never searches
curriculum/l2-uk-en/plans/ and never falls back to it; the arc_path /
doc_path overrides exist for tests and must be passed explicitly.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[3]

ARC_PATH = "curriculum/l2-uk-en/lesson-plans/{level}/_arc.yaml"
SCHEMA_PATH = "schemas/arc.schema.json"


class ArcStaleError(Exception):
    """The arc document changed after _arc.yaml was generated."""


@dataclass(frozen=True)
class ArcPosition:
    """One position of a level arc (one record of _arc.yaml)."""

    position: int
    slug: str
    est_lessons: int
    job: str
    inventory_text: str | None
    phase: str
    skills_text: str
    skills: list[str]
    standard_line_refs: list[tuple[int, int]]
    letters: list[str] | None = None
    band_key: str | None = None


def load_arc(level: str, *, arc_path: Path | None = None, doc_path: Path | None = None) -> list[ArcPosition]:
    """Load the generated arc for a level, validated against the JSON schema.

    Raises ArcStaleError when the arc document no longer matches the recorded
    source.sha256 — regenerate with
    ``scripts/curriculum/arc/generate_arc.py --level <level> --write``.
    arc_path / doc_path overrides exist for tests.
    """
    arc_path = arc_path or REPO_ROOT / ARC_PATH.format(level=level)
    plans_root = (REPO_ROOT / "curriculum/l2-uk-en/plans").resolve()
    resolved_arc = arc_path.resolve()
    if resolved_arc == plans_root or plans_root in resolved_arc.parents:
        raise ValueError(
            f"arc_path {arc_path} lies under curriculum/l2-uk-en/plans/; arcs live under "
            "curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml (lesson-plans/, never plans/)"
        )
    schema = json.loads((REPO_ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
    data = yaml.safe_load(arc_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=str)
    if errors:
        details = "\n".join(
            f"  - at {'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}" for e in errors
        )
        raise ValueError(f"{arc_path} fails {SCHEMA_PATH}:\n{details}")

    source = data["source"]
    doc_path = doc_path or REPO_ROOT / source["path"]
    actual = hashlib.sha256(doc_path.read_bytes()).hexdigest()
    if actual != source["sha256"]:
        raise ArcStaleError(
            f"arc document {source['path']} changed (recorded sha256 {source['sha256'][:12]}…, "
            f"current {actual[:12]}…) but {arc_path} was not regenerated; run "
            f".venv/bin/python scripts/curriculum/arc/generate_arc.py --level {level} --write"
        )

    for record in data["positions"]:
        for ref in record["standard_line_refs"]:
            if ref[0] > ref[1]:
                raise ValueError(
                    f"{arc_path} position {record['position']} has an inverted standard_line_refs range "
                    f"{ref} (start > end); the schema cannot express start <= end, so the loader checks it"
                )

    return [
        ArcPosition(
            position=record["position"],
            slug=record["slug"],
            est_lessons=record["est_lessons"],
            job=record["job"],
            inventory_text=record["inventory_text"],
            phase=record["phase"],
            skills_text=record["skills_text"],
            skills=list(record["skills"]),
            standard_line_refs=[(start, end) for start, end in record["standard_line_refs"]],
            letters=list(record["letters"]) if "letters" in record else None,
            band_key=record.get("band_key"),
        )
        for record in data["positions"]
    ]
