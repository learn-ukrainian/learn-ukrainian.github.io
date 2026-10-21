from __future__ import annotations

import subprocess
from dataclasses import replace

from fastapi.testclient import TestClient

from scripts.ai_agent_bridge import openai_proxy as proxy


def _client() -> TestClient:
    return TestClient(proxy.app)


def _route_with_backend(model: str, backend):
    return replace(proxy._ROUTABLE_MODELS[model], backend=backend)


def _assert_openai_validation_error(response, field: str | None = None) -> None:
    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["type"] == "invalid_request_error"
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"]
    if field is not None:
        assert field in body["error"]["message"]


def test_models_endpoint_lists_routable_models():
    response = _client().get("/v1/models")

    assert response.status_code == 200
    model_ids = {item["id"] for item in response.json()["data"]}
    assert model_ids == set(proxy._ROUTABLE_MODELS)


def test_chat_completions_codex_round_trip(monkeypatch):
    def backend(model, messages, **kwargs):
        return proxy.CompletionResponse(content="hello from codex")

    monkeypatch.setitem(proxy._ROUTABLE_MODELS, "codex", _route_with_backend("codex", backend))

    response = _client().post(
        "/v1/chat/completions",
        json={"model": "codex", "messages": [{"role": "user", "content": "hello"}]},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["model"] == "codex"
    assert body["choices"][0]["message"]["content"] == "hello from codex"
    assert body["choices"][0]["finish_reason"] == "stop"


def test_chat_completions_unknown_model_returns_404():
    response = _client().post(
        "/v1/chat/completions",
        json={"model": "unknown-model-xyz", "messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "model_not_found"


def test_chat_completions_backend_failure_returns_502(monkeypatch):
    def backend(model, messages, **kwargs):
        raise subprocess.CalledProcessError(
            1,
            ["agent"],
            stderr="first failure line\nsecond failure line",
        )

    monkeypatch.setitem(proxy._ROUTABLE_MODELS, "codex", _route_with_backend("codex", backend))

    response = _client().post(
        "/v1/chat/completions",
        json={"model": "codex", "messages": [{"role": "user", "content": "hello"}]},
    )

    body = response.json()
    assert response.status_code == 502
    assert body["error"]["code"] == "backend_failed"
    assert "first failure line" in body["error"]["message"]
    assert "second failure line" not in body["error"]["message"]


def test_chat_completions_backend_timeout_returns_504(monkeypatch):
    def backend(model, messages, **kwargs):
        raise subprocess.TimeoutExpired(["agent"], timeout=120, stderr="timeout line\nlater")

    monkeypatch.setitem(proxy._ROUTABLE_MODELS, "codex", _route_with_backend("codex", backend))

    response = _client().post(
        "/v1/chat/completions",
        json={"model": "codex", "messages": [{"role": "user", "content": "hello"}]},
    )

    body = response.json()
    assert response.status_code == 504
    assert body["error"]["code"] == "backend_timeout"
    assert "timeout line" in body["error"]["message"]


def test_chat_completions_missing_messages_returns_422():
    response = _client().post("/v1/chat/completions", json={"model": "codex"})

    _assert_openai_validation_error(response, "messages")


def test_message_flatten_preserves_role_order(monkeypatch):
    prompts = []

    def backend(model, messages, **kwargs):
        prompts.append(kwargs["prompt"])
        return proxy.CompletionResponse(content="ok")

    monkeypatch.setitem(proxy._ROUTABLE_MODELS, "codex", _route_with_backend("codex", backend))

    response = _client().post(
        "/v1/chat/completions",
        json={
            "model": "codex",
            "messages": [
                {"role": "system", "content": "system rules"},
                {"role": "user", "content": "first user"},
                {"role": "assistant", "content": "first assistant"},
                {"role": "user", "content": "second user"},
            ],
        },
    )

    assert response.status_code == 200
    prompt = prompts[0]
    assert prompt.index("[system]: system rules") < prompt.index("[user]: first user")
    assert prompt.index("[user]: first user") < prompt.index("[assistant]: first assistant")
    assert prompt.index("[assistant]: first assistant") < prompt.index("[user]: second user")


def test_codex_proxy_is_stateless_and_uses_caller_supplied_history(monkeypatch):
    prompts = []
    backend_kwargs = []

    def backend(model, messages, **kwargs):
        prompts.append(kwargs["prompt"])
        backend_kwargs.append(kwargs)
        return proxy.CompletionResponse(content="ok")

    monkeypatch.setitem(proxy._ROUTABLE_MODELS, "codex", _route_with_backend("codex", backend))

    first = _client().post(
        "/v1/chat/completions",
        json={
            "model": "codex",
            "user": "same-user",
            "messages": [{"role": "user", "content": "first"}],
        },
    )
    second = _client().post(
        "/v1/chat/completions",
        json={
            "model": "codex",
            "user": "same-user",
            "messages": [
                {"role": "user", "content": "first"},
                {"role": "assistant", "content": "answer"},
                {"role": "user", "content": "second"},
            ],
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(prompts) == 2
    assert all("session_id" not in kwargs for kwargs in backend_kwargs)
    assert prompts[0] == "--- Round 1 ---\n[user]: first"
    assert "[assistant]: answer" in prompts[1]
    assert "[user]: second" in prompts[1]


def test_healthz_endpoint_returns_backend_status(monkeypatch):
    # Clear any cached state from other tests to keep this test isolated
    with proxy._healthz_cache_lock:
        proxy._healthz_cache.clear()
        proxy._healthz_in_flight.clear()

    monkeypatch.setattr(proxy, "_BRIDGE_HEALTHZ_TTL_SECS", 60)
    monkeypatch.setattr(
        proxy,
        "_BACKEND_PROBES",
        {
            "codex": lambda: (True, "codex v1.2.3"),
            "gemini": lambda: (False, ""),
            "claude": lambda: (True, "claude v4.0"),
            "hermes": lambda: (False, ""),
        },
    )

    response = _client().get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "backends": {
            "codex": True,
            "gemini": False,
            "claude": True,
            "hermes": False,
        },
    }


def test_claude_backend_runs_without_background_work(monkeypatch):
    """The headless Claude backend carries the #9690 controls from the adapter (#9750)."""
    from scripts.agent_runtime.adapters.claude import HEADLESS_BACKGROUND_ENV, HEADLESS_BACKGROUND_TOOL_DENIES

    seen = []

    def run(argv, **kwargs):
        seen.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, stdout="fixture", stderr="")

    monkeypatch.setenv("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS", "0")
    monkeypatch.setattr(proxy.subprocess, "run", run)
    proxy._claude_backend("claude-opus-5-5", [proxy.Message(role="user", content="fixture")])
    ((argv, kwargs),) = seen
    assert argv[argv.index("--disallowedTools") + 1].split(",") == list(HEADLESS_BACKGROUND_TOOL_DENIES)
    defaults = {"TERM": "xterm-256color", "COLORTERM": "truecolor"}
    assert kwargs["env"] == {**defaults, **proxy._PARENT_ENV, **HEADLESS_BACKGROUND_ENV}


def test_codex_backend_rejects_override_before_preparation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("unauthorized model reached preparation")

    monkeypatch.setattr(proxy.tempfile, "NamedTemporaryFile", forbidden)
    monkeypatch.setattr(proxy, "_run_backend_command", forbidden)
    for model in ("gpt-5.6-terra", "unknown", ""):
        monkeypatch.setenv("BRIDGE_PROXY_CODEX_MODEL", model)
        response = _client().post(
            "/v1/chat/completions",
            json={"model": "codex", "messages": [{"role": "user", "content": "fixture"}]},
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "model_not_allowed"
