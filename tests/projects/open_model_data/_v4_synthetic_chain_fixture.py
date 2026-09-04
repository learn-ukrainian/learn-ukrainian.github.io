"""Shared synthetic-chain fixture for V4 A6-A9 per-slot eligibility/
completion tests (PR #7654 repair cycle 2, Option A -- ``batch_state/
tasks/design-7654-partial-stage-evidence.result``).

Builds a self-consistent, on-disk root where exactly one manifest stratum's
A2 residual is resolved (``residual_ids: []``, ``coverage_state:
"resolved"``) and its manifest ``assignment_state`` is ``ASSIGNED`` --
every other stratum, and every other field of every other artifact, stays
real, unmutated production content. Every downstream artifact's binding
hash is patched to match the mutated A2's new bytes, using each artifact's
own real, unmutated structural content (never a fabricated field), so every
stage's own real validator runs live against this root -- never stubbed,
never monkeypatched.

A4's and A5's own ``a2_residuals_carried_forward``/``a4_residuals``
cross-checks are not root-parametric (pre-existing, out of this repair's
A6-A9 scope -- they load A2/A4 via a module-level path constant regardless
of the ``root`` argument passed to their own ``validate_receipt_
independently``). This fixture works within that constraint by never
mutating the *content* of any field those specific checks compare against
(only the binding *hashes* needed to keep the DAG's sha256 chain internally
consistent) -- which is exactly why the resulting root passes every real
A4/A5/A6/A7/A8/A9 validator without any of them being stubbed, even though
A4 and A5 themselves are not rebuilt from scratch here.
"""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import v4_a3_candidate_family_floor as floor
from scripts.projects.open_model_data import v4_a4_deterministic_extraction as a4
from scripts.projects.open_model_data import v4_a6_blind_arena as a6
from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_a8_admission_assembly as a8
from scripts.projects.open_model_data import v4_a9_evaluation_package as a9

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"


def _load(name: str) -> dict[str, Any]:
    return json.loads((ADMISSION / name).read_text(encoding="utf-8"))


REAL_A2 = _load("dataset_v4_a2_source_operation_admission_receipt_v1.json")
REAL_A4 = _load("dataset_v4_a4_deterministic_extraction_receipt_v1.json")
REAL_A5 = _load("dataset_v4_a5_evidence_enrichment_receipt_v1.json")
REAL_MANIFEST = _load("dataset_v4_pilot_slot_manifest_v1.json")
REAL_SEAL_RECEIPT = _load("dataset_v4_a3_heldout_source_family_seal_receipt_v1.json")


def _top_up_supporting_units_for_candidate_family_floor(supporting_ids: list[str]) -> list[str]:
    """Ensure ``supporting_ids`` names units from at least
    ``heldout_count + 1`` distinct families under the real seal receipt's
    own public registry (Invariant D1, PR #7662 repair 4 -- D1 is now
    enforced unconditionally at every A7 load-bearing path, including this
    fixture's own manifest ``ASSIGNED`` transition). Appends additional
    real, unmutated unit ids from other registered families,
    deterministically, only when the stratum's own real supporting ids do
    not already meet the floor -- never invents a fake unit id."""
    registry = REAL_SEAL_RECEIPT["source_family_registry"]
    heldout_count = REAL_SEAL_RECEIPT["heldout_partition_seal"]["heldout_count"]
    mapping = floor.unit_to_family_map(registry)
    supporting = list(supporting_ids)
    have_families = {mapping[u] for u in supporting if u in mapping}
    if len(have_families) >= heldout_count + 1:
        return supporting
    for family in sorted(registry["families"], key=lambda f: f["family_id"]):
        if family["family_id"] in have_families or not family["member_source_unit_ids"]:
            continue
        supporting.append(sorted(family["member_source_unit_ids"])[0])
        have_families.add(family["family_id"])
        if len(have_families) >= heldout_count + 1:
            break
    return supporting


def resolved_a2_receipt(resolved_stratum: str) -> dict[str, Any]:
    """A2 with exactly ``resolved_stratum``'s residual cleared (``residual_
    ids: []``, ``coverage_state: "resolved"``) -- every other stratum's
    real, unresolved residual stays untouched. ``resolved_stratum``'s own
    ``supporting_existing_source_unit_ids`` is topped up (real ids only) so
    the stratum's manifest ``ASSIGNED`` transition below meets Invariant D1."""
    receipt = copy.deepcopy(REAL_A2)
    resolved_ids: set[str] = set()
    for coverage in receipt["stratum_coverage_map"]:
        if coverage["stratum"] == resolved_stratum:
            resolved_ids.update(coverage["residual_ids"])
            coverage["residual_ids"] = []
            coverage["coverage_state"] = "resolved"
            coverage["supporting_existing_source_unit_ids"] = _top_up_supporting_units_for_candidate_family_floor(coverage["supporting_existing_source_unit_ids"])
    receipt["residuals"] = [r for r in receipt["residuals"] if r["residual_id"] not in resolved_ids]
    return receipt


def assigned_manifest(resolved_stratum: str) -> dict[str, Any]:
    """The frozen manifest with exactly ``resolved_stratum``'s
    ``assignment_state`` flipped to ``ASSIGNED``."""
    manifest = copy.deepcopy(REAL_MANIFEST)
    for series in manifest["slot_series"]:
        if series["stratum"] == resolved_stratum:
            series["assignment_state"] = "ASSIGNED"
    return manifest


def build_synthetic_chain_root(tmp_path: Path, *, resolved_stratum: str) -> Path:
    """Writes a full, self-consistent ``data/`` + ``scripts/`` tree under
    ``tmp_path`` with ``resolved_stratum`` prerequisite-eligible and every
    other stratum exactly as blocked as real production today. Returns
    ``tmp_path`` for chaining into ``a6.build_receipt(root=...)`` etc."""
    resolved_a2 = resolved_a2_receipt(resolved_stratum)
    manifest = assigned_manifest(resolved_stratum)

    synthetic_a4 = copy.deepcopy(REAL_A4)
    synthetic_a4["bindings"]["a2_source_operation_admission"]["sha256"] = a4.sha256_text(json.dumps(resolved_a2))

    synthetic_a5 = copy.deepcopy(REAL_A5)
    synthetic_a5["bindings"]["a2_source_operation_admission"]["sha256"] = a4.sha256_text(json.dumps(resolved_a2))
    synthetic_a5["bindings"]["a4_deterministic_extraction"]["sha256"] = a4.sha256_text(json.dumps(synthetic_a4))

    shutil.copytree(ROOT / "data/projects/open_model_data", tmp_path / "data/projects/open_model_data")
    admission_dir = tmp_path / "data/projects/open_model_data/admission"
    (admission_dir / "dataset_v4_a2_source_operation_admission_receipt_v1.json").write_text(json.dumps(resolved_a2))
    (admission_dir / "dataset_v4_a4_deterministic_extraction_receipt_v1.json").write_text(json.dumps(synthetic_a4))
    (admission_dir / "dataset_v4_a5_evidence_enrichment_receipt_v1.json").write_text(json.dumps(synthetic_a5))
    (admission_dir / "dataset_v4_pilot_slot_manifest_v1.json").write_text(json.dumps(manifest))
    shutil.copytree(ROOT / "scripts/projects/open_model_data", tmp_path / "scripts/projects/open_model_data", dirs_exist_ok=True)
    return tmp_path


def run_chain_a6_through_a9(tmp_root: Path) -> dict[str, dict[str, Any]]:
    """Builds and writes real A6, A7, A8, A9 receipts in dependency order
    using each stage's own live ``build_receipt(root=tmp_root)`` -- never a
    hand-authored shape. Each stage's own ``validate_receipt_independently``
    is called before the next stage consumes it, so a defect at any stage
    fails at that stage, not three stages downstream."""
    admission_dir = tmp_root / "data/projects/open_model_data/admission"

    a6_receipt = a6.build_receipt(tmp_root)
    a6.validate_receipt_independently(a6_receipt, tmp_root)
    (admission_dir / "dataset_v4_a6_blind_arena_receipt_v1.json").write_text(json.dumps(a6_receipt))

    a7_receipt = a7.build_receipt(tmp_root)
    a7.validate_receipt_independently(a7_receipt, tmp_root)
    (admission_dir / "dataset_v4_a7_original_row_factory_receipt_v1.json").write_text(json.dumps(a7_receipt))

    a8_receipt = a8.build_receipt(tmp_root)
    a8.validate_receipt_independently(a8_receipt, tmp_root)
    (admission_dir / "dataset_v4_a8_admission_assembly_receipt_v1.json").write_text(json.dumps(a8_receipt))

    a9_receipt = a9.build_receipt(tmp_root)
    a9.validate_receipt_independently(a9_receipt, tmp_root)
    (admission_dir / "dataset_v4_a9_evaluation_package_receipt_v1.json").write_text(json.dumps(a9_receipt))

    return {"a6": a6_receipt, "a7": a7_receipt, "a8": a8_receipt, "a9": a9_receipt}
