import json
import sqlite3

from scripts.etymology.extract_cognate_forms import extract_database, extract_forms_from_text

KNOWN_ENTRIES = [
    (
        "дім",
        ["р.", "бр.", "п.", "ч.", "псл.", "іє."],
        "дім; — р. бр. дом, п. dom, ч. dum; — псл. *domъ; іє. *dem- «будувати».",
        {"р.": "дом", "бр.": "дом", "п.": "dom", "ч.": "dum", "псл.": "*domъ", "іє.": "*dem-"},
        "*domъ",
    ),
    (
        "мати",
        ["р.", "бр.", "п.", "ч."],
        "мати;—р. заст. имать, бр. [імаць], п. miec, ч. miti.",
        {"р.": "имать", "бр.": "імаць", "п.": "miec", "ч.": "miti"},
        None,
    ),
    (
        "серце",
        ["р.", "п.", "ч.", "псл."],
        "серце; — р. сердце, п. serce, ч. srdce; — псл. *sьrdьce.",
        {"р.": "сердце", "п.": "serce", "ч.": "srdce", "псл.": "*sьrdьce"},
        "*sьrdьce",
    ),
    (
        "абажур",
        ["р.", "бр.", "болг.", "п.", "ч."],
        "абажур; — р. бр. болг. абажур, п. abazur, ч. abazur.",
        {"р.": "абажур", "бр.": "абажур", "болг.": "абажур", "п.": "abazur", "ч.": "abazur"},
        None,
    ),
    (
        "аби",
        ["др.", "п.", "слц.", "ч.", "стел."],
        "аби;— др. аби, п. слц. aby, ч. aby, стел. дбы.",
        {"др.": "аби", "п.": "aby", "слц.": "aby", "ч.": "aby", "стел.": "дбы"},
        "дбы",
    ),
]


def _make_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE esum_etymology_meta (
            id INTEGER PRIMARY KEY,
            lemma TEXT NOT NULL,
            vol INTEGER NOT NULL,
            page INTEGER NOT NULL,
            entry_hash TEXT NOT NULL DEFAULT '',
            etymology_text TEXT NOT NULL,
            cognates TEXT NOT NULL DEFAULT '[]',
            source TEXT NOT NULL DEFAULT 'ЕСУМ',
            UNIQUE(lemma, vol, page, entry_hash)
        );
        """
    )
    for idx, (lemma, markers, text, _expected, _proto) in enumerate(KNOWN_ENTRIES, start=1):
        conn.execute(
            """
            INSERT INTO esum_etymology_meta (id, lemma, vol, page, entry_hash, etymology_text, cognates)
            VALUES (?, ?, 1, ?, ?, ?, ?)
            """,
            (idx, lemma, idx, f"hash-{idx}", text, json.dumps(markers, ensure_ascii=False)),
        )
    conn.commit()
    conn.close()


def test_extract_cognates_matches_known_entries():
    for _lemma, markers, text, expected, expected_proto in KNOWN_ENTRIES:
        forms, proto = extract_forms_from_text(text, markers)

        assert forms == expected
        assert proto == expected_proto


def test_database_extraction_writes_telemetry_shape(tmp_path):
    db_path = tmp_path / "sources.db"
    telemetry_path = tmp_path / "coverage.json"
    _make_db(db_path)

    telemetry = extract_database(db_path, telemetry_path)

    assert telemetry["entries_processed"] == 5
    assert telemetry["entries_with_at_least_one_form"] == 5
    assert telemetry["total_forms_extracted"] == 24
    assert telemetry["coverage_pct"] == 100.0
    assert telemetry["per_marker_coverage"]["р."] == {"expected": 4, "extracted": 4, "pct": 100.0}
    assert json.loads(telemetry_path.read_text(encoding="utf-8")) == telemetry


def test_database_extraction_is_idempotent(tmp_path):
    db_path = tmp_path / "sources.db"
    telemetry_path = tmp_path / "coverage.json"
    _make_db(db_path)

    first = extract_database(db_path, telemetry_path)
    second = extract_database(db_path, telemetry_path)

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT entry_id, cognate_forms, proto_form, extracted_count, expected_count FROM esum_cognate_forms ORDER BY entry_id"
    ).fetchall()
    conn.close()
    assert first == second
    assert len(rows) == 5
    assert rows[0][3] == 6
