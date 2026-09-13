"""Unit and contract tests for ULDR Phase 2: 150 Human Gold Seeds (#8001)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.gold_seeds_types import CATEGORY_QUOTAS
from scripts.projects.open_model_data.v4_mine_gold_seeds import check_quote_quality

CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"
SEEDS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "seeds"

TRAJ_SCHEMA_PATH = CONTRACTS_DIR / "v1_decolonization_trajectory.schema.json"
DPO_SCHEMA_PATH = CONTRACTS_DIR / "v1_decolonization_dpo_pair.schema.json"

TRAJ_FILE = SEEDS_DIR / "human_gold_seeds_150_trajectories.jsonl"
DPO_FILE = SEEDS_DIR / "human_gold_seeds_150_dpo.jsonl"
MANIFEST_FILE = SEEDS_DIR / "human_gold_seeds_manifest.json"


@pytest.fixture(scope="module")
def trajectory_schema() -> dict:
    assert TRAJ_SCHEMA_PATH.is_file(), f"Missing schema: {TRAJ_SCHEMA_PATH}"
    with TRAJ_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture(scope="module")
def dpo_pair_schema() -> dict:
    assert DPO_SCHEMA_PATH.is_file(), f"Missing schema: {DPO_SCHEMA_PATH}"
    with DPO_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


def test_gold_seeds_manifest_integrity() -> None:
    """Verify manifest exists, accurately reflects 150 records, and validates SHA256 checksums."""
    assert MANIFEST_FILE.is_file(), f"Missing manifest: {MANIFEST_FILE}"
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["schema_version"] == "v1_human_gold_seeds_manifest"
    assert manifest["total_records"] == 150
    assert manifest["issue"] == 8001
    assert manifest["parent_epic"] == 6321

    # Check category distribution matches exact quotas
    dist = manifest["category_distribution"]
    assert dist == CATEGORY_QUOTAS
    assert sum(dist.values()) == 150

    # Verify SHA-256 digests against files on disk
    for key, f_meta in manifest["files"].items():
        p = SEEDS_DIR / f_meta["filename"]
        assert p.is_file(), f"Missing dataset file: {p}"
        actual_sha = hashlib.sha256(p.read_bytes()).hexdigest()
        assert actual_sha == f_meta["sha256"], f"SHA256 mismatch for {key}: expected {f_meta['sha256']}, got {actual_sha}"
        assert f_meta["record_count"] == 150


def test_human_gold_seeds_trajectories_validate(trajectory_schema: dict) -> None:
    """Verify all 150 trajectories pass schema validation, contract constraints, and quote checks."""
    assert TRAJ_FILE.is_file(), f"Missing trajectory file: {TRAJ_FILE}"
    validator = jsonschema.Draft202012Validator(trajectory_schema)

    records = []
    with TRAJ_FILE.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            errors = list(validator.iter_errors(record))
            assert not errors, f"Trajectory schema error on line {idx}: {[e.message for e in errors]}"
            records.append(record)

    assert len(records) == 150

    # 1. Unique trajectory IDs matching required pattern
    traj_ids = [r["trajectory_id"] for r in records]
    assert len(traj_ids) == len(set(traj_ids))

    # 2. Invariant: register_spectrum alternatives are fully covered in vesum_attestation
    for r in records:
        vesum_lemmas = {v["lemma"] for v in r["vesum_attestation"]}
        for alt in r["register_spectrum"]["alternatives"]:
            assert alt["lemma"] in vesum_lemmas, (
                f"Alternative '{alt['lemma']}' in '{r['target_term']}' missing from vesum_attestation"
            )

    # 3. Verify zero quote quality defects on evidence sources
    for r in records:
        for alt in r["register_spectrum"]["alternatives"]:
            defect = check_quote_quality(alt["evidence_source"])
            assert defect is None, f"Quote quality defect '{defect}' in evidence: {alt['evidence_source']}"

    # 4. Anchor phenomena presence across all 7 categories
    target_terms = {r["target_term"] for r in records}

    # Category 1: Polysemy & Sense
    for term in ["рахувати", "відноситися", "складати", "вірний", "об'єм"]:
        assert term in target_terms, f"Missing anchor polysemy term: {term}"

    # Category 2: Prepositional Government
    for term in ["по закону", "по справах", "при підтримці", "на протязі року", "згідно закону"]:
        assert term in target_terms, f"Missing anchor preposition term: {term}"

    # Category 3: Active Participles
    for term in ["працюючий", "діючий", "головуючий", "оточуючий", "слідуючий"]:
        assert term in target_terms, f"Missing anchor participle term: {term}"

    # Category 4: Voice & Reflexivity
    for term in ["приймається Верховною Радою", "виконується учнем", "користуватися авторитетом", "вибачаюся", "хворіти грипом"]:
        assert term in target_terms, f"Missing anchor voice term: {term}"

    # Category 5: Historical Authority
    for term in ["мисль", "похибка", "філіжанка", "утюг", "трясовина"]:
        assert term in target_terms, f"Missing anchor historical term: {term}"

    # Category 6: Phraseology & Collocations
    for term in ["приймати участь", "кидатися в очі", "підводити підсумки", "перший млинець комом", "лід зрушився"]:
        assert term in target_terms, f"Missing anchor phraseology term: {term}"

    # Category 7: Lexical Restitution
    for term in ["пилосос", "переключити", "задача", "міроприємство", "накладна плата"]:
        assert term in target_terms, f"Missing anchor restitution term: {term}"


def test_human_gold_seeds_dpo_pairs_validate(dpo_pair_schema: dict) -> None:
    """Verify all 150 DPO preference pairs validate against schema and maintain sharp contrast."""
    assert DPO_FILE.is_file(), f"Missing DPO pair file: {DPO_FILE}"
    validator = jsonschema.Draft202012Validator(dpo_pair_schema)

    records = []
    with DPO_FILE.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            errors = list(validator.iter_errors(record))
            assert not errors, f"DPO pair schema error on line {idx}: {[e.message for e in errors]}"
            records.append(record)

    assert len(records) == 150

    # 1. Unique pair IDs
    pair_ids = [r["pair_id"] for r in records]
    assert len(pair_ids) == len(set(pair_ids))

    # 2. Chosen and rejected must be non-identical and substantive
    for r in records:
        assert r["chosen"] != r["rejected"]
        assert len(r["chosen"]) >= 15
        assert len(r["rejected"]) >= 15
        assert r["metadata"]["vesum_verified"] is True

    # 3. Flaw category representation
    flaws = {r["metadata"]["rejected_flaw"] for r in records}
    assert "soviet_lexicography_acceptance" in flaws
    assert "lack_of_morphemic_reasoning" in flaws
    assert "mechanical_wordnet_synset" in flaws


def test_gold_seeds_generator_cli_verify_only() -> None:
    """Verify that the generator script CLI --verify-only succeeds with exit code 0."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "projects" / "open_model_data" / "v4_mine_gold_seeds.py"),
        "--verify-only",
    ]
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)
    assert res.returncode == 0, f"CLI --verify-only failed:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}"
    assert "150 trajectories and 150 DPO pairs are 100% schema-valid!" in res.stdout
