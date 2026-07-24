"""Tests for the native Kimi K3 runtime lane."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.agent_runtime.adapters.kimi import (
    _MODE_FLAGS,
    _READ_ONLY_REFUSAL,
    KIMI_DEFAULT_EFFORT,
    KIMI_DEFAULT_MODEL,
    KIMI_MODEL_ALIASES,
    KimiAdapter,
)
from scripts.agent_runtime.telemetry import resolve_invocation_telemetry
from scripts.agent_runtime.tool_config import build_mcp_tool_config
from scripts.audit.lint_agent_trailer import _TRAILER_RE
from scripts.delegate import build_parser


def _build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    mode: str = "workspace-write",
    model: str | None = None,
    effort: str | None = None,
):
    binary = tmp_path / "kimi"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    monkeypatch.setenv("LEARN_UK_KIMI_BIN", str(binary))
    return KimiAdapter().build_invocation(
        prompt="Inspect the target.",
        mode=mode,
        cwd=tmp_path,
        model=model,
        task_id="kimi-test",
        session_id=None,
        tool_config=None,
        effort=effort,
    )


@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
def test_build_invocation_uses_flagless_write_modes(tmp_path, monkeypatch, mode):
    plan = _build(tmp_path, monkeypatch, mode=mode)

    assert plan.cmd[0] == str(tmp_path / "kimi")
    assert plan.cmd[plan.cmd.index("-m") + 1] == KIMI_MODEL_ALIASES[KIMI_DEFAULT_MODEL]
    assert plan.cmd[plan.cmd.index("--output-format") + 1] == "stream-json"
    assert not ({"--auto", "--yolo", "--plan"} & set(plan.cmd))


def test_mode_flag_mapping_is_empty_for_all_headless_modes():
    assert _MODE_FLAGS == {
        "read-only": (),
        "workspace-write": (),
        "danger": (),
    }


def test_read_only_refuses_on_native_path(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match=re.escape(_READ_ONLY_REFUSAL)):
        _build(tmp_path, monkeypatch, mode="read-only")


def test_short_names_and_full_aliases_resolve_and_unknown_models_reject(tmp_path, monkeypatch):
    for requested, resolved in (
        ("k3", "kimi-code/k3"),
        ("kimi-k3", "kimi-code/k3"),
        ("kimi-k3[1m]", "kimi-code/k3"),
        ("k2.7-coding", "kimi-code/kimi-for-coding"),
        ("k2.7", "kimi-code/kimi-for-coding"),
        ("kimi-for-coding", "kimi-code/kimi-for-coding"),
        ("kimi-k2.7-code", "kimi-code/kimi-for-coding"),
        ("k2.7-coding-highspeed", "kimi-code/kimi-for-coding-highspeed"),
        ("k2.7-highspeed", "kimi-code/kimi-for-coding-highspeed"),
        ("kimi-for-coding-highspeed", "kimi-code/kimi-for-coding-highspeed"),
        ("kimi-k2.7-code-highspeed", "kimi-code/kimi-for-coding-highspeed"),
        ("kimi-code/k3", "kimi-code/k3"),
    ):
        plan = _build(tmp_path, monkeypatch, model=requested)
        assert plan.cmd[plan.cmd.index("-m") + 1] == resolved

    with pytest.raises(ValueError, match="unsupported Kimi model"):
        _build(tmp_path, monkeypatch, model="k1-classic")


def test_effort_warning_fires_only_for_k3(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    plan = _build(tmp_path, monkeypatch, model="k3", effort="high")
    assert KIMI_DEFAULT_EFFORT == "max"
    assert "max effort only" in caplog.text
    assert "--effort" not in plan.cmd

    caplog.clear()
    plan = _build(tmp_path, monkeypatch, model="k2.7-coding", effort="high")
    assert "max effort only" not in caplog.text
    assert "--effort" not in plan.cmd


def test_empty_stdout_with_rc_zero_fails():
    parsed = KimiAdapter().parse_response(stdout="", stderr="", returncode=0, output_file=None)

    assert parsed.ok is False
    assert parsed.response == ""


def test_nonzero_returncode_fails_even_with_assistant_text():
    stdout = json.dumps({"role": "assistant", "content": "looks fine"})
    parsed = KimiAdapter().parse_response(stdout=stdout, stderr="boom", returncode=1, output_file=None)

    assert parsed.ok is False
    assert parsed.response == ""
    assert "boom" in (parsed.stderr_excerpt or "")


def test_non_assistant_event_stream_is_never_promoted_to_success():
    """Silent-error-as-content guard: tool/status-only streams must fail."""
    stdout = "\n".join(
        [
            json.dumps({"role": "tool", "name": "Read", "content": "raw dump"}),
            json.dumps({"role": "meta", "type": "status", "state": "working"}),
        ]
    )
    parsed = KimiAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None)

    assert parsed.ok is False
    assert parsed.response == ""


def test_parse_stream_json_response_session_and_tool_calls(tmp_path):
    events = [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "type": "function",
                    "id": "tool-1",
                    "function": {"name": "Read", "arguments": json.dumps({"path": "AGENTS.md"})},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "tool-1", "content": "# AGENTS.md"},
        {"role": "assistant", "content": "done"},
        {
            "role": "meta",
            "type": "session.resume_hint",
            "session_id": "session-123",
        },
    ]
    parsed = KimiAdapter().parse_response(
        stdout="\n".join(json.dumps(event) for event in events),
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert parsed.ok is True
    assert parsed.response == "done"
    assert parsed.session_id == "session-123"
    assert parsed.tool_calls[0]["name"] == "Read"
    assert parsed.tool_calls[0]["arguments"] == {"path": "AGENTS.md"}
    assert parsed.tool_calls[0]["output_summary"] == "# AGENTS.md"


def test_parse_rate_limit_failure():
    parsed = KimiAdapter().parse_response(
        stdout="",
        stderr="HTTP 429: rate limit exceeded",
        returncode=1,
        output_file=None,
    )
    assert parsed.ok is False
    assert parsed.rate_limited is True
    assert parsed.response == ""


def test_dispatch_parser_and_commit_trailer_accept_kimi():
    args = build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "kimi",
            "--task-id",
            "kimi-smoke",
            "--prompt",
            "probe",
            "--dry-run",
        ]
    )
    assert args.agent == "kimi"
    assert _TRAILER_RE.search("X-Agent: kimi/kimi-smoke")


def test_kimi_mcp_request_fails_closed_without_per_call_selector():
    tool_config, diagnostics = build_mcp_tool_config("kimi", mcp_servers=["sources"])

    assert tool_config is None
    assert diagnostics["resolution_status"] == "servers_not_found"
    assert diagnostics["missing_server_names"] == ["sources"]


def test_invocation_telemetry_is_model_aware_and_reports_native_cli_version(tmp_path, monkeypatch):
    k3_plan = _build(tmp_path, monkeypatch, model="k3", effort="medium")
    with patch("scripts.agent_runtime.telemetry.kimi_cli_version", return_value="0.26.0"):
        k3_telemetry = resolve_invocation_telemetry(
            agent_name="kimi",
            plan=k3_plan,
            requested_model=None,
            requested_effort="medium",
        )

    assert k3_telemetry.model == "kimi-code/k3"
    assert k3_telemetry.effort == "max"  # K3 is always-max; caller request never mislabeled
    assert k3_telemetry.cli_version == "0.26.0"

    coding_plan = _build(tmp_path, monkeypatch, effort="medium")  # default: k2.7-coding
    with patch("scripts.agent_runtime.telemetry.kimi_cli_version", return_value="0.26.0"):
        coding_telemetry = resolve_invocation_telemetry(
            agent_name="kimi",
            plan=coding_plan,
            requested_model=None,
            requested_effort="medium",
        )

    assert coding_telemetry.model == KIMI_MODEL_ALIASES[KIMI_DEFAULT_MODEL]
    assert coding_telemetry.effort == "not-exposed"  # k2.7 models have no effort knob


def test_binary_resolution_prefers_hermes_over_legacy(tmp_path, monkeypatch):
    """No override + nothing on PATH: hermes npm install beats the legacy binary."""
    from scripts.agent_runtime.adapters import kimi as kimi_adapter

    home = tmp_path / "home"
    hermes = home / ".hermes" / "node" / "bin" / "kimi"
    legacy = home / ".kimi-code" / "bin" / "kimi"
    for path in (hermes, legacy):
        path.parent.mkdir(parents=True)
        path.write_text("#!/bin/sh\n", encoding="utf-8")
        path.chmod(0o755)

    monkeypatch.delenv("LEARN_UK_KIMI_BIN", raising=False)
    monkeypatch.setattr(kimi_adapter.shutil, "which", lambda _name: None)
    monkeypatch.setattr(kimi_adapter.Path, "home", lambda: home)

    assert kimi_adapter._resolve_kimi_binary() == str(hermes)


def test_binary_resolution_falls_back_to_legacy_when_hermes_absent(tmp_path, monkeypatch):
    from scripts.agent_runtime.adapters import kimi as kimi_adapter

    home = tmp_path / "home"
    legacy = home / ".kimi-code" / "bin" / "kimi"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("#!/bin/sh\n", encoding="utf-8")
    legacy.chmod(0o755)

    monkeypatch.delenv("LEARN_UK_KIMI_BIN", raising=False)
    monkeypatch.setattr(kimi_adapter.shutil, "which", lambda _name: None)
    monkeypatch.setattr(kimi_adapter.Path, "home", lambda: home)

    assert kimi_adapter._resolve_kimi_binary() == str(legacy)


def test_native_binary_present_selects_native_path(tmp_path, monkeypatch):
    binary = tmp_path / "kimi"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    monkeypatch.setenv("LEARN_UK_KIMI_BIN", str(binary))

    plan = KimiAdapter().build_invocation(
        prompt="Inspect native.",
        mode="workspace-write",
        cwd=tmp_path,
        model="k3",
        task_id="native-test",
        session_id=None,
        tool_config=None,
    )

    assert plan.cmd[0] == str(binary)
    assert "-m" in plan.cmd
    assert plan.cmd[plan.cmd.index("-m") + 1] == "kimi-code/k3"
    assert "ANTHROPIC_BASE_URL" not in plan.env_overrides


def test_native_absent_credential_available_selects_kimicc_path(tmp_path, monkeypatch):
    monkeypatch.delenv("LEARN_UK_KIMI_BIN", raising=False)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimi._resolve_kimi_binary", lambda: None)

    claude_bin = tmp_path / "claude"
    claude_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    claude_bin.chmod(0o755)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimi._resolve_claude_binary", lambda: str(claude_bin))

    monkeypatch.setenv("KIMICC_AUTH_TOKEN", "token-from-kimicc-env")

    plan = KimiAdapter().build_invocation(
        prompt="Inspect kimicc.",
        mode="workspace-write",
        cwd=tmp_path,
        model="k3",
        task_id="kimicc-test",
        session_id=None,
        tool_config=None,
    )

    assert plan.cmd[0] == str(claude_bin)
    assert "--model" in plan.cmd
    assert plan.cmd[plan.cmd.index("--model") + 1] == "k3"
    assert plan.env_overrides["ANTHROPIC_BASE_URL"] == "https://api.kimi.com/coding"
    assert plan.env_overrides["ANTHROPIC_AUTH_TOKEN"] == "token-from-kimicc-env"
    assert plan.env_overrides["LEARN_UKRAINIAN_TRANSPORT"] == "kimicc"


def test_native_absent_no_credential_raises_typed_unavailability_error(tmp_path, monkeypatch):
    monkeypatch.delenv("LEARN_UK_KIMI_BIN", raising=False)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimi._resolve_kimi_binary", lambda: None)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimi._resolve_claude_binary", lambda: "/usr/local/bin/claude")
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimi._resolve_kimicc_auth", lambda _ep: None)

    with pytest.raises(RuntimeError, match="Kimi lane unavailable: no Kimi API credential found"):
        KimiAdapter().build_invocation(
            prompt="Test no cred.",
            mode="workspace-write",
            cwd=tmp_path,
            model="k3",
            task_id="no-cred-test",
            session_id=None,
            tool_config=None,
        )


def test_auth_precedence_order_matches_start_kimicc_sh(monkeypatch):
    from scripts.agent_runtime.adapters.kimi import _resolve_kimicc_auth

    monkeypatch.setenv("KIMICC_AUTH_TOKEN", "token-kimicc")
    monkeypatch.setenv("MOONSHOT_API_KEY", "token-moonshot")
    monkeypatch.setenv("KIMI_API_KEY", "token-kimi")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "token-anthropic")
    monkeypatch.setattr("scripts.lib.kimi_coding_oauth.get_oauth_token", lambda: "token-oauth")

    # 1. KIMICC_AUTH_TOKEN wins over all
    auth = _resolve_kimicc_auth("coding")
    assert auth == ("token-kimicc", "KIMICC_AUTH_TOKEN")

    # 2. MOONSHOT_API_KEY wins over remaining
    monkeypatch.delenv("KIMICC_AUTH_TOKEN")
    auth = _resolve_kimicc_auth("coding")
    assert auth == ("token-moonshot", "MOONSHOT_API_KEY")

    # 3. KIMI_API_KEY wins over remaining
    monkeypatch.delenv("MOONSHOT_API_KEY")
    auth = _resolve_kimicc_auth("coding")
    assert auth == ("token-kimi", "KIMI_API_KEY")

    # 4. ANTHROPIC_AUTH_TOKEN wins over OAuth on coding endpoint
    monkeypatch.delenv("KIMI_API_KEY")
    auth = _resolve_kimicc_auth("coding")
    assert auth == ("token-anthropic", "ANTHROPIC_AUTH_TOKEN")

    # 5. OAuth helper used when no env keys are set on coding endpoint
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN")
    auth = _resolve_kimicc_auth("coding")
    assert auth == ("token-oauth", "oauth(kimi login)")

    # On platform endpoint, ANTHROPIC_AUTH_TOKEN and OAuth are NOT used
    auth_platform = _resolve_kimicc_auth("platform")
    assert auth_platform is None


def test_no_credential_value_written_to_cmd_log_or_telemetry(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    secret_token = "SECRET_TOKEN_VALUE_XYZ_999"

    monkeypatch.delenv("LEARN_UK_KIMI_BIN", raising=False)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimi._resolve_kimi_binary", lambda: None)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimi._resolve_claude_binary", lambda: "/usr/local/bin/claude")
    monkeypatch.setenv("KIMICC_AUTH_TOKEN", secret_token)

    plan = KimiAdapter().build_invocation(
        prompt="Inspect secret safety.",
        mode="workspace-write",
        cwd=tmp_path,
        model="k3",
        task_id="secret-test",
        session_id=None,
        tool_config=None,
    )

    # Secret is in env_overrides (passed safely to subprocess environment)
    assert plan.env_overrides["ANTHROPIC_AUTH_TOKEN"] == secret_token

    # Secret is NEVER in cmd argv
    assert secret_token not in " ".join(plan.cmd)

    # Secret is NEVER in log output
    assert secret_token not in caplog.text

    # Secret is NEVER in resolved telemetry
    telemetry = resolve_invocation_telemetry(
        agent_name="kimi",
        plan=plan,
        requested_model="k3",
        requested_effort="max",
    )
    assert secret_token not in telemetry.model
    assert secret_token not in telemetry.effort
    assert secret_token not in telemetry.cli_version
