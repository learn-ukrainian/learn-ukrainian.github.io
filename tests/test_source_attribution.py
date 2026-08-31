"""Tests for academic Atlas source attribution (#5163)."""

from __future__ import annotations

from scripts.lexicon.enrich_manifest import _merge_homonym_relations, _relation_source_label
from scripts.lexicon.source_attribution import (
    BALLA_LABEL,
    E2U_LABEL,
    GOROH_LABEL,
    GRAC_LABEL,
    GRINCHENKO_LABEL,
    KARAVANSKY_LABEL,
    KHRESHCHATYK_LABEL,
    LINGUISTIC_NORM_LABEL,
    MIYKLAS_LABEL,
    PHRASEOLOGY_LABEL,
    SHTEPA_LABEL,
    SUM20_ACADEMIC_LABEL,
    VOLOSHCHAK_LABEL,
    WIKIDATA_LABEL,
    academic_label_for_slug,
    apply_entry_attribution,
    join_academic_source_labels,
    learner_facing_mirror_violations,
    learner_facing_unmapped_source_violations,
    normalize_academic_label,
    official_url_for_slug,
    official_url_from_mirror,
    remap_mirror_source_string,
)
from scripts.wiki.slovnyk_me import SLOVNYK_ME_DICTS


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


def test_usage_notes_family_labels_match_slovnyk_me_and_stay_mirror_only() -> None:
    """#6460: reuse slovnyk.me labels; do not invent official edition URLs."""
    assert SLOVNYK_ME_DICTS["linguistic_norm"] == LINGUISTIC_NORM_LABEL
    assert SLOVNYK_ME_DICTS["khreshchatyk"] == KHRESHCHATYK_LABEL
    assert academic_label_for_slug("linguistic_norm") == LINGUISTIC_NORM_LABEL
    assert academic_label_for_slug("khreshchatyk") == KHRESHCHATYK_LABEL
    assert official_url_for_slug("linguistic_norm", "що") is None
    assert official_url_for_slug("khreshchatyk", "казати") is None
    assert official_url_from_mirror("https://slovnyk.me/dict/linguistic_norm/%D1%89%D0%BE") is None
    assert (
        official_url_from_mirror("https://slovnyk.me/dict/khreshchatyk/%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D0%B8")
        is None
    )


def test_usage_notes_corrective_labels_match_slovnyk_me_and_stay_mirror_only() -> None:
    """#6460: voloschak / foreign_shtepa corrective notes reuse slovnyk.me
    labels; no official edition URLs are invented for them either."""
    assert SLOVNYK_ME_DICTS["voloschak"] == VOLOSHCHAK_LABEL
    assert SLOVNYK_ME_DICTS["foreign_shtepa"] == SHTEPA_LABEL
    assert academic_label_for_slug("voloschak") == VOLOSHCHAK_LABEL
    assert academic_label_for_slug("foreign_shtepa") == SHTEPA_LABEL
    assert official_url_for_slug("voloschak", "відщепенець") is None
    assert official_url_for_slug("foreign_shtepa", "конекція") is None
    assert (
        official_url_from_mirror("https://slovnyk.me/dict/voloschak/%D0%B2%D1%96%D0%B4%D1%89%D0%B5%D0%BF%D0%B5%D0%BD%D0%B5%D1%86%D1%8C")
        is None
    )
    assert (
        official_url_from_mirror("https://slovnyk.me/dict/foreign_shtepa/%D0%BA%D0%BE%D0%BD%D0%B5%D0%BA%D1%86%D1%96%D1%8F")
        is None
    )


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


def test_bare_mirror_prefix_label_stays_visible_to_gates() -> None:
    # Fail closed (#5166 review finding 3): "slovnyk.me: " with no dictionary label
    # must NOT normalize to an empty learner-facing label — the mirror string stays
    # put so learner_facing_mirror_violations fires instead of shipping a blank.
    assert normalize_academic_label("slovnyk.me: ") == "slovnyk.me:"
    entry = {"lemma": "тест", "sections": {"synonyms": {"source": "slovnyk.me: "}}}
    apply_entry_attribution(entry)
    assert learner_facing_mirror_violations(entry)


def test_relation_with_blank_source_has_no_leading_colon() -> None:
    # #5166 review finding 4: a relation missing its source must not render ": …".
    label = _relation_source_label({"pattern": "corpus relation pair"}, "тест")
    assert label == "corpus relation pair → тест"


def test_learner_provenance_walker_checks_section_singular_source_url() -> None:
    # #5166 review finding 2: sections.*.source_url (singular) is learner-surfaced
    # and must be walked like the plural source_urls list.
    entry = {
        "lemma": "тест",
        "sections": {"synonyms": {"source_url": "https://slovnyk.me/dict/synonyms/тест"}},
    }
    violations = learner_facing_mirror_violations(entry)
    assert any("sections.synonyms.source_url" in item for item in violations)


def test_apply_entry_attribution_handles_goroh_translation() -> None:
    entry = {
        "lemma": "албанці",
        "enrichment": {
            "translation": {
                "en": ["Albanian", "Albanians"],
                "source": "Горох (переклад)",
                "mirror_source_url": "https://goroh.pp.ua/Переклад/%D0%B0%D0%BB%D0%B1%D0%B0%D0%BD%D1%86%D1%96",
            },
            "sources": ["Горох (переклад)"],
        },
    }
    assert apply_entry_attribution(entry) is False
    assert entry["enrichment"]["translation"]["source"] == GOROH_LABEL
    assert "source_url" not in entry["enrichment"]["translation"]
    assert (
        entry["enrichment"]["translation"]["mirror_source_url"]
        == "https://goroh.pp.ua/Переклад/%D0%B0%D0%BB%D0%B1%D0%B0%D0%BD%D1%86%D1%96"
    )
    assert learner_facing_mirror_violations(entry) == []
    assert learner_facing_unmapped_source_violations(entry) == []


def test_normalize_academic_label_maps_goroh() -> None:
    assert normalize_academic_label("goroh.pp.ua") == GOROH_LABEL
    assert normalize_academic_label("goroh.pp.ua: Переклад") == GOROH_LABEL
    assert normalize_academic_label("Горох") == GOROH_LABEL
    assert normalize_academic_label("Горох (переклад)") == GOROH_LABEL


def test_apply_entry_attribution_handles_e2u_translation() -> None:
    entry = {
        "lemma": "ампір",
        "enrichment": {
            "translation": {
                "en": ["Empire style"],
                "source": "e2u.org.ua",
                "source_url": "https://e2u.org.ua/s?w=%D0%B0%D0%BC%D0%BF%D1%96%D1%80&dicts=all",
            },
            "sources": ["e2u.org.ua"],
        },
    }
    assert apply_entry_attribution(entry) is True
    assert entry["enrichment"]["translation"]["source"] == E2U_LABEL
    assert (
        entry["enrichment"]["translation"]["source_url"]
        == "https://e2u.org.ua/s?w=%D0%B0%D0%BC%D0%BF%D1%96%D1%80&dicts=all"
    )
    assert entry["enrichment"]["sources"] == [E2U_LABEL]
    assert learner_facing_mirror_violations(entry) == []
    assert learner_facing_unmapped_source_violations(entry) == []


def test_normalize_academic_label_maps_e2u() -> None:
    assert normalize_academic_label("e2u") == E2U_LABEL
    assert normalize_academic_label("e2u.org.ua") == E2U_LABEL
    assert normalize_academic_label("e2u: Переклад") == E2U_LABEL
    assert normalize_academic_label("e2u (переклад)") == E2U_LABEL
    assert normalize_academic_label(E2U_LABEL) == E2U_LABEL


def test_apply_entry_attribution_handles_wikidata_translation() -> None:
    entry = {
        "lemma": "школа",
        "enrichment": {
            "translation": {
                "en": ["school"],
                "source": "Wikidata",
                "source_url": "https://www.wikidata.org/wiki/Q3914",
            },
            "sources": ["Wikidata"],
        },
    }
    assert apply_entry_attribution(entry) is False
    assert entry["enrichment"]["translation"]["source"] == WIKIDATA_LABEL
    assert (
        entry["enrichment"]["translation"]["source_url"]
        == "https://www.wikidata.org/wiki/Q3914"
    )
    assert entry["enrichment"]["sources"] == [WIKIDATA_LABEL]
    assert learner_facing_mirror_violations(entry) == []
    assert learner_facing_unmapped_source_violations(entry) == []


def test_normalize_academic_label_maps_wikidata() -> None:
    assert normalize_academic_label("wikidata") == WIKIDATA_LABEL
    assert normalize_academic_label("Wikidata") == WIKIDATA_LABEL
    assert normalize_academic_label("wikidata.org") == WIKIDATA_LABEL
    assert normalize_academic_label("wikidata.org/wiki/Q1") == WIKIDATA_LABEL
    assert normalize_academic_label("evilwikidata.org") == "evilwikidata.org"
    assert normalize_academic_label(WIKIDATA_LABEL) == WIKIDATA_LABEL
