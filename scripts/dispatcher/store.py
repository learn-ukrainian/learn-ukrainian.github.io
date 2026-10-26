"""Atomic task records and read-only access to legacy hot/archive records."""

import hashlib
import json
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from scripts.common.git_context import validate_plain_branch_name
from scripts.common.task_store_paths import tasks_dir
from scripts.dispatcher.types import ReviewAttempt

try:
    from scripts.orchestration.task_record_store import iter_task_records, locate_task_record, relocated_result_file
except ImportError:
    iter_task_records = locate_task_record = relocated_result_file = None

ACTIVE = {"spawning", "running"}


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


def check_review_attempt(binding: ReviewAttempt, *, claim=False) -> None:
    """Any legacy receipt artifact or hot/archived binding spends the review/attempt pair."""
    for record in list_tasks(include_archive=True, strict=True):
        bound = record.get("review_attempt")
        if isinstance(bound, dict) and all(bound.get(key) == binding[key] for key in ("review_id", "attempt_id")):
            raise ValueError("review attempt already spent")
    root = tasks_dir().parent / "review-receipts" / binding["review_id"]
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


def new_record(spec, repository: dict, branch: str, sha: str, metadata: dict, *, binding: ReviewAttempt | None = None) -> dict:
    record = dict(pid=None, process_start=None, finished_at=None, duration_s=None, returncode=None)
    record.update(result_sha256=None, usage=None, head_sha=None, remote_head_sha=None, commits_ahead=None)
    record.update(worktree_dirty_on_exit=None, error=None)
    fields = ("task_id", "agent", "provider", "model", "effort", "mode", "claude_account")
    record.update({name: getattr(spec, name) for name in fields})
    metadata_fields = ("research_role", "research_task_family", "research_track", "initiator")
    record.update({name: metadata.get(name) for name in metadata_fields})
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
        worktree_branch=branch, worktree_path=str(spec.worktree), cwd=str(spec.worktree), worktree_base_sha=sha
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
    return record


def record_path(task_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", task_id) or ".." in task_id:
        raise ValueError("task id must contain only letters, digits, underscores, hyphens and dots")
    return tasks_dir() / f"{task_id}.json"


def _write(path: Path, record: dict, exclusive: bool = False) -> None:
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
    if read(record["task_id"], missing_ok=True) is not None:
        raise ValueError("task id already exists; choose a new task id")
    _write(path, record, exclusive=True)
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
    record = json.loads(path.read_text())
    if nonce is not None and record.get("run_nonce") != nonce:
        raise ValueError("run nonce mismatch")
    if relocated_result_file:
        record["result_file"] = relocated_result_file(path, record.get("result_file"))
    return record


def replace(record: dict, path: Path | None = None) -> None:
    _write(path or record_path(record["task_id"]), record)


def list_tasks(status: str | None = None, include_archive=False, *, strict=False) -> list[dict]:
    root = tasks_dir()
    paths = (
        iter_task_records(root, include_archive=include_archive)
        if iter_task_records
        else (
            path
            for folder in ([root, root / "archive"] if include_archive else [root])
            for path in folder.glob("*.json")
        )
    )
    records = []
    for path in paths:
        try:
            record = json.loads(path.read_text())
            if not isinstance(record, dict):
                raise ValueError("invalid task record")
            if status is None or record.get("status") == status:
                if relocated_result_file:
                    record["result_file"] = relocated_result_file(path, record.get("result_file"))
                records.append(record)
        except (OSError, ValueError):
            if strict:
                raise ValueError("unreadable task record; review attempt reuse cannot be excluded") from None
            continue
    return records
