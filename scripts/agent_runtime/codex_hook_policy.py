#!/usr/bin/env python3
"""Run Codex PreToolUse guards with isolated, fail-closed deadlines."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

LOCAL_BASH_GUARDS = (
    ("heal-core-bare.py", 3),
    ("guard-branch-switch-in-main.py", 3),
    ("guard-secret-print.py", 5),
)
ENFORCE_VENV_TIMEOUT = 3
PRIMARY_WRITE_GUARD = ("guard-primary-checkout-write.py", 5)
MERGE_GUARDS = (
    ("guard-admin-merge.py", 30),
    ("guard-pr-merge.py", 30),
)


@dataclass(frozen=True)
class GuardResult:
    name: str
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def run_guard(
    python_bin: Path,
    guard: Path,
    payload: str,
    timeout_seconds: float,
) -> GuardResult:
    """Run one guard and convert a deadline expiry into a blocking result."""
    try:
        completed = subprocess.run(
            [str(python_bin), str(guard)],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return GuardResult(
            name=guard.name,
            returncode=2,
            stdout=_timeout_text(exc.stdout),
            stderr=(
                _timeout_text(exc.stderr) + f"Codex hook guard {guard.name} exceeded {timeout_seconds:g}s; "
                "blocking the tool call fail-closed.\n"
            ),
            timed_out=True,
        )

    return GuardResult(
        name=guard.name,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _emit(result: GuardResult) -> None:
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)


def _tool_name(payload: str) -> str:
    try:
        decoded = json.loads(payload or "{}")
    except (json.JSONDecodeError, TypeError):
        return ""
    value = decoded.get("tool_name") if isinstance(decoded, dict) else None
    return value if isinstance(value, str) else ""


def _run_specs(
    python_bin: Path,
    hooks_dir: Path,
    payload: str,
    specs: tuple[tuple[str, int], ...],
) -> list[GuardResult]:
    return [run_guard(python_bin, hooks_dir / name, payload, timeout) for name, timeout in specs]


def _run_merge_guards(
    python_bin: Path,
    hooks_dir: Path,
    payload: str,
) -> list[GuardResult]:
    """Run independent network guards concurrently, return configured order."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(MERGE_GUARDS)) as pool:
        futures = [
            pool.submit(run_guard, python_bin, hooks_dir / name, payload, timeout) for name, timeout in MERGE_GUARDS
        ]
        return [future.result() for future in futures]


def _run_enforce_venv(
    hooks_dir: Path,
    canonical_root: Path,
    payload: str,
) -> GuardResult:
    environment = os.environ.copy()
    environment["LEARN_UK_HOOK_PROVIDER"] = "codex"
    environment["LEARN_UK_CANONICAL_ROOT"] = str(canonical_root)
    guard = hooks_dir / "enforce-venv.sh"
    try:
        completed = subprocess.run(
            ["/bin/bash", str(guard)],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
            timeout=ENFORCE_VENV_TIMEOUT,
            env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        return GuardResult(
            name=guard.name,
            returncode=2,
            stdout=_timeout_text(exc.stdout),
            stderr=(
                _timeout_text(exc.stderr) + f"Codex hook guard {guard.name} exceeded "
                f"{ENFORCE_VENV_TIMEOUT}s; blocking the tool call fail-closed.\n"
            ),
            timed_out=True,
        )
    return GuardResult(
        name=guard.name,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _result_code(results: list[GuardResult]) -> int:
    for result in results:
        _emit(result)
    if any(result.returncode == 2 for result in results):
        return 2
    return next((result.returncode for result in results if result.returncode), 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-bin", type=Path, required=True)
    parser.add_argument("--hooks-dir", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    args = parser.parse_args()
    payload = sys.stdin.read()
    tool_name = _tool_name(payload)
    rewrite_result = None
    if tool_name == "Bash":
        rewrite_result = _run_enforce_venv(
            args.hooks_dir,
            args.canonical_root,
            payload,
        )
        if rewrite_result.returncode:
            _emit(rewrite_result)
            return rewrite_result.returncode

    local_specs = LOCAL_BASH_GUARDS if tool_name == "Bash" else ()
    local_results = _run_specs(
        args.python_bin,
        args.hooks_dir,
        payload,
        (*local_specs, PRIMARY_WRITE_GUARD),
    )
    local_code = _result_code(local_results)
    if local_code:
        return local_code

    if tool_name == "Bash":
        merge_code = _result_code(_run_merge_guards(args.python_bin, args.hooks_dir, payload))
        if merge_code:
            return merge_code
        if rewrite_result is not None:
            _emit(rewrite_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
