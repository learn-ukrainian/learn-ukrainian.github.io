#!/usr/bin/env python3
"""Repair Entire 0.8.42's native Cursor session-start transcript locator.

Cursor remains the lifecycle owner.  This shim only fills the transcript path
that current Cursor releases omit, then delegates the original event to the
pinned native Entire hook.  Hook-mode failures are deliberately silent and
fail-open so optional capture can never change Cursor behavior.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

_MAX_INPUT_BYTES = 1 << 20
_MAX_HOOKS_BYTES = 1 << 20
_HOOK_TIMEOUT_SECONDS = 10
_SESSION_COMPONENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_NON_ALPHANUMERIC_RE = re.compile(r"[^a-zA-Z0-9]")

_STOCK_HOOKS = {
    "beforeSubmitPrompt": "before-submit-prompt",
    "preCompact": "pre-compact",
    "sessionEnd": "session-end",
    "sessionStart": "session-start",
    "stop": "stop",
    "subagentStart": "subagent-start",
    "subagentStop": "subagent-stop",
}
_STOCK_COMMANDS = {
    key: (
        "sh -c 'if ! command -v entire >/dev/null 2>&1; then exit 0; fi; "
        f"exec entire hooks cursor {verb}'"
    )
    for key, verb in _STOCK_HOOKS.items()
}
_SHIM_COMMAND = (
    "sh -c 'root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0; "
    'common=$(git -C "$root" rev-parse --path-format=absolute --git-common-dir '
    '2>/dev/null) || exit 0; py="$(dirname "$common")/.venv/bin/python"; '
    '[ -x "$py" ] || exit 0; "$py" '
    '"$root/scripts/entire/cursor_session_start_shim.py"; exit 0\''
)


class ReconciliationError(RuntimeError):
    """The ignored Cursor hook configuration is not safely reconcilable."""


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _git_root(cwd: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError("not a Git worktree")
    return Path(result.stdout.strip()).resolve(strict=True)


def _valid_session_component(value: object) -> str:
    if not isinstance(value, str) or value in {"", ".", ".."}:
        raise ValueError("invalid Cursor conversation id")
    if "\x00" in value or not _SESSION_COMPONENT_RE.fullmatch(value):
        raise ValueError("invalid Cursor conversation id")
    return value


def _validate_workspace_roots(raw: object, repo_root: Path) -> None:
    if raw is None:
        return
    if not isinstance(raw, list) or not raw:
        raise ValueError("invalid Cursor workspace roots")
    roots: list[Path] = []
    for item in raw:
        if not isinstance(item, str) or not item:
            raise ValueError("invalid Cursor workspace root")
        roots.append(Path(item).resolve(strict=True))
    if repo_root not in roots:
        raise ValueError("hook worktree is absent from Cursor workspace roots")


def _cursor_transcript_path(
    payload: dict[str, Any], *, repo_root: Path, home: Path
) -> Path:
    conversation_id = _valid_session_component(payload.get("conversation_id"))
    _validate_workspace_roots(payload.get("workspace_roots"), repo_root)
    project = _NON_ALPHANUMERIC_RE.sub("-", str(repo_root).lstrip("/"))
    base = (home / ".cursor" / "projects" / project / "agent-transcripts").resolve(
        strict=True
    )
    nested_dir = base / conversation_id
    nested = nested_dir / f"{conversation_id}.jsonl"
    flat = base / f"{conversation_id}.jsonl"

    if nested.exists():
        resolved = nested.resolve(strict=True)
        if not resolved.is_file() or not _is_within(resolved, base):
            raise ValueError("Cursor transcript escapes its project directory")
        return resolved
    if nested_dir.exists():
        resolved_dir = nested_dir.resolve(strict=True)
        if (
            not resolved_dir.is_dir()
            or nested_dir.is_symlink()
            or not _is_within(resolved_dir, base)
        ):
            raise ValueError("Cursor transcript directory is unsafe")
        return resolved_dir / f"{conversation_id}.jsonl"
    if flat.exists():
        resolved = flat.resolve(strict=True)
        if not resolved.is_file() or not _is_within(resolved, base):
            raise ValueError("Cursor transcript escapes its project directory")
        return resolved
    raise ValueError("Cursor transcript is not available at session start")


def _normalize(raw: bytes, *, cwd: Path, home: Path) -> tuple[bytes, Path]:
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Cursor hook input must be an object")
    repo_root = _git_root(cwd)
    transcript_path = parsed.get("transcript_path")
    if isinstance(transcript_path, str) and transcript_path.strip():
        return raw, repo_root
    if transcript_path not in {None, ""}:
        raise ValueError("invalid Cursor transcript path")
    parsed["transcript_path"] = str(
        _cursor_transcript_path(parsed, repo_root=repo_root, home=home)
    )
    encoded = json.dumps(
        parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return encoded, repo_root


def _hook() -> int:
    try:
        raw = sys.stdin.buffer.read(_MAX_INPUT_BYTES + 1)
        if not raw or len(raw) > _MAX_INPUT_BYTES:
            return 0
        payload, repo_root = _normalize(raw, cwd=Path.cwd(), home=Path.home())
        entire = shutil.which("entire")
        if not entire:
            return 0
        subprocess.run(
            [entire, "hooks", "cursor", "session-start"],
            input=payload,
            check=False,
            capture_output=True,
            cwd=repo_root,
            timeout=_HOOK_TIMEOUT_SECONDS,
        )
    except Exception:
        return 0
    return 0


def _load_hooks(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size > _MAX_HOOKS_BYTES:
        raise ReconciliationError("Cursor hooks file is missing or oversized")
    try:
        parsed = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise ReconciliationError("Cursor hooks file is malformed") from exc
    if not isinstance(parsed, dict) or not isinstance(parsed.get("hooks"), dict):
        raise ReconciliationError("Cursor hooks structure is malformed")
    return parsed


def _native_entry(parsed: dict[str, Any], hook_name: str) -> list[dict[str, Any]]:
    entries = parsed["hooks"].get(hook_name)
    if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
        raise ReconciliationError(f"native Cursor hook {hook_name} is missing")
    return entries


def _command_indexes(entries: list[dict[str, Any]], command: str) -> list[int]:
    return [index for index, entry in enumerate(entries) if entry.get("command") == command]


def _validate_native_hooks(parsed: dict[str, Any]) -> None:
    for hook_name, stock_command in _STOCK_COMMANDS.items():
        entries = _native_entry(parsed, hook_name)
        if hook_name == "sessionStart":
            stock = _command_indexes(entries, stock_command)
            shim = _command_indexes(entries, _SHIM_COMMAND)
            if (len(stock), len(shim)) not in {(1, 0), (0, 1)}:
                raise ReconciliationError("Cursor sessionStart ownership is ambiguous")
        elif len(_command_indexes(entries, stock_command)) != 1:
            raise ReconciliationError(f"native Cursor hook {hook_name} drifted")


def _atomic_write_hooks(path: Path, parsed: dict[str, Any]) -> None:
    encoded = (json.dumps(parsed, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    descriptor = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        path.chmod(0o600)
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()


def _reconcile(path: Path, action: str) -> bool:
    parsed = _load_hooks(path)
    _validate_native_hooks(parsed)
    entries = _native_entry(parsed, "sessionStart")
    shim = _command_indexes(entries, _SHIM_COMMAND)
    if action == "check":
        if len(shim) != 1:
            raise ReconciliationError("Cursor sessionStart shim is not installed")
        return False
    source, target = (
        (_STOCK_COMMANDS["sessionStart"], _SHIM_COMMAND)
        if action == "install"
        else (_SHIM_COMMAND, _STOCK_COMMANDS["sessionStart"])
    )
    indexes = _command_indexes(entries, source)
    if not indexes:
        return False
    entries[indexes[0]]["command"] = target
    _atomic_write_hooks(path, parsed)
    return True


def _admin(action: str) -> int:
    try:
        root = _git_root(Path.cwd())
        _reconcile(root / ".cursor" / "hooks.json", action)
    except (OSError, subprocess.SubprocessError, ValueError, ReconciliationError) as exc:
        print(f"Cursor Entire hook reconciliation failed: {exc}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        return _hook()
    if len(args) == 1 and args[0] in {"install", "uninstall", "check"}:
        return _admin(args[0])
    print("usage: cursor_session_start_shim.py [install|uninstall|check]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
