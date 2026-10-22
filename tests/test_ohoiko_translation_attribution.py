"""Term-level provenance must not assign retained dictionary senses to Ohoiko."""
from scripts.lexicon.ohoiko_quality_enrichment import (
    SOURCE_500_VERBS,
    SOURCE_1000_WORDS,
    apply_ohoiko_quality_enrichment,
    merge_translation,
    parse_500_verbs_chunk,
    parse_1000_words_chunk,
)


def test_merge_does_not_misattribute_distinct_dictionary_sense():
    prior = {"en": ["bus", "coach (long-distance bus)"], "source": "dmklinger", "pos": "noun"}
    merged = merge_translation(prior, "bus", source_file=SOURCE_1000_WORDS, locator="ohoiko-1000-words entry 3")
    assert merged["en"] == ["bus", "coach (long-distance bus)"]
    assert merged["attributions"] == [
        {"text": "bus", "source": "Anna Ohoiko", "source_file": SOURCE_1000_WORDS, "locator": "ohoiko-1000-words entry 3"},
        {"text": "coach (long-distance bus)", "source": "dmklinger"},
    ]
    assert merged["pos"] == "noun"


def test_parser_to_enrichment_preserves_each_books_provenance_without_stores():
    # Synthetic head-only fixtures exercise metadata; no corpus reads or lexical judgments.
    words = parse_1000_words_chunk("fixture_e0003", "", "3. автобус  bus\n")
    verbs = parse_500_verbs_chunk("fixture_e0001", "", "1. аналізувати, проаналізувати\nto analyze\n")
    manifest = {"entries": [{"lemma": lemma} for lemma in words.lemmas + verbs.lemmas]}
    apply_ohoiko_quality_enrichment(manifest, parsed_1000=[words], parsed_500=[verbs])
    for entry in manifest["entries"]:
        parsed = words if entry["lemma"] in words.lemmas else verbs
        attribution = entry["enrichment"]["translation"]["attributions"][0]
        assert attribution == {"text": parsed.gloss, "source": "Anna Ohoiko", "source_file": parsed.source_file, "locator": parsed.locator}
    assert {words.source_file, verbs.source_file} == {SOURCE_1000_WORDS, SOURCE_500_VERBS}


def test_legacy_merged_senses_remain_unknown_after_proven_primary_gloss():
    prior = {"en": ["bus", "coach (long-distance bus)"], "source": "learner_english_gloss"}
    merged = merge_translation(prior, "bus", source_file=SOURCE_1000_WORDS, locator="ohoiko-1000-words entry 3")
    assert merged["en"] == prior["en"]
    assert merged["attributions"][1] == {"text": "coach (long-distance bus)", "source": ""}


def test_repeated_enrichment_retains_both_book_credits_and_is_idempotent():
    first = merge_translation(None, "bus", source_file=SOURCE_1000_WORDS, locator="entry 3")
    second = merge_translation(first, "bus", source_file=SOURCE_500_VERBS, locator="entry 4")
    assert second["en"] == ["bus"]
    assert second["attributions"] == [
        {"text": "bus", "source": "Anna Ohoiko", "source_file": SOURCE_500_VERBS, "locator": "entry 4"},
        {"text": "bus", "source": "Anna Ohoiko", "source_file": SOURCE_1000_WORDS, "locator": "entry 3"},
    ]
    assert merge_translation(second, "bus", source_file=SOURCE_500_VERBS, locator="entry 4") == second


def test_dictionary_locators_and_links_survive_primary_gloss_insertion():
    prior = {"en": ["coach"], "source": "dictionary", "source_url": "https://example.org/dictionary", "locator": "sense 2"}
    merged = merge_translation(prior, "bus")
    assert merged["attributions"][1] == {"text": "coach", "source": "dictionary", "source_url": prior["source_url"], "locator": "sense 2"}


def test_examples_keep_metadata_and_missing_source_is_not_assigned_to_anna():
    from scripts.lexicon.ohoiko_quality_enrichment import enrich_entry_with_ohoiko, merge_examples

    example = {"uk": "Сашко́ ї́здить в шко́лу авто́бусом.", "en": "Sashko goes to school by bus.", "source": "Anna Ohoiko", "source_url": "https://example.org/book"}
    entry = {}
    enrich_entry_with_ohoiko(entry, anna_example=example, source_file=SOURCE_1000_WORDS, locator="entry 3")
    assert entry["enrichment"]["examples"][0] == {**example, "source_file": SOURCE_1000_WORDS, "locator": "entry 3"}
    assert example.get("source_file") is None  # caller input is not mutated
    missing = {"uk": example["uk"], "en": example["en"]}
    assert merge_examples([], [missing]) == [{**missing, "source": "", "locator": ""}]


def test_unknown_prior_translation_source_stays_unknown_without_dropping_sense():
    result = merge_translation({"en": ["coach"]}, "bus")
    assert result["en"] == ["bus", "coach"]
    assert result["attributions"][1] == {"text": "coach", "source": ""}
