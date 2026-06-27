from scripts.audit.audit_atlas_thin_enriched import (
    has_learner_english_anchor,
    summarize_manifest,
    thin_old_gate_entries,
)
from scripts.lexicon.build_kaikki_lookup import KAIKKI_SOURCE


def test_has_learner_english_anchor_accepts_supported_anchor_shapes() -> None:
    assert has_learner_english_anchor({"gloss": "wow"})
    assert has_learner_english_anchor({"enrichment": {"translation": {"en": ["stir"]}}})
    assert has_learner_english_anchor(
        {
            "enrichment": {
                "meaning": {
                    "definitions": ["alphabet"],
                    "source": KAIKKI_SOURCE,
                }
            }
        }
    )


def test_has_learner_english_anchor_rejects_ukrainian_only_enrichment() -> None:
    assert not has_learner_english_anchor(
        {
            "enrichment": {
                "definition_cards": [
                    {
                        "source": "СУМ-20",
                        "definitions": ["помішувати: перемішувати ложкою."],
                    }
                ]
            }
        }
    )
    assert not has_learner_english_anchor(
        {
            "enrichment": {
                "meaning": {
                    "definitions": ["помішувати, перемішувати"],
                    "source": "Вікісловник",
                }
            }
        }
    )


def test_thin_old_gate_entries_reports_old_gate_false_positive() -> None:
    manifest = {
        "entries": [
            {
                "lemma": "помішувати",
                "pos": "verb",
                "primary_source": "built_vocabulary_normalized",
                "course_usage": [{"track": "a2"}],
                "enrichment": {"stress": {"form": "помі́шувати"}},
            },
            {
                "lemma": "ого",
                "pos": "intj",
                "primary_source": "content_lexicon_grow",
                "enrichment": {"translation": {"en": ["wow"]}},
            },
            {"lemma": "pluralia tantum", "gloss": "plural-only nouns"},
        ]
    }

    thin = thin_old_gate_entries(manifest)
    summary = summarize_manifest(manifest)

    assert [entry["lemma"] for entry in thin] == ["помішувати"]
    assert summary["old_gate_enriched"] == 2
    assert summary["old_gate_no_english_anchor"] == 1
    assert summary["course_used_no_english_anchor"] == 1
    assert summary["by_primary_source"] == {"built_vocabulary_normalized": 1}
