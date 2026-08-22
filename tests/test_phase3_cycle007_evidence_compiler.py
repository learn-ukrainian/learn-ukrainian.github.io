"""Synthetic public tests for the Cycle 007 evidence-sidecar compiler.

No private row content, no network access, no provider output. The
``SyntheticSourcesClient`` below never touches a socket or a real database —
every response is a canned in-memory dict, which is what makes these tests
safe to run anywhere.
"""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any

import pytest

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract
from scripts.projects.open_model_data import phase3_cycle007_evidence_validator as validator


class SyntheticSourcesClient:
    """Deterministic, in-memory ``SourcesClient`` double for tests.

    Every lookup defaults to a clean "not found"/empty result; individual
    tests override just the entries they need via the constructor dicts.
    """

    def __init__(
        self,
        *,
        vesum: dict[str, list[dict[str, str]]] | None = None,
        modern: dict[str, dict[str, Any]] | None = None,
        ulif: dict[str, dict[str, Any]] | None = None,
        slovnyk: dict[str, dict[str, Any]] | None = None,
        grac: dict[str, dict[str, Any]] | None = None,
        style_guide: dict[str, dict[str, Any]] | None = None,
        antonenko_text: dict[str, dict[str, Any]] | None = None,
        ua_gec: dict[str, dict[str, Any]] | None = None,
        heritage: dict[str, dict[str, Any]] | None = None,
        russian_shadow: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._vesum = vesum or {}
        self._modern = modern or {}
        self._ulif = ulif or {}
        self._slovnyk = slovnyk or {}
        self._grac = grac or {}
        self._style_guide = style_guide or {}
        self._antonenko_text = antonenko_text or {}
        self._ua_gec = ua_gec or {}
        self._heritage = heritage or {}
        self._russian_shadow = russian_shadow or {}
        self.call_log: list[tuple[str, str]] = []

    def server_identity(self) -> dict[str, Any]:
        return {
            "server_code_sha256": "a" * 64,
            "sources_db_sha256": "b" * 64,
            "sources_db_bytes": 1,
            "vesum_db_sha256": "c" * 64,
            "vesum_db_bytes": 1,
        }

    def verify_words(self, words):
        self.call_log.append(("verify_words", ",".join(words)))
        return {word: self._vesum.get(word, []) for word in words}

    def check_modern_form(self, word):
        self.call_log.append(("check_modern_form", word))
        return self._modern.get(
            word, {"found": False, "is_modern_codified": False, "has_archaic_form": False, "has_only_archaic_form": False}
        )

    def ulif_cached(self, word):
        self.call_log.append(("ulif_cached", word))
        return self._ulif.get(word, {"status": "unavailable", "payload": None})

    def slovnyk_me_cached(self, word):
        self.call_log.append(("slovnyk_me_cached", word))
        return self._slovnyk.get(word, {"status": "unavailable", "payload": None})

    def grac_cached(self, word):
        self.call_log.append(("grac_cached", word))
        return self._grac.get(word, {"status": "unavailable", "payload": None})

    def search_style_guide(self, query):
        self.call_log.append(("search_style_guide", query))
        return self._style_guide.get(query, {"status": "not_found", "hits": []})

    def search_antonenko_text(self, query):
        self.call_log.append(("search_antonenko_text", query))
        return self._antonenko_text.get(query, {"status": "not_found", "hits": []})

    def search_ua_gec_errors(self, query):
        self.call_log.append(("search_ua_gec_errors", query))
        return self._ua_gec.get(query, {"status": "not_found", "hits": []})

    def search_heritage_cached(self, query):
        self.call_log.append(("search_heritage_cached", query))
        return self._heritage.get(query, {"status": "not_found", "hits": []})

    def check_russian_shadow(self, word):
        self.call_log.append(("check_russian_shadow", word))
        return self._russian_shadow.get(word, {"matches_russian": False, "russian_lemma": None, "confidence": 0.0})


def _row(unit_id: str = "unit-1", text: str = "Привіт світ") -> dict[str, Any]:
    return {
        "unit_id": unit_id,
        "unit_sha256": contract.sha256_text(text),
        "family_id": "synthetic",
        "source_text": text,
        "source_text_sha256": contract.sha256_text(text),
        "frozen_locator_sha256": contract.sha256_text("locator:" + unit_id),
    }


# --------------------------------------------------------------------------
# Tokenizer
# --------------------------------------------------------------------------


def test_extract_forms_deduplicates_and_lowercases():
    forms = compiler.extract_forms("Привіт, Привіт! світ-мир.")
    assert forms == sorted({"привіт", "світ-мир"})


def test_split_compound_requires_two_valid_parts():
    assert compiler.split_compound("світ-мир") == ["світ", "мир"]
    assert compiler.split_compound("привіт") is None
    assert compiler.split_compound("світ-123") is None


# --------------------------------------------------------------------------
# Determinism, hash/source/parser drift
# --------------------------------------------------------------------------


def test_compile_row_evidence_is_deterministic():
    row = _row()
    client_a = SyntheticSourcesClient(vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]})
    client_b = SyntheticSourcesClient(vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]})
    result_a = compiler.compile_row_evidence(row, client_a, source_version="v1")
    result_b = compiler.compile_row_evidence(row, client_b, source_version="v1")
    assert result_a["evidence_ids"] == result_b["evidence_ids"]
    assert [r["evidence_id"] for r in result_a["evidence"]] == [r["evidence_id"] for r in result_b["evidence"]]


def test_retrieval_hash_drift_changes_evidence_id():
    row = _row()
    client_hit = SyntheticSourcesClient(vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]})
    client_miss = SyntheticSourcesClient()
    ids_hit = compiler.compile_row_evidence(row, client_hit, source_version="v1")["evidence_ids"]
    ids_miss = compiler.compile_row_evidence(row, client_miss, source_version="v1")["evidence_ids"]
    assert ids_hit != ids_miss


def test_source_version_drift_changes_evidence_id():
    row = _row()
    client = SyntheticSourcesClient(vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]})
    ids_v1 = compiler.compile_row_evidence(row, client, source_version="v1")["evidence_ids"]
    ids_v2 = compiler.compile_row_evidence(row, client, source_version="v2")["evidence_ids"]
    assert ids_v1 != ids_v2


def test_parser_drift_changes_evidence_id_via_contract():
    row = _row()
    common = dict(
        channel="vesum_attestation",
        source_identity="vesum",
        source_version="v1",
        locator="loc",
        query="привіт",
        query_sha256=contract.sha256_text("привіт"),
        status="attested",
        supports="attestation",
        retrieval_sha256=contract.sha256_text("payload"),
        row=row,
    )
    record_a = contract.build_evidence_record(parser_id="p", parser_version="1", **common)
    record_b = contract.build_evidence_record(parser_id="p", parser_version="2", **common)
    assert record_a["evidence_id"] != record_b["evidence_id"]


def test_row_identity_makes_evidence_id_row_scoped():
    """The same query/result compiled for two different rows must yield distinct IDs."""
    client = SyntheticSourcesClient(vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]})
    row_a = _row("unit-a")
    row_b = _row("unit-b")
    ids_a = compiler.compile_row_evidence(row_a, client, source_version="v1")["evidence_ids"]
    ids_b = compiler.compile_row_evidence(row_b, client, source_version="v1")["evidence_ids"]
    assert set(ids_a).isdisjoint(ids_b)


# --------------------------------------------------------------------------
# Unconditional modern-form / heritage / Russianism paths
# --------------------------------------------------------------------------


def test_check_modern_form_runs_regardless_of_vesum_batch_result():
    row = _row()
    client = SyntheticSourcesClient(
        vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]},
        modern={"привіт": {"found": True, "is_modern_codified": False, "has_archaic_form": True, "has_only_archaic_form": True}},
    )
    result = compiler.compile_row_evidence(row, client, source_version="v1")
    assert ("check_modern_form", "привіт") in client.call_log
    assert result["archaic_only_risk"] is True
    vesum_records = [r for r in result["evidence"] if r["source_identity"] == "vesum"]
    assert any(r["supports"] == "archaic_attestation" for r in vesum_records)


def test_heritage_style_ua_gec_and_russian_shadow_run_for_every_row():
    row = _row(text="Проста фраза")
    client = SyntheticSourcesClient()
    result = compiler.compile_row_evidence(row, client, source_version="v1")
    channels = {r["channel"] for r in result["evidence"]}
    assert {"antonenko_style", "ua_gec_calque", "heritage_attestation", "russian_shadow_suspicion", "source_metadata"} <= channels
    assert any(name == "search_style_guide" for name, _ in client.call_log)
    assert any(name == "search_antonenko_text" for name, _ in client.call_log)
    assert any(name == "search_ua_gec_errors" for name, _ in client.call_log)
    assert any(name == "search_heritage_cached" for name, _ in client.call_log)
    assert any(name == "check_russian_shadow" for name, _ in client.call_log)


def test_row_with_no_extractable_forms_still_gets_every_row_channels():
    row = _row(text="12345 !!!")
    client = SyntheticSourcesClient()
    result = compiler.compile_row_evidence(row, client, source_version="v1")
    assert result["extracted_forms"] == []
    channels = {r["channel"] for r in result["evidence"]}
    assert "russian_shadow_suspicion" in channels
    assert "antonenko_style" in channels


# --------------------------------------------------------------------------
# VESUM-miss escalation is never condemnation
# --------------------------------------------------------------------------


def test_vesum_miss_escalates_without_condemning():
    row = _row(text="слово")
    client = SyntheticSourcesClient(
        ulif={"слово": {"status": "not_found", "payload": None}},
        grac={"слово": {"status": "unavailable", "payload": None}},
    )
    result = compiler.compile_row_evidence(row, client, source_version="v1")
    vesum_records = [r for r in result["evidence"] if r["channel"] == "vesum_attestation" and r["source_identity"] == "vesum"]
    assert vesum_records and vesum_records[0]["status"] == "not_found"
    assert vesum_records[0]["negative_reason"] == "vesum_miss"
    # A VESUM miss must never itself be flagged as a Russian/invalid form:
    # russian_shadow_suspicion evidence can only ever carry suspicion-grade
    # (or no_conclusion) support, never attestation/normative_rule.
    assert all(
        r["supports"] in {"suspicion", "no_conclusion"}
        for r in result["evidence"]
        if r["channel"] == "russian_shadow_suspicion"
    )
    assert ("ulif_cached", "слово") in client.call_log
    assert ("grac_cached", "слово") in client.call_log
    assert not result["sufficient_support"]


def test_vesum_miss_escalation_can_still_attest_via_ulif():
    row = _row(text="архаїзм")
    client = SyntheticSourcesClient(ulif={"архаїзм": {"status": "attested", "payload": {"canonical_headword": "архаїзм"}}})
    result = compiler.compile_row_evidence(row, client, source_version="v1")
    ulif_records = [r for r in result["evidence"] if r["source_identity"] == "ulif"]
    assert ulif_records[0]["status"] == "attested"
    assert ulif_records[0]["supports"] == "attestation"
    assert result["sufficient_support"] is True


def test_compound_split_checks_each_part():
    row = _row(text="світ-мир")
    client = SyntheticSourcesClient(vesum={"світ": [{"lemma": "світ", "pos": "noun", "tags": ""}]})
    result = compiler.compile_row_evidence(row, client, source_version="v1")
    assert ("check_modern_form", "світ") in client.call_log
    assert ("check_modern_form", "мир") in client.call_log


# --------------------------------------------------------------------------
# Russian-shadow-only never rejects, never accepts
# --------------------------------------------------------------------------


def test_russian_shadow_alone_is_never_sufficient_support():
    row = _row(text="получити")
    client = SyntheticSourcesClient(russian_shadow={"получити": {"matches_russian": True, "russian_lemma": "получить", "confidence": 0.95}})
    result = compiler.compile_row_evidence(row, client, source_version="v1")
    shadow_records = [r for r in result["evidence"] if r["channel"] == "russian_shadow_suspicion"]
    assert shadow_records and shadow_records[0]["status"] == "attested"
    assert shadow_records[0]["supports"] == "suspicion"
    assert result["sufficient_support"] is False
    # The closed claim boundary makes it structurally impossible for this
    # channel to ever emit "attestation" or "normative_rule".
    assert all(record["supports"] in {"suspicion", "no_conclusion"} for record in shadow_records)


def test_russian_shadow_suspicion_is_a_valid_evidence_reference_but_insufficient():
    row = _row(text="получити")
    client = SyntheticSourcesClient(russian_shadow={"получити": {"matches_russian": True, "russian_lemma": "получить", "confidence": 0.95}})
    row_evidence = compiler.compile_row_evidence(row, client, source_version="v1")
    shadow_id = next(r["evidence_id"] for r in row_evidence["evidence"] if r["channel"] == "russian_shadow_suspicion")
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_label_evidence_refs(
            row_evidence, decision_code="positive", evidence_ids=[shadow_id]
        )
    assert excinfo.value.code == "insufficient_evidence_for_decision"
    # The uncertainty path with the same reference is valid.
    validator.validate_label_evidence_refs(row_evidence, decision_code="abstention", evidence_ids=[shadow_id])


# --------------------------------------------------------------------------
# Source unavailability fails closed, never invents evidence
# --------------------------------------------------------------------------


def test_grac_unavailable_by_default_never_invents_occurrence_evidence():
    row = _row(text="слово")
    client = SyntheticSourcesClient()
    result = compiler.compile_row_evidence(row, client, source_version="v1")
    grac_records = [r for r in result["evidence"] if r["source_identity"] == "grac"]
    assert grac_records and grac_records[0]["status"] == "unavailable"
    assert grac_records[0]["supports"] == "no_conclusion"


def test_pravopys_2026_binding_reports_unavailable_without_context_receipt(tmp_path: Path):
    row = _row()
    missing_receipt = tmp_path / "missing-receipt.json"
    record = compiler.bind_pravopys_2026_evidence(row, "pravopys-2026-apostrophe-rule", context_receipt_path=missing_receipt)
    assert record["status"] == "unavailable"
    assert record["supports"] == "no_conclusion"
    assert record["channel"] == "pravopys_2026_normative"


# --------------------------------------------------------------------------
# Sidecar assembly, permissions, non-disclosure
# --------------------------------------------------------------------------


def test_compile_sidecar_bundle_writes_private_files_with_correct_modes(tmp_path: Path):
    client = SyntheticSourcesClient(vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]})
    packets = [[_row("unit-1"), _row("unit-2", text="Добрий день")], [_row("unit-3", text="Дякую")]]
    output_dir = tmp_path / "sidecars"
    manifest = compiler.compile_sidecar_bundle(packets, client, output_dir)
    assert manifest["packet_count"] == 2
    assert manifest["row_count"] == 3
    assert manifest["network_lookups_performed"] == 0
    assert stat.S_IMODE(output_dir.stat().st_mode) == compiler.PRIVATE_DIR_MODE
    for path in output_dir.iterdir():
        assert stat.S_IMODE(path.stat().st_mode) == compiler.PRIVATE_FILE_MODE


def test_public_manifest_is_text_free(tmp_path: Path):
    client = SyntheticSourcesClient()
    packets = [[_row("unit-1", text="Приватний текст рядка")]]
    manifest = compiler.compile_sidecar_bundle(packets, client, tmp_path / "sidecars")
    dumped = contract.canonical_json(manifest)
    assert "Приватний текст рядка" not in dumped
    assert "unit-1" not in dumped
    forbidden_keys = {"query", "row_identity", "locator", "negative_reason"}
    assert forbidden_keys.isdisjoint(manifest.keys())


def test_public_evidence_projection_strips_private_fields():
    row = _row(text="Приватний текст")
    client = SyntheticSourcesClient()
    row_evidence = compiler.compile_row_evidence(row, client, source_version="v1")
    for record in row_evidence["evidence"]:
        projection = contract.public_evidence_projection(record)
        dumped = contract.canonical_json(projection)
        assert "row_identity" not in projection
        assert "query" not in projection
        assert "Приватний текст" not in dumped


def test_compile_sidecar_bundle_refuses_to_overwrite_existing_sidecar(tmp_path: Path):
    client = SyntheticSourcesClient()
    output_dir = tmp_path / "sidecars"
    compiler.compile_sidecar_bundle([[_row("unit-1")]], client, output_dir)
    with pytest.raises(contract.EvidenceContractError):
        compiler.compile_sidecar_bundle([[_row("unit-1")]], client, output_dir)
