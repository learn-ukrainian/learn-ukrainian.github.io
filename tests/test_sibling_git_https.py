"""Synthetic HTTPS transport boundary proof (#9399)."""

from __future__ import annotations

import base64
import ipaddress
import json
import os
import socket
import ssl
import subprocess
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlsplit

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from scripts.agent_runtime import agent_github_identity as identity
from scripts.fleet import sibling_git as sg
from scripts.orchestration.fleet_repos import FleetRepo
from tests.test_sibling_git import advance, git, snapshot
from tests.test_sibling_git import world as world_fixture

world = world_fixture

_REAL_INIT = sg.Git.__init__
TOKEN = "synthetic-credential"
HEADER = "Basic " + base64.b64encode(f"x-access-token:{TOKEN}".encode()).decode()


@pytest.fixture
def https_world(world, tmp_path, monkeypatch):
    primary, sibling, _upstream = world
    catalog = {
        "public": FleetRepo("public", "org/public", primary.name, "public", True),
        "test": FleetRepo("test", "org/repo", sibling.name, "sibling"),
    }
    registry = tmp_path / "registry.yaml"
    registry.write_text("repos:\n  test:\n    transport: https\n")
    monkeypatch.setattr(sg, "_REGISTRY_PATH", registry)
    monkeypatch.setattr(sg, "load_fleet_repos", lambda: catalog)
    def isolated_init(self, hooks, **kwargs):
        _REAL_INIT(self, hooks, **kwargs)
        self.env["GIT_CONFIG_SYSTEM"] = os.devnull

    monkeypatch.setattr(sg.Git, "__init__", isolated_init)
    monkeypatch.setenv("LU_AGENT_GITHUB_APP_ID", "fixture")
    monkeypatch.setattr(sg, "resolve_agent_github_identity", lambda **kw: identity.GitHubIdentity(TOKEN, "app"))
    monkeypatch.setattr(sg, "revoke_installation_token", lambda *_a, **_kw: None)
    git(sibling, "remote", "set-url", "origin", "https://github.com/org/repo.git")
    return world


@contextmanager
def tls_server(tmp_path, respond, *, family=socket.AF_INET):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append((self.path, self.headers.get("Authorization")))
            respond(self)

        def do_DELETE(self):
            requests.append((self.path, self.headers.get("Authorization")))
            respond(self)

        def do_POST(self):
            self.body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append((self.body, self.headers.get("Authorization")))
            respond(self)

        def log_message(self, *_args):
            pass

    address = socket.getaddrinfo(None, 0, family, socket.SOCK_STREAM)[0][4][0]
    server_type = type("FixtureServer", (ThreadingHTTPServer,), {"address_family": family})
    with server_type((address, 0), Handler) as server:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "fixture")])
        now = datetime.now(UTC)
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1))
            .not_valid_after(now + timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(address))]), False)
            .sign(key, hashes.SHA256())
        )
        cert_file = tmp_path / f"certificate-{server.server_port}"
        key_file = tmp_path / f"material-{server.server_port}"
        cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        key_file.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
            )
        )
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host = f"[{address}]" if family == socket.AF_INET6 else address
            yield f"https://{host}:{server.server_port}", cert_file, requests
        finally:
            server.shutdown()
            thread.join(timeout=5)
        assert not thread.is_alive()


def static_response(upstream, *, accepted=HEADER):
    def respond(handler):
        if handler.headers.get("Authorization") != accepted:
            handler.send_response(401)
            handler.send_header("WWW-Authenticate", 'Basic realm="fixture"')
            handler.end_headers()
            return
        path = upstream / urlsplit(handler.path).path.removeprefix("/org/repo.git/").removeprefix("/org/repo/")
        if not path.is_file():
            handler.send_response(404)
            handler.end_headers()
            return
        data = path.read_bytes()
        handler.send_response(200)
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)

    return respond


def runner(tmp_path, url, ca):
    scratch = tmp_path / "scratch"
    scratch.mkdir(exist_ok=True)
    return sg.Git(scratch, https_base_url=url, ca_file=ca)


def resolved(world, runner):
    return sg.resolve_repository("test", world[0], runner)


def test_https_authenticated_fast_forward_and_credential_containment(https_world, tmp_path, monkeypatch, capsys):
    sha = advance(https_world, tmp_path)
    git(https_world[2], "update-server-info")
    captured = []
    original = subprocess.run

    def capture(args, **kwargs):
        result = original(args, **kwargs)
        captured.append((args, kwargs["env"].copy(), result.stdout, result.stderr))
        return result

    with tls_server(tmp_path, static_response(https_world[2])) as (url, ca, requests):
        client = runner(tmp_path, url, ca)
        repo = resolved(https_world, client)
        monkeypatch.setattr(sg.subprocess, "run", capture)
        assert sg.sync_main(repo, https_world[0], client)["head"] == sha
        assert sg.status(repo, client)["clean"] is True
        assert requests and all(header == HEADER for _, header in requests)
    assert git(https_world[1], "rev-parse", "HEAD") == sha
    assert (https_world[1] / "file.txt").read_text() == "fetched\n"
    fetches = [entry for entry in captured if "fetch" in entry[0]]
    assert len(fetches) == 1
    header_environment = fetches[0][1]
    assert HEADER in header_environment.values() or f"Authorization: {HEADER}" in header_environment.values()
    for args, env, out, err in captured:
        assert TOKEN not in str(args) + out + err
        assert HEADER not in str(args) + out + err
        if "fetch" not in args:
            assert TOKEN not in str(env) and HEADER not in str(env)
    for file in (https_world[1] / ".git/config", https_world[1] / ".git/FETCH_HEAD"):
        assert TOKEN not in file.read_text() and HEADER not in file.read_text()
    output = capsys.readouterr()
    assert TOKEN not in output.out + output.err and HEADER not in output.out + output.err


def test_redirect_fails_without_delivering_credential(https_world, tmp_path):
    def target(handler):
        handler.send_response(200)
        handler.end_headers()

    with tls_server(tmp_path, target, family=socket.AF_INET6) as (target_url, target_ca, target_requests):

        def redirect(handler):
            handler.send_response(302)
            handler.send_header("Location", target_url + "/other")
            handler.end_headers()

        with tls_server(tmp_path, redirect) as (url, ca, source_requests):
            ca.write_bytes(ca.read_bytes() + target_ca.read_bytes())
            client = runner(tmp_path, url, ca)
            before = git(https_world[1], "rev-parse", "HEAD")
            with pytest.raises(sg.Refusal, match="HTTPS fetch failed"):
                sg.sync_main(resolved(https_world, client), https_world[0], client)
            assert source_requests == [("/org/repo.git/info/refs?service=git-upload-pack", HEADER)]
            assert target_requests == []
            assert git(https_world[1], "rev-parse", "HEAD") == before


@pytest.mark.parametrize(
    "key",
    [
        "url.https://github.com/.insteadOf",
        "http.proxy",
        "http.extraHeader",
        "include.path",
        "credential.helper",
        "credential.username",
        "credential.useHttpPath",
        "credential.interactive",
        "credential.https://github.com.username",
    ],
)
@pytest.mark.parametrize("scope", ["local", "worktree", "command"])
def test_config_refused_before_mint_or_network(https_world, tmp_path, monkeypatch, key, scope):
    calls = []
    monkeypatch.setattr(sg, "resolve_agent_github_identity", lambda **kw: calls.append(kw))
    with tls_server(tmp_path, static_response(https_world[2])) as (url, ca, requests):
        client = runner(tmp_path, url, ca)
        included = tmp_path / "included"
        included.write_text("")
        value = str(included) if key == "include.path" else "unsafe"
        if scope == "command":
            client.env.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0=key, GIT_CONFIG_VALUE_0=value)
        else:
            if scope == "worktree":
                git(https_world[1], "config", "extensions.worktreeConfig", "true")
            git(https_world[1], "config", "--" + scope, key, value)
        before = snapshot(https_world[1])
        with pytest.raises(sg.Refusal, match="unsupported redirect"):
            sg.sync_main(resolved(https_world, client), https_world[0], client)
        assert calls == [] and requests == []
        assert snapshot(https_world[1]) == before


def test_hostile_environment_is_excluded(https_world, tmp_path, monkeypatch):
    hostile = {
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "GIT_SSL_NO_VERIFY",
        "GIT_SSL_CAINFO",
        "GIT_SSL_CAPATH",
        "SSL_CERT_FILE",
        "CURL_CA_BUNDLE",
        "GIT_ASKPASS",
        "SSH_ASKPASS",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_KEY_0",
        "GIT_CONFIG_VALUE_0",
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
        "DYLD_INSERT_LIBRARIES",
        "GIT_TRACE",
        "GIT_TRACE_CURL",
        "GIT_TRACE_PACKET",
        "GIT_TRACE2_EVENT",
    }
    original = subprocess.run
    captured = []

    def capture(args, **kwargs):
        if "fetch" in args:
            captured.append(kwargs["env"].copy())
        return original(args, **kwargs)

    with tls_server(tmp_path, static_response(https_world[2])) as (url, ca, _):
        git(https_world[2], "update-server-info")
        client = runner(tmp_path, url, ca)
        repo = resolved(https_world, client)
        for key in hostile:
            monkeypatch.setenv(key, "hostile-value")
        monkeypatch.setattr(sg.subprocess, "run", capture)
        sg.sync_main(repo, https_world[0], client)
    assert len(captured) == 1
    assert all(captured[0].get(key) != "hostile-value" for key in hostile)
    assert captured[0]["GIT_ALLOW_PROTOCOL"] == "https"
    assert captured[0]["HOME"] == str(client.scratch)


def test_ambient_netrc_cannot_authenticate(https_world, tmp_path, monkeypatch):
    netrc_header = "Basic " + base64.b64encode(b"fixture:ambient").decode()
    with tls_server(tmp_path, static_response(https_world[2], accepted=netrc_header)) as (url, ca, requests):
        home = tmp_path / "ambient-home"
        home.mkdir()
        (home / ".netrc").write_text(f"machine {urlsplit(url).hostname} login fixture password ambient\n")
        (home / ".netrc").chmod(0o600)
        monkeypatch.setenv("HOME", str(home))
        git(https_world[2], "update-server-info")
        # Control: the same TLS endpoint accepts credentials from ambient HOME.
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(home),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
        result = subprocess.run(
            ["/usr/bin/git", "-c", f"http.sslCAInfo={ca}", "ls-remote", url + "/org/repo.git"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0
        assert any(header == netrc_header for _, header in requests)
        requests.clear()
        client = runner(tmp_path, url, ca)
        with pytest.raises(sg.Refusal, match="HTTPS fetch failed"):
            sg.sync_main(resolved(https_world, client), https_world[0], client)
        assert requests and all(header != netrc_header for _, header in requests)


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/org/other.git",
        "https://github.com/org/repo.git/extra",
        "https://github.com/org/repo.git?query",
        "https://github.com/org/repo.git#fragment",
        "https://userinfo@github.com/org/repo.git",
        "http://github.com/org/repo.git",
        "https://api.github.com/org/repo.git",
        "https://github.com:443/org/repo.git",
    ],
)
def test_wrong_credential_destination_refused_before_resolution(https_world, tmp_path, monkeypatch, url):
    calls = []
    monkeypatch.setattr(sg, "resolve_agent_github_identity", lambda **kw: calls.append(kw))
    client = runner(tmp_path, None, None)
    repo = sg.Repository(
        "test", https_world[1], https_world[1] / ".git", https_world[1] / ".git", url, "https", "org/repo"
    )
    with pytest.raises(sg.Refusal, match="canonical HTTPS"):
        client.fetch(repo)
    assert calls == []


@pytest.mark.parametrize("source", ["token", "legacy", None])
def test_non_app_identity_refused(https_world, tmp_path, monkeypatch, source):
    monkeypatch.setattr(sg, "resolve_agent_github_identity", lambda **kw: identity.GitHubIdentity(TOKEN, source))
    client = runner(tmp_path, None, None)
    before = snapshot(https_world[1])
    with pytest.raises(sg.Refusal, match="App installation identity") as error:
        sg.sync_main(resolved(https_world, client), https_world[0], client)
    assert TOKEN not in str(error.value)
    assert snapshot(https_world[1]) == before


@pytest.mark.parametrize("variable, value", [
    ("LU_AGENT_GITHUB_TOKEN", TOKEN), ("GH_TOKEN", TOKEN), ("GITHUB_TOKEN", TOKEN),
    ("LU_AGENT_GITHUB_APP_UNRELATED", TOKEN), ("LU_AGENT_GITHUB_APP_ID", ""),
])
def test_broad_environment_identity_never_resolved(https_world, tmp_path, monkeypatch, variable, value):
    monkeypatch.delenv("LU_AGENT_GITHUB_APP_ID")
    for name in list(os.environ):
        if name.startswith("LU_AGENT_GITHUB_APP_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv(variable, value)
    calls = []
    monkeypatch.setattr(sg, "resolve_agent_github_identity", lambda **kw: calls.append(kw))
    client = runner(tmp_path, None, None)
    with pytest.raises(sg.Refusal, match="App installation identity"):
        sg.sync_main(resolved(https_world, client), https_world[0], client)
    assert calls == []


def test_revoked_credential_fails_closed_and_hides_diagnostics(https_world, tmp_path, capsys):
    def revoked(handler):
        handler.send_response(401)
        handler.send_header("WWW-Authenticate", 'Basic realm="fixture"')
        handler.end_headers()
        handler.wfile.write(TOKEN.encode())

    with tls_server(tmp_path, revoked) as (url, ca, requests):
        client = runner(tmp_path, url, ca)
        before = git(https_world[1], "rev-parse", "HEAD")
        with pytest.raises(sg.Refusal, match="HTTPS fetch failed") as error:
            sg.sync_main(resolved(https_world, client), https_world[0], client)
        assert requests and all(header == HEADER for _, header in requests)
        assert TOKEN not in str(error.value) and HEADER not in str(error.value)
        assert git(https_world[1], "rev-parse", "HEAD") == before
    output = capsys.readouterr()
    assert TOKEN not in output.out + output.err


@pytest.mark.parametrize("state", ["dirty", "diverged"])
def test_https_preserves_dirty_and_diverged_checkouts(https_world, tmp_path, state):
    advance(https_world, tmp_path)
    git(https_world[2], "update-server-info")
    if state == "dirty":
        (https_world[1] / "file.txt").write_text("local work\n")
    else:
        from tests.test_sibling_git import commit

        commit(https_world[1], "local.txt", "local work\n")
    with tls_server(tmp_path, static_response(https_world[2])) as (url, ca, requests):
        client = runner(tmp_path, url, ca)
        before = git(https_world[1], "rev-parse", "HEAD")
        with pytest.raises(sg.Refusal, match=r"dirty|diverged"):
            sg.sync_main(resolved(https_world, client), https_world[0], client)
        assert git(https_world[1], "rev-parse", "HEAD") == before
        if state == "dirty":
            assert requests == []
            assert (https_world[1] / "file.txt").read_text() == "local work\n"
        else:
            assert requests
            assert (https_world[1] / "local.txt").read_text() == "local work\n"


@pytest.mark.parametrize("suffix", ["", ".git"])
def test_exact_origin_spellings(https_world, tmp_path, suffix):
    git(https_world[1], "remote", "set-url", "origin", "https://github.com/org/repo" + suffix)
    git(https_world[2], "update-server-info")
    with tls_server(tmp_path, static_response(https_world[2])) as (url, ca, requests):
        client = runner(tmp_path, url, ca)
        repo = resolved(https_world, client)
        assert repo.remote == "https://github.com/org/repo" + suffix
        assert sg.sync_main(repo, https_world[0], client)["changed"] is False
        assert requests and all(path.startswith("/org/repo" + suffix + "/") for path, _ in requests)
        assert all(header == HEADER for _, header in requests)


def test_transport_default_and_invalid_value(tmp_path, monkeypatch):
    registry = tmp_path / "registry.yaml"
    monkeypatch.setattr(sg, "_REGISTRY_PATH", registry)
    registry.write_text("repos:\n  test: {}\n")
    assert sg._registry_transport("test") == "ssh"
    registry.write_text("repos:\n  test:\n    transport: other\n")
    with pytest.raises(sg.Refusal, match="unsupported registered transport"):
        sg._registry_transport("test")


@pytest.mark.parametrize("credential_state", ["valid", "wrong-repository", "expired"])
def test_generated_app_credential_end_to_end(https_world, tmp_path, monkeypatch, credential_state):
    from tests.test_agent_github_identity import restricted_payload

    signing_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    configured_file = tmp_path / "material"
    configured_file.write_bytes(
        signing_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        )
    )
    configured_file.chmod(0o600)
    monkeypatch.setenv("LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE", str(configured_file))
    monkeypatch.setenv("LU_AGENT_GITHUB_APP_INSTALLATION_ID", "fixture")
    monkeypatch.delenv("LU_AGENT_GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.setattr(sg, "resolve_agent_github_identity", identity.resolve_agent_github_identity)
    payload = restricted_payload()
    if credential_state == "wrong-repository":
        payload["repositories"] = [{"full_name": "org/other"}]
    elif credential_state == "expired":
        payload["expires_at"] = "2000-01-01T00:00:00Z"

    monkeypatch.setattr(sg, "revoke_installation_token", identity.revoke_installation_token)

    def mint_response(handler):
        if handler.command == "DELETE":
            handler.send_response(204)
            handler.end_headers()
            return
        assertion = handler.headers["Authorization"].removeprefix("Bearer ")
        claims = identity.jwt.decode(assertion, signing_key.public_key(), algorithms=["RS256"])
        assert claims["iss"] == "fixture"
        handler.send_response(201)
        handler.end_headers()
        handler.wfile.write(json.dumps(payload).encode())

    sha = advance(https_world, tmp_path)
    git(https_world[2], "update-server-info")
    with tls_server(tmp_path, mint_response) as (api_url, api_ca, api_requests):
        with tls_server(tmp_path, static_response(https_world[2])) as (url, ca, fetch_requests):
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            client = sg.Git(
                scratch,
                https_base_url=url,
                ca_file=ca,
                api_base_url=api_url,
                ssl_context=ssl.create_default_context(cafile=str(api_ca)),
            )
            repo = resolved(https_world, client)
            if credential_state == "valid":
                assert sg.sync_main(repo, https_world[0], client)["head"] == sha
                assert git(https_world[1], "rev-parse", "HEAD") == sha
                assert fetch_requests and all(header == HEADER for _, header in fetch_requests)
            else:
                before = snapshot(https_world[1])
                with pytest.raises(sg.Refusal, match="restricted installation credential unavailable") as error:
                    sg.sync_main(repo, https_world[0], client)
                assert fetch_requests == []
                assert snapshot(https_world[1]) == before
                assert TOKEN not in str(error.value)
            assert len(api_requests) == (2 if credential_state == "valid" else 1)
            if credential_state == "valid":
                assert api_requests[1] == ("/installation/token", f"Bearer {TOKEN}")
            assert api_requests[0][0] == {"repositories": ["repo"], "permissions": {"contents": "read"}}


def test_untrusted_tls_certificate_fails_closed(https_world, tmp_path):
    with tls_server(tmp_path, static_response(https_world[2])) as (url, _, requests):
        client = runner(tmp_path, url, None)
        repo = resolved(https_world, client)
        before = git(https_world[1], "rev-parse", "HEAD")
        with pytest.raises(sg.Refusal, match="HTTPS fetch failed"):
            sg.sync_main(repo, https_world[0], client)
        assert requests == []
        assert git(https_world[1], "rev-parse", "HEAD") == before


def test_signing_failure_is_a_safe_typed_refusal(https_world, tmp_path, monkeypatch):
    monkeypatch.setenv("LU_AGENT_GITHUB_APP_PRIVATE_KEY", "synthetic")
    monkeypatch.setenv("LU_AGENT_GITHUB_APP_INSTALLATION_ID", "fixture")
    monkeypatch.setattr(sg, "resolve_agent_github_identity", identity.resolve_agent_github_identity)

    def signing_failure(**_kwargs):
        raise identity.jwt.InvalidKeyError(TOKEN)

    monkeypatch.setattr(identity, "mint_installation_token", signing_failure)
    client = runner(tmp_path, None, None)
    before = snapshot(https_world[1])
    with pytest.raises(sg.Refusal, match="restricted installation credential unavailable") as error:
        sg.sync_main(resolved(https_world, client), https_world[0], client)
    assert TOKEN not in str(error.value)
    assert error.value.__suppress_context__ is True
    assert snapshot(https_world[1]) == before


@pytest.mark.parametrize("setting", ["sslVerify", "proxy", "followRedirects", "sslCAInfo"])
def test_url_scoped_transport_settings_win_after_probe(https_world, tmp_path, monkeypatch, setting):
    git(https_world[2], "update-server-info")

    def respond(handler):
        if setting == "followRedirects":
            handler.send_response(302)
            handler.send_header("Location", "/other")
            handler.end_headers()
        else:
            static_response(https_world[2])(handler)

    with tls_server(tmp_path, respond) as (url, ca, requests):
        client = runner(tmp_path, url, None if setting == "sslVerify" else ca)
        repo = resolved(https_world, client)
        value = {
            "sslVerify": "false", "proxy": "http://unreachable.invalid:1",
            "followRedirects": "true", "sslCAInfo": str(tmp_path / "absent-ca"),
        }[setting]

        def mint(**_kwargs):
            # Simulate a config write after both probes but before the child.
            git(https_world[1], "config", f"http.{url}/org/repo.git.{setting}", value)
            return identity.GitHubIdentity(TOKEN, "app")

        monkeypatch.setattr(sg, "resolve_agent_github_identity", mint)
        if setting in {"sslVerify", "followRedirects"}:
            with pytest.raises(sg.Refusal, match="HTTPS fetch failed"):
                client.fetch(repo)
            assert requests == ([] if setting == "sslVerify" else [
                ("/org/repo.git/info/refs?service=git-upload-pack", HEADER)
            ])
        else:
            client.fetch(repo)
            assert requests and all(header == HEADER for _, header in requests)


def test_direct_fetch_rechecks_configuration_before_credential(https_world, tmp_path, monkeypatch):
    client = runner(tmp_path, None, None)
    repo = resolved(https_world, client)
    git(https_world[1], "config", "credential.helper", "unsafe")
    calls = []

    def unexpected_mint(**kwargs):
        calls.append(kwargs)
        raise RuntimeError("credential should not be requested")

    monkeypatch.setattr(sg, "resolve_agent_github_identity", unexpected_mint)
    with pytest.raises(sg.Refusal, match="unsupported redirect"):
        client.fetch(repo)
    assert calls == []


@pytest.mark.parametrize("fetch_state", ["success", "failure", "timeout"])
@pytest.mark.parametrize("revoke_fails", [False, True])
def test_fetch_revokes_same_token_once_without_changing_outcome(
    https_world, tmp_path, monkeypatch, capsys, fetch_state, revoke_fails,
):
    client = runner(tmp_path, None, None)
    repo = resolved(https_world, client)
    events = []
    original = sg.subprocess.run

    def fetch(args, **kwargs):
        if "fetch" not in args:
            return original(args, **kwargs)
        events.append("fetch")
        if fetch_state == "timeout":
            raise subprocess.TimeoutExpired(args, 120, output=TOKEN, stderr=TOKEN)
        return subprocess.CompletedProcess(args, 0 if fetch_state == "success" else 1, TOKEN, TOKEN)

    def revoke(token, **kwargs):
        events.append("revoke")
        assert token == TOKEN
        assert kwargs == {"api_base_url": client.api_base_url, "ssl_context": client.ssl_context}
        if revoke_fails:
            raise RuntimeError(TOKEN)

    monkeypatch.setattr(sg.subprocess, "run", fetch)
    monkeypatch.setattr(sg, "revoke_installation_token", revoke)
    if fetch_state == "success":
        assert client.fetch(repo) is None
    else:
        with pytest.raises(sg.Refusal, match="HTTPS fetch failed") as error:
            client.fetch(repo)
        assert TOKEN not in str(error.value)
        assert error.value.__suppress_context__ is True or fetch_state == "failure"
    assert events == ["fetch", "revoke"]
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ("Installation credential revocation failed\n" if revoke_fails else "")
    assert TOKEN not in output.out + output.err
