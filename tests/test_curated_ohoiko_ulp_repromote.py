from __future__ import annotations

import inspect

import pytest

from scripts.lexicon import curated_ohoiko_ulp_repromote as ohoiko_repromote
from scripts.lexicon import curated_textbook_jsonl_repromote as textbook_repromote
from scripts.lexicon import ohoiko_paired_headword_split as paired_split

_MODULES = (ohoiko_repromote, textbook_repromote)
_ALL_GLOSS_FILL_MODULES = (*_MODULES, paired_split)


@pytest.mark.parametrize("module", _ALL_GLOSS_FILL_MODULES, ids=lambda m: m.__name__)
def test_module_never_reads_sum11_table(module) -> None:
    """#7453: СУМ-11 (Soviet-era) is banned on Atlas, including as inventory
    gloss fill. No curated gloss-fill script may query the offline ``sum11``
    SQL table anywhere in its source."""
    source = inspect.getsource(module)
    assert "sum11" not in source.lower()
    assert not hasattr(module, "_sum11_gloss")


@pytest.mark.parametrize("module", _MODULES, ids=lambda m: m.__name__)
def test_sum20_vts_gloss_prefers_sum20(monkeypatch, module) -> None:
    monkeypatch.setattr(
        module,
        "_sum20_definition_card",
        lambda lemma: {"definitions": ["Символ держави."]},
    )
    monkeypatch.setattr(
        module,
        "_vts_definition_card",
        lambda lemma: {"definitions": ["ВТС text that must not be used."]},
    )

    assert module._sum20_vts_gloss("прапор") == "Символ держави."


@pytest.mark.parametrize("module", _MODULES, ids=lambda m: m.__name__)
def test_sum20_vts_gloss_falls_back_to_vts_when_sum20_missing(monkeypatch, module) -> None:
    """СУМ-20 volumes 17-20 (С-Я) are unpublished — ВТС fills the gap. Never
    СУМ-11, even though it may have a matching headword."""
    monkeypatch.setattr(module, "_sum20_definition_card", lambda lemma: None)
    monkeypatch.setattr(
        module,
        "_vts_definition_card",
        lambda lemma: {"definitions": ["вишита сорочка"]},
    )

    assert module._sum20_vts_gloss("вишиванка") == "вишита сорочка"


@pytest.mark.parametrize("module", _MODULES, ids=lambda m: m.__name__)
def test_sum20_vts_gloss_none_when_neither_available(monkeypatch, module) -> None:
    """No СУМ-11 fallback: if neither modern dictionary has an entry, the
    gloss helper returns None rather than reaching for the Soviet-era source."""
    monkeypatch.setattr(module, "_sum20_definition_card", lambda lemma: None)
    monkeypatch.setattr(module, "_vts_definition_card", lambda lemma: None)

    assert module._sum20_vts_gloss("ґаджет") is None


@pytest.mark.parametrize("module", _MODULES, ids=lambda m: m.__name__)
def test_sum20_vts_gloss_truncates_long_definitions(monkeypatch, module) -> None:
    long_text = "а" * 200
    monkeypatch.setattr(module, "_sum20_definition_card", lambda lemma: {"definitions": [long_text]})
    monkeypatch.setattr(module, "_vts_definition_card", lambda lemma: None)

    gloss = module._sum20_vts_gloss("довге-слово")

    assert gloss is not None
    assert len(gloss) == 180
    assert gloss.endswith("...")


def test_collect_ulp_headwords_signature_has_no_sum_connection() -> None:
    """The ULP inventory builder no longer needs a sqlite connection now that
    gloss fill goes through _sum20_vts_gloss instead of a sum11 query."""
    params = inspect.signature(ohoiko_repromote.collect_ulp_headwords).parameters
    assert "sum_conn" not in params


def test_mine_headwords_signature_has_no_sum_connection() -> None:
    params = inspect.signature(textbook_repromote.mine_headwords).parameters
    assert "sum_conn" not in params


def test_resolve_leg_pos_gloss_signature_has_no_sum_connection() -> None:
    params = inspect.signature(paired_split.resolve_leg_pos_gloss).parameters
    assert "sum_conn" not in params


def test_resolve_leg_pos_gloss_falls_back_to_sum20_vts_gloss(monkeypatch) -> None:
    """A split leg with no parent gloss fills from СУМ-20/ВТС via the shared
    helper, never from СУМ-11 (#7453)."""
    monkeypatch.setattr(paired_split, "_vesum_pos", lambda lemma: "noun")
    monkeypatch.setattr(paired_split.promo, "_sum20_vts_gloss", lambda lemma: "офіційний символ")

    pos, gloss = paired_split.resolve_leg_pos_gloss({"lemma": "прапор"})

    assert pos == "noun"
    assert gloss == "офіційний символ"


def test_resolve_leg_pos_gloss_prefers_parent_gloss_over_dictionary(monkeypatch) -> None:
    monkeypatch.setattr(paired_split, "_vesum_pos", lambda lemma: "noun")
    monkeypatch.setattr(
        paired_split.promo,
        "_sum20_vts_gloss",
        lambda lemma: pytest.fail("must not be called when a parent gloss exists"),
    )

    _pos, gloss = paired_split.resolve_leg_pos_gloss({"lemma": "прапор", "gloss": "flag"})

    assert gloss == "flag"


def test_resolve_leg_pos_gloss_returns_honest_empty_string_not_lemma(monkeypatch) -> None:
    """#7458: when no parent gloss and no СУМ-20/ВТС hit, the gloss must be an
    honest empty string — never the bare Cyrillic lemma reused as a fake EN
    gloss, and never СУМ-11. Callers use the empty string to hold the leg out
    of promotion (never promote a skeleton)."""
    monkeypatch.setattr(paired_split, "_vesum_pos", lambda lemma: "noun")
    monkeypatch.setattr(paired_split.promo, "_sum20_vts_gloss", lambda lemma: None)

    pos, gloss = paired_split.resolve_leg_pos_gloss({"lemma": "ґаджет"})

    assert pos == "noun"
    assert gloss == ""
