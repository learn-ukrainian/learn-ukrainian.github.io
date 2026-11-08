"""DeepSeek V4.1 Flash runs on an explicit endpoint, refused before spawn when it cannot be paid for (#12376)."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from lu_machinery.api import subscription_usage as usage
from lu_machinery.dispatcher import checks, cli, git, store, worker
from lu_machinery.dispatcher.providers import opencode
from lu_machinery.dispatcher.types import TaskSpec

OPENROUTER_MODEL = "openrouter/deepseek/deepseek-v4.1-flash"
US_PROVIDERS = ["fireworks/us", "baseten/us", "inference-net/us"]  # CTO allow-list, model-assignment.md


@pytest.fixture
def spec(tmp_path):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Reply with exactly: ready\n", encoding="utf-8")
    return TaskSpec("oc", "opencode", "deepseek-v4.1-flash", "high", "read-only", tmp_path, prompt, tmp_path / "final")


@pytest.fixture
def funded(monkeypatch):
    """Both endpoints receive only presence and balance from the private boundary."""
    keys = {"deepseek": True, "openrouter": True}
    balances = {"deepseek": 3.0, "openrouter": 7.0}
    module = SimpleNamespace(
        api_key_present=lambda provider: bool(keys[provider]),
        prepaid_remaining_usd=lambda provider, **kw: balances[provider],
    )
    monkeypatch.setattr(usage, "_private_usage", lambda: module)
    monkeypatch.setattr(opencode, "_resolved_config", lambda env: json.loads(opencode._OPENROUTER_CONFIG))
    monkeypatch.setattr(opencode, "_project_config", lambda *a: [])
    return SimpleNamespace(keys=keys, balances=balances)


@pytest.fixture
def dispatch(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    # The dispatch repository is public; every configured private repository resolves elsewhere.
    monkeypatch.setattr(git, "resolve_repo", lambda key: (
        (tmp_path, dict(key="public", github="example/public")) if key in (None, "public")
        else (tmp_path / "private" / key, dict(key=key, github=f"example/{key}"))))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "deepseek/oc", "a" * 40))
    monkeypatch.setattr(git, "create_worktree", Mock())
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    start = Mock(side_effect=lambda spec, record, prompt, timeout: store.create(
        {**record, "pid": os.getpid(), "process_start": worker._identity(os.getpid())}, prompt,
    ))
    monkeypatch.setattr(worker, "start", start)

    def invoke(*flags, expected=0):
        assert cli.main(["dispatch", "--agent", "deepseek", "--model", "deepseek-v4.1-flash", "--task-id", "oc",
                         "--mode", "read-only", "--prompt", "Reply with exactly: ready", *flags]) == expected
        if expected:
            start.assert_not_called()
            git.create_worktree.assert_not_called()
            assert not (tmp_path / "tasks").exists()
            return None
        return store.read("oc")

    return invoke


def test_openrouter_build_pins_v41_flash_and_allow_list(spec, funded, dispatch):
    invocation = opencode.build(replace(spec, provider="openrouter"), {})
    argv = invocation.argv
    assert argv[argv.index("--model") + 1] == OPENROUTER_MODEL
    config = json.loads(invocation.env["OPENCODE_CONFIG_CONTENT"])
    assert config["small_model"] == OPENROUTER_MODEL  # the title call never reaches another model
    assert config["enabled_providers"] == ["openrouter"]  # no other provider is reachable
    assert {agent["model"] for agent in config["agent"].values()} == {OPENROUTER_MODEL}
    openrouter = config["provider"]["openrouter"]
    assert openrouter["whitelist"] == list(openrouter["models"]) == ["deepseek/deepseek-v4.1-flash"]
    model = openrouter["models"]["deepseek/deepseek-v4.1-flash"]
    routing = {"only": US_PROVIDERS, "allow_fallbacks": False, "data_collection": "deny"}
    assert model["id"] == "deepseek/deepseek-v4.1-flash"
    assert model["options"]["provider"] == model["variants"]["high"]["provider"] == routing
    assert json.loads(invocation.env["OPENCODE_PERMISSION"])["edit"] == "deny"  # read-only lock unchanged
    assert dispatch("--provider", "openrouter")["provider"] == "openrouter"


def test_default_build_stays_direct_api(spec, funded, dispatch):
    for provider in (None, "deepseek"):
        invocation = opencode.build(replace(spec, provider=provider), {})
        assert invocation.argv[invocation.argv.index("--model") + 1] == "deepseek/deepseek-flash"
        assert "OPENCODE_CONFIG_CONTENT" not in invocation.env
    assert dispatch()["provider"] == "deepseek"


@pytest.mark.parametrize("selected", ["deepseek", "openrouter"])
def test_missing_endpoint_access_refused_before_spawn(funded, dispatch, capsys, selected):
    funded.keys[selected] = None
    dispatch("--provider", selected, expected=2)
    err = capsys.readouterr().err
    assert f"opencode_endpoint_no_access: {selected} has no configured API key" in err
    assert "stub-" not in err


@pytest.mark.parametrize("selected", ["deepseek", "openrouter"])
@pytest.mark.parametrize("balance", [0.99, None])
def test_below_floor_refused_before_spawn(funded, dispatch, capsys, selected, balance):
    funded.balances[selected] = balance
    dispatch("--provider", selected, expected=2)
    err = capsys.readouterr().err
    if balance is None:
        assert f"opencode_endpoint_balance_unknown: {selected} balance could not be read" in err
    else:
        assert f"opencode_endpoint_below_floor: {selected} balance $0.99 is below the $1.00 floor" in err
    other = ({"deepseek", "openrouter"} - {selected}).pop()
    funded.balances[other] = 1.00  # the other endpoint exactly at its floor is admitted, never substituted
    assert opencode.endpoint_refusal(other) is None


@pytest.mark.parametrize("provider", ["openrouter/deepseek", "DeepSeek", "native"])
def test_unknown_provider_refused(spec, funded, dispatch, capsys, provider):
    with pytest.raises(ValueError, match="opencode_endpoint_unknown"):
        opencode.build(replace(spec, provider=provider), {})
    dispatch("--provider", provider, expected=2)
    assert "opencode_endpoint_unknown" in capsys.readouterr().err


@pytest.mark.parametrize("provider", ["deepseek", "openrouter"])
def test_endpoint_absent_private_binding_refuses_without_credential_fallback(monkeypatch, provider):
    monkeypatch.setattr(usage, "_private_usage", lambda: None)
    assert opencode.endpoint_refusal(provider) == (
        f"opencode_endpoint_balance_unknown: {provider} balance could not be read"
    )
