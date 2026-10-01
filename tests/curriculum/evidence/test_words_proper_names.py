"""Captured proper-name regression; adversarial identities are synthetic mutations."""

import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence import sources, verify, words
from scripts.verification import stress

CAPTURE = json.loads((Path(__file__).parents[2] / "fixtures/stress/proper-names.json").read_text())


@pytest.fixture
def proper_name_sources(synthetic_sources, synthetic_vesum, monkeypatch):
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("DELETE FROM ulif_dictua_entries")
        conn.execute("DELETE FROM ulif_dictua_sections")
        entry = CAPTURE["entry"]
        columns = [row[1] for row in conn.execute("PRAGMA table_info(ulif_dictua_entries)")]
        conn.execute(
            f"INSERT INTO ulif_dictua_entries VALUES ({','.join('?' for _ in columns)})",
            [entry[key] for key in columns],
        )
        for section in entry["sections"]:
            columns = [row[1] for row in conn.execute("PRAGMA table_info(ulif_dictua_sections)")]
            conn.execute(
                f"INSERT INTO ulif_dictua_sections VALUES ({','.join('?' for _ in columns)})",
                [section[key] for key in columns],
            )
        for table, rows in [("ulif_forms_build", [CAPTURE["build"]]), ("ulif_forms", CAPTURE["ulif_forms"])]:
            columns = list(rows[0])
            if table == "ulif_forms":
                columns = columns[: columns.index("normalized_query")]
            conn.execute(f"CREATE TABLE {table} ({','.join(columns)})")
            conn.executemany(
                f"INSERT INTO {table} VALUES ({','.join('?' for _ in columns)})",
                [[row[key] for key in columns] for row in rows],
            )
    with sqlite3.connect(synthetic_vesum) as conn:
        conn.execute("DELETE FROM forms_all")
        conn.execute("DELETE FROM form_markers")
        for index, row in enumerate(CAPTURE["vesum_forms"], 1):
            conn.execute(
                "INSERT INTO forms_all VALUES (?,?,?,?,?,?,?,?)",
                [index]
                + [
                    row[key]
                    for key in ("entry_id", "word_form", "lemma", "pos", "tags", "source_comment", "source_location")
                ],
            )

    def analyses(form):
        with sqlite3.connect(synthetic_vesum) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute("SELECT * FROM forms_all WHERE word_form=?", (form,))]

    monkeypatch.setattr(stress, "_vesum_lookup", analyses)
    monkeypatch.setattr(stress, "_load_trie", lambda: {})
    return synthetic_sources, synthetic_vesum


def test_ulif_group_uses_oracle_normalization_and_preserves_caller_keys(proper_name_sources, monkeypatch):
    source_db, vesum_db = proper_name_sources
    monkeypatch.setattr(sources, "BATCH_SIZE", 1)
    with sources.Sources(sources_db=source_db, vesum_db=vesum_db) as api:
        result = api.ulif_entries(["Ніна", "ніна", "НІНА", "Ніна", "відсутня"])
        assert list(result.raw) == ["Ніна", "ніна", "НІНА", "відсутня"]
        assert result.raw["Ніна"] == result.raw["ніна"] == result.raw["НІНА"]
        assert result.raw["Ніна"][0]["canonical_headword"] == CAPTURE["entry"]["canonical_headword"]
        assert result.raw["Ніна"][0]["sections"] == CAPTURE["entry"]["sections"]
        assert api.ulif_group_checked(result.raw["Ніна"])
        assert result.raw["відсутня"] == []
        assert result.content_hash == sources.batch_digest(result.raw)


@pytest.mark.parametrize("identity", ["proper", "different_pos", "common_noun", "common_request"])
def test_builder_and_verifier_preserve_name_identity(proper_name_sources, tmp_path, identity):
    source_db, vesum_db = proper_name_sources
    lemma = "Ніна"
    # These deliberately mismatched source rows test the identity guard, not
    # attestation of a common word with this spelling.
    if identity in {"different_pos", "common_noun"}:
        with sqlite3.connect(source_db) as conn:
            label = "дієслово" if identity == "different_pos" else "іменник жіночого роду, істота"
            conn.execute("UPDATE ulif_dictua_entries SET canonical_headword='ні́на', grammatical_label=?", (label,))
            if identity == "different_pos":
                conn.execute('UPDATE ulif_forms SET grammatical_tags=\'["verb", "inf"]\'')
    elif identity == "common_request":
        lemma = "ніна"
        with sqlite3.connect(vesum_db) as conn:
            for row_id, form, tags in conn.execute("SELECT id, word_form, tags FROM forms_all").fetchall():
                conn.execute(
                    "UPDATE forms_all SET word_form=?, lemma=?, tags=? WHERE id=?",
                    (form.lower(), lemma, tags.replace(":prop:fname", ""), row_id),
                )

    request = tmp_path / "request.yaml"
    request.write_text(
        yaml.safe_dump({"request_schema": 1, "level": "a1", "words": [{"lemma": lemma, "pos": "noun", "want": "new"}]})
    )
    with sources.Sources(sources_db=source_db, vesum_db=vesum_db) as api:
        built = words.build_words("a1", request, evidence_dir=tmp_path, sources_instance=api)
    word = built["store"]["words"][0]
    if identity == "proper":
        assert next(form for form in word["forms"] if form["form"] == "Ніні")["stressed"] == "Ні́ні"
        assert all(form["stress_source"] == "ulif" for form in word["forms"] if not words.needs_no_stress(form["form"]))
    else:
        assert all(
            form["stress_source"] == "pending" and "stressed" not in form
            for form in word["forms"]
            if not words.needs_no_stress(form["form"])
        )
    with sources.Sources(sources_db=source_db, vesum_db=vesum_db) as api:
        checked = verify.verify_words_store("a1", evidence_dir=tmp_path, sources_instance=api)
    assert checked["errors"] == []
    assert checked["status"] == "ok"
