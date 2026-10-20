"""Non-interactive AGY selects execution mode and its native Sources config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters import agy


@pytest.fixture
def adapter_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(agy, "require_hook_config", lambda *args, **kwargs: None)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *args: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *args: tmp_path / "agy.log")
    return home


def build(tmp_path: Path, mode: str, tool_config: dict | None = None):
    return agy.AgyAdapter().build_invocation(
        prompt="Call the native Sources verify_words tool once. This is a tool probe.",
        mode=mode,
        cwd=tmp_path,
        model="gemini-3.8-flash-high",
        task_id="sources-probe",
        session_id=None,
        tool_config=tool_config,
    )


@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
def test_noninteractive_command_selects_auto_mode(tmp_path: Path, adapter_home: Path, mode: str) -> None:
    plan = build(tmp_path, mode)

    assert "--mode" in plan.cmd
    assert plan.cmd[plan.cmd.index("--mode") + 1] == "auto"
    assert plan.cmd[plan.cmd.index("--input-format") + 1] == "stream-json"
    assert plan.cmd[plan.cmd.index("--output-format") + 1] == "stream-json"
    assert plan.cmd[plan.cmd.index("--model") + 1] == "gemini-3.8-flash-high"
    assert json.loads(plan.stdin_payload)["event"] == "user"


@pytest.mark.parametrize("route", ["full", "isolated", "permission-only"])
def test_review_command_preserves_read_only_deny_list(tmp_path: Path, adapter_home: Path, route: str) -> None:
    home = tmp_path / "review-home"
    settings = home / ".gemini" / "antigravity-cli" / "settings.json"
    settings.parent.mkdir(parents=True)
    tc = {"agy_home_override": str(home), "review_profile": "code"}
    if route != "permission-only":
        tc["review_access"] = route

    plan = build(tmp_path, "read-only", tc)

    assert "--sandbox" in plan.cmd
    assert "--dangerously-skip-permissions" not in plan.cmd
    assert "--mode" not in plan.cmd
    deny = json.loads(settings.read_text(encoding="utf-8"))["permissions"]["deny"]
    assert "command(*)" in deny
    assert "write_file(*)" in deny


@pytest.mark.parametrize("scoped", [False, True], ids=["ordinary-home", "scoped-home"])
@pytest.mark.parametrize("transport", ["http", "stdio"])
def test_native_sources_config_selected_from_effective_home(
    tmp_path: Path, adapter_home: Path, monkeypatch: pytest.MonkeyPatch, scoped: bool, transport: str
) -> None:
    home = tmp_path / "scoped-home" if scoped else adapter_home
    config = home / ".gemini" / "config" / "mcp_config.json"
    config.parent.mkdir(parents=True)
    server = (
        {"serverUrl": "http://localhost:8766/mcp", "disabled": False}
        if transport == "http"
        else {"command": "/project/.venv/bin/python", "args": ["/project/scripts/mcp_sources_server.py"]}
    )
    config.write_text(json.dumps({"mcpServers": {"sources": server}}), encoding="utf-8")
    # The obsolete app-data config must never win over the CLI's native config.
    app_data = home / ".gemini" / "antigravity-cli"
    app_data.mkdir(parents=True)
    (app_data / "mcp_config.json").write_text('{"mcpServers": {}}', encoding="utf-8")
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(app_data))
    tc = {"mcp_server_names": ["sources"]}
    if scoped:
        tc["agy_home_override"] = str(home)

    plan = build(tmp_path, "read-only", tc)

    effective_home = Path(plan.env_overrides.get("HOME", str(adapter_home)))
    assert effective_home == home
    selected = Path(plan.metadata["agy_mcp_config_path"])
    assert selected == config
    assert selected == effective_home / ".gemini/config/mcp_config.json"
    assert json.loads(selected.read_text(encoding="utf-8")) == {"mcpServers": {"sources": server}}
    assert "--mcp-config" not in plan.cmd  # AGY has no such flag.
