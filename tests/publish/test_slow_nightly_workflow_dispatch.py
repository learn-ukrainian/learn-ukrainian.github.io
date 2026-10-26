"""Keep slow-nightly dispatch exact and reject unregistered publication inputs."""

import subprocess

import pytest

from scripts.opsec import prepublish as gate
from scripts.publish import github as pub
from tests.common.github_cache_isolation import isolate_github_client_cache
from tests.opsec_fixtures import CATALOG


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    yield from isolate_github_client_cache(tmp_path, monkeypatch)


@pytest.fixture
def dispatch_calls(tmp_path, synthetic_opsec, monkeypatch):
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.setenv("GH_HOST", "github.com")
    monkeypatch.setenv("GH_CONFIG_DIR", str(tmp_path / "gh-config"))
    calls = []

    def sender(argv, **kwargs):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, "", "")

    return calls, sender


def test_missing_registration_or_wrong_dispatch_request(dispatch_calls):
    """An omitted workflow or a rewritten destination/ref breaks canonical dispatch."""
    calls, sender = dispatch_calls
    assert pub.main([
        "workflow-run", "--repo", "unit/public",
        "--workflow", "pytest-slow-nightly.yml", "--ref", "reviewed/slow-nightly",
    ], runner=sender) == 0
    assert calls == [
        [
            "gh", "workflow", "run", "pytest-slow-nightly.yml",
            "--repo", "unit/public", "--ref=reviewed/slow-nightly",
        ],
    ]

    assert pub.main([
        "workflow-run", "--repo", "unit/public", "--workflow", "ci.yml", "--ref", "codex/fixture",
        "--inputs", '{"approved_pr":"42","expected_head":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
    ], runner=sender) == 0
    assert calls[-1] == ["gh", "workflow", "run", "ci.yml", "--repo", "unit/public", "--ref=codex/fixture",
                         "--raw-field=approved_pr=42", "--raw-field=expected_head=" + "a" * 40]


def test_unknown_workflow_cannot_reach_dispatch(dispatch_calls, capsys):
    """A near-match filename must not bypass the exact workflow allowlist."""
    calls, sender = dispatch_calls
    with pytest.raises(SystemExit) as error:
        pub.main([
            "workflow-run", "--repo", "unit/public",
            "--workflow", "pytest-slow-nightly.yaml", "--ref", "main",
        ], runner=sender)
    assert error.value.code == 2
    assert capsys.readouterr().err == "OPSEC: invalid publisher arguments; use --help.\n"
    assert calls == []


def test_unexpected_inputs_and_fields_cannot_reach_dispatch(dispatch_calls, capsys):
    """No-input workflow registration must not admit extra inputs or raw fields."""
    calls, sender = dispatch_calls
    assert pub.main([
        "workflow-run", "--repo", "unit/public",
        "--workflow", "pytest-slow-nightly.yml", "--ref", "main",
        "--inputs", '{"force": true}',
    ], runner=sender) == 2
    assert capsys.readouterr().err == "OPSEC: invalid publisher field inputs.\n"
    with pytest.raises(gate.PublishBlocked, match=r"^OPSEC: unknown publisher field\.$"):
        pub.publish(
            "workflow-run", repo="unit/public", workflow="pytest-slow-nightly.yml",
            ref="main", raw_field="force=true", runner=sender,
        )
    assert calls == []


def test_invalid_ref_cannot_reach_dispatch(dispatch_calls, capsys):
    """A ref containing a newline must fail existing ref validation before transport."""
    calls, sender = dispatch_calls
    assert pub.main([
        "workflow-run", "--repo", "unit/public",
        "--workflow", "pytest-slow-nightly.yml", "--ref", "main\nother",
    ], runner=sender) == 2
    assert capsys.readouterr().err == "OPSEC: invalid publisher field ref.\n"
    assert calls == []


@pytest.mark.parametrize("inputs,valid", [
    ({"approved_pr": "42", "expected_head": "a" * 40}, True),
    ({}, True), ({"approved_pr": "42"}, False), ({"expected_head": "a" * 40}, False),
    ({"approved_pr": "0", "expected_head": "a" * 40}, False),
    ({"approved_pr": "42", "expected_head": "a" * 40, "force": "true"}, False),
    ({"approved_pr": "42", "expected_head": "not-a-sha"}, False),
])
def test_ci_dispatch_inputs_remain_narrow_and_paired(inputs, valid):
    fields = {"workflow": "ci.yml", "ref": "codex/fixture", "inputs": inputs}
    if valid:
        pub._validate("workflow-run", fields)
    else:
        with pytest.raises(gate.PublishBlocked, match="inputs"):
            pub._validate("workflow-run", fields)
