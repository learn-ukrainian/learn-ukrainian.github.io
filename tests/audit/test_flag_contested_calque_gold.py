from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.audit.flag_contested_calque_gold import process_fixture


@pytest.fixture
def temp_db_paths(tmp_path: Path) -> tuple[Path, Path]:
    vesum_db = tmp_path / "vesum.db"
    sources_db = tmp_path / "sources.db"

    # Set up vesum.db
    conn_v = sqlite3.connect(str(vesum_db))
    conn_v.execute(
        """
        CREATE TABLE forms (
            word_form TEXT,
            lemma TEXT,
            pos TEXT,
            tags TEXT
        )
        """
    )
    # 1. 'уверх': non-archaic
    conn_v.execute(
        "INSERT INTO forms VALUES (?, ?, ?, ?)",
        ("уверх", "уверх", "adv", "adv"),
    )
    # 2. 'запрокинув': none (unattested in vesum)
    # 3. 'старий_арх': archaic only
    conn_v.execute(
        "INSERT INTO forms VALUES (?, ?, ?, ?)",
        ("старий_арх", "старий", "adj", "adj:arch"),
    )
    # 4. 'вішалкою': non-archaic, maps to lemma 'вішалка'
    conn_v.execute(
        "INSERT INTO forms VALUES (?, ?, ?, ?)",
        ("вішалкою", "вішалка", "noun", "noun:inanim:f:v_oru"),
    )
    conn_v.commit()
    conn_v.close()

    # Set up sources.db
    conn_s = sqlite3.connect(str(sources_db))
    conn_s.execute(
        """
        CREATE TABLE grinchenko (
            word TEXT,
            definition TEXT
        )
        """
    )
    conn_s.execute(
        """
        CREATE TABLE esum_etymology_meta (
            lemma TEXT,
            etymology_text TEXT,
            cognates TEXT,
            vol INT,
            page INT,
            source TEXT
        )
        """
    )
    try:
        conn_s.execute(
            """
            CREATE VIRTUAL TABLE esum_etymology USING fts5(
                lemma,
                etymology_text,
                cognates,
                vol,
                page
            )
            """
        )
    except sqlite3.OperationalError:
        # Fallback to standard table if FTS5 is not supported in the test environment
        conn_s.execute(
            """
            CREATE TABLE esum_etymology (
                lemma TEXT,
                etymology_text TEXT,
                cognates TEXT,
                vol INT,
                page INT
            )
            """
        )

    # Insert heritage data
    # 'уверх' has ESUM etymology FTS match
    conn_s.execute(
        "INSERT INTO esum_etymology (lemma, etymology_text, cognates, vol, page) VALUES (?, ?, ?, ?, ?)",
        ("повзти", "лазить по деревах уверх і вниз", "", 1, 10),
    )
    # 'вішалка' has ESUM FTS match
    conn_s.execute(
        "INSERT INTO esum_etymology (lemma, etymology_text, cognates, vol, page) VALUES (?, ?, ?, ?, ?)",
        ("шараги", "стояча вішалка", "", 1, 20),
    )
    # 'старий_арх' has grinchenko attestation but is archaic in vesum
    conn_s.execute(
        "INSERT INTO grinchenko VALUES (?, ?)",
        ("старий", "old definition"),
    )

    conn_s.commit()
    conn_s.close()

    return vesum_db, sources_db


@pytest.fixture
def mock_gold_fixture(tmp_path: Path) -> Path:
    fixture_file = tmp_path / "ua-gec-gold.json"
    data = {
        "items": [
            {
                "id": "ua-gec-gold-001",
                "tag": "F/Calque",
                "error": "уверх",
                "correction": "вгору",
            },
            {
                "id": "ua-gec-gold-002",
                "tag": "F/Calque",
                "error": "запрокинув",
                "correction": "закинув",
            },
            {
                "id": "ua-gec-gold-003",
                "tag": "F/Calque",
                "error": "старий_арх",
                "correction": "давній",
            },
            {
                "id": "ua-gec-gold-004",
                "tag": "F/Calque",
                "error": "вішалкою",
                "correction": "вішаком",
            },
            {
                "id": "ua-gec-gold-005",
                "tag": "G/Case",
                "error": "інший_тег",
                "correction": "інший",
            },
        ]
    }
    fixture_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return fixture_file


def test_flag_contested_calque_gold(
    temp_db_paths: tuple[Path, Path],
    mock_gold_fixture: Path,
) -> None:
    vesum_db, sources_db = temp_db_paths

    # Record initial state of the gold fixture
    initial_gold_bytes = mock_gold_fixture.read_bytes()

    # Process fixture to get sidecar dict
    sidecar = process_fixture(mock_gold_fixture, vesum_db, sources_db)

    # 1. Attested-native form -> contested
    # 'уверх' is attested in VESUM (non-archaic) and ESUM FTS -> contested=True
    assert sidecar["ua-gec-gold-001"]["contested"] is True
    assert len(sidecar["ua-gec-gold-001"]["evidence"]) > 0
    assert sidecar["ua-gec-gold-001"]["evidence"][0]["table"] == "esum"

    # 'вішалкою' is attested in VESUM (non-archaic via lemma 'вішалка') and ESUM -> contested=True
    assert sidecar["ua-gec-gold-004"]["contested"] is True

    # 2. Unattested form -> not contested
    # 'запрокинув' is not in VESUM -> contested=False
    assert sidecar["ua-gec-gold-002"]["contested"] is False
    assert sidecar["ua-gec-gold-002"]["evidence"] == []

    # 'старий_арх' has only archaic tags in VESUM -> contested=False
    assert sidecar["ua-gec-gold-003"]["contested"] is False

    # 'інший_тег' tag is G/Case, not F/Calque -> contested=False
    assert sidecar["ua-gec-gold-005"]["contested"] is False

    # 3. Gold file remains byte-unchanged
    assert mock_gold_fixture.read_bytes() == initial_gold_bytes


def test_sidecar_idempotency(
    temp_db_paths: tuple[Path, Path],
    mock_gold_fixture: Path,
    tmp_path: Path,
) -> None:
    vesum_db, sources_db = temp_db_paths
    output1 = tmp_path / "sidecar1.json"
    output2 = tmp_path / "sidecar2.json"

    # Run 1
    sidecar1 = process_fixture(mock_gold_fixture, vesum_db, sources_db)
    with open(output1, "w", encoding="utf-8") as f:
        json.dump(sidecar1, f, sort_keys=True, indent=2)

    # Run 2
    sidecar2 = process_fixture(mock_gold_fixture, vesum_db, sources_db)
    with open(output2, "w", encoding="utf-8") as f:
        json.dump(sidecar2, f, sort_keys=True, indent=2)

    # Byte-identical verification
    assert output1.read_bytes() == output2.read_bytes()
