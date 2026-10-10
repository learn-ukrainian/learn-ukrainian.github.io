#!/usr/bin/env python3
"""Run Codex PreToolUse guards with isolated, fail-closed deadlines."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import runpy
import shlex
import shutil
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
# These guards answer by rewriting the command (``updatedInput``), which Codex
# ignores. Running them here turns any rewrite into a block instead of letting
# the call proceed unshimmed.
REWRITE_BASH_GUARDS = (("guard-public-github-text.py", 5),)
MERGE_GUARDS = (
    ("guard-admin-merge.py", 20),
    ("guard-pr-merge.py", 20),
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
    except OSError:
        return GuardResult(guard.name, 2, "", "Codex hook guard unavailable; blocking fail-closed.\n")
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
    except OSError:
        return GuardResult(guard.name, 2, "", "Codex hook guard unavailable; blocking fail-closed.\n")
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
    normalized: list[GuardResult] = []
    for result in results:
        if result.stdout:
            result = GuardResult(
                name=result.name,
                returncode=2,
                stdout="",
                stderr=(
                    result.stderr + f"Codex hook guard {result.name} wrote unexpected stdout; "
                    "blocking fail-closed to preserve the single JSON response channel.\n" + result.stdout
                ),
                timed_out=result.timed_out,
            )
        normalized.append(result)
        _emit(result)
    return 2 if any(result.returncode for result in normalized) else 0


def _has_unescaped_metachars(command: str) -> bool:
    single = False
    double = False
    escaped = False
    for index, char in enumerate(command):
        if escaped:
            escaped = False
            continue
        if char == "\\" and not single:
            escaped = True
            continue
        if char == "'" and not double:
            single = not single
            continue
        if char == '"' and not single:
            double = not double
            continue
        if not single:
            if char in ";|&\n<>{}`()":
                return True
            if char == "$" and index + 1 < len(command) and not command[index + 1].isspace():
                return True
        if double:
            if char in ";`()":
                return True
            if char == "$" and index + 1 < len(command) and not command[index + 1].isspace():
                return True
    return False


def _invokes_or_ambiguous_gh(command: str, recognize_gh: object) -> bool:
    """Recognize command positions, shell expansions, and wrappers hiding gh.

    Fail closed: returns False only if the command is a verified safe data mention.
    """
    if not (re.search(r"\bgh\b", command) or any(Path(w).name == "gh" for w in command.split())):
        return False
    if callable(recognize_gh) and recognize_gh(command):
        return True
    if _has_unescaped_metachars(command):
        return True
    try:
        words = shlex.split(command)
    except ValueError:
        return True
    if not words:
        return True
    cmd = Path(words[0]).name
    if cmd in {"echo", "printf"}:
        return False
    return not (cmd == "git" and len(words) > 1 and words[1] in {
        "commit", "log", "diff", "status", "show", "branch", "checkout", "add",
    })


def _publication_command_code(payload: str, hooks_dir: Path) -> int:
    """Admit only a literal, single gh call resolving to the tracked shim.

    Codex cannot apply updatedInput. Shell composition and expansions cannot
    establish that every publication uses the shim, so refuse those calls.
    Other commands still go through the existing shared guards.
    """
    decoded = json.loads(payload)
    command = decoded.get("tool_input", {}).get("command", "")
    if not isinstance(command, str):
        return 2
    try:
        words = shlex.split(command)
    except ValueError:
        print("Codex publication command cannot be parsed; blocking fail-closed.", file=sys.stderr)
        return 2
    named = any(Path(word).name == "gh" for word in words) or re.search(r"\bgh\b", command)
    if not named:
        return 0
    try:
        # Reuse the shared command-position recognizer; literal gh in data
        # (a commit message, for example) is not a publishing invocation.
        recognize = runpy.run_path(str(hooks_dir / "guard-public-github-text.py"))["invokes_gh"]
    except (OSError, SyntaxError, KeyError):
        print("Codex publication guard is unavailable; blocking fail-closed.", file=sys.stderr)
        return 2
    publication = _invokes_or_ambiguous_gh(command, recognize)
    if not publication:
        return 0
    # Even apparently safe early calls cannot license a later PATH replacement,
    # absolute executable, env -S script, pipe, subshell, or substitution.
    safe = not any(char in command for char in ";&|()$`\n<>\\")
    while words and words[0] in {"env", "/usr/bin/env", "command", "exec"}:
        words.pop(0)
        if words and words[0] == "--":
            words.pop(0)
    safe = safe and bool(words) and words[0] == "gh"
    shim = hooks_dir.parents[2] / "scripts/agent_runtime/shims/gh"
    resolved = shutil.which("gh")
    safe = safe and resolved is not None and Path(resolved).resolve() == shim.resolve()
    if not safe:
        print("Codex publication command is not fully shim guarded; blocking fail-closed.", file=sys.stderr)
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-bin", type=Path, required=True)
    parser.add_argument("--hooks-dir", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    args = parser.parse_args()
    payload = sys.stdin.read()
    tool_name = _tool_name(payload)
    try:
        decoded = json.loads(payload or "{}")
        if not isinstance(decoded, dict):
            raise ValueError("invalid payload")
    except ValueError:
        print("Codex tool payload is invalid; blocking fail-closed.", file=sys.stderr)
        return 2
    tool_input = decoded.get("tool_input", {})
    if tool_name == "write_stdin" or (
        tool_name == "Bash" and isinstance(tool_input, dict) and "chars" in tool_input
    ):
        print("Codex interactive input cannot be command guarded; blocking fail-closed.", file=sys.stderr)
        return 2
    if tool_name == "Bash":
        venv_result = _run_enforce_venv(
            args.hooks_dir,
            args.canonical_root,
            payload,
        )
        if _result_code([venv_result]):
            return 2
        publication_code = _publication_command_code(payload, args.hooks_dir)
        if publication_code:
            return publication_code

    local_specs = (*LOCAL_BASH_GUARDS, *REWRITE_BASH_GUARDS) if tool_name == "Bash" else ()
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
