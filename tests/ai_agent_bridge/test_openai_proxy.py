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


def test_chat_completions_grok_via_hermes(monkeypatch):
    def backend(model, messages, **kwargs):
        return proxy.CompletionResponse(content="hello from grok")

    monkeypatch.setitem(proxy._ROUTABLE_MODELS, "grok-4.3", _route_with_backend("grok-4.3", backend))

    response = _client().post(
        "/v1/chat/completions",
        json={"model": "grok-4.3", "messages": [{"role": "user", "content": "hello"}]},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["model"] == "grok-4.3"
    assert body["choices"][0]["message"]["content"] == "hello from grok"
    assert body["choices"][0]["finish_reason"] == "stop"


def test_chat_completions_gemini_round_trip(monkeypatch):
    model_id = "gemini-3.0-flash-preview"

    def backend(model, messages, **kwargs):
        return proxy.CompletionResponse(content="hello from gemini")

    monkeypatch.setitem(proxy._ROUTABLE_MODELS, model_id, _route_with_backend(model_id, backend))

    response = _client().post(
        "/v1/chat/completions",
        json={"model": model_id, "messages": [{"role": "user", "content": "hello"}]},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["model"] == model_id
    assert body["choices"][0]["message"]["content"] == "hello from gemini"
    assert body["choices"][0]["finish_reason"] == "stop"


def test_chat_completions_claude_round_trip(monkeypatch):
    model_id = "claude-sonnet-4-7"

    def backend(model, messages, **kwargs):
        return proxy.CompletionResponse(content="hello from claude")

    monkeypatch.setitem(proxy._ROUTABLE_MODELS, model_id, _route_with_backend(model_id, backend))

    response = _client().post(
        "/v1/chat/completions",
        json={"model": model_id, "messages": [{"role": "user", "content": "hello"}]},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["model"] == model_id
    assert body["choices"][0]["message"]["content"] == "hello from claude"
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


def test_chat_completions_missing_model_returns_422():
    response = _client().post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    _assert_openai_validation_error(response, "model")


def test_chat_completions_messages_wrong_type_returns_422():
    response = _client().post(
        "/v1/chat/completions",
        json={"model": "codex", "messages": "hello"},
    )

    _assert_openai_validation_error(response, "messages")


def test_chat_completions_empty_body_returns_422():
    response = _client().post("/v1/chat/completions", json={})

    _assert_openai_validation_error(response, "model")


def test_chat_completions_invalid_json_body_returns_422():
    response = _client().post(
        "/v1/chat/completions",
        content='{"model": "codex", "messages":',
        headers={"content-type": "application/json"},
    )

    _assert_openai_validation_error(response)


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


def test_healthz_endpoint_returns_backend_status(monkeypatch):
    monkeypatch.setattr(
        proxy,
        "_BACKEND_PROBES",
        {
            "codex": lambda: True,
            "gemini": lambda: False,
            "claude": lambda: True,
            "hermes": lambda: False,
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
