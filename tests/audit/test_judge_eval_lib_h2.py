"""H2 helpers — Antonenko full-text + UA-GEC calque retrieval."""
from __future__ import annotations

import pytest

from scripts.audit._judge_eval_lib import (
    UA_GEC_ROOT,
    _antonenko_fulltext_search,
    _ua_gec_calque_search,
    _ua_gec_load_index,
    build_judge_prompt_h2,
    retrieve_evidence,
)

pytestmark = pytest.mark.skipif(
    not UA_GEC_ROOT.exists(),
    reason="UA-GEC corpus not present (data/ua-gec missing in this environment)",
)


def test_ua_gec_index_loads_with_relevant_tags() -> None:
    """Index loads ≥1000 triples across the five russianism-adjacent tags."""
    index = _ua_gec_load_index()
    assert len(index) >= 1000, f"expected ≥1000 triples, got {len(index)}"
    tags = {entry[3] for entry in index}
    assert tags.issuperset({"F/Calque"}), f"missing F/Calque in tags: {tags}"


def test_ua_gec_calque_search_hits_known_calque() -> None:
    """`Прошу повістку дня` overlaps with at least one UA-GEC annotation triple.

    The exact triple cited will depend on annotator coverage. We assert ≥1
    hit (the brief's gate) rather than pinning a specific error→correct
    pair, because UA-GEC may add triples in future corpus updates.
    """
    hits = _ua_gec_calque_search("Прошу повістку дня на наступне засідання")
    assert len(hits) >= 1, "expected at least one UA-GEC hit on a calque-rich phrase"
    assert all("error" in h and "correct" in h and "tag" in h for h in hits)


def test_ua_gec_calque_search_returns_empty_on_no_cyrillic() -> None:
    """Latin-only input produces no Cyrillic tokens and so no UA-GEC hits."""
    assert _ua_gec_calque_search("just plain english text") == []


def test_antonenko_fulltext_search_returns_page_and_snippet() -> None:
    """Hits include integer page numbers parsed from the chunk title."""
    hits = _antonenko_fulltext_search("Сьогодні я залишу коментар у вкладенні")
    if not hits:
        pytest.skip("no Antonenko prose hit for this probe (env-dependent)")
    assert all("page" in h and "snippet" in h for h in hits)
    assert any(isinstance(h["page"], int) for h in hits)


def test_retrieve_evidence_returns_all_six_channels() -> None:
    """`retrieve_evidence` aggregates the six H2 channels by name."""
    ev = retrieve_evidence("Доброго дня! Як ваші справи?")
    assert set(ev.keys()) == {
        "antonenko",
        "antonenko_fulltext",
        "heritage_attested",
        "russian_shadow",
        "vesum_unknown_tokens",
        "ua_gec_calques",
    }


def test_build_judge_prompt_h2_renders_all_six_sections() -> None:
    """All six evidence sections appear in the rendered prompt."""
    ev = retrieve_evidence("На наступному тижні я залишу коментарі у вкладенні.")
    prompt = build_judge_prompt_h2("test text", ev)
    expected_headings = [
        "Antonenko-Davydovych — keyed headword entries",
        "Antonenko-Davydovych — full-book prose hits",
        "Heritage attestation",
        "Russian-shadow morphology hits",
        "VESUM-unknown Cyrillic tokens",
        "UA-GEC corpus",
    ]
    for heading in expected_headings:
        assert heading in prompt, f"missing section: {heading!r}"


def test_build_judge_prompt_h2_preserves_canonical_greeting_protection() -> None:
    """The default-clean opener and greeting protection must be present —
    the H1 FP-fix mechanism that survives even when UA-GEC F/Style fuzzes
    a greeting hit."""
    ev = retrieve_evidence("Доброго дня!")
    prompt = build_judge_prompt_h2("Доброго дня!", ev)
    assert "Default verdict: CLEAN" in prompt
    assert "Доброго дня!" in prompt
    assert "stylistic preference of the annotator" in prompt
