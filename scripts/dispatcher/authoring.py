"""Authoring-review admission ported mechanically from delegate.py 17514-18545.

Remote observations and refusals remain those of the legacy gate. The v2
adapter below binds the target and rechecks it under the worktree lock.
"""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import functools
import json
import os
import re
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.common.git_context import sanitized_git_env
from scripts.common.task_store_paths import tasks_dir
from scripts.dispatcher import git

_REPO_ROOT = git.ROOT
DEFAULT_GIT_TIMEOUT_S = 30.0
DEFAULT_NETWORK_GIT_TIMEOUT_S = 180.0
DEFAULT_GH_CLI_TIMEOUT_S = 180.0
_WRITE_CAPABLE_MODES = frozenset({'workspace-write', 'danger'})


def _sanitized_git_env():
    # Legacy delegate.py:5823, over the shared redirect guard.
    env = {key: value for key, value in sanitized_git_env().items() if not key.startswith('PRE_COMMIT')}
    env['GIT_TERMINAL_PROMPT'] = '0'
    return env

AUTHORING_REVIEW_NO_ROUTE = "AUTHORING_REVIEW_NO_ROUTE"
AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN = "AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN"
AUTHORING_REVIEW_SCOPE_UNKNOWN = "AUTHORING_REVIEW_SCOPE_UNKNOWN"
AUTHORING_REVIEW_TARGET_MOVED = "AUTHORING_REVIEW_TARGET_MOVED"
AUTHORING_REVIEW_CATALOG_UNKNOWN = "AUTHORING_REVIEW_CATALOG_UNKNOWN"
AUTHORING_REVIEW_REPOSITORY_MISMATCH = "AUTHORING_REVIEW_REPOSITORY_MISMATCH"
AUTHORING_REVIEW_STATE_KEY = "authoring_review_admission"
# A write dispatch that names no planned review risk is checked at the strictest
# risk; path inference may raise a declared risk, never lower it.
AUTHORING_REVIEW_DEFAULT_RISK = "critical"
# A7 (#9739): an open-PR lookup that returns this many rows may be truncated, so
# it is incomplete (M3).
AUTHORING_REVIEW_PR_LOOKUP_LIMIT = 100
_AUTHORING_COMMIT_SHA_RE = re.compile(r"[0-9a-f]{40}")


class _AuthoringReviewRefused(Exception):
    """Dispatch refused before a task record or a worker.

    The branch is untouched, except a refusal whose record binding is
    ``rebase``: that rebase has already run, and :meth:`render` says so.
    """

    def __init__(self, code: str, detail: str, record: dict[str, Any]) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.record = record

    def render(self) -> str:
        """The stderr refusal: one actionable line, then one JSON line for tools.

        A post-rebase refusal (``binding`` ``rebase``) has already moved the
        worktree. It names the pre-rebase head and the refs that still point
        at it. Every earlier refusal leaves the branch untouched.
        """
        payload = json.dumps({AUTHORING_REVIEW_STATE_KEY: {**self.record, "refusal": self.code}}, sort_keys=True)
        if self.record.get("binding") == "rebase":
            pre = self.record.get("pre_rebase_head") or self.record.get("admitted_sha") or ""
            refs = self.record.get("recovery_refs") or ("ORIG_HEAD", "HEAD@{1}")
            tail = (
                f"Worktree was rebased; pre-rebase head {pre}. "
                f"Recover it with {' or '.join(str(ref) for ref in refs)}. provider_calls=0."
            )
        else:
            tail = "Branch preserved; provider_calls=0."
        return f"❌ {self.code}: {self.detail} {tail}\n{payload}"


class _AuthoringObservationUnknown(Exception):
    """A review-target observation did not complete; the message names no private detail."""


@dataclass(frozen=True)
class _ReviewBase:
    """The commit the verdict recorder enumerates authors from, and what bound it (A7).

    ``source`` is ``pr`` (``--pr``), ``open-pr`` (the one open PR of the head
    branch) or ``default-branch`` (no open PR: the repository's actual default).
    """

    sha: str
    branch: str
    pr: int | None
    source: str

    def binding(self) -> tuple[str, str, int | None]:
        return (self.sha, self.branch, self.pr)

    def receipt(self, repository: str) -> dict[str, Any]:
        return {"repository": repository, "branch": self.branch, "pr": self.pr, "source": self.source}


@dataclass(frozen=True)
class _AuthoringAdmission:
    """The endpoints authoring-review admission froze, for the re-check under the worktree lock (A3, A7).

    ``head_sha`` is the commit authors were enumerated to: an existing target's
    head, or ``creation_sha`` for a new branch, which worktree creation then
    uses as is. ``review_base`` is the enumeration's lower end.
    """

    kind: str  # existing-worktree | existing-branch | new-branch
    head_sha: str
    checkout: Path | None
    branch: str | None
    pinned_head: str | None
    record: dict[str, Any]
    repository: str
    remote: str
    head_branch: str
    pr: int | None
    review_base: _ReviewBase
    default_branch: str
    creation_ref: str | None = None
    creation_sha: str | None = None
    # This writer's facts over ``base..head`` (raises ``_AuthoringReviewRefused``),
    # and the planned risk, for the rebase plan and its result (A7).
    collect: Callable[..., Any] | None = dataclasses.field(default=None, compare=False, repr=False)
    planned_risk: str | None = None
    suspect_history: tuple[str, ...] = ()
    history_remote_head_sha: str | None = None


def _authoring_canonical_remote() -> str:
    """The remote serving the canonical GitHub repository, chosen as the fetch helpers choose it (#7522, M2)."""
    return _resolve_canonical_remote_name(_git_remote_urls(_REPO_ROOT)) or "origin"


def _authoring_default_branch(remote: str) -> tuple[str, str]:
    """The remote's actual default branch and its commit, from ``git ls-remote --symref`` (M4)."""
    try:
        proc = subprocess.run(
            ["git", "ls-remote", "--symref", remote, "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise _AuthoringObservationUnknown("the default-branch lookup timed out") from exc
    except OSError as exc:
        raise _AuthoringObservationUnknown("the default-branch lookup is unavailable") from exc
    name = sha = None
    for line in (proc.stdout or "").splitlines() if proc.returncode == 0 else ():
        value, _, ref = line.partition("\t")
        if ref.strip() != "HEAD":
            continue
        if value.startswith("ref: refs/heads/"):
            name = value.removeprefix("ref: refs/heads/").strip()
        elif _AUTHORING_COMMIT_SHA_RE.fullmatch(value.strip()):
            sha = value.strip()
    if not name or not sha:
        raise _AuthoringObservationUnknown("the canonical remote's default branch is unavailable")
    return name, sha


def _authoring_gh_json(command: list[str], *, what: str) -> Any:
    """One GitHub read; a failure is typed (timeout, quota, unavailable, malformed), never echoed."""
    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=False, timeout=DEFAULT_GH_CLI_TIMEOUT_S)
    except subprocess.TimeoutExpired as exc:
        raise _AuthoringObservationUnknown(f"{what} timed out") from exc
    except OSError as exc:
        raise _AuthoringObservationUnknown(f"{what} is unavailable") from exc
    if proc.returncode != 0:
        detail = f"{proc.stderr or ''} {proc.stdout or ''}".casefold()
        if "rate limit" in detail or "http 429" in detail:
            raise _AuthoringObservationUnknown(f"{what} hit the GitHub API quota")
        raise _AuthoringObservationUnknown(f"{what} is unavailable")
    try:
        return json.loads(proc.stdout)
    except ValueError as exc:
        raise _AuthoringObservationUnknown(f"{what} returned a malformed answer") from exc


def _authoring_pr_base(row: Any, *, source: str, what: str) -> tuple[_ReviewBase, str]:
    """A PR row's review base and head branch; a row missing either is malformed."""
    if not isinstance(row, dict):
        raise _AuthoringObservationUnknown(f"{what} returned a malformed answer")
    number, base, base_sha, head = (row.get(key) for key in ("number", "baseRefName", "baseRefOid", "headRefName"))
    if (
        type(number) is not int
        or not isinstance(base, str)
        or not base.strip()
        or not isinstance(base_sha, str)
        or not _AUTHORING_COMMIT_SHA_RE.fullmatch(base_sha)
        or not isinstance(head, str)
    ):
        raise _AuthoringObservationUnknown(f"{what} returned a malformed answer")
    return _ReviewBase(base_sha, base.strip(), number, source), head


def _authoring_open_pr_bases(repository: str, head_branch: str) -> list[_ReviewBase]:
    """The review base of every open PR whose head is ``head_branch`` in ``repository`` itself (M3).

    A fork's branch of the same name belongs to another repository and is left
    out, so no outside fork can block a dispatch. A list at the lookup limit
    may be truncated and is refused as incomplete.
    """
    what = "the open-PR lookup"
    rows = _authoring_gh_json(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repository,
            "--state",
            "open",
            "--head",
            head_branch,
            "--limit",
            str(AUTHORING_REVIEW_PR_LOOKUP_LIMIT),
            "--json",
            "number,headRefName,isCrossRepository,baseRefName,baseRefOid",
        ],
        what=what,
    )
    if not isinstance(rows, list):
        raise _AuthoringObservationUnknown(f"{what} returned a malformed answer")
    if len(rows) >= AUTHORING_REVIEW_PR_LOOKUP_LIMIT:
        raise _AuthoringObservationUnknown(f"{what} reached its limit, so it is incomplete")
    bases: list[_ReviewBase] = []
    for row in rows:
        cross = row.get("isCrossRepository") if isinstance(row, dict) else None
        if not isinstance(cross, bool):
            raise _AuthoringObservationUnknown(f"{what} returned a malformed answer")
        if cross:
            continue
        base, head = _authoring_pr_base(row, source="open-pr", what=what)
        if head != head_branch:
            raise _AuthoringObservationUnknown(f"{what} returned a malformed answer")
        bases.append(base)
    return bases


def _authoring_review_base(
    repository: str, *, pr: int | None, head_branch: str, default_branch: Callable[[], tuple[str, str]]
) -> _ReviewBase:
    """The base the verdict recorder will enumerate this branch's authors from (A7 §2).

    ``--pr``: that PR's ``baseRefOid``, once the PR is shown open, in this
    repository and headed by ``head_branch``. Otherwise the one open PR of
    ``head_branch``, or, when the lookup establishes there is none, the
    repository's actual default branch commit. A caller's ``--base`` never
    enters. Raises ``_AuthoringObservationUnknown`` when the binding cannot be
    established: unavailable, malformed, incomplete or ambiguous.
    """
    if pr is not None:
        what = f"the lookup of PR #{int(pr)}"
        row = _authoring_gh_json(
            [
                "gh",
                "pr",
                "view",
                str(int(pr)),
                "--repo",
                repository,
                "--json",
                "number,state,headRefName,isCrossRepository,baseRefName,baseRefOid",
            ],
            what=what,
        )
        base, head = _authoring_pr_base(row, source="pr", what=what)
        if row.get("state") != "OPEN" or row.get("isCrossRepository") is not False:
            raise _AuthoringObservationUnknown(f"PR #{int(pr)} is not an open PR headed in {repository}")
        if head != head_branch:
            raise _AuthoringObservationUnknown(f"PR #{int(pr)} is headed by another branch than {head_branch}")
        return base
    bases = _authoring_open_pr_bases(repository, head_branch)
    if len(bases) > 1:
        raise _AuthoringObservationUnknown(
            f"{len(bases)} open PRs are headed by {head_branch}, so the review base is ambiguous"
        )
    if bases:
        return bases[0]
    name, sha = default_branch()
    return _ReviewBase(sha, name, None, "default-branch")


def _authoring_start_commit(remote: str, ref: str, default: tuple[str, str]) -> str:
    """The commit a new branch would start at: ``ref`` on the canonical remote, or the observed default tip."""
    name, sha = default
    start = sha if ref == name else _ls_remote_branch_sha(remote, ref)
    if not start:
        raise _AuthoringObservationUnknown(f"start branch {ref} is not readable on the canonical remote")
    return start


def _authoring_commit_available(sha: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def _authoring_require_commit(sha: str, *, fetch: Callable[[], object], what: str, refresh: bool = False) -> None:
    """M1: make an observed commit local, fetching from the canonical remote at most once.

    The fetch only mirrors remote state into ``origin/<branch>``; the SHA stays
    the one observed and is never resolved from a ref again. ``refresh``
    fetches even when the commit is already local, keeping the tracking ref as
    current as the base fetch at worktree creation used to (the Kimi gate reads
    it, #9275).
    """
    if not refresh and _authoring_commit_available(sha):
        return
    # A failed fetch is judged by its outcome: the commit is still missing.
    with contextlib.suppress(RuntimeError, ValueError):
        fetch()
    if not _authoring_commit_available(sha):
        raise _AuthoringObservationUnknown(f"{what} {sha[:12]} is not available locally after fetching")


def _authoring_attach_head(
    *,
    kind: str,
    checkout: Path | None,
    branch: str | None,
    pinned_head: str | None,
    remote: str,
    observed_branch_head: str | None = None,
) -> str:
    """The head an attaching writer continues: the checkout's commit, or the branch on the canonical remote.

    A branch head is observed on the remote, never read from a possibly stale
    tracking ref (M2); a pinned head is the commit the dispatch was pinned to.
    Initial admission may reuse the early branch observation; rechecks omit it.
    """
    if kind == "existing-worktree":
        head = _resolve_sha(checkout) if checkout is not None and checkout.is_dir() else None
        if not head:
            raise _AuthoringObservationUnknown("the checkout's HEAD is unreadable")
        return head
    head = pinned_head or observed_branch_head or (_ls_remote_branch_sha(remote, branch) if branch else None)
    if not head:
        raise _AuthoringObservationUnknown(f"branch {branch} is not readable on the canonical remote")
    return head


def _git_common_dir_identity(path: Path) -> Path | None:
    """The repository ``path`` belongs to: git's absolute common directory, canonical; None outside git."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    common = (proc.stdout or "").strip() if proc.returncode == 0 else ""
    return Path(common).resolve() if common else None


def _is_other_repository(checkout: Path, repo_root: Path) -> bool:
    """True only when git proves ``checkout`` belongs to a repository other than ``repo_root``'s.

    Repository identity is the shared git common directory, never a path name:
    a sibling worktree laid out like one of the primary's still has its own
    common directory. Unresolvable identity is not proof of a sibling.
    """
    checkout_repo = _git_common_dir_identity(checkout)
    target_repo = _git_common_dir_identity(repo_root)
    return checkout_repo is not None and target_repo is not None and checkout_repo != target_repo


def _authoring_review_admission(
    args: argparse.Namespace,
    *,
    dispatch_agent: str,
    requested_harness: str | None,
    requested_branch: str | None,
    worktree_arg: str | None,
    validated_worktree: Path | None,
    validated_cwd: Path | None,
    target_repo_root: Path,
    repository: str,
    default_repo: bool,
    observed_branch_head: str | None = None,
) -> _AuthoringAdmission | None:
    """Admit a writer only if a qualified independent reviewer remains (#9739).

    Applies to every write-capable dispatch: an attach to an existing branch or
    worktree, and a new branch whose proposed scope is protected. Complete
    authorship (every branch-owned commit plus this
    writer, after substitution, aliases and ``--force-agent``) and protected
    scope come from ``record_cf_verdict.collect_branch_review_facts``, the
    calculation the verdict recorder uses. The check is structural (A2):
    catalog qualification, families, protected seats and the risk floor; it
    records reviewer availability as unknown. Authors are enumerated over
    ``review_base_sha..creation_sha`` for a new branch and
    ``review_base_sha..head_sha`` for an attach (A7): the review base is the
    one the recorder will read (:func:`_authoring_review_base`), never
    ``--base``; main-side commits are excluded from authorship while retaining
    the stale-base diff's protected scope (#9988). Every endpoint is observed on the canonical remote, frozen in
    the receipt and never resolved from a ref again. Fetches only to mirror
    remote state (M1); runs before any task record, archival, forwarding,
    rebase, worktree or provider. Returns None for read-only dispatches and
    for checkouts of a sibling repository (``--repo``, or a ``--cwd`` checkout
    whose git common directory is another repository's); a ``--repo`` whose
    ``--cwd`` belongs to a different repository is refused. Raises
    ``_AuthoringReviewRefused``, which no override flag bypasses.
    """
    if args.mode not in _WRITE_CAPABLE_MODES:
        return None
    from scripts.review.model_catalog import ModelCatalogError

    planned_risk = getattr(args, "authoring_review_risk", None)
    writer_model = args.model
    record: dict[str, Any] = {
        "checked_at": datetime.now(UTC).isoformat(),
        "check": "structural",
        "reviewer_availability": "unknown",
        "planned_risk": planned_risk,
        "incoming_agent": dispatch_agent,
        "incoming_model": writer_model,
    }
    review_plan = getattr(args, "authoring_review_plan", "cross_family")
    if review_plan == "red_team":
        record["review_plan"] = review_plan
    declared = _declared_owned_paths(getattr(args, "owned_path", None))
    if not declared:
        raise _AuthoringReviewRefused(
            AUTHORING_REVIEW_SCOPE_UNKNOWN,
            "write dispatch declares no --owned-path, so its review scope cannot be checked; "
            "pass every path this writer owns.",
            record,
        )
    cwd_only = (
        validated_cwd is not None and validated_worktree is None and worktree_arg != "auto" and not requested_branch
    )
    # Applicability follows the repository the writer's checkout belongs to,
    # never the --repo label alone: protected seats and risk floors describe the
    # default repository's own paths.
    if not default_repo and cwd_only:
        checkout_repo = _git_common_dir_identity(validated_cwd)
        if checkout_repo is None or checkout_repo != _git_common_dir_identity(target_repo_root):
            raise _AuthoringReviewRefused(
                AUTHORING_REVIEW_REPOSITORY_MISMATCH,
                f"--cwd is not a checkout of --repo {repository} (git common directory differs or is unknown); "
                "pass a --cwd worktree of that repository, or drop --repo for a checkout of this one.",
                record,
            )
    if not default_repo or (cwd_only and _is_other_repository(validated_cwd, target_repo_root)):
        record.update({"applicable": False, "reason": "sibling repository"})
        return None
    try:
        from scripts.review.record_cf_verdict import (
            FACTS_SCOPE_UNKNOWN,
            BranchFactsError,
            collect_branch_review_facts,
        )
        from scripts.review.security_paths import is_security_sensitive_change
    except (ImportError, ModelCatalogError) as exc:
        raise _AuthoringReviewRefused(
            AUTHORING_REVIEW_CATALOG_UNKNOWN, f"model catalog or reviewer resolver unavailable ({exc}).", record
        ) from exc

    checkout: Path | None = None
    if validated_worktree is not None:
        checkout = validated_worktree
    elif worktree_arg == "auto" or requested_branch:
        checkout = _auto_worktree_path(dispatch_agent, args.task_id, repo_root=target_repo_root)
    elif validated_cwd is not None:
        checkout = validated_cwd
    pinned_head = getattr(args, "pinned_head", None)
    if checkout is not None and checkout.exists():
        kind = "existing-worktree"
    elif requested_branch:
        kind, checkout = "existing-branch", None
    else:
        kind, checkout = "new-branch", None
    record.update({"target": kind, "branch": requested_branch})
    remote = _authoring_canonical_remote()
    pr = getattr(args, "pr", None)
    creation_ref: str | None = None
    creation_sha: str | None = None
    try:
        default_name, default_sha = _authoring_default_branch(remote)
        if kind == "existing-worktree":
            head_branch = _current_branch(checkout)
            if head_branch in (None, "HEAD"):
                raise _AuthoringObservationUnknown("the checkout has a detached HEAD, which names no PR")
        else:
            head_branch = requested_branch or _derive_worktree_branch(dispatch_agent, args.task_id)
        record["head_branch"] = head_branch
        # Authorship is enumerated from the base the verdict recorder will use,
        # never from --base, which only names where a new branch starts (A2, A7).
        review_base = _authoring_review_base(
            repository, pr=pr, head_branch=head_branch, default_branch=lambda: (default_name, default_sha)
        )
        record.update({"review_base": review_base.receipt(repository), "review_base_sha": review_base.sha})
        _authoring_require_commit(
            review_base.sha, fetch=lambda: _fetch_base(review_base.branch), what="the review base commit"
        )
        if kind == "new-branch":
            # The commit a new worktree starts at, frozen here and used as is by creation.
            base_arg = getattr(args, "base", None)
            creation_ref = _base_branch_name(base_arg) if base_arg else default_name
            creation_sha = _authoring_start_commit(remote, creation_ref, (default_name, default_sha))
            record.update({"creation_base": creation_ref, "creation_sha": creation_sha})
            _authoring_require_commit(
                creation_sha, fetch=lambda: _fetch_base(creation_ref), what="the creation commit", refresh=True
            )
            head = creation_sha
        else:
            head = _authoring_attach_head(
                kind=kind,
                checkout=checkout,
                branch=requested_branch,
                pinned_head=pinned_head,
                remote=remote,
                observed_branch_head=observed_branch_head,
            )
            _authoring_require_commit(
                head, fetch=lambda: _fetch_existing_branch(head_branch), what="the branch head commit"
            )
    except _AuthoringObservationUnknown as exc:
        raise _AuthoringReviewRefused(
            AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN, f"{exc}, so the branch's authors are unknown; retry.", record
        ) from exc

    # A stale main PR base still determines scope, but main's newer commits
    # are not branch authors (#9988). Non-main target branches keep their
    # existing enumeration. The rebase plan and result use this same exclusion,
    # never the caller's --base or the rebase target.
    authorship_exclude = default_sha if review_base.branch == default_name else None
    record["authorship_exclude_sha"] = authorship_exclude
    if authorship_exclude is not None:
        try:
            _authoring_require_commit(
                authorship_exclude, fetch=lambda: _fetch_base(default_name), what="the authorship exclusion commit"
            )
        except _AuthoringObservationUnknown as exc:
            raise _AuthoringReviewRefused(AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN, str(exc), record) from exc

    def collect(
        base_sha: str,
        head_sha: str,
        *,
        authorship_exclude_sha: str | None = authorship_exclude,
        unknown_history: Sequence[str] = (),
    ) -> Any:
        """This writer's branch facts over ``base_sha..head_sha``; a fact that cannot be established refuses."""
        try:
            return collect_branch_review_facts(
                repository=repository,
                repo_root=target_repo_root,
                base_tip_sha=base_sha,
                head_sha=head_sha,
                task_root=tasks_dir(),
                incoming_agent=dispatch_agent,
                incoming_model=writer_model,
                owned_paths=declared,
                subject_seats=tuple(getattr(args, "subject_seat", None) or ()),
                subject_families=tuple(getattr(args, "subject_family", None) or ()),
                authorship_exclude_sha=authorship_exclude_sha,
                unknown_history=unknown_history,
            )
        except BranchFactsError as exc:
            code = (
                AUTHORING_REVIEW_SCOPE_UNKNOWN
                if exc.code == FACTS_SCOPE_UNKNOWN
                else AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN
            )
            raise _AuthoringReviewRefused(code, f"{exc} (head {head_sha[:12]}).", record) from exc

    remote_history_head = None
    remote_history: tuple[str, ...] = ()
    if review_plan == "red_team" and kind != "new-branch":
        try:
            remote_history_head = observed_branch_head or _ls_remote_branch_sha(remote, head_branch, strict=True)
            if not remote_history_head:
                raise _AuthoringObservationUnknown("the continuation's remote head is unavailable")
            _authoring_require_commit(
                remote_history_head, fetch=lambda: _fetch_existing_branch(head_branch), what="the remote branch head"
            )
            if not _git_is_ancestor(remote_history_head, head):
                raise _AuthoringObservationUnknown("the remote branch head is not an ancestor of the continuation")
            listed = _run_git_stdout(target_repo_root, "rev-list", remote_history_head)
            if listed is None or listed[0] != 0:
                raise _AuthoringObservationUnknown("the remote branch history is unavailable")
            remote_history = tuple(listed[1].split())
        except _AuthoringObservationUnknown as exc:
            raise _AuthoringReviewRefused(AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN, str(exc), record) from exc
    facts = collect(review_base.sha, head, unknown_history=remote_history)
    suspect_history = facts.unknown_history
    # These facts can test downstream gates, but grant no historical allowance yet.
    facts = dataclasses.replace(
        facts,
        commits=tuple(
            dataclasses.replace(commit, source="suspect_historical", authorship=None)
            if commit.source == "unknown_historical"
            else commit
            for commit in facts.commits
        ),
    )
    record.update(facts.receipt())
    if kind == "existing-worktree" and requested_branch:
        try:
            remote_head = observed_branch_head or _ls_remote_branch_sha(remote, requested_branch, strict=True)
            if not remote_head:
                raise _AuthoringObservationUnknown("the continuation's remote head is unavailable")
            _authoring_require_commit(
                remote_head, fetch=lambda: _fetch_existing_branch(requested_branch), what="the remote branch head"
            )
            if remote_head != head and _git_is_ancestor(remote_head, head):
                local = collect(remote_head, head, authorship_exclude_sha=remote_head)
                if local.existing_families != {facts.incoming_family}:
                    raise _AuthoringReviewRefused(
                        AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN,
                        "local-only commits are not all by the incoming writer family; "
                        "reconcile the branch before continuation.",
                        record,
                    )
                record["local_continuation"] = {"remote_head_sha": remote_head, "head_sha": head}
        except _AuthoringObservationUnknown as exc:
            raise _AuthoringReviewRefused(AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN, str(exc), record) from exc
    protected = bool(
        facts.subject_seats
        or facts.subject_families
        or is_security_sensitive_change(facts.changed_paths, facts.scope_paths)
    )
    record["protected_scope"] = protected
    admission = _AuthoringAdmission(
        kind=kind,
        head_sha=head,
        checkout=checkout,
        branch=requested_branch,
        pinned_head=pinned_head,
        record=record,
        repository=repository,
        remote=remote,
        head_branch=head_branch,
        pr=pr,
        review_base=review_base,
        default_branch=default_name,
        creation_ref=creation_ref,
        creation_sha=creation_sha,
        collect=collect,
        planned_risk=planned_risk,
        suspect_history=suspect_history,
        history_remote_head_sha=remote_history_head,
    )
    if kind == "new-branch" and not protected:
        record["applicable"] = False
        return admission
    known_commits = tuple(commit for commit in facts.commits if commit.source != "suspect_historical")
    known_facts = dataclasses.replace(
        facts,
        commits=known_commits,
        existing_families=frozenset(commit.family for commit in known_commits if commit.family is not None),
    )
    _authoring_require_route(known_facts, planned_risk=planned_risk, record=record, at=head)
    if suspect_history:
        _authoring_require_route(facts, planned_risk=planned_risk, record=record, at=head, review_mode="red_team")
    return admission


def _authoring_require_route(
    facts: Any, *, planned_risk: str | None, record: dict[str, Any], at: str, review_mode: str = "cross_family"
) -> None:
    """Record the structural reviewer for ``facts``; refuse when none remains outside all authors (A2)."""
    from scripts.review.model_catalog import ModelCatalogError
    from scripts.review.record_cf_verdict import structural_review_route
    from scripts.review.security_paths import effective_review_risk

    risk = str(planned_risk or AUTHORING_REVIEW_DEFAULT_RISK).strip().casefold()
    # A claude reviewer would run as the account a review dispatch resolves and binds (#10630).
    from scripts.fleet import claude_account_lane

    claude_account = claude_account_lane.resolve_route_account(None, strict=False)
    try:
        resolution = structural_review_route(facts, risk=risk, review_mode=review_mode, claude_account=claude_account)
    except ModelCatalogError as exc:
        raise _AuthoringReviewRefused(
            AUTHORING_REVIEW_CATALOG_UNKNOWN, f"model catalog unavailable ({exc}).", record
        ) from exc
    record.update(
        {
            "applicable": True,
            "risk": effective_review_risk(risk, facts.changed_paths, facts.scope_paths),
            "reviewer": (
                {
                    "name": resolution.selected.name,
                    "model": resolution.selected.concrete_model,
                    "family": resolution.selected.family,
                    "route": resolution.selected.route,
                    **({"review_mode": "red_team"} if review_mode == "red_team" else {}),
                }
                if resolution.selected
                else None
            ),
        }
    )
    if resolution.selected is None:
        reason = resolution.fail_closed_reason or "no eligible formal reviewer in the catalog ladder"
        raise _AuthoringReviewRefused(
            AUTHORING_REVIEW_NO_ROUTE,
            f"write dispatch refused at {at[:12]}; authors={','.join(sorted(facts.existing_families)) or '(none)'}; "
            f"incoming={facts.incoming_family}; risk={record['risk']}; no qualified reviewer remains outside all "
            f"authors and protected seats ({reason}).",
            record,
        )


def _authoring_review_state_fields(args: argparse.Namespace, admission: _AuthoringAdmission | None) -> dict[str, Any]:
    """Task-record fields: the admission receipt, and explicit subjects the verdict recorder re-applies."""
    fields: dict[str, Any] = {}
    if admission is not None:
        if admission.record.get("review_plan") == "red_team":
            admission.record.update(
                {
                    "unknown_history": list(admission.suspect_history),
                    "assumed_model": None,
                    "history_remote_head_sha": admission.history_remote_head_sha,
                }
            )
            if admission.suspect_history and admission.record.get("reviewer"):
                admission.record["reviewer"]["review_mode"] = "red_team"
        fields[AUTHORING_REVIEW_STATE_KEY] = admission.record
    for flag, key in (("subject_seat", "review_subject_seats"), ("subject_family", "review_subject_families")):
        values = getattr(args, flag, None)
        if values:
            fields[key] = [values] if isinstance(values, str) else list(values)
    return fields


def _authoring_recheck_under_lock(
    admission: _AuthoringAdmission | None,
    *,
    readmit: Callable[[], _AuthoringAdmission | None],
) -> tuple[_AuthoringAdmission | None, _AuthoringReviewRefused | None]:
    """A3 and A7 under the worktree lock: the admission that now applies, and the refusal if a binding moved.

    A removal holding the lock may take the admitted checkout while dispatch
    waits (#8610); dispatch then creates a fresh worktree, so the observation
    is discarded and admission runs again in full for that target, freezing
    its own creation and review-base commits (becoming a new branch exempts
    nothing). Otherwise every frozen binding is observed again
    (:func:`_authoring_bindings_moved`). Raises ``_AuthoringReviewRefused``
    when the re-run refuses.
    """
    if (
        admission is not None
        and admission.kind == "existing-worktree"
        and admission.checkout is not None
        and not os.path.lexists(admission.checkout)
    ):
        return readmit(), None
    return admission, _authoring_bindings_moved(admission)


def _authoring_bindings_moved(admission: _AuthoringAdmission | None) -> _AuthoringReviewRefused | None:
    """A7: the refusal when an admitted endpoint differs before use; None when every binding is unchanged.

    Observed as at admission: an attached head (the checkout's commit, or the
    branch on the canonical remote), a new branch's start commit, and the
    review base with its branch and PR identity. An observation that cannot
    complete refuses as unknown authorship, never as a proven move. The base
    auto-rebase of a reused worktree runs after this and is not a move (A3).
    """
    if admission is None:
        return None
    default_branch = functools.cache(lambda: _authoring_default_branch(admission.remote))
    try:
        if admission.kind == "new-branch":
            assert admission.creation_ref is not None  # set for every new-branch admission
            current = _authoring_start_commit(admission.remote, admission.creation_ref, default_branch())
            moved = _authoring_drift(admission, "creation", current)
        else:
            current = _authoring_attach_head(
                kind=admission.kind,
                checkout=admission.checkout,
                branch=admission.branch,
                pinned_head=admission.pinned_head,
                remote=admission.remote,
            )
            moved = _authoring_drift(admission, "head", current)
            if not moved and admission.kind == "existing-worktree":
                # The checkout's branch names its PR and so its review base: a switch at
                # the same commit changes both (``HEAD`` when detached).
                assert admission.checkout is not None  # set for every existing-worktree admission
                moved = _authoring_branch_moved(admission, _current_branch(admission.checkout))
        if moved:
            return moved
        base = _authoring_review_base(
            admission.repository, pr=admission.pr, head_branch=admission.head_branch, default_branch=default_branch
        )
    except _AuthoringObservationUnknown as exc:
        return _AuthoringReviewRefused(
            AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN,
            f"{exc} on re-checking the admitted target, so the branch's authors are unknown; retry.",
            admission.record,
        )
    if base.binding() == admission.review_base.binding():
        return None
    return _authoring_drift(admission, "review_base", base.sha, current_base=base)


def _authoring_branch_moved(admission: _AuthoringAdmission, current: str | None) -> _AuthoringReviewRefused | None:
    """The ``TARGET_MOVED`` refusal when the checkout no longer has the branch admission read; None when it does."""
    if current == admission.head_branch:
        return None
    now = "a detached HEAD" if current == "HEAD" else (current or "an unreadable branch")
    record = {
        **admission.record,
        "binding": "head_branch",
        "admitted_branch": admission.head_branch,
        "current_branch": current,
    }
    return _AuthoringReviewRefused(
        AUTHORING_REVIEW_TARGET_MOVED,
        f"the checkout's branch moved after authoring-review admission (admitted {admission.head_branch}, now {now}), "
        "so its PR and review base are no longer the admitted ones; retry the dispatch so its authors are checked again.",
        record,
    )


def _git_is_ancestor(ancestor: str, descendant: str) -> bool:
    """Whether ``ancestor`` is an ancestor of ``descendant``; raises ``_AuthoringObservationUnknown`` on failure."""
    try:
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _AuthoringObservationUnknown("the ancestry check is unavailable") from exc
    if proc.returncode not in (0, 1):
        raise _AuthoringObservationUnknown("the ancestry check is unavailable")
    return proc.returncode == 0


def _authoring_drift(
    admission: _AuthoringAdmission, binding: str, current: str, *, current_base: _ReviewBase | None = None
) -> _AuthoringReviewRefused | None:
    """The structured ``TARGET_MOVED`` refusal (A6, M5) for one binding; None when it still holds."""
    if binding == "review_base":
        assert current_base is not None
        admitted = admission.review_base.sha
        what = f"the review base (admitted branch {admission.review_base.branch}, now {current_base.branch})"
    else:
        admitted = admission.creation_sha if binding == "creation" else admission.head_sha
        what = "the start commit of the new branch" if binding == "creation" else "the branch head"
        if current == admitted:
            return None
    assert admitted is not None
    record = {**admission.record, "binding": binding, "admitted_sha": admitted, "current_sha": current}
    if binding == "head":
        record["current_head_sha"] = current
    if current_base is not None:
        record["current_review_base"] = current_base.receipt(admission.repository)
    return _AuthoringReviewRefused(
        AUTHORING_REVIEW_TARGET_MOVED,
        f"{what} moved after authoring-review admission (admitted {admitted[:12]}, now {current[:12]}); "
        "retry the dispatch so its authors are checked again.",
        record,
    )



def _ls_remote_branch_sha(remote: str, branch: str, *, strict: bool = False) -> str | None:
    """Probe the SHA ``remote`` serves for ``branch`` without touching refs.

    ``git ls-remote`` answers from the remote directly, so a lagging mirror
    can be detected (#7522) while ``refs/remotes/origin/<branch>`` is written
    only by the canonical fetch. Best-effort: a spawn failure, timeout, or
    unresolved ref yields None. With ``strict``, read failures raise instead
    of being confused with an absent branch; diagnostics omit remote URLs.
    """
    try:
        proc = subprocess.run(
            ["git", "ls-remote", remote, f"refs/heads/{branch}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        if strict:
            raise _AuthoringObservationUnknown("canonical remote branch lookup (git ls-remote) timed out") from exc
        return None
    except OSError as exc:
        if strict:
            raise _AuthoringObservationUnknown("canonical remote branch lookup (git ls-remote) could not run") from exc
        return None
    if proc.returncode != 0:
        if strict:
            raise _AuthoringObservationUnknown(
                f"canonical remote branch lookup (git ls-remote) failed (exit {proc.returncode}); "
                "check network/authentication and remote access, then retry"
            )
        return None
    for line in (proc.stdout or "").splitlines():
        sha, sep, ref = line.partition("\t")
        if sep and ref.strip() == f"refs/heads/{branch}":
            return sha.strip() or None
    return None


def _resolve_sha(path: Path, ref: str = "HEAD") -> str | None:
    """Return the commit SHA at ``ref`` in ``path``, or None if unresolvable."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", ref],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    sha = (proc.stdout or "").strip()
    return sha or None


def _current_branch(worktree: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    branch = (proc.stdout or "").strip()
    return branch or None


def _base_branch_name(base_branch: str) -> str:
    """Return a PR base branch name without the remote prefix.

    ``origin/main`` and ``github/main`` both name the canonical ``main`` —
    the dispatch fetch lands every base into ``refs/remotes/origin/<name>``
    regardless of which remote served it (#7522).
    """
    stripped = base_branch.removeprefix("origin/")
    return stripped.removeprefix("github/")


def _declared_owned_paths(raw: object) -> tuple[str, ...] | None:
    """The task record's ``owned_paths`` (its ``--owned-path`` values), or None."""
    if not isinstance(raw, (list, tuple)):
        return None
    paths = tuple(str(item) for item in raw if isinstance(item, str) and item.strip())
    return paths or None


def _run_git_stdout(worktree: Path, *args: str) -> tuple[int, str] | None:
    """``(returncode, stdout)`` of a git command, or None when git could not run."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.returncode, proc.stdout or ""


def _auto_worktree_path(agent, task_id, *, repo_root=None):
    return (repo_root or _REPO_ROOT) / '.worktrees' / 'dispatch' / agent / task_id


def _derive_worktree_branch(agent, task_id):
    return f'{agent}/{task_id}'


_GITHUB_REMOTE_PATTERNS = (
    re.compile(r"^https?://(?:[^/@\s]+@)?github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^ssh://git@github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^git@github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^git://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
)

_CANONICAL_GITHUB_REPO = "learn-ukrainian/learn-ukrainian.github.io"

_GITCONFIG_REMOTE_SECTION_RE = re.compile(r'^\s*\[\s*remote\s+"([^"]+)"\s*\]')

_GITCONFIG_ANY_SECTION_RE = re.compile(r"^\s*\[")

_GITCONFIG_URL_RE = re.compile(r"^\s*url\s*=\s*(.+?)\s*$")


def _git_common_dir(root: Path) -> Path | None:
    """Return the git common dir for a checkout or linked worktree.

    Pure filesystem — never a git subprocess. The dispatch path stays
    independent of the ``subprocess.Popen`` stubs used by dispatch tests,
    same contract as :func:`_resolve_invocation_git_root`.
    """
    dot_git = root / ".git"
    try:
        if dot_git.is_dir():
            return dot_git
        if not dot_git.is_file():
            return None
        text = dot_git.read_text(encoding="utf-8", errors="replace").strip()
        if not text.startswith("gitdir:"):
            return None
        gitdir = Path(text.split(":", 1)[1].strip())
        if not gitdir.is_absolute():
            gitdir = (root / gitdir).resolve()
        commondir_file = gitdir / "commondir"
        if commondir_file.is_file():
            common = Path(commondir_file.read_text(encoding="utf-8", errors="replace").strip())
            if not common.is_absolute():
                common = (gitdir / common).resolve()
            return common
        return gitdir
    except OSError:
        return None


def _git_remote_urls(root: Path) -> dict[str, str]:
    """Map remote names to URLs from the checkout's common git config.

    Pure filesystem, same contract as :func:`_git_common_dir` — never a git
    subprocess, so dispatch-path logic stays independent of the
    ``subprocess.Popen`` stubs used by dispatch tests and hook environments.
    The first ``url`` entry wins for remotes configured with multiple URLs.
    """
    common = _git_common_dir(root)
    if common is None:
        return {}
    try:
        lines = (common / "config").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    urls: dict[str, str] = {}
    current_remote: str | None = None
    for line in lines:
        remote_section = _GITCONFIG_REMOTE_SECTION_RE.match(line)
        if remote_section:
            current_remote = remote_section.group(1)
            continue
        if _GITCONFIG_ANY_SECTION_RE.match(line):
            current_remote = None
            continue
        if current_remote is not None:
            url = _GITCONFIG_URL_RE.match(line)
            if url and current_remote not in urls:
                urls[current_remote] = url.group(1)
    return urls


def _resolve_canonical_remote_name(remote_urls: dict[str, str]) -> str | None:
    """Return the name of the remote that serves the canonical GitHub repo.

    Prefers a remote literally named ``github`` whose URL is the canonical
    ``owner/repo``; otherwise ``origin`` when origin itself is that GitHub
    URL. Any other layout stays unclassified (None) so the dispatch path
    keeps its origin-only behavior instead of inventing a remote (#7522).
    """
    github_url = remote_urls.get("github")
    if github_url and _parse_github_owner_repo(github_url) == _CANONICAL_GITHUB_REPO:
        return "github"
    origin_url = remote_urls.get("origin")
    if origin_url and _parse_github_owner_repo(origin_url) == _CANONICAL_GITHUB_REPO:
        return "origin"
    return None


def _parse_github_owner_repo(remote_url: str | None) -> str | None:
    """Return ``owner/repo`` for a GitHub remote URL, else None (fail closed)."""
    if not remote_url:
        return None
    text = remote_url.strip()
    for pattern in _GITHUB_REMOTE_PATTERNS:
        match = pattern.match(text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None



def _fetch_base(base):
    branch = _base_branch_name(base)
    remote = _authoring_canonical_remote()
    try:
        proc = subprocess.run(
            ['git', 'fetch', '--no-tags', remote,
             f'+refs/heads/{branch}:refs/remotes/origin/{branch}'],
            cwd=_REPO_ROOT, capture_output=True, text=True, check=False,
            env=_sanitized_git_env(), timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def _fetch_existing_branch(branch):
    if not _fetch_base(branch):
        raise ValueError('canonical branch fetch failed')


@contextlib.contextmanager
def repository_scope(repo):
    global _REPO_ROOT
    previous, _REPO_ROOT = _REPO_ROOT, repo
    try:
        yield
    finally:
        _REPO_ROOT = previous


def admit(args, agent, task_id, repo, info, worktree):
    # --branch starts a fresh v2 checkout at that branch; --cwd attaches.
    request = argparse.Namespace(**vars(args))
    request.task_id = task_id
    with repository_scope(repo):
        return _authoring_review_admission(
            request, dispatch_agent=agent, requested_harness=None,
            requested_branch=args.branch, worktree_arg='auto' if not args.cwd else None,
            validated_worktree=None if args.cwd else worktree,
            validated_cwd=worktree if args.cwd else None,
            target_repo_root=repo, repository=info['github'], default_repo=bool(info.get('default')),
        )


def recheck(args, admission, agent, task_id, repo, info, worktree):
    with repository_scope(repo):
        admission, refusal = _authoring_recheck_under_lock(
            admission, readmit=lambda: admit(args, agent, task_id, repo, info, worktree),
        )
        if refusal:
            raise refusal
        return admission


@contextlib.contextmanager
def locked_target(repo, worktree, *, dry_run=False):
    from scripts.orchestration import worktree_claims

    if dry_run:
        yield
        return
    common = _git_common_dir(repo)
    lock_dir = (common if common is not None else tasks_dir().parent) / worktree_claims.LOCK_DIR_NAME
    with worktree_claims.worktree_lock(worktree, lock_dir=lock_dir):
        yield
