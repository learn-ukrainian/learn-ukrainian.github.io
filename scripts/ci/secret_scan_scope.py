"""Resolve bounded secret-scan ranges for landing events.

GitHub's TruffleHog action has built-in range handling for ``push`` and
``pull_request``, but not ``merge_group``.  This resolver supplies explicit
base/head values for merge-queue and main-push runs, and deliberately selects
the action's full-history path when a safe range cannot be established.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_SHA_RE = re.compile(r"[0-9a-fA-F]{40}\Z")
_ZERO_SHA = "0" * 40
_SCOPED_EVENTS = frozenset({"merge_group", "push"})


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
        )
    except OSError:
        return False
    return result.returncode == 0


def _is_ancestor(repo_root: Path, base_sha: str, head_sha: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_sha, head_sha],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
    except OSError:
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
) -> ScanScope:
    """Return a validated landing range or an explicit full-scan fallback.

    ``merge_group.base_sha`` is the queue branch's parent and
    ``merge_group.head_sha`` is the merge-group commit.  For a main push, the
    event's ``before`` and ``after`` SHAs define the pushed range.  Both forms
    are accepted only when the commits exist locally and the base is an
    ancestor of the head; this rejects empty, first-run, force-push, and
    malformed ranges without ever turning a scan into a skip.
    """

    event = event_name.strip()
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

    root = repo_root or Path.cwd()
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
