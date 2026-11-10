from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

from lu_machinery.agent_runtime.errors import AgentTimeoutError
from lu_machinery.agent_runtime.result import Result

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from batch_gemini_runner.constants import TIMEOUT_SECONDS
from batch_gemini_runner.execution import call_gemini


def _make_prompt_file(tmp_path: Path, text: str = "Say hello") -> Path:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(text, encoding="utf-8")
    return prompt_file


def test_return_shape_preserved(tmp_path):
    prompt_file = _make_prompt_file(tmp_path)
    payload = {
        "response": "structured text",
        "stats": {
            "models": {
                "gemini-3.1-pro-preview": {
                    "tokens": {
                        "input": 10,
                        "candidates": 4,
                        "cached": 0,
                    },
                },
            },
        },
    }
    runtime_result = Result(
        ok=True,
        agent="gemini",
        model="gemini-3.1-pro-preview",
        mode="read-only",
        response=json.dumps(payload),
        stderr_excerpt="runtime stderr",
        duration_s=0.25,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={},
    )

    with patch(
        "batch_gemini_runner.execution.runtime_invoke",
        return_value=runtime_result,
    ), patch(
        "batch_gemini_runner.execution._log_api_usage",
    ) as mock_log_usage:
        result = call_gemini(prompt_file, "bio", slug="demo", phase=2, retry=1)

    assert set(result.keys()) == {
        "returncode",
        "stdout",
        "stderr",
        "gemini_json",
        "elapsed_ms",
    }
    assert result["returncode"] == 0
    assert result["stdout"] == "structured text"
    assert result["stderr"] == "runtime stderr"
    assert result["gemini_json"] == payload
    assert result["elapsed_ms"] == 250
    mock_log_usage.assert_called_once()


def test_timeout_returns_existing_shape(tmp_path):
    prompt_file = _make_prompt_file(tmp_path)

    with patch(
        "batch_gemini_runner.execution.runtime_invoke",
        side_effect=AgentTimeoutError("gemini", TIMEOUT_SECONDS),
    ):
        result = call_gemini(prompt_file, "bio", slug="demo", phase=2, retry=0)

    assert result["returncode"] == -1
    assert "Timeout expired" in result["stderr"]
    assert result["stdout"] == ""
    assert result["gemini_json"] == {}
