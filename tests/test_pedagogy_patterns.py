"""Tests for pedagogy pattern library matching (#1051)."""

from pathlib import Path

import yaml

PATTERNS_PATH = Path(__file__).resolve().parents[1] / "docs" / "rules" / "pedagogy-patterns.yaml"


def _load_patterns():
    """Load the pattern library."""
    return yaml.safe_load(PATTERNS_PATH.read_text("utf-8")).get("patterns", {})


def test_patterns_file_valid():
    """Pattern library YAML is valid and non-empty."""
    patterns = _load_patterns()
    assert len(patterns) > 0


def test_every_pattern_has_required_fields():
    """Each pattern has topics list and exercises list."""
    for pid, pattern in _load_patterns().items():
        assert "topics" in pattern, f"{pid}: missing topics"
        assert isinstance(pattern["topics"], list), f"{pid}: topics must be list"
        assert len(pattern["topics"]) > 0, f"{pid}: topics must be non-empty"
        assert "exercises" in pattern, f"{pid}: missing exercises"
        assert isinstance(pattern["exercises"], list), f"{pid}: exercises must be list"
        for ex in pattern["exercises"]:
            assert "type" in ex, f"{pid}: exercise missing type"
            assert "focus" in ex, f"{pid}: exercise missing focus"


def test_phonetics_patterns_match_m01():
    """M01 (sounds/letters) should match phonetics-sounds-letters."""
    patterns = _load_patterns()
    plan = {"title": "Sounds, Letters, and Hello", "content_outline": []}
    search_terms = set(plan["title"].lower().split())

    matched = []
    for pid, p in patterns.items():
        topics = [t.lower() for t in p["topics"]]
        for topic in topics:
            if topic in search_terms or any(
                len(t) > 3 and (t in topic or topic in t) for t in search_terms
            ):
                matched.append(pid)
                break

    assert "phonetics-sounds-letters" in matched


def test_gender_patterns_match_m08():
    """M08 (Things Have Gender) should match grammar-gender."""
    patterns = _load_patterns()
    search_terms = {"things", "have", "gender"}

    matched = []
    for pid, p in patterns.items():
        topics = [t.lower() for t in p["topics"]]
        for topic in topics:
            if topic in search_terms or any(
                len(t) > 3 and (t in topic or topic in t) for t in search_terms
            ):
                matched.append(pid)
                break

    assert "grammar-gender" in matched


def test_syllable_patterns_match_skladopodil():
    """Search terms containing 'склади' should match phonetics-syllables."""
    patterns = _load_patterns()
    search_terms = {"склади", "(syllables)", "голосні", "літери"}

    matched = []
    for pid, p in patterns.items():
        topics = [t.lower() for t in p["topics"]]
        for topic in topics:
            if topic in search_terms:
                matched.append(pid)
                break
            for term in search_terms:
                if len(term) > 3 and (term in topic or topic in term):
                    matched.append(pid)
                    break

    assert "phonetics-syllables" in matched
