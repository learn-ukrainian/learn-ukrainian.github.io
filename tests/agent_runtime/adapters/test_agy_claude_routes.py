"""Shared fixtures retained for product tests; machinery test cases run in machinery."""
from __future__ import annotations

import json
from pathlib import Path

from lu_machinery.agent_runtime.adapters import agy
from lu_machinery.agent_runtime.adapters.base import InvocationPlan

SLUGS = ("claude-sonnet-5-5-high", "claude-opus-5-5-high")


def _identity_stream_plan(tmp_path, slug):
    conversation_id = "7cd3ba85-817f-4a03-8223-1ff39ca42419"
    app_data = tmp_path / "agy-data"
    transcript = app_data / "brain" / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
    transcript.parent.mkdir(parents=True)
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "agy" / "verify_words_transcript.jsonl"
    transcript.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    log_file = tmp_path / "agy.log"
    log_file.write_text(f"Print mode: conversation={conversation_id}, sending message\n", encoding="utf-8")
    plan = InvocationPlan(
        cmd=["agy", "--output-format", "stream-json", "--model", slug],
        cwd=tmp_path,
        env_overrides={"AGY_RUNTIME_LOG_FILE": str(log_file), "AGY_APP_DATA_DIR": str(app_data)},
        metadata={"entire_fleet": {"requested_model": slug}},
    )
    terminal = {
        "event": "result",
        "result": {
            "status": "SUCCESS",
            "conversation_id": conversation_id,
            "response": "READY",
        },
    }
    return plan, terminal


def mock_agy_provider(monkeypatch, tmp_path, runner, *, stdout, exit_kind="complete", version="1.4.0"):
    """Mock only the process boundary, keeping adapter planning/parsing and runner custody."""
    from types import SimpleNamespace

    monkeypatch.setattr(agy, "require_hook_config", lambda *a, **k: None)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    plan, _ = _identity_stream_plan(tmp_path, SLUGS[1])
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(tmp_path / "agy-data"))
    monkeypatch.setattr(agy, "_agy_app_data", lambda overrides: tmp_path / "agy-data")
    monkeypatch.setattr(agy, "_build_log_path", lambda *a: tmp_path / "agy.log")
    binary = tmp_path / "agy-cli-fixture"
    binary.write_bytes(b"synthetic CLI artifact, never executed\n")
    original_which = agy.shutil.which
    monkeypatch.setattr(agy.shutil, "which", lambda name: str(binary) if name == "agy" else original_which(name))
    monkeypatch.setattr(runner, "has_headroom", lambda *a: (True, "fixture"))
    monkeypatch.setattr(runner, "load_failover_chain", lambda *a, **k: None)
    monkeypatch.setattr(runner, "write_record", lambda *a: None)
    monkeypatch.setattr(runner, "resolve_invocation_telemetry", lambda **k: SimpleNamespace(
        model=k["requested_model"], effort="high", cli_version=version,
    ))
    monkeypatch.setattr(runner.PrimaryTreeWatch, "start", lambda **k: None)
    monkeypatch.setattr(runner._ChildCwdPin, "start", lambda **k: None)
    monkeypatch.setattr(runner, "_prepare_spawn_command", lambda cmd, env: (cmd, env))
    launches = []

    class Process:
        pid = 999_999_991
        returncode = None

        def poll(self):
            if self.returncode is not None:
                return self.returncode
            if exit_kind == "timeout":
                return None
            if exit_kind == "cancel":
                raise KeyboardInterrupt("synthetic cancellation")
            if exit_kind == "exception":
                raise RuntimeError("synthetic runtime failure")
            self.returncode = 0
            return self.returncode

        def wait(self, **kwargs):
            return self.returncode

    proc = Process()

    def spawn(cmd, **kwargs):
        launches.append((cmd, kwargs))
        return proc, None, None

    monkeypatch.setattr(runner, "_spawn_subprocess", spawn)
    monkeypatch.setattr(runner, "_kill_process_tree", lambda proc: setattr(proc, "returncode", -15))
    monkeypatch.setattr(runner, "_agy_process_group_exited", lambda pid: True)
    state = SimpleNamespace(stdout_lines=stdout.splitlines(keepends=True), stderr_lines=[])
    monkeypatch.setattr(runner, "start_watchdog", lambda *a, **k: (state, []))
    monkeypatch.setattr(runner, "stop_watchdog", lambda *a, **k: None)
    if exit_kind == "timeout":
        monkeypatch.setattr(runner, "should_kill", lambda *a, **k: "hard_timeout")
    return launches, plan, binary


def consistency_stream(slug, case):
    """Frozen author inputs; expectations live in the consuming tests."""
    other = "claude-opus-5-5-high" if "sonnet" in slug else "claude-sonnet-5-5-high"
    init = {"event": "init", "model": slug, "session_id": "7cd3ba85-817f-4a03-8223-1ff39ca42419"}
    terminal = {"event": "result", "result": {
        "status": "SUCCESS", "response": "READY", "conversation_id": "7cd3ba85-817f-4a03-8223-1ff39ca42419",
    }}
    events = [init]
    if case == "display":
        init["model"] = "Claude Sonnet 5.5 (High)" if "sonnet" in slug else "Claude Opus 5.5 (High)"
    elif case in {"other-pin", "mismatch-then-duplicate", "mismatch-then-session"}:
        init["model"] = other
    elif case == "other-family":
        init["model"] = "gemini-4-hydrogen-medium"
    elif case == "nested-model":
        init["init"] = {"model": other}
    elif case == "nested-session":
        init["init"] = {"session_id": "different-session"}
    elif case == "terminal-session":
        terminal["result"]["conversation_id"] = "different-session"
    elif case.startswith("repeated"):
        repeated = dict(init)
        if case == "repeated-model":
            repeated["model"] = other
        elif case == "repeated-session":
            repeated["session_id"] = "different-session"
        elif case == "repeated-source":
            repeated["source"] = "configuration"
        events.append(repeated)
    elif case in {"unknown", "retired", "non-string"}:
        init["model"] = {"unknown": "unrecognized", "retired": "Claude Opus 4.6 (Thinking)", "non-string": 7}[case]
    elif case == "configuration":
        init["source"] = "requested"
    elif case == "missing":
        events = []
    elif case == "late":
        events.insert(0, {"event": "step_update"})
    elif case == "provider-failure":
        terminal["result"].update(status="ERROR", error="synthetic provider failure")
    if case == "mismatch-then-session":
        events.append({**init, "session_id": "different-session"})
    lines = list(map(json.dumps, events))
    if case in {"duplicate-after", "mismatch-then-duplicate"}:
        lines.append('{"event":"step_update","metadata":[{"model":"one","\\u006dodel":"two"}]}')
    lines.append(json.dumps(terminal))
    return "\n".join(lines) + "\n"
