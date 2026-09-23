"""Protocol and confinement tests for the project-owned text ACP server."""

from __future__ import annotations

import json
import os
import selectors
import shlex
import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SERVER = _ROOT / "scripts" / "agent_runtime" / "acp_text_agent.mjs"
_READY_LINE = "acp-text-agent ready"
# Startup includes importing the ACP SDK under a loaded runner. The budget is
# bounded so a hung child still fails, and it starts only after spawn.
_STARTUP_TIMEOUT_S = 60.0
# Protocol reads start after the ready line, so this bound is the request
# itself, not process startup.
_RPC_TIMEOUT_S = 60.0
# Cancel must return well before the fake provider's 30s sleep. The product
# force-kills after 1s; the extra room is scheduler delay under parallel load.
_CANCEL_ROUNDTRIP_S = 10.0


class _AcpServer:
    """Child ACP server whose stderr is drained until it signals ready."""

    def __init__(self, process: subprocess.Popen[str]) -> None:
        self.process = process
        self._stderr_lines: list[str] = []
        self._stderr_lock = threading.Lock()
        self._ready = threading.Event()
        self._stderr_done = threading.Event()
        self._thread = threading.Thread(target=self._drain_stderr, name="acp-stderr", daemon=True)
        self._thread.start()

    def _drain_stderr(self) -> None:
        stderr = self.process.stderr
        assert stderr is not None
        try:
            for line in stderr:
                with self._stderr_lock:
                    self._stderr_lines.append(line)
                if line.strip() == _READY_LINE:
                    self._ready.set()
        finally:
            self._stderr_done.set()

    def stderr_text(self) -> str:
        with self._stderr_lock:
            return "".join(self._stderr_lines)

    def wait_until_ready(self, timeout: float = _STARTUP_TIMEOUT_S) -> None:
        deadline = time.monotonic() + timeout
        while not self._ready.is_set():
            exited = self.process.poll() is not None and self._stderr_done.wait(1.0)
            if exited and not self._ready.is_set():
                raise AssertionError(
                    "ACP server exited before readiness "
                    f"(code {self.process.returncode}); stderr={self.stderr_text()!r}"
                )
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError(f"timed out waiting for ACP readiness; stderr={self.stderr_text()!r}")
            self._ready.wait(min(0.2, remaining))

    def close(self) -> None:
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=15)
        self._thread.join(timeout=5)


def _read_json_line(server: _AcpServer, timeout: float = _RPC_TIMEOUT_S) -> dict:
    selector = selectors.DefaultSelector()
    process = server.process
    assert process.stdout is not None
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        ready = selector.select(timeout)
        if not ready:
            raise AssertionError(f"timed out waiting for ACP output; stderr={server.stderr_text()!r}")
        line = process.stdout.readline()
    finally:
        selector.close()
    assert line, f"ACP server exited early with code {process.poll()}; stderr={server.stderr_text()!r}"
    return json.loads(line)


def _request(server: _AcpServer, payload: dict) -> None:
    stdin = server.process.stdin
    assert stdin is not None
    stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
    stdin.flush()


def _launch_server(*, provider: str, model: str, binary: Path, extra_env: dict[str, str] | None = None) -> _AcpServer:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is required for the ACP protocol test")
    env = dict(os.environ)
    env.update(extra_env or {})
    process = subprocess.Popen(
        [
            node,
            str(_SERVER),
            "--provider",
            provider,
            "--model",
            model,
            "--binary",
            str(binary),
        ],
        cwd=_ROOT,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    server = _AcpServer(process)
    try:
        server.wait_until_ready()
    except Exception:
        server.close()
        raise
    return server


def _initialize_session(server: _AcpServer) -> str:
    _request(
        server,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": 1,
                "clientCapabilities": {},
                "clientInfo": {"name": "pytest", "version": "1"},
            },
        },
    )
    initialized = _read_json_line(server)
    assert initialized["id"] == 1
    assert initialized["result"]["protocolVersion"] == 1
    _request(
        server,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/new",
            "params": {"cwd": str(_ROOT), "mcpServers": []},
        },
    )
    return _read_json_line(server)["result"]["sessionId"]


def _run_protocol(tmp_path: Path, *, provider: str, model: str, binary: Path) -> tuple[str, str]:
    capture = tmp_path / f"{binary.name}-capture.txt"
    server = _launch_server(
        provider=provider,
        model=model,
        binary=binary,
        extra_env={"UNRELATED_API_KEY": "must-not-reach-provider"},
    )
    try:
        session = _initialize_session(server)
        _request(
            server,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "session/prompt",
                "params": {
                    "sessionId": session,
                    "prompt": [{"type": "text", "text": "Give one sentence."}],
                },
            },
        )

        response = ""
        deadline = time.monotonic() + _RPC_TIMEOUT_S
        while time.monotonic() < deadline:
            message = _read_json_line(server, timeout=max(0.1, deadline - time.monotonic()))
            if message.get("method") == "session/update":
                update = message["params"]["update"]
                if update.get("sessionUpdate") == "agent_message_chunk":
                    response += update["content"]["text"]
            if message.get("id") == 3:
                assert message["result"]["stopReason"] == "end_turn"
                break
        else:  # pragma: no cover - defensive deadline branch
            raise AssertionError(f"prompt response never completed; stderr={server.stderr_text()!r}")

        assert capture.is_file()
        return response, capture.read_text(encoding="utf-8")
    finally:
        server.close()


def _fake_binary(tmp_path: Path, name: str, response: str) -> Path:
    binary = tmp_path / name
    capture = shlex.quote(str(tmp_path / f"{name}-capture.txt"))
    config_capture = shlex.quote(str(tmp_path / f"{name}-config.yaml"))
    binary.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$PWD|${{AGY_APP_DATA_DIR:-}}|${{HERMES_HOME:-}}|$*|${{UNRELATED_API_KEY:-}}\" > {capture}\n"
        'if [ -n "${HERMES_HOME:-}" ]; then\n'
        f'  /bin/cp "$HERMES_HOME/config.yaml" {config_capture}\n'
        "fi\n"
        f"printf '%s' {json.dumps(response)}\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)
    return binary


def test_agy_text_agent_is_source_blind_sandboxed_and_ephemeral(tmp_path):
    binary = _fake_binary(tmp_path, "agy", "agy fake response")
    response, capture = _run_protocol(
        tmp_path,
        provider="agy",
        model="gemini-3.6-flash-high",
        binary=binary,
    )
    cwd, app_data, hermes_home, args, unrelated_secret = capture.strip().split("|", 4)
    assert response == "agy fake response"
    assert cwd != str(_ROOT)
    assert not Path(cwd).exists()
    assert Path(app_data).resolve().is_relative_to(Path(cwd).resolve())
    assert not Path(app_data).exists()
    assert hermes_home == ""
    assert "--mode plan" in args
    assert "--sandbox" in args
    assert "--disable-slash-commands" in args
    assert "--dangerously-skip-permissions" not in args
    assert unrelated_secret == ""


def test_deepseek_text_agent_has_empty_tools_no_fallbacks_and_ephemeral_home(tmp_path):
    binary = _fake_binary(tmp_path, "hermes", "deepseek fake response")
    response, capture = _run_protocol(
        tmp_path,
        provider="deepseek",
        model="deepseek-v4-pro",
        binary=binary,
    )
    cwd, app_data, hermes_home, args, unrelated_secret = capture.strip().split("|", 4)
    assert response == "deepseek fake response"
    assert cwd != str(_ROOT)
    assert app_data == ""
    assert Path(hermes_home).resolve().is_relative_to(Path(cwd).resolve())
    assert not Path(hermes_home).exists()
    assert "--ignore-rules -z" in args
    assert "-m deepseek-v4-pro --provider deepseek" in args
    config = (tmp_path / "hermes-config.yaml").read_text(encoding="utf-8")
    assert "platform_toolsets:\n  cli: []" in config
    assert "fallback_providers: []" in config
    assert "mcp_servers: {}" in config
    assert unrelated_secret == ""


def test_cancel_force_kills_provider_process_group_before_cleanup(tmp_path):
    binary = tmp_path / "agy"
    capture = tmp_path / "cancel-capture.txt"
    binary.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$$|$PWD\" > {shlex.quote(str(capture))}\n"
        "trap '' TERM\n"
        "while :; do sleep 30; done\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)
    server = _launch_server(provider="agy", model="gemini-3.6-flash-high", binary=binary)
    try:
        session = _initialize_session(server)
        _request(
            server,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "session/prompt",
                "params": {
                    "sessionId": session,
                    "prompt": [{"type": "text", "text": "Wait."}],
                },
            },
        )
        deadline = time.monotonic() + _RPC_TIMEOUT_S
        while not capture.is_file() and time.monotonic() < deadline:
            if server.process.poll() is not None:
                break
            time.sleep(0.02)
        assert capture.is_file(), f"provider never started; stderr={server.stderr_text()!r}"
        child_pid_text, child_cwd = capture.read_text(encoding="utf-8").strip().split("|", 1)
        child_pid = int(child_pid_text)
        started = time.monotonic()
        _request(
            server,
            {
                "jsonrpc": "2.0",
                "method": "session/cancel",
                "params": {"sessionId": session},
            },
        )
        cancelled = _read_json_line(server, timeout=_CANCEL_ROUNDTRIP_S)
        assert cancelled["id"] == 3
        assert "error" in cancelled
        assert time.monotonic() - started < _CANCEL_ROUNDTRIP_S
        assert not Path(child_cwd).exists()
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
    finally:
        server.close()
