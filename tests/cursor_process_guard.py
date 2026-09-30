"""Hermetic Cursor execution and session-wide process leak checks (#9241).

The execution tripwire also installs in nested Python interpreters. PATH shims
cover nested shells; explicitly named installed targets are refused before spawn.
Process identities use PID and creation time, never parentage or cwd. Only
same-uid survivors carrying this session's token can fail the controller.
"""
from __future__ import annotations

import contextlib
import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psutil
import pytest

from tests import cursor_exec_tripwire as tripwire

PROCESS_NAMES = frozenset({
    "cursor-agent", "typescript-language-server", "tsserver", "tsserver.js",
    "typingsInstaller", "typingsInstaller.js",
})
_REAL_CURSOR_BINARY = shutil.which("cursor-agent") or shutil.which("agent")
REAL_TARGETS = frozenset(
    str(Path(target).resolve()) for name in ("cursor-agent", "agent")
    if (target := shutil.which(name))
)
REAL_ROOTS = (str(Path.home() / ".local/share/cursor-agent"),)
_DISPATCH_OR_CI = bool(os.environ.get("CI") or os.environ.get("LEARN_UKRAINIAN_DISPATCH_TASK_ID"))


def process_snapshot() -> dict[tuple[int, float], str]:
    """Snapshot live Cursor/LSP processes, including detached node workers."""
    found = {}
    for proc in psutil.process_iter():
        try:
            with proc.oneshot():
                if proc.status() == psutil.STATUS_ZOMBIE:
                    continue
                tokens = [proc.name(), *proc.cmdline()]
                matches = set().union(*(set(Path(token).parts) & PROCESS_NAMES for token in tokens))
                if matches:
                    found[(proc.pid, proc.create_time())] = sorted(matches)[0]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return found


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-real-cursor-smoke", action="store_true", default=False,
                     help="Explicitly run the bounded real Cursor smoke (refused in CI/dispatch).")


def pytest_sessionstart(session: pytest.Session) -> None:
    config = session.config
    if hasattr(config, "workerinput"):
        # Workers share the controller token, including replacement workers.
        token = config.workerinput[tripwire.SESSION_TOKEN_ENV]
    else:
        # Linux /proc start times use boot time rounded to whole seconds,
        # plus clock ticks. Wall time can be almost a second ahead of that
        # epoch. Compare in the same clock and resolution as create_time().
        ticks = os.sysconf("SC_CLK_TCK")
        config._cursor_process_started = psutil.boot_time() + int(
            time.clock_gettime(time.CLOCK_BOOTTIME) * ticks
        ) / ticks
        config._cursor_process_uid = os.getuid()
        config._cursor_process_baseline = process_snapshot()
        token = uuid.uuid4().hex
    config._cursor_process_token = token
    os.environ[tripwire.SESSION_TOKEN_ENV] = token
    tripwire.session_token = token
    tripwire.install(REAL_TARGETS, REAL_ROOTS, tripwire.child_directory)


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node) -> None:
    """Pass controller ownership explicitly; do not mint per-worker tokens."""
    node.workerinput[tripwire.SESSION_TOKEN_ENV] = node.config._cursor_process_token


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    tripwire.active = False
    if hasattr(session.config, "workerinput"):
        # The controller scans after all workers finish; their descendants carry
        # its token. Worker-local snapshots and exit overrides are unnecessary.
        return
    baseline = getattr(session.config, "_cursor_process_baseline", {})
    current = process_snapshot()
    survivors = []
    for pid, created in sorted(current.keys() - baseline.keys()):
        name = current[(pid, created)]
        try:
            proc = psutil.Process(pid)
            # Recheck identity so a PID reused since the snapshot cannot be
            # attributed using another process's environment.
            if proc.create_time() != created or created < session.config._cursor_process_started:
                continue
            if proc.uids().real != session.config._cursor_process_uid:
                print(f"cursor process guard: warning: {name} pid={pid}: different uid; ignored")
                continue
            if proc.environ().get(tripwire.SESSION_TOKEN_ENV) != session.config._cursor_process_token:
                print(f"cursor process guard: warning: {name} pid={pid}: no matching session token; ignored")
                continue
            if proc.status() != psutil.STATUS_ZOMBIE:
                survivors.append((pid, created))
        except psutil.NoSuchProcess:
            continue
        except psutil.AccessDenied:
            print(f"cursor process guard: warning: {name} pid={pid}: ownership/environment unreadable; ignored")
    if survivors:
        for pid, created in sorted(survivors):
            print(f"cursor process guard: survived session: {current[(pid, created)]} pid={pid}")
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
    else:
        print("cursor process guard: baseline diff empty (0 survivors attributed to this session)")


@pytest.fixture(scope="session", autouse=True)
def cursor_nested_execution_guard(tmp_path_factory):
    directory = tmp_path_factory.mktemp("cursor-exec-guard")
    shutil.copyfile(Path(tripwire.__file__), directory / "cursor_exec_tripwire.py")
    (directory / "sitecustomize.py").write_text(
        "import cursor_exec_tripwire\n"
        "cursor_exec_tripwire.install_from_environment()\n", encoding="utf-8",
    )
    tripwire.install(REAL_TARGETS, REAL_ROOTS, directory)
    try:
        yield
    finally:
        tripwire.child_directory = None


@pytest.fixture(scope="session")
def fake_cursor_bin(tmp_path_factory) -> Path:
    directory = tmp_path_factory.mktemp("fake-cursor")
    for name in ("cursor-agent", "agent"):
        binary = directory / name
        binary.write_text(
            f"#!{sys.executable}\nimport json, os, sys\n"
            "record = {'argv': sys.argv[1:], 'stdin': sys.stdin.read()}\n"
            "if os.environ.get('LU_TEST_CURSOR_LOG'):\n"
            "    with open(os.environ['LU_TEST_CURSOR_LOG'], 'a') as log:\n"
            "        log.write(json.dumps(record) + '\\n')\n"
            "print(json.dumps({'type': 'text', 'content': 'PONG'}))\n",
            encoding="utf-8",
        )
        binary.chmod(0o755)
    return directory


@pytest.fixture(autouse=True)
def default_fake_cursor(fake_cursor_bin, monkeypatch):
    inherited = [entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry]
    monkeypatch.setenv("PATH", os.pathsep.join([str(fake_cursor_bin), *inherited]))


@pytest.fixture
def real_cursor_binary(request):
    if not request.config.getoption("--run-real-cursor-smoke"):
        pytest.skip("real Cursor smoke requires --run-real-cursor-smoke")
    if _DISPATCH_OR_CI:
        pytest.fail("real Cursor smoke is forbidden in CI and dispatch workers", pytrace=False)
    if not REAL_TARGETS:
        pytest.fail("explicit real Cursor smoke requested but no binary was found", pytrace=False)
    tripwire.allow_real = True
    try:
        yield _REAL_CURSOR_BINARY
    finally:
        tripwire.allow_real = False


def bounded_cursor_smoke(binary: str, *, timeout: float = 60) -> subprocess.CompletedProcess:
    """Always reap the process group and any detached Cursor/LSP survivors."""
    token = uuid.uuid4().hex
    proc = subprocess.Popen(
        [binary, "-p", "--model", "auto", "--output-format", "stream-json", "--trust"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=True, env=dict(os.environ, LU_TEST_CURSOR_SMOKE_TOKEN=token),
    )
    with proc:
        try:
            stdout, stderr = proc.communicate("Reply with exactly: PONG", timeout=timeout)
            return subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)
        finally:
            # Use the original pgid even when the direct child has already exited.
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
            detached = []
            for child in psutil.process_iter():
                try:
                    if child.status() != psutil.STATUS_ZOMBIE and child.environ().get("LU_TEST_CURSOR_SMOKE_TOKEN") == token:
                        child.kill()
                        detached.append(child)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            _, alive = psutil.wait_procs(detached, timeout=5)
            if any(child.status() != psutil.STATUS_ZOMBIE for child in alive):
                raise RuntimeError("Cursor smoke teardown left a live process")
