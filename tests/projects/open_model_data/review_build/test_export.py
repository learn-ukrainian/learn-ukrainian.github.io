"""Synthetic builds exercise filters without opening any project source store."""

import copy
import json
from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build import __main__ as cli
from scripts.projects.open_model_data.review_build import output
from scripts.projects.open_model_data.review_build.build import execute
from scripts.projects.open_model_data.review_build.contract import canonical, digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.export import export_build, parse_filters
from scripts.projects.open_model_data.review_build.output import OutputGuard
from tests.projects.open_model_data.review_build.conftest import (
    catalog_data,
    register_data,
    save_bundle,
    selector,
    synthetic_components,
    write_db,
)


@pytest.fixture
def verified_build(bundle, monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    # C1: six source-A-only and six mixed; C9: twelve source-B-only.
    write_db(bundle["db"], bundle["rows"], table="units_b")
    original = list(bundle["candidates"])
    second = []
    for index, candidate in enumerate(original):

        def b_value(value):
            return replace(
                value, citations=tuple(replace(c, source_id="synthetic-b", table="units_b") for c in value.citations)
            )

        second.append(
            replace(
                candidate,
                component="C9",
                slots=tuple(map(b_value, candidate.slots)),
                response=tuple(map(b_value, candidate.response)),
            )
        )
        value = candidate.slots[0]
        supporting = b_value(value).citations[0] if index >= 6 else value.citations[0]
        bundle["candidates"][index] = replace(
            candidate, slots=(replace(value, citations=(*value.citations, supporting)),)
        )
    bundle["candidates"].extend(second)
    spec = copy.deepcopy(bundle["spec"])
    spec["unit_query"]["sql"] = "SELECT id FROM units_b"
    spec["unit_id"]["primary"][0]["table"] = "units_b"
    b_policy = {**spec["compatibility"][0], "table": "units_b", "source_id": "synthetic-b"}
    spec["compatibility"] = [b_policy]
    bundle["spec"]["binding"]["rules"].append(
        {"op": "equal", "values": [selector(field="source_field"), selector(citation=1, field="source_field")]}
    )
    bundle["spec"]["compatibility"].append(b_policy)
    bundle["specs"]["C9"] = spec
    bundle["catalog"]["components"].update(catalog_data("C9")["components"])
    bundle["register"] = register_data(sources=("synthetic", "synthetic-b"))
    for entry, status, licence in zip(
        bundle["register"]["sources"], ("granted", "none"), ("SYNTHETIC A", "SYNTHETIC B"), strict=True
    ):
        entry["permission_status"] = status
        entry["terms"]["licence"]["name"] = licence
    bundle["config"]["synthetic_sources"].append("synthetic-b")
    save_bundle(bundle)
    build = bundle["root"] / "SYNTHETIC-build"
    with OutputGuard(build) as guard:
        execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle))
        execute(bundle["root"] / "request.json", guard, component_objects=synthetic_components(bundle), verify=True)
    return build


@pytest.mark.parametrize(
    "key,value",
    [
        ("source_id", "synthetic"),
        ("licence_ref", "permissions-register.yaml#synthetic; SYNTHETIC A"),
        ("permission_status", "granted"),
    ],
)
@pytest.mark.parametrize("direction,kept,dropped", [("include", 6, 18), ("exclude", 12, 12)])
def test_each_filter_key_include_exclude_and_whole_mixed_record(verified_build, key, value, direction, kept, dropped):
    with OutputGuard(verified_build.parent / "SYNTHETIC-export") as guard:
        result = export_build(verified_build, guard, **{direction: [f"{key}={value}"]})
        assert (result["kept"], result["dropped"]) == (kept, dropped)
        manifest = json.loads(guard.read("manifest.json"))
        assert manifest["input_build_sha256"] == digest((verified_build / "manifest.json").read_bytes())
        assert manifest["filter"][direction] == {key: [value]}
        assert manifest["accounting"] == json.loads(guard.read("accounting.json"))
        assert manifest["accounting"]["components"] == {
            "C1": {
                "kept": 6 if direction == "include" else 0,
                "dropped": 6 if direction == "include" else 12,
                "counted": 12,
            },
            "C9": {
                "kept": 0 if direction == "include" else 12,
                "dropped": 12 if direction == "include" else 0,
                "counted": 12,
            },
        }
        assert manifest["accounting"]["sources"] == {
            "synthetic": {
                "kept": 6 if direction == "include" else 0,
                "dropped": 6 if direction == "include" else 12,
                "counted": 12,
            },
            "synthetic-b": {
                "kept": 0 if direction == "include" else 12,
                "dropped": 18 if direction == "include" else 6,
                "counted": 18,
            },
        }
        notices = [json.loads(line) for line in guard.read("licence-notices.jsonl").split(b"\n") if line]
        assert {n["source_id"] for n in notices} == {"synthetic" if direction == "include" else "synthetic-b"}
        for component in ("C1", "C9"):
            original = (verified_build / component / "records.jsonl").read_bytes().split(b"\n")
            records = guard.read(f"{component}/records.jsonl").split(b"\n")
            assert all(line in original for line in records if line)
            assert all(
                len({p["source_id"] for p in json.loads(line)["provenance"].values()}) == 1 for line in records if line
            )
        assert all(digest(guard.read(name)) == sha for name, sha in manifest["files"].items())
        assert all(p.stat().st_mode & 0o777 == (0o700 if p.is_dir() else 0o600) for p in guard.path.rglob("*"))


def test_no_filter_preserves_records_and_uses_only_pinned_register(verified_build, bundle, monkeypatch):
    (bundle["root"] / "register.yaml").write_text("SYNTHETIC live register changed")
    (bundle["root"] / "request.json").write_text("SYNTHETIC live request changed")
    monkeypatch.setattr(cli, "read_request", lambda *a: pytest.fail("export read live request"))
    with OutputGuard(verified_build.parent / "SYNTHETIC-export") as guard:
        result = export_build(verified_build, guard)
        assert (result["kept"], result["dropped"]) == (24, 0)
        for component in ("C1", "C9"):
            assert (
                guard.read(f"{component}/records.jsonl") == (verified_build / component / "records.jsonl").read_bytes()
            )
        assert guard.read("licence-notices.jsonl") == (verified_build / "licence-notices.jsonl").read_bytes()
    with OutputGuard(verified_build.parent / "SYNTHETIC-pinned") as guard:
        assert export_build(verified_build, guard, include=["permission_status=granted"])["kept"] == 6
    assert (
        cli.main(["export", "--from", str(verified_build), "--out", str(verified_build.parent / "SYNTHETIC-cli")]) == 0
    )


def test_combined_filters_and_alternative_values(verified_build):
    with OutputGuard(verified_build.parent / "SYNTHETIC-export") as guard:
        result = export_build(
            verified_build,
            guard,
            include=["source_id=synthetic", "source_id=synthetic-b", "permission_status=granted"],
            exclude=["licence_ref=permissions-register.yaml#synthetic-b; SYNTHETIC B"],
        )
        assert (result["kept"], result["dropped"]) == (6, 18)
    with OutputGuard(verified_build.parent / "SYNTHETIC-both") as guard:
        assert (
            export_build(verified_build, guard, include=["source_id=synthetic", "source_id=synthetic-b"])["kept"] == 24
        )
    with OutputGuard(verified_build.parent / "SYNTHETIC-empty") as guard:
        assert (
            export_build(verified_build, guard, exclude=["source_id=synthetic", "source_id=synthetic-b"])["kept"] == 0
        )
        assert guard.read("licence-notices.jsonl") == b""


@pytest.mark.parametrize("criterion", ["wrong=synthetic", "source_id", "source_id=", "permission_status=   "])
def test_invalid_filters_refused(criterion):
    with pytest.raises(BuildError, match="export_filter"):
        parse_filters([criterion])
    assert parse_filters(["source_id=b", "source_id=a", "source_id=b"]) == {"source_id": ["a", "b"]}


@pytest.mark.parametrize(
    "name",
    [
        "C1/records.jsonl",
        "manifest.json",
        "permissions-register.yaml",
        "licence-notices.jsonl",
        "verification.json",
        "private-manifest.json",
    ],
)
def test_tampered_build_refused_before_record_writes(verified_build, name):
    with OutputGuard(verified_build) as guard:
        guard.write(name, guard.read(name) + b" ")
    with OutputGuard(verified_build.parent / "SYNTHETIC-export") as guard:
        if name == "verification.json":
            # Whitespace is not a semantic receipt change; change the hash.
            with OutputGuard(verified_build) as source:
                source.write(name, canonical({"schema": "omd-review-verification.v1", "build_sha256": "0" * 64}))
        with pytest.raises(BuildError, match=r"artifact_mismatch|export_unverified"):
            export_build(verified_build, guard)
        assert not list(guard.path.iterdir())


def test_unverified_build_and_failed_reverification_refused(verified_build, bundle):
    with OutputGuard(verified_build) as source:
        execute(bundle["root"] / "request.json", source, component_objects=synthetic_components(bundle))
    with OutputGuard(verified_build.parent / "SYNTHETIC-export") as guard:
        with pytest.raises(BuildError, match="export_unverified"):
            export_build(verified_build, guard)
    with OutputGuard(verified_build) as source:
        execute(bundle["root"] / "request.json", source, component_objects=synthetic_components(bundle), verify=True)
        source.write("C1/records.jsonl", b"SYNTHETIC tampered")
        with pytest.raises(BuildError, match="artifact_mismatch"):
            execute(
                bundle["root"] / "request.json", source, component_objects=synthetic_components(bundle), verify=True
            )
        assert json.loads(source.read("verification.json"))["status"] == "unverified"


def test_export_refuses_overlap_nonempty_and_unsafe_output(verified_build, monkeypatch, capsys):
    for path in (verified_build, verified_build / "SYNTHETIC-subset", verified_build.parent):
        with OutputGuard(path) as guard, pytest.raises(BuildError, match="export_overlap"):
            export_build(verified_build, guard)
    with OutputGuard(verified_build.parent / "SYNTHETIC-export") as guard:
        guard.write("SYNTHETIC-existing", b"SYNTHETIC previous output")
        with pytest.raises(BuildError, match="export_output_not_empty"):
            export_build(verified_build, guard)
        assert guard.read("SYNTHETIC-existing") == b"SYNTHETIC previous output"
    monkeypatch.setattr(output, "filesystem", lambda path: "nfs")
    assert (
        cli.main(["export", "--from", str(verified_build), "--out", str(verified_build.parent / "SYNTHETIC-nfs")]) == 1
    )
    assert json.loads(capsys.readouterr().err)["error"] == "filesystem_refused"


def test_export_help_and_private_usage_errors(capsys):
    with pytest.raises(SystemExit):
        cli.main(["export", "--help"])
    help_text = capsys.readouterr().out
    assert all(
        text in help_text
        for text in (
            "--from",
            "--out",
            "--include",
            "--exclude",
            "licence_ref",
            "permission_status",
            "Outputs:",
            "Exit codes:",
        )
    )
    assert cli.main(["export", "--include", "SYNTHETIC PRIVATE CRITERION"]) == 2
    assert "SYNTHETIC PRIVATE" not in capsys.readouterr().err


def reseal_synthetic_fixture(build, changes):
    """Test-only resealing lets malformed semantics reach export's stop checks."""
    with OutputGuard(build) as guard:
        manifest = json.loads(guard.read("manifest.json"))
        receipt = json.loads(guard.read("verification.json"))
        for name, content in changes.items():
            guard.write(name, content)
            manifest["files"][name] = digest(content)
            receipt["files"][name] = digest(content)
        if "permissions-register.yaml" in changes:
            manifest["pins"]["register"] = digest(changes["permissions-register.yaml"])
        raw = canonical(manifest) + b"\n"
        guard.write("manifest.json", raw)
        receipt["files"]["manifest.json"] = receipt["build_sha256"] = digest(raw)
        guard.write("verification.json", canonical(receipt) + b"\n")


@pytest.mark.parametrize(
    "fault", ["empty", "unknown_source", "missing_source", "wrong_licence", "invalid_json", "wrong_component"]
)
def test_indeterminate_or_inconsistent_record_sources_stop_export(verified_build, fault):
    records = (verified_build / "C1/records.jsonl").read_bytes().split(b"\n")
    record = json.loads(records[0])
    provenance = next(iter(record["provenance"].values()))
    if fault == "empty":
        record["provenance"] = {}
    elif fault == "unknown_source":
        provenance["source_id"] = "SYNTHETIC missing source"
    elif fault == "missing_source":
        del provenance["source_id"]
    elif fault == "wrong_licence":
        provenance["licence_ref"] = "SYNTHETIC wrong licence"
    elif fault == "wrong_component":
        record["component"] = "C9"
    records[0] = b"SYNTHETIC invalid JSON" if fault == "invalid_json" else canonical(record)
    reseal_synthetic_fixture(verified_build, {"C1/records.jsonl": b"\n".join(records)})
    with OutputGuard(verified_build.parent / "SYNTHETIC-export") as guard:
        with pytest.raises(BuildError, match=r"export_provenance|export_input"):
            export_build(verified_build, guard, exclude=["source_id=synthetic"])
        assert not list(guard.path.iterdir())


def test_missing_filter_metadata_and_duplicate_register_source_refuse(verified_build):
    import yaml

    register = yaml.safe_load((verified_build / "permissions-register.yaml").read_bytes())
    del register["sources"][0]["permission_status"]
    reseal_synthetic_fixture(verified_build, {"permissions-register.yaml": yaml.safe_dump(register).encode()})
    with OutputGuard(verified_build.parent / "SYNTHETIC-export") as guard:
        with pytest.raises(BuildError, match="export_register"):
            export_build(verified_build, guard, exclude=["permission_status=none"])
        assert not list(guard.path.iterdir())
    register["sources"].append(register["sources"][0])
    reseal_synthetic_fixture(verified_build, {"permissions-register.yaml": yaml.safe_dump(register).encode()})
    with OutputGuard(verified_build.parent / "SYNTHETIC-duplicate") as guard:
        with pytest.raises(BuildError, match="export_register"):
            export_build(verified_build, guard)


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"])
def test_export_preserves_unicode_separators_crlf_and_unterminated_record(verified_build, separator):
    # Physical byte framing remains intact even for valid non-canonical JSONL.
    lines = (verified_build / "C1/records.jsonl").read_bytes().split(b"\n")
    records = [json.loads(line) for line in lines if line]
    records[0]["instruction"] += separator + "SYNTHETIC continuation"
    raw = b"\r\n".join(canonical(record) for record in records)
    reseal_synthetic_fixture(verified_build, {"C1/records.jsonl": raw})
    with OutputGuard(verified_build.parent / "SYNTHETIC-export") as guard:
        assert export_build(verified_build, guard)["kept"] == 24
        assert guard.read("C1/records.jsonl") == raw


def test_missing_build_directory_is_not_recreated(verified_build):
    (verified_build / "C1").rename(verified_build / "SYNTHETIC-unavailable")
    with OutputGuard(verified_build.parent / "SYNTHETIC-export") as guard:
        with pytest.raises(BuildError, match="artifact_mismatch"):
            export_build(verified_build, guard)
    assert not (verified_build / "C1").exists()


def test_cli_refusals_preserve_input_and_existing_destination(verified_build, capsys):
    before = {p.relative_to(verified_build): p.read_bytes() for p in verified_build.rglob("*") if p.is_file()}
    for target in (verified_build, verified_build / "SYNTHETIC-nested", verified_build.parent):
        assert cli.main(["export", "--from", str(verified_build), "--out", str(target)]) == 1
        capsys.readouterr()
    assert not (verified_build / "SYNTHETIC-nested").exists()
    assert before == {p.relative_to(verified_build): p.read_bytes() for p in verified_build.rglob("*") if p.is_file()}
    assert not (verified_build.parent / "logs").exists()
    target = verified_build.parent / "SYNTHETIC-occupied"
    with OutputGuard(target) as guard:
        guard.write("SYNTHETIC-existing", b"SYNTHETIC previous export")
    assert cli.main(["export", "--from", str(verified_build), "--out", str(target)]) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "export_output_not_empty"
    assert list(p.name for p in target.iterdir()) == ["SYNTHETIC-existing"]


def test_cli_failed_request_invalidates_previous_verification(verified_build, bundle, capsys):
    (bundle["root"] / "request.json").write_text("SYNTHETIC invalid request")
    assert cli.main(["verify", "--config", str(bundle["root"] / "request.json"), "--out", str(verified_build)]) == 1
    capsys.readouterr()
    assert json.loads((verified_build / "verification.json").read_bytes())["status"] == "unverified"
