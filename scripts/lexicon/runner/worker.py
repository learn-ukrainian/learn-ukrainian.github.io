"""Hard-capped subprocess workers for leaf-chunk enrichment (#5230 PR1)."""

from __future__ import annotations

import json
import subprocess
import sys
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import ErrorCode, WorkerResult
from scripts.lexicon.runner.memory import (
    MemoryPolicy,
    apply_worker_memory_limit,
    classify_oom_exit,
    current_rss_bytes,
)

ROOT = Path(__file__).resolve().parents[3]


def _worker_main(payload: dict[str, Any], result_path: str) -> None:
    """Child entry: apply memory limit, then run the requested job."""
    policy = MemoryPolicy(
        high_bytes=int(payload.get("memory_high_bytes") or MemoryPolicy().high_bytes),
        max_bytes=int(payload.get("memory_max_bytes") or MemoryPolicy().max_bytes),
    )
    kind = apply_worker_memory_limit(policy)
    job = str(payload.get("job") or "enrich")
    chunk_id = str(payload.get("chunk_id") or "")
    try:
        if job == "inject_oom":
            from scripts.lexicon.runner.memory import _allocate_until_breach

            _allocate_until_breach(int(policy.max_bytes) * 4)
            result = WorkerResult(
                chunk_id=chunk_id,
                outcome="done",
                message="inject_oom unexpectedly survived",
                peak_rss_bytes=current_rss_bytes(),
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
            )
        else:
            result = WorkerResult(
                chunk_id=chunk_id,
                outcome="failed_terminal",
                error_code="unknown_job",
                message=f"unknown job {job!r}",
            )
        Path(result_path).write_text(
            json.dumps(asdict(result), ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except MemoryError:
        result = WorkerResult(
            chunk_id=chunk_id,
            outcome="failed_terminal",
            error_code=ErrorCode.FAILED_OOM.value,
            message="MemoryError",
            peak_rss_bytes=current_rss_bytes(),
        )
        Path(result_path).write_text(
            json.dumps(asdict(result), ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        raise SystemExit(137) from None
    except Exception as exc:
        result = WorkerResult(
            chunk_id=chunk_id,
            outcome="failed_terminal",
            error_code="worker_exception",
            message=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
            peak_rss_bytes=current_rss_bytes(),
        )
        Path(result_path).write_text(
            json.dumps(asdict(result), ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        raise SystemExit(1) from None


def run_capped_worker(
    payload: dict[str, Any],
    *,
    result_path: Path,
    timeout_s: float | None = None,
) -> WorkerResult:
    """Spawn a hard-capped child via subprocess; classify OOM when the OS stops it."""
    result_path.parent.mkdir(parents=True, exist_ok=True)
    if result_path.exists():
        result_path.unlink()
    payload_path = result_path.with_suffix(".payload.json")
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.lexicon.runner.worker",
                str(payload_path),
                str(result_path),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        if payload_path.exists():
            payload_path.unlink()
        return WorkerResult(
            chunk_id=str(payload.get("chunk_id") or ""),
            outcome="failed_terminal",
            error_code="worker_timeout",
            message="worker timed out",
        )
    if payload_path.exists():
        payload_path.unlink()

    if result_path.is_file():
        data = json.loads(result_path.read_text(encoding="utf-8"))
        return WorkerResult(
            chunk_id=str(data.get("chunk_id") or ""),
            outcome=data.get("outcome") or "failed_terminal",
            error_code=data.get("error_code"),
            lemma_artifacts=dict(data.get("lemma_artifacts") or {}),
            peak_rss_bytes=data.get("peak_rss_bytes"),
            message=str(data.get("message") or ""),
        )

    if classify_oom_exit(completed.returncode):
        return WorkerResult(
            chunk_id=str(payload.get("chunk_id") or ""),
            outcome="failed_terminal",
            error_code=ErrorCode.FAILED_OOM.value,
            message=f"OS terminated worker (returncode={completed.returncode})",
        )
    return WorkerResult(
        chunk_id=str(payload.get("chunk_id") or ""),
        outcome="failed_terminal",
        error_code="worker_crash",
        message=f"worker exited without result (returncode={completed.returncode})",
    )


def worker_cli(argv: list[str] | None = None) -> int:
    """``python -m scripts.lexicon.runner.worker <payload.json> <result.json>``."""
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print("usage: worker <payload.json> <result.json>", file=sys.stderr)
        return 2
    payload = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    _worker_main(payload, args[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(worker_cli())
