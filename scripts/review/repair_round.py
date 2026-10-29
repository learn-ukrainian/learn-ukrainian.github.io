"""One repair-verification review round per lineage, ever, outside the review budget.

A PR approved at head A in its last reviewed round can still need a new head N:
CI failed after the approval, or a base-branch change conflicts with it. The
budget may be spent by then, and a recorded rejection or the end of the budget
is never approval. This round lets the recorder admit one more round at N
without a request PR. Approved design: CTO proposal, Sol 6.1 APPROVE WITH
CHANGES (advisory task cto-7923-adv-clog-sol, item 3a and 3c). It replaces the
budget extension's request on the default branch.

Admission, at the recorder and in the pre-dispatch ``budget-check``:

1. Approved. The PR's review lineage before N passes ``review_lineage``: every
   run terminal and published, and A's APPROVE the latest verdict of every
   seat, with as many seats as the profile needs. A is the PR's latest
   reviewed head. An unpublished run that a later verdict of its own seat,
   at another head before N, supersedes is listed in the receipt, never
   dropped; an approval at N supersedes nothing.
2. Classified. Every commit on the first-parent path from N back to A is one
   of: a Git-proven clean merge of the default branch; a conflicted merge of
   it whose tree differs from Git's own merge of its two parents only in the
   paths Git reports conflicted (``git merge-tree --name-only``); or an
   ordinary commit. A path of clean and conflicted merges with at least one
   conflict is a ``conflict-resolution``. A path of clean merges and ordinary
   commits is a ``ci-fix`` only when a failed CI run is tied to A: a failed
   PR run at head A, or a failed merge-queue run of this PR whose candidate
   tree equals Git's merge of its queue base with A. Anything else is
   unclassifiable and refuses: escalate to the CTO.
3. Unused. The lineage has no receipt for another round. Its keys are the
   repository and PR, the head branch, and every issue the PR closes; one
   receipt per key. A receipt for this same PR, approved head and candidate
   is the same round (a second seat, or a retried publication).

The recorder writes the admission receipt for every key before it posts the
verdict and marks it consumed after posting. Receipts are never removed: no
approval, replacement PR or session replenishes the round. The receipt binds
A, N and the complete repair delta (its commits, classification, evidence and
the SHA-256 of ``git diff --binary --full-index A N``), which the round's
reviewer covers with the callers, invariants and weakened tests it affects.
Cooperative threat model, as in ``bounded_advisory``: a process that can
rewrite the receipts, task records or GitHub's records is outside it.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.orchestration.integration_sweep import SHA
from scripts.review import record_cf_verdict as recorder
from scripts.review.review_lineage import LineageRefused, check_lineage, lineage_runs, superseded_runs

RECEIPT_DIR = "review-repair-rounds"
RECEIPT_SCHEMA = "review-repair-round.v1"
CI_FIX = "ci-fix"
CONFLICT_RESOLUTION = "conflict-resolution"
MAX_REPAIR_COMMITS = 20
FAILED_CONCLUSIONS = frozenset({"failure", "timed_out"})
# Only the required CI workflow's PR and merge-queue runs are CI evidence; a manual or other run is not.
REQUIRED_WORKFLOW = ".github/workflows/ci.yml"
CI_EVENTS = frozenset({"pull_request", "merge_group"})
# The round's reviewer verifies the complete delta is only the repair, bound to its digest.
REPAIR_VERIFIED = re.compile(r"(?m)^\s*REPAIR_VERIFIED:\s*([0-9a-f]{64})\s*$")
GIT_TIMEOUT_S = 60.0

# Typed refusal reasons.
LINEAGE = "lineage"
UNCLASSIFIABLE = "unclassifiable"
EVIDENCE = "evidence"
SPENT = "spent"
VERIFICATION = "verification"


class RepairRefused(recorder.RecordError):
    """A repair-verification round condition failed; ``reason`` names which one."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"REPAIR_ROUND_REFUSED[{reason}]: {detail}")
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class GitHubReads:
    """The GitHub facts a CI-fix classification reads; injectable for tests."""

    failed_runs: Callable[[str], list[dict[str, Any]]]
    queue_runs: Callable[[], list[dict[str, Any]]]
    commit_tree: Callable[[str], str | None]
    closing_issues: Callable[[], list[int]]


def github_reads(repository: str, number: int) -> GitHubReads:
    """Live reads through the recorder's GitHub client."""

    def runs(query: str) -> list[dict[str, Any]]:
        data = recorder._run_json(["gh", "api", f"repos/{repository}/actions/runs?{query}&per_page=100"])
        found = data.get("workflow_runs") if isinstance(data, dict) else None
        return [run for run in found if isinstance(run, dict)] if isinstance(found, list) else []

    def commit_tree(sha: str) -> str | None:
        data = recorder._run_json(["gh", "api", f"repos/{repository}/git/commits/{sha}"])
        tree = data.get("tree") if isinstance(data, dict) else None
        value = tree.get("sha") if isinstance(tree, dict) else None
        return value if isinstance(value, str) and SHA.fullmatch(value) else None

    def closing_issues() -> list[int]:
        data = recorder._run_json(
            ["gh", "pr", "view", str(number), "--repo", repository, "--json", "closingIssuesReferences"]
        )
        refs = data.get("closingIssuesReferences") if isinstance(data, dict) else None
        if not isinstance(refs, list):
            raise RepairRefused(LINEAGE, f"PR #{number} closing issues unavailable")
        return sorted({ref["number"] for ref in refs if isinstance(ref, dict) and isinstance(ref.get("number"), int)})

    return GitHubReads(
        failed_runs=lambda sha: runs(f"head_sha={sha}"),
        queue_runs=lambda: runs("event=merge_group"),
        commit_tree=commit_tree,
        closing_issues=closing_issues,
    )


def _run_git(command: list[str], env: Mapping[str, str], ok: tuple[int, ...]) -> tuple[int, bytes]:
    try:
        proc = subprocess.run(command, capture_output=True, env=dict(env), check=False, timeout=GIT_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RepairRefused(UNCLASSIFIABLE, f"git {command[-1]} unavailable: {type(exc).__name__}") from None
    if proc.returncode not in ok:
        raise RepairRefused(UNCLASSIFIABLE, "a git step failed for the repair delta")
    return proc.returncode, proc.stdout


def _git(repo_root: Path, *args: str, ok: tuple[int, ...] = (0,)) -> tuple[int, str]:
    """One bounded Git read with the recorder's isolation; another exit code proves nothing."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({"GIT_NO_REPLACE_OBJECTS": "1", "GIT_GRAFT_FILE": os.devnull, "GIT_NO_LAZY_FETCH": "1"})
    command = ["git", "-C", str(repo_root), "-c", "core.commitGraph=false", "--no-replace-objects", *args]
    code, out = _run_git(command, env, ok)
    return code, out.decode("utf-8", "replace")


def _merge_tree(repo_root: Path, *args: str, compare: str | None = None) -> tuple[int, list[str], set[str] | None]:
    """``git merge-tree --write-tree`` in a throwaway object store (it writes the merged tree).

    Returns its exit code, its output lines and, when ``compare`` names a tree,
    the paths where Git's merge differs from it.
    """
    try:
        with recorder.isolated_object_store(repo_root) as env:
            code, out = _run_git(["git", "merge-tree", "--write-tree", "--no-messages", *args], env, (0, 1))
            lines = out.decode("utf-8", "replace").splitlines()
            changed = None
            if compare is not None and lines and SHA.fullmatch(lines[0]):
                _, diff = _run_git(["git", "diff", "--name-only", "--no-renames", lines[0], compare], env, (0,))
                changed = {line for line in diff.decode("utf-8", "replace").splitlines() if line}
    except OSError:
        raise RepairRefused(UNCLASSIFIABLE, "the object store is unavailable for the repair delta") from None
    return code, lines, changed


@dataclass
class RepairDelta:
    approved: str
    candidate: str
    commits: list[dict[str, Any]] = field(default_factory=list)

    @property
    def kinds(self) -> set[str]:
        return {commit["kind"] for commit in self.commits}


def _conflict_resolution(repo_root: Path, entry: Mapping[str, Any]) -> list[str] | None:
    """The conflicted paths a merge resolves, when its tree differs from Git's merge only there."""
    parents = [parent["sha"] for parent in entry["parents"]]
    tree = entry["commit"]["tree"]["sha"]
    code, lines, edited = _merge_tree(repo_root, "--name-only", *parents, compare=tree)
    if code != 1 or not lines or not SHA.fullmatch(lines[0]) or edited is None:
        return None
    conflicted = sorted({line for line in lines[1:] if line})
    if not conflicted or not edited <= set(conflicted):
        return None
    return conflicted


def classify_delta(repo_root: Path, *, approved: str, candidate: str, base_tip: str) -> RepairDelta:
    """Each commit on the first-parent path from ``candidate`` back to ``approved``, typed."""
    delta = RepairDelta(approved, candidate)
    current = candidate
    deadline = time.monotonic() + recorder.BRANCH_FACTS_TIMEOUT_S
    while current != approved:
        if len(delta.commits) >= MAX_REPAIR_COMMITS:
            raise RepairRefused(
                UNCLASSIFIABLE, f"{candidate} is not within {MAX_REPAIR_COMMITS} first-parent commits of {approved}"
            )
        try:
            entry = recorder._read_commit_entries(repo_root, [current], deadline=deadline)[0]
        except recorder.RecordError:
            raise RepairRefused(UNCLASSIFIABLE, f"commit {current} is not available locally; fetch and retry") from None
        parents = [parent["sha"] for parent in entry["parents"]]
        if not parents:
            raise RepairRefused(UNCLASSIFIABLE, f"{candidate} does not descend from the approved head {approved}")
        item: dict[str, Any] = {"sha": current}
        if len(parents) == 1:
            item["kind"] = "commit"
        elif len(parents) == 2:
            on_base = _git(repo_root, "merge-base", "--is-ancestor", parents[1], base_tip, ok=(0, 1))[0] == 0
            if not on_base:
                raise RepairRefused(UNCLASSIFIABLE, f"merge {current} brings in {parents[1]}, which is not on the base")
            if recorder._clean_merge_source(entry, base_tip, checkout=repo_root) == recorder.CLEAN_BASE_MERGE:
                item["kind"] = "clean-merge"
            else:
                conflicted = _conflict_resolution(repo_root, entry)
                if conflicted is None:
                    raise RepairRefused(
                        UNCLASSIFIABLE,
                        f"merge {current} changes more than the paths its conflict left unresolved, or has no conflict",
                    )
                item.update(kind="conflict-merge", conflicted_paths=conflicted)
        else:
            raise RepairRefused(UNCLASSIFIABLE, f"commit {current} has {len(parents)} parents")
        delta.commits.append(item)
        current = parents[0]
    if not delta.commits:
        raise RepairRefused(UNCLASSIFIABLE, f"head {candidate} is the approved head; nothing to verify")
    return delta


def _required_failure(run: Mapping[str, Any]) -> bool:
    """A failed run of the required CI workflow on a PR or merge-queue event."""
    path = str(run.get("path") or "").split("@", 1)[0]
    return path == REQUIRED_WORKFLOW and run.get("event") in CI_EVENTS and run.get("conclusion") in FAILED_CONCLUSIONS


def failed_runs_for(approved: str, *, number: int, repo_root: Path, github: GitHubReads) -> list[dict[str, Any]]:
    """Failed CI runs of the approved head itself, or of this PR's merge-queue candidate built from it."""
    tied = [
        {"run_id": run.get("id"), "event": run.get("event"), "conclusion": run.get("conclusion")}
        for run in github.failed_runs(approved)
        if run.get("head_sha") == approved and _required_failure(run) and run.get("event") == "pull_request"
    ]
    queue = re.compile(rf"gh-readonly-queue/[^/]+(?:/[^/]+)*/pr-{number}-([0-9a-f]{{40}})\Z")
    for run in github.queue_runs():
        match = queue.match(str(run.get("head_branch") or ""))
        if (
            not match
            or not _required_failure(run)
            or run.get("event") != "merge_group"
            or not SHA.fullmatch(str(run.get("head_sha")))
        ):
            continue
        # The squash candidate holds exactly the queue base merged with this head.
        try:
            code, lines, _ = _merge_tree(repo_root, match[1], approved)
        except RepairRefused:
            continue
        expected = lines[0] if lines else ""
        if code == 0 and SHA.fullmatch(expected) and github.commit_tree(str(run["head_sha"])) == expected:
            tied.append({"run_id": run.get("id"), "event": "merge_group", "conclusion": run.get("conclusion")})
    return tied


def _diff_sha256(repo_root: Path, approved: str, candidate: str) -> str:
    """The SHA-256 of the complete repair delta's bytes."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({"GIT_NO_REPLACE_OBJECTS": "1", "GIT_GRAFT_FILE": os.devnull, "GIT_NO_LAZY_FETCH": "1"})
    command = ["git", "-C", str(repo_root), "--no-replace-objects", "diff", "--binary", "--full-index"]
    _, out = _run_git([*command, "--no-renames", "--no-ext-diff", "--no-textconv", approved, candidate], env, (0,))
    return hashlib.sha256(out).hexdigest()


def lineage_keys(repository: str, number: int, branch: str, issues: Sequence[int]) -> list[str]:
    repo = repository.casefold()
    return sorted({f"pr:{repo}#{number}", f"branch:{repo}:{branch}", *(f"issue:{repo}#{issue}" for issue in issues)})


def _receipt_path(root: Path, key: str) -> Path:
    return root / f"{hashlib.sha256(key.encode('utf-8')).hexdigest()[:32]}.json"


def _read_receipt(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise RepairRefused(SPENT, f"repair receipt {path.name} unreadable: {exc}") from None
    if not isinstance(data, dict) or data.get("schema") != RECEIPT_SCHEMA:
        raise RepairRefused(SPENT, f"repair receipt {path.name} is not a {RECEIPT_SCHEMA} record")
    return data


def _same_round(receipt: Mapping[str, Any], *, repository: str, number: int, approved: str, candidate: str) -> bool:
    return (
        str(receipt.get("repository", "")).casefold() == repository.casefold()
        and receipt.get("pr") == number
        and receipt.get("approved_head") == approved
        and receipt.get("candidate_head") == candidate
    )


def repair_heads(receipt_root: Path, *, repository: str, number: int, branch: str) -> frozenset[str]:
    """Candidate heads this PR's repair round admitted: they consume no budgeted round."""
    repo = repository.casefold()
    receipts = [
        _read_receipt(_receipt_path(receipt_root, key)) for key in (f"pr:{repo}#{number}", f"branch:{repo}:{branch}")
    ]
    return frozenset(
        str(item["candidate_head"])
        for item in receipts
        if item and str(item.get("repository", "")).casefold() == repo and item.get("pr") == number
    )


def admit_repair_round(
    *,
    repository: str,
    number: int,
    branch: str,
    head: str,
    comments: Sequence[Mapping[str, Any]],
    login: str,
    task_root: Path,
    repo_root: Path,
    receipt_root: Path,
    github: GitHubReads | None = None,
    fetch: bool = True,
) -> dict[str, Any]:
    """The receipt of the lineage's one repair round at ``head``, or a refusal. Reads only."""
    github = github or github_reads(repository, number)
    markers = recorder._trusted_markers(comments, login)
    others = [marker for _, marker in markers if marker["sha"] != head]
    if not others:
        raise RepairRefused(LINEAGE, f"PR #{number} has no reviewed head before {head}")
    approved = others[-1]["sha"]
    keys = lineage_keys(repository, number, branch, github.closing_issues())
    # Every key is checked: one receipt of another round anywhere spends the lineage.
    found = {key: _read_receipt(_receipt_path(receipt_root, key)) for key in keys}
    for key, receipt in found.items():
        if receipt is not None and not _same_round(
            receipt, repository=repository, number=number, approved=approved, candidate=head
        ):
            raise RepairRefused(
                SPENT,
                f"lineage {key} used its one repair round at PR #{receipt.get('pr')} "
                f"({receipt.get('approved_head')} to {receipt.get('candidate_head')}); escalate to the CTO",
            )
    try:
        runs = lineage_runs(task_root, repository=repository, number=number, branch=branch)
        seats = check_lineage(runs=runs, comments=comments, login=login, approved=approved, exclude_head=head)
    except LineageRefused as exc:
        raise RepairRefused(
            LINEAGE, f"the last reviewed head {approved} is not an approval of record: {exc.detail}"
        ) from None
    # Listed, never dropped: each unpublished run that its seat's later verdict superseded.
    superseded = superseded_runs(runs=runs, comments=comments, login=login, exclude_head=head)
    prior = next((receipt for receipt in found.values() if receipt is not None), None)
    if prior is not None:
        # A retry of the round admitted here: the lineage is checked again above, its receipt
        # stands, and any key it lacks is added.
        keys = sorted({*prior.get("lineage_keys", ()), *keys})
        return {
            **prior,
            "lineage_keys": keys,
            "approved_seats": seats,
            "superseded_runs": superseded,
            "same_round": True,
        }
    base_tip, _ = recorder.default_branch_review_base(repo_root, head, fetch=fetch)
    delta = classify_delta(repo_root, approved=approved, candidate=head, base_tip=base_tip)
    kinds = delta.kinds
    evidence: dict[str, Any] = {}
    if "conflict-merge" in kinds and kinds <= {"conflict-merge", "clean-merge"}:
        kind = CONFLICT_RESOLUTION
        evidence["conflicted_paths"] = sorted(
            {path for commit in delta.commits for path in commit.get("conflicted_paths", ())}
        )
    elif "commit" in kinds and kinds <= {"commit", "clean-merge"}:
        kind = CI_FIX
        runs = failed_runs_for(approved, number=number, repo_root=repo_root, github=github)
        if not runs:
            raise RepairRefused(
                EVIDENCE,
                f"no failed CI run is tied to the approved head {approved} (its own PR run, or this PR's "
                "merge-queue candidate built from it); a change after approval without one escalates",
            )
        evidence["failed_runs"] = runs
    else:
        raise RepairRefused(
            UNCLASSIFIABLE,
            f"the change after approval mixes {sorted(kinds)}; only a CI fix or a conflict resolution "
            "is verified outside the budget, so escalate to the CTO",
        )
    return {
        "schema": RECEIPT_SCHEMA,
        "repository": repository,
        "pr": number,
        "branch": branch,
        "lineage_keys": keys,
        "approved_head": approved,
        "approved_seats": seats,
        "superseded_runs": superseded,
        "candidate_head": head,
        "class": kind,
        "commits": delta.commits,
        "delta_sha256": _diff_sha256(repo_root, approved, head),
        **evidence,
        "state": "admitted",
    }


def _write_json(path: Path, data: Mapping[str, Any], *, exclusive: bool) -> None:
    payload = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if exclusive:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        return
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def record_admission(receipt_root: Path, receipt: Mapping[str, Any]) -> None:
    """Write the admission receipt under every lineage key that lacks it; a key held by another round refuses.

    A retry completes the keys an interrupted attempt left unwritten, so the
    round is spent under every key before its verdict is posted.
    """
    receipt_root.mkdir(parents=True, exist_ok=True)
    body = {key: value for key, value in receipt.items() if key != "same_round"}
    stamped = {**body, "admitted_at": body.get("admitted_at") or datetime.now(UTC).isoformat(timespec="seconds")}
    written: list[Path] = []
    for key in receipt["lineage_keys"]:
        path = _receipt_path(receipt_root, key)
        try:
            _write_json(path, {**stamped, "state": "admitted"}, exclusive=True)
        except FileExistsError:
            existing = _read_receipt(path)
            if existing and _same_round(
                existing,
                repository=str(receipt["repository"]),
                number=int(receipt["pr"]),
                approved=str(receipt["approved_head"]),
                candidate=str(receipt["candidate_head"]),
            ):
                continue
            for done in written:
                done.unlink(missing_ok=True)
            raise RepairRefused(
                SPENT, f"lineage {key} took its repair round concurrently; escalate to the CTO"
            ) from None
        written.append(path)


def receipt_at(receipt_root: Path, *, repository: str, number: int, branch: str, head: str) -> dict[str, Any] | None:
    """This PR's repair-round receipt when ``head`` is its candidate, else None."""
    repo = repository.casefold()
    for key in (f"pr:{repo}#{number}", f"branch:{repo}:{branch}"):
        receipt = _read_receipt(_receipt_path(receipt_root, key))
        if receipt and receipt.get("pr") == number and receipt.get("candidate_head") == head:
            return receipt
    return None


def require_repair_verified(reply: str, receipt: Mapping[str, Any]) -> None:
    """An APPROVE in the repair round names the delta it verified as only the repair."""
    attested = REPAIR_VERIFIED.findall(reply)
    if attested != [receipt.get("delta_sha256")]:
        raise RepairRefused(
            VERIFICATION,
            "an APPROVE in the repair round needs exactly one line "
            f"`REPAIR_VERIFIED: {receipt.get('delta_sha256')}`, the reviewer's statement that the complete "
            "delta is only the repair it names",
        )


def record_consumption(receipt_root: Path, receipt: Mapping[str, Any], *, comment: str) -> None:
    """Mark the round consumed once its verdict is posted; the receipt itself is never removed."""
    for key in receipt["lineage_keys"]:
        path = _receipt_path(receipt_root, key)
        current = _read_receipt(path)
        if current is None or current.get("state") == "consumed":
            continue
        _write_json(
            path,
            {
                **current,
                "state": "consumed",
                "verdict_comment": comment,
                "consumed_at": datetime.now(UTC).isoformat(timespec="seconds"),
            },
            exclusive=False,
        )
