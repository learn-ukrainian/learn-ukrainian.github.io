"""Native ask effort provenance is configuration, never backend attestation."""

import json
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.ai_agent_bridge import _agy


@pytest.mark.parametrize("requested,configured,expected", [
    ("high", "high", "high"), ("high", "xhigh", "xhigh"),
    ("high", "not-exposed", None), ("high", "unknown", None),
    (None, "not-exposed", None), (None, "high", None),
])
def test_native_ask_reports_only_configured_explicit_effort(
    tmp_path, monkeypatch, capsys, requested, configured, expected,
):
    msg = {"id": 17, "task_id": "effort-fixture", "from": "codex", "to": "agy",
           "type": "query", "content": "Return the fixture reply.",
           "data": json.dumps({"to_model": "gemini-3.8-flash-high", "effort": requested})}
    monkeypatch.setattr(_agy, "_fetch_agy_message", lambda _: msg)
    monkeypatch.setattr(_agy, "provision_review_worktree", lambda *_, **__: nullcontext(None))
    monkeypatch.setattr(_agy, "build_agy_prompt", lambda *_, **__: "fixture prompt")
    monkeypatch.setattr(_agy, "append_review_prompt_evidence", lambda prompt, **_: prompt)
    monkeypatch.setattr(_agy, "_agy_ask_scratch_cwd", lambda: tmp_path)
    invoke = Mock(return_value=SimpleNamespace(
        ok=True, model="gemini-3.8-flash-high", session_id=None, response="fixture reply", effort=configured,
    ))
    monkeypatch.setattr(_agy.agent_runner, "invoke", invoke)
    send = Mock(return_value=18)
    monkeypatch.setattr(_agy, "send_message", send)
    monkeypatch.setattr(_agy, "acknowledge", Mock())
    monkeypatch.setattr(_agy, "record_ask_reply", Mock())
    assert _agy.process_for_agy(17, stdout_only=True) == "fixture reply"
    assert invoke.call_args.args[0] == "agy"
    assert invoke.call_args.kwargs["effort"] == requested
    metadata = json.loads(send.call_args.kwargs["data"])
    assert metadata["effort_requested"] == requested
    assert metadata["effort_applied"] == expected
    assert "effort_reason" not in metadata
    assert "backend_observed_effort" not in metadata
    assert "backend_observed_model" not in metadata
    assert "no per-invocation effort control" not in capsys.readouterr().out
