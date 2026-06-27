from __future__ import annotations

from scripts.lexicon.repair_plural_noun_aliases import repair_plural_noun_aliases


def test_repair_plural_noun_alias_promotes_surface_entry() -> None:
    manifest = {
        "entries": [
            {
                "lemma": "вершок",
                "url_slug": "вершок",
                "gloss": None,
                "pos": None,
                "primary_source": "built_vocabulary_normalized",
                "course_usage": [
                    {
                        "track": "b1",
                        "module_num": 20,
                        "slug": "pluralia-tantum",
                        "context": "built_vocabulary_normalized",
                    }
                ],
                "atlas_normalizations": [
                    {
                        "kind": "vesum_inflection_to_lemma",
                        "source_lemma": "вершки",
                        "target_lemma": "вершок",
                        "reason": (
                            "VESUM: inflected surface «вершки» "
                            "(surface gloss='cream', pos='noun:pl') folded into "
                            "NEWLY-CREATED lemma page «вершок»."
                        ),
                    }
                ],
            },
            {
                "lemma": "вершки",
                "url_slug": "вершки",
                "gloss": "cream",
                "pos": "noun:pl",
                "primary_source": "built_vocabulary_form",
                "course_usage": [
                    {
                        "track": "b1",
                        "module_num": 20,
                        "slug": "pluralia-tantum",
                        "context": "built_vocabulary_form",
                    }
                ],
                "form_of": {"lemma": "вершок", "url_slug": "вершок"},
            },
        ],
        "stats": {"lemmas_total": 2, "form_of_count": 1},
    }

    summary = repair_plural_noun_aliases(manifest)

    assert summary == {
        "promoted_plural_entries": ["вершки"],
        "removed_aliases": 1,
        "entries_total": 1,
    }
    assert [entry["lemma"] for entry in manifest["entries"]] == ["вершки"]
    entry = manifest["entries"][0]
    assert entry["primary_source"] == "built_vocabulary"
    assert "form_of" not in entry
    assert entry["course_usage"] == [
        {
            "track": "b1",
            "module_num": 20,
            "slug": "pluralia-tantum",
            "context": "built_vocabulary",
        }
    ]
    assert manifest["stats"] == {"lemmas_total": 1, "form_of_count": 0}


def test_repair_plural_noun_alias_handles_multiple_aliases_for_same_surface() -> None:
    manifest = {
        "entries": [
            {
                "lemma": "вершок",
                "url_slug": "вершок",
                "primary_source": "built_vocabulary_normalized",
                "course_usage": [{"track": "b1", "module_num": 20, "slug": "pluralia-tantum"}],
                "atlas_normalizations": [
                    {
                        "kind": "vesum_inflection_to_lemma",
                        "source_lemma": "вершки",
                        "target_lemma": "вершок",
                        "reason": "surface gloss='cream', pos='noun:pl'",
                    }
                ],
            },
            {
                "lemma": "вершка",
                "url_slug": "вершка",
                "primary_source": "built_vocabulary_normalized",
                "course_usage": [{"track": "b1", "module_num": 20, "slug": "pluralia-tantum"}],
                "atlas_normalizations": [
                    {
                        "kind": "vesum_inflection_to_lemma",
                        "source_lemma": "вершки",
                        "target_lemma": "вершка",
                        "reason": "surface gloss='cream', pos='noun:pl'",
                    }
                ],
            },
            {
                "lemma": "вершки",
                "url_slug": "вершки",
                "gloss": "cream",
                "pos": "noun:pl",
                "primary_source": "built_vocabulary_form",
                "course_usage": [{"track": "b1", "module_num": 20, "slug": "pluralia-tantum"}],
                "form_of": {"lemma": "вершок", "url_slug": "вершок"},
            },
        ],
        "stats": {"lemmas_total": 3, "form_of_count": 1},
    }

    summary = repair_plural_noun_aliases(manifest)

    assert summary == {
        "promoted_plural_entries": ["вершки", "вершки"],
        "removed_aliases": 2,
        "entries_total": 1,
    }
    assert [entry["lemma"] for entry in manifest["entries"]] == ["вершки"]
    assert manifest["entries"][0]["primary_source"] == "built_vocabulary"


def test_repair_plural_noun_alias_keeps_alias_with_english_anchor() -> None:
    manifest = {
        "entries": [
            {
                "lemma": "вареник",
                "url_slug": "вареник",
                "gloss": None,
                "primary_source": "built_vocabulary_normalized",
                "enrichment": {"translation": {"en": ["dumpling"], "source": "fixture"}},
                "atlas_normalizations": [
                    {
                        "kind": "vesum_inflection_to_lemma",
                        "source_lemma": "вареники",
                        "target_lemma": "вареник",
                        "reason": "surface gloss='varenyky', pos='noun:pl'",
                    }
                ],
            },
            {
                "lemma": "вареники",
                "url_slug": "вареники",
                "gloss": "varenyky",
                "pos": "noun:pl",
                "primary_source": "built_vocabulary_form",
                "form_of": {"lemma": "вареник", "url_slug": "вареник"},
            },
        ],
    }

    summary = repair_plural_noun_aliases(manifest)

    assert summary["removed_aliases"] == 0
    assert [entry["lemma"] for entry in manifest["entries"]] == ["вареник", "вареники"]
