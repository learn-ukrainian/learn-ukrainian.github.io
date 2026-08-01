"""Protocol and confinement tests for the project-owned text ACP server."""

from __future__ import annotations

import json
import os
import selectors
import shlex
import shutil
import subprocess
import time
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SERVER = _ROOT / "scripts" / "agent_runtime" / "acp_text_agent.mjs"


def _read_json_line(process: subprocess.Popen[str], timeout: float = 10.0) -> dict:
    selector = selectors.DefaultSelector()
    assert process.stdout is not None
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        ready = selector.select(timeout)
        if not ready:
            stderr = process.stderr.read() if process.poll() is not None and process.stderr else ""
            raise AssertionError(f"timed out waiting for ACP output; stderr={stderr!r}")
        line = process.stdout.readline()
    finally:
        selector.close()
    assert line, f"ACP server exited early with code {process.poll()}"
    return json.loads(line)


def _request(process: subprocess.Popen[str], payload: dict) -> None:
    assert process.stdin is not None
    process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
    process.stdin.flush()


def _launch_server(
    *, provider: str, model: str, binary: Path, extra_env: dict[str, str] | None = None
) -> subprocess.Popen[str]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is required for the ACP protocol test")
    env = dict(os.environ)
    env.update(extra_env or {})
    return subprocess.Popen(
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


def _initialize_session(process: subprocess.Popen[str]) -> str:
    _request(
        process,
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
    initialized = _read_json_line(process)
    assert initialized["id"] == 1
    assert initialized["result"]["protocolVersion"] == 1
    _request(
        process,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/new",
            "params": {"cwd": str(_ROOT), "mcpServers": []},
        },
    )
    return _read_json_line(process)["result"]["sessionId"]


def _run_protocol(tmp_path: Path, *, provider: str, model: str, binary: Path) -> tuple[str, str]:
    capture = tmp_path / f"{binary.name}-capture.txt"
    process = _launch_server(
        provider=provider,
        model=model,
        binary=binary,
        extra_env={"UNRELATED_API_KEY": "must-not-reach-provider"},
    )
    try:
        session = _initialize_session(process)
        _request(
            process,
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
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            message = _read_json_line(process, timeout=max(0.1, deadline - time.monotonic()))
            if message.get("method") == "session/update":
                update = message["params"]["update"]
                if update.get("sessionUpdate") == "agent_message_chunk":
                    response += update["content"]["text"]
            if message.get("id") == 3:
                assert message["result"]["stopReason"] == "end_turn"
                break
        else:  # pragma: no cover - defensive deadline branch
            raise AssertionError("prompt response never completed")

        assert capture.is_file()
        return response, capture.read_text(encoding="utf-8")
    finally:
        if process.stdin:
            process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)


def _fake_binary(tmp_path: Path, name: str, response: str) -> Path:
    binary = tmp_path / name
    capture = shlex.quote(str(tmp_path / f"{name}-capture.txt"))
    config_capture = shlex.quote(str(tmp_path / f"{name}-config.yaml"))
    binary.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$PWD|${{AGY_APP_DATA_DIR:-}}|${{HERMES_HOME:-}}|$*|${{UNRELATED_API_KEY:-}}\" > {capture}\n"
        "if [ -n \"${HERMES_HOME:-}\" ]; then\n"
        f"  /bin/cp \"$HERMES_HOME/config.yaml\" {config_capture}\n"
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
    process = _launch_server(provider="agy", model="gemini-3.6-flash-high", binary=binary)
    try:
        session = _initialize_session(process)
        _request(
            process,
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
        deadline = time.monotonic() + 3
        while not capture.is_file() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert capture.is_file()
        child_pid_text, child_cwd = capture.read_text(encoding="utf-8").strip().split("|", 1)
        child_pid = int(child_pid_text)
        started = time.monotonic()
        _request(
            process,
            {
                "jsonrpc": "2.0",
                "method": "session/cancel",
                "params": {"sessionId": session},
            },
        )
        cancelled = _read_json_line(process, timeout=5)
        assert cancelled["id"] == 3
        assert "error" in cancelled
        assert time.monotonic() - started < 3
        assert not Path(child_cwd).exists()
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
    finally:
        if process.stdin:
            process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)
