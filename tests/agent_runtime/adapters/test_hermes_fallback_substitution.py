from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from agent_runtime.adapters.base import InvocationPlan
from agent_runtime.adapters.hermes_common import (
    HERMES_GLM_FORBIDDEN_MARKER,
    HERMES_SUBSTITUTION_MARKER,
)
from agent_runtime.adapters.hermes_deepseek import HermesDeepSeekAdapter
from agent_runtime.adapters.hermes_grok import HermesGrokAdapter
from agent_runtime.probe_fallback import ProbeError, build_parser, run_probe
from agent_runtime.runner import invoke
from agent_runtime.usage import _reset_rate_limit_cache_for_tests


@pytest.fixture(autouse=True)
def _isolate_runtime(tmp_path):
    _reset_rate_limit_cache_for_tests()
    with patch("agent_runtime.usage._usage_dir", return_value=tmp_path / "api_usage"):
        yield
    _reset_rate_limit_cache_for_tests()


def _write_config(hermes_home: Path, text: str = "{}\n") -> None:
    hermes_home.mkdir(parents=True, exist_ok=True)
    (hermes_home / "config.yaml").write_text(text, encoding="utf-8")


def _plan_with_metadata(
    tmp_path: Path,
    *,
    requested_provider: str = "deepseek",
    requested_model: str = "deepseek-v4-pro",
    log_offset: int = 0,
) -> InvocationPlan:
    return InvocationPlan(
        cmd=["hermes", "-z", "hi", "-m", requested_model],
        cwd=tmp_path,
        metadata={
            "hermes": {
                "requested_provider": requested_provider,
                "requested_model": requested_model,
                "log_path": str(tmp_path / "logs" / "agent.log"),
                "log_offset": log_offset,
            }
        },
    )


def test_hermes_parse_reads_fallback_from_agent_log(tmp_path, capsys):
    logs = tmp_path / "logs"
    logs.mkdir()
    log_path = logs / "agent.log"
    old_log = "old call\n"
    log_path.write_text(old_log, encoding="utf-8")
    plan = _plan_with_metadata(tmp_path, log_offset=len(old_log))
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "2026-07-05 10:00 INFO Fallback activated: "
            "deepseek-v4-pro -> deepseek/deepseek-v3.2 (openrouter)\n"
        )

    result = HermesDeepSeekAdapter().parse_response(
        stdout="fallback probe ok",
        stderr="",
        returncode=0,
        output_file=None,
        plan=plan,
    )

    assert result.ok is True
    assert result.substitution == {
        "requested_provider": "deepseek",
        "requested_model": "deepseek-v4-pro",
        "actual_provider": "openrouter",
        "actual_model": "deepseek/deepseek-v3.2",
        "substituted": True,
        "source": "hermes-agent.log",
        "marker": HERMES_SUBSTITUTION_MARKER,
    }
    assert HERMES_SUBSTITUTION_MARKER in capsys.readouterr().err


@pytest.mark.parametrize(
    ("emission", "expected_provider", "expected_model"),
    [
        # hermes_cli/cli_agent_setup_mixin.py:65 (auth-failure path, provider-first)
        (
            "⚠️  Primary auth failed — switching to fallback: "
            "openrouter / deepseek/deepseek-v3.2",
            "openrouter",
            "deepseek/deepseek-v3.2",
        ),
        # agent/chat_completion_helpers.py:1484 (buffer status, model-first)
        (
            "🔄 Primary model failed — switching to fallback: "
            "deepseek/deepseek-v3.2 via openrouter",
            "openrouter",
            "deepseek/deepseek-v3.2",
        ),
        # agent/conversation_loop.py:4848 (empty-response buffer status)
        (
            "↻ Switched to fallback: deepseek/deepseek-v3.2 (openrouter)",
            "openrouter",
            "deepseek/deepseek-v3.2",
        ),
        # agent/conversation_loop.py:4853 (empty-response logger line)
        (
            "Fallback activated after empty responses: "
            "now using deepseek/deepseek-v3.2 on openrouter",
            "openrouter",
            "deepseek/deepseek-v3.2",
        ),
    ],
)
def test_hermes_parse_matches_all_real_fallback_emission_formats(
    tmp_path, emission, expected_provider, expected_model
):
    """Every fallback format hermes-agent actually emits must be detected."""
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "agent.log").write_text(f"{emission}\n", encoding="utf-8")
    plan = _plan_with_metadata(tmp_path)

    result = HermesDeepSeekAdapter().parse_response(
        stdout="probe ok",
        stderr="",
        returncode=0,
        output_file=None,
        plan=plan,
    )

    assert result.substitution is not None
    assert result.substitution["substituted"] is True
    assert result.substitution["actual_provider"] == expected_provider
    assert result.substitution["actual_model"] == expected_model


def test_hermes_parse_records_no_substitution_when_route_is_unchanged(tmp_path):
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "agent.log").write_text("", encoding="utf-8")
    plan = _plan_with_metadata(tmp_path)

    result = HermesDeepSeekAdapter().parse_response(
        stdout="hello",
        stderr="",
        returncode=0,
        output_file=None,
        plan=plan,
    )

    assert result.ok is True
    assert result.substitution is not None
    assert result.substitution["requested_provider"] == "deepseek"
    assert result.substitution["actual_provider"] == "deepseek"
    assert result.substitution["substituted"] is False


def test_hermes_build_refuses_configured_zai_glm_fallback(tmp_path, monkeypatch):
    hermes_home = tmp_path / "hermes"
    _write_config(
        hermes_home,
        """
fallback_providers:
  - provider: zai
    model: glm-4.6
""",
    )
    monkeypatch.setattr("agent_runtime.adapters.hermes_deepseek.shutil.which", lambda _: "hermes")

    with pytest.raises(ValueError, match=HERMES_GLM_FORBIDDEN_MARKER):
        HermesDeepSeekAdapter().build_invocation(
            prompt="hi",
            mode="read-only",
            cwd=tmp_path,
            model="deepseek-v4-pro",
            task_id=None,
            session_id=None,
            tool_config={"hermes_home": str(hermes_home)},
        )


def test_hermes_parse_hard_fails_actual_zai_glm_route(tmp_path):
    plan = _plan_with_metadata(
        tmp_path,
        requested_provider="xai",
        requested_model="grok-4.5",
    )

    result = HermesGrokAdapter().parse_response(
        stdout="would otherwise be ok",
        stderr="Primary model failed - switching to fallback: glm-4.6 via zai",
        returncode=0,
        output_file=None,
        plan=plan,
    )

    assert result.ok is False
    assert result.response == ""
    assert HERMES_GLM_FORBIDDEN_MARKER in (result.stderr_excerpt or "")
    assert result.substitution is not None
    assert result.substitution["actual_provider"] == "zai"
    assert result.substitution["actual_model"] == "glm-4.6"


def test_runner_persists_and_emits_hermes_substitution(tmp_path, monkeypatch):
    from telemetry import emit as emit_mod

    adapter = HermesDeepSeekAdapter()
    emitted_events: list[tuple[str, dict]] = []
    sink_events: list[tuple[str, dict]] = []
    records: list[dict] = []

    def fake_build_invocation(**kwargs):
        return InvocationPlan(
            cmd=[
                "/bin/sh",
                "-c",
                (
                    "printf 'fallback probe ok'; "
                    "printf '%s\n' 'switching to fallback: "
                    "deepseek/deepseek-v3.2 via openrouter' >&2"
                ),
            ],
            cwd=Path(kwargs["cwd"]),
            metadata={
                "hermes": {
                    "requested_provider": "deepseek",
                    "requested_model": "deepseek-v4-pro",
                    "log_path": str(tmp_path / "missing.log"),
                    "log_offset": 0,
                }
            },
        )

    monkeypatch.setattr(adapter, "build_invocation", fake_build_invocation)
    monkeypatch.setattr("agent_runtime.runner._load_adapter", lambda _name: adapter)
    monkeypatch.setattr(
        emit_mod,
        "emit_event",
        lambda event_type, payload: emitted_events.append((event_type, payload)),
    )
    monkeypatch.setattr("agent_runtime.runner.write_record", records.append)

    with patch("agent_runtime.runner.has_headroom", return_value=(True, "")):
        result = invoke(
            "deepseek",
            "hello",
            mode="read-only",
            cwd=tmp_path,
            model="deepseek-v4-pro",
            entrypoint="dispatch",
            event_sink=lambda name, **fields: sink_events.append((name, fields)),
        )

    assert result.ok is True
    assert result.model == "deepseek/deepseek-v3.2"
    assert result.substitution is not None
    assert result.usage_record["substitution"]["substituted"] is True
    assert records == [result.usage_record]
    assert sink_events[0][0] == "agent_runtime_substitution"
    assert emitted_events[0][0] == "agent_runtime_substitution"


def test_probe_help_includes_required_sections():
    help_text = build_parser().format_help()

    assert "Outputs:" in help_text
    assert "Exit codes:" in help_text
    assert "--hermes-home" in help_text


def test_probe_refuses_live_hermes_home():
    args = argparse.Namespace(hermes_home=Path.home() / ".hermes")

    with pytest.raises(ProbeError, match=r"live ~/\.hermes"):
        run_probe(args, invoke_fn=lambda *_args, **_kwargs: None)


def test_probe_requires_result_usage_and_event_substitution(tmp_path):
    hermes_home = tmp_path / "hermes"
    _write_config(hermes_home)
    substitution = {
        "requested_provider": "deepseek",
        "requested_model": "deepseek-v4-pro",
        "actual_provider": "openrouter",
        "actual_model": "deepseek/deepseek-v3.2",
        "substituted": True,
    }

    def fake_invoke(*_args, **kwargs):
        kwargs["event_sink"](
            "agent_runtime_substitution",
            substitution={"substituted": True},
        )
        return SimpleNamespace(
            model="deepseek/deepseek-v3.2",
            substitution=substitution,
            usage_record={"substitution": dict(substitution)},
        )

    args = argparse.Namespace(
        hermes_home=hermes_home,
        agent="deepseek",
        model=None,
        expected_fallback_provider="openrouter",
        expected_fallback_model="deepseek/deepseek-v3.2",
        prompt="hi",
        cwd=tmp_path,
        timeout=30,
    )

    summary = run_probe(args, invoke_fn=fake_invoke)

    assert summary["ok"] is True
    assert summary["usage_record_surfaced"] is True
    assert summary["telemetry_event_seen"] is True
