"""Host requests cannot widen admission; component policy and private initialization proof."""

import copy
import json
import os
import stat

import pytest

from scripts.projects.open_model_data.review_build import __main__ as cli
from scripts.projects.open_model_data.review_build import build, output, request
from scripts.projects.open_model_data.review_build.components import admission_policy
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.output import OutputGuard
from tests.projects.open_model_data.review_build.conftest import save_bundle, synthetic_components


@pytest.mark.parametrize("key", ["compatibility", "corpus", "components", "candidates", "adapters", "unknown"])
@pytest.mark.parametrize("verify", [False, True])
def test_request_policy_injection_refuses_before_loading_or_extracting(bundle, monkeypatch, capsys, key, verify):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    bundle["config"][key] = {"SYNTHETIC": "widen admission"}
    save_bundle(bundle)

    def forbidden(*args, **kwargs):
        pytest.fail("request policy reached component loading")

    monkeypatch.setattr(cli, "load_components", forbidden)
    out = bundle["root"] / "SYNTHETIC-out"
    args = ["verify" if verify else "build", "--config", str(bundle["root"] / "request.json"), "--out", str(out)]
    assert cli.main(args) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "request_policy_key"
    with OutputGuard(out) as guard, pytest.raises(BuildError, match="request_policy_key"):
        build.execute(
            bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle), verify=verify
        )
    assert not (out / "manifest.json").exists()


def test_v1_refused_with_clear_migration_error(bundle, monkeypatch, capsys):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    bundle["config"]["schema"] = "omd-review-request.v1"
    save_bundle(bundle)
    assert (
        cli.main(
            ["build", "--config", str(bundle["root"] / "request.json"), "--out", str(bundle["root"] / "SYNTHETIC-out")]
        )
        == 1
    )
    error = json.loads(capsys.readouterr().err)
    assert error["error"] == "request_schema"
    assert "v1" in error["hint"] and "v2" in error["hint"]


@pytest.mark.parametrize("command", ["build", "verify"])
def test_default_missing_request_has_initialization_hint(bundle, monkeypatch, capsys, command):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    monkeypatch.setattr(cli, "default_config", lambda: bundle["root"] / "missing.json")
    assert cli.main([command, "--out", str(bundle["root"] / "SYNTHETIC-out")]) == 1
    error = json.loads(capsys.readouterr().err)
    assert error["error"] == "request_missing" and "init-request" in error["hint"]


@pytest.mark.parametrize("use_default", [False, True])
def test_init_request_private_location_only_defaults(tmp_path, monkeypatch, capsys, use_default):
    root = tmp_path / "SYNTHETIC-repository"
    path = tmp_path / "private/request.json"
    monkeypatch.setattr(request, "repository_root", lambda: root)
    monkeypatch.setattr(cli, "default_config", lambda: path)
    args = ["init-request"] if use_default else ["init-request", "--path", str(path)]
    assert cli.main(args) == 0
    assert json.loads(capsys.readouterr().out) == {"status": "request_initialized"}
    _, config = request.read_request(path)
    assert config == {
        "schema": "omd-review-request.v2",
        "databases": {store: str(root / "data" / store) for store in ("sources.db", "vesum.db")},
        "ua_gec": {"root": str(root / "data/ua-gec")},
        "catalog": str(root / "registry/projects/open_model_data/instruction_catalog.yaml"),
        "register": str(root / "docs/sources/permissions-register.yaml"),
    }
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    original = path.read_bytes()
    assert cli.main(args) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "request_exists"
    assert path.read_bytes() == original
    with pytest.raises(SystemExit) as exited:
        cli.main(["init-request", "--help"])
    assert exited.value.code == 0
    help_text = capsys.readouterr().out
    assert all(text in help_text for text in ("--path", "0600", "0700", "Examples:", "Exit codes:"))


def test_init_request_refuses_symlinks_and_public_parent(tmp_path, monkeypatch):
    monkeypatch.setattr(request, "repository_root", lambda: tmp_path)
    public = tmp_path / "public"
    public.mkdir(mode=0o750)
    os.chmod(public, 0o750)
    with pytest.raises(BuildError, match="request_parent_mode"):
        request.init_request(public / "request.json")
    assert not (public / "request.json").exists()
    linked = tmp_path / "linked"
    linked.symlink_to(public, target_is_directory=True)
    with pytest.raises(OSError):
        request.init_request(linked / "request.json")
    target = tmp_path / "target.json"
    target.write_text("SYNTHETIC untouched")
    symlink = tmp_path / "request.json"
    symlink.symlink_to(target)
    with pytest.raises(BuildError, match="request_exists"):
        request.init_request(symlink)
    assert target.read_text() == "SYNTHETIC untouched"


@pytest.mark.parametrize("location", ["databases", "ua_gec"])
def test_nested_locations_cannot_contain_policy(bundle, location):
    bundle["config"][location] = {"root": "SYNTHETIC", "compatibility": [{"role": "modern"}]}
    save_bundle(bundle)
    with pytest.raises(BuildError, match="request_policy_key" if location == "ua_gec" else "request_locations"):
        request.read_request(bundle["root"] / "request.json")


@pytest.mark.parametrize("key", ["databases", "ua_gec", "catalog", "register"])
def test_required_input_location_missing_refuses(bundle, key):
    del bundle["config"][key]
    save_bundle(bundle)
    with pytest.raises(BuildError, match="request_locations"):
        request.read_request(bundle["root"] / "request.json")


@pytest.mark.parametrize("change", ["source_id", "source_values", "role", "sensitive", "quarantine"])
def test_competing_table_policy_refuses_before_extraction(bundle, monkeypatch, change):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    spec = copy.deepcopy(bundle["spec"])
    spec["compatibility"][0][change] = ["SYNTHETIC other"] if change == "source_values" else "SYNTHETIC other"
    bundle["specs"]["C9"] = spec
    objects = synthetic_components(bundle)

    def forbidden(ctx):
        pytest.fail("conflicting policy reached extraction")

    for obj in objects.values():
        obj.iter_candidates = forbidden
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        with pytest.raises(BuildError, match="compatibility_conflict"):
            build.execute(bundle["root"] / "request.json", guard, component_objects=objects)
        assert (
            build.execute(
                bundle["root"] / "request.json",
                guard,
                component_objects=synthetic_components(bundle),
                components=["C1"],
            )["status"]
            == "built"
        )


def test_selected_component_union_deduplicates_and_refuses_corpus_conflicts(bundle):
    spec = copy.deepcopy(bundle["spec"])
    other = {**spec["compatibility"][0], "table": "SYNTHETIC-other-table"}
    spec["compatibility"].append(other)
    corpus = {
        "store": "sources.db",
        "table": "units",
        "split": "split",
        "document": "document",
        "author": "author",
        "layer": "layer",
        "text": "source_field",
    }
    spec["corpus"] = corpus
    entries, mapping = admission_policy({"C1": bundle["spec"], "C9": spec})
    assert len(entries) == 2 and other in entries and mapping == corpus
    bundle["spec"]["corpus"] = {**corpus, "text": "target_field"}
    with pytest.raises(BuildError, match="corpus_conflict"):
        admission_policy({"C1": bundle["spec"], "C9": spec})


def test_admission_policy_drift_voids_verify_even_if_records_unchanged(bundle, monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    objects = synthetic_components(bundle)
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        build.execute(bundle["root"] / "request.json", guard, component_objects=objects)
        bundle["spec"]["compatibility"][0]["quarantine"] = "is_sensitive"
        with pytest.raises(BuildError, match="artifact_mismatch"):
            build.execute(bundle["root"] / "request.json", guard, component_objects=objects, verify=True)


def test_library_build_loads_registered_policy_without_request_specs(bundle, monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    selected = []

    def load(ids):
        selected.append(ids)
        return synthetic_components(bundle)

    monkeypatch.setattr(build, "load_components", load)
    monkeypatch.setattr(build, "REGISTRY", {"C1": "c1"})
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        assert build.execute(bundle["root"] / "request.json", guard)["status"] == "built"
        assert (
            build.execute(bundle["root"] / "request.json", guard, components=["C1"], verify=True)["status"]
            == "verified"
        )
    assert selected == [["C1"], ["C1"]]


@pytest.mark.parametrize(
    "policy", [{}, {"compatibility": {}}, {"compatibility": [None]}, {"compatibility": [], "corpus": []}]
)
def test_incomplete_component_policy_refuses(policy):
    with pytest.raises(BuildError, match="component_policy"):
        admission_policy({"C1": policy})
