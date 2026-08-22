#!/usr/bin/env python3
"""Synthetic tests for Phase 3 Cycle 007 dual label adjudication."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ADJ_PATH = HERE / "phase3-run-cycle007-dual-label-adjudication-v1.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


adj_mod = _load_module(ADJ_PATH, "adj_mod")


def _setup_disagreement_package(tmp_path: Path):
    pkg = tmp_path / "pkg"
    pkg.mkdir(parents=True, mode=0o700)

    # Basic files
    custody = {
        "schema_version": "phase3_cycle007_custody_receipt_v1",
        "evaluation_cycle_id": adj_mod.CYCLE,
    }
    (pkg / "custody-receipt.json").write_text(json.dumps(custody) + "\n")
    (pkg / "custody-receipt.json").chmod(0o600)

    manifest = {
        "schema_version": "phase3_cycle007_materialization_manifest_v1",
        "evaluation_cycle_id": adj_mod.CYCLE,
    }
    (pkg / "manifest.json").write_text(json.dumps(manifest) + "\n")
    (pkg / "manifest.json").chmod(0o600)

    comp_dir = pkg / adj_mod.COMPARE_OUTPUT / "clean_label"
    comp_dir.mkdir(parents=True, mode=0o700)

    records = [
        {
            "source_row": {"unit_id": "u-1", "unit_sha256": "1" * 64},
            "grok_label": {
                "unit_id": "u-1",
                "unit_sha256": "1" * 64,
                "decision_code": "agree",
                "clean_modern_standard_prose": True,
                "modern_genre_id": "expository_narrative",
                "evidence_ids": [],
            },
            "gemini_label": {
                "unit_id": "u-1",
                "unit_sha256": "1" * 64,
                "decision_code": "reject_fragment_or_too_short",
                "clean_modern_standard_prose": False,
                "modern_genre_id": None,
                "evidence_ids": [],
            },
        },
        {
            "source_row": {"unit_id": "u-2", "unit_sha256": "2" * 64},
            "grok_label": {
                "unit_id": "u-2",
                "unit_sha256": "2" * 64,
                "decision_code": "agree",
                "clean_modern_standard_prose": True,
                "modern_genre_id": "expository_narrative",
                "evidence_ids": [],
            },
            "gemini_label": {
                "unit_id": "u-2",
                "unit_sha256": "2" * 64,
                "decision_code": "reject_exercise_or_task_prompt",
                "clean_modern_standard_prose": False,
                "modern_genre_id": None,
                "evidence_ids": [],
            },
        },
    ]

    dis_p = comp_dir / "disagreements-0001.json"
    dis_p.write_text(json.dumps({"records": records}) + "\n")
    dis_p.chmod(0o600)

    return pkg, records


def test_adjudicate_packet_candidate_only(tmp_path):
    pkg, _records = _setup_disagreement_package(tmp_path)

    # Select Grok for row 1, Gemini for row 2
    selections = {
        "selections": [
            {"unit_id": "u-1", "unit_sha256": "1" * 64, "selection": "grok"},
            {"unit_id": "u-2", "unit_sha256": "2" * 64, "selection": "gemini"},
        ]
    }

    result = adj_mod.adjudicate_packet(pkg, "clean_label", 1, selections_override=selections)
    assert result["disagreement_count"] == 2
    assert result["adjudicated_count"] == 2
    assert result["unresolved_count"] == 0

    labels_p = pkg / adj_mod.OUTPUT / "final" / "clean_label" / "labels-0001.json"
    labels_val = json.loads(labels_p.read_text())
    assert labels_val["labels"][0]["decision_code"] == "agree"
    assert labels_val["labels"][1]["decision_code"] == "reject_exercise_or_task_prompt"


def test_adjudicate_rejects_third_label_invention(tmp_path):
    pkg, _records = _setup_disagreement_package(tmp_path)

    # Select illegal third choice
    selections = {
        "selections": [
            {"unit_id": "u-1", "unit_sha256": "1" * 64, "selection": "third_invented_label"},
            {"unit_id": "u-2", "unit_sha256": "2" * 64, "selection": "gemini"},
        ]
    }

    with pytest.raises(adj_mod.Error) as exc:
        adj_mod.adjudicate_packet(pkg, "clean_label", 1, selections_override=selections)
    assert exc.value.failure_code == "third_label_invented_drift"


def test_adjudicate_rejects_identity_drift(tmp_path):
    pkg, _records = _setup_disagreement_package(tmp_path)

    # Reordered identity
    selections = {
        "selections": [
            {"unit_id": "u-2", "unit_sha256": "2" * 64, "selection": "grok"},
            {"unit_id": "u-1", "unit_sha256": "1" * 64, "selection": "gemini"},
        ]
    }

    with pytest.raises(adj_mod.Error) as exc:
        adj_mod.adjudicate_packet(pkg, "clean_label", 1, selections_override=selections)
    assert exc.value.failure_code == "ordinal_identity_binding_drift"


def test_adjudicate_records_unresolved(tmp_path):
    pkg, _records = _setup_disagreement_package(tmp_path)

    selections = {
        "selections": [
            {"unit_id": "u-1", "unit_sha256": "1" * 64, "selection": "unresolved"},
            {"unit_id": "u-2", "unit_sha256": "2" * 64, "selection": "gemini"},
        ]
    }

    result = adj_mod.adjudicate_packet(pkg, "clean_label", 1, selections_override=selections)
    assert result["disagreement_count"] == 2
    assert result["adjudicated_count"] == 1
    assert result["unresolved_count"] == 1

    unres_p = pkg / adj_mod.OUTPUT / "final" / "clean_label" / "unresolved-0001.json"
    unres_val = json.loads(unres_p.read_text())
    assert len(unres_val["records"]) == 1
    assert unres_val["records"][0]["source_row"]["unit_id"] == "u-1"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
