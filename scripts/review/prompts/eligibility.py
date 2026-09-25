"""Pin eligibility: which documents a reviewer may receive (#8430 Part R2 item 1).

``docs/epics/fresh-build-review-contracts.md`` principle 4 says the reviewer never sees the
writer's prompt, reasoning or self-assessment, no earlier edition and no other module's content,
and "The review attempt manifest (r4)" makes the manifest "the complete, transitive input set".
So the question this module answers is about *documents*, never about text: is every file the
manifest pins one of the inputs the contract lists for this manifest kind, at this module's own
path for the current build? It never judges a file's text; the one file it opens is the pinned lesson,
to list the activity files that lesson imports.

Each manifest kind has one table below (kind -> pin location -> the one path that location may
have). The locations come from the manifest schemas (``schemas/lesson-review-manifest-v1.schema.json``,
``schemas/plan-review-manifest-v1.schema.json``) and the contract sections cited on each table.
A later worker adds ``settle`` by adding its table; a kind without a table is refused.

The manifest is first validated against its schema (``manifest_schema_invalid``), so every input
the schema requires is pinned. Then each pin is judged: the writer-material and foreign-module
refusals apply to every pin of every kind, before anything else can accept it. The one pin kind that
is a *set* rather than a path, ``inputs.activity_data[]``, is refused outright (the engine emits no data
imports), and the pinned lesson's imports (derived with the engine's own ``_activity_imports``, after the
lesson's bytes are checked against its pin) must be empty too: that is the only place this module reads a file.

Refusal codes, one per rule (each pin gets the first that applies):

- ``manifest_schema_invalid``    the manifest does not match its schema (a required input is missing)
- ``manifest_module_invalid``    the manifest's own level or slug is not a valid module
- ``pin_location_not_allowed``   rule (a): the pin sits at a location the contract does not list
                                 for this manifest kind (including a kind with no table)
- ``pin_path_not_repo_relative`` the path is absolute, has ``..``, is not normalised, or a symlink
                                 leads it elsewhere
- ``pin_v1_or_archive_tree``     a v1 tree, the old un-versioned level tree, an archive or ``plans/``
- ``pin_writer_material``        a writer prompt, draft, raw output, gap report or other writer file
- ``pin_superseded_snapshot``    a content-addressed lesson snapshot, a history manifest or another
                                 attempt's review or diff (the re-review's own diff base and previous
                                 findings are the pins at the ``diff`` and ``previous_attempt.*``
                                 locations, so they pass the exact-path rule)
- ``pin_foreign_module``         another module's (or another level's) directory or file
- ``pin_outside_module_paths``   anything else that is not this module's path for that location
- ``pin_activity_data_unsupported`` any ``inputs.activity_data[]`` pin: the engine emits no data imports
- ``pin_activity_data_mismatch`` the pinned lesson imports activity data (which no pin can then cover)
"""

from __future__ import annotations

import functools
import hashlib
import json
import posixpath
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.build.fresh import manifest as lesson_manifest
from scripts.build.fresh import plan_manifest
from scripts.build.fresh.manifest import _activity_imports, pinned_entries
from scripts.build.fresh.path_guard import SLUG_RE
from scripts.build.fresh.prompt import BAND_CARD_MAP

TREE = "curriculum/l2-uk-en"

MANIFEST_SCHEMA_INVALID = "manifest_schema_invalid"
MANIFEST_MODULE_INVALID = "manifest_module_invalid"
PIN_LOCATION_NOT_ALLOWED = "pin_location_not_allowed"
PIN_PATH_NOT_REPO_RELATIVE = "pin_path_not_repo_relative"
PIN_V1_OR_ARCHIVE_TREE = "pin_v1_or_archive_tree"
PIN_WRITER_MATERIAL = "pin_writer_material"
PIN_SUPERSEDED_SNAPSHOT = "pin_superseded_snapshot"
PIN_FOREIGN_MODULE = "pin_foreign_module"
PIN_OUTSIDE_MODULE_PATHS = "pin_outside_module_paths"
PIN_ACTIVITY_DATA_MISMATCH = "pin_activity_data_mismatch"
PIN_ACTIVITY_DATA_UNSUPPORTED = "pin_activity_data_unsupported"


@dataclass(frozen=True)
class Refusal:
    code: str
    location: str
    path: str
    reason: str

    def __str__(self) -> str:
        return f"{self.code}: {self.location} -> {self.path}: {self.reason}"


@dataclass(frozen=True)
class _Module:
    level: str
    slug: str
    lesson: int | None
    attempt: str | None

    @property
    def state(self) -> str:
        return f"{TREE}/evidence/{re.escape(self.level)}/_state/{re.escape(self.slug)}"

    @property
    def plans(self) -> str:
        return f"{TREE}/lesson-plans/{re.escape(self.level)}"

    @property
    def evidence(self) -> str:
        return f"{TREE}/evidence/{re.escape(self.level)}"

    @property
    def pages(self) -> str:
        return f"site/src/content/docs/{re.escape(self.level)}/{re.escape(self.slug)}"


# Each location maps to a function giving the full-match regex of the one path it may have.
_Table = dict[str, Callable[[_Module, dict[str, Any]], str]]

#: Lesson review, first or re-review (contract: "The review attempt manifest (r4)", lesson review;
#: "Contract 2 - lesson review", Receives). ``upstream_lessons[]`` is the recap's built lessons
#: 1..N-1; ``diff`` and ``previous_attempt.*`` exist only on a re-review.
LESSON_LOCATIONS: _Table = {
    "inputs.plan": lambda m, e: f"{m.plans}/{re.escape(m.slug)}\\.yaml",
    "inputs.pack": lambda m, e: f"{m.evidence}/{re.escape(m.slug)}\\.yaml",
    "inputs.pack_lock": lambda m, e: f"{m.evidence}/{re.escape(m.slug)}\\.yaml\\.lock",
    "inputs.words": lambda m, e: f"{m.evidence}/_words\\.yaml",
    "inputs.words_lock": lambda m, e: f"{m.evidence}/_words\\.yaml\\.lock",
    "inputs.learner_state": lambda m, e: f"{m.state}/lesson-{m.lesson}\\.learner-state\\.yaml",
    "inputs.lessons_lock": lambda m, e: f"{m.state}/lessons\\.lock\\.yaml",
    "inputs.lesson": lambda m, e: f"{m.pages}/{m.lesson}\\.mdx",
    # No ``inputs.activity_data[]`` entry on purpose: the engine emits no data imports today (activity data
    # is inline component props), so any such pin is refused (``pin_activity_data_unsupported``). When the
    # engine does emit them, add a positive per-module location rule here (see
    # ``scripts/generate_mdx/core.py:781-822`` and ``_activity_imports`` in ``scripts/build/fresh/manifest.py``).
    "inputs.gate_report": lambda m, e: f"{m.state}/lesson-{m.lesson}\\.gates\\.yaml",
    "inputs.style_card": lambda m, e: (
        f"docs/style-cards/{BAND_CARD_MAP.get(m.level.lower().split('-')[0], 'b1plus')}\\.md"
    ),
    "inputs.decisions": lambda m, e: f"{m.plans}/_decisions\\.yaml",
    "module_digest": lambda m, e: f"{m.state}/digest-upto-{m.lesson}\\.yaml",
    "upstream_lessons[]": lambda m, e: f"{m.pages}/{re.escape(str(e.get('n')))}\\.mdx",
    "diff": lambda m, e: f"{m.state}/lesson-{m.lesson}\\.diff\\.{re.escape(str(m.attempt))}\\.[0-9a-f]{{16}}\\.patch",
    "previous_attempt.review": lambda m, e: (
        f"{m.state}/lesson-{m.lesson}\\.review\\.{re.escape(str(m.attempt))}\\.yaml"
    ),
    "previous_attempt.ledger": lambda m, e: (
        f"batch_state/review-receipts/[A-Za-z0-9][A-Za-z0-9._-]{{0,127}}/{re.escape(str(m.attempt))}\\.jsonl"
    ),
}

#: Plan review (contract: "The review attempt manifest (r4)", plan review; "Contract 1 - plan review",
#: Receives). The arc source is the level's arc document that ``_arc.yaml`` names.
PLAN_LOCATIONS: _Table = {
    "inputs.plan": LESSON_LOCATIONS["inputs.plan"],
    "inputs.pack": LESSON_LOCATIONS["inputs.pack"],
    "inputs.pack_lock": LESSON_LOCATIONS["inputs.pack_lock"],
    "inputs.words": LESSON_LOCATIONS["inputs.words"],
    "inputs.words_lock": LESSON_LOCATIONS["inputs.words_lock"],
    "inputs.learner_state": lambda m, e: f"{m.state}/plan-review\\.learner-state\\.yaml",
    "inputs.requirements": lambda m, e: "docs/epics/fresh-build-requirements\\.md",
    "inputs.arc": lambda m, e: f"{m.plans}/_arc\\.yaml",
    "inputs.arc_source": lambda m, e: f"docs/epics/fresh-build-{re.escape(m.level)}-arc\\.md",
    "inputs.decisions": LESSON_LOCATIONS["inputs.decisions"],
    "inputs.scope": lambda m, e: f"{m.plans}/_scope/{re.escape(m.slug)}\\.yaml",
    "inputs.grammar": lambda m, e: f"{m.plans}/_grammar\\.yaml",
    "inputs.validate_report": lambda m, e: f"{m.state}/plan-validate\\.report\\.json",
    "inputs.pack_verify_report": lambda m, e: f"{m.state}/pack-verify\\.report\\.json",
}

#: The one table per manifest kind; a settle table is added by the worker that adds ``settle.md.j2``.
LOCATIONS: dict[str, _Table] = {"lesson": LESSON_LOCATIONS, "plan": PLAN_LOCATIONS}

#: The re-review's own pins: its diff base (inside the pinned diff) and its previous findings.
RE_REVIEW_LOCATIONS = frozenset({"diff", "previous_attempt.review", "previous_attempt.ledger"})

#: Writer-side files of the fresh engine (``scripts/build/fresh/{writer,runner,regeneration,module}.py``):
#: ``lesson-N.prompt.md`` and its sha256, the draft, the writer's record, its raw output, gap reports,
#: constrained questions and resolutions, the regeneration ledger, and the module build record.
WRITER_FILE = re.compile(
    r"(?:^|/)(?:lesson-\d+\.(?:prompt\.(?:md|sha256)|draft\.yaml|writer\.yaml|raw\.txt|gaps\.yaml"
    r"|questions\.yaml|resolutions\.yaml(?:\.lock)?|regeneration\.yaml)|module\.build\.yaml)\Z"
)
#: Any other file that names itself as a writer prompt, reasoning or self-assessment.
WRITER_WORD = re.compile(r"(?i)(?:^|[/._-])(?:prompt|writer|reasoning|self[-_]?assess\w*)(?:[._-]|\Z)")
#: Dispatch prompts and results (writer and other seats' task files) live here; only receipts do not.
DISPATCH_TREE = "batch_state/"
RECEIPT_TREE = "batch_state/review-receipts/"

#: Kept content-addressed lesson snapshots, history manifests, and other attempts' reviews and diffs.
SUPERSEDED = re.compile(
    r"(?:^|/)manifests/|(?:^|/)lesson\.[0-9a-f]{64}\.mdx\Z|(?:^|/)lesson-\d+\.(?:review|diff)\.[^/]+\Z"
)

#: Module-scoped roots: the pattern names a level and (mostly) a slug.
_MODULE_ROOTS: tuple[re.Pattern[str], ...] = (
    re.compile(rf"{TREE}/evidence/(?P<level>[^/]+)/_state/(?P<slug>[^/]+)/"),
    re.compile(rf"{TREE}/evidence/(?P<level>[^/]+)/(?P<slug>[^/_][^/]*?)\.yaml(?:\.lock)?\Z"),
    re.compile(rf"{TREE}/lesson-plans/(?P<level>[^/]+)/(?P<slug>[^/_][^/]*?)\.yaml\Z"),
    re.compile(rf"{TREE}/lesson-plans/(?P<level>[^/]+)/_scope/(?P<slug>[^/]+?)\.yaml\Z"),
    re.compile(r"site/src/content/docs/(?P<level>[^/]+)/(?P<slug>[^/]+)/"),
)
_LEVEL_ROOT = re.compile(rf"{TREE}/(?:evidence|lesson-plans)/(?P<level>[^/]+)/")


def _is_v1_or_archive(parts: list[str]) -> bool:
    return (
        any(part.endswith("-v1") for part in parts)
        or parts[0] in {"archive", "archives", "plans"}
        or (parts[:2] == ["curriculum", "l2-uk-en"] and len(parts) > 3 and parts[2] not in {"evidence", "lesson-plans"})
    )


def _is_writer_material(path: str, slug: str) -> bool:
    """A writer file by engine name or by self-description (the module's own slug is not a description)."""
    if path.startswith(DISPATCH_TREE) and not path.startswith(RECEIPT_TREE):
        return True
    return bool(WRITER_FILE.search(path) or WRITER_WORD.search(posixpath.basename(path).replace(slug, "")))


def _is_foreign(path: str, module: _Module) -> bool:
    for root in _MODULE_ROOTS:
        found = root.match(path)
        if found and (found.group("level"), found.group("slug")) != (module.level, module.slug):
            return True
    level = _LEVEL_ROOT.match(path)
    return bool(level and level.group("level") != module.level)


def _classify(
    path: str, location: str, module: _Module, entry: dict[str, Any], table: _Table, root: Path
) -> Refusal | None:
    key = re.sub(r"\[\d+\]", "[]", location)

    def refuse(code: str, reason: str) -> Refusal:
        return Refusal(code, location, path, reason)

    if key not in table:
        return refuse(PIN_LOCATION_NOT_ALLOWED, f"the contract lists no {location} input for this manifest kind")
    parts = path.split("/")
    if (
        not path
        or path.startswith("/")
        or "\\" in path
        or ".." in parts
        or posixpath.normpath(path) != path
        or (root / path).resolve() != (root.resolve() / path)
    ):
        return refuse(PIN_PATH_NOT_REPO_RELATIVE, "not a normalised repo-relative path that resolves to itself")
    if _is_v1_or_archive(parts):
        return refuse(PIN_V1_OR_ARCHIVE_TREE, "a v1 tree, the old level tree, an archive or plans/ is never an input")
    # Writer material and another module's files are refused for every pin kind, before any path can be accepted.
    if _is_writer_material(path, module.slug):
        return refuse(PIN_WRITER_MATERIAL, "writer prompts, drafts and raw output are never an input")
    if _is_foreign(path, module):
        return refuse(PIN_FOREIGN_MODULE, f"not a file of module {module.level}/{module.slug}")
    if re.fullmatch(table[key](module, entry), path):
        return None
    if SUPERSEDED.search(path):
        return refuse(PIN_SUPERSEDED_SNAPSHOT, "an earlier edition or another attempt's file is never an input")
    return refuse(PIN_OUTSIDE_MODULE_PATHS, f"{location} is not at this module's path for it")


#: The schema each manifest kind must match; a kind without one has no table either and is refused below.
SCHEMAS: dict[str, Path] = {"lesson": lesson_manifest.SCHEMA, "plan": plan_manifest.SCHEMA}


@functools.cache
def _validator(kind: str) -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMAS[kind].read_text(encoding="utf-8")))


def schema_refusals(manifest: dict[str, Any]) -> list[Refusal]:
    """Each way the manifest departs from its schema, so a required pin cannot simply be left out."""
    kind = manifest.get("kind")
    if kind not in SCHEMAS:
        return []
    return [
        Refusal(
            MANIFEST_SCHEMA_INVALID,
            ".".join(str(part) for part in error.absolute_path) or "manifest",
            SCHEMAS[kind].name,
            error.message[:200],
        )
        for error in sorted(_validator(kind).iter_errors(manifest), key=lambda e: [str(p) for p in e.absolute_path])
    ]


def activity_data_refusals(manifest: dict[str, Any], repo_root: Path) -> list[Refusal]:
    """``inputs.activity_data[]`` must be exactly the activity files the pinned lesson imports.

    The expected set comes from the engine's own ``_activity_imports`` (what the manifest writer pinned),
    read from the lesson only when its bytes hash to its pin; a lesson that does not is left to the hash
    verification, which refuses it. An extra, a missing or a repeated path is refused.
    """
    root = repo_root.resolve()
    pins = dict(pinned_entries(manifest))
    lesson = pins.get("inputs.lesson")
    if lesson is None:
        return []
    location = "inputs.activity_data"
    listed = [(name, entry["path"]) for name, entry in pins.items() if name.startswith(f"{location}[")]
    try:
        mdx = (root / lesson["path"]).resolve()
        if hashlib.sha256(mdx.read_bytes()).hexdigest() != lesson["sha256"]:
            return []
        expected = {path.relative_to(root).as_posix() for path in _activity_imports(mdx, root)}
    except (OSError, ValueError, UnicodeDecodeError) as err:
        return [
            Refusal(
                PIN_ACTIVITY_DATA_MISMATCH,
                location,
                lesson["path"],
                f"the lesson's activity imports are unknown ({err})",
            )
        ]
    refusals = [
        Refusal(PIN_ACTIVITY_DATA_MISMATCH, name, path, "not an activity file the pinned lesson imports")
        for name, path in listed
        if path not in expected
    ]
    refusals += [
        Refusal(PIN_ACTIVITY_DATA_MISMATCH, name, path, "pinned more than once")
        for index, (name, path) in enumerate(listed)
        if path in expected and path in {other for _, other in listed[:index]}
    ]
    refusals += [
        Refusal(PIN_ACTIVITY_DATA_MISMATCH, location, path, "an activity file the pinned lesson imports is not pinned")
        for path in sorted(expected - {path for _, path in listed})
    ]
    return refusals


def pin_refusals(manifest: dict[str, Any], repo_root: Path) -> list[Refusal]:
    """Every pin that may not reach the reviewer, each with its rule's code; empty when all are eligible.

    The manifest must match its schema first. The per-pin rules judge the recorded paths against the
    module the manifest names and read nothing; a path whose symlinks lead somewhere else than the path
    says is refused. Only when every pin passed is the activity-data set compared with the lesson's imports.
    """
    invalid = schema_refusals(manifest)
    if invalid:
        return invalid
    level, slug = manifest.get("level"), manifest.get("slug")
    if not (isinstance(level, str) and isinstance(slug, str) and SLUG_RE.fullmatch(slug) and SLUG_RE.fullmatch(level)):
        return [Refusal(MANIFEST_MODULE_INVALID, "level/slug", f"{level!r}/{slug!r}", "not a valid module identifier")]
    kind = manifest.get("kind")
    table = LOCATIONS.get(str(kind))
    previous = manifest.get("previous_attempt")
    attempt = previous.get("attempt_id") if isinstance(previous, dict) else None
    lesson = manifest.get("lesson")
    module = _Module(
        level, slug, lesson if isinstance(lesson, int) else None, attempt if isinstance(attempt, str) else None
    )
    refusals: list[Refusal] = []
    for location, entry in pinned_entries(manifest):
        path = entry["path"]
        if table is None:
            refusals.append(
                Refusal(PIN_LOCATION_NOT_ALLOWED, location, path, f"the contract lists no inputs for kind {kind!r}")
            )
            continue
        key = re.sub(r"\[\d+\]", "[]", location)
        if key == "inputs.activity_data[]":
            refusals.append(
                Refusal(
                    PIN_ACTIVITY_DATA_UNSUPPORTED,
                    location,
                    path,
                    "the engine emits no data imports; there is no module-owned activity-data location to pin",
                )
            )
            continue
        if key in RE_REVIEW_LOCATIONS and module.attempt is None:
            refusals.append(
                Refusal(
                    PIN_LOCATION_NOT_ALLOWED, location, path, "a re-review input on a manifest with no previous attempt"
                )
            )
            continue
        refusal = _classify(path, location, module, entry, table, repo_root)
        if refusal is not None:
            refusals.append(refusal)
    if not refusals and kind == "lesson":
        refusals.extend(activity_data_refusals(manifest, repo_root))
    return refusals
