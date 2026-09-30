"""Standard-library-only execution tripwire, inherited by nested Python (#9241)."""
from __future__ import annotations

import json
import os
import shlex
import shutil
import sys
from pathlib import Path

active = False
allow_real = False
real_targets: frozenset[str] = frozenset()
real_roots: tuple[str, ...] = ()
child_directory: Path | None = None
SESSION_TOKEN_ENV = "LU_TEST_CURSOR_SESSION_TOKEN"
session_token: str | None = None
_installed = False
_which = shutil.which  # Keep the safety lookup independent of adapter mocks.


def refuse_real_cursor(executable: object, argv: object, env: object = None) -> None:
    """Refuse installed aliases, symlinks, node entrypoints and shell commands."""
    if not active or allow_real:
        return
    environment = env if isinstance(env, dict) else os.environ
    tokens = [os.fsdecode(executable)]
    if isinstance(argv, (list, tuple)):
        tokens.extend(os.fsdecode(arg) for arg in argv)
    elif isinstance(argv, (str, bytes)):
        tokens.append(os.fsdecode(argv))
    for token in tokens:
        # Explicit install paths embedded in shell/Python commands are refused
        # before the nested interpreter can execute them.
        if any(target in token for target in real_targets) or any(root in token for root in real_roots):
            raise RuntimeError("cursor execution tripwire: installed Cursor target refused")
        try:
            lexer = shlex.shlex(token, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            lexer.commenters = ""
            words = list(lexer)
        except ValueError:
            words = [token]
        for word in words:
            candidate = _which(word, path=environment.get("PATH", os.defpath))
            if candidate and str(Path(candidate).resolve()) in real_targets:
                raise RuntimeError("cursor execution tripwire: installed Cursor alias refused")


def audit_exec(event: str, args: tuple) -> None:
    """Block installed targets and propagate the hook before exec reads env."""
    if event in {"subprocess.Popen", "os.exec", "os.posix_spawn"}:
        executable, argv = args[:2]
        env = args[3] if event == "subprocess.Popen" else args[2]
    elif event == "os.system":
        executable, argv, env = "/bin/sh", args[0], None
    else:
        return
    refuse_real_cursor(executable, argv, env)
    # Intentionally mutate the caller's env dict (or os.environ for env=None)
    # before spawn/exec reads it, including when a test supplies env={}.
    if active and session_token is not None:
        environment = env if env is not None else os.environ
        environment[SESSION_TOKEN_ENV] = session_token
    if active and not allow_real and child_directory is not None:
        environment = env if env is not None else os.environ
        environment["LU_TEST_CURSOR_TARGETS"] = json.dumps(sorted(real_targets))
        environment["LU_TEST_CURSOR_ROOTS"] = json.dumps(real_roots)
        entries = [entry for entry in environment.get("PYTHONPATH", "").split(os.pathsep) if entry]
        directory = str(child_directory)
        environment["PYTHONPATH"] = os.pathsep.join([directory, *[entry for entry in entries if entry != directory]])


def install(targets, roots, directory: Path | None) -> None:
    global active, real_targets, real_roots, child_directory, _installed
    active = True
    real_targets = frozenset(targets)
    real_roots = tuple(roots)
    child_directory = directory
    if not _installed:
        sys.addaudithook(audit_exec)
        _installed = True


def install_from_environment() -> None:
    global session_token
    session_token = os.environ.get(SESSION_TOKEN_ENV)
    install(json.loads(os.environ["LU_TEST_CURSOR_TARGETS"]),
            json.loads(os.environ["LU_TEST_CURSOR_ROOTS"]), Path(__file__).parent)
