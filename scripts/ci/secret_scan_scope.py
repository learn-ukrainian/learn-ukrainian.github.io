"""Resolve bounded secret-scan ranges for landing and manual-dispatch events.

GitHub's TruffleHog action has built-in range handling for ``push`` and
``pull_request``, but not ``merge_group``, ``schedule`` or ``workflow_dispatch``.
This resolver supplies explicit base/head values for those events and main
pushes. Invalid landing ranges select the action's full-history path.
Invalid manual-dispatch ranges raise instead of falling back to a full scan.
Only the explicit ``full-history-audit`` dispatch input requests an audit.

A scheduled run has no ``before``/``after``.  Leaving both inputs empty makes
the pinned action scan every commit (``--since-commit '' --branch ''``) and
exit 183 when historical findings exist.  The schedule path therefore walks
a fixed first-parent ancestry window, or the whole branch when history is
shorter, and never the same base and head.  Commit dates are not consulted.
A git failure exits non-zero instead of narrowing that window.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_SHA_RE = re.compile(r"[0-9a-fA-F]{40}\Z")
_ZERO_SHA = "0" * 40
_SCOPED_EVENTS = frozenset({"merge_group", "push"})
# Ancestry depth for the nightly schedule (cron 03:30 UTC).  ``base..HEAD``
# already includes every commit reachable from HEAD and not from base, so
# merges and side branches need no extra walk and no commit date.
#
# Sized from this repository's first-parent history, measured 2026-10-16
# 18:09:05 UTC at 756599a9a492:
#   git rev-list --count --first-parent --since=2026-10-14T18:05:00Z HEAD → 73
#   the same count over the prior 7 days → 244
#   peak 48-hour first-parent count across the prior 90 days → 156
# 400 is more than twice that peak, so one nightly run still covers well
# over 48 hours at the observed rate.  A longer outage can leave older
# commits unscanned; recovering that range is a manual full scan, and that
# gap is a follow-up, not this window.
SCHEDULE_FIRST_PARENT_STEPS = 400
GIT_CAT_FILE_TIMEOUT_SECONDS = 10
GIT_IS_ANCESTOR_TIMEOUT_SECONDS = 30
GIT_REV_LIST_TIMEOUT_SECONDS = 30


class SecretScanScopeError(RuntimeError):
    """A scheduled or dispatched range could not be resolved safely."""


@dataclass(frozen=True, slots=True)
class ScanScope:
    """Values consumed by the TruffleHog action and the OPSEC linter."""

    trufflehog_base: str
    trufflehog_head: str
    opsec_range: str
    mode: str
    reason: str


def _full_scan_scope(reason: str) -> ScanScope:
    """Keep the current full scan, including for an empty push payload."""

    # A non-empty head keeps the action in its explicit BASE/HEAD path.  An
    # empty BASE then means the same full-history scan as the action's current
    # merge_group fallback, while avoiding its push ``commits == []`` early
    # exit.
    return ScanScope(
        trufflehog_base="",
        trufflehog_head="HEAD",
        opsec_range="",
        mode="full-fallback",
        reason=reason,
    )


def _normalize_sha(value: str, label: str) -> tuple[str | None, str | None]:
    raw = value.strip()
    if not raw:
        return None, f"missing-{label}-sha"
    if raw == _ZERO_SHA:
        return None, f"zero-{label}-sha"
    if not _SHA_RE.fullmatch(raw):
        return None, f"invalid-{label}-sha"
    return raw.lower(), None


def _commit_exists(repo_root: Path, sha: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            timeout=GIT_CAT_FILE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _sha(text: str) -> str | None:
    raw = text.strip().lower()
    if _SHA_RE.fullmatch(raw):
        return raw
    return None


def _require_git_stdout(repo_root: Path, args: list[str], timeout: int) -> str:
    """Return git stdout, or raise so the scan cannot shrink quietly."""

    command = " ".join(args)
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SecretScanScopeError(f"git {command} timed out after {timeout}s; refusing to narrow the scan") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise SecretScanScopeError(f"git {command} failed; refusing to narrow the scan") from exc
    if result.returncode != 0:
        detail = (result.stderr or "").strip().splitlines()
        suffix = f": {detail[0][:200]}" if detail else ""
        raise SecretScanScopeError(f"git {command} exited {result.returncode}{suffix}; refusing to narrow the scan")
    return result.stdout


def _schedule_scope(repo_root: Path, head_ref: str = "HEAD") -> ScanScope:
    """Scan the last N first-parent steps, or the whole branch if history is shorter.

    The base is ``head_ref~N`` along ``--first-parent``. ``base..head_ref`` includes
    every commit reachable from head_ref and not from that base, merges and side
    branches included.  No commit date and no wall clock is involved.
    ``opsec_range`` stays empty: the public-identifier lint keeps walking the
    whole checkout, which is what an unscoped schedule already did.

    History shorter than N steps cannot name that ancestor.  An empty base
    with the resolved head then scans the whole branch, including the root.
    A git failure raises :class:`SecretScanScopeError` instead of falling
    back to a narrower range.  The returned base and head are never equal.
    """

    depth = SCHEDULE_FIRST_PARENT_STEPS
    text = _require_git_stdout(
        repo_root,
        ["rev-list", "--first-parent", f"--max-count={depth + 1}", head_ref],
        GIT_REV_LIST_TIMEOUT_SECONDS,
    )
    shas: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        sha = _sha(line)
        if sha is None:
            raise SecretScanScopeError("git rev-list returned a non-commit; refusing to narrow the scheduled scan")
        shas.append(sha)
    if not shas:
        raise SecretScanScopeError("git rev-list returned no commits; refusing to narrow the scheduled scan")

    head = shas[0]
    if len(shas) <= depth:
        return ScanScope("", head, "", "schedule", "branch-history")

    base = shas[depth]
    if base == head:
        raise SecretScanScopeError("refusing an identical scheduled base and head")
    return ScanScope(base, head, "", "schedule", "ancestry-window")


def _is_ancestor(repo_root: Path, base_sha: str, head_sha: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_sha, head_sha],
            cwd=repo_root,
            capture_output=True,
            check=False,
            timeout=GIT_IS_ANCESTOR_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _dispatch_scope(repo_root: Path, raw_head: str, dispatch_ref: str, default_branch_ref: str) -> ScanScope:
    """Resolve a dispatch against the default branch; incomplete history is an error."""

    head, error = _normalize_sha(raw_head, "dispatch-head")
    if error or head is None:
        raise SecretScanScopeError(error or "invalid-dispatch-head-sha")
    if not _commit_exists(repo_root, head):
        raise SecretScanScopeError("unresolvable-dispatch-head-sha")
    if not dispatch_ref or not default_branch_ref.startswith("refs/heads/"):
        raise SecretScanScopeError("missing-or-invalid-dispatch-ref-or-default-branch-ref")
    for ref in (dispatch_ref, default_branch_ref):
        _require_git_stdout(repo_root, ["check-ref-format", ref], GIT_CAT_FILE_TIMEOUT_SECONDS)
    shallow = _require_git_stdout(
        repo_root,
        ["rev-parse", "--is-shallow-repository"],
        GIT_CAT_FILE_TIMEOUT_SECONDS,
    ).strip()
    if shallow != "false":
        raise SecretScanScopeError("incomplete-dispatch-history; refusing to narrow the scan")

    default_remote = "refs/remotes/origin/" + default_branch_ref.removeprefix("refs/heads/")
    base = _sha(
        _require_git_stdout(
            repo_root,
            ["merge-base", default_remote, head],
            GIT_IS_ANCESTOR_TIMEOUT_SECONDS,
        )
    )
    if base is None or not _commit_exists(repo_root, base):
        raise SecretScanScopeError("unresolvable-dispatch-base-sha")
    if not _is_ancestor(repo_root, base, head):
        raise SecretScanScopeError("dispatch-base-not-ancestor")
    if base == head or dispatch_ref == default_branch_ref:
        return _schedule_scope(repo_root, head)
    return ScanScope(base, head, f"{base}..{head}", "scoped", "validated-range")


def resolve_scan_scope(
    event_name: str,
    *,
    merge_group_base_sha: str = "",
    merge_group_head_sha: str = "",
    push_before_sha: str = "",
    push_after_sha: str = "",
    dispatch_head_sha: str = "",
    dispatch_ref: str = "",
    default_branch_ref: str = "",
    dispatch_scan_mode: str = "",
    repo_root: Path | None = None,
) -> ScanScope:
    """Return a validated landing range or an explicit full-scan fallback.

    ``merge_group.base_sha`` is the queue branch's parent and
    ``merge_group.head_sha`` is the merge-group commit.  For a main push, the
    event's ``before`` and ``after`` SHAs define the pushed range.  Both forms
    are accepted only when the commits exist locally and the base is an
    ancestor of the head; this rejects empty, first-run, force-push, and
    malformed ranges without ever turning a scan into a skip.

    ``schedule`` walks :data:`SCHEDULE_FIRST_PARENT_STEPS` first-parent steps.
    Commit dates are not used.  A git failure raises
    :class:`SecretScanScopeError` and the CLI exits non-zero.

    ``workflow_dispatch`` scans the default-branch merge-base through the
    dispatched SHA. Main refs and heads already on main reuse the schedule
    window, anchored to that SHA. Missing inputs or ancestry raise an error.
    Only ``dispatch_scan_mode=full-history-audit`` selects full history with
    ``mode=audit``. An absent or empty mode stays bounded; invalid modes raise.
    """

    event = event_name.strip()
    root = repo_root or Path.cwd()
    if event == "schedule":
        return _schedule_scope(root)
    if event == "workflow_dispatch":
        if dispatch_scan_mode == "full-history-audit":
            return ScanScope("", "HEAD", "", "audit", "explicit-full-history-audit")
        if dispatch_scan_mode not in ("", "bounded"):
            raise SecretScanScopeError("invalid-dispatch-scan-mode")
        return _dispatch_scope(root, dispatch_head_sha, dispatch_ref, default_branch_ref)
    if event not in _SCOPED_EVENTS:
        return ScanScope("", "", "", "unchanged", "event-not-scoped")

    if event == "merge_group":
        raw_base, raw_head = merge_group_base_sha, merge_group_head_sha
    else:
        raw_base, raw_head = push_before_sha, push_after_sha

    base_sha, error = _normalize_sha(raw_base, "base")
    if error:
        return _full_scan_scope(error)
    head_sha, error = _normalize_sha(raw_head, "head")
    if error:
        return _full_scan_scope(error)
    if base_sha is None or head_sha is None:
        return _full_scan_scope("invalid-range")

    if base_sha == head_sha:
        return _full_scan_scope("empty-range")

    if not _commit_exists(root, base_sha):
        return _full_scan_scope("unresolvable-base-sha")
    if not _commit_exists(root, head_sha):
        return _full_scan_scope("unresolvable-head-sha")
    if not _is_ancestor(root, base_sha, head_sha):
        return _full_scan_scope("base-not-ancestor")

    return ScanScope(
        trufflehog_base=base_sha,
        trufflehog_head=head_sha,
        opsec_range=f"{base_sha}..{head_sha}",
        mode="scoped",
        reason="validated-range",
    )


def _write_outputs(scope: ScanScope, output_path: Path | None) -> None:
    lines = (
        f"trufflehog_base={scope.trufflehog_base}",
        f"trufflehog_head={scope.trufflehog_head}",
        f"opsec_range={scope.opsec_range}",
        f"mode={scope.mode}",
        f"reason={scope.reason}",
    )
    if output_path is None:
        for line in lines:
            print(line)
        return
    with output_path.open("a", encoding="utf-8") as output:
        for line in lines:
            output.write(f"{line}\n")


def main() -> int:
    try:
        scope = resolve_scan_scope(
            os.environ.get("EVENT_NAME", ""),
            merge_group_base_sha=os.environ.get("MERGE_GROUP_BASE_SHA", ""),
            merge_group_head_sha=os.environ.get("MERGE_GROUP_HEAD_SHA", ""),
            push_before_sha=os.environ.get("PUSH_BEFORE_SHA", ""),
            push_after_sha=os.environ.get("PUSH_AFTER_SHA", ""),
            dispatch_head_sha=os.environ.get("DISPATCH_HEAD_SHA", ""),
            dispatch_ref=os.environ.get("DISPATCH_REF", ""),
            default_branch_ref=os.environ.get("DEFAULT_BRANCH_REF", ""),
            dispatch_scan_mode=os.environ.get("DISPATCH_SCAN_MODE", ""),
        )
    except SecretScanScopeError as exc:
        print(f"secret-scan-scope: {exc}", file=sys.stderr)
        return 1
    output = os.environ.get("GITHUB_OUTPUT")
    _write_outputs(scope, Path(output) if output else None)
    print(f"secret-scan-scope: mode={scope.mode} reason={scope.reason}")
    if scope.opsec_range:
        print(f"secret-scan-scope: range={scope.opsec_range}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
