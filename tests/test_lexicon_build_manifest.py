from scripts.lexicon.build_data_manifest import SURZHYK_TO_AVOID_SEEDS, build_manifest


def test_surzhyk_to_avoid_seed_group_is_in_manifest() -> None:
    manifest = build_manifest()
    entries = {entry["lemma"]: entry for entry in manifest["entries"]}
    seed_lemmas = [str(seed["lemma"]) for seed in SURZHYK_TO_AVOID_SEEDS]

    assert manifest["stats"]["from_surzhyk_to_avoid"] == len(seed_lemmas)
    assert manifest["seed_groups"] == [
        {
            "id": "surzhyk-to-avoid",
            "source": "surzhyk_to_avoid",
            "description": "Classifier-verified Russianism/surzhyk examples for visible Atlas warnings.",
            "lemmas": seed_lemmas,
        }
    ]
    for lemma in seed_lemmas:
        assert entries[lemma]["primary_source"] == "surzhyk_to_avoid"
        assert entries[lemma]["seed_group"] == "surzhyk-to-avoid"
        assert entries[lemma]["course_usage"] == []


def test_manifest_url_slugs_are_unique() -> None:
    manifest = build_manifest()
    slugs: dict[str, list[str]] = {}
    for entry in manifest["entries"]:
        slugs.setdefault(entry["url_slug"], []).append(entry["lemma"])

    duplicates = {slug: lemmas for slug, lemmas in slugs.items() if len(lemmas) > 1}

    assert duplicates == {}
