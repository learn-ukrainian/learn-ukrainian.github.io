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
   checked-in generated-path registry (``scripts/config/generated_paths.yaml``).
3. ``reproduction``: each such path's generator, run on N in a clean temporary
   worktree, reproduces N's committed bytes exactly.
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
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
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


def load_registry(repo_root: Path, head: str) -> dict[str, Generated]:
    """The generated-path registry as committed at ``head``."""
    raw = _git(repo_root, "cat-file", "blob", f"{head}:{REGISTRY_PATH}", ok=(0, 128))
    try:
        data = yaml.safe_load(raw.decode("utf-8")) if raw else None
    except (UnicodeDecodeError, yaml.YAMLError):
        data = None
    entries = data.get("generated_paths") if isinstance(data, dict) and data.get("schema_version") == 1 else None
    if not isinstance(entries, dict) or not entries:
        raise CarryOverRefused(REGISTRY, f"{REGISTRY_PATH} missing or malformed at {head}")
    registry: dict[str, Generated] = {}
    for path, entry in entries.items():
        command = entry.get("command") if isinstance(entry, dict) else None
        pure = PurePosixPath(path) if isinstance(path, str) else None
        if (
            pure is None
            or pure.is_absolute()
            or ".." in pure.parts
            or str(pure) != path
            or not isinstance(command, list)
            or not command
            or not all(isinstance(part, str) and part for part in command)
        ):
            raise CarryOverRefused(REGISTRY, f"registry entry {path!r} malformed")
        registry[path] = Generated(path, tuple(command))
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


def check_reproduction(
    repo_root: Path, *, head: str, paths: Sequence[str], registry: Mapping[str, Generated]
) -> list[dict[str, str]]:
    """Condition 3: regenerate ``paths`` on a clean worktree of ``head``; return their sha256."""
    if not paths:
        return []
    env = {**sanitized_git_env(), "GIT_LFS_SKIP_SMUDGE": "1"}
    with TemporaryDirectory(prefix="carry-over-", dir=ensure_scratch_root()) as scratch:
        tree = Path(scratch) / "tree"
        # Hooks heal and guard real checkouts; this one is a throwaway copy of ``head``.
        _git(
            repo_root,
            "-c",
            "core.hooksPath=/dev/null",
            "worktree",
            "add",
            "--quiet",
            "--detach",
            str(tree),
            head,
            env=env,
        )
        try:
            node_modules = repo_root / "node_modules"
            if node_modules.is_dir() and not (tree / "node_modules").exists():
                # Generators may need the checkout's Node packages, as they need its interpreter.
                (tree / "node_modules").symlink_to(node_modules, target_is_directory=True)
            for path in paths:
                target = tree / path
                if not target.parent.resolve().is_relative_to(tree.resolve()) or target.is_dir():
                    raise CarryOverRefused(REPRODUCTION, f"{path} is not a file inside the worktree")
                target.unlink(missing_ok=True)
            for command in dict.fromkeys(registry[path].command for path in paths):
                argv = [sys.executable, *command[1:]] if command[0] == "python" else list(command)
                try:
                    result = subprocess.run(
                        argv, cwd=tree, capture_output=True, check=False, timeout=GENERATOR_TIMEOUT_S, env=env
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    raise CarryOverRefused(REPRODUCTION, f"generator {' '.join(command)} did not run: {exc}") from None
                if result.returncode:
                    detail = result.stderr.decode("utf-8", "replace").strip()[-300:]
                    raise CarryOverRefused(
                        REPRODUCTION, f"generator {' '.join(command)} exited {result.returncode}: {detail}"
                    )
            receipts = []
            for path in paths:
                committed = _git(repo_root, "cat-file", "blob", f"{head}:{path}", ok=(0, 128))
                produced = tree / path
                if not produced.is_file() or produced.is_symlink():
                    raise CarryOverRefused(REPRODUCTION, f"generator did not produce {path}")
                if produced.read_bytes() != committed:
                    raise CarryOverRefused(
                        REPRODUCTION, f"regenerated {path} differs from the bytes committed at {head}"
                    )
                receipts.append({"path": path, "sha256": hashlib.sha256(committed).hexdigest()})
            return receipts
        finally:
            try:
                _git(repo_root, "worktree", "remove", "--force", str(tree))
            except CarryOverRefused:
                shutil.rmtree(tree, ignore_errors=True)
                _git(repo_root, "worktree", "prune")


def _is_review_task(task: Mapping[str, Any]) -> bool:
    return bool(
        task.get("require_review_verdict")
        or task.get("review_profile")
        or task.get("review_mode")
        or task.get("review_attempt")
        or task.get("type") == "review"
    )


def lineage_tasks(task_root: Path, *, repository: str, number: int, branch: str) -> dict[str, dict[str, Any]]:
    """Every hot or archived review task record of this PR, by task id."""
    tasks: dict[str, dict[str, Any]] = {}
    try:
        # A hot record is read after its archived copy, so the hot one wins (``_hot_or_archived``).
        paths = [*sorted((task_root / ARCHIVE_DIR_NAME).glob("*.json")), *sorted(task_root.glob("*.json"))]
    except OSError as exc:
        raise CarryOverRefused(LINEAGE, f"task ledger unavailable: {exc}") from None
    for path in paths:
        try:
            task = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CarryOverRefused(LINEAGE, f"task record {path.name} unreadable: {exc}") from None
        if not isinstance(task, dict) or task.get("status") in {"dry_run", "dry-run"} or not _is_review_task(task):
            continue
        if not isinstance(task.get("repository"), str) or normalize_repository(
            task["repository"]
        ) != normalize_repository(repository):
            continue
        if task.get("pr") == number or task.get("review_branch") == branch:
            tasks[path.stem] = {**task, "_result_path": path.with_suffix(".result")}
    return tasks


def check_lineage(
    *,
    tasks: Mapping[str, Mapping[str, Any]],
    comments: Sequence[Mapping[str, Any]],
    login: str,
    approved: str,
) -> list[str]:
    """Condition 4: return the seats (reviewer families) whose latest verdict is A's APPROVE."""
    markers: list[tuple[tuple[str, str], dict[str, Any]]] = []
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
        if marker is None:
            raise CarryOverRefused(LINEAGE, f"unreadable verdict marker in comment {comment.get('id', index)}")
        if comment.get("created_at") != comment.get("updated_at"):
            raise CarryOverRefused(LINEAGE, f"verdict marker in comment {comment.get('id', index)} was edited")
        if marker["family"] in UNATTESTED_FAMILIES:
            raise CarryOverRefused(LINEAGE, f"verdict by task {marker['task']} has no attested reviewer family")
        markers.append(((marker["started"], str(comment.get("created_at"))), marker))
    published = {marker["task"]: marker for _, marker in markers}
    for task_id, task in sorted(tasks.items()):
        status = task.get("status")
        if status not in TERMINAL_TASK_STATUSES:
            raise CarryOverRefused(LINEAGE, f"review task {task_id} is not terminal (status {status!r})")
        if status == "done":
            marker = published.get(task_id)
            if marker is None:
                raise CarryOverRefused(LINEAGE, f"review task {task_id} finished but its verdict is unpublished")
            if marker["sha"] != task.get("worktree_base_sha"):
                raise CarryOverRefused(LINEAGE, f"published verdict of {task_id} names another head than its task")
            continue
        result = task["_result_path"]
        try:
            reply = result.read_text(encoding="utf-8") if result.exists() else ""
        except (OSError, UnicodeError) as exc:
            raise CarryOverRefused(LINEAGE, f"review task {task_id} reply unreadable: {exc}") from None
        if recognized_verdicts(reply):
            raise CarryOverRefused(LINEAGE, f"review task {task_id} ({status}) carries an unpublished verdict")
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
        task.get("worktree_base_sha") == approved and is_ukrainian_review(task) for task in tasks.values()
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
    registry = load_registry(repo_root, head)
    tree, paths = check_merge_result(repo_root, approved=approved_head, base=base, head=head, registry=registry)
    regenerated = check_reproduction(repo_root, head=head, paths=paths, registry=registry)
    adapter = recorder.GitHubAdapter(repo_root)
    try:
        login = adapter.identity()
        comments = adapter.comments(repository, pr_number)
    except SweepError as exc:
        raise CarryOverRefused(LINEAGE, f"PR verdicts unavailable: {exc}") from None
    tasks = lineage_tasks(task_root, repository=repository, number=pr_number, branch=branch)
    seats = check_lineage(tasks=tasks, comments=comments, login=login, approved=approved_head)
    check_ci(pull, head)
    receipt = {
        "pr": pr_number,
        "approved_head": approved_head,
        "base_commit": base,
        "head": head,
        "merge_tree": tree,
        "regenerated": regenerated,
        "seats": seats,
        "review_tasks": len(tasks),
    }
    body = receipt_comment(receipt)
    check_texts(normalize_repository(repository), [body], environment={})
    with recorder.sha_lock(repository, head, lock_root):
        if _pull(repository, pr_number).get("headRefOid") != head:
            raise CarryOverRefused(TARGET, "PR head moved during the carry-over check")
        try:
            existing = any(
                item.get("body") == body
                and item.get("user", {}).get("login") == login
                and item.get("author_association") in TRUSTED_ASSOCIATIONS
                for item in adapter.comments(repository, pr_number)
            )
        except SweepError as exc:
            raise CarryOverRefused(TARGET, f"PR comments unavailable: {exc}") from None
        if not existing:
            posted = recorder._run_json(Request("issue-comment-json", repo=repository, number=pr_number, body=body))
            if not isinstance(posted, dict) or not isinstance(posted.get("id"), int):
                raise recorder.RecordError("receipt comment post response lacked id; retry to reconcile")
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
