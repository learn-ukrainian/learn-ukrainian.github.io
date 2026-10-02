"""CursorAdapter stops the worker server its own CLI leaves behind (#9534).

The fake worker server is a real process shaped like the Cursor one: its last
argument is ``worker-server``, its ``cwd`` is the workspace's Git root, it
serves HTTP on the Unix socket named by ``AGENT_CLI_SOCKET_PATH`` and its
environment carries the ``LU_CURSOR_INVOCATION_ID`` of the CLI that started
it. Every request it receives is appended to a log, so a test can prove a
server was never contacted.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters import cursor as cursor_mod
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.cursor import (
    CursorAdapter,
    WorkerServer,
    cursor_workspace_root,
    find_cursor_worker_servers,
    stop_cursor_worker_servers,
)

_FAKE_SERVER = textwrap.dedent(
    """
    import http.server, os, socketserver, sys

    path = os.environ["AGENT_CLI_SOCKET_PATH"]
    log = os.environ["FAKE_REQUEST_LOG"]
    ignore_kill = os.environ.get("FAKE_IGNORE_KILL") == "1"

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            with open(log, "a", encoding="utf-8") as handle:
                handle.write(self.path + "\\n")
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")
            if self.path == "/kill" and not ignore_kill:
                os.unlink(path)
                os._exit(0)

        def log_message(self, *args):
            pass

    with socketserver.UnixStreamServer(path, Handler) as server:
        server.serve_forever()
    """
)

_MARKER = "a" * 32
_OTHER_MARKER = "b" * 32


@pytest.fixture
def short_dir() -> Iterator[Path]:
    """A directory short enough for a Unix socket path (108 bytes)."""
    path = Path(tempfile.mkdtemp(prefix="cws", dir="/tmp" if os.access("/tmp", os.W_OK) else None))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def servers() -> Iterator[list[subprocess.Popen[bytes]]]:
    started: list[subprocess.Popen[bytes]] = []
    try:
        yield started
    finally:
        for proc in started:
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=5)


def _start_server(
    servers: list[subprocess.Popen[bytes]],
    short_dir: Path,
    cwd: Path,
    *,
    marker: str | None = _MARKER,
    name: str = "worker.sock",
    listen: bool = True,
    ignore_kill: bool = False,
) -> tuple[subprocess.Popen[bytes], Path, Path]:
    """Start a fake worker server; returns the process, its socket and its request log."""
    script = short_dir / "fake_worker_server.py"
    script.write_text(_FAKE_SERVER, encoding="utf-8")
    socket_path = short_dir / name
    request_log = short_dir / f"{name}.{len(servers)}.log"
    request_log.touch()
    env = {**os.environ, "AGENT_CLI_SOCKET_PATH": str(socket_path), "FAKE_REQUEST_LOG": str(request_log)}
    env.pop("LU_CURSOR_INVOCATION_ID", None)
    if marker is not None:
        env["LU_CURSOR_INVOCATION_ID"] = marker
    if ignore_kill:
        env["FAKE_IGNORE_KILL"] = "1"
    argv = [sys.executable, str(script), "worker-server"]
    if not listen:
        # Same shape, but nothing listens on the socket.
        argv = [sys.executable, "-c", "import time; time.sleep(60)", "worker-server"]
    proc = subprocess.Popen(argv, cwd=cwd, env=env, start_new_session=True)
    servers.append(proc)
    if listen:
        deadline = time.monotonic() + 10
        while not socket_path.exists():
            assert proc.poll() is None, "fake worker server exited during startup"
            assert time.monotonic() < deadline, "fake worker server never listened"
            time.sleep(0.02)
    return proc, socket_path, request_log


def _start_cursor_cli(
    servers: list[subprocess.Popen[bytes]], short_dir: Path, workspace: Path, *, marker: str | None
) -> subprocess.Popen[bytes]:
    """A process shaped like a running cursor-agent CLI working on ``workspace``."""
    install = short_dir / "install"
    install.mkdir(exist_ok=True)
    (install / "cursor-agent").write_text("#!/bin/sh\n", encoding="utf-8")
    (install / "index.js").write_text("", encoding="utf-8")
    env = dict(os.environ)
    env.pop("LU_CURSOR_INVOCATION_ID", None)
    if marker is not None:
        env["LU_CURSOR_INVOCATION_ID"] = marker
    argv = [
        sys.executable,
        "-c",
        "import time; time.sleep(60)",
        str(install / "index.js"),
        "-p",
        "--workspace",
        str(workspace),
    ]
    proc = subprocess.Popen(argv, cwd=short_dir, env=env, start_new_session=True)
    servers.append(proc)
    deadline = time.monotonic() + 10
    while b"--workspace" not in Path(f"/proc/{proc.pid}/cmdline").read_bytes():
        assert time.monotonic() < deadline, "fake cursor-agent CLI never started"
        time.sleep(0.02)
    return proc


def _workspace(tmp_path: Path, name: str = "workspace") -> Path:
    """A workspace that is its own Git root, as a dispatch worktree is."""
    path = tmp_path / name
    (path / ".git").mkdir(parents=True)
    return path


def _ticks_before_start() -> int:
    ticks = cursor_mod._boot_ticks()
    assert ticks is not None
    return ticks


def _stop(workspace: Path, started_ticks: int, **kwargs) -> dict[int, bool]:
    return stop_cursor_worker_servers(workspace, invocation_id=_MARKER, started_ticks=started_ticks, **kwargs)


def test_build_invocation_gives_each_run_its_own_marker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cursor_mod, "resolve_cursor_agent_binary", lambda: "/usr/local/bin/cursor-agent")
    adapter = CursorAdapter()
    override = _workspace(tmp_path, "override")
    before = _ticks_before_start()

    def build() -> InvocationPlan:
        return adapter.build_invocation(
            prompt="review",
            mode="read-only",
            cwd=tmp_path,
            model="grok-4.7",
            task_id="t",
            session_id=None,
            tool_config={"cursor_workspace": str(override)},
        )

    first, second = build(), build()

    assert first.metadata["cursor_workspace"] == str(override)
    assert first.cmd[first.cmd.index("--workspace") + 1] == str(override)
    assert first.env_overrides["LU_CURSOR_INVOCATION_ID"] == first.metadata["cursor_invocation_id"]
    assert len(first.metadata["cursor_invocation_id"]) == 32
    assert first.metadata["cursor_invocation_id"] != second.metadata["cursor_invocation_id"]
    assert before <= first.metadata["cursor_invocation_started_ticks"] <= _ticks_before_start()


def test_cleanup_invocation_stops_this_invocations_worker_server(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]], monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(cursor_mod, "resolve_cursor_agent_binary", lambda: "/usr/local/bin/cursor-agent")
    adapter = CursorAdapter()
    workspace = _workspace(tmp_path)
    plan = adapter.build_invocation(
        prompt="review",
        mode="read-only",
        cwd=workspace,
        model="grok-4.7",
        task_id="t",
        session_id=None,
        tool_config=None,
    )
    marker = plan.env_overrides["LU_CURSOR_INVOCATION_ID"]
    proc, socket_path, request_log = _start_server(servers, short_dir, workspace, marker=marker)

    found = find_cursor_worker_servers(
        workspace, invocation_id=marker, started_ticks=plan.metadata["cursor_invocation_started_ticks"]
    )
    assert [(server.pid, server.socket_path) for server in found] == [(proc.pid, str(socket_path))]
    adapter.cleanup_invocation(plan)

    assert proc.wait(timeout=5) == 0
    assert not socket_path.exists()
    assert request_log.read_text(encoding="utf-8") == "/kill\n"


def test_concurrent_sessions_servers_are_never_contacted(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]
):
    """Same workspace, three servers: only the one carrying this run's marker is ours."""
    workspace = _workspace(tmp_path)
    started = _ticks_before_start()
    ours, _, ours_log = _start_server(servers, short_dir, workspace, name="a.sock")
    theirs, theirs_socket, theirs_log = _start_server(
        servers, short_dir, workspace, name="b.sock", marker=_OTHER_MARKER
    )
    unmarked, unmarked_socket, unmarked_log = _start_server(servers, short_dir, workspace, name="c.sock", marker=None)

    assert _stop(workspace, started) == {ours.pid: True}
    assert ours_log.read_text(encoding="utf-8") == "/kill\n"
    for proc, socket_path, request_log in (
        (theirs, theirs_socket, theirs_log),
        (unmarked, unmarked_socket, unmarked_log),
    ):
        assert proc.poll() is None
        assert socket_path.exists()
        assert request_log.read_text(encoding="utf-8") == ""


def test_a_server_older_than_the_invocation_is_not_its(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]
):
    workspace = _workspace(tmp_path)
    older, _, request_log = _start_server(servers, short_dir, workspace)
    time.sleep(0.05)
    started = _ticks_before_start()

    assert _stop(workspace, started) == {}
    assert older.poll() is None
    assert request_log.read_text(encoding="utf-8") == ""


def test_another_cursor_cli_on_the_same_root_keeps_the_server(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]
):
    workspace = _workspace(tmp_path)
    started = _ticks_before_start()
    ours, socket_path, request_log = _start_server(servers, short_dir, workspace)
    _start_cursor_cli(servers, short_dir, workspace / "sub", marker=_OTHER_MARKER)

    assert _stop(workspace, started) == {ours.pid: False}
    assert ours.poll() is None
    assert socket_path.exists()
    assert request_log.read_text(encoding="utf-8") == ""


def test_this_runs_cli_or_one_on_another_root_does_not_keep_the_server(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]
):
    workspace = _workspace(tmp_path)
    started = _ticks_before_start()
    ours, _, _ = _start_server(servers, short_dir, workspace)
    _start_cursor_cli(servers, short_dir, workspace, marker=_MARKER)
    _start_cursor_cli(servers, short_dir, _workspace(tmp_path, "elsewhere"), marker=_OTHER_MARKER)

    assert _stop(workspace, started) == {ours.pid: True}


def test_a_replaced_socket_gets_nothing(tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]):
    """Another process now listens on the socket path this run's server was given."""
    workspace = _workspace(tmp_path)
    started = _ticks_before_start()
    ours, socket_path, ours_log = _start_server(servers, short_dir, workspace)
    socket_path.unlink()
    impostor, _, impostor_log = _start_server(servers, short_dir, _workspace(tmp_path, "impostor"), marker=None)

    assert _stop(workspace, started) == {ours.pid: False}
    assert ours.poll() is None
    assert impostor.poll() is None
    assert ours_log.read_text(encoding="utf-8") == ""
    assert impostor_log.read_text(encoding="utf-8") == ""


def test_a_reused_pid_gets_nothing(tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]):
    """The pid that was found now has another start time: it is another process."""
    workspace = _workspace(tmp_path)
    started = _ticks_before_start()
    proc, socket_path, request_log = _start_server(servers, short_dir, workspace)
    (found,) = find_cursor_worker_servers(workspace, invocation_id=_MARKER, started_ticks=started)
    reused = WorkerServer(found.pid, found.start_ticks + 1, found.socket_path)

    assert cursor_mod._stop_worker_server(reused, proc_root=Path("/proc"), timeout_s=0.5) is True
    assert proc.poll() is None
    assert socket_path.exists()
    assert request_log.read_text(encoding="utf-8") == ""


def test_a_pid_reused_while_connecting_gets_nothing(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]], monkeypatch: pytest.MonkeyPatch
):
    """Identity is rechecked after the connection is made and before the request is sent."""
    workspace = _workspace(tmp_path)
    started = _ticks_before_start()
    proc, _, request_log = _start_server(servers, short_dir, workspace)
    (found,) = find_cursor_worker_servers(workspace, invocation_id=_MARKER, started_ticks=started)
    checks = iter([True, False])
    monkeypatch.setattr(cursor_mod, "_same_process", lambda entry, start_ticks: next(checks))

    assert cursor_mod._stop_worker_server(found, proc_root=Path("/proc"), timeout_s=0.5) is False
    assert proc.poll() is None
    assert request_log.read_text(encoding="utf-8") == ""


def test_a_subdirectory_workspace_finds_the_server_at_its_git_root(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]
):
    repo = _workspace(tmp_path, "repo")
    subdir = repo / "a" / "b"
    subdir.mkdir(parents=True)
    started = _ticks_before_start()
    ours, _, _ = _start_server(servers, short_dir, repo, name="a.sock")
    theirs, _, theirs_log = _start_server(servers, short_dir, repo, name="b.sock", marker=_OTHER_MARKER)

    assert _stop(subdir, started) == {ours.pid: True}
    assert theirs.poll() is None
    assert theirs_log.read_text(encoding="utf-8") == ""


def test_workspace_root_mirrors_the_cli(tmp_path: Path):
    plain = tmp_path / "plain"
    plain.mkdir()
    worktree = tmp_path / "worktree"
    (worktree / "deep").mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")

    assert cursor_workspace_root(worktree / "deep") == worktree
    assert cursor_workspace_root(worktree) == worktree
    if cursor_workspace_root(plain) != plain:
        # tmp_path itself sits inside a Git checkout; the walk found that root.
        assert (cursor_workspace_root(plain) / ".git").exists()


def test_stop_never_signals_a_server_that_does_not_answer(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]
):
    workspace = _workspace(tmp_path)
    started = _ticks_before_start()
    silent, _, _ = _start_server(servers, short_dir, workspace, listen=False)

    assert _stop(workspace, started, timeout_s=0.5) == {silent.pid: False}
    assert silent.poll() is None


def test_stop_reports_a_server_still_running_after_kill(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]
):
    workspace = _workspace(tmp_path)
    started = _ticks_before_start()
    stubborn, _, request_log = _start_server(servers, short_dir, workspace, ignore_kill=True)

    assert _stop(workspace, started, timeout_s=0.3) == {stubborn.pid: False}
    assert stubborn.poll() is None
    assert request_log.read_text(encoding="utf-8") == "/kill\n"


def test_cleanup_without_proven_ownership_contacts_nothing(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]
):
    adapter = CursorAdapter()
    workspace = _workspace(tmp_path)
    started = _ticks_before_start()
    proc, _, request_log = _start_server(servers, short_dir, workspace)

    adapter.cleanup_invocation(InvocationPlan(cmd=["cursor-agent"], cwd=tmp_path, stdin_payload="", output_file=None))
    for metadata in (
        {"cursor_workspace": str(workspace)},
        {"cursor_workspace": str(workspace), "cursor_invocation_id": _MARKER},
        {"cursor_workspace": str(workspace), "cursor_invocation_started_ticks": started},
        {"cursor_workspace": str(workspace), "cursor_invocation_id": _MARKER, "cursor_invocation_started_ticks": None},
    ):
        adapter.cleanup_invocation(InvocationPlan(cmd=["cursor-agent"], cwd=workspace, metadata=metadata))

    assert proc.poll() is None
    assert request_log.read_text(encoding="utf-8") == ""
