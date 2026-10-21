"""#8237: alphabet modules must not receive line-break (перенос) instructions."""
from __future__ import annotations

import pytest

from scripts.build import alphabet_modules as am

pytestmark = pytest.mark.reads_content


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


# --- #8236: the writer never sees a worded empty-sign choice or divide-words as allowed ---


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


# ── legal originals: what the upgrade writer may keep (#8236) ────────────────


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


def test_persist_cloned_winner_yaml_unique_and_no_contradiction(monkeypatch):
    """Cloned [corr, corr, corr] after persist is unique; contradictions() empty."""
    from scripts.build.lesson_gates import contradictions

    monkeypatch.setattr("scripts.build.alphabet_modules.vesum_is_word", lambda _w: False)
    acts = {
        "inline": [
            {
                "id": "act-lozhka",
                "type": "error-correction",
                "instruction": "Fix",
                "items": [
                    {
                        "sentence": "Це ло́шка.",
                        "error": "ло́шка",
                        "correction": "ло́жка",
                        "options": ["ло́жка", "ло́жка", "ло́жка"],
                        "explanation": "Write ж.",
                    },
                    {
                        "sentence": "Моя́ сімя́.",
                        "error": "сімя́",
                        "correction": "сім'я́",
                        "options": ["сім'я́", "сім'я́"],
                        "explanation": "Apostrophe after м.",
                    },
                ],
            }
        ],
        "workbook": [],
    }
    out = am.persist_alphabet_ec_options(acts)
    for item in out["inline"][0]["items"]:
        opts = item["options"]
        assert isinstance(opts, list) and len(opts) >= 2
        keys = [am._chip_key(c) for c in opts]
        assert len(keys) == len(set(keys))
        assert keys[0] == am._chip_key(item["correction"])
    assert contradictions(
        {k: v for k, v in out["inline"][0].items() if k == "items"},
        "act-lozhka",
    ) == []


def test_persist_drops_chip_so_yaml_lacks_din(monkeypatch):
    """If repair drops дінь, persisted YAML no longer contains it (no render-lacks)."""
    monkeypatch.setattr(
        "scripts.build.alphabet_modules.vesum_is_word",
        lambda w: am._chip_key(w) == "дінь",
    )
    acts = {
        "inline": [
            {
                "id": "act-4",
                "type": "error-correction",
                "items": [
                    {
                        "sentence": "Сього́дні га́рний ден.",
                        "error": "ден",
                        "correction": "день",
                        "options": ["день", "дінь", "деннь"],
                    }
                ],
            }
        ],
        "workbook": [
            {
                "id": "act-w-din",
                "type": "error-correction",
                "items": [
                    {
                        "sentence": "Це мій ден.",
                        "error": "ден",
                        "correction": "день",
                        "options": ["день", "дінь"],
                    }
                ],
            }
        ],
    }
    out = am.persist_alphabet_ec_options(acts)
    for placement in ("inline", "workbook"):
        opts = out[placement][0]["items"][0]["options"]
        assert all(am._chip_key(c) != "дінь" for c in opts)
        assert "дінь" not in opts


def test_persist_fills_missing_options(monkeypatch):
    monkeypatch.setattr("scripts.build.alphabet_modules.vesum_is_word", lambda _w: False)
    acts = {
        "inline": [
            {
                "type": "error-correction",
                "items": [
                    {
                        "sentence": "Це лошка.",
                        "error": "лошка",
                        "correction": "ло́жка",
                        # no options key — assembler fills
                    }
                ],
            }
        ],
        "workbook": [],
    }
    out = am.persist_alphabet_ec_options(acts)
    opts = out["inline"][0]["items"][0]["options"]
    assert isinstance(opts, list) and len(opts) >= 2
    assert opts[0] == "ло́жка"
