"""Runtime command diagnostics must not retain argv values (#10751)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from agent_runtime.adapters.codex import CodexAdapter
from agent_runtime.adapters.cursor import CursorAdapter
from agent_runtime.adapters.deepseek import DeepSeekAdapter
from agent_runtime.adapters.gemini import GeminiAdapter
from agent_runtime.adapters.glm import GlmAdapter
from agent_runtime.adapters.grok_build import GrokBuildAdapter
from agent_runtime.adapters.hermes_deepseek import HermesDeepSeekAdapter
from agent_runtime.adapters.hermes_grok import HermesGrokAdapter
from agent_runtime.adapters.hermes_qwen import HermesQwenAdapter
from scripts.agent_runtime.adapters import acpx as acpx_module
from scripts.agent_runtime.adapters import agy as agy_module
from scripts.agent_runtime.adapters.acpx import AcpxGemmaShadowAdapter
from scripts.agent_runtime.adapters.agy import AgyAdapter
from scripts.agent_runtime.adapters.kimi import KimiAdapter
from tests.agent_runtime.adapters.kimi_admitted import admitted_tool_config


@pytest.mark.parametrize(
    ("adapter_type", "expected_message"),
    [
        (DeepSeekAdapter, "deepseek invocation"),
        (GlmAdapter, "glm invocation"),
        (KimiAdapter, "kimi invocation"),
    ],
)
def test_sibling_invocation_logs_constant_message(tmp_path, monkeypatch, caplog, adapter_type, expected_message):
    for variable in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    environment_value = "private-environment-value"
    monkeypatch.setenv("LOG_REDACTION_TEST_VALUE", environment_value)
    secret = "secret-looking-command-option-value"
    adapter = adapter_type()
    tool_config = {}
    if adapter_type is KimiAdapter:
        binary = tmp_path / "private-executable-value"
        binary.write_text("#!/bin/sh\n", encoding="utf-8")
        binary.chmod(0o755)
        monkeypatch.setenv("LEARN_UK_KIMI_BIN", str(binary))
        tool_config = admitted_tool_config(tmp_path, {"kimi_add_dirs": [secret]})
    effort = secret if adapter_type in (DeepSeekAdapter, GlmAdapter) else None
    with (
        patch(f"{adapter_type.__module__}.shutil.which", return_value=str(tmp_path / "runtime-cli")),
        caplog.at_level(logging.DEBUG),
    ):
        plan = adapter.build_invocation(
            prompt="private-prompt-value",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id="private-task-value",
            session_id="private-session-value",
            tool_config=tool_config,
            effort=effort,
        )
    assert secret in plan.cmd
    records = [record for record in caplog.records if record.name == adapter_type.__module__]
    assert len(records) == 1
    assert records[0].getMessage() == expected_message
    assert records[0].args == ()
    assert records[0].exc_info is None
    private_values = (
        secret,
        Path(plan.cmd[0]).name,
        adapter.default_model,
        "private-prompt-value",
        "private-task-value",
        "private-session-value",
        str(tmp_path),
        environment_value,
        *plan.env_overrides.values(),
    )
    for record in caplog.records:
        assert record.args == ()
        for value in plan.cmd:
            assert value not in record.getMessage()
            # Match whole values: the fixed agent_runtime source path contains "run".
            assert repr(value) not in repr(vars(record))
        for value in private_values:
            assert value not in record.getMessage()
            assert value not in repr(vars(record))


def _assert_single_constant_warning(caplog, adapter_type, secret, expected_message):
    warnings = [
        record
        for record in caplog.records
        if record.name == adapter_type.__module__ and record.levelno == logging.WARNING
    ]
    assert len(warnings) == 1
    record = warnings[0]
    assert record.getMessage() == expected_message
    assert record.args == ()
    assert record.exc_info is None
    assert secret not in record.getMessage()
    assert secret not in repr(vars(record))


def test_kimi_full_k3_effort_warning_is_constant(tmp_path, monkeypatch, caplog):
    for variable in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    binary = tmp_path / "private-executable-value"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    monkeypatch.setenv("LEARN_UK_KIMI_BIN", str(binary))
    secret = "secret-looking-effort-value"
    with caplog.at_level(logging.DEBUG):
        KimiAdapter().build_invocation(
            prompt="private-prompt-value",
            mode="workspace-write",
            cwd=tmp_path,
            model="k3",
            task_id="private-task-value",
            session_id="private-session-value",
            tool_config=admitted_tool_config(tmp_path, {}),
            effort=secret,
        )
    _assert_single_constant_warning(
        caplog, KimiAdapter, secret, "kimi: effort ignored for full K3, which exposes max effort only"
    )


def test_deepseek_max_budget_warning_is_constant(tmp_path, monkeypatch, caplog):
    for variable in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL"):
        monkeypatch.delenv(variable, raising=False)
    secret = "secret-looking-budget-value"
    with (
        patch(f"{DeepSeekAdapter.__module__}.shutil.which", return_value=str(tmp_path / "runtime-cli")),
        caplog.at_level(logging.DEBUG),
    ):
        DeepSeekAdapter().build_invocation(
            prompt="private-prompt-value",
            mode="workspace-write",
            cwd=tmp_path,
            tool_config={"max_budget_usd": secret},
        )
    _assert_single_constant_warning(
        caplog,
        DeepSeekAdapter,
        secret,
        "deepseek: max_budget_usd ignored; use hard-timeout/silence-timeout instead",
    )


_NO_CI_VARIABLES = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL")
_BUDGET_MESSAGE = "non-claude adapter ignoring max_budget_usd; use hard-timeout/silence-timeout instead"


def _isolated_environment(monkeypatch, tmp_path):
    for variable in _NO_CI_VARIABLES:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    # The AGY hook wiring is not under test; the warning fires before it.
    monkeypatch.setattr(agy_module, "require_hook_config", lambda *_args, **_kwargs: None)


def _assert_constant_record(caplog, adapter_type, level, message, *secrets):
    """Exactly one record carries ``message``, and nothing logged by the adapter module leaks a secret."""
    module_name = adapter_type.__module__
    matching = [
        record
        for record in caplog.records
        if record.name == module_name and record.levelno == level and record.getMessage() == message
    ]
    assert len(matching) == 1
    assert matching[0].args == ()
    assert matching[0].exc_info is None
    for record in caplog.records:
        if record.name != module_name:
            continue
        for secret in secrets:
            assert secret not in record.getMessage()
            assert secret not in repr(vars(record))


def _build_plan(
    adapter_type, tmp_path, *, tool_config=None, effort=None, mode="workspace-write", model=None, task_id=None
):
    return adapter_type().build_invocation(
        prompt="private-prompt-value",
        mode=mode,
        cwd=tmp_path,
        model=model,
        task_id=task_id,
        session_id=None,
        tool_config=tool_config,
        effort=effort,
    )


_HERMES_ADAPTERS = (HermesQwenAdapter, HermesDeepSeekAdapter, HermesGrokAdapter)
_HERMES_TOOL_CONFIG = {"hermes_mcp_servers": ["sources"]}


@pytest.mark.parametrize(
    ("adapter_type", "mode", "model"),
    [
        (CodexAdapter, "read-only", None),
        (GeminiAdapter, "workspace-write", "gemini-3.1-pro-high"),
        (AgyAdapter, "read-only", None),
        (HermesQwenAdapter, "workspace-write", None),
        (HermesDeepSeekAdapter, "workspace-write", None),
        (HermesGrokAdapter, "workspace-write", None),
    ],
)
def test_non_claude_max_budget_warning_is_constant(tmp_path, monkeypatch, caplog, adapter_type, mode, model):
    _isolated_environment(monkeypatch, tmp_path)
    secret = "secret-looking-budget-value"
    tool_config = {"max_budget_usd": secret}
    if adapter_type in _HERMES_ADAPTERS:
        tool_config.update(_HERMES_TOOL_CONFIG)
    with caplog.at_level(logging.DEBUG):
        _build_plan(adapter_type, tmp_path, tool_config=tool_config, mode=mode, model=model)
    _assert_constant_record(caplog, adapter_type, logging.WARNING, _BUDGET_MESSAGE, secret)


@pytest.mark.parametrize(
    ("adapter_type", "configured_effort", "expected_message"),
    [
        (
            adapter_type,
            configured_effort,
            f"Hermes {label} requested effort differs from ~/.hermes/config.yaml "
            "agent.reasoning_effort; using Hermes config without mutation"
            if configured_effort
            else f"Hermes {label} effort requested, but no readable top-level "
            "agent.reasoning_effort was found in ~/.hermes/config.yaml; using Hermes config without mutation",
        )
        for adapter_type, label in (
            (HermesQwenAdapter, "Qwen"),
            (HermesDeepSeekAdapter, "DeepSeek"),
            (HermesGrokAdapter, "Grok"),
        )
        for configured_effort in ("configured-secret-effort-value", None)
    ],
)
def test_hermes_effort_warnings_are_constant(
    tmp_path, monkeypatch, caplog, adapter_type, configured_effort, expected_message
):
    _isolated_environment(monkeypatch, tmp_path)
    secret = "secret-looking-effort-value"
    monkeypatch.setattr(f"{adapter_type.__module__}.top_level_agent_effort", lambda _config: configured_effort)
    with caplog.at_level(logging.DEBUG):
        _build_plan(adapter_type, tmp_path, tool_config=dict(_HERMES_TOOL_CONFIG), effort=secret)
    _assert_constant_record(
        caplog, adapter_type, logging.WARNING, expected_message, secret, "configured-secret-effort-value"
    )


@pytest.mark.parametrize(
    ("adapter_type", "mode", "model", "expected_message"),
    [
        (
            GeminiAdapter,
            "workspace-write",
            "gemini-3.1-pro-high",
            "gemini effort not yet wired through CLI — using adapter default (#1396 follow-up)",
        ),
        (
            AgyAdapter,
            "read-only",
            None,
            "agy effort not yet wired through CLI — using TUI-selected model default (#1396 follow-up)",
        ),
        (CursorAdapter, "read-only", None, "cursor adapter ignoring effort (not supported by CLI)"),
    ],
)
def test_ignored_effort_debug_is_constant(tmp_path, monkeypatch, caplog, adapter_type, mode, model, expected_message):
    _isolated_environment(monkeypatch, tmp_path)
    secret = "secret-looking-effort-value"
    with caplog.at_level(logging.DEBUG):
        _build_plan(adapter_type, tmp_path, effort=secret, mode=mode, model=model, task_id="private-task-value")
    _assert_constant_record(caplog, adapter_type, logging.DEBUG, expected_message, secret, "private-task-value")


def test_acpx_ignored_effort_debug_is_constant(tmp_path, monkeypatch, caplog):
    from tests.agent_runtime.test_acpx_adapter import _patch_provider_binary_lookup, _stub_binary

    _isolated_environment(monkeypatch, tmp_path)
    _stub_binary(monkeypatch, tmp_path)
    opencode = tmp_path / "opencode"
    opencode.write_text("#!/bin/sh\n", encoding="utf-8")
    opencode.chmod(0o755)
    _patch_provider_binary_lookup(monkeypatch, lambda name, *_a, **_k: {"opencode": str(opencode)}.get(name))
    monkeypatch.setattr(acpx_module, "_probe_participant_cli_compatibility", lambda _path, _executable: ("1.17.13", ()))
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    secret = "secret-looking-effort-value"
    with acpx_module.active_discussion_scope(), caplog.at_level(logging.DEBUG):
        _build_plan(
            AcpxGemmaShadowAdapter,
            tmp_path,
            tool_config={
                "acpx_discussion": True,
                "target_agent": "gemma",
                "correlation_id": "corr-1",
                "idempotency_key": "idem-1",
            },
            effort=secret,
            mode="read-only",
            model="google-ais/gemma-4-31b-it",
            task_id="t-1",
        )
    _assert_constant_record(
        caplog,
        AcpxGemmaShadowAdapter,
        logging.DEBUG,
        "ACPX adapter effort has no ACPX flag equivalent; ignoring",
        secret,
    )


def test_grok_build_invocation_debug_is_constant(tmp_path, monkeypatch, caplog):
    _isolated_environment(monkeypatch, tmp_path)
    secret = "secret-looking-task-value"
    with (
        patch(f"{GrokBuildAdapter.__module__}.shutil.which", return_value=str(tmp_path / "runtime-cli")),
        caplog.at_level(logging.DEBUG),
    ):
        _build_plan(GrokBuildAdapter, tmp_path, mode="danger", task_id=secret)
    _assert_constant_record(caplog, GrokBuildAdapter, logging.DEBUG, "grok invocation", secret)


def test_agy_interim_language_warning_is_constant(caplog):
    secret = "pending-work wording: 'secret-looking-reply-excerpt'"
    with caplog.at_level(logging.DEBUG):
        excerpt = agy_module._with_language_warning(secret, None)
    assert excerpt.splitlines() == [agy_module.AGY_INTERIM_LANGUAGE_WARNING, secret]
    _assert_constant_record(
        caplog, AgyAdapter, logging.WARNING, agy_module.AGY_INTERIM_LANGUAGE_WARNING, "secret-looking-reply-excerpt"
    )
