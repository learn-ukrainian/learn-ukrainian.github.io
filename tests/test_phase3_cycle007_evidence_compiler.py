"""Synthetic public tests for the Cycle 007 evidence-sidecar compiler.

No private row content, no network access, no provider output. The
``SyntheticSourcesClient`` below never touches a socket or a real database —
every response is a canned in-memory dict. ``FakeMcpToolTransport``-backed
tests exercise ``LocalMcpSourcesClient`` itself (the real MCP adapter's
parsing/fail-closed logic) without ever opening a socket either.
"""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any

import pytest

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract
from scripts.projects.open_model_data import phase3_cycle007_evidence_validator as validator
from scripts.projects.open_model_data import phase3_cycle007_materializer as materializer


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
        pravopys: dict[str, dict[str, Any]] | None = None,
        server_identity: dict[str, Any] | None = None,
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
        self._pravopys = pravopys or {}
        self._server_identity = server_identity or {
            "server_code_sha256": "a" * 64,
            "sources_db_sha256": "b" * 64,
            "sources_db_bytes": 1,
            "vesum_db_sha256": "c" * 64,
            "vesum_db_bytes": 1,
        }
        self.call_log: list[tuple[str, str]] = []

    def server_identity(self) -> dict[str, Any]:
        return self._server_identity

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

    def query_pravopys(self, topic):
        self.call_log.append(("query_pravopys", topic))
        return self._pravopys.get(topic, {"status": "not_found", "hits": []})


def _row(unit_id: str = "unit-1", text: str = "Привіт світ") -> dict[str, Any]:
    return {
        "unit_id": unit_id,
        "unit_sha256": contract.sha256_text(text),
        "family_id": "synthetic",
        "source_text": text,
        "source_text_sha256": contract.sha256_text(text),
        "frozen_locator_sha256": contract.sha256_text("locator:" + unit_id),
    }


def _identity(**overrides: Any) -> dict[str, Any]:
    base = {
        "server_code_sha256": "a" * 64,
        "sources_db_sha256": "b" * 64,
        "sources_db_bytes": 1,
        "vesum_db_sha256": "c" * 64,
        "vesum_db_bytes": 1,
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------
# Tokenizer / compound splitter
# --------------------------------------------------------------------------


def test_extract_forms_deduplicates_and_lowercases():
    forms = compiler.extract_forms("Привіт, Привіт! світ-мир.")
    assert forms == sorted({"привіт", "світ-мир"})


def test_split_compound_requires_two_valid_parts():
    assert compiler.split_compound("світ-мир") == ("resolved", ["світ", "мир"])
    assert compiler.split_compound("привіт") == ("not_compound", None)
    assert compiler.split_compound("світ-123") == ("ambiguous", None)


def test_split_compound_marks_short_component_ambiguous():
    """A single-character component is unresolved, never silently accepted (amendment step 2/11)."""
    status, parts = compiler.split_compound("а-приклад")
    assert status == "ambiguous"
    assert parts is None


# --------------------------------------------------------------------------
# Determinism, hash/source/parser drift
# --------------------------------------------------------------------------


def test_compile_row_evidence_is_deterministic():
    row = _row()
    client_a = SyntheticSourcesClient(vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]})
    client_b = SyntheticSourcesClient(vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]})
    result_a = compiler.compile_row_evidence(row, client_a, identity=_identity())
    result_b = compiler.compile_row_evidence(row, client_b, identity=_identity())
    assert result_a["evidence_ids"] == result_b["evidence_ids"]
    assert [r["evidence_id"] for r in result_a["evidence"]] == [r["evidence_id"] for r in result_b["evidence"]]


def test_retrieval_hash_drift_changes_evidence_id():
    row = _row()
    client_hit = SyntheticSourcesClient(vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]})
    client_miss = SyntheticSourcesClient()
    ids_hit = compiler.compile_row_evidence(row, client_hit, identity=_identity())["evidence_ids"]
    ids_miss = compiler.compile_row_evidence(row, client_miss, identity=_identity())["evidence_ids"]
    assert ids_hit != ids_miss


def test_source_version_drift_changes_evidence_id():
    """VESUM-backed evidence is bound to the actual vesum_db_sha256 (amendment step 10)."""
    row = _row()
    client = SyntheticSourcesClient(vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]})
    ids_v1 = compiler.compile_row_evidence(row, client, identity=_identity(vesum_db_sha256="c" * 64))["evidence_ids"]
    ids_v2 = compiler.compile_row_evidence(row, client, identity=_identity(vesum_db_sha256="d" * 64))["evidence_ids"]
    assert ids_v1 != ids_v2


def test_sources_db_version_drift_changes_evidence_id():
    """sources.db-backed channels (style guide, UA-GEC, heritage) bind sources_db_sha256."""
    row = _row()
    client = SyntheticSourcesClient()
    ids_v1 = compiler.compile_row_evidence(row, client, identity=_identity(sources_db_sha256="b" * 64))["evidence_ids"]
    ids_v2 = compiler.compile_row_evidence(row, client, identity=_identity(sources_db_sha256="e" * 64))["evidence_ids"]
    assert ids_v1 != ids_v2


def test_parser_drift_changes_evidence_id_via_contract():
    row = _row()
    common = dict(
        channel="vesum_attestation",
        source_identity="vesum",
        source_version="v1",
        locator="loc",
        query="привіт",
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
    ids_a = compiler.compile_row_evidence(row_a, client, identity=_identity())["evidence_ids"]
    ids_b = compiler.compile_row_evidence(row_b, client, identity=_identity())["evidence_ids"]
    assert set(ids_a).isdisjoint(ids_b)


# --------------------------------------------------------------------------
# query_sha256 tamper rejection (amendment step 9)
# --------------------------------------------------------------------------


def test_build_evidence_record_rejects_tampered_query_sha256_via_recompute():
    """query_sha256 is never accepted from the caller; it is always derived from query."""
    row = _row()
    record = contract.build_evidence_record(
        channel="vesum_attestation",
        source_identity="vesum",
        source_version="v1",
        locator="loc",
        query="привіт",
        status="attested",
        supports="attestation",
        retrieval_sha256=contract.sha256_text("payload"),
        parser_id="p",
        parser_version="1",
        row=row,
    )
    assert record["query_sha256"] == contract.sha256_text("привіт")
    # A hand-tampered record (query_sha256 swapped for a different query's
    # hash) fails the validator's independent re-derivation.
    tampered = dict(record)
    tampered["query_sha256"] = contract.sha256_text("не-привіт")
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_evidence_record(tampered)
    assert excinfo.value.code == "evidence_id_hash_drift"


def test_no_query_evidence_uses_domain_separated_fixed_hash():
    row = _row()
    record = contract.build_evidence_record(
        channel="source_metadata",
        source_identity="fam",
        source_version="v1",
        locator="loc",
        query=None,
        status="attested",
        supports="metadata_only",
        retrieval_sha256=contract.sha256_text("payload"),
        parser_id="p",
        parser_version="1",
        row=row,
    )
    assert record["query_sha256"] == contract.expected_query_sha256(
        None, channel="source_metadata", source_identity="fam", locator="loc"
    )


# --------------------------------------------------------------------------
# Unconditional modern-form / heritage / Russianism paths
# --------------------------------------------------------------------------


def test_check_modern_form_runs_regardless_of_vesum_batch_result():
    row = _row()
    client = SyntheticSourcesClient(
        vesum={"привіт": [{"lemma": "привіт", "pos": "noun", "tags": ""}]},
        modern={"привіт": {"found": True, "is_modern_codified": False, "has_archaic_form": True, "has_only_archaic_form": True}},
    )
    result = compiler.compile_row_evidence(row, client, identity=_identity())
    assert ("check_modern_form", "привіт") in client.call_log
    assert result["archaic_only_risk"] is True
    vesum_records = [r for r in result["evidence"] if r["source_identity"] == "vesum"]
    assert any(r["supports"] == "archaic_attestation" for r in vesum_records)


def test_heritage_style_ua_gec_and_russian_shadow_run_for_every_row():
    row = _row(text="Проста фраза")
    client = SyntheticSourcesClient()
    result = compiler.compile_row_evidence(row, client, identity=_identity())
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
    result = compiler.compile_row_evidence(row, client, identity=_identity())
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
    result = compiler.compile_row_evidence(row, client, identity=_identity())
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
    result = compiler.compile_row_evidence(row, client, identity=_identity())
    ulif_records = [r for r in result["evidence"] if r["source_identity"] == "ulif"]
    assert ulif_records[0]["status"] == "attested"
    assert ulif_records[0]["supports"] == "attestation"
    assert result["sufficient_support"] is True


def test_compound_split_checks_each_part():
    row = _row(text="світ-мир")
    client = SyntheticSourcesClient(vesum={"світ": [{"lemma": "світ", "pos": "noun", "tags": ""}]})
    result = compiler.compile_row_evidence(row, client, identity=_identity())
    assert ("check_modern_form", "світ") in client.call_log
    assert ("check_modern_form", "мир") in client.call_log


def test_compound_split_escalates_each_part_too():
    """Amendment step 11: cache-only escalation runs for each split part, not just the whole form."""
    row = _row(text="слово-два")
    client = SyntheticSourcesClient()
    result = compiler.compile_row_evidence(row, client, identity=_identity())
    ulif_queries = {query for name, query in client.call_log if name == "ulif_cached"}
    assert {"слово-два", "слово", "два"} <= ulif_queries


def test_ambiguous_compound_split_never_invents_a_decomposition():
    """A single-char component is ambiguous: escalation still runs on the whole form only."""
    row = _row(text="а-приклад")
    client = SyntheticSourcesClient()
    result = compiler.compile_row_evidence(row, client, identity=_identity())
    ulif_queries = {query for name, query in client.call_log if name == "ulif_cached"}
    assert "а-приклад" in ulif_queries
    assert "приклад" not in ulif_queries  # never silently split an ambiguous form


# --------------------------------------------------------------------------
# Russian-shadow-only never rejects, never accepts
# --------------------------------------------------------------------------


def test_russian_shadow_alone_is_never_sufficient_support():
    row = _row(text="получити")
    client = SyntheticSourcesClient(russian_shadow={"получити": {"matches_russian": True, "russian_lemma": "получить", "confidence": 0.95}})
    result = compiler.compile_row_evidence(row, client, identity=_identity())
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
    row_evidence = compiler.compile_row_evidence(row, client, identity=_identity())
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
    result = compiler.compile_row_evidence(row, client, identity=_identity())
    grac_records = [r for r in result["evidence"] if r["source_identity"] == "grac"]
    assert grac_records and grac_records[0]["status"] == "unavailable"
    assert grac_records[0]["supports"] == "no_conclusion"


def test_pravopys_2026_binding_reports_unavailable_without_context_receipt(tmp_path: Path):
    row = _row()
    missing_receipt = tmp_path / "missing-receipt.json"
    record = compiler.bind_pravopys_2026_evidence(row, "apostrophe", context_receipt_path=missing_receipt)
    assert record["status"] == "unavailable"
    assert record["supports"] == "no_conclusion"
    assert record["channel"] == "pravopys_2026_normative"


def test_pravopys_2026_binding_rejects_a_phenomenon_id_outside_the_taxonomy(tmp_path: Path):
    row = _row()
    missing_receipt = tmp_path / "missing-receipt.json"
    with pytest.raises(contract.EvidenceContractError):
        compiler.bind_pravopys_2026_evidence(row, "not-a-real-phenomenon", context_receipt_path=missing_receipt)


def test_pravopys_2019_comparison_calls_query_pravopys_not_style_guide():
    """Amendment step 8: 2019 comparison evidence must come from query_pravopys, never search_style_guide."""
    row = _row()
    client = SyntheticSourcesClient(pravopys={"апостроф": {"status": "attested", "hits": "text"}})
    record = compiler.bind_pravopys_2019_comparison_evidence(row, "apostrophe", client, query="апостроф")
    assert ("query_pravopys", "апостроф") in client.call_log
    assert not any(name == "search_style_guide" for name, _ in client.call_log)
    assert record["channel"] == "pravopys_2019_comparison"
    assert record["status"] == "attested"
    assert record["supports"] == "comparison_only"


def test_pravopys_2019_comparison_never_carries_normative_support():
    row = _row()
    client = SyntheticSourcesClient(pravopys={"апостроф": {"status": "attested", "hits": "text"}})
    record = compiler.bind_pravopys_2019_comparison_evidence(row, "apostrophe", client, query="апостроф")
    assert record["supports"] != "normative_rule"


# --------------------------------------------------------------------------
# Amendment step 7: sufficiency ordering — a decisive negative channel
# forces uncertainty even when another record is attested.
# --------------------------------------------------------------------------


def test_attested_plus_unavailable_decisive_channel_forces_uncertainty():
    row = _row(text="слово")
    client = SyntheticSourcesClient(
        vesum={"слово": [{"lemma": "слово", "pos": "noun", "tags": ""}]},
        heritage={"слово": {"status": "unavailable", "hits": []}},
    )
    row_evidence = compiler.compile_row_evidence(row, client, identity=_identity())
    assert row_evidence["sufficient_support"] is True  # a sufficient-positive record does exist
    sufficiency = validator.classify_sufficiency(row_evidence)
    assert sufficiency == "insufficient_unavailable"
    vesum_id = next(
        r["evidence_id"]
        for r in row_evidence["evidence"]
        if r["channel"] == "vesum_attestation" and r["source_identity"] == "vesum" and r["status"] == "attested"
    )
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_label_evidence_refs(row_evidence, decision_code="agree", evidence_ids=[vesum_id])
    assert excinfo.value.code == "insufficient_evidence_for_decision"
    # The uncertainty path remains valid.
    validator.validate_label_evidence_refs(row_evidence, decision_code="abstention", evidence_ids=[vesum_id])


# --------------------------------------------------------------------------
# Phenomenon-scoped residual evidence (amendment: residual scoping)
# --------------------------------------------------------------------------


def test_residual_lane_produces_phenomenon_scoped_evidence_for_every_phenomenon():
    row = _row(text="Проста фраза")
    client = SyntheticSourcesClient()
    result = compiler.compile_row_evidence(
        row, client, identity=_identity(), residual_phenomena=contract.RESIDUAL_PHENOMENON_TAXONOMY
    )
    assert set(result["phenomenon_evidence_ids"]) == set(contract.RESIDUAL_PHENOMENON_TAXONOMY)
    for phenomenon_id, ids in result["phenomenon_evidence_ids"].items():
        assert ids, f"phenomenon {phenomenon_id} has no bound evidence"


def test_phenomenon_scoped_evidence_shares_retrieval_hash_with_row_level_record():
    """Deduplicated by retrieval hash: the underlying retrieval fact is not re-fetched per phenomenon."""
    row = _row(text="Проста фраза")
    client = SyntheticSourcesClient()
    result = compiler.compile_row_evidence(
        row, client, identity=_identity(), residual_phenomena=("apostrophe", "punctuation")
    )
    row_level = next(r for r in result["evidence"] if r["channel"] == "heritage_attestation" and r["phenomenon_id"] is None)
    scoped = [
        r
        for r in result["evidence"]
        if r["channel"] == "heritage_attestation" and r["phenomenon_id"] in {"apostrophe", "punctuation"}
    ]
    assert len(scoped) == 2
    assert {r["retrieval_sha256"] for r in scoped} == {row_level["retrieval_sha256"]}
    assert {r["evidence_id"] for r in scoped} != {row_level["evidence_id"]}


def test_row_level_evidence_id_never_satisfies_a_residual_phenomenon():
    row = _row(text="Проста фраза")
    client = SyntheticSourcesClient()
    row_evidence = compiler.compile_row_evidence(
        row, client, identity=_identity(), residual_phenomena=("apostrophe",)
    )
    row_level_id = next(
        r["evidence_id"] for r in row_evidence["evidence"] if r["channel"] == "heritage_attestation" and r["phenomenon_id"] is None
    )
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_label_evidence_refs(
            row_evidence, decision_code="protected", evidence_ids=[row_level_id], phenomenon_id="apostrophe"
        )
    assert excinfo.value.code == "cross_phenomenon_evidence"


# --------------------------------------------------------------------------
# Real MCP transport (fake double) — round trip, drift, malformed, timeout
# --------------------------------------------------------------------------


def _passing_transport(**overrides: Any) -> compiler.FakeMcpToolTransport:
    responses: dict[str, Any] = {
        "verify_words": "Batch verification: 1 words\n\nFound: 1/1\n\n- **слово** — FOUND (1 match): слово(noun)",
        "check_modern_form": json.dumps({"is_modern_codified": True, "has_archaic_form": False, "has_only_archaic_form": False}),
        "query_ulif": json.dumps({"status": "not_found", "entry": None}),
        "search_slovnyk_me": "No slovnyk.me results for: \"слово\"",
        "query_grac": json.dumps({"status": "unavailable", "entry": None}),
        "search_style_guide": "No results in Антоненко-Давидович for: \"слово\"",
        "search_text": "No results found.",
        "search_ua_gec_errors": "No UA-GEC results found for: \"слово\"",
        "search_heritage": "No heritage evidence found for: \"слово\"",
        "check_russian_shadow": json.dumps({"matches_russian": False, "russian_lemma": None, "confidence": 0.0}),
        "query_pravopys": "No pravopys section found for: 'слово'",
    }
    responses.update(overrides)
    return compiler.FakeMcpToolTransport(tool_names=compiler.REQUIRED_TOOL_NAMES, responses=responses)


def _stub_client_files(tmp_path: Path) -> dict[str, Path]:
    sources_db = tmp_path / "sources.db"
    vesum_db = tmp_path / "vesum.db"
    server_code = tmp_path / "server.py"
    for path in (sources_db, vesum_db, server_code):
        path.write_bytes(b"stub")
    return {"sources_db": sources_db, "vesum_db": vesum_db, "server_code": server_code}


def test_local_mcp_client_round_trips_through_fake_transport(tmp_path: Path):
    transport = _passing_transport()
    files = _stub_client_files(tmp_path)
    client = compiler.LocalMcpSourcesClient(transport=transport, **files)
    result = client.verify_words(["слово"])
    assert result["слово"]
    assert ("verify_words", {"words": ["слово"]}) in transport.calls
    modern = client.check_modern_form("слово")
    assert modern["found"] is True
    assert modern["is_modern_codified"] is True
    client.close()
    assert transport.closed


def test_local_mcp_client_fails_closed_on_tool_set_drift(tmp_path: Path):
    incomplete_tools = compiler.REQUIRED_TOOL_NAMES - {"query_pravopys"}
    transport = compiler.FakeMcpToolTransport(tool_names=incomplete_tools, responses={})
    files = _stub_client_files(tmp_path)
    with pytest.raises(compiler.McpTransportError):
        compiler.LocalMcpSourcesClient(transport=transport, **files)


def test_local_mcp_client_fails_closed_on_malformed_json(tmp_path: Path):
    transport = _passing_transport(check_modern_form="not json")
    files = _stub_client_files(tmp_path)
    client = compiler.LocalMcpSourcesClient(transport=transport, **files)
    with pytest.raises(compiler.LocalMcpSourcesClientError):
        client.check_modern_form("слово")


def test_local_mcp_client_fails_closed_on_tool_error(tmp_path: Path):
    def _boom(_args: Any) -> str:
        raise compiler.McpTransportError("mcp_tool_error:check_russian_shadow")

    transport = _passing_transport(check_russian_shadow=_boom)
    files = _stub_client_files(tmp_path)
    client = compiler.LocalMcpSourcesClient(transport=transport, **files)
    with pytest.raises(compiler.McpTransportError):
        client.check_russian_shadow("слово")


def test_fake_transport_rejects_a_call_to_an_undeclared_tool(tmp_path: Path):
    transport = compiler.FakeMcpToolTransport(tool_names=compiler.REQUIRED_TOOL_NAMES, responses={})
    with pytest.raises(compiler.McpTransportError):
        transport.call_tool("not_a_real_tool", {})


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
    forbidden_keys = {"query", "row_identity", "locator", "negative_reason", "retrieval_payloads"}
    assert forbidden_keys.isdisjoint(manifest.keys())


def test_public_evidence_projection_strips_private_fields():
    row = _row(text="Приватний текст")
    client = SyntheticSourcesClient()
    row_evidence = compiler.compile_row_evidence(row, client, identity=_identity())
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


def test_compile_sidecar_bundle_refuses_a_nonempty_existing_destination(tmp_path: Path):
    client = SyntheticSourcesClient()
    output_dir = tmp_path / "sidecars"
    output_dir.mkdir()
    (output_dir / "stray.txt").write_text("x")
    with pytest.raises(contract.EvidenceContractError):
        compiler.compile_sidecar_bundle([[_row("unit-1")]], client, output_dir)


def test_compile_sidecar_bundle_rollback_never_touches_a_concurrently_created_destination(tmp_path: Path, monkeypatch):
    """A mid-compile failure removes only this call's own staging directory."""
    client = SyntheticSourcesClient()
    output_dir = tmp_path / "sidecars"

    real_write = compiler._atomic_write_private
    call_count = {"n": 0}

    def _flaky_write(path, payload):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("synthetic mid-compile failure")
        return real_write(path, payload)

    monkeypatch.setattr(compiler, "_atomic_write_private", _flaky_write)
    with pytest.raises(RuntimeError):
        compiler.compile_sidecar_bundle([[_row("unit-1")], [_row("unit-2")]], client, output_dir)
    assert not output_dir.exists()
    staging_leftovers = list(tmp_path.glob(f".{output_dir.name}.staging-*"))
    assert staging_leftovers == []


# --------------------------------------------------------------------------
# Package-bound production entrypoint (amendment step 13)
# --------------------------------------------------------------------------


def _write_cycle005_fixture(root: Path) -> Path:
    """A minimal, real materializer.materialize()-compatible Cycle-005 source."""
    import hashlib
    import os

    source = root / "cycle005-source"
    source.mkdir(mode=materializer.PRIVATE_DIR_MODE)
    os.chmod(source, materializer.PRIVATE_DIR_MODE)
    packet_specs = (("clean_label", 1, 2), ("residual_label", 1, 2))
    packet_records: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for lane, index, count in packet_specs:
        rows = []
        for offset in range(count):
            unit_id = f"synthetic.{lane}.{index:03d}.{offset}"
            rows.append(
                {
                    "unit_id": unit_id,
                    "unit_sha256": hashlib.sha256(unit_id.encode()).hexdigest(),
                    "family_id": "synthetic_family",
                    "source_text": f"Привіт {offset}",
                    "source_text_sha256": contract.sha256_text(f"Привіт {offset}"),
                    "frozen_locator_sha256": contract.sha256_text(f"locator-{unit_id}"),
                }
            )
        all_rows.extend(rows)
        packet = {
            "schema_version": "phase3_cycle005_private_packet_v1",
            "evaluation_cycle_id": materializer.CYCLE005,
            "lane": lane,
            "packet_index": index,
            "row_count": count,
            "rows": rows,
            "packet_identity_set_sha256": materializer.identity_set(rows),
        }
        packet_path = source / lane / f"packet-{index:04d}.json"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_raw = materializer.canonical(packet)
        packet_path.write_bytes(packet_raw)
        os.chmod(packet_path, materializer.PRIVATE_FILE_MODE)
        packet_records.append(
            {
                "lane": lane,
                "packet_index": index,
                "canonical_basename": packet_path.name,
                "row_count": count,
                "raw_sha256": materializer.digest(packet_raw),
                "packet_identity_set_sha256": packet["packet_identity_set_sha256"],
            }
        )
    manifest = {
        "schema_version": "phase3_cycle005_label_manifest_v1",
        "evaluation_cycle_id": materializer.CYCLE005,
        "text_free": True,
        "custody_receipt_raw_sha256": "",
        "packet_count": len(packet_records),
        "row_count": len(all_rows),
        "packets": packet_records,
    }
    custody = {
        "schema_version": "phase3_cycle005_custody_receipt_v1",
        "evaluation_cycle_id": materializer.CYCLE005,
        "text_free": True,
        "provider_artifacts_copied": False,
    }
    custody["receipt_sha256"] = materializer._hash_receipt(custody)
    custody_path = source / "custody-receipt.json"
    custody_raw = materializer.canonical(custody)
    custody_path.write_bytes(custody_raw)
    os.chmod(custody_path, materializer.PRIVATE_FILE_MODE)
    manifest["custody_receipt_raw_sha256"] = materializer.digest(custody_raw)
    manifest["receipt_sha256"] = materializer._hash_receipt(manifest)
    manifest_path = source / "label-manifest.json"
    manifest_path.write_bytes(materializer.canonical(manifest))
    os.chmod(manifest_path, materializer.PRIVATE_FILE_MODE)
    return source


def test_compile_cycle007_package_binds_lane_packet_index_and_basename(tmp_path: Path):
    source = _write_cycle005_fixture(tmp_path)
    package = tmp_path / "cycle007-package"
    materializer.materialize(source, package, fixture=True)
    client = SyntheticSourcesClient()
    sidecars_out = tmp_path / "sidecars"
    manifest = compiler.compile_cycle007_package(package, client, sidecars_out, fixture=True)
    assert manifest["packet_count"] == 2
    assert manifest["row_count"] == 4
    # residual_label packet must have been compiled with phenomenon scoping.
    residual_sidecar = json.loads((sidecars_out / "sidecar-0002.json").read_text())
    assert residual_sidecar["rows"][0]["phenomenon_evidence_ids"]
    clean_sidecar = json.loads((sidecars_out / "sidecar-0001.json").read_text())
    assert clean_sidecar["rows"][0]["phenomenon_evidence_ids"] == {}


def test_compile_cycle007_package_rejects_a_tampered_packet_raw_sha(tmp_path: Path):
    source = _write_cycle005_fixture(tmp_path)
    package = tmp_path / "cycle007-package"
    materializer.materialize(source, package, fixture=True)
    # Tamper with a packet after materialization, without updating the manifest.
    tampered_path = package / "clean_label" / "packet-0001.json"
    body = json.loads(tampered_path.read_text())
    body["rows"][0]["source_text"] = "TAMPERED"
    tampered_path.write_text(contract.canonical_json(body))
    client = SyntheticSourcesClient()
    with pytest.raises(contract.EvidenceContractError):
        compiler.compile_cycle007_package(package, client, tmp_path / "sidecars", fixture=True)


def test_compile_cycle007_package_real_mode_requires_the_exact_denominator(tmp_path: Path):
    source = _write_cycle005_fixture(tmp_path)
    package = tmp_path / "cycle007-package"
    materializer.materialize(source, package, fixture=True)
    client = SyntheticSourcesClient()
    with pytest.raises(contract.EvidenceContractError):
        compiler.compile_cycle007_package(package, client, tmp_path / "sidecars", fixture=False)


def test_retrieval_payloads_are_deduplicated_across_phenomenon_scoped_records(tmp_path: Path):
    client = SyntheticSourcesClient()
    packets = [[_row("unit-1", text="Проста фраза")]]
    output_dir = tmp_path / "sidecars"
    compiler.compile_sidecar_bundle(packets, client, output_dir, residual_lane_packets=[True])
    sidecar = json.loads((output_dir / "sidecar-0001.json").read_text())
    payload_table = sidecar["retrieval_payloads"]
    row_evidence = sidecar["rows"][0]
    referenced_hashes = {record["retrieval_sha256"] for record in row_evidence["evidence"]}
    assert referenced_hashes <= set(payload_table)
    # 23 phenomena bind the same heritage/style/etc. retrieval facts; the
    # payload table stores each distinct retrieval fact once.
    assert len(payload_table) < len(row_evidence["evidence"])
