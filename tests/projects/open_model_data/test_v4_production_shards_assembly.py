"""Unit, contract, and regression tests for Phase 3.7 Production Shards Assembly (#8011)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.v4_production_shards_assembly import (
    ANTI_HYPERPURIST_DPO_QUOTA,
    ANTI_SOVIET_DPO_QUOTA,
    CORRECT_SFT_QUOTA,
    DEFAULT_HELDOUT_SUITE,
    DPO_PAIR_SCHEMA_PATH,
    DPO_RECORDS_PER_SHARD,
    DPO_SHARDS_COUNT,
    FORMAT_TARGETS,
    HELDOUT_CORRECT,
    HELDOUT_PRESERVE,
    HELDOUT_TOTAL,
    HISTORICAL_ARCHIVE_DIR,
    PRESERVE_SFT_QUOTA,
    RECEIPT_SCHEMA_PATH,
    SFT_RECORDS_PER_SHARD,
    SFT_SHARDS_COUNT,
    TOTAL_DPO_QUOTA,
    TOTAL_SFT_QUOTA,
    TRAJECTORY_SCHEMA_PATH,
    assert_no_private_host_paths,
    compute_heldout_minhash_similarity,
    load_jsonl,
    sha256_file,
    verify_production_release,
)
from scripts.projects.open_model_data.v4_production_shards_assembly import (
    HISTORICAL_ARCHIVE_DIR as DEFAULT_OUTPUT_DIR,
)


@pytest.fixture(scope="module")
def receipt_data() -> dict[str, Any]:
    receipt_path = DEFAULT_OUTPUT_DIR / "production_release_receipt.json"
    assert receipt_path.exists(), f"Receipt file missing: {receipt_path}"
    with receipt_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def sft_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for shard_idx in range(1, SFT_SHARDS_COUNT + 1):
        shard_path = DEFAULT_OUTPUT_DIR / "sft" / f"sft_shard_{shard_idx:03d}_of_{SFT_SHARDS_COUNT:03d}.jsonl"
        assert shard_path.exists(), f"SFT shard missing: {shard_path}"
        shard_recs = load_jsonl(shard_path)
        assert len(shard_recs) == SFT_RECORDS_PER_SHARD, (
            f"Shard {shard_path.name} has {len(shard_recs)} records, expected {SFT_RECORDS_PER_SHARD}"
        )
        records.extend(shard_recs)
    return records


@pytest.fixture(scope="module")
def dpo_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for shard_idx in range(1, DPO_SHARDS_COUNT + 1):
        shard_path = DEFAULT_OUTPUT_DIR / "dpo" / f"dpo_shard_{shard_idx:03d}_of_{DPO_SHARDS_COUNT:03d}.jsonl"
        assert shard_path.exists(), f"DPO shard missing: {shard_path}"
        shard_recs = load_jsonl(shard_path)
        assert len(shard_recs) == DPO_RECORDS_PER_SHARD, (
            f"Shard {shard_path.name} has {len(shard_recs)} records, expected {DPO_RECORDS_PER_SHARD}"
        )
        records.extend(shard_recs)
    return records


def test_production_release_files_exist() -> None:
    """Verify all 6 SFT shards, 3 DPO shards, receipt, and detached SHA exist."""
    assert DEFAULT_OUTPUT_DIR.exists(), f"Release dir {DEFAULT_OUTPUT_DIR} does not exist"
    receipt_path = DEFAULT_OUTPUT_DIR / "production_release_receipt.json"
    assert receipt_path.exists(), "production_release_receipt.json missing"
    assert receipt_path.with_suffix(".json.sha256").exists(), "detached .sha256 missing"

    for shard_idx in range(1, SFT_SHARDS_COUNT + 1):
        shard_path = DEFAULT_OUTPUT_DIR / "sft" / f"sft_shard_{shard_idx:03d}_of_{SFT_SHARDS_COUNT:03d}.jsonl"
        assert shard_path.exists(), f"SFT shard {shard_path} missing"

    for shard_idx in range(1, DPO_SHARDS_COUNT + 1):
        shard_path = DEFAULT_OUTPUT_DIR / "dpo" / f"dpo_shard_{shard_idx:03d}_of_{DPO_SHARDS_COUNT:03d}.jsonl"
        assert shard_path.exists(), f"DPO shard {shard_path} missing"


def test_production_receipt_schema_valid(receipt_data: dict[str, Any]) -> None:
    """Validate production_release_receipt.json against its Draft2020-12 schema."""
    assert RECEIPT_SCHEMA_PATH.exists(), f"Receipt schema missing: {RECEIPT_SCHEMA_PATH}"
    with RECEIPT_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(receipt_data))
    assert not errors, f"Receipt schema validation errors: {[e.message for e in errors]}"


def test_production_receipt_hashes_match(receipt_data: dict[str, Any]) -> None:
    """Verify detached sha256 matches receipt and shard digests match on-disk files."""
    receipt_path = DEFAULT_OUTPUT_DIR / "production_release_receipt.json"
    computed_receipt_sha = sha256_file(receipt_path)
    detached_sha = receipt_path.with_suffix(".json.sha256").read_text(encoding="utf-8").strip()
    assert detached_sha == computed_receipt_sha, "Detached SHA-256 does not match receipt file digest"

    files_manifest = receipt_data["files"]

    # Verify SFT shards in receipt
    for shard_idx in range(1, SFT_SHARDS_COUNT + 1):
        fname = f"sft_shard_{shard_idx:03d}_of_{SFT_SHARDS_COUNT:03d}.jsonl"
        assert fname in files_manifest, f"Missing file entry in receipt: {fname}"
        entry = files_manifest[fname]
        file_path = DEFAULT_OUTPUT_DIR / "sft" / fname
        assert file_path.exists(), f"SFT shard {file_path} does not exist"
        assert file_path.stat().st_size == entry["bytes"], f"Byte count mismatch for {fname}"
        assert sha256_file(file_path) == entry["sha256"], f"SHA256 mismatch for {fname}"

    # Verify DPO shards in receipt
    for shard_idx in range(1, DPO_SHARDS_COUNT + 1):
        fname = f"dpo_shard_{shard_idx:03d}_of_{DPO_SHARDS_COUNT:03d}.jsonl"
        assert fname in files_manifest, f"Missing file entry in receipt: {fname}"
        entry = files_manifest[fname]
        file_path = DEFAULT_OUTPUT_DIR / "dpo" / fname
        assert file_path.exists(), f"DPO shard {file_path} does not exist"
        assert file_path.stat().st_size == entry["bytes"], f"Byte count mismatch for {fname}"
        assert sha256_file(file_path) == entry["sha256"], f"SHA256 mismatch for {fname}"


def test_sft_shards_exact_quotas_and_distribution(sft_records: list[dict[str, Any]]) -> None:
    """Verify exact 6,000 SFT trajectories, 70/30 CORRECT/PRESERVE split, and format distribution."""
    assert len(sft_records) == TOTAL_SFT_QUOTA, f"Expected {TOTAL_SFT_QUOTA} SFT records, got {len(sft_records)}"

    # Check uniqueness of IDs
    ids = [r["trajectory_id"] for r in sft_records]
    assert len(ids) == len(set(ids)), f"Duplicate IDs found in SFT shards: {len(ids) - len(set(ids))} duplicates"

    # Check CORRECT vs PRESERVE
    correct = [r for r in sft_records if r.get("is_calque_or_russianism", True)]
    preserve = [r for r in sft_records if not r.get("is_calque_or_russianism", False)]
    assert len(correct) == CORRECT_SFT_QUOTA, f"Expected {CORRECT_SFT_QUOTA} CORRECT, got {len(correct)}"
    assert len(preserve) == PRESERVE_SFT_QUOTA, f"Expected {PRESERVE_SFT_QUOTA} PRESERVE, got {len(preserve)}"
    assert (len(preserve) / len(sft_records)) == pytest.approx(0.30, abs=1e-4)

    # Check format breakdown
    fmt_counts = {fmt: 0 for fmt in FORMAT_TARGETS}
    for r in sft_records:
        fmt = r.get("format_type", "")
        assert fmt in fmt_counts, f"Unexpected format_type: {fmt}"
        fmt_counts[fmt] += 1

    for fmt, expected in FORMAT_TARGETS.items():
        assert fmt_counts[fmt] == expected, f"Format {fmt} expected {expected}, got {fmt_counts[fmt]}"


def test_sft_shards_schema_valid(sft_records: list[dict[str, Any]]) -> None:
    """Validate all SFT records against v1_decolonization_trajectory.schema.json."""
    assert TRAJECTORY_SCHEMA_PATH.exists(), f"Trajectory schema missing: {TRAJECTORY_SCHEMA_PATH}"
    with TRAJECTORY_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)

    # Validate sample thoroughly across shards
    for idx, r in enumerate(sft_records):
        if idx < 100 or idx % 50 == 0:
            errors = list(validator.iter_errors(r))
            assert not errors, (
                f"Record {r.get('trajectory_id', idx)} failed schema validation: {[e.message for e in errors]}"
            )


def test_dpo_shards_exact_quotas_and_properties(dpo_records: list[dict[str, Any]]) -> None:
    """Verify exact 3,000 DPO pairs, 2,100 anti-Soviet + 900 anti-hyperpurist, and length matching."""
    assert len(dpo_records) == TOTAL_DPO_QUOTA, f"Expected {TOTAL_DPO_QUOTA} DPO records, got {len(dpo_records)}"

    # Check uniqueness of IDs
    pair_ids = [r["pair_id"] for r in dpo_records]
    assert len(pair_ids) == len(set(pair_ids)), (
        f"Duplicate pair_ids found: {len(pair_ids) - len(set(pair_ids))} duplicates"
    )

    anti_soviet = [
        r for r in dpo_records if r.get("metadata", {}).get("rejected_flaw") != "unvetted_purism_hallucination"
    ]
    anti_hyperpurist = [
        r for r in dpo_records if r.get("metadata", {}).get("rejected_flaw") == "unvetted_purism_hallucination"
    ]

    assert len(anti_soviet) == ANTI_SOVIET_DPO_QUOTA, (
        f"Expected {ANTI_SOVIET_DPO_QUOTA} anti_soviet pairs, got {len(anti_soviet)}"
    )
    assert len(anti_hyperpurist) == ANTI_HYPERPURIST_DPO_QUOTA, (
        f"Expected {ANTI_HYPERPURIST_DPO_QUOTA} anti_hyperpurist pairs, got {len(anti_hyperpurist)}"
    )

    valid_calque_flaws = {
        "soviet_lexicography_acceptance",
        "mechanical_wordnet_synset",
        "lack_of_morphemic_reasoning",
    }
    for r in anti_soviet:
        flaw = r.get("metadata", {}).get("rejected_flaw")
        assert flaw in valid_calque_flaws, f"Invalid calque flaw: {flaw}"

    # Length ratio matching verification: |len(c) - len(r)| / max(len(c), len(r)) <= 10.0%
    for r in dpo_records:
        chosen_len = len(r["chosen"])
        rejected_len = len(r["rejected"])
        max_len = max(chosen_len, rejected_len)
        diff_ratio = abs(chosen_len - rejected_len) / max_len if max_len > 0 else 0.0
        assert diff_ratio <= 0.1001, (
            f"DPO pair {r['pair_id']} length ratio difference {diff_ratio:.4f} > 10.0% "
            f"(chosen: {chosen_len}, rejected: {rejected_len})"
        )


def test_dpo_shards_schema_valid(dpo_records: list[dict[str, Any]]) -> None:
    """Validate DPO records against v1_decolonization_dpo_pair.schema.json."""
    assert DPO_PAIR_SCHEMA_PATH.exists(), f"DPO pair schema missing: {DPO_PAIR_SCHEMA_PATH}"
    with DPO_PAIR_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)

    for idx, r in enumerate(dpo_records):
        if idx < 100 or idx % 50 == 0:
            errors = list(validator.iter_errors(r))
            assert not errors, f"DPO pair {r.get('pair_id', idx)} failed schema: {[e.message for e in errors]}"


def test_partition_firewall_zero_leakage(
    sft_records: list[dict[str, Any]],
    dpo_records: list[dict[str, Any]],
) -> None:
    """Verify partition firewall: zero overlap with 400 held-out CORRECT targets or held-out IDs."""
    assert DEFAULT_HELDOUT_SUITE.exists(), f"Held-out suite missing: {DEFAULT_HELDOUT_SUITE}"
    heldout_items = load_jsonl(DEFAULT_HELDOUT_SUITE)
    assert len(heldout_items) == HELDOUT_TOTAL, f"Expected {HELDOUT_TOTAL} heldout items, got {len(heldout_items)}"

    heldout_preserve = [h for h in heldout_items if h.get("case_type") == "PRESERVE"]
    heldout_correct = [h for h in heldout_items if h.get("case_type") == "CORRECT"]
    assert len(heldout_preserve) == HELDOUT_PRESERVE, f"Expected {HELDOUT_PRESERVE} heldout PRESERVE"
    assert len(heldout_correct) == HELDOUT_CORRECT, f"Expected {HELDOUT_CORRECT} heldout CORRECT"

    heldout_ids = {h["eval_id"] for h in heldout_items}
    heldout_calque_targets = {h["target_term"].casefold().strip() for h in heldout_correct if h.get("target_term")}

    # Check SFT IDs and targets
    for r in sft_records:
        assert r["trajectory_id"] not in heldout_ids, f"Leakage: SFT id {r['trajectory_id']} present in held-out suite"
        if r.get("is_calque_or_russianism"):
            target = (r.get("target_term") or "").casefold().strip()
            if target:
                assert target not in heldout_calque_targets, (
                    f"Leakage: SFT calque target '{target}' collides with held-out CORRECT suite"
                )

    # Check DPO IDs
    for r in dpo_records:
        assert r["pair_id"] not in heldout_ids, f"Leakage: DPO pair_id {r['pair_id']} present in held-out suite"


def test_partition_firewall_minhash_isolation(receipt_data: dict[str, Any]) -> None:
    """Verify empirical MinHash and exact Jaccard near-duplicate similarity are strictly < 0.80."""
    firewall = receipt_data["deliverables"]["heldout_evaluation_suite"]["partition_firewall"]
    assert firewall["partition_isolated"] is True
    assert firewall["target_term_leakage_count"] == 0
    assert firewall["record_id_leakage_count"] == 0

    max_sim = firewall["max_minhash_similarity"]
    assert isinstance(max_sim, (int, float))
    assert max_sim < 0.35, f"MinHash similarity {max_sim} >= 0.35 threshold"
    assert max_sim == 0.3281, f"Unexpected MinHash similarity {max_sim}, expected measured value 0.3281"

    max_jac = firewall["max_token_jaccard_similarity"]
    assert isinstance(max_jac, (int, float))
    assert max_jac < 0.35, f"Token Jaccard similarity {max_jac} >= 0.35 threshold"
    assert max_jac == 0.3000, f"Unexpected Token Jaccard similarity {max_jac}, expected measured value 0.3000"


def test_compute_heldout_minhash_similarity_detects_duplicate(tmp_path: Path) -> None:
    """Verify compute_heldout_minhash_similarity detects duplicate/near-duplicate and raises ValueError."""
    fake_heldout = tmp_path / "fake_heldout.jsonl"
    fake_case = {
        "eval_id": "eval_synth_001",
        "case_type": "CORRECT",
        "input_text": "Особливості деколонізації української термінології та мовних норм",
    }
    fake_heldout.write_text(json.dumps(fake_case, ensure_ascii=False) + "\n", encoding="utf-8")

    # Identical query in SFT
    synth_sft = [
        {
            "query": "Особливості деколонізації української термінології та мовних норм",
            "final_response": "Питома мовна форма повністю відповідає літературній нормі.",
        }
    ]
    synth_dpo: list[dict[str, Any]] = []

    with pytest.raises(ValueError, match="Partition firewall violation"):
        compute_heldout_minhash_similarity(
            heldout_suite_path=fake_heldout,
            sft_records=synth_sft,
            dpo_records=synth_dpo,
        )


def test_compute_heldout_minhash_similarity_synthetic_distinct(tmp_path: Path) -> None:
    """Verify compute_heldout_minhash_similarity produces expected exact values on distinct texts."""
    fake_heldout = tmp_path / "fake_heldout_distinct.jsonl"
    heldout_cases = [
        {"eval_id": "eval_d_01", "input_text": "Фізика твердого тіла та дослідження напівпровідникових кристалів."},
        {"eval_id": "eval_d_02", "input_text": "Хімічний синтез органічних макромолекул у водних розчинах."},
    ]
    with fake_heldout.open("w", encoding="utf-8") as f:
        for c in heldout_cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    synth_sft = [
        {
            "query": "Порівняльний аналіз лексикографічних джерел шістдесятих років.",
            "final_response": "Історична граматика підтверджує питомість давньоруської форми.",
        }
    ]
    synth_dpo = [
        {
            "prompt": "Культура українського публіцистичного мовлення.",
            "chosen": "Вживайте літературний зворот замість калькованого канцеляризму.",
            "rejected": "Радянський канцеляризм залишається поширеним у документації.",
        }
    ]

    minhash_sim, jaccard_sim, count = compute_heldout_minhash_similarity(
        heldout_suite_path=fake_heldout,
        sft_records=synth_sft,
        dpo_records=synth_dpo,
    )

    assert minhash_sim < 0.25
    assert jaccard_sim < 0.20  # Only minimal single-stopword overlap possible
    assert count == 10  # 2 heldout cases x 5 production texts = 10 pairwise comparisons


def test_no_private_host_paths_opsec(receipt_data: dict[str, Any]) -> None:
    """Verify OPSEC: zero host paths, usernames, or raw IPs in receipt."""
    assert_no_private_host_paths(receipt_data, "production_release_receipt.json")


def test_verify_only_cli_execution() -> None:
    """Run production shards assembly in --verify-only mode and verify exit 0."""
    script_path = REPO_ROOT / "scripts" / "projects" / "open_model_data" / "v4_production_shards_assembly.py"
    res = subprocess.run(
        [sys.executable, str(script_path), "--verify-only"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert res.returncode == 0, f"--verify-only failed with code {res.returncode}:\n{res.stderr}\n{res.stdout}"
    assert "[✓] --verify-only checks passed 100% cleanly!" in res.stdout


def test_tamper_detection_on_corrupted_shard(tmp_path: Path) -> None:
    """Verify that tampering with an SFT shard or receipt triggers a verification failure."""
    test_release_dir = tmp_path / "uldr_v1_production"
    shutil.copytree(DEFAULT_OUTPUT_DIR, test_release_dir)

    # Tamper with shard 001 by modifying one byte
    shard_1 = test_release_dir / "sft" / f"sft_shard_001_of_{SFT_SHARDS_COUNT:03d}.jsonl"
    content = shard_1.read_text(encoding="utf-8")
    tampered_content = content + "\n"
    shard_1.write_text(tampered_content, encoding="utf-8")

    # verify_production_release should fail on byte/hash mismatch
    with pytest.raises((ValueError, AssertionError)):
        verify_production_release(test_release_dir)


def test_dual_tier_licensing_structure(receipt_data: dict[str, Any]) -> None:
    """Verify dual-tier licensing declaration in receipt metadata."""
    licensing = receipt_data.get("licensing", {})
    assert licensing.get("packaging_tier") == "dual_tier"
    assert "CC-BY-4.0" in licensing.get("public_release", "")
    assert "Train-only" in licensing.get("research_internal", "")
    assert receipt_data.get("safety_assertions", {}).get("schema_validation_100_percent") is True
    assert receipt_data.get("safety_assertions", {}).get("claim_verification_100_percent") is True


def test_assemble_production_shards_refuses_archive_write() -> None:
    """Verify that assemble_production_shards strictly refuses write destinations in archive/ (#6321)."""
    from scripts.projects.open_model_data.v4_production_shards_assembly import assemble_production_shards

    with pytest.raises(ValueError, match="Prohibited assembly output generation on archived/quarantined path"):
        assemble_production_shards(
            output_dir=HISTORICAL_ARCHIVE_DIR,
            verify_only=False,
        )
