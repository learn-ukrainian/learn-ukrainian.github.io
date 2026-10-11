"""Install or verify the native Kimi Bash no-print hook without rewriting TOML."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import stat
import sys
import tempfile
import time
import tomllib
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.repo_root import main_checkout_root, project_interpreter

BEGIN = b"# BEGIN learn-ukrainian secret-print hook v1"
END = b"# END learn-ukrainian secret-print hook v1"
# Native externalHooks/internal/types.ts and configSection.ts.
EVENTS = frozenset(
    {
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "PermissionRequest",
        "PermissionResult",
        "UserPromptSubmit",
        "UserPromptQueued",
        "TurnStarted",
        "Stop",
        "StopFailure",
        "Interrupt",
        "SessionStart",
        "SessionEnd",
        "SessionHeartbeat",
        "SubagentStart",
        "SubagentStop",
        "TaskStarted",
        "PreCompact",
        "PostCompact",
        "Notification",
    }
)


class RegistrationError(RuntimeError):
    """Privacy-safe cause class, optionally with a source line number."""

    def __init__(self, cause: str, line: int | None = None):
        super().__init__(cause + (f" line {line}" if line is not None else ""))


def config_path(home_mode: str, env: Mapping[str, str] | None = None) -> Path:
    """Mirror launcher inheritance or the sanitized worker's HOME only."""
    env = os.environ if env is None else env
    home = env.get("HOME")
    if not home:
        raise RegistrationError("home_unavailable")
    if home_mode not in {"launcher", "worker"}:
        raise RegistrationError("home_mode_invalid")
    override = env.get("KIMI_CODE_HOME") if home_mode == "launcher" else None
    return (Path(override) if override else Path(home) / ".kimi-code") / "config.toml"


def managed_block() -> bytes:
    """Bind both command paths to the primary checkout, never this worktree."""
    primary = main_checkout_root(Path(__file__).resolve().parents[2])
    command = " ".join(
        (
            shlex.quote(str(project_interpreter(primary))),
            shlex.quote(str(primary / "scripts/agent_runtime/secret_print_hook.py")),
            "--harness kimi || exit 2",
        )
    )
    return b"\n".join(
        (
            BEGIN,
            b"[[hooks]]",
            b'event = "PreToolUse"',
            b'matcher = "^Bash$"',
            b"timeout = 10",
            ("command = " + json.dumps(command, ensure_ascii=False)).encode(),
            END,
            b"",
        )
    )


def _hook_line(text: str, index: int) -> int:
    # Parse prefixes rather than mistaking a [[hooks]] inside a TOML string
    # for a table. Only used on refusal, never on the normal startup path.
    prefix = ""
    for line, fragment in enumerate(text.splitlines(keepends=True), 1):
        prefix += fragment
        try:
            hooks = tomllib.loads(prefix).get("hooks")
        except tomllib.TOMLDecodeError:
            continue
        if isinstance(hooks, list) and len(hooks) > index:
            return line
    return 1


def validate_config(data: bytes) -> None:
    """Validate every hook against the strict native HookDefSchema."""
    try:
        text = data.decode("utf-8")
    except UnicodeError:
        raise RegistrationError("toml_encoding_invalid", 1) from None
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        match = re.search(r"at line (\d+)", str(exc))
        line = int(match[1]) if match else text.count("\n") + 1
        raise RegistrationError("toml_invalid", line) from None
    hooks = parsed.get("hooks", [])
    if not isinstance(hooks, list):
        raise RegistrationError("hooks_schema_invalid", 1)
    for index, hook in enumerate(hooks):
        valid = (
            isinstance(hook, dict)
            and set(hook) <= {"event", "matcher", "command", "timeout"}
            and isinstance(hook.get("event"), str)
            and hook["event"] in EVENTS
            and isinstance(hook.get("command"), str)
            and len(hook["command"]) >= 1
            and ("matcher" not in hook or isinstance(hook["matcher"], str))
            and (
                "timeout" not in hook
                or (
                    type(hook["timeout"]) in (int, float)
                    and 1 <= hook["timeout"] <= 600
                    and int(hook["timeout"]) == hook["timeout"]
                )
            )
        )
        if not valid:
            raise RegistrationError("hooks_schema_invalid", _hook_line(text, index))


def _block_span(data: bytes) -> tuple[int, int] | None:
    starts = list(re.finditer(rb"(?m)^" + re.escape(BEGIN) + rb"\r?$(?:\n)?", data))
    ends = list(re.finditer(rb"(?m)^" + re.escape(END) + rb"\r?$(?:\n)?", data))
    if not starts and not ends and BEGIN not in data and END not in data:
        return None
    if len(starts) > 1 or len(ends) > 1:
        raise RegistrationError("managed_block_duplicate")
    if (
        len(starts) != 1
        or len(ends) != 1
        or starts[0].end() > ends[0].start()
        or data.count(BEGIN) != 1
        or data.count(END) != 1
    ):
        raise RegistrationError("managed_block_malformed")
    # A marker in a multiline TOML string is data, never a hook block.
    try:
        tomllib.loads(data[: starts[0].start()].decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeError):
        raise RegistrationError("managed_block_malformed") from None
    return starts[0].start(), ends[0].end()


def _updated(data: bytes, block: bytes) -> bytes:
    span = _block_span(data)
    if span is not None:
        start, end = span
        return data[:start] + block + data[end:]
    separator = b"\n" if data and not data.endswith(b"\n") else b""
    return data + separator + block


def verify(home_mode: str, env: Mapping[str, str] | None = None) -> None:
    """Read-only preflight; report no config values or paths on refusal."""
    path = config_path(home_mode, env)
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        raise RegistrationError("registration_absent") from None
    except OSError:
        raise RegistrationError("config_unreadable") from None
    validate_config(data)
    span = _block_span(data)
    if span is None:
        raise RegistrationError("registration_absent")
    try:
        block = managed_block()
    except OSError:
        raise RegistrationError("interpreter_unavailable") from None
    if data[span[0] : span[1]] != block:
        raise RegistrationError("registration_stale")


def _mkdir_private(path: Path) -> None:
    if not path.exists():
        _mkdir_private(path.parent)
        path.mkdir(mode=0o700, exist_ok=True)


@contextmanager
def _config_lock(path: Path) -> Iterator[None]:
    # Keep the same exclusive-create protocol as Entire's acquireConfigLock.
    for _ in range(100):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            try:
                if time.time() - path.stat().st_mtime > 60:
                    path.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                pass
            time.sleep(0.020)
            continue
        try:
            with os.fdopen(fd, "w") as lock:
                lock.write(f"{os.getpid()}\n")
            yield
        finally:
            path.unlink(missing_ok=True)
        return
    raise RegistrationError("config_lock_timeout")


def ensure(home_mode: str, env: Mapping[str, str] | None = None) -> None:
    """Validate and atomically splice one managed block under Entire's lock."""
    path = config_path(home_mode, env)
    try:
        _mkdir_private(path.parent)
        with _config_lock(Path(str(path) + ".entire-kimi.lock")):
            try:
                data = path.read_bytes()
                mode = stat.S_IMODE(path.stat().st_mode)
            except FileNotFoundError:
                data, mode = b"", 0o600
            validate_config(data)
            updated = _updated(data, managed_block())
            validate_config(updated)
            if updated == data:
                return
            fd, temporary = tempfile.mkstemp(prefix=".kimi-hook-", dir=path.parent)
            try:
                with os.fdopen(fd, "wb") as output:
                    os.fchmod(output.fileno(), mode)
                    output.write(updated)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, path)
            finally:
                Path(temporary).unlink(missing_ok=True)
    except OSError:
        raise RegistrationError("registration_io_failed") from None


def main(argv: list[str] | None = None) -> int:
    epilog = (
        "Examples:\n"
        "  .venv/bin/python -m scripts.agent_runtime.kimi_hook_registration ensure --home-mode launcher\n"
        "  .venv/bin/python -m scripts.agent_runtime.kimi_hook_registration verify --home-mode worker\n"
        "Outputs: ensure updates config.toml in the selected Kimi home; verify writes nothing.\n"
        "Exit codes: 0 installed/verified; 1 refused (cause class only); 2 invalid CLI arguments.\n"
        "Related: npm run agents:deploy; docs/agent-runtime-guide.md."
    )
    parser = argparse.ArgumentParser(
        description="Install or verify the shared no-print hook for native Kimi Bash.\n"
        "Use ensure during deployment; session startup must use verify only.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(
        dest="command", required=True, help="ensure installs; verify checks without writes"
    )
    for name in ("ensure", "verify"):
        sub = commands.add_parser(
            name,
            help=f"{name} the managed registration",
            epilog=epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=f"{name.capitalize()} the native Kimi hook registration.\n"
            "Use launcher for inherited home; worker for sanitized HOME.",
        )
        sub.add_argument(
            "--home-mode",
            required=True,
            choices=("launcher", "worker"),
            help="launcher honors KIMI_CODE_HOME; worker uses HOME/.kimi-code (e.g. worker; required)",
        )
    args = parser.parse_args(argv)
    try:
        (ensure if args.command == "ensure" else verify)(args.home_mode)
    except RegistrationError as exc:
        print(f"kimi_hook_registration: {exc}", file=sys.stderr)
        return 1
    print(f"kimi_hook_registration: {args.command} ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
