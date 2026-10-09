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
    assert len(message) < driver_state.MAX_INJECT_CHARS + 600
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


def test_agy_hooks_json_wires_preinvocation_script():
    config = json.loads((REPO / "agents_extensions" / "agy" / "hooks.json").read_text(encoding="utf-8"))
    handler = config["driver-state-pin"]["PreInvocation"][0]
    assert handler["command"] == "sh ../scripts/agy_hooks/driver_state_inject.sh"
    # AGY runs hooks from the deployed hooks.json directory (.agents/).
    assert (REPO / ".agents" / handler["command"].split()[1]).resolve() == (
        REPO / "scripts" / "agy_hooks" / "driver_state_inject.sh"
    ).resolve()
