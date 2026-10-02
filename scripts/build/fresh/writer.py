"""Writer dispatch, execution, result harvesting, and schema validation (#8431 r3 §1, §7).

The writer call:
- takes explicit --writer {claude,codex,agy} (code never auto-routes)
- requires preflight result: refuses structurally unless preflight passed (#8431 §7 row 0)
- runs scripts/delegate.py dispatch --agent <writer> --mode read-only --worktree
  --task-id write-<level>-<slug>-<n>-<attempt>-<inputs digest>[-<effort>] --prompt-file ... --research-role writer
- runs delegate.py wait <task-id> (wait is mandatory before reading result)
- forwards explicit effort only when supplied; completed task effort is recorded or unknown
- fails if wait reports non-done status
- saves raw reply and writer metadata (including seat model and prompt hash) with atomic writes (0o644)
  even if schema validation fails
- strips surrounding Markdown fence if present
- parses YAML into dict
- validates with E1's schema (Draft202012Validator + code checks) BEFORE anything else reads it
- writes draft with lock sidecar only after schema validation succeeds.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import sys
from collections.abc import Callable, Mapping
from functools import wraps
from pathlib import Path
from typing import Any

import yaml

from scripts.agent_runtime.registry import AGENTS
from scripts.build.fresh.draft_schema import (
    DraftError,
    DraftValidationError,
    validate_draft,
)
from scripts.build.fresh.preflight import PreflightResult
from scripts.build.fresh.regeneration import (
    HARNESS_EXHAUSTED,
    INPUT_KEYS,
    lesson_mutex,
    load_harness,
    record_harness_failure,
    writer_task_id,
)
from scripts.common.task_store_paths import tasks_dir
from scripts.curriculum.evidence import lock
from scripts.orchestration.task_record_store import locate_task_record

REPO_ROOT = Path(__file__).resolve().parents[3]
ALLOWED_WRITERS: tuple[str, ...] = ("claude", "codex", "agy")
WRITER_EFFORTS: tuple[str, ...] = ("low", "medium", "high", "xhigh")


class WriterCallError(Exception):
    """Failure during the writer call or result harvesting."""

    def __init__(self, message: str, errors: list[DraftError] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.errors = errors or []


class WriterHarnessError(WriterCallError):
    """Dispatch, execution, or harvesting failed before a writer reply was available."""


def _available_task_id(base_id: str, *, writer: str, model: str | None, effort: str | None) -> tuple[str, bool]:
    """Reuse done/live tasks; advance only past terminal failures, preserving their records.

    Preserve legacy IDs for the same verified seat/model. Other seats use a stable
    namespace; only terminal failures or unreadable done results advance retries.
    Unreadable task records and live tasks never advance.
    """
    terminal_failures = {
        "failed",
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "dry_run",
        "needs_finalize",
        "no_deliverable",
    }
    retry = 0
    original_base = base_id
    model = model or AGENTS.get(writer, {}).get("default_model")
    while True:
        task_id = base_id if retry == 0 else f"{base_id}-retry-{retry}"
        record_path = locate_task_record(tasks_dir(), task_id)
        if record_path is None:
            return task_id, False
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
            status = record.get("status") if isinstance(record, dict) else None
        except (OSError, ValueError) as err:
            raise WriterHarnessError(f"Cannot read writer task record for {task_id}: {err}") from err
        if not isinstance(status, str):
            raise WriterHarnessError(f"Writer task {task_id} has unknown status: {status!r}")
        if status in terminal_failures:
            retry += 1
        elif status in {"done", "spawning", "running"}:
            recorded_model = record.get("resolved_model") or record.get("model")
            if not record.get("agent") or not recorded_model or recorded_model == "unknown" or model is None:
                raise WriterHarnessError(
                    f"Writer task {task_id} has unverified writer identity; explicit model required"
                )
            if record["agent"] != writer or recorded_model != model:
                if base_id != original_base:
                    raise WriterHarnessError(f"Writer task {task_id} has conflicting seat identity")
                identity = json.dumps([writer, model], separators=(",", ":")).encode("utf-8")
                base_id = f"{original_base}-seat-{hashlib.sha256(identity).hexdigest()[:10]}"
                retry = 0
                continue
            if effort is not None and (record.get("resolved_effort") or record.get("effort")) != effort:
                raise WriterHarnessError(f"Writer task {task_id} has unverified or conflicting effort")
            if status == "done":
                result = record.get("result_file")
                try:
                    if not isinstance(result, str) or not result:
                        raise OSError("missing result_file")
                    if not Path(result).is_file():
                        raise OSError("result is not a regular file")
                    Path(result).read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    # Preserve the done record, but never reuse unharvestable output.
                    retry += 1
                    continue
            return task_id, True
        else:
            raise WriterHarnessError(f"Writer task {task_id} has unknown status: {status!r}")


def _run_harness(cmd: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    """Turn subprocess launch/timeout failures into an engine-layer error."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError, UnicodeError) as err:
        raise WriterHarnessError(f"Writer harness execution failed: {err}") from err


def strip_markdown_fence(text: str) -> str:
    """Strip an enclosing Markdown code fence (e.g. ```yaml ... ``` or ``` ... ```)."""
    s = text.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return s


def parse_and_validate_reply(
    raw_reply: str,
    level: str,
    *,
    plan_activity_types: dict[str, str] | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Strip markdown fence, parse YAML, and run E1 schema validation."""
    clean_yaml = strip_markdown_fence(raw_reply)
    try:
        draft = yaml.safe_load(clean_yaml)
    except Exception as err:
        raise WriterCallError(f"Failed to parse writer output as YAML: {err}") from err

    if not isinstance(draft, dict):
        raise WriterCallError(f"Writer output is not a YAML dictionary: {type(draft).__name__}")

    errors = validate_draft(
        draft,
        level=level,
        schemas_dir=schemas_dir,
        activity_types=plan_activity_types,
    )
    if errors:
        raise DraftValidationError(errors)

    return draft


def _track_harness_failures(function):
    @wraps(function)
    def tracked(**kwargs):
        # Invalid input snapshots are caller errors, not paid harness attempts.
        inputs = kwargs["inputs"]
        if any(key not in inputs for key in INPUT_KEYS) or inputs["prompt_sha256"] != kwargs["prompt_sha256"]:
            return function(**kwargs)
        output_dir = Path(kwargs["output_dir"])
        n, slug = kwargs["lesson_n"], kwargs["slug"]
        ledger_path = output_dir / f"lesson-{n}.regeneration.yaml"
        # Serialize paid calls as well as accounting: concurrent builds cannot pass
        # the last remaining slot together. Other lessons keep independent mutexes.
        with lesson_mutex(output_dir / f"lesson-{n}.writer-dispatch"):
            evidence = load_harness(ledger_path, slug, n)
            if evidence["terminal_state"] is not None:
                error = WriterHarnessError(HARNESS_EXHAUSTED)
                error.harness_recorded = True
                raise error
            try:
                return function(**kwargs)
            except (OSError, ValueError, KeyError, TypeError, WriterHarnessError) as err:
                record_harness_failure(ledger_path, slug, n, str(err), dict(kwargs["inputs"]))
                if load_harness(ledger_path, slug, n)["terminal_state"] is not None:
                    error = WriterHarnessError(HARNESS_EXHAUSTED)
                    error.harness_recorded = True
                    raise error from err
                err.harness_recorded = True
                raise

    return tracked


@_track_harness_failures
def dispatch_writer(
    *,
    writer: str,
    level: str,
    slug: str,
    lesson_n: int,
    prompt_file: Path,
    prompt_sha256: str,
    output_dir: Path,
    preflight_result: PreflightResult | None = None,
    attempt: int = 1,
    plan_activity_types: dict[str, str] | None = None,
    fake_seat: Path | str | Callable[[str, Path, Path], None] | None = None,
    timeout: int = 1800,
    repo_root: Path | None = None,
    delegate_script: Path | None = None,
    schemas_dir: Path | None = None,
    model: str | None = None,
    effort: str | None = None,
    inputs: Mapping[str, str],
) -> dict[str, Any]:
    """Execute the writer call, wait for completion, parse and validate the draft.

    Structurally refuses if preflight_result did not pass (#8431 §7 row 0, Finding 4).
    Saves raw reply and seat metadata before schema validation so provenance is preserved
    even on schema failure (#8431 §1, Finding 11).
    Fake seats may write <task-id>.json beside their result to supply resolved model/effort.
    ``inputs`` is the complete regeneration-ledger snapshot (``regeneration.writer_inputs``); its digest keys
    the base task ID. Done attempts are waited on and revalidated without another dispatch; terminal
    non-done records get a stable retry suffix. Thus identical successful inputs never pay twice,
    while failed harness attempts can be retried without overwriting or accepting their output.
    """
    # 0. Structural preflight gate (#8431 §7 row 0, Finding 4)
    if preflight_result is None or not preflight_result.passed:
        raise WriterHarnessError("Writer dispatch refused: preflight verification did not pass (#8431 §7 row 0).")

    if writer not in ALLOWED_WRITERS:
        raise ValueError(f"Invalid writer {writer!r}. Explicit writer seat must be one of {ALLOWED_WRITERS}.")
    if effort is not None and effort not in WRITER_EFFORTS:
        raise ValueError(f"Invalid writer effort {effort!r}. Expected one of {WRITER_EFFORTS}.")

    root = repo_root or REPO_ROOT
    missing = [key for key in INPUT_KEYS if key not in inputs]
    if missing:
        raise ValueError(f"Writer inputs snapshot is missing {missing}.")
    if inputs["prompt_sha256"] != prompt_sha256:
        raise ValueError("Writer inputs snapshot does not match prompt_sha256.")
    task_id = writer_task_id(level, slug, lesson_n, attempt, effort, inputs)
    del_script = delegate_script or (root / "scripts/delegate.py")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    draft_file = output_dir / f"lesson-{lesson_n}.draft.yaml"
    raw_file = output_dir / f"lesson-{lesson_n}.raw.txt"
    writer_meta_file = output_dir / f"lesson-{lesson_n}.writer.yaml"

    seat_model = model
    wait_state: dict[str, Any] = {}

    # 1. Execute task (either through fake seat or real delegate.py)
    if fake_seat is not None:
        result_file = root / f"batch_state/tasks/{task_id}.result"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        if callable(fake_seat):
            try:
                fake_seat(task_id, prompt_file, result_file)
            except (OSError, subprocess.SubprocessError) as err:
                raise WriterHarnessError(f"Fake seat execution failed: {err}") from err
        else:
            seat_path = Path(fake_seat)
            cmd = [
                sys.executable,
                str(seat_path),
                "--task-id",
                task_id,
                "--prompt-file",
                str(prompt_file),
                "--result-file",
                str(result_file),
            ]
            if effort is not None:
                cmd.extend(("--effort", effort))
            proc = _run_harness(cmd, timeout=60)
            if proc.returncode != 0:
                raise WriterHarnessError(f"Fake seat script failed with exit code {proc.returncode}: {proc.stderr}")
        # Fake seats may emit the same task-record sidecar as delegate.py.
        task_record = result_file.with_suffix(".json")
        if task_record.is_file():
            try:
                record = json.loads(task_record.read_text(encoding="utf-8"))
            except (OSError, ValueError) as err:
                raise WriterHarnessError(f"Cannot read fake seat task record: {err}") from err
            if isinstance(record, dict):
                wait_state = record
                if "status" in record and record["status"] != "done":
                    raise WriterHarnessError(f"Fake seat completed with non-done status: {record['status']!r}")
    else:
        task_id, reuse = _available_task_id(task_id, writer=writer, model=model, effort=effort)
        # Real delegate dispatch (#8431 §1, Finding 7)
        dispatch_cmd = [
            sys.executable,
            str(del_script),
            "dispatch",
            "--agent",
            writer,
            "--mode",
            "read-only",
            "--worktree",
            "--task-id",
            task_id,
            "--prompt-file",
            str(prompt_file),
            "--research-role",
            "writer",
        ]
        if model is not None:
            dispatch_cmd.extend(("--model", model))
        if effort is not None:
            dispatch_cmd.extend(("--effort", effort))
        if not reuse:
            disp_proc = _run_harness(dispatch_cmd, timeout=60)
            if disp_proc.returncode != 0:
                raise WriterHarnessError(
                    f"delegate.py dispatch failed with exit code {disp_proc.returncode}: {disp_proc.stderr}"
                )

        # Wait for task to finish — mandatory before reading result (#8431 §1, Finding 7, MAJOR D)
        wait_cmd = [
            sys.executable,
            str(del_script),
            "wait",
            task_id,
            "--timeout",
            str(timeout),
        ]
        wait_proc = _run_harness(wait_cmd, timeout=timeout + 30)
        if wait_proc.returncode != 0:
            raise WriterHarnessError(
                f"delegate.py wait failed with exit code {wait_proc.returncode}: {wait_proc.stderr or wait_proc.stdout}"
            )

        # Parse JSON printed by delegate.py wait <task-id> (MAJOR D)
        try:
            wait_state = json.loads(wait_proc.stdout)
        except Exception as err:
            raise WriterHarnessError(
                f"delegate.py wait output was not valid JSON: {err}; stdout={wait_proc.stdout!r}"
            ) from err

        if not isinstance(wait_state, dict):
            raise WriterHarnessError(f"delegate.py wait output must be a JSON object, got {type(wait_state).__name__}")

        status = wait_state.get("status")
        if not isinstance(status, str) or status != "done":
            raise WriterHarnessError(f"Task {task_id} completed with non-done status: {status!r}")

        result_path_str = wait_state.get("result_file")
        if not isinstance(result_path_str, str) or not result_path_str:
            raise WriterHarnessError(f"delegate.py wait state missing 'result_file': {wait_state}")

        result_file = Path(result_path_str)

    seat_model = wait_state.get("resolved_model") or wait_state.get("model") or seat_model
    seat_effort = wait_state.get("resolved_effort") or wait_state.get("effort")
    if not isinstance(seat_effort, str) or not seat_effort.strip():
        seat_effort = "unknown"

    # 2. Read result file
    if not result_file.is_file():
        raise WriterHarnessError(f"Result file {result_file} not found after task completion.")

    try:
        raw_reply = result_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as err:
        raise WriterHarnessError(f"Cannot read writer result: {err}") from err

    # 3. Determine seat model (#8431 §1, Finding 11)
    if seat_model is None:
        seat_model = "unknown"

    # 4. Save raw reply and writer metadata ATOMICALLY (0o644) BEFORE schema validation (#8431 §1, Finding 11)
    # This guarantees provenance is preserved on disk even if schema validation fails.
    lock.atomic_write(raw_file, raw_reply.encode("utf-8"))

    meta = {
        "writer": writer,
        "model": seat_model,
        "effort": seat_effort,
        "prompt_sha256": prompt_sha256,
        "task_id": task_id,
        "attempt": attempt,
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }
    lock.atomic_write(writer_meta_file, yaml.safe_dump(meta, sort_keys=False).encode("utf-8"))

    # 5. Parse and validate draft before anything else reads it
    draft = parse_and_validate_reply(
        raw_reply,
        level=level,
        plan_activity_types=plan_activity_types,
        schemas_dir=schemas_dir,
    )

    # 6. Save validated draft with lock sidecar
    lock.write(draft_file, lock.yaml_bytes(draft))

    return {
        "draft": draft,
        "task_id": task_id,
        "writer": writer,
        "model": seat_model,
        "effort": seat_effort,
        "prompt_sha256": prompt_sha256,
        "draft_file": draft_file,
        "raw_file": raw_file,
        "writer_meta_file": writer_meta_file,
    }
