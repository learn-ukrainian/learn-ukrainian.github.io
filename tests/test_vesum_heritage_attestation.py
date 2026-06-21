from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.build import linear_pipeline

# Mirror the heritage-classifier convention (tests/test_heritage_classifier.py):
# CI ships only a stub sources.db, so existence is not enough — require the full
# ~1.7GB corpus. The engine is verified locally; these cases skip on CI.
requires_sources_db = pytest.mark.skipif(
    not Path("data/sources.db").exists()
    or Path("data/sources.db").stat().st_size < 100_000_000,
    reason="requires the full ~1.7GB corpus sources.db; CI has only a stub; heritage engine verified locally",
)


def _vesum_rejects_all(words: list[str]) -> dict[str, list[dict[str, str]]]:
    return {word: [] for word in words}


def _gate(text: str, *, level: str = "folk") -> dict[str, object]:
    return linear_pipeline._vesum_gate(
        module_text=text,
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=_vesum_rejects_all,
        level=level,
    )


def test_folk_vesum_gate_accepts_committed_slovnyk_attested_terms() -> None:
    gate = _gate("риндзівка ягілка гагілка ягівка")

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["heritage_attested"] == 4
    assert gate["heritage_attested_words"] == ["гагілка", "риндзівка", "ягівка", "ягілка"]


def test_folk_vesum_gate_accepts_committed_attested_plural_surfaces() -> None:
    gate = _gate("риндзівки ягілки гагілки ягівки")

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["heritage_attested"] == 4


def test_folk_vesum_gate_still_rejects_russianism_not_in_attestations() -> None:
    gate = _gate("аранжировку")

    assert gate["passed"] is False
    assert gate["missing"] == ["аранжировку"]
    assert gate["heritage_attested"] == 0


def test_folk_vesum_gate_still_rejects_unattested_coinages() -> None:
    gate = _gate("городалька побажальний")

    assert gate["passed"] is False
    assert gate["missing"] == ["городалька", "побажальний"]
    assert gate["heritage_attested"] == 0


def test_attestation_row_marked_russianism_does_not_satisfy_gate(tmp_path, monkeypatch) -> None:
    path = tmp_path / "folk_heritage_attestations.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "attestations": [
                    {
                        "lemma": "фантомка",
                        "is_russianism": True,
                        "citations": [
                            {
                                "dictionary_slug": "newsum",
                                "url": "https://slovnyk.me/dict/newsum/fantomka",
                            }
                        ],
                        "gloss": "guard row",
                        "accepted_surfaces": ["фантомка"],
                    }
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(linear_pipeline, "FOLK_HERITAGE_ATTESTATIONS_PATH", path)

    gate = _gate("фантомка")

    assert gate["passed"] is False
    assert gate["missing"] == ["фантомка"]
    assert gate["heritage_attested"] == 0


def test_core_level_vesum_gate_does_not_use_folk_attestation_fallback() -> None:
    gate = _gate("риндзівка", level="a1")

    assert gate["passed"] is False
    assert gate["missing"] == ["риндзівка"]
    assert gate["heritage_attested"] == 0


# --- Heritage classifier consumption (#2912) -------------------------------
# The shared classifier is now the primary authority; the committed YAML
# allowlist (#2899) is a thin override. These cases are attested ONLY by the
# classifier (corpus/dictionary evidence), not by the committed allowlist, so
# they prove the gate consumes the engine rather than re-listing terms by hand.


@requires_sources_db
def test_folk_vesum_gate_accepts_engine_authentic_not_in_allowlist() -> None:
    # `Кострубонько` (ritual figure) is NOT in folk_heritage_attestations.yaml;
    # only the classifier attests it as authentic-archaism. (#3647: `другоє` was
    # dropped — VESUM has no such form and search_heritage returns no evidence, so
    # the existence gate correctly does not attest it; the fixture overclaimed it.)
    gate = _gate("Кострубонько")

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["heritage_attested"] == 1


@requires_sources_db
def test_folk_vesum_gate_still_rejects_teaching_prose_russianisms() -> None:
    # Teaching-prose russianisms the classifier flags is_russianism=True must
    # keep failing the gate (→ суперечність / чинна). Gate teeth preserved.
    gate = _gate("протиріччя діюча")

    assert gate["passed"] is False
    # _vesum_gate sorts `missing` internally; Cyrillic order: діюча < протиріччя.
    assert gate["missing"] == ["діюча", "протиріччя"]
    assert gate["heritage_attested"] == 0


def test_folk_vesum_gate_still_rejects_unknown_coinage_via_engine() -> None:
    # `городалька` is an unknown coinage (classification="unknown") — neither the
    # allowlist nor the classifier attests it. Stays flagged with or without the
    # corpus DB (engine degrades to False when unavailable), so no DB guard.
    gate = _gate("городалька")

    assert gate["passed"] is False
    assert gate["missing"] == ["городалька"]
    assert gate["heritage_attested"] == 0


# --- Morphology fallback: VESUM-gap inflections + negated participles ------
# VESUM enumerates the headword of a dialectal noun (гагілка) but not every
# oblique case (гагілку, ягілками), and not the regular `не`-negation of a
# standard participle (незгладжений←згладжений). The gate lemmatises / strips
# `не` and re-checks the base via the classifier, so valid inflected Ukrainian
# passes — while russianisms and coinages stay flagged.


@requires_sources_db
def test_folk_vesum_gate_accepts_oblique_inflections_of_dialect_words() -> None:
    # гагілку (acc.sg) / ягілками (instr.pl): lemma → гагілка / ягілка → dialect.
    gate = _gate("гагілку ягілками")

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["heritage_attested"] == 2


@requires_sources_db
def test_folk_vesum_gate_accepts_negated_participles_of_standard_bases() -> None:
    # незгладжений / непідперта: strip `не` → згладжений / підперта → standard.
    gate = _gate("незгладжений непідперта")

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["heritage_attested"] == 2


@requires_sources_db
def test_folk_vesum_gate_accepts_productive_derivational_bases() -> None:
    # (#3647: `другоє` dropped — unattested in VESUM and the heritage classifier;
    # the existence gate cannot attest it. The remaining 7 are real productive forms.)
    gate = _gate("гаївковий знеособлювальними виворожувати виворожують ягілки гагілку незгладжений")

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["heritage_attested"] == 7


@requires_sources_db
def test_folk_vesum_gate_accepts_productive_noun_diminutives() -> None:
    gate = _gate("гаївочка гаївочку книжечка словечко")

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["heritage_attested"] == 4


def test_russian_shadow_diminutive_surface_guard_blocks_derivational_rescue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.verification.check_ru_morph import is_russian_pattern

    surface = "протирічечка"
    shadow = is_russian_pattern(surface)
    assert shadow["matches_russian"] is True
    assert float(shadow["confidence"]) >= 0.7

    monkeypatch.setattr(
        linear_pipeline,
        "_engine_flags_russianism",
        lambda candidate: candidate == surface,
    )
    monkeypatch.setattr(
        linear_pipeline,
        "_derivational_base_candidates",
        lambda word: {"суперечність"} if word == surface else set(),
    )
    monkeypatch.setattr(
        linear_pipeline,
        "_engine_classifies_authentic",
        lambda candidate: candidate == "суперечність",
    )

    gate = _gate(surface)

    assert gate["passed"] is False
    assert gate["missing"] == [surface]
    assert gate["heritage_attested"] == 0


@requires_sources_db
def test_folk_vesum_gate_accepts_inflected_denominal_adjectives() -> None:
    gate = _gate("веснянкова веснянкове веснянкові")

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["heritage_attested"] == 3


@requires_sources_db
def test_morphology_fallback_does_not_leak_russianism_via_verb_root() -> None:
    # CRITICAL teeth check: `діюча` is a russianism (→ чинна/дійова) whose lemma is
    # the *standard* verb `діяти`. The russianism guard must stop the morphology
    # rescue from leaking it — `діюча` stays flagged despite a standard lemma.
    gate = _gate("діюча")

    assert gate["passed"] is False
    assert gate["missing"] == ["діюча"]
    assert gate["heritage_attested"] == 0


@requires_sources_db
def test_derivational_fallback_does_not_leak_adversarial_russianisms() -> None:
    leak_words = [
        "діюча",
        "протиріччя",
        "получаючий",
        "поступаючий",
        "находячийся",
        "глазний",
        "вкусний",
        "слідувати",
        "оказувати",
        "заказувати",
        "настаювати",
        "решати",
    ]

    gate = _gate(" ".join(leak_words))

    assert gate["passed"] is False
    assert set(gate["missing"]) == set(leak_words)
    assert gate["heritage_attested"] == 0


@requires_sources_db
def test_direct_standard_active_participle_calques_stay_existing_behavior() -> None:
    gate = _gate("бажаючий оточуючий керуючий завідуючий слідуючий")

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["heritage_attested"] == 5


def test_derivational_fallback_does_not_accept_coinages() -> None:
    gate = _gate("двохоровий обрядознавчий городалька")

    assert gate["passed"] is False
    assert set(gate["missing"]) == {"двохоровий", "городалька", "обрядознавчий"}
    assert gate["heritage_attested"] == 0


def test_morphology_fallback_does_not_apply_to_core_levels() -> None:
    # The heritage/morphology fallback is seminar/folk-scoped only.
    gate = _gate("гагілку", level="a1")

    assert gate["passed"] is False
    assert gate["missing"] == ["гагілку"]
    assert gate["heritage_attested"] == 0
