"""Versioned branch ownership, shared by dispatch, repair, keeper and reaper.

Records survive task archival. A branch lock covers read/modify/atomic replace;
the directory fsync makes the rename durable before a worker can start.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

from scripts.common.task_store_paths import tasks_dir


class BindingError(ValueError):
    """Ownership or repair state is unavailable or corrupt; never overwrite it."""


def lifecycle_root() -> Path:
    return tasks_dir().parent / "author-lifecycle" / "v1"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


@contextmanager
def locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def read_json(path: Path) -> dict | None:
    if path.is_symlink():
        raise BindingError("record symlink refused")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError, UnicodeError) as exc:
        raise BindingError("record unreadable or corrupt") from exc
    if not isinstance(value, dict):
        raise BindingError("record must be an object")
    return value


def atomic_write(path: Path, value: dict) -> None:
    payload = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".author-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def validate_identity(repository: str, branch: str) -> None:
    from scripts.common.git_context import UnsafeBranchNameError, validate_plain_branch_name

    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise BindingError("invalid repository")
    try:
        validate_plain_branch_name(branch, repo_root=".")
    except (UnsafeBranchNameError, TypeError) as exc:
        raise BindingError("invalid branch") from exc
    if branch in {"main", "master", "HEAD"}:
        raise BindingError("protected branch")


class BindingStore:
    def __init__(self, root: Path | None = None):
        self.root = root if root is not None else lifecycle_root()

    def path(self, repository: str, branch: str) -> Path:
        validate_identity(repository, branch)
        return self.root / "bindings" / (digest([repository, branch]) + ".json")

    def load(self, repository: str, branch: str) -> dict | None:
        record = read_json(self.path(repository, branch))
        if record is None:
            return None
        authors = record.get("authors")
        if (
            type(record.get("schema_version")) is not int
            or record["schema_version"] != 1
            or not {
                "repository",
                "branch",
                "driver",
                "lane",
                "issue",
                "pr",
                "authors",
                "author_task_ids",
                "author_families",
                "round_count",
            }.issubset(record)
            or record.get("repository") != repository
            or record.get("branch") != branch
            or not isinstance(authors, list)
            or not authors
            or any(
                not isinstance(a, dict) or not all(isinstance(a.get(k), str) and a[k] for k in ("task_id", "family"))
                for a in authors
            )
            or record.get("author_task_ids") != [a["task_id"] for a in authors]
            or len(set(record["author_task_ids"])) != len(authors)
            or record.get("author_families") != list(dict.fromkeys(a["family"] for a in authors))
            or type(record.get("round_count")) is not int
            or record["round_count"] != len(authors) - 1
            or not isinstance(record.get("driver"), str)
            or not isinstance(record.get("lane"), str)
            or (record.get("issue") is not None and (type(record["issue"]) is not int or record["issue"] < 1))
            or (record.get("pr") is not None and (type(record["pr"]) is not int or record["pr"] < 1))
        ):
            raise BindingError("binding schema or identity corrupt")
        return record

    def append(
        self,
        *,
        repository: str,
        branch: str,
        task_id: str,
        family: str,
        driver: str,
        lane: str = "unknown",
        issue: int | None = None,
    ) -> dict:
        if not isinstance(task_id, str) or not task_id:
            raise BindingError("invalid author task id")
        if not all(isinstance(v, str) and v for v in (family, driver, lane)):
            raise BindingError("missing author identity")
        if issue is not None and (type(issue) is not int or issue < 1):
            raise BindingError("invalid issue")
        path = self.path(repository, branch)
        with locked(path.with_suffix(".lock")):
            record = self.load(repository, branch) or {
                "schema_version": 1,
                "repository": repository,
                "branch": branch,
                "driver": driver,
                "lane": lane,
                "issue": issue,
                "pr": None,
                "authors": [],
                "author_task_ids": [],
                "author_families": [],
                "round_count": 0,
            }
            if task_id in record["author_task_ids"]:
                author = next(a for a in record["authors"] if a["task_id"] == task_id)
                if author["family"] != family:
                    raise BindingError("author identity changed")
                return record
            record["authors"].append({"task_id": task_id, "family": family})
            record["author_task_ids"].append(task_id)
            record["author_families"] = list(dict.fromkeys(a["family"] for a in record["authors"]))
            record["round_count"] = len(record["authors"]) - 1
            atomic_write(path, record)
            return record

    def attach_pr(self, repository: str, branch: str, number: int) -> dict:
        if type(number) is not int or number < 1:
            raise BindingError("invalid PR number")
        path = self.path(repository, branch)
        with locked(path.with_suffix(".lock")):
            record = self.load(repository, branch)
            if record is None:
                raise BindingError("binding missing")
            if record["pr"] not in (None, number):
                raise BindingError("PR already attached")
            record["pr"] = number
            atomic_write(path, record)
            return record


def bind_dispatch(state: dict, *, root: Path | None = None, lane: str | None = None) -> None:
    """Observe admitted branch writers; never change routing or admission policy."""
    if (
        state.get("mode") not in {"danger", "workspace-write"}
        or state.get("review")
        or state.get("require_review_verdict")
        or not state.get("worktree_branch")
        or state.get("repository") is None
    ):
        return
    from scripts.review.record_cf_verdict import BranchFactsError, incoming_writer_family

    try:
        family = incoming_writer_family(state.get("agent"), state.get("model"))
    except BranchFactsError:
        family = "unknown"
    dor = state.get("dor_preflight") or {}
    issues = dor.get("issues") or []
    issue = issues[0] if len(issues) == 1 and type(issues[0]) is int else None
    if dor.get("issue_repositories"):
        # Never reinterpret a foreign card's number in the branch repository.
        issue = None
    BindingStore(root).append(
        repository=state.get("repository"),
        branch=state["worktree_branch"],
        task_id=state["task_id"],
        family=family,
        driver=state.get("initiator") or "unknown",
        lane=lane or "unknown",
        issue=issue,
    )
