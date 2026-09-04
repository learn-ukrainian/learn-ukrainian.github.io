"""Synthetic real-slot fixture for the v4-real-slot-mechanism PR-A acceptance
proof: builds on top of ``_v4_synthetic_chain_fixture``'s own partial-
prerequisite-eligible root (15 eligible slots in ``standard_correct``) and
constructs exactly one genuine, gate-passing A7/A8 completion using
``v4_a7_private_ledger`` -- never a hand-authored shape standing in for the
real mechanism.

Every text used here is synthetic, English-safe placeholder content, never
real Ukrainian corpus text and never anything resembling production
material -- this fixture proves the *mechanism*, not a real row. Production
stays untouched: nothing here ever writes outside ``tmp_path``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import _v4_synthetic_chain_fixture as base_fixture

from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_a7_private_ledger as ledger
from scripts.projects.open_model_data import v4_a8_admission_assembly as a8

TEST_SALT = bytes.fromhex("ab" * 32)
TARGET_SLOT_ID = "v4p-standard-correct-001"
CANDIDATE_UNIT_IDS = ["synthetic-fixture-unit-alpha", "synthetic-fixture-unit-beta"]

ROW_TEXT = "This is a synthetic, independently authored placeholder sentence used only to exercise the V4 A7 mechanism."
REFERENCE_TEXTS = {
    "synthetic-fixture-unit-alpha": "A completely different placeholder passage about an unrelated everyday topic entirely.",
    "synthetic-fixture-unit-beta": "Another unrelated placeholder passage, deliberately dissimilar in wording and structure.",
}
VESUM_IDS = ["vesum:lemma-synthetic-example-001", "sources:fixture-attestation-001"]
RIGHTS_RECEIPT_ID = "license.content.cc-by-sa-4.0@0000000000000000000000000000000000000000000000000000000000000000"

AUTHOR = {
    "model_family": "fixture-author-family",
    "exact_model": "fixture-author-model-v1",
    "harness": "fixture-harness",
    "session_id": "fixture-author-session-001",
    "prompt_sha256": "1" * 64,
    "packet_sha256": "2" * 64,
    "verification_tool_ids": ["fixture-tool-1"],
}
REVIEWER = {
    "model_family": "fixture-reviewer-family",
    "exact_model": "fixture-reviewer-model-v1",
    "harness": "fixture-harness",
    "session_id": "fixture-reviewer-session-001",
    "prompt_sha256": "3" * 64,
    "packet_sha256": "4" * 64,
    "verdict": "PASS",
    "rubric_sha256": "5" * 64,
    "verification_tool_ids": ["fixture-tool-2"],
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def a4_unit_commitments(tmp_root: Path) -> list[str]:
    a4_receipt = _load(tmp_root / "data/projects/open_model_data/admission/dataset_v4_a4_deterministic_extraction_receipt_v1.json")
    return a4_receipt["builder_packet_consumption"]["unit_commitments"]


def build_completion(
    tmp_root: Path,
    *,
    slot_id: str = TARGET_SLOT_ID,
    salt: bytes = TEST_SALT,
    candidate_unit_ids: list[str] | None = None,
    row_text: str = ROW_TEXT,
    reference_texts: dict[str, str] | None = None,
    author: dict[str, Any] | None = None,
    reviewer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the real, live ``v4_a7_private_ledger.construct_completion``
    pipeline -- every gate genuinely evaluated -- and return
    ``{"private_entry", "public_completion"}``."""
    return ledger.construct_completion(
        slot_id=slot_id,
        salt=salt,
        candidate_unit_ids=list(candidate_unit_ids or CANDIDATE_UNIT_IDS),
        a4_unit_commitments=a4_unit_commitments(tmp_root),
        row_text=row_text,
        tier="silver",
        author=dict(author or AUTHOR),
        reviewer=dict(reviewer or REVIEWER),
        vesum_ids=list(VESUM_IDS),
        reference_texts=dict(reference_texts if reference_texts is not None else REFERENCE_TEXTS),
        rights_receipt_id=RIGHTS_RECEIPT_ID,
    )


def build_real_slot_root(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Builds the synthetic partial-eligibility root (15 eligible slots in
    ``standard_correct``), constructs one genuine completion for
    ``TARGET_SLOT_ID``, writes the private ledger, and writes real A6/A7/A8
    receipts (A9 untouched, still zero completions) via each stage's own
    live ``build_receipt``. Returns ``(tmp_root, completion)``."""
    tmp_root = base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    admission_dir = tmp_root / "data/projects/open_model_data/admission"

    from scripts.projects.open_model_data import v4_a6_blind_arena as a6

    a6_receipt = a6.build_receipt(tmp_root)
    a6.validate_receipt_independently(a6_receipt, tmp_root)
    (admission_dir / "dataset_v4_a6_blind_arena_receipt_v1.json").write_text(json.dumps(a6_receipt))

    completion = build_completion(tmp_root)
    public_completion = completion["public_completion"]

    ledger_path = tmp_path / "batch_state/open-model-data/v4-a7-factory/v4_a7_private_ledger_v1.json"
    ledger.write_ledger({public_completion["slot_id"]: completion["private_entry"]}, ledger_path)

    a7_receipt = a7.build_receipt(tmp_root, a7_completions=[public_completion])
    a7.validate_receipt_independently(a7_receipt, tmp_root)
    (admission_dir / "dataset_v4_a7_original_row_factory_receipt_v1.json").write_text(json.dumps(a7_receipt))

    a8_completion = {
        "stage": "A8",
        "slot_id": public_completion["slot_id"],
        "row_id": public_completion["row_id"],
        "row_content_sha256": public_completion["row_content_sha256"],
    }
    a8_receipt = a8.build_receipt(tmp_root, a8_completions=[a8_completion])
    a8.validate_receipt_independently(a8_receipt, tmp_root)
    (admission_dir / "dataset_v4_a8_admission_assembly_receipt_v1.json").write_text(json.dumps(a8_receipt))

    from scripts.projects.open_model_data import v4_a9_evaluation_package as a9

    a9_receipt = a9.build_receipt(tmp_root)
    a9.validate_receipt_independently(a9_receipt, tmp_root)
    (admission_dir / "dataset_v4_a9_evaluation_package_receipt_v1.json").write_text(json.dumps(a9_receipt))

    return tmp_root, {
        "completion": completion,
        "a6_receipt": a6_receipt,
        "a7_receipt": a7_receipt,
        "a8_receipt": a8_receipt,
        "a9_receipt": a9_receipt,
        "ledger_path": ledger_path,
    }
