"""Tests for Phase 3.5 Automated CoT Claim-Verifier & Schema Reconciliation (#8009)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import jsonschema
import pytest

from scripts.projects.open_model_data.v4_verify_trajectory_claims import (
    DEFAULT_INPUT_TRAJECTORIES,
    DEFAULT_RECEIPT_OUTPUT,
    DEFAULT_REJECTED_OUTPUT,
    DEFAULT_SOURCES_DB,
    DEFAULT_VERIFIED_OUTPUT,
    DEFAULT_VESUM_DB,
    PRIVATE_HOST_RE,
    RECEIPT_SCHEMA_PATH,
    REPO_ROOT,
    TRAJECTORY_SCHEMA_PATH,
    run_claim_verifier,
)


@pytest.fixture(scope="module")
def trajectory_schema() -> dict:
    assert TRAJECTORY_SCHEMA_PATH.is_file(), f"Missing schema: {TRAJECTORY_SCHEMA_PATH}"
    with TRAJECTORY_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture(scope="module")
def receipt_schema() -> dict:
    assert RECEIPT_SCHEMA_PATH.is_file(), f"Missing schema: {RECEIPT_SCHEMA_PATH}"
    with RECEIPT_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture
def mock_dbs(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create in-memory/isolated SQLite fixtures with test data."""
    vesum_path = tmp_path / "test_vesum.db"
    sources_path = tmp_path / "test_sources.db"
    ulif_path = tmp_path / "test_ulif.db"

    v_conn = sqlite3.connect(vesum_path)
    v_conn.executescript(
        """
        CREATE TABLE forms_all (
            id INTEGER PRIMARY KEY,
            entry_id INTEGER NOT NULL,
            word_form TEXT NOT NULL,
            lemma TEXT NOT NULL,
            pos TEXT NOT NULL,
            tags TEXT NOT NULL,
            source_comment TEXT,
            source_location TEXT NOT NULL
        );
        INSERT INTO forms_all (entry_id, word_form, lemma, pos, tags, source_comment, source_location) VALUES
        (1, 'пилосмок', 'пилосмок', 'noun', 'noun:inanim:m:v_naz', NULL, '1'),
        (1, 'пилосмока', 'пилосмок', 'noun', 'noun:inanim:m:v_rod', NULL, '1'),
        (2, 'дифузія', 'дифузія', 'noun', 'noun:inanim:f:v_naz', NULL, '2'),
        (2, 'дифузії', 'дифузія', 'noun', 'noun:inanim:f:v_rod', NULL, '2'),
        (3, 'перемкнути', 'перемкнути', 'verb', 'verb:perf:inf', 'rv_zna', '3'),
        (3, 'перемкнув', 'перемкнути', 'verb', 'verb:perf:past:m', 'rv_zna', '3');
        """
    )
    v_conn.commit()
    v_conn.close()

    s_conn = sqlite3.connect(sources_path)
    s_conn.executescript(
        """
        CREATE TABLE sum11 (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT '',
            sovietization_risk INTEGER NOT NULL DEFAULT 0,
            sovietization_keywords TEXT NOT NULL DEFAULT ''
        );
        INSERT INTO sum11 (id, word, definition, text, sovietization_risk) VALUES
        (101, 'пилосос', 'Апарат для очищення...', 'Текст про пилосос', 1),
        (102, 'дифузія', 'Фізичне явище...', 'Текст про дифузію', 0);
        """
    )
    s_conn.commit()
    s_conn.close()

    u_conn = sqlite3.connect(ulif_path)
    u_conn.executescript(
        """
        CREATE TABLE ulif_entries (
            lemma TEXT PRIMARY KEY,
            canonical_headword TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL CHECK (status IN ('ok', 'not_found', 'error', 'parse_error')),
            retrieved_at TEXT NOT NULL DEFAULT '',
            paradigm_json TEXT,
            synonyms_json TEXT,
            phraseology_json TEXT,
            antonyms_json TEXT,
            raw_html_json TEXT
        );
        INSERT INTO ulif_entries (lemma, canonical_headword, status) VALUES
        ('пилосмок', 'пилосмо́к', 'ok'),
        ('дифузія', 'дифу́зія', 'ok');
        """
    )
    u_conn.commit()
    u_conn.close()

    return vesum_path, sources_path, ulif_path


def test_seed_trajectories_full_verification_suite(receipt_schema: dict) -> None:
    """Validate that real seed trajectories pass all checks with 100% verification rate."""
    assert DEFAULT_VESUM_DB.is_file(), f"Missing VESUM DB: {DEFAULT_VESUM_DB}"
    assert DEFAULT_SOURCES_DB.is_file(), f"Missing sources DB: {DEFAULT_SOURCES_DB}"

    receipt = run_claim_verifier(
        input_path=DEFAULT_INPUT_TRAJECTORIES,
        verified_output_path=DEFAULT_VERIFIED_OUTPUT,
        rejected_output_path=DEFAULT_REJECTED_OUTPUT,
        receipt_output_path=DEFAULT_RECEIPT_OUTPUT,
        vesum_db=DEFAULT_VESUM_DB,
        sources_db=DEFAULT_SOURCES_DB,
        verify_only=False,
    )

    # Validate receipt against schema
    jsonschema.validate(instance=receipt, schema=receipt_schema)

    assert receipt["counts"]["total_trajectories"] == 3
    assert receipt["counts"]["trajectories_passed"] == 3
    assert receipt["counts"]["trajectories_rejected"] == 0
    assert receipt["counts"]["total_claims_verified"] >= 40
    assert receipt["invariants"]["pass_rate_100_percent"] is True
    assert receipt["invariants"]["zero_unverified_dictionary_claims"] is True
    assert receipt["invariants"]["no_private_host_paths"] is True


def test_verify_only_mode() -> None:
    """Verify that --verify-only succeeds on clean committed outputs."""
    receipt = run_claim_verifier(
        input_path=DEFAULT_INPUT_TRAJECTORIES,
        verified_output_path=DEFAULT_VERIFIED_OUTPUT,
        rejected_output_path=DEFAULT_REJECTED_OUTPUT,
        receipt_output_path=DEFAULT_RECEIPT_OUTPUT,
        vesum_db=DEFAULT_VESUM_DB,
        sources_db=DEFAULT_SOURCES_DB,
        verify_only=True,
    )
    assert receipt["schema_version"] == "v1_cot_claim_verification_receipt"
    assert receipt["invariants"]["pass_rate_100_percent"] is True


def test_verify_only_hash_tamper_fails(tmp_path: Path) -> None:
    """Tampering with verified output file must cause --verify-only to fail-closed."""
    inp = tmp_path / "input.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    inp.write_text(DEFAULT_INPUT_TRAJECTORIES.read_text(encoding="utf-8"), encoding="utf-8")

    run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=DEFAULT_VESUM_DB,
        sources_db=DEFAULT_SOURCES_DB,
        verify_only=False,
    )

    # Tamper with the output file
    out.write_text(out.read_text(encoding="utf-8") + "\n// tampered", encoding="utf-8")

    with pytest.raises(ValueError, match="Hash mismatch"):
        run_claim_verifier(
            input_path=inp,
            verified_output_path=out,
            rejected_output_path=rej,
            receipt_output_path=rcp,
            vesum_db=DEFAULT_VESUM_DB,
            sources_db=DEFAULT_SOURCES_DB,
            verify_only=True,
        )


def test_positive_preserve_negative_control(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Clean STEM PRESERVE control passes with omitted suppression fields."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "preserve_test.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    preserve_rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000001",
        "query": "Що означає фізичний термін «дифузія»?",
        "target_term": "дифузія",
        "is_calque_or_russianism": False,
        "morphemic_breakdown": {
            "source_formation": "Living STEM term with entity type physics_chemistry.",
            "ukrainian_equivalent_mechanism": "No substitution: attested standard term, not a calque.",
        },
        "vesum_attestation": [
            {
                "lemma": "дифузія",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "дифузія",
            "alternatives": [
                {
                    "lemma": "дифузія",
                    "register_tier": "living_standard",
                    "evidence_source": "STEM textbook fizyka",
                }
            ],
        },
        "reasoning_steps": [
            "1. Термін «дифузія» є нормативним фізичним терміном.",
            "2. ВЕСУМ: «дифузія» (2 форми) має повну парадигму.",
        ],
        "final_response": "Термін «дифузія» є нормативним українським терміном.",
    }
    inp.write_text(json.dumps(preserve_rec) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=False,
    )

    assert receipt["counts"]["trajectories_passed"] == 1
    assert receipt["counts"]["trajectories_rejected"] == 0


def test_hard_rejection_fake_vesum_lemma(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Non-existent lemma in vesum_attestation must trigger hard rejection."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "fake_lemma.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000002",
        "query": "Тестове запитання?",
        "target_term": "калька",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "повністю_вигадане_слово_якого_немає",
                "vesum_forms_count": 10,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "повністю_вигадане_слово_якого_немає",
            "alternatives": [
                {
                    "lemma": "повністю_вигадане_слово_якого_немає",
                    "register_tier": "living_standard",
                    "evidence_source": "Вигадане джерело",
                }
            ],
        },
        "reasoning_steps": [
            "1. Пояснення проблеми.",
        ],
        "final_response": "Правильна відповідь для тестування.",
    }
    inp.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=False,
    )

    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert len(rej_data) == 1
    assert any("has 0 forms in vesum.db" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_hard_rejection_vesum_count_mismatch(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Asserting false VESUM form count in reasoning steps triggers hard rejection."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "count_mismatch.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000003",
        "query": "Тестове запитання?",
        "target_term": "пилосос",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "пилосмок",
                "vesum_forms_count": 2,  # Mock DB has 2 forms
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "пилосмок",
            "alternatives": [
                {
                    "lemma": "пилосмок",
                    "register_tier": "living_standard",
                    "evidence_source": "Словник",
                }
            ],
        },
        "reasoning_steps": [
            "1. ВЕСУМ: «пилосмок» (999 форм) має колосальну кількість форм.",  # False claim
        ],
        "final_response": "Правильна відповідь для тестування.",
    }
    inp.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=False,
    )

    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("VESUM form count mismatch" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_hard_rejection_fake_sum11_citation(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Asserting false СУМ-11 headword citation triggers hard rejection."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "fake_sum11.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000004",
        "query": "Тестове запитання?",
        "target_term": "пилосос",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "пилосмок",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "пилосмок",
            "alternatives": [
                {
                    "lemma": "пилосмок",
                    "register_tier": "living_standard",
                    "evidence_source": "Словник",
                }
            ],
        },
        "reasoning_steps": [
            "1. В академічному СУМ-11 прямо зафіксовано гасло «вигаданословонемаєвсум11».",  # Fake headword
        ],
        "final_response": "Правильна відповідь для тестування.",
    }
    inp.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=False,
    )

    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("does not exist in sources.db sum11 table" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_hard_rejection_r2u_network_timeout(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Fail-closed rejection when R2U source is unavailable or timed out."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "r2u_timeout.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    cache_file = tmp_path / "r2u_cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "термін": {
                    "status": "source_unavailable",
                    "translations": [],
                }
            }
        ),
        encoding="utf-8",
    )

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000005",
        "query": "Тестове запитання?",
        "target_term": "термін",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "пилосмок",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "пилосмок",
            "alternatives": [
                {
                    "lemma": "пилосмок",
                    "register_tier": "living_standard",
                    "evidence_source": "Словник",
                }
            ],
        },
        "reasoning_steps": [
            "1. За словниками 1920-х років R2U для «термін» наведено питомі варіанти.",
        ],
        "final_response": "Правильна відповідь для тестування.",
    }
    inp.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        r2u_cache_path=cache_file,
        allow_network=False,
        verify_only=False,
    )

    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("R2U source unavailable" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_hard_rejection_preserve_fabricated_suppression(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """PRESERVE control that fabricates historical Soviet suppression on clean Ukrainian text is rejected."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "fabricated_suppression.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000006",
        "query": "Тестове запитання?",
        "target_term": "дифузія",
        "is_calque_or_russianism": False,
        "morphemic_breakdown": {
            "source_formation": "Living STEM term with entity type physics_chemistry.",
            "ukrainian_equivalent_mechanism": "No substitution: attested standard term, not a calque.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Слово дифузія було репресоване радянськими цензорами та вилучене.",  # Fabricated!
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "дифузія",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "дифузія",
            "alternatives": [
                {
                    "lemma": "дифузія",
                    "register_tier": "living_standard",
                    "evidence_source": "Підручник",
                }
            ],
        },
        "reasoning_steps": [
            "1. Термін «дифузія» є нормативним українським терміном.",
        ],
        "final_response": "Правильна відповідь для тестування.",
    }
    inp.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=False,
    )

    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("falsely claims historical suppression" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_opsec_no_private_host_paths() -> None:
    """Verify that committed verifier artifacts contain no private local machine paths or raw IPs."""
    assert DEFAULT_RECEIPT_OUTPUT.is_file(), f"Missing receipt: {DEFAULT_RECEIPT_OUTPUT}"
    receipt_text = DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8")
    assert not PRIVATE_HOST_RE.search(receipt_text), "Private host path detected in receipt!"

    assert DEFAULT_VERIFIED_OUTPUT.is_file(), f"Missing verified output: {DEFAULT_VERIFIED_OUTPUT}"
    verified_text = DEFAULT_VERIFIED_OUTPUT.read_text(encoding="utf-8")
    assert not PRIVATE_HOST_RE.search(verified_text), "Private host path detected in verified output!"


def test_subprocess_timeout_guard() -> None:
    """All subprocess invocations must specify an explicit timeout= parameter."""
    import ast

    script_path = REPO_ROOT / "scripts" / "projects" / "open_model_data" / "v4_verify_trajectory_claims.py"
    tree = ast.parse(script_path.read_text(encoding="utf-8"))

    checked_calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            is_subp = False
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "subprocess":
                is_subp = True
            if is_subp and func.attr in ("run", "check_output", "call", "check_call"):
                has_timeout = any(kw.arg == "timeout" for kw in node.keywords)
                assert has_timeout, f"Missing explicit timeout= in subprocess.{func.attr} call at line {node.lineno}"
                checked_calls += 1
    assert checked_calls > 0, "Expected at least one subprocess call to check"


def test_hard_rejection_vesum_count_off_by_one(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Off-by-one VESUM form count must fail without tolerance band (Finding 5)."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "off_by_one.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000007",
        "query": "Тестове запитання?",
        "target_term": "пилосос",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "пилосмок",
                "vesum_forms_count": 2,  # Mock DB has exactly 2 forms
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "пилосмок",
            "alternatives": [
                {
                    "lemma": "пилосмок",
                    "register_tier": "living_standard",
                    "evidence_source": "Словник",
                }
            ],
        },
        "reasoning_steps": [
            "1. ВЕСУМ: «пилосмок» (3 форми) має парадигму.",  # Off by exactly +1 (previously passed under +-2)
        ],
        "final_response": "Правильна відповідь для тестування.",
    }
    inp.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=False,
    )

    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("VESUM form count mismatch" in str(r) and "claimed 3, actual 2" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_hard_rejection_r2u_polarity_fabricated_presence(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Claiming 1920s R2U attestation for a term that is absent triggers rejection (Finding 1)."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "r2u_fab_presence.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    cache_file = tmp_path / "r2u_cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "невідоме": {
                    "status": "not_found",
                    "translations": [],
                }
            }
        ),
        encoding="utf-8",
    )

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000008",
        "query": "Тестове запитання?",
        "target_term": "невідоме",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "пилосмок",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "пилосмок",
            "alternatives": [
                {
                    "lemma": "пилосмок",
                    "register_tier": "living_standard",
                    "evidence_source": "Словник",
                }
            ],
        },
        "reasoning_steps": [
            "1. За словниками 1920-х років R2U термін «невідоме» зафіксовано як основний відповідник.",
        ],
        "final_response": "Правильна відповідь для тестування.",
    }
    inp.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        r2u_cache_path=cache_file,
        verify_only=False,
    )

    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("Fabricated 1920s attestation claim" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_hard_rejection_r2u_polarity_fabricated_absence(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Claiming 1920s R2U absence for a term that IS attested triggers rejection (Finding 1)."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "r2u_fab_absence.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    cache_file = tmp_path / "r2u_cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "пилосмок": {
                    "status": "found",
                    "translations": ["пилосмок", "порохотяг"],
                }
            }
        ),
        encoding="utf-8",
    )

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000009",
        "query": "Тестове запитання?",
        "target_term": "пилосос",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "пилосмок",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "пилосмок",
            "alternatives": [
                {
                    "lemma": "пилосмок",
                    "register_tier": "living_standard",
                    "evidence_source": "Словник",
                }
            ],
        },
        "reasoning_steps": [
            "1. У словниках 1920-х років R2U слово «пилосмок» не зафіксовано зовсім.",
        ],
        "final_response": "Правильна відповідь для тестування.",
    }
    inp.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        r2u_cache_path=cache_file,
        verify_only=False,
    )

    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("Fabricated 1920s absence claim" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_hard_rejection_sum11_volume_year_mismatch(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Mismatched СУМ-11 volume alphabetical span or publication year triggers rejection (Findings 2 & 6)."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "sum11_vol_mismatch.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000010",
        "query": "Тестове запитання?",
        "target_term": "перемкнути",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Зафіксовано в СУМ-11 (т. 1, 1970).",  # 'перемкнути' starts with 'п' -> volume 6, not volume 1
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "перемкнути",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "перемкнути",
            "alternatives": [
                {
                    "lemma": "перемкнути",
                    "register_tier": "living_standard",
                    "evidence_source": "Словник",
                }
            ],
        },
        "reasoning_steps": [
            "1. Термін нормативний.",
        ],
        "final_response": "Правильна відповідь для тестування.",
    }
    inp.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=False,
    )

    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("Alphabetical volume mismatch" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_hard_rejection_sum11_stylistic_label_mismatch(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Asserting an ungrounded stylistic label in СУМ-11 triggers rejection (Findings 2 & 6)."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "sum11_style_mismatch.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000011",
        "query": "Тестове запитання?",
        "target_term": "пилосос",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "пилосмок",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "пилосмок",
            "alternatives": [
                {
                    "lemma": "пилосмок",
                    "register_tier": "living_standard",
                    "evidence_source": "Словник",
                }
            ],
        },
        "reasoning_steps": [
            "1. В академічному СУМ-11 «пилосос» подано з ремаркою «діал.» як діалектне.",
        ],
        "final_response": "Правильна відповідь для тестування.",
    }
    inp.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=False,
    )

    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("does not contain claimed stylistic label «діал»" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_hard_rejection_non_living_register_tier_validation(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Non-living register tiers must be attested and have valid evidence_source (Finding 3)."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "reg_tier_unattested.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    # 1. Classical regional term that is completely unattested in VESUM/sources
    rec_unattested = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000012",
        "query": "Тестове запитання?",
        "target_term": "пилосос",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "пилосмок",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "пилосмок",
            "alternatives": [
                {
                    "lemma": "абсолютна_вигадка_немає",
                    "register_tier": "classical_regional",
                    "evidence_source": "Словник Грінченка 1907",
                }
            ],
        },
        "reasoning_steps": ["1. Пояснення."],
        "final_response": "Відповідь.",
    }
    inp.write_text(json.dumps(rec_unattested) + "\n", encoding="utf-8")

    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=False,
    )
    assert receipt["counts"]["trajectories_passed"] == 0
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("is completely unattested in VESUM and sources" in str(r) for r in rej_data[0]["rejection_reasons"])

    # 2. Classical regional term with missing evidence_source
    rec_missing_src = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000013",
        "query": "Тестове запитання?",
        "target_term": "пилосос",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "пилосмок",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "пилосмок",
            "alternatives": [
                {
                    "lemma": "перемкнути",  # Attested in mock DB
                    "register_tier": "classical_regional",
                    "evidence_source": "див.",  # Short/uninformative citation (< 5 chars)
                }
            ],
        },
        "reasoning_steps": ["1. Пояснення."],
        "final_response": "Відповідь.",
    }
    inp.write_text(json.dumps(rec_missing_src) + "\n", encoding="utf-8")
    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=False,
    )
    assert receipt["counts"]["trajectories_passed"] == 0
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("requires non-empty evidence_source citation" in str(r) for r in rej_data[0]["rejection_reasons"])

    # 3. Purist neologism claimed unrecorded (0 forms) but actually attested in VESUM
    rec_purist_conflict = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000015",
        "query": "Тестове запитання?",
        "target_term": "пилосос",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "пилосмок",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "пилосмок",
            "alternatives": [
                {
                    "lemma": "пилосмок",
                    "register_tier": "purist_neologism",
                    "evidence_source": "Сучасні пуристичні пропозиції",
                }
            ],
        },
        "reasoning_steps": ["1. Пояснення."],
        "final_response": "Відповідь.",
    }
    inp.write_text(json.dumps(rec_purist_conflict) + "\n", encoding="utf-8")
    receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=False,
    )
    assert receipt["counts"]["trajectories_passed"] == 0
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("actually has 2 forms in VESUM" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_hard_rejection_opsec_private_host_path_in_trajectory(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Any trajectory containing private host path or IP must trigger OPSEC failure (Finding 4)."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "opsec_violation.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000014",
        "query": "Тестове запитання?",
        "target_term": "пилосос",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "Штучно нав'язано радянською владою.",
            "restoration_era": "Правопис 2019.",
        },
        "vesum_attestation": [
            {
                "lemma": "пилосмок",
                "vesum_forms_count": 2,
                "is_standard_attested": True,
            }
        ],
        "register_spectrum": {
            "primary_living_standard": "пилосмок",
            "alternatives": [
                {
                    "lemma": "пилосмок",
                    "register_tier": "living_standard",
                    "evidence_source": "Словник",
                }
            ],
        },
        "reasoning_steps": [
            "1. За даними з /home/ops/secret_data.txt термін пилосмок підтверджено.",  # OPSEC violation!
        ],
        "final_response": "Правильна відповідь для тестування.",
    }
    inp.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="OPSEC violation: private path detected"):
        run_claim_verifier(
            input_path=inp,
            verified_output_path=out,
            rejected_output_path=rej,
            receipt_output_path=rcp,
            vesum_db=vesum,
            sources_db=sources,
            ulif_db=ulif,
            verify_only=False,
        )
