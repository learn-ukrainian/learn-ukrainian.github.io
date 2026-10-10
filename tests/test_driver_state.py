"""Pinned driver state survives compaction via the AGY PreInvocation hook."""

from __future__ import annotations

import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import delegate, driver_state
from scripts.common import task_store_paths

REPO = Path(__file__).resolve().parents[1]
SYNTHETIC_WORKER_TARGET = 7


@pytest.mark.parametrize("epic", ["../../tmp/evil", "absolute", "UPPER", "bad_name", "-infra", "infra-"])
def test_init_rejects_invalid_epic_before_creating_anything(tmp_path, epic):
    root = tmp_path / "sandbox" / "repo"
    root.mkdir(parents=True)
    if epic == "absolute":
        epic = str(tmp_path / "absolute")
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/driver_state.py"), "init", f"--epic={epic}"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode != 0, result.stdout
    assert not list(tmp_path.rglob("DRIVER-STATE.md"))
    assert not (root / ".claude").exists()


@pytest.mark.parametrize("existing", [False, True])
def test_init_private_new_epic_directory_preserves_existing_mode(tmp_path, monkeypatch, existing):
    monkeypatch.setattr(driver_state, "_repo_root", lambda: tmp_path)
    directory = tmp_path / ".claude" / "infra-epic"
    if existing:
        directory.mkdir(parents=True)
        directory.chmod(0o750)
    old_umask = os.umask(0)
    try:
        assert driver_state.main(["init", "--epic", "infra"]) == 0
    finally:
        os.umask(old_umask)
    assert stat.S_IMODE(directory.stat().st_mode) == (0o750 if existing else 0o700)


@pytest.fixture
def state(tmp_path, monkeypatch):
    path = tmp_path / ".claude" / "infra-epic" / "DRIVER-STATE.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Driver state: infra\n\n## Epic\n- Stream: infra\n\n"
        "## Current goals\n1. fix X — DONE WHEN: CI green\n\n## Next step\n- open PR\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(driver_state.STATE_ENV, str(path))
    monkeypatch.setenv("SESSION_EPIC", "infra")
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "gemini-infra")
    monkeypatch.delenv(driver_state.MIN_WORKERS_ENV, raising=False)
    return path


def test_hook_injects_ephemeral_state(state, tmp_path):
    out = driver_state.cmd_agy_hook(json.dumps({"workspacePaths": [str(tmp_path)], "invocationNum": 7}))
    message = out["injectSteps"][0]["ephemeralMessage"]
    assert "PINNED DRIVER STATE" in message
    assert "Stream: infra" in message
    assert "fix X" in message


def test_hook_is_noop_without_env(monkeypatch):
    monkeypatch.delenv(driver_state.STATE_ENV, raising=False)
    assert driver_state.cmd_agy_hook("{}") == {}


def test_hook_is_noop_for_other_workspace(state, tmp_path):
    other = tmp_path / "worker-checkout"
    other.mkdir()
    assert driver_state.cmd_agy_hook(json.dumps({"workspacePaths": [str(other)]})) == {}


def test_hook_is_noop_when_state_missing(state):
    state.unlink()
    assert driver_state.cmd_agy_hook("{}") == {}


def test_hook_tolerates_bad_payload(state):
    assert driver_state.cmd_agy_hook("not json") == {}


def test_injection_is_rejected_when_envelope_is_oversized(state, tmp_path):
    text = "x\n" * driver_state.MAX_ENVELOPE_CHARS + "\nNewest goal: preserve me"
    state.write_text(text, encoding="utf-8")
    out = driver_state.cmd_agy_hook(json.dumps({"workspacePaths": [str(tmp_path)]}))
    assert set(out) == {"injectSteps"}
    message = out["injectSteps"][0]["ephemeralMessage"]
    assert message.startswith("DRIVER-GATE-FAILED:")
    assert "envelope exceeds" in message
    assert driver_state._read_state(state) == text


def test_whoami_prints_goals_and_next(state, capsys):
    assert driver_state.main(["whoami"]) == 0
    out = capsys.readouterr().out
    assert "epic: infra" in out
    assert "fix X" in out
    assert "open PR" in out
    assert "blocker-policy: Put every owned blocker in --current with complete: true;" in out


@pytest.mark.parametrize("missing", [False, True])
def test_whoami_redacts_state_path(state, capsys, missing):
    path = state.parent / "synthetic-private-state.md"
    if not missing:
        path.write_text(state.read_text(encoding="utf-8"), encoding="utf-8")
    assert driver_state.cmd_whoami(path) == (1 if missing else 0)
    out = capsys.readouterr().out
    assert "state: (configured)" in out
    assert str(path.parent) not in out
    assert path.name not in out
    if missing:
        assert "state file missing" in out
    else:
        assert "fix X" in out
        assert "open PR" in out


def test_init_refuses_overwrite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(driver_state, "_repo_root", lambda start=None: tmp_path)
    assert driver_state.main(["init", "--epic", "demo"]) == 0
    assert (tmp_path / ".claude" / "demo-epic" / "DRIVER-STATE.md").is_file()
    assert driver_state.main(["init", "--epic", "demo"]) == 1


def test_hook_cli_prints_json_end_to_end(state, tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.driver_state", "agy-hook"],
        input=json.dumps({"workspacePaths": [str(tmp_path)]}),
        capture_output=True,
        text=True,
        cwd=REPO,
        check=True,
        timeout=60,
    )
    assert json.loads(proc.stdout)["injectSteps"]


@pytest.mark.parametrize("mode", ["agy-hook", "agy-stop-hook", "agy-pretool-hook"])
@pytest.mark.parametrize(
    ("failure", "output", "exit_code"),
    [
        ("missing", "", 0),
        ("not-executable", "", 0),
        ("interpreter-error", "", 0),
        ("nonzero", "", 1),
        ("nonzero-object", '{"unexpected": true}', 1),
        ("non-json", "not json", 0),
        ("nul-byte", '{"value":\x00 1}', 0),
        ("empty", "", 0),
        ("array", "[]", 0),
        ("scalar", '"text"', 0),
        ("multiple-objects", "{}\n{}", 0),
        ("nonstandard-constant", '{"value": NaN}', 0),
        ("validator-error", '{"unexpected": true}', 0),
    ],
)
def test_hook_shell_falls_back_and_drains_stdin(state, tmp_path, monkeypatch, mode, failure, output, exit_code):
    interpreter = tmp_path / "synthetic-interpreter"
    if failure != "missing":
        interpreter.write_text(
            f"#!{sys.executable}\n"
            "import os\nimport sys\n"
            "if sys.argv[1] == '-m':\n"
            f"    print({output!r})\n"
            f"    sys.exit({exit_code})\n"
            + (
                "sys.exit(1)\n"
                if failure == "validator-error"
                else "os.execv(sys.executable, [sys.executable, *sys.argv[1:]])\n"
            ),
            encoding="utf-8",
        )
        if failure == "interpreter-error":
            interpreter.write_text("#!missing-synthetic-interpreter\n", encoding="utf-8")
        interpreter.chmod(0o600 if failure == "not-executable" else 0o700)
    monkeypatch.setenv("LU_DRIVER_STATE_PYTHON", str(interpreter))
    # Exceed a pipe buffer; the child deliberately never reads its input.
    payload = " " * (256 * 1024) + "{}\n\n"
    input_path = tmp_path / "hook-input.json"
    input_path.write_text(payload, encoding="utf-8")
    with input_path.open(encoding="utf-8") as hook_input:
        proc = subprocess.run(
            ["sh", str(REPO / "scripts" / "agy_hooks" / "driver_state_inject.sh"), mode],
            stdin=hook_input,
            capture_output=True,
            text=True,
            cwd=tmp_path,
            timeout=60,
            check=False,
        )
        assert hook_input.tell() == len(payload)
    assert proc.returncode == 0
    assert json.loads(proc.stdout) == ({"decision": "allow"} if mode != "agy-hook" else {})
    assert proc.stderr == ""


@pytest.mark.parametrize("mode", ["agy-hook", "agy-stop-hook", "agy-pretool-hook"])
def test_hook_shell_preserves_input_bytes(state, tmp_path, monkeypatch, mode):
    interpreter = tmp_path / "synthetic-interpreter"
    interpreter.write_text(
        f"#!{sys.executable}\n"
        "import json\nimport os\nimport sys\n"
        "if sys.argv[1] == '-m':\n"
        "    print(json.dumps({'input_hex': sys.stdin.buffer.read().hex()}))\n"
        "else:\n"
        "    os.execv(sys.executable, [sys.executable, *sys.argv[1:]])\n",
        encoding="utf-8",
    )
    interpreter.chmod(0o700)
    temporary = tmp_path / "synthetic-temporary"
    temporary.mkdir()
    monkeypatch.setenv("TMPDIR", str(temporary))
    monkeypatch.setenv("LU_DRIVER_STATE_PYTHON", str(interpreter))
    payload = b'\x00{"value": "before\x00after"}\x00\r\n\n'
    proc = subprocess.run(
        ["sh", str(REPO / "scripts/agy_hooks/driver_state_inject.sh"), mode],
        input=payload,
        capture_output=True,
        cwd=tmp_path,
        timeout=60,
        check=True,
    )
    assert json.loads(proc.stdout) == {"input_hex": payload.hex()}
    assert proc.stderr == b""
    assert list(temporary.iterdir()) == []


@pytest.mark.parametrize("mode", ["agy-hook", "agy-stop-hook", "agy-pretool-hook"])
def test_hook_shell_normal_path(state, tmp_path, monkeypatch, mode):
    monkeypatch.setenv("LU_DRIVER_STATE_PYTHON", sys.executable)
    payload = {
        "workspacePaths": [str(tmp_path)],
        "terminationReason": "ERROR",
        "toolCall": {"name": "ask_question"},
    }
    proc = subprocess.run(
        ["sh", str(REPO / "scripts" / "agy_hooks" / "driver_state_inject.sh"), mode],
        input=json.dumps(payload) + "\n\n",
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    if mode == "agy-hook":
        assert "fix X" in result["injectSteps"][0]["ephemeralMessage"]
    elif mode == "agy-stop-hook":
        assert result == {"decision": "allow"}
    else:
        assert result["decision"] == "deny"
    assert proc.stderr == ""


def test_agy_hooks_json_wires_all_driver_hooks():
    config = json.loads((REPO / "agents_extensions" / "agy" / "hooks.json").read_text(encoding="utf-8"))
    commands = {
        config["driver-state-pin"]["PreInvocation"][0]["command"],
        config["driver-keep-driving"]["Stop"][0]["command"],
        config["driver-no-ask-question"]["PreToolUse"][0]["hooks"][0]["command"],
    }
    assert config["driver-no-ask-question"]["PreToolUse"][0]["matcher"] == "ask_question"
    modes = set()
    for command in commands:
        _, script, mode = command.split()
        modes.add(mode)
        # AGY runs hooks from the deployed hooks.json directory (.agents/).
        assert (REPO / ".agents" / script).resolve() == (
            REPO / "scripts" / "agy_hooks" / "driver_state_inject.sh"
        ).resolve()
    assert modes == {"agy-hook", "agy-stop-hook", "agy-pretool-hook"}


def _transcript(tmp_path, content, tool_calls=None):
    path = tmp_path / "transcript.jsonl"
    rows = [
        {"source": "USER_EXPLICIT", "type": "USER_INPUT", "content": "go"},
        {"source": "MODEL", "type": "PLANNER_RESPONSE", "content": content, "tool_calls": tool_calls or []},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def _workers(root, seat, n, status="running"):
    tasks = root / "batch_state" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        (tasks / f"t{i}.json").write_text(
            json.dumps({"task_id": f"t{i}", "run_nonce": f"nonce-{i}", "initiator": seat, "status": status}),
            encoding="utf-8",
        )
    (tasks / "other.json").write_text(json.dumps({"initiator": "codex-devops", "status": "running"}), encoding="utf-8")


@pytest.fixture(autouse=True)
def live_monitor(monkeypatch):
    """Replace only the live Monitor transport; never contact another lane."""

    def fetch(task_id, *, run_nonce=None):
        record = driver_state.tasks_dir() / f"{task_id}.json"
        if not record.is_file():
            return None
        task = json.loads(record.read_text(encoding="utf-8"))
        return {"task": task, "alive": True}

    monkeypatch.setattr(delegate, "_fetch_monitor_task", fetch)


@pytest.fixture
def driver(state, tmp_path, monkeypatch):
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "gemini-infra")
    monkeypatch.setenv(driver_state.MIN_WORKERS_ENV, str(SYNTHETIC_WORKER_TARGET))
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "batch_state" / "tasks"))
    return tmp_path


def _stop(tmp_path, transcript, fully_idle=False, conv="c1"):
    return driver_state.cmd_agy_stop_hook(
        json.dumps(
            {
                "conversationId": conv,
                "workspacePaths": [str(tmp_path)],
                "transcriptPath": str(transcript),
                "terminationReason": "NO_TOOL_CALL",
                "fullyIdle": fully_idle,
            }
        )
    )


def test_stop_allows_clean_report_with_workers_and_wakeup(driver):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    assert _stop(driver, _transcript(driver, "Workers dispatched; waiting on them.")) == {"decision": "allow"}


def test_stop_continues_on_question(driver):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    out = _stop(driver, _transcript(driver, "Option A or option B for #10117. Which should I take?"))
    assert out["decision"] == "continue"
    assert "question" in out["reason"]


def test_stop_continues_on_listed_plan(driver):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET + 1)
    out = _stop(driver, _transcript(driver, "Status done.\n\n## Next steps\n- rebase #10197"))
    assert out["decision"] == "continue"
    assert "actions you have not done" in out["reason"]


def test_stop_continues_below_min_workers_counting_only_own_seat(driver):
    _workers(driver, "gemini-infra", 2)
    assert driver_state.running_workers("gemini-infra") == 2
    out = _stop(driver, _transcript(driver, "All good."))
    assert out["decision"] == "continue"
    assert "below the privately configured target" in out["reason"]


def test_stop_requires_wakeup_when_fully_idle(driver):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    out = _stop(driver, _transcript(driver, "All good."), fully_idle=True)
    assert out["decision"] == "continue"
    assert "schedule" in out["reason"]


def test_stop_allows_cto_escalation(driver):
    _workers(driver, "gemini-infra", 0)
    text = "CTO-ESCALATION: deleting the stale branch needs approval. Should I?"
    assert _stop(driver, _transcript(driver, text)) == {"decision": "allow"}


def test_stop_caps_consecutive_continues(driver):
    _workers(driver, "gemini-infra", 0)
    transcript = _transcript(driver, "Which should I take?")
    for _ in range(2):
        results = [_stop(driver, transcript) for _ in range(driver_state.MAX_CONSECUTIVE_CONTINUES + 1)]
        assert all(r.get("decision") == "continue" for r in results[:-1])
        assert results[-1] == {
            "decision": "allow",
            "reason": "DRIVER-GATE-FAILED: corrective retry budget exhausted.",
        }
        failure = driver_state._counter_path(driver_state.state_path(), "c1").with_suffix(".failure.json")
        assert json.loads(failure.read_text())["code"] == "corrective_retry_budget_exhausted"


@pytest.mark.parametrize("oversized", [False, True])
def test_preinvocation_never_changes_stop_retry_counter(driver, state, oversized):
    _workers(driver, "gemini-infra", 0)
    if oversized:
        state.write_text("x" * (driver_state.MAX_ENVELOPE_CHARS + 1))
    transcript = _transcript(driver, "Which should I take?")
    payload = json.dumps({"workspacePaths": [str(driver)], "conversationId": "c1"})
    counter = state.parent / "stop-counters" / "stop-c1.count"
    for attempt in range(driver_state.MAX_CONSECUTIVE_CONTINUES + 1):
        before = counter.read_text() if counter.exists() else None
        invocation = driver_state.cmd_agy_hook(payload)
        message = invocation["injectSteps"][0]["ephemeralMessage"]
        assert message.startswith("DRIVER-GATE-FAILED:" if oversized else "PINNED DRIVER STATE")
        assert (counter.read_text() if counter.exists() else None) == before
        result = _stop(driver, transcript)
        if attempt < driver_state.MAX_CONSECUTIVE_CONTINUES:
            assert result["decision"] == "continue"
            assert counter.read_text() == str(attempt + 1)
        else:
            assert result == {
                "decision": "allow",
                "reason": "DRIVER-GATE-FAILED: corrective retry budget exhausted.",
            }
            assert counter.read_text() == "0"


@pytest.mark.parametrize("mode", ["agy-hook", "agy-pretool-hook"])
def test_cli_non_stop_failure_does_not_reset_counter(state, tmp_path, monkeypatch, capsys, mode):
    driver_state._bump_counter(state, "error")

    def fail(_payload):
        raise OSError("synthetic hook fault")

    monkeypatch.setattr(driver_state, "cmd_agy_hook" if mode == "agy-hook" else "cmd_agy_pretool_hook", fail)
    raw = json.dumps({"workspacePaths": [str(tmp_path)], "conversationId": "error"})
    monkeypatch.setattr(driver_state.sys, "stdin", io.StringIO(raw))
    assert driver_state.main([mode]) == 0
    result = json.loads(capsys.readouterr().out)
    reason = "DRIVER-GATE-FAILED: driver-state hook error."
    assert result == (
        {"injectSteps": [{"ephemeralMessage": reason}]}
        if mode == "agy-hook"
        else {
            "decision": "deny",
            "reason": reason,
        }
    )
    assert driver_state._counter_path(state, "error").read_text() == "1"


def test_bridge_consult_environment_excludes_driver_state_even_in_same_workspace(state, tmp_path, monkeypatch):
    from scripts.ai_agent_bridge._env import build_agent_env

    child_env = build_agent_env(
        {
            "PATH": "/usr/bin",
            "HOME": str(tmp_path),
            "LU_DRIVER_STATE_FILE": str(state),
            "SESSION_HANDOFF_AGENT": "gemini-infra",
        }
    )
    assert driver_state.STATE_ENV not in child_env
    for key in (driver_state.STATE_ENV, "SESSION_HANDOFF_AGENT"):
        monkeypatch.delenv(key, raising=False)
    for key, value in child_env.items():
        monkeypatch.setenv(key, value)
    raw = json.dumps({"workspacePaths": [str(tmp_path)], "toolCall": {"name": "ask_question"}})
    assert driver_state.cmd_agy_hook(raw) == {}
    assert driver_state.cmd_agy_stop_hook(raw) == {"decision": "allow"}
    assert driver_state.cmd_agy_pretool_hook(raw) == {"decision": "allow"}


def test_counter_private_round_trip_and_epic_isolation(state, tmp_path):
    counter = driver_state._counter_path(state, "synthetic-conversation")
    assert counter.parent == state.parent / "stop-counters"
    assert stat.S_IMODE(counter.parent.stat().st_mode) == 0o700
    assert counter.parent.stat().st_uid == driver_state.os.geteuid()
    assert driver_state._bump_counter(state, "synthetic-conversation") == 1
    assert driver_state._bump_counter(state, "synthetic-conversation") == 2
    other = tmp_path / "other-epic" / "DRIVER-STATE.md"
    other.parent.mkdir()
    assert driver_state._bump_counter(other, "synthetic-conversation") == 1
    driver_state._reset_counter(state, "synthetic-conversation")
    assert counter.read_text(encoding="utf-8") == "0"
    driver_state._reset_counter(state, "synthetic-conversation")
    assert driver_state._bump_counter(state, "synthetic-conversation") == 1


@pytest.mark.parametrize("unsafe", ["foreign-owner", "shared", "symlink"])
def test_stop_refuses_unsafe_counter_directory(driver, state, monkeypatch, unsafe):
    directory = state.parent / "stop-counters"
    if unsafe == "symlink":
        target = driver / "synthetic-target"
        target.mkdir(mode=0o700)
        directory.symlink_to(target, target_is_directory=True)
    else:
        directory.mkdir(mode=0o700)
        if unsafe == "foreign-owner":
            monkeypatch.setattr(driver_state.os, "geteuid", lambda: directory.stat().st_uid + 1)
        else:
            directory.chmod(0o777)
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert "counter unavailable" in out["reason"]
    assert list(directory.iterdir()) == []


@pytest.mark.parametrize("operation", ["directory", "read", "write", "lock-open", "lock-acquire", "replace"])
@pytest.mark.parametrize("ending", ["question", "clean", "escalation", "cap"])
def test_stop_cli_counter_io_errors_fail_closed(driver, state, monkeypatch, capsys, operation, ending):
    fault_fired = False
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    content = {
        "question": "Which should I take?",
        "clean": "Work verified.",
        "escalation": "CTO-ESCALATION: approval required.",
        "cap": "Which should I take?",
    }[ending]
    transcript = _transcript(driver, content)
    counter = driver_state._counter_path(state, "synthetic-conversation")
    counter.write_text(str(driver_state.MAX_CONSECUTIVE_CONTINUES if ending == "cap" else 0), encoding="utf-8")
    if operation == "directory":
        original = driver_state.open_unit_dir

        def denied(path, *args, **kwargs):
            nonlocal fault_fired
            if path == counter.parent:
                fault_fired = True
                raise PermissionError("synthetic directory storage fault")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(driver_state, "open_unit_dir", denied)
    elif operation in ("read", "write"):
        name = "read_unit" if operation == "read" else "write_unit"
        original = getattr(driver_state, name)

        def denied(fd, name, *args, **kwargs):
            nonlocal fault_fired
            if name == counter.name:
                fault_fired = True
                raise PermissionError("synthetic counter storage fault")
            return original(fd, name, *args, **kwargs)

        monkeypatch.setattr(driver_state, name, denied)
    elif operation == "lock-open":
        original = os.open

        def denied(name, *args, **kwargs):
            nonlocal fault_fired
            if name == counter.name + ".lock":
                fault_fired = True
                raise PermissionError("synthetic lock storage fault")
            return original(name, *args, **kwargs)

        monkeypatch.setattr(os, "open", denied)
    elif operation == "lock-acquire":

        def denied(*args):
            nonlocal fault_fired
            fault_fired = True
            raise OSError("synthetic flock failure")

        monkeypatch.setattr(driver_state.fcntl, "flock", denied)
    else:
        original = os.replace

        def denied(source, destination, *args, **kwargs):
            nonlocal fault_fired
            if destination == counter.name:
                fault_fired = True
                raise PermissionError("synthetic counter cannot be replaced")
            return original(source, destination, *args, **kwargs)

        monkeypatch.setattr(os, "replace", denied)
    monkeypatch.setattr(
        driver_state.sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "conversationId": "synthetic-conversation",
                    "workspacePaths": [str(driver)],
                    "transcriptPath": str(transcript),
                    "terminationReason": "NO_TOOL_CALL",
                }
            )
        ),
    )
    assert driver_state.main(["agy-stop-hook"]) == 0
    assert fault_fired, f"{operation} fault did not fire for {ending}"
    out = json.loads(capsys.readouterr().out)
    if ending in ("clean", "escalation"):
        assert out == {"decision": "allow"}
    else:
        assert out["decision"] == "allow"
        assert "DRIVER-GATE-FAILED" in out["reason"]
        if ending == "cap" and operation in ("write", "replace"):
            assert "retry budget exhausted" in out["reason"]
        else:
            assert "counter unavailable" in out["reason"]
            assert "question" in out["reason"]


def test_stop_cap_resets_without_unlink(driver, state, monkeypatch):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    counter = driver_state._counter_path(state, "c1")
    counter.write_text(str(driver_state.MAX_CONSECUTIVE_CONTINUES), encoding="utf-8")
    original = Path.unlink

    def denied(path, *args, **kwargs):
        if path == counter:
            raise PermissionError("synthetic counter cannot be unlinked")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", denied)
    transcript = _transcript(driver, "Which should I take?")
    assert _stop(driver, transcript)["decision"] == "allow"
    assert counter.read_text(encoding="utf-8") == "0"
    assert _stop(driver, transcript)["decision"] == "continue"
    assert counter.read_text(encoding="utf-8") == "1"


def test_stop_cap_reset_write_failure_remains_visible_until_reset_succeeds(driver, state, monkeypatch):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    counter = driver_state._counter_path(state, "c1")
    counter.write_text(str(driver_state.MAX_CONSECUTIVE_CONTINUES), encoding="utf-8")
    original = driver_state.write_unit

    def denied(fd, name, data, *args, **kwargs):
        if name == counter.name and data == b"0":
            raise PermissionError("synthetic counter reset is unwritable")
        return original(fd, name, data, *args, **kwargs)

    monkeypatch.setattr(driver_state, "write_unit", denied)
    transcript = _transcript(driver, "Which should I take?")
    for _ in range(2):
        out = _stop(driver, transcript)
        assert out["decision"] == "allow"
        assert "retry budget exhausted" in out["reason"]
    monkeypatch.setattr(driver_state, "write_unit", original)
    assert _stop(driver, transcript)["decision"] == "allow"
    assert counter.read_text(encoding="utf-8") == "0"
    assert _stop(driver, transcript)["decision"] == "continue"


def test_stop_counter_failure_preserves_all_policy_reasons(driver, state, monkeypatch):
    _workers(driver, "gemini-infra", 0)
    counter = driver_state._counter_path(state, "c1")
    original = driver_state.write_unit

    def denied(fd, name, *args, **kwargs):
        if name == counter.name:
            raise PermissionError("synthetic counter storage is unwritable")
        return original(fd, name, *args, **kwargs)

    monkeypatch.setattr(driver_state, "write_unit", denied)
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert "below the privately configured target" in out["reason"]
    assert "question" in out["reason"]
    assert "counter unavailable" in out["reason"]
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    out = _stop(driver, _transcript(driver, "Work verified."), fully_idle=True)
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert "nothing is armed to wake you" in out["reason"]
    assert "counter unavailable" in out["reason"]


def test_stop_corrupt_counter_fails_closed(driver, state):
    counter = driver_state._counter_path(state, "c1")
    counter.write_text("invalid", encoding="utf-8")
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert "counter unavailable" in out["reason"]


def test_stop_ignores_errors_and_non_drivers(driver, monkeypatch):
    transcript = _transcript(driver, "Which should I take?")
    for reason in ("error", "MAX_INVOCATIONS", "EXECUTOR_TERMINATION_REASON_USER_CANCELED"):
        payload = {"workspacePaths": [str(driver)], "transcriptPath": str(transcript), "terminationReason": reason}
        assert driver_state.cmd_agy_stop_hook(json.dumps(payload)) == {"decision": "allow"}
    payload["terminationReason"] = "model_stop"
    assert driver_state.cmd_agy_stop_hook(json.dumps(payload))["decision"] == "continue"
    monkeypatch.delenv(driver_state.STATE_ENV)
    assert _stop(driver, transcript) == {"decision": "allow"}


def test_pretool_denies_ask_question_only_for_drivers(driver, monkeypatch):
    call = {"toolCall": {"name": "ask_question"}, "workspacePaths": [str(driver)]}
    assert driver_state.cmd_agy_pretool_hook(json.dumps(call))["decision"] == "deny"
    other = {"toolCall": {"name": "run_command"}, "workspacePaths": [str(driver)]}
    assert driver_state.cmd_agy_pretool_hook(json.dumps(other)) == {"decision": "allow"}
    monkeypatch.delenv(driver_state.STATE_ENV)
    assert driver_state.cmd_agy_pretool_hook(json.dumps(call)) == {"decision": "allow"}


def test_injection_appends_policy_when_state_lacks_it(state, tmp_path):
    message = driver_state.cmd_agy_hook(json.dumps({"workspacePaths": [str(tmp_path)]}))["injectSteps"][0][
        "ephemeralMessage"
    ]
    assert driver_state.POLICY_TITLE in message
    assert "CTO-ESCALATION:" in message


def test_template_carries_policy(tmp_path, monkeypatch):
    monkeypatch.setattr(driver_state, "_repo_root", lambda start=None: tmp_path)
    assert driver_state.main(["init", "--epic", "demo"]) == 0
    text = (tmp_path / ".claude" / "demo-epic" / "DRIVER-STATE.md").read_text(encoding="utf-8")
    assert driver_state.POLICY_TITLE in text
    assert text.count(driver_state.POLICY_TITLE) == 1


def test_last_model_text_reads_final_response(tmp_path):
    path = _transcript(tmp_path, "final words")
    assert driver_state.last_model_text(str(path)) == "final words"
    assert driver_state.last_model_text(str(tmp_path / "missing.jsonl")) == ""


@pytest.mark.parametrize("prefix", ["No ", "Report complete.\n", "Quoted: "])
def test_stop_does_not_accept_embedded_escalation_marker(driver, prefix):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    text = prefix + "CTO-ESCALATION: is needed. I will run the remaining actions next."
    out = _stop(driver, _transcript(driver, text))
    assert out["decision"] == "continue"
    assert "actions you have not done" in out["reason"]


@pytest.mark.parametrize("raw", [None, "", "invalid", "0", "-1", "1.5", "７"])
def test_stop_unknown_worker_target_does_not_force_continuation(driver, monkeypatch, raw):
    if raw is None:
        monkeypatch.delenv(driver_state.MIN_WORKERS_ENV)
    else:
        monkeypatch.setenv(driver_state.MIN_WORKERS_ENV, raw)
    _workers(driver, "gemini-infra", 0)
    assert driver_state.minimum_workers() is None
    assert _stop(driver, _transcript(driver, "Work verified.")) == {"decision": "allow"}
    assert _stop(driver, _transcript(driver, "I will run the remaining actions next."))["decision"] == "continue"


def test_worker_target_is_read_at_call_time(driver, monkeypatch):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    transcript = _transcript(driver, "Work verified.")
    assert _stop(driver, transcript) == {"decision": "allow"}
    monkeypatch.setenv(driver_state.MIN_WORKERS_ENV, str(SYNTHETIC_WORKER_TARGET + 1))
    assert _stop(driver, transcript)["decision"] == "continue"


def test_running_workers_uses_shared_store_from_linked_worktree(tmp_path, monkeypatch):
    primary = tmp_path / "primary"
    linked = tmp_path / "linked"
    metadata = primary / ".git" / "worktrees" / "linked"
    metadata.mkdir(parents=True)
    linked.mkdir()
    (linked / ".git").write_text(f"gitdir: {metadata}\n", encoding="utf-8")
    module = linked / "scripts" / "common" / "task_store_paths.py"
    module.parent.mkdir(parents=True)
    module.touch()
    monkeypatch.setattr(task_store_paths, "__file__", str(module))
    monkeypatch.delenv("LU_TASKS_DIR", raising=False)
    monkeypatch.chdir(linked)
    _workers(primary, "synthetic-seat", SYNTHETIC_WORKER_TARGET)
    assert driver_state.running_workers("synthetic-seat") == SYNTHETIC_WORKER_TARGET
    _workers(linked, "synthetic-seat", SYNTHETIC_WORKER_TARGET + 1)
    assert driver_state.running_workers("synthetic-seat") == SYNTHETIC_WORKER_TARGET


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"])
def test_last_model_text_preserves_unicode_inside_jsonl(tmp_path, separator):
    content = f"Verified{separator}result"
    path = tmp_path / "unicode.jsonl"
    row = {"source": "MODEL", "type": "PLANNER_RESPONSE", "content": content}
    path.write_text(json.dumps(row, ensure_ascii=False) + "\r\n", encoding="utf-8")
    assert driver_state.last_model_text(str(path)) == content


def test_public_worker_policy_uses_no_numeric_target():
    assert "privately configured worker target" in driver_state.POLICY
    assert not any(char.isdigit() for char in driver_state.POLICY)


@pytest.mark.parametrize("length", [5999, 6000, 6001, 6100])
def test_whole_state_keeps_appended_goals(state, tmp_path, length):
    text = "x" * length + "\nNewest goal: preserve me"
    state.write_text(text, encoding="utf-8")
    out = driver_state.cmd_agy_hook(json.dumps({"workspacePaths": [str(tmp_path)]}))
    message = out["injectSteps"][0]["ephemeralMessage"]
    assert text in message
    assert "truncated" not in message


def test_rendered_envelope_exact_boundary(state):
    wrapper_size = len(driver_state.render_injection(driver_state.POLICY, state))
    text = driver_state.POLICY.rstrip() + "x" * (driver_state.MAX_ENVELOPE_CHARS - wrapper_size)
    assert len(driver_state.render_injection(text, state)) == driver_state.MAX_ENVELOPE_CHARS
    with pytest.raises(ValueError, match="envelope exceeds"):
        driver_state.render_injection(text + "x", state)


@pytest.mark.parametrize(
    "prefix",
    [
        "",
        "The CTO blocker delta policy is mentioned in prose.\n",
        "## CTO blocker delta policy extra\n",
        "### CTO blocker delta policy\n",
        "```markdown\n## CTO blocker delta policy\n```\n",
        "> ## CTO blocker delta policy\n",
        "  ## CTO blocker delta policy\n",
        "<!--\n## CTO blocker delta policy\n-->\n",
        "CTO blocker delta policy\n-----------------------\n",
    ],
)
def test_blocker_policy_requires_exact_real_heading(state, prefix):
    message = driver_state.render_injection(prefix + "Current goals remain intact.", state)
    assert message.count(driver_state.BLOCKER_POLICY.rstrip()) == 1
    assert "Current goals remain intact." in message
    assert "scripts.driver_blockers delta" in message
    assert "scripts.driver_blockers record" in message
    assert "if delta fails or the baseline is unknown, post everything currently blocking" in message


def test_existing_blocker_heading_is_not_duplicated(state):
    text = driver_state.POLICY + "\n" + driver_state.BLOCKER_POLICY
    rendered = driver_state.render_injection(text, state)
    assert rendered.count("## " + driver_state.BLOCKER_POLICY_TITLE) == 1
    assert rendered.count(driver_state.BLOCKER_POLICY.rstrip()) == 1
    assert driver_state.render_injection(text + "\nLast goal", state).endswith("Last goal")


def test_blocker_template_and_complete_envelope_boundary(state, monkeypatch, tmp_path):
    monkeypatch.setattr(driver_state, "_repo_root", lambda start=None: tmp_path)
    assert driver_state.main(["init", "--epic", "demo"]) == 0
    text = (tmp_path / ".claude/demo-epic/DRIVER-STATE.md").read_text()
    assert text.count(driver_state.BLOCKER_POLICY) == 1
    assert "exact case-sensitive standalone token RESOLVED <id>" in text
    assert "on its own non-active line (no other fields or prose)" in text
    policies = driver_state.POLICY + "\n" + driver_state.BLOCKER_POLICY + "\n"
    wrapper_size = len(driver_state.render_injection(policies, state))
    exact = policies.rstrip() + "\n" + "x" * (driver_state.MAX_ENVELOPE_CHARS - wrapper_size - 1)
    assert len(driver_state.render_injection(exact, state)) == driver_state.MAX_ENVELOPE_CHARS
    with pytest.raises(ValueError, match="envelope exceeds"):
        driver_state.render_injection(exact + "x", state)


@pytest.mark.parametrize("baseline", ["absent", "present", "empty"])
def test_whoami_blocker_summary(state, baseline, capsys):
    from scripts import driver_blockers

    ledger = state.parent / driver_blockers.LEDGER_NAME
    if baseline == "empty":
        ledger.write_text("")
    elif baseline == "present":
        body = b"No blockers"
        receipt = {
            "recipient": "cto",
            "message_id": "fixture-msg",
            "created_at": "2026-10-10T01:00:00Z",
            "content_sha256": driver_blockers.hashlib.sha256(body).hexdigest(),
        }
        driver_blockers.record(ledger, "infra", {"epic": "infra", "complete": True, "items": []}, receipt, body, 0)
    assert driver_state.cmd_whoami(state) == 0
    output = capsys.readouterr().out
    assert (
        "CTO blockers: generation 1; 0 recorded blockers" if baseline == "present" else driver_blockers.UNKNOWN_SUMMARY
    ) in output
    assert str(state.parent) not in output


@pytest.mark.parametrize(
    "text",
    [
        "armed a background delegate.py wait. I will now wait for the reviewer verdict.",
        "Work verified.\n\n> Should I dispatch?",
        "Work verified.\n\n> quoted review:\nShould I dispatch?",  # CommonMark lazy quote continuation
        "Work verified.\n\n```text\nShould I dispatch?\n## Next steps\n- fix it\n```",
        "Work verified.\n\n~~~~\nI will now run tests.\n~~~\n~~~~",  # short fence cannot close
        "Work verified.\n\n    Should I dispatch?",  # indented code
        'Reviewer asked "Should I dispatch?" and the report is complete.',
        "Reviewer asked ‘Should I dispatch?’ and the report is complete.",
        "Logged question: `Should I dispatch?`",
        "Option A was rejected, or deferred. Option B was implemented and verified.",
        "## Next steps: none",
        "## Next steps\nNone.",
        "Next steps: none",
        "## Pending actions\nDone.",
        "Plan review passed; PR #123 merged at abc123.",
        "plan-review skill ran clean on a1/foo; merged.",
        "Plan v2 approved by the operator and merged.",
        "Next steps: none; three workers are running and a wait is armed.",
        "I'll check back when the armed wait fires.",
        "I will not run more checks; verification completed.",
        "Pending actions: completed; all checks passed.",
        "Next steps: done — merged #123.",
        "Next steps: done – merged #123.",
        "Next steps: done - merged #123.",
    ],
)
def test_question_plan_detector_allows_reports_quotes_and_armed_waits(driver, text):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    assert driver_state.ends_on_question_or_plan(text) is None
    assert _stop(driver, _transcript(driver, text)) == {"decision": "allow"}


@pytest.mark.parametrize(
    "text",
    [
        "Work verified.\n\n> Should I dispatch?\n\nI will now run tests.",
        "Work verified.\n\n```\nShould I dispatch?\n```\n\nShould I open the PR?",
        "## Next steps\n- Run remaining checks.",
        "Next steps: run remaining checks",
        "I will now dispatch a worker.",
        "I will fix the remaining defect.",
        "Please choose a path.",
        "I'll check the remaining failures.",
        "I’ll merge after CI.",
        "I'll check back when the armed wait fires. I will fix any failures.",
        "Plan: dispatch the remaining worker.",
        "## Plan\n- Dispatch the remaining worker.",
    ],
)
def test_question_plan_detector_preserves_authored_actions(driver, text):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    assert driver_state.ends_on_question_or_plan(text) is not None
    assert _stop(driver, _transcript(driver, text))["decision"] == "continue"


@pytest.mark.parametrize(
    "prefix,suffix",
    [
        ("> ", ""),
        ("```\n", "\n```"),
        ("~~~\n", "\n~~~"),
        ('"', '"'),
        ("`", "`"),
        ("Report: ", ""),
        ("    ", ""),
    ],
)
def test_quoted_or_embedded_escalation_never_exempts_worker_gate(driver, prefix, suffix):
    _workers(driver, "gemini-infra", 0)
    text = prefix + "CTO-ESCALATION: approval required" + suffix
    out = _stop(driver, _transcript(driver, text))
    assert out["decision"] == "continue"
    assert "below the privately configured target" in out["reason"]


def test_trimmed_leading_escalation_resets_counter(driver, state):
    driver_state._bump_counter(state, "c1")
    assert _stop(driver, _transcript(driver, " \nCTO-ESCALATION: approval required?")) == {"decision": "allow"}
    assert driver_state._counter_path(state, "c1").read_text() == "0"


@pytest.mark.parametrize("workspaces", [None, [], "root", [None], [1], [""], ["\x00"]])
def test_non_driver_workspace_payloads_are_allowed(state, workspaces):
    payload = {"toolCall": {"name": "ask_question"}}
    if workspaces is not None:
        payload["workspacePaths"] = workspaces
    raw = json.dumps(payload)
    assert driver_state.cmd_agy_hook(raw) == {}
    assert driver_state.cmd_agy_stop_hook(raw) == {"decision": "allow"}
    assert driver_state.cmd_agy_pretool_hook(raw) == {"decision": "allow"}


@pytest.mark.parametrize("secondary", [False, True])
def test_consult_workspace_is_not_driver_even_with_inherited_env(state, tmp_path, secondary):
    workspaces = [str(tmp_path / "consult")]
    if secondary:
        workspaces.insert(0, str(tmp_path))
    raw = json.dumps({"workspacePaths": workspaces, "toolCall": {"name": "ask_question"}})
    assert driver_state.cmd_agy_hook(raw) == {}
    assert driver_state.cmd_agy_stop_hook(raw) == {"decision": "allow"}
    assert driver_state.cmd_agy_pretool_hook(raw) == {"decision": "allow"}


def test_handoff_identity_required_for_all_hooks(state, tmp_path, monkeypatch):
    monkeypatch.delenv("SESSION_HANDOFF_AGENT")
    raw = json.dumps({"workspacePaths": [str(tmp_path)], "toolCall": {"name": "ask_question"}})
    assert driver_state.cmd_agy_hook(raw) == {}
    assert driver_state.cmd_agy_stop_hook(raw) == {"decision": "allow"}
    assert driver_state.cmd_agy_pretool_hook(raw) == {"decision": "allow"}


@pytest.mark.parametrize("reason", sorted(driver_state.SKIP_TERMINATION_REASONS))
def test_error_exit_resets_counter(driver, state, reason):
    driver_state._bump_counter(state, "exit")
    raw = json.dumps({"workspacePaths": [str(driver)], "conversationId": "exit", "terminationReason": reason})
    assert driver_state.cmd_agy_stop_hook(raw) == {"decision": "allow"}
    assert driver_state._counter_path(state, "exit").read_text() == "0"


def test_clean_stop_resets_counter(driver, state):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    driver_state._bump_counter(state, "c1")
    assert _stop(driver, _transcript(driver, "Work verified.")) == {"decision": "allow"}
    assert driver_state._counter_path(state, "c1").read_text() == "0"


@pytest.mark.parametrize(
    "fault",
    ["missing", "stale", "wrong-seat", "wrong-task", "unknown-status", "unavailable", "bad-json", "no-nonce"],
)
def test_worker_count_unknown_never_satisfies_floor(driver, monkeypatch, fault):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    original = delegate._fetch_monitor_task

    def fetch(task_id, *, run_nonce=None):
        if fault == "unavailable":
            raise delegate.MonitorApiUnavailable("synthetic outage")
        if fault == "missing":
            return None
        out = original(task_id, run_nonce=run_nonce)
        if fault == "stale":
            out["task"]["run_nonce"] = "old-nonce"
        elif fault == "wrong-seat":
            out["task"]["initiator"] = "other-seat"
        elif fault == "wrong-task":
            out["task"]["task_id"] = "other-task"
        elif fault == "unknown-status":
            out["task"].pop("status")
        return out

    monkeypatch.setattr(delegate, "_fetch_monitor_task", fetch)
    record = driver_state.tasks_dir() / "t0.json"
    if fault == "bad-json":
        record.write_text("invalid")
    elif fault == "no-nonce":
        data = json.loads(record.read_text())
        data.pop("run_nonce")
        record.write_text(json.dumps(data))
    assert driver_state.running_workers("gemini-infra") is None
    out = _stop(driver, _transcript(driver, "Work verified."))
    assert out["decision"] == "continue"
    assert "live worker count is unknown" in out["reason"]


@pytest.mark.parametrize("all_dead", [False, True])
def test_dead_running_workers_are_skipped(driver, monkeypatch, all_dead):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    original = delegate._fetch_monitor_task

    def fetch(task_id, *, run_nonce=None):
        out = original(task_id, run_nonce=run_nonce)
        if all_dead or task_id == "t0":
            out["alive"] = False
        return out

    monkeypatch.setattr(delegate, "_fetch_monitor_task", fetch)
    expected = 0 if all_dead else SYNTHETIC_WORKER_TARGET - 1
    assert driver_state.running_workers("gemini-infra") == expected
    out = _stop(driver, _transcript(driver, "Work verified."))
    assert out["decision"] == "continue"
    assert "below the privately configured target" in out["reason"]
    assert "restore worker telemetry" not in out["reason"]


def test_live_terminal_workers_do_not_count(driver, monkeypatch):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    original = delegate._fetch_monitor_task

    def fetch(task_id, *, run_nonce=None):
        out = original(task_id, run_nonce=run_nonce)
        out["task"]["status"] = "done"
        out["alive"] = False
        return out

    monkeypatch.setattr(delegate, "_fetch_monitor_task", fetch)
    assert driver_state.running_workers("gemini-infra") == 0


def test_worker_probe_budget_is_bounded(driver, monkeypatch):
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    ticks = iter([0, 7])
    monkeypatch.setattr(driver_state.time, "monotonic", lambda: next(ticks))
    assert driver_state.running_workers("gemini-infra") is None


@pytest.mark.parametrize("mode", ["agy-hook", "agy-stop-hook", "agy-pretool-hook"])
def test_shell_consult_with_inherited_driver_environment(state, tmp_path, monkeypatch, mode):
    monkeypatch.setenv("LU_DRIVER_STATE_PYTHON", sys.executable)
    raw = json.dumps({"workspacePaths": [str(tmp_path / "consult")], "toolCall": {"name": "ask_question"}})
    proc = subprocess.run(
        ["sh", str(REPO / "scripts/agy_hooks/driver_state_inject.sh"), mode],
        input=raw,
        capture_output=True,
        text=True,
        cwd=REPO,
        timeout=60,
        check=True,
    )
    assert json.loads(proc.stdout) == ({"decision": "allow"} if mode != "agy-hook" else {})


def test_shell_exhaustion_is_visible_and_records_failure(driver, state, monkeypatch):
    monkeypatch.setenv("LU_DRIVER_STATE_PYTHON", sys.executable)
    monkeypatch.delenv(driver_state.MIN_WORKERS_ENV)
    driver_state._counter_path(state, "shell").write_text(str(driver_state.MAX_CONSECUTIVE_CONTINUES))
    transcript = _transcript(driver, "Which should I take?")
    raw = json.dumps({"workspacePaths": [str(driver)], "conversationId": "shell", "transcriptPath": str(transcript)})
    proc = subprocess.run(
        ["sh", str(REPO / "scripts/agy_hooks/driver_state_inject.sh"), "agy-stop-hook"],
        input=raw,
        capture_output=True,
        text=True,
        cwd=REPO,
        timeout=60,
        check=True,
    )
    assert json.loads(proc.stdout) == {
        "decision": "allow",
        "reason": "DRIVER-GATE-FAILED: corrective retry budget exhausted.",
    }
    receipt = driver_state._counter_path(state, "shell").with_suffix(".failure.json")
    assert json.loads(receipt.read_text())["status"] == "failed"


def test_cli_hook_error_resets_counter_and_fails_visibly(driver, state, monkeypatch, capsys):
    driver_state._bump_counter(state, "error")
    monkeypatch.setattr(driver_state, "last_model_text", lambda path: (_ for _ in ()).throw(OSError("synthetic fault")))
    raw = json.dumps({"workspacePaths": [str(driver)], "conversationId": "error"})
    monkeypatch.setattr(driver_state.sys, "stdin", io.StringIO(raw))
    assert driver_state.main(["agy-stop-hook"]) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "allow"
    assert driver_state._counter_path(state, "error").read_text() == "0"


def test_gate_failure_storage_fault_preserves_typed_error(driver, state, monkeypatch, capsys):
    original = driver_state.write_unit

    def denied(fd, name, *args, **kwargs):
        if name.endswith(".failure.json"):
            raise PermissionError("synthetic failure storage fault")
        return original(fd, name, *args, **kwargs)

    monkeypatch.setattr(driver_state, "write_unit", denied)
    out = driver_state._gate_failure(state, "c1", "test_failure", "DRIVER-GATE-FAILED: synthetic failure.")
    assert out["decision"] == "allow"
    assert json.loads(capsys.readouterr().err)["code"] == "test_failure"


def test_shell_oversized_envelope_fails_visibly(state, tmp_path, monkeypatch):
    monkeypatch.setenv("LU_DRIVER_STATE_PYTHON", sys.executable)
    state.write_text("x" * driver_state.MAX_ENVELOPE_CHARS + "\nNewest goal: retain me")
    raw = json.dumps({"workspacePaths": [str(tmp_path)], "conversationId": "oversized"})
    proc = subprocess.run(
        ["sh", str(REPO / "scripts/agy_hooks/driver_state_inject.sh"), "agy-hook"],
        input=raw,
        capture_output=True,
        text=True,
        cwd=REPO,
        timeout=60,
        check=True,
    )
    out = json.loads(proc.stdout)
    assert set(out) == {"injectSteps"}
    assert "envelope exceeds" in out["injectSteps"][0]["ephemeralMessage"]
    failure = driver_state._counter_path(state, "oversized").with_suffix(".failure.json")
    assert json.loads(failure.read_text())["code"] == "state_envelope_oversized"


def test_negative_counter_is_not_a_new_retry_budget(state):
    driver_state._counter_path(state, "c1").write_text("-3")
    with pytest.raises(ValueError, match="invalid continuation counter"):
        driver_state._bump_counter(state, "c1")


def test_cli_help_documents_usage_and_outputs(capsys):
    with pytest.raises(SystemExit) as exc:
        driver_state.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "Examples:" in help_text
    assert "Outputs:" in help_text
    assert "Exit codes:" in help_text
    assert "Related:" in help_text


def test_real_process_counter_increments_are_not_lost(state):
    counter = driver_state._counter_path(state, "race")
    counter.write_text("0")
    script = """import sys, time
from pathlib import Path
from scripts import driver_state as d
# Raise only the test ceiling to measure every increment, independently of the cap.
d.MAX_CONSECUTIVE_CONTINUES = 10000
original_unit = d.read_unit
def delayed_unit(fd, name, **kwargs):
    result = original_unit(fd, name, **kwargs)
    if name.endswith('.count'):
        time.sleep(0.002)
    return result
d.read_unit = delayed_unit
sys.stdin.read(1)
for _ in range(30):
    d._bump_counter(Path(sys.argv[1]), 'race')
"""
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(state)],
            cwd=REPO,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(4)
    ]
    try:
        for process in processes:
            process.stdin.write("x")
            process.stdin.flush()
        outputs = [process.communicate(timeout=20) for process in processes]
        assert [process.returncode for process in processes] == [0] * 4, outputs
        assert counter.read_text() == "120"
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=20)


@pytest.mark.parametrize("linked", ["counter", "lock", "parent"])
def test_stop_refuses_symlinked_counter_state(driver, state, linked):
    counter = driver_state._counter_path(state, "c1")
    target = driver / "counter-target"
    target.write_text("0")
    if linked == "parent":
        moved = state.parent.with_name("moved-epic")
        state.parent.rename(moved)
        state.parent.symlink_to(moved, target_is_directory=True)
    else:
        link = counter if linked == "counter" else counter.with_name(counter.name + ".lock")
        link.symlink_to(target)
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert "counter unavailable" in out["reason"]
    assert target.read_text() == "0"
    if linked != "parent":
        assert link.is_symlink()


@pytest.mark.parametrize("content", [b"", b"invalid", b"-1", b"\xff"])
def test_stop_corrupt_counter_records_typed_failure(driver, state, content):
    counter = driver_state._counter_path(state, "c1")
    counter.write_bytes(content)
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert "question" in out["reason"]
    assert counter.read_bytes() == content
    failure = json.loads(counter.with_suffix(".failure.json").read_text())
    assert failure["code"] == "continuation_counter_unavailable"
    assert failure["reason"] == out["reason"]


@pytest.mark.parametrize("fault", ["unreadable", "lock", "write"])
def test_stop_counter_storage_fault_never_continues(driver, state, monkeypatch, fault):
    counter = driver_state._counter_path(state, "c1")
    counter.write_text("0")
    operation = "read_unit" if fault == "unreadable" else "write_unit"
    original = getattr(driver_state, operation)

    def denied(fd, name, *args, **kwargs):
        if name == counter.name and fault != "lock":
            raise PermissionError("synthetic counter storage fault")
        return original(fd, name, *args, **kwargs)

    monkeypatch.setattr(driver_state, operation, denied)
    original_open = os.open

    def denied_lock(name, *args, **kwargs):
        if str(name).endswith(".lock") and fault == "lock":
            raise PermissionError("synthetic lock failure")
        return original_open(name, *args, **kwargs)

    monkeypatch.setattr(os, "open", denied_lock)
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert "question" in out["reason"]
    failure = json.loads(counter.with_suffix(".failure.json").read_text())
    assert failure["code"] == "continuation_counter_unavailable"


@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_counter_refuses_parent_swap_before_write(state, tmp_path, monkeypatch, replacement):
    counter = driver_state._counter_path(state, "c1")
    counter.write_text("0")
    moved = counter.parent.with_name("moved-counters")
    decoy = tmp_path / "decoy-counters"
    decoy.mkdir(mode=0o700)
    (decoy / counter.name).write_text("0")
    original = driver_state.read_unit
    swapped = False

    def swap(fd, name, **kwargs):
        nonlocal swapped
        result = original(fd, name, **kwargs)
        if name == counter.name and not swapped:
            swapped = True
            counter.parent.rename(moved)
            if replacement == "symlink":
                counter.parent.symlink_to(decoy, target_is_directory=True)
            else:
                counter.parent.mkdir(mode=0o700)
                counter.write_text("0")
        return result

    monkeypatch.setattr(driver_state, "read_unit", swap)
    with pytest.raises(driver_state.COUNTER_STORAGE_ERRORS):
        driver_state._bump_counter(state, "c1")
    assert (moved / counter.name).read_text() == "0"
    assert counter.read_text() == "0"
    assert (decoy / counter.name).read_text() == "0"


@pytest.mark.parametrize("entry", ["counter", "lock"])
def test_counter_refuses_nonregular_storage(driver, state, entry):
    counter = driver_state._counter_path(state, "c1")
    path = counter if entry == "counter" else counter.with_name(counter.name + ".lock")
    path.mkdir()
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert path.is_dir()


@pytest.mark.parametrize("replacement", ["removed", "replaced"])
def test_stop_refuses_lock_entry_change_during_acquisition(driver, state, monkeypatch, replacement):
    counter = driver_state._counter_path(state, "c1")
    counter.write_text("0")
    lock = counter.with_name(counter.name + ".lock")
    original = driver_state.fcntl.flock
    fault_fired = False

    def flock(fd, operation):
        nonlocal fault_fired
        assert operation == driver_state.fcntl.LOCK_EX
        lock.unlink()
        if replacement == "replaced":
            lock.write_bytes(b"")
            assert lock.stat().st_ino != os.fstat(fd).st_ino
        fault_fired = True
        return original(fd, operation)

    monkeypatch.setattr(driver_state.fcntl, "flock", flock)
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert fault_fired
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert "counter unavailable" in out["reason"]
    assert counter.read_text() == "0"


@pytest.mark.parametrize("replacement", ["missing", "symlink", "directory"])
@pytest.mark.parametrize("timing", ["before-write", "during-replace", "after-write"])
def test_stop_detects_parent_swap_at_pinned_write(driver, state, tmp_path, monkeypatch, replacement, timing):
    counter = driver_state._counter_path(state, "c1")
    counter.write_text("0")
    moved = counter.parent.with_name("moved-counters")
    decoy = tmp_path / "decoy-counters"
    decoy.mkdir(mode=0o700)
    (decoy / counter.name).write_text("0")
    fault_fired = False

    def swap_parent():
        nonlocal fault_fired
        counter.parent.rename(moved)
        if replacement == "symlink":
            counter.parent.symlink_to(decoy, target_is_directory=True)
        elif replacement == "directory":
            counter.parent.mkdir(mode=0o700)
            counter.write_text("0")
        fault_fired = True

    original_write, original_replace = driver_state.write_unit, os.replace

    def write(fd, name, content, **kwargs):
        if name == counter.name and timing == "before-write":
            swap_parent()
        original_write(fd, name, content, **kwargs)
        if name == counter.name and timing == "after-write":
            swap_parent()

    def replace(source, destination, **kwargs):
        if destination == counter.name and timing == "during-replace":
            swap_parent()
        return original_replace(source, destination, **kwargs)

    monkeypatch.setattr(driver_state, "write_unit", write)
    monkeypatch.setattr(os, "replace", replace)
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert fault_fired
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert "counter unavailable" in out["reason"]
    assert (moved / counter.name).read_text() == "1"
    assert (decoy / counter.name).read_text() == "0"
    if replacement != "missing":
        assert counter.read_text() == "0"


def test_stop_refuses_oversized_counter_before_read_or_parse(driver, state, monkeypatch):
    monkeypatch.delenv(driver_state.MIN_WORKERS_ENV)
    counter = driver_state._counter_path(state, "c1")
    # The regression runs against the old module before the named bound exists.
    limit = getattr(driver_state, "MAX_COUNTER_BYTES", 4096)
    content = b"1" * (limit + 1)
    counter.write_bytes(content)
    original_read = driver_state.read_unit
    original_int = int
    reads, parses = [], []

    def read(fd, name, **kwargs):
        if name == counter.name:
            reads.append(kwargs.get("max_bytes"))
        return original_read(fd, name, **kwargs)

    def parse(value, *args):
        parses.append(value)
        return original_int(value, *args)

    monkeypatch.setattr(driver_state, "read_unit", read)
    monkeypatch.setattr(driver_state, "int", parse, raising=False)
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "allow"
    assert out["reason"].startswith("DRIVER-GATE-FAILED:")
    assert "counter unavailable" in out["reason"]
    assert reads == [limit]
    # The hook may parse its worker target, but must never parse the counter.
    assert content.decode("utf-8") not in parses
    assert counter.read_bytes() == content
    assert json.loads(counter.with_suffix(".failure.json").read_text())["code"] == "continuation_counter_unavailable"


def test_stop_cli_refuses_oversized_counter_within_hook_timeout(driver, state, monkeypatch):
    # The question triggers continuation without unrelated worker telemetry.
    # Pytest's configured scripts import path is not inherited by the child.
    monkeypatch.delenv(driver_state.MIN_WORKERS_ENV)
    monkeypatch.delenv("PYTHONPATH", raising=False)
    counter = driver_state._counter_path(state, "c1")
    content = b"1" * (4 * 1024 * 1024)
    counter.write_bytes(content)
    transcript = _transcript(driver, "Which should I take?")
    result = subprocess.run(
        [sys.executable, "-m", "scripts.driver_state", "agy-stop-hook"],
        input=json.dumps({"workspacePaths": [str(driver)], "conversationId": "c1", "transcriptPath": str(transcript)}),
        capture_output=True,
        text=True,
        cwd=REPO,
        timeout=10,
        check=True,
    )
    out = json.loads(result.stdout)
    assert out["decision"] == "allow", (result.stdout, result.stderr)
    assert out["reason"].startswith("DRIVER-GATE-FAILED:"), (result.stdout, result.stderr)
    assert "counter unavailable" in out["reason"], (result.stdout, result.stderr)
    assert counter.read_bytes() == content
    assert json.loads(counter.with_suffix(".failure.json").read_text())["code"] == "continuation_counter_unavailable"


def test_counter_atomic_replace_is_private_and_locked(state, monkeypatch):
    counter = driver_state._counter_path(state, "c1")
    counter.write_text("0")
    events = []
    real_fsync, real_replace = os.fsync, os.replace

    def fsync(fd):
        events.append("directory-fsync" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file-fsync")
        real_fsync(fd)

    def replace(source, destination, *, src_dir_fd, dst_dir_fd):
        import fcntl

        assert src_dir_fd == dst_dir_fd
        assert os.fstat(src_dir_fd).st_ino == counter.parent.stat().st_ino
        assert Path(source).name == source
        assert destination == counter.name
        assert stat.S_IMODE(os.stat(source, dir_fd=src_dir_fd).st_mode) == 0o600
        assert (counter.parent / source).read_text() == "1"
        with counter.with_name(counter.name + ".lock").open("rb") as lock:
            with pytest.raises(BlockingIOError):
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        events.append("replace")
        real_replace(source, destination, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(os, "replace", replace)
    old_umask = os.umask(0)
    try:
        assert driver_state._bump_counter(state, "c1") == 1
    finally:
        os.umask(old_umask)
    assert events == ["file-fsync", "replace", "directory-fsync"]
    assert stat.S_IMODE(counter.stat().st_mode) == 0o600
    assert stat.S_IMODE(counter.with_name(counter.name + ".lock").stat().st_mode) == 0o600
    assert list(counter.parent.glob(".*.tmp")) == []


def test_counter_replace_failure_preserves_old_count(driver, state, monkeypatch):
    counter = driver_state._counter_path(state, "c1")
    counter.write_text("0")
    original = os.replace

    def denied(source, destination, **kwargs):
        if destination == counter.name:
            raise OSError("synthetic atomic replace failure")
        return original(source, destination, **kwargs)

    monkeypatch.setattr(os, "replace", denied)
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert counter.read_text() == "0"
    assert list(counter.parent.glob(".*.tmp")) == []
    assert json.loads(counter.with_suffix(".failure.json").read_text())["code"] == "continuation_counter_unavailable"


def test_gate_failure_refuses_symlinked_receipt(driver, state, monkeypatch, capsys):
    counter = driver_state._counter_path(state, "c1")
    target = driver / "receipt-target"
    target.write_text("untouched")
    counter.with_suffix(".failure.json").symlink_to(target)
    counter.write_text("invalid")
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "allow"
    assert "DRIVER-GATE-FAILED" in out["reason"]
    assert json.loads(capsys.readouterr().err)["code"] == "continuation_counter_unavailable"
    assert target.read_text() == "untouched"
