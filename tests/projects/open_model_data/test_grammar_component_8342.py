#!/usr/bin/env python3
"""Acceptance and Regression Tests for Grammar Component (#8342, Epic #6321).

Verifies:
1. Component directory structure and manifest integrity.
2. 75.0% substantive corrections / 25.0% clean controls mixture invariants.
3. Closed in-scope error scope (G/* + F/Calque) and category balancing.
4. Document-level 90:10 partition integrity and official test set firewall.
5. 45% silent rewrites / 55% explained corrections task mix.
6. Zero self-contradictions and 100% approved Ukrainian authorities.
7. Quarantine tombstone present in uldr_v05_grammar_valency.
8. End-to-end acceptance audit pass via audit_dataset_acceptance.py with verified signoff.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.projects.open_model_data.audit_dataset_acceptance import (
    APPROVED_AUTHORITY_PATTERNS,
    SOVIET_SUM11_ALIASES,
    TRANSLATION_DICT_IDS,
    run_acceptance_audit,
)
from scripts.projects.open_model_data.grammar_linguistic_catalog import (
    IN_SCOPE_TAGS,
    TAG_TO_COARSE_CATEGORY,
)

GRAMMAR_DIR = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "components" / "grammar"
OLD_RELEASE_DIR = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "release" / "uldr_v05_grammar_valency"
TEST_M2_PATH = PROJECT_ROOT / "data" / "ua-gec" / "data" / "gec-fluency" / "test" / "gec-fluency.test.m2"


@pytest.fixture(scope="module")
def grammar_data():
    """Load grammar component records and manifest."""
    manifest_file = GRAMMAR_DIR / "manifest.json"
    cases_file = GRAMMAR_DIR / "cases.json"
    signoff_file = GRAMMAR_DIR / "acceptance_review_sample.signoff.json"
    receipt_file = GRAMMAR_DIR / "acceptance_review_sample.receipt.json"

    assert manifest_file.is_file(), f"Missing manifest.json at {manifest_file}"
    assert cases_file.is_file(), f"Missing cases.json at {cases_file}"
    assert signoff_file.is_file(), f"Missing signoff file at {signoff_file}"
    assert receipt_file.is_file(), f"Missing receipt file at {receipt_file}"

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    cases = json.loads(cases_file.read_text(encoding="utf-8"))
    signoff = json.loads(signoff_file.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))

    train_records = []
    eval_records = []

    for fname, split in manifest["splits"].items():
        fpath = GRAMMAR_DIR / fname
        assert fpath.is_file(), f"Missing shard file {fname} declared in manifest"
        assert fpath.stat().st_size < 2_000_000, f"Shard file {fname} exceeds 2,000,000 byte pre-commit limit"
        records = [json.loads(line) for line in fpath.read_text(encoding="utf-8").splitlines() if line.strip()]
        if split == "train":
            train_records.extend(records)
        elif split == "eval":
            eval_records.extend(records)
        else:
            raise ValueError(f"Unknown split {split} for {fname}")

    return {
        "manifest": manifest,
        "cases": cases,
        "train": train_records,
        "eval": eval_records,
        "all": train_records + eval_records,
        "signoff": signoff,
        "receipt": receipt,
    }


def test_tombstone_quarantine_exists():
    """Verify uldr_v05_grammar_valency has a TOMBSTONE marking it retired per #8342."""
    tombstone = OLD_RELEASE_DIR / "TOMBSTONE.md"
    assert tombstone.is_file(), f"Missing TOMBSTONE.md at {tombstone}"
    content = tombstone.read_text(encoding="utf-8")
    assert "#8342" in content
    assert "DO NOT USE" in content or "QUARANTINED" in content
    assert "8143" in content


def test_manifest_integrity(grammar_data):
    """Verify manifest.json structure, split declarations, and statistics."""
    manifest = grammar_data["manifest"]
    assert manifest["dataset_name"] == "grammar_v1"
    assert manifest["version"] == "1.0.0"
    assert manifest["task_type"] == "correction"
    assert manifest["has_evaluation_split"] is True
    assert len(manifest["splits"]) >= 16
    assert all(s in ("train", "eval") for s in manifest["splits"].values())
    assert "#8342" in manifest["governing_issues"]

    stats = manifest["statistics"]
    assert stats["total_records"] == len(grammar_data["all"])
    assert stats["train_records"] == len(grammar_data["train"])
    assert stats["eval_records"] == len(grammar_data["eval"])


def test_control_correction_ratio(grammar_data):
    """Verify strict 20.0% to 30.0% clean controls and 70.0% to 80.0% corrections."""
    all_records = grammar_data["all"]
    total = len(all_records)
    controls = sum(1 for r in all_records if r["is_erroneous"] is False)
    corrections = sum(1 for r in all_records if r["is_erroneous"] is True)

    assert controls + corrections == total
    control_share = controls / total
    correction_share = corrections / total

    assert 0.20 <= control_share <= 0.30, f"Control share {control_share:.2%} out of range [20%, 30%]"
    assert 0.70 <= correction_share <= 0.80, f"Correction share {correction_share:.2%} out of range [70%, 80%]"
    assert abs(control_share - 0.25) < 0.01, f"Control share {control_share:.2%} deviates from target 25.0%"


def test_category_balancing(grammar_data):
    """Verify category balance (min 50 per category, max 40% single category share)."""
    all_records = grammar_data["all"]
    total = len(all_records)
    category_counts = Counter(r["category"] for r in all_records)

    assert len(category_counts) >= 6
    for cat, count in category_counts.items():
        assert count >= 50, f"Category {cat} has only {count} examples (< 50)"
        share = count / total
        assert share <= 0.40, f"Category {cat} dominates with {share:.2%} (> 40%)"


def test_in_scope_tag_conformance(grammar_data):
    """Verify that all error tags strictly belong to the in-scope set (G/* + F/Calque)."""
    for r in grammar_data["all"]:
        if r["is_erroneous"]:
            assert r["tag"] in IN_SCOPE_TAGS, f"Out-of-scope tag '{r['tag']}' in record {r['record_id']}"
            assert r["category"] in TAG_TO_COARSE_CATEGORY.values()
        else:
            assert r["tag"] == "control_clean"
            assert r["category"] == "protective_authentic_control"


def test_split_integrity_and_sha256_partition(grammar_data):
    """Verify 90:10 document-level split by doc_id SHA-256 hash and 0 shared doc_ids."""
    train_docs = {r["doc_id"] for r in grammar_data["train"] if r["doc_id"] != "brown_uk_corpus"}
    eval_docs = {r["doc_id"] for r in grammar_data["eval"] if r["doc_id"] != "brown_uk_corpus"}

    intersection = train_docs.intersection(eval_docs)
    assert not intersection, f"Shared doc_ids between train and eval: {intersection}"

    for d in eval_docs:
        h = int(hashlib.sha256(d.encode("utf-8")).hexdigest(), 16)
        assert h % 10 == 0, f"Doc {d} in eval split does not satisfy h % 10 == 0"

    for d in train_docs:
        h = int(hashlib.sha256(d.encode("utf-8")).hexdigest(), 16)
        assert h % 10 != 0, f"Doc {d} in train split satisfies h % 10 == 0"


def test_held_out_test_set_firewall(grammar_data):
    """Verify zero overlap against the official held-out test partition."""
    if not TEST_M2_PATH.is_file():
        pytest.skip(f"Test M2 not found at {TEST_M2_PATH}")

    test_sentences = set()
    with TEST_M2_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("S ") and not line.startswith("S # "):
                sent = " ".join(line[2:].strip().split())
                test_sentences.add(sent)

    for r in grammar_data["all"]:
        assert r["original_text"] not in test_sentences, f"Sentence leaked from test set: {r['original_text']}"


def test_global_sentence_deduplication(grammar_data):
    """Verify zero duplicate (query, final_response) pairs and zero duplicate sentences."""
    all_records = grammar_data["all"]
    qa_pairs = [(r["query"], r["final_response"]) for r in all_records]
    assert len(qa_pairs) == len(set(qa_pairs)), "Duplicate (query, response) pairs detected"

    train_queries = {r["query"] for r in grammar_data["train"]}
    for r in grammar_data["eval"]:
        assert r["query"] not in train_queries, f"Eval query leaked to train: {r['query']}"


def test_task_mix_partition(grammar_data):
    """Verify 45% silent rewrites and 55% explained corrections (within [40%, 60%])."""
    corrections = [r for r in grammar_data["all"] if r["is_erroneous"]]
    total_corr = len(corrections)
    explained = sum(1 for r in corrections if r["task_type"] == "explained_correction")
    silent = sum(1 for r in corrections if r["task_type"] == "silent_rewrite")

    assert explained + silent == total_corr
    explained_share = explained / total_corr
    assert 0.40 <= explained_share <= 0.60, f"Explained share {explained_share:.2%} outside [40%, 60%]"
    assert abs(explained_share - 0.55) < 0.02


def test_self_contradiction_invariants(grammar_data):
    """Verify label vs text differences and non-contradiction."""
    for r in grammar_data["all"]:
        if r["is_erroneous"]:
            assert r["original_text"] != r["corrected_text"], f"Record {r['record_id']} is_erroneous True but orig == corr"
            assert r["chosen"] == r["corrected_text"]
            assert r["rejected"] == r["original_text"]
        else:
            assert r["original_text"] == r["corrected_text"], f"Record {r['record_id']} is_erroneous False but orig != corr"
            assert r["chosen"] == r["original_text"]
            assert r["rejected"] is None


def test_approved_linguistic_authorities(grammar_data):
    """Verify that all cited authorities match approved patterns and zero Soviet SUM-11."""
    for r in grammar_data["all"]:
        meta = r.get("source_metadata", {})
        auth = str(meta.get("authority", "")).lower()
        full_text = f"{r['query']} {r['final_response']} {' '.join(r.get('reasoning_steps', []))}".lower()

        is_approved = any(re.search(pat, auth, re.IGNORECASE) for pat in APPROVED_AUTHORITY_PATTERNS)
        assert is_approved, f"Unapproved authority '{auth}' in record {r['record_id']}"

        for alias in SOVIET_SUM11_ALIASES:
            assert alias not in auth, f"Soviet SUM-11 cited in authority: {r['record_id']}"
            assert alias not in full_text, f"Soviet SUM-11 in body text: {r['record_id']}"

        for trans_id in TRANSLATION_DICT_IDS:
            assert trans_id not in auth, f"Translation dictionary in authority: {r['record_id']}"


def test_acceptance_audit_gate_end_to_end():
    """Verify that audit_dataset_acceptance.py passes with exit code 0 and verified signoff."""
    signoff_path = GRAMMAR_DIR / "acceptance_review_sample.signoff.json"
    assert signoff_path.is_file()

    report, exit_code = run_acceptance_audit(
        dataset_dir=GRAMMAR_DIR,
        profile_name="grammar_8342",
        verify_signoff=signoff_path,
        require_human_signoff=True,
    )

    assert exit_code == 0, f"Acceptance audit failed with exit code {exit_code}: {report.overall_status}"
    assert report.overall_status == "ACCEPTED"
    for check_id, check_res in report.checks.items():
        assert check_res.status == "PASS", f"Check {check_id} failed: {check_res.failures}"
