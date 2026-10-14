"""An ordinary Claude worker authenticates as its account label's account (#10619).

The default label (or none) keeps the host login and the base plan
byte-for-byte (a checked-in snapshot of the base behaviour). Label ``b`` runs
the worker with the bound account's verified login directory as its only
credential source: a conflicting ambient credential, a competing key source in
the login directory's user settings, a checkout setting that changes the
effective authentication, or an unknown label is refused with a value-free
code before the worker spawns. The fake ``claude`` runs through the real
runner and sanitizer. For ``auth status`` it resolves ``--settings``,
``--setting-sources`` and the user, project and local settings files the way
Claude Code 2.1.299 did in a fixture probe; for a run it records the argv and
environment it received. Where the installed Claude CLI is present, the real
``claude auth status`` and ``claude mcp list`` check the same plans. Every
identity, token and directory is a fixture.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from scripts.agent_runtime import env_sanitize, runner
from scripts.agent_runtime.adapters import claude
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.claude import LABELLED_ACCOUNT_SETTING_SOURCES, ClaudeAdapter
from scripts.agent_runtime.attempt_boundary import CLAUDE_ACCOUNT_REFUSAL_CODES, ClaudeAccountRefused
from scripts.agent_runtime.env_sanitize import build_agent_env
from tests.agent_runtime.test_attempt_boundary import (
    BOUND_ACCOUNT_UUID,
    CLAUDE_AMBIENT_AUTH,
    DEFAULT_ACCOUNT_UUID,
    _credentials,
    _mock_selected_account_runtime,
    _private_json,
)

_GOLDEN = Path(__file__).resolve().parents[1] / "fixtures" / "claude_default_account_plan.json"
_REAL_CLAUDE = shutil.which("claude")

_FAKE_CLAUDE = textwrap.dedent(
    """
    import json, os, sys

    argv = sys.argv[1:]
    if "--version" in argv:
        print("2.1.289 (Claude Code)")
        sys.exit(0)

    def option(name):
        return argv[argv.index(name) + 1] if name in argv else None

    def load(path):
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            return {}

    log = os.environ["LU_FAKE_CLAUDE_DUMP"]
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.environ["HOME"], ".claude")
    if argv[-3:] == ["auth", "status", "--json"]:
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"kind": "auth_status", "argv": argv, "cwd": os.getcwd()}) + "\\n")
        mode = os.environ.get("LU_FAKE_CLAUDE_STATUS_MODE", "")
        if mode == "garbage":
            print("not json")
            sys.exit(1)
        sources = (option("--setting-sources") or "user,project,local").split(",")
        scopes = []  # (scope, settings) in Claude Code's load order, the flag last
        if "user" in sources:
            scopes.append(("user", load(os.path.join(config_dir, "settings.json"))))
        if "project" in sources:
            scopes.append(("project", load(os.path.join(os.getcwd(), ".claude", "settings.json"))))
        if "local" in sources:
            scopes.append(("local", load(os.path.join(os.getcwd(), ".claude", "settings.local.json"))))
        flag = option("--settings")
        if flag:
            scopes.append(("flag", json.loads(flag)))
        env, helper = dict(os.environ), None
        for scope, settings in scopes:
            for name, value in (settings.get("env") or {}).items():
                # Probe: project and local scopes applied provider switches, not keys or endpoints.
                if scope in ("user", "flag") or name.startswith("CLAUDE_CODE_USE_"):
                    env[name] = value
            helper = settings.get("apiKeyHelper") or helper
        status = {"loggedIn": True, "apiProvider": "firstParty", "configDirectory": config_dir}
        if env.get("CLAUDE_CODE_USE_BEDROCK"):
            status.update(authMethod="third_party", apiProvider="bedrock")
        elif helper:
            status["authMethod"] = "api_key_helper"
        elif env.get("ANTHROPIC_API_KEY"):
            status["authMethod"] = "api_key"
        elif os.path.exists(os.path.join(config_dir, ".credentials.json")):
            status["authMethod"] = "claude.ai"
        else:
            status = {"loggedIn": False, "authMethod": "none", "apiProvider": "firstParty"}
        if mode == "other_dir":
            status["configDirectory"] = os.environ["HOME"]
        print(json.dumps(status))
        sys.exit(0 if status["loggedIn"] else 1)
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"kind": "run", "argv": argv, "env": dict(os.environ)}) + "\\n")
    session = "00000000-0000-4000-8000-000000010619"
    print(json.dumps({"type": "system", "subtype": "init", "session_id": session}))
    if os.environ.get("LU_FAKE_CLAUDE_FAIL_RUN"):
        print(json.dumps({"type": "result", "subtype": "error_during_execution", "is_error": True,
                          "result": "Failed to authenticate", "session_id": session}))
        sys.exit(1)
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "done", "session_id": session}))
    """
)

# Labelled user settings: (i) an API key in env, (ii) a key helper, (iii) clean.
USER_SETTINGS = {
    "env_api_key": {"env": {"ANTHROPIC_API_KEY": "fixture-settings-" + "k" * 30}},
    "api_key_helper": {"apiKeyHelper": "fixture-helper-command"},
    "clean": {"model": "fixture-model", "env": {"FIXTURE_FLAG": "1"}},
}


@pytest.fixture
def accounts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """The default account in HOME and account b under its own bound login directory."""
    home = tmp_path / "home"
    home.mkdir(mode=0o700)
    monkeypatch.setenv("HOME", str(home))
    identities, calls = _mock_selected_account_runtime(tmp_path, monkeypatch)
    for key in (*CLAUDE_AMBIENT_AUTH, "CLAUDE_CONFIG_DIR"):
        monkeypatch.delenv(key, raising=False)
    found = SimpleNamespace(
        home=home,
        default_token="fixture-default-" + "d" * 30,
        bound_token="fixture-bound-" + "b" * 30,
        config_dir=tmp_path / "bound-config",
        profile_calls=calls,
    )
    identities.update({found.default_token: DEFAULT_ACCOUNT_UUID, found.bound_token: BOUND_ACCOUNT_UUID})
    _credentials(home / ".claude" / ".credentials.json", found.default_token)
    (home / ".claude").chmod(0o700)
    _private_json(home / ".claude.json", {"oauthAccount": {"accountUuid": DEFAULT_ACCOUNT_UUID}})
    found.config_dir.mkdir(mode=0o700)
    _credentials(found.config_dir / ".credentials.json", found.bound_token)
    _private_json(found.config_dir / ".claude.json", {"oauthAccount": {"accountUuid": BOUND_ACCOUNT_UUID}})
    binding = tmp_path / "private-config" / "claude_accounts.json"
    _private_json(
        binding,
        {
            "schema_version": 1,
            "accounts": {"b": {"config_dir": str(found.config_dir), "account_uuid": BOUND_ACCOUNT_UUID}},
        },
    )
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(binding))
    script = tmp_path / "fake_claude.py"
    script.write_text(_FAKE_CLAUDE, encoding="utf-8")
    found.binary = tmp_path / "claude"
    found.binary.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
    found.binary.chmod(0o755)
    found.dump = tmp_path / "dump.jsonl"
    monkeypatch.setenv("LU_FAKE_CLAUDE_DUMP", str(found.dump))
    found.workdir = tmp_path / "work"
    found.workdir.mkdir()
    return found


def _calls(accounts: SimpleNamespace, kind: str) -> list[dict]:
    if not accounts.dump.exists():
        return []
    calls = [json.loads(line) for line in accounts.dump.read_text(encoding="utf-8").splitlines()]
    return [call for call in calls if call["kind"] == kind]


def _run(accounts: SimpleNamespace) -> dict:
    (spawn,) = _calls(accounts, "run")
    return spawn


def _invoke(accounts: SimpleNamespace, **tool_config) -> tuple[runner.Result, list]:
    with (
        patch.object(runner, "has_headroom", return_value=(True, "")),
        patch.object(runner, "write_record") as record,
    ):
        result = runner.invoke(
            "claude",
            "do the task",
            mode="workspace-write",
            cwd=accounts.workdir,
            tool_config={"cmd_prefix": [str(accounts.binary)], **tool_config},
            hard_timeout=60,
        )
    return result, record.call_args_list


def _plan(accounts: SimpleNamespace, **tool_config) -> InvocationPlan:
    return ClaudeAdapter().build_invocation(
        prompt="do the task",
        mode="workspace-write",
        cwd=accounts.workdir,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"cmd_prefix": [str(accounts.binary)], **tool_config},
    )


def _user_settings(accounts: SimpleNamespace, settings: dict, *, home_too: bool = False) -> None:
    """Write the labelled account's user settings (and optionally the default account's)."""
    _private_json(accounts.config_dir / "settings.json", settings)
    if home_too:
        _private_json(accounts.home / ".claude" / "settings.json", settings)


def test_bound_label_runs_with_only_the_bound_login_directory(accounts):
    """AC-01: label b's worker gets the bound login directory and no other credential source."""
    result, records = _invoke(accounts, claude_account="b")

    assert result.ok is True
    seen = _run(accounts)
    env = seen["env"]
    assert env["CLAUDE_CONFIG_DIR"] == str(accounts.config_dir)
    assert not {name for name in env if name.upper() in CLAUDE_AMBIENT_AUTH or name.upper().startswith("ANTHROPIC_")}
    assert not [name for name, value in env.items() if accounts.bound_token in value or accounts.default_token in value]
    # Verified against the provider with the bound account's own login only.
    assert accounts.profile_calls == [accounts.bound_token]
    # Neither the directory nor the token reaches argv, the usage record or the result.
    rendered = repr(seen["argv"]) + repr(records) + repr(result)
    assert str(accounts.config_dir) not in rendered
    assert accounts.bound_token not in rendered


def test_bound_label_strips_an_inherited_api_key_name_variant(accounts, monkeypatch):
    """The sanitizer keeps the login directory the only source even for a key the check cannot see."""
    monkeypatch.setenv("anthropic_api_key", "fixture-ambient-" + "k" * 30)

    _invoke(accounts, claude_account="b")

    env = _run(accounts)["env"]
    assert env["CLAUDE_CONFIG_DIR"] == str(accounts.config_dir)
    assert "anthropic_api_key" not in env


@pytest.mark.parametrize("case", ["env_api_key", "api_key_helper"])
def test_bound_label_user_settings_key_source_is_refused(accounts, case):
    """AC-01 (i)/(ii): a key or key helper in the labelled user settings is refused value-free, before spawn.

    On fa814a2919 these did not raise: the plan only set the login directory,
    and Claude Code then reported ``api_key`` / ``api_key_helper`` for it.
    """
    _user_settings(accounts, USER_SETTINGS[case])

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_settings_credential_source"
    assert str(refused.value) == "claude_account_settings_credential_source"
    assert "fixture" not in repr(refused.value.__context__) + repr(refused.value.__cause__)
    assert not accounts.dump.exists()
    assert accounts.profile_calls == []


@pytest.mark.parametrize(
    "settings",
    [
        {"env": {"ANTHROPIC_BASE_URL": "https://fixture.invalid"}},
        {"env": {"ANTHROPIC_AUTH_TOKEN": "fixture-token-" + "t" * 30}},
        {"env": {"CLAUDE_CODE_OAUTH_TOKEN": "fixture-token-" + "o" * 30}},
        {"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}},
        {"env": {"CLAUDE_CODE_USE_VERTEX": "1"}},
        {"env": {"CLAUDE_CODE_USE_FOUNDRY": "1"}},
        {"env": {"ANTHROPIC_BEDROCK_BASE_URL": "https://fixture.invalid"}},
        {"env": {"ANTHROPIC_VERTEX_PROJECT_ID": "fixture"}},
        {"env": {"CLAUDE_CONFIG_DIR": "/fixture"}},
        {"env": {"anthropic_api_key": "fixture-key-" + "k" * 30}},
        {"awsAuthRefresh": "fixture-command"},
        {"awsCredentialExport": "fixture-command"},
    ],
)
def test_bound_label_user_settings_credential_class_is_refused(accounts, settings):
    """Every credential, provider or endpoint setting in the labelled user scope is refused."""
    _user_settings(accounts, settings)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_settings_credential_source"
    assert accounts.profile_calls == []


@pytest.mark.parametrize(
    ("content", "mode", "code"),
    [
        ("{not json", 0o600, "claude_account_settings_invalid"),
        ('{"env": ["ANTHROPIC_API_KEY"]}', 0o600, "claude_account_settings_invalid"),
        ("[]", 0o600, "claude_account_settings_invalid"),
        ("{}", 0o620, "claude_account_settings_not_private"),
    ],
)
def test_bound_label_unreadable_user_settings_fail_closed(accounts, content, mode, code):
    """Settings that cannot be read as owner-controlled JSON are refused, not skipped."""
    path = accounts.config_dir / "settings.json"
    path.write_text(content, encoding="utf-8")
    path.chmod(mode)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == code


def test_bound_label_clean_user_settings_is_admitted(accounts):
    """AC-01 (iii): clean user settings run, with the user scope unloaded and the auth method verified."""
    _user_settings(accounts, USER_SETTINGS["clean"])
    accounts.config_dir.joinpath("settings.json").chmod(0o644)  # readable by others is fine

    result, _ = _invoke(accounts, claude_account="b")

    assert result.ok is True
    argv = _run(accounts)["argv"]
    assert argv[argv.index("--setting-sources") + 1] == LABELLED_ACCOUNT_SETTING_SOURCES == "project,local"
    (status,) = _calls(accounts, "auth_status")
    assert status["cwd"] == str(accounts.workdir)
    assert status["argv"][-5:] == ["--setting-sources", "project,local", "auth", "status", "--json"]
    assert status["argv"][status["argv"].index("--settings") + 1] == argv[argv.index("--settings") + 1]


@pytest.mark.parametrize(
    ("name", "settings"),
    [
        ("settings.local.json", {"apiKeyHelper": "fixture-helper-command"}),
        ("settings.json", {"apiKeyHelper": "fixture-helper-command"}),
        ("settings.local.json", {"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}}),
    ],
)
def test_bound_label_checkout_setting_that_changes_auth_is_refused(accounts, name, settings):
    """A project or local setting the run still loads cannot switch its authentication."""
    _private_json(accounts.workdir / ".claude" / name, settings)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_auth_method_conflict"
    assert len(_calls(accounts, "auth_status")) == 1
    assert _calls(accounts, "run") == []


@pytest.mark.parametrize(
    ("mode", "code"),
    [("garbage", "claude_account_auth_status_unavailable"), ("other_dir", "claude_account_auth_method_conflict")],
)
def test_bound_label_unconfirmed_auth_status_is_refused(accounts, monkeypatch, mode, code):
    """No parseable status, or a status for another directory, never admits the run."""
    monkeypatch.setenv("LU_FAKE_CLAUDE_STATUS_MODE", mode)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == code
    assert _calls(accounts, "run") == []


def test_bound_label_logged_out_status_is_refused(accounts):
    accounts.config_dir.joinpath(".credentials.json").unlink()
    with patch.object(claude, "_claude_account_login_dir", return_value=str(accounts.config_dir)):
        with pytest.raises(ClaudeAccountRefused) as refused:
            _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_auth_method_conflict"


def test_bound_label_loads_no_user_hooks_permissions_or_mcp_servers(accounts):
    """Stance: the labelled user scope (hooks, permission rules, MCP servers) never applies; it is not refused.

    The run gets the harness settings and the checkout's settings only, so it
    has no more authority than a default run; the allow list names no user
    server.
    """
    _user_settings(
        accounts,
        {
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "/fixture/hook"}]}]},
            "permissions": {"allow": ["mcp__fixtureuser__*", "NotebookEdit"]},
        },
    )
    global_config = json.loads((accounts.config_dir / ".claude.json").read_text(encoding="utf-8"))
    global_config["mcpServers"] = {"fixtureuser": {"type": "stdio", "command": "/bin/true", "args": []}}
    _private_json(accounts.config_dir / ".claude.json", global_config)

    plan = _plan(accounts, claude_account="b")

    sources = [plan.cmd[i + 1] for i, arg in enumerate(plan.cmd) if arg == "--setting-sources"]
    assert sources == ["project,local"]
    allowed = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert not [tool for tool in allowed if "fixtureuser" in tool or tool == "NotebookEdit"]
    assert "--setting-sources" not in _plan(accounts).cmd


def test_bound_label_auth_failure_is_a_failure_not_a_retry_as_another_account(accounts, monkeypatch):
    """A mid-run auth failure (e.g. a failed token refresh) fails the run; nothing re-runs it on the host login.

    The runner's failover re-sends the same tool_config, label included
    (``failover.tool_config_with_route``), and configures no Claude chain.
    """
    monkeypatch.setenv("LU_FAKE_CLAUDE_FAIL_RUN", "1")

    result, _ = _invoke(accounts, claude_account="b")

    assert result.ok is False
    (spawn,) = _calls(accounts, "run")
    assert spawn["env"]["CLAUDE_CONFIG_DIR"] == str(accounts.config_dir)


def _golden_view(accounts: SimpleNamespace, plan: InvocationPlan) -> dict:
    """The plan in the snapshot's normalised form; the sanitizer runs with the five ambient variables set."""
    ambient = {
        "CLAUDE_CONFIG_DIR": str(accounts.home / "elsewhere"),
        "CLAUDE_CODE_OAUTH_TOKEN": "fixture-ambient-" + "o" * 30,
        "ANTHROPIC_API_KEY": "fixture-ambient-" + "k" * 30,
        "ANTHROPIC_AUTH_TOKEN": "fixture-ambient-" + "t" * 30,
        "CLAUDE_API_KEY": "fixture-ambient-" + "c" * 30,
    }
    with patch.dict(os.environ, ambient):
        env = build_agent_env(provider="claude", overrides=plan.env_overrides)
    cmd = list(plan.cmd)
    settings = cmd.index("--settings") + 1
    assert cmd[settings] == claude._headless_worker_settings(publish_guard=False)
    cmd[settings] = "<worker-settings>"
    tmp = str(accounts.workdir.parent)
    return {
        "cmd": [arg.replace(tmp, "<tmp>") for arg in cmd],
        "env_overrides": dict(plan.env_overrides),
        "env_unsets": list(plan.env_unsets),
        "liveness_paths": [str(path).replace(tmp, "<tmp>") for path in plan.liveness_paths],
        "metadata": plan.metadata,
        "sanitized_env": {key: env.get(key) for key in sorted({*ambient, *plan.env_overrides})},
        "stdin_payload": plan.stdin_payload,
    }


@pytest.mark.parametrize("case", sorted(USER_SETTINGS))
@pytest.mark.parametrize("tool_config", [{}, {"claude_account": "a"}], ids=["omitted", "explicit_default"])
def test_default_label_plan_matches_the_base_snapshot(accounts, monkeypatch, tool_config, case):
    """AC-02 golden: the default account's plan and sanitised environment equal the base snapshot.

    The snapshot was built from the base before this change; the user
    settings of either account never alter the default plan, and nothing
    is verified or probed for it.
    """
    _user_settings(accounts, USER_SETTINGS[case], home_too=True)
    expected = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    expected.pop("_provenance")

    assert _golden_view(accounts, _plan(accounts, **tool_config)) == expected
    assert accounts.profile_calls == []
    assert _calls(accounts, "auth_status") == []


@pytest.mark.parametrize("tool_config", [{}, {"claude_account": "a"}], ids=["omitted", "explicit_default"])
def test_default_label_environment_keeps_existing_sanitisation(accounts, monkeypatch, tool_config):
    """The default account keeps the host login and the existing sanitisation, unverified."""
    other = accounts.home / "elsewhere"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(other))
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fixture-ambient-" + "o" * 30)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-ambient-" + "k" * 30)
    monkeypatch.setattr(env_sanitize, "_isolated_git_env", lambda *_a, **_k: {"GIT_CONFIG_NOSYSTEM": "1"})

    plan = _plan(accounts, **tool_config)

    assert "CLAUDE_CONFIG_DIR" not in plan.env_overrides
    env = build_agent_env(provider="claude", overrides=plan.env_overrides)
    # Existing default sanitisation: no config directory or OAuth token; the API key passes.
    assert "CLAUDE_CONFIG_DIR" not in env and "CLAUDE_CODE_OAUTH_TOKEN" not in env
    assert env["ANTHROPIC_API_KEY"] == "fixture-ambient-" + "k" * 30
    assert accounts.profile_calls == []


@pytest.mark.parametrize("name", [*CLAUDE_AMBIENT_AUTH, "CLAUDE_CONFIG_DIR"])
def test_conflicting_ambient_credential_with_bound_label_is_refused(accounts, monkeypatch, name):
    """AC-01: an ambient token, API key or other config directory is refused value-free, before spawn."""
    value = str(accounts.home / ".claude") if name == "CLAUDE_CONFIG_DIR" else "fixture-ambient-" + "e" * 30
    monkeypatch.setenv(name, value)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_ambient_conflict"
    assert str(refused.value) == "claude_account_ambient_conflict"
    assert not accounts.dump.exists()
    assert accounts.profile_calls == []


@pytest.mark.parametrize("label", ["c", "B", "", 2])
def test_unknown_label_is_refused_before_any_probe(accounts, monkeypatch, label):
    """AC-01: an unknown label never reaches the version probe, the binding or a spawn."""

    def no_probe(*_args, **_kwargs):
        raise AssertionError("probed before the label was refused")

    monkeypatch.setattr(claude, "_ensure_supported_claude_cli_version", no_probe)
    monkeypatch.setattr(claude, "_default_claude_bin", no_probe)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account=label)

    assert refused.value.code == "claude_account_unknown"
    assert accounts.profile_calls == []


def test_bound_label_on_an_unsealed_isolation_route_is_refused(accounts):
    """A bridge isolation run builds its own environment, so it cannot honour another account."""
    with pytest.raises(ClaudeAccountRefused) as refused:
        claude._claude_account_login_dir({"claude_account": "b", "review_isolation": True})

    assert refused.value.code == "claude_account_route_unsealed"
    assert accounts.profile_calls == []


def test_sealed_attempt_keeps_selecting_its_account_at_its_boundary(accounts):
    """The attempt boundary authenticates a sealed attempt; the adapter adds no login directory."""
    assert claude._claude_account_login_dir({"claude_account": "b", "review_attempt_boundary": object()}) is None
    assert accounts.profile_calls == []


def test_bound_label_binding_refusal_is_value_free(accounts):
    _credentials(accounts.config_dir / ".credentials.json", accounts.default_token)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_unverified"
    assert refused.value.code in CLAUDE_ACCOUNT_REFUSAL_CODES
    assert str(accounts.config_dir) not in str(refused.value)


def test_new_refusal_codes_are_registered():
    assert {
        "claude_account_settings_credential_source",
        "claude_account_auth_method_conflict",
        "claude_account_auth_status_unavailable",
        "claude_account_settings_invalid",
        "claude_account_settings_not_private",
    } <= CLAUDE_ACCOUNT_REFUSAL_CODES


def test_bound_label_session_and_liveness_use_the_login_directory(accounts):
    """Tool-call recovery and liveness read the bound account's sessions, not the host's."""
    plan = _plan(accounts, claude_account="b")
    session = "00000000-0000-4000-8000-000000010619"
    project = accounts.config_dir / "projects" / claude._claude_project_slug(accounts.workdir)
    project.mkdir(parents=True)
    tool_use = {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "a"}}
    (project / f"{session}.jsonl").write_text(
        json.dumps({"type": "assistant", "message": {"content": [tool_use]}}) + "\n", encoding="utf-8"
    )
    (accounts.home / ".claude" / "projects" / "host-project").mkdir(parents=True)

    stdout = json.dumps(
        {"type": "result", "subtype": "success", "is_error": False, "result": "ok", "session_id": session}
    )
    parsed = ClaudeAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None, plan=plan)

    assert [call["name"] for call in parsed.tool_calls] == ["Read"]
    assert ClaudeAdapter().liveness_signal_paths(plan) == (project,)


def test_sanitizer_admits_the_login_directory_only_from_the_claude_adapter(monkeypatch):
    """The override survives the token-shape filter; ambient or other-provider values never pass."""
    login_dir = "/fixture/desk-b/claude"  # contains a token-shaped "sk-b" substring
    monkeypatch.setenv("CLAUDE_API_KEY", "fixture-ambient-" + "k" * 30)

    env = build_agent_env(provider="claude", overrides={"CLAUDE_CONFIG_DIR": login_dir})
    assert env["CLAUDE_CONFIG_DIR"] == login_dir
    assert "CLAUDE_API_KEY" not in env

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", login_dir)
    assert "CLAUDE_CONFIG_DIR" not in build_agent_env(provider="claude")
    assert build_agent_env(provider="claude")["CLAUDE_API_KEY"] == "fixture-ambient-" + "k" * 30
    assert "CLAUDE_CONFIG_DIR" not in build_agent_env(provider="codex", overrides={"CLAUDE_CONFIG_DIR": login_dir})
    assert os.environ["CLAUDE_CONFIG_DIR"] == login_dir


# --- The installed Claude CLI, where present ------------------------------------------------------


@pytest.fixture
def real_cli(accounts: SimpleNamespace) -> SimpleNamespace:
    if not _REAL_CLAUDE:
        pytest.skip("Claude CLI is not installed; the fake CLI above covers the same plans")
    accounts.binary = Path(_REAL_CLAUDE)
    # The CLI reports a subscription login only for a token carrying inference scope.
    oauth = json.loads((accounts.config_dir / ".credentials.json").read_text(encoding="utf-8"))["claudeAiOauth"]
    oauth.update(scopes=["user:inference", "user:profile"], subscriptionType="max")
    _private_json(accounts.config_dir / ".credentials.json", {"claudeAiOauth": oauth})
    return accounts


def _real(accounts: SimpleNamespace, *args: str, sources: bool = True) -> str:
    settings = claude._headless_worker_settings(publish_guard=False)
    argv = [str(accounts.binary), "--settings", settings]
    if sources:
        argv += ["--setting-sources", LABELLED_ACCOUNT_SETTING_SOURCES]
    env = build_agent_env(provider="claude", overrides={"CLAUDE_CONFIG_DIR": str(accounts.config_dir)})
    done = subprocess.run(
        [*argv, *args], cwd=accounts.workdir, env=env, capture_output=True, text=True, timeout=60, check=False
    )
    return done.stdout


def test_real_cli_admits_a_clean_bound_login(real_cli):
    _user_settings(real_cli, USER_SETTINGS["clean"])

    plan = _plan(real_cli, claude_account="b")

    assert plan.env_overrides["CLAUDE_CONFIG_DIR"] == str(real_cli.config_dir)


@pytest.mark.parametrize(
    ("name", "settings"),
    [
        ("settings.local.json", {"apiKeyHelper": "fixture-helper-command"}),
        ("settings.local.json", {"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}}),
    ],
)
def test_real_cli_checkout_setting_that_changes_auth_is_refused(real_cli, name, settings):
    _private_json(real_cli.workdir / ".claude" / name, settings)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(real_cli, claude_account="b")

    assert refused.value.code == "claude_account_auth_method_conflict"


@pytest.mark.parametrize("case", ["env_api_key", "api_key_helper"])
def test_real_cli_unloads_the_labelled_user_scope(real_cli, case):
    """The user-scope key source the static check refuses is also not loaded by the labelled run's arguments."""
    _user_settings(real_cli, USER_SETTINGS[case])

    loaded = json.loads(_real(real_cli, "auth", "status", "--json", sources=False))
    unloaded = json.loads(_real(real_cli, "auth", "status", "--json"))

    assert loaded["authMethod"] in {"api_key", "api_key_helper"}  # the fixture is effective
    assert unloaded["authMethod"] == "claude.ai"


def test_real_cli_labelled_run_loads_no_user_mcp_server(real_cli):
    global_config = json.loads((real_cli.config_dir / ".claude.json").read_text(encoding="utf-8"))
    global_config["mcpServers"] = {"fixtureuser": {"type": "stdio", "command": "/bin/true", "args": []}}
    _private_json(real_cli.config_dir / ".claude.json", global_config)

    assert "fixtureuser" in _real(real_cli, "mcp", "list", sources=False)
    assert "fixtureuser" not in _real(real_cli, "mcp", "list")
