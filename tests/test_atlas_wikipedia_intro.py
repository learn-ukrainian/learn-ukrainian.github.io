"""Atlas Wikipedia intro policy (#7379): refuse rusalka-kin encyclopedia leads."""

from __future__ import annotations

from scripts.lexicon.atlas_wikipedia_intro import (
    atlas_wikipedia_ok_as_intro,
    is_rusalka_class_lemma,
    wikipedia_lead_has_rusalka_kin_framing,
)

# Live uk.wikipedia REST extract for Берегиня, 2026-08-27 (#7379).
BEREHYNIA_LIVE_EXTRACT = (
    "Береги́ня — істота східнослов’янської міфології, нижчий дух, "
    "споріднений із русалками. Ім'я духа пов'язують з берегами й «перегинами»-пагорбами."
)
BEREHYNIA_LIVE_DESCRIPTION = "істота слов'янської міфології"
GODDESS_EXTRACT = (
    "Берегиня — за давньослов'янськими релігійними уявленнями, мати всього живого, "
    "первісне божество – захисниця людини, богиня родючості."
)


def test_live_berehynia_extract_is_rusalka_kin_framing() -> None:
    assert wikipedia_lead_has_rusalka_kin_framing(
        BEREHYNIA_LIVE_DESCRIPTION,
        BEREHYNIA_LIVE_EXTRACT,
    )
    assert not atlas_wikipedia_ok_as_intro(
        "берегиня",
        {
            "title": "Берегиня",
            "description": BEREHYNIA_LIVE_DESCRIPTION,
            "extract": BEREHYNIA_LIVE_EXTRACT,
        },
    )
    assert not atlas_wikipedia_ok_as_intro(
        "Берегиня",
        {"title": "Берегиня", "summary": BEREHYNIA_LIVE_EXTRACT},
    )


def test_goddess_protectress_excerpt_still_attaches() -> None:
    assert not wikipedia_lead_has_rusalka_kin_framing(GODDESS_EXTRACT)
    assert atlas_wikipedia_ok_as_intro(
        "берегиня",
        {"title": "Берегиня", "extract": GODDESS_EXTRACT},
    )


def test_school_article_is_not_rusalka_kin() -> None:
    assert atlas_wikipedia_ok_as_intro(
        "школа",
        {
            "title": "Школа",
            "description": "навчальний заклад",
            "extract": "Шко́ла — заклад освіти...",
        },
    )


def test_rusalka_lemma_keeps_its_own_wikipedia_lead() -> None:
    extract = (
        "Русалка — міфологічна істота, нижчий дух, споріднений із русалками "
        "східнослов'янської демонології."
    )
    assert is_rusalka_class_lemma("русалка")
    assert atlas_wikipedia_ok_as_intro(
        "русалка",
        {"title": "Русалка", "extract": extract},
    )


def test_later_sentence_rusalka_mention_does_not_drop_lead() -> None:
    extract = (
        "Берегиня — богиня-захисниця дому і родини. "
        "Заст. тлумачення ототожнювало її з русалками."
    )
    assert atlas_wikipedia_ok_as_intro("берегиня", {"extract": extract})
