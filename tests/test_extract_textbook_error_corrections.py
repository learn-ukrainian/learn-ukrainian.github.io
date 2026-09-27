"""Unit tests for textbook error correction extraction and negative context filtering."""

import sqlite3
from pathlib import Path

import pytest

from scripts.practice.extract_textbook_error_corrections import (
    create_error_correction_drill,
    is_intentional_error_context,
    parse_contrastive_textbook_tables,
    parse_style_guide_entries,
)


def test_is_intentional_error_context_positive():
    error_samples = [
        "Вправа 12. Відредагуйте подані речення.",
        "Знайдіть помилку у слововживанні та виправте її.",
        "НЕПРАВИЛЬНО \t ПРАВИЛЬНО\nна протязі \t протягом",
        "Антисуржик: уникайте типових помилок у мовленні.",
        "Вставте пропущені літери е та и.",
        "Розкрийте дужки і запишіть слова разом або окремо.",
    ]
    for sample in error_samples:
        assert is_intentional_error_context(sample), f"Failed to detect error context in: {sample}"


def test_is_intentional_error_context_negative():
    clean_samples = [
        "Українська мова належить до слов’янської групи індоєвропейської мовної сім’ї.",
        "Іван Франко народився на Львівщині та написав повість «Захар Беркут».",
        "Вечірнє сонце повільно сідало за високі верхівки соснового лісу.",
        "Учні з радістю відвідали музей під час шкільної екскурсії.",
    ]
    for sample in clean_samples:
        assert not is_intentional_error_context(sample), f"Falsely flagged clean sentence: {sample}"


def _textbook_db(*chunks: tuple[int, str, str]) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, grade INTEGER, author TEXT, title TEXT, text TEXT)")
    conn.execute("CREATE TABLE style_guide (id INTEGER PRIMARY KEY, word TEXT, section TEXT, text TEXT)")
    for grade, author, text in chunks:
        conn.execute(
            "INSERT INTO textbooks (grade, author, title, text) VALUES (?, ?, 'Сторінка 1', ?)",
            (grade, author, text),
        )
    return conn


def _fake_vesum(tmp_path: Path, forms: dict[str, tuple[str, bool]]):
    """Minimal VESUM file: word form -> (part of speech, carries a `bad` marker)."""
    from scripts.practice.extract_textbook_error_corrections import VesumLookup

    path = tmp_path / "vesum.db"
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE forms_all (id INTEGER PRIMARY KEY, entry_id INTEGER, word_form TEXT, lemma TEXT,"
        " pos TEXT, tags TEXT, source_comment TEXT, source_location TEXT)"
    )
    conn.execute("CREATE TABLE form_markers (form_id INTEGER, marker TEXT, origin TEXT, marker_class TEXT)")
    for form_id, (form, (pos, bad)) in enumerate(forms.items(), 1):
        conn.execute(
            "INSERT INTO forms_all VALUES (?, ?, ?, ?, ?, ?, NULL, '')",
            (form_id, form_id, form, form, pos, pos + (":bad" if bad else "")),
        )
        if bad:
            conn.execute("INSERT INTO form_markers VALUES (?, 'bad', 'tag', 'invalid')", (form_id,))
    conn.commit()
    conn.close()
    return VesumLookup(path)


def _pairs(rows: list[dict]) -> list[tuple[str, str]]:
    return [(row["error"], row["correct"]) for row in rows]


def test_parse_contrastive_textbook_tables_mock():
    mock_text = """
    КУЛЬТУРА СЛОВА
    Б. Запам’ятайте правильний варіант слововживання.
    НЕПРАВИЛЬНО    ПРАВИЛЬНО
    получається    виходить
    влучний вираз  влучний вислів
    завідувач відділом  завідувач відділу
    7. Прочитайте текст і виконайте завдання.
    """
    pairs = parse_contrastive_textbook_tables(_textbook_db((11, "avramenko", mock_text)))
    assert len(pairs) == 3
    assert pairs[0]["error"] == "получається"
    assert pairs[0]["correct"] == "виходить"
    assert pairs[1]["error"] == "влучний вираз"
    assert pairs[1]["correct"] == "влучний вислів"


def test_table_parsing_stops_where_the_table_ends():
    """#8723 err_0013 «О.»→«Теліга», err_0021, err_0065: prose after a table became drills."""
    text = "\n".join(
        [
            "Б. Запам’ятайте правильний варіант слововживання. НЕПРАВИЛЬНО ПРАВИЛЬНО",
            "природній природний",
            "Мужчинам",
            "Не зірвуться слова, гартовані, як криця,",
            "О. Теліга",
            "Петро Чайковський Марія Заньковецька",
            "Незаконний видобуток бурштину, виру",
        ]
    )
    pairs = parse_contrastive_textbook_tables(_textbook_db((11, "avramenko", text)))
    assert _pairs(pairs) == [("природній", "природний")]


def test_correct_first_column_table_pairs_each_error_with_its_correction():
    """#8723 err_0203 «побудували»→«цегляний»: a ПРАВИЛЬНО/НЕПРАВИЛЬНО column table was
    read as one-line pairs, and a table whose lines wrap cannot be paired at all."""
    columns = "\n".join(
        [
            "Культура мовлення",
            "ПРАВИЛЬНО НЕПРАВИЛЬНО",
            "будь-яка мелодія",
            "чекали дві години",
            "заважати працювати",
            "люба мелодія",
            "чекали два часа",
            "мішати працювати",
            "7. ПАРОНІМИ",
        ]
    )
    wrapped = "\n".join(
        [
            "Культура мовлення",
            "ПРАВИЛЬНО НЕПРАВИЛЬНО",
            "проїзд пасажирським",
            "транспортом",
            "проїзд пасажирів",
            "пасажирським транспортом",
            "побудували будинок",
            "із цегли",
            "побудували цегляний",
            "будинок із цегли",
            "працівники взялися",
            "до роботи",
            "робітники взялися до роботи",
            "53",
        ]
    )
    pairs = _pairs(
        parse_contrastive_textbook_tables(_textbook_db((5, "zabolotnyi", columns), (5, "zabolotnyi", wrapped)))
    )
    assert pairs == [
        ("люба мелодія", "будь-яка мелодія"),
        ("чекали два часа", "чекали дві години"),
        ("мішати працювати", "заважати працювати"),
    ]


def test_interleaved_vertical_table_pairs_adjacent_lines():
    text = "\n".join(
        [
            "Неправильно Правильно",
            "біля трьох кілометрів",
            "близько трьох кілометрів",
            "сім метрів у секунду",
            "сім метрів за секунду",
            "7. Прочитайте вірш і виконайте завдання.",
        ]
    )
    pairs = _pairs(parse_contrastive_textbook_tables(_textbook_db((6, "avramenko", text))))
    assert pairs == [
        ("біля трьох кілометрів", "близько трьох кілометрів"),
        ("сім метрів у секунду", "сім метрів за секунду"),
    ]


def test_style_guide_sentence_is_not_paired_with_a_fragment():
    """#8723 err_0278: a two-line sentence was keyed to the fragment «збори сприйняли»."""
    conn = _textbook_db()
    conn.execute(
        "INSERT INTO style_guide (word, section, text) VALUES (?, ?, ?)",
        (
            "Приймати чи сприймати?",
            "",
            "Хоч слова схожі. Неправильно казати «Доповідь збори прийняли в цілому\n"
            "позитивно, хоч деякі місця викликали незначні заперечення», треба «збори сприйняли».",
        ),
    )
    conn.execute(
        "INSERT INTO style_guide (word, section, text) VALUES (?, ?, ?)",
        (
            "Деякі відмінкові особливості",
            "",
            "Пасив. Неправильно «Головну увагу мною приділено таким явищам», "
            "треба «Головну увагу я приділив таким явищам».",
        ),
    )
    pairs = _pairs(parse_style_guide_entries(conn))
    assert pairs == [("Головну увагу мною приділено таким явищам", "Головну увагу я приділив таким явищам")]


def test_create_error_correction_drill():
    drill = create_error_correction_drill(
        error_phrase="на протязі року",
        correct_phrase="протягом року",
        explanation="В українській мові про часові проміжки кажуть «протягом року». «На протязі» означає струмінь повітря.",
        source="Avramenko Gr 11",
    )
    assert drill["errorWord"] == "на протязі року"
    assert drill["correctForm"] == "протягом року"
    assert "протягом року" in drill["options"]
    assert "на протязі року" in drill["options"]
    assert drill["isUkrainian"] is True
    assert "протягом року" in drill["explanation"]


def test_drill_options_are_only_the_forms_the_source_contrasts():
    """#8723: every option list was error / "error (розм.)" / correction / "correction (застаріле)"."""
    drill = create_error_correction_drill("україномовний", "українськомовний", source="Textbook Gr 11 (avramenko)")
    assert drill["options"] == ["україномовний", "українськомовний"]


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ("виписка з протоколу витяг з протоколу", ("виписка з протоколу", "витяг з протоколу")),
        ("влучний вираз влучний вислів", ("влучний вираз", "влучний вислів")),
        ("у травні місяці у травні", ("у травні місяці", "у травні")),
        ("сто років тому назад сто років тому", ("сто років тому назад", "сто років тому")),
        ("бути правим мати рацію, ваша правда", ("бути правим", "мати рацію, ваша правда")),
        ("самий цікавий найцікавіший", ("самий цікавий", "найцікавіший")),
        ("під відкритим небом просто неба", ("під відкритим небом", "просто неба")),
        ("кофейник кавник", ("кофейник", "кавник")),
        ("у кінці кінців зрештою, урешті-решт", "ambiguous_split"),
        ("як би там не було хай там як", "ambiguous_split"),
        ("кидатися в очі (про щось яскраве) впадати в очі", "ambiguous_split"),
        ("узяти себе в руки опанувати себе, отямитися", "ambiguous_split"),
    ],
)
def test_split_contrastive_row(row, expected):
    from scripts.practice.extract_textbook_error_corrections import split_contrastive_row

    assert split_contrastive_row(row) == expected


def test_split_without_shared_words_needs_a_vesum_part_of_speech_parallel(tmp_path: Path):
    from scripts.practice.extract_textbook_error_corrections import split_contrastive_row

    vesum = _fake_vesum(
        tmp_path,
        {
            "халатне": ("adj", False),
            "відношення": ("noun", False),
            "недбале": ("adj", False),
            "ставлення": ("noun", False),
        },
    )
    assert split_contrastive_row("халатне відношення недбале ставлення") == "ambiguous_split"
    assert split_contrastive_row("халатне відношення недбале ставлення", vesum) == (
        "халатне відношення",
        "недбале ставлення",
    )


def test_row_merged_with_the_next_row_is_withheld():
    text = "\n".join(
        [
            "НЕПРАВИЛЬНО ПРАВИЛЬНО",
            "сто років тому назад сто років тому",
            "не дивлячись на труднощі кумедна собака незважаючи на (попри) труднощі",
            "кумедний собака",
            "1. Прочитайте легенду та виконайте завдання.",
        ]
    )
    withheld: list[dict] = []
    pairs = _pairs(parse_contrastive_textbook_tables(_textbook_db((5, "avramenko", text)), withheld=withheld))
    assert ("сто років тому назад", "сто років тому") in pairs
    assert all(error != "не дивлячись на труднощі" for error, _ in pairs)
    assert any(row["reason"] == "row_interleaved_with_next_row" for row in withheld)


def test_single_word_claims_need_vesum_corroboration(tmp_path: Path):
    """#8723 err_0001 «україномовний»: VESUM lists it as standard, so the claim is contested."""
    vesum = _fake_vesum(
        tmp_path,
        {
            "україномовний": ("adj", False),
            "українськомовний": ("adj", False),
            "природній": ("adj", True),
            "природний": ("adj", False),
            "ясна": ("noun", False),
            "Десна": ("noun", False),
        },
    )
    text = "\n".join(
        [
            "НЕПРАВИЛЬНО ПРАВИЛЬНО",
            "україномовний українськомовний",
            "природній природний",
            "десна ясна",
        ]
    )
    withheld: list[dict] = []
    pairs = _pairs(parse_contrastive_textbook_tables(_textbook_db((11, "avramenko", text)), vesum, withheld))
    # "десна" (gums) is unknown to VESUM; only the capitalised river name "Десна" is listed.
    assert pairs == [("природній", "природний"), ("десна", "ясна")]
    assert [(row["error"], row["reason"]) for row in withheld] == [("україномовний", "error_form_standard_in_vesum")]


def test_contradicting_textbooks_are_withheld():
    """Gr 11 keys «глуха ніч»→«глупа ніч»; Gr 10 keys the reverse. Neither can be taught."""
    from scripts.practice.extract_textbook_error_corrections import extract_error_correction_deck

    conn = _textbook_db(
        (11, "avramenko", "НЕПРАВИЛЬНО ПРАВИЛЬНО\nглуха ніч глупа ніч\nдовга перерва тривала перерва"),
        (10, "avramenko", "НЕПРАВИЛЬНО ПРАВИЛЬНО\nглупа ніч глуха ніч"),
    )
    withheld: list[dict] = []
    deck = extract_error_correction_deck(conn, None, withheld, log=lambda _msg: None)
    assert [(d["errorWord"], d["correctForm"]) for d in deck["drills"]] == [("довга перерва", "тривала перерва")]
    assert sorted(row["reason"] for row in withheld) == ["conflicting_sources", "conflicting_sources"]


def test_culture_deck_shape():
    from scripts.practice.extract_textbook_error_corrections import build_culture_deck

    deck = build_culture_deck([create_error_correction_drill("влучний вираз", "влучний вислів")])
    assert deck["deckId"] == "culture-error-correction"
    assert deck["totalDrills"] == 1
    assert deck["drills"][0]["id"] == "err_0001"


def test_committed_culture_decks_are_one_regeneration():
    """The bundled site deck and the audited registry copy are the same extractor output."""
    root = Path(__file__).resolve().parents[1]
    site = (root / "site/src/data/practice-error-corrections.json").read_text(encoding="utf-8")
    registry = (root / "registry/practice/textbook-error-corrections.json").read_text(encoding="utf-8")
    assert site == registry
