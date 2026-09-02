"""V4 A5 expression-free evidence enrichment: content-blind structural
evidence bound to A4's already-published, hash-only extraction commitments.

Private-artifact-dependent paths (``compute_evidence_enrichment``,
``verify_evidence_privately``, memory-budget failures) are exercised against
synthetic tmp_path fixtures -- mirroring ``test_a4_deterministic_extraction.
py``'s own style -- so this suite passes in a fresh checkout with no
``batch_state/``. The checked-in production receipt is verified separately,
using only public files on disk.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout
from scripts.projects.open_model_data import v4_a4_deterministic_extraction as extraction
from scripts.projects.open_model_data import v4_a5_evidence_enrichment as enrichment

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a5_evidence_enrichment_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
REAL_A4_RECEIPT = json.loads(A4_RECEIPT_PATH.read_text(encoding="utf-8"))

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

FORBIDDEN_KEYS = {
    "content",
    "text",
    "source_body",
    "source_text",
    "source_unit_id",
    "prompt",
    "label",
    "gold",
    "heldout_membership",
    "heldout_locator",
    "heldout_fingerprint",
    "heldout_neighbour",
    "heldout_near_neighbour",
    "held_out_membership",
    "heldout_family_pool",
    "heldout_membership_locator",
    "salt",
    "salt_hex",
    "private_salt",
}

ENRICHMENT_ALGORITHM_DESCRIPTOR = {
    "algorithm_id": "v4-a5-structural-evidence-enrichment-v1",
    "algorithm_version": "v1",
    "unit_of_enrichment": "source_unit_commitment",
    "content_blind": True,
    "expression_blind": True,
    "ordering": "source_unit_commitment_sha256_ascending",
    "aggregated_fields": ["span_count", "total_span_bytes", "min_span_byte_length", "max_span_byte_length"],
    "aggregation_formula": (
        "for each row in A4's private extraction ledger (only source_unit_commitment_sha256 and "
        "span_byte_length are read -- input_sha256/output_sha256/span text are never inspected): "
        "span_count[commitment] += 1; total_span_bytes[commitment] += span_byte_length; "
        "min_span_byte_length[commitment] = min(existing, span_byte_length); "
        "max_span_byte_length[commitment] = max(existing, span_byte_length); a commitment with no rows "
        "keeps span_count 0, total_span_bytes 0, min/max null"
    ),
    "evidence_commitment_formula": (
        "sha256(canonical_json(per_unit_evidence sorted by source_unit_commitment_sha256))"
    ),
    "text_emitted": False,
    "expression_emitted": False,
    "reproducibility": (
        "byte_stable_given_the_identical_private_a4_extraction_ledger_and_the_frozen_aggregation_formula"
    ),
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _receipt() -> dict[str, Any]:
    return _load(RECEIPT)


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


# --- synthetic fixtures ------------------------------------------------------


def _synthetic_a4_receipt(commitments: list[str], *, row_count: int, root_sha256: str, packet_consumed: bool = True) -> dict:
    return {
        "controlling_outcome_sha256": V4_SHA256,
        "builder_packet_consumption": {
            "packet_consumed": packet_consumed,
            "unit_commitments": commitments if packet_consumed else [],
            "extraction_ledger_commitment": {"row_count": row_count, "root_sha256": root_sha256},
        },
    }


def _write_private_ledger(private_dir: Path, rows: list[dict[str, Any]]) -> tuple[str, int]:
    """Write a synthetic private A4-shaped ledger + manifest under
    ``private_dir``, using A4's own real filesystem-hardening writers (so the
    private-artifact loaders A5 depends on accept it). Returns
    (root_sha256, row_count)."""
    state = extraction.new_ledger_rolling_state()
    for row in rows:
        state = extraction.ledger_rolling_update(state, row["output_sha256"])
    root_sha256 = state.hex()
    row_count = len(rows)

    ledger_path = private_dir / extraction.A4_LEDGER_FILENAME
    lines = ((extraction.canonical_json(row) + "\n").encode("utf-8") for row in rows)
    extraction.write_new_private_streamed_artifact(ledger_path, lines)

    manifest_path = private_dir / extraction.A4_LEDGER_MANIFEST_FILENAME
    heldout.write_new_private_json_artifact(
        manifest_path,
        {
            "algorithm_id": extraction.LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_id"],
            "algorithm_version": extraction.LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_version"],
            "row_count": row_count,
            "root_sha256": root_sha256,
            "source_units_extracted": len({row["source_unit_commitment_sha256"] for row in rows}),
            "receipt_binding_sha256": "synthetic-binding-not-checked-by-a5",
        },
    )
    return root_sha256, row_count


def _row(commitment: str, span_index: int, span_byte_length: int) -> dict[str, Any]:
    input_sha256 = hashlib.sha256(f"span-{commitment}-{span_index}".encode()).hexdigest()
    return {
        "source_unit_commitment_sha256": commitment,
        "span_index": span_index,
        "span_byte_length": span_byte_length,
        "input_sha256": input_sha256,
        "output_sha256": extraction.extraction_record_output_hash(commitment, span_index, span_byte_length, input_sha256),
    }


# --- frozen algorithm descriptor ---------------------------------------------


def test_enrichment_algorithm_descriptor_is_frozen_and_hashed() -> None:
    assert enrichment.ENRICHMENT_ALGORITHM_DESCRIPTOR == ENRICHMENT_ALGORITHM_DESCRIPTOR
    assert (
        hashlib.sha256(_canonical_json(ENRICHMENT_ALGORITHM_DESCRIPTOR).encode("utf-8")).hexdigest()
        == enrichment.ENRICHMENT_ALGORITHM_DESCRIPTOR_SHA256
    )


# --- pure, content-blind aggregation -----------------------------------------


def test_new_unit_accumulator_starts_empty() -> None:
    assert enrichment.new_unit_accumulator() == {
        "span_count": 0,
        "total_span_bytes": 0,
        "min_span_byte_length": None,
        "max_span_byte_length": None,
    }


def test_accumulate_row_tracks_count_sum_min_max() -> None:
    accumulator = enrichment.new_unit_accumulator()
    for length in (10, 3, 7):
        enrichment.accumulate_row(accumulator, length)
    assert accumulator == {
        "span_count": 3,
        "total_span_bytes": 20,
        "min_span_byte_length": 3,
        "max_span_byte_length": 10,
    }


def test_aggregate_ledger_rows_groups_by_commitment_and_is_id_free() -> None:
    commitment_a = "a" * 64
    commitment_b = "b" * 64
    rows = [_row(commitment_a, 0, 10), _row(commitment_a, 1, 20), _row(commitment_b, 0, 5)]
    lines = [extraction.canonical_json(row) for row in rows]

    accumulators, total_rows = enrichment.aggregate_ledger_rows(lines, [commitment_a, commitment_b, "c" * 64])

    assert total_rows == 3
    assert accumulators[commitment_a] == {
        "span_count": 2,
        "total_span_bytes": 30,
        "min_span_byte_length": 10,
        "max_span_byte_length": 20,
    }
    assert accumulators[commitment_b] == {
        "span_count": 1,
        "total_span_bytes": 5,
        "min_span_byte_length": 5,
        "max_span_byte_length": 5,
    }
    assert accumulators["c" * 64] == enrichment.new_unit_accumulator()
    assert "input_sha256" not in enrichment.build_per_unit_evidence(accumulators)[0]


def test_aggregate_ledger_rows_refuses_unknown_commitment() -> None:
    row = _row("a" * 64, 0, 10)
    with pytest.raises(enrichment.EnrichmentError, match="outside A4's public unit_commitments"):
        enrichment.aggregate_ledger_rows([extraction.canonical_json(row)], ["b" * 64])


def test_aggregate_ledger_rows_fails_closed_against_a_near_zero_memory_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    """A near-zero cap must fail closed deterministically, regardless of
    whether this particular synthetic stream happens to nudge real
    ``ru_maxrss`` -- so the RSS delta itself is monkeypatched rather than
    left to chance."""
    commitment = "a" * 64
    rows = [extraction.canonical_json(_row(commitment, i, 10)) for i in range(5_000)]
    rss_values = iter([1_000, 1_001])  # baseline snapshot, then one incremental-growth check
    monkeypatch.setattr(enrichment, "_current_rss_bytes", lambda: next(rss_values))
    with pytest.raises(enrichment.MemoryBudgetExceeded, match="incremental resident memory"):
        enrichment.aggregate_ledger_rows(rows, [commitment], memory_cap_bytes=0, memory_check_interval=1)


def test_aggregate_ledger_rows_bounds_growth_not_the_hosts_inherited_high_water(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression for the merge-queue RSS bug: a host process whose inherited
    ``ru_maxrss`` already sits well past the 512 MiB production cap (e.g.
    thousands of prior pytest cases in the same shard) must not trip the
    guard on its own -- only growth incurred *by this pass* counts."""
    commitment = "a" * 64
    rows = [extraction.canonical_json(_row(commitment, i, 10)) for i in range(50)]
    inherited_high_water = 1_702_019_072  # > the 512 MiB production cap, as seen in CI
    monkeypatch.setattr(enrichment, "_current_rss_bytes", lambda: inherited_high_water)

    accumulators, total_rows = enrichment.aggregate_ledger_rows(
        rows, [commitment], memory_cap_bytes=enrichment.DEFAULT_A5_MEMORY_CAP_BYTES, memory_check_interval=1
    )

    assert total_rows == 50
    assert accumulators[commitment]["span_count"] == 50


def test_aggregate_ledger_rows_still_fails_closed_on_real_growth_above_a_high_baseline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The cap must still bite once *this pass* actually grows past it, even
    starting from a high inherited baseline -- proving the fix bounds
    incremental growth rather than disabling the guard outright."""
    commitment = "a" * 64
    rows = [extraction.canonical_json(_row(commitment, i, 10)) for i in range(10)]
    baseline = 1_702_019_072
    grown = baseline + enrichment.DEFAULT_A5_MEMORY_CAP_BYTES + 1
    rss_values = iter([baseline] + [grown] * 20)
    monkeypatch.setattr(enrichment, "_current_rss_bytes", lambda: next(rss_values))

    with pytest.raises(enrichment.MemoryBudgetExceeded, match="incremental resident memory"):
        enrichment.aggregate_ledger_rows(
            rows, [commitment], memory_cap_bytes=enrichment.DEFAULT_A5_MEMORY_CAP_BYTES, memory_check_interval=1
        )


def test_build_per_unit_evidence_is_sorted_by_commitment() -> None:
    accumulators = {"b" * 64: enrichment.new_unit_accumulator(), "a" * 64: enrichment.new_unit_accumulator()}
    evidence = enrichment.build_per_unit_evidence(accumulators)
    assert [entry["source_unit_commitment_sha256"] for entry in evidence] == ["a" * 64, "b" * 64]


def test_evidence_commitment_sha256_is_pure_and_order_sensitive() -> None:
    first = [{"source_unit_commitment_sha256": "a" * 64, "span_count": 1}]
    second = [{"source_unit_commitment_sha256": "a" * 64, "span_count": 2}]
    assert enrichment.evidence_commitment_sha256(first) == enrichment.evidence_commitment_sha256(first)
    assert enrichment.evidence_commitment_sha256(first) != enrichment.evidence_commitment_sha256(second)
    assert enrichment.evidence_commitment_sha256([]) == enrichment.EMPTY_EVIDENCE_COMMITMENT_SHA256


# --- enrichment gate (public-only) ------------------------------------------


def test_gate_open_against_the_real_production_receipts() -> None:
    gate = enrichment.check_enrichment_gate()
    assert gate["a4_receipt_present"] is True
    assert gate["a4_receipt_valid"] is True
    assert gate["a4_extraction_available"] is True
    assert gate["blocked_reason_code"] is None


def test_gate_closed_when_a4_receipt_missing(tmp_path: Path) -> None:
    gate = enrichment.check_enrichment_gate(tmp_path)
    assert gate["a4_receipt_present"] is False
    assert gate["a4_extraction_available"] is False
    assert gate["blocked_reason_code"] == "a4_receipt_missing"


def test_gate_closed_when_a4_receipt_is_invalid(tmp_path: Path) -> None:
    admission_dir = tmp_path / "data/projects/open_model_data/admission"
    admission_dir.mkdir(parents=True)
    forged = copy.deepcopy(REAL_A4_RECEIPT)
    forged["bindings"]["a2_source_operation_admission"]["sha256"] = "0" * 64
    (admission_dir / "dataset_v4_a4_deterministic_extraction_receipt_v1.json").write_text(json.dumps(forged))

    gate = enrichment.check_enrichment_gate(tmp_path)
    assert gate["a4_receipt_present"] is True
    assert gate["a4_receipt_valid"] is False
    assert gate["a4_extraction_available"] is False
    assert gate["blocked_reason_code"] == "a4_receipt_invalid"


# --- real ledger consumption --------------------------------------------------


def test_compute_evidence_enrichment_returns_empty_when_packet_not_consumed() -> None:
    a4_receipt = _synthetic_a4_receipt([], row_count=0, root_sha256=extraction.EMPTY_LEDGER_ROOT_SHA256, packet_consumed=False)
    result = enrichment.compute_evidence_enrichment(a4_receipt, Path("/nonexistent"))
    assert result == {
        "ledger_consumed": False,
        "per_unit_evidence": [],
        "evidence_commitment_sha256": enrichment.EMPTY_EVIDENCE_COMMITMENT_SHA256,
        "spans_covered": 0,
        "units_with_evidence": 0,
    }


def test_compute_evidence_enrichment_streams_real_rows_and_aggregates_id_free(tmp_path: Path) -> None:
    commitment_a = "a" * 64
    commitment_b = "b" * 64
    rows = [_row(commitment_a, 0, 10), _row(commitment_a, 1, 20), _row(commitment_b, 0, 5)]
    root_sha256, row_count = _write_private_ledger(tmp_path, rows)
    a4_receipt = _synthetic_a4_receipt([commitment_a, commitment_b], row_count=row_count, root_sha256=root_sha256)

    result = enrichment.compute_evidence_enrichment(a4_receipt, tmp_path)

    assert result["ledger_consumed"] is True
    assert result["spans_covered"] == 3
    assert result["units_with_evidence"] == 2
    by_commitment = {e["source_unit_commitment_sha256"]: e for e in result["per_unit_evidence"]}
    assert by_commitment[commitment_a]["span_count"] == 2
    assert by_commitment[commitment_a]["total_span_bytes"] == 30
    assert by_commitment[commitment_b]["span_count"] == 1
    serialized = json.dumps(result)
    for row in rows:
        assert row["input_sha256"] not in serialized
        assert row["output_sha256"] not in serialized

    # Rerunning against the same private artifacts is a pure re-read, reproducible.
    assert enrichment.compute_evidence_enrichment(a4_receipt, tmp_path) == result


def test_compute_evidence_enrichment_succeeds_under_a_high_inherited_rss_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression for the merge-queue-only failure (green on the PR fastlane,
    red in the full 4-shard merge-group run): after ~5k prior tests in a
    pytest shard, the host process's inherited ``ru_maxrss`` can already sit
    above the 512 MiB production cap even though this synthetic stream never
    opens the real 1.5 GiB private ledger. The cap must bound only this
    pass's own growth, not that inherited high-water mark."""
    commitment_a = "a" * 64
    commitment_b = "b" * 64
    rows = [_row(commitment_a, 0, 10), _row(commitment_a, 1, 20), _row(commitment_b, 0, 5)]
    root_sha256, row_count = _write_private_ledger(tmp_path, rows)
    a4_receipt = _synthetic_a4_receipt([commitment_a, commitment_b], row_count=row_count, root_sha256=root_sha256)
    monkeypatch.setattr(enrichment, "_current_rss_bytes", lambda: 1_702_019_072)  # the exact CI figure

    result = enrichment.compute_evidence_enrichment(a4_receipt, tmp_path)

    assert result["ledger_consumed"] is True
    assert result["spans_covered"] == 3


def test_compute_evidence_enrichment_handles_a_zero_row_ledger(tmp_path: Path) -> None:
    commitment = "a" * 64
    root_sha256, row_count = _write_private_ledger(tmp_path, [])
    a4_receipt = _synthetic_a4_receipt([commitment], row_count=row_count, root_sha256=root_sha256)

    result = enrichment.compute_evidence_enrichment(a4_receipt, tmp_path)

    assert result["ledger_consumed"] is True
    assert result["spans_covered"] == 0
    assert result["per_unit_evidence"] == [enrichment.new_unit_accumulator() | {"source_unit_commitment_sha256": commitment}]


def test_compute_evidence_enrichment_refuses_when_private_manifest_missing(tmp_path: Path) -> None:
    a4_receipt = _synthetic_a4_receipt(["a" * 64], row_count=1, root_sha256="0" * 64)
    with pytest.raises(heldout.AssignmentError, match="missing"):
        enrichment.compute_evidence_enrichment(a4_receipt, tmp_path)


def test_compute_evidence_enrichment_refuses_a_drifted_manifest(tmp_path: Path) -> None:
    commitment = "a" * 64
    root_sha256, row_count = _write_private_ledger(tmp_path, [_row(commitment, 0, 10)])
    # The live A4 receipt now disagrees with what the private manifest says.
    a4_receipt = _synthetic_a4_receipt([commitment], row_count=row_count + 1, root_sha256=root_sha256)

    with pytest.raises(enrichment.EnrichmentError, match="manifest drift"):
        enrichment.compute_evidence_enrichment(a4_receipt, tmp_path)


def test_compute_evidence_enrichment_refuses_a_truncated_ledger(tmp_path: Path) -> None:
    commitment = "a" * 64
    rows = [_row(commitment, 0, 10), _row(commitment, 1, 20)]
    root_sha256, row_count = _write_private_ledger(tmp_path, rows)
    ledger_path = tmp_path / extraction.A4_LEDGER_FILENAME
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    ledger_path.write_text(lines[0] + "\n", encoding="utf-8")  # drop the second row, keep the manifest's claim
    a4_receipt = _synthetic_a4_receipt([commitment], row_count=row_count, root_sha256=root_sha256)

    with pytest.raises(enrichment.EnrichmentError, match="does not match A4's declared"):
        enrichment.compute_evidence_enrichment(a4_receipt, tmp_path)


def test_verify_evidence_privately_reproduces(tmp_path: Path) -> None:
    commitment = "a" * 64
    rows = [_row(commitment, 0, 10), _row(commitment, 1, 20)]
    root_sha256, row_count = _write_private_ledger(tmp_path, rows)
    a4_receipt = _synthetic_a4_receipt([commitment], row_count=row_count, root_sha256=root_sha256)
    computed = enrichment.compute_evidence_enrichment(a4_receipt, tmp_path)
    receipt_shaped = {"evidence_enrichment": computed}

    enrichment.verify_evidence_privately(receipt_shaped, a4_receipt, tmp_path)  # must not raise


def test_verify_evidence_privately_detects_a_tampered_receipt(tmp_path: Path) -> None:
    commitment = "a" * 64
    rows = [_row(commitment, 0, 10)]
    root_sha256, row_count = _write_private_ledger(tmp_path, rows)
    a4_receipt = _synthetic_a4_receipt([commitment], row_count=row_count, root_sha256=root_sha256)
    computed = enrichment.compute_evidence_enrichment(a4_receipt, tmp_path)
    tampered = copy.deepcopy(computed)
    tampered["spans_covered"] = 999
    receipt_shaped = {"evidence_enrichment": tampered}

    with pytest.raises(enrichment.EnrichmentError, match="does not reproduce"):
        enrichment.verify_evidence_privately(receipt_shaped, a4_receipt, tmp_path)


# --- A5's own per-commitment residuals ---------------------------------------


def test_derive_a5_unit_evidence_residuals_is_pure_reproducible_and_id_free() -> None:
    commitment_evidence = "a" * 64
    commitment_pending = "b" * 64
    a4_receipt = _synthetic_a4_receipt(
        [commitment_evidence, commitment_pending], row_count=1, root_sha256=extraction.EMPTY_LEDGER_ROOT_SHA256
    )
    per_unit_evidence = [
        {"source_unit_commitment_sha256": commitment_evidence, "span_count": 5, "total_span_bytes": 50,
         "min_span_byte_length": 5, "max_span_byte_length": 15},
        {"source_unit_commitment_sha256": commitment_pending, "span_count": 0, "total_span_bytes": 0,
         "min_span_byte_length": None, "max_span_byte_length": None},
    ]

    first = enrichment.derive_a5_unit_evidence_residuals(a4_receipt, per_unit_evidence)
    second = enrichment.derive_a5_unit_evidence_residuals(a4_receipt, per_unit_evidence)
    assert first == second
    assert len(first) == 2

    by_commitment = {r["subject_id"]: r for r in first}
    assert by_commitment[commitment_evidence]["reason_code"] == "structural_evidence_computed"
    assert by_commitment[commitment_evidence]["retryability"] == "not_retryable"
    assert by_commitment[commitment_pending]["reason_code"] == "structural_evidence_pending_source_ingestion"
    assert by_commitment[commitment_pending]["retryability"] == "retryable"
    assert by_commitment[commitment_pending]["owner_role"] == "V4_source_byte_ingestion"
    for residual in first:
        assert residual["stage"] == "A5"
        assert residual["subject_kind"] == "source_unit_commitment"


def test_derive_a5_unit_evidence_residuals_treats_a_missing_evidence_entry_as_zero() -> None:
    commitment = "a" * 64
    a4_receipt = _synthetic_a4_receipt([commitment], row_count=0, root_sha256=extraction.EMPTY_LEDGER_ROOT_SHA256)
    residuals = enrichment.derive_a5_unit_evidence_residuals(a4_receipt, [])
    assert len(residuals) == 1
    assert residuals[0]["reason_code"] == "structural_evidence_pending_source_ingestion"


# --- checked-in receipt: schema, bindings, forbidden content ----------------


def _validator() -> Draft202012Validator:
    schema = _load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _errors(value: dict[str, Any]) -> list[object]:
    return sorted(_validator().iter_errors(value), key=lambda error: list(error.path))


def test_a5_receipt_schema_and_v4_control_binding() -> None:
    receipt = _receipt()
    assert not _errors(receipt)
    assert receipt["controlling_outcome_sha256"] == V4_SHA256
    assert receipt["text_free"] is True
    assert receipt["expression_free"] is True

    changed = copy.deepcopy(receipt)
    changed["controlling_outcome_sha256"] = "0" * 64
    assert _errors(changed)


def test_a5_receipt_bindings_match_exact_inputs() -> None:
    receipt = _receipt()
    for binding in receipt["bindings"].values():
        bound_path = ROOT / binding["path"]
        assert bound_path.is_file()
        assert hashlib.sha256(bound_path.read_bytes()).hexdigest() == binding["sha256"]
    assert receipt["bindings"]["a4_deterministic_extraction"]["path"] == str(A4_RECEIPT_PATH.relative_to(ROOT))


def test_a5_receipt_dataset_rows_emitted_is_zero() -> None:
    receipt = _receipt()
    assert receipt["execution_counters"]["dataset_rows_emitted"] == 0
    assert receipt["safety_assertions"]["training_ready_silver_claimed"] is False


def test_a5_receipt_never_names_a_held_out_family_or_source_unit_or_source_text() -> None:
    receipt = _receipt()
    serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)

    assert not _all_keys(receipt) & FORBIDDEN_KEYS
    for needle in ("fam-", "db.", "historical."):
        assert needle not in serialized


def test_a5_receipt_carries_forward_every_a2_and_a4_residual_unchanged() -> None:
    receipt = _receipt()
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)

    a2_ids = {entry["residual_id"] for entry in a2_receipt["residuals"]}
    carried_a2_ids = {entry["residual_id"] for entry in receipt["a2_residuals_carried_forward"]}
    assert carried_a2_ids == a2_ids
    for entry in receipt["a2_residuals_carried_forward"]:
        assert entry["origin_stage"] == "A2"
        assert entry["status"] == "unresolved_carried_to_a5"

    a4_ids = {entry["residual_id"] for entry in a4_receipt["a4_residuals"]}
    carried_a4_ids = {entry["residual_id"] for entry in receipt["a4_residuals_carried_forward"]}
    assert carried_a4_ids == a4_ids
    for entry in receipt["a4_residuals_carried_forward"]:
        assert entry["origin_stage"] == "A4"
        assert entry["status"] == "unresolved_carried_to_a5"


def test_a5_residuals_are_derivable_and_cover_every_known_a4_commitment() -> None:
    receipt = _receipt()
    a4_receipt = _load(A4_RECEIPT_PATH)
    known_commitments = set(a4_receipt["builder_packet_consumption"]["unit_commitments"])

    assert len(receipt["a5_residuals"]) == len(known_commitments)
    assert {r["subject_id"] for r in receipt["a5_residuals"]} == known_commitments
    assert receipt["a5_residuals"] == enrichment.derive_a5_unit_evidence_residuals(
        a4_receipt, receipt["evidence_enrichment"]["per_unit_evidence"]
    )


def test_a5_evidence_enrichment_is_bound_to_a4_commitments_and_spans_covered() -> None:
    receipt = _receipt()
    a4_receipt = _load(A4_RECEIPT_PATH)
    known_commitments = set(a4_receipt["builder_packet_consumption"]["unit_commitments"])
    per_unit_evidence = receipt["evidence_enrichment"]["per_unit_evidence"]

    assert {e["source_unit_commitment_sha256"] for e in per_unit_evidence} == known_commitments
    assert receipt["evidence_enrichment"]["evidence_commitment_sha256"] == enrichment.evidence_commitment_sha256(
        per_unit_evidence
    )
    assert receipt["evidence_enrichment"]["spans_covered"] == sum(e["span_count"] for e in per_unit_evidence)
    assert receipt["evidence_enrichment"]["spans_covered"] == a4_receipt["builder_packet_consumption"][
        "extraction_ledger_commitment"
    ]["row_count"]


def test_a5_script_verifies_the_checked_in_receipt() -> None:
    receipt = _receipt()
    enrichment.validate_receipt_independently(receipt)  # must not raise


def test_a5_script_refuses_a_tampered_binding_hash() -> None:
    receipt = _receipt()
    tampered = copy.deepcopy(receipt)
    tampered["bindings"]["a4_deterministic_extraction"]["sha256"] = "0" * 64
    with pytest.raises(enrichment.EnrichmentError):
        enrichment.validate_receipt_independently(tampered)


def test_a5_script_refuses_evidence_commitment_drift() -> None:
    receipt = _receipt()
    tampered = copy.deepcopy(receipt)
    tampered["evidence_enrichment"]["evidence_commitment_sha256"] = "0" * 64
    with pytest.raises(enrichment.EnrichmentError, match="evidence_commitment_sha256"):
        enrichment.validate_receipt_independently(tampered)


def test_a5_script_refuses_a5_residuals_that_drift_from_per_unit_evidence() -> None:
    receipt = _receipt()
    tampered = copy.deepcopy(receipt)
    computed_entries = [r for r in tampered["a5_residuals"] if r["reason_code"] == "structural_evidence_computed"]
    pending_entries = [r for r in tampered["a5_residuals"] if r["reason_code"] != "structural_evidence_computed"]
    assert computed_entries and pending_entries  # the real receipt has both kinds
    victim = pending_entries[0]
    victim["reason_code"] = "structural_evidence_computed"
    victim["retryability"] = "not_retryable"
    with pytest.raises(enrichment.EnrichmentError, match="a5_residuals"):
        enrichment.validate_receipt_independently(tampered)


def test_a5_script_refuses_a_carried_forward_residual_with_wrong_status() -> None:
    receipt = _receipt()
    tampered = copy.deepcopy(receipt)
    tampered["a2_residuals_carried_forward"][0]["status"] = "unresolved_carried_to_a4"
    with pytest.raises(enrichment.EnrichmentError, match="a2_residuals_carried_forward"):
        enrichment.validate_receipt_independently(tampered)
