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
            "stratum": "regional_dialect",
            "target_term": "файний",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sft = tmp_path / "sft"
    mock_sft.mkdir()
    (mock_sft / "shard1.jsonl").write_text(
        json.dumps({
            "query": "тест",
            "target_term": "невідомий",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "тест",
            "chosen": "нормативний текст",
            "rejected": "ненормативний текст",
            "metadata": {"target_term": "невідомий", "pair_type": "standard"},
        }) + "\n",
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
        min_cases=1,
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
    """Audit must detect when an SFT shard penalizes a protected term (Fable Finding 4 / Astra Finding 1)."""
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
    # SFT shard flags 'файний' with is_calque_or_russianism=True
    mock_sft = tmp_path / "sft"
    mock_sft.mkdir()
    (mock_sft / "shard.jsonl").write_text(
        json.dumps({
            "query": "Це файний день.",
            "target_term": "файний",
            "is_calque_or_russianism": True,
            "action": "CORRECT",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()
    (mock_dpo / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "test",
            "chosen": "безпечний текст",
            "rejected": "небезпечний текст",
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
        min_cases=1,
        output_md=tmp_path / "report.md",
        output_json=tmp_path / "report.json",
    )
    assert passed is False
    assert data["sft_contradictions_count"] == 1
    assert data["sft_contradictions"][0]["target_term"] == "файний"
    assert data["sft_contradictions"][0]["is_calque_or_russianism"] is True


def test_audit_detects_dpo_preference_contradiction(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Audit must detect when a DPO pair condemns a protected dialect term in chosen text (Astra Finding 1)."""
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
    mock_sft = tmp_path / "sft"
    mock_sft.mkdir()
    (mock_sft / "shard.jsonl").write_text(
        json.dumps({
            "query": "Тестовий запит.",
            "target_term": "безпечний",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    # DPO pair has target_term 'файний' but chosen condemns it as an error/calque
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()
    (mock_dpo / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Чи можна казати «файний»?",
            "chosen": "Ні, це помилка і калька, треба гарний.",
            "rejected": "Так, файний це діалектне слово.",
            "metadata": {"target_term": "файний", "pair_type": "anti_hyper_purist_preservation_pairs"},
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
        min_cases=1,
        output_md=tmp_path / "report.md",
        output_json=tmp_path / "report.json",
    )
    assert passed is False
    assert data["dpo_contradictions_count"] == 1
    assert data["dpo_contradictions"][0]["target_term"] == "файний"


def test_audit_fails_on_invalid_preservation_action(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Protection suite must reject non-PRESERVE actions on dialect/historical cases (Astra Finding 2)."""
    mock_sources, mock_vesum = mock_dbs
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "eval_id": "mock_prot_1",
            "stratum": "regional_dialect",
            "target_term": "файний",
            "expected_action": "CORRECT",  # INVALID: dialect cases must be PRESERVE
        }) + "\n",
        encoding="utf-8",
    )
    mock_sft = tmp_path / "sft"
    mock_sft.mkdir()
    (mock_sft / "shard.jsonl").write_text(
        json.dumps({"target_term": "безпечний", "is_calque_or_russianism": False}) + "\n",
        encoding="utf-8",
    )
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()
    (mock_dpo / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "t",
            "chosen": "c",
            "rejected": "r",
            "metadata": {"target_term": "безпечний"},
        }) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Protection suite has non-PRESERVE dialect/historical cases"):
        run_pretraining_audit(
            protection_path=mock_prot,
            sft_dir=mock_sft,
            dpo_dir=mock_dpo,
            sources_db_path=mock_sources,
            vesum_db_path=mock_vesum,
            min_cases=1,
        )


def test_audit_fails_on_sft_schema_missing_fields(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """SFT records lacking required schema fields must raise ValueError (Astra Finding 1)."""
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
    mock_sft = tmp_path / "sft"
    mock_sft.mkdir()
    # Record lacks target_term
    (mock_sft / "shard.jsonl").write_text(
        json.dumps({"query": "тест", "is_calque_or_russianism": False}) + "\n",
        encoding="utf-8",
    )
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()
    (mock_dpo / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "t",
            "chosen": "c",
            "rejected": "r",
            "metadata": {"target_term": "безпечний"},
        }) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="lacks required 'target_term'"):
        run_pretraining_audit(
            protection_path=mock_prot,
            sft_dir=mock_sft,
            dpo_dir=mock_dpo,
            sources_db_path=mock_sources,
            vesum_db_path=mock_vesum,
            min_cases=1,
        )


def test_audit_fails_on_dpo_schema_missing_fields(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """DPO records lacking required schema fields must raise ValueError (Astra Finding 1)."""
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
    mock_sft = tmp_path / "sft"
    mock_sft.mkdir()
    (mock_sft / "shard.jsonl").write_text(
        json.dumps({"target_term": "безпечний", "is_calque_or_russianism": False}) + "\n",
        encoding="utf-8",
    )
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()
    # DPO record lacks chosen and rejected
    (mock_dpo / "shard.jsonl").write_text(
        json.dumps({"prompt": "t", "metadata": {"target_term": "безпечний"}}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="lacks required prompt/chosen/rejected"):
        run_pretraining_audit(
            protection_path=mock_prot,
            sft_dir=mock_sft,
            dpo_dir=mock_dpo,
            sources_db_path=mock_sources,
            vesum_db_path=mock_vesum,
            min_cases=1,
        )


def test_audit_production_data_passes(tmp_path: Path) -> None:
    """Audit over full production data must pass with 0 contradictions and 100% authority attestation (Astra Finding 4)."""
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
        output_md=tmp_path / "report.md",
        output_json=tmp_path / "report.json",
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


def test_audit_dpo_preservation_intent_probes(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Verify Astra R2 Finding 1: validate target-specific preservation/replacement intent, including negation."""
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
    mock_sft = tmp_path / "sft"
    mock_sft.mkdir()
    (mock_sft / "shard.jsonl").write_text(
        json.dumps({
            "target_term": "безпечний",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()

    # Probe 1: Chosen replaces protected target term -> MUST fail audit with 1 contradiction
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Чи нормативне слово «файний»?",
            "chosen": "Слово «файний» слід замінити на літературний відповідник.",
            "rejected": "«файний» це діалектне слово.",
            "metadata": {"target_term": "файний", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed1, data1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "report1.md",
        output_json=tmp_path / "report1.json",
    )
    assert passed1 is False
    assert data1["dpo_contradictions_count"] == 1
    assert data1["dpo_contradictions"][0]["target_term"] == "файний"

    # Probe 2: Chosen defends protected target term with negation -> MUST pass audit with 0 contradictions
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Чи є слово «файний» калькою?",
            "chosen": "«файний» — не калька і не русизм; збережіть це діалектне слово.",
            "rejected": "Слово «файний» треба замінити.",
            "metadata": {"target_term": "файний", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed2, data2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "report2.md",
        output_json=tmp_path / "report2.json",
    )
    assert passed2 is True
    assert data2["dpo_contradictions_count"] == 0


def test_audit_sft_schema_type_and_action_validation(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Verify Astra R2 Finding 2: SFT schema rejects non-boolean flags and invalid action labels."""
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
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()
    (mock_dpo / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "t",
            "chosen": "c",
            "rejected": "r",
            "metadata": {"target_term": "безпечний"},
        }) + "\n",
        encoding="utf-8",
    )

    # Sub-test 1: String boolean "true" must be rejected with ValueError
    mock_sft1 = tmp_path / "sft1"
    mock_sft1.mkdir()
    (mock_sft1 / "shard.jsonl").write_text(
        json.dumps({
            "target_term": "безпечний",
            "is_calque_or_russianism": "true",  # INVALID: string instead of boolean
            "action": "CORRECT",
        }) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="invalid 'is_calque_or_russianism'"):
        run_pretraining_audit(
            protection_path=mock_prot,
            sft_dir=mock_sft1,
            dpo_dir=mock_dpo,
            sources_db_path=mock_sources,
            vesum_db_path=mock_vesum,
            min_cases=1,
        )

    # Sub-test 2: Unrecognized action "INVALID" must be rejected with ValueError
    mock_sft2 = tmp_path / "sft2"
    mock_sft2.mkdir()
    (mock_sft2 / "shard.jsonl").write_text(
        json.dumps({
            "target_term": "безпечний",
            "is_calque_or_russianism": False,
            "action": "INVALID",  # INVALID: recognized are PRESERVE, CORRECT, REPLACE
        }) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unrecognized action"):
        run_pretraining_audit(
            protection_path=mock_prot,
            sft_dir=mock_sft2,
            dpo_dir=mock_dpo,
            sources_db_path=mock_sources,
            vesum_db_path=mock_vesum,
            min_cases=1,
        )


def test_audit_fails_on_insufficient_unique_protected_terms(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Verify Astra R2 Finding 7: audit enforces unique terms floor (>= 250) before shard scanning."""
    mock_sources, mock_vesum = mock_dbs
    mock_prot = tmp_path / "protection.jsonl"
    # Create 600 records with only 1 unique term
    records = [
        json.dumps({
            "eval_id": f"mock_prot_{i}",
            "stratum": "regional_dialect" if i < 300 else ("historical_text" if i < 500 else "anti_surzhyk_control"),
            "target_term": "файний" if i < 500 else "суржик",
            "expected_action": "PRESERVE" if i < 500 else "CORRECT",
            "expected_replacement": "правильне" if i >= 500 else None,
        })
        for i in range(600)
    ]
    mock_prot.write_text("\n".join(records) + "\n", encoding="utf-8")

    mock_sft = tmp_path / "sft"
    mock_sft.mkdir()
    (mock_sft / "shard.jsonl").write_text(
        json.dumps({
            "target_term": "безпечний",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()
    (mock_dpo / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "t",
            "chosen": "c",
            "rejected": "r",
            "metadata": {"target_term": "безпечний"},
        }) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Insufficient unique protected terms"):
        run_pretraining_audit(
            protection_path=mock_prot,
            sft_dir=mock_sft,
            dpo_dir=mock_dpo,
            sources_db_path=mock_sources,
            vesum_db_path=mock_vesum,
            min_cases=600,
        )


def test_audit_dpo_astra_r3_probes(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Verify Astra R3 Findings 1 & 2: nenormatyvnym condemnation and anaphoric replacement directives."""
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
    mock_sft = tmp_path / "sft"
    mock_sft.mkdir()
    (mock_sft / "shard.jsonl").write_text(
        json.dumps({
            "target_term": "безпечний",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo = tmp_path / "dpo"
    mock_dpo.mkdir()

    # Finding 1 probe: «файний» є ненормативним -> MUST fail audit with 1 contradiction
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Чи нормативне слово «файний»?",
            "chosen": "Слово «файний» є ненормативним.",
            "rejected": "«файний» це діалектне слово.",
            "metadata": {"target_term": "файний", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed1, data1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "report1.md",
        output_json=tmp_path / "report1.json",
    )
    assert passed1 is False
    assert data1["dpo_contradictions_count"] == 1
    assert data1["dpo_contradictions"][0]["target_term"] == "файний"

    # Finding 2 probe: Щодо слова «файний»: це діалектне слово. Його слід замінити на «гарний». -> MUST fail audit
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «файний»?",
            "chosen": "Щодо слова «файний»: це діалектне слово. Його слід замінити на «гарний».",
            "rejected": "«файний» це красиве діалектне слово.",
            "metadata": {"target_term": "файний", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed2, data2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "report2.md",
        output_json=tmp_path / "report2.json",
    )
    assert passed2 is False
    assert data2["dpo_contradictions_count"] == 1
    assert data2["dpo_contradictions"][0]["target_term"] == "файний"
