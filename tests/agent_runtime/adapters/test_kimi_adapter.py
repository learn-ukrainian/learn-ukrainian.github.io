"""Tests for the native Kimi K3 runtime lane."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.agent_runtime.adapters import kimicc as kimicc_adapter
from scripts.agent_runtime.adapters.kimi import (
    _MODE_FLAGS,
    KIMI_DEFAULT_EFFORT,
    KIMI_DEFAULT_MODEL,
    KimiAdapter,
)
from scripts.agent_runtime.adapters.kimicc import KimiccHarness
from scripts.agent_runtime.tool_config import build_mcp_tool_config
from scripts.audit.lint_agent_trailer import _TRAILER_RE
from scripts.delegate import build_parser
from tests.agent_runtime.adapters.kimi_admitted import admitted_tool_config


def _build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    mode: str = "workspace-write",
    model: str | None = None,
    effort: str | None = None,
    tool_config: dict | None = None,
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
        tool_config=admitted_tool_config(tmp_path, tool_config),
        effort=effort,
    )


def test_retired_default_refuses_before_a_command_or_skills_dir(tmp_path, monkeypatch):
    """OO-58: the historical k3-256k default is retired and must not assemble argv."""
    from scripts.agent_runtime.adapters import kimi as kimi_adapter

    with (
        patch.object(kimi_adapter, "_resolve_kimi_binary") as resolve_binary,
        patch.object(kimi_adapter, "_resolve_kimi_skills_dirs") as resolve_skills,
        pytest.raises(ValueError, match="is retired in the model catalog"),
    ):
        _build(tmp_path, monkeypatch, mode="workspace-write")
    resolve_binary.assert_not_called()
    resolve_skills.assert_not_called()
    assert KIMI_DEFAULT_MODEL == "k3-256k"
    assert _MODE_FLAGS == {"workspace-write": ()}


def test_kimicc_harness_opt_in_refuses_the_retired_historical_pin(tmp_path, monkeypatch):
    """OO-58: kimicc stays opt-in, and its historical pin is refused before the wrapper argv."""
    claude = tmp_path / "claude"
    claude.write_text("#!/bin/sh\n", encoding="utf-8")
    claude.chmod(0o755)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimicc._default_claude_bin", lambda: str(claude))
    probed: list[str] = []
    monkeypatch.setattr(
        "scripts.agent_runtime.adapters.kimicc._ensure_supported_claude_cli_version",
        lambda _: probed.append("probed"),
    )

    with pytest.raises(ValueError, match="is retired in the model catalog"):
        KimiAdapter().build_invocation(
            prompt="Inspect the target.",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id="kimi-kimicc-test",
            session_id=None,
            tool_config=admitted_tool_config(tmp_path, {"harness": "kimicc"}),
        )
    assert KimiccHarness.default_model == "kimi-code/k3"
    assert probed == []


def test_kimicc_refuses_model_that_is_not_a_routable_kimicc_alias(tmp_path, monkeypatch):
    claude = tmp_path / "claude"
    claude.write_text("#!/bin/sh\n", encoding="utf-8")
    claude.chmod(0o755)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimicc._default_claude_bin", lambda: str(claude))
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        KimiccHarness().build_invocation(
            prompt="Inspect the target.",
            mode="workspace-write",
            cwd=tmp_path,
            model="k3-256k",
            task_id="kimicc-reject-256k",
            session_id=None,
            tool_config=admitted_tool_config(tmp_path, {"harness": "kimicc"}),
        )


@pytest.mark.parametrize("model", ["k3", "k2.7", None])
def test_kimicc_effort_overrides_never_build_a_retired_model(tmp_path, monkeypatch, model):
    """OO-58: effort flags do not revive a retired Kimi id."""
    claude = tmp_path / "claude"
    claude.write_text("#!/bin/sh\n", encoding="utf-8")
    claude.chmod(0o755)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimicc._default_claude_bin", lambda: str(claude))
    assert KIMI_DEFAULT_EFFORT is None
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        KimiccHarness().build_invocation(
            prompt="Inspect the target.",
            mode="workspace-write",
            cwd=tmp_path,
            model=model,
            task_id="kimi-kimicc-effort",
            session_id=None,
            tool_config=admitted_tool_config(tmp_path),
            effort="max",
        )


def test_kimicc_harness_uses_claude_stream_json_parser(tmp_path, monkeypatch):
    """The parser still reads a kimicc plan. Building one from a retired id is refused."""
    del monkeypatch
    from scripts.agent_runtime.adapters.base import InvocationPlan

    with pytest.raises(ValueError, match="is retired in the model catalog"):
        KimiccHarness().build_invocation(
            prompt="Inspect the target.",
            mode="workspace-write",
            cwd=tmp_path,
            model="k3",
            task_id="kimi-kimicc-parser",
            session_id=None,
            tool_config=admitted_tool_config(tmp_path, {"harness": "kimicc"}),
        )
    plan = InvocationPlan(cmd=["kimicc"], cwd=tmp_path, metadata={"harness": "kimicc"})

    parsed = KimiAdapter().parse_response(
        stdout=json.dumps({"type": "result", "result": "KimiCC response"}),
        stderr="",
        returncode=0,
        output_file=None,
        plan=plan,
    )

    assert parsed.ok is True
    assert parsed.response == "KimiCC response"


def _kimicc_ready(tmp_path, monkeypatch):
    claude = tmp_path / "claude"
    claude.write_text("#!/bin/sh\n", encoding="utf-8")
    claude.chmod(0o755)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimicc._default_claude_bin", lambda: str(claude))
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimicc._ensure_supported_claude_cli_version", lambda _: None)


def test_kimicc_delegate_attempt_keys_do_not_launch_a_retired_model(tmp_path, monkeypatch):
    """OO-58: admitted tool keys still meet the retired-model refusal before argv."""
    _kimicc_ready(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        KimiccHarness().build_invocation(
            prompt="implement",
            mode="workspace-write",
            cwd=tmp_path,
            model="k3",
            task_id="kimicc-write",
            session_id=None,
            tool_config=admitted_tool_config(
                tmp_path,
                {
                    "harness": "kimicc",
                    "mcp_config_path": str(tmp_path / "writer.mcp.json"),
                    "strict_mcp_config": True,
                    "mcp_server_names": ["sources"],
                    "attempt_id": "att-1",
                    "codex_home_override": str(tmp_path / "codex-home"),
                    "agy_home_override": str(tmp_path / "agy-home"),
                },
            ),
        )


def test_kimicc_refuses_a_review_attempt_and_read_only_lease_keys(tmp_path, monkeypatch):
    """A review_id is a review attempt; a read-only lease has no admitted mode to serve."""
    _kimicc_ready(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="KIMI CODING-ONLY"):
        KimiccHarness().build_invocation(
            prompt="critique",
            mode="workspace-write",
            cwd=tmp_path,
            model="k3",
            task_id="kimicc-review-id",
            session_id=None,
            tool_config=admitted_tool_config(tmp_path, {"review_id": "rev-1"}),
        )
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        KimiccHarness().build_invocation(
            prompt="implement",
            mode="workspace-write",
            cwd=tmp_path,
            model="k3",
            task_id="kimicc-lease",
            session_id=None,
            tool_config=admitted_tool_config(tmp_path, {"read_only_tmp_root": str(tmp_path / "lease")}),
        )


@pytest.mark.parametrize("mode", ["read-only", "danger"])
def test_kimicc_refuses_read_only_and_danger_before_any_probe(tmp_path, monkeypatch, mode):
    """Formerly read-only stayed in plan mode; Kimi seats now admit workspace-write only."""
    _kimicc_ready(tmp_path, monkeypatch)
    probed: list[str] = []
    monkeypatch.setattr(
        "scripts.agent_runtime.adapters.kimicc._ensure_supported_claude_cli_version",
        lambda _: probed.append("probed"),
    )
    with pytest.raises(ValueError, match="KIMI CODING-ONLY"):
        KimiccHarness().build_invocation(
            prompt="critique",
            mode=mode,
            cwd=tmp_path,
            model="k3",
            task_id=f"kimicc-{mode}",
            session_id=None,
            tool_config=admitted_tool_config(tmp_path, {"harness": "kimicc"}),
        )
    assert probed == []
    assert not hasattr(kimicc_adapter, "read_only_review_refusal")
    assert not hasattr(kimicc_adapter, "READ_ONLY_REVIEW_ALLOWED_TOOLS")


def test_kimicc_unknown_tool_config_keys_meet_the_retired_model_first(tmp_path, monkeypatch):
    """OO-58: model retirement is before the unknown-key check, and still builds no argv."""
    _kimicc_ready(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        KimiccHarness().build_invocation(
            prompt="critique",
            mode="workspace-write",
            cwd=tmp_path,
            model="k3",
            task_id="kimicc-unknown",
            session_id=None,
            tool_config=admitted_tool_config(tmp_path, {"some_future_field": "no"}),
        )


@pytest.mark.parametrize(
    "requested",
    [
        "k3",
        "kimi-k3",
        "kimi-k3[1m]",
        "k3-256k",
        "kimi-k3-256k",
        "kimi-code/k3-256k",
        "k2.7-coding",
        "k2.7",
        "kimi-for-coding",
        "kimi-k2.7-code",
        "k2.7-coding-highspeed",
        "k2.7-highspeed",
        "kimi-for-coding-highspeed",
        "kimi-k2.7-code-highspeed",
        "kimi-code/k3",
    ],
)
def test_short_names_and_full_aliases_are_refused_as_retired(tmp_path, monkeypatch, requested):
    """OO-58: aliases still resolve, then the catalog refusal stops the command."""
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        _build(tmp_path, monkeypatch, model=requested)


def test_unknown_model_is_still_unsupported_rather_than_retired(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="unsupported Kimi model"):
        _build(tmp_path, monkeypatch, model="k1-classic")


def test_effort_does_not_launch_a_retired_kimi_model(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    assert KIMI_DEFAULT_EFFORT is None
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        _build(tmp_path, monkeypatch, model="k3", effort="high")
    assert "max effort only" not in caplog.text


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


def test_parse_gh_auth_prompt_is_not_rate_limited():
    """#7166 / #7472: an unauthenticated gh prompt in a failed seat's output is
    an auth failure — it must not be labeled rate-limited even when unrelated
    rate-limit text appears alongside it."""
    parsed = KimiAdapter().parse_response(
        stdout="",
        stderr=(
            "To get started with GitHub CLI, please run:  gh auth login\n"
            "Alternatively, populate the GH_TOKEN environment variable with a "
            "GitHub API authentication token.\n"
            "HTTP 429: rate limit exceeded"
        ),
        returncode=1,
        output_file=None,
    )
    assert parsed.ok is False
    assert parsed.rate_limited is False


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


def test_invocation_telemetry_is_not_reached_for_a_retired_model(tmp_path, monkeypatch):
    """OO-58: a retired id raises before telemetry can label a command that was not built."""
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        _build(tmp_path, monkeypatch, model="k3", effort="medium")
    with pytest.raises(ValueError, match="kimi-code/k3-256k"):
        _build(tmp_path, monkeypatch, effort="medium")


def test_default_model_names_the_retired_pin_and_does_not_launch(tmp_path, monkeypatch):
    """The historical default stays k3-256k so the refusal names it. It is not executed."""
    assert KIMI_DEFAULT_MODEL == "k3-256k"
    with pytest.raises(ValueError, match=r"model 'k3-256k' is retired in the model catalog \(kimi-code/k3-256k\)"):
        _build(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match=r"model 'k3' is retired in the model catalog \(kimi-code/k3\)"):
        _build(tmp_path, monkeypatch, model="k3", effort="max")
