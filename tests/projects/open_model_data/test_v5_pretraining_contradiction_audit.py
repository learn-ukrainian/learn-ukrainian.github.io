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
