"""Pinned driver state survives compaction via the AGY PreInvocation hook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import driver_state

REPO = Path(__file__).resolve().parents[1]


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
    assert "injectSteps" in driver_state.cmd_agy_hook("not json")


def test_injection_is_capped(state):
    state.write_text("x\n" * (driver_state.MAX_INJECT_CHARS), encoding="utf-8")
    message = driver_state.cmd_agy_hook("{}")["injectSteps"][0]["ephemeralMessage"]
    assert len(message) < driver_state.MAX_INJECT_CHARS + len(driver_state.POLICY) + 600
    assert "truncated" in message


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
        (tasks / f"t{i}.json").write_text(json.dumps({"initiator": seat, "status": status}), encoding="utf-8")
    (tasks / "other.json").write_text(json.dumps({"initiator": "codex-devops", "status": "running"}), encoding="utf-8")


@pytest.fixture
def driver(state, tmp_path, monkeypatch):
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "gemini-infra")
    monkeypatch.setattr(driver_state.tempfile, "gettempdir", lambda: str(tmp_path / "tmp"))
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
    _workers(driver, "gemini-infra", 4)
    assert _stop(driver, _transcript(driver, "Dispatched 4 workers; waiting on them.")) == {}


def test_stop_continues_on_question(driver):
    _workers(driver, "gemini-infra", 4)
    out = _stop(driver, _transcript(driver, "Option A or option B for #10117. Which should I take?"))
    assert out["decision"] == "continue"
    assert "question" in out["reason"]


def test_stop_continues_on_listed_plan(driver):
    _workers(driver, "gemini-infra", 5)
    out = _stop(driver, _transcript(driver, "Status done.\n\n## Next steps\n- rebase #10197"))
    assert out["decision"] == "continue"
    assert "actions you have not done" in out["reason"]


def test_stop_continues_below_min_workers_counting_only_own_seat(driver):
    _workers(driver, "gemini-infra", 2)
    out = _stop(driver, _transcript(driver, "All good."))
    assert out["decision"] == "continue"
    assert "only 2 of your workers" in out["reason"]


def test_stop_requires_wakeup_when_fully_idle(driver):
    _workers(driver, "gemini-infra", 4)
    out = _stop(driver, _transcript(driver, "All good."), fully_idle=True)
    assert out["decision"] == "continue"
    assert "schedule" in out["reason"]


def test_stop_allows_cto_escalation(driver):
    _workers(driver, "gemini-infra", 0)
    text = "CTO-ESCALATION: deleting the stale branch needs approval. Should I?"
    assert _stop(driver, _transcript(driver, text)) == {}


def test_stop_caps_consecutive_continues(driver):
    _workers(driver, "gemini-infra", 0)
    transcript = _transcript(driver, "Which should I take?")
    results = [_stop(driver, transcript) for _ in range(driver_state.MAX_CONSECUTIVE_CONTINUES + 1)]
    assert all(r.get("decision") == "continue" for r in results[:-1])
    assert results[-1] == {}


def test_stop_ignores_errors_and_non_drivers(driver, monkeypatch):
    transcript = _transcript(driver, "Which should I take?")
    for reason in ("error", "MAX_INVOCATIONS", "EXECUTOR_TERMINATION_REASON_USER_CANCELED"):
        payload = {"workspacePaths": [str(driver)], "transcriptPath": str(transcript), "terminationReason": reason}
        assert driver_state.cmd_agy_stop_hook(json.dumps(payload)) == {}
    payload["terminationReason"] = "model_stop"
    assert driver_state.cmd_agy_stop_hook(json.dumps(payload))["decision"] == "continue"
    monkeypatch.delenv(driver_state.STATE_ENV)
    assert _stop(driver, transcript) == {}


def test_pretool_denies_ask_question_only_for_drivers(driver, monkeypatch):
    call = {"toolCall": {"name": "ask_question"}, "workspacePaths": [str(driver)]}
    assert driver_state.cmd_agy_pretool_hook(json.dumps(call))["decision"] == "deny"
    other = {"toolCall": {"name": "run_command"}, "workspacePaths": [str(driver)]}
    assert driver_state.cmd_agy_pretool_hook(json.dumps(other)) == {"decision": "ask"}
    monkeypatch.delenv(driver_state.STATE_ENV)
    assert driver_state.cmd_agy_pretool_hook(json.dumps(call)) == {"decision": "ask"}


def test_injection_appends_policy_when_state_lacks_it(state):
    message = driver_state.cmd_agy_hook("{}")["injectSteps"][0]["ephemeralMessage"]
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
