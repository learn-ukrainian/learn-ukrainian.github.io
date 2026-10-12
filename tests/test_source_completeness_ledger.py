"""Tests for the Phase 1 Hashed Source-Completeness Acceptance Ledger (#9401 / #8977)."""

from __future__ import annotations

from scripts.atlas.build_source_completeness_ledger import build_ledger


def test_source_completeness_ledger_structure() -> None:
    """AC-01: Ledger must follow source-completeness-ledger.v1 schema and contain all partitions."""
    ledger = build_ledger()
    assert ledger["schema_version"] == "source-completeness-ledger.v1"
    assert ledger["phase"] == "1. Inventory and complete source data"
    assert 8977 in ledger["parent_issues"]

    partitions = ledger["partitions"]
    assert "verified-complete" in partitions
    assert "missing" in partitions
    assert "quarantined" in partitions
    assert "corrupt" in partitions
    assert "genuinely-absent" in partitions


def test_verified_complete_partition_contains_mandatory_sources() -> None:
    """AC-02: Verified-complete partition contains VESUM, ULIF, SUM-20 staging, and PULS."""
    ledger = build_ledger()
    vc = {s["source_id"]: s for s in ledger["partitions"]["verified-complete"]}

    assert "vesum" in vc
    assert vc["vesum"]["canonical_sha256"] == "53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680"
    assert vc["vesum"]["counts"]["forms_all"] == 6970759

    assert "ulif_checked" in vc
    assert vc["ulif_checked"]["counts"]["entries"] >= 262788

    assert "sum20_slovnyk_staging" in vc
    assert vc["sum20_slovnyk_staging"]["counts"]["articles"] >= 164000

    assert "puls_cefr" in vc
    assert vc["puls_cefr"]["counts"]["total_rows"] == 5939


def test_quarantined_partition_isolates_sum11_and_legacy_ulif() -> None:
    """AC-03: SUM-11 and legacy unverified ULIF must be partitioned as quarantined."""
    ledger = build_ledger()
    quarantined = {s["source_id"]: s for s in ledger["partitions"]["quarantined"]}

    assert "sum11" in quarantined
    assert "Sovietization contrast" in quarantined["sum11"]["restriction"]

    assert "ulif_legacy_unverified" in quarantined
    assert "Legacy parser defects" in quarantined["ulif_legacy_unverified"]["restriction"]


def test_missing_partition_records_sum20_official_gap() -> None:
    """AC-04: Official SUM-20 crawl gap is documented with remediation."""
    ledger = build_ledger()
    missing = {s["source_id"]: s for s in ledger["partitions"]["missing"]}

    assert "sum20_official" in missing
    assert missing["sum20_official"]["gap_reason"] == "crawl_blocked_cloudflare_403"
    assert missing["sum20_official"]["counts"]["articles"] == 100


def test_genuinely_absent_partition_names_field_gaps() -> None:
    """AC-05: Genuinely absent lexical attributes are recorded as named field gaps."""
    ledger = build_ledger()
    ga = {s["named_field"]: s for s in ledger["partitions"]["genuinely-absent"]}

    assert "etymology_unattested" in ga
    assert "cefr_unresolved" in ga
    assert "collocations_unrecorded" in ga
