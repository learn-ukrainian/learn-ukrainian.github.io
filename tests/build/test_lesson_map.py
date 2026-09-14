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


def test_mismatched_outline_packs_source_headings():
    filler = "word " * 200
    plan = {"content_outline": [
        {"section": "План А", "words": 300},
        {"section": "План Б", "words": 300},
        {"section": "Підсумок", "words": 150},
    ]}
    prose = (
        "Intro\n"
        f"## Sound First\n{filler}\n"
        f"## Vowels\n{filler}\n"
        f"## Consonants\n{filler}\n"
        f"## Conversation\n{filler}\n"
        "## Close\nend\n"
        "<!-- INJECT_ACTIVITY: act-1 -->\n"
    )
    activities = {"inline": [{"id": "act-1", "type": "quiz", "items": [{}] * 6}],
                  "workbook": [{"type": "quiz"} for _ in range(6)]}
    result = derive_lesson_map(plan, prose, activities)
    assert len(result["lessons"]) == 3
    assert result["lessons"][0]["sections"] == ["Sound First", "Vowels", "Consonants"]
    assert result["lessons"][1]["sections"] == ["Conversation"]
    assert result["lessons"][2]["sections"] == ["Close"]
    assert result["closes_module"] == 3
    assert all(L["activities"]["total"] >= 10 for L in result["lessons"])


def test_source_heading_pack_can_exceed_three_lessons():
    filler = "word " * 300
    plan = {"content_outline": [
        {"section": "UnusedA", "words": 200},
        {"section": "UnusedB", "words": 200},
    ]}
    names = ["A", "B", "C", "D", "E", "F"]
    prose = "Intro\n" + "".join(f"## {name}\n{filler}\n" for name in names)
    prose += "<!-- INJECT_ACTIVITY: act-1 -->\n"
    activities = {"inline": [{"id": "act-1", "type": "quiz", "items": [{}] * 6}],
                  "workbook": [{"type": "quiz"} for _ in range(8)]}
    result = derive_lesson_map(plan, prose, activities)
    assert len(result["lessons"]) >= 4
    assert result["closes_module"] == len(result["lessons"])
    assert result["lessons"][-1]["sections"] == ["F"]


def test_list_activities_split_by_inject_markers():
    plan = {"content_outline": [
        {"section": "First", "words": 280},
        {"section": "Second", "words": 280},
        {"section": "Close", "words": 200},
    ]}
    prose = (
        "Intro\n## First\nA\n<!-- INJECT_ACTIVITY: act-1 -->\n"
        "## Second\nB\n## Close\nC\n"
    )
    activities = [
        {"id": "act-1", "type": "quiz", "items": [{}] * 6},
        {"id": "act-2", "type": "quiz", "items": [{}] * 6},
        {"id": "act-3", "type": "quiz", "items": [{}] * 6},
    ]
    result = derive_lesson_map(plan, prose, activities)
    inline = [row for row in result["provenance"] if row["placement"] == "inline"]
    workbook = [row for row in result["provenance"] if row["placement"] == "workbook"]
    assert inline == [{"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1}]
    assert [row["new_id"] for row in workbook] == ["act-2", "act-3"]


def test_missing_outline_heading_no_longer_hard_fails(baseline):
    plan, prose, activities = baseline
    plan["content_outline"][0]["section"] = "Absent"
    result = derive_lesson_map(plan, prose, activities)
    assert result["lessons"]
    assert result["closes_module"] == len(result["lessons"])


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
