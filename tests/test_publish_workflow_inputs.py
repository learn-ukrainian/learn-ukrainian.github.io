"""Reject untyped workflow inputs and preserve the admitted dispatch request."""

import json
import subprocess

import pytest

from scripts.opsec import prepublish as gate
from scripts.publish import github as pub

SHA = "0123456789abcdefABCDEF0123456789abcdef01"


@pytest.mark.parametrize("entrypoint", ["publisher", "cli"])
def test_coverage_workflow_preserves_typed_sha_in_request(entrypoint, synthetic_opsec):
    calls = []

    def sender(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")

    if entrypoint == "cli":
        assert (
            pub.main(
                [
                    "workflow-run",
                    "--repo",
                    "unit/public",
                    "--workflow",
                    "coverage-ref.yml",
                    "--ref",
                    "main",
                    "--inputs",
                    json.dumps({"sha": SHA}),
                ],
                runner=sender,
            )
            == 0
        )
    else:
        assert (
            pub.publish(
                "workflow-run",
                repo="unit/public",
                workflow="coverage-ref.yml",
                ref="main",
                inputs={"sha": SHA},
                runner=sender,
            ).returncode
            == 0
        )
    assert calls == [
        [
            "gh",
            "workflow",
            "run",
            "coverage-ref.yml",
            "--repo",
            "unit/public",
            "--ref=main",
            "--raw-field=sha=" + SHA,
        ]
    ]


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param({}, id="omitted-inputs"),
        pytest.param({"inputs": {}}, id="missing-sha"),
        pytest.param({"inputs": {"sha": SHA, "extra": "value"}}, id="extra-key"),
        pytest.param({"inputs": {"sha": "a" * 39}}, id="short-sha"),
        pytest.param({"inputs": {"sha": "a" * 41}}, id="long-sha"),
        pytest.param({"inputs": {"sha": "g" * 40}}, id="non-hex-sha"),
        pytest.param({"inputs": {"sha": "a" * 39 + "\n"}}, id="newline-sha"),
        pytest.param({"inputs": {"sha": 123}}, id="integer-sha"),
        pytest.param({"inputs": {"sha": None}}, id="null-sha"),
        pytest.param({"inputs": {"sha": True}}, id="boolean-sha"),
        pytest.param({"inputs": None}, id="null-inputs"),
        pytest.param({"inputs": []}, id="list-inputs"),
        pytest.param({"inputs": "sha=" + SHA}, id="string-inputs"),
    ],
)
@pytest.mark.parametrize("entrypoint", ["publisher", "cli"])
def test_coverage_workflow_refuses_missing_or_untyped_inputs_before_send(fields, entrypoint):
    def sender(*args, **kwargs):
        pytest.fail("invalid inputs reached transport")

    if entrypoint == "cli":
        args = [
            "workflow-run",
            "--repo",
            "unit/public",
            "--workflow",
            "coverage-ref.yml",
            "--ref",
            "main",
        ]
        if "inputs" in fields:
            args += ["--inputs", json.dumps(fields["inputs"])]
        assert pub.main(args, runner=sender) == 2
    else:
        with pytest.raises(gate.PublishBlocked, match=r"^OPSEC: invalid publisher field inputs\.$"):
            pub.publish(
                "workflow-run",
                repo="unit/public",
                workflow="coverage-ref.yml",
                ref="main",
                runner=sender,
                **fields,
            )


@pytest.mark.parametrize(
    "workflow",
    [
        "ci.yml",
        "deploy-pages.yml",
        "stale-branch-cleanup.yml",
        "unknown.yml",
    ],
)
def test_sha_input_cannot_expand_other_workflow_permissions(workflow):
    with pytest.raises(gate.PublishBlocked):
        pub.publish(
            "workflow-run",
            repo="unit/public",
            workflow=workflow,
            ref="main",
            inputs={"sha": SHA},
            runner=lambda *args, **kwargs: pytest.fail("send"),
        )
