"""C5 accept paths and semantic must-fail fixtures; SYNTHETIC rows only."""

import copy
import json
import sqlite3
from dataclasses import replace
from types import SimpleNamespace

import pytest

from scripts.projects.open_model_data.review_build import __main__ as cli
from scripts.projects.open_model_data.review_build import output
from scripts.projects.open_model_data.review_build.attribution import Resolver
from scripts.projects.open_model_data.review_build.build import prepare
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.components import ComponentContext, load_components
from scripts.projects.open_model_data.review_build.components.c5 import (
    COMPONENT,
    FROZEN_COUNT,
    OPERATION,
    SOURCE,
    TABLE,
    UNIT_QUERY,
    example_unit,
    primary_citation,
)
from scripts.projects.open_model_data.review_build.contract import digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.gate import Gate
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import catalog_data


@pytest.fixture
def source(tmp_path):
    db = tmp_path / "SYNTHETIC-sources.db"
    vesum = tmp_path / "SYNTHETIC-vesum.db"
    with sqlite3.connect(db) as writer:
        writer.execute(
            "CREATE TABLE pravopys_paragraphs(source_id TEXT, number INTEGER, text TEXT, "
            "locator TEXT, unresolved_hyphenations INTEGER, hyphen_alternatives TEXT, "
            "PRIMARY KEY(source_id,number))"
        )
        writer.execute("CREATE TABLE pravopys_sources(source_id TEXT PRIMARY KEY, citation TEXT)")
        writer.execute("INSERT INTO pravopys_sources VALUES(?,?)", (SOURCE, "SYNTHETIC bibliography"))
        for number in range(1, 13):
            writer.execute(
                "INSERT INTO pravopys_paragraphs VALUES(?,?,?,?,?,?)",
                (
                    SOURCE,
                    number,
                    f"SYNTHETIC rule {number} examples: TOKEN{number}a, TOKEN{number}b.",
                    f"SYNTHETIC paragraph {number}",
                    0,
                    "[]",
                ),
            )
    with sqlite3.connect(vesum) as writer:
        writer.execute("CREATE TABLE forms_all(id INTEGER PRIMARY KEY, word_form TEXT, word_form_folded TEXT)")
        writer.execute("INSERT INTO forms_all VALUES(1, 'SYNTHETICmore', 'syntheticmore')")
    register = {
        "sources": [
            {
                "id": SOURCE,
                "citation": {"form": "SYNTHETIC bibliography"},
                "terms": {"licence": {"name": "SYNTHETIC licence"}},
            }
        ]
    }
    compatibility = [
        {
            "store": "sources.db",
            "table": TABLE,
            "source_id": SOURCE,
            "role": "modern",
            "source_column": "source_id",
            "source_values": [SOURCE],
        }
    ]
    catalog = catalog_data("C5", OPERATION)
    for line in catalog["components"]["C5"]["instructions"]:
        line["template"] = line["template"].replace("{sentence}", "{example}")
        line["slots"] = ["example"]
    return {
        "db": db,
        "vesum": vesum,
        "register": register,
        "compatibility": compatibility,
        "catalog": catalog,
    }


def gate_and_candidates(source, reader):
    spec = copy.deepcopy(COMPONENT.spec)
    spec["operation_specs"][OPERATION]["frozen_count"] = len(reader.units(UNIT_QUERY))
    gate = Gate(
        reader,
        Catalog(source["catalog"]),
        Resolver(source["register"], COMPONENT.adapters),
        {"C5": spec},
        source["compatibility"],
    )
    return gate, list(COMPONENT.iter_candidates(ComponentContext(reader, {}))), spec


def reader_for(source):
    return SnapshotReader({"sources.db": source["db"], "vesum.db": source["vesum"]})


def update(source, **fields):
    with sqlite3.connect(source["db"]) as writer:
        writer.execute(
            "UPDATE pravopys_paragraphs SET " + ",".join(k + "=?" for k in fields) + " WHERE number=1",
            tuple(fields.values()),
        )


def test_registry_and_independent_span_accounting(source):
    assert load_components(["C5"])["C5"] is COMPONENT
    assert COMPONENT.spec["operation_specs"][OPERATION]["frozen_count"] == FROZEN_COUNT == 11926
    with reader_for(source) as reader:
        gate, candidates, _ = gate_and_candidates(source, reader)
        assert sorted(c.unit_id for c in candidates) == reader.units(UNIT_QUERY)
        records, report = gate.run(candidates)
        assert len(records) == 24
        assert report["accounting"]["C5"] == {
            "counted": 24,
            "accepted": 24,
            "rejected": 0,
            "withheld": 0,
            "excluded": 0,
            "reasons": {"ok": 24},
        }
        assert report["metrics"]["C5." + OPERATION]["status"] == "PASS"
        for candidate in candidates:
            assert candidate.response[0].span is None
            row = reader.row(candidate.slots[0].citations[0])
            assert candidate.response[0].text == row["text"]
            assert candidate.response[1].text == row["locator"]
            assert gate.unit_id(candidate) == example_unit(primary_citation(row), candidate.slots[0].span)


@pytest.mark.parametrize(
    "mutation,error",
    [
        ("wrong_paragraph", "binding_row"),
        ("outside_list", "binding_example"),
        ("fragment_target", "binding_whole_field"),
        ("absent_quote", "quote_mismatch"),
        ("wrong_span", "quote_mismatch"),
        ("empty_locator", "empty_locator"),
        ("paraphrasing", "unknown_transform"),
        ("missing_unit", "missing_unit"),
        ("invented_locator", "binding_locator"),
        ("wrong_target_field", "binding_field"),
    ],
)
def test_must_fail_c5_gate(source, mutation, error):
    with reader_for(source) as reader:
        gate, candidates, _ = gate_and_candidates(source, reader)
        first = candidates[0]
        value = first.slots[0]
        if mutation == "wrong_paragraph":
            candidates[0] = replace(first, response=candidates[2].response)
        elif mutation == "outside_list":
            row = reader.row(value.citations[0])
            span = (0, len("SYNTHETIC"))
            candidates[0] = replace(first, slots=(replace(value, text=row["text"][slice(*span)], span=span),))
            # Retain the denominator identity for this direct semantic binding test.
            with pytest.raises(BuildError, match=error):
                from scripts.projects.open_model_data.review_build.bindings import check

                check(candidates[0], gate.spec(first)["binding"], reader, {})
            return
        elif mutation == "fragment_target":
            target = first.response[0]
            candidates[0] = replace(
                first, response=(replace(target, text=target.text[:9], span=(0, 9)), first.response[1])
            )
        elif mutation == "absent_quote":
            candidates[0] = replace(first, slots=(replace(value, text="SYNTHETIC absent"),))
        elif mutation == "wrong_span":
            target = first.response[0]
            candidates[0] = replace(first, response=(replace(target, span=(1, len(target.text))), first.response[1]))
        elif mutation == "empty_locator":
            candidates[0] = replace(
                first, slots=(replace(value, citations=(replace(value.citations[0], locator=""),)),)
            )
        elif mutation == "invented_locator":
            candidates[0] = replace(
                first, slots=(replace(value, citations=(replace(value.citations[0], locator="SYNTHETIC invented"),)),)
            )
        elif mutation == "wrong_target_field":
            target = first.response[0]
            row = reader.row(target.citations[0])
            swapped = primary_citation(row, "locator")
            candidates[0] = replace(
                first,
                response=(
                    replace(target, text=row["locator"], citations=(swapped,), transform="verbatim"),
                    first.response[1],
                ),
            )
        elif mutation == "paraphrasing":
            candidates[0] = replace(
                first, response=(replace(first.response[0], transform="synthetic_paraphrase"), first.response[1])
            )
        else:
            candidates.pop()
        with pytest.raises(BuildError, match=error):
            gate.run(candidates)


@pytest.mark.parametrize(
    "fields,reason",
    [
        (
            {"unresolved_hyphenations": 1, "hyphen_alternatives": '["SYNTHETIC alternate"]'},
            "paragraph_hyphenation_unresolved",
        ),
        ({"hyphen_alternatives": "invalid"}, "hyphen_metadata_unavailable"),
        ({"hyphen_alternatives": "{}"}, "hyphen_metadata_unavailable"),
        ({"hyphen_alternatives": "[1]", "unresolved_hyphenations": 1}, "hyphen_metadata_unavailable"),
        ({"unresolved_hyphenations": 1}, "hyphen_metadata_unavailable"),
        ({"hyphen_alternatives": " []"}, "hyphen_metadata_unavailable"),
        ({"text": "SYNTHETIC rule UNKNOWN-\nmore examples: FIRST, SECOND."}, "paragraph_hyphenation_unresolved"),
    ],
)
def test_ambiguous_hyphenation_is_withheld(source, fields, reason):
    update(source, **fields)
    with reader_for(source) as reader:
        gate, candidates, _ = gate_and_candidates(source, reader)
        withheld = [c for c in candidates if c.outcome == "withheld"]
        assert len(withheld) == 2
        assert {c.reason for c in withheld} == {reason}
        assert all(c.evidence for c in withheld)
        assert gate.run(candidates)[1]["accounting"]["C5"]["withheld"] == 2


def test_attested_dehyphenation_of_complete_paragraph(source):
    update(source, text="SYNTHETIC-\nmore rule examples: FIRST, SECOND.")
    with reader_for(source) as reader:
        gate, candidates, _ = gate_and_candidates(source, reader)
        first = candidates[0]
        assert first.outcome == "accepted"
        assert first.response[0].transform == "dehyphenate@2"
        assert first.response[0].text == "SYNTHETICmore rule examples: FIRST, SECOND."
        records, _ = gate.run(candidates)
        assert any(p["joins"] for r in records for p in r["provenance"].values())


def test_split_example_retains_raw_identity_and_resolves_target(source):
    update(source, text="SYNTHETIC examples: SYNTHETIC-\nmore, SECOND.")
    with reader_for(source) as reader:
        gate, candidates, _ = gate_and_candidates(source, reader)
        assert candidates[0].outcome == "accepted"
        assert candidates[0].slots[0].text == "SYNTHETIC-\nmore"
        assert candidates[0].response[0].text == "SYNTHETIC examples: SYNTHETICmore, SECOND."
        assert candidates[1].outcome == "accepted"
        assert gate.run(candidates)[1]["accounting"]["C5"]["withheld"] == 0


@pytest.mark.parametrize("case,error", [("metadata", "binding_hyphenation"), ("unattested", "binding_hyphenation")])
def test_forced_ambiguous_hyphen_acceptance_fails(source, case, error):
    if case == "metadata":
        update(source, unresolved_hyphenations=1, hyphen_alternatives='["SYNTHETIC alternate"]')
    else:
        update(source, text="SYNTHETIC unknown-\nmore examples: FIRST, SECOND.")
    with reader_for(source) as reader:
        gate, candidates, _ = gate_and_candidates(source, reader)
        candidates[0] = replace(candidates[0], outcome="accepted", reason="ok", evidence=())
        with pytest.raises(BuildError, match=error):
            gate.run(candidates)


@pytest.mark.parametrize("failure", ["missing_register", "placeholder", "unmapped_form", "missing_metadata"])
def test_unresolved_attribution_withholds_and_authenticates_metadata(source, failure):
    if failure == "missing_register":
        source["register"]["sources"] = []
    elif failure in {"placeholder", "unmapped_form"}:
        source["register"]["sources"][0]["citation"]["form"] = (
            "<SYNTHETIC placeholder>" if failure == "placeholder" else "SYNTHETIC unmapped"
        )
    else:
        with sqlite3.connect(source["db"]) as writer:
            writer.execute("DELETE FROM pravopys_sources")
    with reader_for(source) as reader:
        gate, candidates, _ = gate_and_candidates(source, reader)
        effective = prepare(candidates, gate)
        assert {c.reason for c in effective} == {"attribution_unresolved"}
        assert gate.run(effective)[1]["accounting"]["C5"]["withheld"] == 24


def test_reasoning_and_source_digest_fail(source):
    update(source, text="SYNTHETIC Reasoning: FIRST, SECOND.")
    with reader_for(source) as reader:
        gate, candidates, _ = gate_and_candidates(source, reader)
        with pytest.raises(BuildError, match="reasoning_text"):
            gate.run(candidates)
        first = candidates[0]
        bad = replace(first.slots[0].citations[0], field_sha256=digest(b"SYNTHETIC wrong"))
        candidates[0] = replace(first, slots=(replace(first.slots[0], citations=(bad,)),))
        with pytest.raises(BuildError, match="field_digest"):
            gate.run(candidates)


def test_synthetic_cli_build_verify_and_real_mutation_generation(source, tmp_path, monkeypatch, capsys):
    import yaml

    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    with reader_for(source) as reader:
        _, _, spec = gate_and_candidates(source, reader)
    (tmp_path / "catalog.yaml").write_text(yaml.safe_dump(source["catalog"]))
    (tmp_path / "register.yaml").write_text(yaml.safe_dump(source["register"]))
    config = {
        "schema": "omd-review-request.v1",
        "catalog": "catalog.yaml",
        "register": "register.yaml",
        "components": {"C5": {}},
        "databases": {"sources.db": str(source["db"]), "vesum.db": str(source["vesum"])},
        "compatibility": source["compatibility"],
    }
    path = tmp_path / "request.json"
    path.write_text(json.dumps(config))
    component = SimpleNamespace(
        spec=spec, adapters=COMPONENT.adapters, files={}, iter_candidates=COMPONENT.iter_candidates
    )
    out = tmp_path / "SYNTHETIC-output"
    args = ["--config", str(path), "--out", str(out), "--components", "C5"]
    for action in ("build", "verify"):
        assert cli.main([action, *args], _test_components={"C5": component}) == 0
        assert json.loads(capsys.readouterr().out)["status"] == ("built" if action == "build" else "verified")
    mutations = json.loads((out / "mutation-fixtures/results.json").read_bytes())
    assert len(mutations) == 5


def test_per_hyphen_resolution_withholds_only_remaining_ambiguity(source):
    update(
        source,
        text="SYNTHETIC rule SYNTHETIC-\nmore and unknown-\nmore examples: FIRST, SECOND.",
        unresolved_hyphenations=2,
        hyphen_alternatives='["SYNTHETIC-more", "unknown-more"]',
    )
    with reader_for(source) as reader:
        gate, candidates, _ = gate_and_candidates(source, reader)
        assert {c.reason for c in candidates[:2]} == {"paragraph_hyphenation_unresolved"}
        assert "SYNTHETICmore" in candidates[0].response[0].text
        assert gate.run(candidates)[1]["accounting"]["C5"]["withheld"] == 2


def test_source_text_defect_withholding_cannot_be_forced_through_gate(source):
    update(source, text="SYNTHETIC rule ALPHABETA examples: FIRST, SECOND.")
    with sqlite3.connect(source["db"]) as writer:
        writer.execute(
            "UPDATE pravopys_paragraphs SET text='SYNTHETIC rule ALPHA and BETA examples: THIRD, FOURTH.' WHERE number=2"
        )
    with sqlite3.connect(source["vesum"]) as writer:
        writer.executemany("INSERT INTO forms_all VALUES(?,?,?)", [(2, "ALPHA", "alpha"), (3, "BETA", "beta")])
    with reader_for(source) as reader:
        gate, candidates, _ = gate_and_candidates(source, reader)
        assert candidates[0].reason == "source_text_defect"
        assert gate.run(candidates)[1]["accounting"]["C5"]["withheld"] == 2
        candidates[0] = replace(candidates[0], outcome="accepted", reason="ok", evidence=())
        with pytest.raises(BuildError, match="binding_source_text_defect"):
            gate.run(candidates)


def test_v2_provenance_has_evidence_kind_and_pins_text_witness(source):
    update(
        source,
        text="SYNTHETIC rule ZETA-\nmore examples: FIRST, SECOND.",
        unresolved_hyphenations=1,
        hyphen_alternatives='["ZETA-more"]',
    )
    with sqlite3.connect(source["db"]) as writer:
        writer.execute(
            "UPDATE pravopys_paragraphs SET text='SYNTHETIC ZETAmore examples: THIRD, FOURTH.' WHERE number=2"
        )
    with reader_for(source) as reader:
        gate, candidates, _ = gate_and_candidates(source, reader)
        records, _ = gate.run(candidates)
        evidence = [e for r in records for p in r["provenance"].values() for e in p.get("join_evidence", [])]
        assert evidence and {e[3] for e in evidence} == {"held_text"}
        assert any("field=text" in key for key, _ in reader.reads[("sources.db", TABLE)])
