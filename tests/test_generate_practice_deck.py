from __future__ import annotations

import importlib
import sys
import types


def load_generator(monkeypatch):
    lexeme_filter = types.ModuleType("scripts.audit.lexeme_filter")

    def is_practice_eligible(entry: dict) -> bool:
        has_course = bool(entry.get("course_usage"))
        enrichment = entry.get("enrichment")
        cefr = enrichment.get("cefr") if isinstance(enrichment, dict) else None
        has_cefr = isinstance(cefr, dict) and bool(cefr.get("level"))
        return (
            entry.get("is_lexeme_entry") is True
            and (has_course or has_cefr)
            and entry.get("primary_source") != "surzhyk_to_avoid"
        )

    lexeme_filter.is_practice_eligible = is_practice_eligible
    monkeypatch.setitem(sys.modules, "scripts.audit.lexeme_filter", lexeme_filter)
    sys.modules.pop("scripts.audit.generate_practice_deck", None)
    return importlib.import_module("scripts.audit.generate_practice_deck")


def entry(
    lemma: str,
    *,
    cefr: str | None = None,
    course_usage: list[dict] | None = None,
    is_lexeme_entry: bool = True,
    primary_source: str = "built_vocabulary",
) -> dict:
    enrichment = {"cefr": {"level": cefr}} if cefr else {}
    return {
        "lemma": lemma,
        "url_slug": lemma.lower(),
        "gloss": f"{lemma} gloss",
        "ipa": f"/{lemma}/",
        "pos": "noun",
        "enrichment": enrichment,
        "course_usage": course_usage or [],
        "heritage_status": {"classification": "native"},
        "is_lexeme_entry": is_lexeme_entry,
        "primary_source": primary_source,
    }


def test_practice_deck_filters_grammar_surzhyk_and_derived(monkeypatch):
    generator = load_generator(monkeypatch)
    entries = [
        entry("course", course_usage=[{"track": "a1", "slug": "hello", "context": "course example"}]),
        entry("grammar", cefr="A1", is_lexeme_entry=False),
        entry("surzhyk", cefr="A1", primary_source="surzhyk_to_avoid"),
        entry("derived", cefr="A1", is_lexeme_entry=False),
        entry("fill", cefr="A1"),
    ]

    deck, exceeded = generator.build_practice_deck(entries, target=10, soft_cap=10)

    assert exceeded is False
    assert {item["lemma"] for item in deck} == {"course", "fill"}
    assert deck[0]["lemma"] == "course"
    assert deck[0]["example"] == "course example"


def test_practice_deck_extracts_cefr_from_enrichment_dict(monkeypatch):
    generator = load_generator(monkeypatch)

    deck, _ = generator.build_practice_deck([entry("alpha", cefr="B2")], target=1)

    assert deck == [
        {
            "lemma": "alpha",
            "slug": "alpha",
            "gloss": "alpha gloss",
            "ipa": "/alpha/",
            "pos": "noun",
            "cefr": "B2",
            "heritage": "native",
            "example": None,
            "audioKey": None,
        }
    ]


def test_practice_deck_is_bounded_by_target_and_warns_on_soft_cap(monkeypatch):
    generator = load_generator(monkeypatch)
    entries = [entry(f"word-{index}", cefr="A1") for index in range(8)]

    deck, exceeded = generator.build_practice_deck(entries, target=3, soft_cap=2)

    assert len(deck) == 3
    assert exceeded is True


def test_main_writes_warning_without_failing(monkeypatch, tmp_path, capsys):
    generator = load_generator(monkeypatch)
    manifest = tmp_path / "manifest.json"
    out = tmp_path / "deck.json"
    manifest.write_text(
        '{"entries": ['
        '{"lemma": "one", "url_slug": "one", "gloss": "one", '
        '"is_lexeme_entry": true, "primary_source": "built_vocabulary", '
        '"enrichment": {"cefr": {"level": "A1"}}},'
        '{"lemma": "two", "url_slug": "two", "gloss": "two", '
        '"is_lexeme_entry": true, "primary_source": "built_vocabulary", '
        '"enrichment": {"cefr": {"level": "A1"}}}'
        ']}',
        encoding="utf-8",
    )

    result = generator.main(
        [
            "--manifest",
            str(manifest),
            "--out",
            str(out),
            "--target",
            "2",
            "--soft-cap",
            "1",
        ]
    )

    assert result == 0
    assert "WARNING: practice deck has 2 cards; soft cap is 1" in capsys.readouterr().err
    assert out.exists()
