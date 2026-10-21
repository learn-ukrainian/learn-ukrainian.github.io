"""Release mechanics over synthetic authority, never real language certification."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.atlas import word_card_certification as certification
from scripts.projects.open_model_data.review_build import output
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.word_cards import dataset_projection as projection
from tests.word_card_certification_fixtures import certification_fixture  # noqa: F401


@pytest.fixture(autouse=True)
def synthetic_mount(monkeypatch):
    # Declare fixture storage for CI overlay filesystems. Real mount parsing
    # and failure cases are covered by the existing OutputGuard suite.
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")


@pytest.fixture
def release_input(certification):
    sources = []
    for name in ("vesum", "ulif", "internal", "sum11"):
        sources.append({"id": name, "appears_in": ["internal"] if name == "internal" else ["dataset"],
                        "citation": {"form": f"Synthetic {name} edition"},
                        "terms": {"licence": {"name": "Fixture terms", "spdx": None}}})
    register = {"schema_version": 2, "sources": sources, "operator_decisions": [{"id": "fixture-policy"}]}
    certification.register.write_text(yaml.safe_dump(register))
    card = certification.card
    card["build"]["inputs"]["R"]["register"]["content_sha256"] = hashlib.sha256(
        certification.register.read_bytes()).hexdigest()
    card["assertions"] = []
    for index, (source_id, field, value) in enumerate([
        ("vesum", "spelling", "fixture-head"), ("ulif", "definition_uk", "permitted-definition"),
        ("internal", "definition_uk", "PRIVATE-PAYLOAD"), ("unknown", "examples", "UNKNOWN-PAYLOAD"),
        ("sum11", "definition_uk", "SOVIET-PAYLOAD"), ("sum11", "russification_exposed", "SOVIET-CONTEXT"),
        ("ulif", "stress", "INACTIVE-PAYLOAD"), ("ulif", "examples", "GENERATED-PAYLOAD"),
        ("ulif", "examples", "UNRESOLVED-PAYLOAD"), ("ulif", "examples", "REJECTED-PAYLOAD"),
    ]):
        card["assertions"].append({
            "assertion_id": "wa_" + f"{index:024x}", "subject": {"kind": "card", "id": card["card_id"]},
            "field": field, "value": value, "value_norm": value,
            "source_id": source_id, "snapshot_id": "fixture-v1", "locator": f"{source_id}:row:{index}",
            "source_record_key": f"{source_id}:record:{index}",
            "extraction_version": "fixture-v1", "extraction_confidence": "high",
            "producer": {"kind": "generator" if index == 7 else "source_extract", "name": "fixture"},
            "review": {"status": "rejected" if index == 9 else "none"},
            "licence_ref": {"register_source_id": source_id, "register_version": 2},
            "status": "superseded" if index == 6 else "active",
            **({"mapping": {"confidence": "unresolved", "basis": "entry"}} if index == 8 else {}),
        })
    certification.approve(card)
    return certification


def release(fixture, **kwargs):
    return projection.create_release([fixture.card], release_version="v0.1.0-pilot", **kwargs)


def test_permission_filtering_and_complete_citations(release_input):
    result = release(release_input)
    rows = [json.loads(line) for line in result.dataset.splitlines()]
    assert len(rows) == 1
    assert {f["field"]: f["value"] for f in rows[0]["fields"]} == {
        "spelling": "fixture-head", "definition_uk": "permitted-definition",
    }
    for field in rows[0]["fields"]:
        source = field["citation"]["source_id"]
        assert field["citation"] == {
            "source_id": source, "snapshot_id": "fixture-v1",
            "locator": f"{source}:row:{0 if source == 'vesum' else 1}", "source_record_id": None,
            "source_record_key": f"{source}:record:{0 if source == 'vesum' else 1}",
            "licence_ref": {"register_source_id": source, "register_version": 2},
            "attribution": f"Synthetic {source} edition", "licence": {"name": "Fixture terms", "spdx": None},
            "terms_ref": f"docs/sources/permissions-register.yaml#sources/{source}/terms",
        }
    for forbidden in (b"PRIVATE", b"UNKNOWN", b"SOVIET", b"INACTIVE", b"GENERATED", b"UNRESOLVED", b"REJECTED"):
        assert forbidden not in result.dataset
    assert set(rows[0]) == {"card_id", "card_version", "card_kind", "status", "known_gaps", "fields"}


@pytest.mark.parametrize("format", ["json", "jsonl"])
def test_exact_hashes_denominators_and_package(release_input, tmp_path, format):
    result = release(release_input, format=format)
    result.write(tmp_path / "package")
    manifest = json.loads((tmp_path / "package/manifest.json").read_bytes())
    raw = (tmp_path / "package" / f"word-cards.{format}").read_bytes()
    assert raw == result.dataset
    assert manifest["dataset_sha256"] == hashlib.sha256(raw).hexdigest()
    assert manifest["dataset_bytes"] == len(raw)
    assert (manifest["card_count"], manifest["input_card_count"], manifest["field_citation_count"],
            manifest["input_assertion_count"]) == (1, 1, 2, 10)
    assert sum(s["included_assertions"] + s["filtered_assertions"]
               for s in manifest["source_breakdown"].values()) == 10
    assert manifest["source_breakdown"]["sum11"] == {
        "included_assertions": 0, "filtered_assertions": 2, "filter_reasons": {"historical_context_only": 2},
        "included_source_rows": 0, "filtered_source_rows": 2, "mixed_source_rows": 0,
    }
    assert manifest["operator_decisions"] == [{"id": "fixture-policy"}]
    with pytest.raises(FileExistsError):
        result.write(tmp_path / "package")


def test_determinism_and_input_immutability(release_input):
    original = copy.deepcopy(release_input.card)
    first = release(release_input)
    release_input.card["assertions"].reverse()
    # A new order is a different certified artifact, but projection order is stable.
    release_input.approve(release_input.card)
    reordered = release(release_input)
    first_row, reordered_row = json.loads(first.dataset), json.loads(reordered.dataset)
    assert first_row.pop("card_version") == original["build"]["card_version"]
    assert reordered_row.pop("card_version") == release_input.card["build"]["card_version"]
    assert original["build"]["card_version"] != release_input.card["build"]["card_version"]
    assert first_row == reordered_row
    assert release(release_input) == reordered
    release_input.card["assertions"].reverse()
    assert release_input.card["assertions"] == original["assertions"]
    release_input.approve(release_input.card)
    assert release(release_input) == first


@pytest.mark.parametrize("selector", [
    {"source_id": "ulif"}, {"locator": "ulif:row:1"}, {"source_id": "ulif", "locator": "ulif:record:1"},
])
def test_withdrawal_drill(release_input, tmp_path, selector):
    original = release(release_input)
    options = {"previous_version": "v0.1.0-pilot", "release_version": "v0.1.1-pilot",
               "selector": selector, "justification": "Synthetic removal request"}
    replacement = projection.withdraw_release([release_input.card], **options)
    assert replacement == projection.withdraw_release([release_input.card], **options)
    assert b"permitted-definition" not in replacement.dataset
    assert b"fixture-head" in replacement.dataset
    notice = replacement.withdrawal_notice
    assert notice["previous_dataset_sha256"] == original.manifest["dataset_sha256"]
    assert notice["replacement_dataset_sha256"] == hashlib.sha256(replacement.dataset).hexdigest()
    assert notice["removed_field_citations"] == 1
    assert notice["withdrawal"] == {"selector": selector, "justification": "Synthetic removal request"}
    replacement.write(tmp_path / "replacement")
    raw_notice = (tmp_path / "replacement/withdrawal-notice.json").read_bytes()
    assert replacement.manifest["withdrawal_notice_sha256"] == hashlib.sha256(raw_notice).hexdigest()


def test_cumulative_withdrawal_can_empty_release(release_input):
    prior = [{"selector": {"source_id": "ulif"}, "justification": "First request"}]
    replacement = projection.withdraw_release(
        [release_input.card], previous_version="v0.1.1-pilot", release_version="v0.1.2-pilot",
        selector={"source_id": "vesum"}, justification="Second request", withdrawals=prior,
    )
    assert replacement.dataset == b""
    assert replacement.manifest["card_count"] == replacement.manifest["field_citation_count"] == 0
    assert len(replacement.manifest["withdrawals"]) == 2


@pytest.mark.parametrize("fault", ["missing", "withdrawn", "site_only", "modified", "register", "source"])
def test_certification_refusals(release_input, fault, tmp_path):
    fixture = release_input
    if fault == "missing":
        fixture.ledger["approved_reviews"] = []
    elif fault == "withdrawn":
        fixture.ledger["approved_reviews"][0]["status"] = "withdrawn"
    elif fault == "site_only":
        fixture.ledger["approved_reviews"][0]["approved_for"] = ["site"]
    elif fault == "modified":
        fixture.card["assertions"][0]["value"] = "UNCERTIFIED"
    elif fault == "register":
        fixture.register.write_text("changed")
    else:
        fixture.snapshots["S", "source"].write_text("changed")
    fixture.ledger_path.write_text(json.dumps(fixture.ledger))
    with pytest.raises(certification.UncertifiedCardRefusal):
        release(fixture)
    source = tmp_path / "cards.json"
    source.write_text(json.dumps([fixture.card]))
    assert projection.main(["--cards", str(source), "--version", "v0.1.0", "--output", str(tmp_path / "no")]) == 1
    assert not (tmp_path / "no").exists()


@pytest.mark.parametrize("fault", ["source", "version", "locator", "snapshot", "attribution", "licence"])
def test_incomplete_citations_refuse(release_input, fault):
    a = release_input.card["assertions"][0]
    if fault in {"source", "version"}:
        a["licence_ref"]["register_source_id" if fault == "source" else "register_version"] = "wrong" if fault == "source" else 1
    elif fault in {"locator", "snapshot"}:
        a["locator" if fault == "locator" else "snapshot_id"] = ""
    else:
        register = yaml.safe_load(release_input.register.read_bytes())
        if fault == "attribution":
            register["sources"][0]["citation"]["form"] = ""
        else:
            register["sources"][0]["terms"]["licence"]["name"] = ""
        release_input.register.write_text(yaml.safe_dump(register))
        release_input.card["build"]["inputs"]["R"]["register"]["content_sha256"] = hashlib.sha256(
            release_input.register.read_bytes()).hexdigest()
    release_input.approve(release_input.card)
    with pytest.raises(projection.ProjectionRefusal, match="citation"):
        release(release_input)


def test_other_register_cannot_replace_certified_scope(release_input, tmp_path):
    alternate = tmp_path / "register.yaml"
    alternate.write_bytes(release_input.register.read_bytes() + b"\n")
    with pytest.raises(projection.ProjectionRefusal, match="register differs"):
        release(release_input, register_path=alternate)


def test_scope_must_be_an_explicit_array(release_input):
    register = yaml.safe_load(release_input.register.read_bytes())
    register["sources"][0]["appears_in"] = "dataset"
    release_input.register.write_text(yaml.safe_dump(register))
    release_input.card["build"]["inputs"]["R"]["register"]["content_sha256"] = hashlib.sha256(
        release_input.register.read_bytes()).hexdigest()
    release_input.approve(release_input.card)
    with pytest.raises(projection.ProjectionRefusal, match="source scopes"):
        release(release_input)


def test_mixed_source_row_counts_and_tombstones(release_input):
    card = release_input.card
    card["assertions"][6]["source_record_key"] = "ulif:record:1"
    card["assertions"].append({"assertion_id": "wa_" + "a" * 24, "status": "suppressed",
                               "suppression_ref": "synthetic-withdrawal"})
    release_input.approve(card)
    result = release(release_input)
    assert result.manifest["source_breakdown"]["ulif"]["mixed_source_rows"] == 1
    assert result.manifest["source_breakdown"]["_tombstone"]["filtered_assertions"] == 1
    assert result.manifest["input_assertion_count"] == 11
    assert b"synthetic-withdrawal" not in result.dataset


def test_duplicate_assertions_refuse(release_input):
    release_input.card["assertions"].append(copy.deepcopy(release_input.card["assertions"][0]))
    release_input.approve(release_input.card)
    with pytest.raises(projection.ProjectionRefusal, match="Duplicate assertion"):
        release(release_input)


def test_duplicate_cards_and_empty_inventory_refuse(release_input):
    for cards in ([], [release_input.card, release_input.card]):
        with pytest.raises(projection.ProjectionRefusal, match="nonempty and unique"):
            projection.create_release(cards, release_version="v0.1.0")


def test_withdrawal_requires_new_version(release_input):
    with pytest.raises(projection.ProjectionRefusal, match="new release version"):
        projection.withdraw_release([release_input.card], previous_version="v0.1.0", release_version="v0.1.0",
                                    selector={"source_id": "ulif"}, justification="request")


def test_output_guard_rejects_checkout_and_symlink(release_input, tmp_path):
    result = release(release_input)
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / ".git").write_text("synthetic worktree")
    with pytest.raises(BuildError, match="repository_output"):
        result.write(repository / "release")
    assert not (repository / "release").exists()
    link = tmp_path / "link"
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(BuildError, match="symlink_output"):
        result.write(link / "release")
    assert not (tmp_path / "release").exists()


@pytest.mark.parametrize("withdrawals", [
    [{"selector": {"source_id": "missing"}, "justification": "request"}],
    [{"selector": {}, "justification": "request"}],
    [{"selector": {"source_id": "ulif"}, "justification": ""}],
    [{"selector": {"unknown": "ulif"}, "justification": "request"}],
    {"not": "an array"},
])
def test_invalid_withdrawals_refuse(release_input, withdrawals):
    with pytest.raises(projection.ProjectionRefusal):
        release(release_input, withdrawals=withdrawals)


def test_cli_release_and_withdrawal(release_input, tmp_path, capsys):
    source = tmp_path / "cards.json"
    source.write_text(json.dumps({"cards": {release_input.card["card_id"]: release_input.card}}))
    common = ["--cards", str(source), "--format", "json"]
    assert projection.main([*common, "--version", "v0.1.0-pilot", "--output", str(tmp_path / "release")]) == 0
    assert json.loads(capsys.readouterr().out)["field_citation_count"] == 2
    assert projection.main([*common, "--version", "v0.1.1-pilot", "--output", str(tmp_path / "replacement"),
                            "--previous-version", "v0.1.0-pilot", "--withdraw-source", "ulif",
                            "--justification", "Removal request"]) == 0
    assert (tmp_path / "replacement/withdrawal-notice.json").is_file()


@pytest.mark.parametrize("shape", ["list", "map", "single", "jsonl", "directory", "assembly-directory"])
def test_input_formats(tmp_path, shape):
    card = {"card_id": "fixture", "assertions": []}
    path = tmp_path / ("cards.jsonl" if shape == "jsonl" else "cards.json")
    if "directory" in shape:
        path = tmp_path / "cards"
        directory = path / "cards" if shape == "assembly-directory" else path
        directory.mkdir(parents=True)
        (directory / "fixture.json").write_text(json.dumps(card))
    else:
        value = [card] if shape == "list" else {"fixture": card} if shape == "map" else card
        path.write_text(json.dumps(value) + "\n")
    assert projection.load_cards(path, Path("unused")) == [card]


def test_jsonl_keeps_unicode_separators_in_values(tmp_path):
    card = {"card_id": "fixture", "value": "embedded\u0085separator\u2028and\u2029text"}
    path = tmp_path / "cards.jsonl"
    path.write_bytes((json.dumps(card, ensure_ascii=False) + "\r\n\r\n").encode("utf-8"))
    assert projection.load_cards(path, Path("unused")) == [card]


def test_jsonl_rejects_bare_cr_record_separator(tmp_path):
    record = json.dumps({"card_id": "fixture"}).encode("utf-8")
    path = tmp_path / "cards.jsonl"
    path.write_bytes(record + b"\r" + record)
    with pytest.raises(json.JSONDecodeError):
        projection.load_cards(path, Path("unused"))


def test_pilot_manifest_uses_existing_readonly_assembly(tmp_path, monkeypatch):
    from scripts.atlas import word_card_assembly as assembly

    manifest = tmp_path / "pilot.json"
    manifest.write_text('{"selection": {}}')
    calls = []
    monkeypatch.setattr(assembly, "store_path", lambda name, explicit: tmp_path / f"{name}.db")
    monkeypatch.setattr(assembly, "load_inputs", lambda *args: calls.append(args) or "inputs")
    monkeypatch.setattr(assembly, "build", lambda inputs: {"cards": {"fixture": {"card_id": inputs}}})
    assert projection.load_cards(manifest, tmp_path / "register.yaml") == [{"card_id": "inputs"}]
    assert calls[0][0] == manifest
    assert calls[0][2] == tmp_path / "register.yaml"
    assert all(p.is_absolute() for p in calls[0][3:6])


def test_help_and_invalid_cli(tmp_path, capsys):
    with pytest.raises(SystemExit) as help_result:
        projection.main(["--help"])
    assert help_result.value.code == 0
    assert "Exit codes:" in capsys.readouterr().out
    with pytest.raises(SystemExit) as invalid:
        projection.main(["--cards", "missing", "--version", "v0.1.0", "--output", str(tmp_path / "no"),
                         "--withdraw-source", "ulif"])
    assert invalid.value.code == 2
    assert not (tmp_path / "no").exists()


@pytest.mark.parametrize("options", [{"release_version": "../bad"}, {"format": "csv"}])
def test_invalid_release_metadata(release_input, options):
    with pytest.raises(projection.ProjectionRefusal):
        projection.create_release([release_input.card], **({"release_version": "v0.1.0"} | options))
