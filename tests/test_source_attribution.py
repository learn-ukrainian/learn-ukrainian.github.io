"""Tests for academic Atlas source attribution (#5163)."""

from __future__ import annotations

from scripts.lexicon.enrich_manifest import _merge_homonym_relations, _relation_source_label
from scripts.lexicon.source_attribution import (
    BALLA_LABEL,
    KARAVANSKY_LABEL,
    KHRESHCHATYK_LABEL,
    LINGUISTIC_NORM_LABEL,
    MIYKLAS_LABEL,
    SUM20_ACADEMIC_LABEL,
    academic_label_for_slug,
    apply_entry_attribution,
    attach_official_url,
    cites_soviet_dictionary_outside_context,
    learner_facing_mirror_violations,
    learner_facing_unmapped_source_violations,
    normalize_academic_label,
    official_url_for_slug,
    official_url_from_mirror,
    remap_url_list,
    soviet_citation_learner_violation,
    withhold_legacy_soviet_citations,
)
from scripts.wiki.slovnyk_me import SLOVNYK_ME_DICTS


def test_soviet_citation_is_only_allowed_in_occupation_context() -> None:
    marked = {
        "heritage_status": {
            "soviet_colonization_context": {"source": "СУМ-11", "red_flag": True, "sovietization_risk": 0}
        }
    }
    unmarked = {"heritage_status": {"soviet_colonization_context": {"source": "СУМ-11"}}}
    synonym = {"sections": {"synonyms": {"source": "СУМ-20 + СУМ-11", "items": ["абрикоса"]}}}
    assert not cites_soviet_dictionary_outside_context(marked)
    assert not cites_soviet_dictionary_outside_context(unmarked)
    assert cites_soviet_dictionary_outside_context(synonym)
    assert soviet_citation_learner_violation(marked) is None
    assert soviet_citation_learner_violation(unmarked) == "missing russification marker"
    assert soviet_citation_learner_violation(synonym) == "outside soviet_colonization_context"
    assert soviet_citation_learner_violation({"sections": {"synonyms": {"source": "СУМ-20"}}}) is None


def test_legacy_withholding_counts_sections_and_preserves_marked_context() -> None:
    original = {
        "lemma": "слово",
        "sections": {"synonyms": {"items": ["назва"], "source": "СУМ-20 + СУМ-11"}},
        "enrichment": {"sources": ["СУМ-20", "СУМ-11"]},
        "soviet_colonization_context": {"source": "СУМ-11", "red_flag": True},
    }
    projected, report = withhold_legacy_soviet_citations(original)
    assert report == {
        "entries_touched": 1,
        "citations_withheld": 2,
        "by_section": {"synonyms": 1, "enrichment.sources": 1},
        "relation_sections_touched": 1,
        "clauses_withheld": 2,
        "items_withheld": 0,
        "items_kept": 1,
        "gate_notes_removed": 0,
    }
    assert original["sections"]["synonyms"]["source"] == "СУМ-20 + СУМ-11"
    assert projected["sections"]["synonyms"] == {"items": ["назва"], "source": "СУМ-20"}
    assert projected["enrichment"]["sources"] == ["СУМ-20"]
    assert projected["soviet_colonization_context"] == original["soviet_colonization_context"]
    assert projected["gate_provenance"]["enrichment.sources"] == "source-withdrawn-unverified"


def test_relation_clauses_keep_only_items_with_allowed_support() -> None:
    # Shapes observed in the reviewed абрикос, латиниця, розширити, відбігти entries.
    for lemma, name, source, items, expected in (
        ("абрикос", "synonyms", "Словник синонімів + СУМ-20: Те саме, що → абрикоса + "
         "ВТС: → абрикоса + СУМ-11: → абрикоса", ["абрикоса", "жерделя", "мореля"],
         ["абрикоса", "жерделя", "мореля"]),
        ("латиниця", "synonyms", "СУМ-20: → латинка + СУМ-11: → латинка + СУМ-11: → абетка",
         ["латинка", "абетка"], ["латинка"]),
        ("розширити", "antonyms", "ВТС: протилежне → звузити + СУМ-11: → скоротити",
         ["звузити", "скоротити"], ["звузити"]),
        ("відбігти", "synonyms", "СУМ-20: → віддалитися + СУМ-11: → відскочити",
         ["віддалитися", "відскочити"], ["віддалитися"]),
    ):
        projected, report = withhold_legacy_soviet_citations({
            "lemma": lemma, "sections": {name: {"source": source, "items": items}}
        })
        assert projected["sections"][name]["items"] == expected
        assert "СУМ-11" not in projected["sections"][name]["source"]
        assert report["items_withheld"] == len(items) - len(expected)
        assert report["items_kept"] == len(expected)
        if len(expected) != len(items):
            assert projected["gate_provenance"][name] == "source-withdrawn-unverified"


def test_gate_diagnostic_note_is_removed_without_withholding_wordnet_item() -> None:
    for lemma, item, gate in (
        ("ера", "епоха", "СУМ-11/СУМ-11 stem=булий"),
        ("броня", "кольчуга", "СУМ-20/СУМ-11 stem=воїн"),
    ):
        source = f"Ukrajinet WordNet: gated synset → {item} [gate: VESUM both valid; {gate}]"
        projected, report = withhold_legacy_soviet_citations({
            "lemma": lemma, "sections": {"synonyms": {"items": [item], "source": source}},
            "enrichment": {"sources": [source]},
        })
        clean = f"Ukrajinet WordNet: gated synset → {item}"
        assert projected["sections"]["synonyms"]["items"] == [item]
        assert projected["sections"]["synonyms"]["source"] == clean
        assert projected["enrichment"]["sources"] == [clean]
        assert report["citations_withheld"] == 0
        assert report["gate_notes_removed"] == 2


def test_nested_contrast_key_does_not_exempt_a_section_citation() -> None:
    card = {"sections": {"synonyms": {"items": ["стяг"], "soviet_colonization_context": {
        "source": "СУМ-11", "red_flag": True
    }}}}
    assert cites_soviet_dictionary_outside_context(card)
    assert soviet_citation_learner_violation(card) == "outside soviet_colonization_context"


def test_soviet_label_variants_are_citations() -> None:
    for label in (
        "SUM_11",
        "Словник української мови (1970–1980)",
        "Словник української мови: В 11 томах",
        "Словник української мови в 11 томах (1970 — 80)",
        "https://sum.in.ua/s/word",
        "https://slovnyk.me/dict/sum/word",
    ):
        assert soviet_citation_learner_violation({"source": label}) == "outside soviet_colonization_context"


def test_literary_quote_mentions_dictionary_without_citing_it() -> None:
    quote = "«Словник української мови» в 11 томах (1970 — 80)"
    assert cites_soviet_dictionary_outside_context({"source": quote})
    entry = {"lemma": "тлумачний", "enrichment": {"literary_attestation": {
        "text": quote, "source": "2004 encyclopedia",
    }}}
    assert soviet_citation_learner_violation(entry) is None
    projected, report = withhold_legacy_soviet_citations(entry)
    assert projected["enrichment"]["literary_attestation"]["text"] == quote
    assert report["citations_withheld"] == 0
    entry["enrichment"]["literary_attestation"]["source"] = quote
    assert soviet_citation_learner_violation(entry) == "outside soviet_colonization_context"


def test_usage_notes_family_labels_match_slovnyk_me_and_stay_mirror_only() -> None:
    """#6460: reuse slovnyk.me labels; do not invent official edition URLs."""
    assert SLOVNYK_ME_DICTS["linguistic_norm"] == LINGUISTIC_NORM_LABEL
    assert SLOVNYK_ME_DICTS["khreshchatyk"] == KHRESHCHATYK_LABEL
    assert academic_label_for_slug("linguistic_norm") == LINGUISTIC_NORM_LABEL
    assert academic_label_for_slug("khreshchatyk") == KHRESHCHATYK_LABEL
    assert official_url_for_slug("linguistic_norm", "що") is None
    assert official_url_for_slug("khreshchatyk", "казати") is None
    # The registered VTS mirror has no established official electronic edition.
    assert official_url_for_slug("vts", "коса") is None
    assert official_url_from_mirror("https://slovnyk.me/dict/vts/коса") is None
    assert official_url_from_mirror("https://slovnyk.me/dict/linguistic_norm/%D1%89%D0%BE") is None
    assert (
        official_url_from_mirror("https://slovnyk.me/dict/khreshchatyk/%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D0%B8")
        is None
    )


def test_apply_entry_attribution_moves_mirror_urls_internal(monkeypatch) -> None:
    entry = {
        "lemma": "коса",
        "primary_source": "slovnyk.me: Словник синонімів Караванського",
        "sections": {
            "synonyms": {
                "items": ["жнива", {
                    "text": "плетениця",
                    "source": "slovnyk.me: Словник синонімів Караванського + relation_pairs/miyklas.com.ua",
                    "source_url": "https://slovnyk.me/dict/synonyms_karavansky/коса",
                    "source_urls": ["https://slovnyk.me/dict/synonyms/коса"],
                }],
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
                },
                {
                    "id": "vts",
                    "source": "ВТС",
                    "definitions": ["unchanged"],
                    "source_url": "https://slovnyk.me/dict/vts/коса",
                },
            ],
        },
    }

    assert apply_entry_attribution(entry) is True
    assert entry["primary_source"] == "Словник синонімів С. Караванського"
    assert entry["sections"]["synonyms"]["items"] == ["жнива", {
        "text": "плетениця",
        "source": "Словник синонімів С. Караванського + навчальні матеріали МійКлас (корпусні пари)",
        "mirror_source_url": "https://slovnyk.me/dict/synonyms_karavansky/коса",
        "mirror_source_urls": ["https://slovnyk.me/dict/synonyms/коса"],
    }]
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
    assert entry["enrichment"]["definition_cards"][1] == {
        "id": "vts",
        "source": "Великий тлумачний словник сучасної української мови",
        "definitions": ["unchanged"],
        "mirror_source_url": "https://slovnyk.me/dict/vts/коса",
    }
    assert learner_facing_mirror_violations(entry) == []
    assert learner_facing_unmapped_source_violations(entry) == []
    assert apply_entry_attribution(entry) is False

    from copy import deepcopy

    legacy_card = {
        "id": "vts",
        "source": "Великий тлумачний словник сучасної української мови",
        "source_pill": "ВТС",
        "definitions": ["unchanged"],
        "source_url": "https://www.ulif.org.ua",
        "mirror_source_url": "https://slovnyk.me/dict/vts/коса",
    }
    raw_card = deepcopy(legacy_card)
    legacy_entry = {"lemma": "коса", "enrichment": {"definition_cards": [legacy_card]}}
    assert apply_entry_attribution(legacy_entry) is True
    assert legacy_card == {key: value for key, value in raw_card.items() if key != "source_url"}
    assert raw_card["source_url"] == "https://www.ulif.org.ua"
    assert apply_entry_attribution(legacy_entry) is False
    legacy_card.pop("mirror_source_url")
    legacy_card.update(source="ВТС", source_url="https://www.ulif.org.ua")
    assert apply_entry_attribution(legacy_entry) is True
    assert legacy_card == {
        "id": "vts", "source": "Великий тлумачний словник сучасної української мови",
        "source_pill": "ВТС", "definitions": ["unchanged"],
    }
    assert apply_entry_attribution(legacy_entry) is False

    # Other identities and URLs must not be caught by a domain-wide filter.
    for card in (
        {**raw_card, "id": "sum20", "source": SUM20_ACADEMIC_LABEL},
        {**raw_card, "id": "other", "source": "ВТС"},
        {**raw_card, "id": "vts-other"},
        {**raw_card, "source_url": "https://services.ulif.org.ua/expl/#/word/коса"},
        {**raw_card, "source_url": "https://www.ulif.org.ua/entry"},
    ):
        original_card = deepcopy(card)
        assert apply_entry_attribution({"enrichment": {"definition_cards": [card]}}) is False
        assert card == original_card

    # Exact VTS identity removes the unsupported citation regardless of label.
    for source in ("Культура слова", "", "ВТС: протилежне → звузити", "СУМ-20 + ВТС"):
        card = {**raw_card, "source": source}
        original_card = deepcopy(card)
        wrapped = {"enrichment": {"definition_cards": [card]}}
        assert apply_entry_attribution(wrapped) is True
        assert card == {key: value for key, value in original_card.items() if key != "source_url"}
        assert apply_entry_attribution(wrapped) is False

    genuine_urls = [
        "https://services.ulif.org.ua/expl/#/word/коса",
        "https://lcorp.ulif.org.ua/dictua",
        "https://www.ulif.org.ua/entry",
    ]
    mirror = "https://slovnyk.me/dict/vts/коса"
    for urls in (["https://www.ulif.org.ua"], ["https://www.ulif.org.ua", mirror, *genuine_urls]):
        card = {**raw_card, "source_urls": urls, "mirror_source_urls": [mirror]}
        wrapped = {"enrichment": {"definition_cards": [card]}}
        assert apply_entry_attribution(wrapped) is True
        expected = {key: value for key, value in raw_card.items() if key != "source_url"}
        expected["mirror_source_urls"] = [mirror]
        if len(urls) > 1:
            expected["source_urls"] = genuine_urls
        assert card == expected
        assert apply_entry_attribution(wrapped) is False

    mirror_card = {"id": "vts", "source_urls": [mirror]}
    wrapped = {"enrichment": {"definition_cards": [mirror_card]}}
    assert apply_entry_attribution(wrapped) is True
    assert mirror_card == {
        "id": "vts", "mirror_source_urls": [mirror],
    }
    assert apply_entry_attribution(wrapped) is False
    attach_official_url(legacy_card, mirror_url=mirror, slug="vts")
    assert legacy_card["mirror_source_url"] == mirror
    assert "source_url" not in legacy_card
    assert remap_url_list([mirror, *genuine_urls]) == (genuine_urls, [mirror])

    # Prose labels without a VTS card identity cannot establish URL provenance.
    for source in ("ВТС", "ВТС: протилежне → звузити", "СУМ-20 + ВТС"):
        section = {"source": source, "source_url": "https://www.ulif.org.ua",
                   "source_urls": ["https://www.ulif.org.ua", *genuine_urls]}
        for name in ("synonyms", "antonyms", "homonyms", "paronyms"):
            wrapped = {"sections": {name: deepcopy(section)}}
            apply_entry_attribution(wrapped)
            assert wrapped["sections"][name]["source_url"] == section["source_url"]
            assert wrapped["sections"][name]["source_urls"] == section["source_urls"]
            assert apply_entry_attribution(wrapped) is False

    from tests.test_lexicon_enrich_manifest import _run_synonyms_gate

    source_block = {
        "items": ["обмін"],
        "source": "slovnyk.me: Словник синонімів Караванського + relation_pairs/synonym_verdicts",
        "source_urls": ["https://slovnyk.me/dict/synonyms_karavansky/ключ"],
    }
    original_block = deepcopy(source_block)
    produced = _run_synonyms_gate(
        monkeypatch, offline=False, cache={"lookups": {}},
        new_synonyms=source_block, existing_synonyms={},
    )
    assert source_block == original_block
    assert produced["sections"]["synonyms"] == {
        "items": ["обмін"],
        "source": "Словник синонімів С. Караванського + relation_pairs/synonym_verdicts",
        "mirror_source_urls": ["https://slovnyk.me/dict/synonyms_karavansky/ключ"],
    }
    assert learner_facing_unmapped_source_violations(produced) == [
        "ключ: sections.synonyms.source='Словник синонімів С. Караванського + relation_pairs/synonym_verdicts'",
    ]
    import sqlite3

    from scripts.lexicon import enrich_manifest

    shared_cards = [{"id": "vts", "source": "ВТС", "definitions": ["unchanged"]}]
    monkeypatch.setattr(enrich_manifest, "_definition_cards", lambda *a, **k: shared_cards)
    with sqlite3.connect(":memory:") as conn:
        enrich_manifest.enrich_entry(
            produced, conn, {}, pointer_synonym_relations=[], pointer_antonym_relations=[],
            pointer_homonym_relations=[], pointer_paronym_relations=[],
        )
    assert shared_cards == [{"id": "vts", "source": "ВТС", "definitions": ["unchanged"]}]
    assert produced["enrichment"]["definition_cards"] == [{
        "id": "vts", "source": "Великий тлумачний словник сучасної української мови",
        "definitions": ["unchanged"],
    }]


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

    # Approval carriers and source-name lookalikes must not acquire authority.
    for source in (
        "relation_pairs/synonym_verdicts",
        "relation_pairs/grac-synonym_verdicts",
        "relation_pairs/miyklas.com.ua-unverified",
        "relation_pairs/not-grinchyshyn-1986",
        "relation_pairs/ukr-mova.in.ua-unverified",
        "slovnyk.me: relation_pairs/synonym_verdicts",
    ):
        assert normalize_academic_label(source) == source
        relation["source"] = source
        label = _relation_source_label(relation, "ключ")
        assert label == f"{source}: corpus relation pair → ключ"
        entry = {
            "lemma": "ключ",
            "primary_source": source,
            "enrichment": {"sources": [source]},
            "sections": {"synonyms": {
                "source": f"slovnyk.me: Словник синонімів Караванського + {label}",
                "items": [{"word": "засіб", "source": source, "source_url": "https://example.invalid/raw"}],
            }},
        }
        assert apply_entry_attribution(entry)
        assert entry["primary_source"] == source
        assert entry["enrichment"]["sources"] == [source]
        assert entry["sections"]["synonyms"] == {
            "source": f"Словник синонімів С. Караванського + {label}",
            "items": [{"word": "засіб", "source": source, "source_url": "https://example.invalid/raw"}],
        }
        assert len(learner_facing_unmapped_source_violations(entry)) == 4
        assert apply_entry_attribution(entry) is False


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
    assert normalize_academic_label("slovnyk.me: unknown dictionary") == "slovnyk.me: unknown dictionary"
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
