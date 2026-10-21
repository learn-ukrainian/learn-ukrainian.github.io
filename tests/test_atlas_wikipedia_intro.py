"""Atlas Wikipedia intro policy (#7379): refuse rusalka-kin encyclopedia leads."""

from __future__ import annotations

from scripts.lexicon.atlas_wikipedia_intro import (
    atlas_wikipedia_ok_as_intro,
    wikipedia_lead_has_rusalka_kin_framing,
)

# Live uk.wikipedia REST extract for Берегиня, 2026-08-27 (#7379).
BEREHYNIA_LIVE_EXTRACT = (
    "Береги́ня — істота східнослов’янської міфології, нижчий дух, "
    "споріднений із русалками. Ім'я духа пов'язують з берегами й «перегинами»-пагорбами."
)
BEREHYNIA_LIVE_DESCRIPTION = "істота слов'янської міфології"
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
