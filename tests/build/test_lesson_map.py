"""Held-out fixtures preserve pinned Git content without runtime Git or network."""
import copy

import pytest
import yaml

from scripts.build.lesson_map import derive_lesson_map, source_sections, validate_lesson_map
from tests.build.upgrade_fixtures import (
    ORIGINAL as MODULE,
)
from tests.build.upgrade_fixtures import (
    fixture_text,
    load_upgrade_fixtures,
)


@pytest.fixture
def baseline():
    return (
        yaml.safe_load(fixture_text("baseline", "curriculum/l2-uk-en/plans/a1/things-have-gender.yaml")),
        fixture_text("baseline", f"{MODULE}/module.md"),
        yaml.safe_load(fixture_text("baseline", f"{MODULE}/activities.yaml")),
    )


def test_derivation_matches_held_out_gold_sections_and_provenance(baseline):
    gold = yaml.safe_load(fixture_text("gold", "curriculum/l2-uk-en/a1/things-have-gender/lessons.yaml"))
    result = derive_lesson_map(*baseline)
    assert [lesson["sections"] for lesson in result["lessons"]] == [lesson["sections"] for lesson in gold["lessons"]]
    assert result["closes_module"] == gold["closes_module"]
    assert result["provenance"] == gold["provenance"]
    assert {item["id"] for item in result["items_min_exempt"]} == {item["id"] for item in gold["items_min_exempt"]}
    assert "__intro__" in source_sections(baseline[1])
    assert result == derive_lesson_map(*baseline)
    validate_lesson_map(gold)


def test_generic_ordered_packing_and_workbook_allocation():
    # Original workbook order has no section anchors: proportional assignment is
    # only a stable placement proposal, not inferred semantic topic ownership.
    plan = {"content_outline": [{"section": title, "words": words} for title, words in
                                [("First", 280), ("Second", 280), ("Third", 400), ("Close", 200)]]}
    prose = "Intro\n## First\nA\n## Second\nB\n## Third\nC\n## Close\nD\n## Extra\nE\n"
    result = derive_lesson_map(plan, prose, {"workbook": [{"type": "quiz"} for _ in range(5)]})
    assert [lesson["sections"] for lesson in result["lessons"]] == [["First", "Second"], ["Third"], ["Close", "Extra"]]
    assert [row["lesson"] for row in result["provenance"]] == [1, 2, 2, 3, 3]
    assert [row["new_id"] for row in result["provenance"]] == [f"act-w{n}" for n in range(1, 6)]


def test_acute_normalization_and_fenced_headings():
    sections = source_sections("Intro\n```md\n## Hidden\n```\n## Ca\u0301fe\nText\n")
    assert list(sections) == ["__intro__", "Cafe"]
    assert "## Hidden" in sections["__intro__"]


@pytest.mark.parametrize("mutation", [
    lambda m: m["lessons"][0].update(word_target=549),
    lambda m: m.update(closes_module=1),
    lambda m: m["lessons"][1]["sections"].append(m["lessons"][0]["sections"][0]),
    lambda m: m["provenance"][0].update(lesson=99),
    lambda m: m["provenance"].append(copy.deepcopy(m["provenance"][0])),
    lambda m: m["lessons"][0].update(unverified_stress=[str(n) for n in range(11)]),
])
def test_invalid_map_fails_closed(baseline, mutation):
    mapping = derive_lesson_map(*baseline)
    mutation(mapping)
    with pytest.raises(ValueError):
        validate_lesson_map(mapping)


def test_missing_outline_heading_fails(baseline):
    plan, prose, activities = baseline
    plan["content_outline"][0]["section"] = "Absent"
    with pytest.raises(ValueError, match="every outline section"):
        derive_lesson_map(plan, prose, activities)


def test_orphan_and_duplicate_inline_markers_fail(baseline):
    plan, prose, activities = baseline
    with pytest.raises(ValueError, match="Duplicate inline"):
        derive_lesson_map(plan, prose + "\n<!-- INJECT_ACTIVITY: act-1 -->", activities)
    with pytest.raises(ValueError, match="no original"):
        derive_lesson_map(plan, prose + "\n<!-- INJECT_ACTIVITY: unknown -->", activities)


def test_missing_inline_marker_fails(baseline):
    plan, prose, activities = baseline
    with pytest.raises(ValueError, match="source marker"):
        derive_lesson_map(plan, prose.replace("<!-- INJECT_ACTIVITY: act-1 -->", ""), activities)


@pytest.mark.parametrize("words", [0, -1, True, "300"])
def test_invalid_final_outline_budget_fails(baseline, words):
    plan, prose, activities = baseline
    plan["content_outline"][-1]["words"] = words
    with pytest.raises(ValueError, match="positive integer"):
        derive_lesson_map(plan, prose, activities)


def test_all_held_out_fixture_hashes_and_denominator():
    bundle = load_upgrade_fixtures()
    assert len(bundle["sources"]["baseline"]["files"]) == 5
    assert len(bundle["sources"]["gold"]["files"]) == 15
    assert bundle["sources"]["gold"]["files"]["docs/poc/poc-lesson-split-design.html"]["source_sha256"] == "935c9b632b89b0b4bc3dd124bced27743a93b3dba7a924b8ece5ff28d01a91b6"
