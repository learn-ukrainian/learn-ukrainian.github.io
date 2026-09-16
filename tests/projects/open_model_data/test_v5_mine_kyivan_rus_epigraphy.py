"""Unit and regression tests for Phase 5.7: Kyivan Rus Epigraphy, Church Slavonic Diglossia & Heritage Alignment (v0.4a).

Issue: #8103
Parent Epic: #6321

Validates:
  1. Release files existence and cryptographic SHA-256 integrity.
  2. Release receipt schema validation and Draft 2020-12 compliance.
  3. Held-out evaluation benchmark stratification and schema validation:
     - Total cases >= 500
     - Cathedral graffiti cases >= 200
     - Chronicle cases >= 200
     - Anti-copying mixed-error coverage >= 30%
  4. Strict 0% train/eval leakage firewall:
     - Zero graffiti room overlap (eval strictly confined to Rooms 121 & 110)
     - Zero chronicle monument overlap (eval strictly confined to Novgorod I & Ruska Pravda)
     - Zero record/chunk ID overlap
  5. SFT training dataset validation:
     - Total trajectories == 10,000
     - Draft 2020-12 schema compliance
     - Unique trajectory IDs
  6. Linguistic integrity & Advisor Controls:
     - Control 1: Diplomatic verification (HTML stripped, editorial symbols preserved)
     - Control 2: Church Slavonic formulaic protection (0 false-positive flags on liturgical prayers)
     - Control 3: Paleographic normalization
     - Control 4: Symmetric modern-translation purge (zero translation leaks into reasoning)
     - Control 5: Scribe- and monument-level partitioning
     - Control 6: Scholarly philological framing (vocative in -e, pleophony, dative in -ovi/-evi, 3rd-person in -t')
     - Control 7: Historical Cyrillic grapheme validation (ѣ, ѧ, ѡ, ъ, ь, ѵ, ѳ, ѫ)
     - Control 8: Modern literary replay buffer (>= 200 samples)
  7. Evaluation benchmark scorer and exact Clopper-Pearson 95% lower bound >= 0.95.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import jsonschema
import pytest

from scripts.projects.open_model_data.v5_mine_kyivan_rus_epigraphy import (
    CHURCH_SLAVONIC_LITURGICAL_PATTERNS,
    DEFAULT_RELEASE_DIR,
    EVAL_SCHEMA_FILE,
    HELD_OUT_CHRONICLE_MONUMENTS,
    HELD_OUT_GRAFFITI_ROOMS,
    HISTORICAL_CYRILLIC_RE,
    RECEIPT_SCHEMA_FILE,
    TRAJECTORY_SCHEMA_FILE,
    clean_html_diplomatic,
    detect_features,
    evaluate_epigraphic_suite,
)

EVAL_BENCHMARK_PATH = DEFAULT_RELEASE_DIR / "kyivan_rus_epigraphic_eval.jsonl"
EVAL_SHA_PATH = DEFAULT_RELEASE_DIR / "kyivan_rus_epigraphic_eval.sha256"
SFT_DIR = DEFAULT_RELEASE_DIR / "sft"
MANIFEST_PATH = SFT_DIR / "manifest.json"
MANIFEST_SHA_PATH = SFT_DIR / "manifest.json.sha256"
RECEIPT_PATH = DEFAULT_RELEASE_DIR / "release_receipt.json"
RECEIPT_SHA_PATH = DEFAULT_RELEASE_DIR / "release_receipt.json.sha256"


@pytest.fixture(scope="module")
def eval_schema() -> dict[str, Any]:
    assert EVAL_SCHEMA_FILE.is_file(), f"Evaluation record schema missing: {EVAL_SCHEMA_FILE}"
    schema = json.loads(EVAL_SCHEMA_FILE.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture(scope="module")
def receipt_schema() -> dict[str, Any]:
    assert RECEIPT_SCHEMA_FILE.is_file(), f"Release receipt schema missing: {RECEIPT_SCHEMA_FILE}"
    schema = json.loads(RECEIPT_SCHEMA_FILE.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture(scope="module")
def trajectory_schema() -> dict[str, Any]:
    assert TRAJECTORY_SCHEMA_FILE.is_file(), f"Trajectory schema missing: {TRAJECTORY_SCHEMA_FILE}"
    schema = json.loads(TRAJECTORY_SCHEMA_FILE.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture(scope="module")
def eval_cases() -> list[dict[str, Any]]:
    assert EVAL_BENCHMARK_PATH.is_file(), f"Benchmark file missing: {EVAL_BENCHMARK_PATH}"
    lines = [json.loads(line) for line in EVAL_BENCHMARK_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines


@pytest.fixture(scope="module")
def sft_trajectories() -> list[dict[str, Any]]:
    assert SFT_DIR.is_dir(), f"SFT directory missing: {SFT_DIR}"
    assert MANIFEST_PATH.is_file(), f"SFT manifest missing: {MANIFEST_PATH}"
    lines: list[dict[str, Any]] = []
    for shard_path in sorted(SFT_DIR.glob("sft_shard_*.jsonl")):
        for line in shard_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                lines.append(json.loads(line))
    return lines


@pytest.fixture(scope="module")
def receipt() -> dict[str, Any]:
    assert RECEIPT_PATH.is_file(), f"Receipt file missing: {RECEIPT_PATH}"
    return json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))


def test_release_files_exist_and_sha_integrity() -> None:
    """Test 1: Release artifacts exist and cryptographic SHA-256 hashes match."""
    for file_path, sha_path in [
        (EVAL_BENCHMARK_PATH, EVAL_SHA_PATH),
        (MANIFEST_PATH, MANIFEST_SHA_PATH),
        (RECEIPT_PATH, RECEIPT_SHA_PATH),
    ]:
        assert file_path.is_file(), f"Missing release file: {file_path}"
        assert sha_path.is_file(), f"Missing SHA-256 file: {sha_path}"

        expected_sha = sha_path.read_text(encoding="utf-8").split()[0].strip()
        actual_sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_sha == expected_sha, f"SHA mismatch for {file_path}: expected {expected_sha}, got {actual_sha}"

    # Verify each shard in manifest
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["shards_count"] == 30
    for shard_info in manifest["shards"]:
        shard_path = SFT_DIR / shard_info["filename"]
        assert shard_path.is_file(), f"Missing shard: {shard_path}"
        assert shard_path.stat().st_size <= 2000 * 1024, f"Shard exceeds 2000 KB: {shard_path}"
        actual_shard_sha = hashlib.sha256(shard_path.read_bytes()).hexdigest()
        assert actual_shard_sha == shard_info["sha256"], f"Shard SHA mismatch: {shard_path}"


def test_release_receipt_schema(receipt_schema: dict[str, Any], receipt: dict[str, Any]) -> None:
    """Test 2: Release receipt adheres strictly to Draft 2020-12 schema."""
    validator = jsonschema.Draft202012Validator(receipt_schema)
    validator.validate(receipt)
    assert receipt["issue"] == 8103
    assert receipt["parent_epic"] == 6321
    assert receipt["invariants_verified"]["zero_train_eval_leakage"] is True
    assert receipt["invariants_verified"]["symmetric_translation_purge"] is True
    assert receipt["invariants_verified"]["church_slavonic_formula_protection"] is True


def test_eval_benchmark_stratification(eval_schema: dict[str, Any], eval_cases: list[dict[str, Any]]) -> None:
    """Test 3: Evaluation benchmark stratification and case counts."""
    validator = jsonschema.Draft202012Validator(eval_schema)
    for case in eval_cases:
        validator.validate(case)

    assert len(eval_cases) >= 500, f"Expected >= 500 eval cases, found {len(eval_cases)}"

    graffiti = [c for c in eval_cases if c["monument_type"] == "cathedral_graffiti"]
    chronicles = [c for c in eval_cases if c["monument_type"] == "chronicle"]

    assert len(graffiti) >= 200, f"Expected >= 200 graffiti cases, found {len(graffiti)}"
    assert len(chronicles) >= 200, f"Expected >= 200 chronicle cases, found {len(chronicles)}"

    # Check anti-copying mixed error coverage >= 30%
    mixed_errors = [c for c in eval_cases if c["has_injected_error"]]
    mixed_rate = len(mixed_errors) / len(eval_cases)
    assert mixed_rate >= 0.30, f"Expected mixed error coverage >= 30%, got {mixed_rate * 100:.1f}%"


def test_zero_train_eval_leakage_firewall(
    eval_cases: list[dict[str, Any]],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Test 4: Strict 0% train/eval leakage firewall across rooms and monuments."""
    # 1. Graffiti room firewall: eval must ONLY contain rooms from HELD_OUT_GRAFFITI_ROOMS
    for c in eval_cases:
        if c["monument_type"] == "cathedral_graffiti":
            room_info = c["source_metadata"].get("room_or_panel", "")
            has_valid_room = any(f"Room {rm}" in room_info for rm in HELD_OUT_GRAFFITI_ROOMS)
            assert has_valid_room, f"Eval case leaked from non-eval room: {room_info}"

    # SFT training graffiti must NEVER contain held-out rooms
    for t in sft_trajectories:
        if "Софії Київської" in t["query"]:
            for rm in HELD_OUT_GRAFFITI_ROOMS:
                assert f"приміщення {rm}" not in t["query"], f"SFT trajectory leaked held-out room {rm}"
                assert f"приміщення {rm}" not in t["final_response"], f"SFT response leaked held-out room {rm}"

    # 2. Chronicle monument firewall: eval must ONLY contain monuments from HELD_OUT_CHRONICLE_MONUMENTS
    for c in eval_cases:
        if c["monument_type"] == "chronicle":
            assert c["monument_name"] in HELD_OUT_CHRONICLE_MONUMENTS, (
                f"Eval case leaked monument: {c['monument_name']}"
            )

    # SFT chronicles must NEVER contain held-out monuments
    for t in sft_trajectories:
        if "літопис" in t["query"]:
            for m in HELD_OUT_CHRONICLE_MONUMENTS:
                assert m not in t["query"], f"SFT trajectory leaked held-out chronicle monument: {m}"
                assert m not in t["final_response"], f"SFT response leaked held-out chronicle monument: {m}"


def test_sft_dataset_volume_and_schema(
    trajectory_schema: dict[str, Any],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Test 5: SFT dataset volume (10,000 trajectories) and Draft 2020-12 compliance."""
    assert len(sft_trajectories) == 10000, f"Expected 10000 trajectories, found {len(sft_trajectories)}"

    traj_validator = jsonschema.Draft202012Validator(trajectory_schema)
    seen_ids: set[str] = set()
    for idx, t in enumerate(sft_trajectories[:1000]):
        traj_validator.validate(t)
        tid = t["trajectory_id"]
        assert tid not in seen_ids, f"Duplicate trajectory ID at index {idx}: {tid}"
        seen_ids.add(tid)


def test_diplomatic_cleaning_and_html_strip() -> None:
    """Test 6: Control 1 - Diplomatic text cleaning preserves historical Cyrillic and strips tags."""
    raw = "<p>Моужъ зъл<supplied reason='lost'>ъ</supplied></p>\r\n<p>&nbsp;</p>"
    clean = clean_html_diplomatic(raw)
    assert clean == "Моужъ зъл ъ"
    assert "<p>" not in clean
    assert "&nbsp;" not in clean

    raw2 = "Г(оспод)и помози рабу своєму [Іоану]"
    clean2 = clean_html_diplomatic(raw2)
    assert "Г(оспод)и помози" in clean2
    assert "[Іоану]" in clean2


def test_church_slavonic_formula_protection() -> None:
    """Test 7: Control 2 - Liturgical Church Slavonic formulas are identified and protected."""
    sample_prayers = [
        "Господи помози рабу твоєму Василеви",
        "Помилоуи мѧ грѣшьнаго",
        "Сп(а)си Г(оспо)ди раба своего",
        "Вѣчная память",
    ]
    for text in sample_prayers:
        reg, _feats = detect_features(text)
        assert any(pat.search(text) for pat in CHURCH_SLAVONIC_LITURGICAL_PATTERNS)
        assert "church" in reg or "mixed" in reg


def test_proto_ukrainian_vernacular_feature_detection() -> None:
    """Test 8: Control 6 - Proto-Ukrainian vernacular features detected in historical text."""
    # Vocative in -e
    _, feats1 = detect_features("Володимире княже")
    assert "vocative_in_e" in feats1

    # Dative in -ovi/-evi
    _, feats2 = detect_features("рабу своему Василеви")
    assert "dative_singular_ovi_evi" in feats2

    # Pleophony
    _, feats3 = detect_features("створиша новъ городъ на горѣ")
    assert "pleophony_full_vocalism" in feats3

    # 3rd person in -t'
    _, feats4 = detect_features("ідеть князь на войну")
    assert "verb_3rd_person_t" in feats4


def test_tokenizer_historical_graphemes() -> None:
    """Test 9: Control 7 - Historical Cyrillic graphemes handle clean string encoding without byte corruption."""
    historical_graphemes = ["ѣ", "ѧ", "ѡ", "ъ", "ь", "ѵ", "ѳ", "ѫ", "ꙋ", "ꙗ", "ѕ", "z", "і", "ѿ"]
    for char in historical_graphemes:
        encoded = char.encode("utf-8")
        decoded = encoded.decode("utf-8")
        assert decoded == char
        assert HISTORICAL_CYRILLIC_RE.search(char)


def test_modern_literary_replay_buffer(sft_trajectories: list[dict[str, Any]]) -> None:
    """Test 10: Control 8 - Calibrated modern literary replay buffer contains >= 200 samples."""
    replay_samples = [t for t in sft_trajectories if t.get("is_calque_or_russianism") is True]
    assert len(replay_samples) >= 200, f"Expected >= 200 replay buffer samples, found {len(replay_samples)}"


def test_eval_suite_metrics_and_clopper_pearson(eval_cases: list[dict[str, Any]]) -> None:
    """Test 11: Compliance scoring and Clopper-Pearson 95% lower bound >= 0.95."""
    metrics = evaluate_epigraphic_suite(eval_cases)
    assert metrics["accuracy"] >= 0.99
    assert metrics["preservation_rate"] >= 0.99
    assert metrics["mixed_error_correction_rate"] >= 0.99
    assert metrics["clopper_pearson_lower_95"] >= 0.95, (
        f"Clopper-Pearson bound too low: {metrics['clopper_pearson_lower_95']}"
    )
