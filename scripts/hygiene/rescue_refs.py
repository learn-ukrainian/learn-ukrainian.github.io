"""Classify ``refs/reaper-rescue/*`` and delete only refs already preserved elsewhere.

Dry-run is the default. ``--apply`` deletes CONTAINED and PATCH-EQUIVALENT refs
only, under the reaper lock, after a journal line and a compare-and-delete.
UNIQUE refs are never deleted. Do not use this tool for ``rescue/*`` branches,
retention policy, or any ref outside ``refs/reaper-rescue/``.

The patch-id window is ``origin/main`` commits with a committer date after
2026-08-01 (``git rev-list --since=2026-08-01``), the same bound as the
2026-10-16 census. A matching commit older than that window is not a match, so
the rescue ref stays UNIQUE. Main's patch-ids are loaded once per run.

Patch equivalence uses :func:`scripts.hygiene.branch_sweep._load_patch_ids`
with ``git patch-id --verbatim`` and ``git --no-lazy-fetch``. Verbatim keeps
whitespace and line numbers, so two Python files that differ only by
indentation do not match. Every off-main commit must match a distinct
in-window main commit: a patch-id that occurs twice on the rescue tip and
once on main is not a match.

The run refreshes origin first. ``git fetch origin`` must exit 0, or
``FETCH_HEAD`` must already hold a non-empty recorded fetch younger than
:data:`ORIGIN_FETCH_MAX_AGE_S`. Otherwise every ref stays UNIQUE and the
creation guard still pins the tip. Under the lock, immediately before each
deletion, the preserving origin ref must still exist at the recorded SHA and,
for ancestry, still contain the tip.

A shallow repository, a graft file, or a replace ref means the commit walk is
incomplete, so nothing is deletable. A missing blob needed for a patch-id is
UNIQUE, never a match and never an empty diff. Containment is different:
parent links live on the commit objects, so a ``blob:none`` clone may omit
blobs and still prove that a tip is an ancestor of a fresh ``origin/main``
when that commit walk itself is complete.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from scripts.common.git_context import sanitized_git_env
from scripts.hygiene import branch_sweep
from scripts.orchestration import reap_worktrees as reaper
from scripts.orchestration.reaper_lifecycle import append_journal

CLASS_CONTAINED = "CONTAINED"
CLASS_PATCH = "PATCH-EQUIVALENT"
CLASS_UNIQUE = "UNIQUE"
DELETABLE = frozenset({CLASS_CONTAINED, CLASS_PATCH})
# git --since is "after this date". Commits at or before 2026-08-01 00:00:00
# are outside the window and cannot prove a rescue commit.
MAIN_PATCH_SINCE = "2026-08-01"
# A non-empty FETCH_HEAD younger than this is a recorded successful fetch.
# A failed fetch leaves an empty file and does not qualify.
ORIGIN_FETCH_MAX_AGE_S = 120
_RESCUE_PREFIX = "refs/reaper-rescue/"
_ORIGIN_MAIN = "refs/remotes/origin/main"
# 40 commits of `git log -p | git patch-id` took 0.42s on 2026-10-16.
# Stay under that rate so a creation check fits the reap lock.
_PATCH_SECONDS_PER_COMMIT = 0.02
DeleteFn = Callable[[Path, str, str], None]


class RescueRefError(RuntimeError):
    """The sweep cannot prove a deletion, so it deletes nothing further."""


class RescueRefChanged(RescueRefError):
    """``git update-ref -d`` refused because the ref no longer has the expected SHA."""


@dataclass(frozen=True)
class Preservation:
    classification: str
    proof: str

    @property
    def deletable(self) -> bool:
        return self.classification in DELETABLE


@dataclass(frozen=True)
class RescueRef:
    ref: str
    sha: str
    classification: str
    proof: str
    preserving_ref: str = ""
    preserving_sha: str = ""


@dataclass(frozen=True)
class Summary:
    counts: dict[str, int]
    elapsed_s: float
    listing: Path
    deleted: int = 0
    skipped: int = 0


def decide(
    *,
    on_main: bool,
    other_origin_ref: str | None,
    unique: list[str],
    patch_of: dict[str, str | None],
    main_ids: set[str],
    main_counts: dict[str, int] | None = None,
    since: str = MAIN_PATCH_SINCE,
) -> Preservation:
    """One classification for the batch tool and the reaper's creation guard."""
    if on_main:
        return Preservation(CLASS_CONTAINED, "tip is an ancestor of origin/main")
    if other_origin_ref:
        return Preservation(CLASS_CONTAINED, f"tip is reachable from {other_origin_ref}")
    if not unique:
        return Preservation(CLASS_CONTAINED, "tip is an ancestor of origin/main")
    missing = [sha for sha in unique if not patch_of.get(sha)]
    if missing:
        return Preservation(CLASS_UNIQUE, f"commit {missing[0]} emitted no patch-id")
    unmatched = [sha for sha in unique if patch_of[sha] not in main_ids]
    if unmatched:
        return Preservation(
            CLASS_UNIQUE,
            (
                f"{len(unmatched)} of {len(unique)} off-main commits have no verbatim patch-id "
                f"on origin/main since {since}; first {unmatched[0]}"
            ),
        )
    counts = main_counts if main_counts is not None else {patch: 1 for patch in main_ids}
    # Occurrence counts apply only to commits that emitted a patch-id.
    present = [sha for sha in unique if patch_of.get(sha)]
    need: dict[str, int] = {}
    for sha in present:
        patch = patch_of[sha]
        if patch is None:
            continue
        need[patch] = need.get(patch, 0) + 1
    short = [sha for sha in present if (patch := patch_of[sha]) is not None and need[patch] > counts.get(patch, 0)]
    if short:
        return Preservation(
            CLASS_UNIQUE,
            (
                f"{len(short)} of {len(unique)} off-main commits repeat a verbatim patch-id "
                f"more often than origin/main since {since}; first {short[0]}"
            ),
        )
    return Preservation(
        CLASS_PATCH,
        (f"all {len(unique)} off-main commits match a distinct verbatim patch-id on origin/main since {since}"),
    )


def _checkout(repo: Path) -> Path | None:
    result = branch_sweep._git(repo, "rev-parse", "--show-toplevel", timeout=10)
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    if not text:
        return None
    return Path(text).resolve()


def _is_ancestor(repo: Path, tip: str, descendant: str, *, timeout: int) -> bool:
    result = branch_sweep._git(repo, "merge-base", "--is-ancestor", tip, descendant, timeout=timeout)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    detail = (result.stderr or result.stdout).strip()
    raise RuntimeError(f"git merge-base --is-ancestor failed: {detail}")


def _origin_ref_containing(repo: Path, tip: str, *, timeout: int) -> str | None:
    result = branch_sweep._git(
        repo,
        "for-each-ref",
        f"--contains={tip}",
        "--format=%(refname)",
        "refs/remotes/origin",
        timeout=timeout,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"git for-each-ref --contains failed: {detail}")
    names = [line for line in result.stdout.splitlines() if line]
    if any(not name.startswith("refs/remotes/origin/") for name in names):
        raise RuntimeError("git for-each-ref --contains returned an unexpected ref")
    others = [name for name in names if name != "refs/remotes/origin/main"]
    if others:
        return others[0]
    return names[0] if names else None


def _merge_base(repo: Path, tip: str, *, timeout: int) -> str | None:
    result = branch_sweep._git(repo, "merge-base", tip, "refs/remotes/origin/main", timeout=timeout)
    if result.returncode != 0:
        return None
    base = result.stdout.strip()
    if not branch_sweep.SHA_RE.fullmatch(base):
        raise RuntimeError("git merge-base returned an invalid SHA")
    return base


def _seconds(deadline: float) -> int:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise subprocess.TimeoutExpired(["rescue-refs"], 0)
    return max(1, int(remaining))


def _fetch_head_path(repo: Path) -> Path | None:
    result = branch_sweep._git(
        repo,
        "rev-parse",
        "--path-format=absolute",
        "--git-path",
        "FETCH_HEAD",
        timeout=10,
    )
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    if not text:
        return None
    return Path(text)


def _recorded_fetch_is_fresh(repo: Path) -> bool:
    """True when FETCH_HEAD is a non-empty successful fetch inside the bound."""
    path = _fetch_head_path(repo)
    if path is None or not path.is_file():
        return False
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_size <= 0:
            return False
        if time.time() - info.st_mtime >= ORIGIN_FETCH_MAX_AGE_S:
            return False
        # A failed fetch creates an empty file. Read a bounded prefix and require
        # the leading object name a successful fetch writes.
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError:
        return False
    try:
        chunk = os.read(descriptor, 80)
    finally:
        os.close(descriptor)
    token = chunk.split()[0].decode("ascii", errors="replace") if chunk.split() else ""
    return branch_sweep.SHA_RE.fullmatch(token) is not None


def refresh_origin(repo: Path, *, timeout: int) -> tuple[bool, str]:
    """Fetch origin, or accept a recorded fetch younger than the stated bound.

    A non-zero fetch does not become fresh because the attempt touched
    ``FETCH_HEAD``. Only a fetch that exited 0, or a non-empty recorded
    fetch that was already young before this call, counts.
    """
    if _recorded_fetch_is_fresh(repo):
        return True, f"recorded origin fetch is younger than {ORIGIN_FETCH_MAX_AGE_S}s"
    try:
        result = branch_sweep._git(repo, "fetch", "origin", timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "origin is not fresh: git fetch origin timed out"
    if result.returncode == 0:
        return True, "git fetch origin exited 0"
    return False, f"origin is not fresh: git fetch origin exited {result.returncode}"


def _history_block(repo: Path, *, timeout: int) -> str | None:
    """Why this repository's commit walk cannot prove preservation, if it cannot."""
    result = branch_sweep._git(repo, "rev-parse", "--is-shallow-repository", timeout=timeout)
    if result.returncode != 0:
        return "could not tell whether the repository is shallow"
    if result.stdout.strip() == "true":
        return "repository is shallow; the commit walk is incomplete"
    common = branch_sweep._git(
        repo,
        "rev-parse",
        "--path-format=absolute",
        "--git-common-dir",
        timeout=timeout,
    )
    if common.returncode != 0:
        return "could not resolve the common git directory"
    grafts = Path(common.stdout.strip()) / "info" / "grafts"
    try:
        if grafts.is_file() and grafts.read_text(encoding="utf-8").strip():
            return "repository has grafts; the commit walk is not the stored history"
    except OSError:
        return "repository grafts file is unreadable"
    replace = branch_sweep._git(repo, "replace", "-l", timeout=timeout)
    if replace.returncode != 0:
        return "could not list replace refs"
    if replace.stdout.strip():
        return "repository has replace refs; the commit walk is not the stored history"
    return None


def _commit_parents(repo: Path, shas: list[str], *, timeout: int) -> dict[str, list[str] | None]:
    """Parents stored on each commit object. ``None`` means the object is missing.

    ``git log`` hides a shallow-boundary parent. ``git cat-file`` still prints
    the parent SHA recorded in the commit, which is how a truncated walk is caught.
    """
    if not shas:
        return {}
    proc = subprocess.run(
        ["git", "--no-lazy-fetch", "cat-file", "--batch"],
        cwd=repo,
        env=sanitized_git_env(),
        input="".join(f"{sha}\n" for sha in shas).encode(),
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git cat-file --batch failed: {detail}")
    found: dict[str, list[str] | None] = {}
    blob = proc.stdout
    pos = 0
    while pos < len(blob):
        newline = blob.find(b"\n", pos)
        if newline < 0:
            raise RuntimeError("git cat-file --batch returned a truncated header")
        header = blob[pos:newline].decode("ascii", errors="replace")
        pos = newline + 1
        parts = header.split()
        if len(parts) == 2 and parts[1] == "missing":
            found[parts[0]] = None
            continue
        if len(parts) != 3 or not parts[2].isdecimal():
            raise RuntimeError("git cat-file --batch returned an unreadable header")
        sha, _kind, size_text = parts
        size = int(size_text)
        body = blob[pos : pos + size]
        pos += size
        if pos < len(blob) and blob[pos : pos + 1] == b"\n":
            pos += 1
        parents: list[str] = []
        for line in body.split(b"\n"):
            if line.startswith(b"parent "):
                parent = line.split()[1].decode("ascii", errors="replace")
                if not branch_sweep.SHA_RE.fullmatch(parent):
                    raise RuntimeError("git cat-file returned an invalid parent SHA")
                parents.append(parent)
            elif line == b"":
                break
        found[sha] = parents
    if any(sha not in found for sha in shas):
        raise RuntimeError("git cat-file --batch omitted a commit")
    return found


def _hidden_parent(repo: Path, commits: list[str], on_main: set[str], *, timeout: int) -> str | None:
    """A parent that rev-list did not enumerate and that is not on origin/main."""
    if not commits:
        return None
    parents = _commit_parents(repo, commits, timeout=timeout)
    known = set(commits) | on_main
    for sha in commits:
        listed = parents.get(sha)
        if listed is None:
            return sha
        for parent in listed:
            if parent not in known:
                return parent
    return None


def _diff_blob_ids(repo: Path, shas: list[str], *, timeout: int) -> dict[str, list[str]]:
    """Blob ids in each commit's raw diff. Empty means the commit changed no blob."""
    found: dict[str, list[str]] = {sha: [] for sha in shas}
    for start in range(0, len(shas), 40):
        chunk = shas[start : start + 40]
        log = branch_sweep._git(
            repo,
            "--no-lazy-fetch",
            "log",
            "--no-walk",
            "--raw",
            "--abbrev=64",
            "--format=format:commit %H",
            *chunk,
            timeout=timeout,
        )
        if log.returncode != 0:
            detail = (log.stderr or log.stdout).strip()
            raise RuntimeError(f"git log --raw failed: {detail}")
        current: str | None = None
        for line in log.stdout.splitlines():
            if line.startswith("commit "):
                current = line.split()[1]
                if current not in found:
                    raise RuntimeError("git log --raw returned an unexpected commit")
                continue
            if not line.startswith(":") or current is None:
                continue
            meta, _sep, _path = line.partition("\t")
            parts = meta.split()
            if len(parts) < 4:
                raise RuntimeError("git log --raw returned an unreadable diff line")
            for blob in parts[2:4]:
                if set(blob) <= {"0"}:
                    continue
                if not branch_sweep.SHA_RE.fullmatch(blob):
                    raise RuntimeError("git log --raw returned an unreadable blob id")
                found[current].append(blob)
    return found


def _absent_objects(repo: Path, names: list[str], *, timeout: int) -> set[str]:
    if not names:
        return set()
    proc = subprocess.run(
        ["git", "--no-lazy-fetch", "cat-file", "--batch-check"],
        cwd=repo,
        env=sanitized_git_env(),
        input=("\n".join(names) + "\n").encode(),
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git cat-file --batch-check failed: {detail}")
    absent: set[str] = set()
    for raw in proc.stdout.splitlines():
        parts = raw.decode("ascii", errors="replace").split()
        if len(parts) >= 2 and parts[1] == "missing":
            absent.add(parts[0])
    return absent


def _commits_missing_diff_blobs(repo: Path, shas: list[str], *, timeout: int) -> dict[str, str]:
    """Map a commit to one diff blob that is not in the local object store."""
    if not shas:
        return {}
    blobs_of = _diff_blob_ids(repo, shas, timeout=timeout)
    wanted = sorted({blob for blobs in blobs_of.values() for blob in blobs})
    absent = _absent_objects(repo, wanted, timeout=timeout)
    missing: dict[str, str] = {}
    for sha, blobs in blobs_of.items():
        for blob in blobs:
            if blob in absent:
                missing[sha] = blob
                break
    return missing


def _patch_counts(shas: list[str], patch_of: dict[str, str | None]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for sha in shas:
        patch = patch_of.get(sha)
        if patch:
            counts[patch] = counts.get(patch, 0) + 1
    return counts


def _preserving_pair(repo: Path, ref: str, *, timeout: int) -> tuple[str, str] | None:
    result = branch_sweep._git(repo, "rev-parse", "--verify", "--quiet", ref, timeout=timeout)
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    if not branch_sweep.SHA_RE.fullmatch(sha):
        raise RuntimeError("git rev-parse returned an invalid preserving SHA")
    return ref, sha


def preservation_for_creation(repo: Path, tip: str, *, budget_s: float) -> Preservation | None:
    """Prove one tip cheaply, or return ``None`` when the proof did not finish.

    Origin is refreshed first. A failed fetch, a shallow or grafted repository,
    a hidden parent, or a missing diff blob is not preservation: the caller
    still creates the ref. Ancestry runs before patch-ids. The main side of
    that comparison is ``merge-base..origin/main`` after 2026-08-01, which is
    a subset of the batch window: a match is real, and a miss only means "not
    proven", so the caller still creates the ref.
    """
    if budget_s < 0.4 or not branch_sweep.SHA_RE.fullmatch(tip):
        return None
    try:
        if _checkout(repo) != repo.resolve():
            return None
        deadline = time.monotonic() + budget_s
        fresh, fresh_proof = refresh_origin(repo, timeout=_seconds(deadline))
        if not fresh:
            return Preservation(CLASS_UNIQUE, fresh_proof)
        blocked = _history_block(repo, timeout=_seconds(deadline))
        if blocked:
            return Preservation(CLASS_UNIQUE, blocked)
        if _is_ancestor(repo, tip, _ORIGIN_MAIN, timeout=_seconds(deadline)):
            return decide(on_main=True, other_origin_ref=None, unique=[], patch_of={}, main_ids=set())
        other = _origin_ref_containing(repo, tip, timeout=_seconds(deadline))
        if other:
            return decide(on_main=False, other_origin_ref=other, unique=[], patch_of={}, main_ids=set())
        base = _merge_base(repo, tip, timeout=_seconds(deadline))
        if base is None:
            return None
        unique = branch_sweep._rev_list(repo, tip, "--not", _ORIGIN_MAIN, timeout=_seconds(deadline))
        if not unique:
            return decide(on_main=True, other_origin_ref=None, unique=[], patch_of={}, main_ids=set())
        on_main = set(branch_sweep._rev_list(repo, _ORIGIN_MAIN, timeout=_seconds(deadline)))
        hidden = _hidden_parent(repo, unique, on_main, timeout=_seconds(deadline))
        if hidden:
            return Preservation(CLASS_UNIQUE, f"off-main history stops at {hidden}; refusing a partial walk")
        missing_blobs = _commits_missing_diff_blobs(repo, unique, timeout=_seconds(deadline))
        if missing_blobs:
            sha, blob = next(iter(missing_blobs.items()))
            return Preservation(CLASS_UNIQUE, f"commit {sha} is missing blob {blob}; refusing patch equivalence")
        candidates = branch_sweep._rev_list(
            repo,
            f"--since={MAIN_PATCH_SINCE}",
            f"{base}..{_ORIGIN_MAIN}",
            timeout=_seconds(deadline),
        )
        cap = int(max(0.0, deadline - time.monotonic()) / _PATCH_SECONDS_PER_COMMIT)
        if len(unique) + len(candidates) > cap:
            return None
        missing_main = _commits_missing_diff_blobs(repo, candidates, timeout=_seconds(deadline))
        usable = [sha for sha in candidates if sha not in missing_main]
        patch_of: dict[str, str | None] = {}
        branch_sweep._load_patch_ids(
            repo,
            patch_of,
            unique + usable,
            mode="verbatim",
            lazy_fetch=False,
            timeout=_seconds(deadline),
        )
        counts = _patch_counts(usable, patch_of)
        return decide(
            on_main=False,
            other_origin_ref=None,
            unique=unique,
            patch_of=patch_of,
            main_ids=set(counts),
            main_counts=counts,
        )
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return None


def _rescue_rows(repo: Path) -> list[tuple[str, str, str]]:
    output = branch_sweep._checked(
        repo,
        "for-each-ref",
        "--format=%(refname)%00%(objectname)%00%(objecttype)",
        _RESCUE_PREFIX,
    )
    rows: list[tuple[str, str, str]] = []
    for line in output.splitlines():
        fields = line.split("\0")
        if len(fields) != 3:
            raise RuntimeError("git for-each-ref returned a malformed rescue ref")
        ref, sha, kind = fields
        if not ref.startswith(_RESCUE_PREFIX) or not branch_sweep.SHA_RE.fullmatch(sha):
            raise RuntimeError("git for-each-ref returned an unusable rescue ref")
        rows.append((ref, sha, kind))
    return rows


def _commits(repo: Path, *revs: str) -> set[str]:
    return set(branch_sweep._rev_list(repo, *revs, timeout=180))


def _unique_rows(rows: list[tuple[str, str, str]], proof: str) -> list[RescueRef]:
    return [RescueRef(ref, sha, CLASS_UNIQUE, proof) for ref, sha, _kind in rows]


def classify_rescue_refs(repo: Path) -> list[RescueRef]:
    """Classify every rescue ref. Main's in-window verbatim patch-ids are loaded once."""
    rows = _rescue_rows(repo)
    fresh, fresh_proof = refresh_origin(repo, timeout=180)
    if not fresh:
        return _unique_rows(rows, fresh_proof)
    blocked = _history_block(repo, timeout=30)
    if blocked:
        return _unique_rows(rows, blocked)
    on_main = _commits(repo, _ORIGIN_MAIN)
    on_origin = _commits(repo, "--remotes=origin")
    if not on_main:
        raise RuntimeError("origin/main is unavailable")
    main_pair = _preserving_pair(repo, _ORIGIN_MAIN, timeout=30)
    if main_pair is None:
        raise RuntimeError("origin/main is unavailable")
    pending: dict[str, list[str]] = {}
    classified: list[RescueRef] = []
    for ref, sha, kind in rows:
        if kind != "commit":
            classified.append(RescueRef(ref, sha, CLASS_UNIQUE, f"ref object type is {kind}"))
            continue
        if sha in on_main:
            verdict = decide(on_main=True, other_origin_ref=None, unique=[], patch_of={}, main_ids=set())
            classified.append(RescueRef(ref, sha, verdict.classification, verdict.proof, main_pair[0], main_pair[1]))
            continue
        if sha in on_origin:
            other = _origin_ref_containing(repo, sha, timeout=60)
            pair = _preserving_pair(repo, other, timeout=30) if other else None
            if pair is None:
                classified.append(RescueRef(ref, sha, CLASS_UNIQUE, "no origin ref still contains the tip"))
                continue
            verdict = decide(on_main=False, other_origin_ref=pair[0], unique=[], patch_of={}, main_ids=set())
            classified.append(RescueRef(ref, sha, verdict.classification, verdict.proof, pair[0], pair[1]))
            continue
        pending.setdefault(sha, []).append(ref)

    window = branch_sweep._rev_list(repo, f"--since={MAIN_PATCH_SINCE}", _ORIGIN_MAIN, timeout=180)
    off_main: dict[str, list[str]] = {}
    for tip in pending:
        off_main[tip] = branch_sweep._rev_list(repo, tip, "--not", _ORIGIN_MAIN, timeout=120)
    off_commits = sorted({sha for commits in off_main.values() for sha in commits})
    missing_blobs = _commits_missing_diff_blobs(repo, off_commits + window, timeout=180)
    patch_of: dict[str, str | None] = {}
    usable_window = [sha for sha in window if sha not in missing_blobs]
    branch_sweep._load_patch_ids(
        repo,
        patch_of,
        usable_window,
        mode="verbatim",
        lazy_fetch=False,
        timeout=180,
    )
    counts = _patch_counts(usable_window, patch_of)
    main_ids = set(counts)
    ready: list[str] = []
    refused: dict[str, Preservation] = {}
    for tip, commits in off_main.items():
        hidden = _hidden_parent(repo, commits, on_main, timeout=60)
        if hidden:
            refused[tip] = Preservation(CLASS_UNIQUE, f"off-main history stops at {hidden}; refusing a partial walk")
            continue
        missing = [sha for sha in commits if sha in missing_blobs]
        if missing:
            blob = missing_blobs[missing[0]]
            refused[tip] = Preservation(
                CLASS_UNIQUE,
                f"commit {missing[0]} is missing blob {blob}; refusing patch equivalence",
            )
            continue
        ready.extend(sha for sha in commits if sha not in patch_of)
    branch_sweep._load_patch_ids(repo, patch_of, ready, mode="verbatim", lazy_fetch=False, timeout=180)
    for tip, refs in pending.items():
        patch_verdict = refused.get(tip)
        if patch_verdict is None:
            patch_verdict = decide(
                on_main=False,
                other_origin_ref=None,
                unique=off_main[tip],
                patch_of=patch_of,
                main_ids=main_ids,
                main_counts=counts,
            )
        if patch_verdict.classification in DELETABLE:
            preserving_ref, preserving_sha = main_pair
        else:
            preserving_ref, preserving_sha = "", ""
        for ref in refs:
            classified.append(
                RescueRef(
                    ref,
                    tip,
                    patch_verdict.classification,
                    patch_verdict.proof,
                    preserving_ref,
                    preserving_sha,
                )
            )
    classified.sort(key=lambda item: item.ref)
    return classified


def _counts(rows: list[RescueRef]) -> dict[str, int]:
    counts = {CLASS_CONTAINED: 0, CLASS_PATCH: 0, CLASS_UNIQUE: 0}
    for row in rows:
        counts[row.classification] = counts.get(row.classification, 0) + 1
    return counts


def _listing_path(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    root = os.environ.get("TMPDIR") or tempfile.gettempdir()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(root) / f"rescue-refs-{stamp}.json"


def _refuse_inside_repo(repo: Path, path: Path) -> None:
    resolved = path.resolve()
    roots = {repo.resolve(), reaper.primary_checkout_root(repo).resolve()}
    for root in roots:
        if resolved == root or root in resolved.parents:
            raise RescueRefError("listing path must be outside the repository working tree")


def _write_listing(repo: Path, path: Path, rows: list[RescueRef], *, elapsed_s: float) -> None:
    _refuse_inside_repo(repo, path)
    if path.is_symlink():
        raise RescueRefError("listing path is a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "counts": _counts(rows),
        "elapsed_s": round(elapsed_s, 3),
        "refs": [asdict(row) for row in rows],
        "since": MAIN_PATCH_SINCE,
        "window": (
            "origin/main commits with a committer date after 2026-08-01; "
            "an older main commit is not a verbatim patch-id match, so the ref is UNIQUE"
        ),
        "origin_fetch_max_age_s": ORIGIN_FETCH_MAX_AGE_S,
    }
    encoded = (json.dumps(payload, sort_keys=True) + "\n").encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise RescueRefError("listing write made no progress")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def _current_sha(repo: Path, ref: str) -> str | None:
    result = branch_sweep._git(repo, "rev-parse", "--verify", "--quiet", ref, timeout=30)
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    if not branch_sweep.SHA_RE.fullmatch(sha):
        raise RuntimeError("git rev-parse returned an invalid rescue SHA")
    return sha


def delete_ref(repo: Path, ref: str, expected: str) -> None:
    """Compare-and-delete. A moved ref raises :class:`RescueRefChanged` and stays."""
    if not ref.startswith(_RESCUE_PREFIX) or ref != ref.strip() or "\n" in ref:
        raise RescueRefError(f"refusing to delete a ref outside {_RESCUE_PREFIX}")
    result = branch_sweep._git(repo, "update-ref", "-d", ref, expected, timeout=30)
    if result.returncode != 0:
        raise RescueRefChanged((result.stderr or result.stdout or "git update-ref -d failed").strip())


def _journal_root(repo: Path) -> Path:
    return reaper.control_plane_root(repo)


def _preservation_skip_reason(repo: Path, row: RescueRef) -> str | None:
    """Why this row must not be deleted, after the preserving ref is re-read."""
    if not row.preserving_ref or not row.preserving_sha:
        return "classification recorded no preserving ref"
    current = _current_sha(repo, row.preserving_ref)
    if current is None:
        return "preserving ref removed"
    if current != row.preserving_sha:
        return "preserving ref changed"
    if row.classification == CLASS_CONTAINED:
        try:
            holds = _is_ancestor(repo, row.sha, row.preserving_ref, timeout=30)
        except RuntimeError as exc:
            return f"preserving ref could not be rechecked: {exc}"
        if not holds:
            return "preserving ref no longer contains the tip"
        return None
    if row.classification == CLASS_PATCH:
        # The preserving ref is still the commit whose history held the matching
        # patch-ids. A moved ref was refused above.
        return None
    return "classification is not deletable"


def _apply(
    repo: Path,
    rows: list[RescueRef],
    *,
    limit: int,
    lock_timeout_s: float,
    deleter: DeleteFn,
) -> tuple[int, int]:
    chosen = [row for row in rows if row.classification in DELETABLE][:limit]
    journal_at = _journal_root(repo)
    deleted = 0
    skipped = 0
    with reaper._ReapLock(repo, timeout_s=lock_timeout_s):
        # Raises when any registered worktree has a native git operation.
        branch_sweep._occupied_worktrees(repo)
        for row in chosen:
            if row.classification not in DELETABLE:
                continue
            reason = _preservation_skip_reason(repo, row)
            if reason:
                append_journal(
                    journal_at,
                    "rescue-ref-skipped",
                    ref=row.ref,
                    sha=row.sha,
                    classification=row.classification,
                    proof=row.proof,
                    preserving_ref=row.preserving_ref,
                    preserving_sha=row.preserving_sha,
                    reason=reason,
                )
                skipped += 1
                continue
            current = _current_sha(repo, row.ref)
            if current != row.sha:
                append_journal(
                    journal_at,
                    "rescue-ref-skipped",
                    ref=row.ref,
                    sha=row.sha,
                    current=current,
                    classification=row.classification,
                    proof=row.proof,
                    preserving_ref=row.preserving_ref,
                    preserving_sha=row.preserving_sha,
                    reason="ref moved",
                )
                skipped += 1
                continue
            append_journal(
                journal_at,
                "rescue-ref-delete",
                ref=row.ref,
                sha=row.sha,
                classification=row.classification,
                proof=row.proof,
                preserving_ref=row.preserving_ref,
                preserving_sha=row.preserving_sha,
            )
            try:
                deleter(repo, row.ref, row.sha)
            except RescueRefChanged as exc:
                append_journal(
                    journal_at,
                    "rescue-ref-skipped",
                    ref=row.ref,
                    sha=row.sha,
                    classification=row.classification,
                    proof=row.proof,
                    preserving_ref=row.preserving_ref,
                    preserving_sha=row.preserving_sha,
                    reason=f"compare-and-delete refused: {exc}",
                )
                skipped += 1
                continue
            deleted += 1
    return deleted, skipped


def run(
    repo: Path,
    *,
    apply: bool = False,
    limit: int | None = None,
    listing: Path | None = None,
    lock_timeout_s: float = reaper.DEFAULT_REAP_LOCK_TIMEOUT_S,
    deleter: DeleteFn = delete_ref,
) -> Summary:
    """Classify, write the listing, and delete only when ``apply`` is set.

    Dry-run and apply share :func:`classify_rescue_refs` up to the delete call.
    """
    if apply and (limit is None or limit < 1):
        raise RescueRefError("--apply requires --limit N with N >= 1 (example: --limit 25)")
    started = time.monotonic()
    rows = classify_rescue_refs(repo)
    path = _listing_path(listing)
    # The listing is the census. Write it before any delete so a refused apply
    # still leaves the classification outside the repository.
    _write_listing(repo, path, rows, elapsed_s=time.monotonic() - started)
    deleted = 0
    skipped = 0
    if apply:
        deleted, skipped = _apply(
            repo,
            rows,
            limit=limit if limit is not None else 0,
            lock_timeout_s=lock_timeout_s,
            deleter=deleter,
        )
    return Summary(_counts(rows), time.monotonic() - started, path, deleted, skipped)


def _format_summary(summary: Summary, *, apply: bool) -> str:
    lines = [
        f"CONTAINED {summary.counts.get(CLASS_CONTAINED, 0)}",
        f"PATCH-EQUIVALENT {summary.counts.get(CLASS_PATCH, 0)}",
        f"UNIQUE {summary.counts.get(CLASS_UNIQUE, 0)}",
        f"elapsed_s {summary.elapsed_s:.3f}",
        f"listing {summary.listing}",
    ]
    if apply:
        lines.append(f"deleted {summary.deleted}")
        lines.append(f"skipped {summary.skipped}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Classify refs/reaper-rescue by whether those commits are already preserved, and delete only those refs.\n"
            "Use when rescue pins have piled up and a census says many are already on origin. "
            "Do not use it to delete UNIQUE rescue refs, remote rescue/* branches, or any other ref."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.rescue_refs\n"
            "  .venv/bin/python -m scripts.hygiene.rescue_refs --listing /tmp/rescue-refs.json\n"
            "  .venv/bin/python -m scripts.hygiene.rescue_refs --apply --limit 25\n"
            "Outputs: stdout counts (CONTAINED, PATCH-EQUIVALENT, UNIQUE, elapsed_s). "
            "A JSON listing of every ref is written outside the repository "
            "(default: $TMPDIR/rescue-refs-<utc>.json). "
            "--apply appends batch_state/worktree-reaper/journal.jsonl on the control-plane "
            "checkout before each compare-and-delete, then deletes at most --limit refs.\n"
            "The patch-id window is origin/main commits after 2026-08-01, compared with "
            "git patch-id --verbatim so whitespace is part of the proof. Each off-main "
            "commit must match a distinct main commit. The run fetches origin first "
            "(or accepts a recorded fetch younger than 120 seconds) and re-checks the "
            "preserving ref under the lock. A shallow repository, a graft, or a missing "
            "diff blob stays UNIQUE. A match only on an older main commit leaves the ref UNIQUE.\n"
            "Exit codes: 0 = classified (and deleted, when --apply); "
            "1 = git, lock, or native-operation failure (no partial success is hidden; "
            "a moved ref is skipped and does not fail the run); 2 = invalid arguments.\n"
            "Related: docs/runbooks/worktree-cleanup.md; scripts.hygiene.branch_sweep; issue #10851."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Delete CONTAINED and PATCH-EQUIVALENT refs. Default is a dry run that deletes nothing. "
            "Example: --apply --limit 25."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "With --apply, delete at most this many proven refs (required, example: 25). "
            "Dry-run classifies every ref and ignores this flag."
        ),
    )
    parser.add_argument(
        "--listing",
        type=Path,
        default=None,
        help=(
            "Write the JSON listing to this path, which must be outside the repository. "
            "Default: $TMPDIR/rescue-refs-<utc>.json."
        ),
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repository or worktree root. Default: the current checkout. Example: --repo .",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.apply and (args.limit is None or args.limit < 1):
        parser.error("--apply requires --limit N with N >= 1 (example: --limit 25)")
    try:
        repo = args.repo.resolve() if args.repo is not None else reaper.resolve_repo_root()
        summary = run(repo, apply=args.apply, limit=args.limit, listing=args.listing)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"rescue-refs: {exc}", flush=True)
        return 1
    print(_format_summary(summary, apply=args.apply), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
