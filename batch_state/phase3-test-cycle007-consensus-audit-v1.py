#!/usr/bin/env python3
"""Synthetic tests for Phase 3 Cycle 007 consensus audit and clean sampler."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

HERE = Path(__file__).resolve().parent
AUDIT_PATH = HERE / "phase3-audit-cycle007-consensus-v1.py"
COMPARE_PATH = HERE / "phase3-compare-cycle007-dual-labels-v1.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


audit_mod = _load_module(AUDIT_PATH, "audit_mod")
compare_mod = _load_module(COMPARE_PATH, "compare_mod_audit")


def test_seed_derivation():
    custody = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
    manifest = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
    commitment = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"

    seed = audit_mod.seed_clean_consensus(custody, manifest, commitment)
    assert isinstance(seed, str) and len(seed) == 64

    # Check rank derivation
    rank = audit_mod.rank_row(seed, "clean_label", "unit-1", "a" * 64)
    assert isinstance(rank, str) and len(rank) == 64


def test_zero_event_bound():
    bound_600 = audit_mod.compute_zero_event_bound(600)
    # At 600 rows, 1 - 0.05**(1/600) is approx 0.004975 (< 0.5%)
    assert bound_600 < 0.005
    assert bound_600 > 0.004


def test_sampler_population_under_600(tmp_path):
    # If population <= 600, sampler audits whole population
    pkg = tmp_path / "pkg"
    pkg.mkdir(parents=True, mode=0o700)
    (pkg / "custody-receipt.json").write_text("{}\n")
    (pkg / "manifest.json").write_text("{}\n")

    records = [
        {
            "lane": "clean_label",
            "source_row": {"unit_id": f"u-{i}", "unit_sha256": f"{i:04d}" + "0" * 60},
            "label": {
                "decision_code": "agree",
                "clean_modern_standard_prose": True,
                "modern_genre_id": "expository_narrative",
                "evidence_ids": [],
            },
        }
        for i in range(50)
    ]

    receipt, sample = audit_mod.sample_clean_consensus(pkg, records)
    assert receipt["population_count"] == 50
    assert receipt["audited_count"] == 50
    assert len(sample) == 50


def test_sampler_fill_to_600(tmp_path):
    # Population 1000, 1 stratum (agree). Top 10 from stratum, then fill 590 by global rank -> exactly 600
    pkg = tmp_path / "pkg"
    pkg.mkdir(parents=True, mode=0o700)
    (pkg / "custody-receipt.json").write_text("{}\n")
    (pkg / "manifest.json").write_text("{}\n")

    records = [
        {
            "lane": "clean_label",
            "source_row": {"unit_id": f"u-{i}", "unit_sha256": f"{i:04d}" + "0" * 60},
            "label": {
                "decision_code": "agree",
                "clean_modern_standard_prose": True,
                "modern_genre_id": "expository_narrative",
                "evidence_ids": [],
            },
        }
        for i in range(1000)
    ]

    receipt, sample = audit_mod.sample_clean_consensus(pkg, records)
    assert receipt["population_count"] == 1000
    assert receipt["audited_count"] == 600
    assert len(sample) == 600


def test_sampler_expand_beyond_600(tmp_path):
    # If mandatory union of top 10 per stratum exceeds 600, expands to full union
    pkg = tmp_path / "pkg"
    pkg.mkdir(parents=True, mode=0o700)
    (pkg / "custody-receipt.json").write_text("{}\n")
    (pkg / "manifest.json").write_text("{}\n")

    records = []
    # Create 70 strata with 10 rows each -> 700 rows
    for s in range(70):
        for i in range(10):
            records.append({
                "lane": "residual_label",
                "source_row": {"unit_id": f"u-{s}-{i}", "unit_sha256": f"{s:02d}{i:02d}" + "0" * 60},
                "label": {
                    "phenomena": [
                        {
                            "phenomenon_id": contract.RESIDUAL_PHENOMENON_TAXONOMY[s % 23],
                            "decision_code": f"code_{s}",
                            "evidence_sufficiency": "sufficient",
                            "evidence_ids": [],
                        }
                    ]
                },
            })

    receipt, sample = audit_mod.sample_clean_consensus(pkg, records)
    assert receipt["population_count"] == 700
    assert receipt["audited_count"] == 700
    assert len(sample) == 700


def test_audit_terminal_finding_on_russianism(tmp_path):
    record = {
        "source_row": {
            "unit_id": "u-1",
            "unit_sha256": "0" * 64,
            "is_negative_control": True,
            "control_type": "russianism",
        },
        "label": {
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": [],
        },
    }
    row_ev = {
        "unit_id": "u-1",
        "unit_sha256": "0" * 64,
        "evidence": [],
        "evidence_ids": [],
    }

    with pytest.raises(audit_mod.TerminalAuditFindingError) as exc:
        audit_mod.audit_row_evidence(record, row_ev)
    assert exc.value.failure_code == "russianism_accepted_finding"


def test_audit_terminal_finding_on_unsupported_positive():
    record = {
        "source_row": {
            "unit_id": "u-1",
            "unit_sha256": "0" * 64,
        },
        "label": {
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": ["ev-1"],
        },
    }
    # row evidence has vesum miss -> insufficient
    rec = {
        "evidence_id": "ev-1",
        "channel": "vesum_attestation",
        "status": "not_found",
        "supports": "no_conclusion",
    }
    row_ev = {
        "unit_id": "u-1",
        "unit_sha256": "0" * 64,
        "evidence": [rec],
        "evidence_ids": ["ev-1"],
    }

    with pytest.raises(audit_mod.TerminalAuditFindingError) as exc:
        audit_mod.audit_row_evidence(record, row_ev)
    assert exc.value.failure_code == "unsupported_acceptance_finding"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
