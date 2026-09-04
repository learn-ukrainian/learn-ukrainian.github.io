"""Synthetic real-slot fixture for the v4-real-slot-mechanism PR-A acceptance
proof: builds on top of ``_v4_synthetic_chain_fixture``'s own partial-
prerequisite-eligible root (15 eligible slots in ``standard_correct``),
issues a real, live-verified A3 private builder packet naming
``CANDIDATE_UNIT_IDS`` as builder-eligible, and constructs exactly one
genuine, gate-passing A7/A8 completion using ``v4_a7_private_ledger`` --
never a hand-authored shape standing in for the real mechanism.

Every text used here is synthetic, English-safe placeholder content, never
real Ukrainian corpus text and never anything resembling production
material -- this fixture proves the *mechanism*, not a real row. Production
stays untouched: nothing here ever writes outside ``tmp_path``.

Repair (PR #7662, repair 2): the split/near-duplicate and reconstruction-
gate comparison against reference text is now A3-owned
(``v4_a3_reference_check``) -- this fixture builds that receipt directly
(simulating the A3 role, which privately holds ``REFERENCE_TEXTS``) and
passes only the resulting text-free receipt into
``v4_a7_private_ledger.construct_completion``. A real A3 seal receipt and
private builder packet are issued here too (``build_sealed_receipt_and_
packet``), over a test-only salt, with ``CANDIDATE_UNIT_IDS`` registered as
members of a builder-eligible family and ``HELDOUT_SENTINEL_UNIT_ID``
registered as a member of that salt's held-out family -- so a tamper test
can prove an ineligible/held-out unit is refused before row construction.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

import _v4_synthetic_chain_fixture as base_fixture

from scripts.projects.open_model_data import v4_a3_builder_packet as packet
from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout
from scripts.projects.open_model_data import v4_a3_reference_check as reference_check
from scripts.projects.open_model_data import v4_a7_evidence_binder as evidence_binder
from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_a7_private_ledger as ledger
from scripts.projects.open_model_data import v4_a8_admission_assembly as a8

ROOT = Path(__file__).resolve().parents[3]

# A7's own private slot-unit-pick/lineage salt (construct_completion's own
# ``salt`` argument) -- unrelated to, and never derived from, A3's
# membership/packet salt below.
TEST_SALT = bytes.fromhex("ab" * 32)

# A3's private membership/packet salt for this fixture only -- never the
# real production salt. Chosen (see PR body / repair notes) so that
# ELIGIBLE_FAMILY_ID is builder-eligible and HELDOUT_FAMILY_ID is held out
# for the real 9-family production family registry.
A3_FIXTURE_SALT_HEX = "cd" * 32
A3_FIXTURE_SALT = bytes.fromhex(A3_FIXTURE_SALT_HEX)
ELIGIBLE_FAMILY_ID = "fam-db-textbooks-public"
HELDOUT_FAMILY_ID = "fam-db-external-articles"

TARGET_SLOT_ID = "v4p-standard-correct-001"
CANDIDATE_UNIT_IDS = ["synthetic-fixture-unit-alpha", "synthetic-fixture-unit-beta"]
HELDOUT_SENTINEL_UNIT_ID = "synthetic-fixture-unit-heldout-sentinel"

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


def build_sealed_receipt_and_packet(tmp_path: Path) -> dict[str, Any]:
    """A real, schema-conformant, freshly-sealed A3 receipt over the real
    9-family production registry (deep-copied, never the real private
    membership/salt), with ``CANDIDATE_UNIT_IDS`` added as members of
    ``ELIGIBLE_FAMILY_ID`` and ``HELDOUT_SENTINEL_UNIT_ID`` added as a
    member of ``HELDOUT_FAMILY_ID``, plus a real, live-issued private
    builder packet over it. Returns the paths a privileged caller (A7's
    private ledger) needs to independently re-verify the packet."""
    real_receipt = json.loads((ROOT / heldout.DEFAULT_RECEIPT.relative_to(ROOT)).read_text(encoding="utf-8"))
    receipt = copy.deepcopy(real_receipt)
    for family in receipt["source_family_registry"]["families"]:
        if family["family_id"] == ELIGIBLE_FAMILY_ID:
            family["member_source_unit_ids"] = sorted({*family["member_source_unit_ids"], *CANDIDATE_UNIT_IDS})
        if family["family_id"] == HELDOUT_FAMILY_ID:
            family["member_source_unit_ids"] = sorted({*family["member_source_unit_ids"], HELDOUT_SENTINEL_UNIT_ID})

    private_dir = tmp_path / "v4-a3-heldout-fixture"
    family_ids = sorted(f["family_id"] for f in receipt["source_family_registry"]["families"])

    os.environ[heldout.TEST_SALT_ENV_VAR] = A3_FIXTURE_SALT_HEX
    try:
        result = heldout.assign(A3_FIXTURE_SALT, family_ids)
        assert ELIGIBLE_FAMILY_ID in result["builder_eligible_family_ids"]
        assert HELDOUT_FAMILY_ID in result["heldout_family_ids"]
        summary = heldout.public_commitment_summary(A3_FIXTURE_SALT, result)
        receipt["heldout_partition_seal"]["assignment_algorithm"]["salt_commitment_sha256"] = summary["salt_commitment_sha256"]
        receipt["heldout_partition_seal"]["assignment_algorithm"]["assignment_commitment_sha256"] = summary["assignment_commitment_sha256"]
        heldout.write_private_artifact(private_dir / heldout.MEMBERSHIP_FILENAME, A3_FIXTURE_SALT, result, heldout.receipt_binding_sha256(receipt))
    finally:
        del os.environ[heldout.TEST_SALT_ENV_VAR]

    seal_receipt_path = tmp_path / "v4_a3_seal_receipt_fixture.json"
    seal_receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    packet.issue_packet(seal_receipt_path, private_dir, private_dir)

    return {"seal_receipt_path": seal_receipt_path, "membership_dir": private_dir, "packet_dir": private_dir, "seal_receipt": receipt}


def build_reference_check_receipt(row_text: str = ROW_TEXT, reference_texts: dict[str, str] | None = None) -> dict[str, Any]:
    """Simulates the A3 role: builds the text-free reference-check receipt
    from the (here, synthetic) private reference-text set -- the only thing
    A7's construction API ever receives from this comparison."""
    return reference_check.build_reference_check_receipt(row_text, dict(reference_texts if reference_texts is not None else REFERENCE_TEXTS), A3_FIXTURE_SALT)


def build_completion(
    tmp_root: Path,
    sealed: dict[str, Any],
    *,
    slot_id: str = TARGET_SLOT_ID,
    salt: bytes = TEST_SALT,
    candidate_unit_ids: list[str] | None = None,
    row_text: str = ROW_TEXT,
    reference_texts: dict[str, str] | None = None,
    author: dict[str, Any] | None = None,
    reviewer: dict[str, Any] | None = None,
    allow_synthetic_fixture: bool = True,
) -> dict[str, Any]:
    """Run the real, live ``v4_a7_private_ledger.construct_completion``
    pipeline -- every gate genuinely evaluated -- and return
    ``{"private_entry", "public_completion"}``. Defaults to the explicit
    ``allow_synthetic_fixture=True`` opt-in (this fixture has no real
    verifier-tool access) -- never the silent default."""
    row_content_sha256 = ledger.sha256_text(row_text)
    evidence_receipt = evidence_binder.build_synthetic_fixture_evidence_receipt(row_content_sha256, list(VESUM_IDS))
    reference_check_receipt = build_reference_check_receipt(row_text, reference_texts)
    return ledger.construct_completion(
        slot_id=slot_id,
        salt=salt,
        candidate_unit_ids=list(candidate_unit_ids or CANDIDATE_UNIT_IDS),
        a4_unit_commitments=a4_unit_commitments(tmp_root),
        seal_receipt_path=sealed["seal_receipt_path"],
        membership_dir=sealed["membership_dir"],
        packet_dir=sealed["packet_dir"],
        row_text=row_text,
        tier="silver",
        author=dict(author or AUTHOR),
        reviewer=dict(reviewer or REVIEWER),
        evidence_receipt=evidence_receipt,
        reference_check_receipt=reference_check_receipt,
        rights_receipt_id=RIGHTS_RECEIPT_ID,
        allow_synthetic_fixture=allow_synthetic_fixture,
    )


def build_real_slot_root(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Builds the synthetic partial-eligibility root (15 eligible slots in
    ``standard_correct``), issues a real A3 builder packet, constructs one
    genuine completion for ``TARGET_SLOT_ID``, writes the private ledger,
    and writes real A6/A7/A8 receipts (A9 untouched, still zero
    completions) via each stage's own live ``build_receipt``. Returns
    ``(tmp_root, info)``."""
    tmp_root = base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    admission_dir = tmp_root / "data/projects/open_model_data/admission"
    sealed = build_sealed_receipt_and_packet(tmp_path)

    from scripts.projects.open_model_data import v4_a6_blind_arena as a6

    a6_receipt = a6.build_receipt(tmp_root)
    a6.validate_receipt_independently(a6_receipt, tmp_root)
    (admission_dir / "dataset_v4_a6_blind_arena_receipt_v1.json").write_text(json.dumps(a6_receipt))

    completion = build_completion(tmp_root, sealed)
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
        "sealed": sealed,
    }
