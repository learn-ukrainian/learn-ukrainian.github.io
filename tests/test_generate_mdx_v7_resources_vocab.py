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
    assert mdx.index("<VocabCard") < mdx.index("<FlashcardDeck")
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
    assert "📚 Books" in mdx
    assert "🔗 Online resources" in mdx
    assert "📚 **Караман Grade 10, p.176**" in mdx
    assert "Reflexive verbs with -ся." in mdx
    assert "🔗 **Wikipedia overview**" in mdx


def test_format_resources_for_mdx_groups_mixed_roles_with_icons():
    mdx = format_resources_for_mdx([
        {
            "title": "Караман Grade 10, p.176",
            "author": "Караман",
            "pages": "176",
            "description": "Reflexive verbs with -ся.",
            "role": "textbook",
        },
        {
            "title": "Morning routine clip",
            "url": "https://www.youtube.com/watch?v=abc12345678",
            "channel": "Speak Ukrainian",
            "role": "youtube",
        },
        {
            "title": "Grammar documentary",
            "url": "https://example.com/video",
            "description": "Documentary excerpt.",
            "role": "video",
        },
        {
            "title": "Morning vocabulary blog",
            "url": "https://example.com/blog",
            "description": "Blog post.",
            "role": "blog",
        },
        {
            "title": "Audio drill",
            "url": "https://example.com/audio",
            "description": "Pronunciation practice.",
            "role": "audio",
        },
        {
            "title": "Wikipedia article",
            "url": "https://uk.wikipedia.org/wiki/Ранок",
            "role": "wiki",
        },
    ])

    assert "📚 Books" in mdx
    assert "📺 Videos" in mdx
    assert "📝 Articles" in mdx
    assert "🎧 Audio" in mdx
    assert "🔗 Online resources" in mdx
    assert "📚 **Караман Grade 10, p.176**" in mdx
    assert "📺 [Morning routine clip](https://www.youtube.com/watch?v=abc12345678)" in mdx
    assert "🎥 [Grammar documentary](https://example.com/video)" in mdx
    assert "📝 [Morning vocabulary blog](https://example.com/blog)" in mdx
    assert "🎧 [Audio drill](https://example.com/audio)" in mdx
    assert "🔗 [Wikipedia article](https://uk.wikipedia.org/wiki/Ранок)" in mdx
