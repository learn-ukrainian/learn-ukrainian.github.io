"""Fail-closed, resumable cleanup executor for one task-family branch cleanup."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.orchestration.task_family import codex_state
from scripts.orchestration.task_family import git_safety as safety

CLEANUP_STAGES = (
    "planned",
    "frozen",
    "verified",
    "snapshotted",
    "tasks_archived",
    "worktrees_removed",
    "branches_deleted",
    "runtime_retired",
    "completed",
)


class ExecutorError(RuntimeError):
    """Cleanup execution blocked by safety guard or data mismatch."""


class ExecutionStateError(ExecutorError):
    """Corrupted or unknown executor state payload."""


@dataclass(frozen=True)
class CleanupPlan:
    task_id: int
    family: str
    lineage_id: str
    title: str
    cwd: str
    branch: str
    worktree: Path
    thread_id: int
    db_path: Path
    host: str | None = None
    explicit_protected: frozenset[str] = frozenset()


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def state_path(repo_root: Path, plan: CleanupPlan) -> Path:
    return (
        safety.resolve_state_root(repo_root)
        / "states"
        / plan.family
        / plan.lineage_id
        / f"{plan.task_id}.json"
    )


def _default_state(plan: CleanupPlan) -> dict[str, Any]:
    return {
        "task_id": plan.task_id,
        "family": plan.family,
        "lineage_id": plan.lineage_id,
        "state": "planned",
        "resume_stage": None,
        "updated_at": _iso_now(),
        "stages": {},
        "blocked": None,
        "history": ["planned"],
    }


def _serializable_receipt(payload: Any) -> Any:
    if isinstance(payload, Path):
        return str(payload)
    if isinstance(payload, safety.BundleReceipt):
        return {
            "path": str(payload.path),
            "sha256": payload.sha256,
            "branch": payload.branch,
            "created_at": payload.created_at,
        }
    if isinstance(payload, set):
        return sorted(payload)
    if isinstance(payload, tuple):
        return list(payload)
    return payload


def load_state(repo_root: Path, plan: CleanupPlan) -> dict[str, Any]:
    path = state_path(repo_root, plan)
    if not path.exists():
        return _default_state(plan)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExecutionStateError(f"state file {path} is invalid JSON") from exc
    if not isinstance(raw, dict):
        raise ExecutionStateError(f"state file {path} must be an object")
    return raw


def persist_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{path.stat().st_mtime_ns if path.exists() else 'new'}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _record(payload: dict[str, Any], stage: str, key: str, value: Any) -> None:
    recorded = dict(payload.setdefault("stages", {}).get(stage, {}))
    recorded[key] = _serializable_receipt(value)
    payload.setdefault("stages", {})[stage] = recorded


def _update_state(path: Path, payload: dict[str, Any], *, next_state: str) -> dict[str, Any]:
    payload["state"] = next_state
    payload["resume_stage"] = None
    payload["blocked"] = None
    history = payload.get("history")
    if not isinstance(history, list):
        history = []
        payload["history"] = history
    if not history or history[-1] != next_state:
        history.append(next_state)
    payload["updated_at"] = _iso_now()
    persist_state(path, payload)
    return payload


def _set_blocked(
    path: Path,
    payload: dict[str, Any],
    *,
    stage: str,
    error: str,
) -> dict[str, Any]:
    payload["state"] = "blocked"
    payload["resume_stage"] = stage
    payload["blocked"] = {
        "stage": stage,
        "reason": error,
        "updated_at": _iso_now(),
    }
    payload["updated_at"] = _iso_now()
    persist_state(path, payload)
    return payload


def _extract_simulated_crash_stage(error: str) -> str | None:
    marker = "simulated crash after "
    if not error.startswith(marker):
        return None
    return error[len(marker) :].strip() or None


def _next_stage(stage: str) -> str:
    return {
        "planned": "frozen",
        "frozen": "verified",
        "verified": "snapshotted",
        "snapshotted": "tasks_archived",
        "tasks_archived": "worktrees_removed",
        "worktrees_removed": "branches_deleted",
        "branches_deleted": "runtime_retired",
        "runtime_retired": "completed",
        "completed": "completed",
    }.get(stage, stage)


def _validate_stage(stage: str) -> None:
    if stage not in CLEANUP_STAGES:
        raise ExecutionStateError(f"unknown stage: {stage!r}")


def _starting_stage(payload: dict[str, Any]) -> str:
    state = payload.get("state", "planned")
    if state == "blocked":
        resume = str(payload.get("resume_stage") or "planned")
        _validate_stage(resume)
        return resume
    if state == "completed":
        return "completed"
    if state in CLEANUP_STAGES:
        return state
    raise ExecutionStateError(f"unknown state: {state!r}")


def _assert_no_unknowns(plan: CleanupPlan) -> None:
    if not plan.title:
        raise ExecutorError("plan.title is required")
    if not plan.cwd:
        raise ExecutorError("plan.cwd is required")
    if not plan.branch:
        raise ExecutorError("plan.branch is required")


def _bundle_from_payload(raw: dict[str, Any]) -> safety.BundleReceipt:
    path = Path(str(raw.get("path")))
    return safety.BundleReceipt(
        path=path,
        sha256=str(raw.get("sha256", "")),
        branch=str(raw.get("branch", "")),
        created_at=str(raw.get("created_at", "")),
    )


def _local_branch_exists(repo_root: Path, branch: str) -> bool:
    return (
        safety.run_git(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=repo_root).returncode
        == 0
    )


class CleanupExecutor:
    """Run and persist one cleanup sequence for a single task-family job."""

    def __init__(self, repo_root: Path, plan: CleanupPlan, *, crash_after_stage: str | None = None) -> None:
        self.repo_root = repo_root
        self.plan = plan
        self.crash_after_stage = crash_after_stage

    @property
    def state_file(self) -> Path:
        return state_path(self.repo_root, self.plan)

    def _maybe_crash(self, stage: str) -> None:
        if self.crash_after_stage == stage:
            raise RuntimeError(f"simulated crash after {stage}")

    @staticmethod
    def _has_stage_evidence(payload: dict[str, Any], stage: str) -> bool:
        staged = payload.get("stages")
        if not isinstance(staged, dict):
            return False
        value = staged.get(stage)
        if not (isinstance(value, dict) and bool(value)):
            return False
        return value.keys() != {"cwd"}

    def _restore_blocked_stage(self, payload: dict[str, Any], stage: str) -> dict[str, Any]:
        history = payload.get("history")
        if not isinstance(history, list):
            history = []
            payload["history"] = history

        if self._has_stage_evidence(payload, stage) and stage not in history:
            payload = _update_state(self.state_file, payload, next_state=stage)
            self._record_cwd(payload, stage)
        return payload

    def run(self) -> dict[str, Any]:
        _assert_no_unknowns(self.plan)
        with (
            safety.operation_lock(self.repo_root),
            safety.lineage_lock(self.repo_root, self.plan.lineage_id),
            safety.family_lock(self.repo_root, self.plan.family),
            safety.worktree_lock(self.repo_root, self.plan.worktree),
        ):
            return self._run_locked()

    def _run_locked(self) -> dict[str, Any]:
        payload = load_state(self.repo_root, self.plan)
        stage = _starting_stage(payload)
        if stage == "completed":
            return payload
        if payload.get("state") == "blocked":
            stage = _starting_stage(payload)
            payload = self._restore_blocked_stage(payload, stage)
            stage = _starting_stage(payload)

        try:
            while stage != "completed":
                _validate_stage(stage)
                next_stage = self._advance_once(payload, stage)
                if next_stage == stage:
                    raise ExecutorError(f"transition for {stage!r} did not advance")
                payload = _update_state(self.state_file, payload, next_state=next_stage)
                self._record_cwd(payload, next_stage)
                stage = next_stage
            return payload
        except (ExecutorError, RuntimeError) as exc:
            blocked_stage = _extract_simulated_crash_stage(str(exc)) or stage
            return _set_blocked(self.state_file, payload, stage=blocked_stage, error=str(exc))

    def _advance_once(self, payload: dict[str, Any], stage: str) -> str:
        if stage == "planned":
            return self._to_frozen(payload)
        if stage == "frozen":
            return self._to_verified(payload)
        if stage == "verified":
            return self._to_snapshotted(payload)
        if stage == "snapshotted":
            return self._to_tasks_archived(payload)
        if stage == "tasks_archived":
            return self._to_worktrees_removed(payload)
        if stage == "worktrees_removed":
            return self._to_branches_deleted(payload)
        if stage == "branches_deleted":
            return self._to_runtime_retired(payload)
        if stage == "runtime_retired":
            return self._to_completed(payload)
        if stage == "completed":
            return "completed"
        raise ExecutionStateError(f"invalid stage transition request: {stage!r}")

    def _record_cwd(self, payload: dict[str, Any], stage: str) -> None:
        _record(payload, stage, "cwd", str(Path(self.plan.cwd).resolve()))

    def _verify_frozen_once(self) -> None:
        safety.verify_frozen_preconditions(
            self.repo_root,
            lineage_id=self.plan.lineage_id,
            family=self.plan.family,
            worktree=self.plan.worktree,
        )

    def _to_frozen(self, payload: dict[str, Any]) -> str:
        self._verify_frozen_once()
        frozen_stage = payload.get("stages", {}).get("frozen", {}) if isinstance(payload.get("stages"), dict) else {}
        if isinstance(frozen_stage, dict) and frozen_stage.get("worktree") == str(self.plan.worktree):
            self._maybe_crash("frozen")
            return "verified"
        if isinstance(frozen_stage, dict) and frozen_stage:
            raise ExecutorError(
                f"frozen evidence conflict for worktree: {frozen_stage.get('worktree')!r}"
            )
        _record(payload, "frozen", "worktree", str(self.plan.worktree))
        self._maybe_crash("frozen")
        return "frozen"

    def _to_verified(self, payload: dict[str, Any]) -> str:
        self._verify_frozen_once()
        verified_stage = payload.get("stages", {}).get("verified", {}) if isinstance(payload.get("stages"), dict) else {}
        if isinstance(verified_stage, dict) and verified_stage:
            self._maybe_crash("verified")
            return "snapshotted"
        if not self.plan.worktree.exists():
            raise ExecutorError(f"worktree missing: {self.plan.worktree}")
        planned_cwd = str(Path(self.plan.cwd).resolve())
        if str(self.plan.worktree.resolve()) != planned_cwd:
            raise ExecutorError(
                f"worktree path mismatch for task {self.plan.task_id}: {self.plan.worktree} != {planned_cwd}"
            )

        safety.assert_no_unknown_branch_mutation(
            self.repo_root,
            self.plan.branch,
            explicit_protected=self.plan.explicit_protected,
        )
        safety.assert_primary_checkout(self.repo_root)
        base_branch = safety.repo_default_branch(self.repo_root)
        safety.ensure_clean_base(self.repo_root, base_branch)
        safety.verify_worktree_candidate(self.repo_root, worktree=self.plan.worktree, branch=self.plan.branch)
        head = safety.worktree_head(self.repo_root, self.plan.worktree)
        if head is None:
            raise ExecutorError(f"worktree has no HEAD: {self.plan.worktree}")
        pr = safety.query_pr_by_head(self.repo_root, branch=self.plan.branch)
        safety.assert_pr_is_merged(pr)
        _record(payload, "verified", "base_branch", base_branch)
        _record(payload, "verified", "worktree_head", head)
        _record(payload, "verified", "pr", pr)
        self._maybe_crash("verified")
        return "verified"

    def _to_snapshotted(self, payload: dict[str, Any]) -> str:
        self._verify_frozen_once()
        recorded = payload.get("stages", {}).get("snapshotted", {}).get("bundle")
        if isinstance(recorded, dict):
            try:
                receipt = _bundle_from_payload(recorded)
                safety.assert_bundle_matches_receipt(receipt, branch=self.plan.branch)
                safety.verify_bundle(receipt.path, branch=self.plan.branch, repo_root=self.repo_root)
                _record(payload, "snapshotted", "bundle", receipt)
                self._maybe_crash("snapshotted")
                return "tasks_archived"
            except Exception:
                pass

        bundle = safety.build_bundle(
            self.repo_root,
            branch=self.plan.branch,
            bundle_dir=safety.resolve_state_root(self.repo_root) / "bundles",
        )
        _record(payload, "snapshotted", "bundle", bundle)
        self._maybe_crash("snapshotted")
        return "snapshotted"

    def _to_tasks_archived(self, payload: dict[str, Any]) -> str:
        self._verify_frozen_once()

        existing = payload.get("stages", {}).get("tasks_archived", {})
        if isinstance(existing, dict) and existing:
            return _next_stage("tasks_archived")

        before, after, changed = codex_state.reconcile_task_thread(
            task_id=self.plan.task_id,
            action="archive",
            expected_title=self.plan.title,
            expected_cwd=self.plan.cwd,
            expected_host=self.plan.host,
            db_path=self.plan.db_path,
        )
        _record(
            payload,
            "tasks_archived",
            "reconcile",
            codex_state.build_reconciliation_payload(before, after, changed, action="archive"),
        )
        self._maybe_crash("tasks_archived")
        return "tasks_archived"

    def _to_worktrees_removed(self, payload: dict[str, Any]) -> str:
        self._verify_frozen_once()

        if self.plan.worktree.exists():
            safety.verify_worktree_candidate(self.repo_root, worktree=self.plan.worktree, branch=self.plan.branch)
            safety.remove_worktree(self.repo_root, self.plan.worktree)
            if self.plan.worktree.exists():
                raise ExecutorError(f"worktree still present after remove: {self.plan.worktree}")
        else:
            if safety.is_worktree_registered(self.repo_root, self.plan.worktree):
                raise ExecutorError(f"worktree path missing but still registered: {self.plan.worktree}")

            if self._has_stage_evidence(payload, "worktrees_removed"):
                return _next_stage("worktrees_removed")
            _record(payload, "worktrees_removed", "removed", True)
        _record(payload, "worktrees_removed", "worktree", str(self.plan.worktree))
        self._maybe_crash("worktrees_removed")
        return "worktrees_removed"

    def _bundle_receipt(self, payload: dict[str, Any]) -> safety.BundleReceipt:
        snap = payload.get("stages", {}).get("snapshotted", {}).get("bundle")
        if not isinstance(snap, dict):
            raise ExecutorError("snapshot evidence missing")
        return _bundle_from_payload(snap)

    def _to_branches_deleted(self, payload: dict[str, Any]) -> str:
        self._verify_frozen_once()

        if not _local_branch_exists(self.repo_root, self.plan.branch):
            if safety.remote_branch_present(self.repo_root, self.plan.branch):
                raise ExecutorError(f"remote branch still present: {self.plan.branch}")
            if not safety.is_worktree_registered(self.repo_root, self.plan.worktree):
                _record(payload, "branches_deleted", "local_ref_present_after", False)
                _record(payload, "branches_deleted", "remote_present", False)
                return "branches_deleted"
            raise ExecutorError(f"branch local head removed but worktree still registered: {self.plan.worktree}")

        verified_payload = payload.get("stages", {}).get("verified", {}) if isinstance(payload.get("stages"), dict) else {}
        pr = verified_payload.get("pr") if isinstance(verified_payload, dict) else None
        if not isinstance(pr, dict):
            pr = safety.query_pr_by_head(self.repo_root, branch=self.plan.branch)

        bundle = self._bundle_receipt(payload)
        safety.verify_bundle(bundle.path, branch=self.plan.branch, repo_root=self.repo_root)
        base_branch = safety.repo_default_branch(self.repo_root)
        safety.assert_primary_checkout(self.repo_root)
        safety.ensure_clean_base(self.repo_root, base_branch)
        merge_commit = safety.assert_branch_deletion_preconditions(
            repo_root=self.repo_root,
            branch=self.plan.branch,
            pr_data=pr,
            bundle=bundle,
            explicit_protected=self.plan.explicit_protected,
            require_remote_gone=True,
            worktree_registered=safety.is_worktree_registered(self.repo_root, self.plan.worktree),
        )
        safety.delete_branch(self.repo_root, branch=self.plan.branch, require_force=True)
        if _local_branch_exists(self.repo_root, self.plan.branch):
            raise ExecutorError(f"branch still present after delete attempt: {self.plan.branch}")
        _record(payload, "branches_deleted", "merge_commit", merge_commit)
        _record(payload, "branches_deleted", "bundle", bundle)
        _record(payload, "branches_deleted", "local_ref_present_after", False)
        self._maybe_crash("branches_deleted")
        return "branches_deleted"

    def _to_runtime_retired(self, payload: dict[str, Any]) -> str:
        self._verify_frozen_once()
        if self._has_stage_evidence(payload, "runtime_retired"):
            return _next_stage("runtime_retired")
        bundle = self._bundle_receipt(payload)
        safety.assert_bundle_matches_receipt(bundle, branch=self.plan.branch)
        safety.verify_bundle(bundle.path, branch=self.plan.branch, repo_root=self.repo_root)
        _record(payload, "runtime_retired", "bundle", bundle)
        _record(payload, "runtime_retired", "retained", True)
        self._maybe_crash("runtime_retired")
        return "runtime_retired"

    def _to_completed(self, payload: dict[str, Any]) -> str:
        _record(payload, "completed", "state", "ok")
        return "completed"

    def restore_archive(self) -> dict[str, Any]:
        payload = load_state(self.repo_root, self.plan)
        state = _starting_stage(payload)
        if state in {"runtime_retired", "branches_deleted", "worktrees_removed", "completed"}:
            raise ExecutorError("restore only supported before destructive branch cleanup")
        before, after, changed = codex_state.reconcile_task_thread(
            task_id=self.plan.task_id,
            action="restore",
            expected_title=self.plan.title,
            expected_cwd=self.plan.cwd,
            expected_host=self.plan.host,
            db_path=self.plan.db_path,
        )
        _record(
            payload,
            "tasks_archived",
            "restore",
            codex_state.build_reconciliation_payload(before, after, changed, action="restore"),
        )
        return _update_state(self.state_file, payload, next_state="verified")
