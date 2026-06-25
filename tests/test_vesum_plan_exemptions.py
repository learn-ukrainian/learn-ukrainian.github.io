from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from scripts.build import linear_pipeline


def _rejecting_verifier(
    missing_surfaces: set[str],
) -> Callable[[list[str]], dict[str, list[dict[str, str]]]]:
    missing_lc = {
        linear_pipeline._normalize_for_vesum(surface).lower()
        for surface in missing_surfaces
    }

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        return {
            word: (
                []
                if linear_pipeline._normalize_for_vesum(word).lower() in missing_lc
                else [{"lemma": word}]
            )
            for word in words
        }

    return verify_words


def _disable_existing_attestations(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_attested_missing(
        missing_lc: set[str],
        unchecked_pairs: list[tuple[str, str, str]],
    ) -> set[str]:
        return set()

    monkeypatch.setattr(
        linear_pipeline,
        "_resolve_foreign_proper_noun_attested_missing",
        no_attested_missing,
    )
    monkeypatch.setattr(
        linear_pipeline,
        "_resolve_folk_heritage_attested_missing",
        no_attested_missing,
    )


def _gate(
    text: str,
    monkeypatch: pytest.MonkeyPatch,
    *,
    missing_surfaces: set[str],
    plan: dict[str, Any] | None = None,
    level: str = "folk",
) -> dict[str, Any]:
    _disable_existing_attestations(monkeypatch)
    return linear_pipeline._vesum_gate(
        module_text=text,
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=_rejecting_verifier(missing_surfaces),
        level=level,
        plan_vesum_exemptions=plan,
    )


def test_foreign_cultural_terms_exempt_titlecase_and_lowercase_hanami(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = {
        "foreign_cultural_terms": [
            {
                "term": "Белтейн",
                "forms": ["Белтейн", "Белтейном"],
                "wikipedia_url": "https://uk.wikipedia.org/wiki/Белтейн",
                "rationale": "кельтське весняне свято",
            },
            {
                "term": "ханамі",
                "forms": ["ханамі"],
                "wikipedia_url": "https://uk.wikipedia.org/wiki/Ханамі",
                "rationale": "японський звичай милування квітами",
            },
        ]
    }

    gate = _gate(
        "Белтейн Белтейном ханамі",
        monkeypatch,
        missing_surfaces={"Белтейн", "Белтейном", "ханамі"},
        plan=plan,
    )

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["plan_exempted"] == 3
    assert set(gate["plan_exempted_by_category"]["foreign_cultural_terms"]) == {
        "Белтейн",
        "Белтейном",
        "ханамі",
    }


def test_foreign_cultural_terms_fail_closed_without_valid_ukwiki_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = {
        "foreign_cultural_terms": [
            {
                "term": "Белтейн",
                "forms": ["Белтейн"],
                "wikipedia_url": "https://example.invalid/Белтейн",
                "rationale": "кельтське весняне свято",
            }
        ]
    }

    gate = _gate(
        "Белтейн",
        monkeypatch,
        missing_surfaces={"Белтейн"},
        plan=plan,
    )

    assert gate["passed"] is False
    assert "wikipedia_url" in str(gate["error"])


def test_quoted_critical_terms_require_guillemet_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = {
        "quoted_critical_terms": [
            {
                "term": "общеславянська",
                "forms": ["общеславянської"],
                "rationale": "імперський термін, цитований для критики",
            }
        ]
    }

    quoted_gate = _gate(
        "Термін «общеславянської» тут критикуємо.",
        monkeypatch,
        missing_surfaces={"общеславянської"},
        plan=plan,
    )
    unquoted_gate = _gate(
        "Термін общеславянської тут критикуємо.",
        monkeypatch,
        missing_surfaces={"общеславянської"},
        plan=plan,
    )

    assert quoted_gate["passed"] is True
    assert quoted_gate["missing"] == []
    assert quoted_gate["plan_exempted_by_category"]["quoted_critical_terms"] == [
        "общеславянської"
    ]
    assert unquoted_gate["passed"] is False
    assert unquoted_gate["missing"] == ["общеславянської"]
    assert unquoted_gate["plan_exempted"] == 0


def test_corpus_attested_quotes_accept_guillemet_or_backtick_and_require_source_chunk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = {
        "corpus_attested_quotes": [
            {
                "term": "жаворонку",
                "forms": ["жаворонку"],
                "source_chunk": "da46aa92_c0284",
                "rationale": "вербатим із цитованої веснянки",
            }
        ]
    }

    guillemet_gate = _gate(
        "Порівнюємо жаворонку: «жаворонку».",
        monkeypatch,
        missing_surfaces={"жаворонку"},
        plan=plan,
    )
    backtick_gate = _gate(
        "Порівнюємо жаворонку (`жаворонку`).",
        monkeypatch,
        missing_surfaces={"жаворонку"},
        plan=plan,
    )
    bad_gate = _gate(
        "Порівнюємо жаворонку: «жаворонку».",
        monkeypatch,
        missing_surfaces={"жаворонку"},
        plan={
            "corpus_attested_quotes": [
                {
                    "term": "жаворонку",
                    "forms": ["жаворонку"],
                    "rationale": "вербатим із цитованої веснянки",
                }
            ]
        },
    )

    assert guillemet_gate["passed"] is True
    assert guillemet_gate["missing"] == []
    assert backtick_gate["passed"] is True
    assert backtick_gate["missing"] == []
    assert bad_gate["passed"] is False
    assert "source_chunk" in str(bad_gate["error"])


def test_plan_exemption_entry_requires_non_empty_rationale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = _gate(
        "Белтейн",
        monkeypatch,
        missing_surfaces={"Белтейн"},
        plan={
            "foreign_cultural_terms": [
                {
                    "term": "Белтейн",
                    "forms": ["Белтейн"],
                    "wikipedia_url": "https://uk.wikipedia.org/wiki/Белтейн",
                    "rationale": "   ",
                }
            ]
        },
    )

    assert gate["passed"] is False
    assert "rationale" in str(gate["error"])


def test_core_level_ignores_plan_vesum_exemptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = _gate(
        "ханамі",
        monkeypatch,
        missing_surfaces={"ханамі"},
        level="a1",
        plan={
            "foreign_cultural_terms": [
                {
                    "term": "ханамі",
                    "forms": ["ханамі"],
                    "wikipedia_url": "https://uk.wikipedia.org/wiki/Ханамі",
                    "rationale": "японський звичай милування квітами",
                }
            ]
        },
    )

    assert gate["passed"] is False
    assert gate["missing"] == ["ханамі"]
    assert gate["plan_exempted"] == 0


def test_undeclared_real_misspelling_stays_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = _gate(
        "ханамі музеїфікація",
        monkeypatch,
        missing_surfaces={"ханамі", "музеїфікація"},
        plan={
            "foreign_cultural_terms": [
                {
                    "term": "ханамі",
                    "forms": ["ханамі"],
                    "wikipedia_url": "https://uk.wikipedia.org/wiki/Ханамі",
                    "rationale": "японський звичай милування квітами",
                }
            ]
        },
    )

    assert gate["passed"] is False
    assert gate["missing"] == ["музеїфікація"]
    assert gate["plan_exempted_words"] == ["ханамі"]


def test_plan_exemption_report_shape_by_category(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = _gate(
        "Белтейн. Термін «общеславянської» критикуємо. Жаворонку поруч: `жаворонку`.",
        monkeypatch,
        missing_surfaces={"Белтейн", "общеславянської", "Жаворонку"},
        plan={
            "foreign_cultural_terms": [
                {
                    "term": "Белтейн",
                    "forms": ["Белтейн"],
                    "wikipedia_url": "https://uk.wikipedia.org/wiki/Белтейн",
                    "rationale": "кельтське весняне свято",
                }
            ],
            "quoted_critical_terms": [
                {
                    "term": "общеславянська",
                    "forms": ["общеславянської"],
                    "rationale": "імперський термін, цитований для критики",
                }
            ],
            "corpus_attested_quotes": [
                {
                    "term": "жаворонку",
                    "forms": ["жаворонку"],
                    "source_chunk": "da46aa92_c0284",
                    "rationale": "вербатим із цитованої веснянки",
                }
            ],
        },
    )

    assert gate["passed"] is True
    assert gate["plan_exempted"] == 3
    assert gate["plan_exempted_words"] == [
        "Белтейн",
        "Жаворонку",
        "общеславянської",
    ]
    assert gate["plan_exempted_by_category"] == {
        "foreign_cultural_terms": ["Белтейн"],
        "quoted_critical_terms": ["общеславянської"],
        "corpus_attested_quotes": ["Жаворонку"],
    }


def test_quoted_critical_terms_backtick_context_is_not_enough(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # quoted_critical_terms is guarded by GUILLEMET context ONLY. A surface that
    # is missing (because it occurs in plain prose) and is ALSO shown in backticks
    # — but never in «…» — must NOT be exempted. (Backtick-only text is stripped
    # from VESUM input, so the prose occurrence is what makes it missing.)
    plan = {
        "quoted_critical_terms": [
            {
                "term": "общеславянська",
                "forms": ["общеславянської"],
                "rationale": "імперський термін, цитований для критики",
            }
        ]
    }
    gate = _gate(
        "Термін общеславянської у прозі, а також `общеславянської` у бектиках.",
        monkeypatch,
        missing_surfaces={"общеславянської"},
        plan=plan,
    )
    assert gate["passed"] is False
    assert gate["missing"] == ["общеславянської"]
    assert gate["plan_exempted"] == 0


def test_foreign_cultural_degenerate_ukwiki_url_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The empty-article URL "https://uk.wikipedia.org/wiki/" must NOT validate.
    gate = _gate(
        "Белтейн",
        monkeypatch,
        missing_surfaces={"Белтейн"},
        plan={
            "foreign_cultural_terms": [
                {
                    "term": "Белтейн",
                    "forms": ["Белтейн"],
                    "wikipedia_url": "https://uk.wikipedia.org/wiki/",
                    "rationale": "кельтське весняне свято",
                }
            ]
        },
    )
    assert gate["passed"] is False
    assert "wikipedia_url" in str(gate["error"])


def test_runaway_unbalanced_guillemet_span_does_not_exempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # An unbalanced « paired with a far-later » would otherwise yield a runaway
    # span (> _MAX_GUILLEMET_SPAN_CHARS) that falsely marks an un-quoted declared
    # token as quoted. The span bound must drop it, leaving the token missing.
    filler = "слово " * 60  # ~300 chars between the stray « and the real »
    text = f"Початок « {filler} жаворонку далі правильна цитата»."
    plan = {
        "corpus_attested_quotes": [
            {
                "term": "жаворонку",
                "forms": ["жаворонку"],
                "source_chunk": "da46aa92_c0284",
                "rationale": "вербатим із цитованої веснянки",
            }
        ]
    }
    gate = _gate(
        text,
        monkeypatch,
        missing_surfaces={"жаворонку"},
        plan=plan,
    )
    assert gate["passed"] is False
    assert "жаворонку" in gate["missing"]
    assert gate["plan_exempted"] == 0


def test_empty_forms_list_exempts_only_the_term(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # forms: [] is valid and exempts only the term surface itself, not arbitrary
    # inflections.
    plan = {
        "foreign_cultural_terms": [
            {
                "term": "ханамі",
                "forms": [],
                "wikipedia_url": "https://uk.wikipedia.org/wiki/Милування_квітами",
                "rationale": "японський звичай милування квітами",
            }
        ]
    }
    gate = _gate(
        "ханамі ханамікою",
        monkeypatch,
        missing_surfaces={"ханамі", "ханамікою"},
        plan=plan,
    )
    assert gate["passed"] is False
    assert gate["missing"] == ["ханамікою"]
    assert gate["plan_exempted_words"] == ["ханамі"]
