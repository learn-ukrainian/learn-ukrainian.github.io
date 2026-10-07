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
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.audit_dataset_acceptance import (
    LinguisticNormalizer,
    _resolve_db_path,
)
from scripts.projects.open_model_data.paths import REGISTRY_DECOLONIZATION_DIR
from scripts.projects.open_model_data.sum20_codification_records import ensure_reproducible_sum20_table
from scripts.storage.paths import artifact_set
from tests.projects.open_model_data.test_decolonization_withholding import (
    _healthy_source_schema,
    _query_dictionary,
)
from tests.projects.open_model_data.test_decolonization_withholding import (
    dictionary_probe as dictionary_probe,
)


@pytest.fixture
def source_cursor_factory():
    """Real synthetic schemas exercise SQL and row binding, rather than guessed cursor tuples."""
    connections = []

    def make(text=None):
        conn = sqlite3.connect(":memory:")
        connections.append(conn)
        _healthy_source_schema(conn)
        if text:
            conn.execute(
                "INSERT INTO external_articles (id,title,text,speaker,source_file) VALUES (1,'Unrelated book',?,'Unrelated author','synthetic-unrelated')",
                (text,),
            )
            conn.execute(
                "INSERT INTO textbooks VALUES (1,'Unrelated book',?,'Unrelated author','Unrelated author','synthetic-unrelated')",
                (text,),
            )
        return conn.cursor()

    yield make
    for conn in connections:
        conn.close()


_COMPONENT_GROUP = "open_model_component_payload"
_DECOL_REL = "projects/open_model_data/components/decolonization"


@pytest.fixture(scope="module")
def decolonization_data():
    """Load all records and manifest for component testing."""
    manifest_file = REGISTRY_DECOLONIZATION_DIR / "manifest.json"
    cases_file = REGISTRY_DECOLONIZATION_DIR / "cases.json"
    snapshot = artifact_set(_COMPONENT_GROUP, repo=REPO_ROOT)
    train_rel = f"{_DECOL_REL}/decolonization_train.jsonl"
    eval_rel = f"{_DECOL_REL}/decolonization_eval.jsonl"

    assert manifest_file.is_file(), f"Missing manifest.json at {manifest_file}"
    assert cases_file.is_file(), f"Missing cases.json at {cases_file}"
    assert train_rel in snapshot.artifacts
    assert eval_rel in snapshot.artifacts

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    cases = json.loads(cases_file.read_text(encoding="utf-8"))

    train_records = [
        json.loads(line) for line in snapshot.artifacts[train_rel].decode("utf-8").splitlines() if line.strip()
    ]
    eval_records = [
        json.loads(line) for line in snapshot.artifacts[eval_rel].decode("utf-8").splitlines() if line.strip()
    ]

    return {
        "manifest": manifest,
        "cases": cases,
        "train": train_records,
        "eval": eval_records,
        "all": train_records + eval_records,
    }


@pytest.fixture
def require_vesum_db():
    """Skip test if uncommitted vesum.db is missing in CI."""
    vesum_db = _resolve_db_path("vesum.db", REPO_ROOT)
    if not vesum_db.is_file() or vesum_db.stat().st_size == 0:
        pytest.skip(f"requires {vesum_db} (not provisioned in CI)")
    return vesum_db


@pytest.fixture
def require_local_databases():
    """Skip test if uncommitted sources.db or vesum.db is missing in CI."""
    vesum_db = _resolve_db_path("vesum.db", REPO_ROOT)
    sources_db = _resolve_db_path("sources.db", REPO_ROOT)
    if not vesum_db.is_file() or vesum_db.stat().st_size == 0:
        pytest.skip(f"requires {vesum_db} (not provisioned in CI)")
    if not sources_db.is_file() or sources_db.stat().st_size == 0:
        pytest.skip(f"requires {sources_db} (not provisioned in CI)")
    return sources_db


@pytest.fixture
def require_all_databases():
    """Skip test if uncommitted sources.db or vesum.db is missing in CI."""
    vesum_db = _resolve_db_path("vesum.db", REPO_ROOT)
    sources_db = _resolve_db_path("sources.db", REPO_ROOT)
    if not vesum_db.is_file() or vesum_db.stat().st_size == 0:
        pytest.skip(f"requires {vesum_db} (not provisioned in CI)")
    if not sources_db.is_file() or sources_db.stat().st_size == 0:
        pytest.skip(f"requires {sources_db} (not provisioned in CI)")
    return sources_db


@pytest.fixture
def hermetic_source_cursor():
    """Provide only the case evidence needed by source-binding regression probes.

    These rows exercise lookup and digest checks; they do not attest the sources.
    """
    from scripts.projects.open_model_data.decolonization_evidence_catalog import EXPLICIT_SOURCE_EVIDENCE

    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE external_articles (id INTEGER PRIMARY KEY, title TEXT, text TEXT, "
        "speaker TEXT, source_file TEXT, decolonization_tag TEXT, channel_id TEXT, domain TEXT)"
    )
    conn.execute(
        "CREATE TABLE style_guide (id INTEGER PRIMARY KEY, word TEXT, section TEXT, text TEXT, source TEXT, excerpt_full TEXT, page INTEGER)"
    )
    conn.execute(
        "CREATE TABLE textbooks (id INTEGER PRIMARY KEY, title TEXT, text TEXT, author TEXT, author_uk TEXT, source_file TEXT)"
    )
    conn.execute("CREATE VIRTUAL TABLE textbooks_fts USING fts5(title, text)")
    for case_id in ("decol_syn_032", "decol_lex_003", "decol_lex_004", "decol_lex_020", "decol_prep_020"):
        evidence = EXPLICIT_SOURCE_EVIDENCE[case_id]
        conn.execute(
            "INSERT INTO external_articles (title, text, speaker, source_file, decolonization_tag) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                evidence["source"],
                f"{evidence['supporting_passage']} {evidence['target_term']}",
                evidence["authority"],
                "fixture",
                None,
            ),
        )
    try:
        yield conn.cursor()
    finally:
        conn.close()


@pytest.mark.needs_artifact(
    "open_model_component_payload", "projects/open_model_data/components/decolonization/decolonization_train.jsonl"
)
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


@pytest.mark.needs_artifact(
    "open_model_component_payload", "projects/open_model_data/components/decolonization/decolonization_train.jsonl"
)
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


@pytest.mark.needs_artifact(
    "open_model_component_payload", "projects/open_model_data/components/decolonization/decolonization_train.jsonl"
)
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


@pytest.mark.needs_artifact(
    "open_model_component_payload", "projects/open_model_data/components/decolonization/decolonization_train.jsonl"
)
def test_zero_train_eval_leakage(decolonization_data, require_vesum_db):
    """Verify 100% disjoint train and eval partitions under aspect normalization."""
    normalizer = LinguisticNormalizer(require_vesum_db)

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


@pytest.mark.needs_artifact(
    "open_model_component_payload", "projects/open_model_data/components/decolonization/decolonization_train.jsonl"
)
def test_dataset_acceptance_audit_passes(require_local_databases, tmp_path):
    """Verify that audit_dataset_acceptance.py runs and passes with exit code 0."""
    audit_script = REPO_ROOT / "scripts" / "projects" / "open_model_data" / "audit_dataset_acceptance.py"
    cmd = [
        sys.executable,
        str(audit_script),
        str(REGISTRY_DECOLONIZATION_DIR),
        "--sample-out",
        str(tmp_path / "acceptance_review_sample.md"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60)
    assert proc.returncode == 0, f"Acceptance audit failed (exit {proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
    assert "OVERALL STATUS: PASSED_AUTOMATED_CHECKS" in proc.stdout


@pytest.mark.needs_artifact(
    "open_model_component_payload", "projects/open_model_data/components/decolonization/decolonization_train.jsonl"
)
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


@pytest.mark.needs_artifact(
    "open_model_component_payload", "projects/open_model_data/components/decolonization/decolonization_train.jsonl"
)
def test_supporting_passages_all_non_null_and_authentic(decolonization_data):
    """Verify that 100% of cases (250/250) have non-null, non-empty authentic supporting passages."""
    cases = decolonization_data["cases"]
    assert len(cases) == 250

    for c in cases:
        cid = c["case_id"]
        rev = c.get("reviewer_confirmation", {})
        assert rev.get("status") == "confirmed", f"Case {cid} has status '{rev.get('status')}', expected 'confirmed'"
        assert rev.get("reviewer_family") in {"claude", "independent_human", "independent_expert"}, (
            f"Case {cid} has reviewer_family '{rev.get('reviewer_family')}', expected accredited family"
        )

        source_ev = rev.get("source_evidence", {})
        passage = source_ev.get("supporting_passage")
        assert passage and isinstance(passage, str) and len(passage.strip()) > 10, (
            f"Case {cid} has invalid or null supporting_passage: {passage!r}"
        )
        locus = source_ev.get("locus")
        assert locus and isinstance(locus, str), f"Case {cid} missing locus"


def test_adversarial_probes_and_fail_closed(require_vesum_db, hermetic_source_cursor):
    """Verify fail-closed behavior on adversarial probes and strict UA-GEC phrase alignment (CF-R6 Finding 1 & 3)."""
    import sqlite3

    from scripts.projects.open_model_data.build_decolonization_cases import (
        make_reviewer_confirmation,
        query_source_evidence,
        validate_ua_gec_phrase,
    )

    v_conn = sqlite3.connect(f"{Path(require_vesum_db).resolve().as_uri()}?mode=ro", uri=True)
    v_cur = v_conn.cursor()
    s_cur = hermetic_source_cursor

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
    with pytest.raises(
        ValueError, match=r"content digest mismatch.*Contexts, case metadata, or source evidence tampered with"
    ):
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


@pytest.mark.needs_artifact(
    "open_model_component_payload", "projects/open_model_data/components/decolonization/decolonization_train.jsonl"
)
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
        assert "Конструкція 'по' з іменником у знахідному" not in passage, (
            f"Case {c['case_id']} contains manufactured blanket text"
        )
        assert "помилкова з погляду української граматики" not in passage, (
            f"Case {c['case_id']} contains manufactured blanket text"
        )

    # 3. Check that prepositional calques have accurate authorities
    ponomariv_prep_cases = [
        c for c in cases if c["category"] == "calque_prepositional" and "Пономарів" in c["authority"]
    ]
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


@pytest.mark.needs_artifact(
    "open_model_component_payload", "projects/open_model_data/components/decolonization/decolonization_train.jsonl"
)
def test_dataset_acceptance_with_verified_signoff(require_local_databases, tmp_path):
    """Verify that audit_dataset_acceptance.py passes with verified human signoff and ACCEPTED status (Finding 3)."""
    audit_script = REPO_ROOT / "scripts" / "projects" / "open_model_data" / "audit_dataset_acceptance.py"
    signoff_file = REGISTRY_DECOLONIZATION_DIR / "acceptance_review_sample.signoff.json"
    assert signoff_file.is_file(), f"Missing signoff file at {signoff_file}"

    cmd = [
        sys.executable,
        str(audit_script),
        "--sample-out",
        str(tmp_path / "acceptance_review_sample.md"),
        "--verify-human-signoff",
        str(signoff_file),
        str(REGISTRY_DECOLONIZATION_DIR),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60)
    assert proc.returncode == 0, f"Acceptance audit failed (exit {proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
    assert "OVERALL STATUS: ACCEPTED" in proc.stdout
    assert "signoff_verified: True" in proc.stdout


@pytest.mark.needs_artifact(
    "open_model_component_payload", "projects/open_model_data/components/decolonization/decolonization_train.jsonl"
)
def test_cf_r9_remediations_regression(decolonization_data, require_local_databases):
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
    v_conn = sqlite3.connect(f"{Path(vesum_db).resolve().as_uri()}?mode=ro", uri=True)
    s_conn = sqlite3.connect(f"{Path(sources_db).resolve().as_uri()}?mode=ro", uri=True)
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
    assert "claude_blue_team_ling_review" in ACCREDITED_INDEPENDENT_REVIEWERS
    assert "krisztiankoos_ling_review" in ACCREDITED_INDEPENDENT_REVIEWERS
    assert "dr_horodenska_codification_review" in ACCREDITED_INDEPENDENT_REVIEWERS
    assert "prof_karpenko_ling_ua" not in ACCREDITED_INDEPENDENT_REVIEWERS
    assert "UNVERIFIED_REVIEWER_999" not in ACCREDITED_INDEPENDENT_REVIEWERS

    orig_rev = INDEPENDENT_LANGUAGE_REVIEWS["decol_lex_001"]["reviewer_id"]
    try:
        INDEPENDENT_LANGUAGE_REVIEWS["decol_lex_001"]["reviewer_id"] = "UNVERIFIED_REVIEWER_999"
        with pytest.raises(ValueError, match=r"is not in ACCREDITED_INDEPENDENT_REVIEWERS whitelist"):
            make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])
    finally:
        INDEPENDENT_LANGUAGE_REVIEWS["decol_lex_001"]["reviewer_id"] = orig_rev


def test_cf_r10_remediations_regression(require_local_databases, source_cursor_factory):
    """Verify remediation of all CF-R10 blockers.

    1. Blocker 1: EmptyCursor (0 rows / fetchone() returns None) fails closed with ValueError.
    2. Blocker 1: UnrelatedCursor (fetchone() returns unrelated text) fails closed with ValueError.
    3. Blocker 1: UA-GEC record validation on correction/error alignment fails closed on mismatch.
    4. Blocker 2: Accredited independent reviewer attribution across all dossiers and signoff.
    """
    import sqlite3

    from scripts.projects.open_model_data.build_decolonization_cases import (
        ACCREDITED_INDEPENDENT_REVIEWERS,
        query_source_evidence,
    )
    from scripts.projects.open_model_data.decolonization_language_reviews import INDEPENDENT_LANGUAGE_REVIEWS

    vesum_db = _resolve_db_path("vesum.db", REPO_ROOT)
    sources_db = _resolve_db_path("sources.db", REPO_ROOT)
    v_conn = sqlite3.connect(f"{Path(vesum_db).resolve().as_uri()}?mode=ro", uri=True)
    s_conn = sqlite3.connect(f"{Path(sources_db).resolve().as_uri()}?mode=ro", uri=True)
    real_v_cur = v_conn.cursor()
    real_s_cur = s_conn.cursor()

    class EmptyCursor:
        def execute(self, *args, **kwargs):
            return self

        def fetchone(self):
            return None

        def fetchall(self):
            return []

    empty_cur = EmptyCursor()

    # ── 1. Empty v_cur fails closed (token not in forms_all) ──
    with pytest.raises(ValueError, match=r"VESUM evidence missing.*not found in forms_all"):
        query_source_evidence(
            case_id="decol_lex_001",
            term="лікар",
            copy="доктор",
            auth="Олександр Пономарів «Культура слова»",
            cat_name="calque_lexical",
            s_cur=real_s_cur,
            v_cur=empty_cur,
            style_guide_cache=[],
        )

    # ── 2. Empty s_cur fails closed across all authority branches ──
    # 2a. Textbook / monograph branch (Ponomariv)
    with pytest.raises(ValueError, match=r"(Held source|Committed source record)"):
        query_source_evidence(
            case_id="decol_lex_001",
            term="лікар",
            copy="доктор",
            auth="Олександр Пономарів «Культура слова»",
            cat_name="calque_lexical",
            s_cur=source_cursor_factory(),
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # 2b. Style guide branch (Antonenko-Davydovych)
    with pytest.raises(ValueError, match=r"(Held source|Committed source record)"):
        query_source_evidence(
            case_id="decol_syn_001",
            term="брати участь",
            copy="приймати участь",
            auth="Борис Антоненко-Давидович «Як ми говоримо»",
            cat_name="calque_syntactic",
            s_cur=source_cursor_factory(),
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # 2c. Dictionary branch (SUM-20)
    with pytest.raises(ValueError, match=r"(Held source|Committed source record)"):
        query_source_evidence(
            case_id="decol_lex_002",
            term="капелюх",
            copy="шляпа",
            auth="СУМ-20",
            cat_name="calque_lexical",
            s_cur=source_cursor_factory(),
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # 2d. UA-GEC branch
    with pytest.raises(
        ValueError, match=r"UA-GEC evidence missing: record \d+ for case 'decol_lex_012' not found in ua_gec_errors"
    ):
        query_source_evidence(
            case_id="decol_lex_012",
            term="гусак",
            copy="гусь",
            auth="UA-GEC (Syvokon et al., 2023)",
            cat_name="calque_lexical",
            s_cur=source_cursor_factory(),
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # ── 3. UnrelatedCursor fails closed on content mismatch ──
    unrelated_cur = source_cursor_factory("synthetic unrelated body")

    # 3a. Unrelated textbook record
    with pytest.raises(ValueError, match=r"(Held source|Committed source record)"):
        query_source_evidence(
            case_id="decol_lex_001",
            term="лікар",
            copy="доктор",
            auth="Олександр Пономарів «Культура слова»",
            cat_name="calque_lexical",
            s_cur=unrelated_cur,
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # 3b. Unrelated SUM-20 record
    with pytest.raises(ValueError, match=r"(Held source|Committed source record)"):
        query_source_evidence(
            case_id="decol_lex_002",
            term="капелюх",
            copy="шляпа",
            auth="СУМ-20",
            cat_name="calque_lexical",
            s_cur=unrelated_cur,
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # ── 4. UA-GEC mismatch fails closed ──
    class UAGECMismatchCursor:
        def execute(self, *args, **kwargs):
            return self

        def fetchone(self):
            # Returns an authentic UA-GEC row format (id, error, correct, error_type, doc_id)
            # but with mismatched error and correction
            return (5921, "несумісна помилка", "несумісне виправлення", "Fluency", "doc_001")

        def fetchall(self):
            return [(5921, "несумісна помилка", "несумісне виправлення", "Fluency", "doc_001")]

    gec_mismatch_cur = UAGECMismatchCursor()
    with pytest.raises(ValueError, match=r"UA-GEC record \d+ correction.*does not match"):
        query_source_evidence(
            case_id="decol_lex_012",
            term="гусак",
            copy="гусь",
            auth="UA-GEC (Syvokon et al., 2023)",
            cat_name="calque_lexical",
            s_cur=gec_mismatch_cur,
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # ── 5. Accredited reviewer attribution ──
    assert "claude_blue_team_ling_review" in ACCREDITED_INDEPENDENT_REVIEWERS
    assert "krisztiankoos_ling_review" in ACCREDITED_INDEPENDENT_REVIEWERS
    assert "dr_horodenska_codification_review" in ACCREDITED_INDEPENDENT_REVIEWERS
    assert "prof_karpenko_ling_ua" not in ACCREDITED_INDEPENDENT_REVIEWERS

    for case_id, rev in INDEPENDENT_LANGUAGE_REVIEWS.items():
        assert rev["reviewer_id"] in ACCREDITED_INDEPENDENT_REVIEWERS, (
            f"Case {case_id} has unaccredited reviewer '{rev['reviewer_id']}'"
        )


def test_cf_r11_remediations_regression(monkeypatch, require_local_databases, source_cursor_factory):
    """Verify remediation of all CF-R11 blockers.

    1. Blocker 1:
       a. Unrelated textbook/curriculum record (e.g. agricultural book 'Книга про трактори' with 'лікар')
          fails closed because it does not substantiate claimed citation / curriculum authority.
       b. Soviet dictionary СУМ-11 record in modern dictionary branch fails closed with ValueError.
    2. Blocker 2:
       a. UA-GEC negation mismatch ('не гусь → не гусак' when target is 'гусак') fails closed.
       b. UA-GEC doc_id metadata mismatch fails closed.
    3. Blocker 3:
       make_reviewer_confirmation fails closed on incomplete/defective signoff:
       a. sample_size_reviewed == 0 (incomplete review)
       b. blocker_defect_count > 0 (e.g. 300 blockers)
       c. minor_defect_count > 5
       d. invalid / missing dataset_sha256 hex digest
       e. invalid / missing signoff_date
    """
    import json
    import sqlite3

    from scripts.projects.open_model_data.build_decolonization_cases import (
        make_reviewer_confirmation,
        query_source_evidence,
        validate_ua_gec_phrase,
    )

    vesum_db = _resolve_db_path("vesum.db", REPO_ROOT)
    sources_db = _resolve_db_path("sources.db", REPO_ROOT)
    v_conn = sqlite3.connect(f"{Path(vesum_db).resolve().as_uri()}?mode=ro", uri=True)
    s_conn = sqlite3.connect(f"{Path(sources_db).resolve().as_uri()}?mode=ro", uri=True)
    real_v_cur = v_conn.cursor()
    real_s_cur = s_conn.cursor()

    # ── 1. Blocker 1: Citation binding and Modern Dictionary Fallback ──
    # 1a. Unrelated book with token match but no curriculum/linguistic citation anchors
    unrelated_book_cur = source_cursor_factory("synthetic unrelated body")
    with pytest.raises(ValueError, match=r"(Held source|Committed source record)"):
        query_source_evidence(
            case_id="decol_lex_001",
            term="лікар",
            copy="доктор",
            auth="Олександр Пономарів «Культура слова»",
            cat_name="calque_lexical",
            s_cur=unrelated_book_cur,
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # 1b. Soviet SUM-11 cursor fails closed
    soviet_cur = source_cursor_factory("СУМ-11")
    with pytest.raises(ValueError, match=r"(Held source|Committed source record)"):
        query_source_evidence(
            case_id="decol_lex_002",
            term="капелюх",
            copy="шляпа",
            auth="СУМ-20",
            cat_name="calque_lexical",
            s_cur=soviet_cur,
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # ── 2. Blocker 2: Strict UA-GEC phrase and metadata alignment ──
    # 2a. Negation mismatch
    assert not validate_ua_gec_phrase("гусак", "не гусак", real_v_cur)
    assert not validate_ua_gec_phrase("не гусак", "гусак", real_v_cur)

    class UAGECNegationCursor:
        def execute(self, *args, **kwargs):
            return self

        def fetchone(self):
            # doc_id matches ("1068"), error matches, but correction has negation particle mismatch
            return (5921, "гусь", "не гусак", "Fluency", "1068")

        def fetchall(self):
            return [(5921, "гусь", "не гусак", "Fluency", "1068")]

    neg_cur = UAGECNegationCursor()
    with pytest.raises(ValueError, match=r"UA-GEC record \d+ correction.*does not match"):
        query_source_evidence(
            case_id="decol_lex_012",
            term="гусак",
            copy="гусь",
            auth="UA-GEC (Syvokon et al., 2023)",
            cat_name="calque_lexical",
            s_cur=neg_cur,
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # 2b. doc_id metadata mismatch
    class UAGECDocMismatchCursor:
        def execute(self, *args, **kwargs):
            return self

        def fetchone(self):
            # doc_id is 9999 instead of expected 1068
            return (5921, "гусь", "гусак", "Fluency", "9999")

        def fetchall(self):
            return [(5921, "гусь", "гусак", "Fluency", "9999")]

    doc_mismatch_cur = UAGECDocMismatchCursor()
    with pytest.raises(
        ValueError, match=r"UA-GEC doc_id mismatch for case 'decol_lex_012': expected '1068', got '9999'"
    ):
        query_source_evidence(
            case_id="decol_lex_012",
            term="гусак",
            copy="гусь",
            auth="UA-GEC (Syvokon et al., 2023)",
            cat_name="calque_lexical",
            s_cur=doc_mismatch_cur,
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # ── 3. Blocker 3: make_reviewer_confirmation signoff contract ──
    signoff_path = REGISTRY_DECOLONIZATION_DIR / "acceptance_review_sample.signoff.json"
    valid_signoff = json.loads(signoff_path.read_text(encoding="utf-8"))

    cases_file = REGISTRY_DECOLONIZATION_DIR / "cases.json"
    valid_cases = json.loads(cases_file.read_text(encoding="utf-8"))
    lex_001_item = next(c for c in valid_cases if c["case_id"] == "decol_lex_001")

    # 3a. Incomplete review: sample_size_reviewed = 0
    bad_signoff_3a = dict(valid_signoff, sample_size_reviewed=0)
    monkeypatch.setattr(
        "scripts.projects.open_model_data.build_decolonization_cases.json.loads",
        lambda s: bad_signoff_3a,
    )
    with pytest.raises(ValueError, match="Review incomplete"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])

    # 3b. Unresolved blocker defects: blocker_defect_count = 300
    bad_signoff_3b = dict(valid_signoff, blocker_defect_count=300)
    monkeypatch.setattr(
        "scripts.projects.open_model_data.build_decolonization_cases.json.loads",
        lambda s: bad_signoff_3b,
    )
    with pytest.raises(ValueError, match="unresolved BLOCKER defect"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])

    # 3c. Excessive minor defects: minor_defect_count = 10
    bad_signoff_3c = dict(valid_signoff, minor_defect_count=10)
    monkeypatch.setattr(
        "scripts.projects.open_model_data.build_decolonization_cases.json.loads",
        lambda s: bad_signoff_3c,
    )
    with pytest.raises(ValueError, match="exceeds allowable tolerance limit"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])

    # 3d. Invalid dataset_sha256
    bad_signoff_3d = dict(valid_signoff, dataset_sha256="not_a_valid_sha")
    monkeypatch.setattr(
        "scripts.projects.open_model_data.build_decolonization_cases.json.loads",
        lambda s: bad_signoff_3d,
    )
    with pytest.raises(ValueError, match="not a valid 64-character hex digest"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])

    # 3e. Invalid signoff_date
    bad_signoff_3e = dict(valid_signoff, signoff_date="2026/09/22")
    monkeypatch.setattr(
        "scripts.projects.open_model_data.build_decolonization_cases.json.loads",
        lambda s: bad_signoff_3e,
    )
    with pytest.raises(ValueError, match="invalid date format"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])


def test_cf_r12_remediations_regression(monkeypatch, require_local_databases, source_cursor_factory):
    """Verify remediation of all CF-R12 findings.

    1. Citation binding in query_source_evidence:
       Unrelated book cursors containing generic tokens ('сторінка', 'клас', 'klas',
       'lesson', 'мов', 'українськ', 'культура', 'дослідженн') MUST fail closed with
       'does not substantiate claimed citation'.
    2. Sample-size equality in make_reviewer_confirmation:
       drawn_count and reviewed_count must both be positive integers, not bool,
       and exactly equal.
    3. Calendar date validation in make_reviewer_confirmation:
       signoff_date must be a valid calendar date, rejecting impossible dates
       like '2026-99-99' or '2026-02-31'.
    4. Antonenko style guide retrieval:
       Antonenko cases retrieved from table style_guide succeed even when the author's
       name does not appear in the record body.
    """
    import json
    import sqlite3

    from scripts.projects.open_model_data.build_decolonization_cases import (
        make_reviewer_confirmation,
        query_source_evidence,
    )

    vesum_db = _resolve_db_path("vesum.db", REPO_ROOT)
    sources_db = _resolve_db_path("sources.db", REPO_ROOT)
    v_conn = sqlite3.connect(f"{Path(vesum_db).resolve().as_uri()}?mode=ro", uri=True)
    s_conn = sqlite3.connect(f"{Path(sources_db).resolve().as_uri()}?mode=ro", uri=True)
    real_v_cur = v_conn.cursor()
    real_s_cur = s_conn.cursor()

    # ── 1. Generic tokens in unrelated book fixtures fail closed ──
    generic_fixture_texts = [
        "Книга про трактори. Сторінка 1. Тут є лікар.",
        "Книга про трактори. Клас 5. Тут є лікар.",
        "Книга про трактори. Klas 8. Дослідження тракторів. Тут є лікар.",
        "Книга про трактори. Lesson 3. Українська культура праці на тракторі. Тут є лікар.",
    ]
    for text in generic_fixture_texts:
        cur = source_cursor_factory(text)
        with pytest.raises(ValueError, match=r"(Held source|Committed source record)"):
            query_source_evidence(
                case_id="decol_lex_001",
                term="лікар",
                copy="доктор",
                auth="Олександр Пономарів «Культура слова»",
                cat_name="calque_lexical",
                s_cur=cur,
                v_cur=real_v_cur,
                style_guide_cache=[],
            )

    # ── 2. Sample size equality and type enforcement ──
    signoff_path = REGISTRY_DECOLONIZATION_DIR / "acceptance_review_sample.signoff.json"
    valid_signoff = json.loads(signoff_path.read_text(encoding="utf-8"))

    cases_file = REGISTRY_DECOLONIZATION_DIR / "cases.json"
    valid_cases = json.loads(cases_file.read_text(encoding="utf-8"))
    lex_001_item = next(c for c in valid_cases if c["case_id"] == "decol_lex_001")

    # 2a. sample_size_drawn is None
    bad_signoff_drawn_none = dict(valid_signoff, sample_size_drawn=None)
    monkeypatch.setattr(
        "scripts.projects.open_model_data.build_decolonization_cases.json.loads",
        lambda s: bad_signoff_drawn_none,
    )
    with pytest.raises(ValueError, match="Review incomplete or defective"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])

    # 2b. sample_size_drawn is negative
    bad_signoff_drawn_neg = dict(valid_signoff, sample_size_drawn=-1)
    monkeypatch.setattr(
        "scripts.projects.open_model_data.build_decolonization_cases.json.loads",
        lambda s: bad_signoff_drawn_neg,
    )
    with pytest.raises(ValueError, match="Review incomplete or defective"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])

    # 2c. sample_size_drawn is boolean
    bad_signoff_drawn_bool = dict(valid_signoff, sample_size_drawn=True)
    monkeypatch.setattr(
        "scripts.projects.open_model_data.build_decolonization_cases.json.loads",
        lambda s: bad_signoff_drawn_bool,
    )
    with pytest.raises(ValueError, match="Review incomplete or defective"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])

    # 2d. sample_size_reviewed != sample_size_drawn
    bad_signoff_mismatch = dict(valid_signoff, sample_size_drawn=300, sample_size_reviewed=301)
    monkeypatch.setattr(
        "scripts.projects.open_model_data.build_decolonization_cases.json.loads",
        lambda s: bad_signoff_mismatch,
    )
    with pytest.raises(ValueError, match="Review incomplete or defective"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])

    # ── 3. Calendar date validation ──
    bad_date_99 = dict(valid_signoff, signoff_date="2026-99-99")
    monkeypatch.setattr(
        "scripts.projects.open_model_data.build_decolonization_cases.json.loads",
        lambda s: bad_date_99,
    )
    with pytest.raises(ValueError, match="is not a valid calendar date"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])

    bad_date_feb31 = dict(valid_signoff, signoff_date="2026-02-31")
    monkeypatch.setattr(
        "scripts.projects.open_model_data.build_decolonization_cases.json.loads",
        lambda s: bad_date_feb31,
    )
    with pytest.raises(ValueError, match="is not a valid calendar date"):
        make_reviewer_confirmation(lex_001_item, "calque_lexical", real_v_cur, real_s_cur, [])

    # ── 4. Antonenko style guide retrieval without author name in text ──
    from scripts.projects.open_model_data import build_decolonization_cases as builder

    synthetic = {
        "authority": "Борис Антоненко-Давидович «Як ми говоримо»",
        "source": "Борис Антоненко-Давидович «Як ми говоримо»",
        "target_term": "fixture",
        "supporting_passage": "literal synthetic passage",
        "locus": "synthetic locus",
    }
    monkeypatch.setattr(builder, "EXPLICIT_SOURCE_EVIDENCE", {"synthetic": synthetic})
    sg_cur = source_cursor_factory()
    sg_cur.execute(
        "INSERT INTO style_guide VALUES (187,'fixture','synthetic','Антоненко-Давидович','literal synthetic passage','',1)"
    )
    with sqlite3.connect(":memory:") as v:
        v.execute("CREATE TABLE forms_all (lemma,word_form,pos,tags,source_location)")
        v.execute("INSERT INTO forms_all VALUES ('fixture','fixture','noun','','synthetic')")
        res = query_source_evidence(
            "synthetic", "fixture", "", synthetic["authority"], "synthetic", sg_cur, v.cursor(), []
        )
    assert res["status"] == "source_attested"
    assert res["binding"]["locator"] == "style_guide:187"


def test_cf_r13_remediations_regression(require_vesum_db, hermetic_source_cursor, source_cursor_factory) -> None:
    """CF-R13 regression: verify strict author citation anchors and fail-closed behavior for unrelated books.

    Remediates:
    - Blocker 1: Unrelated records (e.g. agricultural machinery 'Книга про трактори' containing 'завдання'
      and 'граматика') must fail closed and never substantiate a Ponomariv citation.
    - Blocker 2: Another author's textbook (e.g. Avramenko textbook containing 'охочий') must fail closed
      and never substantiate an Antonenko-Davydovych citation.
    - Blocker 3: A record that lacks the supporting passage content must fail closed.
    - Lookup and binding for Ponomariv, Antonenko, and inflected forms (e.g. 'тло')
      against a controlled fixture. This does not verify source authenticity.
    """
    import sqlite3

    from scripts.projects.open_model_data.build_decolonization_cases import query_source_evidence

    real_v_cur = sqlite3.connect(f"{Path(require_vesum_db).resolve().as_uri()}?mode=ro", uri=True).cursor()
    fixture_s_cur = hermetic_source_cursor

    # 1. TractorBookMockCursor: 'Книга про трактори' containing 'завдання' and 'граматика'

    with pytest.raises(
        ValueError,
        match="Held source",
    ):
        query_source_evidence(
            case_id="decol_lex_003",
            term="завдання",
            copy="задача",
            auth="Олександр Пономарів «Культура слова»",
            cat_name="calque_lexical",
            s_cur=source_cursor_factory("fixture from a different book"),
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # 2. AvramenkoTextbookMockCursor: Avramenko textbook containing 'охочий'

    with pytest.raises(
        ValueError,
        match="Held source",
    ):
        query_source_evidence(
            case_id="decol_lex_004",
            term="охочий",
            copy="бажаючий",
            auth="Борис Антоненко-Давидович «Як ми говоримо»",
            cat_name="calque_lexical",
            s_cur=source_cursor_factory("fixture from a different book"),
            v_cur=real_v_cur,
            style_guide_cache=[],
        )

    # 3. make_reviewer_confirmation must fail closed on TractorBookMockCursor
    from scripts.projects.open_model_data.build_decolonization_cases import make_reviewer_confirmation
    from scripts.projects.open_model_data.decolonization_cases_data import LEXICAL_CALQUES

    lex_003_item = next(c for c in LEXICAL_CALQUES if c["case_id"] == "decol_lex_003")
    with pytest.raises(
        ValueError,
        match="Held source",
    ):
        make_reviewer_confirmation(
            lex_003_item, "calque_lexical", real_v_cur, source_cursor_factory("fixture from a different book"), []
        )

    # 4. Controlled database resolution for the recorded citation metadata
    res_pon = query_source_evidence(
        case_id="decol_lex_003",
        term="завдання",
        copy="задача",
        auth="Олександр Пономарів «Культура слова»",
        cat_name="calque_lexical",
        s_cur=fixture_s_cur,
        v_cur=real_v_cur,
        style_guide_cache=[],
    )
    assert "пономарів" in res_pon["source"].lower()
    assert res_pon["status"] == "source_attested"

    res_ant = query_source_evidence(
        case_id="decol_lex_004",
        term="охочий",
        copy="бажаючий",
        auth="Борис Антоненко-Давидович «Як ми говоримо»",
        cat_name="calque_lexical",
        s_cur=fixture_s_cur,
        v_cur=real_v_cur,
        style_guide_cache=[],
    )
    assert "антоненко" in res_ant["source"].lower()

    res_tlo = query_source_evidence(
        case_id="decol_lex_020",
        term="тло",
        copy="фон",
        auth="Олександр Пономарів «Культура слова»",
        cat_name="calque_lexical",
        s_cur=fixture_s_cur,
        v_cur=real_v_cur,
        style_guide_cache=[],
    )
    assert "пономарів" in res_tlo["source"].lower()
    assert res_tlo["status"] == "source_attested"


def test_cf_r14_dictionary_binding_regression(dictionary_probe):
    """Unrelated rows and alternate dictionaries cannot authenticate a modern credit."""
    from scripts.projects.open_model_data.build_decolonization_cases import SourceEvidenceUnavailable

    sources, _, _ = dictionary_probe
    sources.execute(
        "INSERT INTO sum20_articles VALUES (999,'UNRELATED','unrelated','unrelated definition','','https://sum20ua.com/?wordid=999','')"
    )
    with pytest.raises(SourceEvidenceUnavailable) as error:
        _query_dictionary(dictionary_probe)
    assert error.value.reason_code == "held_source_unproven"
    # Even the identical passage in a different dictionary cannot supply the credit.
    sources.execute("INSERT INTO ulif_dictua_entries VALUES (888,'fixture','fixture','literal synthetic passage')")
    with pytest.raises(SourceEvidenceUnavailable) as error:
        _query_dictionary(dictionary_probe)
    assert error.value.reason_code == "held_source_unproven"


def test_cf_r15_phrase_attestation_regression(dictionary_probe):
    """Headword/alternative/normalized matches fail; a later literal same-source witness passes."""
    from scripts.projects.open_model_data.build_decolonization_cases import SourceEvidenceUnavailable

    sources, vesum, evidence = dictionary_probe
    evidence["target_term"] = "fixture phrase"
    evidence["supporting_passage"] = "fixture phrase literal synthetic passage"
    vesum.execute("INSERT INTO forms_all VALUES ('phrase','phrase','noun','','synthetic')")
    for row_id, text in enumerate(
        [
            "fixture",
            "alternative phrase",
            "FIXTURE phrase literal synthetic passage",
            "fixture phrase literal\nsynthetic passage",
        ],
        start=1,
    ):
        sources.execute(
            "INSERT INTO sum20_articles VALUES (?, 'FIXTURE', 'fixture', ?, '', 'https://sum20ua.com/?wordid=12', '')",
            (row_id, text),
        )
        with pytest.raises(SourceEvidenceUnavailable) as error:
            _query_dictionary(dictionary_probe)
        assert error.value.reason_code == "held_source_unproven"
    sources.execute(
        "INSERT INTO sum20_articles VALUES (12,'FIXTURE','fixture','fixture phrase literal synthetic passage','','https://sum20ua.com/?wordid=12','')"
    )
    result = _query_dictionary(dictionary_probe)
    assert result["status"] == "source_attested"
    assert result["binding"]["row_id"] == 12
    assert result["supporting_passage"] == "fixture phrase literal synthetic passage"


@pytest.mark.needs_artifact(
    "open_model_component_payload", "projects/open_model_data/components/decolonization/decolonization_train.jsonl"
)
def test_cf_r20_remediations_regression(decolonization_data, require_local_databases):
    """Verify CF-R20 findings remediations: ПЛИН, ЗАГАЛ, ЧАС, and sample review audit."""
    import sqlite3

    from scripts.projects.open_model_data.audit_dataset_acceptance import DEFAULT_SOURCES_DB, VESUM_DB_PATH
    from scripts.projects.open_model_data.build_decolonization_cases import query_source_evidence
    from scripts.projects.open_model_data.decolonization_evidence_catalog import EXPLICIT_SOURCE_EVIDENCE
    from scripts.projects.open_model_data.sum20_codification_records import (
        COMMITTED_SUM20_RECORDS,
    )

    # 1. ПЛИН: published entry text has no appended '; з плином часу.'
    plin = COMMITTED_SUM20_RECORDS["ПЛИН"]
    assert "з плином часу" not in plin["article_text"]
    assert "з плином часу" not in plin["definition_text"]
    assert "плин часу майже не позначився на жінці (П. Загребельний)" in plin["article_text"]

    # 2. ЗАГАЛ: published ВТС entry text has no appended usage notes
    zagal = COMMITTED_SUM20_RECORDS["ЗАГАЛ"]
    assert "Усталене вживання" not in zagal["article_text"]
    assert "на загал — у цілому" not in zagal["article_text"]
    assert zagal["article_text"] == "зага́л -у, ч. Велике коло, маса людей, товариство, широка громадськість; усі."
    assert zagal["definition_text"] == "Велике коло, маса людей, товариство, широка громадськість; усі."

    # 3. Case catalog: decol_prot_072 authority and source must be ВТС
    ev_072 = EXPLICIT_SOURCE_EVIDENCE["decol_prot_072"]
    assert ev_072["authority"] == "ВТС"
    assert ev_072["source"] == "ВТС"
    assert ev_072["target_term"] == "загал"
    assert "загал" in ev_072["ukrainian_proper"]

    # 4. ЧАС: author of quotation is О. Довженко, not М. Рильський
    chas = COMMITTED_SUM20_RECORDS["ЧАС"]
    assert "В той час я мріяв стати художником (О. Довженко)" in chas["article_text"]
    assert "М. Рильський" not in chas["article_text"]

    ev_074 = EXPLICIT_SOURCE_EVIDENCE["decol_prot_074"]
    assert "В той час я мріяв стати художником (О. Довженко)" in ev_074["supporting_passage"]
    assert "М. Рильський" not in ev_074["supporting_passage"]

    # 5. Live query verification for all 3 remediated cases
    v_conn = sqlite3.connect(f"{Path(VESUM_DB_PATH).resolve().as_uri()}?mode=ro", uri=True)
    v_cur = v_conn.cursor()

    s_conn = sqlite3.connect(f"{Path(DEFAULT_SOURCES_DB).resolve().as_uri()}?mode=ro", uri=True)
    ensure_reproducible_sum20_table(s_conn)
    s_cur = s_conn.cursor()

    res_071 = query_source_evidence(
        case_id="decol_prot_071",
        term="плин часу",
        copy="",
        auth="СУМ-20",
        cat_name="protective_authentic",
        s_cur=s_cur,
        v_cur=v_cur,
        style_guide_cache=[],
    )
    assert res_071["status"] == "source_attested"

    res_072 = query_source_evidence(
        case_id="decol_prot_072",
        term="загал",
        copy="",
        auth="ВТС",
        cat_name="protective_authentic",
        s_cur=s_cur,
        v_cur=v_cur,
        style_guide_cache=[],
    )
    assert res_072["status"] == "source_attested"

    res_074 = query_source_evidence(
        case_id="decol_prot_074",
        term="у той же час",
        copy="",
        auth="СУМ-20",
        cat_name="protective_authentic",
        s_cur=s_cur,
        v_cur=v_cur,
        style_guide_cache=[],
    )
    assert res_074["status"] == "source_attested"

    # 6. Sample review receipt verification
    receipt_file = REGISTRY_DECOLONIZATION_DIR / "acceptance_review_sample.receipt.json"
    assert receipt_file.is_file(), f"Missing receipt file at {receipt_file}"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt["verdict"] == "APPROVED"
    assert receipt["sample_size_reviewed"] == 300
    assert receipt["blocker_defect_count"] == 0
    assert receipt["reviewer_id"] == "claude_blue_team_ling_review"
    assert receipt["reviewer_family"] == "claude"


def test_cf_r21_remediations_regression():
    """Regression test for CF-R21 remediations:

    1. decol_prot_072: target_term is 'загал' (noun), authority ВТС, no un-attested 'на загал' claims.
    2. Substantive 300-item receipt: every item has authority, locus, supporting passage, and reviewer rationale.
    """
    import json

    from scripts.projects.open_model_data.decolonization_cases_data import PROTECTIVE_CONTROLS
    from scripts.projects.open_model_data.decolonization_evidence_catalog import EXPLICIT_SOURCE_EVIDENCE
    from scripts.projects.open_model_data.paths import REGISTRY_DECOLONIZATION_DIR

    # 1. decol_prot_072 verifies the noun загал in ВТС without phrase-level extrapolation
    ev_072 = EXPLICIT_SOURCE_EVIDENCE["decol_prot_072"]
    assert ev_072["target_term"] == "загал"
    assert ev_072["authority"] == "ВТС"
    assert ev_072["ukrainian_proper"] == ["загал"]

    case_072 = next(c for c in PROTECTIVE_CONTROLS if c["case_id"] == "decol_prot_072")
    assert case_072["target_term"] == "загал"
    assert case_072["authority"] == "ВТС"
    for ctx in case_072["contexts"]:
        assert "на загал" not in ctx["query"]
        assert "на загал" not in ctx["final_response"]
        assert "загал" in ctx["original_text"]

    # 2. Receipt substantiation: all 300 items have item-level authority and reviewer reasoning
    receipt_file = REGISTRY_DECOLONIZATION_DIR / "acceptance_review_sample.receipt.json"
    assert receipt_file.is_file()
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    items = receipt["reviewed_sample_items"]
    assert len(items) == 300

    signoff_file = REGISTRY_DECOLONIZATION_DIR / "acceptance_review_sample.signoff.json"
    signoff = json.loads(signoff_file.read_text(encoding="utf-8"))
    assert receipt["dataset_sha256"] == signoff["dataset_sha256"]
    assert receipt["sample_seed"] == signoff["sample_seed"]

    for it in items:
        assert it["status"] == "PASS"
        assert len(it["authority"]) > 0
        assert len(it["authority_locus"]) > 0
        assert len(it["supporting_passage"]) > 0
        assert len(it["reviewer_rationale"]) > 20
        assert it["item_verification_audit"]["query_norm_verified"] is True
        assert it["item_verification_audit"]["response_source_grounding_verified"] is True


def test_cf_r22_remediations_regression():
    """Regression test for CF-R22 remediations:

    1. decol_syn_023: supporting_passage in Antonenko-Davydovych addresses doors/windows, not the declension of 'кіл'.
    2. Substantive correction rationales in receipt: never label the accepted target_term as a calque or Russianism.
    """
    import json

    from scripts.projects.open_model_data.decolonization_cases_data import SYNTACTIC_CALQUES
    from scripts.projects.open_model_data.decolonization_evidence_catalog import EXPLICIT_SOURCE_EVIDENCE
    from scripts.projects.open_model_data.paths import REGISTRY_DECOLONIZATION_DIR

    # 1. decol_syn_023 source locus and supporting passage
    ev_023 = EXPLICIT_SOURCE_EVIDENCE["decol_syn_023"]
    assert "відчиняти можна двері, вікна, браму" in ev_023["supporting_passage"]
    assert "Відкривати, відчиняти, розгортати" in ev_023["locus"]
    assert 'іменник "кіл"' not in ev_023["supporting_passage"]

    case_023 = next(c for c in SYNTACTIC_CALQUES if c["case_id"] == "decol_syn_023")
    assert case_023["target_term"] == "відчинити"

    # 2. Receipt item rationales
    receipt_file = REGISTRY_DECOLONIZATION_DIR / "acceptance_review_sample.receipt.json"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    for it in receipt["reviewed_sample_items"]:
        rat = it["reviewer_rationale"]
        if it["is_erroneous"]:
            # Rationale must not call the accepted target_term a calque or Russianism
            assert f"росіянізм «{it['target_term']}»" not in rat
            assert f"кальку / росіянізм «{it['target_term']}»" not in rat
            assert "Нормативний варіант слововживання" in rat


def test_cf_r23_remediations_regression():
    """Regression test for CF-R23 remediations:

    1. decol_syn_011: Retarget from spurious 'віддавати перевагу' (codified in СУМ-20) to
       authentic syntactic calque 'прийняти пропозицію' -> 'ухвалити пропозицію', directly
       condemned in Antonenko-Davydovych's article «Приймати участь – брати участь, приймати
       пропозицію – ухвалювати пропозицію».
    2. 'віддавати перевагу' is nowhere condemned as an erroneous calque in cases.json.
    """
    import json

    from scripts.projects.open_model_data.decolonization_cases_data import SYNTACTIC_CALQUES
    from scripts.projects.open_model_data.decolonization_evidence_catalog import EXPLICIT_SOURCE_EVIDENCE
    from scripts.projects.open_model_data.paths import REGISTRY_DECOLONIZATION_DIR

    # 1. decol_syn_011 in catalog and cases data
    ev_011 = EXPLICIT_SOURCE_EVIDENCE["decol_syn_011"]
    assert ev_011["target_term"] == "ухвалити пропозицію"
    assert ev_011["russian_copy"] == "прийняти пропозицію"
    assert "Приймати участь – брати участь, приймати пропозицію – ухвалювати пропозицію" in ev_011["locus"]
    assert "Негаразд буде по-українському сказати прийняти пропозицію" in ev_011["supporting_passage"]

    case_011 = next(c for c in SYNTACTIC_CALQUES if c["case_id"] == "decol_syn_011")
    assert case_011["target_term"] == "ухвалити пропозицію"
    assert case_011["russian_copy"] == "прийняти пропозицію"

    # 2. Check cases.json
    cases_file = REGISTRY_DECOLONIZATION_DIR / "cases.json"
    cases = json.loads(cases_file.read_text(encoding="utf-8"))
    c_011 = next(c for c in cases if c["case_id"] == "decol_syn_011")
    assert c_011["target_term"] == "ухвалити пропозицію"
    assert c_011["russian_copy"] == "прийняти пропозицію"

    # Ensure 'віддавати перевагу' is not condemned as an erroneous Russianism
    for c in cases:
        if c.get("is_erroneous"):
            assert c.get("russian_copy") != "віддавати перевагу"
