"""#8237: alphabet modules must not receive line-break (перенос) instructions."""
from __future__ import annotations

import re

import pytest
import yaml

from scripts.build import alphabet_modules as am
from scripts.build import linear_pipeline
from scripts.build.phases.wiki_compressor import _build_scenario_tokens, compress_wiki_packet

PLAN = {
    "slug": "special-signs",
    "level": "a1",
    "sequence": 8,
    "title": "Знаки",
    "objectives": [
        "Розрізняти ь та апостроф",
        "Користуватися готовими моделями переносу (`Мар'-яна`, `дере-в'яний`)",
    ],
    "content_outline": [
        {
            "section": "Перенос і підсумок",
            "words": 300,
            "points": ["Закріпити: `бур'-ян`, `паль-ці`.", "Повторити ь та апостроф."],
        }
    ],
    "activity_hints": [
        {"type": "divide-words", "focus": "Поділи слова для переносу: паль-ці"},
        {"type": "fill-in", "focus": "Вставити знак у слово"},
    ],
}


def test_filter_drops_line_break_text_for_alphabet_slugs_only():
    out = am.filter_line_break_plan(PLAN)
    assert out["objectives"] == ["Розрізняти ь та апостроф"]
    assert out["content_outline"][0]["section"] == "Перенос і підсумок"  # structural
    assert out["content_outline"][0]["points"] == ["Повторити ь та апостроф."]
    assert out["activity_hints"] == [{"type": "fill-in", "focus": "Вставити знак у слово"}]
    assert PLAN["objectives"][1].startswith("Користуватися")  # input untouched

    other = dict(PLAN, slug="my-family")
    assert am.filter_line_break_plan(other) == other


def test_all_three_slugs_are_covered():
    assert {"sounds-letters-and-hello", "reading-ukrainian", "special-signs"} == am.ALPHABET_SLUGS
    for slug in am.ALPHABET_SLUGS:
        assert am.filter_line_break_plan(dict(PLAN, slug=slug))["objectives"] == ["Розрізняти ь та апостроф"]


def test_wiki_compressor_scenario_tokens_ignore_line_break_objectives():
    tokens = _build_scenario_tokens(PLAN)
    assert not any("перенос" in t for t in tokens)
    assert "апостроф" in tokens


def test_compress_wiki_packet_does_not_query_on_line_break_points():
    result = compress_wiki_packet(PLAN, "")
    assert isinstance(result, dict)


def test_upgrade_prompt_drops_line_breaks_from_plan_and_original_artifacts(tmp_path):
    (tmp_path / "module.md").write_text(
        "## Знаки\n\nЦе абзац про апостроф, який ми залишаємо без змін у цьому уроці добре.\n\n"
        "## Перенос і письмо\n\n"
        "Перенос слів: Мар'-яна і дере-в'яний ділимо так у цьому абзаці сьогодні.\n",
        encoding="utf-8",
    )
    (tmp_path / "activities.yaml").write_text(yaml.safe_dump({
        "inline": [
            {"id": "a-div", "type": "divide-words", "title": "Поділ", "items": ["паль-ці"]},
            {"id": "a-fill", "type": "fill-in", "title": "Вставте знак", "items": []},
        ],
        "workbook": [],
    }, allow_unicode=True), encoding="utf-8")
    (tmp_path / "vocabulary.yaml").write_text("[]", encoding="utf-8")
    (tmp_path / "resources.yaml").write_text(yaml.safe_dump([
        {"title": "Вашуленко, 3 клас, p. 90", "role": "textbook",
         "notes": "Line-break rule: apostrophe is not separated from the previous letter."},
    ], allow_unicode=True), encoding="utf-8")

    prompt = linear_pipeline.render_upgrade_prompt(PLAN, tmp_path, {"lessons": []}, lesson=1)

    assert "## Перенос і письмо" not in prompt  # the heading is an order too
    assert "Вашуленко, 3 клас, p. 90" in prompt  # the source stays, its line-break note goes
    assert "Line-break rule" not in prompt
    assert "a-fill" in prompt
    assert "a-div" not in prompt
    assert "Мар'-яна і дере-в'яний ділимо" not in prompt  # original paragraph dropped
    assert "залишаємо без змін" in prompt
    assert "Користуватися готовими моделями переносу" not in prompt
    assert "Поділи слова для переносу" not in prompt


def test_writer_context_plan_content_is_filtered_for_alphabet_slug():
    text = linear_pipeline._plan_content_for_prompt(PLAN, yaml.safe_dump(PLAN, allow_unicode=True))
    assert "переносу" not in text
    assert "divide-words" not in text
    same = yaml.safe_dump(dict(PLAN, slug="my-family"), allow_unicode=True)
    assert linear_pipeline._plan_content_for_prompt(dict(PLAN, slug="my-family"), same) == same


def test_writer_prompts_forbid_line_breaks_and_error_token():
    root = linear_pipeline.PROJECT_ROOT / "scripts" / "build" / "phases"
    for name in ("linear-write.md", "linear-write-upgrade.md"):
        text = (root / name).read_text(encoding="utf-8")
        for slug in am.ALPHABET_SLUGS:
            assert slug in text, (name, slug)
        for model in ("Мар'-яна", "дере-в'яний", "бур'-ян", "паль-ці"):
            assert model in text, (name, model)
        assert "divide-words" in text
        assert re.search(r"NOT\s+contain\s+the\s+(?:spotted\s+)?`error`", text), name  # rule 3
        assert "кінь" in text
        assert '`""`' in text  # empty-string fill-in contract


@pytest.mark.parametrize("text", [
    "You will sometimes see words split across a line in printed Ukrainian.",
    "words split across\na line",
    "Word Hyphenation Rules",
    "do not hyphenate",
    "Пра́вила перено́су слів",  # published titles carry stress marks
    "Safe line-break model",
    "Do not leave one single letter alone on a line.",
])
def test_matcher_catches_the_paraphrases_the_archive_uses(text):
    assert am.mentions_line_breaks(text)


@pytest.mark.parametrize("text", [
    "ма-ма, та-то, мо-ло-ко",
    "Поділи слово на склади: кни-га.",
    "Склади — Syllables",
    "UA — EN hyphen-free line of text",
    "Read each line aloud.",
    "буря́к, бур'я́н, свя́то",
])
def test_matcher_leaves_syllables_alone(text):
    assert not am.mentions_line_breaks(text)


def test_lesson_map_filter_drops_the_line_break_lesson_but_keeps_budgets():
    lesson_map = {
        "lessons": [
            {"n": 1, "title": "Апо́строф · The Apostrophe", "sections": ["Апостроф"],
             "minutes": 60, "word_target": 550},
            {"n": 2, "title": "Пра́вила перено́су слів · Word Hyphenation Rules",
             "sections": ["Перенос і письмо", "Далі"], "minutes": 60, "word_target": 550},
        ],
        "closes_module": 2,
        "provenance": [
            {"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1},
            {"placement": "inline", "index": 1, "new_id": "act-5", "lesson": 2},
        ],
        "items_min_exempt": [{"id": "act-1", "reason": "r"}, {"id": "act-5", "reason": "r"}],
    }
    out = am.filter_line_break_lesson_map(lesson_map, {("inline", 1)})
    assert out["lessons"][0] == lesson_map["lessons"][0]
    assert out["lessons"][1] == {"n": 2, "sections": ["Далі"], "minutes": 60, "word_target": 550}
    assert [p["new_id"] for p in out["provenance"]] == ["act-1"]
    assert out["items_min_exempt"] == [{"id": "act-1", "reason": "r"}]
    assert out["closes_module"] == 2
    assert lesson_map["lessons"][1]["sections"] == ["Перенос і письмо", "Далі"]  # input untouched


SPECIAL_SIGNS_FORBIDDEN = (
    "перенос", "Перенос", "divide-words", "Мар'-яна", "дере-в'яний", "бур'-ян", "паль-ці",
    "line-break", "line break", "split across a line", "prepared models", "hyphenat",
)


def _region(prompt: str, start: str, end: str) -> str:
    return prompt.split(start, 1)[1].split(end, 1)[0]


@pytest.mark.parametrize("lesson", [None, 5])
def test_special_signs_upgrade_prompt_has_no_hyphenation_lesson(monkeypatch, lesson):
    """The real five-lesson map and a1-v1 sources, rendered with no model call."""
    monkeypatch.setattr(
        linear_pipeline, "invoke_writer",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("called a model")),
    )
    root = linear_pipeline.PROJECT_ROOT / "curriculum/l2-uk-en"
    plan = yaml.safe_load((root / "plans/a1/special-signs.yaml").read_text(encoding="utf-8"))
    lesson_map = yaml.safe_load((root / "a1/special-signs/lessons.yaml").read_text(encoding="utf-8"))
    assert len(lesson_map["lessons"]) == 5
    assert "Перенос і письмо" in lesson_map["lessons"][4]["sections"]  # the input does carry it

    prompt = linear_pipeline.render_upgrade_prompt(plan, root / "a1-v1/special-signs", lesson_map, lesson=lesson)

    shown_map = _region(prompt, "## Deterministic lessons.yaml (read-only)", "## Original plan (read-only)")
    artifacts = _region(prompt, "## Existing module artifacts (read-only)", "## Response format")
    for region in (shown_map, artifacts):
        plain = region.replace("\u0301", "")
        for token in SPECIAL_SIGNS_FORBIDDEN:
            assert token not in region, token
            assert token not in plain, token
    shown = yaml.safe_load(shown_map)
    assert [L["n"] for L in shown["lessons"]] == [1, 2, 3, 4, 5]  # five lessons stay
    assert shown["lessons"][4]["sections"] == ["Далі", "Підсумок модуля"]
    assert shown["lessons"][4]["word_target"] == 550
    assert "act-5" not in {p["new_id"] for p in shown["provenance"]}
    assert "act-5" not in {e["id"] for e in shown["items_min_exempt"]}
    assert "act-4" in {p["new_id"] for p in shown["provenance"]}
    assert "## Контраст і пастки" in artifacts and "## Далі" in artifacts


def test_prompt_plan_copy_renames_the_hyphenation_section_and_keeps_its_budget():
    assert am.strip_line_break_title("Перенос і підсумок") == "Підсумок"
    assert am.strip_line_break_title("Апостроф") == "Апостроф"
    assert am.strip_line_break_title("Правила переносу · Word Hyphenation Rules") == ""

    shown = am.line_break_free_titles(PLAN)
    assert shown["content_outline"][0]["section"] == "Підсумок"
    assert shown["content_outline"][0]["words"] == 300
    assert PLAN["content_outline"][0]["section"] == "Перенос і підсумок"  # input untouched
    # The gate's plan keeps the structural title.
    assert am.filter_line_break_plan(PLAN)["content_outline"][0]["section"] == "Перенос і підсумок"

    only = dict(PLAN, content_outline=[{"section": "Перенос", "words": 100}, {"section": "Апостроф", "words": 200}])
    assert [s["section"] for s in am.line_break_free_titles(only)["content_outline"]] == ["Апостроф"]

    other = dict(PLAN, slug="my-family")
    assert am.line_break_free_titles(other) == other
    assert "Перенос" not in linear_pipeline._plan_content_for_prompt(PLAN, yaml.safe_dump(PLAN, allow_unicode=True))


@pytest.mark.parametrize("lesson", [None, 5])
def test_special_signs_upgrade_prompt_original_plan_has_no_hyphenation_title(lesson):
    """Live plan + live lessons.yaml, both read unchanged from disk (#8237 r2)."""
    root = linear_pipeline.PROJECT_ROOT / "curriculum/l2-uk-en"
    plan_path = root / "plans/a1/special-signs.yaml"
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "section: Перенос і підсумок" in plan_text  # the file does carry it
    plan = yaml.safe_load(plan_text)
    lesson_map = yaml.safe_load((root / "a1/special-signs/lessons.yaml").read_text(encoding="utf-8"))

    prompt = linear_pipeline.render_upgrade_prompt(plan, root / "a1-v1/special-signs", lesson_map, lesson=lesson)

    region = _region(prompt, "## Original plan (read-only)", "## Existing module artifacts (read-only)")
    for token in (*SPECIAL_SIGNS_FORBIDDEN, "Line Breaks"):
        assert token not in region.replace("\u0301", ""), token
    shown = yaml.safe_load(region)
    original = {s["section"]: s["words"] for s in plan["content_outline"]}
    sections = {s["section"]: s["words"] for s in shown["content_outline"]}
    assert sections["Підсумок"] == original["Перенос і підсумок"]  # word budget stays
    assert len(sections) == len(original)
    assert plan_path.read_text(encoding="utf-8") == plan_text


def test_no_line_break_english_title_exists_for_the_alphabet_section():
    aliases = linear_pipeline._A1_M1_M7_SECTION_ALIASES
    assert not any(am.mentions_line_breaks(a) or "Line Break" in a for v in aliases.values() for a in v)
    keys = linear_pipeline._section_heading_keys_for_plan_section("Перенос і підсумок", "a1-script-building")
    assert "Підсумок" in keys and "Textbook Check" in keys  # the heading the writer was given passes the gate


def test_live_special_signs_lessons_yaml_still_points_at_the_dropped_original():
    """The gate must cope with this row as-is; nobody removes it by hand."""
    from scripts.build.lesson_map import _normalize_activities

    root = linear_pipeline.PROJECT_ROOT / "curriculum/l2-uk-en"
    source = root / "a1-v1/special-signs"
    base = _normalize_activities((source / "module.md").read_text(encoding="utf-8"),
                                 yaml.safe_load((source / "activities.yaml").read_text(encoding="utf-8")))
    dropped = am.line_break_original_keys(base)
    lesson_map = yaml.safe_load((root / "a1/special-signs/lessons.yaml").read_text(encoding="utf-8"))
    assert dropped and dropped <= {(p["placement"], p["index"]) for p in lesson_map["provenance"]}
