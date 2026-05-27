from __future__ import annotations

from scripts.audit.wiki_coverage_gate import (
    _extract_required_items,
    _normalize_required_claim,
    _strip_source_markers,
    _strip_step_prefix,
)


def test_strip_step_prefix():
    assert _strip_step_prefix("Крок 5: Розширення...") == "Розширення..."
    assert _strip_step_prefix("Step 1: Introduction") == "Introduction"
    assert _strip_step_prefix("Урок 10: Grammar") == "Grammar"
    assert _strip_step_prefix("Розширення...") == "Розширення..."
    assert _strip_step_prefix("") == ""

def test_strip_source_markers():
    assert _strip_source_markers("...автентичні конструкції [S3].") == "...автентичні конструкції ."
    assert _strip_source_markers("...форм [S1, S3].") == "...форм ."
    assert _strip_source_markers("No markers here.") == "No markers here."
    assert _strip_source_markers("Multiple [S1] and [S2, S3] markers.") == "Multiple  and  markers."

def test_normalize_required_claim():
    claim = "Крок 5: Розширення... [S1, S3]."
    assert _normalize_required_claim(claim) == "Розширення... ."

def test_extract_required_items_vocabulary():
    claim = "Розширення... (вода, зарядка, сніданок) ... (раненько, швиденько, завжди, ніколи)..."
    items = _extract_required_items(claim)
    assert items["vocabulary"] == ["вода", "зарядка", "сніданок", "раненько", "швиденько", "завжди", "ніколи"]

def test_extract_required_items_examples():
    claim = "Use the sentence «Я прокидаюся раненько» to illustrate."
    items = _extract_required_items(claim)
    assert items["examples"] == ["Я прокидаюся раненько"]

def test_extract_required_items_mixed():
    claim = "Introduce (вода, сніданок) and the sentence «Я п'ю воду»."
    items = _extract_required_items(claim)
    assert items["vocabulary"] == ["вода", "сніданок"]
    assert items["examples"] == ["Я п'ю воду"]
