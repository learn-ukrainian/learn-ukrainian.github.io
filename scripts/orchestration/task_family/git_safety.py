"""Safety primitives for fail-closed task-family cleanup."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.common.git_context import sanitized_git_env
from scripts.guardrails.worktree_containment import (
    PROTECTED_BRANCHES,
    resolve_main_root,
)


class GitSafetyError(RuntimeError):
    """Any safety failure that blocks cleanup progress."""


class GitCommandError(GitSafetyError):
    """git command failed with non-zero return code."""


class GitHubQueryError(GitSafetyError):
    """GitHub authoritative lookup failed or returned unknown data."""


class BundleError(GitSafetyError):
    """Bundle creation or verification failed."""


class LockAcquisitionError(GitSafetyError):
    """Required advisory lock is unavailable."""


STATE_FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*\.[A-Za-z0-9]{2,8}$")


@dataclass(frozen=True)
class WorktreeInfo:
    path: Path
    branch: str | None
    head: str | None = None
    locked: bool = False
    prunable: bool = False


@dataclass(frozen=True)
class BundleReceipt:
    path: Path
    sha256: str
    branch: str
    created_at: str


def run_git(args: list[str], cwd: Path, *, timeout: float = 30.0, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env if env is not None else sanitized_git_env(),
    )


def run_gh(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: float = 30.0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        cwd=str(cwd) if cwd is not None else None,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _require_success(proc: subprocess.CompletedProcess[str], *, context: str) -> None:
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise GitCommandError(f"{context}: {detail or f'exit {proc.returncode}'}")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        directory_fd = os.open(str(path.parent), os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise


def resolve_lock_root(repo_root: Path) -> Path:
    root = resolve_main_root(repo_root)
    return root / ".agent" / "task-families" / "locks"


def resolve_state_root(repo_root: Path) -> Path:
    return resolve_main_root(repo_root) / ".agent" / "task-families"


def _require_existing_root(root: Path) -> None:
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)


def safe_lock_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "-", value)


def _operation_lock_path(repo_root: Path, operation_id: str | None = None) -> Path:
    lock_root = resolve_lock_root(repo_root)
    suffix = f"{safe_lock_token(operation_id)}.lock" if operation_id else "global.lock"
    return lock_root / f"operation-{suffix}"


def _lineage_lock_path(repo_root: Path, lineage_id: str) -> Path:
    return resolve_lock_root(repo_root) / f"lineage-{safe_lock_token(lineage_id)}.lock"


def _family_lock_path(repo_root: Path, family: str) -> Path:
    return resolve_lock_root(repo_root) / f"family-{safe_lock_token(family)}.lock"


def _worktree_lock_path(repo_root: Path, worktree: Path) -> Path:
    rel = worktree.resolve().as_posix().replace("/", "-")
    return resolve_lock_root(repo_root) / f"worktree-{safe_lock_token(rel)}.lock"


@contextmanager
def flock(lock_path: Path) -> Iterator[Path]:
    _require_existing_root(lock_path.parent)
    with open(lock_path, "a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise LockAcquisitionError(f"lock busy: {lock_path}") from exc
        try:
            yield lock_path
        finally:
            with contextlib.suppress(Exception):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def operation_lock(repo_root: Path, operation_id: str | None = None):
    with flock(_operation_lock_path(repo_root, operation_id=operation_id)):
        yield


@contextmanager
def lineage_lock(repo_root: Path, lineage_id: str):
    with flock(_lineage_lock_path(repo_root, lineage_id)):
        yield


@contextmanager
def family_lock(repo_root: Path, family: str):
    with flock(_family_lock_path(repo_root, family)):
        yield


@contextmanager
def worktree_lock(repo_root: Path, worktree: Path):
    with flock(_worktree_lock_path(repo_root, worktree)):
        yield


def _parse_worktree_porcelain(raw: str) -> list[WorktreeInfo]:
    items: list[WorktreeInfo] = []
    current: dict[str, str] | None = None

    def flush() -> None:
        nonlocal current
        if current is None or "path" not in current:
            current = None
            return
        items.append(
            WorktreeInfo(
                path=Path(current["path"]),
                branch=current.get("branch"),
                head=current.get("head"),
                locked=(current.get("locked") == "true"),
                prunable=(current.get("prunable") == "true"),
            )
        )
        current = None

    for line in raw.splitlines():
        if not line:
            flush()
            continue
        if line.startswith("worktree "):
            flush()
            current = {"path": line.removeprefix("worktree ").strip()}
            continue
        if current is None:
            continue
        if line.startswith("HEAD "):
            current["head"] = line.removeprefix("HEAD ").strip()
            continue
        if line.startswith("branch "):
            branch = line.removeprefix("branch ").strip()
            if branch.startswith("refs/heads/"):
                branch = branch[len("refs/heads/") :]
            current["branch"] = branch
            continue
        if line.startswith("locked"):
            current["locked"] = "true"
            continue
        if line.startswith("prunable"):
            current["prunable"] = "true"
            continue

    flush()
    return items


def worktree_list(repo_root: Path) -> list[WorktreeInfo]:
    proc = run_git(["worktree", "list", "--porcelain"], cwd=repo_root)
    _require_success(proc, context="git worktree list failed")
    return _parse_worktree_porcelain(proc.stdout)


def is_worktree_registered(repo_root: Path, worktree: Path) -> bool:
    canonical = worktree.resolve()
    return any(item.path.resolve() == canonical for item in worktree_list(repo_root))


def worktree_branch(repo_root: Path, worktree: Path) -> str | None:
    canonical = worktree.resolve()
    for item in worktree_list(repo_root):
        if item.path.resolve() == canonical:
            return item.branch
    return None


def worktree_head(repo_root: Path, worktree: Path) -> str | None:
    canonical = worktree.resolve()
    for item in worktree_list(repo_root):
        if item.path.resolve() == canonical:
            return item.head
    return None


def is_worktree_shared(repo_root: Path, worktree: Path) -> bool:
    target_branch = worktree_branch(repo_root, worktree)
    if target_branch is None:
        return False
    count = 0
    for item in worktree_list(repo_root):
        if item.branch == target_branch:
            count += 1
    return count > 1


def is_worktree_permanent(repo_root: Path, worktree: Path) -> bool:
    return worktree.resolve() == resolve_main_root(repo_root).resolve()


def is_worktree_dirty(worktree: Path) -> bool:
    proc = run_git(["status", "--porcelain"], cwd=worktree)
    _require_success(proc, context=f"git status failed for worktree {worktree}")
    return bool((proc.stdout or "").strip())


def worktree_index_locked(worktree: Path) -> bool:
    proc = run_git(["rev-parse", "--git-path", "index.lock"], cwd=worktree)
    if proc.returncode != 0:
        return False
    raw = (proc.stdout or "").strip()
    if not raw:
        return False
    path = Path(raw)
    if not path.is_absolute():
        path = worktree / path
    try:
        return path.exists()
    except OSError:
        return False


def is_worktree_locked(repo_root: Path, worktree: Path) -> bool:
    """Return real Git lock evidence, never our advisory-lock file's existence."""
    canonical = worktree.resolve()
    for item in worktree_list(repo_root):
        if item.path.resolve() == canonical:
            return item.locked or item.prunable or worktree_index_locked(worktree)
    return worktree_index_locked(worktree)


def active_jobs_or_leases(repo_root: Path, lineage_id: str | None = None) -> list[Path]:
    state_root = resolve_state_root(repo_root)
    entries: list[Path] = []
    for path in sorted((state_root / "jobs").glob("*")):
        if not path.is_file() or not STATE_FILE_RE.match(path.name):
            continue
        if lineage_id is not None and lineage_id not in path.name:
            continue
        entries.append(path)
    for path in sorted((state_root / "leases").glob("*")):
        if not path.is_file() or not STATE_FILE_RE.match(path.name):
            continue
        if lineage_id is not None and lineage_id not in path.name:
            continue
        entries.append(path)
    for path in sorted(state_root.glob("*/operations/*/state.json")):
        if not STATE_FILE_RE.match(path.name):
            continue
        entries.append(path)
    return entries


def assert_no_active_jobs_or_leases(repo_root: Path, lineage_id: str | None = None) -> None:
    active = active_jobs_or_leases(repo_root, lineage_id=lineage_id)
    if active:
        names = ", ".join(sorted(path.name for path in active))
        raise GitSafetyError(f"active jobs/leases block cleanup: {names}")


def _repo_owner_and_name(repo_root: Path) -> tuple[str, str]:
    proc = run_gh(["repo", "view", "--json", "owner,name"], cwd=repo_root)
    if proc.returncode != 0:
        raise GitHubQueryError("gh repo view failed")
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise GitHubQueryError("invalid JSON from gh repo view") from exc
    if not isinstance(payload, dict):
        raise GitHubQueryError("unexpected repo payload type")
    owner_data = payload.get("owner")
    name = payload.get("name")
    owner = owner_data.get("login") if isinstance(owner_data, dict) else None
    if not isinstance(owner, str) or not owner or not isinstance(name, str) or not name:
        raise GitHubQueryError("incomplete owner/name payload")
    return owner, name


def _github_repo_default_branch(repo_root: Path) -> str:
    proc = run_gh(
        ["repo", "view", "--json", "defaultBranchRef"],
        cwd=repo_root,
    )
    if proc.returncode != 0:
        raise GitHubQueryError("github repo query failed")
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise GitHubQueryError("invalid JSON from github repo query") from exc
    if not isinstance(payload, dict):
        raise GitHubQueryError("invalid github repo payload type")
    ref = payload.get("defaultBranchRef")
    default_branch = ref.get("name") if isinstance(ref, dict) else None
    if not isinstance(default_branch, str) or not default_branch:
        raise GitHubQueryError("missing default branch in github repo payload")
    return default_branch


def remote_protected_branches(repo_root: Path, *, timeout: float = 30.0) -> set[str]:
    owner, name = _repo_owner_and_name(repo_root)
    proc = run_gh(
        ["api", "--paginate", "--slurp", f"repos/{owner}/{name}/branches?per_page=100"],
        cwd=repo_root,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise GitHubQueryError("github protected-branch query failed")
    try:
        payload = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise GitHubQueryError("invalid JSON from protected-branch query") from exc
    if not isinstance(payload, list):
        raise GitHubQueryError("invalid protected-branch payload")
    pages = payload if not payload or isinstance(payload[0], list) else [payload]
    protected: set[str] = set()
    for page in pages:
        if not isinstance(page, list):
            raise GitHubQueryError("invalid protected-branch page")
        for item in page:
            if not isinstance(item, dict):
                raise GitHubQueryError("invalid protected-branch item")
            name = item.get("name")
            if not isinstance(name, str) or not name:
                continue
            if item.get("protected") is True:
                protected.add(name)
    return protected


def protected_branches(
    repo_root: Path,
    explicit_protected: set[str] | frozenset[str] = frozenset(),
    *,
    timeout: float = 30.0,
) -> set[str]:
    branches = set(PROTECTED_BRANCHES)
    branches.add(repo_default_branch(repo_root))
    branches.update(explicit_protected)
    branches.update(remote_protected_branches(repo_root, timeout=timeout))
    return branches


def is_protected_branch(
    repo_root: Path,
    branch: str,
    explicit_protected: set[str] | frozenset[str] = frozenset(),
) -> bool:
    return branch in protected_branches(repo_root, explicit_protected=explicit_protected)


def repo_default_branch(repo_root: Path) -> str:
    return _github_repo_default_branch(repo_root)


def ensure_clean_base(repo_root: Path, base_branch: str) -> None:
    current_proc = run_git(["symbolic-ref", "--short", "HEAD"], cwd=repo_root)
    _require_success(current_proc, context="cannot determine active branch")
    current = (current_proc.stdout or "").strip()
    if current != base_branch:
        raise GitSafetyError(f"active branch is {current!r}, expected protected base {base_branch!r}")

    proc = run_git([
        "rev-list",
        "--left-right",
        "--count",
        f"origin/{base_branch}...{base_branch}",
    ], cwd=repo_root)
    if proc.returncode != 0:
        raise GitSafetyError(f"cannot verify base branch up-to-date for {base_branch}")
    if (proc.stdout or "").strip() not in {"0\t0", "0 0"}:
        raise GitSafetyError(f"base branch {base_branch} is not up to date")


def assert_primary_checkout(repo_root: Path) -> None:
    main_root = resolve_main_root(repo_root)
    if main_root.resolve() != Path(repo_root).resolve():
        raise GitSafetyError("operation must execute from primary checkout")


def _normalize_merge_commit(raw: Any) -> str:
    if isinstance(raw, str):
        value = raw.strip()
        if value:
            return value
        raise GitSafetyError("PR payload missing merge commit SHA")
    if isinstance(raw, dict):
        value = raw.get("oid") or raw.get("sha") or raw.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise GitSafetyError("PR payload merge commit not provided")


def _normalize_pr_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GitHubQueryError("unexpected pr payload shape")
    data = {
        "number": payload.get("number"),
        "state": str(payload.get("state") or "").upper(),
        "head_ref_oid": str(payload.get("headRefOid") or "").strip(),
        "head_ref_name": str(payload.get("headRefName") or "").strip(),
        "base_ref_name": str(payload.get("baseRefName") or "").strip(),
        "merge_state_status": str(payload.get("mergeStateStatus") or "").strip(),
        "is_cross_repository": bool(payload.get("isCrossRepository")),
        "merge_commit": _normalize_merge_commit(payload.get("mergeCommit")),
    }
    if not data["head_ref_oid"]:
        raise GitHubQueryError("PR payload missing headRefOid")
    return data


def query_pr_by_head(
    repo_root: Path,
    *,
    branch: str,
    pr_number: int | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    if pr_number is not None:
        proc = run_gh(
            [
                "pr",
                "view",
                str(pr_number),
                "--json",
                "number,state,headRefOid,headRefName,baseRefName,mergeStateStatus,mergeCommit,isCrossRepository",
            ],
            cwd=repo_root,
            timeout=timeout,
        )
        if proc.returncode != 0:
            raise GitHubQueryError(f"gh pr view failed for #{pr_number}")
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise GitHubQueryError("invalid JSON from gh pr view") from exc
        if str(payload.get("headRefName") or "") != branch:
            raise GitHubQueryError(f"PR #{pr_number} head mismatch for branch {branch}")
        return _normalize_pr_payload(payload)

    proc = run_gh(
        [
            "pr",
            "list",
            "--head",
            branch,
            "--state",
            "all",
            "--json",
            "number,state,headRefOid,headRefName,baseRefName,mergeStateStatus,mergeCommit,isCrossRepository",
        ],
        cwd=repo_root,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise GitHubQueryError(f"gh pr list failed for {branch!r}: {proc.stderr.strip() or proc.stdout.strip()}")
    try:
        items = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise GitHubQueryError("invalid JSON from gh pr list") from exc
    if not isinstance(items, list):
        raise GitHubQueryError("unexpected pr payload shape")
    if len(items) == 0:
        raise GitHubQueryError(f"no PR found for head {branch}")
    if len(items) != 1:
        raise GitHubQueryError(f"ambiguous PR lookup for head {branch}")
    if not isinstance(items[0], dict):
        raise GitHubQueryError("unexpected pr payload shape")
    return _normalize_pr_payload(items[0])


def assert_pr_is_merged(
    pr: dict[str, Any],
    *,
    expected_number: int | None = None,
    expected_branch: str | None = None,
    expected_head: str | None = None,
    expected_base: str | None = None,
) -> tuple[str, str, str]:
    if pr.get("state") != "MERGED":
        raise GitSafetyError(f"PR is not merged: {pr.get('state', 'MISSING')!r}")
    if pr.get("merge_state_status") and str(pr["merge_state_status"]).upper() not in {"CLEAN", "UNKNOWN"}:
        raise GitSafetyError(f"PR merge state is {pr.get('merge_state_status')!r}")
    if pr.get("is_cross_repository"):
        raise GitSafetyError("PR must not be cross-repository")
    number = int(pr.get("number", 0) or 0)
    if expected_number is not None and number and number != expected_number:
        raise GitSafetyError(
            f"PR number mismatch: expected {expected_number!r}, got {pr.get('number')!r}"
        )
    head_ref_name = pr.get("head_ref_name")
    if expected_branch is not None and head_ref_name != expected_branch:
        raise GitSafetyError(f"PR head branch mismatch: expected {expected_branch!r}, got {head_ref_name!r}")
    if expected_head is not None and pr.get("head_ref_oid") != expected_head:
        raise GitSafetyError(
            f"PR head mismatch: expected {expected_head!r}, got {pr.get('head_ref_oid')!r}"
        )
    if expected_base is not None and str(pr.get("base_ref_name") or "") != expected_base:
        raise GitSafetyError(
            f"PR base mismatch: expected {expected_base!r}, got {pr.get('base_ref_name')!r}"
        )
    return str(number), str(pr["head_ref_oid"]), pr["merge_commit"]


def local_branch_head(repo_root: Path, branch: str) -> str:
    proc = run_git(["rev-parse", f"refs/heads/{branch}"], cwd=repo_root)
    _require_success(proc, context=f"cannot resolve local branch head for {branch}")
    return (proc.stdout or "").strip()


def local_branch_exists(repo_root: Path, branch: str) -> bool:
    proc = run_git(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=repo_root)
    return proc.returncode == 0


def _local_branch_exists(repo_root: Path, branch: str) -> bool:
    return local_branch_exists(repo_root, branch)


def remote_branch_present(repo_root: Path, branch: str) -> bool:
    ref = branch if branch.startswith("refs/heads/") else f"refs/heads/{branch}"
    proc = run_git(["ls-remote", "--heads", "--exit-code", "origin", ref], cwd=repo_root)
    if proc.returncode == 0:
        return bool((proc.stdout or "").strip())
    if proc.returncode == 2:
        return False
    raise GitSafetyError(f"remote branch lookup failed for {branch!r}: {proc.stderr.strip() or proc.stdout.strip()}")


def assert_no_unknown_branch_mutation(
    repo_root: Path,
    branch: str,
    explicit_protected: set[str] | frozenset[str] = frozenset(),
) -> None:
    if ".." in branch or branch.strip() != branch or not branch:
        raise GitSafetyError(f"invalid branch token: {branch!r}")
    if is_protected_branch(repo_root, branch, explicit_protected=explicit_protected):
        raise GitSafetyError(f"refusing to mutate protected branch: {branch!r}")


def _bundle_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_bundle(
    repo_root: Path,
    *,
    branch: str,
    bundle_dir: Path,
    timeout: float = 30.0,
) -> BundleReceipt:
    assert_no_unknown_branch_mutation(repo_root, branch)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = bundle_dir / f"{safe_lock_token(branch)}.bundle"
    proc = run_git(
        ["bundle", "create", str(bundle_path), f"refs/heads/{branch}"],
        cwd=repo_root,
        timeout=timeout,
    )
    _require_success(proc, context=f"bundle create failed for {branch}")
    verify_bundle(bundle_path, branch=branch, repo_root=repo_root, timeout=timeout)
    return BundleReceipt(
        path=bundle_path,
        sha256=_bundle_sha256(bundle_path),
        branch=branch,
        created_at=_utc_now(),
    )


def verify_bundle(
    path: Path,
    *,
    branch: str | None = None,
    repo_root: Path | None = None,
    timeout: float = 30.0,
) -> None:
    if not path.exists():
        raise BundleError(f"bundle missing: {path}")
    proc = run_git(["bundle", "verify", str(path)], cwd=repo_root or Path("."), timeout=timeout)
    _require_success(proc, context="git bundle verify failed")
    if branch:
        listed = run_git(["bundle", "list-heads", str(path)], cwd=repo_root or Path("."), timeout=timeout)
        _require_success(listed, context="git bundle list-heads failed")
        full_ref = f"refs/heads/{branch}"
        included = False
        for line in (listed.stdout or "").splitlines():
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == full_ref:
                included = True
                break
        if not included:
            raise BundleError(f"bundle does not include {full_ref}")


def bundle_branch_head(
    path: Path,
    *,
    branch: str,
    repo_root: Path,
    timeout: float = 30.0,
) -> str:
    """Return the exact branch head recorded by a verified recovery bundle."""
    verify_bundle(path, branch=branch, repo_root=repo_root, timeout=timeout)
    listed = run_git(["bundle", "list-heads", str(path)], cwd=repo_root, timeout=timeout)
    _require_success(listed, context="git bundle list-heads failed")
    full_ref = f"refs/heads/{branch}"
    matches = [
        parts[0]
        for line in (listed.stdout or "").splitlines()
        if len(parts := line.strip().split()) >= 2 and parts[1] == full_ref
    ]
    if len(matches) != 1 or not re.fullmatch(r"[0-9a-fA-F]{40,64}", matches[0]):
        raise BundleError(f"bundle has ambiguous or invalid head for {full_ref}")
    return matches[0].lower()


def assert_bundle_matches_receipt(bundle: BundleReceipt, branch: str) -> None:
    if bundle.branch != branch:
        raise GitSafetyError(f"bundle branch mismatch: {bundle.branch!r} != {branch!r}")
    if not bundle.path.exists():
        raise GitSafetyError(f"bundle path missing: {bundle.path}")
    if not bundle.path.is_file():
        raise GitSafetyError(f"bundle path is not a file: {bundle.path}")
    if not bundle.sha256:
        raise GitSafetyError("bundle checksum missing")
    if _bundle_sha256(bundle.path) != bundle.sha256:
        raise GitSafetyError("bundle digest mismatch")


def remove_worktree(repo_root: Path, worktree: Path) -> None:
    proc = run_git(["worktree", "remove", str(worktree)], cwd=repo_root)
    _require_success(proc, context=f"git worktree remove failed: {worktree}")


def verify_frozen_preconditions(
    repo_root: Path,
    *,
    operation_id: str | None,
    lineage_id: str,
    family: str,
    worktree: Path,
) -> None:
    # Advisory locks are held by the caller.  Their files are not Git locks and
    # existence alone is not live-lock evidence.
    del operation_id, lineage_id, family
    if is_worktree_permanent(repo_root, worktree):
        raise GitSafetyError(f"worktree is primary checkout and cannot be removed: {worktree}")


def verify_worktree_candidate(
    repo_root: Path,
    *,
    worktree: Path,
    branch: str,
    explicit_family: str | None = None,
    planned_family: str | None = None,
) -> None:
    if explicit_family is not None and planned_family is not None and explicit_family != planned_family:
        raise GitSafetyError(f"family mismatch for {worktree}: {explicit_family!r} != {planned_family!r}")
    if not is_worktree_registered(repo_root, worktree):
        raise GitSafetyError(f"worktree is not registered: {worktree}")
    if is_worktree_shared(repo_root, worktree):
        raise GitSafetyError(f"worktree is shared: {worktree}")
    if is_worktree_locked(repo_root, worktree):
        raise GitSafetyError(f"worktree is locked: {worktree}")
    if is_worktree_permanent(repo_root, worktree):
        raise GitSafetyError(f"worktree is primary checkout: {worktree}")
    if is_worktree_dirty(worktree):
        raise GitSafetyError(f"worktree is dirty: {worktree}")
    actual_branch = worktree_branch(repo_root, worktree)
    if actual_branch != branch:
        raise GitSafetyError(
            f"worktree branch mismatch for {worktree}: planned {branch!r}, actual {actual_branch!r}"
        )


def assert_branch_deletion_preconditions(
    *,
    repo_root: Path,
    branch: str,
    pr_data: dict[str, Any],
    bundle: BundleReceipt,
    explicit_protected: set[str] | frozenset[str] = frozenset(),
    require_remote_gone: bool = True,
    allow_current_head: bool = False,
    worktree_registered: bool = False,
    expected_head: str | None = None,
) -> tuple[str, str, str]:
    assert_no_unknown_branch_mutation(repo_root, branch, explicit_protected=explicit_protected)
    assert_bundle_matches_receipt(bundle, branch=branch)
    pr_number, pr_head_oid, merge_commit = assert_pr_is_merged(
        pr_data,
        expected_branch=branch,
        expected_head=expected_head,
    )
    local_head = local_branch_head(repo_root, branch)
    if local_head != pr_head_oid:
        raise GitSafetyError(
            f"local branch head mismatch for {branch}: local {local_head!r}, pr head {pr_head_oid!r}"
        )
    bundle_head = bundle_branch_head(bundle.path, branch=branch, repo_root=repo_root)
    if bundle_head != local_head:
        raise GitSafetyError(
            f"recovery bundle head mismatch for {branch}: bundle {bundle_head!r}, local {local_head!r}"
        )
    if require_remote_gone and remote_branch_present(repo_root, branch):
        raise GitSafetyError(f"remote branch still present: {branch}")
    if worktree_registered:
        raise GitSafetyError(f"branch still has registered worktree: {branch}")
    proc = run_git(["symbolic-ref", "--short", "HEAD"], cwd=repo_root)
    _require_success(proc, context="cannot determine active checkout branch")
    if proc.stdout.strip() == branch:
        raise GitSafetyError(f"cannot delete currently checked out branch: {branch}")
    return pr_number, pr_head_oid, merge_commit


def delete_branch(repo_root: Path, *, branch: str, require_force: bool = False) -> None:
    del require_force
    # Squash/rebase GitHub merges need not make the local branch an ancestor of
    # the checkout.  Preconditions above are the authority; worktree removal is
    # never forced.
    proc = run_git(["branch", "-D", branch], cwd=repo_root)
    _require_success(proc, context=f"git branch deletion failed for {branch}")
