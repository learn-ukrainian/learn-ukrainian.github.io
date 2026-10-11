"""Native hook registration, byte preservation and real shell decisions."""

from __future__ import annotations

import os
import shlex
import stat
import subprocess
import sys
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from scripts.agent_runtime import kimi_hook_registration as registration
from scripts.common.repo_root import main_checkout_root, project_interpreter

# Verbatim JSON.stringify(toHookInputData(...)) output from the installed
# externalHooks/internal/matchHooks.ts serializer, with runPreToolUse's fields.
DUMP_PAYLOAD = b'{"hook_event_name":"PreToolUse","session_id":"synthetic-session","cwd":".","client_type":"cli","tool_name":"Bash","tool_input":{"command":"env"},"tool_call_id":"synthetic-call"}'
BENIGN_PAYLOAD = b'{"hook_event_name":"PreToolUse","session_id":"synthetic-session","cwd":".","client_type":"cli","tool_name":"Bash","tool_input":{"command":"printf benign"},"tool_call_id":"synthetic-call"}'
ENTIRE = (
    b"# BEGIN learn-ukrainian Entire Kimi hooks v1 separator=existing\r\n"
    b'[[hooks]]\r\nevent = "SessionStart"\r\ncommand = "true"\r\ntimeout = 30\r\n'
    b"# END learn-ukrainian Entire Kimi hooks v1\r\n"
)


@pytest.fixture
def homes(tmp_path, monkeypatch):
    home = tmp_path / "home"
    launcher = tmp_path / "launcher home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("KIMI_CODE_HOME", str(launcher))
    return home, launcher


@pytest.mark.parametrize(
    "original",
    [
        b"",
        b'# comment\r\n[unrelated]\r\nvalue = "private fixture"',
        ENTIRE,
        b"# leading\r\n" + ENTIRE + b'[unrelated]\r\nvalue = "private fixture"',
    ],
)
def test_ensure_preserves_bytes_and_mode_and_is_idempotent(homes, original):
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    path.write_bytes(original)
    path.chmod(0o640)
    registration.ensure("launcher")
    first = path.read_bytes()
    assert first.startswith(original)
    assert (
        first == original + (b"\n" if original and not original.endswith(b"\n") else b"") + registration.managed_block()
    )
    assert stat.S_IMODE(path.stat().st_mode) == 0o640
    registration.ensure("launcher")
    assert path.read_bytes() == first
    registration.verify("launcher")
    assert first.count(registration.BEGIN) == 1


def test_empty_home_creation_is_private(homes):
    registration.ensure("worker")
    path = registration.config_path("worker")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.parent.parent.stat().st_mode) == 0o700
    registration.verify("worker")


def test_stale_block_replaced_in_place_with_suffix_intact(homes):
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    prefix, suffix = ENTIRE, b'\r\n[other]\r\nvalue = "unchanged"'
    stale = registration.managed_block().replace(b"timeout = 10", b"timeout = 11")
    path.write_bytes(prefix + stale + suffix)
    registration.ensure("launcher")
    assert path.read_bytes() == prefix + registration.managed_block() + suffix


@pytest.mark.parametrize(
    "bad",
    [
        b'[broken\nvalue = "private fixture"',
        b'[[hooks]]\nevent="Stop"\ncommand="private fixture"\ntimeout="30"\n',
        b'[[hooks]]\nevent="Stop"\ncommand="private fixture"\ntimeout=true\n',
        b'[[hooks]]\nevent="Stop"\ncommand="private fixture"\ntimeout=601\n',
        b'[[hooks]]\nevent="Stop"\ncommand="private fixture"\ntimeout=1.5\n',
        b'[[hooks]]\nevent="Stop"\ncommand=""\n',
        b'[[hooks]]\nevent="Other"\ncommand="private fixture"\n',
        b'[[hooks]]\nevent="Stop"\ncommand="private fixture"\nextra="private fixture"\n',
        b'[[hooks]]\nevent="Stop"\ncommand="private fixture"\nmatcher=1\n',
        b'hooks = "private fixture"\n',
        b'hooks = ["private fixture"]\n',
        b"\xff",
    ],
)
def test_invalid_document_or_unmanaged_entry_refuses_without_write(homes, bad):
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    # Invalid unmanaged entries must disable an otherwise correct registration.
    original = bad + (b"\n" if not bad.endswith(b"\n") else b"") + registration.managed_block()
    path.write_bytes(original)
    for action in (registration.ensure, registration.verify):
        with pytest.raises(registration.RegistrationError) as error:
            action("launcher")
        assert "line " in str(error.value)
        assert "private fixture" not in str(error.value)
        assert path.read_bytes() == original


@pytest.mark.parametrize(
    "change",
    [
        (b'event = "PreToolUse"', b'event = "Stop"'),
        (b'matcher = "^Bash$"', b'matcher = "Bash"'),
        (b"timeout = 10", b"timeout = 20"),
        (b"--harness kimi", b"--harness grok"),
    ],
)
def test_verify_refuses_stale_registration_read_only(homes, change):
    registration.ensure("launcher")
    path = registration.config_path("launcher")
    stale = path.read_bytes().replace(*change)
    path.write_bytes(stale)
    with pytest.raises(registration.RegistrationError, match="registration_stale"):
        registration.verify("launcher")
    assert path.read_bytes() == stale
    assert not Path(str(path) + ".entire-kimi.lock").exists()


@pytest.mark.parametrize("block", [b"", registration.BEGIN + b"\n", registration.END + b"\n"])
def test_absent_and_malformed_blocks(homes, block):
    path = registration.config_path("launcher")
    with pytest.raises(registration.RegistrationError, match="registration_absent"):
        registration.verify("launcher")
    path.parent.mkdir(parents=True)
    path.write_bytes(block)
    with pytest.raises(registration.RegistrationError):
        registration.verify("launcher")
    assert path.read_bytes() == block


def test_duplicate_block_refuses_both_actions(homes):
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    duplicate = registration.managed_block() * 2
    path.write_bytes(duplicate)
    for action in (registration.ensure, registration.verify):
        with pytest.raises(registration.RegistrationError, match="managed_block_duplicate"):
            action("launcher")
        assert path.read_bytes() == duplicate


def test_home_modes_do_not_cross_register(homes):
    home, launcher = homes
    registration.ensure("launcher")
    assert registration.config_path("launcher").parent == launcher
    assert registration.config_path("worker").parent == home / ".kimi-code"
    registration.verify("launcher")
    with pytest.raises(registration.RegistrationError, match="registration_absent"):
        registration.verify("worker")
    registration.ensure("worker")
    registration.verify("worker")
    for value in (None, ""):
        env = {"KIMI_CODE_HOME": str(launcher)}
        if value is not None:
            env["HOME"] = value
        for mode in ("launcher", "worker"):
            for action in (registration.ensure, registration.verify):
                with pytest.raises(registration.RegistrationError, match="home_unavailable"):
                    action(mode, env)
    with pytest.raises(registration.RegistrationError, match="home_mode_invalid"):
        registration.config_path("other")


def test_live_entire_lock_refuses_within_bound_without_writing(homes):
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    path.write_bytes(ENTIRE)
    lock = Path(str(path) + ".entire-kimi.lock")
    lock.write_text(f"{os.getpid()}\n")
    started = time.monotonic()
    with pytest.raises(registration.RegistrationError, match="config_lock_timeout"):
        registration.ensure("launcher")
    assert time.monotonic() - started < 5
    assert path.read_bytes() == ENTIRE
    assert lock.read_text() == f"{os.getpid()}\n"


def test_entire_stale_lock_is_recovered(homes):
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    lock = Path(str(path) + ".entire-kimi.lock")
    lock.write_text("0\n")
    os.utime(lock, (time.time() - 61, time.time() - 61))
    registration.ensure("launcher")
    registration.verify("launcher")
    assert not lock.exists()


def test_two_concurrent_ensure_processes_preserve_entire(homes):
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    path.write_bytes(ENTIRE)
    env = {"HOME": str(homes[0]), "KIMI_CODE_HOME": str(homes[1]), "PATH": os.defpath}

    def run():
        return subprocess.run(
            [sys.executable, "-m", "scripts.agent_runtime.kimi_hook_registration", "ensure", "--home-mode", "launcher"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run(), range(2)))
    assert [r.returncode for r in results] == [0, 0], [r.stderr for r in results]
    assert path.read_bytes() == ENTIRE + registration.managed_block()
    assert not Path(str(path) + ".entire-kimi.lock").exists()


@pytest.mark.parametrize("payload, expected", [(DUMP_PAYLOAD, 2), (BENIGN_PAYLOAD, 0)])
def test_registered_command_real_payload_blocks_or_allows(homes, payload, expected):
    registration.ensure("launcher")
    hook = tomllib.loads(registration.config_path("launcher").read_text())["hooks"][0]
    sentinel = "synthetic-value-must-not-appear"
    result = subprocess.run(
        hook["command"],
        shell=True,
        input=payload,
        capture_output=True,
        env={"HOME": str(homes[0]), "PATH": os.defpath, "SYNTHETIC_GUARD_VALUE": sentinel},
        timeout=10,
    )
    assert result.returncode == expected, result.stderr
    assert sentinel.encode() not in result.stdout + result.stderr
    assert result.stdout == b""
    assert hook["matcher"] == "^Bash$"
    assert hook["timeout"] == 10


@pytest.mark.parametrize("kind", ["missing", "crash", "signal"])
def test_shell_wrapper_maps_interpreter_failure_to_block(homes, tmp_path, kind):
    primary = main_checkout_root(Path(registration.__file__).resolve().parents[2])
    interpreter = shlex.quote(str(project_interpreter(primary)))
    stub = tmp_path / "interpreter stub"
    if kind != "missing":
        stub.write_text("#!/bin/sh\n" + ("kill -TERM $$\n" if kind == "signal" else "exit 17\n"))
        stub.chmod(0o700)
    command = tomllib.loads(registration.managed_block().decode())["hooks"][0]["command"]
    command = command.replace(interpreter, shlex.quote(str(stub)), 1)
    result = subprocess.run(
        command,
        shell=True,
        input=BENIGN_PAYLOAD,
        env={"HOME": str(homes[0]), "PATH": os.defpath},
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 2


def test_cli_help_and_privacy_safe_refusal(homes):
    args = [sys.executable, "-m", "scripts.agent_runtime.kimi_hook_registration"]
    env = {"HOME": str(homes[0]), "KIMI_CODE_HOME": str(homes[1]), "PATH": os.defpath}
    for sub in ([], ["ensure"], ["verify"]):
        result = subprocess.run([*args, *sub, "--help"], env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        for text in ("Examples:", "Outputs:", "Exit codes:", "Related:"):
            assert text in result.stdout
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    path.write_bytes(b'value = "private fixture"\n[broken')
    for action in ("ensure", "verify"):
        result = subprocess.run(
            [*args, action, "--home-mode", "launcher"], env=env, capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr == "kimi_hook_registration: toml_invalid line 2\n"


def test_markers_inside_multiline_string_are_never_registration(homes):
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    data = b"unrelated = '''\n" + registration.managed_block() + b"'''\n"
    path.write_bytes(data)
    for action in (registration.ensure, registration.verify):
        with pytest.raises(registration.RegistrationError, match="managed_block_malformed"):
            action("launcher")
        assert path.read_bytes() == data


def test_schema_line_number_ignores_headers_in_multiline_strings(homes):
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    data = (
        b"note = '''\n[[hooks]]\n'''\n"
        + registration.managed_block()
        + b'[[hooks]]\nevent="Stop"\ncommand="true"\ntimeout="30"\n'
    )
    path.write_bytes(data)
    with pytest.raises(registration.RegistrationError, match="hooks_schema_invalid line 11"):
        registration.ensure("launcher")
    assert path.read_bytes() == data


def test_integral_toml_number_matches_native_zod_integer(homes):
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    original = b'[[hooks]]\nevent="Stop"\ncommand="true"\ntimeout=30.0\n'
    path.write_bytes(original)
    registration.ensure("launcher")
    registration.verify("launcher")
    assert path.read_bytes() == original + registration.managed_block()


def test_io_refusals_are_privacy_safe_and_release_lock(homes, monkeypatch):
    registration.ensure("launcher")
    path = registration.config_path("launcher")
    original = path.read_bytes()
    with monkeypatch.context() as patch:

        def unreadable(*args, **kwargs):
            raise PermissionError("private fixture")

        patch.setattr(Path, "read_bytes", unreadable)
        with pytest.raises(registration.RegistrationError, match="config_unreadable"):
            registration.verify("launcher")
        with pytest.raises(registration.RegistrationError, match="registration_io_failed"):
            registration.ensure("launcher")
    assert path.read_bytes() == original
    assert not Path(str(path) + ".entire-kimi.lock").exists()
    with monkeypatch.context() as patch:

        def unavailable(*args, **kwargs):
            raise FileNotFoundError("private fixture")

        patch.setattr(registration, "project_interpreter", unavailable)
        with pytest.raises(registration.RegistrationError, match="interpreter_unavailable"):
            registration.verify("launcher")
        with pytest.raises(registration.RegistrationError, match="registration_io_failed"):
            registration.ensure("launcher")
    assert path.read_bytes() == original
    assert not Path(str(path) + ".entire-kimi.lock").exists()


def test_failed_atomic_replace_preserves_original_and_removes_temporary(homes, monkeypatch):
    path = registration.config_path("launcher")
    path.parent.mkdir(parents=True)
    path.write_bytes(ENTIRE)

    def unavailable(*args, **kwargs):
        raise PermissionError("private fixture")

    monkeypatch.setattr(registration.os, "replace", unavailable)
    with pytest.raises(registration.RegistrationError, match="registration_io_failed"):
        registration.ensure("launcher")
    assert path.read_bytes() == ENTIRE
    assert sorted(p.name for p in path.parent.iterdir()) == ["config.toml"]


def test_cli_exit_codes_and_safe_output(homes, capsys):
    assert registration.main(["ensure", "--home-mode", "launcher"]) == 0
    assert capsys.readouterr().out == "kimi_hook_registration: ensure ok\n"
    assert registration.main(["verify", "--home-mode", "launcher"]) == 0
    assert capsys.readouterr().out == "kimi_hook_registration: verify ok\n"
    path = registration.config_path("launcher")
    path.write_bytes(b'value = "private fixture"\n[broken')
    assert registration.main(["verify", "--home-mode", "launcher"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "kimi_hook_registration: toml_invalid line 2\n"


def test_command_uses_primary_checkout_paths(homes):
    primary = main_checkout_root(Path(registration.__file__).resolve().parents[2])
    command = tomllib.loads(registration.managed_block().decode())["hooks"][0]["command"]
    assert shlex.split(command) == [
        str(project_interpreter(primary)),
        str(primary / "scripts/agent_runtime/secret_print_hook.py"),
        "--harness", "kimi", "||", "exit", "2",
    ]
