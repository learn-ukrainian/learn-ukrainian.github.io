from __future__ import annotations

from scripts.generate_mdx.resources import format_resources_for_mdx, vocab_items_to_components


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
    assert '"front":"прокидатися"' in mdx
    assert '"translation":"to wake up"' in mdx
    assert '"example":"Я прокидаюся о сьомій."' in mdx


def test_format_resources_for_mdx_uses_author_description_and_role_icon():
    mdx = format_resources_for_mdx({
        "books": [
            {
                "title": "Караман Grade 10, p.176",
                "source_ref": "Караман Grade 10, p.176",
                "author": "Караман",
                "pages": "176",
                "description": "Reflexive verbs with -ся.",
                "role": "textbook",
            },
            {
                "title": "Wikipedia overview",
                "source_ref": "Ukrainian Wikipedia",
                "author": "Вікіпедія",
                "description": "Background article.",
                "role": "wiki",
            },
        ],
    })

    assert "by Unknown" not in mdx
    assert "📚 **Караман Grade 10, p.176**" in mdx
    assert "Reflexive verbs with -ся." in mdx
    assert "🔗 **Вікіпедія — Ukrainian Wikipedia**" in mdx
