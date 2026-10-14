"""An ordinary Claude worker authenticates as its account label's account (#10619).

The default label (or none) keeps the host login byte-for-byte. Label ``b``
runs the worker with the bound account's verified login directory as its only
credential source; a conflicting ambient credential or an unknown label is
refused with a value-free code before anything is probed or spawned. The
fake ``claude`` runs through the real runner and sanitizer and dumps the
environment it received. Every identity, token and directory is a fixture.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from scripts.agent_runtime import env_sanitize, runner
from scripts.agent_runtime.adapters import claude
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.claude import ClaudeAdapter
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

_FAKE_CLAUDE = textwrap.dedent(
    """
    import json, os, sys

    argv = sys.argv[1:]
    if "--version" in argv:
        print("2.1.289 (Claude Code)")
        sys.exit(0)
    with open(os.environ["LU_FAKE_CLAUDE_DUMP"], "w", encoding="utf-8") as handle:
        json.dump({"argv": argv, "env": dict(os.environ)}, handle)
    session = "00000000-0000-4000-8000-000000010619"
    print(json.dumps({"type": "system", "subtype": "init", "session_id": session}))
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "done", "session_id": session}))
    """
)


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
    found.dump = tmp_path / "dump.json"
    monkeypatch.setenv("LU_FAKE_CLAUDE_DUMP", str(found.dump))
    found.workdir = tmp_path / "work"
    found.workdir.mkdir()
    return found


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


def test_bound_label_runs_with_only_the_bound_login_directory(accounts):
    """AC-01: label b's worker gets the bound login directory and no other credential source."""
    result, records = _invoke(accounts, claude_account="b")

    assert result.ok is True
    seen = json.loads(accounts.dump.read_text(encoding="utf-8"))
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

    env = json.loads(accounts.dump.read_text(encoding="utf-8"))["env"]
    assert env["CLAUDE_CONFIG_DIR"] == str(accounts.config_dir)
    assert "anthropic_api_key" not in env


@pytest.mark.parametrize("tool_config", [{}, {"claude_account": "a"}], ids=["omitted", "explicit_default"])
def test_default_label_environment_is_unchanged(accounts, monkeypatch, tool_config):
    """Golden: the default account keeps the host login and the existing sanitisation, unverified."""
    other = accounts.home / "elsewhere"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(other))
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fixture-ambient-" + "o" * 30)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-ambient-" + "k" * 30)
    monkeypatch.setattr(env_sanitize, "_isolated_git_env", lambda *_a, **_k: {"GIT_CONFIG_NOSYSTEM": "1"})

    base = _plan(accounts)
    plan = _plan(accounts, **tool_config)

    assert (plan.cmd, dict(plan.env_overrides), plan.env_unsets, plan.liveness_paths, plan.metadata) == (
        base.cmd,
        dict(base.env_overrides),
        base.env_unsets,
        base.liveness_paths,
        base.metadata,
    )
    assert "CLAUDE_CONFIG_DIR" not in plan.env_overrides
    env = build_agent_env(provider="claude", overrides=plan.env_overrides)
    assert env == build_agent_env(provider="claude", overrides=base.env_overrides)
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
