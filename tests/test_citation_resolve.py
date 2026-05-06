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


def test_unknown_citation_still_rejected() -> None:
    result = _result("Tolstoy, War and Peace, p.500")

    assert result["passed"] is False
    assert result["unknown"] == ["Tolstoy, War and Peace, p.500"]


def test_partial_match_does_not_pass() -> None:
    wrong_grade = _result("Караман, Українська мова, 9 клас, с. 176")
    wrong_page = _result("Караман, Українська мова, 10 клас, с. 999")

    assert wrong_grade["passed"] is False
    assert wrong_grade["unknown"] == ["Караман, Українська мова, 9 клас, с. 176"]
    assert wrong_page["passed"] is False
    assert wrong_page["unknown"] == ["Караман, Українська мова, 10 клас, с. 999"]


def test_page_range_and_second_page_label_do_not_pass() -> None:
    page_range = _result("Караман, Українська мова, 10 клас, с. 176-178")
    second_page = _result("Караман, Українська мова, 10 клас, с. 176, p.999")

    assert page_range["passed"] is False
    assert page_range["unknown"] == ["Караман, Українська мова, 10 клас, с. 176-178"]
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


def test_my_morning_module_passes_citations_resolve() -> None:
    plan_path = linear_pipeline.PROJECT_ROOT / "curriculum/l2-uk-en/plans/a1/my-morning.yaml"
    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    result = linear_pipeline._citation_gate(
        [
            {"source_ref": "Караман, Українська мова, 10 клас, с. 176"},
            {"source_ref": "Кравцова, Українська мова, 4 клас, с. 113"},
            {"source_ref": "Захарійчук, Українська мова, 4 клас, с. 162"},
        ],
        plan,
    )

    assert result["passed"] is True
    assert result["unknown"] == []
