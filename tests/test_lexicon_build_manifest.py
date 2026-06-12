from scripts.lexicon.build_data_manifest import (
    HERITAGE_STATUS_SEEDS,
    SURZHYK_TO_AVOID_SEEDS,
    build_manifest,
)


def test_surzhyk_to_avoid_seed_group_is_in_manifest() -> None:
    manifest = build_manifest()
    entries = {entry["lemma"]: entry for entry in manifest["entries"]}
    seed_lemmas = [str(seed["lemma"]) for seed in SURZHYK_TO_AVOID_SEEDS]

    assert manifest["stats"]["from_surzhyk_to_avoid"] == len(seed_lemmas)
    assert manifest["seed_groups"][0]["lemmas"] == seed_lemmas
    for lemma in seed_lemmas:
        assert entries[lemma]["primary_source"] == "surzhyk_to_avoid"
        assert entries[lemma]["seed_group"] == "surzhyk-to-avoid"
        assert entries[lemma]["course_usage"] == []


def test_heritage_status_seed_group_is_in_manifest() -> None:
    manifest = build_manifest()
    entries = {entry["lemma"]: entry for entry in manifest["entries"]}
    seed_lemmas = [str(seed["lemma"]) for seed in HERITAGE_STATUS_SEEDS]

    assert manifest["stats"]["from_heritage_status_seed"] == len(seed_lemmas)
    assert manifest["seed_groups"][1]["lemmas"] == seed_lemmas
    for lemma in seed_lemmas:
        assert entries[lemma]["primary_source"] == "heritage_status_seed"
        assert entries[lemma]["seed_group"] == "heritage-status-samples"
        assert entries[lemma]["course_usage"] == []


def test_manifest_sources_all_vocabulary_files_and_a2_word_field() -> None:
    manifest = build_manifest()
    entries = {entry["lemma"]: entry for entry in manifest["entries"]}

    assert manifest["stats"]["modules_covered"] >= 120
    assert manifest["stats"]["from_built"] >= 2_000
    assert "батько" in entries
    assert "відмінок" in entries
    assert "голосний" in entries
    assert any(usage["track"] == "a1" and usage["slug"] == "my-family" for usage in entries["батько"]["course_usage"])
    assert any(usage["track"] == "a2" and usage["slug"] == "a2-bridge" for usage in entries["відмінок"]["course_usage"])


def test_manifest_url_slugs_are_unique() -> None:
    manifest = build_manifest()
    slugs: dict[str, list[str]] = {}
    for entry in manifest["entries"]:
        slugs.setdefault(entry["url_slug"], []).append(entry["lemma"])

    duplicates = {slug: lemmas for slug, lemmas in slugs.items() if len(lemmas) > 1}

    assert duplicates == {}
