"""Local lifecycle capture before cleanup, and verified preserved-output recovery.

No GitHub calls or removal operations live here. The lifecycle API owns receipt
appends; the existing common reaper retains every other removal guard.
"""

from __future__ import annotations

import hashlib
import json
import re
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


def _child_association(
    task: Mapping[str, Any], ledger: Mapping[str, Any], child_pr: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind a preserved attempt to a child, without changing its earlier carrier."""
    carrier = task.get("task_lifecycle") or {}
    source = carrier.get("identity") or {}
    target = ledger["identity"]
    try:
        valid_source = carrier.get("lifecycle_id") == tl.lifecycle_id(source)
    except (tl.LifecycleError, ValueError, KeyError, TypeError):
        valid_source = False
    if (
        not valid_source
        or source.get("repository") != target["repository"]
        or source.get("stream_epic") != target["stream_epic"]
        or source.get("github_issue_number") == target["github_issue_number"]
    ):
        raise ObservationRefusal("RECOVERY_LIFECYCLE_MISMATCH")
    if not isinstance(task.get("run_nonce"), str) or not task["run_nonce"]:
        raise ObservationRefusal("RECOVERY_ASSOCIATION_INVALID")
    proof = task.get("worktree_reap_proof") or {}
    if proof.get("pr_state") != "MERGED" or proof.get("pr_number") != ledger["pr"]["number"]:
        raise ObservationRefusal("RECOVERY_MERGED_PR_UNPROVEN")
    # Exact preserved PR membership is required in addition to Git ancestry.
    if (
        child_pr.get("number") != ledger["pr"]["number"]
        or child_pr.get("url") != ledger["pr"]["url"]
        or child_pr.get("state") != "MERGED"
        or not child_pr.get("head_sha")
        or child_pr.get("head_sha") != proof.get("pr_head_sha")
        or child_pr.get("head_branch") != task.get("worktree_branch")
    ):
        raise ObservationRefusal("RECOVERY_CHILD_PR_MISMATCH")
    return {
        "schema_version": "local-recovery-association.v1",
        "task_id": task["task_id"],
        "run_nonce": task["run_nonce"],
        "source": {"lifecycle_id": carrier["lifecycle_id"], "identity": source},
        "target": {"lifecycle_id": ledger["lifecycle_id"], "identity": target},
        "child_pr": {key: child_pr[key] for key in ("number", "url", "state", "head_sha", "head_branch")},
    }


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
    association = recovery.get("association")
    if association is not None:
        expected = _child_association(task, ledger, association["child_pr"])
        if association != expected:
            raise ObservationRefusal("RECOVERY_ASSOCIATION_INVALID")
    elif carrier.get("lifecycle_id") != ledger["lifecycle_id"] or carrier.get("identity") != ledger["identity"]:
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
            association = recovery.get("association")
            if association is not None and head_sha != association["child_pr"]["head_sha"]:
                raise ObservationRefusal("RECOVERY_CHILD_PR_MISMATCH")
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
    child_pr: Mapping[str, Any] | None = None,
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
                recovery = local["recovered_from_preserved"]
                if "association" in recovery:
                    # recovery_refusal verifies the stored locators and digests.
                    # Also bind the caller's replay paths; for unchanged paths,
                    # the repeated digest checks are defence in depth.
                    for name, source in (("task", task_file), ("manifest", manifest_file), ("push", push_file)):
                        if _source(source, repo_root)[1] != recovery["inputs"][name]:
                            raise ObservationRefusal("RECOVERY_DIGEST_MISMATCH")
                    if child_pr is not None and _child_association(task, ledger, child_pr) != recovery["association"]:
                        raise ObservationRefusal("RECOVERY_ASSOCIATION_INVALID")
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
            if child_pr is not None:
                recovery["association"] = _child_association(task, ledger, child_pr)
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


def _execution_succeeded(
    row: Mapping[str, Any], *, merged_at: str, not_before: str, not_after: str | None = None,
) -> bool:
    """Success includes actual execution before merge, not a skipped check."""
    if not all(isinstance(value, str) for value in (row.get("started_at"), row.get("completed_at"), merged_at, not_before)):
        return False
    try:
        start = tl._utc_timestamp(row["started_at"])
        end = tl._utc_timestamp(row["completed_at"])
        merged = tl._utc_timestamp(merged_at)
        return (
            row.get("status") == "completed" and row.get("conclusion") == "success"
            and tl._utc_timestamp(not_before) <= start <= end <= merged
            and (not_after is None or end <= tl._utc_timestamp(not_after))
        )
    except (KeyError, TypeError, ValueError, tl.LifecycleError):
        return False


def merged_run_evidence(
    ledger: Mapping[str, Any],
    observation: dict[str, Any],
    *,
    pull: Mapping[str, Any],
    run: Mapping[str, Any],
    jobs: list[dict[str, Any]],
    now: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Derive CI receipts only from explicitly mapped, executed job steps.

    Existing typed test/CI rows map by their exact job URL and details.step_names.
    The immutable AC policy decides evidence kinds; no check can supply product,
    deployment, review, checkout history or author/reviewer attestation.
    """
    updated = tl.validate_lifecycle(ledger)
    repository = updated["identity"]["repository"]
    pr_number = updated["pr"]["number"]
    if (not isinstance(pull.get("head"), Mapping) or not isinstance(pull.get("base"), Mapping)
            or not isinstance(pull["base"].get("repo"), Mapping)):
        raise ObservationRefusal("CLOSEOUT_MERGED_PR_MISMATCH")
    head = pull["head"].get("sha")
    merge = pull.get("merge_commit_sha")
    merged_at = pull.get("merged_at")
    base_ref = pull.get("base", {}).get("ref")
    pr_url = f"https://github.com/{repository}/pull/{pr_number}"
    observed_pr = observation.get("github", {}).get("pr", {})
    if (
        pull.get("number") != pr_number or pull.get("html_url") != pr_url
        or pull.get("base", {}).get("repo", {}).get("full_name") != repository
        or pull.get("state") != "closed" or pull.get("merged") is not True
        or not isinstance(merged_at, str) or not isinstance(base_ref, str) or not base_ref
        or not all(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha) for sha in (head, merge))
        or observed_pr.get("number") != pr_number or observed_pr.get("url") != pr_url
        or observed_pr.get("state") != "MERGED" or observed_pr.get("head_sha") != head
        or observed_pr.get("merge_sha") != merge
    ):
        raise ObservationRefusal("CLOSEOUT_MERGED_PR_MISMATCH")
    run_id, attempt = run.get("id"), run.get("run_attempt")
    run_url = f"https://github.com/{repository}/actions/runs/{run_id}"
    if (
        type(run_id) is not int or type(attempt) is not int or min(run_id, attempt) < 1
        or not isinstance(run.get("repository"), Mapping) or run["repository"].get("full_name") != repository
        or run.get("event") != "merge_group" or run.get("head_sha") != merge
        or run.get("html_url") != run_url or run.get("path") != ".github/workflows/ci.yml"
        or not re.fullmatch(rf"gh-readonly-queue/{re.escape(base_ref)}/pr-{pr_number}-[0-9a-f]+", str(run.get("head_branch", "")))
        or run.get("status") != "completed" or run.get("conclusion") != "success"
    ):
        raise ObservationRefusal("CLOSEOUT_MERGE_RUN_MISMATCH")
    try:
        if (not all(isinstance(run.get(key), str) for key in ("created_at", "run_started_at"))
                or not isinstance(pull.get("created_at"), str)
                or not tl._utc_timestamp(pull["created_at"]) <= tl._utc_timestamp(run["created_at"]) <= tl._utc_timestamp(run["run_started_at"]) <= tl._utc_timestamp(merged_at)):
            raise ObservationRefusal("CLOSEOUT_MERGE_RUN_STALE")
    except (KeyError, TypeError, ValueError, tl.LifecycleError) as exc:
        raise ObservationRefusal("CLOSEOUT_MERGE_RUN_STALE") from exc
    if not jobs or len({job.get("id") for job in jobs}) != len(jobs):
        raise ObservationRefusal("CLOSEOUT_JOBS_INCOMPLETE")
    for job in jobs:
        job_id = job.get("id")
        if (
            type(job_id) is not int or job_id < 1 or job.get("run_id") != run_id
            or type(job.get("run_attempt")) is not int or job.get("run_attempt") != attempt or job.get("head_sha") != merge
            or job.get("html_url") != f"{run_url}/job/{job_id}"
        ):
            raise ObservationRefusal("CLOSEOUT_JOB_RUN_MISMATCH")
    for name in updated["required_checks"]:
        required = [job for job in jobs if job.get("name") == name]
        if not required or not all(_execution_succeeded(job, merged_at=merged_at, not_before=run["run_started_at"]) for job in required):
            raise ObservationRefusal("CLOSEOUT_REQUIRED_CHECK_NOT_EXECUTED")

    execution = {
        "pull": {
            **{key: pull.get(key) for key in (
                "number", "html_url", "state", "merged", "merge_commit_sha", "merged_at", "created_at",
            )},
            "head": {"sha": head}, "base": {"ref": base_ref, "repo": {"full_name": repository}},
        },
        "run": {**{key: run.get(key) for key in (
            "id", "run_attempt", "event", "head_sha", "head_branch", "path", "html_url",
            "created_at", "run_started_at", "status", "conclusion",
        )}, "repository": {"full_name": repository}},
        "jobs": [{key: job.get(key) for key in (
            "id", "run_id", "run_attempt", "head_sha", "html_url", "name", "status", "conclusion",
            "started_at", "completed_at", "steps",
        )} for job in jobs],
    }
    github = observation["github"]
    # Preserve the branch-head rollup while evaluating the verified merged run.
    github["pr"]["branch_checks"] = github["pr"].get("checks", [])
    github["pr"]["checks"] = [{
        "name": job.get("name"), "status": str(job.get("status", "")).upper(),
        "conclusion": str(job.get("conclusion", "")).upper(), "url": job["html_url"],
    } for job in jobs]
    status = tl._evidence_status(
        updated, head_sha=head,
        comment_urls={comment["url"] for comment in github.get("comments", []) if comment.get("url")},
    )
    valid_ids = status["valid_evidence_ids"]
    mapped: dict[str, list[dict[str, Any]]] = {}
    valid: dict[str, set[str]] = {}
    for record in updated["evidence"]:
        if record["id"] not in valid_ids:
            continue
        kind = record["type"]
        if kind in {"test", "ci"}:
            names = record["details"].get("step_names")
            matching = [job for job in jobs if job["html_url"] == record["url"]]
            if (not isinstance(names, list) or not names or not all(isinstance(name, str) and name for name in names)
                    or len(matching) != 1 or not _execution_succeeded(matching[0], merged_at=merged_at, not_before=run["run_started_at"])):
                continue
            job = matching[0]
            steps = job.get("steps")
            if not isinstance(steps, list) or not all(isinstance(step, dict) for step in steps):
                continue
            if not all(
                len(found := [step for step in steps if step.get("name") == name]) == 1
                and _execution_succeeded(found[0], merged_at=merged_at, not_before=job["started_at"], not_after=job["completed_at"])
                for name in names
            ):
                continue
            mapped.setdefault(record["ac_id"], []).append({
                "evidence_id": record["id"], "type": kind, "job_id": job["id"], "check": job["name"],
                "step_names": names, "url": job["html_url"],
            })
        valid.setdefault(record["ac_id"], set()).add(kind)

    criteria = []
    for criterion in updated["ac_snapshot"]["criteria"]:
        if not criterion["applicable"] or tl.STATE_RANK[criterion["due_state"]] > tl.STATE_RANK["CLEANED_UP"]:
            continue
        ac_id = criterion["id"]
        executed = mapped.get(ac_id, [])
        # An existing criterion-specific test mapping may supply CI execution,
        # but can never supply another required evidence kind.
        if executed and "ci" in criterion["required_evidence"] and "ci" not in valid.get(ac_id, set()):
            source = executed[0]
            updated, evidence = tl.add_evidence(
                updated, ac_id=ac_id, evidence_type="ci", summary="Exact merged-run execution of mapped criterion steps",
                url=source["url"], commit=head, recorded_at=now,
                details={"step_names": source["step_names"], "source_evidence_id": source["evidence_id"],
                         "run_id": run_id, "run_attempt": attempt, "merge_sha": merge,
                         "execution_sha256": tl.digest(execution)},
            )
            valid.setdefault(ac_id, set()).add("ci")
            executed.append({**source, "type": "ci", "evidence_id": evidence["id"]})
        missing = sorted(set(criterion["required_evidence"]) - valid.get(ac_id, set()))
        criteria.append({"ac_id": ac_id, "passed": not missing, "missing": missing, "executed": executed})
    evaluation = tl.evaluate(updated, observation)
    cleanup = observation["local"]
    cleanup_residual = any(cleanup.get(key, True) for key in (
        "worktree_present", "local_branch_present", "remote_branch_present",
    ))
    report = {
        "observed_at": observation["observed_at"],
        "repository": repository, "issue": updated["identity"]["github_issue_number"], "pr": pr_number,
        "head_sha": head, "merge_sha": merge, "run_id": run_id, "run_attempt": attempt, "run_url": run_url,
        "execution_sha256": tl.digest(execution), "execution": execution, "criteria": criteria,
        "criteria_passed": bool(criteria) and all(item["passed"] for item in criteria),
        "cleanup_residual": cleanup_residual, "blockers": evaluation["hard_blockers"],
    }
    checked = {item["id"] for item in tl.parse_issue_acceptance_criteria(github.get("issue", {}).get("body", ""))
               if item["checked"]}
    report["unchecked_criteria"] = [item["ac_id"] for item in criteria if item["ac_id"] not in checked]
    report["closure_ready"] = (
        report["criteria_passed"] and not cleanup_residual and evaluation["goal_reached"]
        and not evaluation["hard_blockers"] and not report["unchecked_criteria"]
    )
    github["closeout_run"] = report
    if not report["criteria_passed"]:
        github["error"] = "CLOSEOUT_CRITERION_EXECUTION_OR_PROOF_MISSING"
    return updated, report


def validated_merged_criteria(ledger: Mapping[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
    """Recompute closure proof instead of trusting copied receipt status flags."""
    from copy import deepcopy

    try:
        report = observation["github"]["closeout_run"]
        execution = report["execution"]
        if (report["observed_at"] != observation["observed_at"]
                or report["execution_sha256"] != tl.digest(execution)):
            raise ObservationRefusal("CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED")
        _, verified = merged_run_evidence(
            ledger, deepcopy(observation), pull=execution["pull"], run=execution["run"],
            jobs=execution["jobs"], now=observation["observed_at"],
        )
        for key in ("repository", "issue", "pr", "head_sha", "merge_sha", "run_id", "run_attempt", "run_url"):
            if type(report[key]) is not type(verified[key]) or report[key] != verified[key]:
                raise ObservationRefusal("CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED")
        return verified
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ObservationRefusal("CLOSEOUT_RECEIPT_MISSING_OR_INVALID") from exc
