"""Atomic task records and read-only access to legacy hot/archive records."""

import hashlib
import json
import os
import re
import subprocess
import unicodedata
import uuid
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath

from scripts.common.git_context import validate_plain_branch_name
from scripts.common.task_store_paths import tasks_dir
from scripts.dispatcher.types import ReviewAttempt
from scripts.orchestration.task_record_store import (
    iter_task_records,
    locate_task_record,
    read_task_record,
    relocated_result_file,
    task_state_lock,
)

ACTIVE = {"spawning", "running"}


class TaskRecordError(ValueError):
    """The supervisor cannot trust its durable record for settlement."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def now() -> str:
    return datetime.now(UTC).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def review_binding(metadata: dict) -> ReviewAttempt | None:
    """Validate the binding without provisioning receipts or spending an attempt."""
    names = ("review_id", "attempt_id", "review_attempt")
    if not any(metadata.get(name) is not None for name in (*names, "review_access")):
        return None
    if metadata.get("mode") != "read-only" or metadata.get("cwd"):
        # Runtime no-reuse enforcement remains gated on the isolation port.
        raise ValueError("review attempt requires --mode read-only and a fresh worktree (no --cwd)")
    if not all(metadata.get(name) for name in names):
        raise ValueError("--review-id, --attempt-id and --review-attempt must be used together")
    if metadata.get("review_access") not in (None, "isolated", "full"):
        raise ValueError("invalid review access")
    for name in names[:2]:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", metadata[name]):
            raise ValueError("invalid review or attempt id")
    manifest = Path(metadata["review_attempt"])
    if not manifest.is_file():
        raise ValueError("--review-attempt must name a manifest file")
    sha = digest(manifest.read_bytes())
    return ReviewAttempt(review_id=metadata["review_id"], attempt_id=metadata["attempt_id"], manifest_sha256=sha)


def receipts_root() -> Path:
    """Where attempt ledgers live: beside the task store (``review-receipts/<review_id>/<attempt_id>.jsonl``)."""
    return tasks_dir().parent / "review-receipts"


def check_review_attempt(binding: ReviewAttempt, *, claim=False, owner: str | None = None) -> None:
    """Any legacy receipt artifact or hot/archived binding spends the review/attempt pair.

    ``owner`` is the task claiming the pair from its own supervisor: its own record does not spend it.
    """
    for record in list_tasks(include_archive=True, strict=True):
        bound = record.get("review_attempt")
        if (isinstance(bound, dict) and record.get("task_id") != owner
                and all(bound.get(key) == binding[key] for key in ("review_id", "attempt_id"))):
            raise ValueError("review attempt already spent")
    root = receipts_root() / binding["review_id"]
    # Legacy prepare_review_attempt checks all five, including dangling symlinks,
    # before creating anything; failed/partial preparation still spends the pair.
    for suffix in (".jsonl", ".jsonl.sha256", ".mcp.json", ".codex-home", ".agy-home"):
        path = root / (binding["attempt_id"] + suffix)
        if path.exists() or path.is_symlink():
            raise ValueError("review attempt already spent")
    if claim:
        from scripts.agent_runtime.review_mcp import _create_file, _open_attempt_dir

        fd = _open_attempt_dir(root, create=True)
        try:
            # Same O_EXCL ledger as legacy: keep it even if later launch steps fail.
            _create_file(binding["attempt_id"] + ".jsonl", fd, b"")
        except FileExistsError:
            raise ValueError("review attempt already spent") from None
        finally:
            os.close(fd)


def new_record(
    spec, repository: dict, branch: str, sha: str, metadata: dict, *,
    binding: ReviewAttempt | None = None, admission_hold: dict | None = None,
) -> dict:
    record = dict(pid=None, process_start=None, finished_at=None, duration_s=None, returncode=None)
    record.update(result_sha256=None, usage=None, head_sha=None, remote_head_sha=None, commits_ahead=None)
    record.update(worktree_dirty_on_exit=None, error=None)
    record["owned_paths"] = list(metadata.get("owned_path") or [])
    record["worktree_base_ref"] = metadata.get("base") or "origin/main"
    from scripts.dispatcher.git import canonical_origins, verification_origin
    if spec.mode != "workspace-write":
        record["worktree_remote_url"] = None
    else:
        try:
            origin = verification_origin(spec.worktree)
            record["worktree_remote_url"] = origin if origin in canonical_origins(repository) else None
        except (OSError, ValueError, subprocess.SubprocessError):
            record["worktree_remote_url"] = None
    fields = ("task_id", "agent", "provider", "model", "effort", "mode", "claude_account", "codex_account")
    record.update({name: getattr(spec, name) for name in fields})
    from scripts.dispatcher.watchdog import deadlines

    record.update(zip(("hard_timeout", "silence_timeout", "initial_response_timeout"), deadlines(spec.options), strict=True))
    record["options"] = spec.options
    metadata_fields = ("research_role", "research_task_family", "research_track", "initiator")
    record.update({name: metadata.get(name) for name in metadata_fields})
    for name in ("trial_role", "trial_qualified_task"):
        if metadata.get(name) is not None:
            record[name] = metadata[name]
    for name in ("output_schema_path", "output_schema_sha256", "review_write_root"):
        if name in spec.options:
            record[name] = spec.options[name]
    for source, target in (
        ("risk", "review_risk"), ("review_profile", "review_profile"),
        ("review_author_model", "review_author_model"), ("review_mode", "review_mode"),
        ("language_lane", "language_lane"), ("pr", "pr"),
        ("subject_seat", "review_subject_seats"), ("subject_family", "review_subject_families"),
        ("require_review_verdict", "require_review_verdict"),
    ):
        if metadata.get(source) is not None and metadata[source] != []:
            record[target] = metadata[source]
    record.update(schema_version=2, run_nonce=uuid.uuid4().hex, status="spawning", started_at=now())
    record.update(repo=repository["key"], repository_id=repository["github"], repository=repository["github"])
    record.update(
        worktree_branch=branch, worktree_path=str(spec.worktree), cwd=str(spec.worktree),
        worktree_base_sha=sha, worktree_start_sha=sha
    )
    if spec.mode == "read-only" and metadata.get("branch") is not None:
        record["review_branch"] = validate_plain_branch_name(metadata["branch"], repo_root=spec.worktree)
        record["pinned_head"] = metadata.get("pinned_head") or sha
    elif spec.mode == "workspace-write" and metadata.get("branch") is not None:
        record["publish_branch"] = validate_plain_branch_name(metadata["branch"], repo_root=spec.worktree)
    record.update(prompt_file=str(spec.prompt_file), prompt_sha256=digest(spec.prompt_file.read_bytes()))
    if binding:
        record.update(review_attempt=binding, review_access=metadata.get("review_access") or "isolated")
    record.update(
        result_file=str(spec.final_file), push_state="unknown", research_owned_paths=metadata["research_owned_path"]
    )
    if admission_hold is not None:
        for name in ("run_nonce", "started_at", "admission", "admission_hold"):
            record[name] = admission_hold[name]
    return record


def record_path(task_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", task_id) or ".." in task_id:
        raise ValueError("task id must contain only letters, digits, underscores, hyphens and dots")
    return tasks_dir() / f"{task_id}.json"


def retention_hold_error(record: dict) -> str | None:
    """Describe a malformed hold without treating false-like values as booleans."""
    if "worktree_retention_hold" in record:
        value = record["worktree_retention_hold"]
        if not isinstance(value, bool):
            return f"worktree_retention_hold must be a boolean; got {value!r}"
    return None


def _write(path: Path, record: dict, exclusive: bool = False, *, grant: dict | None = None,
           require_existing: bool = False) -> None:
    # Reentrant: settlement, create and grant_paths already hold this same inode lock.
    with task_state_lock(path):
        if require_existing and not path.exists():
            raise TaskRecordError("TASK_RECORD_DAMAGED")
        if not exclusive and path.exists():
            try:
                current = json.loads(path.read_text())
                if not isinstance(current, dict):
                    raise ValueError("not an object")
            except (OSError, ValueError, RecursionError) as exc:
                raise TaskRecordError("TASK_RECORD_DAMAGED") from exc
            if current.get("run_nonce") != record.get("run_nonce"):
                raise TaskRecordError("TASK_RECORD_REPLACED: run nonce mismatch")
            if "owned_path_grants" in current:
                record["owned_path_grants"] = current["owned_path_grants"]
            if current.get("settling_at"):
                record["settling_at"] = current["settling_at"]
            # A hold or malformed hold outranks a stale supervisor copy. False is an
            # intentional clear; absence cannot discard a durable retention refusal.
            hold_error = retention_hold_error(current)
            if record.get("worktree_retention_hold") is False:
                record.pop("worktree_retention_hold", None)
            elif current.get("worktree_retention_hold") is True or hold_error:
                record["worktree_retention_hold"] = current["worktree_retention_hold"]
                record["worktree_disposition"] = "retained"
                record["worktree_disposition_reason"] = "retention_hold_invalid" if hold_error else "retention_hold"
                if hold_error:
                    record["worktree_disposition_detail"] = hold_error
                else:
                    record.pop("worktree_disposition_detail", None)
        if grant is not None:
            record["owned_path_grants"] = [*record.get("owned_path_grants", []), grant]
        _write_atomic(path, record, exclusive)


def _write_atomic(path: Path, record: dict, exclusive: bool) -> None:
    # A PID transfers the slot to the supervisor. Every terminal path releases it.
    if record.get("pid") is not None or record.get("status") not in ACTIVE:
        record.pop("admission_hold", None)
    # Stage beside the record so the atomic replacement stays on one filesystem.
    name = path.with_name(f".{path.stem}.{uuid.uuid4().hex}.tmp")
    try:
        with open(name, "x", opener=lambda p, f: os.open(p, f, 0o600)) as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            os.link(name, path)
        else:
            os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def create(record: dict, prompt: bytes) -> Path:
    path = record_path(record["task_id"])
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with task_state_lock(path):
        existing = read(record["task_id"], missing_ok=True)
        if existing is not None:
            from scripts.orchestration.dispatch_admission import is_admission_hold_record

            if not (existing.get("schema_version") == 2 and existing.get("status") == "spawning"
                    and existing.get("run_nonce") == record.get("run_nonce")
                    and is_admission_hold_record(existing) and existing.get("admission_hold") == record.get("admission_hold")):
                raise ValueError("task id already exists; choose a new task id")
        _write(path, record, exclusive=existing is None)
    with open(record["prompt_file"], "xb", opener=lambda p, f: os.open(p, f, 0o600)) as stream:
        stream.write(prompt)
    return path


def read(task_id: str, nonce: str | None = None, *, missing_ok=False) -> dict | None:
    path = record_path(task_id)
    if locate_task_record:
        path = locate_task_record(path.parent, task_id)
    elif not path.exists():
        path = path.parent / "archive" / path.name
    if path is None or not path.exists():
        if missing_ok:
            return None
        raise ValueError("task not found")
    try:
        record = json.loads(path.read_text())
        if not isinstance(record, dict):
            raise ValueError("not an object")
    except (OSError, ValueError, RecursionError) as exc:
        raise TaskRecordError("TASK_RECORD_DAMAGED") from exc
    if nonce is not None and record.get("run_nonce") != nonce:
        raise ValueError("run nonce mismatch")
    if relocated_result_file:
        record["result_file"] = relocated_result_file(path, record.get("result_file"))
    return record


def replace(record: dict, path: Path | None = None, *, require_existing: bool = False) -> None:
    _write(path or record_path(record["task_id"]), record, require_existing=require_existing)


def publish_failed_record(record: dict, path: Path) -> None:
    """Recover a damaged supervisor record as failure, never overwrite another run.

    A deleted record is published again as ``TASK_RECORD_DAMAGED``. Any other read error leaves the
    record unable to prove it is this run's, and a lock or write error leaves the failure unpublished:
    each is a typed ``TASK_RECORD_IO_ERROR``. A worktree already reaped keeps its ``removed`` disposition.
    """
    try:
        with task_state_lock(path):
            try:
                current = json.loads(path.read_text())
            except (FileNotFoundError, ValueError, RecursionError):
                current = None
            if (isinstance(current, dict) and isinstance(current.get("run_nonce"), str)
                    and current["run_nonce"] != record["run_nonce"]):
                raise TaskRecordError("TASK_RECORD_REPLACED: run nonce mismatch")
            record.update(status="cancelled" if record.get("status") == "cancelled" else "crashed",
                          error="TASK_RECORD_DAMAGED", finished_at=now())
            if record.get("worktree_disposition") != "removed":
                record.update(worktree_disposition="retained", worktree_disposition_reason="task_record_damaged")
            _write_atomic(path, record, exclusive=False)
    except OSError as exc:
        raise TaskRecordError(f"TASK_RECORD_IO_ERROR: {type(exc).__name__}") from exc


def _grant_paths_validated(root: Path, paths: list[str]) -> list[str]:
    """Literal relative paths inside the existing worktree; no sparse checkout changes."""
    from scripts.dispatcher import ownership, scope

    def validate(raw: str) -> str:
        if (not isinstance(raw, str) or not raw or raw != raw.strip() or "\\" in raw
                or PureWindowsPath(raw).drive or raw.startswith("/") or any(c in raw for c in "*?:")
                or any(unicodedata.category(c) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for c in raw)
                or any(part in {"", ".", ".."} for part in raw.rstrip("/").split("/"))):
            raise ValueError("grant paths must be literal repository-relative paths without traversal or wildcards")
        path = raw.rstrip("/")
        try:
            resolved = (root / path).resolve()
        except (OSError, RuntimeError) as exc:
            raise ValueError("grant path cannot be resolved inside the worktree") from exc
        if not path or not resolved.is_relative_to(root):
            raise ValueError("grant path escapes the worktree or names its root")
        return path

    paths = sorted(set(validate(path) for path in paths))
    expanded, _ = scope.with_generated_outputs(paths)
    paths = list(dict.fromkeys(validate(path) for path in expanded))
    run = ownership._local_git(root)
    sparse = subprocess.run(["git", "-C", str(root), "config", "--bool", "core.sparseCheckout"],
                            capture_output=True, text=True, check=False, timeout=30)
    if sparse.returncode not in {0, 1}:
        raise OSError("cannot inspect sparse checkout")
    if sparse.stdout.strip() == "true":
        accepted = subprocess.run(["git", "-C", str(root), "sparse-checkout", "check-rules", "-z"],
                                  input="\0".join(paths) + "\0", capture_output=True, text=True,
                                  check=True, timeout=30).stdout.split("\0")
        excluded = set(paths) - set(accepted)
        # A directory above an excluded tree would otherwise quietly grant that tree too.
        excluded.update(path[2:] for path in run("ls-files", "-t", "-z", strip=False).split("\0")
                        if path.startswith("S ") and not ownership.outside_owned([path[2:]], paths))
        if excluded:
            raise ValueError("grant path is sparse-excluded: " + ", ".join(sorted(excluded)[:10]))
    return paths


def _grant_worktree(record: dict) -> Path:
    if record.get("schema_version") != 2 or record.get("status") != "running" or record.get("settling_at"):
        raise ValueError("grants require a running v2 task that is not settling")
    sealed = ("review_attempt", "advisory_envelope", "advisory_binding_sha256", "advisory_binding",
              "advisory_role", "advisory_task", "driver_brief", "bounded", "bounded_implementation")
    options = record.get("options") or {}
    if (record.get("mode") != "workspace-write"
            or any(record.get(key) is not None for key in sealed)
            or any(options.get(key) not in (None, "None", False, "False", "") for key in sealed)
            or record.get("research_task_family") in {"bounded", "bounded_implementation"}):
        raise ValueError("grants are refused for sealed envelopes and read-only tasks")
    return Path(record["worktree_path"]).resolve(strict=True)


def grant_paths(task_id: str, run_nonce: str, paths: list[str], reason: str, approval_ref: str) -> dict:
    """Append attributable approval for an honest worker; caller identity is unauthenticated."""
    from scripts.dispatcher import ownership

    if not reason.strip() or not approval_ref.strip() or not paths:
        raise ValueError("paths, reason and approval-ref must be nonempty")
    caller = os.environ.get(ownership.TASK_ID_ENV)
    ancestor, seen = caller, set()
    while ancestor:
        if ancestor == task_id:
            raise ValueError("self or descendant task cannot grant its own scope")
        if ancestor in seen:
            raise ValueError("caller task ancestry contains a cycle")
        seen.add(ancestor)
        parent = read(ancestor)
        ancestor = parent.get("parent_task_id")
    path = record_path(task_id)
    snapshot = read(task_id, run_nonce)
    root = _grant_worktree(snapshot)
    normalized = _grant_paths_validated(root, paths)
    with task_state_lock(path):
        record = read(task_id, run_nonce)
        if _grant_worktree(record) != root:
            raise ValueError("task worktree changed during grant validation")
        ownership.effective_scope(record)
        request = dict(task_id=task_id, run_nonce=run_nonce, owned_paths=normalized,
                       reason=reason, approval_ref=approval_ref)
        grant = next((old for old in record.get("owned_path_grants", [])
                      if all(old.get(key) == value for key, value in request.items())), None)
        if grant is None:
            grant = dict(request, schema_version=1, grant_id=uuid.uuid4().hex,
                         repository_id=record.get("repository_id"), granted_at=now(),
                         granted_by=caller or os.environ.get("SESSION_HANDOFF_AGENT") or "unknown-seat",
                         granted_by_authenticated=False)
            _write(path, record, grant=grant)
        return dict(task_id=task_id, run_nonce=run_nonce, grant_id=grant["grant_id"],
                    owned_paths=normalized, effective_scope=ownership.effective_scope(record), grant=grant)


def begin_settlement(record: dict) -> None:
    """Close grants and refresh them before delivery evidence is collected."""
    path = record_path(record["task_id"])
    with task_state_lock(path):
        try:
            current = read(record["task_id"], record["run_nonce"])
            if not isinstance(current, dict):
                raise ValueError("not an object")
        except (OSError, ValueError, RecursionError) as exc:
            raise TaskRecordError("TASK_RECORD_DAMAGED") from exc
        current["settling_at"] = current.get("settling_at") or now()
        replace(current, path)
        record["settling_at"] = current["settling_at"]
        record["owned_path_grants"] = current.get("owned_path_grants", [])


def list_tasks(status: str | None = None, include_archive=False, *, strict=False) -> list[dict]:
    root = tasks_dir()
    paths = iter_task_records(root, include_archive=include_archive)
    records = []
    for path in paths:
        try:
            record = read_task_record(path)
            if record is None or "task_id" not in record:
                continue
            if status is None or record.get("status") == status:
                if relocated_result_file:
                    record["result_file"] = relocated_result_file(path, record.get("result_file"))
                records.append(record)
        except (OSError, ValueError):
            if strict:
                raise ValueError(f"unreadable task record {path}; review attempt reuse cannot be excluded") from None
            continue
    return records
