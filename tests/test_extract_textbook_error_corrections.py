"""Unit tests for textbook error correction extraction and negative context filtering."""

import sqlite3

from scripts.practice.extract_textbook_error_corrections import (
    create_error_correction_drill,
    is_intentional_error_context,
    parse_contrastive_textbook_tables,
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


def test_parse_contrastive_textbook_tables_mock():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
    CREATE TABLE textbooks (
        id INTEGER PRIMARY KEY,
        grade INTEGER,
        author TEXT,
        title TEXT,
        text TEXT
    )
    """)
    mock_text = """
    КУЛЬТУРА СЛОВА
    Б. Запам’ятайте правильний варіант слововживання.
    НЕПРАВИЛЬНО    ПРАВИЛЬНО
    получається    виходить
    влучний вираз  влучний вислів
    завідувач відділом  завідувач відділу
    7. Прочитайте текст і виконайте завдання.
    """
    conn.execute(
        "INSERT INTO textbooks (grade, author, title, text) VALUES (11, 'avramenko', 'Сторінка 10', ?)",
        (mock_text,),
    )
    pairs = parse_contrastive_textbook_tables(conn)
    assert len(pairs) == 3
    assert pairs[0]["error"] == "получається"
    assert pairs[0]["correct"] == "виходить"
    assert pairs[1]["error"] == "влучний вираз"
    assert pairs[1]["correct"] == "влучний вислів"


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
