import ast
import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.projects.open_model_data.review_build import __main__ as cli
from scripts.projects.open_model_data.review_build import output
from scripts.projects.open_model_data.review_build.attribution import Attribution, Resolver, SyntheticAdapter
from scripts.projects.open_model_data.review_build.build import execute
from scripts.projects.open_model_data.review_build.contract import canonical, digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.manifest import private_manifest
from scripts.projects.open_model_data.review_build.output import OutputGuard
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import run_gate, save_bundle


@pytest.fixture(autouse=True)
def synthetic_mount(monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")


def test_build_verify_determinism_and_tamper_refusal(bundle):
    results = []
    dirs = [bundle["root"] / name for name in ("SYNTHETIC-one", "SYNTHETIC-two")]
    for path in dirs:
        with OutputGuard(path) as guard:
            result = execute(bundle["root"] / "request.json", guard)
            assert execute(bundle["root"] / "request.json", guard, verify=True)["status"] == "verified"
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
            execute(bundle["root"] / "request.json", guard, verify=True)
    for path in dirs:
        assert all(p.stat().st_mode & 0o777 == (0o700 if p.is_dir() else 0o600) for p in path.rglob("*"))


@pytest.mark.parametrize(
    "form", ["SYNTHETIC <edition> source", "SYNTHETIC cite the book title per source", "SYNTHETIC insert metadata"]
)
def test_unresolved_attribution_fails_gate_and_withholds_source_records(bundle, form):
    bundle["register"]["sources"][0]["citation"]["form"] = form
    with pytest.raises(BuildError, match="attribution_unresolved"):
        run_gate(bundle)
    save_bundle(bundle)
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard)
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


def test_package_has_no_network_or_process_execution_imports():
    root = Path(cli.__file__).parent
    banned = {"requests", "httpx", "urllib.request", "http.client", "socket", "huggingface_hub", "subprocess"}
    for path in root.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert not any(
                    alias.name == name or alias.name.startswith(name + ".") for alias in node.names for name in banned
                ), path.name
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = {module} | {module + "." + alias.name for alias in node.names}
                assert not any(item == name or item.startswith(name + ".") for item in names for name in banned), (
                    path.name
                )
                assert not (module == "os" and any(alias.name == "system" for alias in node.names)), path.name
            if isinstance(node, ast.Attribute):
                assert not (isinstance(node.value, ast.Name) and node.value.id == "os" and node.attr == "system"), (
                    path.name
                )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"__import__", "eval", "exec"}, path.name


def test_missing_catalog_slot_withholds_and_preserves_unit_accounting(bundle):
    candidate = bundle["candidates"][0]
    bundle["candidates"][0] = replace(candidate, slots=(replace(candidate.slots[0], slot="SYNTHETIC_missing_slot"),))
    save_bundle(bundle)
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard)
        accounting = json.loads(guard.read("accounting.json"))["C1"]
        assert accounting["withheld"] == 1
        assert accounting["accepted"] == 11
        assert accounting["counted"] == 12
        assert accounting["reasons"]["catalog_inapplicable"] == 1
        assert execute(bundle["root"] / "request.json", guard, verify=True)["status"] == "verified"


def test_input_pin_drift_fails_verify_even_if_unused_metadata_changed(bundle):
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard)
        bundle["register"]["sources"][0]["SYNTHETIC_note"] = "SYNTHETIC new metadata"
        save_bundle(bundle)
        with pytest.raises(BuildError, match="artifact_mismatch"):
            execute(bundle["root"] / "request.json", guard, verify=True)


def test_cli_logging_failure_and_malformed_request_fail_safely(bundle, monkeypatch, capsys):
    (bundle["root"] / "request.json").write_text("SYNTHETIC malformed input")
    args = ["build", "--config", str(bundle["root"] / "request.json"), "--out", str(bundle["root"] / "SYNTHETIC-out")]
    assert cli.main(args) == 1
    assert "SYNTHETIC" not in capsys.readouterr().err
    monkeypatch.setattr(OutputGuard, "write", lambda *a, **kw: (_ for _ in ()).throw(ValueError("SYNTHETIC secret")))
    assert cli.main(args) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "error_log_unavailable"
