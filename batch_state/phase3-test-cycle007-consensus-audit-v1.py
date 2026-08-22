#!/usr/bin/env python3
"""Synthetic tests for Phase 3 Cycle 007 consensus audit and clean sampler."""

from __future__ import annotations

import importlib.util
import json
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


FAKE_REVIEWER = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

counter_name = os.environ.get("CYCLE007_AUDIT_CALLS")
calls = 0
if counter_name:
    counter = Path(counter_name)
    calls = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(calls + 1), encoding="utf-8")
plan_path = os.environ.get("CYCLE007_AUDIT_PLAN")
if plan_path and not Path(plan_path).is_file():
    raise SystemExit(19)
if os.environ.get("CYCLE007_AUDIT_MODE") == "structural":
    print("not-json")
    raise SystemExit(0)
envelope = json.loads(sys.stdin.buffer.read())
text = envelope["message"]["content"][0]["text"]
targets = json.loads(text.split("--- BEGIN IMMUTABLE SOURCE REVIEW TARGETS JSON ---\n", 1)[1].split("--- END", 1)[0])["targets"]
reviews = [{"lane": target["lane"], "packet_index": target["packet_index"], "unit_id": target["source_row"]["unit_id"], "unit_sha256": target["source_row"]["unit_sha256"], "source_evidence_sha256": target["source_evidence_sha256"], "outcome": "pass"} for target in targets]
if os.environ.get("CYCLE007_AUDIT_MODE") == "missing_second" and calls == 1:
    reviews = []
print(json.dumps({"event": "init", "init": {"model": "Claude Sonnet 4.6 (Thinking)"}}))
print(json.dumps({"event": "result", "result": {"status": "SUCCESS", "structured_output": {"reviews": reviews}}}))
'''


def _review_fixture(tmp_path: Path):
    package = tmp_path / "pkg"
    package.mkdir(parents=True, mode=0o700)
    (package / "custody-receipt.json").write_text("{}\n", encoding="utf-8")
    (package / "custody-receipt.json").chmod(0o600)
    (package / "manifest.json").write_text("{}\n", encoding="utf-8")
    (package / "manifest.json").chmod(0o600)
    evidence = {"unit_id": "u-1", "unit_sha256": "1" * 64, "evidence": [], "private": "PRIVATE_TEXT_DO_NOT_RECEIPT"}
    record = {
        "lane": "clean_label",
        "packet_index": 1,
        "source_row": {"unit_id": "u-1", "unit_sha256": "1" * 64, "private": "PRIVATE_TEXT_DO_NOT_RECEIPT"},
        "label": {"decision_code": "reject_mixed_or_uncertain", "private": "PRIVATE_TEXT_DO_NOT_RECEIPT"},
    }
    sample_receipt = {"receipt_sha256": "2" * 64}
    plan, targets = audit_mod.seal_review_plan(package, [], [record], {("u-1", "1" * 64): evidence}, sample_receipt)
    return package, plan, targets


def _passing_reviews(targets):
    return {
        "reviews": [
            {
                "lane": target["lane"],
                "packet_index": target["packet_index"],
                "unit_id": target["source_row"]["unit_id"],
                "unit_sha256": target["source_row"]["unit_sha256"],
                "source_evidence_sha256": target["source_evidence_sha256"],
                "outcome": "pass",
            }
            for target in targets
        ]
    }


def _multibatch_review_fixture(tmp_path: Path):
    package = tmp_path / "multi-pkg"
    package.mkdir(parents=True, mode=0o700)
    for name in ("custody-receipt.json", "manifest.json"):
        (package / name).write_text("{}\n", encoding="utf-8")
        (package / name).chmod(0o600)
    records = []
    evidence = {}
    for number, packet in (("u-1", 1), ("u-2", 2)):
        unit_sha = str(packet) * 64
        record = {
            "lane": "clean_label",
            "packet_index": packet,
            "source_row": {"unit_id": number, "unit_sha256": unit_sha, "private": "PRIVATE_TEXT_DO_NOT_RECEIPT"},
            "label": {"decision_code": "reject_mixed_or_uncertain"},
        }
        records.append(record)
        evidence[(number, unit_sha)] = {"unit_id": number, "unit_sha256": unit_sha, "evidence": [], "private": "PRIVATE_TEXT_DO_NOT_RECEIPT"}
    return (package, *audit_mod.seal_review_plan(package, [], records, evidence, {"receipt_sha256": "3" * 64}))


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
    assert receipt["seed"] == audit_mod.seed_clean_consensus(
        audit_mod.SOURCE_CUSTODY_SHA256,
        audit_mod.SOURCE_MANIFEST_SHA256,
        audit_mod.ORDERED_IDENTITY_COMMITMENT_SHA256,
    )
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


def test_missing_normative_evidence_is_a_risk_trigger_even_when_none_exists():
    record = {
        "lane": "residual_label",
        "source_row": {"unit_id": "u-1", "unit_sha256": "0" * 64},
        "label": {"phenomena": [{"phenomenon_id": "apostrophe", "decision_code": "positive"}]},
    }
    assert audit_mod._missing_normative_risk(record, {"evidence": []}) is True


def test_source_review_requires_explicit_transport(tmp_path):
    package, plan, targets = _review_fixture(tmp_path)

    with pytest.raises(audit_mod.Error) as exc:
        audit_mod.source_review(package, targets, plan)

    assert exc.value.failure_code == "review_missing"


@pytest.mark.parametrize("mutation", ["incomplete", "duplicate", "foreign"])
def test_review_result_requires_exact_complete_unique_identities(tmp_path, mutation):
    _package, _plan, targets = _review_fixture(tmp_path)
    payload = _passing_reviews(targets)
    if mutation == "incomplete":
        payload["reviews"] = []
    elif mutation == "duplicate":
        payload["reviews"].append(dict(payload["reviews"][0]))
    else:
        payload["reviews"][0]["unit_id"] = "foreign"

    with pytest.raises(audit_mod.Error) as exc:
        audit_mod.validate_review_results(targets, payload)

    assert exc.value.failure_code in {"incomplete_risk_review", "review_identity_drift"}


def test_terminal_review_finding_is_fail_closed(tmp_path):
    package, plan, targets = _review_fixture(tmp_path)
    payload = _passing_reviews(targets)
    payload["reviews"][0]["outcome"] = "russianism_accepted"

    with pytest.raises(audit_mod.TerminalAuditFindingError) as exc:
        audit_mod.source_review(package, targets, plan, synthetic_provider=True, fixture_override=payload)
    assert exc.value.failure_code == "russianism_accepted_finding"
    stop = json.loads((package / audit_mod.OUTPUT / "provider-stop.json").read_text())
    assert stop["failure_code"] == "russianism_accepted_finding" and stop["text_free"] is True


def test_fixture_review_is_explicit_and_receipt_is_text_free(tmp_path):
    package, plan, targets = _review_fixture(tmp_path)
    result = audit_mod.source_review(package, targets, plan, synthetic_provider=True, fixture_override=_passing_reviews(targets))

    assert result["reviewed_count"] == 1 and result["text_free"] is True
    receipt = (package / audit_mod.OUTPUT / "source-review-receipt.json").read_text()
    assert "PRIVATE_TEXT_DO_NOT_RECEIPT" not in receipt
    with pytest.raises(audit_mod.Error) as exc:
        audit_mod.source_review(package, targets, plan, fixture_override=_passing_reviews(targets))
    assert exc.value.failure_code == "mode_drift"


def test_tampered_sealed_review_plan_is_rejected(tmp_path):
    package, plan, targets = _review_fixture(tmp_path)
    plan_path = package / audit_mod.OUTPUT / "source-review-plan.json"
    tampered = json.loads(plan_path.read_text())
    tampered["targets"][0]["scope"] = "tampered"
    plan_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
    plan_path.chmod(0o600)

    with pytest.raises(audit_mod.Error) as exc:
        audit_mod.source_review(package, targets, plan, synthetic_provider=True, fixture_override=_passing_reviews(targets))
    assert exc.value.failure_code == "binding_failure"


def test_plan_is_sealed_before_call_and_structural_retry_is_bounded(tmp_path, monkeypatch):
    package, plan, targets = _review_fixture(tmp_path)
    provider = tmp_path / "reviewer.py"
    provider.write_text(FAKE_REVIEWER, encoding="utf-8")
    provider.chmod(0o700)
    calls = tmp_path / "calls"
    monkeypatch.setenv("CYCLE007_AUDIT_PLAN", str(package / audit_mod.OUTPUT / "source-review-plan.json"))
    monkeypatch.setenv("CYCLE007_AUDIT_CALLS", str(calls))
    monkeypatch.setenv("CYCLE007_AUDIT_MODE", "structural")

    with pytest.raises(audit_mod.Error) as exc:
        audit_mod.source_review(package, targets, plan, provider=provider, synthetic_provider=True)

    assert exc.value.failure_code == "stream_json_invalid"
    assert calls.read_text() == "2"


def test_successful_synthetic_provider_review_binds_exact_reviewer(tmp_path, monkeypatch):
    package, plan, targets = _review_fixture(tmp_path)
    provider = tmp_path / "reviewer.py"
    provider.write_text(FAKE_REVIEWER, encoding="utf-8")
    provider.chmod(0o700)
    monkeypatch.setenv("CYCLE007_AUDIT_PLAN", str(package / audit_mod.OUTPUT / "source-review-plan.json"))

    result = audit_mod.source_review(package, targets, plan, provider=provider, synthetic_provider=True)

    assert result["reviewer"] == {"exact_model": audit_mod.MODEL, "model_family": "anthropic", "harness": "agy"}


def test_multibatch_provider_review_has_exact_complete_union_and_bound_receipts(tmp_path, monkeypatch):
    package, plan, targets = _multibatch_review_fixture(tmp_path)
    provider = tmp_path / "reviewer.py"
    provider.write_text(FAKE_REVIEWER, encoding="utf-8")
    provider.chmod(0o700)
    calls = tmp_path / "calls"
    monkeypatch.setenv("CYCLE007_AUDIT_CALLS", str(calls))
    monkeypatch.setenv("CYCLE007_AUDIT_PLAN", str(package / audit_mod.OUTPUT / "source-review-plan.json"))

    result = audit_mod.source_review(package, targets, plan, provider=provider, synthetic_provider=True)

    assert calls.read_text() == "2"
    assert result["review_batch_count"] == 2
    batch_receipts = [
        json.loads((package / audit_mod.OUTPUT / f"source-review-batch-receipt-{index:04d}.json").read_text())
        for index in (1, 2)
    ]
    assert result["review_batch_receipt_union_sha256"] == audit_mod.digest(audit_mod.canonical([item["receipt_sha256"] for item in batch_receipts]))
    assert all(item["source_review_plan_sha256"] == plan["source_review_plan_sha256"] for item in batch_receipts)
    assert all(item["evidence_manifest_raw_sha256"] == "0" * 64 for item in batch_receipts)
    sealed_plan = json.loads((package / audit_mod.OUTPUT / "source-review-plan.json").read_text())
    assert sealed_plan["targets"] and all("targets" not in descriptor for descriptor in sealed_plan["batches"])
    assert sum(descriptor["target_count"] for descriptor in sealed_plan["batches"]) == len(sealed_plan["targets"])


def test_missing_second_batch_result_stops_without_silent_completion(tmp_path, monkeypatch):
    package, plan, targets = _multibatch_review_fixture(tmp_path)
    provider = tmp_path / "reviewer.py"
    provider.write_text(FAKE_REVIEWER, encoding="utf-8")
    provider.chmod(0o700)
    calls = tmp_path / "calls"
    monkeypatch.setenv("CYCLE007_AUDIT_CALLS", str(calls))
    monkeypatch.setenv("CYCLE007_AUDIT_MODE", "missing_second")

    with pytest.raises(audit_mod.Error) as exc:
        audit_mod.source_review(package, targets, plan, provider=provider, synthetic_provider=True)

    assert exc.value.failure_code == "incomplete_risk_review"
    assert calls.read_text() == "2"
    assert (package / audit_mod.OUTPUT / "provider-stop.json").is_file()


def test_duplicate_identity_across_review_batches_is_terminal(tmp_path):
    package, plan, targets = _multibatch_review_fixture(tmp_path)
    payload = _passing_reviews(targets)
    payload["reviews"][1] = dict(payload["reviews"][0])

    with pytest.raises(audit_mod.Error) as exc:
        audit_mod.source_review(package, targets, plan, synthetic_provider=True, fixture_override=payload)

    assert exc.value.failure_code == "review_identity_drift"
    assert (package / audit_mod.OUTPUT / "provider-stop.json").is_file()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
