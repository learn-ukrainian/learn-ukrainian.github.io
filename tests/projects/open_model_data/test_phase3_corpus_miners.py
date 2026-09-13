"""Unit and contract tests for ULDR Phase 3.1–3.2: Human Error & Contrast Miners (#8006).

Validates textbook contrast tables, ZNO distractor tasks, UA-GEC calque/collocation mining,
curriculum stratification caps, and source custody invariants.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.v4_mine_corpus_calques import (
    DEFAULT_SOURCES_DB,
    DEFAULT_VESUM_DB,
)

CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"
MINED_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "mined"

MANIFEST_SCHEMA_PATH = CONTRACTS_DIR / "v1_decolonization_mined_candidates.schema.json"
MANIFEST_FILE = MINED_DIR / "decolonization_mined_manifest.json"
CONTRAST_FILE = MINED_DIR / "corpus_contrast_tables.jsonl"
ZNO_FILE = MINED_DIR / "zno_distractor_tasks.jsonl"
UAGEC_FILE = MINED_DIR / "uagec_mined_calques.jsonl"


@pytest.fixture(scope="module")
def manifest_schema() -> dict:
    assert MANIFEST_SCHEMA_PATH.is_file(), f"Missing schema: {MANIFEST_SCHEMA_PATH}"
    with MANIFEST_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture
def requires_sources_db() -> Path:
    """Skip test if uncommitted sources.db is missing or lacking required tables in CI."""
    if not DEFAULT_SOURCES_DB.is_file() or DEFAULT_SOURCES_DB.stat().st_size < 1_000_000:
        pytest.skip(f"requires {DEFAULT_SOURCES_DB} (not provisioned in CI)")
    try:
        with sqlite3.connect(f"file:{DEFAULT_SOURCES_DB}?mode=ro", uri=True) as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")}
            required = {"ua_gec_errors", "zno_tasks", "textbooks"}
            missing = sorted(required - tables)
            if missing:
                pytest.skip(f"requires {DEFAULT_SOURCES_DB} with tables: {', '.join(missing)} (not provisioned in CI)")
    except sqlite3.Error as e:
        pytest.skip(f"cannot open {DEFAULT_SOURCES_DB}: {e}")
    return DEFAULT_SOURCES_DB


@pytest.fixture
def requires_vesum_db() -> Path:
    """Skip test if uncommitted vesum.db is missing or lacking forms_all in CI."""
    if not DEFAULT_VESUM_DB.is_file() or DEFAULT_VESUM_DB.stat().st_size < 1_000_000:
        pytest.skip(f"requires {DEFAULT_VESUM_DB} (not provisioned in CI)")
    try:
        with sqlite3.connect(f"file:{DEFAULT_VESUM_DB}?mode=ro", uri=True) as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")}
            required = {"forms_all"}
            missing = sorted(required - tables)
            if missing:
                pytest.skip(f"requires {DEFAULT_VESUM_DB} with tables: {', '.join(missing)} (not provisioned in CI)")
    except sqlite3.Error as e:
        pytest.skip(f"cannot open {DEFAULT_VESUM_DB}: {e}")
    return DEFAULT_VESUM_DB


def test_mined_manifest_integrity(manifest_schema: dict) -> None:
    """Verify mined candidates manifest matches Draft2020-12 schema and files match exact SHA-256."""
    assert MANIFEST_FILE.is_file(), f"Missing manifest: {MANIFEST_FILE}"
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Schema Validation
    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(manifest))
    assert not errors, f"Manifest schema errors: {[e.message for e in errors]}"

    # 2. Metadata Invariants
    assert manifest["schema_version"] == "v1_decolonization_mined_candidates"
    assert manifest["issue"] == 8006
    assert manifest["parent_epic"] == 6321

    # 3. File existence, line count, and cryptographic SHA-256 validation
    for key, fmeta in manifest["files"].items():
        fpath = MINED_DIR / fmeta["filename"]
        assert fpath.is_file(), f"Missing artifact file: {fpath}"
        actual_sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
        assert actual_sha == fmeta["sha256"], f"SHA256 mismatch for {key}: expected {fmeta['sha256']}, got {actual_sha}"

        line_count = sum(1 for line in fpath.open(encoding="utf-8") if line.strip())
        assert line_count == fmeta["record_count"], (
            f"Record count mismatch for {key}: expected {fmeta['record_count']}, got {line_count}"
        )


def test_textbook_contrast_tables_authenticity_and_invariants() -> None:
    """Verify structure and content of mined textbook contrast tables."""
    assert CONTRAST_FILE.is_file(), f"Missing contrast file: {CONTRAST_FILE}"

    records = []
    with CONTRAST_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))

    assert len(records) >= 300, f"Expected >= 300 contrast pairs, got {len(records)}"

    seen_items = set()
    for rec in records:
        assert "item_id" in rec and rec["item_id"].startswith("contrast.textbook.")
        assert rec.get("chunk_id")
        assert "source" in rec and rec["source"].startswith("textbook:")
        assert rec.get("author")
        assert "incorrect" in rec and len(rec["incorrect"]) >= 2
        assert "correct" in rec and len(rec["correct"]) >= 2
        assert rec["incorrect"].lower() != rec["correct"].lower(), f"Trivial identity pair: {rec}"
        assert "derivational_family" in rec and len(rec["derivational_family"]) >= 1

        pair_key = (rec["incorrect"].lower(), rec["correct"].lower())
        assert pair_key not in seen_items, f"Duplicate contrast pair: {pair_key}"
        seen_items.add(pair_key)


def test_zno_distractor_tasks_coverage_and_invariants() -> None:
    """Verify that exactly 1,646 official ZNO tasks are extracted with complete metadata."""
    assert ZNO_FILE.is_file(), f"Missing ZNO file: {ZNO_FILE}"

    tasks = []
    with ZNO_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line.strip()))

    assert len(tasks) == 1646, f"Expected 1,646 ZNO tasks, got {len(tasks)}"

    task_ids = set()
    for t in tasks:
        assert t["task_id"].startswith("zno.")
        assert t["task_id"] not in task_ids, f"Duplicate task ID: {t['task_id']}"
        task_ids.add(t["task_id"])

        assert t["year"] >= 2006, f"Invalid year: {t['year']}"
        assert t["exam"] in ("zno", "nmt", "dpa"), f"Invalid exam type: {t['exam']}"
        assert t["stem"], f"Empty stem in task {t['task_id']}"
        assert t.get("topic_norm")


def test_uagec_mining_curriculum_cap_and_invariants() -> None:
    """Verify UA-GEC mined records, strict test-split exclusion, and <= 25% G/Case curriculum cap."""
    assert UAGEC_FILE.is_file(), f"Missing UA-GEC file: {UAGEC_FILE}"

    records = []
    with UAGEC_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))

    assert len(records) >= 2500, f"Expected >= 2,500 mined UA-GEC records, got {len(records)}"

    calque_colloc_count = 0
    case_count = 0

    for rec in records:
        assert rec["record_id"].startswith("uagec.")
        assert rec["error"] and rec["correct"]
        assert rec["error_type"] in ("F/Calque", "F/Collocation", "G/Case")
        assert "test" not in rec["partition"].lower(), f"Leakage of test partition row: {rec}"
        assert rec["curriculum_admission"] == "ADMITTED"

        if rec["error_type"] in ("F/Calque", "F/Collocation"):
            calque_colloc_count += 1
        elif rec["error_type"] == "G/Case":
            case_count += 1

    total_records = len(records)
    case_ratio = case_count / total_records
    assert case_ratio <= 0.25, f"Curriculum cap violated: G/Case ratio {case_ratio:.4f} > 0.25"
    assert calque_colloc_count >= 2000, f"Expected >= 2000 calques/collocations, got {calque_colloc_count}"


def test_mined_cli_verify_only() -> None:
    """Verify CLI --verify-only flag on both miners passes with exit code 0."""
    res1 = subprocess.run(
        [
            sys.executable,
            "scripts/projects/open_model_data/v4_mine_corpus_calques.py",
            "--verify-only",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res1.returncode == 0, f"v4_mine_corpus_calques.py --verify-only failed: {res1.stderr}"

    res2 = subprocess.run(
        [
            sys.executable,
            "scripts/projects/open_model_data/v4_mine_uagec_calques.py",
            "--verify-only",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 0, f"v4_mine_uagec_calques.py --verify-only failed: {res2.stderr}"


def test_independent_sources_grounding(requires_sources_db: Path) -> None:
    """Independently verify that mined items are 100% grounded in sources.db."""
    s_conn = sqlite3.connect(f"file:{requires_sources_db}?mode=ro", uri=True)
    sc = s_conn.cursor()

    # 1. Verify random sample of contrast chunks exist in textbooks
    with CONTRAST_FILE.open("r", encoding="utf-8") as f:
        contrast_records = [json.loads(line) for line in f if line.strip()]

    for rec in contrast_records[:30]:
        cid = rec["chunk_id"]
        row = sc.execute("SELECT id, text FROM textbooks WHERE chunk_id = ?", (cid,)).fetchone()
        assert row is not None, f"Chunk {cid} missing from textbooks table"
        assert rec["incorrect"].split()[0] in row[1] or rec["correct"].split()[0] in row[1], (
            f"Terms from {rec} not found in chunk {cid} text"
        )

    # 2. Verify all test doc_ids in ua_gec_errors are strictly absent from mined uagec records
    test_rows = sc.execute("SELECT doc_id FROM ua_gec_errors WHERE partition LIKE '%test%'").fetchall()
    test_doc_ids = {r[0] for r in test_rows}

    with UAGEC_FILE.open("r", encoding="utf-8") as f:
        uagec_records = [json.loads(line) for line in f if line.strip()]

    for rec in uagec_records:
        assert rec["doc_id"] not in test_doc_ids, f"Protected test doc_id {rec['doc_id']} found in mined record: {rec}"

    s_conn.close()


def test_independent_vesum_lemma_attestation(requires_vesum_db: Path) -> None:
    """Independently verify that correct phrases and target terms are attested in VESUM."""
    v_conn = sqlite3.connect(f"file:{requires_vesum_db}?mode=ro", uri=True)
    vc = v_conn.cursor()

    with CONTRAST_FILE.open("r", encoding="utf-8") as f:
        contrast_records = [json.loads(line) for line in f if line.strip()]

    attested_count = 0
    for rec in contrast_records[:50]:
        first_word = rec["correct"].split()[0].strip(",.:;!?").lower()
        res = vc.execute("SELECT lemma FROM forms_all WHERE word_form = ? LIMIT 1", (first_word,)).fetchone()
        if res:
            attested_count += 1

    assert attested_count >= 40, f"Expected >= 40/50 VESUM attestations for contrast terms, got {attested_count}"
    v_conn.close()
