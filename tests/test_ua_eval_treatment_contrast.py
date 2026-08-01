from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.ua_eval_harness.compare_treatment_runs import (
    ContrastError,
    paired_contrast,
    safety_contrast,
)

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "data/projects/ua_eval_harness/baselines/v1/identity.responses.jsonl"
FIXTURE = ROOT / "data/projects/ua_eval_harness/baselines/v1/fixture-rules.responses.jsonl"


def test_paired_identical_run_has_zero_delta_and_interval() -> None:
    report = paired_contrast(IDENTITY, IDENTITY, samples=25, seed=6170)
    assert report["primary"] == {"delta_f0_5": 0.0, "delta_f0_5_95_ci": [0.0, 0.0]}
    assert report["secondary"]["delta_exact_sentence_accuracy_95_ci"] == [0.0, 0.0]
    assert report["inference"]["statistical_gate_passed"] is False


def test_paired_contrast_is_antisymmetric_under_arm_swap(tmp_path: Path) -> None:
    identity_rows = IDENTITY.read_text(encoding="utf-8").splitlines()
    fixture_rows = FIXTURE.read_text(encoding="utf-8").splitlines()
    aligned_fixture = tmp_path / "aligned-fixture.jsonl"
    aligned_fixture.write_text(identity_rows[0] + "\n" + "\n".join(fixture_rows[1:]) + "\n", encoding="utf-8")
    forward = paired_contrast(IDENTITY, aligned_fixture, samples=25, seed=6170)
    reverse = paired_contrast(aligned_fixture, IDENTITY, samples=25, seed=6170)
    assert forward["primary"]["delta_f0_5"] == pytest.approx(-reverse["primary"]["delta_f0_5"])
    assert forward["primary"]["delta_f0_5_95_ci"] == pytest.approx(
        [-reverse["primary"]["delta_f0_5_95_ci"][1], -reverse["primary"]["delta_f0_5_95_ci"][0]]
    )


def test_paired_contrast_rejects_decoding_drift(tmp_path: Path) -> None:
    rows = IDENTITY.read_text(encoding="utf-8").splitlines()
    header = json.loads(rows[0])
    header["decoding"] = {"deterministic": False}
    drifted = tmp_path / "drifted.jsonl"
    drifted.write_text(json.dumps(header, sort_keys=True) + "\n" + "\n".join(rows[1:]) + "\n", encoding="utf-8")
    with pytest.raises(ContrastError, match="generation constants drift"):
        paired_contrast(IDENTITY, drifted, samples=1)


def _write_safety_run(path: Path, *, arm: str, probe_hash: str, responses: dict[str, str]) -> None:
    header = {
        "arm": arm,
        "decoding": {"do_sample": False, "temperature": 0},
        "model_revision": "842da3794eaa0b77d5f08bae87a17459d91ff475",
        "probe_artifact_sha256": probe_hash,
        "schema_version": "ua_eval_treatment_safety_responses.v1",
        "type": "safety_run",
    }
    rows = [header, *({"probe_id": probe_id, "raw_response": response} for probe_id, response in responses.items())]
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def test_safety_contrast_enforces_protected_and_no_change_gate(tmp_path: Path) -> None:
    probes = [
        {
            "gold_status": "deterministic_non_human_proxy_not_linguistic_gold",
            "kind": "clean_no_change",
            "probe_id": "probe:clean",
            "source": "Це коректне речення.",
            "source_payload_id": "source-clean",
            "source_sha256": "0" * 64,
            "type": "safety_probe",
        },
        {
            "gold_status": "deterministic_non_human_proxy_not_linguistic_gold",
            "kind": "protected_span",
            "probe_id": "probe:protected",
            "protected": {"end_char": 14, "reason": "quote", "sha256": "1" * 64, "start_char": 8, "text": "цитата"},
            "source": "Тут є цитата у контексті.",
            "source_payload_id": "source-protected",
            "source_sha256": "2" * 64,
            "type": "safety_probe",
        },
    ]
    probes_path = tmp_path / "probes.jsonl"
    probes_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in probes), encoding="utf-8")
    probe_hash = hashlib.sha256(probes_path.read_bytes()).hexdigest()
    faithful = tmp_path / "faithful.jsonl"
    modern = tmp_path / "modern.jsonl"
    responses = {"probe:clean": "Це коректне речення.", "probe:protected": "Тут є цитата у контексті."}
    _write_safety_run(faithful, arm="faithful_cpt", probe_hash=probe_hash, responses=responses)
    _write_safety_run(modern, arm="modern_mask_cpt", probe_hash=probe_hash, responses=responses)
    report = safety_contrast(probes_path, faithful, modern)
    assert report["gate"]["passed"] is True
    failing = {"probe:clean": "Це змінене речення.", "probe:protected": "Тут немає слова у контексті."}
    _write_safety_run(modern, arm="modern_mask_cpt", probe_hash=probe_hash, responses=failing)
    report = safety_contrast(probes_path, faithful, modern)
    assert report["gate"]["passed"] is False
    assert report["modern"]["protected_span"]["failures"] == 1
