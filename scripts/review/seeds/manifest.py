"""The private measurement records: scoring manifests, set assignment, confirmation lock, identities (#8430 R3-A).

Everything here lives under ``batch_state/review-measurement/`` (``measurement_dir``): gitignored, files ``0o600``,
outside every prompt path (the prompt eligibility check refuses pins there). Layout::

    seeds/<seed_id>.yaml      the private scoring manifest of one seeded lesson
    clean/<clean_id>.yaml     the record of one measurement lesson that is meant to be clean
    sets.yaml                 unit id -> first | confirmation | rolling
    confirmation.lock         the frozen confirmation list and its sha256

**Identities are recorded, never assumed.** A seed's writer, planter and gold checker are recorded
when it is made, with the *model* each resolved to and the *family* the closeout resolver gives that
model; ``check_attempt_identity`` re-resolves every recorded model and refuses a record whose family
disagrees. The independence rules (header r2.1 "Roles and independence") are enforced fail-closed: an
identity that cannot be established refuses, it is never defaulted:

* writer is not the reviewer (the production rule);
* planter is neither the writer nor the reviewer;
* gold checker is neither the planter nor the reviewer, and its verdict is ``pass``;
* adjudicator is neither the writer nor the reviewer (``adjudicator_violations``).

A mechanical seed is made by a script: no planter and no gold checker exist, so those two rules do not apply.

**The held-out confirmation set.** ``freeze_confirmation`` partitions the inventory into ``first`` and
``confirmation`` (disjoint) and writes the lock exactly once; ``verify_confirmation_lock`` recomputes its hash and checks
it against the assignments, and the scorer calls it before scoring any run. A unit made after the freeze can only
be assigned ``rolling`` (``assign_set``).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.review import findings_db, second_seat

REPO_ROOT = Path(__file__).resolve().parents[3]
TAXONOMY_PATH = REPO_ROOT / "schemas" / "review-taxonomy-v1.yaml"
MEASUREMENT_DIR = ("batch_state", "review-measurement")
FILE_MODE = 0o600
DIRECTORY_MODE = 0o700

SETS = ("first", "confirmation", "rolling")
SEED_KINDS = ("mechanical", "linguistic")
SOURCE_KINDS = ("real_built", "canary", "fixture")  # only real_built lessons count toward threshold eligibility
GOLD_VERDICTS = ("pass", "fail", "not_applicable")
SEED_PREFIX = "seed-"
CLEAN_PREFIX = "clean-"
_TOKEN = r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}\Z"
SEED_ID_RE = re.compile(re.escape(SEED_PREFIX) + _TOKEN)
CLEAN_ID_RE = re.compile(re.escape(CLEAN_PREFIX) + _TOKEN)
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")

# Named codes. record.py raises RecordError with these; nothing is recorded for a refused pair.
SEED_IDENTITY_UNKNOWN = "seed_identity_unknown"
SEED_IDENTITY_MISMATCH = "seed_identity_mismatch"
REVIEWER_IS_WRITER = "same_family_review"  # the code record.py already uses for the production rule
PLANTER_IS_WRITER = "planter_is_writer"
PLANTER_IS_REVIEWER = "planter_is_reviewer"
GOLD_CHECKER_IS_PLANTER = "gold_checker_is_planter"
GOLD_CHECKER_IS_REVIEWER = "gold_checker_is_reviewer"
GOLD_CHECK_NOT_PASSED = "gold_check_not_passed"
ADJUDICATOR_IS_WRITER = "adjudicator_is_writer"
ADJUDICATOR_IS_REVIEWER = "adjudicator_is_reviewer"
CONFIRMATION_LOCK_MISSING = "confirmation_lock_missing"
CONFIRMATION_LOCK_INVALID = "confirmation_lock_invalid"
CONFIRMATION_FROZEN = "confirmation_frozen"
SET_CONFLICT = "set_conflict"
MANIFEST_INVALID = "manifest_invalid"
MANIFEST_EXISTS = "manifest_exists"
MANIFEST_MISSING = "manifest_missing"


class MeasurementError(Exception):
    """A measurement record is missing, malformed, or would break a rule; carries a named ``code``."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def measurement_dir(repo_root: Path | None = None) -> Path:
    """``batch_state/review-measurement`` of the primary checkout (never a worktree copy)."""
    return findings_db.batch_root(repo_root).joinpath(*MEASUREMENT_DIR)


# --- atomic private files ---------------------------------------------------------------


def write_private(path: Path, data: bytes, *, exclusive: bool = False) -> None:
    """Write ``data`` to ``path`` atomically with mode 0o600 (temp file in the same directory, fsync, rename).

    ``exclusive`` links the finished temp file to the name instead of replacing it, so an existing file is never
    overwritten (FileExistsError).
    """
    path.parent.mkdir(parents=True, exist_ok=True, mode=DIRECTORY_MODE)
    chain = [path.parent, *path.parent.parents]
    names = [directory.name for directory in chain]
    if MEASUREMENT_DIR[-1] in names:  # the measurement directory and everything below it is private, nothing above
        for directory in chain[: names.index(MEASUREMENT_DIR[-1]) + 1]:
            directory.chmod(DIRECTORY_MODE)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), FILE_MODE)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            os.link(temporary, path)
        else:
            os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _dump(document: dict[str, Any]) -> bytes:
    return yaml.safe_dump(document, sort_keys=True, allow_unicode=True, default_flow_style=False).encode("utf-8")


def _load(path: Path, what: str) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_bytes())
    except FileNotFoundError as error:
        raise MeasurementError(f"{what} {path.name} does not exist", MANIFEST_MISSING) from error
    except (OSError, yaml.YAMLError) as error:
        raise MeasurementError(f"{what} {path.name} is unreadable: {error}", MANIFEST_INVALID) from error
    if not isinstance(document, dict):
        raise MeasurementError(f"{what} {path.name} is not a mapping", MANIFEST_INVALID)
    return document


# --- the taxonomy -----------------------------------------------------------------------


def lesson_dimensions(taxonomy_path: Path | None = None) -> tuple[list[str], list[str]]:
    """``(all lesson dimensions, the ones a threshold-eligible report must cover)`` from the versioned taxonomy.

    The required ones are the lesson checks not marked ``optional``; the optional checks
    (``evidence_gap``, ``plan_defect``, ``engine_or_gate``) are not planted.
    """
    document = yaml.safe_load(Path(taxonomy_path or TAXONOMY_PATH).read_bytes())
    checks = document["kinds"]["lesson"]["checks"]
    return [check["name"] for check in checks], [check["name"] for check in checks if not check.get("optional")]


def sub_dimensions(dimension: str, taxonomy_path: Path | None = None) -> list[str]:
    document = yaml.safe_load(Path(taxonomy_path or TAXONOMY_PATH).read_bytes())
    return list((document.get("sub_dimensions") or {}).get(dimension, []))


# --- the seed and clean records ---------------------------------------------------------


@dataclass(frozen=True)
class Seed:
    """The private scoring manifest of one seeded lesson."""

    seed_id: str
    seed_kind: str
    source_kind: str
    level: str
    slug: str
    lesson_n: int
    dimension: str
    sub_dimension: str | None
    target_spans: list[dict[str, Any]]
    semantic_defect: str
    detection_criterion: str
    writer_family: str
    planter_model: str | None
    planter_family: str | None
    gold_checker_model: str | None
    gold_checker_family: str | None
    gold_verdict: str

    def document(self) -> dict[str, Any]:
        return {
            "scoring_manifest": 1,
            "seed_id": self.seed_id,
            "seed_kind": self.seed_kind,
            "source_kind": self.source_kind,
            "level": self.level,
            "slug": self.slug,
            "lesson_n": self.lesson_n,
            "dimension": self.dimension,
            "sub_dimension": self.sub_dimension,
            "target_spans": self.target_spans,
            "semantic_defect": self.semantic_defect,
            "detection_criterion": self.detection_criterion,
            "identities": {
                "writer_family": self.writer_family,
                "planter_model": self.planter_model,
                "planter_family": self.planter_family,
                "gold_checker_model": self.gold_checker_model,
                "gold_checker_family": self.gold_checker_family,
                "gold_verdict": self.gold_verdict,
            },
        }

    def identity_row(self) -> dict[str, Any]:
        """The ``seed_identities`` row: how this seed was made."""
        return {
            "seed_id": self.seed_id,
            "writer_family": self.writer_family,
            "planter_model": self.planter_model,
            "planter_family": self.planter_family,
            "gold_checker_model": self.gold_checker_model,
            "gold_checker_family": self.gold_checker_family,
            "gold_verdict": self.gold_verdict,
        }


@dataclass(frozen=True)
class Clean:
    """The record of one measurement lesson that is meant to be clean (its label comes from adjudication)."""

    clean_id: str
    source_kind: str
    level: str
    slug: str
    lesson_n: int
    writer_family: str

    def document(self) -> dict[str, Any]:
        return {
            "clean_manifest": 1,
            "clean_id": self.clean_id,
            "source_kind": self.source_kind,
            "level": self.level,
            "slug": self.slug,
            "lesson_n": self.lesson_n,
            "identities": {"writer_family": self.writer_family},
        }


def _text(document: dict[str, Any], key: str, what: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MeasurementError(f"{what}: {key} must be a non-empty string", MANIFEST_INVALID)
    return value


def _optional_text(container: dict[str, Any], key: str, what: str) -> str | None:
    value = container.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise MeasurementError(f"{what}: {key} must be a non-empty string or null", MANIFEST_INVALID)
    return value


def _common(document: dict[str, Any], what: str) -> tuple[str, str, int]:
    if document.get("source_kind") not in SOURCE_KINDS:
        raise MeasurementError(f"{what}: source_kind must be one of {list(SOURCE_KINDS)}", MANIFEST_INVALID)
    level = _text(document, "level", what)
    if not findings_db.LEVEL_RE.fullmatch(level):
        raise MeasurementError(f"{what}: level {level!r} is not a level token", MANIFEST_INVALID)
    lesson_n = document.get("lesson_n")
    if isinstance(lesson_n, bool) or not isinstance(lesson_n, int) or lesson_n < 1:
        raise MeasurementError(f"{what}: lesson_n must be a positive integer", MANIFEST_INVALID)
    return level, _text(document, "slug", what), lesson_n


def seed_from_document(document: dict[str, Any], *, taxonomy_path: Path | None = None) -> Seed:
    """Validate a scoring manifest document and return it as a :class:`Seed`; MeasurementError when it is unusable."""
    seed_id = document.get("seed_id")
    what = f"scoring manifest {seed_id!r}"
    if document.get("scoring_manifest") != 1:
        raise MeasurementError(f"{what}: scoring_manifest must be 1", MANIFEST_INVALID)
    if not isinstance(seed_id, str) or not SEED_ID_RE.fullmatch(seed_id):
        raise MeasurementError(f"{what}: seed_id must look like {SEED_PREFIX}<token>", MANIFEST_INVALID)
    if document.get("seed_kind") not in SEED_KINDS:
        raise MeasurementError(f"{what}: seed_kind must be one of {list(SEED_KINDS)}", MANIFEST_INVALID)
    level, slug, lesson_n = _common(document, what)
    dimension = _text(document, "dimension", what)
    all_dimensions, _ = lesson_dimensions(taxonomy_path)
    if dimension not in all_dimensions:
        raise MeasurementError(f"{what}: dimension {dimension!r} is not a lesson dimension", MANIFEST_INVALID)
    sub = _optional_text(document, "sub_dimension", what)
    if dimension == "language":
        if sub not in sub_dimensions("language", taxonomy_path):
            raise MeasurementError(f"{what}: a language seed needs a taxonomy sub_dimension", MANIFEST_INVALID)
    elif sub is not None:
        raise MeasurementError(f"{what}: only a language seed has a sub_dimension", MANIFEST_INVALID)
    spans = document.get("target_spans")
    if not isinstance(spans, list) or not spans or not all(isinstance(item, dict) and item for item in spans):
        raise MeasurementError(f"{what}: target_spans must be a non-empty list of location mappings", MANIFEST_INVALID)
    identities = document.get("identities")
    if not isinstance(identities, dict):
        raise MeasurementError(f"{what}: identities must be a mapping", MANIFEST_INVALID)
    seed = Seed(
        seed_id=seed_id,
        seed_kind=document["seed_kind"],
        source_kind=document["source_kind"],
        level=level,
        slug=slug,
        lesson_n=lesson_n,
        dimension=dimension,
        sub_dimension=sub,
        target_spans=spans,
        semantic_defect=_text(document, "semantic_defect", what),
        detection_criterion=_text(document, "detection_criterion", what),
        writer_family=_text(identities, "writer_family", what),
        planter_model=_optional_text(identities, "planter_model", what),
        planter_family=_optional_text(identities, "planter_family", what),
        gold_checker_model=_optional_text(identities, "gold_checker_model", what),
        gold_checker_family=_optional_text(identities, "gold_checker_family", what),
        gold_verdict=identities.get("gold_verdict"),
    )
    if seed.gold_verdict not in GOLD_VERDICTS:
        raise MeasurementError(f"{what}: gold_verdict must be one of {list(GOLD_VERDICTS)}", MANIFEST_INVALID)
    linguistic = (seed.planter_model, seed.planter_family, seed.gold_checker_model, seed.gold_checker_family)
    if seed.seed_kind == "mechanical":
        if any(value is not None for value in linguistic) or seed.gold_verdict != "not_applicable":
            raise MeasurementError(
                f"{what}: a mechanical seed is made by a script: no planter, no gold checker, gold_verdict"
                " not_applicable",
                MANIFEST_INVALID,
            )
    elif any(value is None for value in linguistic) or seed.gold_verdict == "not_applicable":
        raise MeasurementError(
            f"{what}: a linguistic seed records its planter and gold checker (model and family) and a gold verdict",
            SEED_IDENTITY_UNKNOWN,
        )
    return seed


def clean_from_document(document: dict[str, Any]) -> Clean:
    clean_id = document.get("clean_id")
    what = f"clean record {clean_id!r}"
    if document.get("clean_manifest") != 1:
        raise MeasurementError(f"{what}: clean_manifest must be 1", MANIFEST_INVALID)
    if not isinstance(clean_id, str) or not CLEAN_ID_RE.fullmatch(clean_id):
        raise MeasurementError(f"{what}: clean_id must look like {CLEAN_PREFIX}<token>", MANIFEST_INVALID)
    level, slug, lesson_n = _common(document, what)
    identities = document.get("identities")
    if not isinstance(identities, dict):
        raise MeasurementError(f"{what}: identities must be a mapping", MANIFEST_INVALID)
    return Clean(clean_id, document["source_kind"], level, slug, lesson_n, _text(identities, "writer_family", what))


def _seed_path(root: Path, seed_id: str) -> Path:
    if not SEED_ID_RE.fullmatch(seed_id):
        raise MeasurementError(f"{seed_id!r} is not a seed id ({SEED_PREFIX}<token>)", MANIFEST_INVALID)
    return measurement_dir(root) / "seeds" / f"{seed_id}.yaml"


def _clean_path(root: Path, clean_id: str) -> Path:
    if not CLEAN_ID_RE.fullmatch(clean_id):
        raise MeasurementError(f"{clean_id!r} is not a clean id ({CLEAN_PREFIX}<token>)", MANIFEST_INVALID)
    return measurement_dir(root) / "clean" / f"{clean_id}.yaml"


def _store(path: Path, document: dict[str, Any]) -> None:
    """Write an immutable record: the same content again is a no-op, different content is refused."""
    data = _dump(document)
    try:
        write_private(path, data, exclusive=True)
    except FileExistsError as error:
        if path.read_bytes() != data:
            raise MeasurementError(f"{path.name} already exists with different content", MANIFEST_EXISTS) from error


def write_scoring_manifest(seed: Seed, repo_root: Path | None = None) -> Path:
    """Store a seed's private scoring manifest (0o600). It never changes once written."""
    seed_from_document(seed.document())  # the same validation a reader applies
    path = _seed_path(repo_root, seed.seed_id)
    _store(path, seed.document())
    return path


def write_clean_record(clean: Clean, repo_root: Path | None = None) -> Path:
    clean_from_document(clean.document())
    path = _clean_path(repo_root, clean.clean_id)
    _store(path, clean.document())
    return path


def load_seed(seed_id: str, repo_root: Path | None = None) -> Seed:
    path = _seed_path(repo_root, seed_id)
    seed = seed_from_document(_load(path, "scoring manifest"))
    if seed.seed_id != seed_id:
        raise MeasurementError(f"{path.name} holds the manifest of {seed.seed_id}", MANIFEST_INVALID)
    return seed


def load_clean(clean_id: str, repo_root: Path | None = None) -> Clean:
    path = _clean_path(repo_root, clean_id)
    clean = clean_from_document(_load(path, "clean record"))
    if clean.clean_id != clean_id:
        raise MeasurementError(f"{path.name} holds the record of {clean.clean_id}", MANIFEST_INVALID)
    return clean


def unit_ids(repo_root: Path | None = None) -> tuple[list[str], list[str]]:
    """``(seed ids, clean ids)`` of every record on disk, sorted: the available inventory."""
    base = measurement_dir(repo_root)
    return (
        sorted(path.stem for path in (base / "seeds").glob(f"{SEED_PREFIX}*.yaml")),
        sorted(path.stem for path in (base / "clean").glob(f"{CLEAN_PREFIX}*.yaml")),
    )


def is_clean_id(unit_id: str) -> bool:
    return unit_id.startswith(CLEAN_PREFIX)


# --- independence -----------------------------------------------------------------------


def _unknown(what: str, value: Any) -> MeasurementError:
    return MeasurementError(
        f"{what} is unknown ({value!r}); an identity that cannot be established refuses", SEED_IDENTITY_UNKNOWN
    )


def _require_family(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _unknown(what, value)
    return value


def _reresolve(model: str | None, recorded_family: str | None, what: str) -> None:
    """The family recorded for ``model`` must be the one the resolver gives that model now."""
    try:
        resolved = second_seat.concrete_family(model, what=what)  # type: ignore[arg-type]
    except second_seat.IdentityError as error:
        raise MeasurementError(str(error), SEED_IDENTITY_UNKNOWN) from error
    if resolved != recorded_family:
        raise MeasurementError(
            f"{what}: recorded family {recorded_family!r} but {model!r} resolves to {resolved!r}",
            SEED_IDENTITY_MISMATCH,
        )


def independence_violations(seed: Seed, *, writer_family: str, reviewer_family: str) -> list[str]:
    """The named codes of every independence rule the (seed, reviewer) pair breaks; ``[]`` when it breaks none.

    ``writer_family`` is the writer of the measurement lesson as the record path resolved it from
    ``lesson-<n>.writer.yaml``; ``reviewer_family`` the reviewing seat's. Identities that are missing raise
    MeasurementError(``seed_identity_unknown``) instead: an unknown identity is not a passing one.
    """
    codes: list[str] = []
    if writer_family == reviewer_family:
        codes.append(REVIEWER_IS_WRITER)
    if seed.seed_kind == "linguistic":
        planter = _require_family(seed.planter_family, "the planter family")
        gold = _require_family(seed.gold_checker_family, "the gold checker family")
        if planter == writer_family:
            codes.append(PLANTER_IS_WRITER)
        if planter == reviewer_family:
            codes.append(PLANTER_IS_REVIEWER)
        if gold == planter:
            codes.append(GOLD_CHECKER_IS_PLANTER)
        if gold == reviewer_family:
            codes.append(GOLD_CHECKER_IS_REVIEWER)
        if seed.gold_verdict != "pass":
            codes.append(GOLD_CHECK_NOT_PASSED)
    return codes


def adjudicator_violations(*, writer_family: str, reviewer_family: str, adjudicator_family: str) -> list[str]:
    """The adjudicator is neither the writer's nor the reviewer's family."""
    codes = []
    if adjudicator_family == writer_family:
        codes.append(ADJUDICATOR_IS_WRITER)
    if adjudicator_family == reviewer_family:
        codes.append(ADJUDICATOR_IS_REVIEWER)
    return codes


def check_attempt_identity(
    unit_id: str,
    *,
    target: tuple[str, str, int],
    writer_family: str,
    reviewer_family: str,
    repo_root: Path | None = None,
) -> Seed | Clean:
    """Fail-closed identity check of one seeded or clean attempt; returns its record when every rule holds.

    Raises MeasurementError with the named code of the first violated rule, or ``seed_identity_unknown`` when the
    unit has no record or a recorded identity cannot be established, or ``seed_identity_mismatch`` when a recorded
    family is not what the resolver gives the recorded model, the recorded writer is not the live writer, or the
    attempt's ``target`` (level, slug, lesson number) is not the lesson the unit was recorded for.
    """
    _require_family(writer_family, "the writer family")
    _require_family(reviewer_family, "the reviewer family")
    if is_clean_id(unit_id):
        try:
            record: Seed | Clean = load_clean(unit_id, repo_root)
        except MeasurementError as error:
            if error.code == MANIFEST_MISSING:
                raise _unknown(f"the record of {unit_id}", None) from error
            raise
        violations = [REVIEWER_IS_WRITER] if writer_family == reviewer_family else []
    else:
        try:
            record = load_seed(unit_id, repo_root)
        except MeasurementError as error:
            if error.code == MANIFEST_MISSING:
                raise _unknown(f"the scoring manifest of {unit_id}", None) from error
            raise
        if record.seed_kind == "linguistic":
            _reresolve(record.planter_model, record.planter_family, f"{unit_id} planter")
            _reresolve(record.gold_checker_model, record.gold_checker_family, f"{unit_id} gold checker")
        violations = independence_violations(record, writer_family=writer_family, reviewer_family=reviewer_family)
    if (record.level, record.slug, record.lesson_n) != tuple(target):
        raise MeasurementError(
            f"{unit_id} was recorded for {record.level}/{record.slug} lesson {record.lesson_n}, not {tuple(target)}",
            SEED_IDENTITY_MISMATCH,
        )
    if record.writer_family != writer_family:
        raise MeasurementError(
            f"{unit_id} was recorded with a {record.writer_family!r} writer but lesson-{record.lesson_n}.writer.yaml"
            f" resolves to {writer_family!r}",
            SEED_IDENTITY_MISMATCH,
        )
    if violations:
        raise MeasurementError(
            f"{unit_id} reviewed by family {reviewer_family!r} (writer {writer_family!r}) breaks: {', '.join(violations)}",
            violations[0],
        )
    return record


# --- sets and the confirmation lock -----------------------------------------------------


def _sets_path(root: Path | None) -> Path:
    return measurement_dir(root) / "sets.yaml"


def _lock_path(root: Path | None) -> Path:
    return measurement_dir(root) / "confirmation.lock"


def load_assignments(repo_root: Path | None = None) -> dict[str, str]:
    """Unit id -> set, for every unit that has been assigned; ``{}`` before the first assignment."""
    path = _sets_path(repo_root)
    if not path.exists():
        return {}
    document = _load(path, "set assignments")
    assignments = document.get("assignments")
    if document.get("sets") != 1 or not isinstance(assignments, dict):
        raise MeasurementError("sets.yaml is not a version 1 assignment file", MANIFEST_INVALID)
    if any(value not in SETS for value in assignments.values()):
        raise MeasurementError(f"sets.yaml assigns a set outside {list(SETS)}", MANIFEST_INVALID)
    return dict(assignments)


def _write_assignments(root: Path | None, assignments: dict[str, str]) -> None:
    write_private(_sets_path(root), _dump({"sets": 1, "assignments": dict(sorted(assignments.items()))}))


def _has_record(root: Path | None, unit_id: str) -> bool:
    path = _clean_path(root, unit_id) if is_clean_id(unit_id) else _seed_path(root, unit_id)
    return path.is_file()


def assign_set(unit_id: str, set_name: str, repo_root: Path | None = None) -> None:
    """Put one unit in ``first`` or ``rolling`` (the confirmation set is only ever made by ``freeze_confirmation``).

    An assigned unit never moves; a unit made after the freeze can be ``rolling`` only.
    """
    if set_name not in SETS:
        raise MeasurementError(f"unknown set {set_name!r}", SET_CONFLICT)
    if not _has_record(repo_root, unit_id):
        raise MeasurementError(f"{unit_id} has no record to assign", MANIFEST_MISSING)
    if set_name == "confirmation":
        raise MeasurementError("the confirmation set is made only by freeze_confirmation", CONFIRMATION_FROZEN)
    frozen = _lock_path(repo_root).exists()
    if frozen and set_name == "first":
        raise MeasurementError(
            f"the confirmation set is frozen: {unit_id} made after the freeze can only be rolling", CONFIRMATION_FROZEN
        )
    assignments = load_assignments(repo_root)
    if assignments.get(unit_id, set_name) != set_name:
        raise MeasurementError(f"{unit_id} is already in {assignments[unit_id]}; a unit never moves", SET_CONFLICT)
    assignments[unit_id] = set_name
    _write_assignments(repo_root, assignments)


def lock_digest(seeds: list[str], clean: list[str]) -> str:
    """The sha256 of the frozen list: canonical JSON of the two sorted id lists."""
    payload = json.dumps({"clean": sorted(clean), "seeds": sorted(seeds)}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ConfirmationLock:
    seeds: tuple[str, ...]
    clean: tuple[str, ...]
    sha256: str
    frozen_at: str

    @property
    def unit_ids(self) -> frozenset[str]:
        return frozenset((*self.seeds, *self.clean))


def freeze_confirmation(
    confirmation_ids: list[str], repo_root: Path | None = None, *, now: str | None = None
) -> ConfirmationLock:
    """Partition the inventory into ``first`` and ``confirmation`` (disjoint) and freeze the confirmation list.

    ``confirmation_ids`` (seeds and clean lessons) become the confirmation set; every other record on disk that is
    not yet assigned becomes ``first``. The lock is written exactly once (a second freeze is refused) with the
    sha256 of the sorted list. A crash between the assignments and the lock is completed by running the same
    freeze again.
    """
    if _lock_path(repo_root).exists():
        raise MeasurementError("the confirmation set is already frozen; it is written once", CONFIRMATION_FROZEN)
    ids = sorted(set(confirmation_ids))
    if not ids:
        raise MeasurementError("the confirmation set is empty", CONFIRMATION_LOCK_INVALID)
    assignments = load_assignments(repo_root)
    for unit_id in ids:
        if not _has_record(repo_root, unit_id):
            raise MeasurementError(f"{unit_id} has no record to freeze", MANIFEST_MISSING)
        if assignments.get(unit_id, "confirmation") != "confirmation":
            raise MeasurementError(f"{unit_id} is already in {assignments[unit_id]}", SET_CONFLICT)
    stale = sorted(unit for unit, name in assignments.items() if name == "confirmation" and unit not in ids)
    if stale:
        raise MeasurementError(f"{stale} are assigned confirmation but not in this list", SET_CONFLICT)
    seeds, cleans = unit_ids(repo_root)
    for unit_id in ids:
        assignments[unit_id] = "confirmation"
    for unit_id in (*seeds, *cleans):
        assignments.setdefault(unit_id, "first")
    _write_assignments(repo_root, assignments)
    lock_seeds = [unit for unit in ids if not is_clean_id(unit)]
    lock_clean = [unit for unit in ids if is_clean_id(unit)]
    document = {
        "lock": 1,
        "frozen_at": now or findings_db.now_iso(),
        "seeds": lock_seeds,
        "clean": lock_clean,
        "sha256": lock_digest(lock_seeds, lock_clean),
    }
    write_private(_lock_path(repo_root), _dump(document), exclusive=True)
    return verify_confirmation_lock(repo_root)


def verify_confirmation_lock(repo_root: Path | None = None) -> ConfirmationLock:
    """Read the lock, recompute its hash and check it against the assignments; refuse anything that differs.

    Raises ``confirmation_lock_missing`` when there is no lock and ``confirmation_lock_invalid`` when the list no
    longer hashes to the recorded sha256, a listed unit has no record, or the assignments disagree with the list.
    """
    path = _lock_path(repo_root)
    if not path.exists():
        raise MeasurementError(
            "no confirmation.lock: the confirmation set has not been frozen", CONFIRMATION_LOCK_MISSING
        )
    document = _load(path, "confirmation lock")
    seeds, clean, digest = document.get("seeds"), document.get("clean"), document.get("sha256")
    if (
        document.get("lock") != 1
        or not isinstance(seeds, list)
        or not isinstance(clean, list)
        or not all(isinstance(item, str) for item in (*seeds, *clean))
        or not isinstance(digest, str)
        or not isinstance(document.get("frozen_at"), str)
    ):
        raise MeasurementError("confirmation.lock is malformed", CONFIRMATION_LOCK_INVALID)
    if lock_digest(seeds, clean) != digest:
        raise MeasurementError(
            f"the confirmation list hashes to {lock_digest(seeds, clean)}, the lock records {digest}",
            CONFIRMATION_LOCK_INVALID,
        )
    listed = {*seeds, *clean}
    if (
        len(listed) != len(seeds) + len(clean)
        or any(is_clean_id(item) for item in seeds)
        or not all(is_clean_id(item) for item in clean)
    ):
        raise MeasurementError(
            "confirmation.lock repeats a unit or files it in the wrong list", CONFIRMATION_LOCK_INVALID
        )
    missing = sorted(item for item in listed if not _has_record(repo_root, item))
    if missing:
        raise MeasurementError(f"the locked units {missing} have no record", CONFIRMATION_LOCK_INVALID)
    confirmed = {unit for unit, name in load_assignments(repo_root).items() if name == "confirmation"}
    if confirmed != listed:
        raise MeasurementError(
            f"the assignments put {sorted(confirmed ^ listed)} on one side of the frozen list only",
            CONFIRMATION_LOCK_INVALID,
        )
    return ConfirmationLock(tuple(seeds), tuple(clean), digest, document["frozen_at"])
