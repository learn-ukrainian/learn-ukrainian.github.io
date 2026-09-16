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
    is_target_condemned_in_text,
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
    dpo = tmp_path / "dpo"
    dpo.mkdir()
    (dpo / "shard.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="SFT directory does not exist"):
        run_pretraining_audit(sft_dir=fake_sft, dpo_dir=dpo)


def test_audit_fails_on_empty_sft_dir(tmp_path: Path) -> None:
    """Audit must fail closed with ValueError if SFT dir has zero jsonl files (Fable Finding 1)."""
    empty_sft = tmp_path / "empty_sft"
    empty_sft.mkdir()
    dpo = tmp_path / "dpo"
    dpo.mkdir()
    (dpo / "shard.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="No SFT shards found"):
        run_pretraining_audit(sft_dir=empty_sft, dpo_dir=dpo)



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


def test_audit_dpo_astra_r4_probes(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Verify Astra R4 Findings 1 & 2: scoped defenses and binding replacement directives to target."""
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

    # Finding 1 probe 1: «файний» є діалектним і неправильним словом -> MUST fail audit with 1 contradiction
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Чи правильне слово «файний»?",
            "chosen": "«файний» є діалектним і неправильним словом.",
            "rejected": "«файний» це нормативне слово.",
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

    # Finding 1 probe 2: «файний» — не калька але помилка -> MUST fail audit with 1 contradiction
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Чи є слово «файний» калькою?",
            "chosen": "«файний» — не калька але помилка.",
            "rejected": "«файний» це нормативне слово.",
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

    # Finding 2 probe: «файний» слід зберегти. «общий» слід замінити на «спільний». -> MUST PASS audit (0 contradictions against файний)
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слова «файний» та «общий»?",
            "chosen": "«файний» слід зберегти. «общий» слід замінити на «спільний».",
            "rejected": "Обидва слова слід замінити.",
            "metadata": {"target_term": "файний", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed3, data3, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "report3.md",
        output_json=tmp_path / "report3.json",
    )
    assert passed3 is True
    assert data3["dpo_contradictions_count"] == 0


def test_audit_dpo_astra_r5_probes(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Verify Astra R5 Findings 1, 2, & 3: per-directive negation, coordinate clause subject scoping, and modal negation."""
    mock_sources, mock_vesum = mock_dbs
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "eval_id": "mock_prot_1",
            "stratum": "regional_dialect",
            "target_term": "файний",
            "expected_action": "PRESERVE",
        }) + "\n" +
        json.dumps({
            "eval_id": "mock_prot_2",
            "stratum": "regional_dialect",
            "target_term": "царинками",
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

    # Finding 1 probe: «файний» не слід замінювати але слід уникати -> MUST fail audit with 1 contradiction
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Чи слід уникати «файний»?",
            "chosen": "«файний» не слід замінювати але слід уникати.",
            "rejected": "«файний» це красиве слово.",
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
        min_cases=2,
        output_md=tmp_path / "report1.md",
        output_json=tmp_path / "report1.json",
    )
    assert passed1 is False
    assert data1["dpo_contradictions_count"] == 1
    assert data1["dpo_contradictions"][0]["target_term"] == "файний"

    # Finding 2 probe: «царинками» слід зберегти та «общий» слід замінити на «спільний». -> MUST PASS audit
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Чи слід зберегти «царинками»?",
            "chosen": "«царинками» слід зберегти та «общий» слід замінити на «спільний».",
            "rejected": "Обидва слова слід замінити.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
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
        min_cases=2,
        output_md=tmp_path / "report2.md",
        output_json=tmp_path / "report2.json",
    )
    assert passed2 is True
    assert data2["dpo_contradictions_count"] == 0

    # Finding 3 probe: «царинками» не є помилкою. Його не слід вважати помилкою. -> MUST PASS audit
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Чи є «царинками» помилкою?",
            "chosen": "«царинками» не є помилкою. Його не слід вважати помилкою.",
            "rejected": "Це помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed3, data3, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=2,
        output_md=tmp_path / "report3.md",
        output_json=tmp_path / "report3.json",
    )
    assert passed3 is True
    assert data3["dpo_contradictions_count"] == 0

    # Probe 4 (Fable recommendation): target is recommended replacement for another word -> MUST PASS audit
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Як виправити слово «нормальний»?",
            "chosen": "«нормальний» слід замінити на «файний».",
            "rejected": "Це нормальне слово.",
            "metadata": {"target_term": "файний", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed4, data4, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=2,
        output_md=tmp_path / "report4.md",
        output_json=tmp_path / "report4.json",
    )
    assert passed4 is True
    assert data4["dpo_contradictions_count"] == 0


def test_audit_dpo_astra_r6_probes(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Verify Astra R6 Findings 2 & 3: modal negation 'не можна замінити' and unquoted coordinate subjects."""
    mock_sources, mock_vesum = mock_dbs
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "eval_id": "mock_prot_1",
            "stratum": "regional_dialect",
            "target_term": "царинками",
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

    # Finding 2 probe: «царинками» не можна замінити -> MUST PASS audit with 0 contradictions
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Чи можна замінити «царинками»?",
            "chosen": "«царинками» не можна замінити.",
            "rejected": "Це нормальне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
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
    assert passed1 is True
    assert data1["dpo_contradictions_count"] == 0

    # Finding 3 probe: «царинками» слід зберегти та общий слід замінити на спільний -> MUST PASS audit (unquoted 'общий')
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слова «царинками» та «общий»?",
            "chosen": "«царинками» слід зберегти та общий слід замінити на спільний.",
            "rejected": "Обидва слова слід замінити.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
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

    # Negative control for modal replacement: «царинками» можна замінити на щось -> MUST FAIL audit with 1 contradiction
    (mock_dpo / "shard1.jsonl").write_text(
        json.dumps({
            "prompt": "Чи можна замінити «царинками»?",
            "chosen": "«царинками» можна замінити на інше слово.",
            "rejected": "Це нормальне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed3, data3, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "report3.md",
        output_json=tmp_path / "report3.json",
    )
    assert passed3 is False
    assert data3["dpo_contradictions_count"] == 1
    assert data3["dpo_contradictions"][0]["target_term"] == "царинками"


def test_audit_dpo_astra_r7_probes(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Verify Astra R7 Finding 1: anaphoric pronoun and noun references ('його', 'це') trigger contradiction audit."""
    # 1. Unit checks on is_target_condemned_in_text
    assert is_target_condemned_in_text("царинками", "«царинками» — діалектна форма. Його слід замінити.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» — діалектна форма. Це є помилкою.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» не є помилкою. Його не слід вважати помилкою.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» слід зберегти та общий слід замінити на спільний.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» не можна замінити.") is False

    # 2. Integration audit runs
    mock_sources, mock_vesum = mock_dbs
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "eval_id": "mock_prot_1",
            "stratum": "regional_dialect",
            "target_term": "царинками",
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
    mock_dpo1 = tmp_path / "dpo1"
    mock_dpo1.mkdir()
    (mock_dpo1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як оцінити слово «царинками»?",
            "chosen": "«царинками» — діалектна форма. Його слід замінити.",
            "rejected": "Це нормальне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed1, data1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r7_rep1.md",
        output_json=tmp_path / "r7_rep1.json",
    )
    assert passed1 is False
    assert data1["dpo_contradictions_count"] == 1
    assert data1["dpo_contradictions"][0]["target_term"] == "царинками"

    mock_dpo2 = tmp_path / "dpo2"
    mock_dpo2.mkdir()
    (mock_dpo2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як оцінити слово «царинками»?",
            "chosen": "«царинками» — діалектна форма. Це є помилкою.",
            "rejected": "Це нормальне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed2, data2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r7_rep2.md",
        output_json=tmp_path / "r7_rep2.json",
    )
    assert passed2 is False
    assert data2["dpo_contradictions_count"] == 1
    assert data2["dpo_contradictions"][0]["target_term"] == "царинками"


def test_audit_dpo_astra_r8_probes(tmp_path: Path, mock_dbs: tuple[Path, Path]) -> None:
    """Verify Astra R8 Findings 1 & 2: usage/relative anaphora and correlative negation."""
    # 1. Finding 1: Anaphoric references with usage nouns and relative pronouns trigger condemnation
    assert is_target_condemned_in_text("царинками", "«царинками» — діалектна форма. Його вживання є помилкою.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» — діалектна форма, яку слід замінити.") is True

    # 2. Finding 2: Coordinated correlative negation preserves target without false contradiction
    assert is_target_condemned_in_text("царинками", "«царинками» не є ні помилкою, ні калькою.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» не є ані помилкою, ані калькою.") is False

    # 3. Integration audit runs
    mock_sources, mock_vesum = mock_dbs
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "eval_id": "mock_prot_1",
            "stratum": "regional_dialect",
            "target_term": "царинками",
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

    # Probe 1: «царинками» — діалектна форма. Його вживання є помилкою. -> FAILS audit
    mock_dpo1 = tmp_path / "dpo1"
    mock_dpo1.mkdir()
    (mock_dpo1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як оцінити слово «царинками»?",
            "chosen": "«царинками» — діалектна форма. Його вживання є помилкою.",
            "rejected": "Це нормальне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed1, data1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r8_rep1.md",
        output_json=tmp_path / "r8_rep1.json",
    )
    assert passed1 is False
    assert data1["dpo_contradictions_count"] == 1
    assert data1["dpo_contradictions"][0]["target_term"] == "царинками"

    # Probe 2: «царинками» — діалектна форма, яку слід замінити. -> FAILS audit
    mock_dpo2 = tmp_path / "dpo2"
    mock_dpo2.mkdir()
    (mock_dpo2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як оцінити слово «царинками»?",
            "chosen": "«царинками» — діалектна форма, яку слід замінити.",
            "rejected": "Це нормальне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed2, data2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r8_rep2.md",
        output_json=tmp_path / "r8_rep2.json",
    )
    assert passed2 is False
    assert data2["dpo_contradictions_count"] == 1
    assert data2["dpo_contradictions"][0]["target_term"] == "царинками"

    # Probe 3: «царинками» не є ні помилкою, ні калькою. -> PASSES audit
    mock_dpo3 = tmp_path / "dpo3"
    mock_dpo3.mkdir()
    (mock_dpo3 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як оцінити слово «царинками»?",
            "chosen": "«царинками» не є ні помилкою, ні калькою.",
            "rejected": "Це помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed3, data3, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft,
        dpo_dir=mock_dpo3,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r8_rep3.md",
        output_json=tmp_path / "r8_rep3.json",
    )
    assert passed3 is True
    assert data3["dpo_contradictions_count"] == 0


def test_audit_astra_r9_stress_marks_normalization(
    tmp_path: Path, mock_dbs: tuple[Path, Path]
) -> None:
    """Verify Astra R9 Finding 1: stress marks (combining acute/grave) normalize consistently across SFT, DPO, and text matching."""
    mock_sources, mock_vesum = mock_dbs

    # 1. Direct function checks: combining acute U+0301 on target or text
    assert is_target_condemned_in_text("царинка́ми", "«царинка́ми» є помилкою.") is True
    assert is_target_condemned_in_text("царинками", "«царинка́ми» є помилкою.") is True
    assert is_target_condemned_in_text("царинка́ми", "«царинками» є помилкою.") is True
    assert is_target_condemned_in_text("царинка́ми", "«царинка́ми» не є помилкою.") is False
    assert is_target_condemned_in_text("царинками", "«царинка́ми» не є помилкою.") is False

    # 2. SFT shard with stress marks on target_term matches un-accented protection suite
    mock_prot = tmp_path / "prot_unaccented.jsonl"
    mock_prot.write_text(
        json.dumps({
            "eval_id": "p_r9_1",
            "stratum": "regional_dialect",
            "target_term": "царинками",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sft1 = tmp_path / "sft1"
    mock_sft1.mkdir()
    (mock_sft1 / "shard.jsonl").write_text(
        json.dumps({
            "target_term": "царинка́ми",
            "is_calque_or_russianism": True,
            "action": "CORRECT",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo_empty = tmp_path / "dpo_empty"
    mock_dpo_empty.mkdir()
    (mock_dpo_empty / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як оцінити слово «безпечний»?",
            "chosen": "Це нормативне слово.",
            "rejected": "Це помилка.",
            "metadata": {"target_term": "безпечний", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed1, data1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft1,
        dpo_dir=mock_dpo_empty,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r9_rep1.md",
        output_json=tmp_path / "r9_rep1.json",
    )
    assert passed1 is False
    assert data1["sft_contradictions_count"] == 1
    assert data1["sft_contradictions"][0]["target_term"] == "царинками"

    # 3. DPO shard with stress marks on metadata.target_term and chosen text
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "target_term": "безпечний",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo1 = tmp_path / "dpo1"
    mock_dpo1.mkdir()
    (mock_dpo1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як оцінити слово «царинка́ми»?",
            "chosen": "«царинка́ми» — діалектна форма, яку слід замінити.",
            "rejected": "Це нормальне слово.",
            "metadata": {"target_term": "царинка́ми", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed2, data2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=mock_dpo1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r9_rep2.md",
        output_json=tmp_path / "r9_rep2.json",
    )
    assert passed2 is False
    assert data2["dpo_contradictions_count"] == 1
    assert data2["dpo_contradictions"][0]["target_term"] == "царинками"

    # 4. Reverse: accented protection term matches unaccented SFT shard
    mock_prot_accented = tmp_path / "prot_accented.jsonl"
    mock_prot_accented.write_text(
        json.dumps({
            "eval_id": "p_r9_2",
            "stratum": "regional_dialect",
            "target_term": "царинка́ми",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sft_unaccented = tmp_path / "sft_unaccented"
    mock_sft_unaccented.mkdir()
    (mock_sft_unaccented / "shard.jsonl").write_text(
        json.dumps({
            "target_term": "царинками",
            "is_calque_or_russianism": True,
            "action": "CORRECT",
        }) + "\n",
        encoding="utf-8",
    )
    passed3, data3, _ = run_pretraining_audit(
        protection_path=mock_prot_accented,
        sft_dir=mock_sft_unaccented,
        dpo_dir=mock_dpo_empty,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r9_rep3.md",
        output_json=tmp_path / "r9_rep3.json",
    )
    assert passed3 is False
    assert data3["sft_contradictions_count"] == 1
    assert data3["sft_contradictions"][0]["target_term"] == "царинками"


def test_audit_astra_r11_zamist_replacement_probe(
    tmp_path: Path, mock_dbs: tuple[Path, Path]
) -> None:
    """Verify Astra R11 Finding 2: explicit replacement instructions 'Замість <target> слід вживати <other>' trigger contradictions."""
    mock_sources, mock_vesum = mock_dbs

    # 1. Direct function checks
    assert is_target_condemned_in_text("царинками", "Замість «царинками» слід вживати «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Вживайте «гарний» замість «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Не слід вживати «гарний» замість «царинками».") is False
    assert is_target_condemned_in_text("царинками", "«царинками» — діалектне слово, вживайте його замість «гарний».") is False

    # 2. Integration DPO audit check
    mock_prot = tmp_path / "prot_zamist.jsonl"
    mock_prot.write_text(
        json.dumps({
            "eval_id": "p_r11_zamist",
            "stratum": "regional_dialect",
            "target_term": "царинками",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "target_term": "безпечний",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo_zamist = tmp_path / "dpo_zamist"
    mock_dpo_zamist.mkdir()
    (mock_dpo_zamist / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як оцінити слово «царинками»?",
            "chosen": "Замість «царинками» слід вживати «гарний».",
            "rejected": "Це нормальне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed, data, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=mock_dpo_zamist,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r11_rep.md",
        output_json=tmp_path / "r11_rep.json",
    )
    assert passed is False
    assert data["dpo_contradictions_count"] == 1
    assert data["dpo_contradictions"][0]["target_term"] == "царинками"


def test_audit_astra_r12_zamist_negation_probes(tmp_path: Path):
    """Verify Astra R12 Finding 2: negation scoped to replacement instruction regardless of word order does not falsely condemn preserved targets."""
    # 1. Astra's exact probe: Negation following target preserves term
    assert is_target_condemned_in_text("царинками", "Замість «царинками» не слід вживати «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» не вживайте «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» не варто використовувати «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» не можна вживати «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» заборонено вживати «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» уникайте вживання «гарний».") is False

    # 2. Comma separating prepositional phrase from negated replacement verb
    assert is_target_condemned_in_text("царинками", "Замість «царинками», не слід вживати «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками», не вживайте «гарний».") is False

    # 3. Negation preceding target
    assert is_target_condemned_in_text("царинками", "Не слід вживати «гарний» замість «царинками».") is False
    assert is_target_condemned_in_text("царинками", "Не вживайте «гарний» замість «царинками».") is False

    # 4. Non-negated replacement instructions continue to condemn target
    assert is_target_condemned_in_text("царинками", "Замість «царинками» слід вживати «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «царинками», слід вживати «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Вживайте «гарний» замість «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Замість «царинками» — «гарний».") is True

    # 5. Replacement destination term is never condemned
    assert is_target_condemned_in_text("гарний", "Замість «царинками» не слід вживати «гарний».") is False
    assert is_target_condemned_in_text("гарний", "Замість «царинками» слід вживати «гарний».") is False

    # 6. Full audit pipeline test confirming preservation pair passes audit
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE textbooks (chunk_id TEXT PRIMARY KEY, text TEXT)")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE words (lemma TEXT, form TEXT)")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo_pres = tmp_path / "dpo_pres"
    mock_dpo_pres.mkdir()
    (mock_dpo_pres / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як оцінити слово «царинками»?",
            "chosen": "Замість «царинками» не слід вживати «гарний». Це самобутнє діалектне слово.",
            "rejected": "Це помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed, data, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=mock_dpo_pres,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r12_rep.md",
        output_json=tmp_path / "r12_rep.json",
    )
    assert passed is True
    assert data["dpo_contradictions_count"] == 0
    assert data["dpo_contradictions"] == []


def test_audit_astra_r13_multi_sentence_zamist_probes(tmp_path: Path):
    """Verify Astra R13 Finding 2: earlier negation in one sentence does not hide later replacement instruction in another sentence."""
    # 1. Astra's exact probe: earlier negated sentence does not hide later unnegated replacement instruction
    text1 = "Замість «царинками» не слід вживати «гарний».\nВживайте «добрий» замість «царинками»."
    assert is_target_condemned_in_text("царинками", text1) is True

    # 2. Reversed order: earlier unnegated replacement instruction followed by later negated replacement
    text2 = "Вживайте «добрий» замість «царинками».\nЗамість «царинками» не слід вживати «гарний»."
    assert is_target_condemned_in_text("царинками", text2) is True

    # 3. Both sentences negated: term remains defended and preserved
    text3 = "Замість «царинками» не слід вживати «гарний».\nНе слід вживати «добрий» замість «царинками»."
    assert is_target_condemned_in_text("царинками", text3) is False

    # 4. Integration probe: DPO pair with unnegated replacement following negated replacement fails audit
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE textbooks (chunk_id TEXT PRIMARY KEY, text TEXT)")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE words (lemma TEXT, form TEXT)")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo_contradict = tmp_path / "dpo_contradict"
    mock_dpo_contradict.mkdir()
    (mock_dpo_contradict / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як оцінити слово «царинками»?",
            "chosen": "Замість «царинками» не слід вживати «гарний». Вживайте «добрий» замість «царинками».",
            "rejected": "Це нормальне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed, data, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=mock_dpo_contradict,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r13_rep.md",
        output_json=tmp_path / "r13_rep.json",
    )
    assert passed is False
    assert data["dpo_contradictions_count"] == 1
    assert data["dpo_contradictions"][0]["target_term"] == "царинками"


def test_audit_astra_r14_multi_clause_zamist_probes(tmp_path: Path):
    """Verify Astra R14 Finding 1: negation in another clause does not suppress affirmative replacement instruction for both orders."""
    # 1. Astra's exact reproducer: negation in first clause does not hide affirmative replacement in second clause
    text1 = "Не слід вживати «гарний», але вживайте «добрий» замість «царинками»."
    assert is_target_condemned_in_text("царинками", text1) is True

    # 2. Reversed order: affirmative replacement in first clause is not suppressed by negation in second clause
    text2 = "Вживайте «добрий» замість «царинками», але не слід вживати «гарний»."
    assert is_target_condemned_in_text("царинками", text2) is True

    # 3. Asyndetic coordination (without conjunctions)
    assert is_target_condemned_in_text("царинками", "Не слід вживати «гарний», вживайте «добрий» замість «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Вживайте «добрий» замість «царинками», не слід вживати «гарний».") is True

    # 4. Order 2 with other clauses
    assert is_target_condemned_in_text("царинками", "Замість «царинками» вживайте «добрий», але не слід вживати «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Не слід вживати «гарний», але замість «царинками» вживайте «добрий».") is True

    # 5. Negated replacement remains defended across clauses
    assert is_target_condemned_in_text("царинками", "Не слід вживати «гарний», але замість «царинками» не слід вживати «добрий».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» не слід вживати «гарний», але й «добрий» не слід вживати замість «царинками».") is False

    # 6. Parentheticals with comma
    assert is_target_condemned_in_text("царинками", "Замість «царинками», безумовно, не слід вживати «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками», безумовно, слід вживати «добрий».") is True

    # 7. Full integration audit on Astra R14 reproducer in chosen text
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_dpo_f1 = tmp_path / "dpo_f1"
    mock_dpo_f1.mkdir()
    (mock_dpo_f1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": text1,
            "rejected": "«царинками» — чудове слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed, data, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=mock_dpo_f1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r14_rep.md",
        output_json=tmp_path / "r14_rep.json",
    )
    assert passed is False
    assert data["dpo_contradictions_count"] == 1
    assert data["dpo_contradictions"][0]["target_term"] == "царинками"

    # Also verify reversed reproducer in integration audit
    mock_dpo_f2 = tmp_path / "dpo_f2"
    mock_dpo_f2.mkdir()
    (mock_dpo_f2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": text2,
            "rejected": "«царинками» — чудове слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed2, data2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=mock_dpo_f2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r14_rep2.md",
        output_json=tmp_path / "r14_rep2.json",
    )
    assert passed2 is False
    assert data2["dpo_contradictions_count"] == 1
    assert data2["dpo_contradictions"][0]["target_term"] == "царинками"


def test_audit_astra_r15_probes(tmp_path: Path):
    """Verify Astra R15 Findings: parentheticals with commas and coordinating conjunctions (і, й, та) scoping."""
    # 1. Finding 1: parenthetical commas do not discard the governing directive
    assert is_target_condemned_in_text("царинками", "Вживайте, безумовно, «добрий» замість «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Вживайте, будь ласка, «добрий» замість «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Не вживайте, безумовно, «добрий» замість «царинками».") is False

    # 2. Finding 2: coordinated directives with і / та / й do not leak negation across clauses
    assert is_target_condemned_in_text("царинками", "Не вживайте «гарний» і вживайте «добрий» замість «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Вживайте «добрий» замість «царинками» і не вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Не вживайте «гарний» та вживайте «добрий» замість «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Вживайте «добрий» замість «царинками» й не вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Не вживайте «гарний» і не вживайте «добрий» замість «царинками».") is False

    # 3. Integration tests on all three Astra R15 reproducers
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    reproducers = [
        "Вживайте, безумовно, «добрий» замість «царинками».",
        "Не вживайте «гарний» і вживайте «добрий» замість «царинками».",
        "Вживайте «добрий» замість «царинками» і не вживайте «гарний».",
    ]

    for idx, repro_text in enumerate(reproducers, 1):
        dpo_dir = tmp_path / f"dpo_r15_{idx}"
        dpo_dir.mkdir()
        (dpo_dir / "shard.jsonl").write_text(
            json.dumps({
                "prompt": "Як вживати слово «царинками»?",
                "chosen": repro_text,
                "rejected": "«царинками» — чудове слово.",
                "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
            }) + "\n",
            encoding="utf-8",
        )
        passed, data, _ = run_pretraining_audit(
            protection_path=mock_prot,
            sft_dir=mock_sft_clean,
            dpo_dir=dpo_dir,
            sources_db_path=mock_sources,
            vesum_db_path=mock_vesum,
            min_sft_records=1,
            min_dpo_pairs=1,
            min_cases=1,
            output_md=tmp_path / f"r15_rep_{idx}.md",
            output_json=tmp_path / f"r15_rep_{idx}.json",
        )
        assert passed is False, f"Expected audit failure for: {repro_text}"
        assert data["dpo_contradictions_count"] == 1
        assert data["dpo_contradictions"][0]["target_term"] == "царинками"


def test_audit_astra_r16_probes(tmp_path: Path):
    """Verify Astra R16 Findings: coordinated replacement words and parenthetical modal negation."""
    # 1. Finding 1: coordinated replacement words do not split the governing directive clause
    assert is_target_condemned_in_text("царинками", "Вживайте «добрий» і «гарний» замість «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Вживайте «добрий» та «гарний» замість «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Не вживайте «добрий» і «гарний» замість «царинками».") is False

    # 2. Finding 2: parenthetical commas do not discard the governing modal negation
    assert is_target_condemned_in_text("царинками", "Не слід, безумовно, вживати «добрий» замість «царинками».") is False
    assert is_target_condemned_in_text("царинками", "Не варто, безперечно, використовувати «добрий» замість «царинками».") is False
    assert is_target_condemned_in_text("царинками", "Слід, безумовно, вживати «добрий» замість «царинками».") is True

    # 3. Integration tests on Astra R16 reproducers
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # Finding 1 reproducers: coordinated words in replacement instruction should trigger contradiction
    f1_reproducers = [
        "Вживайте «добрий» і «гарний» замість «царинками».",
        "Вживайте «добрий» та «гарний» замість «царинками».",
    ]
    for idx, repro_text in enumerate(f1_reproducers, 1):
        dpo_dir = tmp_path / f"dpo_r16_f1_{idx}"
        dpo_dir.mkdir()
        (dpo_dir / "shard.jsonl").write_text(
            json.dumps({
                "prompt": "Як вживати слово «царинками»?",
                "chosen": repro_text,
                "rejected": "«царинками» — чудове слово.",
                "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
            }) + "\n",
            encoding="utf-8",
        )
        passed, data, _ = run_pretraining_audit(
            protection_path=mock_prot,
            sft_dir=mock_sft_clean,
            dpo_dir=dpo_dir,
            sources_db_path=mock_sources,
            vesum_db_path=mock_vesum,
            min_sft_records=1,
            min_dpo_pairs=1,
            min_cases=1,
            output_md=tmp_path / f"r16_f1_rep_{idx}.md",
            output_json=tmp_path / f"r16_f1_rep_{idx}.json",
        )
        assert passed is False, f"Expected audit failure for: {repro_text}"
        assert data["dpo_contradictions_count"] == 1
        assert data["dpo_contradictions"][0]["target_term"] == "царинками"

    # Finding 2 reproducer: modal negation with parenthetical commas should NOT trigger contradiction
    dpo_f2 = tmp_path / "dpo_r16_f2"
    dpo_f2.mkdir()
    (dpo_f2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Не слід, безумовно, вживати «добрий» замість «царинками».",
            "rejected": "«царинками» — помилкове слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2, data_f2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r16_f2_rep.md",
        output_json=tmp_path / "r16_f2_rep.json",
    )
    assert passed_f2 is True, "Expected audit pass for negated modal replacement"
    assert data_f2["dpo_contradictions_count"] == 0


def test_audit_astra_r17_probes(tmp_path: Path):
    """Verify Astra R17 Findings: coordinated infinitives under modal negation and suffix clause bounding."""
    # 1. Finding 1: coordinated infinitives preserve shared modal auxiliary negation
    assert is_target_condemned_in_text("царинками", "Не слід вживати «добрий» і використовувати «гарний» замість «царинками».") is False
    assert is_target_condemned_in_text("царинками", "Не слід вживати «добрий» та використовувати «гарний» замість «царинками».") is False
    assert is_target_condemned_in_text("царинками", "Слід вживати «добрий» і використовувати «гарний» замість «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Слід вживати «добрий» та використовувати «гарний» замість «царинками».") is True

    # 2. Finding 2: suffix directives across clause boundaries do not govern introductory замість <target>
    assert is_target_condemned_in_text("царинками", "Замість «царинками» нічого не пропоную, але вживайте «добрий» в іншому реченні.") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» нічого не пропоную; вживайте «добрий» в іншому реченні.") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» нічого не пропоную, проте вживайте «добрий».") is False

    # 3. Integration tests on Astra R17 reproducers
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # Finding 1 reproducer in DPO: shared modal negation must pass audit
    dpo_f1 = tmp_path / "dpo_r17_f1"
    dpo_f1.mkdir()
    (dpo_f1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Не слід вживати «добрий» і використовувати «гарний» замість «царинками».",
            "rejected": "«царинками» — помилкове слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1, data_f1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r17_f1_rep.md",
        output_json=tmp_path / "r17_f1_rep.json",
    )
    assert passed_f1 is True, "Expected audit pass for coordinated infinitives under modal negation"
    assert data_f1["dpo_contradictions_count"] == 0

    # Finding 2 reproducer in DPO: adversative clause boundary must pass audit
    dpo_f2 = tmp_path / "dpo_r17_f2"
    dpo_f2.mkdir()
    (dpo_f2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Замість «царинками» нічого не пропоную, але вживайте «добрий» в іншому реченні.",
            "rejected": "«царинками» — помилкове слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2, data_f2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r17_f2_rep.md",
        output_json=tmp_path / "r17_f2_rep.json",
    )
    assert passed_f2 is True, "Expected audit pass for directive across adversative boundary"
    assert data_f2["dpo_contradictions_count"] == 0

    # Positive control: affirmative coordinated infinitives must fail audit
    dpo_f1_pos = tmp_path / "dpo_r17_f1_pos"
    dpo_f1_pos.mkdir()
    (dpo_f1_pos / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Слід вживати «добрий» і використовувати «гарний» замість «царинками».",
            "rejected": "«царинками» — чудове слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_pos, data_pos, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1_pos,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r17_pos.md",
        output_json=tmp_path / "r17_pos.json",
    )
    assert passed_pos is False, "Expected audit failure for affirmative replacement"
    assert data_pos["dpo_contradictions_count"] == 1


def test_audit_astra_r18_probes(tmp_path: Path):
    """Verify Astra R18 Findings: coordinated targets and unlisted parentheticals/adverbials."""
    # 1. Finding 1: coordinated targets do not terminate directive search
    assert is_target_condemned_in_text("царинками", "Замість «царинками» і «добрий» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «царинками» та «добрий» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «царинками» й «добрий» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «царинками» і «добрий» не слід вживати «гарний».") is False

    # 2. Finding 2: unlisted parentheticals and introductory adverbial phrases do not terminate directive search
    assert is_target_condemned_in_text("царинками", "Замість «царинками» у цьому реченні, без сумніву, слід вживати «добрий».") is True
    assert is_target_condemned_in_text("царинками", "Замість «царинками» на мою думку, без сумніву, слід вживати «добрий».") is True
    assert is_target_condemned_in_text("царинками", "Замість «царинками» у цьому реченні, без сумніву, не слід вживати «добрий».") is False

    # 3. Integration tests on Astra R18 reproducers in DPO
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.execute("INSERT INTO sum20 VALUES (2, 'гарний');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.execute("INSERT INTO vesum VALUES ('гарний');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # Finding 1 reproducer: coordinated target replacement in chosen MUST fail audit (contradiction detected)
    dpo_f1 = tmp_path / "dpo_r18_f1"
    dpo_f1.mkdir()
    (dpo_f1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Замість «царинками» і «добрий» вживайте «гарний».",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1, data_f1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r18_f1_rep.md",
        output_json=tmp_path / "r18_f1_rep.json",
    )
    assert passed_f1 is False, "Expected audit failure for coordinated target replacement"
    assert data_f1["dpo_contradictions_count"] == 1

    # Finding 2 reproducer: unlisted parenthetical replacement in chosen MUST fail audit (contradiction detected)
    dpo_f2 = tmp_path / "dpo_r18_f2"
    dpo_f2.mkdir()
    (dpo_f2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Замість «царинками» у цьому реченні, без сумніву, слід вживати «добрий».",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2, data_f2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r18_f2_rep.md",
        output_json=tmp_path / "r18_f2_rep.json",
    )
    assert passed_f2 is False, "Expected audit failure for parenthetical replacement"
    assert data_f2["dpo_contradictions_count"] == 1


def test_audit_astra_r19_probes(tmp_path: Path):
    """Verify Astra R19 Findings: coordinated replacement targets in second or later positions."""
    # 1. Finding 1: coordinated targets in second/later positions detected correctly
    assert is_target_condemned_in_text("царинками", "Замість «добрий» і «царинками» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «добрий» та «царинками» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «добрий» й «царинками» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «добрий», «файний» та «царинками» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «добрий», «царинками» і «файний» вживайте «гарний».") is True

    # 2. Item classifiers and collective nouns
    assert is_target_condemned_in_text("царинками", "Замість «добрий» і слова «царинками» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість слів «добрий» і «царинками» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість слова «царинками» вживайте «гарний».") is True

    # 3. Order 1 (directive precedes) with coordinated targets
    assert is_target_condemned_in_text("царинками", "Вживайте «гарний» замість «добрий» і «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Вживайте «гарний» замість слів «добрий» і «царинками».") is True

    # 4. Negated replacement protects target
    assert is_target_condemned_in_text("царинками", "Замість «добрий» і «царинками» не слід вживати «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «добрий» і «царинками» не вживайте «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість слів «добрий» і «царинками» не слід вживати «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Вживайте «добрий» замість «царинками», але не слід вживати «гарний».") is True

    # 5. Em-dash shorthand with coordinated targets
    assert is_target_condemned_in_text("царинками", "Замість «добрий» і «царинками» — «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «царинками» і «добрий» — «гарний».") is True

    # 6. DPO integration test with R19 reproducer
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.execute("INSERT INTO sum20 VALUES (2, 'гарний');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.execute("INSERT INTO vesum VALUES ('гарний');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    dpo_f1 = tmp_path / "dpo_r19_f1"
    dpo_f1.mkdir()
    (dpo_f1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Замість «добрий» і «царинками» вживайте «гарний».",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1, data_f1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r19_f1_rep.md",
        output_json=tmp_path / "r19_f1_rep.json",
    )
    assert passed_f1 is False, "Expected audit failure for coordinated target in second position"
    assert data_f1["dpo_contradictions_count"] == 1


def test_audit_astra_r20_probes(tmp_path: Path):
    """Verify Astra R20 Findings: disjunctive conjunctions (або, чи) and fallback avoidance scan."""
    # 1. Finding 1: Disjunctive coordination with або / чи
    assert is_target_condemned_in_text("царинками", "Замість «добрий» або «царинками» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «добрий» чи «царинками» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «царинками» або «добрий» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «царинками» чи «добрий» вживайте «гарний».") is True
    assert is_target_condemned_in_text("царинками", "Замість «добрий» або «царинками» не слід вживати «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «добрий» чи «царинками» не слід вживати «гарний».") is False

    # 2. Finding 2: Expanded replacement syntax in fallback avoidance scan
    assert is_target_condemned_in_text("царинками", "Замість «добрий» і «царинками» уникайте «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість слова «царинками» уникайте «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» уникайте «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «добрий» або «царинками» уникайте «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «добрий» чи «царинками» уникайте «гарний».") is False

    # 3. Isolated DPO integration tests
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.execute("INSERT INTO sum20 VALUES (2, 'гарний');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.execute("INSERT INTO vesum VALUES ('гарний');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # Finding 1 reproducer: або coordination in chosen MUST fail audit
    dpo_f1_abo = tmp_path / "dpo_r20_f1_abo"
    dpo_f1_abo.mkdir()
    (dpo_f1_abo / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Замість «добрий» або «царинками» вживайте «гарний».",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1_abo, data_f1_abo, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1_abo,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r20_f1_abo.md",
        output_json=tmp_path / "r20_f1_abo.json",
    )
    assert passed_f1_abo is False, "Expected audit failure for або coordinated replacement"
    assert data_f1_abo["dpo_contradictions_count"] == 1

    # Finding 1 reproducer: чи coordination in chosen MUST fail audit
    dpo_f1_chy = tmp_path / "dpo_r20_f1_chy"
    dpo_f1_chy.mkdir()
    (dpo_f1_chy / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Замість «добрий» чи «царинками» вживайте «гарний».",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1_chy, data_f1_chy, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1_chy,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r20_f1_chy.md",
        output_json=tmp_path / "r20_f1_chy.json",
    )
    assert passed_f1_chy is False, "Expected audit failure for чи coordinated replacement"
    assert data_f1_chy["dpo_contradictions_count"] == 1

    # Finding 2 reproducer: avoided other word does NOT condemn protected target
    dpo_f2 = tmp_path / "dpo_r20_f2"
    dpo_f2.mkdir()
    (dpo_f2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Замість «добрий» і «царинками» уникайте «гарний».",
            "rejected": "«царинками» — помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2, data_f2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r20_f2.md",
        output_json=tmp_path / "r20_f2.json",
    )
    assert passed_f2 is True, "Expected audit to pass when avoided word is not protected target"
    assert data_f2["dpo_contradictions_count"] == 0


def test_audit_astra_r21_probes(tmp_path: Path):
    """Verify Astra R21 Findings: quoted subject scoping and comma-separated replacement lists in avoidance scan."""
    # 1. Finding 1: Quoted subject scoping across coordinating conjunctions
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і «общий» потребує заміни.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і «общий» вважається помилкою.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і «общий» замініть на «спільний».") is False

    # 2. Finding 2: Comma-separated replacement lists in avoidance scan
    assert is_target_condemned_in_text("царинками", "Замість «добрий», «царинками» уникайте «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «добрий» і «царинками» уникайте «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість слова «царинками» уникайте «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» уникайте «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «добрий», «царинками» уникайте «гарний». А слово «царинками» є помилкою.") is True

    # 3. Isolated DPO integration tests
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.execute("INSERT INTO sum20 VALUES (2, 'гарний');")
    conn_s.execute("INSERT INTO sum20 VALUES (3, 'общий');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.execute("INSERT INTO vesum VALUES ('гарний');")
    conn_v.execute("INSERT INTO vesum VALUES ('общий');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # Finding 1 reproducer: second clause concerns different term -> MUST pass audit
    dpo_f1 = tmp_path / "dpo_r21_f1"
    dpo_f1.mkdir()
    (dpo_f1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» є нормативним словом і «общий» потребує заміни.",
            "rejected": "«царинками» — помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1, data_f1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r21_f1.md",
        output_json=tmp_path / "r21_f1.json",
    )
    assert passed_f1 is True, "Expected audit to pass when directive governs different term"
    assert data_f1["dpo_contradictions_count"] == 0

    # Finding 2 reproducer: comma-separated list with avoided other word -> MUST pass audit
    dpo_f2 = tmp_path / "dpo_r21_f2"
    dpo_f2.mkdir()
    (dpo_f2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Замість «добрий», «царинками» уникайте «гарний».",
            "rejected": "«царинками» — помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2, data_f2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r21_f2.md",
        output_json=tmp_path / "r21_f2.json",
    )
    assert passed_f2 is True, "Expected audit to pass when avoided word is not protected target in comma-separated list"
    assert data_f2["dpo_contradictions_count"] == 0


def test_audit_astra_r22_probes(tmp_path: Path):
    """Verify Astra R22 Findings: shared avoidance directive across coordinated objects and antecedent preservation in relative clause condemnations."""
    # 1. Finding 1: Shared avoidance directive across coordinated objects (R22-F1)
    assert is_target_condemned_in_text("царинками", "Уникайте «добрий» і «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Уникайте «добрий», «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Уникайте «добрий» і «гарний».") is False
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і «общий» потребує заміни.") is False

    # 2. Finding 2: Antecedent preservation for subsequent condemnation (R22-F2)
    assert is_target_condemned_in_text("царинками", "Не вживайте «добрий» замість «царинками», яке є помилкою.") is True
    assert is_target_condemned_in_text("царинками", "Не вживайте «добрий» замість «царинками».") is False
    assert is_target_condemned_in_text("царинками", "Замість «добрий», «царинками» уникайте «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «добрий», «царинками» уникайте «гарний». А слово «царинками» є помилкою.") is True

    # 3. Isolated DPO integration tests: both reproducers must fail audit
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.execute("INSERT INTO sum20 VALUES (2, 'гарний');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.execute("INSERT INTO vesum VALUES ('гарний');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # Finding 1 reproducer: shared avoidance directive in chosen response -> MUST fail audit
    dpo_f1 = tmp_path / "dpo_r22_f1"
    dpo_f1.mkdir()
    (dpo_f1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Уникайте «добрий» і «царинками».",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1, data_f1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r22_f1.md",
        output_json=tmp_path / "r22_f1.json",
    )
    assert passed_f1 is False, "Expected audit to fail when chosen response condemns protected target via shared avoidance directive"
    assert data_f1["dpo_contradictions_count"] == 1

    # Finding 2 reproducer: antecedent relative clause condemnation in chosen response -> MUST fail audit
    dpo_f2 = tmp_path / "dpo_r22_f2"
    dpo_f2.mkdir()
    (dpo_f2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Не вживайте «добрий» замість «царинками», яке є помилкою.",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2, data_f2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r22_f2.md",
        output_json=tmp_path / "r22_f2.json",
    )
    assert passed_f2 is False, "Expected audit to fail when chosen response condemns protected target via relative clause"
    assert data_f2["dpo_contradictions_count"] == 1


def test_audit_astra_r23_probes(tmp_path: Path):
    """Verify Astra R23 Findings: coordinated avoidance objects with classifiers and dash predicate scoping."""
    # 1. Finding 1: Shared avoidance with classifiers before subsequent objects (R23-F1)
    assert is_target_condemned_in_text("царинками", "Уникайте «добрий» і слова «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Уникайте «добрий», слова «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Уникайте «добрий» і слова «гарний».") is False

    # 2. Finding 2: Dash predicate separates clauses without boundary regex failure (R23-F2)
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і «общий» — помилка.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і общий — помилка.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і «общий» є помилкою.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» — помилка.") is True

    # 3. Isolated DPO integration tests
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.execute("INSERT INTO sum20 VALUES (2, 'гарний');")
    conn_s.execute("INSERT INTO sum20 VALUES (3, 'общий');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.execute("INSERT INTO vesum VALUES ('гарний');")
    conn_v.execute("INSERT INTO vesum VALUES ('общий');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # Finding 1 reproducer: classifier before coordinated target in avoidance -> MUST fail audit
    dpo_f1 = tmp_path / "dpo_r23_f1"
    dpo_f1.mkdir()
    (dpo_f1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Уникайте «добрий» і слова «царинками».",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1, data_f1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r23_f1.md",
        output_json=tmp_path / "r23_f1.json",
    )
    assert passed_f1 is False, "Expected audit to fail when chosen response condemns protected target via classified avoidance list"
    assert data_f1["dpo_contradictions_count"] == 1

    # Finding 2 reproducer: coordinated other word condemned via dash predicate -> MUST pass audit
    dpo_f2 = tmp_path / "dpo_r23_f2"
    dpo_f2.mkdir()
    (dpo_f2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» є нормативним словом і «общий» — помилка.",
            "rejected": "«царинками» — помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2, data_f2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r23_f2.md",
        output_json=tmp_path / "r23_f2.json",
    )
    assert passed_f2 is True, "Expected audit to pass when condemnation after dash belongs to different coordinated subject"
    assert data_f2["dpo_contradictions_count"] == 0


def test_audit_r24_findings_mixed_quoted_unquoted_and_implicit_copulas(tmp_path: Path) -> None:
    """Verify Astra R24 Findings: mixed quoted/unquoted avoidance lists and implicit copulas in coordinated clauses."""
    # 1. Finding 1: Mixed quoted/unquoted avoidance lists (R24-F1)
    assert is_target_condemned_in_text("царинками", "Уникайте «добрий» і царинками.") is True
    assert is_target_condemned_in_text("царинками", "Уникайте «добрий» і слова царинками.") is True
    assert is_target_condemned_in_text("царинками", "Уникайте царинками і «добрий».") is True
    assert is_target_condemned_in_text("царинками", "Уникайте добрий і царинками.") is True
    assert is_target_condemned_in_text("царинками", "Уникайте «добрий» і слова «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Уникайте «добрий» і слова гарний.") is False

    # 2. Finding 2: Implicit copula predicates across coordinated subjects (R24-F2)
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і «общий» помилка.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і общий помилка.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і «общий» — помилка.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і общий — помилка.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» помилка.") is True
    assert is_target_condemned_in_text("царинками", "царинками помилка.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» не помилка.") is False

    # 3. Isolated DPO integration tests
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.execute("INSERT INTO sum20 VALUES (2, 'гарний');")
    conn_s.execute("INSERT INTO sum20 VALUES (3, 'общий');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.execute("INSERT INTO vesum VALUES ('гарний');")
    conn_v.execute("INSERT INTO vesum VALUES ('общий');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # R24-F1: unquoted target in mixed avoidance list -> MUST fail audit
    dpo_f1_a = tmp_path / "dpo_r24_f1_a"
    dpo_f1_a.mkdir()
    (dpo_f1_a / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Уникайте «добрий» і царинками.",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1_a, data_f1_a, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1_a,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r24_f1_a.md",
        output_json=tmp_path / "r24_f1_a.json",
    )
    assert passed_f1_a is False, "Expected audit to fail when chosen response condemns target via unquoted avoidance object"
    assert data_f1_a["dpo_contradictions_count"] == 1

    dpo_f1_b = tmp_path / "dpo_r24_f1_b"
    dpo_f1_b.mkdir()
    (dpo_f1_b / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Уникайте «добрий» і слова царинками.",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1_b, data_f1_b, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1_b,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r24_f1_b.md",
        output_json=tmp_path / "r24_f1_b.json",
    )
    assert passed_f1_b is False, "Expected audit to fail when chosen response condemns target via classified unquoted avoidance"
    assert data_f1_b["dpo_contradictions_count"] == 1

    # R24-F2: implicit copula on other coordinated subject -> MUST pass audit
    dpo_f2_a = tmp_path / "dpo_r24_f2_a"
    dpo_f2_a.mkdir()
    (dpo_f2_a / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» є нормативним словом і «общий» помилка.",
            "rejected": "«царинками» — помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2_a, data_f2_a, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2_a,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r24_f2_a.md",
        output_json=tmp_path / "r24_f2_a.json",
    )
    assert passed_f2_a is True, "Expected audit to pass when quoted other subject with implicit copula is condemned"
    assert data_f2_a["dpo_contradictions_count"] == 0

    dpo_f2_b = tmp_path / "dpo_r24_f2_b"
    dpo_f2_b.mkdir()
    (dpo_f2_b / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» є нормативним словом і общий помилка.",
            "rejected": "«царинками» — помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2_b, data_f2_b, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2_b,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r24_f2_b.md",
        output_json=tmp_path / "r24_f2_b.json",
    )
    assert passed_f2_b is True, "Expected audit to pass when unquoted other subject with implicit copula is condemned"
    assert data_f2_b["dpo_contradictions_count"] == 0


def test_audit_r25_findings_replacement_complements_and_imperatives(tmp_path: Path) -> None:
    """Verify Astra R25 Findings: instrumental replacement complements and imperative directives with anaphoric objects."""
    # 1. Finding 1: Instrumental replacement complements and anaphoric usage nouns (R25-F1)
    assert is_target_condemned_in_text("царинками", "«царинками» слід замінити словом «добрий».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» слід замінити на «добрий».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» варто замінити виразом «добрий».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» потрібно замінити формою «добрий».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Уникайте вживання цього слова.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Уникайте його.") is True

    # 2. Finding 2: Replacement and correction imperatives with pronominal anaphora (R25-F2)
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Замініть це слово.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Виправте це слово.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Замініть його.") is True

    # 3. Negative controls: target as replacement destination or directive governing another term
    assert is_target_condemned_in_text("царинками", "«общий» слід замінити словом «царинками».") is False
    assert is_target_condemned_in_text("царинками", "«царинками» є нормативним словом і «общий» слід замінити словом «добрий».") is False
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Замініть слово «общий».") is False

    # 4. Isolated DPO integration tests
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.execute("INSERT INTO sum20 VALUES (2, 'гарний');")
    conn_s.execute("INSERT INTO sum20 VALUES (3, 'общий');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.execute("INSERT INTO vesum VALUES ('гарний');")
    conn_v.execute("INSERT INTO vesum VALUES ('общий');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # R25-F1: replacement destination complement in chosen response -> MUST fail audit
    dpo_f1_a = tmp_path / "dpo_r25_f1_a"
    dpo_f1_a.mkdir()
    (dpo_f1_a / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» слід замінити словом «добрий».",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1_a, data_f1_a, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1_a,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r25_f1_a.md",
        output_json=tmp_path / "r25_f1_a.json",
    )
    assert passed_f1_a is False, "Expected audit to fail when chosen condemns target via replacement complement"
    assert data_f1_a["dpo_contradictions_count"] == 1

    # R25-F1: anaphoric usage noun avoidance in chosen response -> MUST fail audit
    dpo_f1_b = tmp_path / "dpo_r25_f1_b"
    dpo_f1_b.mkdir()
    (dpo_f1_b / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» — нормативне слово. Уникайте вживання цього слова.",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1_b, data_f1_b, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1_b,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r25_f1_b.md",
        output_json=tmp_path / "r25_f1_b.json",
    )
    assert passed_f1_b is False, "Expected audit to fail when chosen condemns target via anaphoric usage noun"
    assert data_f1_b["dpo_contradictions_count"] == 1

    # R25-F2: replacement imperative with anaphora in chosen response -> MUST fail audit
    dpo_f2 = tmp_path / "dpo_r25_f2"
    dpo_f2.mkdir()
    (dpo_f2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» — нормативне слово. Замініть це слово.",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2, data_f2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r25_f2.md",
        output_json=tmp_path / "r25_f2.json",
    )
    assert passed_f2 is False, "Expected audit to fail when chosen condemns target via replacement imperative"
    assert data_f2["dpo_contradictions_count"] == 1

    # Negative control: target is destination in replacement complement -> MUST pass audit
    dpo_ctrl = tmp_path / "dpo_r25_ctrl"
    dpo_ctrl.mkdir()
    (dpo_ctrl / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«общий» слід замінити словом «царинками».",
            "rejected": "«царинками» — помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_ctrl, data_ctrl, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_ctrl,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r25_ctrl.md",
        output_json=tmp_path / "r25_ctrl.json",
    )
    assert passed_ctrl is True, "Expected audit to pass when target is destination in replacement complement"
    assert data_ctrl["dpo_contradictions_count"] == 0


def test_audit_r26_findings_imperfectives_adjuncts_and_focusing_particles(tmp_path: Path) -> None:
    """Verify Astra R26 Findings: imperfective imperatives, scoped anaphora vs adjuncts, and focusing particles."""
    # 1. Finding 1: Imperfective imperatives замінюйте and виправляйте (R26-F1)
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Замінюйте це слово.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Виправляйте це слово.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Замінюйте його.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Виправляйте його.") is True

    # 2. Finding 2: Scoped anaphora vs prepositional adjuncts containing pronouns (R26-F2)
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Уникайте слова общий у цьому реченні.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Уникайте слова «общий» у цьому реченні.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Замініть слово общий у цьому тексті.") is False

    # 3. Finding 3: Focusing particles before replacement destination complement (R26-F3)
    assert is_target_condemned_in_text("царинками", "«царинками» слід замінити саме словом «добрий».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» слід замінити лише словом «добрий».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» слід замінити тільки словом «добрий».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» слід замінити саме на «добрий».") is True

    # 4. Isolated DPO integration tests
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.execute("INSERT INTO sum20 VALUES (2, 'гарний');")
    conn_s.execute("INSERT INTO sum20 VALUES (3, 'общий');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.execute("INSERT INTO vesum VALUES ('гарний');")
    conn_v.execute("INSERT INTO vesum VALUES ('общий');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # R26-F1: imperfective imperative замінюйте in chosen response -> MUST fail audit
    dpo_f1 = tmp_path / "dpo_r26_f1"
    dpo_f1.mkdir()
    (dpo_f1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» — нормативне слово. Замінюйте це слово.",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1, data_f1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r26_f1.md",
        output_json=tmp_path / "r26_f1.json",
    )
    assert passed_f1 is False, "Expected audit to fail when chosen response condemns target via imperfective imperative"
    assert data_f1["dpo_contradictions_count"] == 1

    # R26-F2: other unquoted object with prepositional adjunct containing pronoun -> MUST pass audit
    dpo_f2 = tmp_path / "dpo_r26_f2"
    dpo_f2.mkdir()
    (dpo_f2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» — нормативне слово. Уникайте слова общий у цьому реченні.",
            "rejected": "«царинками» — помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2, data_f2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r26_f2.md",
        output_json=tmp_path / "r26_f2.json",
    )
    assert passed_f2 is True, "Expected audit to pass when other unquoted word is avoided despite pronoun in adjunct"
    assert data_f2["dpo_contradictions_count"] == 0

    # R26-F3: focusing particle before replacement destination complement -> MUST fail audit
    dpo_f3 = tmp_path / "dpo_r26_f3"
    dpo_f3.mkdir()
    (dpo_f3 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» слід замінити саме словом «добрий».",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f3, data_f3, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f3,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r26_f3.md",
        output_json=tmp_path / "r26_f3.json",
    )
    assert passed_f3 is False, "Expected audit to fail when chosen response condemns target with focusing particle"
    assert data_f3["dpo_contradictions_count"] == 1


def test_audit_r27_findings_adjunct_placement_and_usage_prohibitions(tmp_path: Path):
    """Verify Astra R27 Findings: prepositional adjunct preceding non-target object and explicit usage prohibitions."""
    # 1. Finding 1 (R27-F1): Prepositional adjunct preceding non-target object
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Уникайте в цьому реченні слова общий.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Уникайте в цьому контексті слова общий.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Уникайте на письмі слова общий.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Уникайте тут слова общий.") is False

    # Contrastive: when target IS the object following the prepositional adjunct
    assert is_target_condemned_in_text("царинками", "«царинками» — помилкове слово. Уникайте в цьому реченні «царинками».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» — помилкове слово. Уникайте в цьому реченні слова «царинками».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» — помилкове слово. Уникайте в цьому реченні його.") is True

    # 2. Finding 2 (R27-F2): Explicit usage prohibitions
    # Astra's exact probes
    assert is_target_condemned_in_text("царинками", "Не вживайте «царинками».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» заборонено вживати.") is True

    # Extended finite and modal usage prohibitions
    assert is_target_condemned_in_text("царинками", "Не використовуйте «царинками».") is True
    assert is_target_condemned_in_text("царинками", "Не пишіть «царинками».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» забороняється використовувати.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» не слід вживати.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» не варто вживати.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» не можна вживати.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» вживати заборонено.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» вживати не слід.") is True

    # Prohibitions governing other non-target objects do not condemn target
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Не вживайте в цьому реченні слова общий.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» слід зберегти. Не вживайте «общий».") is False

    # Positive usage recommendations do not condemn target
    assert is_target_condemned_in_text("царинками", "«царинками» слід вживати.") is False
    assert is_target_condemned_in_text("царинками", "Вживайте «царинками».") is False

    # Replacement prohibitions defend target
    assert is_target_condemned_in_text("царинками", "«царинками» заборонено замінювати.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» не слід замінювати.") is False

    # 3. Isolated DPO integration tests
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.execute("INSERT INTO sum20 VALUES (2, 'гарний');")
    conn_s.execute("INSERT INTO sum20 VALUES (3, 'общий');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.execute("INSERT INTO vesum VALUES ('гарний');")
    conn_v.execute("INSERT INTO vesum VALUES ('общий');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # R27-F1: Intervening prepositional adjunct before other unquoted object -> MUST pass audit
    dpo_f1 = tmp_path / "dpo_r27_f1"
    dpo_f1.mkdir()
    (dpo_f1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» — нормативне слово. Уникайте в цьому реченні слова общий.",
            "rejected": "«царинками» — помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1, data_f1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r27_f1.md",
        output_json=tmp_path / "r27_f1.json",
    )
    assert passed_f1 is True, "Expected audit pass when adjunct precedes non-target object"
    assert data_f1["dpo_contradictions_count"] == 0

    # R27-F2 probe 1: Explicit usage prohibition in chosen -> MUST fail audit
    dpo_f2_1 = tmp_path / "dpo_r27_f2_1"
    dpo_f2_1.mkdir()
    (dpo_f2_1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Не вживайте «царинками».",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2_1, data_f2_1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2_1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r27_f2_1.md",
        output_json=tmp_path / "r27_f2_1.json",
    )
    assert passed_f2_1 is False, "Expected audit to fail when chosen response explicitly prohibits target via 'Не вживайте'"
    assert data_f2_1["dpo_contradictions_count"] == 1

    # R27-F2 probe 2: Explicit usage prohibition via 'заборонено вживати' -> MUST fail audit
    dpo_f2_2 = tmp_path / "dpo_r27_f2_2"
    dpo_f2_2.mkdir()
    (dpo_f2_2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» заборонено вживати.",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2_2, data_f2_2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2_2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r27_f2_2.md",
        output_json=tmp_path / "r27_f2_2.json",
    )
    assert passed_f2_2 is False, "Expected audit to fail when chosen response explicitly prohibits target via 'заборонено вживати'"
    assert data_f2_2["dpo_contradictions_count"] == 1


def test_audit_r28_findings_zamist_and_trailing_adverbs(tmp_path: Path) -> None:
    """Verify Astra R28 findings:

    1. R28-F1: замість does not grant clause-wide immunity against explicit prohibitions
       governing target.
    2. R28-F2: Trailing adverbs (e.g. взагалі, зовсім, ніколи) are not mistaken for non-target
       direct objects.
    """
    # 1. Finding 1 (R28-F1): замість and substitution direction in explicit prohibitions
    # Astra probe:
    assert is_target_condemned_in_text("царинками", "Не вживайте «царинками» замість «полями».") is True
    # Order variants:
    assert is_target_condemned_in_text("царинками", "Замість «полями» не вживайте «царинками».") is True
    assert is_target_condemned_in_text("царинками", "«царинками» замість «полями» не слід вживати.") is True

    # Controls where target is in замість clause (defended or replaced):
    assert is_target_condemned_in_text("царинками", "Не вживайте «полями» замість «царинками».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» не слід вживати «гарний».") is False
    assert is_target_condemned_in_text("царинками", "Замість «царинками» вживайте «полями».") is True

    # 2. Finding 2 (R28-F2): Trailing adverbs modifying verbs are not objects
    # Astra probe:
    assert is_target_condemned_in_text("царинками", "«царинками» не слід вживати взагалі.") is True
    # Variations across modals and adverbs:
    assert is_target_condemned_in_text("царинками", "«царинками» заборонено вживати взагалі.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» вживати заборонено взагалі.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» не слід вживати зовсім.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» не слід вживати ніколи.") is True
    assert is_target_condemned_in_text("царинками", "«царинками» не слід вживати категорично.") is True
    assert is_target_condemned_in_text("царинками", "Не вживайте «царинками» взагалі.") is True
    assert is_target_condemned_in_text("царинками", "Не слід вживати взагалі «царинками».") is True

    # Prohibitions governing non-target objects with adverbs do NOT condemn target:
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Не вживайте слова общий взагалі.") is False
    assert is_target_condemned_in_text("царинками", "«царинками» — нормативне слово. Не вживайте взагалі слова общий.") is False

    # 3. Isolated DPO integration tests
    mock_prot = tmp_path / "protection.jsonl"
    mock_prot.write_text(
        json.dumps({
            "target_term": "царинками",
            "category": "dialectal",
            "expected_action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )
    mock_sources = tmp_path / "sources.db"
    conn_s = sqlite3.connect(mock_sources)
    conn_s.execute("CREATE TABLE sum20 (entry_id INTEGER PRIMARY KEY, lemma TEXT);")
    conn_s.execute("INSERT INTO sum20 VALUES (1, 'добрий');")
    conn_s.execute("INSERT INTO sum20 VALUES (2, 'гарний');")
    conn_s.execute("INSERT INTO sum20 VALUES (3, 'общий');")
    conn_s.commit()
    conn_s.close()
    mock_vesum = tmp_path / "vesum.db"
    conn_v = sqlite3.connect(mock_vesum)
    conn_v.execute("CREATE TABLE vesum (lemma TEXT);")
    conn_v.execute("INSERT INTO vesum VALUES ('добрий');")
    conn_v.execute("INSERT INTO vesum VALUES ('гарний');")
    conn_v.execute("INSERT INTO vesum VALUES ('общий');")
    conn_v.commit()
    conn_v.close()
    mock_sft_clean = tmp_path / "sft_clean"
    mock_sft_clean.mkdir()
    (mock_sft_clean / "shard.jsonl").write_text(
        json.dumps({
            "instruction": "Поясніть вживання слова «царинками».",
            "response": "«царинками» — автентичне діалектне слово, яке слід зберегти.",
            "target_term": "царинками",
            "is_calque_or_russianism": False,
            "action": "PRESERVE",
        }) + "\n",
        encoding="utf-8",
    )

    # R28-F1 probe: Explicit prohibition in chosen with замість -> MUST fail audit
    dpo_f1 = tmp_path / "dpo_r28_f1"
    dpo_f1.mkdir()
    (dpo_f1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Не вживайте «царинками» замість «полями».",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f1, data_f1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r28_f1.md",
        output_json=tmp_path / "r28_f1.json",
    )
    assert passed_f1 is False, "Expected audit to fail when chosen prohibits target in 'Не вживайте <target> замість <other>'"
    assert data_f1["dpo_contradictions_count"] == 1

    # R28-F2 probe: Explicit prohibition in chosen with trailing adverb -> MUST fail audit
    dpo_f2 = tmp_path / "dpo_r28_f2"
    dpo_f2.mkdir()
    (dpo_f2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» не слід вживати взагалі.",
            "rejected": "«царинками» — нормативне слово.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_f2, data_f2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_f2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r28_f2.md",
        output_json=tmp_path / "r28_f2.json",
    )
    assert passed_f2 is False, "Expected audit to fail when chosen prohibits target with trailing adverb 'взагалі'"
    assert data_f2["dpo_contradictions_count"] == 1

    # Preservation control 1: Target defended in замість clause -> MUST pass audit
    dpo_ctrl1 = tmp_path / "dpo_r28_ctrl1"
    dpo_ctrl1.mkdir()
    (dpo_ctrl1 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "Не вживайте «полями» замість «царинками».",
            "rejected": "«царинками» — помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_ctrl1, data_ctrl1, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_ctrl1,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r28_ctrl1.md",
        output_json=tmp_path / "r28_ctrl1.json",
    )
    assert passed_ctrl1 is True, "Expected audit pass when target is preserved in замість frame"
    assert data_ctrl1["dpo_contradictions_count"] == 0

    # Preservation control 2: Non-target object prohibited with trailing adverb -> MUST pass audit
    dpo_ctrl2 = tmp_path / "dpo_r28_ctrl2"
    dpo_ctrl2.mkdir()
    (dpo_ctrl2 / "shard.jsonl").write_text(
        json.dumps({
            "prompt": "Як вживати слово «царинками»?",
            "chosen": "«царинками» — нормативне слово. Не вживайте слова общий взагалі.",
            "rejected": "«царинками» — помилка.",
            "metadata": {"target_term": "царинками", "pair_type": "anti_hyper_purist_preservation_pairs"},
        }) + "\n",
        encoding="utf-8",
    )
    passed_ctrl2, data_ctrl2, _ = run_pretraining_audit(
        protection_path=mock_prot,
        sft_dir=mock_sft_clean,
        dpo_dir=dpo_ctrl2,
        sources_db_path=mock_sources,
        vesum_db_path=mock_vesum,
        min_sft_records=1,
        min_dpo_pairs=1,
        min_cases=1,
        output_md=tmp_path / "r28_ctrl2.md",
        output_json=tmp_path / "r28_ctrl2.json",
    )
    assert passed_ctrl2 is True, "Expected audit pass when non-target object is prohibited with trailing adverb"
    assert data_ctrl2["dpo_contradictions_count"] == 0
