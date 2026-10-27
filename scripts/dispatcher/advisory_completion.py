"""Measured bounded completion, ported from delegate.py:7413,7769,7882,8070."""

import shutil
import subprocess
from pathlib import Path

from scripts.agent_runtime import bounded_advisory as contract
from scripts.common.git_context import sanitized_git_env
from scripts.common.task_scratch import TaskScratchError, allocate


def _git(worktree: Path, args, *, env=None):
    return subprocess.run(["git", *args], cwd=worktree, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=False, timeout=60,
                          env=env if env is not None else sanitized_git_env(strip_config_injection=True))


def _worktree_diff_read(worktree: Path, diff_args) -> tuple[str | None, str | None]:
    """Legacy scratch-index measurement includes untracked files, without touching the real index."""
    env = sanitized_git_env(strip_config_injection=True)
    code = "temp_index_failed"
    scratch = None
    try:
        index_proc = _git(worktree, ["rev-parse", "--path-format=absolute", "--git-path", "index"], env=env)
        if index_proc.returncode != 0:
            return None, f"{code} (return code {index_proc.returncode})"
        scratch = allocate("advisory-diff")
        scratch_index = scratch.payload_dir / "index"
        real_index = Path(index_proc.stdout.strip())
        if real_index.is_file():
            shutil.copyfile(real_index, scratch_index)
        scratch_env = {**env, "GIT_INDEX_FILE": str(scratch_index)}
        add_proc = _git(worktree, ["add", "-A", "--intent-to-add"], env=scratch_env)
        if add_proc.returncode != 0:
            return None, f"{code} (return code {add_proc.returncode})"
        code = "diff_command_failed"
        diff_proc = _git(worktree, ["diff", *diff_args], env=scratch_env)
    except (OSError, subprocess.TimeoutExpired, TaskScratchError) as exc:
        return None, f"{code} ({type(exc).__name__})"
    finally:
        if scratch is not None:
            try:
                scratch.remove()
            finally:
                scratch.preserve()
    if diff_proc.returncode != 0:
        return None, f"{code} (return code {diff_proc.returncode})"
    return diff_proc.stdout, None


def worker_diff(record: dict, diff_args, *, committed_only=False) -> tuple[str | None, str | None]:
    worktree = Path(record["worktree_path"])
    if not worktree.is_dir():
        return None, "no worktree to measure"
    merge_base = None
    try:
        # V2 --cwd attaches at the recorded SHA; a fresh checkout uses the base merge point.
        admitted = record.get("driver_brief") or record.get("advisory_envelope") or {}
        args = admitted.get("advisory_args") or {}
        if args.get("cwd"):
            merge_base = record["worktree_base_sha"]
            proc = _git(worktree, ["rev-parse", "--verify", f"{merge_base}^{{commit}}"])
            if proc.returncode:
                return None, f"round-start head {merge_base} is missing"
        else:
            for ref in (record.get("worktree_base_ref") or "origin/main", record.get("worktree_base_sha"),
                        "refs/remotes/origin/main", "refs/heads/main"):
                if not ref:
                    continue
                proc = _git(worktree, ["merge-base", "HEAD", ref])
                if proc.returncode == 0 and proc.stdout.strip():
                    merge_base = proc.stdout.strip()
                    break
            if not merge_base:
                return None, "merge-base with the base branch is unknown"
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"round-start head could not be read ({type(exc).__name__})"
    error = "the worker's diff could not be read"
    for _attempt in range(2):
        if committed_only:
            try:
                proc = _git(worktree, ["diff", *diff_args, merge_base, "HEAD", "--"])
            except (OSError, subprocess.TimeoutExpired) as exc:
                error = f"the worker's committed diff could not be read ({type(exc).__name__})"
            else:
                if proc.returncode == 0:
                    return proc.stdout, None
                error = f"the worker's committed diff could not be read (return code {proc.returncode})"
        else:
            output, why = _worktree_diff_read(worktree, [*diff_args, merge_base, "--"])
            if output is not None:
                return output, None
            error = f"the worker's diff could not be read ({why})" if why else error
    return None, error


def ceiling_check(record: dict) -> dict:
    envelope = record["advisory_envelope"]
    try:
        max_files, max_loc = int(envelope["max_changed_files"]), int(envelope["max_non_test_loc"])
    except (KeyError, TypeError, ValueError):
        return {"measured": False, "error": "the task record's envelope has no ceilings"}
    numstat, error = worker_diff(record, ["--numstat", "-z", "--no-renames"])
    if numstat is None:
        return {"measured": False, "error": error}
    try:
        entries = contract.parse_numstat_z(numstat)
    except ValueError as exc:
        return {"measured": False, "error": str(exc)}
    return contract.ceiling_verdict(entries, max_changed_files=max_files, max_non_test_loc=max_loc)


def exempt_check(record: dict) -> dict:
    from scripts.fleet.regenerable_output import is_disposable_auto_finalize_path

    names, error = worker_diff(record, ["--name-only", "-z", "--no-renames"])
    committed, committed_error = worker_diff(record, ["--name-only", "-z", "--no-renames"], committed_only=True)
    if names is None or committed is None:
        return {"measured": False, "error": error or committed_error}
    committed_paths = {name for name in committed.split("\0") if name}
    all_paths = {name for name in names.split("\0") if name} | committed_paths
    residue = sorted(path for path in all_paths if path not in committed_paths and is_disposable_auto_finalize_path(path))
    changed = sorted(all_paths - set(residue))
    try:
        problems = contract.exempt_change_problems(changed, Path(record["worktree_path"]))
    except RuntimeError as exc:
        return {"measured": False, "error": str(exc)}
    return {"measured": True, "changed_paths": changed, "ignored_residue": residue, "problems": problems}


def settle(record: dict) -> None:
    """Fail closed before any successful terminal record is persisted."""
    if record["mode"] != "workspace-write" or record["status"] != "done":
        return
    if isinstance(record.get("advisory_envelope"), dict):
        key, check = "advisory_ceiling_check", ceiling_check(record)
        failure = (contract.CEILING_UNMEASURED if not check.get("measured")
                   else contract.CEILING_EXCEEDED if check.get("exceeded") else None)
        detail = "; ".join(check.get("exceeded") or []) or str(check.get("error") or "unmeasured")
    elif isinstance(record.get("advisory_exemption"), dict):
        key, check = "advisory_exempt_change_check", exempt_check(record)
        failure = (contract.EXEMPT_CHANGES_UNMEASURED if not check.get("measured")
                   else contract.EXEMPT_CODE_CHANGE if check.get("problems") else None)
        detail = "; ".join(check.get("problems") or []) or str(check.get("error") or "unmeasured")
    else:
        return
    record[key] = check
    if failure:
        message = f"{failure}: {detail}"
        record.update(status="failed", failure_reason=failure, last_error=message, error=message)
