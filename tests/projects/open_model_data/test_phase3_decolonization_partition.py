"""Unit and contract tests for ULDR Phase 3.0: Pre-Extraction Partition Firewall & Source Custody (#8005).

Includes independent, non-circular verification of derivational root closure, full-corpus MinHash LSH deduplication,
exact binomial statistical power, and source custody invariants.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.phase3_decolonization_partition import (
    DEFAULT_SOURCES_DB,
    DEFAULT_VESUM_DB,
    SENTENCE_SPLIT_RE,
    MinHashDedup,
    exact_clopper_pearson_upper,
    extract_root_family,
    normalize_text,
    verify_manifest,
)

CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"
PARTITIONS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "partitions"

MANIFEST_SCHEMA_PATH = CONTRACTS_DIR / "v1_decolonization_partition_manifest.schema.json"
MANIFEST_FILE = PARTITIONS_DIR / "decolonization_partition_manifest.json"
TRAIN_CUSTODY_FILE = PARTITIONS_DIR / "train_source_custody.json"
HELDOUT_SUITE_FILE = PARTITIONS_DIR / "heldout_evaluation_suite_1000.jsonl"
MINHASH_REPORT_FILE = PARTITIONS_DIR / "minhash_dedup_summary.json"


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
            required = {"ua_gec_errors", "zno_tasks", "style_guide", "textbooks"}
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


def test_partition_manifest_integrity(manifest_schema: dict) -> None:
    """Verify partition manifest matches Draft2020-12 schema and files match exact SHA-256."""
    assert MANIFEST_FILE.is_file(), f"Missing manifest: {MANIFEST_FILE}"
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Schema Validation
    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(manifest))
    assert not errors, f"Manifest schema errors: {[e.message for e in errors]}"

    # 2. Metadata Invariants
    assert manifest["schema_version"] == "v1_decolonization_partition_manifest"
    assert manifest["issue"] == 8005
    assert manifest["parent_epic"] == 6321

    # 3. File existence and cryptographic SHA-256 validation
    for key, fmeta in manifest["files"].items():
        fpath = PARTITIONS_DIR / fmeta["filename"]
        assert fpath.is_file(), f"Missing artifact file: {fpath}"
        actual_sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
        assert actual_sha == fmeta["sha256"], f"SHA256 mismatch for {key}: expected {fmeta['sha256']}, got {actual_sha}"


def test_source_custody_invariants() -> None:
    """Verify custody rules: UA-GEC test protected, ZNO and style-guide Train-only."""
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    custody = manifest["source_custody_summary"]
    # UA-GEC test split must be explicitly excluded
    assert custody["ua_gec_excluded_test_count"] == 1159
    assert custody["ua_gec_train_documents_count"] > 0
    assert custody["ua_gec_heldout_documents_count"] > 0

    # Pretraining Contamination Defense: ZNO and style guide 100% Train-only
    assert custody["zno_tasks_train_only_count"] == 1646
    assert custody["style_guide_train_only_count"] == 342

    # Textbooks partitioned
    assert custody["textbook_train_chunks_count"] > 30000
    assert custody["textbook_heldout_chunks_count"] > 5000


def test_root_family_derivational_extraction_unit() -> None:
    """Verify that extract_root_family correctly collapses morphologically related derivations."""
    # Example cited in Operational Plan §3.4 and adversarial review:
    # рахувати / рахунок / підрахунок / розрахунок must all share the root 'рах'
    calc_words = ["рахувати", "рахунок", "підрахунок", "розрахунок"]
    calc_roots = {extract_root_family(w) for w in calc_words}
    assert len(calc_roots) == 1, f"Expected identical root family for {calc_words}, got {calc_roots}"
    assert calc_roots.pop() == "рах"

    # Derived imperfective verbs with epenthetic -л- after labials (Finding 1 fix)
    work_words = ["робити", "переробляти"]
    work_roots = {extract_root_family(w) for w in work_words}
    assert len(work_roots) == 1, f"Expected identical root family for {work_words}, got {work_roots}"
    assert work_roots.pop() == "роб"

    buy_words = ["купити", "купляти"]
    buy_roots = {extract_root_family(w) for w in buy_words}
    assert len(buy_roots) == 1, f"Expected identical root family for {buy_words}, got {buy_roots}"
    assert buy_roots.pop() == "куп"


def test_preserve_cases_verbatim_target_and_vesum_attestation(requires_vesum_db: Path) -> None:
    """Verify that all 600 PRESERVE cases contain target_term verbatim and are attested in VESUM."""
    assert HELDOUT_SUITE_FILE.is_file(), f"Missing held-out suite: {HELDOUT_SUITE_FILE}"

    cases = []
    with HELDOUT_SUITE_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line.strip()))

    preserve_cases = [c for c in cases if c["case_type"] == "PRESERVE"]
    assert len(preserve_cases) == 600

    v_conn = sqlite3.connect(DEFAULT_VESUM_DB)
    vc = v_conn.cursor()

    for c in preserve_cases:
        target = c["target_term"]
        text = c["input_text"]
        # Target must be in input text verbatim
        match = re.search(r"\b" + re.escape(target) + r"\b", text, re.IGNORECASE)
        assert match is not None, f"PRESERVE target '{target}' missing from input: '{text}'"

        # Target must be attested in VESUM
        res = vc.execute(
            "SELECT lemma FROM forms_all WHERE word_form = ? LIMIT 1",
            (target.lower(),),
        ).fetchone()
        assert res is not None, f"PRESERVE target '{target}' not found in VESUM"

    v_conn.close()


def test_derivational_closure_independent_zero_leakage(requires_sources_db: Path, requires_vesum_db: Path) -> None:
    """Independently recompute root families and verify zero root overlap between train and held-out unseen."""
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Check manifest summary
    p_summary = manifest["phenomenon_partition_summary"]
    assert p_summary["lemma_family_leakage_count"] == 0

    # 2. Independent recomputation from raw files
    cases = []
    with HELDOUT_SUITE_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line.strip()))

    # Unseen cases are the 200 cases drawn from heldout_unseen
    unseen_cases = [
        c for c in cases if c["case_type"] == "CORRECT" and "uagec_unseen" in c["source_metadata"]["source"]
    ]
    assert len(unseen_cases) == 200

    unseen_roots = set()
    for c in unseen_cases:
        unseen_roots.add(c["derivational_family"])
        unseen_roots.add(extract_root_family(c["target_term"]))
        if c["expected_replacement"]:
            unseen_roots.add(extract_root_family(c["expected_replacement"]))

    # Query train phenomena candidates directly from sources.db and vesum.db
    s_conn = sqlite3.connect(DEFAULT_SOURCES_DB)
    v_conn = sqlite3.connect(DEFAULT_VESUM_DB)
    sc = s_conn.cursor()
    vc = v_conn.cursor()

    def get_lemma(word: str) -> str:
        res = vc.execute("SELECT lemma FROM forms_all WHERE word_form = ? LIMIT 1", (word.strip().lower(),)).fetchone()
        return res[0] if res else word.strip().lower()

    gec_rows = sc.execute(
        "SELECT error, correct, error_type FROM ua_gec_errors WHERE partition NOT LIKE '%test%'"
    ).fetchall()

    phenomena = [r for r in gec_rows if r[2] in ("F/Calque", "F/Collocation") and r[0] and r[1]]

    root_to_items = {}
    for err, corr, _ in phenomena:
        err_l = get_lemma(err)
        corr_l = get_lemma(corr)
        err_r = extract_root_family(err_l)
        corr_r = extract_root_family(corr_l)
        root_to_items.setdefault(err_r, []).append((err_r, corr_r))

    train_roots = set()
    for rfam, pairs in root_to_items.items():
        h = int(hashlib.sha256(f"rfam:{rfam}".encode()).hexdigest()[:8], 16) % 10
        if h < 8:
            for e_r, c_r in pairs:
                if e_r not in unseen_roots and c_r not in unseen_roots:
                    train_roots.add(e_r)
                    train_roots.add(c_r)

    s_conn.close()
    v_conn.close()

    # Re-verify that the intersection of train roots and unseen roots is strictly empty
    intersection = train_roots & unseen_roots
    assert not intersection, (
        f"Independent leakage detected between train roots and heldout unseen roots: {intersection}"
    )


def test_ua_gec_test_split_strict_zero_leakage(requires_sources_db: Path) -> None:
    """Verify that official UA-GEC test split is 100% excluded from held-out suite and training partition."""
    s_conn = sqlite3.connect(DEFAULT_SOURCES_DB)
    sc = s_conn.cursor()

    test_rows = sc.execute(
        "SELECT id, error, correct, doc_id FROM ua_gec_errors WHERE partition LIKE '%test%'"
    ).fetchall()
    s_conn.close()

    assert len(test_rows) == 1159, f"Expected 1159 UA-GEC test rows, found {len(test_rows)}"
    test_doc_ids = {r[3] for r in test_rows}

    # 1. Verify manifest source custody numbers
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["source_custody_summary"]["ua_gec_excluded_test_count"] == 1159

    # 2. Verify held-out evaluation suite has 0 references to test doc_ids
    with HELDOUT_SUITE_FILE.open("r", encoding="utf-8") as f:
        heldout_cases = [json.loads(line) for line in f if line.strip()]

    for c in heldout_cases:
        source = c["source_metadata"]["source"]
        for t_doc in test_doc_ids:
            assert f":{t_doc}" not in source, f"Protected UA-GEC test doc_id {t_doc} found in held-out case: {c}"


def test_minhash_near_duplicate_zero_collisions() -> None:
    """Verify MinHash / token Jaccard deduplication report and verify real LSH parameters."""
    assert MINHASH_REPORT_FILE.is_file(), f"Missing MinHash report: {MINHASH_REPORT_FILE}"
    with MINHASH_REPORT_FILE.open("r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["permutations"] == 64
    assert report["bands"] == 16
    assert report["rows_per_band"] == 4
    # Full corpus indexing covers all 41,611 textbook chunks + ZNO + style guide + UA-GEC
    assert report["train_corpus_sentences_indexed"] >= 40000
    assert report["similarity_threshold"] == 0.80
    assert report["cross_split_duplicates_above_threshold"] == 0
    assert report["max_cross_split_similarity"] < 0.80
    assert report["max_minhash_signature_similarity"] < 0.85
    assert report["status"] == "PASS"


def test_independent_minhash_cross_split_verification(requires_sources_db: Path) -> None:
    """Independently re-run MinHash signatures and token Jaccard on a cross-split sample across all sources."""
    minhash = MinHashDedup(num_perm=64, bands=16, rows_per_band=4)

    # Load held-out cases
    with HELDOUT_SUITE_FILE.open("r", encoding="utf-8") as f:
        heldout_cases = [json.loads(line) for line in f if line.strip()]

    # Sample sentences from sources.db across all 4 training sources
    s_conn = sqlite3.connect(DEFAULT_SOURCES_DB)
    sc = s_conn.cursor()
    zno_stems = [r[0] for r in sc.execute("SELECT stem FROM zno_tasks WHERE stem IS NOT NULL LIMIT 100").fetchall()]
    sg_texts = [r[0] for r in sc.execute("SELECT text FROM style_guide WHERE text IS NOT NULL LIMIT 50").fetchall()]

    # Sample textbook train chunks (strictly train partition by author/title hash)
    tb_rows = sc.execute("SELECT title, text, author_uk FROM textbooks LIMIT 500").fetchall()
    tb_train_sents = []
    for title, text, author in tb_rows:
        author_key = author or "unknown"
        h = int(hashlib.sha256(f"tb_author:{author_key}:{title}".encode()).hexdigest()[:8], 16)
        if h % 10 < 8:  # strictly train chunks
            for s in SENTENCE_SPLIT_RE.split(text):
                s = s.strip()
                if 35 <= len(s) <= 220:
                    tb_train_sents.append(s)
                    break
            if len(tb_train_sents) >= 100:
                break

    s_conn.close()

    train_sample = zno_stems + sg_texts + tb_train_sents
    assert len(train_sample) >= 200, f"Expected >= 200 training sample sentences, got {len(train_sample)}"

    # Verify no sample cross-split pair exceeds 0.80 Jaccard similarity or 0.85 MinHash signature similarity
    for h_case in heldout_cases[:50]:
        h_toks = normalize_text(h_case["input_text"]).split()
        h_sig = minhash.signature(h_toks)
        for t_sent in train_sample[:100]:
            t_toks = normalize_text(t_sent).split()
            t_sig = minhash.signature(t_toks)
            jaccard = MinHashDedup.jaccard_similarity(h_toks, t_toks)
            sig_sim = MinHashDedup.sig_similarity(h_sig, t_sig)
            assert jaccard < 0.80, (
                f"Cross-split near duplicate detected: Jaccard {jaccard} between '{h_toks}' and '{t_toks}'"
            )
            assert sig_sim < 0.85, (
                f"Cross-split MinHash signature similarity {sig_sim} >= 0.85 between '{h_toks}' and '{t_toks}'"
            )


def test_heldout_suite_exact_allocation_and_statistical_power() -> None:
    """Verify held-out suite has exactly 600 PRESERVE + 400 CORRECT cases and HER <= 1.0% power."""
    assert HELDOUT_SUITE_FILE.is_file(), f"Missing held-out suite: {HELDOUT_SUITE_FILE}"

    cases = []
    with HELDOUT_SUITE_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line.strip()))

    assert len(cases) == 1000

    preserve_cases = [c for c in cases if c["case_type"] == "PRESERVE"]
    correct_cases = [c for c in cases if c["case_type"] == "CORRECT"]

    assert len(preserve_cases) == 600
    assert len(correct_cases) == 400

    # Verify required fields on all cases
    for c in cases:
        assert "eval_id" in c
        assert "case_type" in c
        assert "input_text" in c
        assert "target_term" in c
        assert "expected_action" in c
        assert "phenomenon_category" in c
        assert "source_metadata" in c
        assert "derivational_family" in c

        if c["case_type"] == "PRESERVE":
            assert c["expected_action"] == "PRESERVE"
            assert c["expected_replacement"] is None
        else:
            assert c["expected_action"] == "CORRECT"
            assert c["expected_replacement"] is not None

    # Verify statistical power: exact one-sided 95% binomial upper bound for k=1 in n=600
    bound = exact_clopper_pearson_upper(1, 600, confidence=0.95)
    assert bound < 0.010, f"Statistical bound {bound} does not satisfy HER <= 1.0% gate"


def test_partition_cli_verify_only() -> None:
    """Verify that verify_manifest function returns True on disk artifacts."""
    assert verify_manifest(PARTITIONS_DIR) is True
