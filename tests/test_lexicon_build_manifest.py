import scripts.lexicon.build_data_manifest as build_data_manifest
from scripts.lexicon.build_data_manifest import (
    HERITAGE_STATUS_SEEDS,
    SURZHYK_TO_AVOID_SEEDS,
    _atlas_record_for_manifest,
    _lemma_key,
    build_manifest,
)


def test_vesum_alias_folds_inflection_into_taught_lemma(monkeypatch) -> None:
    monkeypatch.setattr(
        build_data_manifest,
        "VESUM_INFLECTION_ALIASES_BY_KEY",
        {_lemma_key("брата"): "брат"},
    )
    rec = {"lemma": "брата", "source": "built_vocabulary"}
    out = _atlas_record_for_manifest(rec, {_lemma_key("брат")})
    assert out["lemma"] == "брат"
    assert out["atlas_normalization"]["kind"] == "vesum_inflection_to_lemma"
    assert out["atlas_normalization"]["source_lemma"] == "брата"


def test_vesum_alias_skips_when_target_lemma_not_taught(monkeypatch) -> None:
    # never create a new lemma page: if the target isn't already taught, leave the form alone
    monkeypatch.setattr(
        build_data_manifest,
        "VESUM_INFLECTION_ALIASES_BY_KEY",
        {_lemma_key("вареники"): "вареник"},
    )
    rec = {"lemma": "вареники", "source": "built_vocabulary"}
    out = _atlas_record_for_manifest(rec, set())
    assert out["lemma"] == "вареники"
    assert "atlas_normalization" not in out


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


def test_manifest_omits_non_lemma_surface_entries() -> None:
    manifest = build_manifest()
    entries = {entry["lemma"]: entry for entry in manifest["entries"]}

    for lemma in (
        "Давай!",
        "Смачного!",
        "Ходімо!",
        "в/у",
        "у/в",
        "і/й",
        "Богдане",
        "Соломіє",
    ):
        assert lemma not in entries


def test_manifest_maps_taught_vocatives_to_nominative_lemmas() -> None:
    manifest = build_manifest()
    entries = {entry["lemma"]: entry for entry in manifest["entries"]}

    expected = {
        "Олена": "Олено",
        "Марія": "Маріє",
        "Тарас": "Тарасе",
    }
    for lemma, source_lemma in expected.items():
        normalizations = entries[lemma]["atlas_normalizations"]

        assert any(
            normalization["kind"] == "vocative_to_nominative"
            and normalization["source_lemma"] == source_lemma
            for normalization in normalizations
        )


def test_manifest_canonicalizes_real_words_missing_from_vesum() -> None:
    manifest = build_manifest()
    entries = {entry["lemma"]: entry for entry in manifest["entries"]}

    assert "бірка" not in entries
    assert entries["бирка"]["atlas_normalizations"][0]["source_lemma"] == "бірка"
    assert any(
        usage["track"] == "a2" and usage["slug"] == "genitive-adjectives-pronouns"
        for usage in entries["бирка"]["course_usage"]
    )

    assert "прийом" not in entries
    assert entries["приймання"]["atlas_normalizations"][0]["source_lemma"] == "прийом"
    assert any(
        usage["track"] == "a2" and usage["slug"] == "genitive-prepositions-direction"
        for usage in entries["приймання"]["course_usage"]
    )


def test_manifest_url_slugs_are_unique() -> None:
    manifest = build_manifest()
    slugs: dict[str, list[str]] = {}
    for entry in manifest["entries"]:
        slugs.setdefault(entry["url_slug"], []).append(entry["lemma"])

    duplicates = {slug: lemmas for slug, lemmas in slugs.items() if len(lemmas) > 1}

    assert duplicates == {}
