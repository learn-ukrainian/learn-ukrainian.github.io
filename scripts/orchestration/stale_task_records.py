"""Settle orphaned ``needs_finalize`` task records and archive old terminal ones (#8625).

``batch_state/tasks/`` is the hot directory every claim scan, Monitor view and
reaper reads. Records that settled ``needs_finalize`` before the #8468 fix, and
whose worktree, local branch and remote branch are all gone, can never be
finalized; they only inflate every scan and read as open attention items.

``settle-stale`` classifies each ``needs_finalize`` record older than
``--min-age-days`` exactly as the read-only #8625 report did:

* **A** the dispatch branch is still on ``origin`` (report only: no finalizer
  exists for a published branch without its worktree);
* **B** possible unpushed work: the local branch still exists, or the worktree
  exists and is dirty (never modified);
* **C** orphaned: worktree, local branch and remote branch are all gone;
* **D** anything else, including every record whose evidence is unavailable
  (never modified).

Only class C is written: a merged pull request for the branch settles ``done``,
a clean exit with no commits settles ``no_deliverable``, anything else settles
``failed``. Evidence comes from one ``git ls-remote --heads`` and one local
branch listing per repository, worktree probes for the few records whose
checkout still exists, and one paged REST pull list per repository (never
GraphQL, never a per-record GitHub call).

``archive`` moves terminal records (statuses that no longer claim a worktree,
:data:`worktree_claims.RELEASED_TASK_STATUSES`) older than ``--min-age-days``
into ``batch_state/tasks/archive/`` with their ``.result`` and read-only
snapshot sidecars. The claim scan globs only the top level, which is correct
because archived records are terminal and claim nothing. A record whose linked
worktree still exists stays hot, because the reaper and the branch-holder
release read it as the ownership proof for that checkout. ``restore`` moves an
archived record back.

Every record write goes through ``delegate._write_state_atomic`` (PID-suffixed
tmp file plus ``os.replace``) while holding ``delegate.worktree_lock`` for the
record's worktree path, the lock dispatch holds while it publishes a record
naming that checkout. A record whose mtime changed since classification is
skipped: a live writer touched it.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# delegate imports ``agent_runtime`` as a top-level package (see reconcile_sweep.py).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
for _path in (PROJECT_ROOT, PROJECT_ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts import delegate
from scripts.common.git_context import sanitized_git_env
from scripts.orchestration import fleet_repos, worktree_claims

SETTLED_BY = "settle-stale"
ARCHIVE_DIR_NAME = worktree_claims.ARCHIVE_DIR_NAME
NEEDS_FINALIZE = "needs_finalize"
DEFAULT_SETTLE_MIN_AGE_DAYS = 7.0
DEFAULT_ARCHIVE_MIN_AGE_DAYS = 14.0
DEFAULT_MAX_PR_PAGES = 40
DEFAULT_LOCK_TIMEOUT_S = 5.0
PR_PAGE_SIZE = 100
# Delegate-owned sidecars that travel with a record: ``<stem>.result`` and the
# read-only checkout snapshot directory (see delegate._read_only_snapshot_dir_for).
_SNAPSHOT_SUFFIX = ".snapshots"
# ``delegate._archive_task_artifacts`` renames a re-dispatched record to
# ``<stem>.<stamp>[.<pid>].archived.json`` and its snapshot directory to
# ``<stem>.snapshots.<stamp>[.<pid>].archived``.
_REDISPATCH_ARCHIVED_STEM_RE = re.compile(r"^(?P<base>.+)\.(?P<tag>\d{8}T\d{6}\d*Z(?:\.\d+)?)\.archived$")

EXIT_OK = 0
EXIT_ERRORS = 1
EXIT_USAGE = 2

# (slug, page) -> one page of ``GET /repos/{slug}/pulls`` objects.
PullPager = Callable[[str, int], list[dict[str, Any]]]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _record_age_days(record: dict[str, Any], mtime_ns: int, now: datetime) -> float:
    """Age from ``finished_at``; the file mtime when the record has none."""
    finished = _parse_ts(record.get("finished_at"))
    if finished is None:
        finished = datetime.fromtimestamp(mtime_ns / 1e9, UTC)
    return (now - finished).total_seconds() / 86400.0


def _normalize_branch(raw: Any) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    branch = raw.strip().removeprefix("refs/heads/").removeprefix("origin/")
    return branch or None


def _git(args: list[str], *, cwd: Path, timeout: float) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env=sanitized_git_env(),
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _iter_record_files(tasks_dir: Path) -> list[Path]:
    """Top-level task records only; the archive is never scanned."""
    return sorted(path for path in tasks_dir.glob("*.json") if path.is_file())


# ---------------------------------------------------------------------------
# Repository evidence (batched per repository)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class RepoFacts:
    """Batched git evidence for one repository checkout."""

    slug: str
    checkout: Path | None
    remote_heads: dict[str, str] | None = None
    local_branches: dict[str, str] | None = None
    error: str | None = None


def default_repo_checkouts() -> dict[str, Path]:
    """Map each fleet repository slug to its local checkout beside the primary."""
    checkouts: dict[str, Path] = {}
    for key, repo in fleet_repos.load_fleet_repos().items():
        try:
            _repo, checkout = fleet_repos.resolve_fleet_repo(key, primary_root=delegate._REPO_ROOT)
        except fleet_repos.FleetRepoError:
            continue
        checkouts[repo.github] = checkout
    return checkouts


def collect_repo_facts(slug: str, checkout: Path | None) -> RepoFacts:
    """One ``git ls-remote --heads origin`` plus one local branch listing."""
    facts = RepoFacts(slug=slug, checkout=checkout)
    if checkout is None:
        facts.error = f"no local checkout for repository {slug}"
        return facts
    remote = _git(["ls-remote", "--heads", "origin"], cwd=checkout, timeout=delegate.DEFAULT_NETWORK_GIT_TIMEOUT_S)
    if remote is None or remote.returncode != 0:
        facts.error = "git ls-remote --heads origin failed"
        return facts
    heads: dict[str, str] = {}
    for line in remote.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].startswith("refs/heads/"):
            heads[parts[1].removeprefix("refs/heads/")] = parts[0]
    local = _git(
        ["for-each-ref", "--format=%(objectname) %(refname:short)", "refs/heads"],
        cwd=checkout,
        timeout=delegate.DEFAULT_GIT_TIMEOUT_S,
    )
    if local is None or local.returncode != 0:
        facts.error = "git for-each-ref refs/heads failed"
        return facts
    branches: dict[str, str] = {}
    for line in local.stdout.splitlines():
        sha, _, name = line.partition(" ")
        if name:
            branches[name] = sha
    facts.remote_heads = heads
    facts.local_branches = branches
    return facts


def _commits_ahead_of_base(checkout: Path, branch: str, base: str) -> int | None:
    proc = _git(
        ["rev-list", "--count", f"refs/remotes/origin/{base}..refs/heads/{branch}"],
        cwd=checkout,
        timeout=delegate.DEFAULT_GIT_TIMEOUT_S,
    )
    if proc is None or proc.returncode != 0:
        return None
    try:
        return int(proc.stdout.strip())
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Pull request evidence (one paged REST list per repository)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class PullIndex:
    """Merged same-repository pull requests grouped by head branch.

    Pages are listed newest-``updated_at`` first. ``covered_since`` is ``None``
    when the listing reached every pull request any candidate could need;
    otherwise only pull requests updated at or after it were seen.
    """

    merged_by_branch: dict[str, list[dict[str, Any]]]
    covered_since: datetime | None = None
    pages: int = 0
    error: str | None = None


def gh_pull_page(slug: str, page: int) -> list[dict[str, Any]]:
    """Fetch one page of closed pull requests through the REST API (``gh api``)."""
    endpoint = f"repos/{slug}/pulls?state=closed&sort=updated&direction=desc&per_page={PR_PAGE_SIZE}&page={page}"
    proc = subprocess.run(
        ["gh", "api", endpoint],
        capture_output=True,
        text=True,
        check=False,
        timeout=delegate.DEFAULT_GH_CLI_TIMEOUT_S,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise RuntimeError(f"gh api {endpoint} failed: {detail[-1] if detail else proc.returncode}")
    loaded = json.loads(proc.stdout or "[]")
    if not isinstance(loaded, list):
        raise RuntimeError(f"gh api {endpoint} returned {type(loaded).__name__}, not a list")
    return loaded


def build_pull_index(
    slug: str,
    *,
    oldest_start: datetime | None,
    pager: PullPager,
    max_pages: int,
) -> PullIndex:
    """Page closed pull requests until every one updated since ``oldest_start`` is seen.

    A pull request merged after a task started was updated at or after that
    start, so paging newest-updated first can stop once a page ends before
    ``oldest_start``. ``oldest_start`` of ``None`` pages to the end.
    """
    index = PullIndex(merged_by_branch=defaultdict(list))
    last_updated: datetime | None = None
    for page in range(1, max_pages + 1):
        try:
            pulls = pager(slug, page)
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            index.error = f"{type(exc).__name__}: {exc}"[:300]
            return index
        index.pages = page
        if not pulls:
            return index
        for pull in pulls:
            head = pull.get("head") if isinstance(pull, dict) else None
            head_repo = head.get("repo") if isinstance(head, dict) else None
            if not pull.get("merged_at") or not isinstance(head_repo, dict):
                continue
            if head_repo.get("full_name") != slug or not isinstance(head.get("ref"), str):
                continue
            index.merged_by_branch[head["ref"]].append(
                {"number": pull.get("number"), "url": pull.get("html_url"), "merged_at": pull.get("merged_at")}
            )
        last_updated = _parse_ts(pulls[-1].get("updated_at")) if isinstance(pulls[-1], dict) else None
        if len(pulls) < PR_PAGE_SIZE:
            return index
        if oldest_start is not None and last_updated is not None and last_updated < oldest_start:
            return index
    index.covered_since = last_updated or datetime.max.replace(tzinfo=UTC)
    return index


# ---------------------------------------------------------------------------
# settle-stale
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class Candidate:
    """One ``needs_finalize`` record and its classification."""

    path: Path
    mtime_ns: int
    record: dict[str, Any]
    age_days: float
    klass: str = "D"
    evidence: dict[str, Any] = dataclasses.field(default_factory=dict)
    outcome: str | None = None
    settle_reason: str | None = None
    merged_pr: dict[str, Any] | None = None
    skip_reason: str | None = None
    action: str = "report"

    @property
    def task_id(self) -> str:
        return str(self.record.get("task_id") or self.path.stem)

    @property
    def task_start(self) -> datetime | None:
        started = _parse_ts(self.record.get("started_at"))
        if started is not None:
            return started
        finished = _parse_ts(self.record.get("finished_at"))
        duration = self.record.get("duration_s")
        if finished is not None and isinstance(duration, int | float):
            return finished - timedelta(seconds=float(duration))
        return finished

    def as_report(self) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "file": self.path.name,
            "task_id": self.task_id,
            "agent": self.record.get("agent"),
            "class": self.klass,
            "age_days": round(self.age_days, 1),
            "action": self.action,
        }
        if self.outcome is not None:
            entry["outcome"] = self.outcome
            entry["settle_reason"] = self.settle_reason
        if self.merged_pr is not None:
            entry["merged_pr"] = self.merged_pr
        if self.skip_reason is not None:
            entry["skip_reason"] = self.skip_reason
        entry["evidence"] = self.evidence
        return entry


def select_needs_finalize(tasks_dir: Path, *, min_age_days: float, now: datetime) -> tuple[list[Candidate], int]:
    """Return old ``needs_finalize`` records and the count of younger ones left alone."""
    candidates: list[Candidate] = []
    younger = 0
    for path in _iter_record_files(tasks_dir):
        try:
            mtime_ns = path.stat().st_mtime_ns
        except OSError:
            continue
        record = delegate._read_state_json(path)
        if record is None or record.get("status") != NEEDS_FINALIZE:
            continue
        age = _record_age_days(record, mtime_ns, now)
        if age < min_age_days:
            younger += 1
            continue
        candidates.append(Candidate(path=path, mtime_ns=mtime_ns, record=record, age_days=age))
    return candidates, younger


def _classify_one(candidate: Candidate, facts: RepoFacts | None) -> None:
    record = candidate.record
    evidence = candidate.evidence
    slug = record.get("repository")
    branch = _normalize_branch(record.get("worktree_branch"))
    worktree_raw = record.get("worktree_path")
    evidence.update(
        {
            "repository": slug,
            "branch": branch,
            "worktree_path": worktree_raw,
            "returncode": record.get("returncode"),
            "commits_ahead": record.get("commits_ahead"),
        }
    )
    if not isinstance(slug, str) or facts is None:
        candidate.klass, candidate.skip_reason = "D", "record has no known repository"
        return
    if facts.error is not None or facts.remote_heads is None or facts.local_branches is None:
        candidate.klass, candidate.skip_reason = "D", f"repository evidence unavailable: {facts.error}"
        return
    if branch is None or not isinstance(worktree_raw, str) or not worktree_raw.strip():
        candidate.klass, candidate.skip_reason = "D", "record names no worktree branch or path"
        return

    worktree = Path(worktree_raw)
    worktree_exists = worktree.exists()
    dirty = worktree_claims.worktree_is_dirty(worktree) if worktree_exists else False
    on_origin = branch in facts.remote_heads
    local_sha = facts.local_branches.get(branch)
    evidence.update(
        {
            "worktree_exists": worktree_exists,
            "worktree_dirty": dirty,
            "branch_on_origin": on_origin,
            "local_branch": local_sha is not None,
        }
    )
    if local_sha is not None:
        evidence["local_branch_sha"] = local_sha
        if on_origin:
            evidence["local_matches_origin"] = local_sha == facts.remote_heads[branch]
        elif facts.checkout is not None:
            base = _normalize_branch(record.get("worktree_base")) or "main"
            evidence["local_commits_ahead_of_base"] = _commits_ahead_of_base(facts.checkout, branch, base)

    if on_origin:
        candidate.klass = "A"
        candidate.skip_reason = "branch still on origin; no finalizer publishes a branch without its worktree"
    elif local_sha is not None or dirty in (True, None):
        candidate.klass = "B"
        candidate.skip_reason = "possible unpushed work: " + (
            "local branch not on origin" if local_sha is not None else "worktree dirty or unreadable"
        )
    elif not worktree_exists:
        candidate.klass = "C"
    else:
        candidate.klass = "D"
        candidate.skip_reason = "clean worktree exists without a local or remote branch"


def _decide_outcome(candidate: Candidate, index: PullIndex | None) -> None:
    """Pick the terminal status of an orphaned (class C) record."""
    if index is None or index.error is not None:
        candidate.skip_reason = f"pull request list unavailable: {index.error if index else 'not fetched'}"
        return
    start = candidate.task_start
    if index.covered_since is not None and (start is None or start < index.covered_since):
        candidate.skip_reason = "pull request list does not reach back to the task start; raise --max-pr-pages"
        return
    branch = candidate.evidence.get("branch")
    merged = [
        pull
        for pull in index.merged_by_branch.get(branch or "", [])
        if start is None or ((merged_at := _parse_ts(pull.get("merged_at"))) is not None and merged_at >= start)
    ]
    record = candidate.record
    if merged:
        pull = max(merged, key=lambda item: str(item.get("merged_at") or ""))
        candidate.outcome = "done"
        candidate.merged_pr = pull
        candidate.settle_reason = f"orphaned: branch {branch} merged in PR #{pull.get('number')}"
    elif record.get("commits_ahead") == 0 and record.get("returncode") == 0:
        candidate.outcome = delegate._NO_DELIVERABLE_STATUS
        candidate.settle_reason = "orphaned: clean exit with no commits; worktree and branch gone"
    else:
        candidate.outcome = "failed"
        candidate.settle_reason = (
            f"orphaned: returncode={record.get('returncode')} commits_ahead={record.get('commits_ahead')}, "
            "no merged pull request; worktree and branch gone"
        )


def classify(
    candidates: list[Candidate],
    *,
    repo_checkouts: Mapping[str, Path],
    pager: PullPager,
    max_pr_pages: int,
) -> dict[str, PullIndex]:
    """Classify every candidate in place; return the pull index built per repository."""
    facts_by_slug: dict[str, RepoFacts] = {}
    for candidate in candidates:
        slug = candidate.record.get("repository")
        if isinstance(slug, str) and slug not in facts_by_slug:
            facts_by_slug[slug] = collect_repo_facts(slug, repo_checkouts.get(slug))
        _classify_one(candidate, facts_by_slug.get(slug) if isinstance(slug, str) else None)

    orphaned_by_slug: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        if candidate.klass == "C":
            orphaned_by_slug[str(candidate.record.get("repository"))].append(candidate)
    indexes: dict[str, PullIndex] = {}
    for slug, orphaned in orphaned_by_slug.items():
        starts = [candidate.task_start for candidate in orphaned]
        oldest = None if any(start is None for start in starts) else min(s for s in starts if s is not None)
        indexes[slug] = build_pull_index(slug, oldest_start=oldest, pager=pager, max_pages=max_pr_pages)
        for candidate in orphaned:
            _decide_outcome(candidate, indexes[slug])
    return indexes


def _settled_record(candidate: Candidate, current: dict[str, Any], settled_at: str) -> dict[str, Any]:
    updated = {
        **current,
        "status": candidate.outcome,
        "needs_finalize": False,
        "settled_by": SETTLED_BY,
        "settled_at": settled_at,
        "settle_reason": candidate.settle_reason,
        "settle_previous_status": NEEDS_FINALIZE,
        "settle_evidence": candidate.evidence,
    }
    if candidate.merged_pr is not None:
        updated["merged_pr"] = candidate.merged_pr
    if candidate.outcome == delegate._NO_DELIVERABLE_STATUS and not updated.get("no_deliverable_reason"):
        updated["no_deliverable_reason"] = candidate.settle_reason
    return updated


def apply_settlement(candidate: Candidate, *, lock_timeout_s: float, now: datetime) -> None:
    """Write one class C record's terminal status, or record why it was skipped."""
    try:
        with delegate.worktree_lock(str(candidate.evidence["worktree_path"]), timeout_s=lock_timeout_s):
            try:
                mtime_ns = candidate.path.stat().st_mtime_ns
            except FileNotFoundError:
                candidate.action, candidate.skip_reason = "skipped", "record moved since classification"
                return
            if mtime_ns != candidate.mtime_ns:
                candidate.action, candidate.skip_reason = "skipped", "record changed since classification"
                return
            current = delegate._read_state_json(candidate.path)
            if current is None or current.get("status") != NEEDS_FINALIZE:
                candidate.action, candidate.skip_reason = "skipped", "record no longer needs_finalize"
                return
            delegate._write_state_atomic(candidate.path, _settled_record(candidate, current, now.isoformat()))
    except worktree_claims.WorktreeLockError as exc:
        candidate.action, candidate.skip_reason = "skipped", worktree_claims.lock_refusal(exc)
        return
    except OSError as exc:
        candidate.action, candidate.skip_reason = "error", f"write failed: {type(exc).__name__}: {exc}"
        return
    candidate.action = "settled"


def settle_stale(
    tasks_dir: Path,
    *,
    min_age_days: float = DEFAULT_SETTLE_MIN_AGE_DAYS,
    apply: bool = False,
    repo_checkouts: Mapping[str, Path] | None = None,
    pager: PullPager = gh_pull_page,
    max_pr_pages: int = DEFAULT_MAX_PR_PAGES,
    lock_timeout_s: float = DEFAULT_LOCK_TIMEOUT_S,
    now: datetime | None = None,
    before_apply: Callable[[list[Candidate]], None] | None = None,
) -> dict[str, Any]:
    """Classify stale ``needs_finalize`` records and, with ``apply``, settle class C.

    ``before_apply`` is a test seam called between classification and writes.
    """
    now = now or datetime.now(UTC)
    candidates, younger = select_needs_finalize(tasks_dir, min_age_days=min_age_days, now=now)
    indexes = classify(
        candidates,
        repo_checkouts=default_repo_checkouts() if repo_checkouts is None else repo_checkouts,
        pager=pager,
        max_pr_pages=max_pr_pages,
    )
    settleable = [candidate for candidate in candidates if candidate.klass == "C" and candidate.outcome]
    for candidate in settleable:
        candidate.action = "would_settle"
    if apply:
        if before_apply is not None:
            before_apply(candidates)
        for candidate in settleable:
            apply_settlement(candidate, lock_timeout_s=lock_timeout_s, now=now)

    by_class = Counter(candidate.klass for candidate in candidates)
    order = {"B": 0, "A": 1, "D": 2, "C": 3}
    return {
        "command": "settle-stale",
        "mode": "apply" if apply else "dry-run",
        "tasks_dir": str(tasks_dir),
        "min_age_days": min_age_days,
        "selected": len(candidates),
        "younger_left_alone": younger,
        "classes": {klass: by_class.get(klass, 0) for klass in ("A", "B", "C", "D")},
        "outcomes": dict(Counter(c.outcome for c in candidates if c.klass == "C" and c.outcome)),
        "actions": dict(Counter(candidate.action for candidate in candidates)),
        "pull_lists": {
            slug: {
                "pages": index.pages,
                "error": index.error,
                "covered_since": index.covered_since.isoformat() if index.covered_since else None,
            }
            for slug, index in indexes.items()
        },
        "records": [
            candidate.as_report()
            for candidate in sorted(candidates, key=lambda item: (order[item.klass], item.path.name))
        ],
    }


# ---------------------------------------------------------------------------
# archive / restore
# ---------------------------------------------------------------------------


def _sidecar_names(stem: str) -> tuple[str, str]:
    """``(<result>, <snapshot dir>)`` names that belong to the record ``<stem>.json``."""
    match = _REDISPATCH_ARCHIVED_STEM_RE.match(stem)
    if match is None:
        return f"{stem}.result", f"{stem}{_SNAPSHOT_SUFFIX}"
    return f"{stem}.result", f"{match['base']}{_SNAPSHOT_SUFFIX}.{match['tag']}.archived"


def sidecar_paths(record_path: Path) -> list[Path]:
    """Delegate-owned sidecars of a record: ``<stem>.result`` and its snapshot directory."""
    candidates = (record_path.with_name(name) for name in _sidecar_names(record_path.stem))
    return [path for path in candidates if path.exists()]


def _linked_worktree_exists(record: dict[str, Any]) -> bool:
    raw = record.get("worktree_path") or record.get("cwd")
    if not isinstance(raw, str) or not raw.strip():
        return False
    return (Path(raw) / ".git").is_file()


def _free_destination(dest_dir: Path, name: str, stamp: str) -> Path:
    dest = dest_dir / name
    if not dest.exists():
        return dest
    return delegate._archived_artifact_path(dest, stamp)


def _move_group(record_path: Path, dest_dir: Path, stamp: str) -> list[str]:
    """Move a record then its sidecars; never overwrite a destination."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    record_dest = _free_destination(dest_dir, record_path.name, stamp)
    # A renamed record takes its sidecars' names along, so they still pair up.
    pairs = zip(_sidecar_names(record_path.stem), _sidecar_names(record_dest.stem), strict=True)
    sidecars = [(record_path.with_name(src), dst) for src, dst in pairs if record_path.with_name(src).exists()]
    os.rename(record_path, record_dest)
    moved.append(record_dest.name)
    for sidecar, name in sidecars:
        dest = _free_destination(dest_dir, name, stamp)
        os.rename(sidecar, dest)
        moved.append(dest.name)
    return moved


def archive_terminal(
    tasks_dir: Path,
    *,
    min_age_days: float = DEFAULT_ARCHIVE_MIN_AGE_DAYS,
    apply: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Move old terminal records and their sidecars into ``<tasks_dir>/archive/``."""
    now = now or datetime.now(UTC)
    archive_dir = tasks_dir / ARCHIVE_DIR_NAME
    stamp = delegate._archive_stamp()
    rows: list[dict[str, Any]] = []
    kept_worktree = younger = 0
    for path in _iter_record_files(tasks_dir):
        try:
            mtime_ns = path.stat().st_mtime_ns
        except OSError:
            continue
        record = delegate._read_state_json(path)
        if record is None or record.get("status") not in worktree_claims.RELEASED_TASK_STATUSES:
            continue
        age = _record_age_days(record, mtime_ns, now)
        if age < min_age_days:
            younger += 1
            continue
        if _linked_worktree_exists(record):
            kept_worktree += 1
            continue
        row: dict[str, Any] = {
            "file": path.name,
            "status": record.get("status"),
            "age_days": round(age, 1),
            "sidecars": [sidecar.name for sidecar in sidecar_paths(path)],
            "action": "would_archive",
        }
        if apply:
            try:
                if path.stat().st_mtime_ns != mtime_ns:
                    row["action"], row["skip_reason"] = "skipped", "record changed since selection"
                else:
                    row["moved"] = _move_group(path, archive_dir, stamp)
                    row["action"] = "archived"
            except FileNotFoundError:
                row["action"], row["skip_reason"] = "skipped", "record moved since selection"
            except OSError as exc:
                row["action"], row["error"] = "error", f"{type(exc).__name__}: {exc}"
        rows.append(row)
    return {
        "command": "archive",
        "mode": "apply" if apply else "dry-run",
        "tasks_dir": str(tasks_dir),
        "archive_dir": str(archive_dir),
        "min_age_days": min_age_days,
        "selected": len(rows),
        "younger_left_alone": younger,
        "kept_worktree_exists": kept_worktree,
        "actions": dict(Counter(row["action"] for row in rows)),
        "by_status": dict(Counter(str(row["status"]) for row in rows)),
        "records": rows,
    }


def restore_archived(tasks_dir: Path, names: Iterable[str], *, apply: bool = False) -> dict[str, Any]:
    """Move archived records (by task id or file name) and their sidecars back to the hot directory."""
    archive_dir = tasks_dir / ARCHIVE_DIR_NAME
    rows: list[dict[str, Any]] = []
    for name in names:
        record_path = (
            archive_dir / name if name.endswith(".json") else worktree_claims.archived_task_record_path(tasks_dir, name)
        )
        file_name = record_path.name
        row: dict[str, Any] = {"file": file_name}
        if not record_path.is_file():
            row["action"], row["skip_reason"] = "skipped", "not in archive"
        else:
            group = [record_path, *sidecar_paths(record_path)]
            clashes = [path.name for path in group if (tasks_dir / path.name).exists()]
            if clashes:
                row["action"], row["skip_reason"] = "skipped", f"hot directory already holds {', '.join(clashes)}"
            elif not apply:
                row["action"] = "would_restore"
            else:
                try:
                    for path in group:
                        os.rename(path, tasks_dir / path.name)
                    row["action"] = "restored"
                except OSError as exc:
                    row["action"], row["error"] = "error", f"{type(exc).__name__}: {exc}"
            row["files"] = [path.name for path in group]
        rows.append(row)
    return {
        "command": "restore",
        "mode": "apply" if apply else "dry-run",
        "tasks_dir": str(tasks_dir),
        "actions": dict(Counter(row["action"] for row in rows)),
        "records": rows,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_PROG = "python -m scripts.orchestration.stale_task_records"
_RELATED = (
    "Related: scripts/delegate.py (record writer _write_state_atomic, worktree_lock),\n"
    "  scripts/orchestration/worktree_claims.py (claim scan, RELEASED_TASK_STATUSES),\n"
    "  batch_state/tasks/report-8625.result (classification report), issue #8625."
)


def _print_summary(report: dict[str, Any]) -> None:
    head = {key: value for key, value in report.items() if key != "records"}
    print(json.dumps(head, indent=2, default=str))
    for row in report["records"]:
        if row.get("class") in (None, "C") and row.get("action") in ("would_settle", "would_archive"):
            continue
        reason = row.get("skip_reason") or row.get("error") or row.get("settle_reason") or ""
        label = row.get("class") or row.get("status")
        print(f"  [{label}] {row.get('action')}: {row['file']}  {reason}")
    if report["mode"] == "dry-run":
        print("dry-run only — re-run with --apply to write these changes")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description=(
            "Settle orphaned needs_finalize delegate task records and archive old terminal ones (#8625).\n"
            "Use it to clear pre-#8468 bookkeeping out of batch_state/tasks/; never to finalize live\n"
            "work (class A/B/D records are only reported). Every command is a dry run without --apply."
        ),
        epilog=(
            "Commands:\n"
            "  settle-stale   Classify old needs_finalize records (A/B/C/D) and settle class C.\n"
            "  archive        Move old terminal records into batch_state/tasks/archive/.\n"
            "  restore        Move archived records back into batch_state/tasks/.\n"
            "\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.orchestration.stale_task_records settle-stale --json\n"
            "  .venv/bin/python -m scripts.orchestration.stale_task_records settle-stale --apply\n"
            "  .venv/bin/python -m scripts.orchestration.stale_task_records archive --min-age-days 30 --apply\n"
            "  .venv/bin/python -m scripts.orchestration.stale_task_records restore review-7393-r3 --apply\n"
            "\n"
            "Outputs:\n"
            "  stdout: a summary (or with --json the full report with per-record evidence).\n"
            "  --apply rewrites settled records in place / moves archived records; nothing else.\n"
            "\n"
            "Exit codes:\n"
            "  0  finished (dry run, or every write succeeded or was safely skipped)\n"
            "  1  at least one write or move failed\n"
            "  2  unusable arguments or missing tasks directory\n"
            "\n" + _RELATED
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def common(sub: argparse.ArgumentParser, *, min_age_default: float | None) -> None:
        sub.add_argument(
            "--tasks-dir",
            type=Path,
            default=None,
            help=f"Task record directory (default: {delegate._TASKS_DIR}).",
        )
        if min_age_default is not None:
            sub.add_argument(
                "--min-age-days",
                type=float,
                default=min_age_default,
                help=f"Only records whose finished_at is at least this many days old (default: {min_age_default:g}).",
            )
        sub.add_argument("--apply", action="store_true", help="Write the changes (default: dry run, writes nothing).")
        sub.add_argument("--json", action="store_true", help="Print the full JSON report instead of a summary.")

    settle = commands.add_parser(
        "settle-stale",
        help="Classify old needs_finalize records and settle orphaned (class C) ones.",
        description=(
            "Classify needs_finalize records older than --min-age-days and settle class C records.\n"
            "Use it for records whose worktree, local branch and remote branch are all gone."
        ),
        epilog=(
            "Classes (evidence: one git ls-remote + one local branch list per repository, worktree\n"
            "probes, one paged REST pull list per repository; never GraphQL or per-record calls):\n"
            "  A  branch still on origin                        report only\n"
            "  B  local branch exists, or worktree dirty         never modified\n"
            "  C  worktree, local and remote branch all gone     settled\n"
            "  D  anything else or evidence unavailable          never modified\n"
            "Class C settles to: done (+merged_pr) when a same-repository PR for the branch merged\n"
            "after the task started; no_deliverable when commits_ahead == 0 and returncode == 0;\n"
            "failed otherwise. Each write adds settled_by='settle-stale', settled_at, settle_reason,\n"
            "settle_previous_status and settle_evidence, holds the record's worktree lock, and is\n"
            "skipped if the record's mtime changed since classification.\n"
            "\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.orchestration.stale_task_records settle-stale --json | head -c 3000\n"
            "  .venv/bin/python -m scripts.orchestration.stale_task_records settle-stale --min-age-days 14 --apply\n"
            "\n"
            "Outputs: rewrites settled records in batch_state/tasks/ (with --apply only).\n"
            "Exit codes: 0 finished, 1 a write failed, 2 bad arguments.\n" + _RELATED
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    common(settle, min_age_default=DEFAULT_SETTLE_MIN_AGE_DAYS)
    settle.add_argument(
        "--max-pr-pages",
        type=int,
        default=DEFAULT_MAX_PR_PAGES,
        help=(
            f"Cap on {PR_PAGE_SIZE}-item REST pages of closed PRs per repository (default: {DEFAULT_MAX_PR_PAGES}); "
            "records older than the pages reached are skipped, never guessed."
        ),
    )
    settle.add_argument(
        "--lock-timeout",
        type=float,
        default=DEFAULT_LOCK_TIMEOUT_S,
        help=f"Seconds to wait for a record's worktree lock before skipping it (default: {DEFAULT_LOCK_TIMEOUT_S:g}).",
    )

    archive = commands.add_parser(
        "archive",
        help="Move old terminal records and their sidecars into batch_state/tasks/archive/.",
        description=(
            "Move terminal records (done, failed, no_deliverable, timeout, rate_limited, cancelled, crashed,\n"
            "dry_run, reaped) older than --min-age-days, with their .result and .snapshots sidecars, into\n"
            "batch_state/tasks/archive/. Records whose linked worktree still exists stay in place."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.orchestration.stale_task_records archive --json | head -c 1500\n"
            "  .venv/bin/python -m scripts.orchestration.stale_task_records archive --apply\n"
            "\n"
            "Outputs: moves files into <tasks-dir>/archive/ (with --apply only); a clashing name gets\n"
            "a .<stamp>.archived suffix, nothing is overwritten.\n"
            "Exit codes: 0 finished, 1 a move failed, 2 bad arguments.\n" + _RELATED
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    common(archive, min_age_default=DEFAULT_ARCHIVE_MIN_AGE_DAYS)

    restore = commands.add_parser(
        "restore",
        help="Move archived records back into batch_state/tasks/.",
        description=(
            "Move archived records and their sidecars back into the hot task directory.\n"
            "Use it when a tool needs an archived record in place; it never overwrites a hot file."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.orchestration.stale_task_records restore review-7393-r3\n"
            "  .venv/bin/python -m scripts.orchestration.stale_task_records restore review-7393-r3.json --apply\n"
            "\n"
            "Outputs: moves files from <tasks-dir>/archive/ back (with --apply only).\n"
            "Exit codes: 0 finished, 1 a move failed, 2 bad arguments.\n" + _RELATED
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    restore.add_argument(
        "names", nargs="+", metavar="TASK", help="Task id (e.g. review-7393-r3) or archived file name."
    )
    common(restore, min_age_default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    tasks_dir: Path = args.tasks_dir or delegate._TASKS_DIR
    if not tasks_dir.is_dir():
        print(f"tasks dir not found: {tasks_dir}", file=sys.stderr)
        return EXIT_USAGE
    if args.command == "settle-stale":
        if args.max_pr_pages < 1:
            print("--max-pr-pages must be at least 1", file=sys.stderr)
            return EXIT_USAGE
        report = settle_stale(
            tasks_dir,
            min_age_days=args.min_age_days,
            apply=args.apply,
            max_pr_pages=args.max_pr_pages,
            lock_timeout_s=args.lock_timeout,
        )
    elif args.command == "archive":
        report = archive_terminal(tasks_dir, min_age_days=args.min_age_days, apply=args.apply)
    else:
        report = restore_archived(tasks_dir, args.names, apply=args.apply)
    exit_code = EXIT_ERRORS if report["actions"].get("error") else EXIT_OK
    try:
        if args.json:
            print(json.dumps(report, indent=2, default=str))
        else:
            _print_summary(report)
        sys.stdout.flush()
    except BrokenPipeError:
        # A reader such as ``| head -c 3000`` closed stdout early; the work is done.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
