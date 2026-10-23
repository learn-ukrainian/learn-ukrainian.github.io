"""Catch missing slow-nightly registration and unintended dispatch permissions."""

import json
import subprocess

import pytest

from scripts.opsec import prepublish as gate
from scripts.publish import github as pub


@pytest.mark.parametrize("entrypoint", ["publisher", "cli"])
@pytest.mark.parametrize("ref", ["main", "unit/reviewed", "0123456789abcdef0123456789abcdef01234567"])
@pytest.mark.parametrize("fields", [{}, {"inputs": {}}], ids=["omitted-inputs", "empty-inputs"])
def test_missing_slow_nightly_registration_blocks_normalized_dispatch(entrypoint, ref, fields, synthetic_opsec):
    calls = []

    def sender(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")

    if entrypoint == "cli":
        args = ["workflow-run", "--repo", "unit/public", "--workflow", "pytest-slow-nightly.yml", "--ref", ref]
        if "inputs" in fields:
            args += ["--inputs", json.dumps(fields["inputs"])]
        assert pub.main(args, runner=sender) == 0
    else:
        assert (
            pub.publish(
                "workflow-run",
                repo="unit/public",
                workflow="pytest-slow-nightly.yml",
                ref=ref,
                runner=sender,
                **fields,
            ).returncode
            == 0
        )
    assert calls == [["gh", "workflow", "run", "pytest-slow-nightly.yml", "--repo", "unit/public", "--ref=" + ref]]


def test_unknown_workflow_cannot_reach_dispatch_transport():
    def sender(*args, **kwargs):
        pytest.fail("unknown workflow reached transport")

    with pytest.raises(gate.PublishBlocked, match="invalid publisher field workflow"):
        pub.publish("workflow-run", repo="unit/public", workflow="unknown.yml", ref="main", runner=sender)
    with pytest.raises(SystemExit) as error:
        pub.main(
            ["workflow-run", "--repo", "unit/public", "--workflow", "unknown.yml", "--ref", "main"], runner=sender
        )
    assert error.value.code == 2


@pytest.mark.parametrize("fields", [{"extra": "value"}, {"inputs": {"force": "true"}}, {"inputs": None}])
def test_slow_nightly_unexpected_fields_and_inputs_cannot_reach_transport(fields):
    def sender(*args, **kwargs):
        pytest.fail("unexpected fields or inputs reached transport")

    with pytest.raises(gate.PublishBlocked):
        pub.publish(
            "workflow-run", repo="unit/public", workflow="pytest-slow-nightly.yml", ref="main", runner=sender, **fields
        )
    args = ["workflow-run", "--repo", "unit/public", "--workflow", "pytest-slow-nightly.yml", "--ref", "main"]
    for key, value in fields.items():
        args += ["--" + key, json.dumps(value) if key == "inputs" else value]
    if "extra" in fields:
        with pytest.raises(SystemExit) as error:
            pub.main(args, runner=sender)
        assert error.value.code == 2
    else:
        assert pub.main(args, runner=sender) == 2


@pytest.mark.parametrize("ref", ["", "--flag", "main\nother", "main other", "main;other"])
def test_slow_nightly_invalid_ref_cannot_reach_dispatch_transport(ref):
    def sender(*args, **kwargs):
        pytest.fail("invalid ref reached transport")

    with pytest.raises(gate.PublishBlocked, match="invalid publisher field ref"):
        pub.publish("workflow-run", repo="unit/public", workflow="pytest-slow-nightly.yml", ref=ref, runner=sender)
    assert (
        pub.main(
            ["workflow-run", "--repo", "unit/public", "--workflow", "pytest-slow-nightly.yml", "--ref=" + ref],
            runner=sender,
        )
        == 2
    )
