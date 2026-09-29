"""Hard-capped subprocess workers for leaf-chunk enrichment (#5230 PR1)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import ErrorCode, WorkerResult
from scripts.lexicon.runner.memory import (
    BoundedTimeoutExpired,
    MemoryPolicy,
    apply_worker_memory_limit,
    classify_oom_exit,
    current_rss_bytes,
    observed_memory_mechanism,
    project_interpreter,
    run_bounded_command,
    self_cgroup_relative,
)

ROOT = Path(__file__).resolve().parents[3]
# Reachable only when the parent exports this. A production payload cannot
# opt in: the job name alone is rejected.
_PROBE_JOBS_ENV = "LEXICON_WORKER_PROBE_JOBS"
_PROBE_ONLY_JOBS = frozenset({"stderr_exit", "sleep", "placement"})


def _write_result(result_path: str, result: WorkerResult) -> None:
    Path(result_path).write_text(
        json.dumps(asdict(result), ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _probe_jobs_enabled() -> bool:
    return os.environ.get(_PROBE_JOBS_ENV) == "1"


def _stderr_exit_probe(payload: dict[str, Any]) -> None:
    """Print a scope-failure-shaped line and exit. Tests count the executions."""
    counter = payload.get("counter_path")
    if counter:
        with Path(str(counter)).open("a", encoding="utf-8") as handle:
            handle.write("1\n")
    print(str(payload.get("stderr_text") or "Failed to connect"), file=sys.stderr)
    raise SystemExit(int(payload.get("exit_code") or 1))


def _worker_main(payload: dict[str, Any], result_path: str, *, scope_capped: bool = False) -> None:
    """Child entry: apply memory limit, then run the requested job."""
    policy = MemoryPolicy(
        high_bytes=int(payload.get("memory_high_bytes") or MemoryPolicy().high_bytes),
        max_bytes=int(payload.get("memory_max_bytes") or MemoryPolicy().max_bytes),
    )
    kind = apply_worker_memory_limit(policy, scope_capped=scope_capped)
    job = str(payload.get("job") or "enrich")
    chunk_id = str(payload.get("chunk_id") or "")
    if job in _PROBE_ONLY_JOBS and not _probe_jobs_enabled():
        _write_result(
            result_path,
            WorkerResult(
                chunk_id=chunk_id,
                outcome="failed_terminal",
                error_code="unknown_job",
                message=f"unknown job {job!r}",
                memory_mechanism=kind,
            ),
        )
        return
    if job == "stderr_exit":
        _stderr_exit_probe(payload)
        return
    if job == "sleep":
        time.sleep(float(payload.get("sleep_s") or 30))
        _write_result(
            result_path,
            WorkerResult(
                chunk_id=chunk_id,
                outcome="done",
                message="slept",
                memory_mechanism=kind,
                peak_rss_bytes=current_rss_bytes(),
            ),
        )
        return
    if job == "placement":
        _write_result(
            result_path,
            WorkerResult(
                chunk_id=chunk_id,
                outcome="done",
                message=self_cgroup_relative() or "",
                memory_mechanism=kind,
                peak_rss_bytes=current_rss_bytes(),
            ),
        )
        return
    try:
        if job == "inject_oom":
            from scripts.lexicon.runner.memory import _allocate_until_breach

            _allocate_until_breach(int(policy.max_bytes) * 4)
            result = WorkerResult(
                chunk_id=chunk_id,
                outcome="done",
                message="inject_oom unexpectedly survived",
                peak_rss_bytes=current_rss_bytes(),
                memory_mechanism=kind,
            )
        elif job == "enrich":
            from scripts.lexicon.runner.worker_enrich import enrich_chunk_payload

            artifacts = enrich_chunk_payload(payload)
            result = WorkerResult(
                chunk_id=chunk_id,
                outcome="done",
                lemma_artifacts=artifacts,
                peak_rss_bytes=current_rss_bytes(),
                message=f"enforcement={kind}",
                memory_mechanism=kind,
            )
        else:
            result = WorkerResult(
                chunk_id=chunk_id,
                outcome="failed_terminal",
                error_code="unknown_job",
                message=f"unknown job {job!r}",
                memory_mechanism=kind,
            )
        _write_result(result_path, result)
    except MemoryError:
        result = WorkerResult(
            chunk_id=chunk_id,
            outcome="failed_terminal",
            error_code=ErrorCode.FAILED_OOM.value,
            message="MemoryError",
            peak_rss_bytes=current_rss_bytes(),
            memory_mechanism=kind,
        )
        _write_result(result_path, result)
        raise SystemExit(137) from None
    except Exception as exc:
        result = WorkerResult(
            chunk_id=chunk_id,
            outcome="failed_terminal",
            error_code="worker_exception",
            message=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
            peak_rss_bytes=current_rss_bytes(),
            memory_mechanism=kind,
        )
        _write_result(result_path, result)
        raise SystemExit(1) from None


def run_capped_worker(
    payload: dict[str, Any],
    *,
    result_path: Path,
    timeout_s: float | None = None,
) -> WorkerResult:
    """Spawn a hard-capped child in its own scope; classify OOM when the OS stops it."""
    interpreter = project_interpreter()
    result_path.parent.mkdir(parents=True, exist_ok=True)
    if result_path.exists():
        result_path.unlink()
    payload_path = result_path.with_suffix(".payload.json")
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    policy = MemoryPolicy(
        high_bytes=int(payload.get("memory_high_bytes") or MemoryPolicy().high_bytes),
        max_bytes=int(payload.get("memory_max_bytes") or MemoryPolicy().max_bytes),
    )
    try:
        bounded = run_bounded_command(
            [
                str(interpreter),
                "-m",
                "scripts.lexicon.runner.worker",
                str(payload_path),
                str(result_path),
            ],
            policy,
            cwd=str(ROOT),
            timeout_s=timeout_s,
        )
    except BoundedTimeoutExpired as exc:
        if payload_path.exists():
            payload_path.unlink()
        return WorkerResult(
            chunk_id=str(payload.get("chunk_id") or ""),
            outcome="failed_terminal",
            error_code="worker_timeout",
            message="worker timed out",
            memory_mechanism=exc.memory_mechanism,
        )
    if payload_path.exists():
        payload_path.unlink()

    completed = bounded.completed
    if result_path.is_file():
        data = json.loads(result_path.read_text(encoding="utf-8"))
        mechanism = observed_memory_mechanism(bounded.mechanism, str(data.get("memory_mechanism") or ""))
        return WorkerResult(
            chunk_id=str(data.get("chunk_id") or ""),
            outcome=data.get("outcome") or "failed_terminal",
            error_code=data.get("error_code"),
            lemma_artifacts=dict(data.get("lemma_artifacts") or {}),
            peak_rss_bytes=data.get("peak_rss_bytes"),
            message=str(data.get("message") or ""),
            memory_mechanism=mechanism,
            oom_kill=bounded.oom_kill,
        )

    mechanism = observed_memory_mechanism(bounded.mechanism, "")
    if classify_oom_exit(
        completed.returncode, oom_kill=bounded.oom_kill,
        require_oom_record=bounded.mechanism == "systemd_scope",
    ):
        return WorkerResult(
            chunk_id=str(payload.get("chunk_id") or ""),
            outcome="failed_terminal",
            error_code=ErrorCode.FAILED_OOM.value,
            message=f"OS terminated worker (returncode={completed.returncode})",
            memory_mechanism=mechanism,
            oom_kill=bounded.oom_kill,
        )
    return WorkerResult(
        chunk_id=str(payload.get("chunk_id") or ""),
        outcome="failed_terminal",
        error_code="worker_crash",
        message=_worker_crash_message(completed),
        memory_mechanism=mechanism,
        oom_kill=bounded.oom_kill,
    )


def _worker_crash_message(completed: subprocess.CompletedProcess[str]) -> str:
    """Crash text, including a stderr tail when the scope or worker left one."""
    message = f"worker exited without result (returncode={completed.returncode})"
    tail = (completed.stderr or "").strip()
    if not tail:
        return message
    return f"{message}; stderr={tail[-500:]}"


def worker_cli(argv: list[str] | None = None) -> int:
    """``python -m scripts.lexicon.runner.worker <payload.json> <result.json>``."""
    args = argv if argv is not None else sys.argv[1:]
    if len(args) not in (2, 3) or (len(args) == 3 and args[2] != "--scope-capped"):
        print("usage: worker <payload.json> <result.json>", file=sys.stderr)
        return 2
    payload = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    _worker_main(payload, args[1], scope_capped=len(args) == 3)
    return 0


if __name__ == "__main__":
    raise SystemExit(worker_cli())
