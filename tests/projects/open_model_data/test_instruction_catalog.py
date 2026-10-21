"""E10 draft contract and arithmetic fixtures; no production E5 proof is claimed."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "registry/projects/open_model_data"
CATALOG = yaml.safe_load((ASSETS / "instruction_catalog.yaml").read_text())
SCHEMA = json.loads((ASSETS / "instruction_catalog.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)
LINES = [line for entry in CATALOG["components"].values() for line in entry["instructions"]]


def test_catalog_schema_counts_ids_and_plan_binding() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    VALIDATOR.validate(CATALOG)
    assert set(CATALOG["components"]) == {"C1", "C2", "C3", "C4", "C5", "C6", "C7", "C9"}
    assert len(CATALOG["components"]) == 8
    assert len(LINES) == len({line["id"] for line in LINES}) == 156
    operations = set()
    for component, entry in CATALOG["components"].items():
        assert entry["line_count"] == len(entry["instructions"])
        counts = Counter((line["operation"], line.get("sense_variant")) for line in entry["instructions"])
        expected = (
            {
                ("synonyms", None): 12,
                ("antonyms", None): 12,
                ("sense_definition", "with_citations"): 12,
                ("sense_definition", "single_sense"): 12,
            }
            if component == "C3"
            else None
        )
        if expected is not None:
            assert counts == expected
        else:
            assert set(counts.values()) == {12}
        operations.update((component, operation) for operation, _ in counts)
    assert operations == {
        ("C1", "sentence_correction"),
        ("C2", "agreed_form"),
        ("C3", "synonyms"),
        ("C3", "antonyms"),
        ("C3", "sense_definition"),
        ("C4", "idiom_definition"),
        ("C5", "printed_spelling_rule"),
        ("C6", "calque_correction"),
        ("C6", "book_calque_replacement"),
        ("C7", "modern_norm_selection"),
        ("C9", "verbatim_section"),
    }
    assert len(operations) == 11
    assert CATALOG["plan"] == {
        "path": "docs/projects/open-model-data/PLAN.md",
        "version": "3.5.0",
        "body_sha256": "d8aaf46bea650d4a3331e7ebe4d90dccf2aae9c9bc9eefb270a41760d71acbeb",
    }
    plan = ROOT / CATALOG["plan"]["path"]
    assert hashlib.sha256(plan.read_bytes().split(b"-->\n", 1)[1]).hexdigest() == CATALOG["plan"]["body_sha256"]
