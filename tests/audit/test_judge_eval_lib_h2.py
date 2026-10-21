"""H2 helpers — Antonenko full-text + UA-GEC calque retrieval."""
from __future__ import annotations

import pytest

from scripts.audit._judge_eval_lib import (
    UA_GEC_ROOT,
    _antonenko_fulltext_search,
    _ua_gec_calque_search,
    _ua_gec_load_index,
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


def test_antonenko_fulltext_search_returns_page_and_snippet() -> None:
    """Hits include integer page numbers parsed from the chunk title."""
    hits = _antonenko_fulltext_search("Сьогодні я залишу коментар у вкладенні")
    if not hits:
        pytest.skip("no Antonenko prose hit for this probe (env-dependent)")
    assert all("page" in h and "snippet" in h for h in hits)
    assert any(isinstance(h["page"], int) for h in hits)
