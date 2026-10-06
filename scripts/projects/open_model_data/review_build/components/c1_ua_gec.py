"""C1 sentence × annotator candidates from the held gec-only layer."""

from copy import deepcopy

from ..contract import Candidate
from ..errors import require
from ..gate import REASONING
from .ua_gec_split import COMPATIBILITY, CORPUS, UaGecFileStore, cited_value, exclusion, parser_hashes

FROZEN_COUNT = 32_306
SENTENCE = {"area": "slots", "slot": "sentence"}
TARGET = {"area": "response", "slot": "correction"}
REASONS = {
    "accepted": ["aligned_pair"],
    "rejected": [],
    "withheld": [
        "unparsed_annotation_markup",
        "unaligned",
        "boundary_ambiguous",
        "empty",
        "reasoning_marker_in_source",
        "attribution_unresolved",
        "locator_unavailable",
        "catalog_inapplicable",
    ],
    "excluded": ["test_source", "dev_source", "sensitive_source", "ruler_overlap"],
}


def spec() -> dict:
    return {
        "compatibility": deepcopy(COMPATIBILITY),
        "corpus": deepcopy(CORPUS),
        "unit_query": {
            "kind": "official_reader",
            "store": "ua-gec",
            "split": "train",
            "layer": "gec-only",
            "selection": "all_sentences",
        },
        "unit_id": {
            "primary": [{"selector": SENTENCE, "store": "ua-gec", "table": "data/gec-only"}],
            "separator": ";",
        },
        "frozen_count": FROZEN_COUNT,
        "reasons": REASONS,
        "operations": ["sentence_correction"],
        "unit_grain": "sentence x annotator; official reader zero-based sentence index",
        "annotation_layer": "gec-only",
        "reference_multiplicity": "Each annotator supplies a separate unit; unchanged sentences are retained.",
        "parser_hashes": parser_hashes(),
        "binding": {
            "schema": "binding-spec.v1",
            "rules": [
                {"op": "same_row", "values": [SENTENCE, TARGET]},
                {"op": "equal", "values": [SENTENCE, {**SENTENCE, "field": "source_sentence"}]},
                {"op": "equal", "values": [TARGET, {**TARGET, "field": "target_sentence"}]},
                {"op": "literal", "values": [{**SENTENCE, "field": "layer"}], "expected": "gec-only"},
                {"op": "literal", "values": [{**SENTENCE, "field": "aligned"}], "expected": True},
                {"op": "literal", "values": [{**SENTENCE, "field": "unparsed_annotation_markup"}], "expected": False},
            ],
        },
    }


def candidate(row: dict, splits) -> Candidate:
    require(row["layer"] == "gec-only", "component_layer")
    reason = exclusion(row, splits)
    outcome = "excluded" if reason else "accepted"
    if not reason and row["unparsed_annotation_markup"]:
        outcome, reason = "withheld", "unparsed_annotation_markup"
    if not reason and not row["aligned"]:
        outcome, reason = "withheld", row.get("alignment_reason") or "unaligned"
    if not reason and (not row["source_sentence"].strip() or not row["target_sentence"].strip()):
        outcome, reason = "withheld", "empty"
    if not reason and any(REASONING.search(row[field]) for field in ("source_sentence", "target_sentence")):
        outcome, reason = "withheld", "reasoning_marker_in_source"
    flags = ()
    if row["submission_type"] == "translation":
        require(bool(row["source_language"]), "translation_language_unavailable")
        flags = ("translation:" + row["source_language"],)
    return Candidate(
        "C1",
        row["row_key"],
        outcome,
        reason or "aligned_pair",
        (reason,) if reason else (),
        "sentence_correction",
        (cited_value(row, "sentence", "source"),),
        (),
        (cited_value(row, "correction", "target"),) if row["aligned"] else (),
        flags,
    )


def extract(store: UaGecFileStore) -> list[Candidate]:
    return [
        candidate(r, store.splits)
        for r in store.all_rows("corpus")
        if r["layer"] == "gec-only" and r["split"] == "train"
    ]
