"""Classify ``refs/reaper-rescue/*`` and delete only refs already preserved elsewhere.

Dry-run is the default. ``--apply`` deletes CONTAINED and PATCH-EQUIVALENT refs
only, under the reaper lock, after a journal line and a compare-and-delete.
UNIQUE refs are never deleted. Do not use this tool for ``rescue/*`` branches,
retention policy, or any ref outside ``refs/reaper-rescue/``.

The patch-id window is ``origin/main`` commits with a committer date after
2026-08-01 (``git rev-list --since=2026-08-01``), the same bound as the
2026-10-16 census. A matching commit older than that window is not a match, so
the rescue ref stays UNIQUE. Main's patch-ids are loaded once per run.

Patch-ids are read through :func:`scripts.hygiene.branch_sweep._load_patch_ids`
(``git patch-id --stable``). Ancestry of one tip uses ``git merge-base
--is-ancestor``, the same command branch sweep uses. The batch form of that
fact is membership in ``git rev-list refs/remotes/origin/main``; reachability
from any other origin ref is membership in ``git rev-list --remotes=origin``.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

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
_RESCUE_PREFIX = "refs/reaper-rescue/"
# 40 commits of `git log -p | git patch-id --stable` took 0.42s on 2026-10-16.
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
                f"{len(unmatched)} of {len(unique)} off-main commits have no stable patch-id "
                f"on origin/main since {since}; first {unmatched[0]}"
            ),
        )
    return Preservation(
        CLASS_PATCH,
        f"all {len(unique)} off-main commits match a stable patch-id on origin/main since {since}",
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


def preservation_for_creation(repo: Path, tip: str, *, budget_s: float) -> Preservation | None:
    """Prove one tip cheaply, or return ``None`` when the proof did not finish.

    Ancestry runs first. Patch-ids run only when the tip is not already on an
    origin ref. The main side of that comparison is ``merge-base..origin/main``
    after 2026-08-01, which is a subset of the batch window: a match is real,
    and a miss only means "not proven", so the caller still creates the ref.
    """
    if budget_s < 0.4 or not branch_sweep.SHA_RE.fullmatch(tip):
        return None
    try:
        if _checkout(repo) != repo.resolve():
            return None
        deadline = time.monotonic() + budget_s
        if _is_ancestor(repo, tip, "refs/remotes/origin/main", timeout=_seconds(deadline)):
            return decide(on_main=True, other_origin_ref=None, unique=[], patch_of={}, main_ids=set())
        other = _origin_ref_containing(repo, tip, timeout=_seconds(deadline))
        if other:
            return decide(on_main=False, other_origin_ref=other, unique=[], patch_of={}, main_ids=set())
        base = _merge_base(repo, tip, timeout=_seconds(deadline))
        if base is None:
            return None
        unique = branch_sweep._rev_list(repo, tip, "--not", "refs/remotes/origin/main", timeout=_seconds(deadline))
        if not unique:
            return decide(on_main=True, other_origin_ref=None, unique=[], patch_of={}, main_ids=set())
        candidates = branch_sweep._rev_list(
            repo,
            f"--since={MAIN_PATCH_SINCE}",
            f"{base}..refs/remotes/origin/main",
            timeout=_seconds(deadline),
        )
        cap = int(max(0.0, deadline - time.monotonic()) / _PATCH_SECONDS_PER_COMMIT)
        if len(unique) + len(candidates) > cap:
            return None
        patch_of: dict[str, str | None] = {}
        branch_sweep._load_patch_ids(repo, patch_of, unique + candidates, timeout=_seconds(deadline))
        main_ids = {patch for sha in candidates if (patch := patch_of.get(sha))}
        return decide(
            on_main=False,
            other_origin_ref=None,
            unique=unique,
            patch_of=patch_of,
            main_ids=main_ids,
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


def classify_rescue_refs(repo: Path) -> list[RescueRef]:
    """Classify every rescue ref. Main's in-window patch-ids are loaded once."""
    rows = _rescue_rows(repo)
    on_main = _commits(repo, "refs/remotes/origin/main")
    on_origin = _commits(repo, "--remotes=origin")
    if not on_main:
        raise RuntimeError("origin/main is unavailable")
    pending: dict[str, list[str]] = {}
    classified: list[tuple[str, str, Preservation]] = []
    for ref, sha, kind in rows:
        if kind != "commit":
            classified.append((ref, sha, Preservation(CLASS_UNIQUE, f"ref object type is {kind}")))
            continue
        if sha in on_main:
            classified.append(
                (ref, sha, decide(on_main=True, other_origin_ref=None, unique=[], patch_of={}, main_ids=set()))
            )
            continue
        if sha in on_origin:
            classified.append(
                (
                    ref,
                    sha,
                    decide(
                        on_main=False,
                        other_origin_ref="an origin/* ref other than origin/main",
                        unique=[],
                        patch_of={},
                        main_ids=set(),
                    ),
                )
            )
            continue
        pending.setdefault(sha, []).append(ref)

    window = branch_sweep._rev_list(repo, f"--since={MAIN_PATCH_SINCE}", "refs/remotes/origin/main", timeout=180)
    patch_of: dict[str, str | None] = {}
    branch_sweep._load_patch_ids(repo, patch_of, window, timeout=180)
    main_ids = {patch for sha in window if (patch := patch_of.get(sha))}
    off_main: dict[str, list[str]] = {}
    for tip in pending:
        off_main[tip] = branch_sweep._rev_list(repo, tip, "--not", "refs/remotes/origin/main", timeout=120)
    extra = [sha for commits in off_main.values() for sha in commits if sha not in patch_of]
    branch_sweep._load_patch_ids(repo, patch_of, extra, timeout=180)
    for tip, refs in pending.items():
        verdict = decide(
            on_main=False,
            other_origin_ref=None,
            unique=off_main[tip],
            patch_of=patch_of,
            main_ids=main_ids,
        )
        for ref in refs:
            classified.append((ref, tip, verdict))
    classified.sort(key=lambda item: item[0])
    return [RescueRef(ref, sha, verdict.classification, verdict.proof) for ref, sha, verdict in classified]


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
            "an older main commit is not a patch-id match, so the ref is UNIQUE"
        ),
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
            "The patch-id window is origin/main commits after 2026-08-01. "
            "A match only on an older main commit leaves the ref UNIQUE.\n"
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
