#!/usr/bin/env python3
"""Acceptance and Regression Tests for Decolonization Component (#8340, Epic #6321).

Verifies:
1. Dataset files existence and manifest integrity.
2. Exact record counts (500 records: 400 train, 100 eval; 250 phenomena).
3. 70% substantive corrections, 30% protective authentic controls.
4. Category balance across lexical, syntactic, prepositional, and protective.
5. Zero self-contradictions (orig != corr for errors, orig == corr for controls, target term present).
6. 100% disjoint held-out eval partition (0 query leakage, 0 target term leakage, 0 high containment).
7. Epic source rules (approved modern authorities, 0 Soviet SUM-11 normative citations).
8. End-to-end acceptance audit pass via audit_dataset_acceptance.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.audit_dataset_acceptance import (
    VESUM_DB_PATH,
    LinguisticNormalizer,
    _resolve_db_path,
)
from scripts.projects.open_model_data.paths import DECOLONIZATION_DIR


@pytest.fixture(scope="module")
def decolonization_data():
    """Load all records and manifest for component testing."""
    manifest_file = DECOLONIZATION_DIR / "manifest.json"
    cases_file = DECOLONIZATION_DIR / "cases.json"
    train_file = DECOLONIZATION_DIR / "decolonization_train.jsonl"
    eval_file = DECOLONIZATION_DIR / "decolonization_eval.jsonl"

    assert manifest_file.is_file(), f"Missing manifest.json at {manifest_file}"
    assert cases_file.is_file(), f"Missing cases.json at {cases_file}"
    assert train_file.is_file(), f"Missing decolonization_train.jsonl at {train_file}"
    assert eval_file.is_file(), f"Missing decolonization_eval.jsonl at {eval_file}"

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    cases = json.loads(cases_file.read_text(encoding="utf-8"))

    train_records = [json.loads(line) for line in train_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    eval_records = [json.loads(line) for line in eval_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    return {
        "manifest": manifest,
        "cases": cases,
        "train": train_records,
        "eval": eval_records,
        "all": train_records + eval_records,
    }


def test_manifest_and_catalog_integrity(decolonization_data):
    """Verify manifest metadata and cases catalog alignment."""
    manifest = decolonization_data["manifest"]
    cases = decolonization_data["cases"]
    train = decolonization_data["train"]
    eval_recs = decolonization_data["eval"]

    assert manifest["dataset_name"] == "decolonization_v1"
    assert manifest["task_type"] == "correction"
    assert manifest["has_evaluation_split"] is True
    assert manifest["splits"]["decolonization_train.jsonl"] == "train"
    assert manifest["splits"]["decolonization_eval.jsonl"] == "eval"

    assert len(cases) == 250
    assert len(train) == 400
    assert len(eval_recs) == 100

    stats = manifest["statistics"]
    assert stats["total_records"] == 500
    assert stats["train_records"] == 400
    assert stats["eval_records"] == 100
    assert stats["total_phenomena"] == 250
    assert stats["substantive_corrections"] == 350
    assert stats["protective_controls"] == 150


def test_real_content_share_and_category_balance(decolonization_data):
    """Verify 70/30 substantive/protective split and 4 balanced categories."""
    records = decolonization_data["all"]
    assert len(records) == 500

    corrections = sum(1 for r in records if r["is_erroneous"])
    controls = sum(1 for r in records if not r["is_erroneous"])

    assert corrections == 350  # 70%
    assert controls == 150  # 30%

    cat_counts = {}
    for r in records:
        cat = r["category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    expected_categories = {
        "calque_lexical": 120,
        "calque_syntactic": 130,
        "calque_prepositional": 100,
        "protective_authentic": 150,
    }
    assert cat_counts == expected_categories


def test_zero_contradictions(decolonization_data):
    """Verify that erroneous rows have diffs and protective controls are unchanged."""
    records = decolonization_data["all"]

    for r in records:
        orig = r["original_text"].strip()
        corr = r["corrected_text"].strip()
        if r["is_erroneous"]:
            assert orig != corr, f"Record {r['record_id']} is erroneous but original_text == corrected_text"
            assert r["chosen"] == corr
            assert r["rejected"] == orig
        else:
            assert orig == corr, f"Record {r['record_id']} is protective control but original_text != corrected_text"
            assert r["chosen"] == orig


def test_zero_train_eval_leakage(decolonization_data):
    """Verify 100% disjoint train and eval partitions under aspect normalization."""
    normalizer = LinguisticNormalizer(VESUM_DB_PATH)

    def norm_term(t: str) -> str:
        return " ".join(normalizer.get_canonical_tokens(t))

    train = decolonization_data["train"]
    eval_recs = decolonization_data["eval"]

    train_queries = {r["query"].strip() for r in train}
    for r in eval_recs:
        assert r["query"].strip() not in train_queries, f"Query leakage in {r['record_id']}"

    train_targets = {norm_term(r["target_term"]) for r in train if r.get("target_term")}
    for r in eval_recs:
        if r.get("target_term"):
            nt = norm_term(r["target_term"])
            assert nt not in train_targets, f"Target leakage in {r['record_id']}: {r['target_term']} ({nt})"


def test_dataset_acceptance_audit_passes():
    """Verify that audit_dataset_acceptance.py runs and passes with exit code 0."""
    audit_script = REPO_ROOT / "scripts" / "projects" / "open_model_data" / "audit_dataset_acceptance.py"
    cmd = [
        sys.executable,
        str(audit_script),
        str(DECOLONIZATION_DIR),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert proc.returncode == 0, f"Acceptance audit failed (exit {proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
    assert "OVERALL STATUS: PASSED_AUTOMATED_CHECKS" in proc.stdout


def test_decol_syn_014_antonenko_davydovych_norm(decolonization_data):
    """Verify that decol_syn_014 follows Antonenko-Davydovych §77: targets таким способом, corrects таким шляхом."""
    cases = decolonization_data["cases"]
    syn_014 = next((c for c in cases if c["case_id"] == "decol_syn_014"), None)
    assert syn_014 is not None, "decol_syn_014 not found in cases.json"

    assert syn_014["target_term"] == "таким способом"
    assert syn_014["russian_copy"] == "таким шляхом"
    assert "таким способом" in syn_014["ukrainian_proper"]
    assert "таким чином" in syn_014["ukrainian_proper"]

    # Verify train records for decol_syn_014
    train_records = [r for r in decolonization_data["train"] if r.get("target_term") == "таким способом"]
    assert len(train_records) == 2
    for r in train_records:
        assert "таким шляхом" in r["original_text"].lower()
        assert "таким способом" in r["corrected_text"].lower()
        assert "таким чином" not in r["rejected"]  # таким чином is valid standard Ukrainian, never condemned


def test_supporting_passages_all_non_null_and_authentic(decolonization_data):
    """Verify that 100% of cases (250/250) have non-null, non-empty authentic supporting passages."""
    cases = decolonization_data["cases"]
    assert len(cases) == 250

    for c in cases:
        cid = c["case_id"]
        rev = c.get("reviewer_confirmation", {})
        assert rev.get("status") == "confirmed", f"Case {cid} has status '{rev.get('status')}', expected 'confirmed'"
        assert (
            rev.get("reviewer_family") == "independent_language_review"
        ), f"Case {cid} has reviewer_family '{rev.get('reviewer_family')}', expected 'independent_language_review'"

        source_ev = rev.get("source_evidence", {})
        passage = source_ev.get("supporting_passage")
        assert passage and isinstance(passage, str) and len(passage.strip()) > 10, (
            f"Case {cid} has invalid or null supporting_passage: {passage!r}"
        )
        locus = source_ev.get("locus")
        assert locus and isinstance(locus, str), f"Case {cid} missing locus"


def test_adversarial_probes_and_fail_closed():
    """Verify fail-closed behavior on adversarial probes and strict UA-GEC phrase alignment (CF-R6 Finding 1 & 3)."""
    import sqlite3

    from scripts.projects.open_model_data.audit_dataset_acceptance import DEFAULT_SOURCES_DB, VESUM_DB_PATH
    from scripts.projects.open_model_data.build_decolonization_cases import (
        make_reviewer_confirmation,
        query_source_evidence,
        validate_ua_gec_phrase,
    )

    v_conn = sqlite3.connect(f"file:{VESUM_DB_PATH}?mode=ro", uri=True)
    v_cur = v_conn.cursor()

    s_conn = sqlite3.connect(f"file:{DEFAULT_SOURCES_DB}?mode=ro", uri=True)
    s_cur = s_conn.cursor()

    # 1. validate_ua_gec_phrase must reject incompatible phrases
    assert not validate_ua_gec_phrase("змогу книга", "дає змогу", v_cur)
    assert not validate_ua_gec_phrase("не давати змогу", "дає змогу", v_cur)
    assert not validate_ua_gec_phrase("дозволити все", "дозволяє", v_cur)

    # validate_ua_gec_phrase must accept authentic pairs
    assert validate_ua_gec_phrase("давати змогу", "дає змогу", v_cur)
    assert validate_ua_gec_phrase("дозволяти", "дозволяє", v_cur)
    assert validate_ua_gec_phrase("гусак", "гусак", v_cur)

    # 2. query_source_evidence must raise ValueError on unattested nonsense probes
    with pytest.raises(ValueError, match="has no verified attestation"):
        query_source_evidence(
            case_id="probe_adversarial_999",
            term="абракадабраневідома",
            copy="хххххх",
            auth="Борис Антоненко-Давидович «Як ми говоримо»",
            cat_name="calque_lexical",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
        )

    # 3. query_source_evidence must fail closed on case_id reuse with mismatched authority (Finding 1)
    with pytest.raises(ValueError, match="Mismatched authority for case 'decol_syn_032'"):
        query_source_evidence(
            case_id="decol_syn_032",
            term="мати дотичність",
            copy="мати відношення до",
            auth="Борис Антоненко-Давидович «Як ми говоримо»",
            cat_name="calque_syntactic",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
        )

    # 4. query_source_evidence must fail closed on case_id reuse with nonsense term/copy (CF-R7 Finding 1)
    with pytest.raises(ValueError, match="Mismatched target term for catalog case 'decol_syn_032'"):
        query_source_evidence(
            case_id="decol_syn_032",
            term="абракадабраневідома",
            copy="хххххх",
            auth="Катерина Городенська «Чи правильне слововживання?»",
            cat_name="calque_syntactic",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
        )

    # 4a. Probe with invalid target and valid copy (CF-R7 counterexample 1)
    with pytest.raises(ValueError, match="Mismatched target term for catalog case 'decol_syn_032'"):
        query_source_evidence(
            case_id="decol_syn_032",
            term="невірний_термін",
            copy="мати відношення до",
            auth="Катерина Городенська «Чи правильне слововживання?»",
            cat_name="calque_syntactic",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
        )

    # 4b. Probe with valid target and invalid copy (CF-R7 counterexample 2)
    with pytest.raises(ValueError, match="Mismatched russian_copy for catalog case 'decol_syn_032'"):
        query_source_evidence(
            case_id="decol_syn_032",
            term="мати дотичність",
            copy="невірна_копія",
            auth="Катерина Городенська «Чи правильне слововживання?»",
            cat_name="calque_syntactic",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
        )

    # 4c. Probe with invalid target and empty copy (CF-R7 counterexample 3)
    with pytest.raises(ValueError):
        query_source_evidence(
            case_id="decol_syn_032",
            term="невірний_термін",
            copy="",
            auth="Катерина Городенська «Чи правильне слововживання?»",
            cat_name="calque_syntactic",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
        )

    # 4d. Probe with empty authority (CF-R7 counterexample 4)
    with pytest.raises(ValueError, match="Empty authority provided for case 'decol_syn_032'"):
        query_source_evidence(
            case_id="decol_syn_032",
            term="мати дотичність",
            copy="мати відношення до",
            auth="",
            cat_name="calque_syntactic",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
        )

    # 4e. Probe with one-character target (CF-R8 Finding 1)
    with pytest.raises(ValueError, match="Mismatched target term for catalog case 'decol_syn_032'"):
        query_source_evidence(
            case_id="decol_syn_032",
            term="м",
            copy="мати відношення до",
            auth="Катерина Городенська «Чи правильне слововживання?»",
            cat_name="calque_syntactic",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
        )

    # 4f. Probe with one-character copy (CF-R8 Finding 1)
    with pytest.raises(ValueError, match="Mismatched russian_copy for catalog case 'decol_syn_032'"):
        query_source_evidence(
            case_id="decol_syn_032",
            term="мати дотичність",
            copy="м",
            auth="Катерина Городенська «Чи правильне слововживання?»",
            cat_name="calque_syntactic",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
        )

    # 4g. Probe with caller-supplied proper_list bypass attempt (CF-R8 Finding 1)
    with pytest.raises(ValueError, match="Mismatched target term for catalog case 'decol_syn_032'"):
        query_source_evidence(
            case_id="decol_syn_032",
            term="INVALID_TARGET",
            copy="мати відношення до",
            auth="Катерина Городенська «Чи правильне слововживання?»",
            cat_name="calque_syntactic",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
            proper_list=["INVALID_TARGET"],
        )

    # 4h. Probe with unapproved/partial authority (CF-R8 Finding 1)
    with pytest.raises(ValueError, match="Mismatched authority for case 'decol_syn_032'"):
        query_source_evidence(
            case_id="decol_syn_032",
            term="мати дотичність",
            copy="мати відношення до",
            auth="Unrelated Катерина textbook",
            cat_name="calque_syntactic",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
        )

    # 5. query_source_evidence must fail closed on unknown prepositional probe (Finding 1, no fallback)
    with pytest.raises(ValueError, match="has no verified attestation"):
        query_source_evidence(
            case_id="probe_prep_unknown_001",
            term="по якихось справах",
            copy="по якимось ділам",
            auth="Олександр Пономарів «Культура слова»",
            cat_name="calque_prepositional",
            s_cur=s_cur,
            v_cur=v_cur,
            style_guide_cache=[],
        )

    # 6. make_reviewer_confirmation must fail closed on unreviewed probes (Finding 3)
    dummy_item = {
        "case_id": "probe_unreviewed_999",
        "target_term": "невідомий термін",
        "russian_copy": "невідома копія",
        "authority": "Борис Антоненко-Давидович «Як ми говоримо»",
        "is_erroneous": True,
    }
    with pytest.raises(ValueError, match="has not been confirmed by independent language review"):
        make_reviewer_confirmation(dummy_item, "calque_lexical", v_cur, s_cur, [])

    # 7. make_reviewer_confirmation must fail closed on reviewed case ID with corrupted term (Finding 3)
    corrupted_item = {
        "case_id": "decol_syn_032",
        "target_term": "несумісний термін",
        "russian_copy": "мати відношення до",
        "authority": "Катерина Городенська «Чи правильне слововживання?»",
        "is_erroneous": True,
    }
    with pytest.raises(ValueError, match="Material change detected for case 'decol_syn_032'"):
        make_reviewer_confirmation(corrupted_item, "calque_syntactic", v_cur, s_cur, [])

    # 8. make_reviewer_confirmation must fail closed on tampered contexts (CF-R7 Finding 3)
    from scripts.projects.open_model_data.decolonization_cases_data import SYNTACTIC_CALQUES
    syn_032 = next(c for c in SYNTACTIC_CALQUES if c["case_id"] == "decol_syn_032")
    tampered_contexts_item = dict(syn_032)
    tampered_contexts_item["contexts"] = [
        {**syn_032["contexts"][0], "query": "Абсолютно сфальсифікований запит"},
        syn_032["contexts"][1],
    ]
    with pytest.raises(ValueError, match=r"content digest mismatch.*Contexts, case metadata, or source evidence tampered with"):
        make_reviewer_confirmation(tampered_contexts_item, "calque_syntactic", v_cur, s_cur, [])

    # 9. make_reviewer_confirmation must fail closed on flipped is_erroneous (CF-R7 Finding 3)
    flipped_err_item = dict(syn_032)
    flipped_err_item["is_erroneous"] = False
    with pytest.raises(ValueError, match="is_erroneous 'False' differs from reviewed"):
        make_reviewer_confirmation(flipped_err_item, "calque_syntactic", v_cur, s_cur, [])

    # 10. make_reviewer_confirmation must fail closed on changed category (CF-R7 Finding 3)
    with pytest.raises(ValueError, match="category 'calque_lexical' differs from reviewed"):
        make_reviewer_confirmation(syn_032, "calque_lexical", v_cur, s_cur, [])

    # 11. make_reviewer_confirmation must fail closed on tampered supporting passage (CF-R8 Finding 2)
    from scripts.projects.open_model_data.decolonization_cases_data import PREPOSITIONAL_CALQUES
    from scripts.projects.open_model_data.decolonization_evidence_catalog import EXPLICIT_SOURCE_EVIDENCE
    prep_020 = next(c for c in PREPOSITIONAL_CALQUES if c["case_id"] == "decol_prep_020")
    orig_passage = EXPLICIT_SOURCE_EVIDENCE["decol_prep_020"]["supporting_passage"]
    try:
        EXPLICIT_SOURCE_EVIDENCE["decol_prep_020"]["supporting_passage"] = "UNVERIFIED_SENTINEL_PASSAGE"
        with pytest.raises(
            ValueError,
            match=r"Material change detected for case 'decol_prep_020': supporting_passage.*Confirmation invalidated",
        ):
            make_reviewer_confirmation(prep_020, "calque_prepositional", v_cur, s_cur, [])
    finally:
        EXPLICIT_SOURCE_EVIDENCE["decol_prep_020"]["supporting_passage"] = orig_passage

    # 12. make_reviewer_confirmation must fail closed on nonexistent dossier file (CF-R8 Finding 3)
    from scripts.projects.open_model_data.decolonization_language_reviews import INDEPENDENT_LANGUAGE_REVIEWS
    orig_locator = INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["review_dossier_locator"]
    try:
        INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["review_dossier_locator"] = (
            "data/projects/open_model_data/components/decolonization/reviews/nonexistent_dossier_999.json"
        )
        with pytest.raises(ValueError, match=r"Review dossier file not found at .*nonexistent_dossier_999.json"):
            make_reviewer_confirmation(syn_032, "calque_syntactic", v_cur, s_cur, [])
    finally:
        INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["review_dossier_locator"] = orig_locator

    # 13. make_reviewer_confirmation must fail closed when receipt ID is missing (CF-R8 Finding 3)
    orig_receipt = INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["review_receipt_id"]
    try:
        INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["review_receipt_id"] = ""
        with pytest.raises(ValueError, match=r"missing review_receipt_id"):
            make_reviewer_confirmation(syn_032, "calque_syntactic", v_cur, s_cur, [])
    finally:
        INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["review_receipt_id"] = orig_receipt

    # 14. make_reviewer_confirmation must fail closed on builder/non-independent reviewer (CF-R8 Finding 3)
    orig_rev_id = INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["reviewer_id"]
    orig_rev_fam = INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["reviewer_family"]
    try:
        INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["reviewer_id"] = "builder"
        INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["reviewer_family"] = "gemini"
        with pytest.raises(ValueError, match=r"independent language review cannot be performed by builder or model"):
            make_reviewer_confirmation(syn_032, "calque_syntactic", v_cur, s_cur, [])
    finally:
        INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["reviewer_id"] = orig_rev_id
        INDEPENDENT_LANGUAGE_REVIEWS["decol_syn_032"]["reviewer_family"] = orig_rev_fam


def test_supporting_passages_and_no_manufactured_statements(decolonization_data):
    """Verify authentic citations, no manufactured blanket statements, and correct loci (CF-R6 Finding 2)."""
    cases = decolonization_data["cases"]

    # 1. decol_syn_014 must bind to article 77, not article 43
    syn_014 = next(c for c in cases if c["case_id"] == "decol_syn_014")
    ev_014 = syn_014["reviewer_confirmation"]["source_evidence"]
    assert "стаття «Шлях, дорога, путь, путівець, спосіб»" in ev_014["locus"]
    assert "с. 77" in ev_014["locus"]
    assert "спосіб" in ev_014["supporting_passage"].lower()
    assert "крамниця" not in ev_014["supporting_passage"].lower()

    # 2. Zero cases must contain the manufactured blanket statement contradicted by style_guide id=222
    for c in cases:
        ev = c["reviewer_confirmation"]["source_evidence"]
        passage = ev.get("supporting_passage", "")
        assert "Конструкція 'по' з іменником у знахідному" not in passage, f"Case {c['case_id']} contains manufactured blanket text"
        assert "помилкова з погляду української граматики" not in passage, f"Case {c['case_id']} contains manufactured blanket text"

    # 3. Check that prepositional calques have accurate authorities
    ponomariv_prep_cases = [c for c in cases if c["category"] == "calque_prepositional" and "Пономарів" in c["authority"]]
    assert len(ponomariv_prep_cases) == 36
    for c in ponomariv_prep_cases:
        ev = c["reviewer_confirmation"]["source_evidence"]
        assert "Олександр Пономарів" in ev["source_name"]
        assert "Культура слова" in ev["source_name"]
        assert "с." in ev["locus"]

    antonenko_prep = [c for c in cases if c["category"] == "calque_prepositional" and "Антоненко" in c["authority"]]
    assert len(antonenko_prep) == 12
    for c in antonenko_prep:
        ev = c["reviewer_confirmation"]["source_evidence"]
        assert "Антоненко-Давидович" in ev["source_name"]
        assert "стаття «" in ev["locus"]

    # 4. decol_prep_020 must cite Ponomariv page 76 and verbatim authentic text (CF-R8 Finding 2)
    prep_020 = next(c for c in cases if c["case_id"] == "decol_prep_020")
    ev_020 = prep_020["reviewer_confirmation"]["source_evidence"]
    assert "с. 76" in ev_020["locus"]
    assert "у вихідні (дні)" in ev_020["supporting_passage"]
    assert "у вихідний (день)" in ev_020["supporting_passage"]


def test_dataset_acceptance_with_verified_signoff():
    """Verify that audit_dataset_acceptance.py passes with verified human signoff and ACCEPTED status (Finding 3)."""
    audit_script = REPO_ROOT / "scripts" / "projects" / "open_model_data" / "audit_dataset_acceptance.py"
    signoff_file = DECOLONIZATION_DIR / "acceptance_review_sample.signoff.json"
    assert signoff_file.is_file(), f"Missing signoff file at {signoff_file}"

    cmd = [
        sys.executable,
        str(audit_script),
        "--verify-human-signoff",
        str(signoff_file),
        str(DECOLONIZATION_DIR),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert proc.returncode == 0, f"Acceptance audit failed (exit {proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
    assert "OVERALL STATUS: ACCEPTED" in proc.stdout
    assert "signoff_verified: True" in proc.stdout


def test_cf_r9_remediations_regression(decolonization_data):
    """Verify remediation of all 3 CF-R9 blockers.

    1. Blocker 1: Authentic authorities and establishing passages for lexical calques (decol_lex_001/002/003).
    2. Blocker 2: Non-bypassable live SQL execution on s_cur and v_cur in query_source_evidence.
    3. Blocker 3: Reviewer whitelist enforcement via ACCREDITED_INDEPENDENT_REVIEWERS and signoff cross-reference.
    """
    import sqlite3

    from scripts.projects.open_model_data.build_decolonization_cases import (
        ACCREDITED_INDEPENDENT_REVIEWERS,
        make_reviewer_confirmation,
        query_source_evidence,
    )
    from scripts.projects.open_model_data.decolonization_cases_data import (
        LEXICAL_CALQUES,
    )
    from scripts.projects.open_model_data.decolonization_language_reviews import INDEPENDENT_LANGUAGE_REVIEWS

    cases = decolonization_data["cases"]

    # ── Blocker 1: Passages establish corrections with authentic modern authorities ──
    lex_001 = next(c for c in cases if c["case_id"] == "decol_lex_001")
    ev_001 = lex_001["reviewer_confirmation"]["source_evidence"]
    assert "Пономарів" in lex_001["authority"]
    assert "с. 42" in ev_001["locus"]
    assert "лікар" in ev_001["supporting_passage"].lower()
    assert "доктор" in ev_001["supporting_passage"].lower()
    assert "стаття 99" not in ev_001["locus"]

    lex_002 = next(c for c in cases if c["case_id"] == "decol_lex_002")
    ev_002 = lex_002["reviewer_confirmation"]["source_evidence"]
    assert "СУМ-20" in lex_002["authority"]
    assert "Капелюх" in ev_002["locus"]
    assert "капелюх" in ev_002["supporting_passage"].lower()
    assert "шляпа" in ev_002["supporting_passage"].lower()
    assert "стаття 59" not in ev_002["locus"]

    lex_003 = next(c for c in cases if c["case_id"] == "decol_lex_003")
    ev_003 = lex_003["reviewer_confirmation"]["source_evidence"]
    assert "Пономарів" in lex_003["authority"]
    assert "с. 51" in ev_003["locus"]
    assert "завдання" in ev_003["supporting_passage"].lower()
    assert "задача" in ev_003["supporting_passage"].lower()
    assert "стаття 35" not in ev_003["locus"]

    # ── Blocker 2: Live SQL execution on s_cur and v_cur (RaisingCursor fails closed) ──
    class RaisingCursor:
        def execute(self, *args, **kwargs):
            raise RuntimeError("Live SQL query executed: simulated cursor failure")
        def fetchone(self):
            raise RuntimeError("Live SQL query executed: simulated cursor failure")
        def fetchall(self):
            raise RuntimeError("Live SQL query executed: simulated cursor failure")

    raising_cur = RaisingCursor()

    vesum_db = _resolve_db_path("vesum.db", REPO_ROOT)
    sources_db = _resolve_db_path("sources.db", REPO_ROOT)
    v_conn = sqlite3.connect(f"file:{vesum_db}?mode=ro", uri=True)
    s_conn = sqlite3.connect(f"file:{sources_db}?mode=ro", uri=True)
    real_v_cur = v_conn.cursor()
    real_s_cur = s_conn.cursor()

    # decol_lex_001 with raising v_cur
    with pytest.raises(RuntimeError, match="Live SQL query executed"):
        query_source_evidence(
            case_id="decol_lex_001",
            term="лікар",
            copy="доктор",
            auth="Олександр Пономарів «Культура слова»",
            cat_name="calque_lexical",
            s_cur=real_s_cur,
            v_cur=raising_cur,
            style_guide_cache=[],
        )

    # decol_lex_001 with raising s_cur
    with pytest.raises(RuntimeError, match="Live SQL query executed"):
        query_source_evidence(
            case_id="decol_lex_001",
            term="лікар",
            copy="доктор",
            auth="Олександр Пономарів «Культура слова»",
            cat_name="calque_lexical",
            s_cur=raising_cur,
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # decol_lex_012 (UA-GEC) with raising v_cur
    with pytest.raises(RuntimeError, match="Live SQL query executed"):
        query_source_evidence(
            case_id="decol_lex_012",
            term="гусак",
            copy="гусь",
            auth="UA-GEC (Syvokon et al., 2023)",
            cat_name="calque_lexical",
            s_cur=real_s_cur,
            v_cur=raising_cur,
            style_guide_cache=[],
        )

    # decol_lex_012 (UA-GEC) with raising s_cur
    with pytest.raises(RuntimeError, match="Live SQL query executed"):
        query_source_evidence(
            case_id="decol_lex_012",
            term="гусак",
            copy="гусь",
            auth="UA-GEC (Syvokon et al., 2023)",
            cat_name="calque_lexical",
            s_cur=raising_cur,
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # make_reviewer_confirmation with raising v_cur fails closed
    lex_001_item = next(c for c in LEXICAL_CALQUES if c["case_id"] == "decol_lex_001")
    with pytest.raises(RuntimeError, match="Live SQL query executed"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", raising_cur, real_s_cur, [])

    # make_reviewer_confirmation with raising s_cur fails closed
    with pytest.raises(RuntimeError, match="Live SQL query executed"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, raising_cur, [])

    # ── Blocker 3: Reviewer whitelist enforcement (ACCREDITED_INDEPENDENT_REVIEWERS) ──
    assert "prof_karpenko_ling_ua" in ACCREDITED_INDEPENDENT_REVIEWERS
    assert "UNVERIFIED_REVIEWER_999" not in ACCREDITED_INDEPENDENT_REVIEWERS

    orig_rev = INDEPENDENT_LANGUAGE_REVIEWS["decol_lex_001"]["reviewer_id"]
    try:
        INDEPENDENT_LANGUAGE_REVIEWS["decol_lex_001"]["reviewer_id"] = "UNVERIFIED_REVIEWER_999"
        with pytest.raises(ValueError, match=r"is not in ACCREDITED_INDEPENDENT_REVIEWERS whitelist"):
            make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])
    finally:
        INDEPENDENT_LANGUAGE_REVIEWS["decol_lex_001"]["reviewer_id"] = orig_rev
