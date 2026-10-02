"""CursorAdapter stops the worker server its CLI leaves behind (#9534).

The fake worker server is a real process shaped like the Cursor one: its last
argument is ``worker-server``, its ``cwd`` is the workspace, and it serves
HTTP on the Unix socket named by ``AGENT_CLI_SOCKET_PATH``.
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
    find_cursor_worker_servers,
    stop_cursor_worker_servers,
)

_FAKE_SERVER = textwrap.dedent(
    """
    import http.server, os, socketserver, sys

    path = os.environ["AGENT_CLI_SOCKET_PATH"]
    ignore_kill = os.environ.get("FAKE_IGNORE_KILL") == "1"

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
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


@pytest.fixture
def short_dir() -> Iterator[Path]:
    """A directory short enough for a Unix socket path (108 bytes)."""
    path = Path(tempfile.mkdtemp(prefix="cws", dir="/tmp"))
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
    workspace: Path,
    *,
    name: str = "worker.sock",
    listen: bool = True,
    ignore_kill: bool = False,
) -> tuple[subprocess.Popen[bytes], Path]:
    script = short_dir / "fake_worker_server.py"
    script.write_text(_FAKE_SERVER, encoding="utf-8")
    socket_path = short_dir / name
    env = {**os.environ, "AGENT_CLI_SOCKET_PATH": str(socket_path)}
    if ignore_kill:
        env["FAKE_IGNORE_KILL"] = "1"
    argv = [sys.executable, str(script), "worker-server"]
    if not listen:
        # Same shape, but nothing listens on the socket.
        argv = [sys.executable, "-c", "import time; time.sleep(60)", "worker-server"]
    proc = subprocess.Popen(argv, cwd=workspace, env=env, start_new_session=True)
    servers.append(proc)
    if listen:
        deadline = time.monotonic() + 10
        while not socket_path.exists():
            assert proc.poll() is None, "fake worker server exited during startup"
            assert time.monotonic() < deadline, "fake worker server never listened"
            time.sleep(0.02)
    return proc, socket_path


def _workspace(tmp_path: Path, name: str = "workspace") -> Path:
    path = tmp_path / name
    path.mkdir()
    return path


def test_build_invocation_keeps_the_workspace_for_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cursor_mod, "resolve_cursor_agent_binary", lambda: "/usr/local/bin/cursor-agent")
    adapter = CursorAdapter()
    override = _workspace(tmp_path, "override")
    plan = adapter.build_invocation(
        prompt="review",
        mode="read-only",
        cwd=tmp_path,
        model="grok-4.7",
        task_id="t",
        session_id=None,
        tool_config={"cursor_workspace": str(override)},
    )

    assert plan.metadata["cursor_workspace"] == str(override)
    assert plan.cmd[plan.cmd.index("--workspace") + 1] == str(override)


def test_cleanup_invocation_stops_this_workspaces_worker_server(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]], monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(cursor_mod, "resolve_cursor_agent_binary", lambda: "/usr/local/bin/cursor-agent")
    adapter = CursorAdapter()
    workspace = _workspace(tmp_path)
    proc, socket_path = _start_server(servers, short_dir, workspace)
    plan = adapter.build_invocation(
        prompt="review",
        mode="read-only",
        cwd=workspace,
        model="grok-4.7",
        task_id="t",
        session_id=None,
        tool_config=None,
    )

    assert [(pid, path) for pid, _start, path in find_cursor_worker_servers(workspace)] == [
        (proc.pid, str(socket_path))
    ]
    adapter.cleanup_invocation(plan)

    assert proc.wait(timeout=5) == 0
    assert not socket_path.exists()


def test_stop_reports_the_exit_and_leaves_other_workspaces_alone(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]
):
    workspace = _workspace(tmp_path)
    other = _workspace(tmp_path, "other")
    ours, _ = _start_server(servers, short_dir, workspace, name="a.sock")
    theirs, theirs_socket = _start_server(servers, short_dir, other, name="b.sock")

    assert stop_cursor_worker_servers(workspace) == {ours.pid: True}
    assert theirs.poll() is None
    assert theirs_socket.exists()


def test_stop_never_signals_a_server_that_does_not_answer(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]
):
    workspace = _workspace(tmp_path)
    silent, _ = _start_server(servers, short_dir, workspace, listen=False)

    assert stop_cursor_worker_servers(workspace, timeout_s=0.5) == {silent.pid: False}
    assert silent.poll() is None


def test_stop_reports_a_server_still_running_after_kill(
    tmp_path: Path, short_dir: Path, servers: list[subprocess.Popen[bytes]]
):
    workspace = _workspace(tmp_path)
    stubborn, _ = _start_server(servers, short_dir, workspace, ignore_kill=True)

    assert stop_cursor_worker_servers(workspace, timeout_s=0.3) == {stubborn.pid: False}
    assert stubborn.poll() is None


def test_cleanup_without_a_workspace_or_server_is_a_no_op(tmp_path: Path):
    adapter = CursorAdapter()
    adapter.cleanup_invocation(InvocationPlan(cmd=["cursor-agent"], cwd=tmp_path, stdin_payload="", output_file=None))

    assert stop_cursor_worker_servers(_workspace(tmp_path)) == {}
    assert find_cursor_worker_servers(tmp_path / "missing") == []
