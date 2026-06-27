import unicodedata

import scripts.lexicon.build_data_manifest as build_data_manifest
from scripts.lexicon.build_data_manifest import (
    HERITAGE_STATUS_SEEDS,
    SURZHYK_TO_AVOID_SEEDS,
    _atlas_record_for_manifest,
    _lemma_key,
    _merge_lemma_records,
    _slug_for_url,
    build_manifest,
)
from scripts.lexicon.lemma_normalization import strip_acute_stress


def test_strip_acute_stress_preserves_ukrainian_letters() -> None:
    assert strip_acute_stress("авантю\u0301рний") == "авантюрний"
    assert strip_acute_stress("й ї") == "й ї"
    assert "\u0306" in unicodedata.normalize("NFD", strip_acute_stress("й"))
    assert "\u0308" in unicodedata.normalize("NFD", strip_acute_stress("ї"))


def test_manifest_merge_strips_acute_stress_from_display_lemma() -> None:
    by_lemma: dict[str, dict] = {}
    module = {"track": "a1", "module_num": 1, "slug": "stress"}
    _merge_lemma_records(
        by_lemma,
        module,
        [
            {
                "lemma": "авантю\u0301рний",
                "source": "built_vocabulary",
                "gloss": "adventurous",
                "pos": "adj",
                "ipa": None,
            },
            {
                "lemma": "авантюрний",
                "source": "built_vocabulary",
                "gloss": "adventurous",
                "pos": "adj",
                "ipa": None,
            },
        ],
    )

    assert list(by_lemma) == [_lemma_key("авантюрний")]
    entry = by_lemma[_lemma_key("авантюрний")]
    assert entry["lemma"] == "авантюрний"
    assert entry["url_slug"] == "авантюрний"
    assert "\u0301" not in entry["lemma"]


def test_vesum_alias_folds_inflection_into_taught_lemma(monkeypatch) -> None:
    monkeypatch.setattr(
        build_data_manifest,
        "VESUM_INFLECTION_ALIASES_BY_KEY",
        {_lemma_key("брата"): "брат"},
    )
    rec = {"lemma": "брата", "source": "built_vocabulary", "gloss": "brother (gen./acc.)", "pos": "noun"}
    out = _atlas_record_for_manifest(rec, {_lemma_key("брат")})
    assert isinstance(out, list)
    assert len(out) == 2
    aliased, form_rec = out
    assert aliased["lemma"] == "брат"
    assert aliased["atlas_normalization"]["kind"] == "vesum_inflection_to_lemma"
    assert aliased["atlas_normalization"]["source_lemma"] == "брата"
    # Fold into an ALREADY-TAUGHT lemma keeps surface fields — they merge into the taught
    # head (whose own gloss/pos win in _merge_lemma_records), so they are harmless here.
    assert aliased["gloss"] == "brother (gen./acc.)"
    assert aliased["pos"] == "noun"
    assert form_rec["lemma"] == "брата"
    assert form_rec["source"] == "built_vocabulary_form"
    assert form_rec["form_of"] == {
        "lemma": "брат",
        "url_slug": _slug_for_url("брат"),
    }


def test_vesum_alias_folds_create_case_even_when_target_not_taught(monkeypatch) -> None:
    # tranche 2: the committed map is the authority. A create-case (lemma not separately
    # taught) folds and CREATES the lemma page — _merge_lemma_records materializes вареник.
    monkeypatch.setattr(
        build_data_manifest,
        "VESUM_INFLECTION_ALIASES_BY_KEY",
        {_lemma_key("вареники"): "вареник"},
    )
    rec = {"lemma": "вареники", "source": "built_vocabulary", "gloss": "varenyky", "pos": "noun"}
    out = _atlas_record_for_manifest(rec, set())  # вареник NOT in taught set
    assert isinstance(out, list)
    assert len(out) == 2
    aliased, form_rec = out
    assert aliased["lemma"] == "вареник"
    assert aliased["atlas_normalization"]["kind"] == "vesum_inflection_to_lemma"
    # Create-case: the surface's gloss/pos describe the inflected surface, NOT the new
    # citation-form lemma head, so they must NOT be asserted on it (#3277 real-data catch:
    # заходьте→заходити was published as pos="imperative", восьма→восьмий as "feminine").
    # Enrichment supplies the lemma's meaning; renderer degrades gracefully on null.
    assert aliased["gloss"] is None
    assert aliased["pos"] is None
    # Surface values are preserved as provenance for traceability.
    assert "varenyky" in aliased["atlas_normalization"]["reason"]
    assert form_rec["lemma"] == "вареники"
    assert form_rec["source"] == "built_vocabulary_form"
    assert form_rec["form_of"] == {
        "lemma": "вареник",
        "url_slug": _slug_for_url("вареник"),
    }


def test_vesum_alias_leaves_unmapped_form_untouched(monkeypatch) -> None:
    # a form NOT in the map (e.g. a homograph deferred to the curated pass) is unchanged
    monkeypatch.setattr(build_data_manifest, "VESUM_INFLECTION_ALIASES_BY_KEY", {})
    rec = {"lemma": "сьома", "source": "built_vocabulary"}
    out = _atlas_record_for_manifest(rec, set())
    assert out["lemma"] == "сьома"
    assert "atlas_normalization" not in out


def test_slash_particle_not_published_as_atlas_head() -> None:
    rec = {"lemma": "б/би", "source": "built_vocabulary", "gloss": "conditional particle", "pos": "particle"}

    assert _atlas_record_for_manifest(rec, set()) is None


def test_suffixes_abbreviations_and_labels_not_published_as_atlas_heads() -> None:
    for lemma in (
        "-ся",
        "-сь",
        "1к",
        "2к",
        "кв.м",
        "грн/міс",
        "б/м",
        "з/із/зі",
        "най-",
        "неозначено-кількісний",
        "палаючий",
        "парковка",
        "пасивноподібний",
        "питально-відносний",
    ):
        rec = {"lemma": lemma, "source": "built_vocabulary"}

        assert _atlas_record_for_manifest(rec, set()) is None


def test_manifest_canonicalizes_service_vocab_to_valid_atlas_heads() -> None:
    delivery = _atlas_record_for_manifest(
        {"lemma": "доставка", "source": "built_vocabulary", "gloss": "delivery", "pos": "noun:f"},
        set(),
    )
    fitting_room = _atlas_record_for_manifest(
        {"lemma": "примірочна", "source": "built_vocabulary", "gloss": "fitting room", "pos": "noun:f"},
        set(),
    )

    assert delivery["lemma"] == "доставляння"
    assert delivery["atlas_normalization"]["kind"] == "vesum_canonical_head"
    assert fitting_room["lemma"] == "примірочна кімната"
    assert fitting_room["atlas_normalization"]["kind"] == "vesum_canonical_head"


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
        assert entries[lemma]["seed_group"] == "heritage-status-samples"
        if entries[lemma]["primary_source"] == "heritage_status_seed":
            assert entries[lemma]["course_usage"] == []
        else:
            assert entries[lemma]["primary_source"].startswith("built_vocabulary")
            assert entries[lemma]["course_usage"]


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
            normalization["kind"] == "vocative_to_nominative" and normalization["source_lemma"] == source_lemma
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


def test_resolve_slug_collisions_folds_comma_variant() -> None:
    """Comma-variant lemmas that collide on slug fold into one canonical entry."""
    from scripts.lexicon.build_data_manifest import (
        _resolve_slug_collisions,
        _slug_for_url,
    )

    # Precondition: the slug function folds commas, so these collide.
    assert _slug_for_url("тому що") == _slug_for_url("тому, що")

    by_lemma = {
        "тому що": {
            "lemma": "тому що",
            "url_slug": _slug_for_url("тому що"),
            "gloss": "because",
            "pos": "conj",
            "ipa": None,
            "primary_source": "built_vocabulary",
            "course_usage": [{"track": "b1", "module_num": 1, "slug": "m1", "context": "built_vocabulary"}],
        },
        "тому, що": {
            "lemma": "тому, що",
            "url_slug": _slug_for_url("тому, що"),
            "gloss": "because (comma form)",
            "pos": "conj",
            "ipa": None,
            "primary_source": "built_vocabulary",
            "course_usage": [{"track": "b1", "module_num": 2, "slug": "m2", "context": "built_vocabulary"}],
            "atlas_normalizations": [{"kind": "calque_correction", "source_lemma": "x"}],
        },
    }

    _resolve_slug_collisions(by_lemma)

    survivors = list(by_lemma.values())
    assert len(survivors) == 1
    entry = survivors[0]
    # Canonical = the form WITHOUT interior punctuation.
    assert entry["lemma"] == "тому що"
    assert entry["slug_variants"] == ["тому, що"]
    # course_usage from both folded entries is merged (deduped by module identity).
    assert {u["module_num"] for u in entry["course_usage"]} == {1, 2}
    # normalizations from the folded entry are carried over.
    assert any(n["kind"] == "calque_correction" for n in entry.get("atlas_normalizations", []))
