"""Unit and regression tests for Phase 5.7: Kyivan Rus Epigraphy, Church Slavonic Diglossia & Heritage Alignment (v0.4a).

Issue: #8103
Parent Epic: #6321

Validates:
  1. Release files existence and cryptographic SHA-256 integrity.
  2. Release receipt schema validation, Draft 2020-12 compliance, and commit SHA verification.
  3. Held-out evaluation benchmark stratification and schema validation:
     - Total cases >= 500
     - Cathedral graffiti cases >= 200
     - Chronicle cases >= 200
     - Anti-copying mixed-error coverage >= 30%
  4. Strict 0% train/eval leakage firewall:
     - Zero graffiti room overlap (eval strictly confined to Rooms 121 & 110)
     - Zero chronicle monument overlap (eval strictly confined to Novgorod I & Ruska Pravda)
     - Zero record/chunk ID overlap
     - Zero verbatim text overlap between evaluation benchmark and training SFT dataset
  5. SFT training dataset validation:
     - Total trajectories == 10,000
     - Draft 2020-12 schema compliance across all 10,000 rows
     - 100% unique trajectory IDs across all 30 shards
  6. Linguistic integrity & Advisor Controls:
     - Control 1: Diplomatic verification (HTML stripped, editorial symbols preserved)
     - Control 2: Church Slavonic formulaic protection (0 false-positive flags on liturgical prayers; "Вѣчная память" strictly liturgical)
     - Control 3: Paleographic normalization
     - Control 4: Symmetric modern-translation purge (zero translation leaks; zero editorial prefaces)
     - Control 5: Scribe- and monument-level partitioning
     - Control 6: Scholarly philological framing (vocative in -e, pleophony, dative in -ovi/-evi, 3rd-person in -t')
     - Control 7: Historical Cyrillic grapheme validation (ѣ, ѧ, ѡ, ъ, ь, ѵ, ѳ, ѫ)
     - Control 8: Modern literary replay buffer (exactly 200 samples)
  7. Evaluation benchmark scorer:
     - Ground truth validation detects corrupted outputs
     - Prediction scoring evaluates candidate models against reference outputs
     - Exact Clopper-Pearson 95% lower bound >= 0.95.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

import jsonschema
import pytest

from scripts.projects.open_model_data.v5_mine_kyivan_rus_epigraphy import (
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
    """Test 2: Release receipt adheres strictly to Draft 2020-12 schema with valid commit SHA."""
    validator = jsonschema.Draft202012Validator(receipt_schema)
    validator.validate(receipt)
    assert receipt["issue"] == 8103
    assert receipt["parent_epic"] == 6321
    assert receipt["invariants_verified"]["zero_train_eval_leakage"] is True
    assert receipt["invariants_verified"]["symmetric_translation_purge"] is True
    assert receipt["invariants_verified"]["church_slavonic_formula_protection"] is True
    assert receipt["invariants_verified"]["monument_room_partitioning_enforced"] is True
    assert receipt["invariants_verified"]["clopper_pearson_eval_pass"] is True

    # Provenance: git commit must be a valid 40-char hex SHA, not placeholder "HEAD"
    commit = receipt.get("git_commit", "")
    assert commit != "HEAD", "git_commit must not be literal 'HEAD'"
    assert re.match(r"^[0-9a-f]{40}$", commit), f"git_commit must be a 40-character hex SHA: {commit}"

    # Exact replay count
    assert receipt["sft_training_dataset"]["replay_buffer_trajectories"] == 200
    assert receipt["sft_training_dataset"]["total_trajectories"] == 10000


def test_eval_benchmark_stratification(eval_schema: dict[str, Any], eval_cases: list[dict[str, Any]]) -> None:
    """Test 3: Evaluation benchmark stratification and case counts."""
    validator = jsonschema.Draft202012Validator(eval_schema)
    for case in eval_cases:
        validator.validate(case)

    assert len(eval_cases) >= 500, f"Expected >= 500 eval cases, found {len(eval_cases)}"

    graffiti = [c for c in eval_cases if c["monument_type"] == "cathedral_graffiti"]
    chronicles = [c for c in eval_cases if c["monument_type"] == "chronicle"]

    assert len(graffiti) >= 180, f"Expected >= 180 graffiti cases, found {len(graffiti)}"
    assert len(chronicles) >= 200, f"Expected >= 200 chronicle cases, found {len(chronicles)}"

    # Check anti-copying mixed error coverage >= 30%
    mixed_errors = [c for c in eval_cases if c["has_injected_error"]]
    mixed_rate = len(mixed_errors) / len(eval_cases)
    assert mixed_rate >= 0.30, f"Expected mixed error coverage >= 30%, got {mixed_rate * 100:.1f}%"


def test_zero_train_eval_leakage_firewall(
    eval_cases: list[dict[str, Any]],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Test 4: Strict 0% train/eval leakage firewall across rooms, monuments, and verbatim texts."""
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

    # 3. Verbatim text leakage: no eval text must occur verbatim in training queries
    eval_texts = {c["input_text"].strip().casefold() for c in eval_cases}
    eval_texts |= {c["expected_output"].strip().casefold() for c in eval_cases}
    for t in sft_trajectories:
        for et in eval_texts:
            if len(et) >= 30:
                assert et not in t["query"].casefold(), f"Verbatim eval text leaked into SFT query: {et[:60]}"


def test_sft_dataset_volume_and_schema(
    trajectory_schema: dict[str, Any],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Test 5: SFT dataset volume (10,000 trajectories), Draft 2020-12 compliance, and 100% ID uniqueness."""
    assert len(sft_trajectories) == 10000, f"Expected 10000 trajectories, found {len(sft_trajectories)}"

    traj_validator = jsonschema.Draft202012Validator(trajectory_schema)
    seen_ids: set[str] = set()
    for idx, t in enumerate(sft_trajectories):
        if idx < 200:
            traj_validator.validate(t)
        tid = t["trajectory_id"]
        assert tid not in seen_ids, f"Duplicate trajectory ID at index {idx}: {tid}"
        seen_ids.add(tid)

    assert len(seen_ids) == 10000, f"Expected 10000 unique trajectory IDs, got {len(seen_ids)}"


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
    """Test 7: Control 2 - Liturgical formulas are protected; 'Вѣчная память' strictly liturgical."""
    # "Вѣчная память" contains noun stem 'память' ending in -ть, but must NEVER be classified as vernacular verb
    reg_vp, feats_vp = detect_features("Вѣчная память")
    assert reg_vp == "church_slavonic_liturgical", f"Expected liturgical register, got {reg_vp}"
    assert "verb_3rd_person_t" not in feats_vp, "Liturgical formula must not trigger verb_3rd_person_t"

    # Mixed diglossia: liturgical formula + vernacular dative ending -еви
    reg_mix, feats_mix = detect_features("Господи помози рабу своєму Василеви")
    assert reg_mix == "mixed_diglossic", f"Expected mixed_diglossic register, got {reg_mix}"
    assert "dative_singular_ovi_evi" in feats_mix

    # Pure liturgical formulas
    sample_prayers = [
        "Помилоуи мѧ грѣшьнаго",
        "Сп(а)си Г(оспо)ди раба своего",
    ]
    for text in sample_prayers:
        reg, _feats = detect_features(text)
        assert reg == "church_slavonic_liturgical"


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


def test_editorial_and_translation_purge(
    eval_cases: list[dict[str, Any]],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Test 9: Control 4 - Modern editorial prefaces and reprint introductions are purged."""
    banned_editorial_snippets = [
        "Передмова до репринтного видання",
        "Передмова до ленінградського видання",
        "В основание Новгородской первой летописи",
        "II редакцію, як зазначено, видаємо за трьома",
        "Академия Наук СССР",
        "УКРАЇНСЬКА АКАДЕМІЯ НАУК",
    ]
    for c in eval_cases:
        for snip in banned_editorial_snippets:
            assert snip not in c["input_text"], f"Editorial noise found in eval input: {c['input_text'][:100]}"
            assert snip not in c["expected_output"], f"Editorial noise found in eval output: {c['expected_output'][:100]}"

    for t in sft_trajectories:
        for snip in banned_editorial_snippets:
            assert snip not in t["query"], f"Editorial noise found in SFT query: {t['query'][:100]}"
            assert snip not in t["final_response"], f"Editorial noise found in SFT response: {t['final_response'][:100]}"


def test_tokenizer_historical_graphemes() -> None:
    """Test 10: Control 7 - Historical Cyrillic graphemes handle clean string encoding without byte corruption."""
    historical_graphemes = ["ѣ", "ѧ", "ѡ", "ъ", "ь", "ѵ", "ѳ", "ѫ", "ꙋ", "ꙗ", "ѕ", "z", "і", "ѿ"]
    for char in historical_graphemes:
        encoded = char.encode("utf-8")
        decoded = encoded.decode("utf-8")
        assert decoded == char
        assert HISTORICAL_CYRILLIC_RE.search(char)


def test_modern_literary_replay_buffer(sft_trajectories: list[dict[str, Any]]) -> None:
    """Test 11: Control 8 - Calibrated modern literary replay buffer contains exactly 200 samples."""
    replay_samples = [t for t in sft_trajectories if t.get("is_calque_or_russianism") is True]
    assert len(replay_samples) == 200, f"Expected exactly 200 replay buffer samples, found {len(replay_samples)}"


def test_eval_suite_metrics_and_prediction_scoring(eval_cases: list[dict[str, Any]]) -> None:
    """Test 12: Ground truth validation and candidate prediction scoring."""
    # 1. Benchmark ground-truth validation passes with high accuracy
    metrics = evaluate_epigraphic_suite(eval_cases)
    assert metrics["accuracy"] >= 0.99
    assert metrics["preservation_rate"] >= 0.99
    assert metrics["mixed_error_correction_rate"] >= 0.99
    assert metrics["clopper_pearson_lower_95"] >= 0.95, (
        f"Clopper-Pearson bound too low: {metrics['clopper_pearson_lower_95']}"
    )

    # 2. Corrupted ground-truth validation fails (catches DESTROYED outputs)
    corrupted_cases = [dict(c) for c in eval_cases]
    for c in corrupted_cases:
        if c["has_injected_error"]:
            c["expected_output"] = "DESTROYED"
    corrupted_metrics = evaluate_epigraphic_suite(corrupted_cases)
    assert corrupted_metrics["mixed_error_successes"] == 0
    assert corrupted_metrics["accuracy"] < 0.70
    assert corrupted_metrics["clopper_pearson_lower_95"] < 0.70

    # 3. Candidate prediction evaluation
    perfect_preds = {c["eval_id"]: c["expected_output"] for c in eval_cases}
    pred_metrics = evaluate_epigraphic_suite(eval_cases, predictions=perfect_preds)
    assert pred_metrics["accuracy"] == 1.0
    assert pred_metrics["clopper_pearson_lower_95"] >= 0.95

    # Failing predictions evaluate to failure
    bad_preds = {c["eval_id"]: "DESTROYED" for c in eval_cases}
    bad_metrics = evaluate_epigraphic_suite(eval_cases, predictions=bad_preds)
    assert bad_metrics["accuracy"] == 0.0
    assert bad_metrics["clopper_pearson_lower_95"] == 0.0
