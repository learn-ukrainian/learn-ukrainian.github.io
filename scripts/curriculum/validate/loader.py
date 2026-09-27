"""Finds and loads one module plan, failing closed (issue #8412, Brief A).

Scoping rule (docs/epics/fresh-build-plan-schema.md §1): a plan lives at
curriculum/l2-uk-en/lesson-plans/<level>/<slug>.yaml and nowhere else. The
loader resolves the path first, then refuses anything not under that root —
a path under curriculum/l2-uk-en/plans/ gets a message naming lesson-plans/ —
refuses a file whose name begins with an underscore ("not a plan"), refuses
a plan whose file name, requested slug and ``slug`` field are not one value,
and rejects v1 plans and removed v1 fields before the JSON Schema ever runs, so
those failures name their own rule code instead of surfacing as a generic
schema error. The root is read off the resolved path's components, so tests
can build a fixture tree anywhere.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from . import codes

REPO_ROOT = Path(__file__).resolve().parents[3]

PLAN_SCHEMA_PATH = "schemas/module-plan-v2.schema.json"

#: Removed v1 top-level fields and where each moved (§2, §2a). `content_outline`
#: is absent here on purpose: its presence makes the file a v1 plan (V1_PLAN).
REMOVED_V1_FIELDS = {
    "word_target": "word_target is per lesson now (§2), not a module-level field",
    "references": "references moved to the evidence pack (§2)",
    "vocabulary_hints": "vocabulary_hints moved to the evidence pack (§2)",
    "pedagogy": "pedagogy: PPP as a module-wide label was replaced by the lesson shape (§2)",
    "minutes": "minutes is computed, never typed (§2a); until the constants exist it is not computed either",
}


class PlanError(Exception):
    """A plan (or one of its inputs) failed; carries the outcome code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _path_parts(path: Path) -> tuple[str, ...]:
    return path.resolve().parts


def resolve_plan_path(level: str, slug: str, plan_path: Path | None = None) -> Path:
    """Resolve the plan path and enforce the lesson-plans/ scoping rule.

    The default path is <cwd>/curriculum/l2-uk-en/lesson-plans/<level>/<slug>.yaml
    relative to this repository; plan_path overrides exist for tests, but the
    root rule applies to them too.
    """
    plan_path = plan_path or REPO_ROOT / f"curriculum/l2-uk-en/lesson-plans/{level}/{slug}.yaml"
    resolved = plan_path.resolve()
    parts = _path_parts(resolved)
    for index in range(len(parts) - 2):
        if parts[index : index + 3] == ("curriculum", "l2-uk-en", "plans"):
            raise PlanError(
                codes.PLAN_OUTSIDE_LESSON_PLANS,
                f"{resolved} lies under curriculum/l2-uk-en/plans/; v2 plans live under "
                "curriculum/l2-uk-en/lesson-plans/<level>/ (lesson-plans/, never plans/)",
            )
    tail = ("curriculum", "l2-uk-en", "lesson-plans", level)
    if len(parts) > len(tail) and parts[-len(tail) - 1 : -1] == tail:
        if resolved.name.startswith("_"):
            raise PlanError(
                codes.NOT_A_PLAN,
                f"{resolved.name} begins with _; every name in lesson-plans/<level>/ that "
                "begins with an underscore is not a plan (§2a)",
            )
        return resolved
    raise PlanError(
        codes.PLAN_OUTSIDE_LESSON_PLANS,
        f"{resolved} is not curriculum/l2-uk-en/lesson-plans/{level}/<slug>.yaml; "
        "the validator reads plans only under lesson-plans/<level>/",
    )


def evidence_root(plan_path: Path) -> Path:
    """The curriculum/l2-uk-en directory the resolved plan lives under."""
    parts = _path_parts(plan_path)
    for index in range(len(parts) - 1):
        if parts[index : index + 2] == ("curriculum", "l2-uk-en"):
            return Path(*parts[: index + 2])
    raise PlanError(
        codes.PLAN_OUTSIDE_LESSON_PLANS,
        f"{plan_path} is not under curriculum/l2-uk-en/; cannot derive the evidence root",
    )


def load_plan(plan_path: Path, *, text: str | None = None) -> dict:
    """Read the plan file, reject v1 plans and removed v1 fields, return the dict.

    The raw text is returned by read_plan_text for the stress-mark scan; JSON
    Schema validation itself happens in validate.py. ``text`` replaces the file
    read (plan-promote validates the bytes it is about to publish in memory);
    plan_path still names where the plan lives.
    """
    if text is None and not plan_path.is_file():
        raise PlanError(codes.PLAN_NOT_FOUND, f"plan file {plan_path} does not exist")
    try:
        data = yaml.safe_load(plan_path.read_text(encoding="utf-8") if text is None else text)
    except yaml.YAMLError as error:
        raise PlanError(codes.PLAN_YAML_INVALID, f"{plan_path} is not valid YAML: {error}") from error
    if not isinstance(data, dict):
        raise PlanError(codes.PLAN_YAML_INVALID, f"{plan_path} does not hold a mapping at the top level")
    if data.get("plan_schema") != 2 or "content_outline" in data:
        raise PlanError(
            codes.V1_PLAN,
            f"{plan_path} is a v1 plan (no plan_schema: 2, or a content_outline key); "
            "v1 plans are not read or converted (§7.4)",
        )
    for field, moved in REMOVED_V1_FIELDS.items():
        if field in data:
            raise PlanError(codes.REMOVED_V1_FIELD, f"{plan_path} carries removed v1 field {field!r}: {moved}")
    if "scope" in data:
        raise PlanError(
            codes.SCOPE_KEY_IN_PLAN,
            f"{plan_path} carries a 'scope' key; scope is a generated sidecar "
            "(lesson-plans/<level>/_scope/<slug>.yaml), never part of the hand-written plan (§2a)",
        )
    return data


def check_plan_slug(plan_path: Path, slug: str, plan: dict) -> None:
    """The file name, the requested slug and plan["slug"] must be one value (§2a).

    A module plan is <slug>.yaml. Single-plan mode is asked for a slug on the
    command line and --all reads the plan's own slug field; the scope sidecar
    is keyed on that slug, so a renamed file (or a slug field that disagrees
    with its file name) would let the two modes read different sidecars.
    """
    if plan_path.stem != slug:
        raise PlanError(
            codes.PLAN_SLUG_MISMATCH,
            f"{plan_path.name} was validated as slug {slug!r}; a module plan is <slug>.yaml (§2a)",
        )
    if plan.get("slug") != slug:
        raise PlanError(
            codes.PLAN_SLUG_MISMATCH,
            f"{plan_path.name} carries slug {plan.get('slug')!r}; a module plan is <slug>.yaml, "
            "so its slug field must equal its file name (§2a)",
        )


def read_plan_text(plan_path: Path) -> str:
    """The plan file's raw text, for the U+0301/U+0300 scan (rule 7)."""
    if not plan_path.is_file():
        raise PlanError(codes.PLAN_NOT_FOUND, f"plan file {plan_path} does not exist")
    return plan_path.read_text(encoding="utf-8")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
