from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.practice_deck.markup_integrity import stem_requires_markup
from scripts.practice_deck.zno import (
    LEXICAL_NORM_LIVE_CANDIDATE_COUNT,
    LEXICAL_NORM_SQL,
    MORPHOLOGICAL_NORM_SQL,
    MORPHOLOGY_LIVE_CANDIDATE_COUNT,
    MORPHOLOGY_SQL,
    ORTHOGRAPHY_LIVE_CANDIDATE_COUNT,
    ORTHOGRAPHY_SQL,
    PARONYM_LIVE_CANDIDATE_COUNT,
    PHONETICS_SQL,
    SYNTACTIC_NORM_SQL,
    SYNTAX_SQL,
    build_zno_shards,
    learner_attribution,
    write_zno_fill_residual,
    write_zno_shards,
)


def _database(path: Path) -> Path:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE zno_documents (
            id INTEGER PRIMARY KEY, fetch_status TEXT NOT NULL, year INTEGER NOT NULL, text_layer TEXT NOT NULL
        );
        CREATE TABLE zno_tasks (
            id INTEGER PRIMARY KEY, document_id INTEGER, year INTEGER, exam TEXT, session TEXT,
            task_no INTEGER, task_format TEXT, stem TEXT, options_json TEXT, correct_json TEXT,
            topic_tag TEXT, topic_norm TEXT, task_subtype TEXT, paronym_pair TEXT
        );
        INSERT INTO zno_documents VALUES (1, 'ok', 2021, 'garbled'), (2, 'dead', 2010, 'clean');
        """
    )
    rows = [
        (1, 1, 2021, "zno", "osnovna", 2, "single-choice", " Наголос?\n", '[" а ", "б", "в", "г", "ґ"]', "Б", "ТЕМА: Наголос", "", "", ""),
        (2, 1, 2024, "nmt", "sesiya-1", 3, "single-choice", "Паронім?", '["а", "б", "в", "г", "ґ"]', "Д", "", "", "paronym", ""),
        (3, 1, 2021, "zno", "osnovna", 4, "single-choice", "Лексика?", '["а", "б", "в", "г", "ґ"]', "А", "", "lexical_norm", "word_choice", ""),
        (4, 1, 2021, "zno", "osnovna", 5, "single-choice", "Зламані варіанти", '["а", "а"]', "А", "ТЕМА: Наголос", "", "", ""),
        (5, 1, 2021, "zno", "osnovna", 6, "own-statement", "Власна відповідь", '[]', "", "", "", "", ""),
        (6, 1, 2021, "zno", "osnovna", 7, "single-choice", "Орфографія?", '["а", "б", "в", "г", "ґ"]', "Г", "ТЕМА: Орфографія. Апостроф", "", "", ""),
        (7, 1, 2021, "zno", "osnovna", 8, "single-choice", "Зламані варіанти", '["а", "а"]', "А", "ТЕМА: Орфографія. Апостроф", "", "", ""),
        (8, 1, 2021, "zno", "osnovna", 9, "single-choice", "Морфологія?", '["а", "б", "в", "г", "ґ"]', "В", "ТЕМА: Морфологія", "morphological_norm", "", ""),
        (9, 1, 2021, "zno", "osnovna", 10, "single-choice", "Синтаксис?", '["а", "б", "в", "г", "ґ"]', "Д", "ТЕМА: Синтаксис", "syntactic_norm", "", ""),
        (10, 1, 2021, "zno", "osnovna", 11, "single-choice", "Морфологія без норми?", '["а", "б", "в", "г", "ґ"]', "А", "ТЕМА: Морфологія. Іменник", "", "", ""),
        (11, 1, 2021, "zno", "osnovna", 12, "single-choice", "Синтаксис. Розділові знаки?", '["а", "б", "в", "г", "ґ"]', "Б", "ТЕМА: Синтаксис. Розділові знаки в реченні", "", "", ""),
        (12, 1, 2021, "zno", "osnovna", 13, "single-choice", "Фонетика?", '["а", "б", "в", "г", "ґ"]', "В", "ТЕМА: Фонетика", "", "", ""),
        (
            13,
            1,
            2024,
            "nmt",
            "sesiya-2",
            1,
            "single-choice",
            "Однаковий звук позначають букви, виділені в кожному слові рядка",
            '["бігти, поріг, злегка", "повість, сяйво, свічка", "лічба, почасти, чітко", "кістці, тім\'я, житній"]',
            "Б",
            "ТЕМА: Фонетика. Зміни звуків",
            "",
            "",
            "",
        ),
    ]
    connection.executemany("INSERT INTO zno_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    connection.commit()
    connection.close()
    return path


def test_builder_keeps_ukrainian_item_text_maps_letter_and_reports_drops(tmp_path: Path) -> None:
    shards, residual, fill_residual = build_zno_shards(_database(tmp_path / "sources.db"))

    stress = shards["stress"]
    assert stress["items"][0]["stem"] == " Наголос?\n"
    assert stress["items"][0]["options"][0] == " а "
    assert stress["items"][0]["correctLetter"] == "Б"
    assert stress["items"][0]["correctIndex"] == 1
    assert stress["items"][0]["znoMode"] == "choice"
    assert stress["items"][0]["znoTaskId"] == "zno:1"
    assert stress["items"][0]["attribution"] == "Джерело: УЦОЯО · ЗНО 2021, основна сесія · завдання №2"
    assert residual["decks"]["stress"]["candidates"] == 2
    assert residual["decks"]["stress"]["emitted"] == 1
    assert residual["decks"]["stress"]["dropped"] == {"invalid_options": 1}
    assert residual["namedResidual"]["emptyKeyOwnStatement"] == 1
    assert residual["namedResidual"]["documentsFetchNotOk"] == 1
    assert residual["namedResidual"]["garbledPdfDocuments"] == 1
    assert residual["namedResidual"]["excluded2009"] == 1
    assert fill_residual["schema"] == "zno-practice-fill-residual"
    assert fill_residual["deckDrops"]["stress"][0]["reason"] == "invalid_options"


def test_lexical_predicate_is_explicit_and_output_is_deterministic(tmp_path: Path) -> None:
    database = _database(tmp_path / "sources.db")
    assert "trim(t.topic_norm) = 'lexical_norm'" in LEXICAL_NORM_SQL
    assert "trim(t.task_subtype) = 'lexical_error'" in LEXICAL_NORM_SQL
    first, first_residual, first_fill = build_zno_shards(database)
    second, second_residual, second_fill = build_zno_shards(database)
    assert first == second
    assert first_residual == second_residual
    assert first_fill == second_fill

    output = tmp_path / "out"
    write_zno_shards(first, first_residual, output)
    write_zno_fill_residual(first_fill, output / "zno-fill-residual.json")
    assert json.loads((output / "practice-zno.paronym.json").read_text(encoding="utf-8"))["thinDeck"] is True
    assert json.loads((output / "zno-fill-residual.json").read_text(encoding="utf-8"))["inventory"]["stress"]["emitted"] == 1


def test_orthography_membership_is_pinned_and_malformed_candidates_drop(tmp_path: Path) -> None:
    shards, residual, _fill = build_zno_shards(_database(tmp_path / "sources.db"))

    assert "instr(t.topic_tag, 'Орфограф') > 0" in ORTHOGRAPHY_SQL
    # This frozen live denominator makes an intentional source-corpus or predicate
    # change visible in review before the generated shard is refreshed.
    assert ORTHOGRAPHY_LIVE_CANDIDATE_COUNT == 168
    assert residual["decks"]["orthography"]["candidates"] == 2
    assert residual["decks"]["orthography"]["emitted"] == 1
    assert residual["decks"]["orthography"]["dropped"] == {"invalid_options": 1}
    assert shards["orthography"]["deckId"] == "zno-orthography"
    assert shards["orthography"]["items"][0]["stem"] == "Орфографія?"


def test_morphological_and_syntactic_norm_decks_use_exact_topic_norm_predicates(tmp_path: Path) -> None:
    shards, residual, _fill = build_zno_shards(_database(tmp_path / "sources.db"))

    assert "trim(t.topic_norm) = 'morphological_norm'" in MORPHOLOGICAL_NORM_SQL
    assert "trim(t.topic_norm) = 'syntactic_norm'" in SYNTACTIC_NORM_SQL
    assert shards["morphological-norm"]["deckId"] == "zno-morphological-norm"
    assert shards["morphological-norm"]["items"][0]["stem"] == "Морфологія?"
    assert shards["syntactic-norm"]["deckId"] == "zno-syntactic-norm"
    assert shards["syntactic-norm"]["items"][0]["stem"] == "Синтаксис?"
    assert residual["decks"]["morphological-norm"]["candidates"] == 1
    assert residual["decks"]["syntactic-norm"]["candidates"] == 1


def test_wave_3_decks_emit_from_broad_topic_tag_families(tmp_path: Path) -> None:
    """#6620: morphology/syntax/phonetics were untapped topic_tag families sitting
    behind the four thin/repetitive original decks; this pins their predicates and
    proves each emits real, letter-valid items when candidates exist."""
    shards, residual, _fill = build_zno_shards(_database(tmp_path / "sources.db"))

    assert "instr(t.topic_tag, 'Морфолог') > 0" in MORPHOLOGY_SQL
    assert "instr(t.topic_tag, 'Словотвір') > 0" in MORPHOLOGY_SQL
    assert "instr(t.topic_tag, 'Синтаксис') > 0" in SYNTAX_SQL
    assert "instr(t.topic_tag, 'Фонетик') > 0" in PHONETICS_SQL
    assert MORPHOLOGY_LIVE_CANDIDATE_COUNT == 195
    assert LEXICAL_NORM_LIVE_CANDIDATE_COUNT == 40
    assert PARONYM_LIVE_CANDIDATE_COUNT == 7

    assert shards["morphology"]["deckId"] == "zno-morphology"
    assert residual["decks"]["morphology"]["candidates"] == 2
    assert residual["decks"]["morphology"]["emitted"] == 2

    assert shards["syntax"]["deckId"] == "zno-syntax"
    assert residual["decks"]["syntax"]["candidates"] == 2
    assert residual["decks"]["syntax"]["emitted"] == 2

    assert shards["phonetics"]["deckId"] == "zno-phonetics"
    assert residual["decks"]["phonetics"]["candidates"] == 2
    assert residual["decks"]["phonetics"]["emitted"] == 1
    assert residual["decks"]["phonetics"]["dropped"] == {"broken_missing_markup": 1}
    assert shards["phonetics"]["items"][0]["stem"] == "Фонетика?"


def test_attribution_uses_ucyoo_and_never_a_mirror() -> None:
    assert learner_attribution(year=2024, exam="nmt", session="sesiya-2", task_no=7) == (
        "Джерело: УЦОЯО · НМТ 2024, сесія 2 · завдання №7"
    )


def test_builder_quarantines_markup_dependent_items_without_overlay(tmp_path: Path) -> None:
    database = _database(tmp_path / "sources.db")
    empty_overlay = tmp_path / "empty-overlay.json"
    empty_overlay.write_text('{"schema":"zno-markup-overlay","schemaVersion":1,"items":{}}', encoding="utf-8")

    shards, residual, _fill = build_zno_shards(database, markup_overlay_path=empty_overlay)

    assert residual["markupIntegrity"]["quarantinedMissingMarkup"] == 1
    assert residual["decks"]["phonetics"]["dropped"]["broken_missing_markup"] == 1
    assert all(item["znoTaskId"] != "zno:13" for item in shards["phonetics"]["items"])
    assert stem_requires_markup(
        "Однаковий звук позначають букви, виділені в кожному слові рядка",
    )


def test_fill_report_distinguishes_blocked_candidates_from_predicate_misses(tmp_path: Path) -> None:
    import subprocess
    import sys

    database = _database(tmp_path / "sources.db")
    overlay = tmp_path / "missing-overlay.json"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE zno_tasks SET topic_tag = (SELECT topic_tag FROM zno_tasks WHERE id = 8), "
            "topic_norm = 'morphological_norm' WHERE id = 13"
        )
    _, _, blocked_only = build_zno_shards(database, markup_overlay_path=overlay)
    assert blocked_only["predicateMissByTopicNorm"] == {}
    assert [entry for entry in blocked_only["blocked"] if entry["znoTaskId"] == "zno:13"] == [
        {"deck": "morphological-norm", "znoTaskId": "zno:13", "reason": "broken_missing_markup"},
        {"deck": "morphology", "znoTaskId": "zno:13", "reason": "broken_missing_markup"},
    ]
    assert blocked_only["unparsed"] == [
        {"znoTaskId": "zno:4", "reason": "invalid_options"},
        {"znoTaskId": "zno:7", "reason": "invalid_options"},
    ]

    with sqlite3.connect(database) as connection:
        template = list(connection.execute("SELECT * FROM zno_tasks WHERE id = 8").fetchone())
        for task_id, topic_norm, task_format in (
            (14, "", "single-choice"),
            (15, " MixedCase ", "single-choice"),
            (16, "mixedcase", "single-choice"),
            (17, "", "own-statement"),
        ):
            row = template.copy()
            row[0], row[6], row[7], row[10], row[11] = task_id, task_format, "unmatched fixture", "", topic_norm
            connection.execute("INSERT INTO zno_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
    _, _, expected_fill = build_zno_shards(database, markup_overlay_path=overlay)
    assert expected_fill["predicateMissByTopicNorm"] == {"MixedCase": 1, "empty": 1, "mixedcase": 1}
    assert expected_fill["blocked"] == blocked_only["blocked"]
    assert expected_fill["unparsed"] == blocked_only["unparsed"]

    fill_path = tmp_path / "fill.json"
    process = subprocess.run(
        [
            sys.executable, "-m", "scripts.practice_deck.zno", "--db", str(database),
            "--out-dir", str(tmp_path / "shards"), "--fill-residual", str(fill_path),
            "--markup-overlay", str(overlay),
        ],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=False, timeout=30,
    )
    assert process.returncode == 0, process.stderr
    assert process.stderr == ""
    assert json.loads(fill_path.read_text(encoding="utf-8")) == expected_fill


def _option_cases_cli(tmp_path: Path, cases: list[tuple]) -> tuple[dict, dict, dict]:
    import subprocess
    import sys

    database = _database(tmp_path / "sources.db")
    overlays = {}
    with sqlite3.connect(database) as connection:
        template = list(connection.execute("SELECT * FROM zno_tasks WHERE id = 8").fetchone())
        marked_stem = connection.execute("SELECT stem FROM zno_tasks WHERE id = 13").fetchone()[0]
        connection.execute("DELETE FROM zno_tasks")
        for task_id, (options, marks, required, letter) in enumerate(cases, 1):
            row = template.copy()
            row[0], row[7], row[8], row[9] = task_id, marked_stem if required else "plain", json.dumps(options), letter
            connection.execute("INSERT INTO zno_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
            if marks is not None:
                overlays[f"zno:{task_id}"] = {"optionMarks": marks}
    overlay = tmp_path / "overlay.json"
    overlay.write_text(json.dumps({"items": overlays}), encoding="utf-8")
    out = tmp_path / "out"
    process = subprocess.run(
        [sys.executable, "-m", "scripts.practice_deck.zno", "--db", str(database), "--out-dir", str(out),
         "--fill-residual", str(out / "fill.json"), "--markup-overlay", str(overlay)],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=False, timeout=30,
    )
    assert process.returncode == 0, process.stderr
    assert process.stderr == ""
    payloads = {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in out.glob("*.json")}
    return payloads, payloads["practice-zno.residual"], payloads["fill"]


_SPACE_OPTIONS = ["alpha", " alpha ", "beta"]
_DIFFERENT_LETTER = [[{"start": 0, "end": 1, "style": "underline"}],
                     [{"start": 2, "end": 3, "style": "underline"}],
                     [{"start": 0, "end": 1, "style": "underline"}]]
_SAME_LETTER = [_DIFFERENT_LETTER[0], [{"start": 1, "end": 2, "style": "underline"}], _DIFFERENT_LETTER[2]]
_DIFFERENT_STYLE = [_DIFFERENT_LETTER[0], [{"start": 1, "end": 2, "style": "bold"}], _DIFFERENT_LETTER[2]]


@pytest.mark.parametrize("options,marks,required,letter,reason", [
    (["alpha", " alpha", "beta"], None, False, "А", "invalid_options"),
    (["alpha", "alpha ", "beta"], None, False, "А", "invalid_options"),
    (_SPACE_OPTIONS, None, False, "А", "invalid_options"),
    (["alpha", "alpha", "beta"], None, False, "А", "invalid_options"),
    ([" alpha ", "beta", "gamma"], None, False, "А", None),
    (["Alpha", "alpha", "beta"], None, False, "А", None),
    (["al pha", "alpha", "beta"], None, False, "А", None),
    (["a\u0301", "a", "beta"], None, False, "А", None),
    (["alpha", "beta", "gamma"], None, False, "А", None),
    (["alpha", "\u00a0alpha\u00a0", "beta"], None, False, "А", None),
    (["alpha", "\talpha\t", "beta"], None, False, "А", None),
    (_SPACE_OPTIONS, _DIFFERENT_LETTER, True, "А", None),
    (_SPACE_OPTIONS, _DIFFERENT_STYLE, True, "А", None),
    (_SPACE_OPTIONS, _SAME_LETTER, True, "А", "invalid_options"),
    (_SPACE_OPTIONS, None, True, "А", "broken_missing_markup"),
    (["alpha", " ", "beta"], None, False, "А", "invalid_options"),
    (["alpha", 7, "beta"], None, False, "А", "invalid_options"),
    (["alpha", "beta"], None, False, "Д", "invalid_options"),
    (["alpha", "alpha", "beta"], _DIFFERENT_LETTER, True, "А", "invalid_options"),
    (_SPACE_OPTIONS, [[{"start": -1, "end": 1}], [], []], True, "А", "broken_missing_markup"),
    (_SPACE_OPTIONS, [[{"start": 0, "end": 1}], [{"start": 1, "end": 2}], []], True, "А", "invalid_options"),
])
def test_cli_option_distinctions_and_quarantine(tmp_path: Path, options, marks, required, letter, reason) -> None:
    payloads, residual, fill = _option_cases_cli(tmp_path, [(options, marks, required, letter)])
    assert residual["markupIntegrity"]["quarantinedMissingMarkup"] == (2 if reason == "broken_missing_markup" else 0)
    for deck in ("morphological-norm", "morphology"):
        receipt = residual["decks"][deck]
        assert receipt["candidates"] == 1
        assert receipt["emitted"] == (0 if reason else 1)
        assert receipt["dropped"] == ({reason: 1} if reason else {})
        items = payloads[f"practice-zno.{deck}"]["items"]
        if reason:
            assert items == []
            assert fill["deckDrops"][deck] == [{"znoTaskId": "zno:1", "reason": reason}]
        else:
            assert len(items) == 1
            assert items[0]["options"] == options
            assert [s.encode("utf-8") for s in items[0]["options"]] == [s.encode("utf-8") for s in options]
            assert items[0]["correctIndex"] == 0
            assert items[0]["correctLetter"] == letter
            assert items[0].get("optionMarks") == marks
            assert fill["deckDrops"][deck] == []
        assert fill["inventory"][deck]["dropped"] == receipt["dropped"]
    assert fill["predicateMissByTopicNorm"] == {}


def test_cli_overlap_keeps_unique_tasks_separate_from_deck_occurrences(tmp_path: Path) -> None:
    payloads, residual, fill = _option_cases_cli(tmp_path, [
        (_SPACE_OPTIONS, _DIFFERENT_LETTER, True, "А"),
        (["alpha", "alpha", "beta"], None, False, "А"),
        (_SPACE_OPTIONS, None, True, "А"),
    ])
    for deck in ("morphological-norm", "morphology"):
        assert residual["decks"][deck]["candidates"] == 3
        assert residual["decks"][deck]["emitted"] == 1
        assert residual["decks"][deck]["dropped"] == {"invalid_options": 1, "broken_missing_markup": 1}
        assert [item["znoTaskId"] for item in payloads[f"practice-zno.{deck}"]["items"]] == ["zno:1"]
        assert fill["deckDrops"][deck] == [
            {"znoTaskId": "zno:2", "reason": "invalid_options"},
            {"znoTaskId": "zno:3", "reason": "broken_missing_markup"},
        ]
    assert {entry["znoTaskId"] for entry in fill["blocked"]} == {"zno:2", "zno:3"}
    assert len(fill["blocked"]) == 4
    assert fill["unparsed"] == [{"znoTaskId": "zno:2", "reason": "invalid_options"}]
    assert fill["predicateMissByTopicNorm"] == {}
