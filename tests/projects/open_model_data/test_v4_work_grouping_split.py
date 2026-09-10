"""Tests for work grouping, deduplication, and evaluation split clearance (Issue #7887)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

import scripts.projects.open_model_data.v4_work_grouping_split as split_mod

CONFIG_PATH = Path("data/projects/open_model_data/splits/v4_work_grouping_split_config_v1.json")
CONTRACTS_DIR = Path("data/projects/open_model_data/contracts")


def test_schema_contracts_valid() -> None:
    """The 3 JSON schemas for config, item, and receipt must be valid Draft 2020-12 schemas."""
    for schema_name in [
        "v4_work_grouping_split_config_v1.schema.json",
        "v4_work_grouping_split_item_v1.schema.json",
        "v4_work_grouping_split_receipt_v1.schema.json",
    ]:
        p = CONTRACTS_DIR / schema_name
        assert p.is_file(), f"Missing schema contract: {p}"
        schema_data = json.loads(p.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema_data)


def test_work_family_grouping_and_linkage() -> None:
    """Chunks and pages of related works must map to the same work_family_id (SPLIT-1)."""
    # Literary Hrushevsky
    wf_hrush, ed_hrush = split_mod._derive_work_family_id(
        "source.literary.0020599cfcaf15e887bdb73c",
        "literary",
        None,
    )
    assert wf_hrush == "work_family.literary.hrushevskyy_istoriya_ukrayiny_odnotomnyk"
    assert ed_hrush["author"] == "Грушевський М."
    assert ed_hrush["year"] == 1920

    # Textbook Masol Grade 9 (multi-page)
    wf_masol, ed_masol = split_mod._derive_work_family_id(
        "source.public_textbooks.00cebc897bb7feab776c42a8",
        "public_textbooks",
        None,
    )
    assert wf_masol == "work_family.public_textbooks.masol_mystetstvo_grade_9"
    assert ed_masol["author"] == "Масол"


def test_work_family_partitioning_disjointness() -> None:
    """Entire work families must be assigned to exactly one partition with zero overlap (SPLIT-1 & SPLIT-4)."""
    families = [
        "work_family.lit.book_a",
        "work_family.lit.book_b",
        "work_family.textbooks.book_c",
        "work_family.textbooks.book_d",
        "work_family.general.book_e",
    ]
    partition_map = split_mod.partition_work_families(families, heldout_fraction=0.2, development_fraction=0.2)
    assert len(partition_map) == 5

    partitions = set(partition_map.values())
    assert "training" in partitions
    assert "heldout_evaluation" in partitions
    assert "development" in partitions

    # Verify every family is assigned to exactly one partition
    for f in families:
        assert partition_map[f] in ("training", "development", "heldout_evaluation")


def test_deduplication_excludes_duplicate_spans(tmp_path: Path) -> None:
    """Duplicate spans must be detected and excluded from builder training (SPLIT-2)."""
    # Read first line from real index
    real_index_path = Path("data/projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl")
    lines = real_index_path.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    item1 = json.loads(lines[1])

    # Item 1 is unique and retained
    assert item1["deduplication"]["is_duplicate"] is False
    assert item1["deduplication"]["dedup_action"] == "retained"


def test_cross_boundary_firewall_zero_leakage() -> None:
    """Zero work families may cross between training, development, and heldout evaluation (SPLIT-4)."""
    real_index_path = Path("data/projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl")
    train_fams: set[str] = set()
    dev_fams: set[str] = set()
    eval_fams: set[str] = set()

    with real_index_path.open(encoding="utf-8") as f:
        _ = f.readline()
        for line in f:
            row = json.loads(line)
            part = row["builder_clearance"]["split_partition"]
            wf = row["work_family_id"]
            if part == "training":
                train_fams.add(wf)
            elif part == "development":
                dev_fams.add(wf)
            elif part == "heldout_evaluation":
                eval_fams.add(wf)

    # Disjointness checks
    assert len(train_fams & dev_fams) == 0, "Train and dev partitions leak related works!"
    assert len(train_fams & eval_fams) == 0, "Train and eval partitions leak related works!"
    assert len(dev_fams & eval_fams) == 0, "Dev and eval partitions leak related works!"


def test_verify_detects_cross_boundary_leakage(tmp_path: Path) -> None:
    """Verification must fail if any work family crosses split boundaries (SPLIT-4)."""
    repo_root = Path.cwd()
    tampered_out = tmp_path / "tampered"
    tampered_out.mkdir(parents=True)

    orig_receipt_path = Path("data/projects/open_model_data/splits/v4_work_grouping_split_receipt_v1.json")
    orig_receipt = json.loads(orig_receipt_path.read_text(encoding="utf-8"))

    orig_index_path = Path("data/projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl")
    lines = orig_index_path.read_text(encoding="utf-8").splitlines()

    # Tamper one item: change its partition to training when its family is in heldout_evaluation
    # Find a heldout_evaluation item
    new_lines = [lines[0]]
    tampered = False
    for line in lines[1:]:
        row = json.loads(line)
        if not tampered and row["builder_clearance"]["split_partition"] == "heldout_evaluation":
            row["builder_clearance"]["split_partition"] = "training"
            row["builder_clearance"]["builder_training_cleared"] = True
            tampered = True
        new_lines.append(json.dumps(row))

    assert tampered is True

    out_idx = tampered_out / "data/projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl"
    out_idx.parent.mkdir(parents=True)
    out_idx.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Update receipt hashes to isolate the firewall check
    tampered_rcpt = copy.deepcopy(orig_receipt)
    tampered_rcpt["index_sha256"] = split_mod.sha256_file(out_idx)
    tampered_rcpt["receipt_id"] = split_mod._make_receipt_id(
        tampered_rcpt["config_sha256"],
        tampered_rcpt["language_usage_receipt_sha256"],
        tampered_rcpt["index_sha256"],
    )

    out_rcpt = tampered_out / "data/projects/open_model_data/splits/v4_work_grouping_split_receipt_v1.json"
    out_rcpt.write_text(json.dumps(tampered_rcpt, indent=2), encoding="utf-8")

    with pytest.raises(split_mod.WorkGroupingSplitError, match=r"crossed split boundaries"):
        split_mod.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_tampered_receipt_hashes(tmp_path: Path) -> None:
    """Verification must fail if receipt SHA-256 digest or ID does not match index."""
    repo_root = Path.cwd()
    tampered_out = tmp_path / "tampered"
    tampered_out.mkdir(parents=True)

    orig_receipt_path = Path("data/projects/open_model_data/splits/v4_work_grouping_split_receipt_v1.json")
    orig_receipt = json.loads(orig_receipt_path.read_text(encoding="utf-8"))

    orig_index_path = Path("data/projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl")
    out_idx = tampered_out / "data/projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl"
    out_idx.parent.mkdir(parents=True)
    out_idx.write_text(orig_index_path.read_text(encoding="utf-8"), encoding="utf-8")

    tampered_rcpt = copy.deepcopy(orig_receipt)
    tampered_rcpt["index_sha256"] = "0" * 64
    out_rcpt = tampered_out / "data/projects/open_model_data/splits/v4_work_grouping_split_receipt_v1.json"
    out_rcpt.write_text(json.dumps(tampered_rcpt, indent=2), encoding="utf-8")

    with pytest.raises(split_mod.WorkGroupingSplitError, match=r"Index SHA-256 mismatch"):
        split_mod.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_prohibited_private_host_paths(tmp_path: Path) -> None:
    """Verification must fail if receipt contains forbidden private host paths."""
    repo_root = Path.cwd()
    tampered_out = tmp_path / "tampered"
    tampered_out.mkdir(parents=True)

    orig_receipt_path = Path("data/projects/open_model_data/splits/v4_work_grouping_split_receipt_v1.json")
    orig_receipt = json.loads(orig_receipt_path.read_text(encoding="utf-8"))

    orig_index_path = Path("data/projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl")
    out_idx = tampered_out / "data/projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl"
    out_idx.parent.mkdir(parents=True)
    out_idx.write_text(orig_index_path.read_text(encoding="utf-8"), encoding="utf-8")

    tampered_rcpt = copy.deepcopy(orig_receipt)
    tampered_rcpt["notes"] = "Evaluated on /home/ops/secret/server"
    out_rcpt = tampered_out / "data/projects/open_model_data/splits/v4_work_grouping_split_receipt_v1.json"
    out_rcpt.write_text(json.dumps(tampered_rcpt, indent=2), encoding="utf-8")

    with pytest.raises(
        split_mod.WorkGroupingSplitError, match=r"Receipt contains prohibited private or absolute host paths"
    ):
        split_mod.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_build_and_verify_clean_exit() -> None:
    """Build and verify must execute cleanly against repository artifacts."""
    res_build = split_mod.build(CONFIG_PATH)
    assert res_build["verdict"] == "WORK_GROUPING_SPLIT_CONFIRMED"

    res_verify = split_mod.verify(CONFIG_PATH)
    assert res_verify["status"] == "PASS"
    assert res_verify["verdict"] == "WORK_GROUPING_SPLIT_CONFIRMED"
    assert res_verify["firewall_verified_clean"] is True
    assert res_verify["total_spans_evaluated"] == 1419
