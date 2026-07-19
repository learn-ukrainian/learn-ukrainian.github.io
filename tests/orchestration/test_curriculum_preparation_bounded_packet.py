"""Fixture proofs for bounded curriculum-preparation packets."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Mapping, Sequence
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


def _target_fixture(
    track: str,
    slug: str,
    profile: str,
    family: str,
    manifest: str,
    preparation: str,
    cells: Sequence[tuple[str, str]],
) -> dict[str, Any]:
    return {
        "track": track,
        "slug": slug,
        "profile_id": profile,
        "profile_version": "1.1.0",
        "family": family,
        "manifest_sha256": manifest * 64,
        "preparation_identity": preparation * 64,
        "deterministic": {"passed": True, "reason_codes": []},
        "cells": [{"path": path, "source_sha256": digest * 64} for path, digest in cells],
    }


def _prior_pass(target: Mapping[str, Any], cell_index: int) -> dict[str, Any]:
    cell = target["cells"][cell_index]
    return {
        "target": f"{target['track']}/{target['slug']}",
        "profile_id": target["profile_id"],
        "profile_version": target["profile_version"],
        "family": target["family"],
        "manifest_sha256": target["manifest_sha256"],
        "path": cell["path"],
        "source_sha256": cell["source_sha256"],
        "preparation_identity": target["preparation_identity"],
        "verdict": "PASS",
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
            _target_fixture(
                "bio",
                "fixture-a",
                "bio",
                "seminar",
                "0",
                "1",
                [
                    ("evidence/bio/fixture-a-plan.yaml", "a"),
                    ("evidence/bio/fixture-a-dossier.md", "b"),
                ],
            ),
            _target_fixture(
                "bio",
                "fixture-b",
                "bio",
                "seminar",
                "0",
                "2",
                [
                    ("evidence/bio/fixture-b-plan.yaml", "c"),
                    ("evidence/bio/fixture-b-dossier.md", "d"),
                ],
            ),
        ],
        "core": [
            _target_fixture(
                "core",
                "fixture-c",
                "core",
                "core-module",
                "5",
                "3",
                [("evidence/core/fixture-c-plan.yaml", "f")],
            ),
            _target_fixture(
                "core",
                "fixture-d",
                "core",
                "core-module",
                "5",
                "4",
                [("evidence/core/fixture-d-plan.yaml", "9")],
            ),
        ],
    }
    value["prior_passes"] = [
        _prior_pass(value["bio"][0], 0),
        _prior_pass(value["bio"][0], 1),
        _prior_pass(value["bio"][1], 0),
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
    assert [cell["path"] for cell in admitted["cells"] if not cell["reused_pass"]] == [
        "evidence/bio/fixture-b-dossier.md"
    ]

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


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("profile_id", "bio-v2"),
        ("profile_version", "2.0.0"),
        ("family", "seminar-v2"),
        ("manifest_sha256", "6" * 64),
    ],
)
def test_profile_and_manifest_drift_invalidate_exact_pass_reuse(
    preparation_fixture: dict[str, Any],
    field: str,
    replacement: str,
) -> None:
    original = _admit_bio(preparation_fixture)
    drifted_targets = deepcopy(preparation_fixture["bio"])
    for target in drifted_targets:
        target[field] = replacement

    drifted = packet.admit_packet(
        drifted_targets,
        limit=2,
        prior_passes=preparation_fixture["prior_passes"],
    )

    assert drifted["counts"]["reused_pass_cells"] == 0
    assert packet.source_identity(drifted) != packet.source_identity(original)


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

    initial_pending = packet.pending_dispatch_receipt(admitted, run)
    assert initial_pending["phase"] == "INITIAL"
    assert initial_pending["scope_sha256"] == admitted["scope_sha256"]
    assert initial_pending["reviewed_source_identity"] == initial_source
    assert initial_pending["protocol_identity_sha256"] == protocol["identity_sha256"]
    assert initial_pending["paths"] == ["evidence/bio/fixture-b-dossier.md"]
    assert initial_pending["hashes"] == [
        {
            "path": "evidence/bio/fixture-b-dossier.md",
            "source_sha256": "d" * 64,
            "preparation_identity": "2" * 64,
        }
    ]
    assert initial_pending["reason_codes"] == ["INITIAL_NON_REUSED_ONLY"]
    assert initial_pending["counts"] == {"model_calls": 1, "repairs": 0}
    assert run["measurements"]["model_call_count"] == 0

    failed_path = initial_pending["paths"][0]
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
    assert len(blockers) == len(initial_pending["paths"]) == 1

    with pytest.raises(packet.PreparationPacketError) as wrong_phase:
        packet.pending_dispatch_receipt(admitted, run)
    assert wrong_phase.value.code == "STATE_INVALID"

    forged = deepcopy(admitted)
    forged["cells"][0]["source_sha256"] = "4" * 64
    forged_source = packet.source_identity(forged)
    forged_run = bc.record_consolidated_repair(run, learner_source_sha256=forged_source)
    forged_run = bc.record_deterministic_verification(
        forged_run,
        learner_source_sha256=forged_source,
        passed=True,
    )
    with pytest.raises(packet.PreparationPacketError) as forged_change:
        packet.pending_dispatch_receipt(
            forged,
            forged_run,
            initial_receipt=initial_pending,
            blocker_paths=[failed_path],
        )
    assert forged_change.value.code == "INITIAL_RECEIPT_IDENTITY_INVALID"

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

    before_singleton = deepcopy(run)
    with pytest.raises(packet.PreparationPacketError) as singleton:
        packet.pending_dispatch_receipt(
            repaired,
            run,
            initial_receipt=initial_pending,
            blocker_paths=["evidence/bio/fixture-a-dossier.md"],
        )
    assert singleton.value.code == "BLOCKER_SCOPE_INVALID"
    assert run == before_singleton

    final_pending = packet.pending_dispatch_receipt(
        repaired,
        run,
        initial_receipt=initial_pending,
        blocker_paths=[failed_path],
    )
    assert final_pending["phase"] == "FINAL"
    assert final_pending["paths"] == [failed_path]
    assert final_pending["hashes"][0]["source_sha256"] == "e" * 64
    assert final_pending["reason_codes"] == ["FINAL_HASH_CHANGED_BLOCKERS_ONLY"]
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

    stale_final = deepcopy(final_pending)
    stale_final["hashes"][0]["source_sha256"] = "d" * 64
    with pytest.raises(packet.PreparationPacketError) as stale_hold:
        packet.terminal_hold_receipt(
            repaired,
            run,
            final_receipt=stale_final,
            blockers=blockers,
            date="2026-07-19",
            evidence_url="https://example.test/reviews/stale",
        )
    assert stale_hold.value.code == "PENDING_RECEIPT_STALE"

    remapped_blockers = deepcopy(blockers)
    remapped_blockers[0]["path"] = "evidence/bio/fixture-a-dossier.md"
    with pytest.raises(packet.PreparationPacketError) as remapped_hold:
        packet.terminal_hold_receipt(
            repaired,
            run,
            final_receipt=final_pending,
            still_failing_paths=["evidence/bio/fixture-a-dossier.md"],
            blockers=remapped_blockers,
            date="2026-07-19",
            evidence_url="https://example.test/reviews/remapped",
        )
    assert remapped_hold.value.code == "HOLD_SCOPE_INVALID"

    terminal = packet.terminal_hold_receipt(
        repaired,
        run,
        final_receipt=final_pending,
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
    pending = packet.pending_dispatch_receipt(admitted, run)
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
    assert set(pending) == {
        "phase",
        "scope_sha256",
        "reviewed_source_identity",
        "protocol_identity_sha256",
        "paths",
        "hashes",
        "reason_codes",
        "counts",
    }
    assert "provider" not in pending
    assert run["measurements"]["final_quality_disposition"] == "PUBLISHABLE"
    assert run["measurements"]["model_call_count"] == 1
