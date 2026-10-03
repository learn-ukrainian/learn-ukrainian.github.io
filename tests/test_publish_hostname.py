"""Resolve hosts once for built-in, REST and GraphQL publishing transports."""

import subprocess

import pytest

from scripts.opsec import prepublish as gate
from scripts.opsec.gh_snapshot import repository
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
    ("g/unit/public", ["--hostname", "g"]),
    ("7/unit/public", ["--hostname", "7"]),
    ("unknown", []),
]
INVALID_DESTINATIONS = [
    "github.com@evil/unit/public",
    "github.com:443/unit/public",
    "",
    "/unit/public",
    "github.com",
    "github.com/",
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


SOURCES = ["explicit", "explicit-host", "environment", "environment-host", "origin-https", "origin-http", "origin-ssh"]
PATHS = ["publish-builtin", "publish-rest", "publish-graphql", "read-graphql", "read-rest"]


@pytest.mark.parametrize("dest,expected", VALID_DESTINATIONS)
def test_hostname_flag_uses_normalized_destinations(dest, expected):
    assert pub._hostname_flag(gate.normalize_repository(dest)) == expected


@pytest.mark.parametrize("dest", INVALID_DESTINATIONS)
def test_resolver_rejects_malformed_hosts(dest):
    assert gate.normalize_repository(dest) == "unknown"


@pytest.fixture
def destination_transport(monkeypatch, synthetic_opsec):
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    calls = []

    def send(argv, **kwargs):
        calls.append((argv, kwargs["env"]))
        return subprocess.CompletedProcess(argv, 0, "{}", "")

    def invoke(path, dest, source):
        host, _, short = dest.partition("/")
        environment, fields = {}, {}
        origin = "not-a-repository"
        if source == "explicit":
            fields["repo"] = dest
        elif source == "explicit-host":
            fields["repo"] = short
            environment["GH_HOST"] = host
        elif source == "environment":
            environment["GH_REPO"] = dest
        elif source == "environment-host":
            environment.update(GH_REPO=short, GH_HOST=host)
        elif source == "origin-ssh":
            origin = f"git@{host}:{short}.git"
        else:
            origin = f"{source.removeprefix('origin-')}://{dest}.git"

        def git_read(argv, **kwargs):
            assert argv == ["git", "remote", "get-url", "origin"]
            return subprocess.CompletedProcess(argv, 0, origin, "")

        # Keep real resolution/normalization; replace only the local Git probe.
        monkeypatch.setattr(pub, "repository", lambda *args: repository(*args, reader=git_read))
        if path == "publish-builtin":
            return pub.publish("issue-reopen", number=1, env=environment, runner=send, **fields)
        if path == "publish-rest":
            return pub.publish("issue-comment-json", number=1, body="clean", env=environment, runner=send, **fields)
        if path == "publish-graphql":
            return pub.publish(
                "issue-link", parent_id="parent", child_id="child", env=environment, runner=send, **fields
            )
        if path == "read-graphql":
            return pub.read("membership", number=1, env=environment, runner=send, **fields)
        return pub.read("issue", number=1, env=environment, runner=send, **fields)

    return invoke, calls


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("dest,expected", VALID_DESTINATIONS[:-1])
def test_transports_select_exact_hostname(source, path, dest, expected, destination_transport):
    invoke, calls = destination_transport
    assert invoke(path, dest, source).returncode == 0
    assert len(calls) == 1
    argv, environment = calls[0]
    host = dest.split("/", 1)[0].lower()
    assert environment["GH_HOST"] == host
    if path == "publish-builtin":
        assert argv == ["gh", "issue", "reopen", "1", "--repo", "unit/public"]
        return
    assert argv[:4] == ["gh", "api", "--method", "GET" if path == "read-rest" else "POST"]
    if path == "publish-rest":
        assert "--hostname" not in argv
        return  # REST publishing selects the validated host through GH_HOST.
    if expected:
        index = argv.index("--hostname")
        assert argv[index : index + 2] == expected
        assert argv.count("--hostname") == 1
    else:
        assert "--hostname" not in argv


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("dest", [dest for dest in INVALID_DESTINATIONS if dest.endswith("/unit/public")])
def test_transports_reject_malformed_hostname_before_send(source, path, dest, destination_transport):
    invoke, calls = destination_transport
    with pytest.raises(gate.PublishBlocked):
        invoke(path, dest, source)
    assert calls == []


@pytest.mark.parametrize("path", PATHS)
def test_repository_bound_transports_refuse_unknown(path, destination_transport):
    invoke, calls = destination_transport
    with pytest.raises(gate.PublishBlocked, match="repository unresolved"):
        invoke(path, "unknown", "environment")
    assert calls == []


@pytest.mark.parametrize("operation", ["identity", "budget"])
def test_unbound_reads_preserve_unknown(operation, monkeypatch):
    monkeypatch.setattr(pub, "repository", lambda *args: "unknown")
    calls = []

    def send(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "{}", "")

    assert pub.read(operation, env={}, runner=send).returncode == 0
    assert len(calls) == 1
    assert "--hostname" not in calls[0]
