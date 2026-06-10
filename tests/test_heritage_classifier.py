from pathlib import Path

import pytest

from scripts.lexicon.heritage_classifier import classify_lemma, classify_surface_form

pytestmark = pytest.mark.skipif(
    not Path("data/sources.db").exists(),
    reason="requires gitignored corpus DB (data/sources.db); heritage engine verified locally 5/5",
)
def test_surface_drugoje_uses_verified_literary_quote() -> None:
    status = classify_surface_form("другоє")

    assert status["classification"] == "authentic-archaism"
    assert status["is_russianism"] is False
    assert status["russian_shadow"] is True
    assert any(
        attestation["source"] == "literary_fts"
        and attestation["ref"] == "feaa5fa7_c0572"
        and attestation["score"] == 1.0
        and attestation["quote"] == "на другоє літо поховаємо"
        for attestation in status["attestations"]
    )


def test_dialect_heritage_forms_are_not_blocked_by_russian_shadow() -> None:
    for word in ("ягілка", "гагілка"):
        lemma_status = classify_lemma(word)
        surface_status = classify_surface_form(word)

        assert lemma_status["classification"] == "dialect"
        assert lemma_status["is_russianism"] is False
        assert lemma_status["russian_shadow"] is True
        assert surface_status["classification"] == "dialect"
        assert surface_status["is_russianism"] is False
        assert surface_status["attestations"]


def test_pereklychka_is_attested_standard_despite_vesum_gap() -> None:
    status = classify_surface_form("перекличка")

    assert status["classification"] in {"standard", "borrowing"}
    assert status["is_russianism"] is False
    assert any(attestation["source"] == "sum11" for attestation in status["attestations"])


def test_slash_separated_atlas_lemmas_merge_variant_attestations() -> None:
    status = classify_lemma("вчителька / учителька")

    assert status["classification"] == "standard"
    assert status["is_russianism"] is False
    assert {attestation["ref"] for attestation in status["attestations"]} == {"вчителька", "учителька"}


def test_specified_russianisms_keep_standard_alternatives() -> None:
    expected = {
        "протиріччя": "суперечність",
        "діюча": "чинна",
    }

    for word, alternative in expected.items():
        status = classify_surface_form(word)

        assert status["classification"] == "russianism"
        assert status["is_russianism"] is True
        assert any(
            attestation["source"] == "standard_alternative" and attestation["ref"] == alternative
            for attestation in status["attestations"]
        )
