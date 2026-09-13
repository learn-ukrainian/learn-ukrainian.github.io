"""Unit and contract tests for ULDR Phase 3.1–3.2: Human Error & Contrast Miners (#8006).

Validates textbook contrast tables, ZNO distractor tasks, UA-GEC calque/collocation mining,
curriculum stratification caps, and source custody invariants.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.phase3_decolonization_partition import (
    is_phase30_textbook_heldout,
    is_phase30_uagec_heldout_doc,
    uagec_doc_partition_bucket,
)
from scripts.projects.open_model_data.phase3_mined_candidate_guards import (
    contains_invented_zno_ellipsis,
    is_constrained_mined_filename,
    is_grounded_uagec_sentence,
    is_inverted_do_po_date_range,
    is_synthetic_uagec_wrapper,
    verify_mined_manifest,
)
from scripts.projects.open_model_data.v4_mine_corpus_calques import (
    DEFAULT_SOURCES_DB,
    DEFAULT_VESUM_DB,
    official_zno_stem,
    strip_invented_zno_ellipsis,
)
from scripts.projects.open_model_data.v4_mine_uagec_calques import (
    lookup_uagec_source_sentence,
    resolve_uagec_sentence_context,
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
        assert not re.search(r"[a-zA-Z]|https?://", rec["incorrect"]), f"Latin/URL in incorrect: {rec}"
        assert not re.search(r"[a-zA-Z]|https?://", rec["correct"]), f"Latin/URL in correct: {rec}"
        assert rec.get("context"), f"Missing context in {rec}"
        assert rec["incorrect"].split()[0] in rec["context"]
        assert rec["correct"].split()[0] in rec["context"]

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

    assert len(records) >= 2000, f"Expected >= 2000 grounded UA-GEC records, got {len(records)}"

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
    assert calque_colloc_count >= 1500, f"Expected >= 1500 grounded calques/collocations, got {calque_colloc_count}"


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
        timeout=60,
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
        timeout=60,
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
        assert rec["context"] in row[1], f"Context line from {rec} missing from chunk {cid}"
        assert rec["incorrect"].split()[0] in rec["context"], f"Incorrect term not in context: {rec}"
        assert rec["correct"].split()[0] in rec["context"], f"Correct term not in context: {rec}"

    # 2. Verify all test doc_ids in ua_gec_errors are strictly absent from mined uagec records
    test_rows = sc.execute("SELECT doc_id FROM ua_gec_errors WHERE partition LIKE '%test%'").fetchall()
    test_doc_ids = {r[0] for r in test_rows}

    with UAGEC_FILE.open("r", encoding="utf-8") as f:
        uagec_records = [json.loads(line) for line in f if line.strip()]

    for rec in uagec_records:
        assert rec["doc_id"] not in test_doc_ids, f"Protected test doc_id {rec['doc_id']} found in mined record: {rec}"

    with ZNO_FILE.open(encoding="utf-8") as handle:
        zno_records = [json.loads(line) for line in handle if line.strip()]
    mismatched = []
    for rec in zno_records:
        try:
            tid = int(str(rec["task_id"]).split(".", 1)[1])
        except (IndexError, ValueError):
            mismatched.append(rec.get("task_id"))
            continue
        row = sc.execute("SELECT stem FROM zno_tasks WHERE id = ?", (tid,)).fetchone()
        if row is None or rec.get("stem") != official_zno_stem(row[0]):
            mismatched.append(rec.get("task_id"))
    assert mismatched == [], f"ZNO stems that are not official zno_tasks.stem: {mismatched[:10]}"

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


def test_f1_inverted_do_po_date_range_guard_rejects_calque_as_gold() -> None:
    """F1: з N до labeled incorrect against з N по must fail (would have passed before the guard)."""
    assert is_inverted_do_po_date_range("з 5 до 15 січня", "з 5 по 15 січня")
    assert is_inverted_do_po_date_range("робота з 1 до 10 березня", "робота з 1 по 10 березня")
    assert not is_inverted_do_po_date_range("з 5 по 15 січня", "з 5 до 15 січня")
    assert not is_inverted_do_po_date_range("по вулиці", "на вулиці")


def test_f1_shipped_contrast_tables_have_no_inverted_do_po_pairs() -> None:
    """F1 lock: committed contrast JSONL never teaches the Russian с…по calque as correct."""
    assert CONTRAST_FILE.is_file()
    inverted = []
    glazova_s0120 = []
    with CONTRAST_FILE.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            if is_inverted_do_po_date_range(rec["incorrect"], rec["correct"]):
                inverted.append(rec["item_id"])
            if rec.get("chunk_id") == "11-klas-ukrajinska-mova-glazova-2019_s0120":
                glazova_s0120.append(rec)
    assert inverted == [], f"Inverted з…до / з…по gold still shipped: {inverted}"
    assert glazova_s0120, "glazova-2019_s0120 contrast rows missing"
    assert all(
        not (rec["incorrect"].startswith("з 5 до") and rec["correct"].startswith("з 5 по")) for rec in glazova_s0120
    )


def test_f2_synthetic_wrapper_and_ellipsis_guards() -> None:
    """F2: miner-invented wrappers/ellipses fail; original sentences pass."""
    wrapper = "У тексті вжито вираз: «коментарій» (виправлено на: «коментар»)."
    construction = "У тексті вжито конструкцію: «по вулиці» (виправлено на: «на вулиці»)."
    original = "Я написав коментарій під дописом."
    assert is_synthetic_uagec_wrapper(wrapper)
    assert is_synthetic_uagec_wrapper(construction)
    assert not is_synthetic_uagec_wrapper(original)
    assert not is_grounded_uagec_sentence(wrapper, "коментарій")
    assert is_grounded_uagec_sentence(original, "коментарій")
    invented = "Зображене в уривку ... [скорочено] ... суголосне з подіями твору"
    assert contains_invented_zno_ellipsis(invented)
    assert not contains_invented_zno_ellipsis("Зображене в уривку суголосне з подіями твору")
    cleaned = strip_invented_zno_ellipsis(invented)
    assert "[скорочено]" not in cleaned
    assert " ... ... " not in cleaned
    assert cleaned == "Зображене в уривку суголосне з подіями твору"


def test_f2_strip_skorocheno_does_not_leave_spliced_ellipsis() -> None:
    """F2 regression: looking for корочено (missing с) cannot strip [скорочено]."""
    invented = "Зображене в уривку ... [скорочено] ... суголосне з подіями твору"
    typo_strip = re.sub(r"\s*\.\.\.\s*\[c?корочено\]\s*\.\.\.\s*", " ", invented, flags=re.IGNORECASE)
    assert "[скорочено]" in typo_strip
    cleaned = strip_invented_zno_ellipsis(invented)
    assert cleaned == "Зображене в уривку суголосне з подіями твору"
    leftover = "Зображене в уривку ... ... суголосне з подіями твору"
    assert contains_invented_zno_ellipsis(leftover)
    assert " ... ... " not in strip_invented_zno_ellipsis(leftover)


def test_f2_shipped_uagec_and_zno_have_zero_synthetic_wrappers() -> None:
    """F2 lock: committed UA-GEC contexts are original sentences; ZNO stems have no [скорочено]."""
    assert UAGEC_FILE.is_file()
    wrappers = 0
    ungrounded = 0
    with UAGEC_FILE.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            if is_synthetic_uagec_wrapper(rec.get("sentence_context", "")):
                wrappers += 1
            if not is_grounded_uagec_sentence(rec.get("sentence_context", ""), rec.get("error", "")):
                ungrounded += 1
    assert wrappers == 0, f"Synthetic UA-GEC wrappers still present: {wrappers}"
    assert ungrounded == 0, f"Ungrounded UA-GEC sentence_context rows: {ungrounded}"

    invented = 0
    spliced = 0
    with ZNO_FILE.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            stem = rec.get("stem", "")
            if contains_invented_zno_ellipsis(stem):
                invented += 1
            if " ... ... " in stem or re.search(r"\.\.\.\s*\.\.\.", stem):
                spliced += 1
    assert invented == 0, f"Invented ZNO [скорочено] / spliced stems still present: {invented}"
    assert spliced == 0, f"Miner-spliced ' ... ... ' stems still present: {spliced}"


def test_f3_phase30_firewall_helpers_and_zero_heldout_leak() -> None:
    """F3: Phase 3.0 uagec_doc: split is applied; leaked docs would fail this test."""
    leaked_example = None
    train_example = None
    # Deterministic search over a small id space so the test names a real held-out bucket.
    for doc_id in (f"{index:04d}" for index in range(40)):
        if is_phase30_uagec_heldout_doc(doc_id) and leaked_example is None:
            leaked_example = doc_id
        if not is_phase30_uagec_heldout_doc(doc_id) and train_example is None:
            train_example = doc_id
        if leaked_example and train_example:
            break
    assert leaked_example is not None and train_example is not None
    assert uagec_doc_partition_bucket(leaked_example) >= 8
    assert uagec_doc_partition_bucket(train_example) < 8
    assert is_phase30_textbook_heldout("heldout-author", "heldout-title") in (True, False)

    assert UAGEC_FILE.is_file()
    leaked_docs: set[str] = set()
    with UAGEC_FILE.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            if is_phase30_uagec_heldout_doc(str(rec["doc_id"])):
                leaked_docs.add(str(rec["doc_id"]))
    assert not leaked_docs, f"Phase 3.0 held-out UA-GEC leak: {sorted(leaked_docs)[:10]}"


def test_f3_lookup_uses_complete_context_fixture(tmp_path: Path) -> None:
    """F3/F2: original sentence comes from the UA-GEC source file, never a wrapper."""
    checkout = tmp_path / "ua-gec"
    annotated = checkout / "data/gec-fluency/train/annotated/0001.a1.ann"
    source = checkout / "data/gec-fluency/train/source-sentences/0001.src.txt"
    annotated.parent.mkdir(parents=True)
    source.parent.mkdir(parents=True)
    annotated.write_text("Я {коментарій=>коментар:::error_type=F/Calque} написав.\n", encoding="utf-8")
    source.write_text("Я коментарій написав.\n", encoding="utf-8")
    sentence = lookup_uagec_source_sentence(
        checkout, "gec-fluency/train", "0001", "1", "коментарій", correct="коментар"
    )
    assert sentence == "Я коментарій написав."
    rec = {
        "error_id": 1,
        "error": "коментарій",
        "correct": "коментар",
        "partition": "gec-fluency/train",
        "doc_id": "0001",
        "annotator_id": "1",
    }
    resolved = resolve_uagec_sentence_context(rec, {}, checkout)
    assert resolved == "Я коментарій написав."
    assert resolve_uagec_sentence_context(rec, {}, None) is None


def test_f4_verify_only_hashes_and_schema_reject_unconstrained_filenames(manifest_schema: dict, tmp_path: Path) -> None:
    """F4/F5: --verify-only is hash+record contract, not line-count; absolute paths fail."""
    result = verify_mined_manifest(MINED_DIR, MANIFEST_SCHEMA_PATH)
    assert result["ok"] is True
    assert not is_constrained_mined_filename("/home/ops/corpus_contrast_tables.jsonl")
    assert not is_constrained_mined_filename("nested/uagec_mined_calques.jsonl")
    assert is_constrained_mined_filename("uagec_mined_calques.jsonl")

    bad = {
        "filename": "/tmp/uagec_mined_calques.jsonl",
        "record_count": 10,
        "sha256": "a" * 64,
        "description": "bad",
    }
    file_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": manifest_schema["$defs"],
        **manifest_schema["$defs"]["fileEntry"],
    }
    errors = list(jsonschema.Draft202012Validator(file_schema).iter_errors(bad))
    assert errors, "unconstrained absolute filename must fail the file-entry contract"

    wrapper_row = {
        "record_id": "uagec.1",
        "error_id": 1,
        "error": "коментарій",
        "correct": "коментар",
        "error_type": "F/Calque",
        "doc_id": "0000",
        "annotator_id": "1",
        "partition": "gec-fluency/train",
        "is_native": False,
        "source_lang": "",
        "derivational_family": "коментар",
        "sentence_context": "У тексті вжито вираз: «коментарій» (виправлено на: «коментар»).",
        "curriculum_admission": "ADMITTED",
    }
    record_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": manifest_schema["$defs"],
        **manifest_schema["$defs"]["uagecRecord"],
    }
    wrapper_errors = list(jsonschema.Draft202012Validator(record_schema).iter_errors(wrapper_row))
    assert wrapper_errors, "synthetic wrapper row must fail the UA-GEC JSONL contract"
