"""GrokBuildAdapter tests — native `grok` CLI headless adapter.

Kept deliberately separate from the Hermes-backed `grok` agent
(HermesGrokAdapter, grok-4.3/4.20). These tests don't require the grok binary
to be installed — `shutil.which` is mocked.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime import registry
from agent_runtime.adapters.base import AgentAdapter, InvocationPlan
from agent_runtime.adapters.grok_build import GrokBuildAdapter, _parse_json_object

FAKE_GROK = "/usr/local/bin/grok"


def _build(prompt: str, tmp_path: Path, **kw):
    with patch(
        "agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK
    ):
        return GrokBuildAdapter().build_invocation(
            prompt=prompt,
            mode=kw.pop("mode", "danger"),
            cwd=tmp_path,
            model=kw.pop("model", None),
            task_id=kw.pop("task_id", None),
            session_id=kw.pop("session_id", None),
            tool_config=kw.pop("tool_config", None),
            effort=kw.pop("effort", None),
        )


def _val(cmd: list[str], flag: str) -> str:
    return cmd[cmd.index(flag) + 1]


def test_basic_headless_invocation(tmp_path):
    plan = _build("Fix the bug in foo.py", tmp_path)
    assert plan.cmd[0] == FAKE_GROK
    assert _val(plan.cmd, "-p") == "Fix the bug in foo.py"
    assert _val(plan.cmd, "--output-format") == "json"
    assert "--no-alt-screen" in plan.cmd
    assert _val(plan.cmd, "--cwd") == str(tmp_path)
    assert plan.stdin_payload == ""
    assert plan.output_file is None


def test_mode_permission_mapping(tmp_path):
    for mode, perm in [
        ("read-only", "plan"),
        ("workspace-write", "acceptEdits"),
        ("danger", "bypassPermissions"),
    ]:
        plan = _build("do x", tmp_path, mode=mode)
        assert _val(plan.cmd, "--permission-mode") == perm


def test_unsupported_mode_raises(tmp_path):
    with pytest.raises(ValueError, match="unsupported mode"):
        _build("x", tmp_path, mode="bogus")


def test_model_and_effort_flags(tmp_path):
    plan = _build("x", tmp_path, model="grok-4.20", effort="high")
    assert _val(plan.cmd, "-m") == "grok-4.20"
    assert _val(plan.cmd, "--effort") == "high"


def test_no_model_no_effort_by_default(tmp_path):
    plan = _build("x", tmp_path)
    assert "-m" not in plan.cmd
    assert "--effort" not in plan.cmd


def test_hyphen_leading_prompt_uses_prompt_file(tmp_path):
    plan = _build("--- context: shared\nfix it", tmp_path)
    assert "-p" not in plan.cmd
    pf = Path(_val(plan.cmd, "--prompt-file"))
    assert pf.read_text(encoding="utf-8").startswith("--- context")


def test_tool_config_allow_deny(tmp_path):
    plan = _build(
        "x", tmp_path, tool_config={"allowed_tools": "Read,Grep", "disallowed_tools": "Bash"}
    )
    assert _val(plan.cmd, "--tools") == "Read,Grep"
    assert _val(plan.cmd, "--disallowed-tools") == "Bash"


def test_missing_grok_binary_raises(tmp_path):
    with patch("agent_runtime.adapters.grok_build.shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="grok CLI"):
            GrokBuildAdapter().build_invocation(
                prompt="x",
                mode="danger",
                cwd=tmp_path,
                model=None,
                task_id=None,
                session_id=None,
                tool_config=None,
            )


def test_parse_success_json():
    out = json.dumps({"text": "done\n", "stopReason": "EndTurn", "sessionId": "abc-123"})
    r = GrokBuildAdapter().parse_response(stdout=out, stderr="", returncode=0, output_file=None)
    assert r.ok
    assert r.response == "done"
    assert r.session_id == "abc-123"
    assert r.rate_limited is False


def test_parse_failure_nonzero():
    r = GrokBuildAdapter().parse_response(stdout="", stderr="boom", returncode=1, output_file=None)
    assert not r.ok
    assert r.response == ""
    assert r.stderr_excerpt == "boom"


def test_parse_rate_limited():
    r = GrokBuildAdapter().parse_response(
        stdout="", stderr="HTTP 429 too many requests", returncode=1, output_file=None
    )
    assert r.rate_limited is True
    assert not r.ok


def test_parse_json_with_log_noise():
    out = "some startup log\n" + json.dumps({"text": "ok"}) + "\ntrailing line"
    assert _parse_json_object(out) == {"text": "ok"}


def test_parse_plain_fallback():
    r = GrokBuildAdapter().parse_response(
        stdout="just plain text", stderr="", returncode=0, output_file=None
    )
    assert r.ok
    assert r.response == "just plain text"


def test_registry_grok_build_distinct_from_hermes_grok():
    gb = registry.get_agent_entry("grok-build")
    g = registry.get_agent_entry("grok")
    assert "grok_build:GrokBuildAdapter" in gb["adapter"]
    assert "hermes_grok:HermesGrokAdapter" in g["adapter"]
    assert gb["adapter"] != g["adapter"]
    assert "code_writing" in gb["capabilities"]
    assert "grok-build" in registry.available_agents()


def test_conforms_to_agent_adapter_protocol():
    assert isinstance(GrokBuildAdapter(), AgentAdapter)


def test_liveness_signal_paths_returns_tuple(tmp_path):
    paths = GrokBuildAdapter().liveness_signal_paths(InvocationPlan(cmd=[], cwd=tmp_path))
    assert isinstance(paths, tuple)
