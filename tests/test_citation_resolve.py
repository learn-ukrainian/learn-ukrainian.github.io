from __future__ import annotations

from typing import Any

import pytest
import yaml

from scripts.build import linear_pipeline


def _result(source_ref: str, title: str = "Караман Grade 10, p.176") -> dict[str, Any]:
    return linear_pipeline._citation_gate(
        [{"source_ref": source_ref}],
        {"references": [{"title": title}]},
    )


def test_plan_compact_form_matches_writer_expanded() -> None:
    result = _result("Караман, Українська мова, 10 клас, с. 176")

    assert result["passed"] is True
    assert result["unknown"] == []


def test_grade_word_order_tolerated() -> None:
    assert _result("Караман, 10 клас, с. 176")["passed"] is True
    assert _result("Караман, Grade 10, p.176")["passed"] is True


def test_page_label_variants() -> None:
    assert _result("Караман, 10 клас, p.176")["passed"] is True
    assert _result("Караман, 10 клас, с. 176")["passed"] is True
    assert _result("Караман, 10 клас, стор. 176")["passed"] is True


def test_latin_mixed_author_matches_plan_reference() -> None:
    assert _result("Karaman Ukrainian language, Grade 10, p.176")["passed"] is True
    assert _result("Kараман Ukrainian language, Grade 10, p.176")["passed"] is True


@pytest.mark.parametrize(
    "author",
    [
        "Кaraman",
        "Kаraman",
        "Karаman",
        "Karamаn",
        "Караman",
    ],
)
def test_cyrillic_latin_lookalike_author_forms_match(author: str) -> None:
    assert _result(f"{author}, Grade 10, p.176")["passed"] is True


def test_author_prefixed_scholarly_title_matches_plan_reference_by_containment() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Костомаров М. «Слов'янська міфологія»"}],
        {"references": [{"title": "Слов'янська міфологія", "author": "Костомаров М."}]},
    )

    assert result["passed"] is True
    assert result["unknown"] == []


def test_initial_before_surname_matches_plan_author_by_containment() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "М. Костомаров «Слов'янська міфологія»"}],
        {"references": [{"title": "Слов'янська міфологія", "author": "Костомаров М."}]},
    )

    assert result["passed"] is True
    assert result["unknown"] == []


def test_author_mismatch_does_not_launder_generic_title_by_containment() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Інший Автор, Українська мова, 9 клас"}],
        {"references": [{"title": "Українська мова", "author": "Караман О."}]},
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Інший Автор, Українська мова, 9 клас"]


def test_authorless_generic_title_does_not_resolve_by_containment() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Єфремов С. «Історія української літератури»"}],
        {"references": [{"title": "Історія української літератури"}]},
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Єфремов С. «Історія української літератури»"]


def test_punctuation_collapse_does_not_cross_token_boundaries() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Автор Х., Точка: Нульова гіпотеза"}],
        {"references": [{"title": "Точка Нуль", "author": "Автор Х."}]},
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Автор Х., Точка: Нульова гіпотеза"]


def test_author_corroboration_accepts_surname_initial_source_ref() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Шевченко Т.Г. «Садок вишневий»"}],
        {"references": [{"title": "Садок вишневий", "author": "Тарас Шевченко"}]},
    )

    assert result["passed"] is True
    assert result["unknown"] == []


def test_first_name_alone_does_not_satisfy_author_corroboration() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Тарас Петренко «Садок вишневий»"}],
        {"references": [{"title": "Садок вишневий", "author": "Тарас Шевченко"}]},
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Тарас Петренко «Садок вишневий»"]


def test_title_word_does_not_satisfy_author_corroboration() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Костомаров М. «Слов'янська міфологія»"}],
        {"references": [{"title": "Слов'янська міфологія", "author": "Міфологія"}]},
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Костомаров М. «Слов'янська міфологія»"]


def test_author_word_inside_quoted_title_does_not_corroborate_author() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Петренко О. «Шевченко: Садок вишневий»"}],
        {"references": [{"title": "Садок вишневий", "author": "Тарас Шевченко"}]},
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Петренко О. «Шевченко: Садок вишневий»"]


def test_nested_title_quote_does_not_corroborate_author_from_title_prefix() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Петренко О. «Шевченко “Садок вишневий”»"}],
        {"references": [{"title": "Садок вишневий", "author": "Тарас Шевченко"}]},
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Петренко О. «Шевченко “Садок вишневий”»"]


def test_unquoted_title_does_not_resolve_by_containment() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Петренко О. Шевченко: Садок вишневий"}],
        {"references": [{"title": "Садок вишневий", "author": "Тарас Шевченко"}]},
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Петренко О. Шевченко: Садок вишневий"]


def test_quoted_title_with_no_plan_match_still_rejected() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Петренко О. «Немає такого твору»"}],
        {"references": [{"title": "Садок вишневий", "author": "Тарас Шевченко"}]},
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Петренко О. «Немає такого твору»"]


def test_koliadky_author_prefixed_plan_references_resolve_by_containment() -> None:
    plan = {
        "references": [
            {"title": "Слов'янська міфологія", "author": "Костомаров М."},
            {"title": "Нарис історії культури України", "author": "Попович М."},
            {
                "title": "Історія української літератури",
                "author": "Чижевський Д.",
            },
            {
                "title": (
                    "Праці етнографічно-статистичної експедиції "
                    "в Західно-Руський край"
                ),
                "author": "Чубинський П.",
            },
        ]
    }
    resources = [
        {"source_ref": "Костомаров М. «Слов'янська міфологія»"},
        {"source_ref": "Попович М. «Нарис історії культури України»"},
        {"source_ref": "Чижевський Д. «Історія української літератури»"},
        {
            "source_ref": (
                "Чубинський П. «Праці етнографічно-статистичної експедиції "
                "в Західно-Руський край»"
            )
        },
    ]

    result = linear_pipeline._citation_gate(resources, plan)

    assert result["passed"] is True
    assert result["unknown"] == []

    order_variant = linear_pipeline._citation_gate(
        [{"source_ref": "М. Костомаров «Слов'янська міфологія»"}],
        plan,
    )

    assert order_variant["passed"] is True
    assert order_variant["unknown"] == []


def test_unknown_citation_still_rejected() -> None:
    result = _result("Tolstoy, War and Peace, p.500")

    assert result["passed"] is False
    assert result["unknown"] == ["Tolstoy, War and Peace, p.500"]


def test_author_prefixed_title_not_in_plan_still_rejected() -> None:
    result = _result(
        "Костомаров М. «Слов'янська міфологія»",
        "Історія української літератури",
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Костомаров М. «Слов'янська міфологія»"]


def test_one_word_generic_plan_title_does_not_resolve_by_containment() -> None:
    result = _result(
        "Костомаров М. «Слов'янська міфологія»",
        "Міфологія",
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Костомаров М. «Слов'янська міфологія»"]


def test_partial_match_does_not_pass() -> None:
    wrong_grade = _result("Караман, Українська мова, 9 клас, с. 176")
    wrong_page = _result("Караман, Українська мова, 10 клас, с. 999")

    assert wrong_grade["passed"] is False
    assert wrong_grade["unknown"] == ["Караман, Українська мова, 9 клас, с. 176"]
    assert wrong_page["passed"] is False
    assert wrong_page["unknown"] == ["Караман, Українська мова, 10 клас, с. 999"]


def test_page_range_passes_but_second_page_label_does_not() -> None:
    page_range = _result("Караман, Українська мова, 10 клас, с. 176-178")
    second_page = _result("Караман, Українська мова, 10 клас, с. 176, p.999")

    assert page_range["passed"] is True
    assert page_range["unknown"] == []
    assert second_page["passed"] is False
    assert second_page["unknown"] == ["Караман, Українська мова, 10 клас, с. 176, p.999"]


def test_unparseable_near_match_does_not_pass() -> None:
    result = _result("Караман")

    assert result["passed"] is False
    assert result["unknown"] == ["Караман"]


def test_plan_references_field_is_supported() -> None:
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Караман, Українська мова, 10 клас, с. 176"}],
        {"plan_references": [{"title": "Караман Grade 10, p.176"}]},
    )

    assert result["passed"] is True


def test_anonymous_folk_primary_resolves_against_module_primary(monkeypatch) -> None:
    monkeypatch.setattr(linear_pipeline, "_search_literary_hits", lambda *args, **kwargs: [])
    module_text = """
## Читання

> Як ще не було початку світа,
> Тогди не було неба, ні землі.

— Народна творчість, «Як ще не було початку світа»
"""
    result = linear_pipeline._citation_gate(
        [{"source_ref": "«Як ще не було початку світа» (народна творчість)"}],
        {"level": "folk", "references": []},
        module_text=module_text,
        level="folk",
    )

    assert result["passed"] is True
    assert result["unknown"] == []


def test_anonymous_folk_primary_rejects_known_author_corpus_hit(monkeypatch) -> None:
    def search_literary_hits(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [
            {
                "title": "Тарас Шевченко. Мені однаково, чи буду...",
                "text": (
                    "Мені однаково, чи буду\n\n"
                    "Я жить в Україні, чи ні.\n\n"
                    "Чи хто згадає, чи забуде"
                ),
                "source_file": "ukrlib-shevchenko",
                "author": "Шевченко Т.",
                "work": "Тарас Шевченко. Мені однаково, чи буду...",
                "genre": "poetry",
                "source_type": "literary",
                "corpus": "literary_texts",
            }
        ]

    monkeypatch.setattr(linear_pipeline, "_search_literary_hits", search_literary_hits)

    result = linear_pipeline._citation_gate(
        [{"source_ref": "Народна творчість «Мені однаково чи буду»"}],
        {"level": "lit", "references": []},
        level="lit",
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Народна творчість «Мені однаково чи буду»"]


def test_anonymous_folk_primary_rejects_known_author_module_primary(monkeypatch) -> None:
    monkeypatch.setattr(linear_pipeline, "_search_literary_hits", lambda *args, **kwargs: [])
    module_text = """
## Читання

> Мені однаково, чи буду
> Я жить в Україні, чи ні.
> Чи хто згадає, чи забуде

— Шевченко Т., «Мені однаково, чи буду»
"""

    result = linear_pipeline._citation_gate(
        [{"source_ref": "Народна творчість «Мені однаково чи буду»"}],
        {"level": "lit", "references": []},
        module_text=module_text,
        level="lit",
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Народна творчість «Мені однаково чи буду»"]


def test_fabricated_anonymous_folk_primary_still_rejected(monkeypatch) -> None:
    monkeypatch.setattr(linear_pipeline, "_search_literary_hits", lambda *args, **kwargs: [])
    module_text = """
## Читання

> Як ще не було початку світа,
> Тогди не було неба, ні землі.

— Народна творчість, «Як ще не було початку світа»
"""
    result = linear_pipeline._citation_gate(
        [{"source_ref": "«Вигаданий рядок без корпусу» (народна творчість)"}],
        {"level": "folk", "references": []},
        module_text=module_text,
        level="folk",
    )

    assert result["passed"] is False
    assert result["unknown"] == ["«Вигаданий рядок без корпусу» (народна творчість)"]


def test_my_morning_module_passes_citations_resolve() -> None:
    # Source refs must match the LIVE plan_references at curriculum/l2-uk-en/
    # plans/a1/my-morning.yaml. Citation history on this plan:
    # - PR #2014 (2026-05-15) replaced off-level `Караман Grade 10, p.187`
    #   with `Захарійчук Grade 4, p.162/163`.
    # - PR #2038 (2026-05-16, this commit) replaced Захарійчук Grade 4 (NOT
    #   in corpus per #1901) with MCP-grounded Grade 1 chunks at p.24/p.52.
    # Pinned to the current Grade 1 state.
    plan_path = linear_pipeline.PROJECT_ROOT / "curriculum/l2-uk-en/plans/a1/my-morning.yaml"
    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    result = linear_pipeline._citation_gate(
        [
            {"source_ref": "Захарійчук, Українська мова, 1 клас, с. 24"},
            {"source_ref": "Захарійчук, Українська мова, 1 клас, с. 52"},
        ],
        plan,
    )

    assert result["passed"] is True
    assert result["unknown"] == []
