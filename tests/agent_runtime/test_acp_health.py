"""ACP capability refusals must remain actionable and exclude only ACP routes."""

from pathlib import Path

import pytest

from scripts.agent_runtime import acp_health
from scripts.agent_runtime.adapters import acpx

_HELP = "codex kimi cursor claude pool --file " + " ".join(acpx._ACPX_REQUIRED_GLOBAL_FLAGS)


@pytest.mark.parametrize("probe", [acpx._probe_acpx_version, acpx._probe_cli_help])
def test_acp_node_refusal_is_not_reported_as_missing_help(monkeypatch, probe):
    def refuse(*_args, **_kwargs):
        raise acpx.AcpxShadowRefusalError("Node runtime missing", failure_code="node_runtime_unavailable")

    monkeypatch.setattr(acpx, "_acpx_spawn_argv", refuse)
    with pytest.raises(acpx.AcpxShadowRefusalError, match="Node runtime missing") as error:
        probe("acpx")
    assert error.value.failure_code == "node_runtime_unavailable"


@pytest.mark.parametrize("code", ["node_runtime_unavailable", "cli_incompatible"])
def test_acp_shared_capability_failure_excludes_all_participants(monkeypatch, tmp_path, code):
    def refuse(**_kwargs):
        raise acpx.AcpxShadowRefusalError("incompatible", failure_code=code)

    monkeypatch.setattr(acpx, "_resolve_acpx_binary", refuse)
    monkeypatch.setattr(acpx, "_resolve_participant_binary", lambda *_a, **_k: pytest.fail("shared probe failed"))
    health = acp_health.probe_acp_health(tmp_path)
    assert set(health) == set(acpx.ACPX_SUPPORTED_PARTICIPANTS)
    assert all(row["eligible"] is False and row["healthy"] is False for row in health.values())
    assert all(row["failure_code"] == code for row in health.values())


def _healthy_probes(monkeypatch):
    monkeypatch.setattr(acpx, "_resolve_acpx_binary", lambda **_kw: "acpx")
    monkeypatch.setattr(acpx, "_resolve_participant_binary", lambda *_a, **_k: ("provider", "1.0.0"))
    monkeypatch.setattr(acpx, "_probe_cli_help", lambda *_a: _HELP)
    monkeypatch.setattr(acpx, "_require_text_agent", lambda **_kw: "wrapper")
    monkeypatch.setattr(acpx, "_require_local_claude_acp_adapter", lambda *_a, **_kw: {})
    monkeypatch.setattr(acpx, "_resolve_grok_binary", lambda: "grok")
    monkeypatch.setattr(acpx, "_probe_grok_cli_compatibility", lambda _b: ("1.0.0", ()))
    monkeypatch.setattr(acpx, "_require_grok_profile", lambda: "profile")


def test_acp_provider_contract_failure_is_scoped_and_recovers(monkeypatch, tmp_path):
    _healthy_probes(monkeypatch)
    calls = []

    def provider(executable, **_kwargs):
        calls.append(executable)
        if executable == "opencode":
            raise acpx.AcpxShadowRefusalError("missing acp --pure", failure_code="cli_incompatible")
        return executable, "1.0.0"

    monkeypatch.setattr(acpx, "_resolve_participant_binary", provider)
    health = acp_health.probe_acp_health(tmp_path)
    assert calls.count("opencode") == 1
    assert health["deepseek"]["eligible"] is False
    assert health["glm"]["eligible"] is False
    assert health["agy"]["eligible"] is True
    assert health["codex"]["eligible"] is True
    monkeypatch.setattr(acpx, "_resolve_participant_binary", lambda *_a, **_kw: ("opencode", "1.0.1"))
    assert acp_health.probe_acp_health(tmp_path)["deepseek"]["eligible"] is True


@pytest.mark.parametrize("lane", ["codex", "cursor", "kimi"])
def test_acp_missing_builtin_exec_excludes_only_that_lane(monkeypatch, tmp_path, lane):
    _healthy_probes(monkeypatch)

    def help_text(_binary, *args):
        return "" if args == (lane, "exec") else _HELP

    monkeypatch.setattr(acpx, "_probe_cli_help", help_text)
    health = acp_health.probe_acp_health(tmp_path)
    assert health[lane]["eligible"] is False
    assert health[lane]["failure_code"] == "cli_incompatible"
    assert health["agy"]["eligible"] is True


def test_acp_unavailable_probe_is_unknown_and_ineligible(monkeypatch):
    def unavailable(**_kwargs):
        raise OSError("probe unavailable")

    monkeypatch.setattr(acpx, "_resolve_acpx_binary", unavailable)
    health = acp_health.probe_acp_health(Path("."))
    assert all(row["healthy"] is None and row["eligible"] is False for row in health.values())
    assert all(row["failure_code"] == "probe_unavailable" for row in health.values())


def test_acp_missing_generic_exec_does_not_exclude_builtin_routes(monkeypatch, tmp_path):
    _healthy_probes(monkeypatch)
    monkeypatch.setattr(acpx, "_probe_cli_help", lambda _b, *args: "" if args == ("exec",) else _HELP)
    health = acp_health.probe_acp_health(tmp_path)
    assert health["agy"]["eligible"] is False
    assert health["deepseek"]["eligible"] is False
    assert health["grok"]["eligible"] is False
    assert health["codex"]["eligible"] is True
    assert health["cursor"]["eligible"] is True
