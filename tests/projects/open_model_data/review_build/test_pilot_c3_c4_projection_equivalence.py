"""Compare pilot card payloads and ingestion projections with direct WP3 extraction.

Real cards are rebuilt host-only and pinned to the committed Batch 1 receipt.
Synthetic mutation tests run in CI without the private source stores. A successful
ingestion round trip does not prove that an unrepresented operation is on cards.
Set LU_9821_EQUIVALENCE_RECEIPT to write the content-free host verification receipt.
"""

import copy
import hashlib
import os
import re
import tempfile
from collections import Counter
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path

import pytest

from scripts.atlas import word_card_assembly as assembly
from scripts.atlas import word_card_batch1 as batch
from scripts.atlas import word_card_foundation as foundation
from scripts.common.scratch import ensure_scratch_root
from scripts.projects.open_model_data.review_build.components import (
    ComponentContext,
    c3_relations,
    c3_sum20_meaning,
    c4_phraseology,
)
from scripts.projects.open_model_data.review_build.components.wp3_sources import STORE
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.components import test_c3_c4 as synthetic

synthetic_sources = synthetic.sources

MODULES = (c3_relations, c3_sum20_meaning, c4_phraseology)
OPERATIONS = ("synonyms", "antonyms", "sense_definition", "idiom_definition")


def keyed(candidates):
    """Duplicate units must fail before a dict can silently overwrite them."""
    result = {}
    for candidate in candidates:
        key = (candidate.operation, candidate.unit_id)
        assert key not in result, f"Duplicate direct unit: {key}"
        result[key] = candidate
    return result


def assert_relation_payload(assertion, candidate, group):
    members, = candidate.response
    discriminator = next(v for v in candidate.slots if v.slot == "sense")
    assert candidate.outcome == "accepted"
    assert assertion["field"] == candidate.operation
    assert assertion["subject"]["kind"] == "sense"
    assert assertion["value"] == {
        "members": members.text,
        "group": group,
        "span": list(members.span) if members.span else None,
        "discriminator": discriminator.text,
    }
    assert assertion["snapshot_id"] == "ulif-section@sha256:" + members.citations[0].field_sha256


def assert_idiom_payload(assertions, candidate):
    """Compare the whole idiom record, including ordered, attributed quotations."""
    assert candidate.outcome == "accepted"
    definition, *quotes = candidate.response
    idiom = next(v for v in candidate.slots if v.slot == "idiom")
    assert [a["value"] for a in assertions if a["field"] == "definition_uk"] == [definition.text]
    assert [a["value"] for a in assertions if a["field"] == "examples"] == [q.text for q in quotes]
    assert [a["value"] for a in assertions if a["field"] == "mwe_form"] == [
        assembly.src.nfc(assembly.unstressed_idiom(idiom.text))
    ]
    assert all(a["snapshot_id"] == "ulif-section@sha256:" + definition.citations[0].field_sha256
               for a in assertions)
    assert all(a["subject"]["kind"] == ("card" if a["field"] == "mwe_form" else "sense")
               for a in assertions)


@pytest.fixture(scope="module")
def pilot():
    primary = batch.main_checkout_root(batch.ROOT)
    stores = [primary / "data" / f"{name}.db" for name in ("sources", "vesum", "atlas")]
    if not all(p.is_file() for p in stores) or not assembly.raw_cache_path(stores[0]).is_file():
        pytest.skip("Canonical pilot source stores and raw cache are host-only")
    with ExitStack() as stack:
        scratch = Path(stack.enter_context(tempfile.TemporaryDirectory(
            prefix="9821-equivalence-", dir=ensure_scratch_root())))
        inputs = assembly.load_inputs(batch.ROOT / batch.PILOT, batch.ROOT / batch.REGISTRY,
                                      batch.ROOT / batch.REGISTER, *stores, stack, scratch)
        result, report, receipt = batch.assemble(inputs)
        assert receipt == foundation.load(batch.ROOT / batch.RECEIPT), "Rebuilt pilot differs from Batch 1"
        assert report["passed"]
        assert len(result["cards"]) == receipt["card_count"] == 150
        assert receipt["locator_count"] == 2834
        with SnapshotReader({STORE: scratch / "pilot-wp3-extract.sqlite"}) as reader:
            ctx = ComponentContext(reader, {})
            yield inputs, result, receipt, ctx


def test_pilot_ingestion_projects_exact_candidates_on_the_same_units(pilot):
    inputs, _, _, ctx = pilot
    parents = {int(u.parent_key.rpartition("=")[2]) for u in inputs.wp3_units}
    # The extract also retains homonym siblings; exclude them from BOTH streams.
    expected_parents = {r["raw_row"]["id"] for r in inputs.manifest["selection"]["source_records"]
                        if r["table"] == "ulif_dictua_entries"}
    assert parents <= expected_parents
    for module in (c3_relations, c4_phraseology):
        units = [u for u in inputs.wp3_units
                 if u.candidate.operation in (c3_relations.COUNTS if module is c3_relations else {"idiom_definition"})]
        direct = [c for c in module.iter_candidates(ctx)
                  if ctx.reader.connections[STORE].execute(
                      "SELECT entry_id FROM ulif_dictua_sections WHERE id=?", (c.unit_id,)
                  ).fetchone()[0] in expected_parents]
        assert keyed(u.project(ctx) for u in units) == keyed(direct)
        assert direct, "A missing pilot operation must not pass vacuously"


def test_pilot_card_payloads_match_direct_extraction(pilot):
    inputs, result, receipt, ctx = pilot
    direct = keyed(c for module in MODULES for c in module.iter_candidates(ctx))
    projected = Counter()
    seen = set()
    card_parents = {inputs.entry_by_unit[u["unit_key"]]["card_id"]:
                    inputs.records[u["anchor_locator"]]["raw_row"]["id"]
                    for u in inputs.units if u["entry_type"] == "lexeme_candidate"}
    for card in result["cards"].values():
        idioms = {}
        for assertion in card["assertions"]:
            if assertion["source_id"] != "ulif":
                continue
            match = re.fullmatch(r"ulif:ulif_dictua_sections:id:(\d+) \[payload_json#/raw_html\]",
                                 assertion["locator"])
            if not match:
                continue
            key = match.group(1)
            if assertion["field"] in c3_relations.COUNTS:
                identity = (assertion["field"], key)
                assert identity not in seen, f"Duplicate card projection: {identity}"
                candidate = direct[identity]
                row = ctx.reader.connections[STORE].execute(
                    "SELECT sense_or_group_id,entry_id FROM ulif_dictua_sections WHERE id=?", (key,)
                ).fetchone()
                assert row[1] == card_parents[card["card_id"]], "Relation moved to a foreign card"
                assert assertion["subject"]["id"] in {s["sense_id"] for s in card["senses"]}
                assert_relation_payload(assertion, candidate, row[0])
                seen.add(identity)
                projected[candidate.operation] += 1
            elif assertion["field"] in {"definition_uk", "examples", "mwe_form"}:
                idioms.setdefault(key, []).append(assertion)
        for key, assertions in idioms.items():
            assert_idiom_payload(assertions, direct["idiom_definition", key])
            seen.add(("idiom_definition", key))
            projected["idiom_definition"] += 1
    expected_relations = {(u.candidate.operation, u.candidate.unit_id) for u in inputs.wp3_units
                          if u.candidate.operation in c3_relations.COUNTS and u.candidate.outcome == "accepted"}
    assert {key for key in seen if key[0] in c3_relations.COUNTS} == expected_relations
    assert expected_relations, "No accepted relations reached the pilot cards"
    # This receipt distinguishes ingestion equivalence from actual card coverage.
    # SUM20 is intentionally held by the current assembler, never counted as proof.
    ingestion = Counter((u.candidate.operation, u.candidate.outcome) for u in inputs.wp3_units)
    coverage = {op: {"projected_card_records": projected[op],
                     "ingested_units": sum(n for (operation, _), n in ingestion.items() if operation == op),
                     "ingestion_outcomes": {outcome: n for (operation, outcome), n in ingestion.items()
                                            if operation == op}}
                for op in OPERATIONS}
    gaps = [op for op in OPERATIONS if not projected[op]]
    evidence = {
        "schema": "9821-ac2-equivalence.v1", "issue": 9821,
        "status": "partial" if gaps else "passed", "ac2_complete": not gaps,
        "pilot_cards": len(result["cards"]), "pilot_locators": receipt["locator_count"],
        "pilot_manifest_sha256": receipt["pilot_manifest_sha256"],
        "batch_cards_sha256": receipt["cards_sha256"], "build_id": receipt["build_id"],
        "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "extract_sha256": inputs.hashes["extract_sha256"],
        "ingestion_projection_equivalent": True,
        "direct_candidates_sha256": foundation.digest([asdict(c) for c in direct.values()]),
        "coverage": coverage, "compared_card_records": sum(projected.values()),
        "mismatches": 0, "unrepresented_operations": gaps,
        "independent_heldout_evaluation": "not_performed",
        "residuals": [{"operation": op, "reason": "no_records_on_pilot_cards",
                       "owner": "open-model-data driver"} for op in gaps],
        "residual_owner": "open-model-data driver" if gaps else "none",
    }
    if path := os.environ.get("LU_9821_EQUIVALENCE_RECEIPT"):
        foundation.write(Path(path), evidence)
    print(evidence)


@pytest.mark.parametrize("module", MODULES)
def test_synthetic_full_candidate_equivalence(synthetic_sources, module):
    with SnapshotReader({STORE: synthetic_sources}) as reader:
        ctx = ComponentContext(reader, {})
        direct = keyed(module.iter_candidates(ctx))
        projected = keyed(u.project(ctx) for u in module.iter_card_units(ctx))
        assert direct and projected == direct


@pytest.mark.parametrize("damage", ("members", "group", "span", "discriminator", "snapshot"))
def test_relation_comparison_detects_payload_corruption(synthetic_sources, damage):
    with SnapshotReader({STORE: synthetic_sources}) as reader:
        ctx = ComponentContext(reader, {})
        unit = next(c3_relations.iter_card_units(ctx))
        candidate = next(c3_relations.iter_candidates(ctx))
        members, = candidate.response
        assertion = {"field": candidate.operation, "subject": {"kind": "sense"},
                     "snapshot_id": "ulif-section@sha256:" + members.citations[0].field_sha256,
                     "value": {"members": members.text, "group": unit.group_key,
                               "span": list(members.span) if members.span else None,
                               "discriminator": next(v.text for v in candidate.slots if v.slot == "sense")}}
        assert_relation_payload(assertion, candidate, unit.group_key)
        broken = copy.deepcopy(assertion)
        if damage == "snapshot":
            broken["snapshot_id"] = "wrong"
        else:
            broken["value"][damage] = "wrong"
        with pytest.raises(AssertionError):
            assert_relation_payload(broken, candidate, unit.group_key)


@pytest.mark.parametrize("damage", ("definition", "missing_quote", "reordered_quotes", "duplicate_quote", "idiom"))
def test_idiom_comparison_detects_payload_corruption(synthetic_sources, damage):
    with SnapshotReader({STORE: synthetic_sources}) as reader:
        ctx = ComponentContext(reader, {})
        candidate = next(c4_phraseology.iter_candidates(ctx))
        definition, *quotes = candidate.response
        idiom = next(v for v in candidate.slots if v.slot == "idiom")
        assertion = {"snapshot_id": "ulif-section@sha256:" + definition.citations[0].field_sha256}
        rows = [{**assertion, "subject": {"kind": "sense"}, "field": "definition_uk", "value": definition.text},
                *({**assertion, "subject": {"kind": "sense"}, "field": "examples", "value": q.text} for q in quotes),
                {**assertion, "subject": {"kind": "card"}, "field": "mwe_form",
                 "value": assembly.src.nfc(assembly.unstressed_idiom(idiom.text))}]
        assert_idiom_payload(rows, candidate)
        broken = copy.deepcopy(rows)
        if damage == "definition":
            broken[0]["value"] = "wrong"
        elif damage == "idiom":
            broken[-1]["value"] = "wrong"
        elif damage == "missing_quote":
            broken.pop(1)
        elif damage == "duplicate_quote":
            broken.insert(1, copy.deepcopy(broken[1]))
        else:
            broken[1:3] = reversed(broken[1:3])
        with pytest.raises(AssertionError):
            assert_idiom_payload(broken, candidate)
