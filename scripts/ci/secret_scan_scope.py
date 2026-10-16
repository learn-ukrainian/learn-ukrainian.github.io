"""Resolve bounded secret-scan ranges for landing events.

GitHub's TruffleHog action has built-in range handling for ``push`` and
``pull_request``, but not ``merge_group`` or ``schedule``.  This resolver
supplies explicit base/head values for merge-queue, main-push, and scheduled
runs, and deliberately selects the action's full-history path when a safe
landing range cannot be established.

A scheduled run has no ``before``/``after``.  Leaving both inputs empty makes
the pinned action scan every commit (``--since-commit '' --branch ''``) and
exit 183 when historical findings exist.  The schedule path therefore passes
a 48-hour lookback, or the tip commit when nothing landed in that window,
and never the same base and head.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

_SHA_RE = re.compile(r"[0-9a-fA-F]{40}\Z")
_ZERO_SHA = "0" * 40
_SCOPED_EVENTS = frozenset({"merge_group", "push"})
# The nightly cron is 03:30 UTC.  Forty-eight hours covers that interval plus
# one delayed or skipped night without re-scanning history that already failed
# the full scan.
SCHEDULE_LOOKBACK = timedelta(hours=48)
GIT_CAT_FILE_TIMEOUT_SECONDS = 10
GIT_IS_ANCESTOR_TIMEOUT_SECONDS = 30
GIT_REV_PARSE_TIMEOUT_SECONDS = 10
GIT_REV_LIST_TIMEOUT_SECONDS = 30


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


def _git_stdout(repo_root: Path, args: list[str], timeout: int) -> tuple[bool, str]:
    """Return ``(ok, stdout)``.  A timeout or non-zero exit is not an empty success."""

    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return False, ""
    if result.returncode != 0:
        return False, ""
    return True, result.stdout.strip()


def _sha(text: str) -> str | None:
    raw = text.strip().lower()
    if _SHA_RE.fullmatch(raw):
        return raw
    return None


def _schedule_scope(repo_root: Path, now: datetime) -> ScanScope:
    """Scan commits since the lookback, never an identical base and head.

    ``--since-commit`` is exclusive.  The base is the newest commit at or
    before the cutoff, so the scan starts with the first commit after it.
    ``opsec_range`` stays empty: the public-identifier lint keeps walking the
    whole checkout, which is what an unscoped schedule already did.
    """

    ok, head_text = _git_stdout(repo_root, ["rev-parse", "HEAD"], GIT_REV_PARSE_TIMEOUT_SECONDS)
    head = _sha(head_text) if ok else None
    if head is None:
        return _full_scan_scope("unresolvable-head-sha")

    cutoff = (now - SCHEDULE_LOOKBACK).strftime("%Y-%m-%dT%H:%M:%SZ")
    listed, base_text = _git_stdout(
        repo_root,
        ["rev-list", "-n", "1", f"--before={cutoff}", "HEAD"],
        GIT_REV_LIST_TIMEOUT_SECONDS,
    )
    base = _sha(base_text) if listed else None
    parent_ok, parent_text = _git_stdout(
        repo_root,
        ["rev-parse", "--verify", "HEAD^"],
        GIT_REV_PARSE_TIMEOUT_SECONDS,
    )
    parent = _sha(parent_text) if parent_ok else None

    if listed and base and base != head:
        return ScanScope(base, head, "", "schedule", "lookback")
    if not listed and parent and parent != head:
        # The lookback could not be resolved.  Scan the tip rather than every
        # commit: an empty pair is what made the nightly job exit 183.
        return ScanScope(parent, head, "", "schedule", "lookback-unresolved")
    if parent and parent != head and base == head:
        # Nothing landed inside the window.  The tip commit is still a real,
        # non-identical range, and it does not reopen older history.
        return ScanScope(parent, head, "", "schedule", "tip-commit")
    # Every commit is inside the window, or this is the root commit.  An empty
    # base with this head scans that branch and is not an identical pair.
    return ScanScope("", head, "", "schedule", "branch-history")


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


def resolve_scan_scope(
    event_name: str,
    *,
    merge_group_base_sha: str = "",
    merge_group_head_sha: str = "",
    push_before_sha: str = "",
    push_after_sha: str = "",
    repo_root: Path | None = None,
    now: datetime | None = None,
) -> ScanScope:
    """Return a validated landing range or an explicit full-scan fallback.

    ``merge_group.base_sha`` is the queue branch's parent and
    ``merge_group.head_sha`` is the merge-group commit.  For a main push, the
    event's ``before`` and ``after`` SHAs define the pushed range.  Both forms
    are accepted only when the commits exist locally and the base is an
    ancestor of the head; this rejects empty, first-run, force-push, and
    malformed ranges without ever turning a scan into a skip.

    ``schedule`` uses ``now`` (UTC) minus :data:`SCHEDULE_LOOKBACK`.  Callers
    omit ``now`` to read the clock.
    """

    event = event_name.strip()
    root = repo_root or Path.cwd()
    if event == "schedule":
        moment = now if now is not None else datetime.now(UTC)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        return _schedule_scope(root, moment)
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
    scope = resolve_scan_scope(
        os.environ.get("EVENT_NAME", ""),
        merge_group_base_sha=os.environ.get("MERGE_GROUP_BASE_SHA", ""),
        merge_group_head_sha=os.environ.get("MERGE_GROUP_HEAD_SHA", ""),
        push_before_sha=os.environ.get("PUSH_BEFORE_SHA", ""),
        push_after_sha=os.environ.get("PUSH_AFTER_SHA", ""),
    )
    output = os.environ.get("GITHUB_OUTPUT")
    _write_outputs(scope, Path(output) if output else None)
    print(f"secret-scan-scope: mode={scope.mode} reason={scope.reason}")
    if scope.opsec_range:
        print(f"secret-scan-scope: range={scope.opsec_range}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
