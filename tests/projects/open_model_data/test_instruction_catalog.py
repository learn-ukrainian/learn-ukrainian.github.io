"""E10 draft contract and arithmetic fixtures; no production E5 proof is claimed."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "registry/projects/open_model_data"
CATALOG = yaml.safe_load((ASSETS / "instruction_catalog.yaml").read_text())
SCHEMA = json.loads((ASSETS / "instruction_catalog.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)
LINES = [line for entry in CATALOG["components"].values() for line in entry["instructions"]]
DECLARED_VARIANTS = [
    (component, branch["properties"]["operation"]["const"], variant)
    for component in CATALOG["components"]
    for items in [SCHEMA["$defs"][component]["properties"]["instructions"]["items"]]
    for branch in items.get("oneOf", [items])
    for definition in [branch["properties"].get("sense_variant", {"const": None})]
    for variant in definition.get("enum", [definition.get("const")])
]
C2_RECORD_VALIDATOR = Draft202012Validator({"$ref": "#/$defs/c2SourceRecord", "$defs": SCHEMA["$defs"]})
C2_RECORD = {
    "lemma": "SOURCE_LEMMA",
    "slot": [[], "SOURCE_CASE", ["SOURCE_NUMBER"]],
    "sense": "(SOURCE_SENSE)",
    "homonym_forms_differ": True,
    "headword_group_has_parse_error": False,
    "agreed_forms": ["SOURCE_FORM_1", "SOURCE_FORM_2"],
}


def tokens(template: str) -> tuple[str, ...]:
    """Project literals only; source values and slot names cannot add diversity."""
    masked = re.sub(r"\{[a-z_]+\}", "SLOT", template)
    normalized = unicodedata.normalize("NFC", masked).casefold().replace("'", "’")
    return tuple(re.findall(r"[^\W\d_]+(?:’[^\W\d_]+)*", normalized))


def shares(keys: list[tuple[str, ...]]) -> tuple[Fraction, Fraction]:
    counts = sorted(Counter(keys).values(), reverse=True)
    return Fraction(counts[0], len(keys)), Fraction(sum(counts[:5]), len(keys))


def repetition(sequences: list[tuple[str, ...]], length: int = 8) -> tuple[Fraction, Fraction]:
    suffix_top1 = shares([seq[-length:] for seq in sequences])[0]
    grams = Counter(
        gram for seq in sequences for gram in {seq[i : i + length] for i in range(max(1, len(seq) - length + 1))}
    )
    return suffix_top1, Fraction(max(grams.values()), len(sequences))


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


@pytest.mark.parametrize("line", LINES, ids=lambda line: line["id"])
def test_every_template_contains_exactly_its_declared_slots(line: dict) -> None:
    assert re.findall(r"\{([a-z_]+)\}", line["template"]) == line["slots"]
    component = line["id"].split(".")[0]
    assert set(line["slots"]) <= set(CATALOG["components"][component]["source_fields"])


@pytest.mark.parametrize("reviewer", range(len(CATALOG["review_status"]["amendment"]["reviewers"]) + 1))
@pytest.mark.parametrize("state", ["pending", "rejected", "missing"])
def test_rb1_approved_requires_every_listed_review_approved(reviewer: int, state: str) -> None:
    bad = copy.deepcopy(CATALOG)
    bad["status"] = "rb1_approved"
    bad["review_status"]["amendment"]["status"] = "approved"
    entries = bad["review_status"]["amendment"]["reviewers"]
    entries.append({"seat": "OTHER_REVIEWER", "task": "OTHER_TASK", "role": "ukrainian", "status": "approved"})
    for entry in entries:
        entry["status"] = "approved"
    VALIDATOR.validate(bad)
    if state == "missing":
        del entries[reviewer]["status"]
    else:
        entries[reviewer]["status"] = state
    assert list(VALIDATOR.iter_errors(bad))
    bad["status"] = "rb1_amendment_pending_reviews"
    assert list(VALIDATOR.iter_errors(bad))  # An approved amendment also requires all reviewers approved.
    bad["review_status"]["amendment"]["status"] = "pending"
    assert bool(list(VALIDATOR.iter_errors(bad))) == (state != "pending")


def test_balanced_catalog_and_two_line_drop_retain_prefix_slack() -> None:
    groups = defaultdict(list)
    for line in LINES:
        variant = line.get("sense_variant")
        groups[line["id"].split(".")[0], line["operation"], variant].append(tokens(line["template"]))
    assert set(groups) == set(DECLARED_VARIANTS)
    assert len(groups) == 13
    assert CATALOG["prefix_metric"]["prefix_lengths"] == [1, 4]
    assert Fraction(str(CATALOG["prefix_metric"]["top1_max"])) == Fraction("0.15")
    assert Fraction(str(CATALOG["prefix_metric"]["top5_max"])) == Fraction("0.60")
    for sequences in groups.values():
        assert len(sequences) == 12
        for seqs in (sequences, sequences[:-2]):
            for length in CATALOG["prefix_metric"]["prefix_lengths"]:
                top1, top5 = shares([seq[:length] for seq in seqs])
                assert (top1, top5) == (Fraction(1, len(seqs)), Fraction(5, len(seqs)))
                assert top1 <= Fraction("0.15")
                assert top5 <= Fraction("0.60")
            assert shares(seqs)[0] <= Fraction("0.15")
            assert shares(seqs)[1] <= Fraction("0.60")
            assert max(repetition(seqs)) <= Fraction("0.60")


def select_c2_lines(record: dict) -> list[dict]:
    """Admission/selection fixture only; E4/E5 must authenticate group flags."""
    C2_RECORD_VALIDATOR.validate(record)
    variant = "with_sense" if record["sense"].strip() else "without_sense"
    return [line for line in CATALOG["components"]["C2"]["instructions"] if line["sense_variant"] == variant]


@pytest.mark.parametrize("forms_differ", [False, True])
@pytest.mark.parametrize("parse_error", [False, True])
@pytest.mark.parametrize("sense", ["", " ", "\n", "SOURCE_SENSE"])
def test_c2_group_parse_error_withholds_empty_sense_even_with_equal_known_forms(
    forms_differ: bool, parse_error: bool, sense: str
) -> None:
    record = copy.deepcopy(C2_RECORD)
    record.update(homonym_forms_differ=forms_differ, headword_group_has_parse_error=parse_error, sense=sense)
    if not sense.strip() and (forms_differ or parse_error):
        assert list(C2_RECORD_VALIDATOR.iter_errors(record))
    else:
        assert len(select_c2_lines(record)) == 12
