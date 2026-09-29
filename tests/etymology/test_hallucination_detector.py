import json
from pathlib import Path

import pytest

from scripts.etymology.hallucination_detector import is_gemini_hallucination

FIXTURES_DIR = Path("tests/fixtures/etymology/gemini-hallucinations")
# vol5_p0469.md is the known semantic hallucination (fake cognates). Semantic
# hallucinations need RAG verification, so the static detector cannot flag it.
SEMANTIC_FIXTURES = {"vol5_p0469.md"}

def get_positive_fixtures():
    # Only return .md files
    if not FIXTURES_DIR.exists():
        return []
    return [
        p for p in sorted(FIXTURES_DIR.glob("*.md")) if p.name != "README.md" and p.name not in SEMANTIC_FIXTURES
    ]

@pytest.mark.parametrize("filepath", get_positive_fixtures(), ids=lambda p: p.name)
def test_hallucination_detector_positive(filepath):
    text = filepath.read_text(encoding="utf-8")

    flagged, reason = is_gemini_hallucination(text)

    assert flagged is True, f"Failed to flag {filepath.name}. Expected hallucination but was missed."
    assert "shadow uniqueness check failed" in reason or "substring repetition check failed" in reason, f"Unexpected reason: {reason}"

def test_hallucination_detector_negative():
    # Negative cases: pull 10 random clean entries from data/processed/esum_vol1.jsonl
    esum_path = Path("data/processed/esum_vol1.jsonl")
    if not esum_path.exists():
        esum_path = Path("../../data/processed/esum_vol1.jsonl") # Fallback if running from tests dir directly
        if not esum_path.exists():
            pytest.skip("data/processed/esum_vol1.jsonl not found")

    clean_entries = []
    with open(esum_path, encoding="utf-8") as f:
        for _ in range(10):
            line = f.readline()
            if not line:
                break
            entry = json.loads(line)
            clean_entries.append(entry.get("etymology_text", ""))

    assert len(clean_entries) == 10, "Failed to load 10 clean entries"

    for i, text in enumerate(clean_entries):
        flagged, reason = is_gemini_hallucination(text)
        assert flagged is False, f"Clean entry {i} was falsely flagged. Reason: {reason}"
