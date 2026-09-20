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


# --- #8236: the writer never sees a worded empty-sign choice or divide-words as allowed ---

@pytest.mark.parametrize("choice", ["без знака", "без зна́ка — no sign", "Немає знака", "No sign", "Немає знака — No sign"])
def test_whole_worded_empty_sign_choice_is_recognised(choice):
    assert am.is_empty_sign_choice(choice)


@pytest.mark.parametrize("text", ["", "ь", "'", "слово без знака", "інші слова тут без знака.", None, 3])
def test_prose_and_real_choices_are_not_empty_sign_choices(text):
    assert not am.is_empty_sign_choice(text)


def test_blank_empty_sign_choices_rewrites_only_options_and_answers():
    from scripts.build import lesson_gates

    fill = {
        "id": "act-3", "type": "fill-in",
        "instruction": "Обери ь, апо́строф або без знака. — Choose ь, an apostrophe, or no sign.",
        "items": [
            {"sentence": "свя___то", "answer": "без знака — no sign", "options": ["ь", "'", "без знака — no sign"],
             "explanation": "Тут без знака."},
            {"sentence": "ден___", "answer": "ь", "options": ["ь", "'", "Немає знака"]},
        ],
    }
    sort = {"id": "act-4", "type": "group-sort", "groups": [{"label": "Немає знака — No sign", "items": ["свято"]}]}
    data = {"inline": [fill], "workbook": [sort]}
    assert lesson_gates.fill_in_activity_defects(fill)  # the dirty original still fails the gate

    out = am.blank_empty_sign_choices(data)

    items = out["inline"][0]["items"]
    assert items[0]["answer"] == "" and items[0]["options"] == ["ь", "'", ""]
    assert items[1]["answer"] == "ь" and items[1]["options"] == ["ь", "'", ""]
    assert items[0]["explanation"] == "Тут без знака."
    assert out["inline"][0]["instruction"] == fill["instruction"]
    assert out["workbook"] == [sort]  # the sorting concept keeps its words
    assert lesson_gates.fill_in_activity_defects(out["inline"][0]) == []
    assert fill["items"][0]["answer"] == "без знака — no sign"  # input untouched


def test_non_alphabet_original_activities_keep_their_wording():
    text = yaml.safe_dump({"inline": [{"type": "fill-in", "items": [{"answer": "no sign", "options": ["no sign"]}]}]})
    assert linear_pipeline._original_artifact_for_prompt({"slug": "my-family"}, "activities.yaml", text) == text


@pytest.mark.parametrize("slug", sorted(am.ALPHABET_SLUGS))
def test_alphabet_activity_config_forbids_divide_words(slug):
    config = linear_pipeline._activity_config("a1", 3, slug)
    for key in ("INLINE_ALLOWED_TYPES", "WORKBOOK_ALLOWED_TYPES", "ALLOWED_ACTIVITY_TYPES"):
        assert "divide-words" not in config[key], key
    assert "divide-words" in config["FORBIDDEN_ACTIVITY_TYPES"]
    other = linear_pipeline._activity_config("a1", 4, "stress-and-melody")
    assert "divide-words" in other["ALLOWED_ACTIVITY_TYPES"]
    assert "divide-words" not in other["FORBIDDEN_ACTIVITY_TYPES"]


def test_alphabet_type_gate_rejects_divide_words():
    acts = [{"type": "divide-words"}]
    assert linear_pipeline._activity_type_gate(acts, "a1", 3, "special-signs")["forbidden"] == ["divide-words"]
    assert linear_pipeline._activity_type_gate(acts, "a1", 4, "stress-and-melody")["passed"]


@pytest.mark.parametrize("lesson", [None, 5])
def test_special_signs_upgrade_prompt_has_no_worded_empty_choice_or_divide_words_type(lesson):
    from scripts.build import lesson_gates

    root = linear_pipeline.PROJECT_ROOT / "curriculum/l2-uk-en"
    plan = yaml.safe_load((root / "plans/a1/special-signs.yaml").read_text(encoding="utf-8"))
    lesson_map = yaml.safe_load((root / "a1/special-signs/lessons.yaml").read_text(encoding="utf-8"))
    source = root / "a1-v1/special-signs"
    dirty = yaml.safe_load((source / "activities.yaml").read_text(encoding="utf-8"))
    assert any(lesson_gates.fill_in_activity_defects(a) for a in dirty["inline"] + dirty["workbook"])

    prompt = linear_pipeline.render_upgrade_prompt(plan, source, lesson_map, lesson=lesson)

    artifacts = _region(prompt, "## Existing module artifacts (read-only)", "## Response format")
    shown = yaml.safe_load(artifacts.split("### activities.yaml", 1)[1].split("### ", 1)[0])
    fill_ins = [a for a in shown["inline"] + shown["workbook"] if a["type"] == "fill-in"]
    assert fill_ins
    for activity in fill_ins:
        assert lesson_gates.fill_in_activity_defects(activity) == []
    assert any("" in item["options"] and item["answer"] == "" for a in fill_ins for item in a["items"])
    assert "без зна́ка" in artifacts  # the three-way contrast is still taught in prose

    for line in re.findall(r"^[A-Z_]*ALLOWED[A-Z_]*TYPES:.*(?:\n  .*)*", prompt, re.MULTILINE):
        assert "divide-words" not in line, line
    assert re.search(r"^FORBIDDEN_ACTIVITY_TYPES:.*(?:\n  .*)*divide-words", prompt, re.MULTILINE)
    assert "Do **not** teach `перенос`" in prompt
    shown_map = yaml.safe_load(_region(prompt, "## Deterministic lessons.yaml (read-only)", "## Original plan (read-only)"))
    assert "title" not in shown_map["lessons"][4] and shown_map["closes_module"] == 5  # lesson 5 stays as the close


# ── legal originals: what the upgrade writer may keep (#8236) ────────────────

def test_legal_original_activity_blanks_chips_and_omits_error_correction_options():
    ec = {"id": "act-4", "type": "error-correction", "items": [
        {"sentence": "Моя́ сімя живе́ у Ки́єві.", "error": "сімя", "correction": "сім'я́",
         "options": ["сім'я́", "сімя"], "explanation": "У слові сім'я́ потрібен апо́строф."}]}
    out = am.legal_original_activity(ec)
    assert "options" not in out["items"][0]  # never a one-chip list to clone
    assert {k: out["items"][0][k] for k in ("sentence", "error", "correction", "explanation")} == {
        k: ec["items"][0][k] for k in ("sentence", "error", "correction", "explanation")}
    assert ec["items"][0]["options"] == ["сім'я́", "сімя"]  # input untouched

    # A quiz that happens to list an ``error`` key keeps its options: EC only.
    quiz = {"type": "quiz", "items": [{"error": "сімя", "options": ["сімя", "сім'я́"]}]}
    assert am.legal_original_activity(quiz) == quiz

    sort = {"type": "group-sort", "groups": [{"label": "Немає знака — No sign", "items": ["свято"]}]}
    assert am.legal_original_activity(sort) == sort


def test_preservation_baseline_omits_error_correction_explanations_only():
    ec = {"id": "act-4", "type": "error-correction", "items": [
        {"sentence": "Моя́ сімя живе́ у Ки́єві.", "error": "сімя", "correction": "сім'я́",
         "options": ["сім'я́", "сімя"], "explanation": "У слові сім'я́ потрібен апо́строф."}]}
    assert am.preservation_baseline_activity(ec)["items"] == [
        {"sentence": "Моя́ сімя живе́ у Ки́єві.", "error": "сімя", "correction": "сім'я́"}]
    assert "explanation" in am.legal_original_activity(ec)["items"][0]  # the writer still sees it
    fill = {"type": "fill-in", "items": [{"sentence": "ден___", "answer": "ь", "options": ["ь", "'"],
                                          "explanation": "М'який знак."}]}
    assert am.preservation_baseline_activity(fill) == am.legal_original_activity(fill)


def test_upgrade_prompt_originals_match_the_preservation_baseline():
    plan = {"slug": "special-signs"}
    acts = yaml.safe_dump({"inline": [
        {"id": "act-3", "type": "fill-in", "items": [
            {"sentence": "свя___то", "answer": "без знака — no sign", "options": ["без знака — no sign", "'", "ь"]}]},
        {"id": "act-4", "type": "error-correction", "items": [
            {"sentence": "Теплий ден.", "error": "ден", "correction": "день", "options": ["день", "ден"]}]},
        {"id": "act-5", "type": "group-sort", "groups": [{"label": "Немає знака — No sign", "items": ["свято"]}]},
    ]}, allow_unicode=True)
    shown = yaml.safe_load(linear_pipeline._original_artifact_for_prompt(plan, "activities.yaml", acts))["inline"]
    assert shown[0]["items"][0]["answer"] == ""
    assert shown[0]["items"][0]["options"] == ["", "'", "ь"]
    assert "options" not in shown[1]["items"][0]
    assert shown[1]["items"][0]["error"] == "ден"
    assert shown[2]["groups"][0]["label"] == "Немає знака — No sign"
    assert shown == [am.legal_original_activity(a) for a in yaml.safe_load(acts)["inline"]]


def test_letter_module_floor_is_advisory_only_for_long_uk_and_tab3_four_of_five():
    def floor(**observed):
        required = {"uk_dialogue_lines": 0, "uk_tab3_activities": 5}
        return {"required": required, "observed": {"uk_dialogue_lines": 3, "uk_tab3_activities": 5, **observed}}

    assert am.letter_module_floor_is_advisory("long_uk_ceiling", {"offending_runs": ["— Привіт!"]})
    assert am.letter_module_floor_is_advisory("l2_exposure_floor", floor(uk_tab3_activities=4))
    assert not am.letter_module_floor_is_advisory("l2_exposure_floor", floor(uk_tab3_activities=3))
    both = floor(uk_tab3_activities=4)
    both["required"]["uk_dialogue_lines"] = 10
    assert not am.letter_module_floor_is_advisory("l2_exposure_floor", both)
    assert not am.letter_module_floor_is_advisory("component_density", {})


def test_upgrade_prompt_prose_drops_banned_phrase_paragraphs_only():
    text = ("## Знаки\n\nThree choices: ь, apostrophe, or no sign at all.\n\n"
            "Stay inside Ukrainian for this lesson. The apostrophe and soft sign already\nhave Ukrainian jobs.\n\n"
            "Before you leave the lesson\ntab, check that you can do these things:\n\n- read день\n")
    shown = linear_pipeline._original_artifact_for_prompt({"slug": "special-signs"}, "module.md", text)
    assert "Stay inside Ukrainian" not in shown
    assert "leave the lesson" not in shown
    assert "or no sign at all" in shown and "- read день" in shown
    assert linear_pipeline._original_artifact_for_prompt({"slug": "my-family"}, "module.md", text) == text


def _chai_is_word(form: str) -> bool:
    from scripts.build.alphabet_modules import _chip_key

    return _chip_key(form) in {"чаю", "чаї"}


def test_repair_drops_vesum_legal_neighbors():
    repaired = am.repair_error_correction_options(
        "чаі", "чай", ["чай", "чаї́", "чаю"], is_word=_chai_is_word,
    )
    keys = {am._chip_key(c) for c in repaired}
    assert "чай" in keys
    assert "чаю" not in keys and "чаї" not in keys
    assert len(repaired) >= 2
    assert repaired[0] == "чай"


def test_repair_never_clones_winner_or_error():
    repaired = am.repair_error_correction_options(
        "чаі", "чай", ["чай", "чаі", "чай"], is_word=lambda _w: False,
    )
    keys = [am._chip_key(c) for c in repaired]
    assert keys.count("чай") == 1
    assert "чаі" not in keys


def test_repair_mutants_keep_stress_and_are_deterministic():
    first = am.repair_error_correction_options(
        "лошка", "ло́жка", ["ло́жка", "ложка"], is_word=lambda w: am._chip_key(w) == "ложка",
    )
    second = am.repair_error_correction_options(
        "лошка", "ло́жка", ["ло́жка", "ложка"], is_word=lambda w: am._chip_key(w) == "ложка",
    )
    assert first == second
    assert first[0] == "ло́жка"
    assert "\u0301" in first[0]
    for chip in first[1:]:
        # Mutants of a stressed winner keep the acute on the same vowel beat.
        assert "\u0301" in chip or chip == first[0]


def test_repair_returns_winner_only_when_no_illegal_mutant():
    # Every mutant is declared a word → no illegal second chip.
    repaired = am.repair_error_correction_options(
        "х", "а", ["а"], is_word=lambda _w: True,
    )
    assert repaired == ["а"]


def test_repair_chai_neighbors_are_vesum_words_and_mutants_are_not():
    """Real-VESUM proof for the чай case (#7994); skip if VESUM is unavailable."""
    from scripts.verification.vesum import verify_word

    try:
        assert verify_word("чаю") or verify_word("чаю".lower())
        assert verify_word("чаї") or verify_word("чаї".lower())
    except (FileNotFoundError, OSError) as exc:  # pragma: no cover - CI / no db
        pytest.skip(f"VESUM unavailable: {exc}")
    assert am.vesum_is_word("чаю")
    assert am.vesum_is_word("чаї")
    repaired = am.repair_error_correction_options(
        "чаі", "чай", ["чай", "чаї́", "чаю"], is_word=am.vesum_is_word,
    )
    assert repaired[0] == "чай"
    assert am._chip_key("чаю") not in {am._chip_key(c) for c in repaired}
    assert am._chip_key("чаї") not in {am._chip_key(c) for c in repaired}
    for chip in repaired[1:]:
        assert not am.vesum_is_word(chip)


def test_vesum_is_word_fail_open_when_db_missing(monkeypatch):
    """Absent VESUM must not crash alphabet EC repair / render (#7994 CI)."""
    from scripts.build.activity_renderer import error_correction_render_values

    def boom(_form, **_kwargs):
        raise FileNotFoundError(
            "VESUM database not found at data/vesum.db. "
            "Step 1 builds an explicit shadow database only."
        )

    monkeypatch.setattr("scripts.verification.vesum.verify_word", boom)

    assert am.vesum_is_word("чаю") is False
    assert am.vesum_is_word("чаї") is False

    repaired = am.repair_error_correction_options(
        "чаі", "чай", ["чай", "чаї́", "чаю"], is_word=am.vesum_is_word,
    )
    assert repaired[0] == "чай"
    assert len(repaired) >= 2
    # Fail-open: legal neighbors are not dropped when VESUM cannot be consulted.
    keys = {am._chip_key(c) for c in repaired}
    assert "чаю" in keys or "чаї" in keys

    winner, options = error_correction_render_values(
        "Вра́нці я пив чаі з лимо́ном.",
        "чаі",
        "чай",
        ["чай", "чаї́", "чаю"],
        alphabet=True,
    )
    assert winner == "чай"
    assert isinstance(options, list) and len(options) >= 2
    assert options[0] == "чай"
