"""Synthetic generic component artifacts use the existing private output gate."""

import json

import pytest

from scripts.projects.open_model_data.review_build import output
from scripts.projects.open_model_data.review_build.build import execute
from scripts.projects.open_model_data.review_build.contract import digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.output import OutputGuard


class SyntheticArtifacts:
    def __init__(self, bundle, files):
        self.spec = bundle["spec"]
        self.adapters = {}
        self.files = {}
        self.bundle = bundle
        self.generated = files

    def iter_candidates(self, ctx):
        return iter(self.bundle["candidates"])

    def artifact_files(self, ctx):
        return self.generated


def test_private_component_artifacts_pinned_and_verified(bundle, monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda p: "ext4")
    generated = {"C1/review-packets/one.json": b'{"text":"SYNTHETIC review packet"}\n'}
    obj = SyntheticArtifacts(bundle, generated)
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard, component_objects={"C1": obj})
        manifest = json.loads(guard.read("manifest.json"))
        name = next(iter(generated))
        assert manifest["files"][name] == digest(generated[name])
        register = (bundle["root"] / "register.yaml").read_bytes()
        assert guard.read("permissions-register.yaml") == register
        assert manifest["files"]["permissions-register.yaml"] == manifest["pins"]["register"] == digest(register)
        assert (
            execute(bundle["root"] / "request.json", guard, verify=True, component_objects={"C1": obj})["status"]
            == "verified"
        )
        guard.write(name, b"SYNTHETIC tamper")
        with pytest.raises(BuildError, match="artifact_mismatch"):
            execute(bundle["root"] / "request.json", guard, verify=True, component_objects={"C1": obj})


@pytest.mark.parametrize(
    "files,code",
    [
        ({"manifest.json": b"SYNTHETIC"}, "artifact_conflict"),
        ({"C1/records.jsonl": b"SYNTHETIC"}, "artifact_conflict"),
        ({"permissions-register.yaml": b"SYNTHETIC"}, "artifact_conflict"),
        ({"../escape.json": b"SYNTHETIC"}, "output_name"),
        ({"C1/one.json": "SYNTHETIC"}, "component_artifact"),
    ],
)
def test_component_artifacts_refuse_conflicts_and_unsafe_paths(bundle, monkeypatch, files, code):
    monkeypatch.setattr(output, "filesystem", lambda p: "ext4")
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        with pytest.raises(BuildError, match=code):
            execute(bundle["root"] / "request.json", guard, component_objects={"C1": SyntheticArtifacts(bundle, files)})


@pytest.mark.parametrize("verify", [False, True], ids=["build", "verify"])
@pytest.mark.parametrize(
    "name",
    [
        "verification.json",
        "mutation-fixtures",
        "mutation-fixtures/results.json",
        "mutation-fixtures/component-results.json",
        "mutation-fixtures/absent_quote.jsonl",
        "mutation-fixtures/nested/arbitrary.bin",
    ],
)
def test_component_artifacts_refuse_reserved_outputs(bundle, monkeypatch, name, verify):
    monkeypatch.setattr(output, "filesystem", lambda p: "ext4")
    obj = SyntheticArtifacts(bundle, {})
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        if verify:
            execute(bundle["root"] / "request.json", guard, component_objects={"C1": obj})
        obj.generated = {name: b"SYNTHETIC forged proof"}
        with pytest.raises(BuildError, match=r"^artifact_conflict$"):
            execute(bundle["root"] / "request.json", guard, verify=verify, component_objects={"C1": obj})
        assert json.loads(guard.read("verification.json")) == {
            "schema": "omd-review-verification.v1",
            "status": "unverified",
        }
        assert not (guard.path / "mutation-fixtures").exists()
        assert (guard.path / "manifest.json").exists() == verify


@pytest.mark.parametrize(
    "name",
    [
        "verification.json.bak",
        "mutation-fixtures-backup/results.json",
        "C1/verification.json",
        "C1/mutation-fixtures/results.json",
    ],
)
def test_component_artifacts_allow_non_reserved_paths(bundle, monkeypatch, name):
    monkeypatch.setattr(output, "filesystem", lambda p: "ext4")
    content = b"SYNTHETIC ordinary artifact\n"
    obj = SyntheticArtifacts(bundle, {name: content})
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard, component_objects={"C1": obj})
        assert guard.read(name) == content
        assert json.loads(guard.read("manifest.json"))["files"][name] == digest(content)
        assert (
            execute(bundle["root"] / "request.json", guard, verify=True, component_objects={"C1": obj})["status"]
            == "verified"
        )
        assert guard.read(name) == content


def test_artifact_hook_cannot_change_component_policy(bundle, monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda p: "ext4")
    obj = SyntheticArtifacts(bundle, {})

    def mutate(ctx):
        obj.spec["compatibility"][0]["role"] = "forbidden"
        return {}

    obj.artifact_files = mutate
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        with pytest.raises(BuildError, match="spec_mutated"):
            execute(bundle["root"] / "request.json", guard, component_objects={"C1": obj})
