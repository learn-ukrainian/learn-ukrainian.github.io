from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.agent_github_identity import resolve_agent_github_identity
from agent_runtime.env_sanitize import build_agent_env


def test_dedicated_agent_token_replaces_parent_github_tokens() -> None:
    parent_env = {
        "PATH": "/usr/bin",
        "HOME": "/Users/example",
        "GH_TOKEN": "ghp_operator",
        "GITHUB_TOKEN": "ghp_operator_other",
        "LU_AGENT_GITHUB_TOKEN": "ghp_agent",
    }

    with patch.dict("os.environ", parent_env, clear=True):
        env = build_agent_env(provider="codex")

    assert env["GH_TOKEN"] == "ghp_agent"
    assert env["LU_AGENT_GITHUB_IDENTITY_SOURCE"] == "token"
    assert "GITHUB_TOKEN" not in env


def test_app_identity_mints_a_repository_scoped_token(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def read(self) -> bytes:
            return b'{"token":"ghs_app_token"}'

        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    def fake_urlopen(request, *, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("agent_runtime.agent_github_identity.urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr("agent_runtime.agent_github_identity.jwt.encode", lambda *_args, **_kwargs: "signed-jwt")
    identity = resolve_agent_github_identity(
        environment={
            "LU_AGENT_GITHUB_APP_ID": "123",
            "LU_AGENT_GITHUB_APP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\\nkey",
            "LU_AGENT_GITHUB_APP_INSTALLATION_ID": "456",
        },
        repository="learn-ukrainian",
    )

    request = captured["request"]
    assert identity.token == "ghs_app_token"
    assert identity.source == "app"
    assert request.full_url.endswith("/app/installations/456/access_tokens")
    assert json.loads(request.data.decode("utf-8")) == {"repositories": ["learn-ukrainian"]}
    assert request.get_header("Authorization") == "Bearer signed-jwt"
    assert captured["timeout"] == 15


def test_legacy_identity_falls_back_with_a_warning(tmp_path, capsys) -> None:
    secrets_path = tmp_path / ".bash_secrets"
    secrets_path.write_text("export GITHUB_TOKEN=ghp_operator\n", encoding="utf-8")

    identity = resolve_agent_github_identity(environment={}, bash_secrets_path=secrets_path)

    assert identity.token == "ghp_operator"
    assert identity.source == "legacy"
    assert "operator GitHub identity" in capsys.readouterr().err
