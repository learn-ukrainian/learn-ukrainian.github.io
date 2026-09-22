"""Writer dispatch, execution, result harvesting, and schema validation (#8431 r3 §1, §7).

The writer call:
- takes explicit --writer {claude,codex,agy,grok} (code never auto-routes)
- runs scripts/delegate.py dispatch --agent <writer> --mode read-only --worktree
  --task-id write-<level>-<slug>-<n>-<attempt> --prompt-file ... --research-role writer
- runs delegate.py wait <task-id> (wait is mandatory)
- reads batch_state/tasks/<task-id>.result
- strips surrounding Markdown fence if present
- parses YAML into dict
- validates with E1's schema (Draft202012Validator + code checks) BEFORE anything else reads it
- keeps raw reply, prompt hash, and seat identity beside draft:
  lesson-<n>.draft.yaml, lesson-<n>.raw.txt, lesson-<n>.writer.yaml
- supports fake_seat parameter for test execution without paid calls
- no retry inside this step; schema failure is check-1 failure.
"""

from __future__ import annotations

import datetime
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.build.fresh.draft_schema import (
    DraftError,
    DraftValidationError,
    validate_draft,
)
from scripts.curriculum.evidence import lock

REPO_ROOT = Path(__file__).resolve().parents[3]
ALLOWED_WRITERS: tuple[str, ...] = ("claude", "codex", "agy", "grok")


class WriterCallError(Exception):
    """Failure during the writer call or result harvesting."""

    def __init__(self, message: str, errors: list[DraftError] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.errors = errors or []


def strip_markdown_fence(text: str) -> str:
    """Strip an enclosing Markdown code fence (e.g. ```yaml ... ``` or ``` ... ```)."""
    s = text.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        # Remove opening fence line
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing fence line
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


def dispatch_writer(
    *,
    writer: str,
    level: str,
    slug: str,
    lesson_n: int,
    prompt_file: Path,
    prompt_sha256: str,
    output_dir: Path,
    attempt: int = 1,
    plan_activity_types: dict[str, str] | None = None,
    fake_seat: Path | str | Callable[[str, Path, Path], None] | None = None,
    timeout: int = 1800,
    repo_root: Path | None = None,
    delegate_script: Path | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute the writer call, wait for completion, parse and validate the draft."""
    if writer not in ALLOWED_WRITERS:
        raise ValueError(
            f"Invalid writer {writer!r}. Explicit writer seat must be one of {ALLOWED_WRITERS}."
        )

    root = repo_root or REPO_ROOT
    task_id = f"write-{level}-{slug}-{lesson_n}-{attempt}"
    result_file = root / f"batch_state/tasks/{task_id}.result"
    del_script = delegate_script or (root / "scripts/delegate.py")

    # 1. Execute task (either through fake seat or real delegate.py)
    if fake_seat is not None:
        result_file.parent.mkdir(parents=True, exist_ok=True)
        if callable(fake_seat):
            fake_seat(task_id, prompt_file, result_file)
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
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
            if proc.returncode != 0:
                raise WriterCallError(
                    f"Fake seat script failed with exit code {proc.returncode}: {proc.stderr}"
                )
    else:
        # Real delegate dispatch
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
        disp_proc = subprocess.run(dispatch_cmd, capture_output=True, text=True, timeout=60, check=False)
        if disp_proc.returncode != 0:
            raise WriterCallError(
                f"delegate.py dispatch failed with exit code {disp_proc.returncode}: {disp_proc.stderr}"
            )

        # Wait for task to finish
        wait_cmd = [
            sys.executable,
            str(del_script),
            "wait",
            task_id,
            "--timeout",
            str(timeout),
        ]
        wait_proc = subprocess.run(wait_cmd, capture_output=True, text=True, timeout=timeout + 30, check=False)
        if wait_proc.returncode != 0:
            raise WriterCallError(
                f"delegate.py wait failed with exit code {wait_proc.returncode}: {wait_proc.stderr}"
            )

    # 2. Read result file
    if not result_file.is_file():
        raise WriterCallError(f"Result file {result_file} not found after task completion.")

    raw_reply = result_file.read_text(encoding="utf-8")

    # 3. Parse and validate draft before anything else reads it
    draft = parse_and_validate_reply(
        raw_reply,
        level=level,
        plan_activity_types=plan_activity_types,
        schemas_dir=schemas_dir,
    )

    # 4. Save state files beside draft in output_dir
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    draft_file = output_dir / f"lesson-{lesson_n}.draft.yaml"
    raw_file = output_dir / f"lesson-{lesson_n}.raw.txt"
    writer_meta_file = output_dir / f"lesson-{lesson_n}.writer.yaml"

    # Write draft with lock sidecar
    lock.write(draft_file, lock.yaml_bytes(draft))
    raw_file.write_text(raw_reply, encoding="utf-8")

    meta = {
        "writer": writer,
        "prompt_sha256": prompt_sha256,
        "task_id": task_id,
        "attempt": attempt,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    writer_meta_file.write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")

    return {
        "draft": draft,
        "task_id": task_id,
        "writer": writer,
        "prompt_sha256": prompt_sha256,
        "draft_file": draft_file,
        "raw_file": raw_file,
        "writer_meta_file": writer_meta_file,
    }
