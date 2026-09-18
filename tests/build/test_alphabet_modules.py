"""#8237: alphabet modules must not receive line-break (перенос) instructions."""
from __future__ import annotations

import re

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
    (tmp_path / "resources.yaml").write_text("[]", encoding="utf-8")

    prompt = linear_pipeline.render_upgrade_prompt(PLAN, tmp_path, {"lessons": []}, lesson=1)

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
