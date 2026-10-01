from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

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
            "LU_AGENT_GITHUB_APP_PRIVATE_KEY": "synthetic-signing-material",
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


def restricted_payload():
    from datetime import UTC, datetime, timedelta

    return {
        "token": "synthetic-credential",
        "repositories": [{"full_name": "org/repo"}],
        "permissions": {"contents": "read", "metadata": "read"},
        "expires_at": (datetime.now(UTC) + timedelta(minutes=30)).isoformat(),
    }


def test_restricted_mint_uses_exact_scope_and_verified_tls(tmp_path, monkeypatch):
    import ssl

    from scripts.agent_runtime import agent_github_identity as module
    from tests.test_sibling_git_https import tls_server

    payload = restricted_payload()

    def respond(handler):
        handler.send_response(201)
        handler.end_headers()
        handler.wfile.write(json.dumps(payload).encode())

    monkeypatch.setattr(module.jwt, "encode", lambda *_a, **_kw: "synthetic-assertion")
    with tls_server(tmp_path, respond) as (url, ca, requests):
        token = module.mint_installation_token(
            app_id="fixture",
            private_key="synthetic",
            installation_id="fixture",
            repository="org/repo",
            permissions={"contents": "read"},
            api_base_url=url,
            ssl_context=ssl.create_default_context(cafile=str(ca)),
        )
    assert token == payload["token"]
    assert requests == [({"repositories": ["repo"], "permissions": {"contents": "read"}}, "Bearer synthetic-assertion")]


def test_restricted_identity_passes_minimum_permissions(tmp_path, monkeypatch):
    from scripts.agent_runtime import agent_github_identity as module

    captured = []
    monkeypatch.setattr(module, "mint_installation_token", lambda **kw: captured.append(kw) or "synthetic")
    result = module.resolve_agent_github_identity(
        environment={
            "LU_AGENT_GITHUB_APP_ID": "fixture",
            "LU_AGENT_GITHUB_APP_PRIVATE_KEY": "synthetic",
            "LU_AGENT_GITHUB_APP_INSTALLATION_ID": "fixture",
        },
        repository="org/repo",
        permissions={"contents": "read"},
    )
    assert result.source == "app"
    assert captured[0]["permissions"] == {"contents": "read"}
    assert captured[0]["repository"] == "org/repo"


def test_configured_key_file_and_existing_inline_call_contract(tmp_path, monkeypatch):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    from scripts.agent_runtime import agent_github_identity as module

    configured_file = tmp_path / "material"
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    material = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    configured_file.write_text(material)
    configured_file.chmod(0o600)
    captured = []
    monkeypatch.setattr(module, "mint_installation_token", lambda **kw: captured.append(kw) or "synthetic")
    result = module.resolve_agent_github_identity(
        environment={
            "LU_AGENT_GITHUB_APP_ID": "fixture",
            "LU_AGENT_GITHUB_APP_INSTALLATION_ID": "fixture",
            "LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE": str(configured_file),
        },
        repository="repo",
    )
    assert result.source == "app" and captured[0]["private_key"] == material
    assert "permissions" not in captured[0] and "api_base_url" not in captured[0]


def test_unreadable_configured_key_file_has_safe_error(tmp_path):
    import pytest

    from scripts.agent_runtime import agent_github_identity as module

    configured_file = tmp_path / "missing-material"
    with pytest.raises(module.GitHubIdentityError, match="configured key file") as error:
        module.resolve_agent_github_identity(environment={"LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE": str(configured_file)})
    assert str(configured_file) not in str(error.value)


def test_partial_file_configuration_cannot_fall_back(tmp_path, monkeypatch):
    import pytest

    from scripts.agent_runtime import agent_github_identity as module

    configured_file = tmp_path / "material"
    configured_file.write_text("synthetic")
    configured_file.chmod(0o600)
    with pytest.raises(module.GitHubIdentityError, match="incomplete"):
        module.resolve_agent_github_identity(
            environment={
                "LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE": str(configured_file),
                "LU_AGENT_GITHUB_TOKEN": "synthetic",
            }
        )


def test_restricted_mint_refuses_wider_scope_and_invalid_expiry(monkeypatch):
    import pytest

    from scripts.agent_runtime import agent_github_identity as module

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def read(self):
            return json.dumps(payload).encode()

    class Opener:
        def open(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr(module.jwt, "encode", lambda *_a, **_kw: "synthetic-assertion")
    monkeypatch.setattr(module.urllib.request, "build_opener", lambda *_args: Opener())
    mutations = [
        {"repositories": [{"full_name": "org/other"}]},
        {"repositories": [{"full_name": "other/repo"}]},
        {"repositories": []},
        {"repositories": [{"full_name": "org/repo"}, {"full_name": "org/other"}]},
        {"permissions": {"contents": "write"}},
        {"permissions": {"contents": "read", "issues": "read"}},
        {"permissions": {"contents": "read", "metadata": "write"}},
        {"permissions": {}},
        {"permissions": []},
        {"expires_at": "2000-01-01T00:00:00Z"},
        {"expires_at": "malformed"},
        {"expires_at": "2999-01-01T00:00:00"},
        {"expires_at": None},
        {"token": ""},
    ]
    for mutation in mutations:
        payload = restricted_payload() | mutation
        with pytest.raises(module.GitHubIdentityError) as error:
            module.mint_installation_token(
                app_id="fixture",
                private_key="synthetic",
                installation_id="fixture",
                repository="org/repo",
                permissions={"contents": "read"},
            )
        assert "synthetic-credential" not in str(error.value)
    for missing in ("repositories", "permissions", "expires_at"):
        payload = restricted_payload()
        del payload[missing]
        with pytest.raises(module.GitHubIdentityError, match="scope or expiry refused"):
            module.mint_installation_token(
                app_id="fixture",
                private_key="synthetic",
                installation_id="fixture",
                repository="org/repo",
                permissions={"contents": "read"},
            )


def test_mint_redirect_never_delivers_assertion(tmp_path, monkeypatch):
    import socket
    import ssl

    import pytest

    from scripts.agent_runtime import agent_github_identity as module
    from tests.test_sibling_git_https import tls_server

    def target(handler):
        handler.send_response(201)
        handler.end_headers()
        handler.wfile.write(json.dumps(restricted_payload()).encode())

    monkeypatch.setattr(module.jwt, "encode", lambda *_a, **_kw: "synthetic-assertion")
    with tls_server(tmp_path, target, family=socket.AF_INET6) as (target_url, target_ca, target_requests):

        def redirect(handler):
            handler.send_response(302)
            handler.send_header("Location", target_url + "/redirect")
            handler.end_headers()

        with tls_server(tmp_path, redirect) as (url, ca, source_requests):
            ca.write_bytes(ca.read_bytes() + target_ca.read_bytes())
            with pytest.raises(module.GitHubIdentityError, match="minting failed"):
                module.mint_installation_token(
                    app_id="fixture",
                    private_key="synthetic",
                    installation_id="fixture",
                    repository="org/repo",
                    permissions={"contents": "read"},
                    api_base_url=url,
                    ssl_context=ssl.create_default_context(cafile=str(ca)),
                )
            assert len(source_requests) == 1
            assert target_requests == []


def test_restricted_mint_excludes_parent_tls_overrides(tmp_path, monkeypatch):
    import pytest

    from scripts.agent_runtime import agent_github_identity as module
    from tests.test_sibling_git_https import tls_server

    def respond(handler):
        handler.send_response(201)
        handler.end_headers()
        handler.wfile.write(json.dumps(restricted_payload()).encode())

    monkeypatch.setattr(module.jwt, "encode", lambda *_a, **_kw: "synthetic-assertion")
    with tls_server(tmp_path, respond) as (url, ca, requests):
        monkeypatch.setenv("SSL_CERT_FILE", str(ca))
        monkeypatch.setenv("SSL_CERT_DIR", str(tmp_path))
        with pytest.raises(module.GitHubIdentityError, match="minting failed"):
            module.mint_installation_token(app_id="fixture", private_key="synthetic", installation_id="fixture",
                                           repository="org/repo", permissions={"contents": "read"}, api_base_url=url)
        assert requests == []


@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo", "group-read", "group-write", "world-read", "world-execute"])
def test_configured_key_file_refuses_unsafe_type_or_permissions(tmp_path, monkeypatch, capsys, kind):
    import os

    from scripts.agent_runtime import agent_github_identity as module

    path = tmp_path / "material"
    if kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path, 0o600)
    elif kind == "symlink":
        target = tmp_path / "target"
        target.write_text("generated-material")
        target.chmod(0o600)
        path.symlink_to(target)
    else:
        path.write_text("generated-material")
        path.chmod({"group-read": 0o640, "group-write": 0o620, "world-read": 0o604, "world-execute": 0o601}[kind])
    opened = []
    original = module.os.open

    def capture(*args, **kwargs):
        opened.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(module.os, "open", capture)
    with pytest.raises(module.GitHubIdentityError, match="configured key file") as error:
        module.resolve_agent_github_identity(environment={"LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE": str(path)})
    assert opened == []  # In particular, a FIFO is refused before opening it.
    assert str(path) not in str(error.value) and "generated-material" not in str(error.value)
    assert error.value.__suppress_context__ is True
    output = capsys.readouterr()
    assert output.out + output.err == ""


@pytest.mark.parametrize("changed", ["permissions", "inode", "fifo"])
def test_configured_key_file_revalidates_opened_descriptor(tmp_path, monkeypatch, changed):
    import os

    from scripts.agent_runtime import agent_github_identity as module

    path = tmp_path / "material"
    path.write_text("generated-material")
    path.chmod(0o600)
    original = module.os.open

    def replace_before_open(filename, flags):
        if changed == "permissions":
            path.chmod(0o640)
        else:
            replacement = tmp_path / "replacement"
            if changed == "fifo":
                os.mkfifo(replacement, 0o600)
            else:
                replacement.write_text("different-generated-material")
                replacement.chmod(0o600)
            replacement.replace(path)
        return original(filename, flags)

    monkeypatch.setattr(module.os, "open", replace_before_open)
    with pytest.raises(module.GitHubIdentityError, match="configured key file"):
        module.resolve_agent_github_identity(environment={"LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE": str(path)})


@pytest.mark.parametrize("status", [204, 500, 200])
def test_revoke_uses_same_token_and_safe_request_settings(tmp_path, monkeypatch, capsys, status):
    import ssl

    from scripts.agent_runtime import agent_github_identity as module
    from tests.test_sibling_git_https import TOKEN, tls_server

    def respond(handler):
        handler.send_response(status)
        handler.end_headers()
        handler.wfile.write(TOKEN.encode())

    # A poisoned proxy would prevent reaching this local endpoint if inherited.
    monkeypatch.setenv("HTTPS_PROXY", "http://unreachable.invalid:1")
    monkeypatch.setenv("NO_PROXY", "")
    with tls_server(tmp_path, respond) as (url, ca, requests):
        kwargs = {"api_base_url": url, "ssl_context": ssl.create_default_context(cafile=str(ca))}
        if status == 204:
            assert module.revoke_installation_token(TOKEN, **kwargs) is None
        else:
            with pytest.raises(module.GitHubIdentityError, match="revocation failed") as error:
                module.revoke_installation_token(TOKEN, **kwargs)
            assert TOKEN not in str(error.value)
            assert error.value.__suppress_context__ is True
        assert requests == [("/installation/token", f"Bearer {TOKEN}")]
    output = capsys.readouterr()
    assert output.out + output.err == ""


def test_revoke_redirect_never_delivers_token(tmp_path):
    import socket
    import ssl

    from scripts.agent_runtime import agent_github_identity as module
    from tests.test_sibling_git_https import TOKEN, tls_server

    def target(handler):
        handler.send_response(204)
        handler.end_headers()

    with tls_server(tmp_path, target, family=socket.AF_INET6) as (target_url, target_ca, target_requests):
        def redirect(handler):
            handler.send_response(302)
            handler.send_header("Location", target_url + "/other")
            handler.end_headers()

        with tls_server(tmp_path, redirect) as (url, ca, requests):
            ca.write_bytes(ca.read_bytes() + target_ca.read_bytes())
            with pytest.raises(module.GitHubIdentityError, match="revocation failed"):
                module.revoke_installation_token(TOKEN, api_base_url=url, ssl_context=ssl.create_default_context(cafile=str(ca)))
            assert requests == [("/installation/token", f"Bearer {TOKEN}")]
            assert target_requests == []


def test_revoke_excludes_parent_tls_overrides(tmp_path, monkeypatch):
    from scripts.agent_runtime import agent_github_identity as module
    from tests.test_sibling_git_https import TOKEN, tls_server

    def respond(handler):
        handler.send_response(204)
        handler.end_headers()

    with tls_server(tmp_path, respond) as (url, ca, requests):
        monkeypatch.setenv("SSL_CERT_FILE", str(ca))
        monkeypatch.setenv("SSL_CERT_DIR", str(tmp_path))
        with pytest.raises(module.GitHubIdentityError, match="revocation failed"):
            module.revoke_installation_token(TOKEN, api_base_url=url)
        assert requests == []
