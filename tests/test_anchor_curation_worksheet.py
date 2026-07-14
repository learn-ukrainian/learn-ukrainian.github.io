from __future__ import annotations

from pathlib import Path

import yaml

WORKSHEET = Path("data/lexicon/anchor_curation_worksheet.yaml")
REQUIRED_FIELDS = {
    "lemma",
    "cefr",
    "url_slug",
    "proposed_anchor",
    "balla_reverse_hints",
    "sum11_sense",
    "vesum_verified",
    "confidence",
}


def test_anchor_curation_worksheet_has_exactly_158_unique_evidenced_records() -> None:
    payload = yaml.safe_load(WORKSHEET.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    records = payload["records"]
    assert len(records) == 158
    lemmas = [record["lemma"] for record in records]
    assert len(lemmas) == len(set(lemmas))

    for record in records:
        assert record.keys() >= REQUIRED_FIELDS
        assert record["cefr"]
        assert record["url_slug"]
        assert record["vesum_verified"] is True
        assert isinstance(record["balla_reverse_hints"], list)
        assert isinstance(record["sum11_sense"], str) and record["sum11_sense"]
        assert record["confidence"] in {"high", "medium", "low"}
        if record["proposed_anchor"] is None:
            assert record["confidence"] == "low"
            assert record.get("notes")
        else:
            assert 1 <= len(record["proposed_anchor"].split()) <= 4
        if "sovietization_flag" in record:
            assert record["sovietization_flag"] is True
