"""Tests for contract generation and wiki compression."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.phases.plan_contract import build_contract
from build.phases.wiki_compressor import compress_wiki_packet
from build.v6_build import _build_wiki_packet


@pytest.mark.parametrize(
    ("level", "slug"),
    [
        ("a1", "sounds-letters-and-hello"),
        ("a2", "a2-bridge"),
        ("b1", "verb-formation-suffixes"),
    ],
)
def test_real_plan_and_wiki_pairs_produce_contract(level: str, slug: str) -> None:
    plan_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / level / f"{slug}.yaml"
    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    packet = _build_wiki_packet(level, slug)

    contract, excerpts = build_contract(
        plan,
        packet,
        level=level,
        slug=slug,
        module_num=int(plan["sequence"]),
    )

    assert contract["module"]["slug"] == slug
    assert contract["teaching_beats"]["section_order"]
    assert "dialogue_acts" in contract  # may be [] for phonetics/skills modules
    assert contract["activity_obligations"]
    assert contract["section_word_budgets"]
    assert excerpts["sections"]
    assert excerpts["factual_anchors"]

    first_section = contract["teaching_beats"]["sections"][0]
    assert first_section["factual_anchors"]
    assert first_section["word_budget"]["min"] <= first_section["word_budget"]["target"]


def test_contract_builder_fails_fast_without_required_plan_fields() -> None:
    # content_outline is required
    with pytest.raises(Exception, match="content_outline"):
        build_contract(
            {
                "dialogue_situations": [],
                "activity_hints": [{"id": "quiz", "type": "quiz", "focus": "x"}],
                "word_target": 100,
            },
            "",
            level="a1",
            slug="broken",
            module_num=1,
        )


def test_contract_builder_accepts_plan_without_dialogue_situations() -> None:
    """Phonetics/skills modules legitimately have no dialogue situations.
    The contract should produce dialogue_acts: [] rather than failing.
    """
    contract, _ = build_contract(
        {
            "content_outline": [{"section": "Syllables", "words": 200, "points": ["Count vowels."]}],
            "activity_hints": [{"id": "quiz", "type": "quiz", "focus": "syllable count"}],
            "word_target": 200,
        },
        "",
        level="a1",
        slug="reading-ukrainian",
        module_num=2,
    )
    assert contract["dialogue_acts"] == []
    assert contract["module"]["slug"] == "reading-ukrainian"


def test_wiki_compressor_uses_dialogue_situations_for_dialogue_sections() -> None:
    plan = {
        "content_outline": [
            {
                "section": "Діалоги (Dialogues)",
                "points": ["Build a short natural service exchange."],
            }
        ],
        "dialogue_situations": [
            {
                "setting": "Ordering at a café",
                "speakers": ["Клієнт", "Офіціантка"],
                "motivation": "order coffee politely",
            }
        ],
    }
    wiki_packet = (
        "### Вікі: pedagogy/a1/i-want-i-can.md\n\n"
        "## Overview\n\n"
        "хотіти, могти, мушу. General modal overview.\n\n"
        "### Вікі: pedagogy/a1/at-the-cafe.md\n\n"
        "## Overview\n\n"
        "Можна мені, будь ласка, каву? Що можете порадити?\n"
    )

    compression = compress_wiki_packet(plan, wiki_packet)
    excerpts = compression["section_excerpts"]["Діалоги (Dialogues)"]

    assert excerpts
    assert excerpts[0]["source_path"] == "pedagogy/a1/at-the-cafe.md"


# #1282 — scenario-aware excerpt selection.
#
# The fixture below simulates the real failure mode the issue reported: a
# scenario-specific wiki article (``at-the-cafe.md``) coexisting with a
# generic, token-dense article (``i-eat-i-drink.md``) that could win on raw
# overlap. Exercises (1) ##-heading split, (2) scenario-token + article-path
# bonus, (3) determinism across repeated runs, (4) selection-trace shape.


_CAFE_PLAN = {
    "slug": "at-the-cafe",
    "title": "У кафе",
    "subtitle": "У кафе — замовлення, оплата та культура кафе",
    "objectives": [
        "Замовляти їжу та напої в українському кафе",
        "Розуміти українську культуру кафе",
    ],
    "content_outline": [
        {
            "section": "Діалоги",
            "words": 300,
            "points": [
                "Діалог 1 — Замовлення в кафе. — Добрий день! Ось меню.",
                "Діалог 2 — Оплата рахунку. Можна карткою?",
            ],
        },
        {
            "section": "Як замовити",
            "words": 300,
            "points": ["Мені каву, будь ласка. Можна воду?"],
        },
    ],
    "dialogue_situations": [
        {
            "setting": "Замовлення в кафе — кава, чай, тістечко, меню, рахунок",
            "speakers": ["Клієнт", "Офіціантка"],
            "motivation": "Замовлення та оплата в українському кафе",
        }
    ],
    "activity_hints": [{"id": "quiz", "type": "quiz", "focus": "x"}],
    "word_target": 1200,
}


_CAFE_PACKET = (
    # A realistic generic article — food/drink verbs and vocabulary, but no
    # cafe-specific ordering / payment vocabulary. This is the kind of
    # article that coexists in the same knowledge packet as the scenario
    # one and that the ranker must not over-promote on shared food tokens.
    "### Вікі: pedagogy/a1/i-eat-i-drink.md\n\n"
    "## Методичний підхід\n\n"
    "Дієслова їсти і пити на рівні A1. Базова харчова лексика: хліб, "
    "молоко, сік, чай, кава, вода. Відмінювання теперішнього часу. "
    "Формування простих речень про харчування вдома.\n\n"
    "## Приклади\n\n"
    "Я їм хліб. Я п'ю молоко. Ти їси суп. Він п'є чай вранці.\n\n"
    # The scenario-specific article — shares some food tokens with the
    # generic one (кава, чай, вода) but owns the cafe-situation vocabulary.
    "### Вікі: pedagogy/a1/at-the-cafe.md\n\n"
    "## Методичний підхід\n\n"
    "Сценарій кафе — основа комунікативного навчання A1. Ввічливе "
    "замовлення, оплата рахунку, культура чайових у кафе.\n\n"
    "## Приклади з підручників\n\n"
    "Добрий день, ось меню. Мені каву, будь ласка. Можна рахунок, будь "
    "ласка? Так, звичайно. З вас 250 гривень. Оплата карткою чи "
    "готівкою?\n"
)


def test_wiki_compressor_promotes_scenario_article_over_generic_token_winner() -> None:
    """#1282 AC-1/AC-2: scenario-specific article wins over a generic
    article with higher raw token overlap.

    ``i-eat-i-drink.md`` is padded with cafe-adjacent tokens on purpose so
    the pre-fix ranker would score it competitively; the fix must still pick
    ``at-the-cafe.md`` thanks to the plan-slug article bonus."""
    compression = compress_wiki_packet(_CAFE_PLAN, _CAFE_PACKET)
    dialog_items = compression["section_excerpts"]["Діалоги"]
    assert dialog_items, "Діалоги section must have picks"
    assert dialog_items[0]["source_path"] == "pedagogy/a1/at-the-cafe.md"
    assert dialog_items[0]["score_breakdown"]["article"] == 3
    assert dialog_items[0]["score_breakdown"]["scenario"] >= 1


def test_wiki_compressor_splits_on_h2_headings() -> None:
    """#1282 root cause: pedagogy articles use ``##`` headings, so block
    splitting must fire on ``##`` not only ``###``. Otherwise each article
    collapses to a single giant "Overview" block that truncates away the
    concrete example sections writers rely on."""
    compression = compress_wiki_packet(_CAFE_PLAN, _CAFE_PACKET)
    trace = compression["selection_trace"]["Діалоги"]
    headings = {entry["source_heading"] for entry in trace}
    # Both ##-headed sub-sections of at-the-cafe.md must be addressable as
    # separate blocks; the generic-article sub-sections too.
    assert "Приклади з підручників" in headings
    assert "Методичний підхід" in headings


def test_wiki_compressor_is_deterministic() -> None:
    """#1282 AC-3: repeated runs on the same inputs must produce byte-for-byte
    identical section picks and selection traces."""
    r1 = compress_wiki_packet(_CAFE_PLAN, _CAFE_PACKET)
    r2 = compress_wiki_packet(_CAFE_PLAN, _CAFE_PACKET)
    assert r1["section_excerpts"] == r2["section_excerpts"]
    assert r1["selection_trace"] == r2["selection_trace"]


def test_wiki_compressor_selection_trace_ranked_and_inspectable() -> None:
    """#1282 AC-3: the selection trace persists the ranked candidate list
    with per-dimension score breakdowns so the choice is auditable."""
    compression = compress_wiki_packet(_CAFE_PLAN, _CAFE_PACKET)
    trace = compression["selection_trace"]["Діалоги"]
    assert len(trace) >= 2
    # Ranked descending by total score (ties broken by citation).
    scores = [entry["score"] for entry in trace]
    assert scores == sorted(scores, reverse=True)
    for entry in trace:
        breakdown = entry["score_breakdown"]
        assert set(breakdown.keys()) == {"query", "scenario", "article"}
        assert entry["score"] == breakdown["query"] + breakdown["scenario"] + breakdown["article"]


def test_wiki_compressor_fallback_when_no_scenario_article_present() -> None:
    """When the packet has no article matching the plan slug, ranking falls
    back to query + capped scenario overlap — the generic article still
    surfaces something useful instead of crashing or returning empty.

    Guards against over-fitting to the cafe case (an explicit Gemini
    adversarial-review concern)."""
    packet = (
        "### Вікі: pedagogy/a1/i-eat-i-drink.md\n\n"
        "## Overview\n\n"
        "Я їм хліб. Я п'ю чай. Кава, чай, вода, сік. Замовлення, меню, "
        "будь ласка.\n"
    )
    compression = compress_wiki_packet(_CAFE_PLAN, packet)
    dialog_items = compression["section_excerpts"]["Діалоги"]
    assert dialog_items, "Must still pick a fallback even without scenario article"
    assert dialog_items[0]["source_path"] == "pedagogy/a1/i-eat-i-drink.md"
    assert dialog_items[0]["score_breakdown"]["article"] == 0


def test_wiki_compressor_generic_article_wins_for_non_scenario_section() -> None:
    """#1282 Gemini adversarial-review finding: a scenario-specific article
    must not monopolise every section of a multi-section module. When a
    section (e.g. a grammar breakdown) has zero query overlap with the
    scenario article's blocks, the generic article's relevant block must
    win — otherwise the article-path + scenario bonuses starve the writer
    of the actually-relevant generic context.

    Regression for the ``query_score == 0 → skip`` relevance floor."""
    plan = {
        "slug": "at-the-cafe",
        "title": "У кафе",
        "subtitle": "Сценарій замовлення у кафе",
        "objectives": ["Замовляти їжу у кафе"],
        "content_outline": [
            {
                "section": "Діалоги",
                "words": 300,
                "points": ["Замовлення в кафе — кава, меню, рахунок."],
            },
            {
                "section": "Знахідний відмінок",
                "words": 300,
                "points": [
                    "Знахідний відмінок іменника чоловічого роду: живі "
                    "істоти отримують закінчення -а, -я; неживі — нульове.",
                ],
            },
        ],
        "dialogue_situations": [
            {
                "setting": "Замовлення у кафе — кава, меню, рахунок",
                "speakers": ["Клієнт", "Офіціантка"],
                "motivation": "Ввічливе замовлення",
            }
        ],
        "activity_hints": [{"id": "quiz", "type": "quiz", "focus": "x"}],
        "word_target": 600,
    }
    packet = (
        # Scenario-specific article but its only block is pure cafe
        # dialogue — zero content about the accusative case.
        "### Вікі: pedagogy/a1/at-the-cafe.md\n\n"
        "## Приклади з підручників\n\n"
        "Мені каву, будь ласка. Можна меню? Рахунок, будь ласка.\n\n"
        # Generic grammar article — carries the tokens the grammar section
        # actually asks about.
        "### Вікі: grammar/accusative-case.md\n\n"
        "## Закінчення\n\n"
        "Знахідний відмінок іменника чоловічого роду: живі істоти "
        "отримують закінчення -а, -я; неживі зберігають нульове "
        "закінчення.\n"
    )
    compression = compress_wiki_packet(plan, packet)

    dialog_picks = compression["section_excerpts"]["Діалоги"]
    assert dialog_picks, "Scenario-aligned section must have picks"
    assert dialog_picks[0]["source_path"] == "pedagogy/a1/at-the-cafe.md"

    grammar_picks = compression["section_excerpts"]["Знахідний відмінок"]
    assert grammar_picks, "Grammar section must surface the grammar article"
    assert grammar_picks[0]["source_path"] == "grammar/accusative-case.md"
    # And the scenario article must not appear at all for the grammar
    # section, since its one block has zero query overlap there.
    assert not any(
        item["source_path"] == "pedagogy/a1/at-the-cafe.md"
        for item in grammar_picks
    )


def test_build_contract_persists_selection_trace_in_artifact() -> None:
    """#1282 AC-3: the wiki-excerpts.yaml artifact must carry the trace so
    reviewers can inspect why each section got its picks."""
    packet = _CAFE_PACKET
    _, excerpts = build_contract(
        _CAFE_PLAN,
        packet,
        level="a1",
        slug="at-the-cafe",
        module_num=38,
    )
    assert "selection_trace" in excerpts
    assert excerpts["selection_trace"]["Діалоги"]
    assert excerpts["sections"]["Діалоги"][0]["source_path"] == "pedagogy/a1/at-the-cafe.md"


def test_build_contract_filters_colors_required_terms_to_learner_targets() -> None:
    plan_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / "a1" / "colors.yaml"
    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    packet = _build_wiki_packet("a1", "colors")

    contract, _ = build_contract(
        plan,
        packet,
        level="a1",
        slug="colors",
        module_num=int(plan["sequence"]),
    )

    sections = contract["teaching_beats"]["sections"]
    colors_section = next(section for section in sections if section["name"] == "Кольори")
    required_terms = set(colors_section["required_terms"])

    banned_terms = {"для", "мові", "активно", "вчимо", "пару", "такий", "поділених", "типами"}
    learner_targets = {
        "червоний",
        "жовтий",
        "зелений",
        "синій",
        "чорний",
        "білий",
        "сірий",
        "блакитний",
        "коричневий",
        "рожевий",
        "помаранчевий",
        "фіолетовий",
        "колір",
    }

    assert required_terms.isdisjoint(banned_terms)
    assert required_terms <= learner_targets
