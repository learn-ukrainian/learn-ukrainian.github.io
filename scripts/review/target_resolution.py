"""Deterministic review-target selection.

Four explicit modes — ``local`` / ``commit`` / ``branch`` / ``pr`` — chosen
by the caller, never inferred from working-tree state. This matters because
a clean working tree under ``local`` mode must never be read as proof that a
commit or PR was reviewed: each mode records its own base/head SHAs so a
report can't conflate "nothing uncommitted right now" with "the committed
change was reviewed."

Resolution never mutates repository or remote state. PR-mode resolution may
``git fetch`` the two SHAs it needs (read-only), but never pushes — a target
that only exists on the remote is a reason to fetch, not to push a local
branch just so a diff exists.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from scripts.common import github_client
from scripts.common.git_context import sanitized_git_env
from scripts.common.repo_root import main_checkout_root
from scripts.orchestration.fleet_repos import (
    FleetRepoError,
    MissingFleetCheckout,
    canonical_repo_key,
    load_fleet_repos,
    resolve_fleet_repo,
)

TEST_DIR_MARKERS = ("tests/", "__tests__/", "test/")
TEST_FILE_PREFIXES = ("test_",)
TEST_FILE_SUFFIXES = (
    "_test.py",
    ".test.ts",
    ".test.tsx",
    ".test.js",
    ".test.jsx",
    ".spec.ts",
    ".spec.tsx",
    ".spec.js",
    ".spec.jsx",
)


class TargetResolutionError(RuntimeError):
    """A review target could not be resolved deterministically."""


class MissingReviewCommit(TargetResolutionError):
    """The review target's commit object is not in the checkout.

    Raised only for that object. A wrong ``--base`` ref stays a plain
    ``TargetResolutionError``, so rewording the missing-commit text cannot
    drop or widen the neutral private refusal.
    """


# Fail closed on lookalike hosts. Same shapes as delegate's remote parser.
_GITHUB_ORIGIN_PATTERNS = (
    re.compile(r"^https?://(?:[^/@\s]+@)?github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^ssh://git@github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^git@github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^git://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
)
_FULL_SHA = re.compile(r"^[0-9a-fA-F]{40}$")

PRIVATE_REVIEW_TARGET_UNRESOLVED = (
    "PRIVATE_REVIEW_TARGET_UNRESOLVED: --repo infra-private checkout or target unavailable; "
    "use the private review trigger in the infra-private repository"
)
REVIEW_ROOT_MISMATCH = (
    "REVIEW_ROOT_MISMATCH: --repo-root origin does not match the catalog repository; "
    "symbolic refs and local mode are refused"
)
REVIEW_ROOT_UNAVAILABLE = "REVIEW_ROOT_UNAVAILABLE: --repo-root is not a checkout"


def spells_private_repo(repo_key: str | None) -> bool:
    """True when *repo_key* is the private catalog key, ignoring pad and case."""
    return isinstance(repo_key, str) and repo_key.strip().casefold() == "infra-private"


def repository_target_error(repo_key: str | None, error: Exception) -> TargetResolutionError:
    """Hide a missing private checkout or commit; keep every other refusal specific."""
    if spells_private_repo(repo_key) and isinstance(error, (MissingFleetCheckout, MissingReviewCommit, OSError)):
        return TargetResolutionError(PRIVATE_REVIEW_TARGET_UNRESOLVED)
    if isinstance(error, TargetResolutionError):
        return error
    if isinstance(error, OSError):
        return TargetResolutionError(REVIEW_ROOT_UNAVAILABLE)
    return TargetResolutionError(str(error))


def _directory_root(repo_root: Path) -> bool:
    try:
        return repo_root.is_dir()
    except OSError:
        return False


def _origin_github_repo(checkout: Path) -> str | None:
    if not _directory_root(checkout):
        raise OSError(REVIEW_ROOT_UNAVAILABLE)
    try:
        proc = _run_git(["config", "--get", "remote.origin.url"], checkout)
    except OSError:
        raise OSError(REVIEW_ROOT_UNAVAILABLE) from None
    if proc.returncode != 0:
        return None
    text = proc.stdout.strip()
    for pattern in _GITHUB_ORIGIN_PATTERNS:
        match = pattern.match(text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None


def _is_symbolic_review_ref(ref: str | None) -> bool:
    """True for ``HEAD`` and branch-relative ``~`` / ``^`` forms.

    A full SHA and a branch name are not symbolic: those still resolve in the
    catalog checkout when ``--repo-root`` is a different repository.
    """
    if ref is None or _FULL_SHA.fullmatch(ref):
        return False
    if ref in {"HEAD", "@"} or ref.endswith("/HEAD"):
        return True
    return "~" in ref or "^" in ref or "@{" in ref


def _review_refs(mode: str | None, *, commit: str | None, branch: str | None, base: str | None) -> tuple[str, ...]:
    if mode == "commit":
        return (commit,) if commit else ()
    if mode == "branch":
        return tuple(ref for ref in (branch, base) if ref)
    return ()


def resolve_review_repository(
    repo_root: Path,
    repo_key: str | None = None,
    *,
    mode: str | None = None,
    commit: str | None = None,
    branch: str | None = None,
    base: str | None = None,
) -> Path:
    """Select the catalog checkout, keeping a root whose origin already matches.

    A linked worktree of the catalog repository is that repository: ``HEAD``
    and ``--mode local`` stay there. A missing, unparsable, or different
    origin is not that checkout. Symbolic refs and local mode are refused;
    a full SHA, a branch name, or a PR number still resolves in the catalog
    checkout found from ``repo_root``.
    """
    if repo_key is None:
        return repo_root
    try:
        catalog = load_fleet_repos()
        canonical = canonical_repo_key(repo_key, catalog)
    except FleetRepoError as exc:
        raise repository_target_error(repo_key, exc) from exc
    if not _directory_root(repo_root):
        raise repository_target_error(canonical, OSError(REVIEW_ROOT_UNAVAILABLE)) from None
    fleet_repo = catalog[canonical]
    try:
        origin = _origin_github_repo(repo_root)
    except OSError as exc:
        raise repository_target_error(canonical, exc) from None
    if origin is not None and origin.casefold() == fleet_repo.github.casefold():
        return repo_root
    refs = _review_refs(mode, commit=commit, branch=branch, base=base)
    if mode == "local" or any(_is_symbolic_review_ref(ref) for ref in refs):
        raise TargetResolutionError(REVIEW_ROOT_MISMATCH)
    try:
        resolved, checkout = resolve_fleet_repo(canonical, primary_root=main_checkout_root(repo_root))
    except FleetRepoError as exc:
        raise repository_target_error(canonical, exc) from exc
    try:
        catalog_origin = _origin_github_repo(checkout)
    except OSError as exc:
        raise repository_target_error(canonical, exc) from None
    if catalog_origin is None or catalog_origin.casefold() != resolved.github.casefold():
        raise TargetResolutionError(
            f"--repo {resolved.key} checkout origin does not match catalog repository {resolved.github}"
        )
    return checkout


@dataclass(frozen=True)
class ReviewTarget:
    """One resolved review target. Immutable — the scope baseline freezes on it."""

    mode: str
    base_sha: str | None
    head_sha: str | None
    changed_paths: tuple[str, ...]
    non_test_loc: int
    clean_tree: bool
    description: str
    # The PR base ref name. Closeout stores it so a later resolve-reviewer can
    # exclude the default branch. Absent for local, commit, and branch targets.
    base_ref_name: str | None = None


def is_test_path(path: str) -> bool:
    """True if ``path`` looks like a test file, for non-test LOC accounting."""
    normalized = path.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1]
    if any(marker in f"{normalized}/" for marker in TEST_DIR_MARKERS):
        return True
    if name.startswith(TEST_FILE_PREFIXES):
        return True
    return any(name.endswith(suffix) for suffix in TEST_FILE_SUFFIXES)


def _run_git(args: list[str], cwd: Path, *, timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=sanitized_git_env(),
    )


def _run_gh(args: list[str], cwd: Path, *, timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    return github_client.run(
        ["gh", *args],
        cwd=str(cwd),
        check=False,
        fresh=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _rev_parse(repo_root: Path, ref: str, *, missing_commit: bool = False) -> str:
    # A full SHA is echoed by ``rev-parse`` even when the object is absent.
    # ``--verify`` with the commit peel refuses that missing object here.
    proc = _run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"], repo_root)
    if proc.returncode != 0:
        message = f"cannot resolve ref {ref!r}: {proc.stderr.strip()}"
        if missing_commit:
            raise MissingReviewCommit(message)
        raise TargetResolutionError(message)
    return proc.stdout.strip()


def rev_parse(repo_root: Path, ref: str) -> str:
    """Public wrapper: resolve ``ref`` to a full SHA. Read-only."""
    return _rev_parse(repo_root, ref)


def _numstat_loc(repo_root: Path, diff_range: list[str]) -> tuple[tuple[str, ...], int]:
    """Return (changed_paths, non_test_loc) for a ``git diff --numstat`` range."""
    proc = _run_git(["diff", "--numstat", *diff_range], repo_root)
    if proc.returncode != 0:
        raise TargetResolutionError(f"git diff --numstat failed: {proc.stderr.strip()}")
    changed: list[str] = []
    loc = 0
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        added_raw, removed_raw, path = parts
        changed.append(path)
        if is_test_path(path):
            continue
        # Binary files report "-" for both counts; they contribute 0 LOC
        # but still count as a changed path.
        added = int(added_raw) if added_raw.isdigit() else 0
        removed = int(removed_raw) if removed_raw.isdigit() else 0
        loc += added + removed
    return tuple(changed), loc


def diff_against_base(repo_root: Path, base_sha: str, head_sha: str) -> tuple[tuple[str, ...], int]:
    """Public wrapper: (changed_paths, non_test_loc) for an explicit
    ``base_sha..head_sha`` range. Read-only — used to re-measure a frozen
    commit/branch/PR target's full diff after committed fixes land, without
    re-resolving the target from scratch (e.g. re-querying ``gh pr view``,
    whose live base/head could have moved since the target was frozen)."""
    return _numstat_loc(repo_root, [base_sha, head_sha])


def _untracked_paths(repo_root: Path) -> tuple[str, ...]:
    proc = _run_git(["status", "--porcelain", "--untracked-files=all"], repo_root)
    if proc.returncode != 0:
        raise TargetResolutionError(f"git status failed: {proc.stderr.strip()}")
    untracked = []
    for line in proc.stdout.splitlines():
        if line.startswith("??"):
            untracked.append(line[3:].strip())
    return tuple(untracked)


def _untracked_loc(repo_root: Path, paths: tuple[str, ...]) -> int:
    total = 0
    for rel_path in paths:
        if is_test_path(rel_path):
            continue
        full = repo_root / rel_path
        if not full.is_file():
            continue
        try:
            text = full.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        total += len(text.splitlines())
    return total


def resolve_local_target(repo_root: Path) -> ReviewTarget:
    """Staged + unstaged + untracked working-tree changes, diffed against HEAD.

    ``base_sha``/``head_sha`` are ``None`` — this mode has no committed
    endpoints by definition. A caller must not treat a ``clean_tree=True``
    result here as evidence that a *commit* or *PR* was reviewed; that
    requires a separate ``commit``/``branch``/``pr`` resolution.
    """
    tracked_changed, tracked_loc = _numstat_loc(repo_root, ["HEAD"])
    untracked = _untracked_paths(repo_root)
    untracked_loc = _untracked_loc(repo_root, untracked)
    changed_paths = tuple(dict.fromkeys([*tracked_changed, *untracked]))
    clean_tree = len(changed_paths) == 0
    description = (
        "local working tree: no staged/unstaged/untracked changes (nothing to review)"
        if clean_tree
        else f"local working tree: {len(changed_paths)} changed path(s) vs HEAD"
    )
    return ReviewTarget(
        mode="local",
        base_sha=None,
        head_sha=None,
        changed_paths=changed_paths,
        non_test_loc=tracked_loc + untracked_loc,
        clean_tree=clean_tree,
        description=description,
    )


def resolve_commit_target(repo_root: Path, commit: str) -> ReviewTarget:
    """A single already-made commit, diffed against its first parent."""
    head_sha = _rev_parse(repo_root, commit, missing_commit=True)
    base_proc = _run_git(["rev-parse", f"{commit}^"], repo_root)
    if base_proc.returncode != 0:
        raise TargetResolutionError(
            f"cannot resolve parent of {commit!r} (root commit is not supported): {base_proc.stderr.strip()}"
        )
    base_sha = base_proc.stdout.strip()
    changed_paths, non_test_loc = _numstat_loc(repo_root, [base_sha, head_sha])
    return ReviewTarget(
        mode="commit",
        base_sha=base_sha,
        head_sha=head_sha,
        changed_paths=changed_paths,
        non_test_loc=non_test_loc,
        clean_tree=False,
        description=f"commit {head_sha[:12]} vs parent {base_sha[:12]}",
    )


def resolve_branch_target(repo_root: Path, branch: str, base: str) -> ReviewTarget:
    """A branch diffed against an explicit base ref (merge-base semantics)."""
    head_sha = _rev_parse(repo_root, branch, missing_commit=True)
    base_ref_sha = _rev_parse(repo_root, base)
    merge_base_proc = _run_git(["merge-base", base_ref_sha, head_sha], repo_root)
    if merge_base_proc.returncode != 0:
        raise TargetResolutionError(f"no merge-base between {base!r} and {branch!r}: {merge_base_proc.stderr.strip()}")
    merge_base_sha = merge_base_proc.stdout.strip()
    changed_paths, non_test_loc = _numstat_loc(repo_root, [merge_base_sha, head_sha])
    return ReviewTarget(
        mode="branch",
        base_sha=merge_base_sha,
        head_sha=head_sha,
        changed_paths=changed_paths,
        non_test_loc=non_test_loc,
        clean_tree=False,
        description=f"branch {branch} vs base {base} (merge-base {merge_base_sha[:12]})",
    )


def _ensure_commit_available(repo_root: Path, sha: str) -> None:
    check = _run_git(["cat-file", "-e", f"{sha}^{{commit}}"], repo_root)
    if check.returncode == 0:
        return
    # Read-only fetch of the missing object — never a push, never a new local branch.
    fetch = _run_git(["fetch", "origin", sha], repo_root, timeout=60.0)
    if fetch.returncode != 0:
        raise MissingReviewCommit(f"commit {sha!r} unreachable locally and fetch failed: {fetch.stderr.strip()}")
    recheck = _run_git(["cat-file", "-e", f"{sha}^{{commit}}"], repo_root)
    if recheck.returncode != 0:
        raise MissingReviewCommit(f"commit {sha!r} still unreachable after fetch")


def resolve_pr_target(repo_root: Path, pr_number: int) -> ReviewTarget:
    """A PR's diff using the merge-base with its actual base branch (not an
    assumed default branch, and not the base branch's possibly-moved tip).

    ``baseRefOid`` is the base branch's *current tip* at query time, not
    necessarily the commit the PR actually forked from — the base branch can
    advance after the feature diverged. Diffing straight against that tip
    would pull in every commit the base gained since divergence as if the PR
    introduced them. The merge-base is the fork point and is what a diff
    must be computed against. The base ref name is kept on the target so a
    later review can exclude the default branch; the base tip stays in
    ``description`` for provenance.
    """
    slug = _origin_github_repo(repo_root)
    if slug is None:
        raise TargetResolutionError("checkout origin is not a GitHub owner/name; refusing an unpinned gh pr view")
    proc = _run_gh(
        [
            "pr",
            "view",
            str(pr_number),
            "--repo",
            slug,
            "--json",
            "number,baseRefName,baseRefOid,headRefName,headRefOid",
        ],
        repo_root,
    )
    if proc.returncode != 0:
        raise TargetResolutionError(f"gh pr view failed for #{pr_number}: {proc.stderr.strip() or proc.stdout.strip()}")
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise TargetResolutionError(f"invalid JSON from gh pr view #{pr_number}") from exc

    base_tip_sha = str(payload.get("baseRefOid") or "").strip()
    head_sha = str(payload.get("headRefOid") or "").strip()
    raw_base_name = payload.get("baseRefName")
    head_ref_name = str(payload.get("headRefName") or "").strip()
    if not isinstance(raw_base_name, str) or not raw_base_name.strip():
        raise TargetResolutionError(f"PR #{pr_number} payload missing base ref name")
    base_ref_name = raw_base_name.strip()
    if not base_tip_sha or not head_sha:
        raise TargetResolutionError(f"PR #{pr_number} payload missing base/head SHA")

    _ensure_commit_available(repo_root, base_tip_sha)
    _ensure_commit_available(repo_root, head_sha)
    merge_base_proc = _run_git(["merge-base", base_tip_sha, head_sha], repo_root)
    if merge_base_proc.returncode != 0:
        raise TargetResolutionError(
            f"no merge-base between PR #{pr_number} base {base_tip_sha!r} and head {head_sha!r}: "
            f"{merge_base_proc.stderr.strip()}"
        )
    merge_base_sha = merge_base_proc.stdout.strip()
    changed_paths, non_test_loc = _numstat_loc(repo_root, [merge_base_sha, head_sha])
    return ReviewTarget(
        mode="pr",
        base_sha=merge_base_sha,
        head_sha=head_sha,
        changed_paths=changed_paths,
        non_test_loc=non_test_loc,
        clean_tree=False,
        description=(
            f"PR #{pr_number}: {head_ref_name}@{head_sha[:12]} vs merge-base {merge_base_sha[:12]} "
            f"(base tip {base_ref_name}@{base_tip_sha[:12]})"
        ),
        base_ref_name=base_ref_name,
    )


def resolve_review_target(
    mode: str,
    repo_root: Path,
    *,
    commit: str | None = None,
    branch: str | None = None,
    base: str | None = None,
    pr_number: int | None = None,
) -> ReviewTarget:
    """Dispatch to the mode-specific resolver. ``mode`` must be explicit."""
    if mode == "local":
        return resolve_local_target(repo_root)
    if mode == "commit":
        if not commit:
            raise TargetResolutionError("mode=commit requires --commit")
        return resolve_commit_target(repo_root, commit)
    if mode == "branch":
        if not branch or not base:
            raise TargetResolutionError("mode=branch requires --branch and --base")
        return resolve_branch_target(repo_root, branch, base)
    if mode == "pr":
        if pr_number is None:
            raise TargetResolutionError("mode=pr requires --pr")
        return resolve_pr_target(repo_root, pr_number)
    raise TargetResolutionError(f"unknown mode {mode!r} (expected local/commit/branch/pr)")


def _main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=["local", "commit", "branch", "pr"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--commit")
    parser.add_argument("--branch")
    parser.add_argument("--base")
    parser.add_argument("--pr", type=int, dest="pr_number")
    args = parser.parse_args(argv)

    try:
        target = resolve_review_target(
            args.mode,
            Path(args.repo_root).resolve(),
            commit=args.commit,
            branch=args.branch,
            base=args.base,
            pr_number=args.pr_number,
        )
    except TargetResolutionError as exc:
        print(json.dumps({"error": str(exc)}), file=__import__("sys").stderr)
        return 1

    print(json.dumps(target.__dict__, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
