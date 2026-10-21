from scripts.audit.audit_atlas_thin_enriched import (
    summarize_manifest,
    thin_old_gate_entries,
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
