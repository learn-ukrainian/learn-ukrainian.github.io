"""Complete 30-source Phase 3 policy tests."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.ingest import incremental_textbook_ingest as textbook_ingest
from scripts.projects.open_model_data import phase3_source_policy_v4 as policy_v4
from scripts.projects.open_model_data import phase3_university_source_admission as admission
from scripts.projects.open_model_data import university_source_policy

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "data/projects/open_model_data/admission/phase3_complete_source_policy_v4.json"


def _policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _reseal(policy: dict) -> dict:
    body = {key: value for key, value in policy.items() if key != "receipt_sha256"}
    policy["receipt_sha256"] = hashlib.sha256((policy_v4.canonical_json(body) + "\n").encode("utf-8")).hexdigest()
    return policy


def test_tracked_policy_is_exact_and_semantically_closed():
    document, policy_sha256 = policy_v4.load_policy(POLICY_PATH)

    assert policy_sha256 == policy_v4.EXPECTED_POLICY_SHA256
    assert document["source_count"] == 30
    assert document["disposition_counts"] == {
        "admit_scoped": 11,
        "contextual_only": 15,
        "quarantine": 4,
        "total": 30,
    }
    assert [source["source_id"] for source in document["sources"]] == sorted(admission.FULL_SOURCE_IDS)
    assert document["bindings"] == {
        **policy_v4.EXPECTED_INPUT_HASHES,
        "pr6630_merge_commit": policy_v4.PR6630_MERGE_COMMIT,
    }
    assert document["source_freeze_ready"] is False
    assert document["phase3_complete"] is False
    assert document["phase4_blocked"] is True


def test_policy_preserves_ingest_denominator_without_authorizing_live_mutation():
    document = _policy()
    ingest = document["database_ingest"]

    assert ingest["eligible_source_ids"] == list(admission.SOURCE_IDS)
    assert ingest["staged_not_ingested_source_ids"] == sorted(policy_v4.STAGED_IDS)
    assert ingest["staged_expected_rows"] == {
        "uni-ukrmova-corpus-linguistics-khpi-2021-part-1": 47,
        "uni-ukrmova-corpus-linguistics-khpi-2021-part-2": 51,
        "uni-ukrmova-morphology-volkova-maslo-2012": 205,
        "uni-ukrmova-text-linguistics-shevel-bilyk-2024": 282,
    }
    assert ingest["staged_expected_row_count"] == 585
    assert ingest["copied_database_rehearsal_required"] is True
    assert ingest["live_ingest_authorized"] is False


def test_policy_preserves_historical_and_language_contact_context():
    by_id = {source["source_id"]: source for source in _policy()["sources"]}

    historical_grammar = by_id["uni-ukrmova-historical-grammar-kupchynska-piletskyi-2024"]
    assert historical_grammar["final_disposition"] == "contextual_only"
    assert historical_grammar["supported_uses"] == [
        "historical_diachronic_grammar_context",
        "diachronic_sound_change_and_morphological_evolution",
    ]
    assert "modern_orthography_enforcement" in historical_grammar["prohibited_uses"]

    assert by_id["uni-istoriya-kalynichenko-olianych-2025"]["final_disposition"] == ("contextual_only")
    assert by_id["uni-ukrlit-kalinichenko-2024"]["final_disposition"] == ("contextual_only")
    assert by_id["uni-ukrmova-sociolinguistics-masenko-2010"]["final_disposition"] == "contextual_only"


def test_policy_separates_university_jsonl_from_external_reference_sources():
    sources = _policy()["sources"]
    jsonl_sources = [source for source in sources if source["source_kind"] == "university_jsonl"]
    external_sources = [source for source in sources if source["source_kind"] == "external_reference"]

    assert len(jsonl_sources) == 24
    assert len(external_sources) == 6
    assert all("jsonl_evidence" in source for source in jsonl_sources)
    assert all("jsonl_evidence" not in source for source in external_sources)
    assert all("corpus_ingest" not in source["allowed_lanes"] for source in external_sources)


def test_policy_preserves_pre_2019_and_noncommercial_restrictions():
    for source in _policy()["sources"]:
        if source["final_disposition"] == "admit_scoped" and source["orthography_regime"] == "pre_2019":
            assert set(source["prohibited_uses"]) & policy_v4.POST_2019_AUTHORITY_RESTRICTIONS
        if source["rights_capability"] == "cc_by_nc_4_0_noncommercial_only":
            assert policy_v4.NONCOMMERCIAL_RESTRICTION in source["prohibited_uses"]


def test_policy_rejects_staged_jsonl_identity_drift_even_when_resealed():
    document = copy.deepcopy(_policy())
    staged = next(
        source for source in document["sources"] if source["source_id"] == "uni-ukrmova-morphology-volkova-maslo-2012"
    )
    staged["jsonl_evidence"]["jsonl_sha256"] = "0" * 64

    with pytest.raises(policy_v4.CompleteSourcePolicyError, match="staged JSONL evidence drift"):
        policy_v4.validate_policy_document(_reseal(document))


def test_policy_rejects_external_corpus_ingest_even_when_resealed():
    document = copy.deepcopy(_policy())
    external = next(source for source in document["sources"] if source["source_kind"] == "external_reference")
    external["allowed_lanes"].append("corpus_ingest")

    with pytest.raises(policy_v4.CompleteSourcePolicyError, match="schema violation"):
        policy_v4.validate_policy_document(_reseal(document))


def test_policy_rejects_source_omission_even_when_counts_are_rewritten():
    document = copy.deepcopy(_policy())
    document["sources"] = document["sources"][:-1]
    document["source_count"] = 29
    document["disposition_counts"]["quarantine"] = 3
    document["disposition_counts"]["total"] = 29

    with pytest.raises(policy_v4.CompleteSourcePolicyError, match="schema violation"):
        policy_v4.validate_policy_document(_reseal(document))


def test_schema_rejects_open_source_fields():
    document = copy.deepcopy(_policy())
    document["sources"][0]["unreviewed_note"] = "not allowed"
    schema = json.loads(policy_v4.SCHEMA_PATH.read_text(encoding="utf-8"))

    errors = list(Draft202012Validator(schema).iter_errors(document))
    assert errors
    assert any("Additional properties are not allowed" in error.message for error in errors)


def test_legacy_policy_loader_accepts_v4_for_jsonl_consumers():
    document, policy_sha256 = university_source_policy.load_policy(POLICY_PATH)

    assert document["schema_version"] == policy_v4.SCHEMA_VERSION
    assert policy_sha256 == policy_v4.EXPECTED_POLICY_SHA256


def test_runtime_loader_rejects_byte_drift_even_when_json_is_semantically_identical(tmp_path):
    drifted = tmp_path / POLICY_PATH.name
    drifted.write_text(POLICY_PATH.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(policy_v4.CompleteSourcePolicyError, match="byte drift"):
        policy_v4.load_policy(drifted)
    with pytest.raises(university_source_policy.UniversitySourcePolicyError, match="byte drift"):
        university_source_policy.load_policy(drifted)


def test_external_reference_cannot_impersonate_university_jsonl(tmp_path):
    dummy_jsonl = tmp_path / "khpi-ukrainian-morphological-tagging-petrasova-et-al-2017.jsonl"
    dummy_jsonl.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        university_source_policy.UniversitySourcePolicyError,
        match="external reference has no university JSONL identity",
    ):
        university_source_policy.require_source_admission(
            source_file="khpi-ukrainian-morphological-tagging-petrasova-et-al-2017",
            jsonl_path=dummy_jsonl,
            policy_path=POLICY_PATH,
            lane="contextual_retrieval",
        )


def test_staged_argument_parser_is_closed():
    with pytest.raises(policy_v4.CompleteSourcePolicyError, match="SOURCE_ID=PATH"):
        policy_v4._parse_staged_jsonls(["missing-separator"])
    with pytest.raises(policy_v4.CompleteSourcePolicyError, match="duplicate"):
        policy_v4._parse_staged_jsonls(["source=/one", "source=/two"])


def test_v4_policy_blocks_live_ingest_before_reading_chunks(tmp_path):
    disposable_db = tmp_path / "copy.db"
    disposable_db.touch()

    with pytest.raises(textbook_ingest.IngestError, match="does not authorize live ingest"):
        textbook_ingest.ingest(
            ["uni-ukrmova-corpus-linguistics-khpi-2021-part-1"],
            db_path=disposable_db,
            dry_run=False,
            chunks_root=tmp_path / "absent-chunks",
            university_policy_path=POLICY_PATH,
        )


def test_v4_rehearsal_refuses_live_database_inode(tmp_path, monkeypatch):
    live_db = tmp_path / "sources.db"
    live_db.touch()
    alias_db = tmp_path / "separate-path-same-inode.db"
    alias_db.hardlink_to(live_db)
    monkeypatch.setattr(textbook_ingest, "DEFAULT_DB", live_db)

    with pytest.raises(textbook_ingest.IngestError, match="refuses the live sources database"):
        textbook_ingest.ingest(
            ["uni-ukrmova-corpus-linguistics-khpi-2021-part-1"],
            db_path=alias_db,
            dry_run=False,
            chunks_root=tmp_path / "absent-chunks",
            university_policy_path=POLICY_PATH,
            copied_database_rehearsal=True,
        )


def test_v4_rehearsal_requires_a_committed_disposable_copy(tmp_path):
    disposable_db = tmp_path / "copy.db"
    disposable_db.touch()

    with pytest.raises(textbook_ingest.IngestError, match="must commit"):
        textbook_ingest.ingest(
            ["uni-ukrmova-corpus-linguistics-khpi-2021-part-1"],
            db_path=disposable_db,
            dry_run=True,
            chunks_root=tmp_path / "absent-chunks",
            university_policy_path=POLICY_PATH,
            copied_database_rehearsal=True,
        )
