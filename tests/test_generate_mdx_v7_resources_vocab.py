from __future__ import annotations

import pytest

from scripts.generate_mdx.resources import format_resources_for_mdx, vocab_items_to_components

pytestmark = pytest.mark.reads_content


def test_vocab_items_to_components_emits_flashcards_and_vocab_card():
    mdx = vocab_items_to_components([
        {
            "lemma": "прокидатися",
            "translation": "to wake up",
            "pos": "verb",
            "usage": "Я прокидаюся о сьомій.",
        },
        {
            "lemma": "кава",
            "translation": "coffee",
            "pos": "noun",
            "gender": "f",
            "usage": "Я п'ю каву.",
        },
        {
            "lemma": "потім",
            "translation": "then",
            "pos": "adv",
            "usage": "Потім я вмиваюся.",
        },
    ])

    assert "<FlashcardDeck" in mdx
    assert "<VocabCard" in mdx
    assert mdx.index("<VocabCard") < mdx.index("<FlashcardDeck")
    assert '"front":"прокидатися"' in mdx
    assert '"translation":"to wake up"' in mdx
    assert '"example":"Я прокидаюся о сьомій."' in mdx


def test_format_resources_for_mdx_textbook_shows_title_not_source_ref_path():
    """B1 regression: a textbook citation must render its human `title`, never its
    internal `source_ref` repo path; a public `url` makes it a clickable link."""
    mdx = format_resources_for_mdx({
        "books": [
            {
                "title": "9 клас: підрядні обставинні речення",
                "role": "textbook",
                "source_ref": "docs/references/textbooks-txt/9-klas-ukrajinska-mova-voron-2017.txt",
                "notes": "Джерело для класифікації підрядних частин.",
                "url": "https://pidruchnyk.com.ua/1027-ukrmova-voron-9klas.html",
            },
        ],
    })
    assert "docs/references/textbooks-txt" not in mdx  # internal path never leaks
    assert (
        "[9 клас: підрядні обставинні речення]"
        "(https://pidruchnyk.com.ua/1027-ukrmova-voron-9klas.html)"
    ) in mdx
