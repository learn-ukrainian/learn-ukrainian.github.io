"""A bounded worker is dispatched only with a complete advisory envelope (#9275).

Operator decision 2026-09-30: there is no direct bounded dispatch. Every
dispatch that resolves to the catalog's bounded worker
(``execution_routing.sol_advised_bounded.preferred_worker``), or to its Gemini
Flash fallback without an explicit Ukrainian authoring/review classification,
needs an envelope from the catalog advisor route, bound to that dispatch.

The envelope is accepted only by reference to the advisor's task
(``delegate.py dispatch --advisory-task <task-id>``), never as a free file. The
advisor task must have run with ``--advisory-role bounded_advisory_envelope``
on the advisor model, read-only, and finished ``done``. Its canonical result
must hold exactly one fenced ``advisory-envelope`` JSON object with every
catalog ``output_fields`` key, typed and meaningful, plus the
``dispatch_args_sha256`` binding digest of the worker dispatch that the advisor
dispatch recorded as ``advisory_binding_sha256``.

This module is pure validation: it reads a task record and its result, and
raises ``AdvisoryRefused`` with a typed code. ``delegate.py`` computes the
binding digest, calls it after route resolution and again just before the task
record is published, and checks the ceilings at finalize.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.review.model_catalog import (
    ADVISOR_ROUTE,
    BoundedExecutionPolicy,
    bounded_execution_policy,
    canonical_model_id,
)

ENVELOPE_FENCE = "advisory-envelope"
BINDING_FIELD = "dispatch_args_sha256"
_FENCE_RE = re.compile(r"^```" + re.escape(ENVELOPE_FENCE) + r"[ \t]*\n(.*?)\n```[ \t]*$", re.MULTILINE | re.DOTALL)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GLOB_CHARS = frozenset("*?[")
# Repo roots a bounded worker never owns: git metadata, dispatch worktrees,
# interpreter and dependency trees, and delegate's own task state.
_FORBIDDEN_ROOTS = frozenset({".git", ".worktrees", ".venv", "node_modules", "batch_state"})
# Owned paths that make a Ukrainian classification contradictory: a Ukrainian
# authoring or review task does not own code.
_CODE_ROOTS = ("scripts/", "tests/", ".github/", "agents_extensions/", "hooks/")

# Typed refusal codes.
ENVELOPE_REQUIRED = "BOUNDED_ENVELOPE_REQUIRED"
FLAG_CONFLICT = "ADVISORY_FLAG_CONFLICT"
TASK_NOT_FOUND = "ADVISORY_TASK_NOT_FOUND"
TASK_NOT_DONE = "ADVISORY_TASK_NOT_DONE"
TASK_WRONG_MODEL = "ADVISORY_TASK_WRONG_MODEL"
TASK_WRONG_ROLE = "ADVISORY_TASK_WRONG_ROLE"
RESULT_UNREADABLE = "ADVISORY_RESULT_UNREADABLE"
ENVELOPE_MISSING = "ADVISORY_ENVELOPE_MISSING"
ENVELOPE_INCOMPLETE = "ADVISORY_ENVELOPE_INCOMPLETE"
OWNED_PATHS_INVALID = "ADVISORY_OWNED_PATHS_INVALID"
BINDING_MISMATCH = "ADVISORY_BINDING_MISMATCH"
OWNED_PATHS_MISMATCH = "ADVISORY_OWNED_PATHS_MISMATCH"
ENVELOPE_CHANGED = "ADVISORY_ENVELOPE_CHANGED"
ADVISOR_ROUTE_REFUSED = "ADVISORY_ROLE_REFUSED"
CEILING_EXCEEDED = "advisory_ceiling_exceeded"
CEILING_UNMEASURED = "advisory_ceiling_unmeasured"


class AdvisoryRefused(Exception):
    """A bounded dispatch or an advisor dispatch is refused; ``code`` names why."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ValidatedEnvelope:
    """An envelope read from a finished advisor task, with the digests that bind it."""

    advisor_task_id: str
    advisor_model: str
    advisor_run_nonce: str | None
    result_path: str
    result_sha256: str
    envelope: dict[str, Any]
    envelope_sha256: str
    binding_sha256: str

    @property
    def owned_paths(self) -> list[str]:
        return list(self.envelope["owned_paths"])

    def state_record(self, requirement: str) -> dict[str, Any]:
        """What the worker's task record keeps: the envelope's source, digests, scope and ceilings."""
        return {
            "requirement": requirement,
            "advisor_task_id": self.advisor_task_id,
            "advisor_model": self.advisor_model,
            "advisor_run_nonce": self.advisor_run_nonce,
            "result_path": self.result_path,
            "result_sha256": self.result_sha256,
            "envelope_sha256": self.envelope_sha256,
            "dispatch_args_sha256": self.binding_sha256,
            "owned_paths": self.owned_paths,
            "max_changed_files": self.envelope["max_changed_files"],
            "max_non_test_loc": self.envelope["max_non_test_loc"],
        }


def _normalized(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def bounded_requirement(
    model_id: str | None,
    *,
    mode: str,
    task_family: str | None,
    review_profile: str | None,
    owned_paths: Iterable[str] = (),
    policy: BoundedExecutionPolicy | None = None,
) -> str | None:
    """Why this launch needs an advisory envelope, or None when it does not.

    ``model_id`` is the canonical catalog id of the model the admitted route
    launches, after aliases, ``--force-agent`` and any substitution. Every
    bounded-worker dispatch needs one. A Gemini Flash dispatch is the bounded
    fallback unless it is explicitly classified non-bounded — a Ukrainian
    authoring or review task family, or ``--review-profile ukrainian`` for a
    read-only review — and nothing contradicts that; missing or conflicting
    classification counts as bounded (fail closed).
    """
    policy = policy or bounded_execution_policy()
    if model_id is None:
        return None
    if model_id == policy.bounded_worker_model_id:
        return f"{model_id} is the bounded worker"
    if model_id != policy.bounded_fallback_model_id:
        return None
    family = _normalized(task_family)
    ukrainian_family = family in policy.non_bounded_task_families
    conflicts: list[str] = []
    if ukrainian_family and review_profile == "code":
        conflicts.append(f"task family {family!r} with --review-profile code")
    if review_profile == "ukrainian" and family is not None and not ukrainian_family:
        conflicts.append(f"--review-profile ukrainian with non-Ukrainian task family {family!r}")
    if ukrainian_family:
        code_paths = sorted(path for path in owned_paths if str(path).removeprefix("./").startswith(_CODE_ROOTS))
        if code_paths:
            conflicts.append(f"task family {family!r} owning code paths {code_paths}")
    if conflicts:
        return f"{model_id} with an ambiguous classification ({'; '.join(conflicts)}) is the bounded fallback"
    if ukrainian_family:
        return None
    if review_profile == "ukrainian" and mode == "read-only":
        return None
    if review_profile == "ukrainian":
        return (
            f"{model_id} in {mode} mode with --review-profile ukrainian but no Ukrainian authoring/review "
            "task family is the bounded fallback"
        )
    return (
        f"{model_id} without a Ukrainian authoring/review classification "
        f"(--research-task-family one of {sorted(policy.non_bounded_task_families)}, or read-only "
        "--review-profile ukrainian) is the bounded fallback"
    )


def validate_owned_path(path: Any, repo_root: Path) -> str:
    """Return ``path`` when it is a repo-relative path that exists or is creatable under an allowed root."""
    if not isinstance(path, str) or not path or path != path.strip():
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} must be a non-blank string")
    if any(unicodedata.category(char).startswith(("C", "Z")) and char != " " for char in path) or "\\" in path:
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} holds control, format or separator characters")
    pure = PurePosixPath(path)
    if pure.is_absolute() or path.startswith("~"):
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} must be repo-relative")
    segments = path.rstrip("/").split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} has an empty, '.' or '..' segment")
    if segments[0] in _FORBIDDEN_ROOTS:
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} is under a forbidden root {segments[0]!r}")
    static: list[str] = []
    for segment in segments:
        if _GLOB_CHARS & set(segment):
            break
        static.append(segment)
    if not static:
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} does not name a root directory")
    root = repo_root.resolve()
    top = repo_root / static[0]
    if not top.exists() and not top.is_symlink():
        raise AdvisoryRefused(
            OWNED_PATHS_INVALID, f"owned path {path!r} is not under an existing repository root ({static[0]!r})"
        )
    current = repo_root
    for index, segment in enumerate(static):
        current = current / segment
        if not current.exists() and not current.is_symlink():
            break
        try:
            current.resolve().relative_to(root)
        except ValueError:
            raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} leaves the repository") from None
        if current.is_file() and index < len(static) - 1:
            raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} descends into file {segment!r}")
    return path


def _require_text(envelope: Mapping[str, Any], field: str) -> None:
    value = envelope.get(field)
    if not isinstance(value, str) or not value.strip():
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"{field} must be a non-empty string")


def _require_text_list(envelope: Mapping[str, Any], field: str) -> None:
    value = envelope.get(field)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"{field} must be a non-empty list of non-empty strings")


def _require_positive_int(envelope: Mapping[str, Any], field: str) -> None:
    value = envelope.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"{field} must be a positive integer, got {value!r}")


def parse_envelope(
    result_text: str,
    *,
    repo_root: Path,
    policy: BoundedExecutionPolicy | None = None,
) -> dict[str, Any]:
    """The one ``advisory-envelope`` JSON object in ``result_text``, validated field by field."""
    policy = policy or bounded_execution_policy()
    blocks = _FENCE_RE.findall(result_text)
    if not blocks:
        raise AdvisoryRefused(ENVELOPE_MISSING, f"the advisor result holds no ```{ENVELOPE_FENCE} block")
    if len(blocks) > 1:
        raise AdvisoryRefused(ENVELOPE_MISSING, f"the advisor result holds {len(blocks)} ```{ENVELOPE_FENCE} blocks")
    try:
        envelope = json.loads(blocks[0])
    except ValueError as exc:
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"the envelope is not JSON: {exc}") from None
    if not isinstance(envelope, dict):
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, "the envelope must be a JSON object")
    expected = {*policy.advisor_output_fields, BINDING_FIELD}
    missing = sorted(expected - set(envelope))
    extra = sorted(set(envelope) - expected)
    if missing or extra:
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"envelope fields missing {missing}, unexpected {extra}")
    for field in policy.advisor_output_fields:
        if field in {"max_changed_files", "max_non_test_loc"}:
            _require_positive_int(envelope, field)
        elif field == "task_contract":
            _require_text(envelope, field)
        else:
            _require_text_list(envelope, field)
    binding = envelope[BINDING_FIELD]
    if not isinstance(binding, str) or not _SHA256_RE.fullmatch(binding):
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"{BINDING_FIELD} must be a lowercase sha256 hex digest")
    owned = [validate_owned_path(path, repo_root) for path in envelope["owned_paths"]]
    if len(set(owned)) != len(owned):
        raise AdvisoryRefused(OWNED_PATHS_INVALID, "owned_paths repeats a path")
    return envelope


def _read_record(state_path: Path, advisor_task_id: str) -> dict[str, Any]:
    try:
        record = json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AdvisoryRefused(TASK_NOT_FOUND, f"no task record for advisory task {advisor_task_id!r}") from None
    except (OSError, ValueError) as exc:
        raise AdvisoryRefused(
            TASK_NOT_FOUND, f"advisory task {advisor_task_id!r} record is unreadable: {exc}"
        ) from None
    if not isinstance(record, dict) or record.get("task_id") != advisor_task_id:
        raise AdvisoryRefused(TASK_NOT_FOUND, f"advisory task {advisor_task_id!r} record does not name that task")
    return record


def load_envelope(
    advisor_task_id: str,
    *,
    state_path: Path,
    binding_sha256: str,
    repo_root: Path,
    policy: BoundedExecutionPolicy | None = None,
) -> ValidatedEnvelope:
    """Validate the advisor task's canonical record and result, and the envelope's binding to this dispatch."""
    policy = policy or bounded_execution_policy()
    record = _read_record(state_path, advisor_task_id)
    status = record.get("status")
    if status != "done":
        raise AdvisoryRefused(TASK_NOT_DONE, f"advisory task {advisor_task_id!r} is {status!r}, not 'done'")
    if record.get("advisory_role") != policy.advisor_role or record.get("advisory_route") != ADVISOR_ROUTE:
        raise AdvisoryRefused(
            TASK_WRONG_ROLE,
            f"advisory task {advisor_task_id!r} did not run as {policy.advisor_role!r} on {ADVISOR_ROUTE}",
        )
    if record.get("mode") != "read-only":
        raise AdvisoryRefused(TASK_WRONG_ROLE, f"advisory task {advisor_task_id!r} did not run read-only")
    recorded_model = record.get("model")
    if canonical_model_id(recorded_model) != policy.advisor_model_id or record.get("resolved_model_known") is False:
        raise AdvisoryRefused(
            TASK_WRONG_MODEL,
            f"advisory task {advisor_task_id!r} ran on {recorded_model!r}, not the advisor {policy.advisor_model_id}",
        )
    if record.get("advisory_binding_sha256") != binding_sha256:
        raise AdvisoryRefused(
            BINDING_MISMATCH,
            f"advisory task {advisor_task_id!r} was issued for dispatch arguments "
            f"{record.get('advisory_binding_sha256')!r}, not {binding_sha256}",
        )
    result_path = state_path.with_suffix(".result")
    recorded_result = record.get("result_file")
    if not isinstance(recorded_result, str) or Path(recorded_result).resolve() != result_path.resolve():
        raise AdvisoryRefused(
            RESULT_UNREADABLE,
            f"advisory task {advisor_task_id!r} result_file {recorded_result!r} is not its canonical result",
        )
    try:
        result_bytes = result_path.read_bytes()
        result_text = result_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise AdvisoryRefused(RESULT_UNREADABLE, f"advisory task {advisor_task_id!r} result: {exc}") from None
    envelope = parse_envelope(result_text, repo_root=repo_root, policy=policy)
    if envelope[BINDING_FIELD] != binding_sha256:
        raise AdvisoryRefused(
            BINDING_MISMATCH,
            f"the envelope is bound to dispatch arguments {envelope[BINDING_FIELD]}, not {binding_sha256}",
        )
    canonical = json.dumps(envelope, sort_keys=True, separators=(",", ":"))
    return ValidatedEnvelope(
        advisor_task_id=advisor_task_id,
        advisor_model=str(recorded_model),
        advisor_run_nonce=record.get("run_nonce"),
        result_path=str(result_path),
        result_sha256=hashlib.sha256(result_bytes).hexdigest(),
        envelope=envelope,
        envelope_sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        binding_sha256=binding_sha256,
    )


def require_unchanged(validated: ValidatedEnvelope, current: ValidatedEnvelope) -> None:
    """Refuse when the advisor record or result changed between validation and spawn."""
    if (current.result_sha256, current.envelope_sha256, current.advisor_run_nonce) != (
        validated.result_sha256,
        validated.envelope_sha256,
        validated.advisor_run_nonce,
    ):
        raise AdvisoryRefused(
            ENVELOPE_CHANGED,
            f"advisory task {validated.advisor_task_id!r} result changed after validation "
            f"(sha256 {validated.result_sha256} → {current.result_sha256})",
        )


def require_owned_paths_match(envelope_paths: Sequence[str], dispatch_paths: Sequence[str] | None) -> None:
    """The envelope's owned paths are the dispatch's ``--owned-path`` set, exactly."""
    declared = sorted({str(path).strip() for path in dispatch_paths or []})
    if declared != sorted(set(envelope_paths)):
        raise AdvisoryRefused(
            OWNED_PATHS_MISMATCH,
            f"--owned-path {declared} must equal the envelope owned_paths {sorted(set(envelope_paths))}",
        )


def worker_prompt_block(validated: ValidatedEnvelope) -> str:
    """The envelope as the bounded worker reads it, ceilings included."""
    envelope = validated.envelope

    def bullets(field: str) -> str:
        return "\n".join(f"- {item}" for item in envelope[field])

    return (
        "\n\n## Advisory envelope (bounded worker)\n\n"
        f"Issued by advisory task `{validated.advisor_task_id}` on {validated.advisor_model} "
        f"(result sha256 `{validated.result_sha256}`). Work only within it.\n\n"
        f"Task contract: {envelope['task_contract']}\n\n"
        f"Owned paths:\n{bullets('owned_paths')}\n\n"
        f"Scope ceilings, checked when the task finalizes (exceeding either fails the task): "
        f"at most {envelope['max_changed_files']} changed files and at most "
        f"{envelope['max_non_test_loc']} changed non-test lines (added plus deleted).\n\n"
        f"Constraints:\n{bullets('constraints')}\n\n"
        f"Risk boundaries:\n{bullets('risk_boundaries')}\n\n"
        f"Acceptance evidence:\n{bullets('acceptance_evidence')}\n\n"
        f"Escalation triggers — stop and report instead of continuing when:\n{bullets('escalation_triggers')}\n"
    )


def advisor_prompt_block(binding_sha256: str, policy: BoundedExecutionPolicy | None = None) -> str:
    """How the advisor must write its envelope so the bounded dispatch can admit it."""
    policy = policy or bounded_execution_policy()
    fields = ", ".join(f"`{field}`" for field in policy.advisor_output_fields)
    return (
        "\n\n## Advisory envelope output contract\n\n"
        f"You are the {policy.advisor_role} advisor for one bounded-worker dispatch. End your reply with "
        f"exactly one fenced block whose info string is `{ENVELOPE_FENCE}`, holding one JSON object with "
        f"exactly these keys: {fields}, and `{BINDING_FIELD}`.\n"
        "- `task_contract`: non-empty string.\n"
        "- `owned_paths`: non-empty list of repo-relative paths (dir/, dir/**, file or glob) under existing "
        "top-level roots; it must equal the worker dispatch's --owned-path set.\n"
        "- `max_changed_files`, `max_non_test_loc`: positive integers; the worker fails if it exceeds them.\n"
        "- `constraints`, `risk_boundaries`, `acceptance_evidence`, `escalation_triggers`: non-empty lists of "
        "non-empty strings.\n"
        f"- `{BINDING_FIELD}`: exactly `{binding_sha256}`.\n"
    )


def parse_numstat_z(text: str) -> list[tuple[int | None, int | None, str]]:
    """``git diff --numstat -z --no-renames`` entries: (added, deleted, path); binary counts are None."""
    entries: list[tuple[int | None, int | None, str]] = []
    for record in text.split("\0"):
        if not record:
            continue
        parts = record.split("\t", 2)
        if len(parts) != 3:
            raise ValueError(f"unexpected numstat record {record!r}")
        added, deleted, path = parts
        entries.append((None if added == "-" else int(added), None if deleted == "-" else int(deleted), path))
    return entries


def is_test_path(path: str) -> bool:
    """A test file: under a ``tests`` directory, or named ``test_*``, ``*_test.*`` or ``conftest.py``."""
    parts = PurePosixPath(path).parts
    name = parts[-1] if parts else ""
    return "tests" in parts[:-1] or name.startswith("test_") or "_test." in name or name == "conftest.py"


def ceiling_verdict(
    entries: Sequence[tuple[int | None, int | None, str]],
    *,
    max_changed_files: int,
    max_non_test_loc: int,
) -> dict[str, Any]:
    """Compare a worker's changes with the envelope ceilings; ``exceeded`` lists each breach."""
    changed_files = len({path for _added, _deleted, path in entries})
    non_test_loc = sum((added or 0) + (deleted or 0) for added, deleted, path in entries if not is_test_path(path))
    exceeded: list[str] = []
    if changed_files > max_changed_files:
        exceeded.append(f"changed_files {changed_files} > max_changed_files {max_changed_files}")
    if non_test_loc > max_non_test_loc:
        exceeded.append(f"non_test_loc {non_test_loc} > max_non_test_loc {max_non_test_loc}")
    return {
        "measured": True,
        "changed_files": changed_files,
        "non_test_loc": non_test_loc,
        "max_changed_files": max_changed_files,
        "max_non_test_loc": max_non_test_loc,
        "exceeded": exceeded,
    }
