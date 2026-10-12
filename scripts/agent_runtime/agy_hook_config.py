"""Validate AGY guard registration without executing hook commands."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shlex
import uuid
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from scripts.common.repo_root import main_checkout_root, project_interpreter
from scripts.common.safe_open import safe_open_below

ROOT = Path(__file__).resolve().parents[2]
GUARD_NAME = "shell-secret-print-guard"
ENTRY_POINT = Path("scripts/agent_runtime/secret_print_hook.py")
GUARD_TIMEOUT_FLOOR = 10


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
    def unique_members(pairs: list[tuple[str, object]]) -> dict:
        data = {}
        for key, value in pairs:
            if key in data:
                raise ValueError("duplicate_member")
            data[key] = value
        return data

    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_members)
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
    timeout = hook.get("timeout")
    if type(timeout) is not int or timeout < GUARD_TIMEOUT_FLOOR:
        raise AgyHookConfigError("invalid_timeout")
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
    """Require a valid enabled guard in every existing loadable candidate.

    An absent workspace or effective-HOME candidate cannot load and is skipped.
    At least one candidate must exist and validate. Existing invalid files still
    refuse, even alongside a valid file. Scoped HOME replaces ordinary HOME.
    PASS certifies registration in every loadable candidate, not hook execution
    or native blocking on any route. On the review route, the load-bearing
    control is the exact validated command-denial settings: ``command(*)`` and
    ``write_file(*)`` denied, checked by ``_write_review_permissions`` before
    launch, plus ``--sandbox``. Scoped-home guard registration is defense in
    depth. PASS does not certify that the hook can execute inside the review OS
    sandbox: the probe at 69690b9667 found its interpreter and entry point
    unreadable there. The failure disposition of a hook that cannot start is
    UNKNOWN. It can only fire on ``run_command``, which the settings deny.
    """
    try:
        interpreter = project_interpreter(repo_root)
        checked = 0
        for path in locations:
            try:
                path.lstat()
            except FileNotFoundError:
                continue
            _check_file(path, interpreter, repo_root / ENTRY_POINT, absolute=path.parent.name == "config")
            checked += 1
        if not checked:
            raise AgyHookConfigError("missing_file")
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
    target = cwd.resolve(strict=True)
    primary = main_checkout_root(target).resolve(strict=True)
    dispatch = (primary / ".worktrees/dispatch").resolve(strict=True) if primary != target else primary
    if ".." in cwd.parts or primary == target or target == dispatch or not target.is_relative_to(dispatch):
        raise AgyHookConfigError("install_requires_dispatch_worktree")
    provision_workspace_guard(cwd, repo_root=repo_root)


def provision_workspace_guard(cwd: Path, *, repo_root: Path = ROOT) -> None:
    """Explicitly provision a caller-created workspace, never an ordinary HOME.

    The caller owns the directory and its lifecycle. Walk real directories and
    atomically merge a missing guard, retaining unrelated bytes. Published files
    have mode 0600. This is not an implicit repair of existing gate candidates.
    """
    if ".." in cwd.parts:
        raise AgyHookConfigError("unsafe_install_path")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    directory_fd = os.open(cwd.absolute().anchor, flags)
    temporary = None
    try:
        for component in cwd.absolute().parts[1:]:
            child_fd = os.open(component, flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
        if os.fstat(directory_fd).st_uid != os.geteuid():
            raise AgyHookConfigError("unsafe_install_path")
        with suppress(FileExistsError):
            os.mkdir(".agents", dir_fd=directory_fd)
        child_fd = os.open(".agents", flags, dir_fd=directory_fd)
        os.close(directory_fd)
        directory_fd = child_fd
        try:
            fd = safe_open_below(directory_fd, "hooks.json", os.O_RDONLY)
        except FileNotFoundError:
            original = "{}"
        else:
            with os.fdopen(fd, "r", encoding="utf-8", newline="") as handle:
                original = handle.read()
        try:
            data = json.loads(original)
        except (ValueError, UnicodeError):
            raise AgyHookConfigError("invalid_json") from None
        if not isinstance(data, dict):
            raise AgyHookConfigError("invalid_json")
        if GUARD_NAME in data:
            return  # Preserve explicitly disabled or invalid user wiring.
        # Insert only the new member, keeping unrelated hook bytes unchanged.
        end = original.rindex("}")
        member = json.dumps({GUARD_NAME: guard_registration(repo_root=repo_root)}, indent=2)[1:-1]
        payload = original[:end] + ("," if data else "") + member + original[end:]
        temporary = f".hooks-{uuid.uuid4().hex}.tmp"
        fd = safe_open_below(directory_fd, temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, "hooks.json", src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
    except OSError:
        raise AgyHookConfigError("unsafe_install_path") from None
    finally:
        if temporary is not None:
            with suppress(FileNotFoundError):
                os.unlink(temporary, dir_fd=directory_fd)
        os.close(directory_fd)


def require_hook_config(cwd: Path, home: Path, agy_home: Path | None = None, *, install: bool = False) -> None:
    """Refuse before provider subprocesses; install only absent worktree files.

    Every existing candidate must validate, and at least one must contain the
    guard. Never repair an existing invalid candidate or write ordinary HOME.
    """
    try:
        if install and not os.path.lexists(cwd / ".agents/hooks.json") and main_checkout_root(cwd) != cwd:
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
