import json
import sqlite3

from scripts.etymology.recover_latin_cognates import (
    recover_cognate_forms,
    recover_database,
    recover_latin,
    should_recover_marker,
)


def test_known_damaged_forms_recover_to_latin():
    assert recover_latin("зіегдгізку") == "sierdzisty"
    assert recover_latin("5гбей") == "srdce"
    assert recover_latin("5егрепіуп") == "serpentyn"
    assert recover_latin("8егрепіїп") == "serpentin"


def test_clean_latin_cases_stay_clean_or_improve_digit_noise():
    assert recover_latin("serce") == "serce"
    assert recover_latin("abazur") == "abazur"
    assert recover_latin("5cgemenetz") == "scgemenetz"


def test_marker_scope_avoids_cyrillic_script_cognates():
    forms = {
        "р.": "сердце",
        "бр.": "сэрца",
        "п.": "зіегдгізку",
        "ч.": "5гбей",
        "псл.": "*sьrdьce",
    }

    assert recover_cognate_forms(forms) == {"п.": "sierdzisty", "ч.": "srdce"}
    assert not should_recover_marker("р.")
    assert not should_recover_marker("псл.")
    assert should_recover_marker("ч. слц.")


def test_edge_cases():
    assert recover_latin("") == ""
    assert recover_latin("5") == "s"
    assert recover_latin("s") == "s"
    assert recover_latin("1234") == "1234"


def test_recover_database_adds_column_and_populates(tmp_path):
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE esum_cognate_forms (
            entry_id INTEGER PRIMARY KEY,
            cognate_forms TEXT NOT NULL DEFAULT '{}',
            proto_form TEXT,
            extracted_count INTEGER NOT NULL DEFAULT 0,
            expected_count INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    conn.executemany(
        "INSERT INTO esum_cognate_forms (entry_id, cognate_forms, extracted_count, expected_count)"
        " VALUES (?, ?, ?, ?)",
        [
            (1, json.dumps({"п.": "5егрепіуп", "р.": "серпентин"}, ensure_ascii=False), 2, 2),
            (2, json.dumps({"р.": "сердце"}, ensure_ascii=False), 1, 1),
        ],
    )
    conn.commit()
    conn.close()

    stats = recover_database(db_path)

    conn = sqlite3.connect(db_path)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(esum_cognate_forms)")}
    rows = conn.execute(
        "SELECT entry_id, cognate_forms_recovered FROM esum_cognate_forms ORDER BY entry_id"
    ).fetchall()
    conn.close()

    assert "cognate_forms_recovered" in columns
    assert stats["entries_with_non_cyrillic_markers"] == 1
    assert stats["entries_with_recovered_latin"] == 1
    assert json.loads(rows[0][1]) == {"п.": "serpentyn"}
    assert json.loads(rows[1][1]) == {}
