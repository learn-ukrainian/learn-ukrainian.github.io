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
SLOT_CASES = [(line, slot) for line in LINES for slot in line["slots"]]


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
    assert len(CATALOG["components"]) == 9
    assert len(LINES) == len({line["id"] for line in LINES}) == 132
    operations = set()
    for component, entry in CATALOG["components"].items():
        assert entry["line_count"] == len(entry["instructions"])
        counts = Counter(line["operation"] for line in entry["instructions"])
        assert set(counts.values()) == {12}
        operations.update((component, operation) for operation in counts)
    assert len(operations) == 11
    plan = ROOT / CATALOG["plan"]["path"]
    assert hashlib.sha256(plan.read_bytes().split(b"-->\n", 1)[1]).hexdigest() == CATALOG["plan"]["body_sha256"]


@pytest.mark.parametrize("line", LINES, ids=lambda line: line["id"])
def test_every_template_contains_exactly_its_declared_slots(line: dict) -> None:
    assert re.findall(r"\{([a-z_]+)\}", line["template"]) == line["slots"]
    component = line["id"].split(".")[0]
    assert set(line["slots"]) <= set(CATALOG["components"][component]["source_fields"])


@pytest.mark.parametrize("line,slot", SLOT_CASES, ids=[f"{line['id']}:{slot}" for line, slot in SLOT_CASES])
def test_schema_rejects_a_template_missing_any_declared_slot(line: dict, slot: str) -> None:
    bad = copy.deepcopy(CATALOG)
    component = line["id"].split(".")[0]
    target = next(item for item in bad["components"][component]["instructions"] if item["id"] == line["id"])
    target["template"] = target["template"].replace("{" + slot + "}", "")
    assert list(VALIDATOR.iter_errors(bad))


def test_approved_metadata_is_versionable_but_draft_cannot_be_eligible() -> None:
    approved = copy.deepcopy(CATALOG)
    approved.update(version="1.0.0", status="approved", training_eligible=True)
    approved["plan"].update(version="3.4.5", body_sha256="a" * 64)
    approved["prefix_metric"]["status"] = "frozen"
    VALIDATOR.validate(approved)  # Shape only, never approval or an eligibility receipt.
    approved["status"] = "draft"
    assert list(VALIDATOR.iter_errors(approved))


@pytest.mark.parametrize("mutation", ["component", "placeholder", "operation", "source_field", "answer"])
def test_schema_refuses_out_of_contract_fields(mutation: str) -> None:
    bad = copy.deepcopy(CATALOG)
    if mutation == "component":
        del bad["components"]["C9"]
    elif mutation == "source_field":
        bad["components"]["C9"]["source_fields"]["invented"] = "unattested"
    elif mutation == "answer":
        bad["answer"] = "forbidden"
    else:
        line = bad["components"]["C9"]["instructions"][0]
        line["template" if mutation == "placeholder" else "operation"] = "{invented}"
    assert list(VALIDATOR.iter_errors(bad))


def test_sentence_and_printed_example_slots_follow_a_colon_without_outer_quotes() -> None:
    for line in LINES:
        for slot in {"sentence", "example", "context"} & set(line["slots"]):
            assert line["template"].endswith(": {" + slot + "}")
    assert all("homonym" not in line["slots"] for line in CATALOG["components"]["C2"]["instructions"])
    assert all(
        set(line["slots"]) == {"book_title", "grade", "section_title"}
        for line in CATALOG["components"]["C9"]["instructions"]
    )


def test_tokens_normalize_metric_only_and_mask_all_source_roles() -> None:
    assert tokens("СЛОВО {lemma} {sense}") == ("слово", "slot", "slot")
    assert tokens("п'ять") == tokens("п’ять")
    assert tokens("і\u0308") == tokens("ї")


def test_balanced_catalog_and_two_line_drop_retain_prefix_slack() -> None:
    groups = defaultdict(list)
    for line in LINES:
        groups[line["id"].split(".")[0], line["operation"]].append(tokens(line["template"]))
    for sequences in groups.values():
        for seqs in (sequences, sequences[:-2]):
            for length in CATALOG["prefix_metric"]["prefix_lengths"]:
                top1, top5 = shares([seq[:length] for seq in seqs])
                assert top1 <= Fraction("0.15")
                assert top5 <= Fraction("0.60")
            assert shares(seqs)[0] <= Fraction("0.15")
            assert shares(seqs)[1] <= Fraction("0.60")
            assert max(repetition(seqs)) <= Fraction("0.60")


def test_single_template_and_distinct_ids_with_one_start_fail() -> None:
    repeated = [tokens(LINES[0]["template"])] * 100
    assert shares(repeated) == (Fraction(1), Fraction(1))
    assert repetition(repeated) == (Fraction(1), Fraction(1))
    distinct = [("подай", str(index)) for index in range(12)]
    assert shares(distinct) == (Fraction(1, 12), Fraction(5, 12))
    assert shares([seq[:1] for seq in distinct]) == (Fraction(1), Fraction(1))


def test_shared_c8_suffix_and_middle_are_visible_despite_balanced_prefixes() -> None:
    common = tokens("Наведи також оцінку цієї вимови з того самого абзацу.")
    sequences = [(str(index), "a", "b", "c", *common) for index in range(12)]
    assert shares([seq[:4] for seq in sequences]) == (Fraction(1, 12), Fraction(5, 12))
    assert repetition(sequences) == (Fraction(1), Fraction(1))
    middle = [(*seq, str(index)) for index, seq in enumerate(sequences)]
    assert repetition(middle)[0] == Fraction(1, 12)
    assert repetition(middle)[1] == 1  # Moving the shared sentence cannot hide it.


def test_ngram_prevalence_counts_a_record_once_and_keeps_short_templates() -> None:
    assert repetition([("a",) * 20, ("b",) * 20]) == (Fraction(1, 2), Fraction(1, 2))
    assert repetition([("a",), ("a",)]) == (Fraction(1), Fraction(1))
