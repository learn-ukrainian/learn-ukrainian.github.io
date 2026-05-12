from pathlib import Path

from scripts.build.linear_pipeline import (
    _advisory_immersion_pct,
    _long_uk_ceiling_gate,
    _long_ukrainian_sentences,
    _split_immersion_sentences,
)

PLAN = {"level": "a1", "sequence": 15}


def test_em_dash_line_start_is_sentence_boundary() -> None:
    text = "Що ти робиш?\n— Вмиваюся.\n–Одягаюся.\n- Снідаю."

    sentences = _split_immersion_sentences(text)

    assert sentences == ["Що ти робиш", "— Вмиваюся", "–Одягаюся", "- Снідаю"]
    assert _long_ukrainian_sentences(text) == []


def test_markdown_table_rows_split() -> None:
    text = """| Особа | Форма |
|---|---|
| я | прокидаюся вранці швидко спокійно вдома |
| ти | вмиваєшся після сну повільно у ванній |
| вона | снідає рано вдома з мамою |
| ми | йдемо на роботу о восьмій |"""

    sentences = _split_immersion_sentences(text)

    assert len(sentences) >= 4
    assert _long_ukrainian_sentences(text) == []


def test_bullet_items_split() -> None:
    text = """- Прокидаюся о сьомій
- Вмиваюся швидко
- Снідаю вдома"""

    sentences = _split_immersion_sentences(text)

    assert sentences == [
        "- Прокидаюся о сьомій",
        "- Вмиваюся швидко",
        "- Снідаю вдома",
    ]
    assert _long_ukrainian_sentences(text) == []


def test_blockquote_dialogue_split() -> None:
    text = "> **Ліна:** Я прокидаюся о сьомій.\n> **Настя:** Я снідаю вдома."

    sentences = _split_immersion_sentences(text)

    assert sentences == ["> **Ліна:** Я прокидаюся о сьомій", "> **Настя:** Я снідаю вдома"]


def test_closing_markdown_and_quotes_do_not_block_sentence_boundary() -> None:
    text = "**«Спочатку я прокидаюся.»**  \n**«Потім вмиваюся.»**"

    sentences = _split_immersion_sentences(text)

    assert sentences == ["**«Спочатку я прокидаюся", "**«Потім вмиваюся"]


def test_opening_quotes_before_dialogue_dash_split() -> None:
    text = "«— Привіт»\n“— Як справи?”"

    sentences = _split_immersion_sentences(text)

    assert sentences == ["«— Привіт»", "“— Як справи"]


def test_markdown_hard_break_splits_pattern_lines() -> None:
    text = "**вмивати → я вмиваю → я вмиваюся**  \n**одягати → ти одягаєш → ти одягаєшся**"

    sentences = _split_immersion_sentences(text)

    assert sentences == [
        "**вмивати → я вмиваю → я вмиваюся**",
        "**одягати → ти одягаєш → ти одягаєшся**",
    ]


def test_markdown_header_terminates_prior_sentence() -> None:
    text = """Прокидаюся вранці без крапки
## Ранок і щоденні звички учня
Снідаю вдома."""

    sentences = _split_immersion_sentences(text)

    assert sentences == ["Прокидаюся вранці без крапки", "Снідаю вдома"]


def test_code_fence_excluded_or_split() -> None:
    long_code = " ".join(
        [
            "прокидаюся",
            "вмиваюся",
            "одягаюся",
            "снідаю",
            "працюю",
            "читаю",
            "пишу",
            "слухаю",
            "повторюю",
            "навчаюся",
            "відпочиваю",
        ]
    )
    text = f"```md\n{long_code}\n```"

    assert _long_ukrainian_sentences(text) == []


def test_real_long_sentence_still_caught() -> None:
    long_sentence = " ".join(
        [
            "Український",
            "студент",
            "повільно",
            "прокидається",
            "вмивається",
            "одягається",
            "снідає",
            "планує",
            "повторює",
            "записує",
            "читає",
            "слухає",
            "практикує",
            "розповідає",
            "запитує",
            "відповідає",
            "працює",
            "навчається",
            "уважно",
            "щодня",
        ]
    )

    assert _long_ukrainian_sentences(long_sentence) == [long_sentence]


def test_long_uk_ceiling_gate_fails_real_long_sentence() -> None:
    long_sentence = " ".join(
        [
            "Український",
            "студент",
            "повільно",
            "прокидається",
            "вмивається",
            "одягається",
            "снідає",
            "планує",
            "повторює",
            "записує",
            "читає",
            "слухає",
            "практикує",
            "розповідає",
            "запитує",
            "відповідає",
        ]
    )

    # Use an early A1 band (a1-m01-03, calibrated max_unsupported_uk_words=10)
    # so the 16-word unsupported UK run trips the gate. The module-level PLAN
    # sits in a1-m15-24 (calibrated cap=28) where 16 words is within ceiling.
    early_plan = {"level": "a1", "sequence": 1}
    result = _long_uk_ceiling_gate(long_sentence, early_plan)

    assert result["passed"] is False
    assert result["reason"] == "long_uk_without_gloss"
    assert result["offending_runs"] == [long_sentence]


def test_advisory_immersion_pct_reports_a1_m15_24_policy_cap() -> None:
    result = _advisory_immersion_pct(
        "English scaffold with **ранок** and **вмиваюся**.",
        PLAN,
    )

    assert result["policy"] == "a1-m15-24"
    assert result["max_pct"] == 24
    assert result["passed"] is True


def test_my_morning_immersion_passes() -> None:
    fixture = Path("audit/bakeoff-2026-05-05/claude/module.md")
    if fixture.exists():
        text = fixture.read_text(encoding="utf-8")
    else:
        text = """English context keeps the A1 immersion ratio bounded for learners.
This short grammar note explains the morning routine pattern in plain English.
Learners read the examples, notice the endings, compare the forms, and then
practice the dialogue aloud with a partner before writing their own version.
The surrounding English is intentionally present because early A1 modules need
clear scaffolding and should not become full immersion lessons yet.
Additional English teacher notes keep this compact fixture inside the stricter
policy cap while the Ukrainian examples remain available for sentence checks.

Що ти робиш потім?**
— **Вмиваюся, одягаюся, снідаю.**
— **А коли ти йдеш на роботу?**
— **О восьмій

| Особа | Форма |
|---|---|
| я | прокидаюся |
| ти | прокидаєшся |
| вона | прокидається |
"""

    result = _advisory_immersion_pct(text, PLAN)

    assert result["min_pct"] <= result["pct"] <= result["max_pct"]
