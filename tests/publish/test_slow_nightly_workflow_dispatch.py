"""Keep slow-nightly dispatch exact and reject unregistered publication inputs."""

import json

import pytest

from scripts.common.github_client import Response
from scripts.opsec import prepublish as gate
from scripts.publish import github as pub
from tests.common.github_cache_isolation import isolate_github_client_cache
from tests.opsec_fixtures import CATALOG


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    yield from isolate_github_client_cache(tmp_path, monkeypatch)


@pytest.fixture
def dispatch_calls(github_transport, synthetic_opsec, monkeypatch):
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.setenv("GH_HOST", "github.com")

    def respond(method, endpoint, headers, body, timeout):
        return Response(204, {}, b"")

    return github_transport(respond)


def test_missing_registration_or_wrong_dispatch_request(dispatch_calls):
    """An omitted workflow or a rewritten destination/ref breaks canonical dispatch."""
    assert pub.main([
        "workflow-run", "--repo", "unit/public",
        "--workflow", "pytest-slow-nightly.yml", "--ref", "reviewed/slow-nightly",
    ]) == 0
    assert [(method, endpoint, json.loads(body)) for method, endpoint, _, body, _ in dispatch_calls] == [
        (
            "POST",
            "repos/unit/public/actions/workflows/pytest-slow-nightly.yml/dispatches",
            {"ref": "reviewed/slow-nightly"},
        ),
    ]


def test_unknown_workflow_cannot_reach_dispatch(dispatch_calls, capsys):
    """A near-match filename must not bypass the exact workflow allowlist."""
    with pytest.raises(SystemExit) as error:
        pub.main([
            "workflow-run", "--repo", "unit/public",
            "--workflow", "pytest-slow-nightly.yaml", "--ref", "main",
        ])
    assert error.value.code == 2
    assert capsys.readouterr().err == "OPSEC: invalid publisher arguments; use --help.\n"
    assert dispatch_calls == []


def test_unexpected_inputs_and_fields_cannot_reach_dispatch(dispatch_calls, capsys):
    """No-input workflow registration must not admit extra inputs or raw fields."""
    assert pub.main([
        "workflow-run", "--repo", "unit/public",
        "--workflow", "pytest-slow-nightly.yml", "--ref", "main",
        "--inputs", '{"force": true}',
    ]) == 2
    assert capsys.readouterr().err == "OPSEC: invalid publisher field inputs.\n"
    with pytest.raises(gate.PublishBlocked, match="^OPSEC: unknown publisher field\\.$"):
        pub.publish(
            "workflow-run", repo="unit/public", workflow="pytest-slow-nightly.yml",
            ref="main", raw_field="force=true",
        )
    assert dispatch_calls == []


def test_invalid_ref_cannot_reach_dispatch(dispatch_calls, capsys):
    """A ref containing a newline must fail existing ref validation before transport."""
    assert pub.main([
        "workflow-run", "--repo", "unit/public",
        "--workflow", "pytest-slow-nightly.yml", "--ref", "main\nother",
    ]) == 2
    assert capsys.readouterr().err == "OPSEC: invalid publisher field ref.\n"
    assert dispatch_calls == []
