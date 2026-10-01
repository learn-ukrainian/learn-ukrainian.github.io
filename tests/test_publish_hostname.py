"""Hostname selection regressions for all three typed API transport paths."""

import subprocess

import pytest

from scripts.opsec import prepublish as gate
from scripts.publish import github as pub
from tests.opsec_fixtures import CATALOG

VALID_DESTINATIONS = [
    ("github.com/unit/public", []),
    ("GitHub.com/unit/public", []),
    ("git.enterprise-example.test/unit/public", ["--hostname", "git.enterprise-example.test"]),
    ("GIT.Enterprise-Example.test/unit/public", ["--hostname", "git.enterprise-example.test"]),
    ("github.com.evil.example/unit/public", ["--hostname", "github.com.evil.example"]),
    ("evilgithub.com/unit/public", ["--hostname", "evilgithub.com"]),
    ("1-git.test/unit/public", ["--hostname", "1-git.test"]),
    ("unknown", []),
]
INVALID_DESTINATIONS = [
    "github.com@evil/unit/public",
    "github.com:443/unit/public",
    "",
    "/unit/public",
    "github.com",
    "github.com/",
    " github.com/unit/public",
    "github.com /unit/public",
    "git hub.com/unit/public",
    "github.com\t/unit/public",
    "github.com\n/unit/public",
    "github.com\r/unit/public",
    "github.com\0/unit/public",
    "github.com\x1f/unit/public",
    "github.com\x7f/unit/public",
    "gіthub.com/unit/public",  # Cyrillic i
    "github．com/unit/public",  # Full-width dot
    "Kithub.com/unit/public",  # Lowercasing would produce ASCII k
    "github.com\u202e/unit/public",  # Bidi control
    "git_hub.com/unit/public",
    ".github.com/unit/public",
    "github..com/unit/public",
    "github.com./unit/public",
    "-github.com/unit/public",
    "github-.com/unit/public",
]


@pytest.mark.parametrize("dest,expected", VALID_DESTINATIONS)
def test_hostname_flag_valid_destinations(dest, expected):
    assert pub._hostname_flag(dest) == expected


@pytest.mark.parametrize("dest", INVALID_DESTINATIONS)
def test_hostname_flag_rejects_malformed_hosts(dest):
    with pytest.raises(gate.PublishBlocked, match=r"^OPSEC: invalid publisher hostname\.$"):
        pub._hostname_flag(dest)


@pytest.fixture
def destination_transport(monkeypatch, synthetic_opsec):
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    calls = []

    def send(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "{}", "")

    def invoke(path, dest):
        # Exercise the transport boundary independently of resolver normalization.
        monkeypatch.setattr(pub, "repository", lambda *args: dest)
        if path == "publish-graphql":
            return pub.publish("issue-link", parent_id="parent", child_id="child", env={}, runner=send)
        if path == "read-graphql":
            return pub.read("budget" if dest == "unknown" else "membership", env={}, runner=send,
                            **({} if dest == "unknown" else {"number": 1}))
        return pub.read("identity", env={}, runner=send)

    return invoke, calls


@pytest.mark.parametrize("path", ["publish-graphql", "read-graphql", "read-rest"])
@pytest.mark.parametrize("dest,expected", VALID_DESTINATIONS)
def test_api_paths_select_exact_hostname(path, dest, expected, destination_transport):
    invoke, calls = destination_transport
    if path == "publish-graphql" and dest == "unknown":
        # Repository-bound publishing already refuses unresolved destinations.
        with pytest.raises(gate.PublishBlocked, match="publisher repository unresolved"):
            invoke(path, dest)
        assert calls == []
        return
    assert invoke(path, dest).returncode == 0
    assert len(calls) == 1
    argv = calls[0]
    assert argv[:4] == ["gh", "api", "--method", "GET" if path == "read-rest" else "POST"]
    if expected:
        assert argv[-2:] == expected
        assert argv.count("--hostname") == 1
    else:
        assert "--hostname" not in argv


@pytest.mark.parametrize("path", ["publish-graphql", "read-graphql", "read-rest"])
@pytest.mark.parametrize("dest", [dest for dest in INVALID_DESTINATIONS if "/" in dest and dest.split("/", 1)[1]])
def test_api_paths_reject_malformed_hostname_before_send(path, dest, destination_transport):
    invoke, calls = destination_transport
    with pytest.raises(gate.PublishBlocked, match="invalid publisher hostname"):
        invoke(path, dest)
    assert calls == []
