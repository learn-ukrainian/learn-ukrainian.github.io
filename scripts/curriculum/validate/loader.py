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
import re
from pathlib import Path

import yaml

from . import codes

REPO_ROOT = Path(__file__).resolve().parents[3]

PLAN_SCHEMA_PATH = "schemas/module-plan-v2.schema.json"

#: Removed v1 top-level fields and where each moved (§2, §2a). `content_outline`
#: is absent here on purpose: its presence makes the file a v1 plan (V1_PLAN).
REMOVED_V1_FIELDS = {
    "word_target": "word_target is deprecated per-lesson metadata (§2), not a module-level field",
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


def retirement_record(level_dir: Path) -> dict:
    """Read the strict append-only retirement inventory, or an empty inventory.

    Retirement is an exact-byte exclusion, never a waiver for an arc mismatch.
    Replacements with different bytes must pass every ordinary plan gate.
    """
    path = level_dir / "_retired.yaml"
    if not path.exists():
        return {"retirement_schema": 1, "plans": [], "routes": []}

    class UniqueLoader(yaml.SafeLoader):
        pass

    def unique_mapping(loader, node):
        pairs = loader.construct_pairs(node)
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key {key!r}")
            result[key] = value
        return result

    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
    try:
        record = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueLoader)
        if not isinstance(record, dict) or set(record) != {"retirement_schema", "plans", "routes"}:
            raise ValueError("expected exactly retirement_schema, plans and routes")
        if type(record["retirement_schema"]) is not int or record["retirement_schema"] != 1:
            raise ValueError("retirement_schema must be 1")
        for kind in ("plans", "routes"):
            entries = record[kind]
            if not isinstance(entries, list):
                raise ValueError(f"{kind} must be a list")
            seen = set()
            keys = {"slug", "old_position", "sha256"} if kind == "plans" else {"slug", "old_position"}
            for entry in entries:
                if not isinstance(entry, dict) or set(entry) != keys:
                    raise ValueError(f"{kind} entries require exactly {sorted(keys)}")
                slug = entry["slug"]
                if not isinstance(slug, str) or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) is None:
                    raise ValueError("slug must be a plain route slug")
                position = entry["old_position"]
                if type(position) is not int or position < 1:
                    raise ValueError("old_position must be a positive integer")
                if kind == "plans":
                    digest = entry["sha256"]
                    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                        raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
                    identity = (slug, digest)
                else:
                    identity = slug
                if identity in seen:
                    raise ValueError(f"duplicate {kind} retirement entry for {slug}")
                seen.add(identity)
        return record
    except (OSError, UnicodeError, yaml.YAMLError, ValueError, TypeError) as error:
        raise PlanError(codes.RETIREMENT_RECORD_INVALID, f"{path}: {error}") from error


def _retired_bytes(plan_path: Path, raw: bytes, record: dict) -> bool:
    digest = hashlib.sha256(raw).hexdigest()
    return any(entry["slug"] == plan_path.stem and entry["sha256"] == digest for entry in record["plans"])


def active_plan_paths(level_dir: Path) -> list[Path]:
    """List ordinary plans, excluding only explicitly retired exact bytes."""
    record = retirement_record(level_dir)
    return [
        path for path in sorted(level_dir.glob("*.yaml"))
        if not path.name.startswith("_") and not _retired_bytes(path, path.read_bytes(), record)
    ]


def retired_plan_paths(level_dir: Path) -> list[Path]:
    """Name the current exact-byte exclusions for honest whole-level reports."""
    active = set(active_plan_paths(level_dir))
    return [path for path in sorted(level_dir.glob("*.yaml")) if not path.name.startswith("_") and path not in active]


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
    Schema validation itself happens in validate.py. Typed core/incidental
    ``a1_reference_exception`` objects are preserved unchanged for C29; they
    never alter the vocabulary or letter state loaded for other gates. ``text`` replaces the file
    read (plan-promote validates the bytes it is about to publish in memory);
    plan_path still names where the plan lives.
    """
    record = retirement_record(plan_path.parent)
    if plan_path.name.startswith("_"):
        raise PlanError(codes.NOT_A_PLAN, f"{plan_path.name} begins with _; not a plan")
    if text is None and not plan_path.is_file():
        raise PlanError(codes.PLAN_NOT_FOUND, f"plan file {plan_path} does not exist")
    raw = plan_path.read_bytes() if text is None else text.encode("utf-8")
    if _retired_bytes(plan_path, raw, record):
        raise PlanError(codes.PLAN_RETIRED, f"{plan_path.stem} is explicitly retired at its exact SHA-256")
    try:
        data = yaml.safe_load(raw.decode("utf-8"))
    except (yaml.YAMLError, UnicodeError) as error:
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
    """Read ordinary plan text, refusing retired bytes before decoding content.

    Raw-text consumers share eligibility with ``load_plan`` without conflating
    that gate with their own publication, integrity or review checks.
    """
    record = retirement_record(plan_path.parent)
    if not plan_path.is_file():
        raise PlanError(codes.PLAN_NOT_FOUND, f"plan file {plan_path} does not exist")
    raw = plan_path.read_bytes()
    if _retired_bytes(plan_path, raw, record):
        raise PlanError(codes.PLAN_RETIRED, f"{plan_path.stem} is explicitly retired at its exact SHA-256")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PlanError(codes.PLAN_YAML_INVALID, f"{plan_path} is not valid UTF-8: {error}") from error


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
