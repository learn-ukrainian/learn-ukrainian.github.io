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
    assert len(LINES) == len({line["id"] for line in LINES}) == 144
    operations = set()
    for component, entry in CATALOG["components"].items():
        assert entry["line_count"] == len(entry["instructions"])
        counts = Counter((line["operation"], line.get("sense_variant")) for line in entry["instructions"])
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


@pytest.mark.parametrize("line,slot", SLOT_CASES, ids=[f"{line['id']}:{slot}" for line, slot in SLOT_CASES])
def test_schema_rejects_a_template_missing_any_declared_slot(line: dict, slot: str) -> None:
    bad = copy.deepcopy(CATALOG)
    component = line["id"].split(".")[0]
    target = next(item for item in bad["components"][component]["instructions"] if item["id"] == line["id"])
    target["template"] = target["template"].replace("{" + slot + "}", "")
    assert list(VALIDATOR.iter_errors(bad))


@pytest.mark.parametrize("pending_status", ["draft", "rb1_amendment_pending_reviews"])
def test_approved_metadata_is_versionable_but_pending_cannot_be_eligible(pending_status: str) -> None:
    approved = copy.deepcopy(CATALOG)
    approved.update(version="1.0.0", status="approved", training_eligible=True)
    approved["plan"].update(version="3.5.1", body_sha256="a" * 64)
    approved["prefix_metric"]["status"] = "frozen"
    VALIDATOR.validate(approved)  # Shape only, never approval or an eligibility receipt.
    approved["status"] = pending_status
    assert list(VALIDATOR.iter_errors(approved))


@pytest.mark.parametrize(
    "mutation", ["component", "removed_component", "placeholder", "operation", "source_field", "answer"]
)
def test_schema_refuses_out_of_contract_fields(mutation: str) -> None:
    bad = copy.deepcopy(CATALOG)
    if mutation == "component":
        del bad["components"]["C9"]
    elif mutation == "removed_component":
        bad["components"]["C8"] = copy.deepcopy(CATALOG["components"]["C9"])
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
        for slot in {"sentence", "example"} & set(line["slots"]):
            assert line["template"].endswith(": {" + slot + "}")
    assert all("homonym" not in line["slots"] for line in CATALOG["components"]["C2"]["instructions"])
    assert all(
        set(line["slots"]) == {"book_title", "grade", "section_title"}
        for line in CATALOG["components"]["C9"]["instructions"]
    )


@pytest.mark.parametrize("sense", ["SOURCE.", "SOURCE,", "SOURCE;", "SOURCE:", "(SOURCE)", "(SOURCE)."])
def test_sense_punctuation_and_parentheses_are_verbatim_final_unquoted_fields(sense: str) -> None:
    for line in LINES:
        if "sense" not in line["slots"]:
            continue
        values = dict.fromkeys(line["slots"], "SOURCE")
        values["sense"] = sense
        rendered = line["template"].format_map(values)
        assert rendered.endswith(": " + sense)
        assert "«" + sense + "»" not in rendered
        assert ".." not in rendered
        bad = copy.deepcopy(CATALOG)
        component = line["id"].split(".")[0]
        target = next(item for item in bad["components"][component]["instructions"] if item["id"] == line["id"])
        target["template"] = target["template"].replace(": {sense}", ": «{sense}».")
        assert list(VALIDATOR.iter_errors(bad))


@pytest.mark.parametrize(
    "mutation",
    [
        "serialization",
        "sense_visibility",
        "ambiguous_sense",
        "target_subset",
        "authored_join",
        "missing_sense",
        "empty_headers",
        "codes",
    ],
)
def test_c2_refuses_missing_serialization_or_model_visible_source_context(mutation: str) -> None:
    bad = copy.deepcopy(CATALOG)
    c2 = bad["components"]["C2"]
    if mutation == "serialization":
        del c2["serialization"]
    elif mutation == "sense_visibility":
        c2["serialization"]["sense_visibility"] = "metadata_only"
    elif mutation == "ambiguous_sense":
        c2["serialization"]["ambiguous_sense"] = "allow_conflicting_targets"
    elif mutation == "target_subset":
        c2["serialization"]["target"] = "first_variant_only"
    elif mutation == "authored_join":
        c2["serialization"]["header_slot"] = "free_form_join"
    elif mutation == "missing_sense":
        del c2["source_fields"]["sense"]
    else:
        record = copy.deepcopy(C2_RECORD)
        record["slot"] = [[], "", []] if mutation == "empty_headers" else ["v_rod", "p"]
        assert list(C2_RECORD_VALIDATOR.iter_errors(record))
        return
    assert list(VALIDATOR.iter_errors(bad))


@pytest.mark.parametrize("sense", ["", " ", "\n"])
def test_c2_ambiguous_homonyms_require_a_printable_source_sense(sense: str) -> None:
    record = copy.deepcopy(C2_RECORD)
    record["sense"] = sense
    assert list(C2_RECORD_VALIDATOR.iter_errors(record))
    record.update(homonym_forms_differ=False, sense="")
    C2_RECORD_VALIDATOR.validate(record)


def test_c2_header_serialization_and_all_variants_round_trip_without_joining() -> None:
    for headers in (
        C2_RECORD["slot"],
        [["SOURCE_TENSE", "SOURCE_VERBFORM"], "", []],
        [["SOURCE_TENSE"], "SOURCE_PERSON", ["SOURCE_NUMBER"]],
    ):
        record = copy.deepcopy(C2_RECORD)
        record["slot"] = headers
        C2_RECORD_VALIDATOR.validate(record)
        slot = json.dumps(headers, ensure_ascii=False, separators=(",", ":"))
        target = json.dumps(record["agreed_forms"], ensure_ascii=False, separators=(",", ":"))
        assert json.loads(slot) == headers
        assert not any(key in slot for key in ("section_headers", "row_header", "column_headers"))
        assert json.loads(target) == record["agreed_forms"]
        for line in select_c2_lines(record):
            rendered = line["template"].format(lemma=record["lemma"], slot=slot, sense=record["sense"])
            assert slot in rendered
            assert rendered.endswith(": " + record["sense"])
    record["agreed_forms"] = []
    assert list(C2_RECORD_VALIDATOR.iter_errors(record))
    question = next(line for line in LINES if line["id"] == "C2.agreed_form.08")
    assert "{slot}?\n" in question["template"]


def test_tokens_normalize_metric_only_and_mask_all_source_roles() -> None:
    assert tokens("СЛОВО {lemma} {sense}") == ("слово", "slot", "slot")
    assert tokens("п'ять") == tokens("п’ять")
    assert tokens("і\u0308") == tokens("ї")


def test_rb1_status_records_prior_instruction_reviews_and_pending_amendment() -> None:
    assert CATALOG["version"] == "0.5.0-rb1"
    assert CATALOG["status"] == "rb1_amendment_pending_reviews"
    assert CATALOG["training_eligible"] is False
    reviews = CATALOG["review_status"]
    assert reviews["pa6"]["status"] == "instruction_reviews_approved"
    assert reviews["pa6"]["reviewed_head"] == "17dbf1e7"
    assert reviews["pa6"]["issue"] == 9611
    assert "E5" in reviews["pa6"]["remaining_gate"]
    assert reviews["amendment"]["issue"] == 9818
    assert reviews["amendment"]["status"] == "pending"
    assert set(reviews["amendment"]["ukrainian_reviews"].values()) == {"pending"}
    assert set(reviews["amendment"]["code_review"].values()) == {"pending"}
    bad = copy.deepcopy(CATALOG)
    del bad["review_status"]
    assert list(VALIDATOR.iter_errors(bad))


@pytest.mark.parametrize("component,contract", [("C3", "sense_definition_contract"), ("C7", "serialization")])
def test_rb1_refuses_missing_or_changed_context_target_and_applicability_contracts(
    component: str, contract: str
) -> None:
    bad = copy.deepcopy(CATALOG)
    del bad["components"][component][contract]
    assert list(VALIDATOR.iter_errors(bad))
    for key in CATALOG["components"][component][contract]:
        bad = copy.deepcopy(CATALOG)
        bad["components"][component][contract][key] = "UNBOUND_OR_ANSWER_LEAKING"
        assert list(VALIDATOR.iter_errors(bad)), key


@pytest.mark.parametrize("pos", ["SOURCE_POS.", "(SOURCE_POS)", "SOURCE_{headword}:"])
def test_c3_definition_lines_preserve_stress_printed_pos_and_hide_definition(pos: str) -> None:
    headword = "SOURCE_HEA\u0301DWORD"
    definition = "SOURCE_DEFINITION."
    context = [["SOURCE_REGISTER"], ["SOURCE_CITATION_1.", "SOURCE_CITATION_2."]]
    serialized = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    assert json.loads(serialized) == context
    lines = [line for line in CATALOG["components"]["C3"]["instructions"] if line["operation"] == "sense_definition"]
    assert len(lines) == 12
    for line in lines:
        assert line["slots"] == ["headword", "pos"]
        rendered = line["template"].format(headword=headword, pos=pos)
        assert "«" + headword + "»" in rendered
        assert rendered.endswith(": " + pos)
        assert definition not in rendered
        assert "sense" not in line["slots"]
    bad = copy.deepcopy(CATALOG)
    del bad["components"]["C3"]["source_fields"]["pos"]
    assert list(VALIDATOR.iter_errors(bad))


def test_c7_pair_context_is_lossless_hash_ordered_and_has_no_answer_labels() -> None:
    forms = ["SOURCE_FORM_A", "SOURCE_FORM_B"]
    positions = set()
    for index in range(32):
        record_id = hashlib.sha256(str(index).encode()).hexdigest()

        def order(form: str, record_hash: str = record_id) -> bytes:
            return hashlib.sha256((record_hash + "\0" + form).encode("utf-8")).digest()

        pair = sorted(forms, key=order)
        assert sorted(reversed(forms), key=order) == pair
        context = json.dumps(pair, ensure_ascii=False, separators=(",", ":"))
        assert json.loads(context) == pair
        assert set(json.loads(context)) == set(forms)
        positions.add(pair.index(forms[0]))
        for line in CATALOG["components"]["C7"]["instructions"]:
            assert line["slots"] == []
            assert not re.search(r"\{[a-z_]+\}", line["template"])
            assert forms[0] in context and forms[1] in context
            assert not any(label in context for label in ("recommended", "rejected", "normative"))
    assert positions == {0, 1}


def test_c9_exclusion_names_wp5_as_authenticated_heading_supplier() -> None:
    exclusion = CATALOG["components"]["C9"]["exclusions"][1]
    assert "Until WP5 (#8341) supplies authenticated printed headings, withhold C9 records." in exclusion


def test_balanced_catalog_and_two_line_drop_retain_prefix_slack() -> None:
    groups = defaultdict(list)
    for line in LINES:
        groups[line["id"].split(".")[0], line["operation"], line.get("sense_variant")].append(tokens(line["template"]))
    assert len(groups) == 12
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


def test_single_template_and_distinct_ids_with_one_start_fail() -> None:
    repeated = [tokens(LINES[0]["template"])] * 100
    assert shares(repeated) == (Fraction(1), Fraction(1))
    assert repetition(repeated) == (Fraction(1), Fraction(1))
    distinct = [("подай", str(index)) for index in range(12)]
    assert shares(distinct) == (Fraction(1, 12), Fraction(5, 12))
    assert shares([seq[:1] for seq in distinct]) == (Fraction(1), Fraction(1))


def test_shared_suffix_and_middle_are_visible_despite_balanced_prefixes() -> None:
    common = tokens("Shared sentence remains identical across otherwise distinct instruction lines.")
    sequences = [(str(index), "a", "b", "c", *common) for index in range(12)]
    assert shares([seq[:4] for seq in sequences]) == (Fraction(1, 12), Fraction(5, 12))
    assert repetition(sequences) == (Fraction(1), Fraction(1))
    middle = [(*seq, str(index)) for index, seq in enumerate(sequences)]
    assert repetition(middle)[0] == Fraction(1, 12)
    assert repetition(middle)[1] == 1  # Moving the shared sentence cannot hide it.


def test_ngram_prevalence_counts_a_record_once_and_keeps_short_templates() -> None:
    assert repetition([("a",) * 20, ("b",) * 20]) == (Fraction(1, 2), Fraction(1, 2))
    assert repetition([("a",), ("a",)]) == (Fraction(1), Fraction(1))


def select_c2_lines(record: dict) -> list[dict]:
    """Admission/selection fixture only; E4/E5 must authenticate group flags."""
    C2_RECORD_VALIDATOR.validate(record)
    variant = "with_sense" if record["sense"].strip() else "without_sense"
    return [line for line in CATALOG["components"]["C2"]["instructions"] if line["sense_variant"] == variant]


@pytest.mark.parametrize("sense", ["", " ", "\n", "SOURCE.", "(SOURCE)."])
def test_c2_selects_only_applicable_lines_without_a_dangling_sense(sense: str) -> None:
    record = copy.deepcopy(C2_RECORD)
    record.update(sense=sense, homonym_forms_differ=False)
    lines = select_c2_lines(record)
    assert len(lines) == 12
    for line in lines:
        rendered = line["template"].format(lemma=record["lemma"], slot=json.dumps(record["slot"]), sense=sense)
        assert ("Значення: " in rendered) == bool(sense.strip())
        assert ("sense" in line["slots"]) == bool(sense.strip())
        if sense.strip():
            assert rendered.endswith("Значення: " + sense)
        else:
            assert line["id"].startswith("C2.agreed_form_without_sense.")


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


@pytest.mark.parametrize("field", ["lemma", "slot", "sense", "headword_group_has_parse_error"])
def test_c2_missing_fields_withhold_instead_of_selecting_without_sense(field: str) -> None:
    record = copy.deepcopy(C2_RECORD)
    del record[field]
    assert list(C2_RECORD_VALIDATOR.iter_errors(record))


@pytest.mark.parametrize(
    "headers",
    [
        [[], " ", []],
        [["SOURCE_TENSE"], " ", []],
        [[" "], "", []],
        [[], "", ["\n"]],
        [["A", "B", "C"], "", []],
        [[], "ROW", [], "EXTRA"],
        {"section_headers": [], "row_header": "ROW", "column_headers": []},
    ],
)
def test_c2_positional_headers_reject_blank_cells_wrong_arity_and_old_keys(headers: object) -> None:
    record = copy.deepcopy(C2_RECORD)
    record["slot"] = headers
    assert list(C2_RECORD_VALIDATOR.iter_errors(record))


def test_c2_positional_headers_preserve_source_unicode_quotes_order_and_duplicates() -> None:
    headers = [["МАЙБУТНІЙ ЧАС", '"SOURCE"'], "1 особа", ["однина", "однина"]]
    record = copy.deepcopy(C2_RECORD)
    record["slot"] = headers
    C2_RECORD_VALIDATOR.validate(record)
    serialized = json.dumps(headers, ensure_ascii=False, separators=(",", ":"))
    assert json.loads(serialized) == headers
    assert "МАЙБУТНІЙ ЧАС" in serialized


@pytest.mark.parametrize(
    "mutation", ["sense_variant", "sense_slot", "dangling_label", "missing_variant", "variant_count"]
)
def test_c2_schema_binds_fixed_line_sets_to_their_sense_variants(mutation: str) -> None:
    bad = copy.deepcopy(CATALOG)
    c2 = bad["components"]["C2"]
    line = c2["instructions"][-1]
    if mutation == "sense_variant":
        line["sense_variant"] = "with_sense"
    elif mutation == "sense_slot":
        line["template"] += "\nЗначення: {sense}"
        line["slots"].append("sense")
    elif mutation == "dangling_label":
        line["template"] += "\nЗначення: "
    elif mutation == "missing_variant":
        del line["sense_variant"]
    else:
        c2["instructions"] = c2["instructions"][:12]
        c2["line_count"] = 12
    assert list(VALIDATOR.iter_errors(bad))


def test_c2_combined_operation_keeps_prefix_bounds_as_well_as_each_variant() -> None:
    seqs = [tokens(line["template"]) for line in CATALOG["components"]["C2"]["instructions"]]
    for length in CATALOG["prefix_metric"]["prefix_lengths"]:
        assert shares([seq[:length] for seq in seqs]) == (Fraction(1, 12), Fraction(5, 12))
    assert max(repetition(seqs)) <= Fraction("0.60")


def test_c3_final_lines_have_one_sense_label_and_no_forward_reference() -> None:
    for line in CATALOG["components"]["C3"]["instructions"]:
        if line["operation"] in {"synonyms", "antonyms"} and line["id"].endswith((".11", ".12")):
            assert line["template"].count("Значення") == 1
            assert "У цьому значенні" not in line["template"]
            assert line["template"].endswith("Значення: {sense}")
