"""Filesystem registration proof is separate from native enforcement."""

from __future__ import annotations

import copy
import json
import os
import shlex
from pathlib import Path

import pytest

from scripts.agent_runtime import agy_hook_config as config
from scripts.common.repo_root import project_interpreter

ROOT = Path(__file__).resolve().parents[2]


def write_guard(path: Path) -> dict:
    data = {config.GUARD_NAME: config.guard_registration()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data


@pytest.mark.parametrize("matcher", ["run_command", "*", "", "^run_command$"])
def test_matchers_cover_native_tool(tmp_path, matcher):
    path = tmp_path / ".agents/hooks.json"
    data = write_guard(path)
    data[config.GUARD_NAME]["PreToolUse"][0]["matcher"] = matcher
    path.write_text(json.dumps(data))
    assert config.check_hook_config((path,)) == config.HookConfigResult("PASS", "guard_registered")


@pytest.mark.parametrize(
    ("failure", "reason"),
    [
        ("absent", "missing_file"),
        ("json", "invalid_json"),
        ("non_object", "invalid_json"),
        ("missing_guard", "missing_guard"),
        ("disabled", "disabled"),
        ("wrong_event", "wrong_event"),
        ("ask_question", "wrong_matcher"),
        ("regex", "invalid_matcher"),
        ("script", "missing_script"),
        ("relative_interpreter", "invalid_interpreter"),
        ("duplicate", "wrong_event"),
        ("shell_command", "invalid_command"),
        ("disabled_command", "disabled"),
        ("disabled_group", "disabled"),
        ("non_string_matcher", "invalid_matcher"),
        ("empty_hooks", "invalid_command"),
    ],
)
def test_bad_registration_refuses(tmp_path, failure, reason):
    path = tmp_path / ".agents/hooks.json"
    if failure == "absent":
        assert config.check_hook_config((path,)).reason == reason
        return
    data = write_guard(path)
    guard = data[config.GUARD_NAME]
    group = guard["PreToolUse"][0]
    hook = group["hooks"][0]
    if failure == "json":
        path.write_text("{")
    elif failure == "non_object":
        path.write_text("[]")
    else:
        if failure == "missing_guard":
            data = {}
        elif failure == "disabled":
            guard["enabled"] = False
        elif failure == "wrong_event":
            guard["PostToolUse"] = guard.pop("PreToolUse")
        elif failure in {"ask_question", "regex", "non_string_matcher"}:
            group["matcher"] = {"ask_question": "ask_question", "regex": "[", "non_string_matcher": None}[failure]
        elif failure == "duplicate":
            guard["PreToolUse"].append(copy.deepcopy(group))
        elif failure == "disabled_command":
            hook["enabled"] = False
        elif failure == "disabled_group":
            group["enabled"] = False
        elif failure == "empty_hooks":
            group["hooks"] = []
        elif failure == "shell_command":
            hook["command"] += " ; true"
        else:
            args = shlex.split(hook["command"])
            args[1 if failure == "script" else 0] = "../absent.py" if failure == "script" else "../.venv/bin/python"
            hook["command"] = shlex.join(args)
        path.write_text(json.dumps(data))
    result = config.check_hook_config((path,))
    assert result.status == "REFUSE"
    assert result.reason == reason


@pytest.mark.parametrize("scoped", [False, True])
def test_existing_effective_candidates_required(tmp_path, scoped):
    cwd, home, scoped_home = tmp_path / "worker", tmp_path / "home", tmp_path / "scoped"
    paths = config.hook_locations(cwd, home, scoped_home if scoped else None)
    write_guard(paths[0])
    assert config.check_hook_config(paths).passed
    write_guard(paths[1])
    assert config.check_hook_config(paths).passed
    data = json.loads(paths[1].read_text())
    data[config.GUARD_NAME]["PreToolUse"][0]["hooks"][0]["command"] = (
        f"../.venv/bin/python ../{config.ENTRY_POINT} --harness agy"
    )
    paths[1].write_text(json.dumps(data))
    assert config.check_hook_config(paths).reason == "relative_home_command"


@pytest.mark.parametrize("scoped", [False, True], ids=["ordinary", "scoped"])
@pytest.mark.parametrize("workspace_state", ["absent", "valid", "invalid"])
@pytest.mark.parametrize("home_state", ["absent", "valid", "invalid"])
@pytest.mark.parametrize("scoped_state", ["absent", "valid", "invalid"])
def test_candidate_existence_matrix(tmp_path, scoped, workspace_state, home_state, scoped_state):
    cwd, home, scoped_home = tmp_path / "worker", tmp_path / "home", tmp_path / "scoped"
    candidates = (
        cwd / ".agents/hooks.json",
        home / ".gemini/config/hooks.json",
        scoped_home / ".gemini/config/hooks.json",
    )
    for path, state in zip(candidates, (workspace_state, home_state, scoped_state), strict=True):
        if state != "absent":
            write_guard(path)
            if state == "invalid":
                path.write_text("{}")
    paths = config.hook_locations(cwd, home, scoped_home if scoped else None)
    assert paths == (candidates[0], candidates[2 if scoped else 1])
    effective_states = (workspace_state, scoped_state if scoped else home_state)
    expected = (
        config.HookConfigResult("REFUSE", "missing_guard")
        if "invalid" in effective_states
        else config.HookConfigResult("PASS", "guard_registered")
        if "valid" in effective_states
        else config.HookConfigResult("REFUSE", "missing_file")
    )
    assert config.check_hook_config(paths) == expected


@pytest.mark.parametrize("candidate", ["workspace", "home"])
@pytest.mark.parametrize("failure", ["disabled", "event", "matcher", "relative", "unresolved", "dangling"])
def test_invalid_candidate_cannot_hide_behind_valid_peer(tmp_path, candidate, failure):
    paths = config.hook_locations(tmp_path / "cwd", tmp_path / "home")
    for path in paths:
        write_guard(path)
    path = paths[0 if candidate == "workspace" else 1]
    data = json.loads(path.read_text())
    guard = data[config.GUARD_NAME]
    group = guard["PreToolUse"][0]
    if failure == "disabled":
        guard["enabled"] = False
    elif failure == "event":
        guard["PostToolUse"] = guard.pop("PreToolUse")
    elif failure == "matcher":
        group["matcher"] = "ask_question"
    elif failure in {"relative", "unresolved"}:
        group["hooks"][0]["command"] = (
            "absent-python absent-guard --harness agy"
            if failure == "relative"
            else "/absent/python /absent/guard --harness agy"
        )
    else:
        path.unlink()
        path.symlink_to(tmp_path / "absent-hooks")
    if failure != "dangling":
        path.write_text(json.dumps(data))
    assert not config.check_hook_config(paths).passed
    with pytest.raises(config.AgyHookConfigError):
        config.require_hook_config(tmp_path / "cwd", tmp_path / "home")


def test_implicit_install_never_repairs_existing_unguarded_workspace(tmp_path):
    cwd = dispatch_tree(tmp_path)
    paths = config.hook_locations(cwd, tmp_path / "home")
    write_guard(paths[1])
    paths[0].parent.mkdir()
    original = b'{"unrelated-hook": {"Stop": []}}\n'
    paths[0].write_bytes(original)
    with pytest.raises(config.AgyHookConfigError, match="missing_guard"):
        config.require_hook_config(cwd, tmp_path / "home", install=True)
    assert paths[0].read_bytes() == original


def test_worker_provisions_absent_workspace_without_home_file(tmp_path):
    cwd = dispatch_tree(tmp_path)
    home = tmp_path / "home"
    config.require_hook_config(cwd, home, install=True)
    assert config.check_hook_config(config.hook_locations(cwd, home)).passed
    assert not home.exists()


@pytest.mark.parametrize("candidate", ["workspace", "home"])
@pytest.mark.parametrize("duplicate", ["guard", "enabled", "command"])
def test_duplicate_members_cannot_hide_disabled_or_wrong_guard(tmp_path, candidate, duplicate):
    paths = config.hook_locations(tmp_path / "cwd", tmp_path / "home")
    for path in paths:
        write_guard(path)
    path = paths[0 if candidate == "workspace" else 1]
    guard = config.guard_registration()
    if duplicate == "guard":
        invalid = {**guard, "enabled": False}
        text = f'{{"{config.GUARD_NAME}": {json.dumps(invalid)}, "{config.GUARD_NAME}": {json.dumps(guard)}}}'
    elif duplicate == "enabled":
        guard["enabled"] = True
        text = json.dumps({config.GUARD_NAME: guard}).replace('"enabled": true', '"enabled": false, "enabled": true')
    else:
        text = json.dumps({config.GUARD_NAME: guard}).replace('"command": ', '"command": "false", "command": ')
    path.write_text(text)
    assert config.check_hook_config(paths) == config.HookConfigResult("REFUSE", "invalid_json")
    with pytest.raises(config.AgyHookConfigError, match="invalid_json"):
        config.require_hook_config(tmp_path / "cwd", tmp_path / "home")


def dispatch_tree(tmp_path):
    primary = tmp_path / "primary"
    cwd = primary / ".worktrees/dispatch/codex/worker"
    cwd.mkdir(parents=True)
    (cwd / ".git").write_text(f"gitdir: {primary}/.git/worktrees/worker\n")
    return cwd


def test_install_twice_byte_equal_preserves_user_and_driver_hooks(tmp_path):
    cwd = dispatch_tree(tmp_path)
    path = cwd / ".agents/hooks.json"
    original = json.loads((ROOT / "agents_extensions/agy/hooks.json").read_text())
    original.pop(config.GUARD_NAME)
    original["user-hook"] = {"Stop": [{"type": "command", "command": "echo user"}]}
    path.parent.mkdir()
    path.write_text(json.dumps(original))
    config.install_worktree_guard(cwd)
    first = path.read_bytes()
    config.install_worktree_guard(cwd)
    assert path.read_bytes() == first
    result = json.loads(first)
    assert {key: value for key, value in result.items() if key != config.GUARD_NAME} == original
    assert list(result).count(config.GUARD_NAME) == 1
    assert path.stat().st_mode & 0o777 == 0o600
    assert config.check_hook_config((path,)).passed
    assert not (cwd / ".venv").exists()


def test_scratch_provision_refuses_foreign_workspace_without_writing(tmp_path, monkeypatch):
    from types import SimpleNamespace

    cwd = tmp_path / "workspace"
    cwd.mkdir()
    monkeypatch.setattr(config.os, "fstat", lambda fd: SimpleNamespace(st_uid=os.geteuid() + 1))
    with pytest.raises(config.AgyHookConfigError, match="unsafe_install_path"):
        config.provision_workspace_guard(cwd)
    assert list(cwd.iterdir()) == []


def test_scratch_provision_refuses_traversal_without_writing(tmp_path):
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(config.AgyHookConfigError, match="unsafe_install_path"):
        config.provision_workspace_guard(cwd / "../other")
    assert list(cwd.iterdir()) == []
    assert list(other.iterdir()) == []


def test_empty_worktree_installs_primary_interpreter(tmp_path):
    cwd = dispatch_tree(tmp_path)
    assert not (cwd / ".agents").exists()
    config.install_worktree_guard(cwd)
    path = cwd / ".agents/hooks.json"
    args = shlex.split(json.loads(path.read_text())[config.GUARD_NAME]["PreToolUse"][0]["hooks"][0]["command"])
    assert args[0] == str(project_interpreter(ROOT))
    assert config.check_hook_config((path,)).passed


@pytest.mark.parametrize("unsafe", ["primary", "symlink"])
def test_install_refuses_non_dispatch_or_symlink(tmp_path, unsafe):
    cwd = tmp_path if unsafe == "primary" else dispatch_tree(tmp_path)
    if unsafe == "symlink":
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (cwd / ".agents").symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(config.AgyHookConfigError):
        config.install_worktree_guard(cwd)


def test_install_does_not_reenable_guard(tmp_path):
    cwd = dispatch_tree(tmp_path)
    path = cwd / ".agents/hooks.json"
    data = write_guard(path)
    data[config.GUARD_NAME]["enabled"] = False
    path.write_text(json.dumps(data))
    before = path.read_bytes()
    config.install_worktree_guard(cwd)
    assert path.read_bytes() == before
    assert config.check_hook_config((path,)).reason == "disabled"


def test_overlay_keeps_existing_driver_hooks():
    data = json.loads((ROOT / "agents_extensions/agy/hooks.json").read_text())
    assert len(data) == 4
    for name, event, matcher, action, timeout in [
        ("driver-state-pin", "PreInvocation", None, "agy-hook", 10),
        ("driver-keep-driving", "Stop", None, "agy-stop-hook", 20),
        ("driver-no-ask-question", "PreToolUse", "ask_question", "agy-pretool-hook", 10),
    ]:
        hook = {
            "type": "command",
            "command": f"sh ../scripts/agy_hooks/driver_state_inject.sh {action}",
            "timeout": timeout,
        }
        assert data[name] == {event: [{"matcher": matcher, "hooks": [hook]}] if matcher else [hook]}
    guard = data[config.GUARD_NAME]["PreToolUse"][0]
    assert guard["matcher"] == "run_command"
    assert guard["hooks"][0]["timeout"] == config.GUARD_TIMEOUT_FLOOR


@pytest.mark.parametrize("timeout", [None, 1, 9, True, "10", 10, 30])
def test_guard_timeout_floor(tmp_path, timeout):
    path = tmp_path / ".agents/hooks.json"
    data = write_guard(path)
    hook = data[config.GUARD_NAME]["PreToolUse"][0]["hooks"][0]
    if timeout is None:
        hook.pop("timeout")
    else:
        hook["timeout"] = timeout
    path.write_text(json.dumps(data))
    expected = (
        config.HookConfigResult("PASS", "guard_registered")
        if timeout in (10, 30)
        else config.HookConfigResult("REFUSE", "invalid_timeout")
    )
    assert config.check_hook_config((path,)) == expected


def test_install_refuses_dotdot_escape_without_writing(tmp_path):
    cwd = dispatch_tree(tmp_path)
    primary = cwd.parents[3]
    other = primary / "other-worktree"
    other.mkdir()
    (other / ".git").write_bytes((cwd / ".git").read_bytes())
    hooks = other / ".agents/hooks.json"
    hooks.parent.mkdir()
    original = b'{"other-hook": {"Stop": []}}\n'
    hooks.write_bytes(original)
    escaped = cwd / "../../../../other-worktree"
    assert escaped.resolve(strict=True) == other
    with pytest.raises(config.AgyHookConfigError, match="install_requires_dispatch_worktree"):
        config.install_worktree_guard(escaped)
    assert hooks.read_bytes() == original
    assert list(hooks.parent.iterdir()) == [hooks]


@pytest.mark.parametrize("component", ["workspace", "ancestor", "agents", "hooks"])
def test_install_refuses_each_symlink_component(tmp_path, component):
    cwd = dispatch_tree(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    original = b'{"other-hook": {"Stop": []}}\n'
    external = elsewhere / "hooks.json"
    external.write_bytes(original)
    if component == "workspace":
        alias = cwd.parent / "alias"
        alias.symlink_to(cwd, target_is_directory=True)
        cwd = alias
    elif component == "ancestor":
        alias = tmp_path / "primary-alias"
        alias.symlink_to(cwd.parents[3], target_is_directory=True)
        cwd = alias / cwd.relative_to(cwd.parents[3])
    elif component == "agents":
        (cwd / ".agents").symlink_to(elsewhere, target_is_directory=True)
    else:
        (cwd / ".agents").mkdir()
        (cwd / ".agents/hooks.json").symlink_to(external)
    with pytest.raises(config.AgyHookConfigError, match="unsafe_install_path"):
        config.install_worktree_guard(cwd)
    assert external.read_bytes() == original


@pytest.mark.parametrize("interrupt", [False, True])
def test_install_atomic_publication_preserves_unrelated_bytes(tmp_path, monkeypatch, interrupt):
    cwd = dispatch_tree(tmp_path)
    hooks = cwd / ".agents/hooks.json"
    hooks.parent.mkdir()
    original = b'{\r\n  "user-hook" : { "Stop": [{"command" : "echo user"}] }\r\n}\r\n'
    hooks.write_bytes(original)
    replace = os.replace

    def publish(source, destination, **kwargs):
        assert hooks.read_bytes() == original
        assert kwargs["src_dir_fd"] == kwargs["dst_dir_fd"]
        assert len(list(hooks.parent.iterdir())) == 2
        if interrupt:
            raise OSError("synthetic interruption before replace")
        replace(source, destination, **kwargs)

    monkeypatch.setattr(config.os, "replace", publish)
    if interrupt:
        with pytest.raises(config.AgyHookConfigError, match="unsafe_install_path"):
            config.install_worktree_guard(cwd)
        assert hooks.read_bytes() == original
    else:
        config.install_worktree_guard(cwd)
        assert hooks.read_bytes().startswith(original[: original.rindex(b"}")])
        assert config.check_hook_config((hooks,)).passed
    assert list(hooks.parent.iterdir()) == [hooks]


def test_gate_and_cli(tmp_path, capsys):
    paths = config.hook_locations(tmp_path / "cwd", tmp_path / "home")
    assert config.check_hook_config(()).reason == "missing_file"
    with pytest.raises(config.AgyHookConfigError, match="missing_file"):
        config.require_hook_config(tmp_path / "cwd", tmp_path / "home")
    assert config.main(["--cwd", str(tmp_path / "cwd"), "--home", str(tmp_path / "home")]) == 2
    assert capsys.readouterr().out == "REFUSE: missing_file\n"
    for path in paths:
        write_guard(path)
    config.require_hook_config(tmp_path / "cwd", tmp_path / "home")
    assert config.main(["--cwd", str(tmp_path / "cwd"), "--home", str(tmp_path / "home")]) == 0
    assert capsys.readouterr().out == "PASS: guard_registered\n"


def test_scoped_home_must_be_absolute(tmp_path):
    with pytest.raises(config.AgyHookConfigError, match="relative_scoped_home"):
        config.require_hook_config(tmp_path, tmp_path / "home", Path("relative-home"))


def test_review_provisioner_writes_absolute_guard_and_keeps_command_denial(tmp_path):
    import os

    from scripts.agent_runtime.review_mcp import _populate_agy_review_home, agy_review_settings

    home = tmp_path / "attempt-home"
    home.mkdir(mode=0o700)
    token = tmp_path / "synthetic-token"
    token.write_text("synthetic")
    fd = os.open(home, os.O_RDONLY | os.O_DIRECTORY)
    try:
        _populate_agy_review_home(
            fd, token, json.dumps({"mcpServers": {"sources": {"env": {"LU_REVIEW_ACCESS": "full"}}}}).encode()
        )
    finally:
        os.close(fd)
    path = home / ".gemini/config/hooks.json"
    assert config.check_hook_config((path,)).passed
    settings = json.loads((home / ".gemini/antigravity-cli/settings.json").read_text())
    assert settings == agy_review_settings("full")
    assert "command(*)" in settings["permissions"]["deny"]


@pytest.mark.parametrize("access", ["isolated", "full"])
def test_review_registration_pass_does_not_certify_hook_execution(tmp_path, access):
    from dataclasses import asdict

    from scripts.agent_runtime.review_mcp import _populate_agy_review_home

    home = tmp_path / "attempt-home"
    home.mkdir(mode=0o700)
    token = tmp_path / "synthetic-token"
    token.write_text("synthetic")
    fd = os.open(home, os.O_RDONLY | os.O_DIRECTORY)
    try:
        _populate_agy_review_home(
            fd, token, json.dumps({"mcpServers": {"sources": {"env": {"LU_REVIEW_ACCESS": access}}}}).encode()
        )
    finally:
        os.close(fd)

    result = config.check_hook_config(config.hook_locations(tmp_path / "workspace", tmp_path / "home", home))
    assert asdict(result) == {"status": "PASS", "reason": "guard_registered"}
    settings = json.loads((home / ".gemini/antigravity-cli/settings.json").read_text())
    assert settings["permissions"]["deny"][:2] == ["command(*)", "write_file(*)"]
