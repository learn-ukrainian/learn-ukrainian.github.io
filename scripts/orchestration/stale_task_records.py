"""Settle orphaned ``needs_finalize`` task records and archive old terminal ones (#8625).

``batch_state/tasks/`` is the hot directory every claim scan, Monitor view and
reaper reads. Records that settled ``needs_finalize`` before the #8468 fix, and
whose worktree, local branch and remote branch are all gone, can never be
finalized; they only inflate every scan and read as open attention items.

``settle-stale`` classifies each ``needs_finalize`` record older than
``--min-age-days``:

* **A** report only: the dispatch branch, or a commit the record names, is
  still on ``origin`` under any branch (no finalizer publishes a branch
  without its worktree);
* **B** possible unpushed work (never modified): the local branch still exists,
  the worktree exists and is dirty, or a local ref (a renamed branch) or a
  worktree HEAD still holds a commit the record names;
* **C** orphaned: the worktree path, the local branch and the remote branch are
  all gone, and so is the work. Either the record names a commit
  (``auto_finalize.commit_sha``; records carry no other head id) that no ref
  reaches, every remote branch freshly fetched, or the task exited with no
  commits and a clean tree, leaving nothing to lose;
* **D** anything else (never modified): evidence unavailable, a failed fetch
  (``fetch_failed``: stale remote refs cannot prove the work gone),
  commits or a dirty exit without a recorded commit id (a renamed branch cannot be ruled
  out), a recorded commit missing from the object store, or a merged pull
  request that shares the branch name but none of the record's commits.

Only class C is written. ``done`` needs a merged pull request tied to the task
by commit identity: its head or merge commit is a recorded commit, or its head
descends from one. A pull request that only reuses the branch name may belong
to a later task, so that record moves to D instead. A clean exit with no
commits settles ``no_deliverable``; anything else settles ``failed``. Evidence
comes from one fetch per repository of every remote branch into the private
namespace ``refs/lu-stale-scan/<repo-key>/`` (dry runs too: it writes only that
namespace), from the allowlisted ``https://github.com/<slug>.git`` with an
explicit refspec and config injection scrubbed from the environment (see
:func:`_fetch_scan_refs`), and one ``for-each-ref`` over that namespace and
the local branches; one ``git cat-file --batch-check`` and one
``git rev-list --all`` per repository when records name commits (one walk into
a set beats ~425 per-commit ``for-each-ref --contains`` walks); worktree probes
for checkouts that still exist; and one paged REST pull list per repository (never GraphQL, never
a per-record GitHub call). Per-record git calls happen only to name the refs
holding a commit or to test a same-branch pull request head's ancestry. Git and
``gh`` error text reaches the report only with URL userinfo stripped and
secrets redacted (:func:`_scrub`).

``archive`` moves terminal records (statuses that no longer claim a worktree,
:data:`worktree_claims.RELEASED_TASK_STATUSES`) older than ``--min-age-days``
into ``batch_state/tasks/archive/`` with their ``.result`` and read-only
snapshot sidecars. A record stays hot while its checkout path (``worktree_path``,
else a ``cwd`` that is not a primary checkout) exists at all, with or without a
``.git`` file, or while any ``acp_runtime_paths`` entry exists: the reaper, the
branch-holder release and ``post_task_reap`` read the hot record as the
ownership proof. ``restore`` moves an archived record back. Which readers see
the archive is documented in :mod:`scripts.orchestration.task_record_store`.

Settle and archive both hold the record's lock while they write or move it:
``delegate.worktree_lock`` for its checkout, the lock dispatch holds while it
publishes a record naming that checkout (a record naming no checkout locks its
own file). The lock is taken even for a missing path, because dispatch takes it
before it attaches a checkout. Under the lock the record is re-read; one whose
mtime or status changed since selection is skipped, because a live writer
touched it. Settle writes through ``delegate._write_state_atomic``. Archive
first renames the record to a private staging name, verifies that the file it
took is the one it checked, and puts it back if a writer replaced it in
between. No move ever replaces a file: archive, put-back and ``restore`` place
each file with ``os.link`` (which fails if the name is taken) before unlinking
the source, so a writer that created the destination first keeps its file. A
snapshot directory moves whole with one ``os.rename``, which fails if the
destination is a non-empty directory; it is never split between hot and
archive. A staged file that cannot be archived goes back to its hot name, or, if a writer
took that name, to a visible ``<name>.unplaced-<hex>`` in the archive that the
report names; no failure leaves a file at its hidden staging name.
"""

from __future__ import annotations

import argparse
import dataclasses
import errno
import json
import os
import re
import subprocess
import sys
import uuid
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

from scripts import delegate, secret_redactor
from scripts.common.git_context import sanitized_git_env
from scripts.orchestration import fleet_repos, task_record_store, worktree_claims

SETTLED_BY = "settle-stale"
ARCHIVE_DIR_NAME = task_record_store.ARCHIVE_DIR_NAME
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


# Environment that could redirect or reconfigure git beyond the checkout's own
# config: every ``GIT_CONFIG*`` channel (``GIT_CONFIG_COUNT``/``KEY_n``/``VALUE_n``,
# ``GIT_CONFIG_PARAMETERS``, config-file overrides), transport overrides, and
# tracing that would copy credentials to stderr. Credentials still come from the
# normal credential helper in the user's global config.
_GIT_ENV_DROP = frozenset(
    {
        "GIT_ASKPASS",
        "GIT_CURL_VERBOSE",
        "GIT_EXEC_PATH",
        "GIT_PROXY_COMMAND",
        "GIT_SSH",
        "GIT_SSH_COMMAND",
        "GIT_SSL_NO_VERIFY",
    }
)
_GIT_ENV_DROP_PREFIXES = ("GIT_CONFIG", "GIT_TRACE")


def _git_env() -> dict[str, str]:
    """:func:`sanitized_git_env` minus config injection, transport overrides and tracing."""
    env = {
        key: value
        for key, value in sanitized_git_env().items()
        if key not in _GIT_ENV_DROP and not key.startswith(_GIT_ENV_DROP_PREFIXES)
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git(
    args: list[str], *, cwd: Path, timeout: float, stdin: str | None = None
) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
            env=_git_env(),
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


# ``scheme://user:password@host`` -> ``scheme://host``.
_URL_USERINFO_RE = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)[^/\s'\"]*@")


def _scrub(text: str) -> str:
    """Strip URL userinfo and redact secrets from text bound for a report field or log."""
    return secret_redactor.redact_text(_URL_USERINFO_RE.sub(r"\1", text)) or ""


def _failure_detail(proc: subprocess.CompletedProcess[str]) -> str:
    """The last line git printed on failure, scrubbed, or its exit code."""
    lines = (proc.stderr or proc.stdout or "").strip().splitlines()
    return _scrub(lines[-1]) if lines else str(proc.returncode)


def _iter_record_files(tasks_dir: Path) -> list[Path]:
    """Hot task records only; settle and archive never read the archive."""
    return list(task_record_store.iter_task_records(tasks_dir, include_archive=False))


# ---------------------------------------------------------------------------
# Repository evidence (batched per repository)
# ---------------------------------------------------------------------------


SCAN_REF_ROOT = "refs/lu-stale-scan"
_SAFE_REPO_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


@dataclasses.dataclass(frozen=True)
class FetchTarget:
    """Where a repository's branches are fetched from, and the private ref namespace they land in."""

    key: str
    url: str

    @property
    def ref_prefix(self) -> str:
        return f"{SCAN_REF_ROOT}/{self.key}"


def fleet_fetch_target(slug: str) -> FetchTarget | None:
    """The fetch target of an allowlisted repository (``scripts/config/fleet_repos.yaml``).

    The URL is the canonical ``https://github.com/<slug>.git`` built from the
    allowlist, never the checkout's ``origin``: a remote's URL and refspec are
    checkout state that can drift or be narrowed, and the allowlist is the one
    place that says which repository a slug is. Credentials come from the
    normal git credential helper for ``https://github.com``.
    """
    for key, repo in fleet_repos.load_fleet_repos().items():
        if repo.github == slug and _SAFE_REPO_KEY_RE.match(key):
            return FetchTarget(key=key, url=f"https://github.com/{slug}.git")
    return None


@dataclasses.dataclass
class RepoFacts:
    """Batched git evidence for one repository checkout."""

    slug: str
    checkout: Path | None
    target: FetchTarget | None = None
    remote_heads: dict[str, str] | None = None
    local_branches: dict[str, str] | None = None
    error: str | None = None
    # Set when the fetch failed: refs from an older scan may be stale, so no
    # record of this repository may be classified from them.
    fetch_error: str | None = None


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


def _fetch_scan_refs(checkout: Path, target: FetchTarget) -> str | None:
    """Mirror the repository's branches into ``refs/lu-stale-scan/<key>/``; return why it failed, or ``None``.

    Reachability proves a commit is off the remote only when every remote
    branch is current, so the fetch never depends on the checkout's remote
    configuration: it names the allowlisted URL and an explicit refspec into a
    private namespace (``--prune`` drops branches deleted upstream), and runs
    with config injection scrubbed from the environment (:func:`_git_env`).
    ``url.<base>.insteadOf`` in the checkout's own config could still rewrite
    the URL, so the effective URL is checked first.
    """
    resolved = _git(["ls-remote", "--get-url", target.url], cwd=checkout, timeout=delegate.DEFAULT_GIT_TIMEOUT_S)
    if resolved is None or resolved.returncode != 0:
        return f"git ls-remote --get-url failed: {_failure_detail(resolved) if resolved else 'did not finish'}"
    effective = resolved.stdout.strip()
    if effective != target.url:
        return f"git config rewrites {target.url} to {_scrub(effective)} (url.*.insteadOf); refusing to fetch"
    proc = _git(
        [
            "fetch",
            "--no-tags",
            "--prune",
            "--no-write-fetch-head",
            target.url,
            f"+refs/heads/*:{target.ref_prefix}/*",
        ],
        cwd=checkout,
        timeout=delegate.DEFAULT_NETWORK_GIT_TIMEOUT_S,
    )
    if proc is None:
        return f"git fetch {target.url} did not finish within {delegate.DEFAULT_NETWORK_GIT_TIMEOUT_S:g}s"
    if proc.returncode != 0:
        return f"git fetch {target.url} failed: {_failure_detail(proc)}"[:300]
    return None


def collect_repo_facts(slug: str, checkout: Path | None, target: FetchTarget | None) -> RepoFacts:
    """One fetch into the scan namespace, then one ``for-each-ref`` over it and the local branches."""
    facts = RepoFacts(slug=slug, checkout=checkout, target=target)
    if checkout is None:
        facts.error = f"no local checkout for repository {slug}"
        return facts
    if target is None:
        facts.error = f"repository {slug} is not in scripts/config/fleet_repos.yaml"
        return facts
    facts.fetch_error = _fetch_scan_refs(checkout, target)
    if facts.fetch_error is not None:
        return facts
    listing = _git(
        ["for-each-ref", "--format=%(objectname) %(refname)", "refs/heads/", f"{target.ref_prefix}/"],
        cwd=checkout,
        timeout=delegate.DEFAULT_GIT_TIMEOUT_S,
    )
    if listing is None or listing.returncode != 0:
        facts.error = "git for-each-ref failed"
        return facts
    heads: dict[str, str] = {}
    branches: dict[str, str] = {}
    for line in listing.stdout.splitlines():
        sha, _, ref = line.partition(" ")
        if ref.startswith(f"{target.ref_prefix}/"):
            heads[ref.removeprefix(f"{target.ref_prefix}/")] = sha
        elif ref.startswith("refs/heads/"):
            branches[ref.removeprefix("refs/heads/")] = sha
    facts.remote_heads = heads
    facts.local_branches = branches
    return facts


def _commits_ahead_of_base(checkout: Path, base_ref: str, branch: str) -> int | None:
    proc = _git(
        ["rev-list", "--count", f"{base_ref}..refs/heads/{branch}"],
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
# Commit identity (one object lookup and one reachability pass per repository)
# ---------------------------------------------------------------------------

_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


def recorded_work_commits(record: Mapping[str, Any]) -> list[str]:
    """Commit ids a record names as its work.

    Delegate records carry no final head sha: ``worktree_base_sha`` is the
    base the task started from, not its work. The one commit a record does
    name is ``auto_finalize.commit_sha``, the commit delegate made from a dirty
    tree at exit.
    """
    auto_finalize = record.get("auto_finalize")
    raw = auto_finalize.get("commit_sha") if isinstance(auto_finalize, dict) else None
    if isinstance(raw, str) and _SHA_RE.match(raw.strip().lower()):
        return [raw.strip().lower()]
    return []


@dataclasses.dataclass
class CommitFacts:
    """Which recorded commits exist locally and which any ref still reaches."""

    resolved: dict[str, str | None]
    reachable: set[str]
    error: str | None = None


def collect_commit_facts(checkout: Path, shas: Iterable[str]) -> CommitFacts:
    """Resolve ``shas`` with one ``git cat-file --batch-check`` and one ``git rev-list --all``.

    ``rev-list --all`` walks every ref (local branches, tags, remote-tracking
    refs, the ``refs/lu-stale-scan`` namespace, stash) plus the HEAD of every
    linked worktree, so a commit it does not list is held by no ref under any
    name. Callers run it only after :func:`_fetch_scan_refs` succeeded, so the
    scan namespace holds every current remote branch and one that descends
    from the commit is seen.
    """
    wanted = sorted(set(shas))
    facts = CommitFacts(resolved={}, reachable=set())
    if not wanted:
        return facts
    lookup = _git(
        ["cat-file", "--batch-check=%(objectname) %(objecttype)"],
        cwd=checkout,
        timeout=delegate.DEFAULT_GIT_TIMEOUT_S,
        stdin="".join(f"{sha}^{{commit}}\n" for sha in wanted),
    )
    lines = lookup.stdout.splitlines() if lookup is not None and lookup.returncode == 0 else []
    if len(lines) != len(wanted):
        facts.error = "git cat-file --batch-check failed"
        return facts
    for sha, line in zip(wanted, lines, strict=True):
        parts = line.split()
        facts.resolved[sha] = parts[0] if len(parts) == 2 and parts[1] == "commit" else None
    if not any(facts.resolved.values()):
        return facts
    walk = _git(["rev-list", "--all"], cwd=checkout, timeout=delegate.DEFAULT_GIT_TIMEOUT_S)
    if walk is None or walk.returncode != 0:
        facts.error = "git rev-list --all failed"
        return facts
    facts.reachable = set(walk.stdout.split())
    return facts


def _refs_containing(checkout: Path, sha: str) -> list[str]:
    proc = _git(
        ["for-each-ref", "--format=%(refname)", "--contains", sha],
        cwd=checkout,
        timeout=delegate.DEFAULT_GIT_TIMEOUT_S,
    )
    return proc.stdout.split() if proc is not None and proc.returncode == 0 else []


def _is_ancestor(checkout: Path, ancestor: str, descendant: str) -> bool:
    """True only when git proves ``ancestor`` is in ``descendant``'s history."""
    proc = _git(
        ["merge-base", "--is-ancestor", ancestor, descendant],
        cwd=checkout,
        timeout=delegate.DEFAULT_GIT_TIMEOUT_S,
    )
    return proc is not None and proc.returncode == 0


# ---------------------------------------------------------------------------
# Pull request evidence (one paged REST list per repository)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class PullIndex:
    """Merged same-repository pull requests grouped by head branch and by commit.

    ``merged_by_sha`` indexes each pull request under its head sha and its
    merge commit sha. Pages are listed newest-``updated_at`` first.
    ``covered_since`` is ``None`` when the listing reached every pull request
    any candidate could need; otherwise only pull requests updated at or after
    it were seen.
    """

    merged_by_branch: dict[str, list[dict[str, Any]]]
    merged_by_sha: dict[str, list[dict[str, Any]]] = dataclasses.field(default_factory=lambda: defaultdict(list))
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
        raise RuntimeError(f"gh api {endpoint} failed: {_failure_detail(proc)}")
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
            index.error = _scrub(f"{type(exc).__name__}: {exc}")[:300]
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
            entry = {
                "number": pull.get("number"),
                "url": pull.get("html_url"),
                "merged_at": pull.get("merged_at"),
                "head_sha": head.get("sha"),
                "merge_commit_sha": pull.get("merge_commit_sha"),
            }
            index.merged_by_branch[head["ref"]].append(entry)
            for sha in {entry["head_sha"], entry["merge_commit_sha"]}:
                if isinstance(sha, str) and sha:
                    index.merged_by_sha[sha.lower()].append(entry)
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
    # Full shas of the recorded commits, set once no ref is proven to hold them.
    work_commits: list[str] = dataclasses.field(default_factory=list)

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


def _is_zero(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value == 0


def _classify_one(candidate: Candidate, facts: RepoFacts | None) -> None:
    """Classify one record from branch-name and worktree evidence.

    A record that reaches class C here is provisional when it names a commit:
    :func:`_apply_commit_facts` keeps it in C only if no ref still holds that
    commit. Without a recorded commit a branch rename cannot be ruled out, so C
    needs a clean exit that left nothing to lose (no commits, clean tree).
    """
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
            "worktree_dirty_on_exit": record.get("worktree_dirty_on_exit"),
            "recorded_commits": recorded_work_commits(record),
        }
    )
    if not isinstance(slug, str) or facts is None:
        candidate.klass, candidate.skip_reason = "D", "record has no known repository"
        return
    if facts.fetch_error is not None:
        evidence["fetch_failed"] = facts.fetch_error
        candidate.klass = "D"
        candidate.skip_reason = f"fetch_failed: {facts.fetch_error}; stale remote refs cannot prove the work gone"
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
        elif facts.checkout is not None and facts.target is not None:
            base = _normalize_branch(record.get("worktree_base")) or "main"
            evidence["local_commits_ahead_of_base"] = _commits_ahead_of_base(
                facts.checkout, f"{facts.target.ref_prefix}/{base}", branch
            )

    if on_origin:
        candidate.klass = "A"
        candidate.skip_reason = "branch still on origin; no finalizer publishes a branch without its worktree"
    elif local_sha is not None or dirty in (True, None):
        candidate.klass = "B"
        candidate.skip_reason = "possible unpushed work: " + (
            "local branch not on origin" if local_sha is not None else "worktree dirty or unreadable"
        )
    elif worktree_exists:
        candidate.klass = "D"
        candidate.skip_reason = "clean worktree exists without a local or remote branch"
    elif evidence["recorded_commits"]:
        candidate.klass = "C"
    elif not _is_zero(record.get("commits_ahead")):
        candidate.klass = "D"
        candidate.skip_reason = (
            f"commits_ahead={record.get('commits_ahead')} but the record names no commit; "
            "a renamed branch could still hold the work"
        )
    elif record.get("worktree_dirty_on_exit") is not False:
        candidate.klass = "D"
        candidate.skip_reason = (
            "uncommitted work at exit and the record names no commit; "
            "it could since have been committed under another branch name"
        )
    else:
        candidate.klass = "C"


def _apply_commit_facts(candidate: Candidate, commits: CommitFacts, facts: RepoFacts) -> None:
    """Keep a provisional class C record only when no ref holds any recorded commit."""
    evidence = candidate.evidence
    recorded: list[str] = evidence["recorded_commits"]
    if commits.error is not None:
        candidate.klass, candidate.skip_reason = "D", f"commit evidence unavailable: {commits.error}"
        return
    missing = [sha for sha in recorded if not commits.resolved.get(sha)]
    if missing:
        candidate.klass = "D"
        candidate.skip_reason = (
            f"recorded commit {missing[0]} is not in the local object store; cannot prove it is gone"
        )
        return
    full = [commits.resolved[sha] or sha for sha in recorded]
    candidate.work_commits = full
    held = [sha for sha in full if sha in commits.reachable]
    published = sorted(name for name, head in (facts.remote_heads or {}).items() if head in full)
    refs = sorted({ref for sha in held for ref in _refs_containing(facts.checkout, sha)}) if facts.checkout else []
    local_refs = [ref for ref in refs if not ref.startswith(("refs/remotes/", f"{SCAN_REF_ROOT}/"))]
    evidence.update({"recorded_commits_reachable": bool(held), "refs_containing_commit": refs})
    if published:
        evidence["origin_heads_at_commit"] = published
    if held and (local_refs or not refs):
        candidate.klass = "B"
        holder = ", ".join(local_refs) if local_refs else "a worktree HEAD"
        candidate.skip_reason = f"possible unpushed work: {holder} still holds the recorded commit"
    elif held or published:
        candidate.klass = "A"
        candidate.skip_reason = "recorded commit still on origin under " + ", ".join(published or refs)


def _merged_since(pull: Mapping[str, Any], start: datetime | None) -> bool:
    if start is None:
        return True
    merged_at = _parse_ts(pull.get("merged_at"))
    return merged_at is not None and merged_at >= start


def _decide_outcome(candidate: Candidate, index: PullIndex | None, checkout: Path | None) -> None:
    """Pick the terminal status of an orphaned (class C) record.

    ``done`` needs a merged pull request tied to this task by commit identity:
    its head or merge commit is a recorded commit, or its head descends from
    one. A merged pull request that only shares the branch name may be a later
    task reusing the ref, so that record moves to class D rather than being
    guessed.
    """
    if index is None or index.error is not None:
        candidate.skip_reason = f"pull request list unavailable: {index.error if index else 'not fetched'}"
        return
    start = candidate.task_start
    if index.covered_since is not None and (start is None or start < index.covered_since):
        candidate.skip_reason = "pull request list does not reach back to the task start; raise --max-pr-pages"
        return
    branch = candidate.evidence.get("branch")
    same_branch = [pull for pull in index.merged_by_branch.get(branch or "", []) if _merged_since(pull, start)]
    tied = [pull for sha in candidate.work_commits for pull in index.merged_by_sha.get(sha, [])]
    if not tied and checkout is not None:
        tied = [
            pull
            for pull in same_branch
            if isinstance(pull.get("head_sha"), str)
            and any(_is_ancestor(checkout, sha, pull["head_sha"]) for sha in candidate.work_commits)
        ]
    record = candidate.record
    if tied:
        pull = max(tied, key=lambda item: str(item.get("merged_at") or ""))
        candidate.outcome = "done"
        candidate.merged_pr = pull
        candidate.settle_reason = f"orphaned: PR #{pull.get('number')} merged this task's recorded commit"
    elif same_branch:
        candidate.klass = "D"
        candidate.evidence["untied_merged_prs"] = [pull.get("number") for pull in same_branch]
        numbers = ", ".join(f"#{pull.get('number')}" for pull in same_branch)
        candidate.skip_reason = f"ambiguous: merged PR {numbers} reuses branch {branch} but " + (
            "carries none of this task's recorded commits"
            if candidate.work_commits
            else "the record names no commit that ties it to this task"
        )
    elif not candidate.work_commits and _is_zero(record.get("commits_ahead")) and record.get("returncode") == 0:
        candidate.outcome = delegate._NO_DELIVERABLE_STATUS
        candidate.settle_reason = "orphaned: clean exit with no commits; worktree and branch gone"
    else:
        candidate.outcome = "failed"
        candidate.settle_reason = (
            f"orphaned: returncode={record.get('returncode')} commits_ahead={record.get('commits_ahead')}, "
            "no merged pull request carries its work; worktree and branch gone"
            + ("; no ref holds the recorded commit" if candidate.work_commits else "")
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
            facts_by_slug[slug] = collect_repo_facts(slug, repo_checkouts.get(slug), fleet_fetch_target(slug))
        _classify_one(candidate, facts_by_slug.get(slug) if isinstance(slug, str) else None)

    naming_commits: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        if candidate.klass == "C" and candidate.evidence["recorded_commits"]:
            naming_commits[str(candidate.record.get("repository"))].append(candidate)
    for slug, group in naming_commits.items():
        facts = facts_by_slug[slug]
        shas = [sha for candidate in group for sha in candidate.evidence["recorded_commits"]]
        commit_facts = (
            collect_commit_facts(facts.checkout, shas)
            if facts.checkout is not None
            else CommitFacts(resolved={}, reachable=set(), error=f"no local checkout for repository {slug}")
        )
        for candidate in group:
            _apply_commit_facts(candidate, commit_facts, facts)

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
            _decide_outcome(candidate, indexes[slug], facts_by_slug[slug].checkout)
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
        with delegate.worktree_lock(_record_lock_target(candidate.record, candidate.path), timeout_s=lock_timeout_s):
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
            if os.path.lexists(str(candidate.evidence["worktree_path"])):
                candidate.action, candidate.skip_reason = "skipped", "worktree path reappeared since classification"
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


def _owned_checkout(record: Mapping[str, Any]) -> str | None:
    """The checkout a record may still own: ``worktree_path``, else a non-primary ``cwd``.

    Read-only tasks run in a repository's primary checkout, whose ``.git`` is a
    directory. No task owns that checkout, so it never keeps a record hot.
    """
    raw = record.get("worktree_path")
    if isinstance(raw, str) and raw.strip():
        return raw
    cwd = record.get("cwd")
    if isinstance(cwd, str) and cwd.strip() and not (Path(cwd) / ".git").is_dir():
        return cwd
    return None


def keep_hot_reason(record: Mapping[str, Any]) -> str | None:
    """Why a terminal record must stay in the hot directory, or ``None``.

    The reaper and the branch-holder release read the hot record as the
    ownership proof for its checkout, and ``post_task_reap`` finds a task's ACP
    runtime worktrees only through ``acp_runtime_paths`` in the hot record. A
    path that still exists keeps the record hot whether or not it holds a
    ``.git`` file.
    """
    checkout = _owned_checkout(record)
    if checkout is not None and os.path.lexists(checkout):
        return "worktree path still exists"
    acp_paths = record.get("acp_runtime_paths")
    if isinstance(acp_paths, list) and any(item and os.path.lexists(str(item)) for item in acp_paths):
        return "ACP runtime path still exists"
    return None


def _record_lock_target(record: Mapping[str, Any], record_path: Path) -> str:
    """The lock settle and archive hold while they rewrite or move a record.

    It is the lock of the record's checkout, which dispatch holds while it
    publishes a record naming that checkout and every remover holds while it
    removes one. A record that names no checkout locks its own file, so two
    runs of this tool never move the same record at once.
    """
    return _owned_checkout(record) or str(record_path)


def _read_pinned(path: Path) -> tuple[dict[str, Any] | None, os.stat_result]:
    """Read a record and the ``stat`` of the very inode its bytes came from."""
    with path.open("rb") as handle:
        stat = os.fstat(handle.fileno())
        raw = handle.read()
    try:
        record = json.loads(raw)
    except (ValueError, RecursionError):
        return None, stat
    return (record if isinstance(record, dict) else None), stat


class _RecordReplaced(Exception):
    """A writer replaced the record between the final check and the move."""


# ``rename(2)`` of a directory fails when the destination is a non-empty
# directory (ENOTEMPTY, or EEXIST, which POSIX also allows) or is not a
# directory (ENOTDIR), and replaces only an empty directory. POSIX rename(),
# Linux rename(2) and macOS rename(2) (ERRORS: ENOTEMPTY, ENOTDIR) all specify
# this, so a directory moves in one atomic step that neither destroys data
# nor splits the directory.
_DIR_TAKEN_ERRNOS = frozenset({errno.ENOTEMPTY, errno.EEXIST, errno.ENOTDIR})


def _move_no_replace(src: Path, dst: Path) -> None:
    """Move ``src`` to ``dst`` without ever replacing what is at ``dst``.

    ``src`` must be a path no writer replaces, since it is unlinked after the
    copy lands: a staging name, or an archived file. A file is hard-linked to
    ``dst`` (``os.link`` raises :class:`FileExistsError`, atomically, if the
    name is taken) and then unlinked. A directory moves whole with one
    ``os.rename`` (see ``_DIR_TAKEN_ERRNOS``); if ``dst`` holds anything it
    raises :class:`FileExistsError` and ``src`` stays whole where it was.
    """
    if src.is_dir() and not src.is_symlink():
        try:
            os.rename(src, dst)
        except OSError as exc:
            if exc.errno in _DIR_TAKEN_ERRNOS:
                raise FileExistsError(exc.errno, f"{dst} already exists", str(dst)) from exc
            raise
        return
    os.link(src, dst, follow_symlinks=False)
    os.unlink(src)


def _stage(path: Path, staging_dir: Path) -> Path:
    """Take whatever ``path`` holds right now to a private name nobody else writes."""
    staged = staging_dir / f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.moving"
    os.rename(path, staged)
    return staged


def _place(staged: Path, dest_dir: Path, name: str, stamp: str) -> Path:
    """Move a staged file into ``dest_dir`` as ``name``, else its stamped name; never overwrite."""
    first = dest_dir / name
    for dest in (first, delegate._archived_artifact_path(first, stamp)):
        try:
            _move_no_replace(staged, dest)
        except FileExistsError:
            continue
        return dest
    raise FileExistsError(f"archive already holds {name} and its stamped name")


class _Unplaced(OSError):
    """A staged file was not archived; it went back to ``home`` or was parked at ``where``."""

    def __init__(self, reason: str, *, home: Path, where: Path):
        super().__init__(reason)
        self.reason, self.home, self.where = reason, home, where


def _unstage(staged: Path, home: Path, dest_dir: Path) -> Path:
    """Return a staged file to ``home`` without replacing anything; else park it where people look.

    ``home`` is the name it was taken from. If a writer has taken that name
    since, the file goes to ``<dest_dir>/<name>.unplaced-<hex>``, a name no
    record reader globs for. A directory moves whole, so it is never split
    between the two. Returns where the file now is: the staging name only if
    both moves failed.
    """
    for target in (home, dest_dir / f"{home.name}.unplaced-{uuid.uuid4().hex[:12]}"):
        try:
            _move_no_replace(staged, target)
        except OSError:
            continue
        return target
    return staged


def _place_or_unstage(staged: Path, home: Path, dest_dir: Path, name: str, stamp: str) -> Path:
    """:func:`_place` a staged file; on any failure :func:`_unstage` it before raising.

    An :class:`OSError` becomes :class:`_Unplaced`, which says where the file is.
    """
    try:
        return _place(staged, dest_dir, name, stamp)
    except BaseException as exc:
        where = _unstage(staged, home, dest_dir)
        if isinstance(exc, OSError):
            raise _Unplaced(str(exc), home=home, where=where) from exc
        raise


def _move_group(
    record_path: Path, dest_dir: Path, stamp: str, *, checked: os.stat_result
) -> tuple[list[str], list[str]]:
    """Move a record then its sidecars; never overwrite a destination.

    Each file is first renamed to a private staging name, which takes it
    atomically whatever a writer does next. ``checked`` is the ``stat`` of the
    record as last verified. If the staged record is not that file, a writer
    replaced it in between: it is put back and :class:`_RecordReplaced` is
    raised before any sidecar moves. No failure leaves a file at its staging
    name: it goes back to its hot name or, if a writer took that name, to a
    visible ``.unplaced-<hex>`` name in the archive (:class:`_Unplaced` says
    which). Returns the names archived and a note for each sidecar that was not.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    sidecars = [record_path.with_name(name) for name in _sidecar_names(record_path.stem)]
    staged = _stage(record_path, dest_dir)
    try:
        landed = os.lstat(staged)
        replaced = (landed.st_ino, landed.st_mtime_ns) != (checked.st_ino, checked.st_mtime_ns)
    except BaseException as exc:
        where = _unstage(staged, record_path, dest_dir)
        if isinstance(exc, OSError):
            raise _Unplaced(str(exc), home=record_path, where=where) from exc
        raise
    if replaced:
        where = _unstage(staged, record_path, dest_dir)
        if where == record_path:
            raise _RecordReplaced
        raise _Unplaced("record replaced during the move and rewritten again", home=record_path, where=where)
    record_dest = _place_or_unstage(staged, record_path, dest_dir, record_path.name, stamp)
    moved, problems = [record_dest.name], []
    # A renamed record takes its sidecars' names along, so they still pair up.
    for sidecar, name in zip(sidecars, _sidecar_names(record_dest.stem), strict=True):
        try:
            staged = _stage(sidecar, dest_dir)
        except FileNotFoundError:
            continue
        except OSError as exc:
            problems.append(f"{sidecar.name} not archived: {exc}")
            continue
        try:
            moved.append(_place_or_unstage(staged, sidecar, dest_dir, name, stamp).name)
        except _Unplaced as exc:
            problems.append(f"{sidecar.name} not archived ({exc.reason}); left at {exc.where}")
    return moved, problems


def _archive_one(
    path: Path,
    row: dict[str, Any],
    *,
    selected_mtime_ns: int,
    lock_target: str,
    archive_dir: Path,
    stamp: str,
    lock_timeout_s: float,
    before_move: Callable[[Path], None] | None,
) -> None:
    """Move one record under its lock after re-checking it, or record why not."""
    try:
        with delegate.worktree_lock(lock_target, timeout_s=lock_timeout_s):
            if before_move is not None:
                before_move(path)
            current, stat = _read_pinned(path)
            if stat.st_mtime_ns != selected_mtime_ns:
                row["action"], row["skip_reason"] = "skipped", "record changed since selection"
            elif current is None or current.get("status") not in worktree_claims.RELEASED_TASK_STATUSES:
                row["action"], row["skip_reason"] = "skipped", "record no longer terminal"
            elif (reason := keep_hot_reason(current)) is not None:
                row["action"], row["skip_reason"] = "skipped", reason
            else:
                row["moved"], problems = _move_group(path, archive_dir, stamp, checked=stat)
                row["action"] = "error" if problems else "archived"
                if problems:
                    row["error"] = "record archived; " + "; ".join(problems)
    except worktree_claims.WorktreeLockError as exc:
        row["action"], row["skip_reason"] = "skipped", worktree_claims.lock_refusal(exc)
    except FileNotFoundError:
        row["action"], row["skip_reason"] = "skipped", "record moved since selection"
    except _RecordReplaced:
        row["action"], row["skip_reason"] = "skipped", "record replaced during the move; put back"
    except _Unplaced as exc:
        if exc.where == exc.home:
            row["action"], row["skip_reason"] = "skipped", f"{exc.reason}; record left in place"
        else:
            row["action"], row["error"] = "error", f"{exc.reason}; record left at {exc.where}"
            row["recover_path"] = str(exc.where)
    except OSError as exc:
        row["action"], row["error"] = "error", f"{type(exc).__name__}: {exc}"


def archive_terminal(
    tasks_dir: Path,
    *,
    min_age_days: float = DEFAULT_ARCHIVE_MIN_AGE_DAYS,
    apply: bool = False,
    lock_timeout_s: float = DEFAULT_LOCK_TIMEOUT_S,
    now: datetime | None = None,
    before_move: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    """Move old terminal records and their sidecars into ``<tasks_dir>/archive/``.

    Each move holds the record's lock (:func:`_record_lock_target`) and first
    re-reads the record: it is skipped if its mtime changed since selection,
    its status is no longer terminal, or it still owns a path
    (:func:`keep_hot_reason`). ``before_move`` is a test seam called under the
    lock, before that re-check.
    """
    now = now or datetime.now(UTC)
    archive_dir = tasks_dir / ARCHIVE_DIR_NAME
    stamp = delegate._archive_stamp()
    rows: list[dict[str, Any]] = []
    kept: Counter[str] = Counter()
    younger = 0
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
        if (reason := keep_hot_reason(record)) is not None:
            kept[reason] += 1
            continue
        row: dict[str, Any] = {
            "file": path.name,
            "status": record.get("status"),
            "age_days": round(age, 1),
            "sidecars": [sidecar.name for sidecar in sidecar_paths(path)],
            "action": "would_archive",
        }
        if apply:
            _archive_one(
                path,
                row,
                selected_mtime_ns=mtime_ns,
                lock_target=_record_lock_target(record, path),
                archive_dir=archive_dir,
                stamp=stamp,
                lock_timeout_s=lock_timeout_s,
                before_move=before_move,
            )
        rows.append(row)
    return {
        "command": "archive",
        "mode": "apply" if apply else "dry-run",
        "tasks_dir": str(tasks_dir),
        "archive_dir": str(archive_dir),
        "min_age_days": min_age_days,
        "selected": len(rows),
        "younger_left_alone": younger,
        "kept_hot": dict(kept),
        "actions": dict(Counter(row["action"] for row in rows)),
        "by_status": dict(Counter(str(row["status"]) for row in rows)),
        "records": rows,
    }


def _restore_group(group: list[Path], tasks_dir: Path, row: dict[str, Any]) -> None:
    """Move an archived record, then its sidecars, back without replacing a hot file.

    The clash check before this is advisory: a writer can create the hot record
    after it. Every move is :func:`_move_no_replace`, so that writer's file is
    kept and the archived copy (a snapshot directory whole) stays where it is.
    """
    record_path, *sidecars = group
    try:
        _move_no_replace(record_path, tasks_dir / record_path.name)
    except FileExistsError:
        row["action"] = "skipped"
        row["skip_reason"] = f"a writer created {record_path.name} in the hot directory first; archived copy kept"
        return
    except OSError as exc:
        row["action"], row["error"] = "error", f"{type(exc).__name__}: {exc}"
        return
    kept: list[str] = []
    try:
        for sidecar in sidecars:
            try:
                _move_no_replace(sidecar, tasks_dir / sidecar.name)
            except FileExistsError:
                kept.append(str(sidecar))
    except OSError as exc:
        row["action"], row["error"] = "error", f"{type(exc).__name__}: {exc}"
        return
    row["action"] = "restored"
    if kept:
        row["kept_in_archive"] = kept
        row["note"] = "a writer created these in the hot directory first; archived copies kept"


def restore_archived(tasks_dir: Path, names: Iterable[str], *, apply: bool = False) -> dict[str, Any]:
    """Move archived records (by task id or file name) and their sidecars back to the hot directory."""
    archive_dir = tasks_dir / ARCHIVE_DIR_NAME
    rows: list[dict[str, Any]] = []
    for name in names:
        record_path = (
            archive_dir / name
            if name.endswith(".json")
            else task_record_store.archived_task_record_path(tasks_dir, name)
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
                _restore_group(group, tasks_dir, row)
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
    "  scripts/orchestration/task_record_store.py (hot/archive layout; which readers see the archive),\n"
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
            "Classes (evidence: one git fetch per repository of every branch of the allowlisted\n"
            "https://github.com/<slug>.git into refs/lu-stale-scan/<repo-key>/ (dry run too; it writes\n"
            "only that namespace), a ref listing and, for records naming a commit, one cat-file + one\n"
            "rev-list --all per repository; worktree probes; one paged REST pull list per repository;\n"
            "never GraphQL or per-record GitHub calls):\n"
            "  A  branch, or a recorded commit, still on origin          report only\n"
            "  B  local branch or a ref holding a recorded commit, or    never modified\n"
            "     worktree dirty\n"
            "  C  worktree, branches and the work all gone: a recorded   settled\n"
            "     commit no ref holds, or a clean exit with no commits\n"
            "  D  anything else: evidence unavailable, a failed fetch    never modified\n"
            "     (fetch_failed), commits or a dirty exit with no\n"
            "     recorded commit, a PR that only reuses the branch name\n"
            "Class C settles to: done (+merged_pr) when a merged same-repository PR carries a recorded\n"
            "commit (head, merge commit, or a head descending from it); no_deliverable for a clean exit\n"
            "with no commits; failed otherwise. Each write adds settled_by='settle-stale', settled_at,\n"
            "settle_reason, settle_previous_status and settle_evidence, holds the record's lock, and is\n"
            "skipped if the record's mtime or status changed since classification.\n"
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

    def lock_timeout(sub: argparse.ArgumentParser) -> None:
        sub.add_argument(
            "--lock-timeout",
            type=float,
            default=DEFAULT_LOCK_TIMEOUT_S,
            help=f"Seconds to wait for a record's lock before skipping it (default: {DEFAULT_LOCK_TIMEOUT_S:g}).",
        )

    lock_timeout(settle)

    archive = commands.add_parser(
        "archive",
        help="Move old terminal records and their sidecars into batch_state/tasks/archive/.",
        description=(
            "Move terminal records (done, failed, no_deliverable, timeout, rate_limited, cancelled, crashed,\n"
            "dry_run, reaped) older than --min-age-days, with their .result and .snapshots sidecars, into\n"
            "batch_state/tasks/archive/. A record stays in place while its checkout path or any\n"
            "acp_runtime_paths entry still exists. Each move holds the record's lock and re-checks its\n"
            "mtime and status first."
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
    lock_timeout(archive)

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
        report = archive_terminal(
            tasks_dir, min_age_days=args.min_age_days, apply=args.apply, lock_timeout_s=args.lock_timeout
        )
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
