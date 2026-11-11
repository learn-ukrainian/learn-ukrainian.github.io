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

from scripts.common.repo_root import (
    configure_native_hook_roots,
    machinery_path,
    main_checkout_root,
    product_root,
    project_interpreter,
)
from scripts.common.safe_open import safe_open_below

ROOT = Path(__file__).resolve().parents[2]
GUARD_NAME = "shell-secret-print-guard"
GUARD_TIMEOUT_FLOOR = 10
GUARD_MODE = "agy-secret-print"
# Every mode a product hook manifest may name, in the order of the tail's case.
NATIVE_HOOK_MODES = (
    GUARD_MODE,
    "agy-pending-orders",
    "agy-hook",
    "agy-stop-hook",
    "agy-pretool-hook",
    "claude-hook",
    "claude-stop-hook",
    "codex-pre-tool-use",
    "codex-post-tool-use",
    "codex-user-prompt-submit",
)
# $0 of the generated command, so the contract version shows in process listings.
NATIVE_HOOK_NAME = "lu-machinery-hook-v1"
_RESOLVERS_FILE = "lib/project_interpreter.sh"
_RESOLVERS_BEGIN = "# LU_HOOK_RESOLVERS_BEGIN"
_RESOLVERS_END = "# LU_HOOK_RESOLVERS_END"
# Runs after the resolver block, with the mode as $1. A bootstrap failure answers
# in the mode's native shape: AGY Stop continues, other AGY entries deny, Claude
# Stop blocks, Claude SessionStart/UserPromptSubmit stops, Codex exits 2. Once
# the context resolves, the installed entry replaces this shell, so its own
# output and exit status are the hook's.
_HOOK_TAIL = r"""_lu_hook_fail() {
    cat >/dev/null 2>&1
    printf '%s\n' 'HOOK-BOOTSTRAP-FAILED: product root, shared state, interpreter or machinery unavailable.' >&2
    case "$1" in
        agy-stop-hook) printf '%s\n' '{"decision":"continue","reason":"HOOK-BOOTSTRAP-FAILED: hook context unavailable."}' ;;
        agy-*) printf '%s\n' '{"decision":"deny","reason":"HOOK-BOOTSTRAP-FAILED: hook context unavailable."}' ;;
        claude-stop-hook) printf '%s\n' '{"decision":"block","reason":"HOOK-BOOTSTRAP-FAILED: hook context unavailable."}' ;;
        claude-hook) printf '%s\n' '{"continue":false,"stopReason":"HOOK-BOOTSTRAP-FAILED: hook context unavailable."}' ;;
        *) exit 2 ;;
    esac
    exit 0
}
_lu_hook_mode="$1"
project_hook_context_resolve 2>/dev/null || _lu_hook_fail "$_lu_hook_mode"
case "$_lu_hook_mode" in
    agy-secret-print)
        "$LEARN_UKRAINIAN_PYTHON" -I -m lu_machinery.agent_runtime.secret_print_hook --harness agy \
            || _lu_hook_fail "$_lu_hook_mode"
        exit 0 ;;
    agy-pending-orders) _lu_hook_entry=agy_hooks/pending_orders_inject.sh; set -- ;;
    agy-hook|agy-stop-hook|agy-pretool-hook|claude-hook|claude-stop-hook)
        _lu_hook_entry=agy_hooks/driver_state_inject.sh; set -- "$_lu_hook_mode" ;;
    codex-pre-tool-use|codex-post-tool-use|codex-user-prompt-submit)
        _lu_hook_entry=agent_runtime/codex_hook_entry.sh; set -- "${_lu_hook_mode#codex-}" ;;
    *) _lu_hook_fail "$_lu_hook_mode" ;;
esac
_lu_hook_entry="$("$LEARN_UKRAINIAN_PYTHON" -I -c 'import sys
from lu_machinery.common.repo_root import machinery_path
print(machinery_path(sys.argv[1]))' "$_lu_hook_entry" </dev/null 2>/dev/null)" || _lu_hook_fail "$_lu_hook_mode"
[ -f "$_lu_hook_entry" ] || _lu_hook_fail "$_lu_hook_mode"
shopt -s execfail
exec /bin/bash "$_lu_hook_entry" "$@"
_lu_hook_fail "$_lu_hook_mode"
"""
# The shared primary-checkout write guard, by its product-checkout path. AGY reads the
# guard's toolCall decision from stdout; the guard file protects the checkout that owns it.
PRIMARY_GUARD_NAME = "primary-checkout-write-guard"
PRIMARY_GUARD_ENTRY = Path("agents_extensions/shared/hooks/guard-primary-checkout-write.py")


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


def _hook_resolvers() -> str:
    """The marked resolver block of the packaged shell library, read as data."""
    try:
        lines = machinery_path(_RESOLVERS_FILE).read_text(encoding="utf-8").splitlines(keepends=True)
    except (OSError, UnicodeError):
        raise AgyHookConfigError("hook_resolvers_unavailable") from None
    begins = [index for index, line in enumerate(lines) if line.rstrip("\n") == _RESOLVERS_BEGIN]
    ends = [index for index, line in enumerate(lines) if line.rstrip("\n") == _RESOLVERS_END]
    if len(begins) != 1 or len(ends) != 1 or ends[0] < begins[0]:
        raise AgyHookConfigError("hook_resolvers_unmarked")
    return "".join(lines[begins[0] + 1 : ends[0]])


def native_hook_command(mode: str) -> str:
    """The one native hook command for ``mode``; every product manifest uses these bytes.

    ``/bin/bash -c <body> lu-machinery-hook-v1 <mode>``, serialized with ``shlex.join``.
    The body is ``set -u``, the packaged resolver block and a fixed tail. It holds no
    host path: it resolves the product, shared-state anchor and interpreter by the
    shell rule before any Python starts, then runs the installed entry for ``mode``
    under ``-I``. Validators compare these exact bytes, never an equivalent argv.
    """
    if mode not in NATIVE_HOOK_MODES:
        raise AgyHookConfigError("unsupported_hook_mode")
    body = "set -u\n" + _hook_resolvers() + _HOOK_TAIL
    return shlex.join(["/bin/bash", "-c", body, NATIVE_HOOK_NAME, mode])


def _check_file(path: Path, command: str) -> None:
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
    # Byte equality: a differently quoted equivalent could expand before argv forms.
    if hook.get("type") != "command" or hook.get("command") != command:
        raise AgyHookConfigError("invalid_command")


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
        command = native_hook_command(GUARD_MODE)
        checked = 0
        for path in locations:
            try:
                path.lstat()
            except FileNotFoundError:
                continue
            _check_file(path, command)
            checked += 1
        if not checked:
            raise AgyHookConfigError("missing_file")
    except AgyHookConfigError as exc:
        return HookConfigResult("REFUSE", exc.reason)
    except (OSError, ValueError):
        return HookConfigResult("REFUSE", "unresolved_path")
    return HookConfigResult("PASS", "guard_registered")


def guard_registration(*, repo_root: Path = ROOT) -> dict:
    """The tracked overlay's guard, with the one generated guard command.

    The overlay is product configuration, read from the product checkout ``product_root``
    selects (C-4746); its other hook metadata is kept. The command is
    ``native_hook_command(GUARD_MODE)``, the exact bytes ``_check_file`` accepts, so the
    hook resolves its interpreter by the shared shell rule, never from this process.
    """
    guard = copy.deepcopy(_read_config(product_root() / "agents_extensions/agy/hooks.json")[GUARD_NAME])
    guard["PreToolUse"][0]["hooks"][0]["command"] = native_hook_command(GUARD_MODE)
    return guard


def primary_guard_registration(*, repo_root: Path = ROOT) -> dict:
    """The overlay's primary-checkout write guard with absolute interpreter and guard paths.

    The guard is product configuration from ``product_root``; its interpreter is the
    machinery checkout's, as for ``guard_registration``.
    """
    root = product_root()
    guard: dict = copy.deepcopy(_read_config(root / "agents_extensions/agy/hooks.json")[PRIMARY_GUARD_NAME])
    guard["PreToolUse"][0]["hooks"][0]["command"] = shlex.join(
        [str(project_interpreter(repo_root)), str((root / PRIMARY_GUARD_ENTRY).absolute())]
    )
    return guard


def require_dispatch_guards(worktree: Path, home: Path) -> None:
    """Provision and verify both guards before a dispatched workspace-write AGY run.

    That run skips AGY's permission prompts on the host, so the primary-checkout write
    guard is its boundary on the primary checkout. Missing members are merged; an existing
    primary-guard member must equal the absolute registration exactly, and the secret
    guard passes the same gate as every other launch.
    """
    try:
        install_worktree_guard(worktree)
        result = check_hook_config(hook_locations(worktree, home))
        if result.passed:
            registered = _read_config(worktree / ".agents/hooks.json").get(PRIMARY_GUARD_NAME)
            if registered != primary_guard_registration():
                result = HookConfigResult("REFUSE", "primary_guard_mismatch")
            elif not (product_root() / PRIMARY_GUARD_ENTRY).is_file():
                result = HookConfigResult("REFUSE", "missing_primary_guard_script")
    except AgyHookConfigError:
        raise
    except (OSError, ValueError):
        raise AgyHookConfigError("install_failed") from None
    if not result.passed:
        raise AgyHookConfigError(result.reason)


def install_worktree_guard(cwd: Path, *, repo_root: Path = ROOT) -> None:
    """Merge only missing guards into a dispatch workspace; never write homes."""
    target = cwd.resolve(strict=True)
    primary = main_checkout_root(target).resolve(strict=True)
    dispatch = (primary / ".worktrees/dispatch").resolve(strict=True) if primary != target else primary
    if ".." in cwd.parts or primary == target or target == dispatch or not target.is_relative_to(dispatch):
        raise AgyHookConfigError("install_requires_dispatch_worktree")
    provision_workspace_guard(cwd)


def provision_workspace_guard(cwd: Path, *, repo_root: Path = ROOT) -> None:
    """Explicitly provision a caller-created workspace, never an ordinary HOME.

    The caller owns the directory and its lifecycle. Walk real directories and
    atomically merge a missing guard, retaining unrelated bytes. Published files
    have mode 0600. This is not an implicit repair of existing gate candidates: an
    existing member, even a disabled or invalid one, is kept as written.
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
        missing = {
            name: register(repo_root=repo_root)
            for name, register in ((GUARD_NAME, guard_registration), (PRIMARY_GUARD_NAME, primary_guard_registration))
            if name not in data  # Preserve explicitly disabled or invalid user wiring.
        }
        if not missing:
            return
        # Insert only the new members, keeping unrelated hook bytes unchanged.
        end = original.rindex("}")
        member = json.dumps(missing, indent=2)[1:-1]
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
    ``cwd`` is the invocation boundary: missing product and shared-state roots are
    configured from it by the shared shell rule before anything is provisioned, so
    the provider and its hooks inherit them. Configured roots are kept; invalid
    ones refuse.
    """
    try:
        configure_native_hook_roots(cwd)
    except (OSError, ValueError):
        raise AgyHookConfigError("hook_context_unavailable") from None
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
    # Named canonically, under the unresolved name of the package directory this file is in.
    entry = f"-m {Path(__file__).absolute().parents[1].name}.agent_runtime.agy_hook_config"
    parser = argparse.ArgumentParser(
        description="Read effective AGY hooks files and refuse missing no-print wiring.",
        epilog=f"Example: .venv/bin/python {entry} --cwd .\n"
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
