from __future__ import annotations

from scripts.audit.wiki_coverage_gate import _extract_required_items


def test_extract_required_items_drops_discourse_marker_from_parenthetical_vocab() -> None:
    claim = "Teach first conjugation endings (наприклад, читати) [S8]."

    items = _extract_required_items(claim)

    assert items["vocabulary"] == ["читати"]
    assert "наприклад" not in items["vocabulary"]


def test_extract_required_items_keeps_legit_one_word_parenthetical_lemma() -> None:
    claim = "Introduce the morning routine verb (прокидатися) before examples."

    items = _extract_required_items(claim)

    assert items["vocabulary"] == ["прокидатися"]
