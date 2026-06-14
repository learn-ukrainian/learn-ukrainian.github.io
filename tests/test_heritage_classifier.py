import json
from pathlib import Path

from scripts.lexicon.heritage_classifier import classify_lemma, classify_surface_form

DB = Path(__file__).resolve().parent / "fixtures" / "heritage_sample.db"
VESUM_DB = Path(__file__).resolve().parent / "fixtures" / "vesum_sample.db"


def test_surface_drugoje_literary_quote_does_not_create_heritage_badge() -> None:
    status = classify_surface_form("другоє", db_path=DB, vesum_db_path=VESUM_DB)

    assert status["classification"] == "unknown"
    assert status["is_russianism"] is False
    assert status["russian_shadow"] is True
    assert status["attestations"] == []


def test_dialect_heritage_forms_are_not_blocked_by_russian_shadow() -> None:
    for word in ("ягілка", "гагілка"):
        lemma_status = classify_lemma(word, db_path=DB, vesum_db_path=VESUM_DB)
        surface_status = classify_surface_form(word, db_path=DB, vesum_db_path=VESUM_DB)

        assert lemma_status["classification"] == "dialect"
        assert lemma_status["is_russianism"] is False
        assert lemma_status["russian_shadow"] is True
        assert surface_status["classification"] == "dialect"
        assert surface_status["is_russianism"] is False
        assert surface_status["attestations"]


def test_pereklychka_is_attested_standard_despite_vesum_gap() -> None:
    status = classify_surface_form("перекличка", db_path=DB, vesum_db_path=VESUM_DB)

    assert status["classification"] in {"standard", "borrowing"}
    assert status["is_russianism"] is False
    assert any(attestation["source"] == "sum11" for attestation in status["attestations"])


def test_slash_separated_atlas_lemmas_merge_variant_attestations() -> None:
    status = classify_lemma("вчителька / учителька", db_path=DB, vesum_db_path=VESUM_DB)

    assert status["classification"] == "standard"
    assert status["is_russianism"] is False
    assert {attestation["ref"] for attestation in status["attestations"]} == {"вчителька", "учителька"}


def test_specified_russianisms_keep_standard_alternatives() -> None:
    expected = {
        "протиріччя": "суперечність",
        "діюча": "чинна",
    }

    for word, alternative in expected.items():
        status = classify_surface_form(word, db_path=DB, vesum_db_path=VESUM_DB)

        assert status["classification"] == "russianism"
        assert status["is_russianism"] is True
        assert any(
            attestation["source"] == "standard_alternative" and attestation["ref"] == alternative
            for attestation in status["attestations"]
        )


def test_atlas_heritage_labels_use_source_backed_evidence() -> None:
    expected = {
        "глагол": "authentic-archaism",
        "опришок": "historism",
        "ягілка": "dialect",
        "гагілка": "dialect",
    }

    for lemma, classification in expected.items():
        status = classify_lemma(lemma, db_path=DB, vesum_db_path=VESUM_DB)

        assert status["classification"] == classification
        assert status["is_russianism"] is False
        assert any(
            attestation["source"] in {"grinchenko_1907", "esum"}
            for attestation in status["attestations"]
        )


def test_fixture_supports_search_heritage_db_path() -> None:
    from wiki.sources_db import search_heritage

    expected_families = {
        "глагол": "grinchenko",
        "опришок": "esum",
        "ягілка": "esum",
        "гагілка": "esum",
    }

    for lemma, source_family in expected_families.items():
        hits = search_heritage(lemma, include_live_slovnyk=False, db_path=DB)

        assert any(hit["source_family"] == source_family for hit in hits)


def test_common_modern_lemmas_do_not_get_heritage_badges() -> None:
    for lemma in (
        "бути",
        "автобус",
        "журналіст",
        "книга",
        "білий",
        "гарний",
        "адреса",
        "банкір",
        "вельми",
        "гетьман",
        "десятина",
    ):
        status = classify_lemma(lemma, db_path=DB, vesum_db_path=VESUM_DB)

        assert status["classification"] == "standard"
        assert status["is_russianism"] is False


def test_kobita_ignores_cached_sum20_regional_evidence(monkeypatch, tmp_path) -> None:
    cache_dir = tmp_path / "slovnyk_cache"
    cache_dir.mkdir()
    (cache_dir / "кобіта.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "lemma": "кобіта",
                "lookup_word": "кобіта",
                "lookups": {
                    "newsum": {
                        "dictionary_slug": "newsum",
                        "dictionary_label": "Словник української мови у 20 томах (СУМ-20)",
                        "word": "кобіта",
                        "text": "КОБІТА, и, ж., зах. Те саме, що жінка.",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LEXICON_SLOVNYK_CACHE", str(cache_dir))

    status = classify_lemma("кобіта", db_path=DB, vesum_db_path=VESUM_DB)

    assert status["classification"] == "standard"
    assert status["is_russianism"] is False
    assert not any("СУМ-20" in attestation["source"] for attestation in status["attestations"])
    assert [(attestation["source"], attestation["ref"]) for attestation in status["attestations"]] == [
        ("VESUM", "кобіта")
    ]
