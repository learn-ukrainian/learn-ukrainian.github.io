"""Content-addressed plan-review attempt manifest and the plan review's freshness rules.

A plan review (docs/epics/fresh-build-review-contracts.md, "Contract 1") runs
against one manifest holding the sha256 of every input the reviewer sees. The
engine writes it after two reports exist and are current: the strict
``pack-verify`` report of the provisional pack (written here, in-process) and the
provisional ``plan-validate`` report (written by ``plan-validate --write-report``).
This module also owns the shared freshness check that decides whether a review of
record still describes the tree — before promotion (every input unchanged) and
after promotion (every input unchanged except the plan, whose only allowed
difference is the ``evidence_ref.sha256`` transition proven by the promotion
receipt). The helpers of ``manifest.py`` are reused, including its private
``_input``.

The manifest names every file the reviewer receives. Besides the plan, the pack
and word store (each with its lock) and the reports, that includes the full prior
planned learner state: the engine writes it as deterministic YAML
(``plan-review.learner-state.yaml`` with its lock sidecar) and records it as
``inputs.learner_state``. ``learner_state.sha256`` stays the canonical-JSON
identity of the same ``planned_state`` result the file holds.

Contract 1 also hands the reviewer "the requirements and the arc's system-or-chunk
table". The requirements are ``docs/epics/fresh-build-requirements.md``
(``inputs.requirements``). ``_arc.yaml`` is a per-position extract that does not
carry the system-or-chunk table, so the arc source document it names in
``source.path`` (``docs/epics/fresh-build-<level>-arc.md``, section 3) is pinned as
``inputs.arc_source``.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.manifest import _input, learner_state_document, learner_state_sha256, materialize_learner_state
from scripts.build.fresh.manifest import sha256 as file_sha256
from scripts.build.fresh.path_guard import checked_path, validate_module
from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state.planned import PlannedStateError, planned_state
from scripts.curriculum.validate.loader import PlanError, load_plan
from scripts.curriculum.validate.validate import REPORT_NAME as VALIDATE_REPORT_NAME
from scripts.curriculum.validate.validate import _declared_pack_path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA = REPO_ROOT / "schemas" / "plan-review-manifest-v1.schema.json"
TREE = "curriculum/l2-uk-en"
PACK_VERIFY_REPORT_NAME = "pack-verify.report.json"
MANIFEST_NAME = "plan-review.manifest.yaml"
SIDECAR_NAME = "plan-review.manifest.sha256"
LEARNER_STATE_NAME = "plan-review.learner-state.yaml"
REQUIREMENTS_REL = "docs/epics/fresh-build-requirements.md"
REVIEW_NAME = "plan-review.yaml"
RECEIPT_NAME = "plan-promotion.yaml"
_SHA = re.compile(r"[0-9a-f]{64}")

#: The manifest input names, in schema order.
INPUT_NAMES = (
    "plan",
    "pack",
    "pack_lock",
    "words",
    "words_lock",
    "learner_state",
    "requirements",
    "arc",
    "arc_source",
    "decisions",
    "scope",
    "grammar",
    "validate_report",
    "pack_verify_report",
)
_RECEIPT_KEYS = (
    "manifest_sha256",
    "reviewed_plan_sha256",
    "promoted_plan_sha256",
    "pack_sha256",
    "attempt_id",
    "promoted_at",
)

# Refusal codes (stable identifiers; the CLI prints them as the JSON reason prefix).
INPUT_MISSING = "input_missing"
PLAN_UNREADABLE = "plan_unreadable"
ARC_UNREADABLE = "arc_unreadable"
PACK_PATH_MISMATCH = "pack_path_mismatch"
PACK_CHANGED_DURING_VERIFY = "pack_changed_during_verify"
PACK_VERIFY_REFUSED = "pack_verify_report_refused"
VALIDATE_REPORT_REFUSED = "validate_report_refused"
LEARNER_STATE_UNAVAILABLE = "learner_state_unavailable"
LOCK_MISMATCH = "lock_mismatch"
MANIFEST_INVALID = "manifest_invalid"
MANIFEST_COLLISION = "manifest_collision"
REVIEW_MISSING = "review_missing"
REVIEW_NOT_APPROVED = "review_not_approved"
MANIFEST_HASH_MISMATCH = "manifest_hash_mismatch"
INPUTS_CHANGED_SINCE_REVIEW = "inputs_changed_since_review"
PROMOTED_PLAN_INVALID = "promoted_plan_invalid"
PROMOTION_FAILED = "promotion_failed"


class PlanReviewError(ValueError):
    """A refusal with a stable code and, when it concerns files, the paths at fault."""

    def __init__(self, code: str, message: str, paths: list[str] | None = None):
        self.code = code
        self.message = message
        self.paths = sorted(paths or [])
        super().__init__(f"{code}: {message}")


def state_dir(root: Path, level: str, slug: str) -> Path:
    return root / TREE / "evidence" / level / "_state" / slug


def _guarded(root: Path, path: Path, allowed: str = f"{TREE}/evidence") -> Path:
    return checked_path(root, path.relative_to(root), allowed)


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def current_sha(root: Path, relative: str) -> str | None:
    """sha256 of a recorded repo-relative path now; None when it is not a file.

    ``schemas/…`` entries are code, resolved against this repository (the same
    root outside tests); everything else against the tree's repository root.
    """
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        return None
    base = REPO_ROOT if rel.parts[:1] == ("schemas",) else root
    path = base / rel
    return file_sha256(path) if path.is_file() else None


# --- the plan's single-field promotion edit ------------------------------------------


def promoted_plan_bytes(plan_bytes: bytes, pack_sha256: str) -> bytes:
    """The plan bytes with ``evidence_ref.sha256`` set to ``pack_sha256`` and nothing else changed.

    A YAML-preserving edit: the value's own span in the file is replaced (its
    quote style kept), so comments, key order and every other byte survive. The
    result is parsed and compared with the original document; anything but the
    one field differing — or the value not reading back as a string — is refused.
    """
    text = plan_bytes.decode("utf-8")
    node = yaml.compose(text, Loader=yaml.SafeLoader)
    for key in ("evidence_ref", "sha256"):
        if not isinstance(node, yaml.MappingNode):
            raise PlanReviewError(PLAN_UNREADABLE, "the plan has no evidence_ref.sha256 mapping to promote")
        node = next((value for name, value in node.value if getattr(name, "value", None) == key), None)
    if not isinstance(node, yaml.ScalarNode):
        raise PlanReviewError(PLAN_UNREADABLE, "the plan has no evidence_ref.sha256 scalar to promote")
    start, end = node.start_mark.index, node.end_mark.index
    quote = text[start] if text[start : start + 1] in {"'", '"'} else ""
    candidates = [quote + pack_sha256 + quote] if quote else [pack_sha256, f"'{pack_sha256}'"]
    expected = yaml.safe_load(text)
    expected["evidence_ref"]["sha256"] = pack_sha256
    for candidate in candidates:
        edited = text[:start] + candidate + text[end:]
        if yaml.safe_load(edited) == expected:
            return edited.encode("utf-8")
    raise PlanReviewError(PLAN_UNREADABLE, "evidence_ref.sha256 cannot be replaced without changing another field")


# --- reports ---------------------------------------------------------------------------


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def verify_pack_strict(level: str, slug: str, **kwargs: Any) -> dict[str, Any]:
    """``pack-verify --strict`` in-process on the pack of (level, slug).

    A thin import-late wrapper over ``scripts.curriculum.evidence.verify.verify_pack``
    (not edited here; #8527 owns it) so importing this module stays cheap.
    """
    from scripts.curriculum.evidence.verify import verify_pack

    return verify_pack(level, slug, strict=True, **kwargs)


def pack_verify_report(
    level: str, slug: str, result: dict[str, Any], pack: dict[str, str], pack_lock: dict[str, str]
) -> dict:
    """The stored pack-verify report: the verified pack and lock hashes, the status and every finding."""
    return {
        "report_schema": 1,
        "kind": "pack-verify",
        "strict": True,
        "level": level,
        "slug": slug,
        "pack": pack,
        "pack_lock": pack_lock,
        "status": result.get("status"),
        "errors": list(result.get("errors", [])),
        "warnings": list(result.get("warnings", [])),
        "reports": list(result.get("reports", [])),
        "chunk_id_moved": list(result.get("chunk_id_moved", [])),
        "not_checked": list(result.get("not_checked", [])),
        "counts": {key: value for key, value in sorted(result.items()) if key.endswith("_count")},
    }


def json_bytes(document: dict) -> bytes:
    """Deterministic report bytes: sorted keys, UTF-8, trailing newline."""
    return (json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def pack_verify_problems(root: Path, level: str, slug: str, report_path: Path) -> dict[str, str]:
    """Why the stored pack-verify report is not a strict pass over the current pack and lock ({path: why})."""
    pack_rel = f"{TREE}/evidence/{level}/{slug}.yaml"
    report_rel = _relative(root, report_path)
    report = _read_json(report_path)
    if report is None:
        return {report_rel: "missing, unreadable or not a JSON object"}
    problems: dict[str, str] = {}
    if report.get("kind") != "pack-verify" or (report.get("level"), report.get("slug")) != (level, slug):
        problems[report_rel] = "not a pack-verify report of this module"
    if report.get("strict") is not True or report.get("status") != "ok" or report.get("errors"):
        problems[report_rel] = "not a strict pass (status ok, no errors)"
    for key, rel in (("pack", pack_rel), ("pack_lock", f"{pack_rel}.lock")):
        recorded = report.get(key) if isinstance(report.get(key), dict) else {}
        actual = current_sha(root, rel)
        if recorded.get("path") != rel or actual is None or recorded.get("sha256") != actual:
            problems[rel] = f"differs from the {key} the pack-verify report verified"
    if not lock.check(root / pack_rel):
        problems[pack_rel] = "the pack bytes disagree with their lock"
    return problems


def validate_report_problems(
    root: Path,
    level: str,
    slug: str,
    report_path: Path,
    *,
    plan_transition: tuple[str, str] | None = None,
) -> dict[str, str]:
    """Why the stored plan-validate report is not a current provisional pass ({path: why}).

    Every recorded input hash must equal the file now. ``plan_transition`` is
    ``(plan path, reviewed sha)``: after a proven promotion the report's plan
    entry legitimately still holds the reviewed hash.
    """
    report_rel = _relative(root, report_path)
    report = _read_json(report_path)
    if report is None:
        return {report_rel: "missing, unreadable or not a JSON object"}
    problems: dict[str, str] = {}
    if (report.get("level"), report.get("slug")) != (level, slug):
        problems[report_rel] = "not a plan-validate report of this module"
    if report.get("status") != "pass" or report.get("failures") or report.get("waivers"):
        problems[report_rel] = "not a clean pass (status pass, zero failures, no waivers)"
    if report.get("mode") != "provisional":
        problems[report_rel] = "not a provisional-mode report (run plan-validate --provisional-pack --write-report)"
    inputs = report.get("inputs")
    if not isinstance(inputs, dict) or not inputs:
        problems[report_rel] = "records no inputs"
        return problems
    plan_rel = f"{TREE}/lesson-plans/{level}/{slug}.yaml"
    pack_rel = f"{TREE}/evidence/{level}/{slug}.yaml"
    required = {
        plan_rel,
        pack_rel,
        f"{pack_rel}.lock",
        f"{TREE}/evidence/{level}/_words.yaml",
        f"{TREE}/evidence/{level}/_words.yaml.lock",
        f"{TREE}/lesson-plans/{level}/_arc.yaml",
        f"{TREE}/lesson-plans/{level}/_grammar.yaml",
        f"{TREE}/lesson-plans/{level}/_scope/{slug}.yaml",
    }
    for path in sorted(required - set(inputs)):
        problems[path] = "not among the inputs the plan-validate report recorded"
    for path, recorded in sorted(inputs.items()):
        if plan_transition is not None and path == plan_transition[0]:
            if recorded != plan_transition[1]:
                problems[path] = "the plan-validate report recorded a plan other than the reviewed one"
            continue
        if current_sha(root, path) != recorded:
            problems[path] = "changed since the plan-validate report read it"
    return problems


# --- manifest ----------------------------------------------------------------------------


def _manifest_schema_validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))


def validate_manifest_document(manifest: Any) -> None:
    errors = sorted(_manifest_schema_validator().iter_errors(manifest), key=lambda error: error.json_path)
    if errors:
        raise PlanReviewError(MANIFEST_INVALID, "; ".join(f"{e.json_path}: {e.message}" for e in errors))
    try:
        validate_module(manifest["level"], manifest["slug"])
    except ValueError as error:
        raise PlanReviewError(MANIFEST_INVALID, str(error)) from error
    for name, entry in manifest["inputs"].items():
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise PlanReviewError(MANIFEST_INVALID, f"inputs.{name}.path {entry['path']!r} is not repo-relative")


def manifest_paths(root: Path, level: str, slug: str) -> tuple[Path, Path]:
    directory = state_dir(root, level, slug)
    return directory / MANIFEST_NAME, directory / SIDECAR_NAME


def history_path(root: Path, level: str, slug: str, digest: str) -> Path:
    return state_dir(root, level, slug) / "manifests" / "plan" / f"{digest}.yaml"


def unlink_current(root: Path, level: str, slug: str) -> None:
    for path in manifest_paths(root, level, slug):
        path.unlink(missing_ok=True)


def prior_planned_state(root: Path, level: str, position: int) -> Any:
    """The full prior planned learner state before this position (lesson 1).

    No waiver: a plan review needs every earlier position present, so a missing
    prior plan refuses instead of reviewing against an incomplete state.
    """
    try:
        return planned_state(
            level,
            position,
            1,
            plans_dir=root / TREE / "lesson-plans" / level,
            evidence_dir=root / TREE / "evidence" / level,
        )
    except PlannedStateError as error:
        raise PlanReviewError(LEARNER_STATE_UNAVAILABLE, str(error)) from error


def planned_state_sha256(root: Path, level: str, position: int) -> str:
    """The canonical-JSON identity of :func:`prior_planned_state`."""
    return learner_state_sha256(prior_planned_state(root, level, position))


def _arc_source_path(root: Path, arc_path: Path) -> Path:
    """The arc source document ``_arc.yaml`` names in ``source.path`` (a repo-relative docs/epics markdown file)."""
    try:
        recorded = yaml.safe_load(arc_path.read_bytes())["source"]["path"]
    except (OSError, yaml.YAMLError, KeyError, TypeError) as error:
        raise PlanReviewError(ARC_UNREADABLE, f"{_relative(root, arc_path)} names no source document") from error
    relative = Path(str(recorded))
    if relative.is_absolute() or ".." in relative.parts or relative.parts[:2] != ("docs", "epics"):
        raise PlanReviewError(
            ARC_UNREADABLE, f"{_relative(root, arc_path)} source.path {recorded!r} is not under docs/epics"
        )
    path = root / relative
    if not path.is_file():
        raise PlanReviewError(INPUT_MISSING, f"input missing: {relative.as_posix()}", [relative.as_posix()])
    return path


def _entry(root: Path, path: Path) -> dict[str, str]:
    try:
        return _input(path, root)
    except FileNotFoundError as error:
        raise PlanReviewError(
            INPUT_MISSING, f"input missing: {_relative(root, path)}", [_relative(root, path)]
        ) from error


def write_plan_manifest(level: str, slug: str, *, repo_root: Path, sources_instance: Any = None) -> tuple[dict, str]:
    """Run pack-verify --strict on the provisional pack, then write the plan-review manifest.

    Refuses (PlanReviewError, and the current manifest pointer is removed so a
    stale one is never read as current) when an input is missing, the
    pack-verify result is not a strict pass, or the plan-validate report is
    not a current provisional pass. Returns (manifest, sha256 of its bytes).
    """
    root = repo_root.resolve()
    try:
        return _write_plan_manifest(level, slug, root, sources_instance)
    except PlanReviewError:
        unlink_current(root, level, slug)
        raise


def _write_plan_manifest(level: str, slug: str, root: Path, sources_instance: Any) -> tuple[dict, str]:
    plans = root / TREE / "lesson-plans" / level
    evidence = root / TREE / "evidence" / level
    directory = state_dir(root, level, slug)
    plan_path = plans / f"{slug}.yaml"
    pack_path = evidence / f"{slug}.yaml"
    words_path = evidence / "_words.yaml"
    files = {
        "plan": plan_path,
        "pack": pack_path,
        "pack_lock": Path(f"{pack_path}.lock"),
        "words": words_path,
        "words_lock": Path(f"{words_path}.lock"),
        "arc": plans / "_arc.yaml",
        "decisions": plans / "_decisions.yaml",
        "scope": plans / "_scope" / f"{slug}.yaml",
        "grammar": plans / "_grammar.yaml",
        "validate_report": directory / VALIDATE_REPORT_NAME,
        "requirements": root / REQUIREMENTS_REL,
    }
    missing = [_relative(root, path) for path in files.values() if not path.is_file()]
    if missing:
        raise PlanReviewError(INPUT_MISSING, "input missing: " + ", ".join(missing), missing)
    files["arc_source"] = _arc_source_path(root, files["arc"])

    try:
        plan = load_plan(plan_path)
        position = plan["arc_ref"]["position"]
        declared = _declared_pack_path(root / TREE, plan["evidence_ref"]["path"])
    except (PlanError, KeyError, TypeError) as error:
        raise PlanReviewError(PLAN_UNREADABLE, f"{_relative(root, plan_path)}: {error}") from error
    if declared != pack_path.resolve():
        raise PlanReviewError(
            PACK_PATH_MISMATCH,
            f"evidence_ref.path resolves to {declared}, not the module pack {_relative(root, pack_path)} "
            "that pack-verify checks",
        )

    pack_before = (file_sha256(pack_path), file_sha256(files["pack_lock"]))
    try:
        result = verify_pack_strict(
            level, slug, evidence_dir=evidence, plans_dir=plans, sources_instance=sources_instance
        )
    except (OSError, sqlite3.Error) as error:
        raise PlanReviewError(PACK_VERIFY_REFUSED, f"pack-verify --strict could not run: {error}") from error
    if (file_sha256(pack_path), file_sha256(files["pack_lock"])) != pack_before:
        raise PlanReviewError(PACK_CHANGED_DURING_VERIFY, f"{_relative(root, pack_path)} changed while pack-verify ran")
    report_path = _guarded(root, directory / PACK_VERIFY_REPORT_NAME)
    document = pack_verify_report(
        level,
        slug,
        result,
        {"path": _relative(root, pack_path), "sha256": pack_before[0]},
        {"path": _relative(root, files["pack_lock"]), "sha256": pack_before[1]},
    )
    lock.atomic_write(report_path, json_bytes(document), mode=0o600)
    files["pack_verify_report"] = report_path

    problems = pack_verify_problems(root, level, slug, report_path)
    if problems:
        raise PlanReviewError(
            PACK_VERIFY_REFUSED,
            "pack-verify --strict is not a pass over the current pack: "
            + "; ".join(f"{path} ({why})" for path, why in sorted(problems.items())),
            list(problems),
        )
    problems = validate_report_problems(root, level, slug, files["validate_report"])
    if problems:
        raise PlanReviewError(
            VALIDATE_REPORT_REFUSED,
            "the plan-validate report is not a current provisional pass: "
            + "; ".join(f"{path} ({why})" for path, why in sorted(problems.items())),
            list(problems),
        )

    for name in ("pack", "words"):
        if not lock.check(files[name]):
            raise PlanReviewError(
                LOCK_MISMATCH, f"{_relative(root, files[name])} disagrees with its lock", [_relative(root, files[name])]
            )
    state = prior_planned_state(root, level, position)
    state_path = _guarded(root, directory / LEARNER_STATE_NAME)
    try:
        materialize_learner_state(state_path, learner_state_document(state), root)
    except (OSError, ValueError) as error:
        raise PlanReviewError(
            LEARNER_STATE_UNAVAILABLE, f"cannot write {_relative(root, state_path)}: {error}"
        ) from error
    files["learner_state"] = state_path

    manifest = {
        "manifest_schema": 1,
        "kind": "plan",
        "level": level,
        "slug": slug,
        "position": position,
        "inputs": {name: _entry(root, files[name]) for name in INPUT_NAMES},
        "learner_state": {"sha256": learner_state_sha256(state), "source": "planned_state"},
    }
    validate_manifest_document(manifest)
    content = lock.yaml_bytes(manifest)
    digest = sha256_bytes(content)
    history = _guarded(root, history_path(root, level, slug, digest))
    if history.exists():
        if history.read_bytes() != content:
            raise PlanReviewError(
                MANIFEST_COLLISION, f"content-addressed manifest collision: {_relative(root, history)}"
            )
    else:
        lock.atomic_write(history, content)
    current, sidecar = (_guarded(root, path) for path in manifest_paths(root, level, slug))
    lock.atomic_write(current, content)
    lock.atomic_write(sidecar, f"{digest}\n".encode("ascii"))
    return manifest, digest


# --- freshness ---------------------------------------------------------------------------


@dataclass
class Freshness:
    """Whether a manifest's inputs still describe the tree.

    ``state`` is ``fresh`` (every input unchanged), ``promoted`` (every input
    unchanged except the plan, whose evidence_ref.sha256 transition the
    promotion receipt proves) or ``stale``; ``stale`` maps each offending path
    to why.
    """

    state: str
    stale: dict[str, str] = field(default_factory=dict)


def _read_receipt(directory: Path) -> dict | None:
    path = directory / RECEIPT_NAME
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_bytes())
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _receipt_proof(root: Path, manifest: dict, manifest_sha: str, live_plan: bytes | None) -> tuple[bool, str]:
    """(proved, why not): the promotion receipt proves the live plan is the reviewed plan plus the pack hash."""
    level, slug = manifest["level"], manifest["slug"]
    directory = state_dir(root, level, slug)
    receipt = _read_receipt(directory)
    if receipt is None:
        return False, "no promotion receipt"
    if receipt.get("manifest_sha256") != manifest_sha:
        return False, "the promotion receipt belongs to another manifest"
    if set(receipt) != set(_RECEIPT_KEYS) or not all(isinstance(receipt[key], str) for key in _RECEIPT_KEYS):
        return False, "the promotion receipt is malformed"
    reviewed_sha = manifest["inputs"]["plan"]["sha256"]
    if receipt["reviewed_plan_sha256"] != reviewed_sha:
        return False, "the promotion receipt does not map the reviewed plan hash"
    if live_plan is None or receipt["promoted_plan_sha256"] != sha256_bytes(live_plan):
        return False, "the plan is not the plan the promotion receipt recorded"
    pack_path = root / TREE / "evidence" / level / f"{slug}.yaml"
    if not pack_path.is_file() or receipt["pack_sha256"] != file_sha256(pack_path):
        return False, "the pack is not the pack the promotion receipt recorded"
    reviewed_copy = directory / f"plan-reviewed.{reviewed_sha}.yaml"
    if not reviewed_copy.is_file() or sha256_bytes(reviewed_copy.read_bytes()) != reviewed_sha:
        return False, "the reviewed plan copy is missing or altered"
    try:
        expected = promoted_plan_bytes(reviewed_copy.read_bytes(), receipt["pack_sha256"])
    except PlanReviewError:
        return False, "the reviewed plan copy cannot be promoted"
    if expected != live_plan:
        return False, "the plan differs from the reviewed plan in more than evidence_ref.sha256"
    return True, ""


def plan_review_freshness(root: Path, manifest: dict, manifest_sha: str) -> Freshness:
    """Re-check every manifest input, both reports' recorded inputs, the pack and words
    against their locks, and the planned learner-state hash.

    The one allowed difference from the manifest is the plan hash, and only when
    the promotion receipt proves the transition (see ``_receipt_proof``).
    """
    root = root.resolve()
    level, slug = manifest["level"], manifest["slug"]
    stale: dict[str, str] = {}
    inputs = manifest["inputs"]

    for name in INPUT_NAMES:
        if name == "plan":
            continue
        entry = inputs[name]
        actual = current_sha(root, entry["path"])
        if actual is None:
            stale.setdefault(entry["path"], "missing")
        elif actual != entry["sha256"]:
            stale.setdefault(entry["path"], "changed since the manifest")

    plan_entry = inputs["plan"]
    plan_file = root / plan_entry["path"]
    live_plan = plan_file.read_bytes() if plan_file.is_file() else None
    proved, why = _receipt_proof(root, manifest, manifest_sha, live_plan)
    promoted = proved
    if live_plan is None:
        stale.setdefault(plan_entry["path"], "missing")
    elif not proved and sha256_bytes(live_plan) != plan_entry["sha256"]:
        stale.setdefault(plan_entry["path"], f"changed since the manifest ({why})")

    pack_rel = f"{TREE}/evidence/{level}/{slug}.yaml"
    words_rel = f"{TREE}/evidence/{level}/_words.yaml"
    for rel in (pack_rel, words_rel):
        if not (root / rel).is_file():
            stale.setdefault(rel, "missing")
        elif not lock.check(root / rel):
            stale.setdefault(rel, "its bytes disagree with its lock")

    directory = state_dir(root, level, slug)
    transition = (plan_entry["path"], plan_entry["sha256"]) if promoted else None
    for path, reason in validate_report_problems(
        root, level, slug, directory / VALIDATE_REPORT_NAME, plan_transition=transition
    ).items():
        stale.setdefault(path, reason)
    for path, reason in pack_verify_problems(root, level, slug, directory / PACK_VERIFY_REPORT_NAME).items():
        stale.setdefault(path, reason)

    try:
        state_sha = planned_state_sha256(root, level, manifest["position"])
    except PlanReviewError as error:
        stale.setdefault("learner_state", f"cannot be recomputed ({error.message})")
    else:
        if state_sha != manifest["learner_state"]["sha256"]:
            stale.setdefault("learner_state", "the planned learner state changed since the manifest")

    if stale:
        return Freshness("stale", stale)
    return Freshness("promoted" if promoted else "fresh")


def load_manifest_of_record(root: Path, level: str, slug: str, digest: str) -> dict:
    """The immutable history copy of a manifest, verified against its content address."""
    path = history_path(root, level, slug, digest)
    try:
        content = path.read_bytes()
    except OSError as error:
        raise PlanReviewError(
            MANIFEST_HASH_MISMATCH, f"no manifest {digest} in the history", [_relative(root, path)]
        ) from error
    if sha256_bytes(content) != digest:
        raise PlanReviewError(
            MANIFEST_HASH_MISMATCH, f"{_relative(root, path)} does not hash to its name", [_relative(root, path)]
        )
    manifest = yaml.safe_load(content)
    validate_manifest_document(manifest)
    return manifest


def read_review(root: Path, level: str, slug: str) -> dict:
    """plan-review.yaml (written by the future R2b record step): the three fields read here are
    ``verdict``, ``manifest_sha256`` and ``attempt_id``."""
    path = state_dir(root, level, slug) / REVIEW_NAME
    if not path.is_file():
        raise PlanReviewError(
            REVIEW_MISSING, f"no plan review of record: {_relative(root, path)}", [_relative(root, path)]
        )
    try:
        review = yaml.safe_load(path.read_bytes())
    except yaml.YAMLError as error:
        raise PlanReviewError(REVIEW_MISSING, f"{_relative(root, path)} is not valid YAML: {error}") from error
    if not isinstance(review, dict) or not _SHA.fullmatch(str(review.get("manifest_sha256", ""))):
        raise PlanReviewError(REVIEW_MISSING, f"{_relative(root, path)} carries no manifest_sha256")
    if review.get("verdict") != "APPROVE":
        raise PlanReviewError(REVIEW_NOT_APPROVED, f"the plan review verdict is {review.get('verdict')!r}, not APPROVE")
    if not isinstance(review.get("attempt_id"), str) or not review["attempt_id"]:
        raise PlanReviewError(REVIEW_MISSING, f"{_relative(root, path)} carries no attempt_id")
    return review


def plan_review_status(level: str, slug: str, *, repo_root: Path) -> dict[str, Any]:
    """The state of the plan review of record.

    ``unreviewed`` (no review file), ``not_approved``, ``reviewed_pending_promotion``
    (APPROVE, every input unchanged, plan not yet promoted), ``reviewed_promoted``
    (APPROVE and the receipt-proven plan transition) or ``stale`` (with every
    changed path). Only the two ``reviewed_*`` states are a plan review a build may rely on.
    """
    root = repo_root.resolve()
    try:
        review = read_review(root, level, slug)
    except PlanReviewError as error:
        state = {REVIEW_MISSING: "unreviewed", REVIEW_NOT_APPROVED: "not_approved"}[error.code]
        return {"state": state, "reason": error.message, "stale": {}}
    digest = review["manifest_sha256"]
    try:
        manifest = load_manifest_of_record(root, level, slug, digest)
    except PlanReviewError as error:
        return {
            "state": "stale",
            "reason": error.message,
            "stale": {path: "manifest of record unavailable" for path in error.paths},
        }
    freshness = plan_review_freshness(root, manifest, digest)
    if freshness.state == "stale":
        return {"state": "stale", "manifest_sha256": digest, "stale": dict(sorted(freshness.stale.items()))}
    state = "reviewed_promoted" if freshness.state == "promoted" else "reviewed_pending_promotion"
    return {"state": state, "manifest_sha256": digest, "attempt_id": review["attempt_id"], "stale": {}}
