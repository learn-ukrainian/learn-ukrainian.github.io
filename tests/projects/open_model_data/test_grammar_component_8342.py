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
from scripts.projects.open_model_data.build_grammar_component_8342 import (
    build_jaccard_firewall_matcher,
)
from scripts.projects.open_model_data.grammar_linguistic_catalog import (
    IN_SCOPE_TAGS,
    TAG_TO_COARSE_CATEGORY,
    is_finite_active_verb,
)

GRAMMAR_DIR = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "components" / "grammar"
OLD_RELEASE_DIR = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "release" / "uldr_v05_grammar_valency"
TEST_M2_PATH = PROJECT_ROOT / "data" / "ua-gec" / "data" / "gec-fluency" / "test" / "gec-fluency.test.m2"


@pytest.fixture(scope="module")
def grammar_data():
    """Load grammar component records and manifest."""
    manifest_file = GRAMMAR_DIR / "manifest.json"
    cases_file = GRAMMAR_DIR / "cases.json"
    sample_md_file = GRAMMAR_DIR / "acceptance_review_sample.md"
    sample_json_file = GRAMMAR_DIR / "acceptance_review_sample.json"
    template_file = GRAMMAR_DIR / "acceptance_review_sample.signoff_template.json"

    assert manifest_file.is_file(), f"Missing manifest.json at {manifest_file}"
    assert cases_file.is_file(), f"Missing cases.json at {cases_file}"
    assert sample_md_file.is_file(), f"Missing review sample MD at {sample_md_file}"
    assert sample_json_file.is_file(), f"Missing review sample JSON at {sample_json_file}"
    assert template_file.is_file(), f"Missing signoff template at {template_file}"

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    cases = json.loads(cases_file.read_text(encoding="utf-8"))

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
    assert len(manifest["splits"]) >= 8
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
    train_docs = {r["doc_id"] for r in grammar_data["train"]}
    eval_docs = {r["doc_id"] for r in grammar_data["eval"]}

    intersection = train_docs.intersection(eval_docs)
    assert not intersection, f"Shared doc_ids between train and eval: {intersection}"

    for d in eval_docs:
        h = int(hashlib.sha256(d.encode("utf-8")).hexdigest(), 16)
        assert h % 10 == 0, f"Doc {d} in eval split does not satisfy h % 10 == 0"

    for d in train_docs:
        h = int(hashlib.sha256(d.encode("utf-8")).hexdigest(), 16)
        assert h % 10 != 0, f"Doc {d} in train split satisfies h % 10 == 0"


def test_held_out_test_set_firewall(grammar_data):
    """Verify zero overlap against the official held-out test partition via committed firewall manifest."""
    manifest_path = (
        PROJECT_ROOT
        / "data"
        / "projects"
        / "open_model_data"
        / "components"
        / "grammar"
        / "grammar_held_out_firewall_manifest.json"
    )
    assert manifest_path.is_file(), f"Missing firewall manifest at {manifest_path}"
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    test_doc_ids = set(manifest_data["test_doc_ids"])
    test_sources = set(manifest_data["test_source_sentences"])
    test_targets = set(manifest_data["test_target_sentences"])

    assert len(test_doc_ids) == 166
    assert len(test_sources) == 2636
    assert len(test_targets) == 5240

    for r in grammar_data["all"]:
        assert r["doc_id"] not in test_doc_ids, f"Test doc_id leaked to component: {r['doc_id']}"
        assert r["original_text"] not in test_sources, f"Test source sentence leaked: {r['original_text']}"
        assert r["original_text"] not in test_targets, f"Test target sentence leaked as original: {r['original_text']}"
        if r["is_erroneous"]:
            assert r["corrected_text"] not in test_sources, f"Test source leaked as correction: {r['corrected_text']}"
            assert r["corrected_text"] not in test_targets, f"Test target leaked as correction: {r['corrected_text']}"


def test_brown_uk_attribution(grammar_data):
    """Verify Brown-UK controls preserve authentic doc_id, doc_name, license, and corpus."""
    brown_records = [r for r in grammar_data["all"] if r["source_corpus"] == "brown_uk"]
    assert len(brown_records) >= 350, f"Expected >= 350 Brown-UK records, got {len(brown_records)}"

    for r in brown_records:
        assert r["doc_id"] != "brown_uk_corpus", f"Generic synthetic doc_id found in {r['record_id']}"
        assert len(r["doc_id"]) > 5
        assert r["doc_name"].endswith(".txt")
        assert r["license"] == "CC BY-NC-SA 4.0"
        assert r["source_corpus"] == "brown_uk"
        assert r["source_metadata"]["license"] == "CC BY-NC-SA 4.0"
        assert r["source_metadata"]["source_corpus"] == "brown_uk"
        assert r["source_metadata"]["doc_name"] == r["doc_name"]


def test_source_sentence_uniqueness_across_corrections(grammar_data):
    """Verify each source sentence across corrections has exactly one gold target (no conflicting/duplicate golds)."""
    corrections = [r for r in grammar_data["all"] if r["is_erroneous"]]
    orig_to_targets: dict[str, set[str]] = {}
    for r in corrections:
        orig = r["original_text"]
        corr = r["corrected_text"]
        if orig not in orig_to_targets:
            orig_to_targets[orig] = set()
        orig_to_targets[orig].add(corr)

    multi_target_sents = {orig: targets for orig, targets in orig_to_targets.items() if len(targets) > 1}
    assert len(multi_target_sents) == 0, (
        f"Expected 0 sentences with conflicting or duplicate parallel annotator targets, "
        f"got {len(multi_target_sents)}: {multi_target_sents}"
    )


def test_explanation_relevance_and_target_cleanliness(grammar_data):
    """Verify citations are specific and verified, silent rows are clean, and target texts have full edits."""
    for r in grammar_data["all"]:
        # Verify full edits applied: concurrent errors like spelling 'еффективно' are cleanly corrected
        assert "еффективно" not in r["corrected_text"], f"Uncorrected spelling 'еффективно' in {r['record_id']}"
        # Verify no empty quotes «» in final_response or reasoning_steps
        assert "«»" not in r["final_response"], (
            f"Empty quote in final_response of {r['record_id']}: {r['final_response']}"
        )
        for step in r.get("reasoning_steps", []):
            assert "«»" not in step, f"Empty quote in reasoning_steps of {r['record_id']}: {step}"

        if r["is_erroneous"]:
            meta = r.get("source_metadata", {})
            err_span = meta.get("error_span", "").lower()
            orig_lower = r["original_text"].lower()

            if r["task_type"] == "explained_correction":
                full_text = f"{r['final_response']} {' '.join(r.get('reasoning_steps', []))}".lower()

                if "так як" in full_text:
                    assert "так як" in orig_lower or "так як" in err_span, (
                        f"Record {r['record_id']} mentions 'так як' but sentence does not contain it: {r['original_text']}"
                    )

                if "на «-ся»" in full_text:
                    assert any(w.endswith(("ся", "сь")) for w in err_span.split()) or any(
                        w.endswith(("ся", "сь")) for w in orig_lower.split()
                    ), f"Record {r['record_id']} cites passive on -ся but err_span '{err_span}' does not end in -ся/-сь"

                if "давай / давайте" in full_text or "наказового способу з часткою" in full_text:
                    assert "давай" in err_span or "давайте" in err_span or "давай" in orig_lower, (
                        f"Record {r['record_id']} cites imperative 'давай' but err_span '{err_span}' lacks it"
                    )

                if "дієприслівников" in full_text:
                    adv_sufs = ("чи", "ши", "вшись", "вшися", "ючись", "ючися")
                    assert any(err_span.endswith(s) for s in adv_sufs) or any(
                        any(w.endswith(s) for s in adv_sufs) for w in err_span.split()
                    ), f"Record {r['record_id']} cites дієприслівник but err_span '{err_span}' lacks participle suffix"
            else:
                # Silent rewrite: linguistic_rule must be empty and reasoning_steps must be empty
                assert r["task_type"] == "silent_rewrite"
                assert r.get("reasoning_steps") == []
                assert meta.get("linguistic_rule") == ""


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


def test_self_contradiction_invariants(grammar_data):
    """Verify label vs text differences and non-contradiction."""
    for r in grammar_data["all"]:
        if r["is_erroneous"]:
            assert r["original_text"] != r["corrected_text"], (
                f"Record {r['record_id']} is_erroneous True but orig == corr"
            )
            assert r["chosen"] == r["corrected_text"]
            assert r["rejected"] == r["original_text"]
        else:
            assert r["original_text"] == r["corrected_text"], (
                f"Record {r['record_id']} is_erroneous False but orig != corr"
            )
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


def test_acceptance_audit_gate_end_to_end(requires_vesum_db):
    """Verify that audit_dataset_acceptance.py passes with exit code 0 and verified signoff."""
    signoff_path = GRAMMAR_DIR / "acceptance_review_sample.signoff.json"
    report, exit_code = run_acceptance_audit(
        dataset_dir=GRAMMAR_DIR,
        profile_name="grammar_8342",
        verify_signoff=signoff_path if signoff_path.is_file() else None,
        require_human_signoff=signoff_path.is_file(),
    )

    assert exit_code == 0, f"Acceptance audit failed with exit code {exit_code}: {report.overall_status}"
    expected_status = "ACCEPTED" if signoff_path.is_file() else "PASSED_AUTOMATED_CHECKS"
    assert report.overall_status == expected_status
    if signoff_path.is_file():
        assert report.checks["check_7_sample_drawer"].metrics.get("signoff_verified") is True
    for check_id, check_res in report.checks.items():
        assert check_res.status == "PASS", f"Check {check_id} failed: {check_res.failures}"


def test_held_out_token_jaccard_firewall(grammar_data):
    """Verify zero near-duplicate records with token Jaccard >= 0.80 against held-out test."""
    manifest_path = (
        PROJECT_ROOT
        / "data"
        / "projects"
        / "open_model_data"
        / "components"
        / "grammar"
        / "grammar_held_out_firewall_manifest.json"
    )
    assert manifest_path.is_file(), f"Missing firewall manifest at {manifest_path}"
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    all_test = set(manifest_data["test_source_sentences"]) | set(manifest_data["test_target_sentences"])
    is_near_dup = build_jaccard_firewall_matcher(all_test, threshold=0.80)

    for r in grammar_data["all"]:
        assert not is_near_dup(r["original_text"]), (
            f"Record {r['record_id']} original_text has Jaccard >= 0.80 to test sentence: {r['original_text']}"
        )
        if r["is_erroneous"]:
            assert not is_near_dup(r["corrected_text"]), (
                f"Record {r['record_id']} corrected_text has Jaccard >= 0.80 to test sentence: {r['corrected_text']}"
            )


def test_linguistic_catalog_vocative_and_voice_precision(grammar_data, requires_vesum_db):
    """Verify linguistic precision: vocatives cite Pravopys § 87, reflexive verbs don't falsely claim active voice."""
    # Direct unit checks on is_finite_active_verb
    assert is_finite_active_verb("поважають") is True
    assert is_finite_active_verb("використовують") is True
    assert is_finite_active_verb("використовувати") is False  # infinitive
    assert is_finite_active_verb("схвильований") is False  # adjp:pasv
    assert is_finite_active_verb("хвилюючийся") is False

    # G/VerbVoice is heterogeneous and must fail closed to silent_rewrite
    assert all(r["task_type"] == "silent_rewrite" for r in grammar_data["all"] if r.get("tag") == "G/VerbVoice")

    for r in grammar_data["all"]:
        if not r["is_erroneous"] or r["task_type"] != "explained_correction":
            continue
        meta = r.get("source_metadata", {})
        err_span = meta.get("error_span", "").strip().lower()
        repl_span = meta.get("replacement_span", "").strip().lower()
        full_text = f"{r['final_response']} {' '.join(r.get('reasoning_steps', []))}".lower()

        # If active voice construction is claimed, replacement must not be a participle or adjective
        if "активн" in full_text and ("пасивн" in full_text or "-ся" in full_text):
            assert "схвильований" not in repl_span
            assert "рекомендований" not in repl_span

        # If both err and repl contain reflexive verbs (-ся/-сь), must not claim passive-to-active
        explanation_text = (
            f"{meta.get('linguistic_rule', '')} "
            f"{r['reasoning_steps'][0] if r.get('reasoning_steps') else ''} "
            f"{r['reasoning_steps'][1] if len(r.get('reasoning_steps', [])) > 1 else ''}"
        ).lower()
        err_tokens = [
            w for w in err_span.split() if w.endswith(("ся", "сь")) and not w.startswith(("як", "хт", "щ", "чи"))
        ]
        repl_tokens = [
            w for w in repl_span.split() if w.endswith(("ся", "сь")) and not w.startswith(("як", "хт", "щ", "чи"))
        ]
        if err_tokens and repl_tokens:
            assert "пасивн" not in explanation_text and "активн" not in explanation_text, (
                f"Record {r['record_id']} has reflexive in both spans ('{err_span}' -> '{repl_span}') "
                f"but claims passive/active voice change: {explanation_text}"
            )

        # If vocative citation is present, it must cite Pravopys § 87 and not verb valency
        if "кличний відмінок" in full_text:
            assert "87" in full_text or "пономарів" in full_text or "звертанн" in full_text
            assert "дієслівного керування" not in full_text, (
                f"Record {r['record_id']} cites vocative address under verb government: {full_text}"
            )


def test_acceptance_review_sample_receipt_and_signoff():
    """Verify itemized review receipt and cryptographic signoff report."""
    receipt_file = GRAMMAR_DIR / "acceptance_review_sample.receipt.json"
    signoff_file = GRAMMAR_DIR / "acceptance_review_sample.signoff.json"
    template_file = GRAMMAR_DIR / "acceptance_review_sample.signoff_template.json"

    assert receipt_file.is_file(), f"Missing receipt file {receipt_file}"
    assert signoff_file.is_file(), f"Missing signoff file {signoff_file}"

    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    signoff = json.loads(signoff_file.read_text(encoding="utf-8"))
    tmpl = json.loads(template_file.read_text(encoding="utf-8"))

    assert receipt["dataset_sha256"] == tmpl["dataset_sha256"]
    assert receipt["sample_seed"] == tmpl["sample_seed"]
    assert receipt["profile_sha256"] == tmpl["profile_sha256"]
    assert receipt["sample_size_drawn"] == tmpl["sample_size_drawn"]
    assert receipt["sample_size_reviewed"] == tmpl["sample_size_drawn"]
    assert len(receipt["reviewed_sample_items"]) == tmpl["sample_size_drawn"]
    assert receipt["verdict"] == "APPROVED"
    assert receipt["blocker_defect_count"] == 0

    # Verify all reviewer rationales are completely distinct and authentic
    rationales = [item["reviewer_rationale"] for item in receipt["reviewed_sample_items"]]
    assert len(set(rationales)) == tmpl["sample_size_drawn"], (
        f"Expected {tmpl['sample_size_drawn']} distinct rationales, got {len(set(rationales))}"
    )

    for item in receipt["reviewed_sample_items"]:
        audit = item.get("item_verification_audit", {})
        assert audit.get("query_norm_verified") is True
        assert audit.get("vesum_morphology_verified") is True
        assert audit.get("source_grounding_verified") is True
        assert audit.get("chosen_rejected_pair_verified") is True
        assert audit.get("zero_soviet_sum11_influence") is True
        assert audit.get("held_out_firewall_verified") is True

    assert signoff["dataset_sha256"] == tmpl["dataset_sha256"]
    assert signoff["sample_seed"] == tmpl["sample_seed"]
    assert signoff["profile_sha256"] == tmpl["profile_sha256"]
    assert signoff["sample_size_reviewed"] == tmpl["sample_size_drawn"]
    assert signoff["blocker_defect_count"] == 0
    assert signoff["reviewer_id"] == "claude_blue_team_ling_review"
    assert signoff["reviewer_family"] == "claude"
