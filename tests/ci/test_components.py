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
    result = c.affected(["scripts/projects/open_model_data/view.py"], manifest)
    assert set(result["components"]) == set(c.NODE_IDS)
    assert result["unresolved_edges"] > 0


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


def test_test_prefixes_expand_index_and_sparse_census_is_complete(repo, manifest):
    manifest["shared_integration_tests"] = []
    manifest["components"]["harness"]["test_files"] = []
    manifest["components"]["harness"]["test_prefixes"] = ["tests/"]
    assert c.test_files("harness", manifest, repo) == ["tests/test_fixture.py"]
    (repo / "tests/test_fixture.py").unlink()
    assert c.test_files("harness", manifest, repo) == ["tests/test_fixture.py"]


def test_ast_closure_relative_bare_literal_loads_and_nonliteral():
    sources = {
        "scripts/lexicon/source.py": b"X = 1\n",
        "scripts/lexicon/relative.py": b"from . import source\n",
        "scripts/build/consumer.py": b"from lexicon import relative\n",
        "scripts/audit/loader.py": b'''from pathlib import Path
import importlib.util as util
ROOT = Path(__file__).resolve().parents[2]
def load(name, path):
    return util.spec_from_file_location(name, path)
load('source', ROOT / 'scripts' / 'lexicon' / 'source.py')
''',
        "tests/test_use.py": b"import scripts.build.consumer\n",
        "tests/test_dynamic.py": b"from importlib import import_module as load\nload(target)\n",
    }
    graph = c.scan_imports(sources)
    assert ("scripts/lexicon/relative.py", "scripts/lexicon/source.py") in graph["file_edges"]
    assert ("scripts/build/consumer.py", "scripts/lexicon/relative.py") in graph["file_edges"]
    assert ("scripts/audit/loader.py", "scripts/lexicon/source.py") in graph["file_edges"]
    assert any(e["path"] == "tests/test_dynamic.py" for e in graph["unresolved_edges"])


def test_indexed_imports_survive_sparse_checkout_and_invalidate_on_edits(repo, manifest):
    path = repo / "scripts/config.py"
    path.write_text("from scripts.ci import components\n")
    git(repo, "add", "scripts/config.py")
    git(repo, "update-index", "--skip-worktree", "scripts/config.py")
    path.unlink()
    assert ("scripts/config.py", "scripts/ci/components.py") in c.import_graph(manifest, repo)["file_edges"]
    path.write_text("import importlib\nimportlib.import_module(target)\n")
    git(repo, "update-index", "--no-skip-worktree", "scripts/config.py")
    assert any(e["path"] == "scripts/config.py" for e in c.import_graph(manifest, repo)["unresolved_edges"])


def test_complete_node_test_set_ownership_importers_and_integration(repo, manifest):
    manifest["shared_integration_tests"] = ["tests/test_fixture.py"]
    manifest["components"]["atlas-data"]["test_files"] = []
    for path, source in {
        "scripts/lexicon/source.py": "VALUE = 1\n",
        "scripts/build/consumer.py": "from scripts.lexicon.source import VALUE\n",
        "tests/test_source.py": "from scripts.build.consumer import VALUE\n",
        "tests/test_other.py": "VALUE = 2\n",
        "tests/test_mapped.py": "VALUE = 3\n",
    }.items():
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source)
    manifest["exact_paths"]["tests/test_mapped.py"] = ["atlas-data"]
    git(repo, "add", ".")
    assert c.test_files("atlas-data", manifest, repo) == [
        "tests/test_fixture.py", "tests/test_mapped.py", "tests/test_source.py"]


def test_unresolved_and_missing_mandatory_edges_force_all(manifest):
    graph = {"node_edges": [], "file_edges": [], "unresolved_edges": [], "missing_mandatory_edges": ["lost"]}
    assert set(c.affected(["scripts/lexicon/source.py"], manifest, graph)["components"]) == set(c.NODE_IDS)
    graph["missing_mandatory_edges"] = []
    graph["unresolved_edges"] = [{"path": "scripts/loader.py"}]
    assert c.affected(["site/new.ts"], manifest, graph)["fallback_reasons"] == ["dynamic-unresolved"]


@pytest.mark.parametrize(("producer", "consumer"), [
    ("harness", "curriculum-generation"), ("curriculum-generation", "harness"), ("harness", "atlas-data"),
])
def test_review_probes_computed_even_without_unresolved_fallback(manifest, producer, consumer):
    graph = c.import_graph(manifest)
    assert (producer, consumer) in graph["node_edges"]
    graph = graph | {"unresolved_edges": [], "missing_mandatory_edges": []}
    probes = {"harness": "scripts/agent_runtime/runner.py", "curriculum-generation": "scripts/build/fresh/assemble.py"}
    assert consumer in c.affected([probes[producer]], manifest, graph)["components"]


def test_vitest_files_follow_ownership_and_existing_scripts(repo, manifest):
    path = repo / "site/tests/unit/shared.test.ts"
    path.parent.mkdir(parents=True)
    path.write_text("// test\n")
    git(repo, "add", ".")
    for node in manifest["selector_contracts"]["frontend_components"]:
        files = c.vitest_files(node, manifest, repo)
        assert files == ["site/tests/unit/shared.test.ts"]
        commands = c.node_test_commands(node, manifest, ["tests/test_fixture.py"], files)
        assert commands[1]["argv"] == ["npm", "run", "test:unit", "--", "tests/unit/shared.test.ts"]
    built = manifest["vitest"]["built_output_files"]
    assert c.node_test_commands("atlas-frontend", manifest, [], built)[1]["argv"][:3] == ["npm", "run", "test:built-output"]


def test_list_reports_resolved_sets_without_running(monkeypatch, capsys):
    monkeypatch.setattr(c, "test_files", lambda *a: ["tests/test_one.py", "tests/test_two.py"])
    monkeypatch.setattr(c, "vitest_files", lambda *a: ["site/tests/unit/shared.test.ts"])
    monkeypatch.setattr(c, "collect_tests", lambda *a: pytest.fail("list must not collect"))
    assert c.main(["test", "--component", "atlas-frontend", "--list"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["test_file_count"] == 3 and result["pytest_file_count"] == 2 and result["vitest_file_count"] == 1


def test_literal_targets_and_parse_errors_are_conservative():
    assert c.literal_target(c.ast.parse("Path(__file__).parent / 'x.py'", mode="eval").body, {}, "scripts/load.py") == c.PurePosixPath("scripts/x.py")
    graph = c.scan_imports({"scripts/broken.py": b"def invalid(\n"})
    assert graph["unresolved_edges"][0]["reason"] == "parse-error"


def test_vitest_collection_uses_installed_cli_and_keeps_failures(monkeypatch):
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, '[{"file":"shared.test.ts","name":"renders"}]')
    monkeypatch.setattr(c.subprocess, "run", run)
    rows, code = c.collect_vitest(["site/tests/unit/shared.test.ts"])
    assert code == 0 and rows[0]["name"] == "renders"
    assert calls[0][0][-1] == "tests/unit/shared.test.ts"
    assert calls[0][1]["env"]["npm_config_offline"] == "true"
    assert c.collect_vitest([]) == ([], 0)
    monkeypatch.setattr(c.subprocess, "run", lambda argv, **kw: subprocess.CompletedProcess(argv, 2, ""))
    assert c.collect_vitest(["site/tests/unit/shared.test.ts"])[1] == 2


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
    reports, code = c.run_commands([command, command], repo, None, {}, keep_going=True)
    assert code == 1 and len(reports) == 2


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
    monkeypatch.setattr(c, "run_commands", lambda *a, **kw: ([{"result": "pass"}], 0))
    assert c.main(["test", "--component", "atlas-data"]) == 0
    assert json.loads(capsys.readouterr().out)["commands"][0]["result"] == "pass"
    assert c.main(["verify", "--component", "atlas-data"]) == 0
    assert json.loads(capsys.readouterr().out)["artifact_certification"].startswith("not_certified")


def test_cli_help_and_required_build_arguments(capsys):
    for operation in ([], ["build"], ["test"], ["verify"], ["junit"]):
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


def test_imported_parent_initializers_relative_missing_and_keyword_loads():
    sources = {
        "scripts/__init__.py": b"",
        "scripts/lexicon/__init__.py": b"from . import source\n",
        "scripts/lexicon/source.py": b"X = 1\n",
        "scripts/lexicon/consumer.py": b"from .missing import X\nfrom lexicon.absent import Y\n",
        "tests/test_use.py": b"import scripts.lexicon.source\n",
        "tests/test_load.py": b"from importlib.util import spec_from_file_location as load\nload(name='x', location='scripts/lexicon/source.py')\n",
    }
    graph = c.scan_imports(sources)
    assert ("scripts/lexicon/__init__.py", "scripts/lexicon/source.py") in graph["file_edges"]
    assert ("tests/test_use.py", "scripts/lexicon/__init__.py") in graph["file_edges"]
    assert ("tests/test_use.py", "scripts/__init__.py") in graph["file_edges"]
    assert ("tests/test_load.py", "scripts/lexicon/source.py") in graph["file_edges"]
    assert graph["unresolved_edges"] == [
        {"path": "scripts/lexicon/consumer.py", "line": line, "reason": "missing-local-import"}
        for line in (1, 2)
    ]


def test_call_name_only_reads_dotted_names():
    assert c.call_name(c.ast.parse("util.spec_from_file_location", mode="eval").body) == "util.spec_from_file_location"
    assert c.call_name(c.ast.parse("factory().loader", mode="eval").body) == ""


def test_skips_never_hide_a_failed_command(repo, monkeypatch):
    monkeypatch.setattr(c, "project_interpreter", lambda root: Path(sys.executable))
    (repo / "tests/test_fixture.py").write_text(
        "import pytest\ndef test_skip():\n    pytest.skip('artifact absent')\ndef test_fail():\n    assert False\n"
    )
    command = {"argv": ["{python}", "-m", "pytest", "-q", "tests/test_fixture.py"], "cwd": ".", "scope": "code-contract"}
    reports, code = c.run_commands([command], repo, None, {})
    assert code == 1 and reports[0]["skipped"] == 1 and reports[0]["result"] == "fail"


def test_unknown_loads_and_their_importers_are_in_every_node_set(repo, manifest):
    manifest["shared_integration_tests"] = []
    manifest["components"]["atlas-data"]["test_files"] = []
    for path, text in {
        "scripts/build/unknown_loader.py": "import importlib\nimportlib.import_module(target)\n",
        "tests/test_indirect_load.py": "from scripts.build import unknown_loader\n",
        "tests/test_direct_load.py": "import importlib\nimportlib.import_module(target)\n",
        "tests/test_unrelated.py": "X = 1\n",
    }.items():
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    git(repo, "add", ".")
    assert c.test_files("atlas-data", manifest, repo) == ["tests/test_direct_load.py", "tests/test_indirect_load.py"]
    report = c.inventory(manifest, repo)
    assert report["dynamic_unresolved"] == report["unresolved_import_edges"] == 2


def test_resolved_test_sets_do_not_freeze_to_manifest_samples(manifest):
    graph = c.import_graph(manifest)
    paths = c.tracked_paths()
    for node in c.NODE_IDS:
        resolved = set(c.test_files(node, manifest))
        mapped = {path for path in paths if path.startswith("tests/")
                  and Path(path).name.startswith("test_") and path.endswith(".py")
                  and node in c.assign_path(path, manifest)[0]}
        assert mapped <= resolved
        assert set(manifest["shared_integration_tests"]) <= resolved
    # Check the review's atlas-data -> harness direction without the fallback.
    assert ("atlas-data", "harness") in graph["node_edges"]
    graph = graph | {"unresolved_edges": [], "missing_mandatory_edges": []}
    assert "harness" in c.affected(["scripts/lexicon/runner/atlas_job.py"], manifest, graph)["components"]


def test_frontend_build_declares_shared_astro_scope(tmp_path, monkeypatch, capsys, manifest):
    monkeypatch.setattr(c, "verify_inputs", lambda *args: {})
    monkeypatch.setattr(c, "run_commands", lambda *args, **kw: ([{"result": "pass"}], 0))
    for node in manifest["selector_contracts"]["frontend_components"]:
        assert c.main(["build", "--component", node, "--inputs", str(tmp_path / "inputs.json"),
                       "--output-dir", str(tmp_path / node)]) == 0
        report = json.loads(capsys.readouterr().out)
        assert report["build_scope"] == "shared-astro"
        assert report["input_bytes_verified"] is True
        assert report["artifact_certification"].startswith("not_certified")
    residual = next(r for r in manifest["residual_commands"] if r["id"] == "open-model-prepared-build-inputs")
    assert residual["status"] == "artifact-dependent" and residual["owner_slice"] == 5


def test_complete_node_commands_have_bounded_parallel_execution(monkeypatch, manifest, tmp_path):
    command = c.node_test_commands("harness", manifest, ["tests/test_fixture.py"], [])[0]
    assert command["argv"][2:7] == ["pytest", "-q", "-n", "2", "tests/test_fixture.py"]
    calls = []
    monkeypatch.setattr(c, "project_interpreter", lambda root: Path(sys.executable))
    def run(argv, **kw):
        calls.append(kw)
        return subprocess.CompletedProcess(argv, 0, "tests/test_fixture.py::test_fixture\n")
    monkeypatch.setattr(c.subprocess, "run", run)
    assert c.collect_tests(["tests/test_fixture.py"], [], tmp_path)[1] == 0
    assert calls[-1]["timeout"] == 900
    monkeypatch.setattr(c, "execute_command", lambda argv, **kw: (calls.append(kw) or 0, False))
    assert c.run_commands([command], tmp_path, None, {})[1] == 0
    assert calls[-1]["timeout"] is None
    assert c.run_commands([command | {"scope": "code-contract", "timeout": 1800}], tmp_path, None, {})[1] == 0
    assert calls[-1]["timeout"] == 1800


@pytest.mark.parametrize('gap', ['unassigned', 'ambiguous', 'unmapped_test_files', 'selector_parity_gaps', 'missing_mandatory_edges'])
def test_inventory_check_allows_unknown_imports_but_rejects_contract_gaps(monkeypatch, capsys, gap):
    report = dict.fromkeys(('unassigned', 'ambiguous', 'unmapped_test_files', 'selector_parity_gaps'), 0)
    report.update(dynamic_unresolved=239, import_graph={'missing_mandatory_edges': []})
    monkeypatch.setattr(c, 'inventory', lambda m: report)
    assert c.main(['inventory', '--check']) == 0
    assert json.loads(capsys.readouterr().out)['dynamic_unresolved'] == 239
    if gap == 'missing_mandatory_edges':
        report['import_graph'][gap] = ['required-edge']
    else:
        report[gap] = 1
    assert c.main(['inventory', '--check']) == 1


def test_open_model_subprocess_test_prefix_is_owned(manifest):
    path = 'tests/projects/open_model_data/test_direct_cli_help.py'
    assert c.assign_path(path, manifest) == (['open-model-data', 'shared-core'], 'prefix')
    assert path in c.test_files('open-model-data', manifest)


def test_test_cli_forwards_workers_and_timeout(monkeypatch, capsys):
    monkeypatch.setattr(c, 'test_files', lambda *a: ['tests/test_fixture.py'])
    monkeypatch.setattr(c, 'vitest_files', lambda *a: [])
    monkeypatch.setattr(c, 'collect_tests', lambda *a: (['tests/test_fixture.py::test_fixture'], 0))
    commands = []
    def run(rows, *a, **kw):
        commands.extend(rows)
        return [], 0
    monkeypatch.setattr(c, 'run_commands', run)
    assert c.main(['test', '--component', 'harness', '--workers', '1', '--timeout', '4']) == 0
    assert commands[0]['argv'][4:6] == ['-n', '1']
    assert commands[0]['timeout'] == 4
    capsys.readouterr()
    for args in (['--workers', '0'], ['--timeout', '0'], ['--timeout', 'nan']):
        assert c.main(['test', '--component', 'harness', *args]) == 2
        capsys.readouterr()


def test_journal_counts_phases_and_ignores_worker_duplicates(tmp_path, monkeypatch):
    from types import SimpleNamespace
    path = tmp_path / 'results.jsonl'
    monkeypatch.setenv('LU_COMPONENT_TEST_JOURNAL', str(path))
    monkeypatch.delenv('PYTEST_XDIST_WORKER', raising=False)
    c.pytest_runtest_logreport(SimpleNamespace(nodeid='pass', when='setup', outcome='passed'))
    c.pytest_runtest_logreport(SimpleNamespace(nodeid='pass', when='call', outcome='passed'))
    c.pytest_runtest_logreport(SimpleNamespace(nodeid='error', when='call', outcome='passed'))
    c.pytest_runtest_logreport(SimpleNamespace(nodeid='error', when='teardown', outcome='failed'))
    c.pytest_runtest_logreport(SimpleNamespace(nodeid='skip', when='setup', outcome='skipped'))
    monkeypatch.setenv('PYTEST_XDIST_WORKER', 'gw0')
    c.pytest_runtest_logreport(SimpleNamespace(nodeid='ignored', when='call', outcome='passed'))
    assert c.partial_test_results(path) == {'passed': 1, 'failed': 1, 'skipped': 1, 'failing_test_ids': ['error']}
    assert c.partial_test_results(tmp_path / 'missing')['passed'] == 0
    path.write_text(json.dumps({'id': 'unicode\u2028inside', 'when': 'call', 'outcome': 'failed'}, ensure_ascii=False) + '\n')
    assert c.partial_test_results(path)['failing_test_ids'] == ['unicode\u2028inside']


def test_timeout_retains_real_completed_pytest_results(tmp_path, monkeypatch):
    monkeypatch.setattr(c, 'project_interpreter', lambda root: Path(sys.executable))
    monkeypatch.delenv('PYTEST_XDIST_WORKER', raising=False)
    path = tmp_path / 'test_partial.py'
    path.write_text('import time\ndef test_pass():\n    assert True\ndef test_fail():\n    assert False\ndef test_wait():\n    time.sleep(60)\n')
    command = {'argv': ['{python}', '-m', 'pytest', '-q', str(path)], 'cwd': '.',
               'scope': 'complete-node-pytest', 'timeout': 15}
    reports, code = c.run_commands([command], c.ROOT, None, {})
    assert code == 124 and reports[0]['result'] == 'timeout'
    assert reports[0]['partial_results'] is True
    assert reports[0]['passed'] == reports[0]['failed'] == 1
    assert reports[0]['failing_test_ids'] == ['test_partial.py::test_fail']


def test_junit_coverage_fresh_sets_failures_skips_absence_and_duplicate_precedence(repo, manifest, monkeypatch):
    git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '-m', 'fixture\n\nX-Agent: codex/impl-9884-d')
    path = repo / 'full.xml'
    path.write_text('''<testsuites><testsuite>
      <testcase classname="tests.test_fixture" name="test_ok[dot.value]"/>
      <testcase classname="tests.test_fixture.OtherClass" name="test_fail"><failure/></testcase>
      <testcase classname="tests.test_fixture" name="test_skip"><skipped/></testcase>
      </testsuite></testsuites>''')
    duplicate = repo / 'duplicate.xml'
    duplicate.write_text('<testsuite><testcase classname="tests.test_fixture.OtherClass" name="test_fail"/></testsuite>')
    ids = ['tests/test_fixture.py::test_ok[dot.value]', 'tests/test_fixture.py::OtherClass::test_fail',
           'tests/test_fixture.py::test_skip', 'tests/test_fixture.py::test_absent', 'tests/test_other.py::test_other']
    monkeypatch.setattr(c, 'test_files', lambda *a: ['tests/test_fixture.py'])
    calls = []
    def collect(files, args, root):
        calls.append((files, args))
        return ids, 0
    monkeypatch.setattr(c, 'collect_tests', collect)
    report, code = c.junit_coverage([path, duplicate], manifest, ['atlas-data', 'harness'], repo)
    assert len(calls) == 1
    for row in report['nodes'].values():
        assert {key: row[key] for key in ('collected', 'passed', 'failed', 'skipped', 'absent')} == {
            'collected': 4, 'passed': 1, 'failed': 1, 'skipped': 1, 'absent': 1}
        assert row['failing_test_ids'] == [ids[1]] and row['absent_test_ids'] == [ids[3]]
    assert code == 1
    assert report['junit_inputs'][0]['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(c, 'collect_tests', lambda *a: ([ids[0]], 0))
    assert c.junit_coverage([path], manifest, ['harness'], repo)[1] == 0
    monkeypatch.setattr(c, 'collect_tests', lambda *a: ([], 2))
    report, code = c.junit_coverage([path], manifest, ['harness'], repo)
    assert code == 2 and report['fallback_reason'] == 'collection-error'
    with pytest.raises(ValueError):
        c.junit_coverage([], manifest, ['harness'], repo)
    path.write_text('<testsuite><testcase name="tests.test_fixture"><skipped/></testcase></testsuite>')
    monkeypatch.setattr(c, 'collect_tests', lambda *a: ([ids[0]], 0))
    report, code = c.junit_coverage([path], manifest, ['harness'], repo)
    assert code == 1
    assert report['nodes']['harness']['module_results'] == {'tests/test_fixture.py': 'skipped'}
    assert report['nodes']['harness']['absent'] == 1
    path.write_text('<testsuite/>')
    with pytest.raises(ValueError):
        c.junit_coverage([path], manifest, ['harness'], repo)


def test_junit_cli_dispatch(monkeypatch, tmp_path, capsys):
    calls = []
    def coverage(paths, manifest, components):
        calls.append((paths, components))
        return {'nodes': {}}, 0
    monkeypatch.setattr(c, 'junit_coverage', coverage)
    assert c.main(['junit', '--junit', str(tmp_path / 'full.xml')]) == 0
    assert calls[-1][1] == c.NODE_IDS
    assert c.main(['junit', '--component', 'harness', '--junit', str(tmp_path / 'full.xml')]) == 0
    assert calls[-1][1] == ['harness']


@pytest.mark.parametrize("source,target", [
    ('from pathlib import Path\nPath("schemas/input.json").read_text()', "schemas/input.json"),
    ('open("schemas/input.json")', "schemas/input.json"),
    ('import io\nio.open("schemas/input.json")', "schemas/input.json"),
    ('import builtins\nbuiltins.open(file="schemas/input.json")', "schemas/input.json"),
    ('import subprocess, sys\nsubprocess.run([sys.executable, "scripts/config.py"])', "scripts/config.py"),
    ('from subprocess import run as go\ngo(["python3", "-m", "scripts.config"])', "scripts/config.py"),
])
def test_runtime_literal_file_and_subprocess_edges(source, target):
    graph = c.scan_imports({"tests/test_reader.py": source.encode(), "scripts/config.py": b"VALUE = 1"},
                           {"tests/test_reader.py", "scripts/config.py", "schemas/input.json"})
    assert ("tests/test_reader.py", target) in graph["file_edges"]
    assert not graph["unresolved_edges"]


@pytest.mark.parametrize("source,reason", [
    ('open(variable)', "unresolved-file-read"),
    ('Path(variable).read_bytes()', "unresolved-file-read"),
    ('from pathlib import Path\nPath("missing.json").open()', "unresolved-file-read"),
    ('import sys as system\nsystem.path.insert(0, "scripts")', "sys-path"),
    ('import sys\nsys.path = ["scripts"]', "sys-path"),
    ('from sys import path as paths\npaths[:] = ["scripts"]', "sys-path"),
    ('import subprocess\nsubprocess.run(command)', "unresolved-subprocess"),
    ('import subprocess\nsubprocess.run(["python3", "scripts/config.py", argument])', "unresolved-subprocess"),
    ('import subprocess\nsubprocess.run(["python3", "scripts/config.py"], shell=True)', "unresolved-subprocess"),
    ('import os\nos.system("echo hello")', "unresolved-subprocess"),
])
def test_unresolved_runtime_edges_force_full_selection(manifest, source, reason):
    graph = c.scan_imports({"scripts/projects/open_model_data/reader.py": source.encode()})
    assert any(edge["reason"] == reason for edge in graph["unresolved_edges"])
    graph |= {"node_edges": [], "missing_mandatory_edges": []}
    assert set(c.affected(["scripts/projects/open_model_data/reader.py"], manifest, graph)["components"]) == set(c.NODE_IDS)


def test_literal_file_read_importer_in_resolved_test_set(repo, manifest):
    schema = repo / "site/schemas/input.json"
    schema.parent.mkdir(parents=True)
    schema.write_text("{}")
    reader = repo / "tests/test_schema_reader.py"
    reader.write_text('from pathlib import Path\nPath("site/schemas/input.json").read_text()\n')
    git(repo, "add", ".")
    assert "tests/test_schema_reader.py" in c.test_files("atlas-frontend", manifest, repo)
