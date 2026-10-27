"""Detached supervision, client waits and process-group cancellation."""

import contextlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from scripts.common.repo_root import project_interpreter
from scripts.common.scratch import ensure_scratch_root
from scripts.common.task_scratch import TaskScratchError
from scripts.dispatcher import admission, git, providers, store
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.types import TaskSpec
from scripts.dispatcher.watchdog import DeadlineExpired, communicate, deadlines, liveness_paths


def _identity(pid: int | None) -> str | None:
    if not pid:
        return None
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        return None if fields[0] == "Z" else f"{boot}:{fields[19]}"
    except (OSError, IndexError):
        return None


def _observe(record: dict) -> dict:
    if (
        record.get("schema_version") == 2
        and record["status"] in store.ACTIVE
        and record.get("pid")
        and _identity(record["pid"]) != record.get("process_start")
    ):
        current = store.read(record["task_id"], record["run_nonce"])
        if current["status"] not in store.ACTIVE:
            return current
        record.update(status="crashed", finished_at=store.now(), error="supervisor exited without a result")
        record["duration_s"] = (
            datetime.fromisoformat(record["finished_at"]) - datetime.fromisoformat(record["started_at"])
        ).total_seconds()
        record.update(git.snapshot_delivery(_spec(record, {}), record))
        store.replace(record)
    return record


def start(spec: TaskSpec, record: dict, prompt: bytes, hard_timeout: float) -> None:
    if spec.agent == "cursor":
        record.update(resolved_model="unknown", resolved_model_known=False, resolved_model_source="pending")
    path = store.create(record, prompt)
    logs = path.parent / "logs"
    logs.mkdir(exist_ok=True, mode=0o700)
    try:
        with open(logs / f"{spec.task_id}.stderr.log", "ab", opener=lambda p, f: os.open(p, f, 0o600)) as err:
            mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM, signal.SIGINT})
            try:
                process, launch = admission.spawn_supervisor(
                    [str(project_interpreter()), "-m", "scripts.dispatcher.worker", str(path)],
                    task_id=spec.task_id, run_nonce=record["run_nonce"], cwd=Path(__file__).resolve().parents[2],
                    stderr=err, stderr_log=logs / f"{spec.task_id}.stderr.log",
                )
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, mask)
        record.update(pid=process.pid, process_start=_identity(process.pid), **launch)
        store.replace(record, path)
        payload = json.dumps({"options": spec.options, "hard_timeout": hard_timeout}).encode()
        process.stdin.write(payload)
        process.stdin.close()
    except admission.LaunchRefused as exc:
        record.update(exc.fields, finished_at=store.now())
        store.replace(record, path)
        raise
    except Exception:
        record.update(status="crashed", finished_at=store.now(), error="supervisor launch failed")
        store.replace(record, path)
        raise


class _Cancelled(Exception):
    pass


def _spec(record: dict, options: dict) -> TaskSpec:
    return TaskSpec(
        record["task_id"],
        record["agent"],
        record["model"],
        record["effort"],
        record["mode"],
        Path(record["worktree_path"]),
        Path(record["prompt_file"]),
        Path(record["result_file"]),
        record["claude_account"],
        record["provider"],
        {**record.get("options", {}), **options},
    )


def _enforce_delivery(record: dict) -> None:
    if record["mode"] == "read-only" or record["status"] != "done":
        return
    cause = None
    if owned := record.get("owned_paths"):
        from scripts.guardrails.delegate_ownership import path_is_owned, sanitize_for_display
        from scripts.secret_redactor import redact_text

        try:
            with git.ownership_git(record) as run:
                base_sha = run("rev-parse", "--verify", "refs/heads/base^{commit}")
                merge_base = run("merge-base", record["head_sha"], base_sha)
                revision_range = (record["head_sha"], "--not", merge_base, record["worktree_base_sha"])
                if (record["commits_ahead"] or 0) > 0 and not run("rev-list", "--max-count=1", *revision_range):
                    raise ValueError("empty ownership range with recorded commits ahead")
                version = tuple(int(part) for part in run("version").split()[2].split(".")[:2])
                remerge = version >= (2, 36)
                # Remerge diffs isolate edits made during a merge from clean upstream changes.
                # Older Git and octopus merges cannot prove the absence of resolution edits.
                paths = run(
                    "log", "--format=", "--name-only", "-z", "-r", "--no-renames", "--root",
                    "--remerge-diff" if remerge else "--cc", *revision_range, strip=False,
                ).split("\0")
                if run("rev-list", "--min-parents=3" if remerge else "--min-parents=2", *revision_range):
                    raise ValueError("merge resolution paths cannot be verified")
            outside = sorted(path for path in set(paths) if path and not path_is_owned(path, owned))
            if outside:
                cause = "outside_owned_paths: " + ", ".join(
                    sanitize_for_display(redact_text(path)) for path in outside
                )
                if len(cause) > 1024:
                    cause = cause[:1009] + "... (truncated)"
        except (OSError, ValueError, TypeError, IndexError, KeyError, TaskScratchError, subprocess.SubprocessError):
            cause = "owned_paths_verification_failed"
    if cause is None:
        if record["worktree_dirty_on_exit"] is not False:
            cause = "worktree_dirty_or_unknown"
        elif record["commits_ahead"] is None or record["commits_ahead"] == 0:
            cause = "no_commits_or_unknown"
        elif record["push_state"] != "pushed":
            cause = "work_not_pushed_or_unknown"
    if cause:
        record.update(status="no_deliverable", error=cause, no_deliverable_reason=cause)


def _reap_settled(record: dict, path: Path) -> None:
    # The sole caller persists terminal status before this call, so no retry is needed.
    if record.get("status") not in {
        "done", "failed", "timeout", "rate_limited", "cancelled", "crashed",
        "dry_run", "needs_finalize", "no_deliverable",
    }:
        record["reap_note"] = f"common reaper skipped: task status is not terminal ({record.get('status')})"
        with contextlib.suppress(OSError):
            store.replace(record, path)
        return
    if record.get("worktree_dirty_on_exit") is not False or record.get("push_state") != (
        "not_applicable" if record["mode"] == "read-only" else "pushed"
    ):
        return
    try:
        owner = os.getpid()
        identity = _identity(owner)
        if os.fork():
            return
    except OSError:
        record["reap_note"] = "common reaper helper launch failed"
        with contextlib.suppress(OSError):
            store.replace(record, path)
        return
    # The common reaper refuses live task PIDs. Keep the recorded identity intact
    # and wait outside the worktree until this supervisor has actually exited.
    try:
        os.setsid()
        os.chdir(git.ROOT)
        while identity is not None and _identity(owner) == identity:
            time.sleep(0.05)
        result = subprocess.run(
            [str(project_interpreter()), "-m", "scripts.fleet.post_task_reap",
             "--task-id", record["task_id"], "--apply", "--tasks-dir", str(path.parent)],
            cwd=git.ROOT, capture_output=True, check=True, timeout=120,
        )
        action = json.loads(result.stdout)["main_worktree"]["action"]
        note = "common reaper: " + (action if action in {"removed", "retained", "skipped", "error"} else "unknown")
        current = json.loads(path.read_text())
        current["reap_note"] = note
        store.replace(current, path)
    except Exception:
        with contextlib.suppress(OSError, ValueError):
            current = json.loads(path.read_text())
            current["reap_note"] = "common reaper failed"
            store.replace(current, path)
    finally:
        os._exit(0)


def supervise(path: Path, options: dict | None = None, hard_timeout: float | None = None) -> None:
    os.umask(0o077)
    record = json.loads(path.read_text())
    spec = _spec(record, options or {})
    options = spec.options
    hard_timeout, silence_timeout, initial_response_timeout = deadlines({
        **options, **{key: record[key] for key in ("hard_timeout", "silence_timeout", "initial_response_timeout")
                     if key in record},
        **({"hard_timeout": hard_timeout} if hard_timeout is not None else {}),
    })
    child, status, returncode, error, usage, text = None, "crashed", None, None, None, None
    slots = None
    resolved_model = None
    started = time.monotonic()

    def cancelled(_signum, _frame):
        raise _Cancelled()

    def terminate():
        # Only an unreaped leader still pins its group id; a reaped one's id may name another group.
        if child and child.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(child.pid, signal.SIGKILL)
            child.wait()

    signal.signal(signal.SIGTERM, cancelled)
    signal.signal(signal.SIGINT, cancelled)
    stdout_path = path.parent / "logs" / f"{spec.task_id}.stdout.log"
    stderr_path = path.parent / "logs" / f"{spec.task_id}.stderr.log"
    try:
        signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM, signal.SIGINT})
        schema = None
        if options.get("output_schema_path") is not None:
            from scripts.dispatcher.output_schema import load

            try:
                schema = load(options)
            except (OSError, ValueError):
                status, error = "failed", "output schema binding invalid"
                return
        provider = providers.load(spec.agent)
        invocation = provider.build(spec, child_env(spec))
        try:
            invocation = admission.claude_launch(spec, invocation)
        except ValueError as exc:
            status, error = "failed", str(exc)
            return
        slots, slots_record = admission.hold_review_test_slots(
            agent=spec.agent, mode=spec.mode, review_typed=admission.review_typed(record),
            sealed_attempt=bool(record.get("review_attempt")), task_id=spec.task_id,
        )
        if slots_record is not None:
            record["review_test_slots"] = slots_record
        with tempfile.TemporaryFile(dir=ensure_scratch_root()) as stdin, stdout_path.open("wb") as out, stderr_path.open("ab") as err:
            stdin.write(invocation.stdin or b"")
            stdin.seek(0)
            output_sizes = out.tell(), err.tell()
            child = subprocess.Popen(
                invocation.argv,
                stdin=stdin,
                stdout=out,
                stderr=err,
                cwd=spec.worktree,
                # The CLI's governed test runs join this hold through its marker (#11230).
                env={**invocation.env, **slots.environment()} if slots else invocation.env,
                start_new_session=True,
            )
            record.update(status="running")
            store.replace(record, path)
            communicate(child, invocation, stdout_path, stderr_path, hard_timeout, silence_timeout,
                        initial_response_timeout, liveness_paths(spec, invocation), output_sizes)
        returncode = child.returncode
        final = invocation.final_file
        final_text = final.read_text(errors="replace") if final and final.exists() else None
        parsed = provider.parse(
            stdout_path.read_text(errors="replace"), stderr_path.read_text(errors="replace"), returncode, final_text
        )
        text, usage = parsed.text, parsed.usage
        if schema is not None:
            from scripts.agent_runtime.adapters._output_schema import json_value, structured_result

            result = structured_result(json_value(text), schema, returncode=returncode, terminal_ok=not parsed.error)
            text = result.response
            if not result.ok:
                error = f"{result.failure_code}: {result.stderr_excerpt}"
                status = "failed"
                return
        resolved_model = parsed.resolved_model
        status = "done" if returncode == 0 and not parsed.error and text and text.strip() else "failed"
        if returncode < 0:
            status = "crashed"
        if status != "done":
            error = parsed.error or (
                "provider exited unsuccessfully" if returncode else "provider returned no successful final response"
            )
        if status == "done" and record.get("schema_version") == 2 and record.get("require_review_verdict") is True:
            try:
                from scripts.review.verdict_parser import recognized_verdicts

                verdicts = set(recognized_verdicts(text))
                if not verdicts:
                    status, error = "failed", "review_missing_verdict_line"
                elif len(verdicts) > 1:
                    status, error = "failed", "review_ambiguous_verdict"
            except Exception:
                status, error = "failed", "review_gate_error"
    except _Cancelled:
        status, error = "cancelled", "cancelled by client"
    except DeadlineExpired as exc:
        status, error = "timeout", exc.diagnostic
        record.update(kill_reason=exc.kind, stderr_excerpt=exc.diagnostic)
    except subprocess.TimeoutExpired:
        status, error = "timeout", "process deadline exceeded"
    except Exception:
        status, error = "crashed", "supervisor or provider processing failed"
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if child and (child.returncode is None or status in {"cancelled", "timeout", "crashed"}):
            terminate()
            returncode = child.returncode
        if slots is not None:
            # The hold is the supervisor's: a killed supervisor ends it, and the governed runs in flight
            # keep their slots shared until they exit (test_slots).
            slots.release()
        if text is not None:
            spec.final_file.write_text(text)
            spec.final_file.chmod(0o600)
        record.update(
            status=status,
            returncode=returncode,
            error=error,
            usage=usage,
            finished_at=store.now(),
            duration_s=round(time.monotonic() - started, 3),
            result_sha256=store.digest(spec.final_file.read_bytes()) if spec.final_file.exists() else None,
        )
        record.update(git.snapshot_delivery(spec, record))
        _enforce_delivery(record)
        if spec.agent == "cursor":
            record.update(
                resolved_model=resolved_model if resolved_model is not None else "unknown",
                resolved_model_known=resolved_model is not None,
                resolved_model_source="cursor-stream-json" if resolved_model is not None else "pending",
            )
        store.replace(record, path)

        _reap_settled(record, path)


def wait(task_id: str, nonce: str | None = None, timeout: float = 0, poll_interval: float = 1) -> tuple[dict, int]:
    deadline = time.monotonic() + timeout if timeout else None
    while True:
        record = _observe(store.read(task_id, nonce))
        if record["status"] not in store.ACTIVE:
            return record, 0 if record["status"] == "done" else 1
        remaining = deadline - time.monotonic() if deadline else None
        if remaining is not None and remaining <= 0:
            return record, 124
        time.sleep(min(poll_interval, remaining) if remaining is not None else poll_interval)


def cancel(task_id: str, nonce: str | None = None) -> dict:
    record = _observe(store.read(task_id, nonce))
    if record.get("schema_version") != 2:
        raise ValueError("legacy task cancellation belongs to its original supervisor")
    if record["status"] in store.ACTIVE:
        if not record.get("pid") or not record.get("process_start"):
            raise ValueError("supervisor identity is unavailable; cancellation refused")
        try:
            pidfd = os.pidfd_open(record["pid"])
            try:
                if _identity(record["pid"]) != record["process_start"]:
                    raise ValueError("supervisor identity changed; cancellation refused")
                signal.pidfd_send_signal(pidfd, signal.SIGTERM)
            finally:
                os.close(pidfd)
        except ProcessLookupError:
            return _observe(record)
        return wait(task_id, nonce, timeout=10, poll_interval=0.05)[0]
    return record


if __name__ == "__main__":
    settings = json.load(sys.stdin)
    supervise(Path(sys.argv[1]), **settings)
