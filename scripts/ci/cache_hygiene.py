#!/usr/bin/env python3
"""Prune dead GitHub Actions cache entries so the repository stays under 10 GB (#9101).

Two entry kinds are pruned; every other entry is left alone.

- ``codeql-trap-<cache version>-<cli version>-<language>-<commit sha>``:
  CodeQL default setup saves one TRAP cache (~247 MB) per main commit. A pull
  request run restores the exact key for its ``pull_request.base.sha`` and
  falls back to the newest entry with the family prefix (the key without its
  commit sha); see ``src/trap-caching.ts`` in github/codeql-action. On
  ``refs/heads/main`` the newest entry per family (by ``created_at``) and
  every entry whose commit is the base of an open pull request are kept; the
  rest are deleted. Entries with the full TRAP key shape on any other ref are
  deleted. Keys that do not match the shape are left alone.
- ``setup-uv-<...>-<lock hash>`` on ``refs/heads/main``: the entry for the
  current ``requirements-lock.txt`` and the newest entry per family are kept.
  A superseded entry is deleted only once it has not been read for
  ``--uv-grace-hours`` (default 24), so PRs still based on the previous lock
  keep restoring it for a day. ``last_accessed_at`` is never earlier than
  ``created_at``, so this is at least as conservative as an age check.

Nothing is deleted unless both listings are complete: every cache entry
(``total_count`` checked, stable ``created_at`` order) and every open pull
request (``totalCount`` checked). Any mismatch or API error aborts the run.

The default is a dry run that prints the plan. ``--apply`` deletes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

MAIN_REF = "refs/heads/main"
PER_PAGE = 100
MAX_PAGES = 50
GH_TIMEOUT_SECONDS = 60
DEFAULT_UV_GRACE_HOURS = 24.0

# codeql-action cachePrefix() + cacheKey(): "codeql-trap-" CACHE_VERSION "-"
# CLI version "-" language "-" commit sha.
CODEQL_TRAP_RE = re.compile(r"^(codeql-trap-\d+-\d+\.\d+\.\d+(?:\+[0-9A-Za-z.]+)?-[a-z][a-z0-9_]*-)([0-9a-f]{40})$")
SETUP_UV_RE = re.compile(r"^(setup-uv-.+-)([0-9a-f]{64})$")
COMMIT_SHA_RE = re.compile(r"[0-9a-f]{40}")

GhApi = Callable[[list[str]], str]

OPEN_PR_BASES_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: OPEN, first: 100, after: $cursor) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { number baseRefOid }
    }
  }
}
"""

KEEP_TRAP_NEWEST = "newest TRAP per family"
KEEP_TRAP_PR_BASE = "TRAP at an open PR base"
KEEP_UV_CURRENT = "uv for the current lock"
KEEP_UV_NEWEST = "newest uv per family"
KEEP_UV_GRACE = "uv read within grace"


class IncompleteListingError(RuntimeError):
    """A listing could not be proven complete, so nothing may be deleted."""


@dataclass(frozen=True)
class CacheEntry:
    id: int
    key: str
    ref: str
    size_in_bytes: int
    created_at: datetime
    last_accessed_at: datetime

    @classmethod
    def from_api(cls, raw: dict) -> CacheEntry:
        return cls(
            id=int(raw["id"]),
            key=str(raw["key"]),
            ref=str(raw["ref"]),
            size_in_bytes=int(raw["size_in_bytes"]),
            created_at=_parse_time(raw["created_at"]),
            last_accessed_at=_parse_time(raw["last_accessed_at"]),
        )


@dataclass(frozen=True)
class Deletion:
    entry: CacheEntry
    reason: str


@dataclass
class Plan:
    deletions: list[Deletion] = field(default_factory=list)
    kept: Counter[str] = field(default_factory=Counter)


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def lock_hash(lock_file: Path) -> str:
    """Hash setup-uv puts at the end of its cache key for ``cache-dependency-glob``.

    Same algorithm as ``hashFiles()``: SHA-256 over each matched file's
    SHA-256 digest. The composite action matches exactly one file.
    """
    file_digest = hashlib.sha256(lock_file.read_bytes()).digest()
    return hashlib.sha256(file_digest).hexdigest()


def _gh_api(args: list[str]) -> str:
    result = subprocess.run(
        ["gh", "api", *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=GH_TIMEOUT_SECONDS,
    )
    return result.stdout


def list_caches(repo: str, gh_api: GhApi = _gh_api) -> list[CacheEntry]:
    """Every cache entry in the repository, or IncompleteListingError.

    Pages are requested oldest first by ``created_at``, so entries saved while
    paging land on later pages instead of shifting earlier ones. The result
    must hold exactly ``total_count`` distinct ids, with the same
    ``total_count`` on every page; eviction or deletion mid-listing fails that
    check and the run aborts rather than planning from a partial view.
    """
    entries: list[CacheEntry] = []
    totals: set[int] = set()
    for page in range(1, MAX_PAGES + 1):
        body = json.loads(
            gh_api([f"repos/{repo}/actions/caches?per_page={PER_PAGE}&page={page}&sort=created_at&direction=asc"])
        )
        totals.add(int(body["total_count"]))
        batch = body["actions_caches"]
        entries.extend(CacheEntry.from_api(raw) for raw in batch)
        if len(batch) < PER_PAGE or len(entries) >= max(totals):
            break
    else:
        raise IncompleteListingError(f"cache list did not end within {MAX_PAGES} pages")
    ids = {e.id for e in entries}
    if len(totals) != 1 or len(entries) != next(iter(totals)) or len(ids) != len(entries):
        raise IncompleteListingError(
            f"cache list is incomplete: {len(entries)} entries ({len(ids)} distinct ids), "
            f"total_count per page {sorted(totals)}"
        )
    return entries


def open_pr_base_shas(repo: str, gh_api: GhApi = _gh_api) -> set[str]:
    """``pull_request.base.sha`` of every open pull request, or IncompleteListingError.

    CodeQL reads ``pull_request.base.sha`` from the event payload; GraphQL
    ``baseRefOid`` is the same field, and its cursor pagination plus
    ``totalCount`` let the listing be checked for completeness. Every open
    pull request must yield a 40-hex base SHA: one without it would leave its
    TRAP entry unprotected, so it fails the listing like a missing page.
    """
    owner, name = repo.split("/", 1)
    shas: set[str] = set()
    numbers: set[int] = set()
    totals: set[int] = set()
    cursor: str | None = None
    for _ in range(MAX_PAGES):
        args = ["graphql", "-f", f"query={OPEN_PR_BASES_QUERY}", "-f", f"owner={owner}", "-f", f"name={name}"]
        if cursor:
            args += ["-f", f"cursor={cursor}"]
        prs = json.loads(gh_api(args))["data"]["repository"]["pullRequests"]
        totals.add(int(prs["totalCount"]))
        for node in prs["nodes"]:
            base = node["baseRefOid"]
            if not isinstance(base, str) or not COMMIT_SHA_RE.fullmatch(base):
                raise IncompleteListingError(f"open pull request #{node['number']} has no valid base SHA: {base!r}")
            numbers.add(int(node["number"]))
            shas.add(base)
        if not prs["pageInfo"]["hasNextPage"]:
            break
        cursor = prs["pageInfo"]["endCursor"]
    else:
        raise IncompleteListingError(f"open pull request list did not end within {MAX_PAGES} pages")
    if len(totals) != 1 or len(numbers) != next(iter(totals)):
        raise IncompleteListingError(
            f"open pull request list is incomplete: {len(numbers)} pull requests, totalCount per page {sorted(totals)}"
        )
    return shas


def plan_deletions(
    entries: Iterable[CacheEntry],
    current_lock_hash: str,
    now: datetime,
    pr_base_shas: frozenset[str] | set[str] = frozenset(),
    uv_grace: timedelta = timedelta(hours=DEFAULT_UV_GRACE_HOURS),
) -> Plan:
    trap_families: dict[str, list[CacheEntry]] = {}
    uv_families: dict[str, list[CacheEntry]] = {}
    plan = Plan()

    for entry in entries:
        if trap := CODEQL_TRAP_RE.match(entry.key):
            if entry.ref == MAIN_REF:
                trap_families.setdefault(trap.group(1), []).append(entry)
            else:
                plan.deletions.append(Deletion(entry, f"CodeQL TRAP cache on {entry.ref}, not main"))
        elif entry.ref == MAIN_REF and (uv := SETUP_UV_RE.match(entry.key)):
            uv_families.setdefault(uv.group(1), []).append(entry)

    for family, members in trap_families.items():
        newest = max(members, key=lambda e: (e.created_at, e.id))
        for entry in members:
            if entry is newest:
                plan.kept[KEEP_TRAP_NEWEST] += 1
            elif entry.key[len(family) :] in pr_base_shas:
                plan.kept[KEEP_TRAP_PR_BASE] += 1
            else:
                plan.deletions.append(Deletion(entry, f"superseded by newest {family}* ({newest.key[len(family) :]})"))

    for members in uv_families.values():
        newest = max(members, key=lambda e: (e.created_at, e.id))
        for entry in members:
            idle = now - entry.last_accessed_at
            if entry.key.endswith(f"-{current_lock_hash}"):
                plan.kept[KEEP_UV_CURRENT] += 1
            elif entry is newest:
                plan.kept[KEEP_UV_NEWEST] += 1
            elif idle < uv_grace:
                plan.kept[KEEP_UV_GRACE] += 1
            else:
                hours = idle.total_seconds() / 3600
                plan.deletions.append(Deletion(entry, f"superseded uv lock, unread for {hours:.1f} h"))

    plan.deletions.sort(key=lambda d: (d.entry.ref, d.entry.key))
    return plan


def _gb(size: int) -> str:
    return f"{size / 1e9:.2f} GB"


def render_plan(entries: list[CacheEntry], plan: Plan, apply: bool) -> str:
    deletions = plan.deletions
    total = sum(e.size_in_bytes for e in entries)
    freed = sum(d.entry.size_in_bytes for d in deletions)
    lines = [
        f"{'DELETE' if apply else 'would delete'} {d.entry.ref} {d.entry.key} ({_gb(d.entry.size_in_bytes)}): {d.reason}"
        for d in deletions
    ]
    managed = sum(plan.kept.values())
    rules = (KEEP_TRAP_NEWEST, KEEP_TRAP_PR_BASE, KEEP_UV_CURRENT, KEEP_UV_NEWEST, KEEP_UV_GRACE)
    lines.append(
        "keep: "
        + "; ".join(f"{plan.kept[rule]} {rule}" for rule in rules)
        + f"; {len(entries) - len(deletions) - managed} not managed"
    )
    lines.append(
        f"total: {len(entries)} entries, {_gb(total)}; "
        f"delete {len(deletions)} entries, {_gb(freed)}; "
        f"remaining {len(entries) - len(deletions)} entries, {_gb(total - freed)}"
    )
    return "\n".join(lines)


def delete_entries(repo: str, deletions: list[Deletion], gh_api: GhApi = _gh_api) -> list[str]:
    """Delete by id; return the keys that failed (an entry already gone is not a failure)."""
    failed: list[str] = []
    for deletion in deletions:
        try:
            gh_api(["--method", "DELETE", f"repos/{repo}/actions/caches/{deletion.entry.id}"])
        except subprocess.CalledProcessError as exc:
            if "404" in (exc.stderr or ""):
                continue
            print(f"failed to delete {deletion.entry.key}: {(exc.stderr or '').strip()}", file=sys.stderr)
            failed.append(deletion.entry.key)
    return failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--lock-file", type=Path, default=Path("requirements-lock.txt"))
    parser.add_argument("--uv-grace-hours", type=float, default=DEFAULT_UV_GRACE_HOURS)
    parser.add_argument("--apply", action="store_true", help="delete the planned entries (default: dry run)")
    args = parser.parse_args(argv)

    try:
        entries = list_caches(args.repo)
        pr_base_shas = open_pr_base_shas(args.repo)
    except (IncompleteListingError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as exc:
        detail = getattr(exc, "stderr", None) or exc
        print(
            f"aborting, nothing deleted: could not list caches and open pull requests completely: {detail}",
            file=sys.stderr,
        )
        return 2
    plan = plan_deletions(
        entries,
        current_lock_hash=lock_hash(args.lock_file),
        now=datetime.now(UTC),
        pr_base_shas=pr_base_shas,
        uv_grace=timedelta(hours=args.uv_grace_hours),
    )
    print(render_plan(entries, plan, args.apply))
    if not args.apply:
        return 0
    failed = delete_entries(args.repo, plan.deletions)
    if failed:
        print(f"{len(failed)} deletions failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
