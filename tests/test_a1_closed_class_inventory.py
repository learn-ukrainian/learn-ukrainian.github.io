"""Words-only PULS generation, combined spelling rows and class-specific lookup."""

import sqlite3

import pytest
import yaml

from scripts.audit.source_inventory_intake import read_source_inventory
from scripts.curriculum.validate.a1_reference import CLOSED_CLASS_PATH, _closed_class_from_bytes, closed_class_a1
from scripts.ingest.build_a1_closed_class import build_inventory, main


def all_rows(payload):
    return [r for s in payload["sources"] for r in s["headwords"]]


def database(path, rows):
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE puls_cefr (word TEXT, level TEXT, pos TEXT)")
        conn.executemany("INSERT INTO puls_cefr VALUES (?,?,?)", rows)
    return path


def test_generator_covers_a1_rows_and_comma_variants_read_only(tmp_path):
    path = database(tmp_path / "sources.db", [
        ("я", "A1", "займенник"), ("а", "A1", "сполучник"), ("а", "B2", "частка"),
        ("що", "A2", "сполучник"), ("не", "A1", "частка"), ("над", "A2", "прийменник"),
        ("з, із, зі", "A1", "прийменник"), ("кожний, кожен", "A1", "займенник"),
        ("і, й", "A1", "сполучник"), ("у, в", "A1", "прийменник"), ("ой", "A1", "вигук"),
        ("мама", "A1", "іменник"), ("я", "A1", "займенник"),
    ])
    before = path.read_bytes()
    payload = build_inventory(path)
    assert path.read_bytes() == before
    puls = {(r["lemma"], r["class"]) for r in all_rows(payload) if r["source"] == "PULS"}
    assert puls == {("я", "pron"), ("а", "conj"), ("не", "part"), ("з", "prep"), ("із", "prep"),
                    ("зі", "prep"), ("кожний", "pron"), ("кожен", "pron"),
                    ("і", "conj"), ("й", "conj"), ("у", "prep"), ("в", "prep")}
    assert all(r["source"] == "PULS" and "page" not in r for r in all_rows(payload))
    output = tmp_path / "result.yaml"
    assert main(["--db", str(path), "--output", str(output)]) == 0
    assert yaml.safe_load(output.read_text()) == payload


def test_generator_failures_do_not_create_database_or_output(tmp_path):
    missing = tmp_path / "missing.db"
    output = tmp_path / "result.yaml"
    assert main(["--db", str(missing), "--output", str(output)]) == 1
    assert not missing.exists() and not output.exists()
    path = database(tmp_path / "sources.db", [("word gloss", "A1", "частка")])
    assert main(["--db", str(path), "--output", str(output)]) == 1
    assert not output.exists()


def test_committed_words_only_closed_class_inventory():
    payload = yaml.safe_load(CLOSED_CLASS_PATH.read_text())
    assert len(all_rows(payload)) == 63
    members = closed_class_a1()
    assert len(members) == 63
    assert {("що", "pron"), ("а", "conj"), ("не", "part")} <= members
    assert not {("що", "conj"), ("а", "part"), ("над", "prep"), ("аби", "conj")} & members
    records = read_source_inventory(CLOSED_CLASS_PATH)
    for record, row in zip(records, all_rows(payload), strict=True):
        provenance = record.provenance_payload()
        assert record.pos == row["class"]
        assert {k: provenance[k] for k in ("class", "level", "source")} == {k: row[k] for k in ("class", "level", "source")}
        assert row["source"] == "PULS" and "page" not in provenance


@pytest.mark.parametrize("mutate", [
    lambda p: p.update(version=2), lambda p: p["sources"][0].update(headwords="invalid"), lambda p: p["sources"][0].update(headwords=[]),
    lambda p: p.update(extra="gloss"), lambda p: p["sources"][0]["headwords"][0].update(source="unknown"),
    lambda p: p["sources"][0]["headwords"][0].update(level="A2"), lambda p: p["sources"][0]["headwords"][0].update(lemma="English"),
    lambda p: p["sources"][0]["headwords"][0].update(lemma="не слово"), lambda p: p["sources"][0]["headwords"][0].update(gloss="word"),
    lambda p: p["sources"][0]["headwords"][0].update(**{"class": "intj"}),
    lambda p: p["sources"][0]["headwords"].append(dict(p["sources"][0]["headwords"][0])),
    lambda p: p["sources"][0]["headwords"].append({"lemma": "а", "class": "conj", "level": "A1", "source": "reference_units", "page": 47}),
    lambda p: p["sources"][0]["headwords"][0].update(page=40),
    lambda p: p["sources"][0]["headwords"][0].update(page=True),
    lambda p: p["sources"][0]["headwords"][0].update(page=47),
    lambda p: p["sources"][0]["headwords"][0].update(source=[]),
    lambda p: p["sources"].pop(),
])
def test_invalid_closed_class_data_fails_closed(mutate):
    payload = yaml.safe_load(CLOSED_CLASS_PATH.read_text())
    mutate(payload)
    with pytest.raises(ValueError):
        _closed_class_from_bytes(yaml.safe_dump(payload, allow_unicode=True).encode())


def test_closed_class_cache_tracks_exact_bytes(tmp_path):
    payload = yaml.safe_load(CLOSED_CLASS_PATH.read_text())
    path = tmp_path / "inventory.yaml"
    path.write_text(yaml.safe_dump(payload, allow_unicode=True))
    original = closed_class_a1(path)
    assert closed_class_a1(path) is original
    payload["sources"][0]["headwords"] = [r for r in payload["sources"][0]["headwords"] if r["lemma"] != "не"]
    path.write_text(yaml.safe_dump(payload, allow_unicode=True))
    assert ("не", "part") not in closed_class_a1(path) and ("не", "part") in original


def test_validator_data_is_not_discovered_by_atlas_census():
    from scripts.audit.atlas_intake_census import discover_inventory_paths

    assert CLOSED_CLASS_PATH not in discover_inventory_paths()
    assert CLOSED_CLASS_PATH.parent.name == "data"
