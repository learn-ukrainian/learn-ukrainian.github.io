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
    CoTClaimVerifier,
    run_claim_verifier,
)
from tests._host_path_guard import FIXTURE_HOME


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


def test_seed_trajectories_full_verification_suite(tmp_path: Path, source_role_fixture) -> None:
    """Prove batch routing on synthetic records, without recertifying legacy seeds."""
    import copy

    module, vesum, sources, control, validator = source_role_fixture
    historical = copy.deepcopy(control)
    historical["trajectory_id"] = "traj.decolonize.bbbbbbbbbbbbbbbb"
    historical["final_response"] = "SUM-11 proves UNRELATED_MEANING_SENTINEL"
    register = copy.deepcopy(control)
    register["trajectory_id"] = "traj.decolonize.cccccccccccccccc"
    register["register_spectrum"]["alternatives"][0]["register_tier"] = "classical_regional"
    records = [control, historical, register]
    for rec in records:
        validator.validate(rec)
    inp, accepted, refused, receipt_path = [
        tmp_path / name for name in ("input.jsonl", "accepted.jsonl", "refused.jsonl", "receipt.json")
    ]
    inp.write_text("".join(json.dumps(rec) + "\n" for rec in records))
    receipt = module.run_claim_verifier(inp, accepted, refused, receipt_path, vesum, sources)
    jsonschema.validate(receipt, json.loads(module.RECEIPT_SCHEMA_PATH.read_text()))
    assert [json.loads(line) for line in accepted.read_text().splitlines()] == [control]
    assert [json.loads(line)["trajectory_id"] for line in refused.read_text().splitlines()] == [
        "traj.decolonize.bbbbbbbbbbbbbbbb",
        "traj.decolonize.cccccccccccccccc",
    ]
    assert receipt["counts"] == {
        "total_trajectories": 3,
        "trajectories_passed": 1,
        "trajectories_rejected": 2,
        "total_claims_verified": 14,
        "vesum_claims_verified": 9,
        "sum11_claims_verified": 0,
        "r2u_claims_verified": 0,
        "ulif_claims_verified": 5,
    }
    assert receipt["invariants"]["pass_rate_100_percent"] is False
    assert receipt["invariants"]["zero_unverified_dictionary_claims"] is False
    assert receipt["invariants"]["no_private_host_paths"] is True


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/decolonization/seeds/seed_decolonization_trajectories.jsonl",
)
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


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/decolonization/seeds/seed_decolonization_trajectories.jsonl",
)
def test_verify_only_hash_tamper_fails(tmp_path: Path) -> None:
    """Tampering with verified output file must cause --verify-only to fail-closed."""
    inp = tmp_path / "input.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    inp.write_bytes(DEFAULT_INPUT_TRAJECTORIES.read_bytes())
    out.write_bytes(DEFAULT_VERIFIED_OUTPUT.read_bytes())
    rej.write_bytes(DEFAULT_REJECTED_OUTPUT.read_bytes())
    rcp.write_bytes(DEFAULT_RECEIPT_OUTPUT.read_bytes())

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


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/trajectories/verified_trajectories.jsonl",
)
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
    assert any(
        "VESUM form count mismatch" in str(r) and "claimed 3, actual 2" in str(r)
        for r in rej_data[0]["rejection_reasons"]
    )


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
    assert any(
        "a SUM-11 editorial label cannot establish modern register" in str(r) for r in rej_data[0]["rejection_reasons"]
    )


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
    assert any("requires approved sense-bound evidence" in str(r) for r in rej_data[0]["rejection_reasons"])

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
    assert any("requires approved sense-bound evidence" in str(r) for r in rej_data[0]["rejection_reasons"])

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


def test_hard_rejection_opsec_private_host_path_in_trajectory(
    mock_dbs: tuple[Path, Path, Path], tmp_path: Path
) -> None:
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
            f"1. За даними з {FIXTURE_HOME}/secret_data.txt термін пилосмок підтверджено.",  # OPSEC violation!
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

    # Assert pre-write failure: no files were written to disk
    assert not out.exists(), "Verified output file must not be created when OPSEC violation is detected"
    assert not rej.exists(), "Rejected output file must not be created when OPSEC violation is detected"
    assert not rcp.exists(), "Receipt file must not be created when OPSEC violation is detected"


def test_hard_rejection_r2u_polarity_ambiguous_phrasing_fails(
    mock_dbs: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    """Ambiguous 1920s R2U claims without clear presence or absence cues must not silently pass."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "r2u_ambiguous.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    cache_file = tmp_path / "r2u_cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "пилосмок": {
                    "status": "found",
                    "translations": ["пилосмок"],
                }
            }
        ),
        encoding="utf-8",
    )

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000016",
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
            "1. За словниками 1920-х років R2U для слова «пилосмок» є контекст.",  # Ambiguous: neither presence nor absence asserted
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
    assert any("Ambiguous 1920s lexicographical claim" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_r2u_polarity_expanded_negation_phrasing(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """Diverse Ukrainian negation phrasing (не трапляється, не існує, випадає з реєстру) correctly triggers absence verification."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "r2u_expanded_neg.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    # In cache: word is FOUND
    cache_file = tmp_path / "r2u_cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "пилосмок": {
                    "status": "found",
                    "translations": ["пилосмок"],
                }
            }
        ),
        encoding="utf-8",
    )

    # Trajectory falsely asserts absence using non-standard Ukrainian phrasing
    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000017",
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
            "1. У словниках 1920-х років R2U слово «пилосмок» не трапляється і випадає з реєстру.",
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

    # Since it was claimed absent (polarity=False) but status is 'found', it must hard-reject as fabricated absence
    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    rej_data = [json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines() if line]
    assert any("Fabricated 1920s absence claim" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_dynamic_invariants_non_tautological(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """When a batch contains unverified dictionary claims, receipt invariants evaluate to False across all outcomes."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "mixed_batch.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    valid_rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000018",
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
                    "evidence_source": "STEM textbook",
                }
            ],
        },
        "reasoning_steps": [
            "1. Термін «дифузія» є нормативним фізичним терміном.",
        ],
        "final_response": "Термін «дифузія» є нормативним.",
    }

    # Second record with fabricated СУМ-11 claim
    invalid_rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000019",
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
            "1. В академічному СУМ-11 прямо зафіксовано «вигадане_слово_немає».",  # Fabricated headword!
        ],
        "final_response": "Відповідь.",
    }

    inp.write_text(json.dumps(valid_rec) + "\n" + json.dumps(invalid_rec) + "\n", encoding="utf-8")

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
    assert receipt["counts"]["trajectories_rejected"] == 1
    # Crucial non-tautology check: invariant must be False because one outcome failed a dictionary claim
    assert receipt["invariants"]["pass_rate_100_percent"] is False
    assert receipt["invariants"]["zero_unverified_dictionary_claims"] is False


def test_sum11_volume_7_and_8_authoritative_boundaries() -> None:
    """Verify official boundaries for СУМ-11 volumes 6, 7, and 8 based on Institute of Linguistics edition."""
    from scripts.projects.open_model_data.v4_verify_trajectory_claims import is_term_in_sum11_volume

    # Volume 6: П - Поїти
    assert is_term_in_sum11_volume("поїти", 6) is True
    assert is_term_in_sum11_volume("поїхати", 6) is False  # Belongs to Vol 7

    # Volume 7: Поїхати - Приробляти
    assert is_term_in_sum11_volume("поїхати", 7) is True
    assert is_term_in_sum11_volume("приробляти", 7) is True
    assert is_term_in_sum11_volume("природа", 7) is False  # Belongs to Vol 8
    assert is_term_in_sum11_volume("радісний", 7) is False  # 'Р' words are not in Vol 7!

    # Volume 8: Природа - Ряхтливий
    assert is_term_in_sum11_volume("природа", 8) is True
    assert is_term_in_sum11_volume("радісний", 8) is True
    assert is_term_in_sum11_volume("ряхтливий", 8) is True
    assert is_term_in_sum11_volume("світло", 8) is False  # Belongs to Vol 9


def test_r2u_polarity_in_historical_suppression_note_expanded_negation(
    mock_dbs: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    """Ungrounded absence claim using expanded negation stem in historical_suppression_note triggers hard rejection."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "r2u_suppression_note_neg.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    cache_file = tmp_path / "r2u_cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "пилосмок": {
                    "status": "found",
                    "translations": ["пилосмок"],
                }
            }
        ),
        encoding="utf-8",
    )

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000020",
        "query": "Тестове запитання?",
        "target_term": "пилосос",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "У словнику R2U 1920-х років слово «пилосмок» не трапляється.",
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
            "1. Аналіз джерел без згадки словників.",
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


def test_r2u_polarity_in_historical_suppression_note_ambiguous_fails(
    mock_dbs: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    """Ambiguous 1920s R2U claim in historical_suppression_note without clear polarity cues hard-rejects."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "r2u_suppression_note_ambig.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    cache_file = tmp_path / "r2u_cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "пилосмок": {
                    "status": "found",
                    "translations": ["пилосмок"],
                }
            }
        ),
        encoding="utf-8",
    )

    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000021",
        "query": "Тестове запитання?",
        "target_term": "пилосос",
        "is_calque_or_russianism": True,
        "morphemic_breakdown": {
            "source_formation": "Калька з російської мови.",
            "ukrainian_equivalent_mechanism": "Питома словотвірна модель.",
        },
        "lexicographical_context": {
            "historical_suppression_note": "За словниками 1920-х років R2U для слова «пилосмок» є певний контекст.",
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
            "1. Аналіз контексту.",
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
    assert any("Ambiguous 1920s lexicographical claim" in str(r) for r in rej_data[0]["rejection_reasons"])


def test_pure_stem_zero_dictionary_batch_passes_verify_only(mock_dbs: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """A batch with zero dictionary claims (pure STEM negative control) evaluates zero_unverified_dictionary_claims as True and passes --verify-only."""
    vesum, sources, ulif = mock_dbs
    inp = tmp_path / "pure_stem_batch.jsonl"
    out = tmp_path / "verified.jsonl"
    rej = tmp_path / "rejected.jsonl"
    rcp = tmp_path / "receipt.json"

    valid_stem_rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000022",
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
                    "evidence_source": "STEM textbook",
                }
            ],
        },
        "reasoning_steps": [
            "1. Термін «дифузія» є нормативним фізичним терміном.",
        ],
        "final_response": "Термін «дифузія» є нормативним.",
    }
    inp.write_text(json.dumps(valid_stem_rec) + "\n", encoding="utf-8")

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
    assert receipt["invariants"]["zero_unverified_dictionary_claims"] is True
    assert receipt["invariants"]["zero_unattested_living_standard_terms"] is True

    # Crucial test: run in verify_only mode on receipt without ValueError
    verify_receipt = run_claim_verifier(
        input_path=inp,
        verified_output_path=out,
        rejected_output_path=rej,
        receipt_output_path=rcp,
        vesum_db=vesum,
        sources_db=sources,
        ulif_db=ulif,
        verify_only=True,
    )
    assert verify_receipt["invariants"]["zero_unverified_dictionary_claims"] is True


def test_check_ulif_attestation_mixed_status_homonyms(tmp_path: Path) -> None:
    """A failed homonym (parse_error) must not mask an accepted homonym (ok) (#8798)."""
    s_db = tmp_path / "sources_mixed.db"
    v_db = tmp_path / "vesum_dummy.db"
    s_conn = sqlite3.connect(s_db)
    s_conn.executescript(
        """
        CREATE TABLE ulif_dictua_entries (
            id INTEGER PRIMARY KEY,
            normalized_query TEXT,
            canonical_headword TEXT,
            status TEXT,
            homonym_index INTEGER
        );
        """
    )
    # Homonym 1 is parse_error, Homonym 2 is ok (e.g. підмет)
    s_conn.execute("INSERT INTO ulif_dictua_entries VALUES (1, 'підмет', '', 'parse_error', 1)")
    s_conn.execute("INSERT INTO ulif_dictua_entries VALUES (2, 'підмет', 'пі́дмет', 'ok', 2)")
    s_conn.commit()

    v_conn = sqlite3.connect(v_db)
    verifier = CoTClaimVerifier(vesum_conn=v_conn, sources_conn=s_conn)
    assert verifier.check_ulif_attestation("підмет") is True
    assert verifier.check_ulif_attestation("неіснуюче") is False


def test_check_ulif_attestation_separately_supplied_canonical_db(tmp_path: Path) -> None:
    """Separately supplied ulif_conn with canonical ulif_dictua_entries must be recognized (#8798)."""
    s_db = tmp_path / "empty_sources.db"
    u_db = tmp_path / "separate_ulif.db"
    v_db = tmp_path / "vesum_dummy.db"

    s_conn = sqlite3.connect(s_db)
    v_conn = sqlite3.connect(v_db)

    u_conn = sqlite3.connect(u_db)
    u_conn.executescript(
        """
        CREATE TABLE ulif_dictua_entries (
            id INTEGER PRIMARY KEY,
            normalized_query TEXT,
            canonical_headword TEXT,
            status TEXT
        );
        """
    )
    u_conn.execute("INSERT INTO ulif_dictua_entries VALUES (1, 'словник', 'словни́к', 'ok')")
    u_conn.commit()

    verifier = CoTClaimVerifier(vesum_conn=v_conn, sources_conn=s_conn, ulif_conn=u_conn)
    assert verifier.check_ulif_attestation("словник") is True
    assert verifier.check_ulif_attestation("неіснуюче") is False


@pytest.fixture
def source_role_fixture(tmp_path, monkeypatch):
    """Disposable pseudowords; bind the tracked contracts rather than missing-schema fallback."""
    from scripts.projects.open_model_data import v4_verify_trajectory_claims as module

    contracts = Path(__file__).resolve().parents[3] / "registry/projects/open_model_data/contracts"
    for attr, name in (
        ("TRAJECTORY_SCHEMA_PATH", "v1_decolonization_trajectory.schema.json"),
        ("RECEIPT_SCHEMA_PATH", "v1_cot_claim_verification_receipt.schema.json"),
    ):
        path = contracts / name
        assert path.is_file()
        monkeypatch.setattr(module, attr, path)
    monkeypatch.setattr(module, "DEFAULT_ULIF_DB", None)
    monkeypatch.setattr(module, "DEFAULT_R2U_CACHE", None)
    vesum = tmp_path / "synthetic_vesum.db"
    sources = tmp_path / "synthetic_sources.db"
    with sqlite3.connect(vesum) as conn:
        conn.execute("CREATE TABLE forms_all (lemma TEXT, word_form TEXT, pos TEXT, tags TEXT)")
        conn.execute("INSERT INTO forms_all VALUES ('zorf', 'zorfa', 'noun', 'noun:m')")
    with sqlite3.connect(sources) as conn:
        conn.execute(
            "CREATE TABLE sum11 (id INTEGER, word TEXT, definition TEXT, text TEXT, "
            "sovietization_risk INTEGER, sovietization_keywords TEXT, ideological_markers TEXT)"
        )
        conn.execute(
            "INSERT INTO sum11 VALUES (1, 'zorf', 'GLOSS_SENTINEL', 'діал. RAW_SENTINEL', "
            "0, 'KEYWORD_SENTINEL', 'MARKER_SENTINEL')"
        )
        conn.execute(
            "INSERT INTO sum11 VALUES (2, 'blorf', 'GLOSS_SENTINEL', 'RAW_SENTINEL', "
            "2, 'KEYWORD_SENTINEL', 'MARKER_SENTINEL')"
        )
    rec = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.aaaaaaaaaaaaaaaa",
        "query": "SENTINEL question",
        "target_term": "zorf",
        "is_calque_or_russianism": False,
        "morphemic_breakdown": {
            "source_formation": "SENTINEL formation",
            "ukrainian_equivalent_mechanism": "SENTINEL mechanism",
        },
        "vesum_attestation": [{"lemma": "zorf", "vesum_forms_count": 1, "is_standard_attested": True}],
        "register_spectrum": {
            "primary_living_standard": "zorf",
            "alternatives": [{"lemma": "zorf", "register_tier": "living_standard", "evidence_source": "SENTINEL"}],
        },
        "reasoning_steps": ["SENTINEL only"],
        "final_response": "SENTINEL answer",
    }
    validator = jsonschema.Draft202012Validator(json.loads(module.TRAJECTORY_SCHEMA_PATH.read_text()))
    validator.validate(rec)
    return module, vesum, sources, rec, validator


@pytest.mark.parametrize("tier", ["classical_regional", "technical_compound"])
@pytest.mark.parametrize("term", ["zorf", "blorf", "missing_sentinel"])
def test_source_role_register_acceptance_and_receipt(source_role_fixture, tmp_path, tier, term):
    module, vesum, sources, rec, validator = source_role_fixture
    rec["register_spectrum"]["alternatives"] = [
        {
            "lemma": term,
            "register_tier": tier,
            "evidence_source": "arbitrary citation " * 20,
        }
    ]
    validator.validate(rec)
    inp, accepted, refused, receipt_path = [
        tmp_path / name for name in ("input.jsonl", "accepted.jsonl", "refused.jsonl", "receipt.json")
    ]
    inp.write_text(json.dumps(rec) + "\n")
    receipt = module.run_claim_verifier(inp, accepted, refused, receipt_path, vesum, sources)
    jsonschema.validate(receipt, json.loads(module.RECEIPT_SCHEMA_PATH.read_text()))
    assert accepted.read_text() == ""
    rejection = json.loads(refused.read_text())
    assert rejection["rejected"] is True
    assert rejection["rejection_reasons"] == [
        {
            "claim_type": "ULIF_REGISTER",
            "source_field": "register_spectrum.alternatives[0]",
            "term": term,
            "claim_text": f"Alternative «{term}» register tier claims «{tier}»",
            "error": f"Register tier «{tier}» requires approved sense-bound evidence; "
            "SUM-11, morphology and an arbitrary citation cannot establish it",
            "evidence": "Unresolved register evidence",
        }
    ]
    assert receipt["counts"]["trajectories_passed"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    assert receipt["counts"]["ulif_claims_verified"] == 1
    assert receipt["counts"]["sum11_claims_verified"] == 0


@pytest.mark.parametrize(
    "field",
    ["reasoning_steps", "final_response", "lexicographical_context", "morphemic_breakdown", "register_spectrum"],
)
def test_source_role_semantic_prose_cannot_hide_behind_citation(source_role_fixture, field):
    module, vesum, sources, rec, validator = source_role_fixture
    text = "SUM-11: zorf means ARBITRARY_UNRELATED_MEANING"
    if field == "reasoning_steps":
        rec[field] = [text]
    elif field == "lexicographical_context":
        rec[field] = {"historical_suppression_note": text}
    elif field == "morphemic_breakdown":
        rec[field]["source_formation"] = text
    elif field == "register_spectrum":
        rec[field]["alternatives"][0]["evidence_source"] = text
    else:
        rec[field] = text
    validator.validate(rec)
    with sqlite3.connect(vesum) as v_conn, sqlite3.connect(sources) as s_conn:
        outcome = module.CoTClaimVerifier(v_conn, s_conn).verify_trajectory(rec, validator)
    assert outcome.passed is False
    assert outcome.rejection_reasons[0] == {
        "claim_type": "SUM11_SOURCE_ROLE",
        "source_field": "root",
        "evidence": "soviet_colonization_context",
        "error": "Unresolved: historical SUM-11 context cannot certify modern semantic prose",
    }


@pytest.mark.parametrize(
    "claim_type,attributes",
    [
        ("SUM11_HEADWORD", {}),
        ("SUM11_STYLISTIC", {"label": "діал"}),
        ("SUM11_VOLUME_YEAR", {"volume": 3, "year": 1972, "target_term": "зорф"}),
        ("SUM11_SOVIETIZATION", {"context": "INVENTED suppression assertion"}),
    ],
)
def test_source_role_historical_facts_never_verify_semantics(source_role_fixture, claim_type, attributes):
    module, vesum, sources, rec, _validator = source_role_fixture
    claim = module.ParsedClaim(module.ClaimType(claim_type), "sentinel", "zorf", "SENTINEL", attributes)
    with sqlite3.connect(vesum) as v_conn, sqlite3.connect(sources) as s_conn:
        result = module.CoTClaimVerifier(v_conn, s_conn).verify_claim(claim, rec)
    assert result.passed is False
    assert result.evidence == "soviet_colonization_context"
    assert result.error_message.startswith("Unresolved:")


@pytest.mark.parametrize("term", ["zorf", "zorfa", "zorf extra"])
def test_source_role_lookup_fallback_keeps_context_not_raw_definition(source_role_fixture, term):
    module, vesum, sources, _rec, _validator = source_role_fixture
    with sqlite3.connect(vesum) as v_conn, sqlite3.connect(sources) as s_conn:
        entry = module.CoTClaimVerifier(v_conn, s_conn).get_sum11_entry(term)
    # A phrase/head fallback is diagnostic only; raw definitions never escape.
    if term == "zorf extra":
        assert entry is None
    else:
        assert entry == {
            "id": 1,
            "word": "zorf",
            "soviet_colonization_context": {
                "sovietization_risk": 0,
                "sovietization_keywords": "KEYWORD_SENTINEL",
                "ideological_markers": "MARKER_SENTINEL",
            },
        }


@pytest.mark.parametrize("citation", ["СУМ-20", "SUM-20", "підсумок SENTINEL"])
def test_source_role_does_not_reclassify_other_sources(source_role_fixture, citation):
    module, vesum, sources, rec, validator = source_role_fixture
    rec["final_response"] = citation + " SENTINEL answer"
    validator.validate(rec)
    with sqlite3.connect(vesum) as v_conn, sqlite3.connect(sources) as s_conn:
        outcome = module.CoTClaimVerifier(v_conn, s_conn).verify_trajectory(rec, validator)
    assert outcome.passed is True
    assert outcome.rejection_reasons == []


def test_source_role_unparsed_citation_marks_receipt_unverified(source_role_fixture, tmp_path):
    module, vesum, sources, rec, validator = source_role_fixture
    rec["final_response"] = "SUM11 proves ARBITRARY_UNSUPPORTED_SENSE"
    validator.validate(rec)
    inp, accepted, refused, receipt_path = [
        tmp_path / name for name in ("input.jsonl", "accepted.jsonl", "refused.jsonl", "receipt.json")
    ]
    inp.write_text(json.dumps(rec) + "\n")
    receipt = module.run_claim_verifier(inp, accepted, refused, receipt_path, vesum, sources)
    assert accepted.read_text() == ""
    assert receipt["invariants"]["zero_unverified_dictionary_claims"] is False
    assert receipt["counts"]["sum11_claims_verified"] == 0
    assert receipt["counts"]["trajectories_rejected"] == 1
    assert json.loads(refused.read_text())["rejection_reasons"][0]["claim_type"] == "SUM11_SOURCE_ROLE"


@pytest.mark.parametrize(
    "kind,term,attributes,passed,evidence",
    [
        ("SUM11_HEADWORD", "zorf extra", {}, False, "soviet_colonization_context"),
        ("SUM11_STYLISTIC", "missing_sentinel", {"label": "діал"}, False, "Not in sum11"),
        ("SUM11_SOVIETIZATION", "missing_sentinel", {}, False, "Term not in СУМ-11"),
        ("SUM11_VOLUME_YEAR", "зорф", {"volume": 12}, False, "Invalid volume 12"),
        ("SUM11_VOLUME_YEAR", "зорф", {"volume": 3, "year": 1971}, False, "Year mismatch for vol 3"),
        ("SUM11_VOLUME_YEAR", "зорф", {"volume": 1, "year": 1970}, False, "Alphabetical volume mismatch"),
        ("VESUM_TAGS", "zorf", {"tags": ["noun"]}, True, "Tags ['noun'] attested in VESUM"),
        ("VESUM_TAGS", "zorf", {"tags": ["verb"]}, False, "Tags not found"),
        ("VESUM_TAGS", "missing_sentinel", {"tags": ["noun"]}, False, "Tags not found"),
        ("VESUM_LEMMA", "zorf zorf", {}, True, "Attested phrase in VESUM (words attested: [1, 1])"),
    ],
)
def test_source_role_diagnostics_and_morphology_controls(source_role_fixture, kind, term, attributes, passed, evidence):
    module, vesum, sources, rec, _validator = source_role_fixture
    claim = module.ParsedClaim(module.ClaimType(kind), "sentinel", term, "SENTINEL", attributes)
    with sqlite3.connect(vesum) as v_conn, sqlite3.connect(sources) as s_conn:
        result = module.CoTClaimVerifier(v_conn, s_conn).verify_claim(claim, rec)
    assert result.passed is passed
    assert result.evidence == evidence
