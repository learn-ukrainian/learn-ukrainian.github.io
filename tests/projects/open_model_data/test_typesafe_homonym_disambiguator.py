"""Tests for TypeSafe System One Contextual Homonym & Valency Disambiguation (#8182)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.projects.open_model_data.typesafe_homonym_disambiguator import (
    GrammaticalForm,
    SyntacticRole,
    TypeSafeHomonymDisambiguator,
    _resolve_typesafe_key,
)


def test_myla_homonym_disambiguation_heuristic() -> None:
    """Verify that «мила» is correctly disambiguated across verb, noun, and adjective contexts."""
    disambiguator = TypeSafeHomonymDisambiguator(api_key="")

    # 1. Verb reading: «дівчина мила руки»
    s_verb = "Дівчина ретельно мила руки перед обідом."
    res_verb = disambiguator.disambiguate(s_verb, "мила")
    assert res_verb.grammatical_form == GrammaticalForm.FINITE_VERB_PAST
    assert res_verb.syntactic_role == SyntacticRole.PREDICATE_VERB
    assert res_verb.lemma == "мити"
    assert res_verb.confidence >= 0.85

    # 2. Noun reading: «шматок мила»
    s_noun = "Він узяв невеликий шматок мила з полиці."
    res_noun = disambiguator.disambiguate(s_noun, "мила")
    assert res_noun.grammatical_form == GrammaticalForm.NOUN_GENITIVE
    assert res_noun.syntactic_role == SyntacticRole.ADNOMINAL_ATTRIBUTE
    assert res_noun.lemma == "мило"
    assert res_noun.confidence >= 0.85

    # 3. Adjective reading: «була мила»
    s_adj = "Ця дівчина була напрочуд мила і привітна."
    res_adj = disambiguator.disambiguate(s_adj, "мила")
    assert res_adj.grammatical_form == GrammaticalForm.ADJECTIVE
    assert res_adj.lemma in ("милий", "мила")
    assert res_adj.confidence >= 0.85


def test_pyly_homonym_disambiguation_heuristic() -> None:
    """Verify that «пили» is disambiguated between verb and noun."""
    disambiguator = TypeSafeHomonymDisambiguator(api_key="")

    # Verb reading: «вони пили воду»
    s_verb = "Вони пили воду біля джерела."
    res_verb = disambiguator.disambiguate(s_verb, "пили")
    assert res_verb.grammatical_form == GrammaticalForm.FINITE_VERB_PAST
    assert res_verb.syntactic_role == SyntacticRole.PREDICATE_VERB
    assert res_verb.lemma == "пити"

    # Noun reading: «дві пили заводу»
    s_noun = "На складі лежали дві пили заводу."
    res_noun = disambiguator.disambiguate(s_noun, "пили")
    assert res_noun.grammatical_form == GrammaticalForm.NOUN_GENITIVE
    assert res_noun.syntactic_role == SyntacticRole.ADNOMINAL_ATTRIBUTE
    assert res_noun.lemma == "пила"


@patch("urllib.request.urlopen")
def test_remote_batched_api_mock(mock_urlopen: MagicMock) -> None:
    """Verify mock TypeSafe System One API parsing."""
    resp_mock = MagicMock()
    resp_mock.read.return_value = json.dumps(
        {
            "model": "jev-latest",
            "answers": {
                "i0_form": {"type": "choice", "choice": "finite_verb_past", "confidence": 0.98},
                "i0_role": {"type": "choice", "choice": "predicate_verb", "confidence": 0.97},
                "i1_form": {"type": "choice", "choice": "noun_genitive", "confidence": 0.96},
                "i1_role": {"type": "choice", "choice": "adnominal_attribute", "confidence": 0.95},
            },
        }
    ).encode("utf-8")

    mock_urlopen.return_value.__enter__.return_value = resp_mock

    disambiguator = TypeSafeHomonymDisambiguator(api_key="fake-key")
    items = [
        ("Вона мила посуд.", "мила"),
        ("Брусок мила висох.", "мила"),
    ]
    results = disambiguator.batch_disambiguate(items)

    assert len(results) == 2
    assert results[0].grammatical_form == GrammaticalForm.FINITE_VERB_PAST
    assert results[0].syntactic_role == SyntacticRole.PREDICATE_VERB
    assert results[0].confidence >= 0.95
    assert results[1].grammatical_form == GrammaticalForm.NOUN_GENITIVE
    assert results[1].syntactic_role == SyntacticRole.ADNOMINAL_ATTRIBUTE


@pytest.mark.live_network
def test_live_typesafe_api_homonym_disambiguation() -> None:
    """Live network test against TypeSafe System One API if key is present."""
    api_key = _resolve_typesafe_key()
    if not api_key:
        pytest.skip("TypeSafe API key not found; skipping live test")

    disambiguator = TypeSafeHomonymDisambiguator(api_key=api_key)
    items = [
        ("Сестра уважно шила новий святковий одяг.", "шила"),
        ("Гострого шила не сховаєш у мішку.", "шила"),
    ]
    results = disambiguator.batch_disambiguate(items)

    assert len(results) == 2
    # 1. шила (verb past): «Сестра уважно шила новий святковий одяг»
    assert results[0].grammatical_form == GrammaticalForm.FINITE_VERB_PAST
    assert results[0].syntactic_role == SyntacticRole.PREDICATE_VERB
    assert results[0].lemma == "шити"

    # 2. шила (noun genitive from шило): «Гострого шила не сховаєш у мішку»
    assert results[1].grammatical_form == GrammaticalForm.NOUN_GENITIVE
    assert results[1].lemma == "шило"
    # Low confidence / complex negative government triggers verification
    assert results[1].confidence <= 0.85
    assert results[1].needs_verification is True


def test_homonym_disambiguation_hermetic_without_vesum(tmp_path) -> None:
    """Verify hermetic fallback when vesum database is completely unavailable (e.g. in CI)."""
    fake_path = tmp_path / "nonexistent_vesum.db"
    disambiguator = TypeSafeHomonymDisambiguator(api_key="", vesum_path=fake_path)

    # Disambiguate without database connection
    res_verb = disambiguator.disambiguate("Дівчина ретельно мила руки.", "мила")
    assert res_verb.grammatical_form == GrammaticalForm.FINITE_VERB_PAST
    assert res_verb.lemma == "мити"

    res_noun = disambiguator.disambiguate("Шматок мила лежав на столі.", "мила")
    assert res_noun.grammatical_form == GrammaticalForm.NOUN_GENITIVE
    assert res_noun.lemma == "мило"

    res_saw = disambiguator.disambiguate("Дві пили заводу стояли в кутку.", "пили")
    assert res_saw.grammatical_form == GrammaticalForm.NOUN_GENITIVE
    assert res_saw.lemma == "пила"
