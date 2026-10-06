import ast
import copy
import json
import pkgutil
import sqlite3
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from scripts.common.jsonl import jsonl_lines
from scripts.projects.open_model_data import review_build as framework
from scripts.projects.open_model_data.review_build import __main__ as cli
from scripts.projects.open_model_data.review_build import output
from scripts.projects.open_model_data.review_build.attribution import Attribution, Resolver, SyntheticAdapter
from scripts.projects.open_model_data.review_build.build import _jsonl, execute
from scripts.projects.open_model_data.review_build.contract import canonical, digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.manifest import private_manifest
from scripts.projects.open_model_data.review_build.output import OutputGuard
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import run_gate, save_bundle, synthetic_components


@pytest.fixture(autouse=True)
def synthetic_mount(monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")


@pytest.fixture(autouse=True)
def cli_test_component(bundle, monkeypatch):
    from scripts.projects.open_model_data.review_build import components

    monkeypatch.setattr(cli, "REGISTRY", {"C1": "c1"})
    monkeypatch.setattr(
        cli,
        "load_components",
        lambda ids, **kwargs: components.load_components(ids, _test_overrides=synthetic_components(bundle)),
    )


def test_build_verify_determinism_and_tamper_refusal(bundle):
    results = []
    dirs = [bundle["root"] / name for name in ("SYNTHETIC-one", "SYNTHETIC-two")]
    for path in dirs:
        with OutputGuard(path) as guard:
            result = execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle))
            assert (
                execute(
                    bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle), verify=True
                )["status"]
                == "verified"
            )
            results.append(result)
    assert results[0] == results[1]
    first = {p.relative_to(dirs[0]): p.read_bytes() for p in dirs[0].rglob("*") if p.is_file()}
    second = {p.relative_to(dirs[1]): p.read_bytes() for p in dirs[1].rglob("*") if p.is_file()}
    assert first == second
    manifest = json.loads(first[Path("manifest.json")])
    assert manifest["pins"]["catalog"] == digest((bundle["root"] / "catalog.yaml").read_bytes())
    assert len(manifest["pins"]["code"]["code_sha"]) == 40
    assert manifest["accounting"]["C1"]["accepted"] == 12
    assert all(digest(first[Path(name)]) == sha for name, sha in manifest["files"].items())
    with OutputGuard(dirs[0]) as guard:
        guard.write("C1/records.jsonl", b"SYNTHETIC forged artifact\n")
        with pytest.raises(BuildError, match="artifact_mismatch"):
            execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle), verify=True)
    for path in dirs:
        assert all(p.stat().st_mode & 0o777 == (0o700 if p.is_dir() else 0o600) for p in path.rglob("*"))


@pytest.mark.parametrize("separator", ["\u2028", "\u2029", "\u0085"])
def test_unicode_separators_round_trip_write_read_verify(bundle, separator):
    candidate = bundle["candidates"][0]
    value = candidate.slots[0]
    text = value.text + separator + "SYNTHETIC continuation"
    citation = replace(value.citations[0], field_sha256=digest(text.encode("utf-8")))
    bundle["candidates"][0] = replace(candidate, slots=(replace(value, text=text, citations=(citation,)),))
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("UPDATE units SET source_field=? WHERE id=1", (text,))
    raw = _jsonl([asdict(c) for c in bundle["candidates"]])
    assert separator.encode("utf-8") in raw
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle))
        emitted = guard.read("C1/records.jsonl")
        assert separator.encode("utf-8") in emitted
        records = [json.loads(line) for line in jsonl_lines(emitted.decode("utf-8")) if line.strip()]
        assert len(records) == len(bundle["candidates"])
        assert [v["text"] for r in records for v in r["values"] if v["slot"] == "sentence"].count(text) == 1
        assert (
            execute(
                bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle), verify=True
            )["status"]
            == "verified"
        )


@pytest.mark.parametrize(
    "form", ["SYNTHETIC <edition> source", "SYNTHETIC cite the book title per source", "SYNTHETIC insert metadata"]
)
def test_unresolved_attribution_fails_gate_and_withholds_source_records(bundle, form):
    bundle["register"]["sources"][0]["citation"]["form"] = form
    with pytest.raises(BuildError, match="attribution_unresolved"):
        run_gate(bundle)
    save_bundle(bundle)
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle))
        manifest = json.loads(guard.read("manifest.json"))
        assert manifest["accounting"]["C1"]["accepted"] == 0
        assert manifest["accounting"]["C1"]["withheld"] == 12
        assert guard.read("C1/records.jsonl") == b""
        assert manifest["metrics"]["C1.sentence_correction"]["status"] == "missing_coverage"
        assert b"not training-ready" in guard.read("README.md")


def test_adapter_requires_mapping_and_register_licence(bundle):
    c = bundle["candidates"][0].slots[0].citations[0]

    class IncompleteAdapter:
        def resolve(self, form, citation, row, reader):
            return Attribution("SYNTHETIC invented bibliography", "SYNTHETIC unmapped form")

    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        for adapters in ({}, {"synthetic": IncompleteAdapter()}):
            with pytest.raises(BuildError, match="attribution_unresolved"):
                Resolver(bundle["register"], adapters).resolve(c, reader)
        entry = copy.deepcopy(bundle["register"])
        del entry["sources"][0]["terms"]["licence"]["name"]
        with pytest.raises(BuildError, match="attribution_unresolved"):
            Resolver(entry, {"synthetic": SyntheticAdapter()}).resolve(c, reader)
        with pytest.raises(BuildError, match="locator_unavailable"):
            Resolver(bundle["register"], {"synthetic": SyntheticAdapter()}).resolve(replace(c, locator=""), reader)
        with pytest.raises(BuildError, match="attribution_unresolved"):
            SyntheticAdapter().resolve("UNMARKED form", c, {}, reader)
    with pytest.raises(BuildError, match="register_duplicate"):
        Resolver({"sources": bundle["register"]["sources"] * 2}, {})


def test_cli_help_build_verify_and_usage_privacy(bundle, capsys):
    with pytest.raises(SystemExit) as help_exit:
        cli.main(["--help"])
    assert help_exit.value.code == 0
    help_text = capsys.readouterr().out
    assert all(text in help_text for text in ("Examples:", "Outputs:", "Exit codes:", "Related:", "build", "verify"))
    for sub in ("build", "verify"):
        with pytest.raises(SystemExit):
            cli.main([sub, "--help"])
        assert "--out" in capsys.readouterr().out
    out = bundle["root"] / "SYNTHETIC-out"
    args = ["--config", str(bundle["root"] / "request.json"), "--out", str(out)]
    assert cli.main(["build", *args]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "built"
    assert str(out) not in canonical(result).decode()
    assert cli.main(["verify", *args]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "verified"
    assert cli.main(["SYNTHETIC PRIVATE INPUT"]) == 2
    message = capsys.readouterr()
    assert "SYNTHETIC PRIVATE INPUT" not in message.out + message.err
    assert json.loads(message.err)["error"] == "cli_usage"


def test_cli_error_text_only_goes_to_guarded_logs(bundle, capsys, monkeypatch):
    def failure(*args, **kwargs):
        raise ValueError("SYNTHETIC PRIVATE SOURCE TEXT")

    monkeypatch.setattr(cli, "execute", failure)
    out = bundle["root"] / "SYNTHETIC-out"
    assert cli.main(["build", "--config", str(bundle["root"] / "request.json"), "--out", str(out)]) == 1
    message = capsys.readouterr()
    assert "SYNTHETIC PRIVATE SOURCE TEXT" not in message.out + message.err
    assert str(out) not in message.out + message.err
    assert b"SYNTHETIC PRIVATE SOURCE TEXT" in (out / "logs/failure.txt").read_bytes()
    assert (out / "logs/failure.txt").stat().st_mode & 0o777 == 0o600
    error = BuildError("bad", record_id="0" * 64, component="C1", row_key="SYNTHETIC private headword")
    safe = error.diagnostic()
    assert safe["row_key"] == digest(b"SYNTHETIC private headword")
    assert "SYNTHETIC" not in canonical(safe).decode()
    assert BuildError("SYNTHETIC unsafe", component="SYNTHETIC").diagnostic()["error"] == "build_failure"


def test_output_refused_before_input_read(bundle, capsys, monkeypatch):
    touched = []
    monkeypatch.setattr(cli, "execute", lambda *a, **kw: touched.append(True))
    out = bundle["root"] / "SYNTHETIC-repo"
    out.mkdir()
    (out / ".git").mkdir()
    assert cli.main(["build", "--config", "SYNTHETIC-secret-file", "--out", str(out)]) == 1
    assert not touched
    assert not (out / "logs").exists()
    assert json.loads(capsys.readouterr().err)["error"] == "repository_output"


def test_private_manifest_allowlist_and_string_refusals(bundle):
    data = {
        "hashes": {"build": "a" * 64},
        "counts": {"C1.counted": 12},
        "versions": {"record": "omd-review-record.v1", "catalog": "1.0.0", "framework": "1.0.0"},
        "code_sha": "b" * 40,
        "reason_code_tallies": {"ok": 12},
    }
    assert private_manifest(data) == data
    cases = [
        dict(data, locator="SYNTHETIC"),
        dict(data, hashes={"text": "a" * 64}),
        dict(data, versions={"catalog": "SYNTHETIC \u0410"}),
        dict(data, counts={"SYNTHETIC": 1}),
        dict(data, reason_code_tallies={"SYNTHETIC private": 1}),
        dict(data, hashes={"build": "SYNTHETIC"}),
        dict(data, code_sha="SYNTHETIC"),
    ]
    for bad in cases:
        with pytest.raises(BuildError):
            private_manifest(bad)


@pytest.mark.parametrize(
    "version,valid",
    [
        ("0.5.0-rb1", True),
        ("0.5.0-rb1.2", True),
        ("1.0.0", True),
        ("0.5.0-", False),
        ("0.5.0-rb1-", False),
        ("0.5.0-rb1.", False),
        ("0.5.0-.rb1", False),
        ("0.5.0-rb1..2", False),
        ("0.5.0-rb-1", False),
        ("0.5.0-RB1", False),
    ],
)
def test_private_manifest_version_suffix(version, valid):
    data = {
        "hashes": {},
        "counts": {},
        "versions": {"catalog": version},
        "code_sha": "b" * 40,
        "reason_code_tallies": {},
    }
    if valid:
        assert private_manifest(data) == data
    else:
        with pytest.raises(BuildError, match="private_manifest_string"):
            private_manifest(data)


BANNED_MODULES = {"requests", "httpx", "urllib.request", "http.client", "socket", "huggingface_hub", "subprocess"}
BANNED_CALLS = {"os.system", "builtins.__import__", "builtins.eval", "builtins.exec"}


def assert_no_execution(source):
    tree = ast.parse(source)
    aliases = {"__import__": "builtins.__import__", "eval": "builtins.eval", "exec": "builtins.exec"}

    def banned(name):
        return name in BANNED_CALLS or any(name == mod or name.startswith(mod + ".") for mod in BANNED_MODULES)

    def dotted(node):
        if isinstance(node, ast.Name):
            return aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return dotted(node.value) + "." + node.attr
        return ""

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not banned(alias.name), alias.name
                aliases[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not banned(module), module
            for alias in node.names:
                assert not (
                    alias.name == "*" and (module == "os" or any(m.startswith(module + ".") for m in BANNED_MODULES))
                ), module
                name = module + "." + alias.name
                assert not banned(name), name
                aliases[alias.asname or alias.name] = name
    # Propagate straightforward local aliases, so an alias cannot erase the
    # imported module/function identity before a banned attribute is used.
    for _ in range(len(list(ast.walk(tree)))):
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                name = dotted(node.value)
                for target in node.targets:
                    if name and isinstance(target, ast.Name) and aliases.get(target.id) != name:
                        aliases[target.id] = name
                        changed = True
        if not changed:
            break
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert not banned(dotted(node)), dotted(node)
        if isinstance(node, ast.Call):
            name = dotted(node.func)
            assert not banned(name), name
            if name in {"importlib.import_module", "builtins.__import__"} and node.args:
                module = node.args[0]
                assert not (isinstance(module, ast.Constant) and isinstance(module.value, str) and banned(module.value))
            if name in {"getattr", "builtins.getattr"} and len(node.args) >= 2:
                attribute = node.args[1]
                if isinstance(attribute, ast.Constant) and isinstance(attribute.value, str):
                    assert not banned(dotted(node.args[0]) + "." + attribute.value)


def test_package_has_no_network_or_process_execution_imports():
    modules = [(framework.__name__, framework.__spec__)]
    for info in pkgutil.walk_packages(framework.__path__, framework.__name__ + "."):
        modules.append((info.name, info.module_finder.find_spec(info.name)))
    for name, spec in modules:
        assert spec is not None and hasattr(spec.loader, "get_source"), name
        source = spec.loader.get_source(name)
        assert source is not None, name
        assert_no_execution(source)


@pytest.mark.parametrize(
    "source",
    [
        'import importlib; importlib.import_module("socket")',
        'import importlib as i; i.import_module("subprocess")',
        'from importlib import import_module as load; load("urllib.request")',
        '__import__("socket")',
        'import os; getattr(os, "system")("SYNTHETIC")',
        'import os as o; o.system("SYNTHETIC")',
        'import os as o; p = o; p.system("SYNTHETIC")',
        'from os import system as run; run("SYNTHETIC")',
        "from socket import *",
        "from os import *",
        "from urllib import request as r",
        'import urllib as u; u.request.urlopen("SYNTHETIC")',
    ],
)
def test_semantic_import_guard_refuses_dynamic_and_alias_bypasses(source):
    with pytest.raises(AssertionError):
        assert_no_execution(source)


def test_synthetic_build_never_calls_network_or_process_execution(bundle, monkeypatch):
    import os
    import socket
    import subprocess

    def forbidden(*args, **kwargs):
        raise AssertionError("SYNTHETIC forbidden runtime execution")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(os, "system", forbidden)
    with OutputGuard(bundle["root"] / "SYNTHETIC-runtime-out") as guard:
        assert (
            execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle))["status"]
            == "built"
        )
        assert (
            execute(
                bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle), verify=True
            )["status"]
            == "verified"
        )


def test_missing_catalog_slot_withholds_and_preserves_unit_accounting(bundle):
    for line in bundle["catalog"]["components"]["C1"]["instructions"]:
        line["slots"] = ["sentence", "SYNTHETIC_missing_slot"]
        line["template"] += " {SYNTHETIC_missing_slot}"
    save_bundle(bundle)
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle))
        accounting = json.loads(guard.read("accounting.json"))["C1"]
        assert accounting["withheld"] == 12
        assert accounting["accepted"] == 0
        assert accounting["counted"] == 12
        assert accounting["reasons"]["catalog_inapplicable"] == 12
        with pytest.raises(BuildError, match="mutation_unavailable"):
            execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle), verify=True)


def test_input_pin_drift_fails_verify_even_if_unused_metadata_changed(bundle):
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle))
        bundle["register"]["sources"][0]["SYNTHETIC_note"] = "SYNTHETIC new metadata"
        save_bundle(bundle)
        with pytest.raises(BuildError, match="artifact_mismatch"):
            execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle), verify=True)


def test_cli_logging_failure_and_malformed_request_fail_safely(bundle, monkeypatch, capsys):
    (bundle["root"] / "request.json").write_text("SYNTHETIC malformed input")
    args = ["build", "--config", str(bundle["root"] / "request.json"), "--out", str(bundle["root"] / "SYNTHETIC-out")]
    assert cli.main(args) == 1
    assert "SYNTHETIC" not in capsys.readouterr().err
    monkeypatch.setattr(OutputGuard, "write", lambda *a, **kw: (_ for _ in ()).throw(ValueError("SYNTHETIC secret")))
    assert cli.main(args) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "error_log_unavailable"


@pytest.mark.parametrize("error", [KeyError, TypeError])
def test_adapter_programming_errors_fail_build_without_withholding(bundle, error):
    class BrokenAdapter:
        def resolve(self, *args):
            raise error("SYNTHETIC bug")

    bundle["config"]["synthetic_sources"] = []
    save_bundle(bundle)
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        with pytest.raises(BuildError, match="attribution_adapter"):
            execute(
                bundle["root"] / "request.json",
                guard,
                component_objects=synthetic_components(bundle),
                adapters={"synthetic": BrokenAdapter()},
            )


def test_verify_generates_five_private_generic_mutation_fixtures(bundle):
    from scripts.projects.open_model_data.review_build.contract import candidate_from_dict

    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle))
        execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle), verify=True)
        results = json.loads(guard.read("mutation-fixtures/results.json"))
        assert results == {
            "absent_quote": "quote_mismatch",
            "wrong_span": "quote_span",
            "empty_locator": "empty_locator",
            "missing_unit": "missing_unit",
            "swapped_citation": "unit_id_mismatch",
        }
        for name, code in results.items():
            stream = [
                candidate_from_dict(json.loads(line))
                for line in jsonl_lines(guard.read(f"mutation-fixtures/{name}.jsonl").decode("utf-8"))
                if line.strip()
            ]
            with pytest.raises(BuildError, match=code):
                run_gate(bundle, stream)


def test_verify_refuses_a_mutation_that_the_gate_admits(bundle, monkeypatch):
    from scripts.projects.open_model_data.review_build.build import verify_mutations
    from scripts.projects.open_model_data.review_build.catalog import Catalog
    from scripts.projects.open_model_data.review_build.gate import Gate

    with SnapshotReader({"sources.db": bundle["db"]}) as reader, OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        resolver = Resolver(bundle["register"], {"synthetic": SyntheticAdapter()})
        monkeypatch.setattr(Gate, "run", lambda self, candidates: ([], {}))
        with pytest.raises(BuildError, match="mutation_admitted"):
            verify_mutations(
                {**bundle["config"], "components": bundle["specs"]},
                bundle["candidates"],
                reader,
                Catalog(bundle["catalog"]),
                resolver,
                guard,
            )

        def wrong_failure(self, candidates):
            raise BuildError("SYNTHETIC unrelated")

        monkeypatch.setattr(Gate, "run", wrong_failure)
        with pytest.raises(BuildError, match="mutation_wrong_failure"):
            verify_mutations(
                {**bundle["config"], "components": bundle["specs"]},
                bundle["candidates"],
                reader,
                Catalog(bundle["catalog"]),
                resolver,
                guard,
            )


def test_cli_passes_derived_repository_root_to_output_guard(bundle, monkeypatch, capsys):
    supplied = []
    real_guard = cli.OutputGuard

    def capture(path, protected_roots):
        supplied.extend(protected_roots)
        return real_guard(path, protected_roots)

    monkeypatch.setattr(cli, "OutputGuard", capture)
    assert (
        cli.main(
            ["build", "--config", str(bundle["root"] / "request.json"), "--out", str(bundle["root"] / "SYNTHETIC-out")]
        )
        == 0
    )
    assert supplied == [Path(cli.__file__).resolve().parents[4]]
    assert (supplied[0] / ".git").exists()
    capsys.readouterr()


@pytest.mark.parametrize("component", ["C1", "C9"])
def test_verify_mutations_work_on_a_single_unit_from_any_component(bundle, component):
    bundle["candidates"] = [replace(bundle["candidates"][0], component=component)]
    bundle["spec"]["unit_query"]["sql"] += " WHERE id=1"
    bundle["spec"]["frozen_count"] = 1
    bundle["specs"] = {component: bundle["spec"]}
    bundle["catalog"]["components"] = {component: bundle["catalog"]["components"]["C1"]}
    save_bundle(bundle)
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle))
        assert (
            execute(
                bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle), verify=True
            )["status"]
            == "verified"
        )
        assert json.loads(guard.read("mutation-fixtures/results.json"))["swapped_citation"] == "quote_mismatch"
