from __future__ import annotations

import subprocess
from collections.abc import Callable

import pytest

from scripts.ai_agent_bridge import openai_proxy as proxy


@pytest.mark.parametrize(
    ("backend", "model"),
    [
        (proxy._gemini_backend, "gemini-3.1-pro-preview"),
        (proxy._claude_backend, "claude-sonnet-4-7"),
        (proxy._hermes_backend, "grok-4.5"),
    ],
)
def test_large_prompt_is_passed_via_stdin(
    monkeypatch: pytest.MonkeyPatch,
    backend: Callable[..., proxy.CompletionResponse],
    model: str,
) -> None:
    prompt = "x" * 300_000
    captured: dict[str, object] = {}

    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["argv"] = argv
        captured["input"] = kwargs.get("input")
        return subprocess.CompletedProcess(argv, 0, stdout="backend response\n", stderr="")

    monkeypatch.setattr(proxy.subprocess, "run", fake_run)
    monkeypatch.setattr(proxy, "_hermes_python_argv", lambda: ["hermes-python"])

    completion = backend(model, [], prompt=prompt)

    argv = captured["argv"]
    assert isinstance(argv, list)
    assert completion.content == "backend response"
    assert captured["input"] == prompt
    assert all(prompt not in str(item) for item in argv)
