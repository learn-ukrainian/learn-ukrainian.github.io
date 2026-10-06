"""C6(a) sentence × annotator calque corrections, never paragraph blocks."""

from copy import deepcopy

from ..contract import Candidate
from ..errors import require
from ..gate import REASONING
from . import c1_ua_gec
from .ua_gec_split import UaGecFileStore, cited_value, exclusion

# Measured by the declared official-reader query. The design's 1,230 / 50
# figures describe paragraphs; 2,113 describes markers, not accounting units.
FROZEN_COUNT = 1_873
REASONS = {
    "accepted": ["calque_only"],
    "rejected": [],
    "withheld": [
        "unaligned",
        "boundary_ambiguous",
        "empty",
        "reasoning_marker_in_source",
        "attribution_unresolved",
        "locator_unavailable",
        "catalog_inapplicable",
    ],
    "excluded": ["test_source", "dev_source", "sensitive_source", "ruler_overlap", "mixed_to_c1"],
}


def spec() -> dict:
    result = deepcopy(c1_ua_gec.spec())
    result.update(
        frozen_count=FROZEN_COUNT,
        reasons=REASONS,
        operations=["calque_correction"],
        annotation_layer="gec-fluency",
        reference_multiplicity="Each annotator supplies a separate unit with nonempty all-F/Calque edits.",
    )
    result["unit_query"].update(layer="gec-fluency", selection="contains_calque")
    result["unit_id"]["primary"][0]["table"] = "data/gec-fluency"
    result["binding"]["rules"][3]["expected"] = "gec-fluency"
    result["binding"]["rules"].append(
        {
            "op": "literal",
            "values": [{**c1_ua_gec.SENTENCE, "field": "edit_aligned"}],
            "expected": True,
        }
    )
    # The framework's UA-GEC role independently authenticates the nonempty
    # all-F/Calque edit list and the layer, from this same source row.
    return result


def candidate(row: dict, splits) -> Candidate:
    require(row["layer"] == "gec-fluency" and "F/Calque" in row["edits"], "component_layer")
    reason = exclusion(row, splits)
    outcome = "excluded" if reason else "accepted"
    if not reason and not row["edit_aligned"]:
        outcome, reason = "withheld", "boundary_ambiguous"
    if not reason and any(tag != "F/Calque" for tag in row["edits"]):
        outcome, reason = "excluded", "mixed_to_c1"
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
        "C6a",
        row["row_key"],
        outcome,
        reason or "calque_only",
        (reason,) if reason else (),
        "calque_correction",
        (cited_value(row, "sentence", "source"),),
        (),
        (cited_value(row, "correction", "target"),) if row["aligned"] else (),
        flags,
    )


def extract(store: UaGecFileStore) -> list[Candidate]:
    return [
        candidate(r, store.splits)
        for r in store.all_rows("corpus")
        if r["layer"] == "gec-fluency" and r["split"] == "train" and "F/Calque" in r["edits"]
    ]
