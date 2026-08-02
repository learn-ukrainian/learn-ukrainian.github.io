"""Tests for textbook end-dictionary classifier and parsers (#6188)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.practice_deck.end_dictionaries import (
    SCHEMA,
    EndDictionaryEntry,
    EndDictionarySection,
    build_inventory_payload,
    classify_section_title,
    coverage_intersection_report,
    enumerate_end_dictionary_sections,
    infer_layout,
    parse_academic_gloss,
    parse_gloss_emdash,
    parse_section_entries,
    parse_word_list,
    read_end_dictionary_stress_overlay,
    stress_overlay_from_entries,
)


def test_classify_section_title_dominant_kinds() -> None:
    assert classify_section_title("Короткий словник наголосів")[0] == "stress"
    assert classify_section_title("КОРОТКИЙ СЛОВНИК ФРАЗЕОЛОГІЗМІВ")[0] == "phraseology"
    assert (
        classify_section_title("Короткий словник колоритної української лексики")[0]
        == "color_lexicon"
    )
    assert classify_section_title("З тлумачного словника")[0] == "gloss"
    assert classify_section_title("ТЛУМАЧНИЙ СЛОВНИК")[0] == "gloss"
    assert classify_section_title("Додаток 2. СЛОВНИЧОК ПАРОНІМІВ")[0] == "paronym"
    # Lesson prose about dictionaries must not classify as end-glossary.
    assert classify_section_title("§ 14. Орфоепічна помилка. Орфоепічний словник") is None


def test_infer_layout_forces_academic_morph_for_z_tlumachnoho() -> None:
    layout = infer_layout(
        "gloss",
        "ратай, ратая, ч. Плугатар. румак, -а, ч. Кінь.",
        section_title="З тлумачного словника",
    )
    assert layout == "academic_morph"


def test_parse_word_list_stress_and_color() -> None:
    text = """
202
КОРОТКИЙ СЛОВНИК НАГОЛОСІВ
А
агрономія
алкоголь
Б
багаторазовий
вигода (користь)
гальмо, гальма
•\tЗа тлумачним словником з’ясуйте значення
базіка
"""
    rows = parse_word_list(text)
    plains = [plain for plain, _ in rows]
    assert "агрономія" in plains
    assert "алкоголь" in plains
    assert "багаторазовий" in plains
    assert "вигода" in plains
    assert "гальмо" in plains
    assert "базіка" in plains
    assert all(stress is None for _, stress in rows)


def test_parse_word_list_keeps_combining_acute() -> None:
    rows = parse_word_list("катало́г\nкіломе́тр\n")
    by_plain = dict(rows)
    assert by_plain["каталог"] == "катало́г"
    assert by_plain["кілометр"] == "кіломе́тр"


def test_parse_gloss_emdash_and_phraseology() -> None:
    text = """
КОРОТКИЙ СЛОВНИК ФРАЗЕОЛОГІЗМІВ
Бачити наскрізь — уміти розпізнавати чиї-небудь думки.
Байрак — ліс у яру.
"""
    rows = parse_gloss_emdash(text)
    by_plain = {plain: (gloss, multi) for plain, _, gloss, multi in rows}
    assert by_plain["бачити наскрізь"][1] is True
    assert "розпізнавати" in by_plain["бачити наскрізь"][0]
    assert by_plain["байрак"][1] is False


def test_parse_academic_simple_voron_style() -> None:
    text = """
ТЛУМАЧНИЙ СЛОВНИК
Абрис. Обриси предмета, контур.
Авангардний. Передовий.
Альтанка. Покрита зверху легка будівля в саду.
"""
    rows = parse_academic_gloss(text, style="simple")
    plains = [plain for plain, *_ in rows]
    assert "абрис" in plains
    assert "авангардний" in plains
    assert "альтанка" in plains


def test_parse_academic_morph_precision() -> None:
    text = """
З тлумачного словника
розпірка, -и, ж. Розріз в одязі, зроблений відповідно до його крою.
румак, -а, ч. Старовинна назва породистого верхового коня.
"""
    rows = parse_academic_gloss(text, style="morph")
    by_plain = {plain: gloss for plain, _, gloss, _ in rows}
    assert "розпірка" in by_plain
    assert "румак" in by_plain
    assert "перен" not in by_plain


def test_stress_overlay_requires_combining_acute() -> None:
    entries = [
        EndDictionaryEntry(
            lemma_plain="каталог",
            stress="катало́г",
            section_id=1,
            grade=10,
            source_file="x",
            kind="stress",
            layout="stress_list",
            locator="textbook_sections:1",
        ),
        EndDictionaryEntry(
            lemma_plain="алфавіт",
            stress=None,
            section_id=1,
            grade=10,
            source_file="x",
            kind="stress",
            layout="stress_list",
            locator="textbook_sections:1",
        ),
    ]
    overlay = stress_overlay_from_entries(entries)
    assert overlay == {
        "каталог": {
            "form": "катало́г",
            "source": "textbook-end-dictionary:textbook_sections:1",
        }
    }


def test_enumerate_sections_from_sqlite(tmp_path: Path) -> None:
    db = tmp_path / "sources.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE textbook_sections (
            section_id INTEGER PRIMARY KEY,
            source_file TEXT,
            grade INTEGER,
            section_title TEXT,
            section_number TEXT,
            page_start INTEGER,
            page_end INTEGER,
            chunk_count INTEGER,
            full_text TEXT
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO textbook_sections(
            section_id, source_file, grade, section_title, page_start, page_end, full_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                "10-klas-ukrajinska-mova-avramenko-2018",
                10,
                "Короткий словник наголосів",
                203,
                204,
                "А\nагрономія\nалкоголь\n",
            ),
            (
                2,
                "5-klas-ukrmova-avramenko-2022",
                5,
                "ТЛУМАЧНИЙ СЛОВНИК",
                193,
                193,
                "Байрак — ліс у яру.\nБагва — болотисте місце.\n",
            ),
            (
                3,
                "10-klas-ukrmova-glazova-2018",
                10,
                "§ 14. Орфоепічна помилка. Орфоепічний словник",
                50,
                51,
                "lesson prose",
            ),
            (
                4,
                "11-klas-istoriya-ukr-galimov-2024",
                11,
                "Короткий словник наголосів",
                1,
                1,
                "ignored non-ukrmova",
            ),
        ],
    )
    conn.commit()
    sections = enumerate_end_dictionary_sections(conn)
    conn.close()
    assert {section.section_id for section in sections} == {1, 2}
    assert {section.kind for section in sections} == {"stress", "gloss"}


def test_parse_section_entries_round_trip() -> None:
    section = EndDictionarySection(
        section_id=10,
        grade=5,
        section_title="ТЛУМАЧНИЙ СЛОВНИК",
        source_file="5-klas-ukrmova-avramenko-2022",
        page_start=193,
        page_end=193,
        char_count=100,
        kind="gloss",
        layout="gloss_emdash",
        match_reason="title",
    )
    entries = parse_section_entries(section, "Байрак — ліс у яру.\n")
    assert len(entries) == 1
    assert entries[0].lemma_plain == "байрак"
    assert entries[0].locator == "textbook_sections:10"
    assert entries[0].gloss and "ліс" in entries[0].gloss


def test_inventory_payload_schema_and_cloze_policy() -> None:
    section = EndDictionarySection(
        section_id=1,
        grade=10,
        section_title="Короткий словник наголосів",
        source_file="x",
        page_start=1,
        page_end=1,
        char_count=10,
        kind="stress",
        layout="stress_list",
        match_reason="title",
    )
    entry = EndDictionaryEntry(
        lemma_plain="агрономія",
        section_id=1,
        grade=10,
        source_file="x",
        kind="stress",
        layout="stress_list",
        locator="textbook_sections:1",
    )
    payload = build_inventory_payload([section], [entry])
    assert payload["schema"] == SCHEMA
    assert payload["clozePolicy"]["fakeClozeFromDefinitions"] is False
    assert payload["counts"]["sections"] == 1
    assert payload["counts"]["entries"] == 1


def test_coverage_intersection_report_does_not_claim_cloze() -> None:
    report = coverage_intersection_report(
        {"A1": {"кіт", "собака", "стіл"}},
        {"A1": {"кіт"}},
        [{"lemmaPlain": "собака"}, {"lemmaPlain": "вікно"}],
    )
    assert report["levels"]["A1"]["residual"] == 2
    assert report["levels"]["A1"]["residualInEndDictionary"] == 1
    assert "do not unlock cloze" in report["note"]


def test_read_end_dictionary_stress_overlay(tmp_path: Path) -> None:
    path = tmp_path / "inventory.json"
    path.write_text(
        json.dumps(
            {
                "schema": SCHEMA,
                "schemaVersion": 1,
                "entries": [
                    {
                        "lemmaPlain": "каталог",
                        "stress": "катало́г",
                        "locator": "textbook_sections:9",
                    },
                    {"lemmaPlain": "алфавіт"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    overlay = read_end_dictionary_stress_overlay(path)
    assert overlay["каталог"]["form"] == "катало́г"
    assert "алфавіт" not in overlay
