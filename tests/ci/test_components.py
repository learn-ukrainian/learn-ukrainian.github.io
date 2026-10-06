"""Component inventory, conservative closure and runnable interface contracts."""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci import components as c


@pytest.fixture
def manifest():
    return c.load_manifest()


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, timeout=30)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init")
    for name, text in {
        "scripts/config.py": "CONFIG = 1\n",
        "scripts/ci/components.py": "# runner\n",
        "curriculum/hidden.yaml": "version: 1\n",
        "tests/test_fixture.py": "def test_fixture():\n    assert True\n",
        "scripts/ci/frontend_change_denominator.json": json.dumps({"version": "1", "paths": ["site/"]}),
        "requirements-lock.txt": "# lock\n",
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    git(tmp_path, "add", ".")
    return tmp_path


def test_manifest_approved_nodes_edges_and_no_frozen_test_ids(manifest):
    assert set(manifest["components"]) == set(c.NODE_IDS)
    assert manifest["schema_version"] == 1
    assert manifest["plan_version"] == 2
    assert len(manifest["edges"]) == len({edge["id"] for edge in manifest["edges"]})
    pairs = {(e["producer"], e["consumer"]) for e in manifest["edges"]}
    required = {
        ("curriculum-generation", "atlas-data"), ("atlas-data", "curriculum-generation"),
        ("atlas-data", "curriculum-display"), ("shared-core", "curriculum-generation"),
        ("shared-core", "practice-frontend"), ("atlas-data", "open-model-data"),
        ("shared-core", "open-model-data"), ("harness", "open-model-data"),
        ("atlas-data", "atlas-data"), ("curriculum-generation", "curriculum-display"),
        ("open-model-data", "open-model-data"),
    }
    assert required <= pairs
    for frontend in manifest["selector_contracts"]["frontend_components"]:
        assert ("atlas-data", frontend) in pairs
        assert ("practice-frontend", frontend) in pairs
        assert (frontend, "curriculum-generation") in pairs
    assert any(e["kind"] == "dynamic" and e["resolved"] for e in manifest["edges"])
    assert all("::" not in path for node in manifest["components"].values() for path in node["test_files"])


def test_exact_overrides_precede_longest_prefix_and_shared_fallback(manifest):
    assert c.assign_path("scripts/practice/euphony_stem_engine.py", manifest) == (["shared-core"], "exact")
    assert c.assign_path("scripts/practice/new.py", manifest) == (["practice-frontend"], "prefix")
    assert c.assign_path("tests/test_unclassified.py", manifest) == (["shared-core"], "prefix")
    assert c.assign_path("new-root/file.txt", manifest) == (list(c.NODE_IDS), "unmapped")
    assert c.assign_path("../outside", manifest) == (list(c.NODE_IDS), "unmapped")


def test_ambiguous_and_dynamic_unknowns_select_all(manifest):
    manifest["path_prefixes"].append({"path": "scripts/practice/", "components": ["atlas-data"]})
    assert c.assign_path("scripts/practice/new.py", manifest)[1] == "ambiguous"
    assert set(c.affected(["scripts/practice/new.py"], manifest)["components"]) == set(c.NODE_IDS)
    manifest["unresolved_edges"] = [{"path": "scripts/atlas/loader.py"}]
    assert c.assign_path("scripts/atlas/loader.py", manifest)[1] == "dynamic-unresolved"
    manifest["edges"][0]["resolved"] = False
    assert c.affected(["scripts/projects/open_model_data/view.py"], manifest)["fallback_reasons"] == ["dynamic-unresolved"]


def test_affected_reaches_cycle_consumers_shared_and_empty(manifest):
    selected = c.affected(["curriculum/a.yaml"], manifest)["components"]
    assert {"curriculum-generation", "curriculum-display", "atlas-data", "atlas-frontend", "practice-frontend", "open-model-data"} <= set(selected)
    assert set(c.affected(["scripts/config.py"], manifest)["components"]) == set(c.NODE_IDS)
    assert c.affected([], manifest)["components"] == []
    assert c.affected(["scripts/projects/open_model_data/view.py"], manifest)["components"] == ["open-model-data"]


def test_inventory_includes_index_only_sparse_and_odd_paths(repo, manifest):
    hidden = repo / "curriculum/hidden.yaml"
    hidden.unlink()
    odd = repo / 'site/слово "name".ts'
    odd.parent.mkdir()
    odd.write_text("// fixture\n")
    git(repo, "add", str(odd.relative_to(repo)))
    assert "curriculum/hidden.yaml" in c.tracked_paths(repo)
    assert str(odd.relative_to(repo)) in c.tracked_paths(repo)
    report = c.inventory(manifest, repo)
    assert report["unassigned"] == report["unmapped_test_files"] == report["selector_parity_gaps"] == 0
    assert report["tracked_paths"] == 7
    rogue = repo / "new-root/file.py"
    rogue.parent.mkdir()
    rogue.write_text("# new\n")
    git(repo, "add", str(rogue.relative_to(repo)))
    assert c.inventory(manifest, repo)["unassigned"] == 1


def test_parity_detects_missing_frontend_consumer_edge(repo, manifest):
    manifest["exact_paths"]["site/new.ts"] = ["open-model-data"]
    assert c.parity_gaps(["site/new.ts"], manifest, repo) == ["site/new.ts"]


@pytest.mark.parametrize("mutation", ["schema", "node", "owner", "test-id", "prefix", "argv", "edge"])
def test_manifest_validation_rejects_bad_contract(tmp_path, manifest, mutation):
    if mutation == "schema":
        manifest["schema_version"] = 2
    elif mutation == "node":
        manifest["components"].pop("harness")
    elif mutation == "owner":
        manifest["exact_paths"]["a"] = ["unknown"]
    elif mutation == "test-id":
        manifest["components"]["harness"]["test_files"] = ["tests/test_a.py::test_one"]
    elif mutation == "prefix":
        manifest["path_prefixes"].append({"path": "scripts", "components": ["harness"]})
    elif mutation == "argv":
        manifest["components"]["harness"]["verify"][0]["argv"] = []
    else:
        manifest["edges"][0]["consumer"] = "unknown"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        c.load_manifest(path)


def test_test_prefixes_expand_index_and_absence_refuses(repo, manifest):
    manifest["components"]["harness"]["test_files"] = []
    manifest["components"]["harness"]["test_prefixes"] = ["tests/"]
    assert c.test_files("harness", manifest, repo) == ["tests/test_fixture.py"]
    (repo / "tests/test_fixture.py").unlink()
    with pytest.raises(ValueError, match="absent"):
        c.test_files("harness", manifest, repo)


def test_collect_ids_at_check_time_and_collection_failure(repo, monkeypatch):
    monkeypatch.setattr(c, "project_interpreter", lambda root: Path(sys.executable))
    (repo / "pytest.ini").write_text("[pytest]\naddopts = -v\n")
    path = repo / "tests/test_fixture.py"
    path.write_text("import pytest\n@pytest.mark.parametrize('n', [1, 2])\ndef test_fixture(n):\n    assert n > 0\n")
    ids, code = c.collect_tests(["tests/test_fixture.py"], [], repo)
    assert code == 0
    assert ids == ["tests/test_fixture.py::test_fixture[1]", "tests/test_fixture.py::test_fixture[2]"]
    path.write_text("raise RuntimeError('broken collection')\n")
    assert c.collect_tests(["tests/test_fixture.py"], [], repo)[1] != 0


def input_wrapper(repo, manifest, component="atlas-data"):
    member = repo / "input.json"
    member.write_text('{"schema_version": 1}\n')
    return {
        "schema": "component-inputs.v1", "component": component,
        "identities": c.current_identities(component, manifest, repo),
        "families": [{"name": name, "schema": "existing-family-schema", "version": 1,
                      "members": [{"name": name, "path": "input.json", "sha256": hashlib.sha256(member.read_bytes()).hexdigest()}]}
                     for name in manifest["components"][component]["input_families"]],
    }


def test_input_verification_and_source_lock_drift(repo, manifest):
    wrapper = input_wrapper(repo, manifest)
    path = repo / "inputs.json"
    path.write_text(json.dumps(wrapper))
    members = c.verify_inputs(path, "atlas-data", manifest, repo)
    assert members["lexicon-manifest"] == repo / "input.json"
    (repo / "requirements-lock.txt").write_text("# changed lock\n")
    with pytest.raises(ValueError, match="stale"):
        c.verify_inputs(path, "atlas-data", manifest, repo)


@pytest.mark.parametrize("mutation", ["schema", "component", "missing-family", "duplicate", "corrupt", "missing", "traversal", "symlink", "version"])
def test_input_refusals_do_not_write_outputs(repo, manifest, mutation):
    wrapper = input_wrapper(repo, manifest)
    if mutation in {"schema", "component"}:
        wrapper[mutation] = "wrong"
    elif mutation == "missing-family":
        wrapper["families"].pop()
    elif mutation == "duplicate":
        wrapper["families"].append(copy.deepcopy(wrapper["families"][0]))
    elif mutation == "corrupt":
        (repo / "input.json").write_text("corrupt\n")
    elif mutation == "missing":
        (repo / "input.json").unlink()
    elif mutation == "traversal":
        wrapper["families"][0]["members"][0]["path"] = "../outside"
    elif mutation == "symlink":
        (repo / "input.json").unlink()
        (repo / "input.json").symlink_to(repo.parent)
    else:
        wrapper["families"][0]["version"] = 0
    path = repo / "inputs.json"
    path.write_text(json.dumps(wrapper))
    with pytest.raises(ValueError):
        c.verify_inputs(path, "atlas-data", manifest, repo)
    assert not (repo / "output").exists()


def test_expand_commands_fixed_argv_and_missing_inputs(repo, monkeypatch):
    monkeypatch.setattr(c, "project_interpreter", lambda root: Path(sys.executable))
    command = {"argv": ["{python}", "producer.py", "{member:source}", "{output_dir}/artifact.json"]}
    args = c.expand_command(command, repo, repo / "out", {"source": repo / "source $(literal).json"})
    assert args == [sys.executable, "producer.py", str(repo / "source $(literal).json"), str(repo / "out/artifact.json")]
    with pytest.raises(ValueError, match="missing named"):
        c.expand_command(command, repo, repo / "out", {})
    with pytest.raises(ValueError, match="output-dir"):
        c.expand_command(command, repo, None, {"source": repo / "source.json"})
    with pytest.raises(ValueError, match="placeholder"):
        c.expand_command({"argv": ["{unknown}"]}, repo, None, {})


def test_run_commands_real_pass_failure_and_skips(repo, monkeypatch):
    monkeypatch.setattr(c, "project_interpreter", lambda root: Path(sys.executable))
    command = {"argv": ["{python}", "-m", "pytest", "-q", "tests/test_fixture.py"], "cwd": ".", "scope": "code-contract"}
    reports, code = c.run_commands([command], repo, None, {})
    assert code == 0 and reports[0]["result"] == "pass"
    (repo / "tests/test_fixture.py").write_text("import pytest\ndef test_fixture():\n    pytest.skip('artifact absent')\n")
    reports, code = c.run_commands([command], repo, None, {})
    assert code == 3 and reports[0]["result"] == "artifact-dependent" and reports[0]["skipped"] == 1
    (repo / "tests/test_fixture.py").write_text("def test_fixture():\n    assert False\n")
    reports, code = c.run_commands([command], repo, None, {})
    assert code == 1 and reports[0]["result"] == "fail"


def test_atlas_build_argv_runs_real_db_search_and_daily_producers(tmp_path, manifest):
    """Exercise the frozen argv against an existing source fixture, no producer stubs."""
    from tests.test_atlas_db import _manifest

    source = _manifest(tmp_path)
    aliases = tmp_path / "aliases.yaml"
    aliases.write_text("aliases: []\n")
    output = tmp_path / "outputs"
    output.mkdir()
    reports, code = c.run_commands(
        manifest["components"]["atlas-data"]["build"], c.ROOT, output,
        {"lexicon-manifest": source, "curated-aliases": aliases},
    )
    assert code == 0 and len(reports) == 3
    with sqlite3.connect(f"file:{output / 'atlas.db'}?mode=ro", uri=True) as connection:
        assert connection.execute("SELECT count(*) FROM articles").fetchone()[0] == 3
    search = json.loads((output / "search.json").read_text())
    assert isinstance(search, list) and len(search) == 3
    assert (output / "browse-meta.json").is_file()
    assert (output / "daily.json").is_file()


def test_build_refuses_inputs_before_creating_output(tmp_path, monkeypatch, capsys):
    invalid = tmp_path / "invalid-inputs.json"
    invalid.write_text('{}\n')
    output = tmp_path / "output"
    assert c.main(["build", "--component", "atlas-data", "--inputs", str(invalid), "--output-dir", str(output)]) == 2
    assert not output.exists()
    assert json.loads(capsys.readouterr().out)["result"] == "error"


def test_inventory_collection_and_identities_and_nul_paths(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(c, "current_identities", lambda *a: {"source": "structural-fixture"})
    monkeypatch.setattr(c, "collect_tests", lambda *a: (["tests/test_fixture.py::test_one"], 0))
    assert c.main(["inventory", "--component", "atlas-data", "--collect", "--identities"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["identities"]["source"] == "structural-fixture"
    assert report["test_ids"] == ["tests/test_fixture.py::test_one"]
    paths = tmp_path / "changed.z"
    paths.write_bytes(b"scripts/config.py\0new-root/weird\nname.ts\0")
    assert c.main(["affected", "--paths-file", str(paths)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["changed_paths"] == 2 and set(report["components"]) == set(c.NODE_IDS)


def test_cli_inventory_affected_and_error_are_structural(monkeypatch, capsys, manifest):
    assert c.main(["list"]) == 0
    assert set(json.loads(capsys.readouterr().out)["components"]) == set(c.NODE_IDS)
    assert c.main(["affected", "never-classified/new.txt"]) == 0
    assert set(json.loads(capsys.readouterr().out)["components"]) == set(c.NODE_IDS)
    monkeypatch.setattr(c, "inventory", lambda m: {"unassigned": 1, "ambiguous": 0, "dynamic_unresolved": 0,
                                                  "unmapped_test_files": 0, "selector_parity_gaps": 0})
    assert c.main(["inventory", "--check"]) == 1
    capsys.readouterr()
    assert c.main(["inventory", "--collect"]) == 2
    assert "invalid_or_unavailable" in capsys.readouterr().out
    monkeypatch.setattr(c, "collect_tests", lambda *a: ([], 2))
    assert c.main(["test", "--component", "atlas-data"]) == 2
    assert json.loads(capsys.readouterr().out)["fallback_reason"] == "collection-error"


def test_cli_command_dispatch_and_no_artifact_certification(monkeypatch, capsys):
    monkeypatch.setattr(c, "collect_tests", lambda *a: (["tests/test_fixture.py::test_fixture"], 0))
    monkeypatch.setattr(c, "run_commands", lambda *a: ([{"result": "pass"}], 0))
    assert c.main(["test", "--component", "atlas-data"]) == 0
    assert json.loads(capsys.readouterr().out)["commands"][0]["result"] == "pass"
    assert c.main(["verify", "--component", "atlas-data"]) == 0
    assert json.loads(capsys.readouterr().out)["artifact_certification"].startswith("not_certified")


def test_cli_help_and_required_build_arguments(capsys):
    for operation in ([], ["build"], ["test"], ["verify"]):
        with pytest.raises(SystemExit) as exit_info:
            c.parser().parse_args([*operation, "--help"])
        assert exit_info.value.code == 0
        help_text = capsys.readouterr().out
        assert all(label in help_text for label in ["Outputs:", "Exit codes:", "Related:", "Examples:"])
    with pytest.raises(SystemExit) as exit_info:
        c.parser().parse_args(["build", "--component", "atlas-data"])
    assert exit_info.value.code == 2


def test_known_failures_are_owned_and_never_verify_commands(manifest):
    residuals = {r["id"]: r for r in manifest["residual_commands"]}
    assert residuals["legacy-atlas-make"]["owner_slice"] == 3
    assert residuals["non-arc-landing"]["owner_slice"] == 4
    assert residuals["open-model-data-tier"]["owner_slice"] == 5
    commands = [v["argv"] for node in manifest["components"].values() for v in node["verify"]]
    assert residuals["legacy-atlas-make"]["argv"] not in commands
    assert residuals["non-arc-landing"]["argv"] not in commands
    assert residuals["open-model-data-tier"]["argv"] not in commands
    for frontend in manifest["selector_contracts"]["frontend_components"]:
        argv = manifest["components"][frontend]["build"][0]["argv"]
        assert argv[:3] == ["npm", "run", "build:shell"]
        assert "hydrate" not in " ".join(argv)
