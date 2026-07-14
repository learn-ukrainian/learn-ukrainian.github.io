"""Tests for academic Atlas source attribution (#5163)."""

from __future__ import annotations

from scripts.lexicon.enrich_manifest import _merge_homonym_relations, _relation_source_label
from scripts.lexicon.source_attribution import (
    BALLA_LABEL,
    GRAC_LABEL,
    GRINCHENKO_LABEL,
    KARAVANSKY_LABEL,
    MIYKLAS_LABEL,
    PHRASEOLOGY_LABEL,
    SUM20_ACADEMIC_LABEL,
    apply_entry_attribution,
    join_academic_source_labels,
    learner_facing_mirror_violations,
    learner_facing_unmapped_source_violations,
    normalize_academic_label,
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


def test_normalize_academic_label_maps_relation_pairs_corpora() -> None:
    assert normalize_academic_label("relation_pairs/grac19a") == GRAC_LABEL
    assert normalize_academic_label("relation_pairs/miyklas.com.ua") == MIYKLAS_LABEL
    assert normalize_academic_label("Грінченко") == GRINCHENKO_LABEL


def test_relation_pairs_label_flows_to_provenance_footer_and_gate() -> None:
    relation = {
        "source": "relation_pairs/miyklas.com.ua",
        "pattern": "corpus relation pair",
        "word": "атлас",
        "gloss": "атлас - map-book",
        "vein": 3,
    }
    label = _relation_source_label(relation, "атлас")
    assert label.startswith(f"{MIYKLAS_LABEL}: corpus relation pair → атлас")

    merged = _merge_homonym_relations(None, [relation])
    assert merged is not None
    assert MIYKLAS_LABEL in merged["source"]
    assert "relation_pairs/" not in merged["source"]

    entry = {"lemma": "атлас", "sections": {"homonyms": merged}}
    assert learner_facing_unmapped_source_violations(entry) == []


def test_unmapped_relation_pairs_fail_closed_in_conformance_gate() -> None:
    relation = {
        "source": "relation_pairs/uk.wikipedia",
        "pattern": "corpus relation pair",
        "word": "ключ",
        "gloss": "джерело води",
        "vein": 3,
    }
    merged = _merge_homonym_relations(None, [relation])
    assert merged is not None
    assert "relation_pairs/uk.wikipedia" in merged["source"]

    entry = {"lemma": "ключ", "sections": {"homonyms": merged}}
    violations = learner_facing_unmapped_source_violations(entry)
    assert len(violations) == 2
    assert all("relation_pairs/uk.wikipedia" in item for item in violations)


def test_learner_provenance_walker_checks_literary_attestation_and_enrichment_blocks() -> None:
    entry = {
        "lemma": "книга",
        "enrichment": {
            "meaning": {"definitions": ["test"], "source": "slovnyk.me: bad"},
            "literary_attestation": {
                "text": "Приклад.",
                "source": "corpus",
                "source_url": "https://slovnyk.me/dict/newsum/test",
            },
        },
    }
    mirror_violations = learner_facing_mirror_violations(entry)
    assert any("enrichment.meaning.source" in item for item in mirror_violations)
    assert any("enrichment.literary_attestation.source_url" in item for item in mirror_violations)
