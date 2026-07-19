"""Fixture proofs for bounded curriculum-preparation packets."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "agents_extensions/shared/skills/curriculum-preparation/scripts/bounded_packet.py"
SPEC = importlib.util.spec_from_file_location("curriculum_preparation_bounded_packet_tests", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
packet = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = packet
SPEC.loader.exec_module(packet)
bc = packet.bounded_completion

PASS_SCORES = {
    "engagement": 9.0,
    "pedagogical": 9.0,
    "naturalness": 9.0,
    "decolonization": 9.0,
    "tone": 9.0,
}


@pytest.fixture
def preparation_fixture(tmp_path: Path) -> dict[str, Any]:
    """Round-trip all synthetic inputs through tmp_path; touch no curriculum."""

    value = {
        "protocol": {
            "protocol_version": "5.0.0",
            "tool_sha256": "6" * 64,
            "prompt_sha256": "7" * 64,
            "schema_sha256": "8" * 64,
            "reviewer_family": "fixture-cross-family",
            "reviewer_model": "fixture-model",
        },
        "bio": [
            {
                "track": "bio",
                "slug": "fixture-a",
                "profile_id": "bio",
                "profile_version": "1.1.0",
                "family": "seminar",
                "preparation_identity": "1" * 64,
                "deterministic": {"passed": True, "reason_codes": []},
                "cells": [
                    {"path": "evidence/bio/fixture-a-plan.yaml", "source_sha256": "a" * 64},
                    {"path": "evidence/bio/fixture-a-dossier.md", "source_sha256": "b" * 64},
                ],
            },
            {
                "track": "bio",
                "slug": "fixture-b",
                "profile_id": "bio",
                "profile_version": "1.1.0",
                "family": "seminar",
                "preparation_identity": "2" * 64,
                "deterministic": {"passed": True, "reason_codes": []},
                "cells": [
                    {"path": "evidence/bio/fixture-b-plan.yaml", "source_sha256": "c" * 64},
                    {"path": "evidence/bio/fixture-b-dossier.md", "source_sha256": "d" * 64},
                ],
            },
        ],
        "core": [
            {
                "track": "core",
                "slug": "fixture-c",
                "profile_id": "core",
                "profile_version": "1.1.0",
                "family": "core-module",
                "preparation_identity": "3" * 64,
                "deterministic": {"passed": True, "reason_codes": []},
                "cells": [{"path": "evidence/core/fixture-c-plan.yaml", "source_sha256": "f" * 64}],
            },
            {
                "track": "core",
                "slug": "fixture-d",
                "profile_id": "core",
                "profile_version": "1.1.0",
                "family": "core-module",
                "preparation_identity": "4" * 64,
                "deterministic": {"passed": True, "reason_codes": []},
                "cells": [{"path": "evidence/core/fixture-d-plan.yaml", "source_sha256": "9" * 64}],
            },
        ],
    }
    value["prior_passes"] = [
        {
            "target": "bio/fixture-a",
            "path": "evidence/bio/fixture-a-plan.yaml",
            "source_sha256": "a" * 64,
            "preparation_identity": "1" * 64,
            "verdict": "PASS",
        },
        {
            "target": "bio/fixture-a",
            "path": "evidence/bio/fixture-a-dossier.md",
            "source_sha256": "b" * 64,
            "preparation_identity": "1" * 64,
            "verdict": "PASS",
        },
        {
            "target": "bio/fixture-b",
            "path": "evidence/bio/fixture-b-plan.yaml",
            "source_sha256": "c" * 64,
            "preparation_identity": "2" * 64,
            "verdict": "PASS",
        },
    ]
    path = tmp_path / "bounded-preparation-packets.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def _protocol(value: Mapping[str, Any]) -> dict[str, str]:
    return bc.make_review_protocol_identity(**value["protocol"])


def _admit_bio(value: Mapping[str, Any]) -> dict[str, Any]:
    return packet.admit_packet(value["bio"], limit=2, prior_passes=value["prior_passes"])


def test_admission_is_finite_homogeneous_and_exact_hash_bound(
    preparation_fixture: dict[str, Any],
) -> None:
    value = preparation_fixture
    admitted = _admit_bio(value)

    assert [item["target"] for item in admitted["scope"]] == ["bio/fixture-a", "bio/fixture-b"]
    assert admitted["counts"] == {"model_calls": 0, "repairs": 0, "reused_pass_cells": 3}
    assert all(cell["reused_pass"] for cell in admitted["cells"] if cell["target"] == "bio/fixture-a")
    assert packet.select_review_paths(admitted, phase="INITIAL") == ["evidence/bio/fixture-b-dossier.md"]

    preparation_drift = deepcopy(value["bio"])
    preparation_drift[0]["preparation_identity"] = "5" * 64
    drifted = packet.admit_packet(preparation_drift, limit=2, prior_passes=value["prior_passes"])
    assert [cell["path"] for cell in drifted["cells"] if not cell["reused_pass"]] == [
        "evidence/bio/fixture-a-plan.yaml",
        "evidence/bio/fixture-a-dossier.md",
        "evidence/bio/fixture-b-dossier.md",
    ]

    with pytest.raises(packet.PreparationPacketError) as limited:
        packet.admit_packet(value["bio"], limit=1)
    assert limited.value.code == "PACKET_LIMIT_EXCEEDED"
    assert limited.value.receipt["counts"]["model_calls"] == 0

    with pytest.raises(packet.PreparationPacketError) as mixed:
        packet.admit_packet([value["bio"][0], value["core"][0]], limit=2)
    assert mixed.value.code == "PACKET_HETEROGENEOUS"
    assert mixed.value.receipt["counts"]["model_calls"] == 0


def test_deterministic_failure_rejects_before_packet_or_model_call(
    preparation_fixture: dict[str, Any],
) -> None:
    targets = deepcopy(preparation_fixture["core"])
    targets[0]["deterministic"] = {
        "passed": False,
        "reason_codes": ["MISSING_REQUIRED_SOURCE"],
    }

    with pytest.raises(packet.PreparationPacketError) as rejected:
        packet.admit_packet(targets, limit=2)

    assert rejected.value.code == "DETERMINISTIC_FAILURE"
    assert rejected.value.receipt["reason_codes"] == ["MISSING_REQUIRED_SOURCE"]
    assert rejected.value.receipt["counts"] == {"model_calls": 0, "repairs": 0}
    assert rejected.value.receipt["paths"] == [
        "evidence/core/fixture-c-plan.yaml",
        "evidence/core/fixture-d-plan.yaml",
    ]


def test_bio_fixture_composes_one_repair_two_reviews_and_terminal_hold(
    preparation_fixture: dict[str, Any],
) -> None:
    value = preparation_fixture
    admitted = _admit_bio(value)
    protocol = _protocol(value)
    initial_source = packet.source_identity(admitted)
    run = bc.start_run(
        target=f"bio/packet-{admitted['scope_sha256'][:16]}",
        run_id="a" * 32,
        review_protocol_identity=protocol,
        learner_source_sha256=initial_source,
    )
    run = bc.complete_inspection(run, needs_build=False)
    run = bc.record_deterministic_verification(run, learner_source_sha256=initial_source, passed=True)

    phase = bc.semantic_review_phase(
        run,
        review_protocol_identity=protocol,
        learner_source_sha256=initial_source,
    )
    initial_paths = packet.select_review_paths(admitted, phase=phase)
    initial_pending = packet.pending_dispatch_receipt(admitted, run, phase=phase, paths=initial_paths)
    assert initial_pending == {
        "phase": "INITIAL",
        "paths": ["evidence/bio/fixture-b-dossier.md"],
        "hashes": [
            {
                "path": "evidence/bio/fixture-b-dossier.md",
                "source_sha256": "d" * 64,
                "preparation_identity": "2" * 64,
            }
        ],
        "reason_codes": ["INITIAL_NON_REUSED_ONLY"],
        "counts": {"model_calls": 1, "repairs": 0},
    }
    assert run["measurements"]["model_call_count"] == 0

    failed_path = initial_paths[0]
    blockers = [
        {
            "path": failed_path,
            "reason_code": "SOURCE_CONFLICT",
            "reason": "The reviewed sources conflict on the bounded factual claim.",
            "owner": "bio-preparation",
            "evidence": "fixture packet review evidence",
            "unblock_condition": "A stable authoritative source resolves the conflict.",
        }
    ]
    run = bc.record_semantic_review(
        run,
        review_protocol_identity=protocol,
        learner_source_sha256=initial_source,
        evidence_id="1" * 64,
        reported_disposition="REVISE",
        dimension_scores=PASS_SCORES,
        prompt_bytes=120,
        schema_bytes=40,
    )
    assert run["state"] == "CONSOLIDATED_REPAIR"
    assert len(blockers) == len(initial_paths) == 1

    repaired = deepcopy(admitted)
    next(cell for cell in repaired["cells"] if cell["path"] == failed_path)["source_sha256"] = "e" * 64
    repaired["hashes"] = [
        {
            "path": cell["path"],
            "source_sha256": cell["source_sha256"],
            "preparation_identity": cell["preparation_identity"],
        }
        for cell in repaired["cells"]
    ]
    final_source = packet.source_identity(repaired)
    run = bc.record_consolidated_repair(run, learner_source_sha256=final_source)
    run = bc.record_deterministic_verification(run, learner_source_sha256=final_source, passed=True)

    pass_paths = [cell["path"] for cell in repaired["cells"] if cell["path"] != failed_path]
    before_singleton = deepcopy(run)
    with pytest.raises(packet.PreparationPacketError) as singleton:
        packet.select_review_paths(
            repaired,
            phase="FINAL",
            failed_paths=[failed_path],
            changed_paths=[failed_path],
            pass_paths=pass_paths,
            requested_paths=[pass_paths[0]],
        )
    assert singleton.value.code == "UNCHANGED_PASS_SINGLETON_REVIEW"
    assert run == before_singleton

    phase = bc.semantic_review_phase(
        run,
        review_protocol_identity=protocol,
        learner_source_sha256=final_source,
    )
    final_paths = packet.select_review_paths(
        repaired,
        phase=phase,
        failed_paths=[failed_path],
        changed_paths=[failed_path],
        pass_paths=pass_paths,
    )
    final_pending = packet.pending_dispatch_receipt(repaired, run, phase=phase, paths=final_paths)
    assert final_pending["paths"] == [failed_path]
    assert final_pending["hashes"][0]["source_sha256"] == "e" * 64
    assert final_pending["reason_codes"] == ["FINAL_CHANGED_FAILED_ONLY"]
    assert final_pending["counts"] == {"model_calls": 2, "repairs": 1}

    run = bc.record_semantic_review(
        run,
        review_protocol_identity=protocol,
        learner_source_sha256=final_source,
        evidence_id="2" * 64,
        reported_disposition="REVISE",
        dimension_scores=PASS_SCORES,
        prompt_bytes=100,
        schema_bytes=40,
    )
    assert [review["phase"] for review in run["reviews"]] == ["INITIAL", "FINAL"]
    assert run["measurements"]["model_call_count"] == 2
    assert run["measurements"]["repair_count"] == 1

    terminal = packet.terminal_hold_receipt(
        repaired,
        run,
        failed_paths=[failed_path],
        blockers=blockers,
        date="2026-07-19",
        evidence_url="https://example.test/reviews/bio-fixture-b",
        token_count=83,
        cost_usd=0.024,
    )
    assert terminal["next_action"] == "stop"
    assert terminal["reason_codes"] == ["PREPARATION_REVIEW_BUDGET_EXHAUSTED", "PREPARATION_HOLD_ACTIVE"]
    assert terminal["counts"] == {"model_calls": 2, "repairs": 1}
    assert terminal["token_count"] == 83
    assert terminal["cost_usd"] == 0.024
    assert terminal["holds"] == {
        "bio/fixture-b": {
            "status": "pass",
            "reviewer_family": "fixture-cross-family",
            "date": "2026-07-19",
            "evidence_url": "https://example.test/reviews/bio-fixture-b",
            "active": True,
            "reason": "The reviewed sources conflict on the bounded factual claim.",
            "owner": "bio-preparation",
            "checked_evidence": [f"fixture packet review evidence; {failed_path} sha256={'e' * 64}"],
            "unblock_condition": "A stable authoritative source resolves the conflict.",
        }
    }
    assert set(terminal) == {
        "next_action",
        "paths",
        "hashes",
        "reason_codes",
        "counts",
        "holds",
        "token_count",
        "cost_usd",
    }

    before_third = deepcopy(run)
    with pytest.raises(bc.BoundedCompletionError) as third:
        bc.semantic_review_phase(
            run,
            review_protocol_identity=protocol,
            learner_source_sha256=final_source,
        )
    assert third.value.code == "SEMANTIC_REVIEW_BUDGET_EXHAUSTED"
    assert run == before_third


def test_non_bio_profile_forward_case_uses_the_same_pure_boundary(
    preparation_fixture: dict[str, Any],
) -> None:
    value = preparation_fixture
    admitted = packet.admit_packet(value["core"], limit=2)
    protocol = _protocol(value)
    source = packet.source_identity(admitted)
    run = bc.start_run(
        target=f"core/packet-{admitted['scope_sha256'][:16]}",
        run_id="f" * 32,
        review_protocol_identity=protocol,
        learner_source_sha256=source,
    )
    run = bc.complete_inspection(run, needs_build=False)
    run = bc.record_deterministic_verification(run, learner_source_sha256=source, passed=True)
    phase = bc.semantic_review_phase(
        run,
        review_protocol_identity=protocol,
        learner_source_sha256=source,
    )
    paths = packet.select_review_paths(admitted, phase=phase)
    pending = packet.pending_dispatch_receipt(admitted, run, phase=phase, paths=paths)
    run = bc.record_semantic_review(
        run,
        review_protocol_identity=protocol,
        learner_source_sha256=source,
        evidence_id="3" * 64,
        reported_disposition="PASS",
        dimension_scores=PASS_SCORES,
        prompt_bytes=10,
        schema_bytes=5,
    )

    assert [item["profile_id"] for item in admitted["scope"]] == ["core", "core"]
    assert pending["paths"] == [
        "evidence/core/fixture-c-plan.yaml",
        "evidence/core/fixture-d-plan.yaml",
    ]
    assert set(pending) == {"phase", "paths", "hashes", "reason_codes", "counts"}
    assert "provider" not in pending
    assert run["measurements"]["final_quality_disposition"] == "PUBLISHABLE"
    assert run["measurements"]["model_call_count"] == 1
