"""Unit and contract tests for ULDR Phase 3.4: Differential Soviet Candidate Miner & Modern Whitelist Filter (Issue #8008)."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.v4_differential_soviet_miner import (
    AUTHENTIC_SOVIET_CALQUE_REPLACEMENTS,
    AdjudicationCategory,
    AdjudicationStatus,
    R2ULookupStatus,
    Sum11RiskEntry,
    adjudicate_sum11_entry,
    build_differential_receipt,
    is_neologism_whitelisted,
    is_skrypnykivka_archaism,
    is_soviet_ideological_realia,
    query_r2u_safe,
    validate_no_private_host_paths,
    verify_in_vesum,
)

CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"
CANDIDATE_SCHEMA_PATH = CONTRACTS_DIR / "v1_differential_soviet_candidate.schema.json"
RECEIPT_SCHEMA_PATH = CONTRACTS_DIR / "v1_differential_soviet_receipt.schema.json"
OUTPUT_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "soviet_candidates"
RECEIPT_FILE = OUTPUT_DIR / "differential_soviet_receipt.json"
MANIFEST_FILE = OUTPUT_DIR / "differential_soviet_manifest.json"
CANDIDATES_FILE = OUTPUT_DIR / "differential_soviet_candidates.jsonl"


@pytest.fixture(scope="module")
def candidate_schema() -> dict:
    assert CANDIDATE_SCHEMA_PATH.is_file(), f"Missing schema: {CANDIDATE_SCHEMA_PATH}"
    with CANDIDATE_SCHEMA_PATH.open("r", encoding="utf-8") as f:
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
def mock_vesum_cursor() -> sqlite3.Cursor:
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE forms_all (id INTEGER PRIMARY KEY, lemma TEXT, word_form TEXT)")
    cursor.execute("CREATE INDEX idx_forms_all_lemma ON forms_all(lemma)")
    cursor.execute("CREATE INDEX idx_forms_all_word_form ON forms_all(word_form)")
    test_lemmas = [
        "чинний", "переважний", "збігатися", "брати", "участь", "принаймні",
        "міра", "того", "як", "ініціатива", "щодо", "наступний", "крайній",
        "раз", "мати", "рація", "відбуватися", "впадати", "око", "насамперед",
        "кошт", "порушити", "питання", "панівний", "відсталий", "віджилий",
        "домінантний", "надихальний", "організаційний", "підрослий",
        "підпорядковувальний", "перетворювальний", "життєствердний",
        "принизливий", "спрямовувальний", "стримувальний", "хвилювальний",
        "програмування", "комп'ютер", "авіація", "транзистор", "лазер",
        "пластмаса", "полімер", "радар", "генетика", "інтернет",
        "рівнобіжник", "терпуг", "прямовис", "довгокутник", "дрібножил",
        "комсомол", "колгосп", "партком", "райком", "стахановець",
        "діючий", "подавляючий", "співпадати", "слідуючий",
    ]
    for lem in test_lemmas:
        cursor.execute("INSERT INTO forms_all (lemma, word_form) VALUES (?, ?)", (lem, lem))
    return cursor


def test_contracts_schema_validity(candidate_schema: dict, receipt_schema: dict) -> None:
    """Ensure JSON Schema definitions are valid Draft 2020-12 schemas."""
    assert candidate_schema["title"] == "DifferentialSovietCandidateV1"
    assert receipt_schema["title"] == "DifferentialSovietReceiptV1"


def test_modern_20th_century_neologism_whitelist(candidate_schema: dict, mock_vesum_cursor: sqlite3.Cursor) -> None:
    """Acceptance criterion: Zero false calque flags on 20th-century technical neologisms.

    Absence of modern computing/aviation/physics terms in 1920s R2U must NOT trigger calque flags.
    """
    sample_neologisms = [
        "програмування",
        "комп'ютер",
        "авіація",
        "транзистор",
        "лазер",
        "пластмаса",
        "полімер",
        "радар",
        "генетика",
        "інтернет",
    ]

    for word in sample_neologisms:
        assert is_neologism_whitelisted(word), f"Expected '{word}' to be in modern neologism whitelist"
        entry = Sum11RiskEntry(
            id=99999,
            word=word,
            definition=f"Modern definition of {word}",
            text=f"Sample sentence mentioning {word} in Soviet context",
            sovietization_risk=1,
            sovietization_keywords=["кпрс"],
        )
        result = adjudicate_sum11_entry(entry, vesum_cursor=mock_vesum_cursor, allow_network=False)
        jsonschema.validate(instance=result, schema=candidate_schema)

        assert result["status"] == AdjudicationStatus.WHITELIST_PRESERVED.value
        assert result["adjudication_category"] == AdjudicationCategory.MODERN_NEOLOGISM_TECHNICAL.value
        assert result["is_neologism_whitelisted"] is True
        assert result["authentic_alternatives"] == []


def test_neologism_whitelist_avoids_substring_false_positives() -> None:
    """Verify whitelist rejects non-neologisms and does not match via loose infix substrings."""
    assert not is_neologism_whitelisted("автомобільний"), "автомобільний must not match via infix 'мобільний'"
    assert not is_neologism_whitelisted("стереотип"), "стереотип must not match via prefix 'стерео'"


def test_r2u_network_timeout_vs_absence_disambiguation() -> None:
    """Acceptance criterion: Zero network timeouts logged as missing words.

    Differentiate SOURCE_UNAVAILABLE from NOT_FOUND_WITHIN_VERIFIED_COVERAGE.
    """
    # 1. Network error / Timeout must return SOURCE_UNAVAILABLE
    with patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
        with patch("scripts.rag.source_query.r2u_translate_with_status", side_effect=OSError("Network down")):
            status, translations = query_r2u_safe("програмування", allow_network=True)
            assert status == R2ULookupStatus.SOURCE_UNAVAILABLE
            assert translations == []

    # 2. Legitimate absence in verified coverage must return NOT_FOUND_WITHIN_VERIFIED_COVERAGE
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b"<html><body>No entries found</body></html>"

    with patch("urllib.request.urlopen", return_value=mock_response):
        with patch("scripts.rag.source_query.r2u_translate_with_status", return_value=(R2ULookupStatus.NOT_FOUND_WITHIN_VERIFIED_COVERAGE, [])):
            status, translations = query_r2u_safe("неіснуючеслово123", allow_network=True)
            assert status == R2ULookupStatus.NOT_FOUND_WITHIN_VERIFIED_COVERAGE
            assert translations == []


def test_skrypnykivka_only_archaism_rejection(candidate_schema: dict, mock_vesum_cursor: sqlite3.Cursor) -> None:
    """Acceptance criterion: Reject Skrypnykivka-only archaisms from modern replacement."""
    sample_archaisms = ["рівнобіжник", "терпуг", "прямовис", "довгокутник", "дрібножил"]

    for word in sample_archaisms:
        assert is_skrypnykivka_archaism(word), f"Expected '{word}' to be identified as Skrypnykivka archaism"
        entry = Sum11RiskEntry(
            id=88888,
            word=word,
            definition=f"Archaic definition of {word}",
            text="Text",
            sovietization_risk=1,
            sovietization_keywords=["ленін"],
        )
        result = adjudicate_sum11_entry(entry, vesum_cursor=mock_vesum_cursor, allow_network=False)
        jsonschema.validate(instance=result, schema=candidate_schema)

        assert result["status"] == AdjudicationStatus.SKRYPNYKIVKA_ARCHAISM_REJECTED.value
        assert result["adjudication_category"] == AdjudicationCategory.SKRYPNYKIVKA_ARCHAISM.value
        assert result["is_neologism_whitelisted"] is False


def test_soviet_ideological_realia_tagging(candidate_schema: dict, mock_vesum_cursor: sqlite3.Cursor) -> None:
    """Ensure Soviet ideological realia are categorized as historical political terms, not calques."""
    sample_realia = [
        ("комсомол", ["комсомол"]),
        ("колгосп", ["колгосп"]),
        ("партком", ["партком"]),
        ("райком", ["райком"]),
        ("стахановець", ["стаханов"]),
    ]

    for word, keywords in sample_realia:
        assert is_soviet_ideological_realia(word, keywords)
        entry = Sum11RiskEntry(
            id=77777,
            word=word,
            definition=f"Soviet realia {word}",
            text="Text",
            sovietization_risk=2,
            sovietization_keywords=keywords,
        )
        result = adjudicate_sum11_entry(entry, vesum_cursor=mock_vesum_cursor, allow_network=False)
        jsonschema.validate(instance=result, schema=candidate_schema)

        assert result["status"] == AdjudicationStatus.IDEOLOGICAL_HISTORICAL_ONLY.value
        assert result["adjudication_category"] == AdjudicationCategory.SOVIET_REALIA_IDEOLOGY.value


def test_authentic_soviet_calque_replacements(candidate_schema: dict, mock_vesum_cursor: sqlite3.Cursor) -> None:
    """Verify authentic Ukrainian replacements for verified Soviet/Russian calques."""
    assert len(AUTHENTIC_SOVIET_CALQUE_REPLACEMENTS) >= 10

    for calque, info in AUTHENTIC_SOVIET_CALQUE_REPLACEMENTS.items():
        entry = Sum11RiskEntry(
            id=66666,
            word=calque,
            definition="Calque definition",
            text="Text",
            sovietization_risk=1,
            sovietization_keywords=["партія"],
        )
        result = adjudicate_sum11_entry(entry, vesum_cursor=mock_vesum_cursor, allow_network=False)
        jsonschema.validate(instance=result, schema=candidate_schema)

        assert result["status"] == AdjudicationStatus.CANDIDATE_ADMITTED.value
        assert len(result["authentic_alternatives"]) == 1
        alt = result["authentic_alternatives"][0]
        assert alt["term"] == info["replacement"]
        assert alt["is_modern_standard"] is True


def test_vesum_attestation_mock() -> None:
    """Verify VESUM database lookup checks both lemma and word_form in forms_all."""
    mock_conn = sqlite3.connect(":memory:")
    mock_cursor = mock_conn.cursor()
    mock_cursor.execute("CREATE TABLE forms_all (id INTEGER PRIMARY KEY, lemma TEXT, word_form TEXT)")
    mock_cursor.execute("CREATE INDEX idx_forms_all_lemma ON forms_all(lemma)")
    mock_cursor.execute("CREATE INDEX idx_forms_all_word_form ON forms_all(word_form)")
    mock_cursor.execute("INSERT INTO forms_all (lemma, word_form) VALUES ('чинний', 'чинний')")
    mock_cursor.execute("INSERT INTO forms_all (lemma, word_form) VALUES ('йти', 'йшов')")

    assert verify_in_vesum("чинний", mock_cursor) is True
    assert verify_in_vesum("йшов", mock_cursor) is True
    assert verify_in_vesum("неіснуючеслово", mock_cursor) is False


def test_vesum_attestation_fails_closed_without_cursor() -> None:
    """Verify verify_in_vesum fails closed (raises RuntimeError) when cursor is None."""
    with pytest.raises(RuntimeError, match="VESUM database cursor required"):
        verify_in_vesum("чинний", None)


def test_build_differential_receipt_enforces_vesum_invariant() -> None:
    """Verify build_differential_receipt raises ValueError if any replacement lacks VESUM attestation."""
    bad_candidates = [
        {
            "schema_version": "v1_differential_soviet_candidate",
            "candidate_id": "soviet.cand.1111222233334444",
            "sum11_id": 100,
            "word": "діючий",
            "sovietization_risk": 1,
            "sovietization_keywords": ["партія"],
            "status": "CANDIDATE_ADMITTED",
            "adjudication_category": "lexical_calque",
            "authentic_alternatives": [
                {
                    "term": "вигаданеслово",
                    "source": "Antonenko-Davydovych",
                    "vesum_attested": False,
                    "is_modern_standard": True,
                }
            ],
            "is_neologism_whitelisted": False,
            "vesum_attested": True,
            "r2u_lookup_status": "found",
        }
    ]
    with pytest.raises(ValueError, match="authentic alternatives lack VESUM attestation"):
        build_differential_receipt(bad_candidates, OUTPUT_DIR)


def test_opsec_no_private_host_paths() -> None:
    """Ensure no metal paths or host usernames exist in committed structures."""
    clean_data = {"receipt_id": "receipt.soviet_miner.1234567812345678", "word": "авіація"}
    validate_no_private_host_paths(clean_data)

    dirty_samples = [
        {"path": "/home/ops/learn-ukrainian/data"},
        {"path": "/home/ubuntu/repo"},
        {"path": "/Users/developer/project"},
        {"ip": f"{192}.{168}.1.1"},
    ]
    for sample in dirty_samples:
        with pytest.raises(ValueError, match="OPSEC violation: private path detected"):
            validate_no_private_host_paths(sample)


def test_differential_receipt_manifest_and_invariants(receipt_schema: dict) -> None:
    """Verify generated receipt and manifest satisfy schemas and non-skippable invariants."""
    if not RECEIPT_FILE.is_file():
        pytest.skip(f"Receipt file not found: {RECEIPT_FILE}")

    with RECEIPT_FILE.open("r", encoding="utf-8") as f:
        receipt = json.load(f)

    jsonschema.validate(instance=receipt, schema=receipt_schema)
    validate_no_private_host_paths(receipt)

    assert receipt["issue"] == 8008
    assert receipt["epic"] == 6321
    assert receipt["sum11_risk_pool"]["total_entries"] == 7152
    assert receipt["counts"]["false_calque_flags_on_whitelist"] == 0
    assert receipt["counts"]["network_timeouts_as_missing_words"] == 0
    assert receipt["invariants"]["zero_false_calque_on_neologisms"] is True
    assert receipt["invariants"]["zero_network_errors_as_missing_word"] is True
    assert receipt["invariants"]["all_replacements_vesum_attested"] is True
    assert receipt["invariants"]["no_private_host_paths"] is True

    # Manifest check
    assert MANIFEST_FILE.is_file()
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["entry_count"] == receipt["files"]["candidates_index"]["line_count"]
    assert manifest["entry_count"] >= 190
    validate_no_private_host_paths(manifest)


def test_miner_cli_verify_only() -> None:
    """Execute v4_differential_soviet_miner.py --verify-only with mandatory subprocess timeout."""
    script_path = REPO_ROOT / "scripts" / "projects" / "open_model_data" / "v4_differential_soviet_miner.py"
    res = subprocess.run(
        [sys.executable, str(script_path), "--verify-only", "--output-dir", str(OUTPUT_DIR)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res.returncode == 0, f"--verify-only failed: stdout={res.stdout}, stderr={res.stderr}"
    assert "verified clean" in res.stdout


def test_miner_cli_verify_only_fails_on_manifest_tampering(tmp_path: Path) -> None:
    """Ensure --verify-only fails if the manifest file is missing or has a hash mismatch."""
    import shutil

    tmp_out = tmp_path / "soviet_candidates"
    tmp_out.mkdir()
    shutil.copy(RECEIPT_FILE, tmp_out / RECEIPT_FILE.name)
    shutil.copy(CANDIDATES_FILE, tmp_out / CANDIDATES_FILE.name)

    script_path = REPO_ROOT / "scripts" / "projects" / "open_model_data" / "v4_differential_soviet_miner.py"

    # 1. Missing manifest must fail
    res_missing = subprocess.run(
        [sys.executable, str(script_path), "--verify-only", "--output-dir", str(tmp_out)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res_missing.returncode != 0
    assert "Required files missing" in res_missing.stdout

    # 2. Corrupted manifest hash must fail
    (tmp_out / MANIFEST_FILE.name).write_text('{"tampered": true}\n', encoding="utf-8")
    res_tampered = subprocess.run(
        [sys.executable, str(script_path), "--verify-only", "--output-dir", str(tmp_out)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res_tampered.returncode != 0
    assert "Hash mismatch" in res_tampered.stdout
