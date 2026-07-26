"""Shared pytest-stamp identity and writer for agent and Git hooks.

The agent hook records a successful pytest run. The Git pre-push hook reads the
same marker before allowing pytest-triggering changes to update ``main``.
Both sides must use the exact same repository, worktree, branch, and TMPDIR
contract or the guard alternates between false blocks and false greens.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MARKER_MAX_AGE_SECONDS = 10 * 60
MARKER_VERSION = 2
_CONTROL_OPERATORS = frozenset({"&&", "||", ";", "|", "&"})
_PYTEST_WRAPPERS = frozenset({"env", "nohup", "sudo", "time"})
_FAILURE_OUTCOMES = frozenset({"failed", "error", "errors"})
_CWD_MUTATORS = frozenset({"cd", "popd", "pushd"})
_NO_RUN_OPTIONS = frozenset(
    {
        "--collect-only",
        "--fixtures",
        "--fixtures-per-test",
        "--help",
        "--markers",
        "--trace-config",
        "--version",
        "-h",
    }
)
_SUMMARY_RE = re.compile(
    r"(?P<counts>(?:\d+\s+[A-Za-z_]+(?:,\s*|\s+))+)"
    r"in\s+\d+(?:\.\d+)?s\b",
    re.IGNORECASE,
)
_COUNT_RE = re.compile(r"(?P<count>\d+)\s+(?P<outcome>[A-Za-z_]+)", re.IGNORECASE)


@dataclass(frozen=True)
class StampIdentity:
    """The checkout identity a pytest result belongs to."""

    repository: Path
    worktree: Path
    branch: str
    key: str


def _git_environment() -> dict[str, str]:
    """Remove inherited Git selectors that could redirect repository discovery."""
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def _git_output(cwd: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            check=False,
            cwd=cwd,
            env=_git_environment(),
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _absolute_git_path(cwd: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = cwd / path
    return path.resolve()


def stamp_identity(worktree: Path, branch: str | None = None) -> StampIdentity | None:
    """Resolve a collision-resistant identity for one registered Git worktree."""
    top_output = _git_output(worktree, "rev-parse", "--show-toplevel")
    common_output = _git_output(worktree, "rev-parse", "--git-common-dir")
    branch_output = (
        f"{branch}\n"
        if branch is not None
        else _git_output(worktree, "symbolic-ref", "--quiet", "--short", "HEAD")
    )
    if top_output is None or common_output is None or branch_output is None:
        return None

    top_value = top_output.strip()
    common_value = common_output.strip()
    branch_value = branch_output.strip()
    if not top_value or not common_value or not branch_value:
        return None

    top = _absolute_git_path(worktree, top_value)
    common = _absolute_git_path(worktree, common_value)
    raw_identity = "\0".join((str(common), str(top), branch_value))
    key = hashlib.sha256(raw_identity.encode("utf-8")).hexdigest()[:24]
    return StampIdentity(
        repository=common,
        worktree=top,
        branch=branch_value,
        key=key,
    )


def stamp_identity_for_branch(repo_cwd: Path, branch: str) -> StampIdentity | None:
    """Find the unique registered worktree that currently owns ``branch``."""
    output = _git_output(repo_cwd, "worktree", "list", "--porcelain")
    if output is None:
        return None

    expected_ref = f"refs/heads/{branch}"
    matches: list[Path] = []
    worktree: Path | None = None
    branch_ref: str | None = None

    def finish_record() -> None:
        if worktree is not None and branch_ref == expected_ref:
            matches.append(worktree)

    for line in (*output.splitlines(), ""):
        if not line:
            finish_record()
            worktree = None
            branch_ref = None
        elif line.startswith("worktree "):
            worktree = Path(line.removeprefix("worktree ")).resolve()
        elif line.startswith("branch "):
            branch_ref = line.removeprefix("branch ")

    if len(matches) != 1:
        return None
    return stamp_identity(matches[0], branch)


def _tmpdir(environment: dict[str, str] | None = None) -> Path:
    env = os.environ if environment is None else environment
    raw = env.get("TMPDIR") or "/tmp"
    if not raw.startswith("/"):
        raw = "/tmp"
    return Path(raw)


def marker_path(
    identity: StampIdentity,
    environment: dict[str, str] | None = None,
) -> Path:
    """Return the namespaced marker path shared by the writer and reader."""
    return _tmpdir(environment) / f"learn-uk-pytest.v{MARKER_VERSION}.{identity.key}.stamp"


def marker_is_fresh(
    marker: Path,
    identity: StampIdentity,
    *,
    now: float | None = None,
) -> bool | None:
    """Return freshness, or ``None`` when marker inspection itself failed."""
    try:
        if marker.read_text(encoding="utf-8").strip() != identity.key:
            return False
        current_time = time.time() if now is None else now
        return current_time - marker.stat().st_mtime <= MARKER_MAX_AGE_SECONDS
    except FileNotFoundError:
        return False
    except OSError:
        return None


def write_marker(identity: StampIdentity) -> bool:
    """Atomically refresh one marker without exposing a partially written file."""
    marker = marker_path(identity)
    temporary: Path | None = None
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        descriptor, raw_path = tempfile.mkstemp(
            dir=marker.parent,
            prefix=f".{marker.name}.",
        )
        temporary = Path(raw_path)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(f"{identity.key}\n")
        os.replace(temporary, marker)
        temporary = None
    except OSError:
        return False
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass
    return True


def _tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("tool_input", "arguments", "input", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def payload_workdir(payload: dict[str, Any]) -> Path | None:
    """Resolve the Bash execution cwd from structured hook fields.

    Tool-specific cwd fields outrank the session envelope. A relative tool cwd
    is resolved only against an absolute envelope cwd; guessing from the hook
    process cwd would recreate the primary-vs-worktree bug this contract fixes.
    """
    tool_input = _tool_input(payload)
    envelope_raw = payload.get("cwd") or payload.get("working_directory")
    tool_raw = (
        tool_input.get("cwd")
        or tool_input.get("workdir")
        or tool_input.get("working_directory")
    )

    envelope = Path(str(envelope_raw)).expanduser() if envelope_raw else None
    candidate = Path(str(tool_raw)).expanduser() if tool_raw else envelope
    if candidate is None:
        return None
    if candidate.is_absolute():
        return candidate.resolve()
    if envelope is None or not envelope.is_absolute():
        return None
    return (envelope / candidate).resolve()


def _shell_tokens(command: str) -> list[str] | None:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return None


def _split_segments(tokens: list[str]) -> tuple[list[list[str]], bool]:
    segments: list[list[str]] = []
    current: list[str] = []
    compound = False
    for token in tokens:
        if token in _CONTROL_OPERATORS or (token and set(token) <= {"&", "|", ";"}):
            compound = True
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments, compound


def _is_assignment(token: str) -> bool:
    name, separator, _ = token.partition("=")
    return bool(separator and name and name.replace("_", "a").isalnum() and not name[0].isdigit())


def _is_pytest_segment(segment: list[str]) -> bool:
    index = 0
    while index < len(segment) and (
        segment[index] in _PYTEST_WRAPPERS or _is_assignment(segment[index])
    ):
        index += 1
    if index >= len(segment):
        return False
    executable = segment[index]
    if executable == "pytest" or executable.endswith("/pytest"):
        return True
    is_project_python = executable == ".venv/bin/python" or executable.endswith("/.venv/bin/python")
    if is_project_python and segment[index + 1 : index + 3] == ["-m", "pytest"]:
        return True
    return segment[index : index + 3] == ["dagger", "call", "pytest"]


def _is_no_run_pytest(segment: list[str]) -> bool:
    return any(token == "--co" or token.partition("=")[0] in _NO_RUN_OPTIONS for token in segment)


def _command_is_compound_pytest(command: str) -> bool | None:
    tokens = _shell_tokens(command)
    if not tokens:
        return None
    segments, compound = _split_segments(tokens)
    if any(segment and segment[0] in _CWD_MUTATORS for segment in segments):
        return None
    pytest_invocations = [segment for segment in segments if _is_pytest_segment(segment)]
    if len(pytest_invocations) != 1 or _is_no_run_pytest(pytest_invocations[0]):
        return None
    return compound or len(segments) != 1


def _command_output(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        direct: list[str] = []
        for key in ("tool_output", "output", "result", "stdout", "stderr"):
            item = value.get(key)
            if isinstance(item, str) and item:
                direct.append(item)
        if direct:
            return "\n".join(direct)
        nested: list[str] = []
        for key in ("tool_response", "tool_result"):
            item = _command_output(value.get(key))
            if item:
                nested.append(item)
        return "\n".join(nested)
    if isinstance(value, list):
        return "\n".join(filter(None, (_command_output(item) for item in value)))
    return ""


def _passing_summaries(output: str) -> list[bool]:
    summaries: list[bool] = []
    for match in _SUMMARY_RE.finditer(output):
        outcomes = {
            item.group("outcome").lower(): int(item.group("count"))
            for item in _COUNT_RE.finditer(match.group("counts"))
        }
        passed = outcomes.get("passed", 0) > 0
        failed = any(outcomes.get(outcome, 0) > 0 for outcome in _FAILURE_OUTCOMES)
        summaries.append(passed and not failed)
    return summaries


def payload_proves_pytest_success(payload: dict[str, Any]) -> bool:
    """Accept only a proven pytest success for the command shape and event."""
    tool_input = _tool_input(payload)
    command = tool_input.get("command") or payload.get("command")
    if not isinstance(command, str) or not command.strip():
        return False

    compound = _command_is_compound_pytest(command)
    if compound is None:
        return False
    event_name = str(payload.get("hook_event_name") or "")
    if event_name == "PostToolUse" and not compound:
        return True

    summaries = _passing_summaries(_command_output(payload))
    return bool(summaries) and all(summaries)


def record_payload(payload: dict[str, Any]) -> bool:
    """Write a stamp only when checkout identity and pytest success are proven."""
    if not payload_proves_pytest_success(payload):
        return False
    workdir = payload_workdir(payload)
    if workdir is None:
        return False
    identity = stamp_identity(workdir)
    if identity is None:
        return False
    return write_marker(identity)


def main() -> int:
    """Agent hooks are observational: inability to stamp must not block a tool."""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return 0
    if isinstance(payload, dict):
        record_payload(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
