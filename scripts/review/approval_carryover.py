"""Carry an exact-head approval across a generated-only base merge (FR-54).

A PR approved at head A can meet a concurrent base change that conflicts only in
generated files. Its owner merges the base commit B into A, regenerates, and pushes
the merge commit N. The ``carry-over`` verb of ``record_cf_verdict`` then records a
carry-over status on N, and only when all of these hold (otherwise it refuses with a
typed reason):

1. ``pinned-merge``: N is a merge commit whose first parent is exactly A and whose
   second parent B is an ancestor of the PR's base branch at check time.
2. ``merge-result``: every path where N's tree differs from ``git merge-tree
   --write-tree A B``, and every path that merge reports as conflicted, is in the
   generated-path registry as merged on the base branch
   (``scripts/config/generated_paths.yaml``).
3. ``reproduction``: each such path's generator, run on N in a clean temporary
   worktree, reproduces N's committed bytes exactly and writes nothing else: it
   runs under bubblewrap, seeing only system files, its runtimes and the worktree,
   all read-only except its targets, with no network or host service sockets.
4. ``lineage``: every review task of the PR is terminal, every review verdict is
   published, and A's APPROVE is the latest verdict of every reviewer seat.
5. ``ci``: same-head CI on N is green.

A carry-over is not a review: it posts no verdict marker, opens no review round, and
the merge queue still runs its own CI. Approved design: CTO proposal with Sol 6.1
APPROVE (advisory task cto-7eba-adv-carryover2), answering cto-7eba-adv-carryover.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Any

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.git_context import sanitized_git_env
from scripts.common.scratch import ensure_scratch_root
from scripts.guardrails.delegate_ownership import TERMINAL_TASK_STATUSES
from scripts.opsec.prepublish import check_texts, normalize_repository, publication_boundary, publication_cli
from scripts.orchestration.integration_sweep import (
    MARKER_PREFIX,
    REJECTED,
    SHA,
    TRUSTED_ASSOCIATIONS,
    SweepError,
    _check_blockers,
    lookup_verdict,
    parse_marker,
)
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME
from scripts.publish.github import Request
from scripts.review import record_cf_verdict as recorder
from scripts.review.language_lane import is_ukrainian_review
from scripts.review.reviewer_resolver import resolve_family
from scripts.review.verdict_parser import recognized_verdicts

REGISTRY_PATH = "scripts/config/generated_paths.yaml"
STATUS_CONTEXT = "fleet/approval-carry-over"
RECEIPT_HEADING = "### Approval carry-over (not a review)"
RECEIPT_MARKER = "<!-- approval-carry-over v1"
GIT_TIMEOUT_S = 120
GENERATOR_TIMEOUT_S = 900
# A learner-facing Ukrainian change seats two reviewers from two families
# (review-loop references/ukrainian.md § Seats); every other profile seats one.
UKRAINIAN_SEATS = 2
NODE_PACKAGE = re.compile(r"(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*\Z")
# The only host paths a sandboxed generator sees, besides its runtimes and worktree.
SANDBOX_SYSTEM_PATHS = ("/usr", "/etc", "/bin", "/sbin", "/lib", "/lib32", "/lib64", "/libx32")
UNATTESTED_FAMILIES = frozenset({"unknown", "unattested", "ambiguous", "conflicting"})

# Typed refusal reasons, one per condition plus the inputs they read.
TARGET = "target"
PINNED_MERGE = "pinned-merge"
REGISTRY = "registry"
MERGE_RESULT = "merge-result"
REPRODUCTION = "reproduction"
LINEAGE = "lineage"
CI = "ci"


class CarryOverRefused(recorder.RecordError):
    """A carry-over condition failed; ``reason`` names which one."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"CARRY_OVER_REFUSED[{reason}]: {detail}")
        self.reason = reason


@dataclass(frozen=True)
class Generated:
    path: str
    command: tuple[str, ...]
    # Node packages the generator loads, copied privately into the worktree.
    node_packages: tuple[str, ...] = ()


def _git(repo_root: Path, *args: str, ok: Sequence[int] = (0,), env: Mapping[str, str] | None = None) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT_S,
            env=dict(env) if env is not None else sanitized_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CarryOverRefused(TARGET, f"git {args[0]} unavailable: {exc}") from None
    if result.returncode not in ok:
        detail = result.stderr.decode("utf-8", "replace").strip()[:300]
        raise CarryOverRefused(TARGET, f"git {args[0]} failed ({result.returncode}): {detail}")
    return result.stdout


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", ancestor, descendant],
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT_S,
            env=sanitized_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CarryOverRefused(TARGET, f"git merge-base unavailable: {exc}") from None
    if result.returncode not in {0, 1}:
        raise CarryOverRefused(TARGET, f"ancestry of {ancestor} unknown")
    return result.returncode == 0


def _ensure_commits(repo_root: Path, shas: Sequence[str]) -> None:
    """Fetch only the commits the checkout lacks; refs stay untouched."""
    missing = [sha for sha in shas if _git(repo_root, "cat-file", "-t", sha, ok=(0, 128)).strip() != b"commit"]
    if missing:
        _git(repo_root, "fetch", "--quiet", "--no-tags", "--no-write-fetch-head", "origin", *missing)


def _nul_list(raw: bytes) -> list[str]:
    return [item.decode("utf-8") for item in raw.split(b"\0") if item]


def check_pinned_merge(repo_root: Path, *, approved: str, head: str, base_tip: str) -> str:
    """Condition 1: return B, the merged base commit."""
    parents = _git(repo_root, "rev-list", "--parents", "-n", "1", head).decode("ascii").split()
    if len(parents) != 3:
        raise CarryOverRefused(PINNED_MERGE, f"head {head} is not a two-parent merge commit")
    if parents[1] != approved:
        raise CarryOverRefused(PINNED_MERGE, f"first parent {parents[1]} is not the approved head {approved}")
    base = parents[2]
    if not _is_ancestor(repo_root, base, base_tip):
        raise CarryOverRefused(PINNED_MERGE, f"second parent {base} is not on the base branch tip {base_tip}")
    return base


def load_registry(repo_root: Path, base_tip: str) -> dict[str, Generated]:
    """The generated-path registry as merged on the base branch tip.

    Only the merged copy has passed review and the merge gate; a registry the PR
    edits, or one N carries, never decides which of N's paths may differ.
    """
    raw = _git(repo_root, "cat-file", "blob", f"{base_tip}:{REGISTRY_PATH}", ok=(0, 128))
    try:
        data = yaml.safe_load(raw.decode("utf-8")) if raw else None
    except (UnicodeDecodeError, yaml.YAMLError):
        data = None
    entries = data.get("generated_paths") if isinstance(data, dict) and data.get("schema_version") == 1 else None
    if not isinstance(entries, dict) or not entries:
        raise CarryOverRefused(REGISTRY, f"{REGISTRY_PATH} missing or malformed at {base_tip}")
    registry: dict[str, Generated] = {}
    for path, entry in entries.items():
        command = entry.get("command") if isinstance(entry, dict) else None
        packages = entry.get("node_packages", []) if isinstance(entry, dict) else None
        pure = PurePosixPath(path) if isinstance(path, str) else None
        if (
            pure is None
            or pure.is_absolute()
            or ".." in pure.parts
            or str(pure) != path
            or path == REGISTRY_PATH
            or not isinstance(command, list)
            or not command
            or not all(isinstance(part, str) and part for part in command)
            or not isinstance(packages, list)
            or not all(isinstance(name, str) and NODE_PACKAGE.fullmatch(name) for name in packages)
        ):
            raise CarryOverRefused(REGISTRY, f"registry entry {path!r} malformed")
        registry[path] = Generated(path, tuple(command), tuple(packages))
    return registry


def check_merge_result(
    repo_root: Path, *, approved: str, base: str, head: str, registry: Mapping[str, Generated]
) -> tuple[str, tuple[str, ...]]:
    """Condition 2: return the merge-tree OID and the paths that must regenerate."""
    merged = _nul_list(
        _git(repo_root, "merge-tree", "--write-tree", "--name-only", "--no-messages", "-z", approved, base, ok=(0, 1))
    )
    if not merged or not SHA.fullmatch(merged[0]):
        raise CarryOverRefused(MERGE_RESULT, "git merge-tree returned no tree")
    tree, conflicted = merged[0], set(merged[1:])
    differing = set(_nul_list(_git(repo_root, "diff-tree", "-r", "-z", "--name-only", tree, f"{head}^{{tree}}")))
    paths = tuple(sorted(conflicted | differing))
    if unregistered := [path for path in paths if path not in registry]:
        raise CarryOverRefused(
            MERGE_RESULT,
            f"paths differ from git's merge of {approved} and {base} outside the registry: " + ", ".join(unregistered),
        )
    return tree, paths


def _committed_blob(repo_root: Path, head: str, path: str) -> bytes:
    """``path``'s bytes at ``head``, which must be a regular file.

    Git records no entry beneath a symlink, so a regular blob at ``path`` also
    proves that none of its parent directories is a symlink.
    """
    listing = _git(repo_root, "ls-tree", "-z", head, "--", path)
    meta, _, name = listing.rstrip(b"\0").partition(b"\t")
    fields = meta.split()
    if (
        name.decode("utf-8", "replace") != path
        or len(fields) != 3
        or fields[:2]
        not in (
            [b"100644", b"blob"],
            [b"100755", b"blob"],
        )
    ):
        raise CarryOverRefused(REPRODUCTION, f"{path} is not a regular file committed at {head}")
    return _git(repo_root, "cat-file", "blob", fields[2].decode("ascii"))


def _snapshot(tree: Path) -> dict[str, tuple[Any, ...]]:
    """Every path under ``tree``, ignored ones included, with its ``lstat`` identity.

    A write, a replacement or a restored mtime all change a file's ctime, which
    no process can set back. Symlinks, to directories too, are recorded with
    their targets, and directories with their mode, so comparing snapshots
    detects any change that outlives the run.
    """
    entries: dict[str, tuple[Any, ...]] = {}
    for root, dirs, files in os.walk(tree):
        for name in (*dirs, *files):
            path = os.path.join(root, name)
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                identity: tuple[Any, ...] = ("link", os.readlink(path), info.st_ino, info.st_ctime_ns)
            elif stat.S_ISDIR(info.st_mode):
                identity = ("dir", info.st_mode, info.st_ino)
            else:
                identity = ("file", info.st_mode, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
            entries[os.path.relpath(path, tree)] = identity
    return entries


def _runtime_roots(*, node: bool) -> list[Path]:
    """Install trees of the interpreters a generator runs on: Python, and Node when it loads packages."""
    roots = {Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()}
    if node:
        found = shutil.which("node")
        if found is None:
            raise CarryOverRefused(REPRODUCTION, "Node is required by a registered generator but is not installed")
        roots.add(Path(found).resolve().parent.parent)
    return sorted(roots)


def _sandboxed(argv: Sequence[str], *, tree: Path, writable: Sequence[Path], node: bool) -> list[str]:
    """``argv`` under bubblewrap, seeing only system files, its runtimes and the worktree.

    Everything is read-only except ``writable``. Host paths that hold service
    sockets (``/run``, ``/tmp``, home directories) are not mounted, and the
    network namespace isolates abstract sockets and loopback, so no host service
    can write on the generator's behalf either.
    """
    bwrap = shutil.which("bwrap")
    if bwrap is None:
        raise CarryOverRefused(REPRODUCTION, "bubblewrap (bwrap) is required to sandbox generators")
    mounts: list[str] = []
    for system in SANDBOX_SYSTEM_PATHS:
        path = Path(system)
        if path.is_symlink():
            mounts += ["--symlink", os.readlink(path), system]
        elif path.is_dir():
            mounts += ["--ro-bind", system, system]
    for root in _runtime_roots(node=node):
        if not any(root.is_relative_to(system) for system in SANDBOX_SYSTEM_PATHS):
            mounts += ["--ro-bind", str(root), str(root)]
    mounts += ["--ro-bind", str(tree), str(tree)]
    mounts += [arg for path in writable for arg in ("--bind", str(path), str(path))]
    return [
        bwrap,
        *mounts,
        "--dev",
        "/dev",
        "--proc",
        "/proc",
        # The sandbox's own root (a tmpfs holding the mount points) is read-only too.
        "--remount-ro",
        "/",
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--chdir",
        str(tree),
        "--",
        *argv,
    ]


def check_reproduction(
    repo_root: Path, *, head: str, paths: Sequence[str], registry: Mapping[str, Generated]
) -> list[dict[str, str]]:
    """Condition 3: regenerate ``paths`` on a clean worktree of ``head``; return their sha256."""
    if not paths:
        return []
    env = {**sanitized_git_env(), "GIT_LFS_SKIP_SMUDGE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    with TemporaryDirectory(prefix="carry-over-", dir=ensure_scratch_root()) as scratch:
        tree = Path(scratch) / "tree"
        # A plain export of ``head`` through a private index: Git registers no
        # worktree, runs no hooks, and leaves no route back to its directory.
        export_env = {**env, "GIT_INDEX_FILE": str(Path(scratch) / "index")}
        _git(repo_root, "read-tree", head, env=export_env)
        _git(repo_root, "checkout-index", "--all", f"--prefix={tree}/", env=export_env)
        committed = {path: _committed_blob(repo_root, head, path) for path in paths}
        for package in sorted({name for path in paths for name in registry[path].node_packages}):
            # A private copy: nothing a generator does reaches the checkout's own packages.
            source = repo_root / "node_modules" / package
            if source.is_symlink() or not source.is_dir():
                raise CarryOverRefused(REPRODUCTION, f"Node package {package} is not installed in the checkout")
            try:
                # Links are dereferenced, so the copy holds no route back to shared files.
                shutil.copytree(source, tree / "node_modules" / package, symlinks=False)
            except (OSError, shutil.Error) as exc:
                raise CarryOverRefused(REPRODUCTION, f"Node package {package} could not be copied: {exc}") from None
        if empty := [path for path in paths if not committed[path]]:
            raise CarryOverRefused(REPRODUCTION, "an empty committed file proves no generation: " + ", ".join(empty))
        for path in paths:
            # Emptied, not removed: each target stays the sandbox's only writable file.
            (tree / path).write_bytes(b"")
        node = any(registry[path].node_packages for path in paths)
        before = _snapshot(tree)
        for command in dict.fromkeys(registry[path].command for path in paths):
            argv = [sys.executable, *command[1:]] if command[0] == "python" else list(command)
            try:
                result = subprocess.run(
                    _sandboxed(argv, tree=tree, writable=[tree / path for path in paths], node=node),
                    cwd=tree,
                    capture_output=True,
                    check=False,
                    timeout=GENERATOR_TIMEOUT_S,
                    env=env,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise CarryOverRefused(REPRODUCTION, f"generator {' '.join(command)} did not run: {exc}") from None
            if result.returncode:
                detail = result.stderr.decode("utf-8", "replace").strip()[-300:]
                raise CarryOverRefused(
                    REPRODUCTION, f"generator {' '.join(command)} exited {result.returncode}: {detail}"
                )
        after = _snapshot(tree)
        outside = sorted(
            path
            for path in before.keys() | after.keys()
            if path not in paths and before.get(path, "absent") != after.get(path, "absent")
        )
        if outside:
            raise CarryOverRefused(
                REPRODUCTION, "generators wrote outside the registered paths: " + ", ".join(outside[:20])
            )
        receipts = []
        for path in paths:
            produced = tree / path
            if produced.is_symlink() or not produced.is_file():
                raise CarryOverRefused(REPRODUCTION, f"generator did not produce {path}")
            if produced.read_bytes() != committed[path]:
                raise CarryOverRefused(REPRODUCTION, f"regenerated {path} differs from the bytes committed at {head}")
            receipts.append({"path": path, "sha256": hashlib.sha256(committed[path]).hexdigest()})
        return receipts


def _is_review_task(task: Mapping[str, Any]) -> bool:
    return bool(
        task.get("require_review_verdict")
        or task.get("review_profile")
        or task.get("review_mode")
        or task.get("review_attempt")
        or task.get("type") == "review"
    )


@dataclass(frozen=True)
class ReviewRun:
    """One dispatch run of a review task: its record and its reply, read together."""

    task_id: str
    record: Mapping[str, Any]
    reply: str | None


def _read_run(path: Path, record: Mapping[str, Any]) -> ReviewRun:
    """Read one run's reply, refusing a reply its record's digest disowns."""
    result = path.with_suffix(".result")
    try:
        raw = result.read_bytes() if result.exists() else None
    except OSError as exc:
        raise CarryOverRefused(LINEAGE, f"review task {path.stem} reply unreadable: {exc}") from None
    expected = record.get("result_sha256")
    if raw is not None and expected is not None and hashlib.sha256(raw).hexdigest() != expected:
        raise CarryOverRefused(LINEAGE, f"review task {path.stem} reply does not match its recorded digest")
    try:
        reply = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n") if raw is not None else None
    except UnicodeDecodeError:
        raise CarryOverRefused(LINEAGE, f"review task {path.stem} reply is not UTF-8") from None
    return ReviewRun(path.stem, record, reply)


def lineage_runs(task_root: Path, *, repository: str, number: int, branch: str) -> list[ReviewRun]:
    """Every hot and archived review run of this PR; an archived run is kept beside a hot one."""
    try:
        paths = [*sorted((task_root / ARCHIVE_DIR_NAME).glob("*.json")), *sorted(task_root.glob("*.json"))]
    except OSError as exc:
        raise CarryOverRefused(LINEAGE, f"task ledger unavailable: {exc}") from None
    runs = []
    for path in paths:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CarryOverRefused(LINEAGE, f"task record {path.name} unreadable: {exc}") from None
        if (
            not isinstance(record, dict)
            or record.get("status") in {"dry_run", "dry-run"}
            or not _is_review_task(record)
        ):
            continue
        if not isinstance(record.get("repository"), str) or normalize_repository(
            record["repository"]
        ) != normalize_repository(repository):
            continue
        if record.get("pr") == number or record.get("review_branch") == branch:
            runs.append(_read_run(path, record))
    return runs


def _started(record: Mapping[str, Any]) -> str | None:
    """The run's start as the recorder writes it into a marker."""
    try:
        started = datetime.fromisoformat(str(record.get("started_at") or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    if started.tzinfo is None:
        return None
    return started.astimezone(UTC).isoformat(timespec="microseconds")


def _trusted_markers(comments: Sequence[Mapping[str, Any]], login: str) -> list[tuple[tuple[str, str], dict[str, Any]]]:
    markers = []
    for index, comment in enumerate(comments):
        body = comment.get("body") if isinstance(comment, Mapping) else None
        if not isinstance(body, str):
            raise CarryOverRefused(LINEAGE, f"PR comment {index} malformed")
        if MARKER_PREFIX not in body:
            continue
        if (
            comment.get("user", {}).get("login") != login
            or comment.get("author_association") not in TRUSTED_ASSOCIATIONS
        ):
            continue
        marker = parse_marker(body)
        ref = comment.get("id", index)
        if marker is None:
            raise CarryOverRefused(LINEAGE, f"unreadable verdict marker in comment {ref}")
        if comment.get("created_at") != comment.get("updated_at"):
            raise CarryOverRefused(LINEAGE, f"verdict marker in comment {ref} was edited")
        if marker["family"] in UNATTESTED_FAMILIES or resolve_family(marker["model"]) != marker["family"]:
            raise CarryOverRefused(LINEAGE, f"verdict marker in comment {ref} has no attested reviewer family")
        markers.append(((marker["started"], str(comment.get("created_at"))), marker))
    return markers


def check_lineage(
    *,
    runs: Sequence[ReviewRun],
    comments: Sequence[Mapping[str, Any]],
    login: str,
    approved: str,
) -> list[str]:
    """Condition 4: return the seats (reviewer families) whose latest verdict is A's APPROVE.

    Every published verdict must belong to a run on record, and every run must
    be terminal with a reply: a finished run's verdict, model, family and start
    must match its published marker, and any other run's reply must carry no
    verdict at all.
    """
    markers = _trusted_markers(comments, login)
    claimed: set[tuple[str, str]] = set()
    for run in runs:
        status = run.record.get("status")
        if status not in TERMINAL_TASK_STATUSES:
            raise CarryOverRefused(LINEAGE, f"review task {run.task_id} is not terminal (status {status!r})")
        if run.reply is None:
            raise CarryOverRefused(LINEAGE, f"review task {run.task_id} ({status}) has no reply on record")
        if status != "done":
            if recognized_verdicts(run.reply):
                raise CarryOverRefused(LINEAGE, f"review task {run.task_id} ({status}) carries an unpublished verdict")
            continue
        try:
            verdict = recorder._review_verdict_and_count(run.reply)[0]
            # The recorder's own attestation and formal-reviewer rules decide who reviewed.
            model, family = recorder.reviewer_identity(run.record)
        except recorder.RecordError as exc:
            raise CarryOverRefused(LINEAGE, f"review task {run.task_id} evidence refused: {exc}") from None
        started = _started(run.record)
        published = [m for _, m in markers if m["task"] == run.task_id and m["started"] == started]
        if not published:
            raise CarryOverRefused(LINEAGE, f"review task {run.task_id} finished but its verdict is unpublished")
        for marker in published:
            if (
                marker["sha"] != run.record.get("worktree_base_sha")
                or marker["verdict"] != verdict
                or marker["model"] != model
                or marker["family"] != family
            ):
                raise CarryOverRefused(LINEAGE, f"published verdict of {run.task_id} conflicts with its task record")
        claimed.add((run.task_id, started))
    for _, marker in markers:
        if (marker["task"], marker["started"]) not in claimed:
            raise CarryOverRefused(LINEAGE, f"published verdict of task {marker['task']} has no review run on record")
    current = lookup_verdict(list(comments), approved, login)
    if current.state != "APPROVED":
        raise CarryOverRefused(LINEAGE, f"approved head {approved} reads as {current.state}, not APPROVED")
    latest: dict[str, dict[str, Any]] = {}
    for _, marker in sorted(markers, key=lambda item: item[0]):
        latest[marker["family"]] = marker
    for family, marker in sorted(latest.items()):
        if marker["sha"] != approved or marker["verdict"] in REJECTED:
            raise CarryOverRefused(
                LINEAGE, f"seat {family}'s latest verdict is {marker['verdict']} at {marker['sha']}, not A's APPROVE"
            )
    seats = sorted(latest)
    ukrainian = any(marker["sha"] == approved and is_ukrainian_review(marker) for _, marker in markers) or any(
        run.record.get("worktree_base_sha") == approved and is_ukrainian_review(run.record) for run in runs
    )
    required = UKRAINIAN_SEATS if ukrainian else 1
    if len(seats) < required:
        raise CarryOverRefused(LINEAGE, f"{len(seats)} seat(s) approved {approved}; this profile requires {required}")
    return seats


def check_ci(pull: Mapping[str, Any], head: str) -> None:
    """Condition 5: the PR's own CI rollup at N is green."""
    if pull.get("headRefOid") != head:
        raise CarryOverRefused(CI, "CI rollup does not belong to the carry-over head")
    if blockers := _check_blockers(pull):
        raise CarryOverRefused(CI, "same-head CI is not green: " + ", ".join(blockers))


def receipt_comment(receipt: Mapping[str, Any]) -> str:
    lines = [
        RECEIPT_HEADING,
        f"Approved head: {receipt['approved_head']}",
        f"Merged base commit: {receipt['base_commit']}",
        f"Carry-over head: {receipt['head']}",
        f"Merge-tree OID: {receipt['merge_tree']}",
        "Regenerated paths:",
        *(f"- `{item['path']}` sha256 `{item['sha256']}`" for item in receipt["regenerated"]),
        *([] if receipt["regenerated"] else ["- none"]),
        f"Seats whose latest verdict is the approval: {', '.join(receipt['seats'])}",
        f"Review tasks checked: {receipt['review_tasks']}",
        "Same-head CI: green",
        f"{RECEIPT_MARKER} approved={receipt['approved_head']} base={receipt['base_commit']} "
        f"head={receipt['head']} merge_tree={receipt['merge_tree']} -->",
    ]
    return "\n".join(lines)


def _pull(repository: str, number: int) -> dict[str, Any]:
    data = recorder._run_json(
        [
            "gh",
            "pr",
            "view",
            str(number),
            "--repo",
            repository,
            "--json",
            "number,state,headRefName,headRefOid,baseRefName,statusCheckRollup",
        ]
    )
    if not isinstance(data, dict) or data.get("state") != "OPEN" or data.get("number") != number:
        raise CarryOverRefused(TARGET, f"PR #{number} is not open")
    return data


def _base_tip(repository: str, base: str) -> str:
    data = recorder._run_json(["gh", "api", "--method", "GET", f"repos/{repository}/branches/{base}"])
    sha = data.get("commit", {}).get("sha") if isinstance(data, dict) else None
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise CarryOverRefused(TARGET, f"base branch {base} tip unavailable")
    return sha


@publication_boundary(recorder.RecordError)
def carry_over(
    pr_number: int,
    approved_head: str,
    *,
    repository: str,
    repo_root: Path,
    task_root: Path,
    lock_root: Path,
) -> dict[str, Any]:
    """Check conditions 1-5 for PR ``pr_number`` and record the carry-over on its head."""
    if not SHA.fullmatch(approved_head):
        raise CarryOverRefused(TARGET, "approved head must be a full lowercase SHA")
    pull = _pull(repository, pr_number)
    head, branch = pull.get("headRefOid"), pull.get("headRefName")
    if not isinstance(head, str) or not SHA.fullmatch(head) or not isinstance(branch, str):
        raise CarryOverRefused(TARGET, "PR head unavailable")
    base_tip = _base_tip(repository, str(pull.get("baseRefName") or ""))
    _ensure_commits(repo_root, [head, base_tip])
    base = check_pinned_merge(repo_root, approved=approved_head, head=head, base_tip=base_tip)
    registry = load_registry(repo_root, base_tip)
    tree, paths = check_merge_result(repo_root, approved=approved_head, base=base, head=head, registry=registry)
    regenerated = check_reproduction(repo_root, head=head, paths=paths, registry=registry)
    adapter = recorder.GitHubAdapter(repo_root)
    with recorder.sha_lock(repository, head, lock_root):
        # CI and review evidence are read here, under the lock and just before
        # publication, so nothing that arrives during regeneration is missed.
        current = _pull(repository, pr_number)
        if current.get("headRefOid") != head:
            raise CarryOverRefused(TARGET, "PR head moved during the carry-over check")
        check_ci(current, head)
        try:
            login = adapter.identity()
            comments = adapter.comments(repository, pr_number)
        except SweepError as exc:
            raise CarryOverRefused(LINEAGE, f"PR verdicts unavailable: {exc}") from None
        runs = lineage_runs(task_root, repository=repository, number=pr_number, branch=branch)
        seats = check_lineage(runs=runs, comments=comments, login=login, approved=approved_head)
        receipt = {
            "pr": pr_number,
            "approved_head": approved_head,
            "base_commit": base,
            "head": head,
            "merge_tree": tree,
            "regenerated": regenerated,
            "seats": seats,
            "review_tasks": len(runs),
        }
        body = receipt_comment(receipt)
        check_texts(normalize_repository(repository), [body], environment={})
        existing = any(
            item.get("body") == body
            and item.get("user", {}).get("login") == login
            and item.get("author_association") in TRUSTED_ASSOCIATIONS
            and item.get("created_at") == item.get("updated_at")
            for item in comments
        )
        if not existing:
            posted = recorder._run_json(Request("issue-comment-json", repo=repository, number=pr_number, body=body))
            comment_id = posted.get("id") if isinstance(posted, dict) else None
            if not isinstance(comment_id, int):
                raise recorder.RecordError("receipt comment post response lacked id; retry to reconcile")
            readback = recorder._run_json(Request("read-comment", repo=repository, number=comment_id))
            if (
                not isinstance(readback, dict)
                or readback.get("body") != body
                or readback.get("user", {}).get("login") != login
                or readback.get("author_association") not in TRUSTED_ASSOCIATIONS
                or readback.get("created_at") != readback.get("updated_at")
            ):
                raise recorder.RecordError("receipt comment readback mismatch; publication state unknown")
        try:
            recorder.post_commit_status(
                repository=repository,
                head_sha=head,
                state="success",
                context=STATUS_CONTEXT,
                description=f"carry-over of {approved_head[:12]} via base {base[:12]}; {len(regenerated)} regenerated",
            )
            status = "posted"
        except Exception as exc:
            status = f"failed: {exc}"
    return {**receipt, "comment": "existing" if existing else "posted", "status": status}


@publication_cli(recorder.RecordError)
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="record_cf_verdict.py carry-over",
        description="Carry an exact-head APPROVE across a generated-only base merge; never a review.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  .venv/bin/python scripts/review/record_cf_verdict.py carry-over --pr 1 "
        "--approved-head <40-hex>\n"
        f"Outputs: a receipt comment and the {STATUS_CONTEXT} commit status on the PR head; JSON receipt on stdout.\n"
        "Exit codes: 0: recorded; 1: refused (CARRY_OVER_REFUSED[reason]) or status publication failed.\n"
        "Policy: agents_extensions/shared/skills/review-loop/references/policy.md § Gate of record",
    )
    parser.add_argument("--pr", type=int, required=True, help="Open PR whose head is the base merge commit")
    parser.add_argument("--approved-head", required=True, help="Head A that holds every seat's latest APPROVE")
    parser.add_argument("--repository", help="owner/repo of a registered fleet repository (default: the default one)")
    args = parser.parse_args(argv)
    root = recorder._repo_root()
    try:
        catalog = recorder.load_fleet_repos()
        keys = [
            key
            for key, repo in catalog.items()
            if (repo.github.casefold() == args.repository.casefold() if args.repository else repo.default)
        ]
        if len(keys) != 1:
            raise CarryOverRefused(TARGET, "repository is not uniquely registered in the fleet catalog")
        try:
            repo_root = recorder.resolve_review_repository(root, keys[0], mode="pr")
        except (recorder.FleetRepoError, recorder.TargetResolutionError, OSError, subprocess.TimeoutExpired):
            raise CarryOverRefused(TARGET, "repository checkout unavailable") from None
        result = carry_over(
            args.pr,
            args.approved_head,
            repository=catalog[keys[0]].github,
            repo_root=repo_root,
            task_root=root / "batch_state" / "tasks",
            lock_root=root / "batch_state" / "locks",
        )
    except (recorder.RecordError, recorder.FleetRepoError, SweepError) as exc:
        print(f"carry-over refused: {exc}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "posted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
