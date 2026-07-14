"""Tests for academic Atlas source attribution (#5163)."""

from __future__ import annotations

from scripts.lexicon.source_attribution import (
    BALLA_LABEL,
    KARAVANSKY_LABEL,
    PHRASEOLOGY_LABEL,
    SUM20_ACADEMIC_LABEL,
    apply_entry_attribution,
    join_academic_source_labels,
    learner_facing_mirror_violations,
    official_url_from_mirror,
    remap_mirror_source_string,
)


def test_remap_mirror_source_string_strips_slovnyk_prefix() -> None:
    assert remap_mirror_source_string("slovnyk.me: Словник синонімів Караванського") == KARAVANSKY_LABEL
    assert (
        remap_mirror_source_string(
            "slovnyk.me: Словник синонімів Караванського + Словник синонімів української мови"
        )
        == f"{KARAVANSKY_LABEL} + Словник синонімів української мови"
    )


def test_official_url_from_mirror_maps_sum20() -> None:
    mirror = "https://slovnyk.me/dict/newsum/%D0%BA%D0%BE%D1%81%D0%B0"
    assert official_url_from_mirror(mirror) == "https://services.ulif.org.ua/expl/#/word/%D0%BA%D0%BE%D1%81%D0%B0"


def test_join_academic_source_labels_deduplicates() -> None:
    labels = join_academic_source_labels(
        [
            "slovnyk.me: Словник синонімів Караванського",
            "Словник синонімів Караванського",
        ]
    )
    assert labels == KARAVANSKY_LABEL


def test_apply_entry_attribution_moves_mirror_urls_internal() -> None:
    entry = {
        "lemma": "коса",
        "sections": {
            "synonyms": {
                "items": ["жнива"],
                "source": "slovnyk.me: Словник синонімів Караванського",
                "source_urls": ["https://slovnyk.me/dict/synonyms_karavansky/%D0%BA%D0%BE%D1%81%D0%B0"],
            }
        },
        "enrichment": {
            "translation": {
                "en": ["braid"],
                "source": "slovnyk.me: Українсько-англійський словник",
                "source_url": "https://slovnyk.me/dict/ukreng/%D0%BA%D0%BE%D1%81%D0%B0",
            },
            "definition_cards": [
                {
                    "id": "sum20",
                    "source": "СУМ-20",
                    "source_pill": "СУМ-20",
                    "definitions": ["test"],
                    "source_url": "https://slovnyk.me/dict/newsum/%D0%BA%D0%BE%D1%81%D0%B0",
                }
            ],
        },
    }

    assert apply_entry_attribution(entry) is True
    assert entry["sections"]["synonyms"]["source"] == KARAVANSKY_LABEL
    assert "source_urls" not in entry["sections"]["synonyms"]
    assert entry["sections"]["synonyms"]["mirror_source_urls"] == [
        "https://slovnyk.me/dict/synonyms_karavansky/%D0%BA%D0%BE%D1%81%D0%B0"
    ]
    assert entry["enrichment"]["translation"]["source"] == BALLA_LABEL
    assert "source_url" not in entry["enrichment"]["translation"]
    assert entry["enrichment"]["definition_cards"][0]["source"] == SUM20_ACADEMIC_LABEL
    assert entry["enrichment"]["definition_cards"][0]["source_url"].startswith(
        "https://services.ulif.org.ua/expl/#/word/"
    )
    assert learner_facing_mirror_violations(entry) == []


def test_idiom_section_source_remaps_phraseology_label() -> None:
    entry = {
        "lemma": "яблуко",
        "sections": {
            "idioms": {
                "items": [{"phrase": "яблуко розбрату", "definition": "test", "source": PHRASEOLOGY_LABEL}],
                "source": "slovnyk.me: Фразеологічний словник української мови",
                "source_urls": ["https://slovnyk.me/dict/phraseology/%D1%8F%D0%B1%D0%BB%D1%83%D0%BA%D0%BE"],
            }
        },
    }
    apply_entry_attribution(entry)
    assert entry["sections"]["idioms"]["source"] == PHRASEOLOGY_LABEL
    assert learner_facing_mirror_violations(entry) == []
