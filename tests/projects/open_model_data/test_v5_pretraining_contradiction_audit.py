"""Unit tests for Phase 5.5 Pre-training Contradiction Audit (Issue #8054 / Fable R1)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.projects.open_model_data.v5_pretraining_contradiction_audit import (
    DEFAULT_DPO_DIR,
    DEFAULT_PROTECTION_SUITE,
    DEFAULT_SFT_DIR,
    DEFAULT_SOURCES_DB,
    DEFAULT_VESUM_DB,
    resolve_data_path,
    run_pretraining_audit,
    verify_replacement_attestation,
)


@pytest.fixture
def mock_dbs(tmp_path: Path) -> tuple[Path, Path]:
    """Create minimal mock SQLite databases for isolated CI testing."""
    sources_path = tmp_path / "mock_sources.db"
    vesum_path = tmp_path / "mock_vesum.db"

    with sqlite3.connect(sources_path) as conn:
        conn.execute("CREATE TABLE sum20_articles (headword TEXT, normalized_lookup_key TEXT)")
        conn.execute("CREATE TABLE grinchenko (word TEXT)")
        conn.execute("INSERT INTO sum20_articles VALUES ('принаймні', 'принаймні')")
        conn.execute("INSERT INTO grinchenko VALUES ('файний')")

    with sqlite3.connect(vesum_path) as conn:
        conn.execute("CREATE TABLE forms_all (word_form TEXT, lemma TEXT)")
        conn.execute("INSERT INTO forms_all VALUES ('безпечний', 'безпечний')")

    return sources_path, vesum_path


def test_audit_fails_on_missing_sft_dir(tmp_path: Path) -> None:
    """Audit must fail closed with FileNotFoundError if SFT dir does not exist (Fable Finding 1)."""
    fake_sft = tmp_path / "nonexistent_sft"
    with pytest.raises(FileNotFoundError, match="SFT directory does not exist"):
        run_pretraining_audit(sft_dir=fake_sft)


def test_audit_fails_on_empty_sft_dir(tmp_path: Path) -> None:
    """Audit must fail closed with ValueError if SFT dir has zero jsonl files (Fable Finding 1)."""
    empty_sft = tmp_path / "empty_sft"
    empty_sft.mkdir()
    with pytest.raises(ValueError, match="No SFT shards found"):
        run_pretraining_audit(sft_dir=empty_sft)


def test_audit_fails_on_missing_dpo_dir(tmp_path: Path) -> None:
    """Audit must fail closed with FileNotFoundError if DPO dir does not exist (Fable Finding 1)."""
    fake_dpo = tmp_path / "nonexistent_dpo"
    sft = tmp_path / "sft"
    sft.mkdir()
    (sft / "shard.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="DPO directory does not exist"):
        run_pretraining_audit(sft_dir=sft, dpo_dir=fake_dpo)


def test_audit_fails_on_empty_dpo_dir(tmp_path: Path) -> None:
    """Audit must fail closed with ValueError if DPO dir has zero jsonl files (Fable Finding 1)."""
    sft = tmp_path / "sft"
    sft.mkdir()
    (sft / "shard.jsonl").write_text("{}\n", encoding="utf-8")
    empty_dpo = tmp_path / "empty_dpo"
    empty_dpo.mkdir()
    with pytest.raises(ValueError, match="No DPO shards found"):
        run_pretraining_audit(sft_dir=sft, dpo_dir=empty_dpo)


def test_audit_fails_when_below_min_records(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Audit must fail if SFT or DPO shard population falls below expected minimums (Fable Finding 1)."""
    mock_sources, mock_vesum = mock_dbs
    mock_prot = tmp_path / "prot.jsonl"
    mock_prot.write_text(
        json.dumps({
            "eval_id": "p1",
            "stratum": "anti_surzhyk_control",
            "target_term": "тест",
            "replacement": "принаймні",
            "expected_action": "CORRECT",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sft = tmp_path / "sft"
    mock_sft.mkdir()
    (mock_sft / "shard1.jsonl").write_text(
        json.dumps({"input_text": "тест", "target_term": "невідомий", "action": "PRESERVE"}) + "\n",
        encoding="utf-8",
    )
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({"prompt": "тест", "metadata": {"target_term": "невідомий", "pair_type": "standard"}}) + "\n",
        encoding="utf-8",
    )
    out_md = tmp_path / "report.md"
    out_json = tmp_path / "report.json"

    # Require 6000 SFT and 3000 DPO; here we only have 1 record each
    passed, data, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=6000,
        min_dpo_pairs=3000,
        output_md=out_md,
        output_json=out_json,
    )
    assert passed is False
    assert data["sft_records_audited"] == 1
    assert data["dpo_pairs_audited"] == 1


def test_verify_replacement_attestation_real_databases() -> None:
    """Verify linguistic authority lookup against VESUM and sources.db (Fable Finding 2)."""
    sources_p = resolve_data_path(DEFAULT_SOURCES_DB)
    vesum_p = resolve_data_path(DEFAULT_VESUM_DB)
    if not sources_p.exists() or not vesum_p.exists():
        pytest.skip("Local data/sources.db or data/vesum.db not present (CI-normal)")

    with (
        sqlite3.connect(f"file:{sources_p.resolve()}?mode=ro", uri=True) as sources_conn,
        sqlite3.connect(f"file:{vesum_p.resolve()}?mode=ro", uri=True) as vesum_conn,
    ):
        # Attested Ukrainian words/phrases must return True
        assert verify_replacement_attestation("принаймні", vesum_conn, sources_conn) is True
        assert verify_replacement_attestation("брати участь", vesum_conn, sources_conn) is True
        assert verify_replacement_attestation("насамперед", vesum_conn, sources_conn) is True
        # Stress-marked and curly-apostrophe words must normalize cleanly
        assert verify_replacement_attestation("прина́ймні", vesum_conn, sources_conn) is True
        assert verify_replacement_attestation("сім’я́", vesum_conn, sources_conn) is True

        # Fabricated non-existent tokens must return False
        assert verify_replacement_attestation("зорблаксія", vesum_conn, sources_conn) is False
        assert verify_replacement_attestation("вигаданеслово123", vesum_conn, sources_conn) is False


def test_audit_detects_sft_contradiction(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Audit must detect when an SFT shard penalizes a protected term (Fable Finding 4)."""
    mock_sources, mock_vesum = mock_dbs
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "eval_id": "mock_prot_1",
            "stratum": "regional_dialect",
            "target_term": "файний",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    # SFT shard attempts to CORRECT 'файний'
    mock_sft = tmp_path / "sft"
    mock_sft.mkdir()
    (mock_sft / "shard.jsonl").write_text(
        json.dumps({
            "input_text": "Це файний день.",
            "target_term": "файний",
            "action": "CORRECT",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()
    (mock_dpo / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "test",
            "metadata": {"target_term": "безпечний", "pair_type": "standard"},
        }) + "\n",
        encoding="utf-8",
    )

    passed, data, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        output_md=tmp_path / "report.md",
        output_json=tmp_path / "report.json",
    )
    assert passed is False
    assert data["sft_contradictions_count"] == 1
    assert data["sft_contradictions"][0]["target_term"] == "файний"
    assert data["sft_contradictions"][0]["action"] == "CORRECT"


def test_audit_production_data_passes() -> None:
    """Audit over full production data must pass with 0 contradictions and 100% authority attestation."""
    protection_p = resolve_data_path(DEFAULT_PROTECTION_SUITE)
    sft_p = resolve_data_path(DEFAULT_SFT_DIR)
    dpo_p = resolve_data_path(DEFAULT_DPO_DIR)
    sources_p = resolve_data_path(DEFAULT_SOURCES_DB)
    vesum_p = resolve_data_path(DEFAULT_VESUM_DB)

    if (
        not protection_p.exists()
        or not sft_p.exists()
        or not dpo_p.exists()
        or not sources_p.exists()
        or not vesum_p.exists()
    ):
        pytest.skip("Full production datasets or local databases not available in test runner environment (CI-normal)")

    passed, data, _ = run_pretraining_audit(
        protection_path=protection_p,
        sft_dir=sft_p,
        dpo_dir=dpo_p,
        sources_db_path=sources_p,
        vesum_db_path=vesum_p,
        min_sft_records=6000,
        min_dpo_pairs=3000,
    )
    assert passed is True
    assert data["protection_suite_cases"] == 600
    assert data["stratum_counts"]["regional_dialect"] == 300
    assert data["stratum_counts"]["historical_text"] == 200
    assert data["stratum_counts"]["anti_surzhyk_control"] == 100
    assert data["sft_records_audited"] == 6000
    assert data["dpo_pairs_audited"] == 3000
    assert data["sft_contradictions_count"] == 0
    assert data["dpo_contradictions_count"] == 0
    assert data["anti_surzhyk_valid"] is True
    assert len(data["anti_surzhyk_anomalies"]) == 0
