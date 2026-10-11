"""Validate effective AGY no-print wiring without executing hook commands."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

from scripts.common.repo_root import main_checkout_root, project_interpreter

ROOT = Path(__file__).resolve().parents[2]
GUARD_NAME = "shell-secret-print-guard"
ENTRY_POINT = Path("scripts/agent_runtime/secret_print_hook.py")


@dataclass(frozen=True)
class HookConfigResult:
    status: str
    reason: str

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


class AgyHookConfigError(ValueError):
    """A startup refusal, safe to include in diagnostics."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"agy_hook_config_refused: {reason}")


def hook_locations(cwd: Path, home: Path, agy_home: Path | None = None) -> tuple[Path, ...]:
    """List every filesystem candidate for this spawn's effective HOME."""
    if agy_home is not None and not agy_home.is_absolute():
        raise AgyHookConfigError("relative_scoped_home")
    effective_home = agy_home if agy_home is not None else home
    return (cwd / ".agents/hooks.json", effective_home / ".gemini/config/hooks.json")


def _read_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AgyHookConfigError("missing_file") from None
    except (OSError, UnicodeError, ValueError):
        raise AgyHookConfigError("invalid_json") from None
    if not isinstance(data, dict):
        raise AgyHookConfigError("invalid_json")
    return data


def _check_file(path: Path, interpreter: Path, script: Path, *, absolute: bool) -> None:
    guard = _read_config(path).get(GUARD_NAME)
    if not isinstance(guard, dict):
        raise AgyHookConfigError("missing_guard")
    if guard.get("enabled", True) is not True or guard.get("disabled", False) is not False:
        raise AgyHookConfigError("disabled")
    groups = guard.get("PreToolUse")
    if not isinstance(groups, list) or len(groups) != 1:
        raise AgyHookConfigError("wrong_event")
    group = groups[0]
    if not isinstance(group, dict):
        raise AgyHookConfigError("invalid_group")
    matcher = group.get("matcher")
    if not isinstance(matcher, str):
        raise AgyHookConfigError("invalid_matcher")
    try:
        matches = matcher in {"*", ""} or re.search(matcher, "run_command") is not None
    except re.error:
        raise AgyHookConfigError("invalid_matcher") from None
    if not matches:
        raise AgyHookConfigError("wrong_matcher")
    hooks = group.get("hooks")
    if not isinstance(hooks, list) or len(hooks) != 1 or not isinstance(hooks[0], dict):
        raise AgyHookConfigError("invalid_command")
    hook = hooks[0]
    if any(item.get("enabled", True) is not True or item.get("disabled", False) is not False for item in (group, hook)):
        raise AgyHookConfigError("disabled")
    if hook.get("type") != "command" or not isinstance(hook.get("command"), str):
        raise AgyHookConfigError("invalid_command")
    try:
        argv = shlex.split(hook["command"])
    except ValueError:
        raise AgyHookConfigError("invalid_command") from None
    if len(argv) != 4 or argv[2:] != ["--harness", "agy"]:
        raise AgyHookConfigError("invalid_command")
    paths = [Path(arg) for arg in argv[:2]]
    if absolute and not all(p.is_absolute() for p in paths):
        raise AgyHookConfigError("relative_home_command")
    resolved = [Path(os.path.abspath(path.parent / p)) for p in paths]
    # Compare interpreter spelling too: resolving its final symlink would accept
    # a system Python that bypasses the project's environment.
    if (
        resolved[0] != Path(os.path.abspath(interpreter))
        or not resolved[0].is_file()
        or not os.access(resolved[0], os.X_OK)
    ):
        raise AgyHookConfigError("invalid_interpreter")
    if resolved[1].resolve() != script.resolve() or not resolved[1].is_file():
        raise AgyHookConfigError("missing_script")


def check_hook_config(locations: tuple[Path, ...], *, repo_root: Path = ROOT) -> HookConfigResult:
    """PASS proves registration in each candidate, never native enforcement."""
    try:
        if not locations:
            raise AgyHookConfigError("missing_file")
        interpreter = project_interpreter(repo_root)
        for path in locations:
            _check_file(path, interpreter, repo_root / ENTRY_POINT, absolute=path.parent.name == "config")
    except AgyHookConfigError as exc:
        return HookConfigResult("REFUSE", exc.reason)
    except (OSError, ValueError):
        return HookConfigResult("REFUSE", "unresolved_path")
    return HookConfigResult("PASS", "guard_registered")


def guard_registration(*, repo_root: Path = ROOT) -> dict:
    """Use the tracked overlay, with absolute interpreter and entry-point paths."""
    guard = copy.deepcopy(_read_config(repo_root / "agents_extensions/agy/hooks.json")[GUARD_NAME])
    guard["PreToolUse"][0]["hooks"][0]["command"] = shlex.join(
        [str(project_interpreter(repo_root)), str((repo_root / ENTRY_POINT).absolute()), "--harness", "agy"]
    )
    return guard


def install_worktree_guard(cwd: Path, *, repo_root: Path = ROOT) -> None:
    """Merge only a missing guard into a dispatch workspace; never write homes."""
    primary = main_checkout_root(cwd)
    if primary == cwd or not cwd.absolute().is_relative_to(primary / ".worktrees/dispatch"):
        raise AgyHookConfigError("install_requires_dispatch_worktree")
    directory = cwd / ".agents"
    path = directory / "hooks.json"
    if directory.is_symlink() or path.is_symlink():
        raise AgyHookConfigError("unsafe_install_path")
    data = _read_config(path) if path.exists() else {}
    if GUARD_NAME in data:
        return  # Explicit disabled/invalid user wiring must refuse, not be repaired.
    data[GUARD_NAME] = guard_registration(repo_root=repo_root)
    directory.mkdir(exist_ok=True)
    with path.open("x" if not path.exists() else "w", encoding="utf-8") as handle:
        handle.write(json.dumps(data, indent=2) + "\n")


def require_hook_config(cwd: Path, home: Path, agy_home: Path | None = None, *, install: bool = False) -> None:
    """Refuse before any provider subprocess; optional install is workspace-only."""
    try:
        if install and main_checkout_root(cwd) != cwd:
            install_worktree_guard(cwd)
        result = check_hook_config(hook_locations(cwd, home, agy_home))
    except (OSError, ValueError) as exc:
        if isinstance(exc, AgyHookConfigError):
            raise
        raise AgyHookConfigError("install_failed") from None
    if not result.passed:
        raise AgyHookConfigError(result.reason)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read effective AGY hooks files and refuse missing no-print wiring.",
        epilog="Example: .venv/bin/python -m scripts.agent_runtime.agy_hook_config --cwd .\n"
        "Outputs: PASS or REFUSE with a reason code. Writes: none. Exit: 0 PASS, 2 REFUSE.",
    )
    parser.add_argument("--cwd", type=Path, required=True, help="AGY workspace directory.")
    parser.add_argument("--home", type=Path, default=Path.home(), help="Effective ordinary HOME.")
    args = parser.parse_args(argv)
    result = check_hook_config(hook_locations(args.cwd, args.home))
    print(f"{result.status}: {result.reason}")
    return 0 if result.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
