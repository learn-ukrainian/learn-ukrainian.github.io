from __future__ import annotations

from scripts.wiki.strip_l2_framing import process_article


def test_removes_explicit_l2_section_preserving_meta() -> None:
    original = """# Demo

<!-- wiki-meta
slug: demo
domain: pedagogy/a1
generated_by_model: gemini-2.5-pro
-->

## Методичний підхід

Корисний абзац. [S1]

## Типові помилки L2 (англомовні учні)

Тут має зникнути все.

| A | B |
| :--- | :--- |
| bad | good |

## Деколонізаційні застереження

Це треба залишити.
"""

    updated, sections_removed, sentences_removed, tables_removed = process_article(original)

    assert "<!-- wiki-meta" in updated
    assert "generated_by_model: gemini-2.5-pro" in updated
    assert "Типові помилки L2" not in updated
    assert "Тут має зникнути все." not in updated
    assert "Це треба залишити." in updated
    assert sections_removed == 1
    assert sentences_removed == 0
    assert tables_removed == 0


def test_removes_only_target_sentence_inside_kept_section() -> None:
    original = """## Послідовність введення

Корисне речення. Це критично важливий момент для англомовних учнів [S1]. Ще одне корисне речення.
"""

    updated, sections_removed, sentences_removed, tables_removed = process_article(original)

    assert "англомовних учнів" not in updated
    assert "Корисне речення." in updated
    assert "Ще одне корисне речення." in updated
    assert sections_removed == 0
    assert sentences_removed == 1
    assert tables_removed == 0


def test_removes_explicit_english_vs_ukrainian_table() -> None:
    original = """## Пояснення

| English vs Ukrainian | Comment |
| :--- | :--- |
| present simple / теперішній час | comparison |

Після таблиці текст залишається.
"""

    updated, sections_removed, sentences_removed, tables_removed = process_article(original)

    assert "| English vs Ukrainian | Comment |" not in updated
    assert "Після таблиці текст залишається." in updated
    assert sections_removed == 0
    assert sentences_removed == 0
    assert tables_removed == 1


def test_is_idempotent() -> None:
    original = """## Послідовність введення

Корисне речення. На відміну від англійської мови, тут є інша логіка. Ще одне корисне речення.

## Типові помилки L2

Цей розділ треба прибрати.
"""

    once, *_ = process_article(original)
    twice, *_ = process_article(once)

    assert once == twice
