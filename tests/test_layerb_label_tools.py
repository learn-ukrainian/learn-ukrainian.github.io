"""Focused offline tests for Layer B label-union, scaffold, and merge tooling."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.audit.layerb_derivation import derive_keyed_records
from scripts.audit.layerb_keys import _build_event_index, _stable_grounding_key
from scripts.audit.layerb_label_common import LabelJoinError, sha256_text
from scripts.audit.layerb_label_merge import merge_annotator_sidecars
from scripts.audit.layerb_label_scaffold import (
    JUDGMENT_CASE_FIELDS,
    _artifact_events,
    build_scaffold,
    validate_annotator_record,
    write_scaffold,
)
from scripts.audit.layerb_label_union import (
    assert_no_drift,
    attach_keys,
    derive_union,
    rederive_keyed_derivation,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((REPO_ROOT / "schemas" / "qg-layer-b-labels.v2.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)
RAW_OUTPUT = "source evidence used for deterministic label checks"
EXCERPT = "source evidence"


def _sha(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _candidate(index: int, event_output_id: str) -> dict[str, Any]:
    normalized = RAW_OUTPUT
    return {
        "schema_version": "qg-anchor-candidate.v1",
        "candidate_id": _sha(f"candidate-{index}"),
        "event_output_id": event_output_id,
        "canonical_source_id": _sha("synthetic-source"),
        "source_index": 0,
        "tool_identity": {"raw_name": "sources_query_wikipedia", "canonical_name": "query_wikipedia"},
        "query_identity": {"canonical_json": '{"query":"synthetic"}', "sha256": _sha('{"query":"synthetic"}')},
        "raw_output_sha256": _sha(RAW_OUTPUT),
        "normalized_output_sha256": _sha(normalized),
        "output_capture_complete": True,
        "anchor_scan_complete": True,
        "match_type": "EXACT_CONTIGUOUS",
        "similarity": 1.0,
        "tool_query_matched": True,
        "eligibility": "ELIGIBLE",
        "error_status": "NONE",
        "ordered_segment_spans": [
            {
                "segment_index": 0,
                "excerpt_normalized_start": 0,
                "excerpt_normalized_end": len(EXCERPT),
                "output_normalized_start": 0,
                "output_normalized_end": len(EXCERPT),
                "output_raw_start": 0,
                "output_raw_end": len(EXCERPT),
                "normalized_segment_sha256": _sha(EXCERPT),
                "raw_segment_sha256": _sha(EXCERPT),
            }
        ],
    }


def _inputs(tmp_path: Path, count: int = 8) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Path]:
    corpus_dir = tmp_path / "audit-corpus"
    corpus_dir.mkdir()
    metadata = {"pin_slug": "synthetic-pin", "family": "synthetic"}
    artifact_name = "synthetic-pin__ahatanhel-krymskyi.json"
    event = {
        "tool": "sources_query_wikipedia",
        "input": {"query": "synthetic"},
        "status": "completed",
        "output": RAW_OUTPUT,
    }
    event_output_id = next(iter(_build_event_index([event])))
    fact_checks: list[dict[str, Any]] = []
    for index in range(count):
        fact_checks.append(
            {
                "fact_check_id": f"fact-{index}",
                "claim": f"Synthetic claim {index}",
                "verdict": "CONFIRMED",
                "grounding": {
                    "evidence_excerpt": EXCERPT,
                    "tool": "sources_query_wikipedia",
                    "query": "synthetic",
                },
            }
        )
    artifact = {
        "schema_version": "qg_bakeoff_run.v1",
        "seat_arm": metadata,
        "fixture": {"slug": "ahatanhel-krymskyi"},
        "payload": {"fact_checks": fact_checks},
        "dispatch": {"tool_events": [event]},
    }
    (corpus_dir / artifact_name).write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
    derivations: list[dict[str, Any]] = []
    shadows: list[dict[str, Any]] = []
    union_rows: list[dict[str, Any]] = []
    for index, fact_check in enumerate(fact_checks):
        v1_admissible = index in {1, 3, 4}
        v2_effective = index in {0, 2, 3, 4}
        v2_abstained = index == 2
        base = {
            "fixture": "ahatanhel-krymskyi",
            "seat_arm": repr(metadata) + "/tooled",
            "claim": fact_check["claim"],
            "excerpt": EXCERPT,
            "v1_admissible": v1_admissible,
            "v2_anchored": v2_effective and not v2_abstained,
            "v2_abstained": v2_abstained,
            "similarity": 1.0,
            "abstain_recovered": v2_abstained,
            "v2_effective": v2_effective,
            "tool_query_matched": True,
            "best_span_preview": EXCERPT,
            "gold_is_true": True,
        }
        derivations.append(base)
        key = _stable_grounding_key(Path(artifact_name), index, fact_check)
        shadows.append(
            {
                "grounding_key": key,
                "artifact": artifact_name,
                "seat_metadata": metadata,
                "fixture": "ahatanhel-krymskyi",
                "fact_check_id": key,
                "claim": fact_check["claim"],
                "reviewer_verdict": "CONFIRMED",
                "layer_a": {
                    "decision": "ANCHOR",
                    "reason": "ANCHORED_CONTIGUOUS",
                    "candidate_set_complete": True,
                    "candidates": [_candidate(index, event_output_id)],
                },
                "candidate_details": [{"candidate": _candidate(index, event_output_id)}],
            }
        )
        union = dict(base)
        union["source_index"] = index
        union["union_categories"] = ["recovered"]
        union_rows.append(union)
    return (
        {"kind": "qg-layer-b-label-union-input", "rows": union_rows, "total_rows": len(union_rows)},
        {"records": derivations},
        {"records": list(reversed(shadows))},
        corpus_dir,
    )


def _completed_case(case: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(case))
    result.update(
        {
            "claim_is_true": True,
            "expected_reviewer_verdict": "CONFIRMED",
            "expected_layer_a_decision": "ANCHOR",
            "expected_layer_a_reason": "ANCHORED_CONTIGUOUS",
            "expected_aggregate_relation": "ENTAILS",
            "expected_fact_check_decision": "ACCEPT",
            "context_sufficient": True,
            "failure_class": "ELLIPSIZED_GENUINE_EXCERPT",
            "corpus_verification_status": "VERIFIED",
            "annotators": ["annotator-a", "annotator-b"],
            "adjudication": {"status": "AGREED", "adjudicator": None, "note": "Original completed case."},
        }
    )
    for candidates in result["candidates_by_event_output_id"].values():
        for candidate in candidates:
            candidate["expected_source_relation"] = "ENTAILS"
            candidate["expected_support_spans"] = [{"start": 0, "end": len(EXCERPT), "role": "SUPPORTS"}]
    return result


def _keyed_inputs(tmp_path: Path, count: int = 8) -> tuple[dict[str, Any], dict[str, Any], Path]:
    union, derivation, shadow, corpus_dir = _inputs(tmp_path, count)
    keyed, _report = attach_keys(union, derivation, shadow, corpus_dir=corpus_dir)
    return keyed, shadow, corpus_dir


def _keyed_derivation(derivation: Mapping[str, Any], shadow: Mapping[str, Any]) -> dict[str, Any]:
    """Build source-keyed synthetic derivations without using ``attach``."""
    records: list[dict[str, Any]] = []
    for index, row in enumerate(derivation["records"]):
        keyed = dict(row)
        grounding_key = _shadow_for_fact_index(shadow, index)["grounding_key"]
        keyed["grounding_key"] = grounding_key
        keyed["fact_check_index"] = index
        records.append(keyed)
    return {"kind": "qg-layer-b-keyed-union-derivation", "records": records, "total_rows": len(records)}


def _frozen_category_union(keyed_derivation: Mapping[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(keyed_derivation["records"]):
        categories: list[str] = []
        if row["v1_admissible"] is False and row["v2_effective"] is True:
            categories.append("recovered")
        if row["v1_admissible"] is True and row["v2_effective"] is False:
            categories.append("regression")
        if row["v2_abstained"] is True:
            categories.append("abstain")
        if not categories:
            continue
        frozen_row = {
            key: value for key, value in row.items() if key not in {"grounding_key", "fact_check_index"}
        }
        frozen_row["source_index"] = index
        frozen_row["union_categories"] = [
            category for category in ("recovered", "regression", "abstain") if category in categories
        ]
        rows.append(frozen_row)
    return {"kind": "qg-layer-b-label-union-input", "rows": rows, "total_rows": len(rows)}


def _raw_rederive_inputs(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    corpus_dir = tmp_path / "raw-corpus"
    fixtures_dir = tmp_path / "fixtures"
    corpus_dir.mkdir()
    fixtures_dir.mkdir()
    claims = ["Synthetic source claim zero", "Synthetic source claim one"]
    (fixtures_dir / "synthetic.json").write_text(
        json.dumps(
            {
                "slug": "synthetic",
                "title": "Synthetic",
                "passage_md": " ".join(claims),
                "claims": [
                    {"claim_id": f"synthetic-{index}", "claim": claim, "is_true": True}
                    for index, claim in enumerate(claims)
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    artifact = {
        "schema_version": "qg_bakeoff_run.v1",
        "arm": "tooled",
        "seat": "synthetic-seat",
        "fixture": {"slug": "synthetic"},
        "payload": {
            "fact_checks": [
                {
                    "fact_check_id": f"synthetic-{index}",
                    "claim": claim,
                    "verdict": "CONFIRMED",
                    "grounding": {
                        "evidence_excerpt": claim,
                        "tool": "sources_query_wikipedia",
                        "query": "synthetic",
                    },
                }
                for index, claim in enumerate(claims)
            ]
        },
        "dispatch": {
            "tool_events": [
                {
                    "tool": "sources_query_wikipedia",
                    "input": {"query": "synthetic"},
                    "status": "completed",
                    "output": " ".join(claims),
                }
            ]
        },
    }
    (corpus_dir / "synthetic__synthetic.json").write_text(
        json.dumps(artifact, ensure_ascii=False), encoding="utf-8"
    )
    records = derive_keyed_records(corpus_dir, fixtures_dir=fixtures_dir)
    frozen = {
        "records": [
            {key: value for key, value in record.items() if key not in {"grounding_key", "fact_check_index"}}
            for record in records
        ]
    }
    return corpus_dir, fixtures_dir, frozen


def _make_duplicate_structural_group(
    tmp_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Path]:
    """Create two fact checks with one structural key and distinct stable keys."""
    union, derivation, shadow, corpus_dir = _inputs(tmp_path, count=2)
    artifact_path = next(corpus_dir.glob("*.json"))
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    shared_claim = artifact["payload"]["fact_checks"][0]["claim"]
    artifact["payload"]["fact_checks"][1]["claim"] = shared_claim
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
    for document in (union, derivation):
        document["rows" if document is union else "records"][1]["claim"] = shared_claim
    for record in shadow["records"]:
        record["claim"] = shared_claim
    return union, derivation, shadow, corpus_dir


def _shadow_for_fact_index(shadow: Mapping[str, Any], index: int) -> dict[str, Any]:
    marker = f"#fact_checks[{index}]"
    return next(record for record in shadow["records"] if marker in record["grounding_key"])


def test_attach_totality_bijection_and_original_row_preservation_for_535_rows(tmp_path: Path) -> None:
    union, derivation, shadow, corpus_dir = _inputs(tmp_path, count=535)

    keyed, report = attach_keys(union, derivation, shadow, corpus_dir=corpus_dir)

    assert report["matched_rows"] == report["union_rows"] == 535
    assert report["total"] is True
    assert report["bijective"] is True
    assert len({row["grounding_key"] for row in keyed["rows"]}) == 535
    for original, emitted in zip(union["rows"], keyed["rows"], strict=True):
        preserved = {key: value for key, value in emitted.items() if key not in {"grounding_key", "fact_check_index"}}
        assert preserved == original


def test_attach_hard_fails_with_exact_ambiguous_key(tmp_path: Path) -> None:
    union, derivation, shadow, corpus_dir = _inputs(tmp_path, count=2)
    duplicate = copy.deepcopy(derivation["records"][0])
    derivation["records"].append(duplicate)
    ambiguous = copy.deepcopy(union["rows"][0])
    ambiguous.pop("source_index")
    union["rows"] = [ambiguous]

    with pytest.raises(LabelJoinError, match=r"ambiguous keys=.*Synthetic claim 0"):
        attach_keys(union, derivation, shadow, corpus_dir=corpus_dir)


def test_attach_duplicate_group_uses_per_row_candidate_identity(tmp_path: Path) -> None:
    union, derivation, shadow, corpus_dir = _make_duplicate_structural_group(tmp_path)
    derivation["records"][0]["similarity"] = 0.91
    derivation["records"][1]["similarity"] = 0.82
    union["rows"][0]["similarity"] = 0.91
    union["rows"][1]["similarity"] = 0.82
    for document in (union, derivation):
        records = document["rows" if document is union else "records"]
        records[1]["v1_admissible"] = False
        records[1]["v2_anchored"] = True
        records[1]["v2_effective"] = True
    for index, similarity in enumerate((0.91, 0.82)):
        record = _shadow_for_fact_index(shadow, index)
        record["layer_a"]["candidates"][0]["similarity"] = similarity
        record["layer_a"]["candidates"][0]["source_index"] = index
        record["candidate_details"][0]["candidate"]["similarity"] = similarity
        record["candidate_details"][0]["candidate"]["source_index"] = index

    keyed, report = attach_keys(union, derivation, shadow, corpus_dir=corpus_dir)

    expected = {index: _shadow_for_fact_index(shadow, index)["grounding_key"] for index in range(2)}
    assert [row["grounding_key"] for row in keyed["rows"]] == [expected[0], expected[1]]
    assert report["duplicate_group_resolutions"][0]["resolution_basis"] == "per_row_identity"


def test_attach_duplicate_group_records_equivalence_class_resolution(tmp_path: Path) -> None:
    union, derivation, shadow, corpus_dir = _make_duplicate_structural_group(tmp_path)
    first = _shadow_for_fact_index(shadow, 0)
    second = _shadow_for_fact_index(shadow, 1)
    second["layer_a"] = copy.deepcopy(first["layer_a"])

    _keyed, report = attach_keys(union, derivation, shadow, corpus_dir=corpus_dir)

    assert report["duplicate_group_resolutions"][0]["resolution_basis"] == "equivalence_class"


def test_attach_duplicate_group_hard_fails_when_members_differ_without_identity(tmp_path: Path) -> None:
    union, derivation, shadow, corpus_dir = _make_duplicate_structural_group(tmp_path)
    for document in (union, derivation):
        document["rows" if document is union else "records"][1]["v1_admissible"] = False
    second = _shadow_for_fact_index(shadow, 1)
    second["layer_a"]["candidates"][0]["similarity"] = 0.82
    second["candidate_details"][0]["candidate"]["similarity"] = 0.82

    with pytest.raises(LabelJoinError, match="duplicate structural-key group"):
        attach_keys(union, derivation, shadow, corpus_dir=corpus_dir)


def test_attached_keys_equal_shadow_helper_for_sampled_rows(tmp_path: Path) -> None:
    keyed, _shadow, corpus_dir = _keyed_inputs(tmp_path, count=12)
    artifact_path = next(corpus_dir.glob("*.json"))
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    for row in keyed["rows"][::5]:
        index = row["fact_check_index"]
        assert row["grounding_key"] == _stable_grounding_key(
            artifact_path, index, artifact["payload"]["fact_checks"][index]
        )


def test_keyed_union_is_byte_identical_and_matches_frozen_category_fixture(tmp_path: Path) -> None:
    union, derivation, shadow, _corpus_dir = _inputs(tmp_path, count=8)
    del union
    keyed_derivation = _keyed_derivation(derivation, shadow)
    frozen_union = _frozen_category_union(keyed_derivation)

    first, first_report = derive_union(
        keyed_derivation,
        frozen_union_document=frozen_union,
        seed=4913,
        control_per_stratum=1,
    )
    second, second_report = derive_union(
        keyed_derivation,
        frozen_union_document=frozen_union,
        seed=4913,
        control_per_stratum=1,
    )

    assert json.dumps(first, ensure_ascii=False, separators=(",", ":")) == json.dumps(
        second, ensure_ascii=False, separators=(",", ":")
    )
    assert first_report == second_report
    assert first_report["category_membership"]["category_multiset_equal"] is True
    assert first_report["control_resampled"] is True
    assert first_report["frozen_control_sample_reproduction_guaranteed"] is False


def test_rederive_no_drift_positive_and_synthetic_drift_hard_fail(tmp_path: Path) -> None:
    corpus_dir, fixtures_dir, frozen = _raw_rederive_inputs(tmp_path)
    regenerated = derive_keyed_records(corpus_dir, fixtures_dir=fixtures_dir)

    proof = assert_no_drift(regenerated, frozen)
    document, rederive_report = rederive_keyed_derivation(
        artifacts_dir=corpus_dir,
        fixtures_dir=fixtures_dir,
        frozen_derivation_document=frozen,
        expected_rows=2,
    )

    assert proof["no_drift"] is True
    assert document["total_rows"] == rederive_report["grounding_keys_unique"] == 2
    drifted = copy.deepcopy(regenerated)
    drifted[0]["claim"] = "Changed source claim"
    with pytest.raises(LabelJoinError, match="symmetric_difference"):
        assert_no_drift(drifted, frozen)


def test_source_derivation_retains_comparison_only_no_fixture_fallback(tmp_path: Path) -> None:
    corpus_dir, _fixtures_dir, _frozen = _raw_rederive_inputs(tmp_path)

    records = derive_keyed_records(corpus_dir, fixtures_dir=None)

    assert len(records) == 2
    assert {record["gold_is_true"] for record in records} == {None}


def test_rederive_cli_is_byte_identical_for_two_source_walks(tmp_path: Path) -> None:
    corpus_dir, fixtures_dir, frozen = _raw_rederive_inputs(tmp_path)
    frozen_path = tmp_path / "frozen-derivation.json"
    frozen_path.write_text(json.dumps(frozen, ensure_ascii=False), encoding="utf-8")
    first_path = tmp_path / "keyed-first.json"
    second_path = tmp_path / "keyed-second.json"
    command = [
        sys.executable,
        "scripts/audit/layerb_label_union.py",
        "rederive",
        "--derivation",
        str(frozen_path),
        "--artifacts-dir",
        str(corpus_dir),
        "--fixtures-dir",
        str(fixtures_dir),
        "--expected-rows",
        "2",
    ]
    for output in (first_path, second_path):
        completed = subprocess.run(
            [*command, "--output", str(output)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr

    assert first_path.read_bytes() == second_path.read_bytes()
    keyed_document = json.loads(first_path.read_text(encoding="utf-8"))
    assert keyed_document["keying"]["join_report"]["no_drift"] is True
    assert [row["fact_check_index"] for row in keyed_document["records"]] == [0, 1]


def test_scaffold_consumes_union_derived_from_keyed_source_records(tmp_path: Path) -> None:
    union, derivation, shadow, corpus_dir = _inputs(tmp_path, count=8)
    del union
    keyed_derivation = _keyed_derivation(derivation, shadow)
    keyed_union, union_report = derive_union(
        keyed_derivation,
        frozen_union_document=_frozen_category_union(keyed_derivation),
        seed=4913,
        control_per_stratum=1,
    )
    keyed_path = tmp_path / "keyed-union.json"
    shadow_path = tmp_path / "phase1-shadow.json"
    keyed_path.write_text(json.dumps(keyed_union, ensure_ascii=False), encoding="utf-8")
    shadow_path.write_text(json.dumps(shadow, ensure_ascii=False), encoding="utf-8")

    scaffold, manifest = write_scaffold(
        keyed_path,
        shadow_path,
        corpus_dir=corpus_dir,
        output_dir=tmp_path / "keyed-scaffold",
        shard_count=2,
    )

    assert len(scaffold["cases"]) == keyed_union["total_rows"] == 5
    assert manifest["counts"]["segment_verified_candidates"] == 5
    assert union_report["category_membership"]["category_rows"] == 3


def test_scaffold_null_judgments_hashes_windows_and_resume(tmp_path: Path) -> None:
    keyed, shadow, corpus_dir = _keyed_inputs(tmp_path, count=8)
    output_dir = tmp_path / "scaffold"

    with pytest.raises(RuntimeError, match="simulated crash"):
        build_scaffold(keyed, shadow, corpus_dir=corpus_dir, output_dir=output_dir, shard_count=4, crash_after_shards=1)
    scaffold, report = build_scaffold(keyed, shadow, corpus_dir=corpus_dir, output_dir=output_dir, shard_count=4)

    assert report["cases"] == 8
    assert report["segment_verified_candidates"] == 8
    assert all(case[field] is None for case in scaffold["cases"] for field in JUDGMENT_CASE_FIELDS)
    packet_case_ids: list[str] = []
    for packet_path in sorted((output_dir / "packets").glob("shard-*.jsonl")):
        marker = packet_path.with_suffix(".done.json")
        assert marker.is_file()
        for line in packet_path.read_text(encoding="utf-8").splitlines():
            packet = json.loads(line)
            packet_case_ids.append(packet["case"]["case_id"])
            for navigation in packet["candidate_navigation"]:
                assert navigation["full_output_sha256"] == _sha(RAW_OUTPUT)
                assert navigation["full_output_bytes"] == len(RAW_OUTPUT.encode("utf-8"))
                assert (
                    navigation["raw_window_text"]
                    == RAW_OUTPUT[navigation["raw_window_start"] : navigation["raw_window_end"]]
                )
                assert navigation["comment"].startswith("NAVIGATION AID ONLY")
    assert sorted(packet_case_ids) == sorted(case["case_id"] for case in scaffold["cases"])
    assert len(packet_case_ids) == len(set(packet_case_ids)) == 8
    for case in scaffold["cases"]:
        for event_output_id, candidates in case["candidates_by_event_output_id"].items():
            for candidate in candidates:
                assert candidate["raw_output_sha256"] == sha256_text(RAW_OUTPUT)
                assert candidate["normalized_output_sha256"] == sha256_text(RAW_OUTPUT)
                assert event_output_id
                for segment in candidate["ordered_segment_spans"]:
                    raw = RAW_OUTPUT[segment["output_raw_start"] : segment["output_raw_end"]]
                    assert sha256_text(raw) == segment["raw_segment_sha256"]
    keyed_path = tmp_path / "keyed-union.json"
    shadow_path = tmp_path / "phase1-shadow.json"
    keyed_path.write_text(json.dumps(keyed, ensure_ascii=False), encoding="utf-8")
    shadow_path.write_text(json.dumps(shadow, ensure_ascii=False), encoding="utf-8")
    _manifest_scaffold, manifest = write_scaffold(
        keyed_path,
        shadow_path,
        corpus_dir=corpus_dir,
        output_dir=tmp_path / "manifest-scaffold",
    )
    assert manifest["counts"]["segment_verified_candidates"] == 8


def test_scaffold_hard_fails_when_a_shadow_segment_hash_does_not_match(tmp_path: Path) -> None:
    keyed, shadow, corpus_dir = _keyed_inputs(tmp_path)
    corrupt = copy.deepcopy(shadow)
    corrupt["records"][0]["layer_a"]["candidates"][0]["ordered_segment_spans"][0]["raw_segment_sha256"] = "0" * 64

    with pytest.raises(LabelJoinError, match="segment SHA-256 does not match captured output"):
        build_scaffold(keyed, corrupt, corpus_dir=corpus_dir, output_dir=tmp_path / "scaffold")


@pytest.mark.parametrize(
    "module",
    (
        "scripts.audit.layerb_derivation",
        "scripts.audit.layerb_label_common",
        "scripts.audit.layerb_label_union",
        "scripts.audit.layerb_label_scaffold",
        "scripts.audit.layerb_label_merge",
    ),
)
def test_label_tool_imports_do_not_load_runtime_reviewer_dispatch(module: str) -> None:
    command = (
        "import importlib, sys; "
        f"importlib.import_module({module!r}); "
        "raise SystemExit('scripts.audit.llm_reviewer_dispatch' in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr


def test_validate_annotator_record_rejects_out_of_bounds_spans(tmp_path: Path) -> None:
    keyed, shadow, corpus_dir = _keyed_inputs(tmp_path)
    scaffold, _report = build_scaffold(keyed, shadow, corpus_dir=corpus_dir, output_dir=tmp_path / "scaffold")
    working = _completed_case(scaffold["cases"][0])
    working.pop("annotators")
    working.pop("adjudication")
    artifact = json.loads(next(corpus_dir.glob("*.json")).read_text(encoding="utf-8"))
    outputs = _build_event_index(_artifact_events(artifact))

    validate_annotator_record(working, outputs)
    invalid = copy.deepcopy(working)
    candidate = next(iter(invalid["candidates_by_event_output_id"].values()))[0]
    candidate["ordered_segment_spans"][0]["output_raw_end"] = len(RAW_OUTPUT) + 1
    with pytest.raises(LabelJoinError, match="out of bounds"):
        validate_annotator_record(invalid, outputs)


def test_merge_agreement_and_exact_span_disagreement(tmp_path: Path) -> None:
    keyed, shadow, corpus_dir = _keyed_inputs(tmp_path)
    scaffold, _report = build_scaffold(keyed, shadow, corpus_dir=corpus_dir, output_dir=tmp_path / "scaffold")
    completed = copy.deepcopy(scaffold)
    completed["cases"] = [_completed_case(case) for case in scaffold["cases"]]

    report, merged = merge_annotator_sidecars(completed, copy.deepcopy(completed))
    assert report["counts"]["agreed"] == len(completed["cases"])
    assert all(case["adjudication"]["status"] == "AGREED" for case in merged["cases"])
    assert not list(VALIDATOR.iter_errors(merged))

    right = copy.deepcopy(completed)
    target = next(iter(right["cases"][0]["candidates_by_event_output_id"].values()))[0]
    target["ordered_segment_spans"][0]["output_raw_end"] -= 1
    report, merged = merge_annotator_sidecars(completed, right)
    assert report["counts"]["material_disagreements"] == 1
    assert report["counts"]["span_only_disagreements"] == 1
    assert report["cases"][0]["material_differences"][0]["field"].endswith("ordered_segment_spans")
    assert "adjudication" not in merged["cases"][0]
    assert list(VALIDATOR.iter_errors(merged))
