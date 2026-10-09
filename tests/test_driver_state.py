"""Pinned driver state survives compaction via the AGY PreInvocation hook."""

from __future__ import annotations

import io
import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import delegate, driver_state
from scripts.common import task_store_paths

REPO = Path(__file__).resolve().parents[1]
SYNTHETIC_WORKER_TARGET = 7


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
    assert out["decision"] == "continue"
    assert "counter unavailable" in out["reason"]
    assert list(directory.iterdir()) == []


@pytest.mark.parametrize(
    "operation,ending",
    [
        (operation, ending)
        for operation in ("mkdir", "lstat", "read_text", "write_text", "unlink")
        for ending in ("question", "clean", "escalation", "cap")
        if not (operation == "read_text" and ending in ("clean", "escalation"))
        and not (operation == "unlink" and ending == "question")
    ],
)
def test_stop_cli_counter_io_errors_fail_closed(driver, state, monkeypatch, capsys, operation, ending):
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
    original = getattr(Path, operation)

    def denied(path, *args, **kwargs):
        if path in (counter, counter.parent):
            raise PermissionError("synthetic counter storage is unwritable")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, operation, denied)
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
    out = json.loads(capsys.readouterr().out)
    if ending in ("clean", "escalation"):
        assert out == {"decision": "allow"}
        return
    if ending == "cap" and operation in ("write_text", "unlink"):
        assert out["decision"] == "allow"
        if operation == "unlink":
            assert counter.read_text(encoding="utf-8") == "0"
        return
    assert out["decision"] == "continue"
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
    original = Path.write_text

    def denied(path, data, *args, **kwargs):
        if path == counter and data == "0":
            raise PermissionError("synthetic counter reset is unwritable")
        return original(path, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", denied)
    transcript = _transcript(driver, "Which should I take?")
    for _ in range(2):
        out = _stop(driver, transcript)
        assert out["decision"] == "allow"
        assert "retry budget exhausted" in out["reason"]
    monkeypatch.setattr(Path, "write_text", original)
    assert _stop(driver, transcript)["decision"] == "allow"
    assert counter.read_text(encoding="utf-8") == "0"
    assert _stop(driver, transcript)["decision"] == "continue"


def test_stop_counter_failure_preserves_all_policy_reasons(driver, state, monkeypatch):
    _workers(driver, "gemini-infra", 0)
    counter = driver_state._counter_path(state, "c1")
    original = Path.write_text

    def denied(path, *args, **kwargs):
        if path == counter:
            raise PermissionError("synthetic counter storage is unwritable")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", denied)
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "continue"
    assert "below the privately configured target" in out["reason"]
    assert "question" in out["reason"]
    assert "counter unavailable" in out["reason"]
    _workers(driver, "gemini-infra", SYNTHETIC_WORKER_TARGET)
    out = _stop(driver, _transcript(driver, "Work verified."), fully_idle=True)
    assert out["decision"] == "continue"
    assert "nothing is armed to wake you" in out["reason"]
    assert "counter unavailable" in out["reason"]


def test_stop_corrupt_counter_fails_closed(driver, state):
    counter = driver_state._counter_path(state, "c1")
    counter.write_text("invalid", encoding="utf-8")
    out = _stop(driver, _transcript(driver, "Which should I take?"))
    assert out["decision"] == "continue"
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
    ["missing", "dead", "stale", "wrong-seat", "wrong-task", "unknown-status", "unavailable", "bad-json", "no-nonce"],
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
        if fault == "dead":
            out["alive"] = False
        elif fault == "stale":
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
    original = Path.write_text

    def denied(path, *args, **kwargs):
        if path.name.endswith(".failure.json"):
            raise PermissionError("synthetic failure storage fault")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", denied)
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
