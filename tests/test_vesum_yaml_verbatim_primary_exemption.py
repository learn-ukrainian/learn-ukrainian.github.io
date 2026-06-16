"""Regression tests for seminar primary-text VESUM exemptions in YAML artifacts."""

from __future__ import annotations

from scripts.build import linear_pipeline

KOLIADKY_MODULE = """
## Primary

> Коли не било з нащада світа,
> тогди не било неба, ні землі, лишень синє море.
>
> *— Грушевський [S1]*
"""

KOLIADKY_ACTIVITY_QUOTE = (
    "Коли не било з нащада світа, / тогди не било неба, ні землі, лишень синє море."
)

SHCHEDRIVKA_PASSAGE = (
    "Ясне небонько, світле сонінько, / Світле сонінько, ясен місячик"
)


def _literary_hit_for_shchedrivka(
    query: str,
    *,
    level: str,
    limit: int = 20,
) -> list[dict[str, str]]:
    _ = query, level, limit
    return [
        {
            "source_type": "literary",
            "corpus": "literary_texts",
            "text": f"{SHCHEDRIVKA_PASSAGE}. Ой у полі криниченька.",
        }
    ]


def test_yaml_primary_spans_are_stripped_but_scoped_terms_remain(monkeypatch) -> None:
    monkeypatch.setattr(
        linear_pipeline,
        "_search_literary_hits",
        _literary_hit_for_shchedrivka,
    )

    activities = [
        {
            "type": "analysis",
            "passage": SHCHEDRIVKA_PASSAGE,
            "items": [
                {
                    "quote": KOLIADKY_ACTIVITY_QUOTE,
                    "prompt": "Порівняйте Йоль і дерево-явір як першопочаток.",
                }
            ],
        }
    ]

    text = linear_pipeline._build_vesum_text(
        KOLIADKY_MODULE,
        activities,
        [],
        [],
        level="folk",
    )

    for word in ("нащада", "било", "сонінько"):
        assert word not in text
    for word in ("Йоль", "дерево-явір", "першопочаток"):
        assert word in text


def test_module_primary_cross_reference_does_not_need_corpus(monkeypatch) -> None:
    def fail_literary_search(*args: object, **kwargs: object) -> list[dict[str, str]]:
        raise AssertionError("module-primary fast path should avoid corpus lookup")

    monkeypatch.setattr(linear_pipeline, "_search_literary_hits", fail_literary_search)

    text = linear_pipeline._build_vesum_text(
        KOLIADKY_MODULE,
        [{"type": "analysis", "passage": KOLIADKY_ACTIVITY_QUOTE}],
        [],
        [],
        level="folk",
    )

    assert "нащада" not in text
    assert "било" not in text


def test_vocabulary_usage_primary_span_is_stripped(monkeypatch) -> None:
    monkeypatch.setattr(
        linear_pipeline,
        "_search_literary_hits",
        _literary_hit_for_shchedrivka,
    )

    text = linear_pipeline._build_vesum_text(
        "",
        [],
        [
            {
                "lemma": "колядка",
                "usage": f"У щедрівці: {SHCHEDRIVKA_PASSAGE}. Сучасний коментар лишається.",
            }
        ],
        [],
        level="folk",
    )

    assert "сонінько" not in text
    assert "колядка" in text
    assert "Сучасний коментар лишається" in text


def test_core_level_yaml_primary_text_is_not_exempted(monkeypatch) -> None:
    def fail_literary_search(*args: object, **kwargs: object) -> list[dict[str, str]]:
        raise AssertionError("core levels must not use literary primary stripping")

    monkeypatch.setattr(linear_pipeline, "_search_literary_hits", fail_literary_search)

    text = linear_pipeline._build_vesum_text(
        KOLIADKY_MODULE,
        [{"type": "analysis", "passage": KOLIADKY_ACTIVITY_QUOTE}],
        [],
        [],
        level="a1",
    )

    assert "нащада" in text
    assert "било" in text


def test_literary_corpus_exemption_does_not_cross_activity_field_boundary(monkeypatch) -> None:
    cross_field_hit = "Йоль дерево явір як першопочаток стоїть у лісі"

    def literary_hit_for_cross_field_window(
        query: str,
        *,
        level: str,
        limit: int = 20,
    ) -> list[dict[str, str]]:
        _ = query, level, limit
        return [
            {
                "source_type": "literary",
                "corpus": "literary_texts",
                "text": cross_field_hit,
            }
        ]

    monkeypatch.setattr(
        linear_pipeline,
        "_search_literary_hits",
        literary_hit_for_cross_field_window,
    )

    text = linear_pipeline._build_vesum_text(
        "",
        [
            {
                "type": "analysis",
                "quote": "Йоль",
                "prompt": "дерево явір як першопочаток стоїть у лісі",
            }
        ],
        [],
        [],
        level="folk",
    )

    assert "Йоль" in text


def test_modern_activity_nonword_still_fails_vesum(monkeypatch) -> None:
    monkeypatch.setattr(linear_pipeline, "_search_literary_hits", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        linear_pipeline,
        "_resolve_folk_heritage_attested_missing",
        lambda *args, **kwargs: set(),
    )

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        return {
            word: ([] if word == "привітаннячкоз" else [{"lemma": word}])
            for word in words
        }

    result = linear_pipeline._vesum_gate(
        module_text="",
        activities=[
            {
                "type": "short-answer",
                "passage": (
                    "Сьогодні учні пишуть привітаннячкоз для друга у класі "
                    "разом після уроку."
                ),
            }
        ],
        vocabulary=[],
        resources=[],
        level="folk",
        verify_words_fn=verify_words,
    )

    assert result["passed"] is False
    assert "привітаннячкоз" in result["missing"]
