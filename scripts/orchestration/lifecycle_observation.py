"""Local lifecycle capture before cleanup, and verified preserved-output recovery.

No GitHub calls or removal operations live here. The lifecycle API owns receipt
appends; the existing common reaper retains every other removal guard.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.fleet import ignored_task_output
from scripts.orchestration import task_lifecycle as tl


class ObservationRefusal(tl.LifecycleError):
    """A stable refusal code suitable for cleanup and recovery receipts."""


_REPOSITORY_ROOT: ContextVar[Path | None] = ContextVar("lifecycle_observation_root", default=None)


@contextmanager
def repository_context(repo_root: Path):
    """Supply runtime locator context without persisting a host path."""
    token = _REPOSITORY_ROOT.set(repo_root)
    try:
        yield
    finally:
        _REPOSITORY_ROOT.reset(token)


def _resolve_locator(root: Path, locator: str) -> Path:
    relative = Path(locator)
    if not locator or relative.is_absolute() or ".." in relative.parts:
        raise ObservationRefusal("RECOVERY_LOCATOR_INVALID")
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ObservationRefusal("RECOVERY_LOCATOR_INVALID")
    return path


def _locator(root: Path, path: Path) -> str:
    try:
        relative = path.absolute().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ObservationRefusal("RECOVERY_LOCATOR_INVALID") from exc
    _resolve_locator(root, relative)
    return relative


def _source(path: Path, root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    try:
        locator = _locator(root, path)
        if path.resolve(strict=True) != path.absolute() or not path.is_file():
            raise ObservationRefusal("RECOVERY_INPUT_NOT_REGULAR")
        raw = path.read_bytes()
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ObservationRefusal("RECOVERY_INPUT_INVALID")
        return value, {"path": locator, "sha256": hashlib.sha256(raw).hexdigest()}
    except ObservationRefusal:
        raise
    except (OSError, ValueError) as exc:
        raise ObservationRefusal("RECOVERY_INPUT_UNAVAILABLE") from exc


def _local_paths(repo_root: Path, local: Mapping[str, Any]) -> dict[str, Any]:
    primary = tl.canonical_state_root(repo_root)
    result = dict(local)
    result["primary_checkout"] = "."
    if result.get("worktree"):
        result["worktree"] = _locator(primary, Path(result["worktree"]))
    return result


def _append(path: Path, ledger: Mapping[str, Any], local: Mapping[str, Any], now: str):
    observation = {
        "schema_version": tl.OBSERVATION_SCHEMA_VERSION,
        "observed_at": now,
        "github": {"error": "local capture only; reconcile with current GitHub authority before closure"},
        "local": dict(local),
    }
    updated, receipt, replayed = tl.reconcile(ledger, observation, now=now)
    tl.write_lifecycle(path, updated)
    return receipt, replayed


def before_reap(
    repo_root: Path,
    worktree: Path,
    *,
    tasks_dir: Path | None = None,
    no_lifecycle_observation: str | None = None,
) -> list[dict[str, Any]]:
    """Append local observations for every bound lifecycle, or refuse removal.

    An explicit bypass reason is returned in the caller's cleanup report.
    Missing ledgers leave existing cleanup behavior unchanged.
    """
    if no_lifecycle_observation is not None:
        if not no_lifecycle_observation.strip():
            raise ObservationRefusal("LIFECYCLE_OBSERVATION_BYPASS_REASON_REQUIRED")
        return [{"status": "bypassed", "reason": no_lifecycle_observation}]
    primary = tl.canonical_state_root(repo_root)
    records = ignored_task_output.matching_worktree_records(
        worktree,
        tasks_dir or primary / "batch_state/tasks",
        repo_root=repo_root,
        publish_cache=False,
    )
    receipts = []
    for _, task in records:
        carrier = task.get("task_lifecycle")
        if not carrier:
            continue
        locator = carrier.get("state_file")
        path = primary / Path(locator) if locator else tl.lifecycle_path(repo_root, carrier["identity"])
        if not path.exists():
            # A carried lifecycle is a claim that must not silently disappear.
            raise ObservationRefusal("LIFECYCLE_LEDGER_MISSING")
        with repository_context(repo_root), tl.lifecycle_lock(path):
            ledger = tl.load_lifecycle(path)
            if ledger["lifecycle_id"] != carrier["lifecycle_id"]:
                raise ObservationRefusal("LIFECYCLE_IDENTITY_MISMATCH")
            if tl._latest_premerge_local(ledger) is not None:
                continue
            if not worktree.is_dir():
                raise ObservationRefusal("LIFECYCLE_WORKTREE_ABSENT")
            head = tl._run_git(worktree, ["rev-parse", "HEAD"])
            local = tl.observe_local_git(
                repo_root,
                head_sha=head,
                branch=task.get("worktree_branch"),
                worktree=str(worktree),
                base_sha=task.get("worktree_base_sha"),
            )
            if not all(
                local.get(k)
                for k in (
                    "dispatch_worktree_used",
                    "worktree_present",
                    "worktree_branch_matches",
                    "commits",
                )
            ):
                raise ObservationRefusal("LIFECYCLE_LOCAL_OBSERVATION_INCOMPLETE")
            now = datetime.now(UTC).isoformat()
            receipt, _ = _append(path, ledger, _local_paths(repo_root, local), now)
            receipts.append({"status": "recorded", "receipt_id": receipt["id"]})
    return receipts


def _recovered_local(repo_root: Path, ledger: Mapping[str, Any], recovery: Mapping[str, Any]) -> dict[str, Any]:
    """Re-read every input and reconstruct facts; stored booleans are not proof."""
    inputs = recovery["inputs"]
    if set(inputs) != {"manifest", "task", "push"}:
        raise ObservationRefusal("RECOVERY_INPUTS_MISSING")
    values = {}
    for name, reference in inputs.items():
        path = _resolve_locator(repo_root, reference["path"])
        value, actual = _source(path, repo_root)
        if actual != reference:
            raise ObservationRefusal("RECOVERY_DIGEST_MISMATCH")
        values[name] = value
    task, manifest, push = (values[k] for k in ("task", "manifest", "push"))
    task_id = recovery["task_id"]
    if (
        not task_id
        or task.get("task_id") != task_id
        or manifest.get("task_id") != task_id
        or manifest.get("owner") != task_id
    ):
        raise ObservationRefusal("RECOVERY_TASK_MISMATCH")
    carrier = task.get("task_lifecycle") or {}
    if carrier.get("lifecycle_id") != ledger["lifecycle_id"] or carrier.get("identity") != ledger["identity"]:
        raise ObservationRefusal("RECOVERY_LIFECYCLE_MISMATCH")
    preserved = task.get("preserved_artifacts") or {}
    if any(
        preserved.get(k) != manifest.get(k)
        for k in (
            "location",
            "paths",
            "content_sha256",
            "worktree_sha256",
            "task_id",
            "run_nonce",
        )
    ) or manifest.get("run_nonce") != task.get("run_nonce"):
        raise ObservationRefusal("RECOVERY_BUNDLE_MISMATCH")
    manifest_path = _resolve_locator(repo_root, inputs["manifest"]["path"])
    location = Path(manifest["location"])
    _resolve_locator(repo_root, manifest["location"])
    if location.parts[:3] != ("batch_state", "preserved", task_id):
        raise ObservationRefusal("RECOVERY_BUNDLE_MISMATCH")
    # Copies may relocate the entire evidence root; its internal layout stays canonical.
    evidence_root = manifest_path
    for _ in location.parts:
        evidence_root = evidence_root.parent
    if manifest_path != (evidence_root / location).with_suffix(".manifest.json"):
        raise ObservationRefusal("RECOVERY_BUNDLE_MISMATCH")
    try:
        ignored_task_output.verify_retrieval(evidence_root, manifest)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ObservationRefusal("RECOVERY_BUNDLE_DIGEST_MISMATCH") from exc
    worktree = task.get("worktree_path")
    branch, head, base = (task.get(k) for k in ("worktree_branch", "final_branch_head_commit", "worktree_base_sha"))
    if not isinstance(worktree, str) or "/.worktrees/dispatch/" not in worktree:
        raise ObservationRefusal("RECOVERY_WORKTREE_MISMATCH")
    if hashlib.sha256(worktree.encode()).hexdigest() != manifest.get("worktree_sha256"):
        raise ObservationRefusal("RECOVERY_WORKTREE_MISMATCH")
    if not branch or push.get("cwd") != worktree:
        raise ObservationRefusal("RECOVERY_BRANCH_MISMATCH")
    if (
        push.get("head") != head
        or push.get("remote_head") != head
        or push.get("status") != "pushed_exact_head"
        or not any(
            step.get("name") == "push" and type(step.get("exit_code")) is int and step["exit_code"] == 0
            for step in push.get("steps", [])
        )
    ):
        raise ObservationRefusal("RECOVERY_PUSH_UNPROVEN")
    proof = task.get("worktree_reap_proof") or {}
    if proof.get("pr_state") != "MERGED" or proof.get("pr_number") != ledger["pr"]["number"]:
        raise ObservationRefusal("RECOVERY_MERGED_PR_UNPROVEN")
    # The preserved merged cohort binds the branch independently of its label.
    members = proof.get("members", [])
    if not any(
        m.get("task_id") == task_id and m.get("branch") == branch and m.get("head_sha") == head for m in members
    ):
        raise ObservationRefusal("RECOVERY_BRANCH_MISMATCH")
    if not all(
        isinstance(sha, str) and len(sha) == 40 and all(c in "0123456789abcdef" for c in sha)
        for sha in (base, head, proof.get("pr_head_sha"))
    ):
        raise ObservationRefusal("RECOVERY_COMMITS_MISSING")
    try:
        tl._run_git(repo_root, ["merge-base", "--is-ancestor", base, "origin/main"])
        tl._run_git(repo_root, ["merge-base", "--is-ancestor", base, head])
        tl._run_git(repo_root, ["merge-base", "--is-ancestor", head, proof["pr_head_sha"]])
        local = tl.observe_local_git(repo_root, head_sha=head, branch=branch, worktree=None, base_sha=base)
    except tl.LifecycleError as exc:
        raise ObservationRefusal("RECOVERY_COMMIT_ANCESTRY_MISMATCH") from exc
    if not local["commits"]:
        raise ObservationRefusal("RECOVERY_COMMITS_MISSING")
    local = _local_paths(repo_root, local)
    # The hashed source still binds the original host path. Persist only its
    # dispatch suffix so moving the evidence tree does not invalidate the proof.
    relative_worktree = ".worktrees/dispatch/" + worktree.split("/.worktrees/dispatch/", 1)[1]
    _resolve_locator(repo_root, relative_worktree)
    local.update(
        dispatch_worktree_used=True,
        worktree=relative_worktree,
        worktree_present=True,
        actual_worktree_branch=branch,
        worktree_branch_matches=True,
        recovered_from_preserved=dict(recovery),
    )
    return local


def recovery_refusal(
    ledger: Mapping[str, Any],
    local: Mapping[str, Any],
    *,
    head_sha: str | None = None,
    branch: str | None = None,
) -> str | None:
    """Return a typed refusal for changed inputs, facts or merged-head ancestry."""
    try:
        recovery = local["recovered_from_preserved"]
        primary = tl.canonical_state_root(_REPOSITORY_ROOT.get() or Path.cwd())
        repo_root = _resolve_locator(primary, recovery["repo_root"])
        rebuilt = _recovered_local(repo_root, ledger, recovery)
        for key in (
            "commits",
            "changed_paths",
            "forbidden_paths",
            "branch",
            "worktree",
            "dispatch_worktree_used",
            "worktree_present",
            "worktree_branch_matches",
            "actual_worktree_branch",
        ):
            if local.get(key) != rebuilt.get(key):
                raise ObservationRefusal("RECOVERY_FACTS_MISMATCH")
        if branch is not None and branch != rebuilt["branch"]:
            raise ObservationRefusal("RECOVERY_BRANCH_MISMATCH")
        if head_sha:
            try:
                tl._run_git(repo_root, ["merge-base", "--is-ancestor", rebuilt["commits"][0]["sha"], head_sha])
            except tl.LifecycleError as exc:
                raise ObservationRefusal("RECOVERY_PR_HEAD_ANCESTRY_MISMATCH") from exc
    except ObservationRefusal as exc:
        return str(exc)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return "RECOVERY_INPUT_INVALID"
    return None


def recover(
    repo_root: Path,
    *,
    state_file: Path,
    task_file: Path,
    manifest_file: Path,
    push_file: Path,
    now: str,
) -> tuple[dict[str, Any], bool]:
    """Append one recovery receipt, returning the verified existing receipt on retry."""
    with repository_context(repo_root), tl.lifecycle_lock(state_file):
        repo_root = tl.canonical_state_root(repo_root)
        ledger = tl.load_lifecycle(state_file)
        task = _source(task_file, repo_root)[0]
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise ObservationRefusal("RECOVERY_TASK_MISMATCH")
        for receipt in ledger["observation_receipts"]:
            local = receipt.get("observation", {}).get("local", {})
            if local.get("recovered_from_preserved", {}).get("task_id") == task_id:
                refusal = recovery_refusal(ledger, local)
                if refusal:
                    raise ObservationRefusal(refusal)
                return receipt, True
        if not isinstance(task.get("worktree_path"), str):
            raise ObservationRefusal("RECOVERY_WORKTREE_MISMATCH")
        if Path(task["worktree_path"]).exists():
            raise ObservationRefusal("RECOVERY_WORKTREE_STILL_PRESENT")
        recovery = {
            "task_id": task_id,
            "repo_root": ".",
            "inputs": {
                k: _source(p, repo_root)[1]
                for k, p in (("manifest", manifest_file), ("task", task_file), ("push", push_file))
            },
        }
        try:
            local = _recovered_local(repo_root, ledger, recovery)
        except ObservationRefusal:
            raise
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise ObservationRefusal("RECOVERY_INPUT_INVALID") from exc
        for existing in reversed(ledger["observation_receipts"]):
            pr = existing.get("observation", {}).get("github", {}).get("pr") or {}
            if pr.get("state") == "MERGED":
                refusal = recovery_refusal(ledger, local, head_sha=pr.get("head_sha"), branch=pr.get("head_branch"))
                if refusal:
                    raise ObservationRefusal(refusal)
                break
        return _append(state_file, ledger, local, now)
