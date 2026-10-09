from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import scripts.ai_agent_bridge._cursor as ask_cursor
import scripts.audit.cursor_judge_calibration as cursor_judge
from scripts.agent_runtime.adapters.acpx import AcpxCursorShadowAdapter
from scripts.agent_runtime.adapters.cursor import CursorAdapter
from scripts.review.model_catalog import ModelCatalogError

CALLERS = [
    "adapter",
    "acpx",
    "ask",
    "judge"
]

MODELS_ALLOWED = [
    ("grok-4.7", "grok-4.7-high"),
    ("grok-4.7-high", "grok-4.7-high"),
    ("composer-2.5", "composer-2.5"),
    ("composer-2.5[fast=false]", "composer-2.5[fast=false]"),
]

MODELS_REFUSED = [
    ("grok-4.7-low", "CURSOR_UNATTESTED_GROK_VARIANT"),
    ("grok-4.7-medium", "CURSOR_UNATTESTED_GROK_VARIANT"),
    ("grok-4.7-xhigh", "CURSOR_UNATTESTED_GROK_VARIANT"),
    ("grok-4.7-fast", "CURSOR_UNATTESTED_GROK_VARIANT"),
    ("grok-4.7[context=500k]", "CURSOR_UNATTESTED_GROK_VARIANT"),
    ("grok-4.7[fast=false]", "CURSOR_UNATTESTED_GROK_VARIANT"),
    ("opus", "CURSOR_CLAUDE_REFUSED"),
    ("sonnet", "CURSOR_CLAUDE_REFUSED"),
    ("haiku", "CURSOR_MODEL_NOT_APPROVED"),
    ("haiku-5-5", "CURSOR_MODEL_NOT_APPROVED"),
    ("haiku-4.5", "CURSOR_MODEL_NOT_APPROVED"),
    ("fable", "CURSOR_CLAUDE_REFUSED"),
    ("random-unknown-model", "CURSOR_MODEL_NOT_APPROVED"),
    ("composer-2.5[fast=true]", "CURSOR_MODEL_NOT_APPROVED"),
    ("composer-2.5[arbitrary=value]", "CURSOR_MODEL_NOT_APPROVED"),
]

def extract_argv(caller, model):
    if caller == "adapter":
        adapter = CursorAdapter()
        plan = adapter.build_invocation(
            prompt="hello", mode="workspace-write", cwd=Path("."), model=model,
            task_id="1", session_id=None, tool_config={"CURSOR_AUTO_ADMITTED": True}
        )
        return plan.cmd
    elif caller == "acpx":
        adapter = AcpxCursorShadowAdapter()
        tc = {"correlation_id": "1", "idempotency_key": "1", "acpx_transport": True}
        plan = adapter.build_invocation(
            prompt="hello", mode="read-only", cwd=Path("/tmp/nonprimary/.worktrees/w1"),
            model=model, task_id="1", session_id=None, tool_config=tc
        )
        return plan.cmd
    elif caller == "ask":
        with patch("subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout='{"verdict": "ok"}', stderr="")
            ask_cursor._invoke_cursor("hello", model=model)
            if not run_mock.called:
                return None
            return run_mock.call_args[0][0]
    elif caller == "judge":
        with patch("subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout='{"verdict": "ok"}', stderr="")
            cursor_judge.call_cursor("hello", model)
            if not run_mock.called:
                return None
            return run_mock.call_args[0][0]
@pytest.mark.parametrize("caller", CALLERS)
@pytest.mark.parametrize("input_model,expected_wire", MODELS_ALLOWED)
def test_callers_apply_wire_normalization(caller, input_model, expected_wire, monkeypatch):
    import scripts.agent_runtime.adapters.claude as claude_module
    monkeypatch.setattr(claude_module, "_default_claude_bin", lambda: "/usr/bin/claude")
    try:
        import scripts.agent_runtime.adapters.acpx as acpx_module
        monkeypatch.setattr(acpx_module, "_require_communication_transport", lambda **kw: None)
        monkeypatch.setattr(acpx_module, "_require_communication_target", lambda **kw: None)
    except Exception:
        pass

    argv = extract_argv(caller, input_model)
    model_idx = argv.index("--model")
    assert argv[model_idx + 1] == expected_wire

@pytest.mark.parametrize("caller", CALLERS)
@pytest.mark.parametrize("input_model,refusal_code", MODELS_REFUSED)
def test_callers_refuse_forbidden_variants(caller, input_model, refusal_code, monkeypatch):
    import scripts.agent_runtime.adapters.claude as claude_module
    monkeypatch.setattr(claude_module, "_default_claude_bin", lambda: "/usr/bin/claude")
    try:
        import scripts.agent_runtime.adapters.acpx as acpx_module
        monkeypatch.setattr(acpx_module, "_require_communication_transport", lambda **kw: None)
        monkeypatch.setattr(acpx_module, "_require_communication_target", lambda **kw: None)
    except Exception:
        pass

    with pytest.raises((ValueError, SystemExit, ModelCatalogError)) as excinfo:
        extract_argv(caller, input_model)
    assert refusal_code in str(excinfo.value)
