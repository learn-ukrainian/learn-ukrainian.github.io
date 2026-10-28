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
A scheduled run widens the window to the last successfully scanned head.
Missing or invalid coverage and git failures exit non-zero.

``materialize`` prepares a blobless checkout for the scan; see
:func:`materialize_scan_objects`.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from scripts.ci.check_large_files import prefetch_missing_blobs
from scripts.common import github_client

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
# over 48 hours at the observed rate. Recovery widens this window when the
# last successful scan is older, so outages cannot silently lose coverage.
SCHEDULE_FIRST_PARENT_STEPS = 400
GIT_CAT_FILE_TIMEOUT_SECONDS = 10
GIT_IS_ANCESTOR_TIMEOUT_SECONDS = 30
GIT_REV_LIST_TIMEOUT_SECONDS = 30
# Listing, fetching and re-reading a whole history's blobs; the job's own
# timeout-minutes is the real bound.
GIT_SCAN_OBJECTS_TIMEOUT_SECONDS = 3600
# Blobs per fetch request, the batch size `git backfill` uses.
_FETCH_BATCH = 50_000
_COVERAGE_RECOVERY = "coverage unknown; run full-history-audit on the default branch to establish coverage"
_COVERAGE_ARTIFACT = "secret-scan-covered-head-v1"


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


def _schedule_recovery_scope(repo_root: Path, last_scanned_head: str) -> ScanScope:
    scope = _schedule_scope(repo_root)
    record, error = _normalize_sha(last_scanned_head, "last-scanned-head")
    if error or record is None or not _commit_exists(repo_root, record):
        raise SecretScanScopeError(_COVERAGE_RECOVERY)
    shallow = _require_git_stdout(
        repo_root, ["rev-parse", "--is-shallow-repository"], GIT_CAT_FILE_TIMEOUT_SECONDS
    ).strip()
    if shallow != "false" or not _is_ancestor(repo_root, record, scope.trufflehog_head):
        raise SecretScanScopeError(_COVERAGE_RECOVERY)
    if not scope.trufflehog_base:
        return scope
    # An older record covers everything before it; everything after it must
    # be scanned now. A newer record keeps the normal overlapping window.
    common = _sha(
        _require_git_stdout(repo_root, ["merge-base", scope.trufflehog_base, record], GIT_IS_ANCESTOR_TIMEOUT_SECONDS)
    )
    if common is None:
        raise SecretScanScopeError(_COVERAGE_RECOVERY)
    if common == scope.trufflehog_base:
        return scope
    return ScanScope(record, scope.trufflehog_head, "", "schedule", "coverage-recovery")


def _github_json(endpoint: str) -> dict:
    """Read metadata only, never download or extract an artifact archive."""
    try:
        result = github_client.run(
            ["gh", "api", endpoint], fresh=True, allow_stale=False, capture_output=True, text=True, check=True, timeout=30
        )
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            raise ValueError("invalid response")
        return payload
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise SecretScanScopeError(_COVERAGE_RECOVERY) from exc


def _last_scanned_head(repository: str, repository_id: str, default_branch_ref: str) -> str:
    """Use GitHub's immutable artifact run SHA, checking branch and producer.

    Only successful scans publish this artifact. Untrusted PR/fork artifacts
    are ignored. A bounded metadata search that finds no record fails closed.
    """
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository) or not repository_id.isdecimal():
        raise SecretScanScopeError(_COVERAGE_RECOVERY)
    if not default_branch_ref.startswith("refs/heads/"):
        raise SecretScanScopeError(_COVERAGE_RECOVERY)
    branch = default_branch_ref.removeprefix("refs/heads/")
    prefix = f"repos/{repository}/actions"
    try:
        artifacts = _github_json(f"{prefix}/artifacts?name={_COVERAGE_ARTIFACT}&per_page=100")["artifacts"]
        for artifact in sorted(artifacts, key=lambda item: int(item["id"]), reverse=True):
            run = artifact["workflow_run"]
            if (
                artifact["name"] != _COVERAGE_ARTIFACT
                or artifact["expired"]
                or str(run["repository_id"]) != repository_id
                or str(run["head_repository_id"]) != repository_id
                or run["head_branch"] != branch
            ):
                continue
            run_id = int(run["id"])
            producer = _github_json(f"{prefix}/runs/{run_id}")
            if (
                producer["path"] != ".github/workflows/ci.yml"
                or producer["event"] not in {"schedule", "workflow_dispatch"}
                or producer["head_branch"] != branch
                or producer["head_sha"] != run["head_sha"]
            ):
                continue
            head = _sha(run["head_sha"]) if isinstance(run["head_sha"], str) else None
            if head:
                return head
    except (KeyError, TypeError, ValueError) as exc:
        raise SecretScanScopeError(_COVERAGE_RECOVERY) from exc
    raise SecretScanScopeError(_COVERAGE_RECOVERY)


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
    schedule_last_scanned_head: str = "",
    repo_root: Path | None = None,
) -> ScanScope:
    """Return a validated landing range or an explicit full-scan fallback.

    ``merge_group.base_sha`` is the queue branch's parent and
    ``merge_group.head_sha`` is the merge-group commit.  For a main push, the
    event's ``before`` and ``after`` SHAs define the pushed range.  Both forms
    are accepted only when the commits exist locally and the base is an
    ancestor of the head; this rejects empty, first-run, force-push, and
    malformed ranges without ever turning a scan into a skip.

    ``schedule`` walks at least :data:`SCHEDULE_FIRST_PARENT_STEPS` first-parent
    steps, widening to ``schedule_last_scanned_head`` when older. Missing or
    invalid coverage fails visibly. Commit dates are not used. A git failure raises
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
        return _schedule_recovery_scope(root, schedule_last_scanned_head)
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


def _trufflehog_log_args(head: str, excluded: str) -> list[str]:
    """The ``git log`` TruffleHog 3.99.0 runs for a scan (``gitparse.prepGitArgs``).

    A scan without a base skips deletions (``--diff-filter=AM``); with no head
    TruffleHog walks every ref.
    """
    args = ["log", "--patch", "--date=iso-strict", "--pretty=fuller", "--notes"]
    if not excluded:
        args.append("--diff-filter=AM")
    args += ["--full-history", head or "--all"]
    if excluded:
        args.append(f"^{excluded}")
    return args


def _range_blobs(repo_root: Path, head: str, excluded: str) -> list[str]:
    """Blobs on either side of every diff ``git log --patch`` prints for the range."""

    text = _require_git_stdout(
        repo_root,
        ["log", "--format=", "--raw", "-r", "--no-renames", "--no-abbrev", head or "--all", f"^{excluded}"],
        GIT_SCAN_OBJECTS_TIMEOUT_SECONDS,
    )
    blobs: dict[str, None] = {}
    for line in text.splitlines():
        if not line.startswith(":"):
            continue
        old_mode, new_mode, old_sha, new_sha = line[1:].split("\t", 1)[0].split()[:4]
        for mode, sha in ((old_mode, old_sha), (new_mode, new_sha)):
            # 160000 is a submodule commit, which the diff names but never reads.
            if mode != "160000" and sha != _ZERO_SHA:
                blobs[sha] = None
    return list(blobs)


def materialize_scan_objects(base: str, head: str, repo_root: Path | None = None) -> str:
    """Download every blob the TruffleHog scan reads, then prove each one is local.

    CI checks out a blobless partial clone and TruffleHog scans it in place
    (``--trust-local-git-config``), because its default ``git clone`` of a
    partial clone fails. In place, a blob that is missing and cannot be fetched
    makes TruffleHog exit 0 having scanned nothing. This fetches, in batches,
    the blobs on both sides of every diff in the range (every blob of the
    history without a base), then re-runs TruffleHog's own ``git log`` with lazy
    fetching disabled; a missing object raises. TruffleHog scans
    ``head ^merge-base(head, base)`` and go-git may pick any of several merge
    bases, so each one is covered. A full clone holds every blob and is left as is.
    """

    root = repo_root or Path.cwd()
    head, base = head.strip(), base.strip()
    # The marks git sets on a partial clone (git 2.53 writes only the promisor remote).
    marks = subprocess.run(
        ["git", "config", "--get-regexp", r"^(remote\..*\.promisor|extensions\.partialclone)$"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_CAT_FILE_TIMEOUT_SECONDS,
    ).stdout.split("\n")
    if not any(
        value.lower() not in ("", "false", "no", "off", "0") for _, _, value in (line.partition(" ") for line in marks)
    ):
        return "full clone; every object is local"
    if base and head:
        merge_bases = _require_git_stdout(
            root, ["merge-base", "--all", head, base], GIT_IS_ANCESTOR_TIMEOUT_SECONDS
        ).split()
        if not merge_bases:
            raise SecretScanScopeError(f"no merge base of {head} and {base}; refusing to scan an unknown range")
    else:
        merge_bases = [base]

    candidates: dict[str, None] = {}
    for excluded in merge_bases:
        if excluded:
            candidates.update(dict.fromkeys(_range_blobs(root, head, excluded)))
        else:
            listed = _require_git_stdout(
                root, ["rev-list", "--objects", "--missing=print", head or "--all"], GIT_SCAN_OBJECTS_TIMEOUT_SECONDS
            )
            candidates.update(dict.fromkeys(line[1:] for line in listed.splitlines() if line.startswith("?")))
    wanted = list(candidates)
    fetched = 0
    try:
        for start in range(0, len(wanted), _FETCH_BATCH):
            fetched += prefetch_missing_blobs(
                wanted[start : start + _FETCH_BATCH], root, timeout=GIT_SCAN_OBJECTS_TIMEOUT_SECONDS
            )
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        raise SecretScanScopeError(f"blob prefetch failed; refusing to scan a partial range: {exc}") from exc

    no_lazy_fetch = {**os.environ, "GIT_NO_LAZY_FETCH": "1"}
    commits = 0
    for excluded in merge_bases:
        try:
            result = subprocess.run(
                ["git", *_trufflehog_log_args(head, excluded)],
                cwd=root,
                env=no_lazy_fetch,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=GIT_SCAN_OBJECTS_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise SecretScanScopeError("git log --patch over the scan range failed; refusing to scan") from exc
        if result.returncode != 0:
            detail = (result.stderr or "").strip().splitlines()
            suffix = f": {detail[-1][:200]}" if detail else ""
            raise SecretScanScopeError(f"scan range is not fully local{suffix}; refusing to scan")
        count = ["rev-list", "--count", head or "--all"] + ([f"^{excluded}"] if excluded else [])
        commits = max(commits, int(_require_git_stdout(root, count, GIT_REV_LIST_TIMEOUT_SECONDS).strip()))
    return f"commits={commits} merge_bases={len(merge_bases)} blobs_listed={len(wanted)} blobs_fetched={fetched}"


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


def _materialize_main() -> int:
    try:
        summary = materialize_scan_objects(os.environ.get("SCAN_BASE", ""), os.environ.get("SCAN_HEAD", ""))
    except SecretScanScopeError as exc:
        print(f"secret-scan-objects: {exc}", file=sys.stderr)
        return 1
    print(f"secret-scan-objects: {summary}")
    return 0


def main(argv: list[str] | tuple[str, ...] = ()) -> int:
    if list(argv) == ["materialize"]:
        return _materialize_main()
    if argv:
        print(f"secret-scan-scope: unknown arguments {list(argv)}", file=sys.stderr)
        return 2
    try:
        last_scanned_head = ""
        if os.environ.get("EVENT_NAME", "").strip() == "schedule":
            last_scanned_head = _last_scanned_head(
                os.environ.get("GITHUB_REPOSITORY", ""),
                os.environ.get("GITHUB_REPOSITORY_ID", ""),
                os.environ.get("DEFAULT_BRANCH_REF", ""),
            )
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
            schedule_last_scanned_head=last_scanned_head,
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
    raise SystemExit(main(sys.argv[1:]))
