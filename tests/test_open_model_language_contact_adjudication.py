"""Contracts and behavior for real language-contact blind adjudication."""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import language_contact_adjudication as workflow

ROOT = Path(__file__).resolve().parents[1]


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _candidate(
    index: int,
    *,
    category: str,
    period: str = "modern",
    register: str = "reference",
    discourse_role: str = "narration",
) -> tuple[dict[str, Any], str]:
    core = f"форма{index}"
    text = f"Контекст містить {core} для незалежної перевірки."
    start = 100 * index
    core_local_start = text.index(core)
    r2u_lookups = []
    ru_tokens = []
    if category in {
        "modern_narration_interference",
        "mixed_surzhyk_candidate",
        "ukrainian_phonetic_russian",
    }:
        r2u_lookups = [{"query": core, "status": "miss"}]
        ru_tokens = [{"confidence": 0.9, "lemma": core, "token": core}]
    value = {
        "automatic_error_label": False,
        "classification": {
            "category": category,
            "confidence": "low",
            "discourse_role": discourse_role,
            "downstream_disposition": (
                "protected_historical_or_register_variation"
                if category in {"historical_unresolved", "protected_authentic_ukrainian"}
                else "human_review_required"
            ),
            "language_identity": (
                "historical_east_slavic_unresolved"
                if category == "historical_unresolved"
                else ("other_language" if category == "other_language" else "uncertain")
            ),
            "representation": ("ocr_or_encoding_candidate" if category == "ocr_or_encoding_candidate" else "unknown"),
        },
        "evidence": {
            "external_pending": [
                {
                    "adapter_id": "fixture.ulif",
                    "dictionary_identity": "ULIF pending",
                    "status": "not_queried",
                },
                {
                    "adapter_id": "fixture.slovnyk",
                    "dictionary_identity": "dictionary pending",
                    "status": "lookup_pending",
                },
            ],
            "heritage": {"adapter_id": "fixture.heritage", "lookups": [], "status": "used"},
            "network_performed": False,
            "r2u": {
                "adapter_id": "fixture.r2u",
                "cache_id": "fixture-cache",
                "lookups": r2u_lookups,
                "status": "used",
            },
            "reconstruction_candidates": [],
            "russian_morphology": {
                "adapter_id": "fixture.ru",
                "status": "used",
                "tokens": ru_tokens,
            },
            "valid_word_routes": (
                [{"evidence_key": "fixture:valid-word", "route_type": "vetted_semantic_calque"}]
                if category == "valid_word_contact_candidate"
                else []
            ),
            "vesum": {
                "adapter_id": "fixture.vesum",
                "snapshot_id": "fixture-vesum",
                "status": "used",
                "tokens": [{"analyses": [], "surface": core}],
            },
        },
        "locator": f"sqlite:data/sources.db#wikipedia/{index}",
        "metadata": {
            "origin": "human_authored_source",
            "period": period,
            "register": register,
        },
        "queue_route": "unresolved_review",
        "record_hash": _hash(text),
        "record_id": str(index),
        "review_state": "unresolved",
        "schema_version": "language_contact_candidate_v1",
        "source_family": "wikipedia",
        "source_record_id": f"db.wikipedia:{index}",
        "span": {
            "boundary_kind": "sentence",
            "core_end_char": start + core_local_start + len(core),
            "core_start_char": start + core_local_start,
            "end_char": start + len(text),
            "max_chars": 240,
            "original_text": text,
            "span_hash": _hash(text),
            "start_char": start,
        },
    }
    Draft202012Validator(json.loads(workflow.DETECTOR_CANDIDATE_SCHEMA.read_text())).validate(value)
    return value, text


def _write_candidates(path: Path, candidates: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(_canonical(candidate) + "\n" for candidate in candidates),
        encoding="utf-8",
    )


def _detector_receipt(path: Path, candidates_path: Path, records: int) -> dict[str, Any]:
    source_count = {"wikipedia": records}
    category_count: dict[str, int] = {}
    period_count: dict[str, int] = {}
    register_count: dict[str, int] = {}
    for row in workflow.iter_jsonl(candidates_path):
        for target, key in (
            (category_count, row["classification"]["category"]),
            (period_count, row["metadata"]["period"]),
            (register_count, row["metadata"]["register"]),
        ):
            target[key] = target.get(key, 0) + 1
    value = {
        "candidate_arithmetic": {
            "modern_interference_candidates": 0,
            "other_routes": 0,
            "protected_rescues": 0,
            "queue_route_counts": {"unresolved_review": records},
            "quoted_russian": 0,
            "total_candidates": records,
            "unresolved_review_queue": records,
        },
        "claims": {
            "correction_gold_created": False,
            "precision_or_recall_claimed": False,
            "source_admission_changed": False,
            "training_or_publication_performed": False,
        },
        "coverage": {
            "complete": True,
            "dropped_lexical_words": 0,
            "dropped_rows": 0,
            "expected_lexical_words": records,
            "expected_rows": records,
            "inaccessible_sources": [],
            "processed_lexical_words": records,
            "processed_rows": records,
            "source_results": [
                {
                    "actual": {"lexical_words": records, "rows": records},
                    "expected": {"lexical_words": records, "rows": records},
                    "inventory_asset_id": "db.wikipedia",
                    "matches_expected": True,
                    "source_family": "wikipedia",
                }
            ],
        },
        "detector_id": "fixture-language-contact",
        "determinism": {
            "candidate_order": "fixture order",
            "runtime_and_rss_omitted": True,
            "serialization": "canonical JSONL",
            "timestamps_omitted": True,
        },
        "deterministic_sample_locators": ["fixture:one"],
        "evidence_source_usage": {},
        "offsets_rejected": 0,
        "outputs": {
            "review_candidates": {
                "bytes": candidates_path.stat().st_size,
                "records": records,
                "sha256": workflow.sha256_file(candidates_path),
            }
        },
        "prefilter": {"rows_with_signal": records, "rows_without_signal": 0},
        "schema_version": "language_contact_receipt_v1",
        "source_snapshot_id": "fixture-snapshot",
        "yields_by_category": category_count,
        "yields_by_period": period_count,
        "yields_by_register": register_count,
        "yields_by_source_family": source_count,
    }
    Draft202012Validator(json.loads(workflow.DETECTOR_RECEIPT_SCHEMA.read_text())).validate(value)
    path.write_text(_canonical(value) + "\n", encoding="utf-8")
    return value


def _approved_plan(frame_receipt: dict[str, Any], *, salt_a: str, salt_b: str) -> dict[str, Any]:
    strata_counts = frame_receipt["counts"]["by_stratum"]
    return {
        "approval": {
            "approved_at": "2026-08-01T12:00:00Z",
            "issue_url": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6168",
            "operator_id": "operator.fixture",
            "rationale": "Synthetic test-only capacity and thresholds.",
            "status": "approved",
        },
        "frame_sha256": frame_receipt["logical_frame_artifact"]["sha256"],
        "packet_controls": {
            "first_pass_packet_salt_sha256": [
                workflow.sha256_text(salt_a),
                workflow.sha256_text(salt_b),
            ]
        },
        "plan_id": "plan.fixture-001",
        "reviewer_capacity": {
            "evidence": "Synthetic fixture only.",
            "first_pass_reviewer_ids": ["reviewer.fixture-a", "reviewer.fixture-b"],
            "hours_per_person_per_wave": 1,
            "items_per_hour": 100,
            "source": "Synthetic fixture.",
            "third_resolver_id": "reviewer.fixture-c",
        },
        "schema_version": "language_contact_sampling_plan_v1",
        "statistical_stop": {
            "category_coverage_rule": {"minimum_reviewed_per_stratum": 1},
            "confidence_level": 0.95,
            "consecutive_stable_waves": 2,
            "interval_method": "wilson",
            "learning_curve_rule": {
                "maximum_consecutive_wave_change": 1.0,
                "metric": "correction_yield_rate",
            },
            "maximum_consecutive_wave_change": 1.0,
            "maximum_interval_width": 1.0,
            "stability_metric": "per_stratum_adjudicative_core_agreement_rate",
        },
        "strata": [
            {
                "calibration_target": 1,
                "observed_frame_count": strata_counts[stratum],
                "production_target": 1,
                "rationale": "Synthetic fixture coverage.",
                "stratum_id": stratum,
            }
            for stratum in workflow.STRATA
        ],
    }


def _source_db(root: Path, rows: list[tuple[int, str]]) -> None:
    database = root / "data/sources.db"
    database.parent.mkdir(parents=True)
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE wikipedia (id INTEGER PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL DEFAULT '', text TEXT NOT NULL DEFAULT '', char_count INTEGER DEFAULT 0, fetched_at TEXT NOT NULL DEFAULT '')"
    )
    connection.executemany(
        "INSERT INTO wikipedia(id, title, text, char_count) VALUES (?, ?, ?, ?)",
        [(index, f"Стаття {index}", text, len(text)) for index, text in rows],
    )
    connection.commit()
    connection.close()


def _response(
    item: dict[str, Any],
    *,
    reviewer_id: str,
    decision: str = "acceptable_as_is",
) -> dict[str, Any]:
    projection = {
        "accepted_correction": None,
        "acceptable_alternatives": [],
        "citations": [
            {
                "content_sha256": None,
                "locator": "fixture:dictionary-entry",
                "source_identity": "Fixture Ukrainian dictionary",
                "source_kind": "dictionary",
                "supports": "Synthetic test evidence only.",
            }
        ],
        "decision": decision,
        "discourse_role": "narration",
        "language_identity": "ukrainian" if decision != "unresolved" else "uncertain",
        "rationale": "Synthetic qualified-human response contract fixture.",
        "representation": "standard_orthography" if decision != "unresolved" else "unknown",
        "uncertainty": ["synthetic fixture"],
        "views": {
            "correction": "not_applicable" if decision != "unresolved" else "unresolved",
            "evaluation": "excluded_from_non_evaluation_views",
            "faithful_literary": "retain_original",
            "modern_literary_ukrainian": "retain_original" if decision != "unresolved" else "unresolved",
            "preference": "not_applicable" if decision != "unresolved" else "unresolved",
        },
    }
    return {
        "candidate_id": item["candidate_id"],
        "candidate_sha256": item["candidate_sha256"],
        "item_id": item["item_id"],
        "packet_id": item["packet_id"],
        "process": {
            "completed_at": "2026-08-01T12:01:00Z",
            "detector_output_exposed": False,
            "duration_seconds": 60,
            "evidence_viewed": ["Fixture Ukrainian dictionary"],
            "prior_reviewer_output_exposed": False,
            "started_at": "2026-08-01T12:00:00Z",
        },
        "projection": projection,
        "reviewer": {
            "human": True,
            "independence_attested": True,
            "qualification_evidence": "Synthetic test qualification evidence.",
            "reviewer_id": reviewer_id,
            "test_fixture": False,
            "ukrainian_qualification": "qualified_ukrainian_language_reviewer",
        },
        "schema_version": "language_contact_blind_response_v1",
    }


@pytest.fixture
def corpus(tmp_path: Path) -> dict[str, Any]:
    base_specifications = [
        ("modern_narration_interference", "modern", "reference", "narration"),
        ("valid_word_contact_candidate", "modern", "reference", "narration"),
        ("protected_authentic_ukrainian", "modern", "reference", "narration"),
        ("historical_unresolved", "middle_ukrainian", "literary", "narration"),
        ("uncertain", "modern", "scripted", "dialogue"),
        ("russian_quotation", "modern", "literary", "quotation"),
        ("other_language", "modern", "reference", "quotation"),
        ("ocr_or_encoding_candidate", "modern", "reference", "narration"),
        ("proper_name", "modern", "reference", "narration"),
        ("mixed_surzhyk_candidate", "modern", "reference", "narration"),
    ]
    specifications = base_specifications * 4
    candidates: list[dict[str, Any]] = []
    sources: list[tuple[int, str]] = []
    for index, (category, period, register, role) in enumerate(specifications, 1):
        candidate, text = _candidate(
            index,
            category=category,
            period=period,
            register=register,
            discourse_role=role,
        )
        candidates.append(candidate)
        sources.append((index, text))
    candidates_path = tmp_path / "candidates.jsonl"
    receipt_path = tmp_path / "detector-receipt.json"
    _write_candidates(candidates_path, candidates)
    _detector_receipt(receipt_path, candidates_path, len(candidates))
    _source_db(tmp_path / "input", sources)
    return {
        "candidates": candidates_path,
        "detector_receipt": receipt_path,
        "input_root": tmp_path / "input",
    }


def test_contract_schemas_are_valid() -> None:
    for path in (
        workflow.FRAME_ITEM_SCHEMA,
        workflow.FRAME_RECEIPT_SCHEMA,
        workflow.SAMPLING_PLAN_SCHEMA,
        workflow.BLIND_ITEM_SCHEMA,
        workflow.BLIND_RESPONSE_SCHEMA,
        workflow.WAVE_RECEIPT_SCHEMA,
        workflow.FIRST_PASS_SUMMARY_SCHEMA,
        workflow.CAMPAIGN_RECEIPT_SCHEMA,
        workflow.RESOLVER_ITEM_SCHEMA,
        workflow.RESOLVER_RESPONSE_SCHEMA,
        workflow.GOLD_FREEZE_RECEIPT_SCHEMA,
    ):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))


def test_packet_salt_files_must_be_private(tmp_path: Path) -> None:
    secret = tmp_path / "packet.salt"
    secret.write_text("fixture-secret\n", encoding="utf-8")
    secret.chmod(0o644)
    with pytest.raises(workflow.AdjudicationError, match="deny group/other"):
        workflow.read_secret(secret)
    secret.chmod(0o600)
    assert workflow.read_secret(secret) == "fixture-secret"


def test_build_frame_is_text_free_deterministic_and_complete(tmp_path: Path, corpus: dict[str, Any]) -> None:
    outputs = []
    for suffix in ("a", "b"):
        frame = tmp_path / f"frame-{suffix}.jsonl"
        receipt = tmp_path / f"frame-{suffix}.json"
        value = workflow.build_frame(
            candidates_path=corpus["candidates"],
            detector_receipt_path=corpus["detector_receipt"],
            frame_output=frame,
            receipt_output=receipt,
        )
        outputs.append((frame, receipt, value))
    assert outputs[0][0].read_bytes() == outputs[1][0].read_bytes()
    assert outputs[0][1].read_bytes() == outputs[1][1].read_bytes()
    rows = list(workflow.iter_jsonl(outputs[0][0]))
    assert len(rows) == 40
    assert all("text" not in row for row in rows)
    assert set(outputs[0][2]["counts"]["by_stratum"]) == set(workflow.STRATA)


def test_build_frame_rejects_tampering_and_preserves_existing_output(tmp_path: Path, corpus: dict[str, Any]) -> None:
    frame = tmp_path / "frame.jsonl"
    receipt = tmp_path / "frame.json"
    frame.write_text("keep-frame\n", encoding="utf-8")
    receipt.write_text("keep-receipt\n", encoding="utf-8")
    candidates = corpus["candidates"]
    original = candidates.read_text(encoding="utf-8")
    candidates.write_text(original + "{}\n", encoding="utf-8")
    with pytest.raises(workflow.AdjudicationError, match="byte count differs"):
        workflow.build_frame(
            candidates_path=candidates,
            detector_receipt_path=corpus["detector_receipt"],
            frame_output=frame,
            receipt_output=receipt,
        )
    assert frame.read_text(encoding="utf-8") == "keep-frame\n"
    assert receipt.read_text(encoding="utf-8") == "keep-receipt\n"


def test_atomic_promotion_restores_outputs_and_cleans_reserved_backups(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_a, output_b = tmp_path / "a.json", tmp_path / "b.json"
    temporary_a, temporary_b = tmp_path / "new-a.tmp", tmp_path / "new-b.tmp"
    output_a.write_text("old-a", encoding="utf-8")
    output_b.write_text("old-b", encoding="utf-8")
    temporary_a.write_text("new-a", encoding="utf-8")
    temporary_b.write_text("new-b", encoding="utf-8")
    real_replace = workflow.os.replace

    def fail_second_backup(source: Path, destination: Path) -> None:
        if Path(source) == output_b:
            raise OSError("injected backup failure")
        real_replace(source, destination)

    monkeypatch.setattr(workflow.os, "replace", fail_second_backup)
    with pytest.raises(OSError, match="injected backup failure"):
        workflow._promote_outputs(((temporary_a, output_a), (temporary_b, output_b)))
    assert output_a.read_text(encoding="utf-8") == "old-a"
    assert output_b.read_text(encoding="utf-8") == "old-b"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["a.json", "b.json"]


def test_pending_plan_and_salt_mismatch_fail_closed(tmp_path: Path, corpus: dict[str, Any]) -> None:
    frame, frame_receipt_path = tmp_path / "frame.jsonl", tmp_path / "frame.json"
    receipt = workflow.build_frame(
        candidates_path=corpus["candidates"],
        detector_receipt_path=corpus["detector_receipt"],
        frame_output=frame,
        receipt_output=frame_receipt_path,
    )
    plan = _approved_plan(receipt, salt_a="salt-a", salt_b="salt-b")
    plan["approval"] = {
        "approved_at": None,
        "issue_url": plan["approval"]["issue_url"],
        "operator_id": None,
        "rationale": "Operator capacity and statistical stop rule are pending.",
        "status": "pending",
    }
    plan["reviewer_capacity"] = None
    plan["statistical_stop"] = None
    plan["packet_controls"] = None
    for row in plan["strata"]:
        row["calibration_target"] = None
        row["production_target"] = None
    plan_path = tmp_path / "pending.json"
    plan_path.write_text(_canonical(plan), encoding="utf-8")
    with pytest.raises(workflow.AdjudicationError, match="not approved"):
        workflow._select_frame_items(frame, plan=plan, stage="calibration")


def test_draft_plan_retains_measured_yields_but_invents_no_targets(tmp_path: Path, corpus: dict[str, Any]) -> None:
    frame, frame_receipt_path = tmp_path / "frame.jsonl", tmp_path / "frame.json"
    receipt = workflow.build_frame(
        candidates_path=corpus["candidates"],
        detector_receipt_path=corpus["detector_receipt"],
        frame_output=frame,
        receipt_output=frame_receipt_path,
    )
    plan_path = tmp_path / "pending-plan.json"
    plan = workflow.draft_sampling_plan(
        frame_receipt_path=frame_receipt_path,
        plan_output=plan_path,
        plan_id="plan.pending-fixture",
        issue_url="https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6168",
    )
    assert plan["approval"]["status"] == "pending"
    assert plan["reviewer_capacity"] is None
    assert plan["statistical_stop"] is None
    assert all(row["calibration_target"] is None for row in plan["strata"])
    observed = {row["stratum_id"]: row["observed_frame_count"] for row in plan["strata"]}
    assert observed == receipt["counts"]["by_stratum"]


def test_prepare_wave_is_blind_capacity_bound_and_factory_valid(tmp_path: Path, corpus: dict[str, Any]) -> None:
    frame, frame_receipt_path = tmp_path / "frame.jsonl", tmp_path / "frame.json"
    frame_receipt = workflow.build_frame(
        candidates_path=corpus["candidates"],
        detector_receipt_path=corpus["detector_receipt"],
        frame_output=frame,
        receipt_output=frame_receipt_path,
    )
    salt_a, salt_b = "reviewer-a-private-order", "reviewer-b-private-order"
    plan = _approved_plan(frame_receipt, salt_a=salt_a, salt_b=salt_b)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(_canonical(plan), encoding="utf-8")
    outputs = {
        name: tmp_path / filename
        for name, filename in {
            "selected": "selected.jsonl",
            "correction": "correction.jsonl",
            "blind_a": "blind-a.jsonl",
            "blind_b": "blind-b.jsonl",
            "workspace_a": "workspace-a.html",
            "workspace_b": "workspace-b.html",
            "receipt": "wave.json",
        }.items()
    }
    receipt = workflow.prepare_wave(
        candidates_path=corpus["candidates"],
        detector_receipt_path=corpus["detector_receipt"],
        frame_path=frame,
        frame_receipt_path=frame_receipt_path,
        plan_path=plan_path,
        input_root=corpus["input_root"],
        stage="calibration",
        wave_number=1,
        prior_wave_receipt_paths=[],
        prior_selected_manifest_paths=[],
        salt_a=salt_a,
        salt_b=salt_b,
        selected_output=outputs["selected"],
        correction_output=outputs["correction"],
        blind_a_output=outputs["blind_a"],
        blind_b_output=outputs["blind_b"],
        workspace_a_output=outputs["workspace_a"],
        workspace_b_output=outputs["workspace_b"],
        receipt_output=outputs["receipt"],
    )
    blind_a = list(workflow.iter_jsonl(outputs["blind_a"]))
    blind_b = list(workflow.iter_jsonl(outputs["blind_b"]))
    assert {row["candidate_id"] for row in blind_a} == {row["candidate_id"] for row in blind_b}
    assert [row["candidate_id"] for row in blind_a] != [row["candidate_id"] for row in blind_b]
    serialized = outputs["blind_a"].read_text(encoding="utf-8")
    for forbidden in ("classification", "queue_route", "confidence", "automatic_error_label"):
        assert forbidden not in serialized
    assert "Українська експертна перевірка" in outputs["workspace_a"].read_text(encoding="utf-8")
    workspace = outputs["workspace_a"].read_text(encoding="utf-8")
    assert "language_contact_blind_response_v1" in workspace
    assert "reviewer.fixture-a" in workspace
    assert "detector_output_exposed:false" in workspace
    assert receipt["claims"] == {
        "gold_created": False,
        "labels_created": False,
        "publication_performed": False,
        "training_performed": False,
    }
    assert receipt["human_review_gate"]["human_review_completed"] is False
    assert receipt["stage"] == "calibration"
    assert receipt["wave_number"] == 1
    assert receipt["prior_waves"] == []
    assert list(workflow.iter_jsonl(outputs["correction"]))

    production_outputs = {
        name: tmp_path / f"production-{filename}"
        for name, filename in {
            "selected": "selected.jsonl",
            "correction": "correction.jsonl",
            "blind_a": "blind-a.jsonl",
            "blind_b": "blind-b.jsonl",
            "workspace_a": "workspace-a.html",
            "workspace_b": "workspace-b.html",
            "receipt": "wave.json",
        }.items()
    }
    production_receipt = workflow.prepare_wave(
        candidates_path=corpus["candidates"],
        detector_receipt_path=corpus["detector_receipt"],
        frame_path=frame,
        frame_receipt_path=frame_receipt_path,
        plan_path=plan_path,
        input_root=corpus["input_root"],
        stage="production",
        wave_number=1,
        prior_wave_receipt_paths=[outputs["receipt"]],
        prior_selected_manifest_paths=[outputs["selected"]],
        salt_a=salt_a,
        salt_b=salt_b,
        selected_output=production_outputs["selected"],
        correction_output=production_outputs["correction"],
        blind_a_output=production_outputs["blind_a"],
        blind_b_output=production_outputs["blind_b"],
        workspace_a_output=production_outputs["workspace_a"],
        workspace_b_output=production_outputs["workspace_b"],
        receipt_output=production_outputs["receipt"],
    )
    calibration_ids = {row["candidate_id"] for row in workflow.iter_jsonl(outputs["selected"])}
    production_ids = {row["candidate_id"] for row in workflow.iter_jsonl(production_outputs["selected"])}
    assert calibration_ids.isdisjoint(production_ids)
    assert production_receipt["prior_waves"][0]["stage"] == "calibration"
    assert production_receipt["prior_waves"][0]["wave_number"] == 1
    with pytest.raises(workflow.AdjudicationError, match="calibration wave chain"):
        workflow.prepare_wave(
            candidates_path=corpus["candidates"],
            detector_receipt_path=corpus["detector_receipt"],
            frame_path=frame,
            frame_receipt_path=frame_receipt_path,
            plan_path=plan_path,
            input_root=corpus["input_root"],
            stage="production",
            wave_number=1,
            prior_wave_receipt_paths=[],
            prior_selected_manifest_paths=[],
            salt_a=salt_a,
            salt_b=salt_b,
            selected_output=production_outputs["selected"],
            correction_output=production_outputs["correction"],
            blind_a_output=production_outputs["blind_a"],
            blind_b_output=production_outputs["blind_b"],
            workspace_a_output=production_outputs["workspace_a"],
            workspace_b_output=production_outputs["workspace_b"],
            receipt_output=production_outputs["receipt"],
        )

    responses_a = [_response(item, reviewer_id="reviewer.fixture-a") for item in blind_a]
    responses_b = [_response(item, reviewer_id="reviewer.fixture-b") for item in blind_b]
    evidence_wording_candidate = responses_b[0]["candidate_id"]
    responses_b[0]["projection"]["rationale"] = "Independent Ukrainian rationale wording."
    responses_b[-1]["projection"]["decision"] = "unresolved"
    responses_b[-1]["projection"]["language_identity"] = "uncertain"
    responses_b[-1]["projection"]["representation"] = "unknown"
    responses_b[-1]["projection"]["views"] = {
        "correction": "unresolved",
        "evaluation": "excluded_from_non_evaluation_views",
        "faithful_literary": "retain_original",
        "modern_literary_ukrainian": "unresolved",
        "preference": "unresolved",
    }
    responses_a_path = tmp_path / "responses-a.jsonl"
    responses_b_path = tmp_path / "responses-b.jsonl"
    _write_candidates(responses_a_path, responses_a)
    _write_candidates(responses_b_path, responses_b)
    decisions_path = tmp_path / "decisions.jsonl"
    summary_path = tmp_path / "first-pass-summary.json"
    summary = workflow.assemble_first_pass_decisions(
        plan_path=plan_path,
        stage="calibration",
        wave_number=1,
        wave_receipt_path=outputs["receipt"],
        selected_manifest_path=outputs["selected"],
        correction_packet_path=outputs["correction"],
        blind_a_path=outputs["blind_a"],
        blind_b_path=outputs["blind_b"],
        responses_a_path=responses_a_path,
        responses_b_path=responses_b_path,
        decisions_output=decisions_path,
        summary_output=summary_path,
    )
    decisions = list(workflow.iter_jsonl(decisions_path))
    assert len(decisions) == len(blind_a)
    assert summary["decision_counts"]["unresolved_conflict"] == 1
    assert summary["first_pass_review_completed"] is True
    assert summary["all_conflicts_resolved"] is False
    assert set(summary["per_stratum"]) == set(workflow.STRATA)
    assert sum(row["reviewed"] for row in summary["per_stratum"].values()) >= len(blind_a)
    assert summary["overall"]["conflict_rate"]["numerator"] == 1
    assert summary["overall"]["conflict_rate"]["interval"]["method"] == "wilson"
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary
    assert sum(item["final_resolution"]["kind"] == "unresolved_conflict" for item in decisions) == 1
    evidence_merged = next(row for row in decisions if row["candidate_id"] == evidence_wording_candidate)
    assert evidence_merged["final_resolution"]["kind"] == "first_pass_agreement"
    assert "Первинний рецензент A:" in evidence_merged["final"]["rationale"]
    resolver_packet = tmp_path / "resolver-packet.jsonl"
    resolver_workspace = tmp_path / "resolver-workspace.html"
    resolver_receipt = workflow.prepare_resolver_packet(
        plan_path=plan_path,
        stage="calibration",
        wave_number=1,
        wave_receipt_path=outputs["receipt"],
        first_pass_summary_path=summary_path,
        decisions_path=decisions_path,
        blind_a_path=outputs["blind_a"],
        packet_output=resolver_packet,
        workspace_output=resolver_workspace,
    )
    assert resolver_receipt["conflicts"] == 1
    assert "Українське вирішення розбіжностей" in resolver_workspace.read_text(encoding="utf-8")
    assert "prior_reviewer_output_exposed:RESOLVER" in resolver_workspace.read_text(encoding="utf-8")
    resolver_items = list(workflow.iter_jsonl(resolver_packet))
    resolver_responses = []
    for item in resolver_items:
        response = _response(item, reviewer_id="reviewer.fixture-c")
        response["schema_version"] = "language_contact_resolver_response_v1"
        response["process"]["prior_reviewer_output_exposed"] = True
        resolver_responses.append(response)
    resolver_responses_path = tmp_path / "resolver-responses.jsonl"
    _write_candidates(resolver_responses_path, resolver_responses)
    resolved_decisions_path = tmp_path / "resolved-decisions.jsonl"
    resolution_summary_path = tmp_path / "resolution-summary.json"
    resolution_summary = workflow.resolve_conflicts(
        plan_path=plan_path,
        packet_path=resolver_packet,
        responses_path=resolver_responses_path,
        decisions_path=decisions_path,
        correction_packet_path=outputs["correction"],
        decisions_output=resolved_decisions_path,
        summary_output=resolution_summary_path,
    )
    assert resolution_summary["counts"]["third_human_adjudication"] == 1
    assert any(
        row["final_resolution"]["kind"] == "third_human_adjudication"
        for row in workflow.iter_jsonl(resolved_decisions_path)
    )

    production_responses_a = [
        _response(item, reviewer_id="reviewer.fixture-a")
        for item in workflow.iter_jsonl(production_outputs["blind_a"])
    ]
    production_responses_b = [
        _response(item, reviewer_id="reviewer.fixture-b")
        for item in workflow.iter_jsonl(production_outputs["blind_b"])
    ]
    production_responses_a_path = tmp_path / "production-responses-a.jsonl"
    production_responses_b_path = tmp_path / "production-responses-b.jsonl"
    _write_candidates(production_responses_a_path, production_responses_a)
    _write_candidates(production_responses_b_path, production_responses_b)
    production_decisions_path = tmp_path / "production-decisions.jsonl"
    production_summary_path = tmp_path / "production-summary.json"
    workflow.assemble_first_pass_decisions(
        plan_path=plan_path,
        stage="production",
        wave_number=1,
        wave_receipt_path=production_outputs["receipt"],
        selected_manifest_path=production_outputs["selected"],
        correction_packet_path=production_outputs["correction"],
        blind_a_path=production_outputs["blind_a"],
        blind_b_path=production_outputs["blind_b"],
        responses_a_path=production_responses_a_path,
        responses_b_path=production_responses_b_path,
        decisions_output=production_decisions_path,
        summary_output=production_summary_path,
    )

    production_two_outputs = {
        name: tmp_path / f"production-2-{filename}"
        for name, filename in {
            "selected": "selected.jsonl",
            "correction": "correction.jsonl",
            "blind_a": "blind-a.jsonl",
            "blind_b": "blind-b.jsonl",
            "workspace_a": "workspace-a.html",
            "workspace_b": "workspace-b.html",
            "receipt": "wave.json",
        }.items()
    }
    workflow.prepare_wave(
        candidates_path=corpus["candidates"],
        detector_receipt_path=corpus["detector_receipt"],
        frame_path=frame,
        frame_receipt_path=frame_receipt_path,
        plan_path=plan_path,
        input_root=corpus["input_root"],
        stage="production",
        wave_number=2,
        prior_wave_receipt_paths=[outputs["receipt"], production_outputs["receipt"]],
        prior_selected_manifest_paths=[outputs["selected"], production_outputs["selected"]],
        salt_a=salt_a,
        salt_b=salt_b,
        selected_output=production_two_outputs["selected"],
        correction_output=production_two_outputs["correction"],
        blind_a_output=production_two_outputs["blind_a"],
        blind_b_output=production_two_outputs["blind_b"],
        workspace_a_output=production_two_outputs["workspace_a"],
        workspace_b_output=production_two_outputs["workspace_b"],
        receipt_output=production_two_outputs["receipt"],
    )
    production_two_ids = {
        row["candidate_id"] for row in workflow.iter_jsonl(production_two_outputs["selected"])
    }
    assert production_two_ids.isdisjoint(calibration_ids | production_ids)
    production_two_responses_a = [
        _response(item, reviewer_id="reviewer.fixture-a")
        for item in workflow.iter_jsonl(production_two_outputs["blind_a"])
    ]
    production_two_responses_b = [
        _response(item, reviewer_id="reviewer.fixture-b")
        for item in workflow.iter_jsonl(production_two_outputs["blind_b"])
    ]
    production_two_responses_a_path = tmp_path / "production-2-responses-a.jsonl"
    production_two_responses_b_path = tmp_path / "production-2-responses-b.jsonl"
    _write_candidates(production_two_responses_a_path, production_two_responses_a)
    _write_candidates(production_two_responses_b_path, production_two_responses_b)
    production_two_decisions_path = tmp_path / "production-2-decisions.jsonl"
    production_two_summary_path = tmp_path / "production-2-summary.json"
    workflow.assemble_first_pass_decisions(
        plan_path=plan_path,
        stage="production",
        wave_number=2,
        wave_receipt_path=production_two_outputs["receipt"],
        selected_manifest_path=production_two_outputs["selected"],
        correction_packet_path=production_two_outputs["correction"],
        blind_a_path=production_two_outputs["blind_a"],
        blind_b_path=production_two_outputs["blind_b"],
        responses_a_path=production_two_responses_a_path,
        responses_b_path=production_two_responses_b_path,
        decisions_output=production_two_decisions_path,
        summary_output=production_two_summary_path,
    )
    campaign_path = tmp_path / "campaign.json"
    campaign = workflow.summarize_campaign(
        plan_path=plan_path,
        first_pass_summary_paths=[summary_path, production_summary_path, production_two_summary_path],
        wave_receipt_paths=[
            outputs["receipt"],
            production_outputs["receipt"],
            production_two_outputs["receipt"],
        ],
        output_path=campaign_path,
    )
    assert campaign["production_wave_count"] == 2
    assert campaign["stop_evaluation"]["stop_eligible"] is True
    assert campaign["claims"]["gold_frozen"] is False

    def resolve_agreement_wave(
        *,
        prefix: str,
        wave_number: int,
        wave_outputs: dict[str, Path],
        first_pass_decisions: Path,
        first_pass_summary: Path,
    ) -> tuple[Path, Path, Path, Path]:
        packet = tmp_path / f"{prefix}-resolver-packet.jsonl"
        workspace_path = tmp_path / f"{prefix}-resolver.html"
        workflow.prepare_resolver_packet(
            plan_path=plan_path,
            stage="production",
            wave_number=wave_number,
            wave_receipt_path=wave_outputs["receipt"],
            first_pass_summary_path=first_pass_summary,
            decisions_path=first_pass_decisions,
            blind_a_path=wave_outputs["blind_a"],
            packet_output=packet,
            workspace_output=workspace_path,
        )
        assert packet.read_bytes() == b""
        resolver_response = tmp_path / f"{prefix}-resolver-responses.jsonl"
        resolver_response.write_bytes(b"")
        final_decisions = tmp_path / f"{prefix}-final-decisions.jsonl"
        resolution_summary = tmp_path / f"{prefix}-resolution-summary.json"
        workflow.resolve_conflicts(
            plan_path=plan_path,
            packet_path=packet,
            responses_path=resolver_response,
            decisions_path=first_pass_decisions,
            correction_packet_path=wave_outputs["correction"],
            decisions_output=final_decisions,
            summary_output=resolution_summary,
        )
        return packet, resolver_response, resolution_summary, final_decisions

    production_resolver = resolve_agreement_wave(
        prefix="production-1",
        wave_number=1,
        wave_outputs=production_outputs,
        first_pass_decisions=production_decisions_path,
        first_pass_summary=production_summary_path,
    )
    production_two_resolver = resolve_agreement_wave(
        prefix="production-2",
        wave_number=2,
        wave_outputs=production_two_outputs,
        first_pass_decisions=production_two_decisions_path,
        first_pass_summary=production_two_summary_path,
    )
    records_path = tmp_path / "frozen-records.jsonl"
    factory_receipt_path = tmp_path / "frozen-records.factory.json"
    freeze_receipt_path = tmp_path / "gold-freeze.json"
    freeze_receipt = workflow.freeze_gold(
        plan_path=plan_path,
        campaign_receipt_path=campaign_path,
        wave_receipt_paths=[
            outputs["receipt"],
            production_outputs["receipt"],
            production_two_outputs["receipt"],
        ],
        first_pass_summary_paths=[summary_path, production_summary_path, production_two_summary_path],
        responses_a_paths=[responses_a_path, production_responses_a_path, production_two_responses_a_path],
        responses_b_paths=[responses_b_path, production_responses_b_path, production_two_responses_b_path],
        resolver_packet_paths=[resolver_packet, production_resolver[0], production_two_resolver[0]],
        resolver_responses_paths=[
            resolver_responses_path,
            production_resolver[1],
            production_two_resolver[1],
        ],
        resolution_summary_paths=[
            resolution_summary_path,
            production_resolver[2],
            production_two_resolver[2],
        ],
        correction_packet_paths=[
            outputs["correction"],
            production_outputs["correction"],
            production_two_outputs["correction"],
        ],
        final_decisions_paths=[
            resolved_decisions_path,
            production_resolver[3],
            production_two_resolver[3],
        ],
        records_output=records_path,
        factory_receipt_output=factory_receipt_path,
        freeze_receipt_output=freeze_receipt_path,
    )
    assert freeze_receipt["claims"]["gold_frozen"] is True
    assert freeze_receipt["claims"]["model_training_or_export_eligible"] is False
    assert freeze_receipt["totals"]["calibration_evidence_non_gold"] > 0
    assert freeze_receipt["totals"]["headline_gold"] > 0
    assert freeze_receipt["totals"]["records"] == sum(1 for _ in workflow.iter_jsonl(records_path))

    preserved = decisions_path.read_bytes()
    preserved_summary = summary_path.read_bytes()
    responses_b[0]["reviewer"]["qualification_evidence"] = "Changed mid-packet."
    _write_candidates(responses_b_path, responses_b)
    with pytest.raises(workflow.AdjudicationError, match="profile changes"):
        workflow.assemble_first_pass_decisions(
            plan_path=plan_path,
            stage="calibration",
            wave_number=1,
            wave_receipt_path=outputs["receipt"],
            selected_manifest_path=outputs["selected"],
            correction_packet_path=outputs["correction"],
            blind_a_path=outputs["blind_a"],
            blind_b_path=outputs["blind_b"],
            responses_a_path=responses_a_path,
            responses_b_path=responses_b_path,
            decisions_output=decisions_path,
            summary_output=summary_path,
        )
    assert decisions_path.read_bytes() == preserved
    assert summary_path.read_bytes() == preserved_summary


def test_sampling_plan_requires_distinct_complete_strata(corpus: dict[str, Any], tmp_path: Path) -> None:
    frame, frame_receipt_path = tmp_path / "frame.jsonl", tmp_path / "frame.json"
    receipt = workflow.build_frame(
        candidates_path=corpus["candidates"],
        detector_receipt_path=corpus["detector_receipt"],
        frame_output=frame,
        receipt_output=frame_receipt_path,
    )
    plan = _approved_plan(receipt, salt_a="a", salt_b="b")
    plan["strata"].append(copy.deepcopy(plan["strata"][0]))
    with pytest.raises(workflow.AdjudicationError, match="exactly once"):
        workflow._approved_targets(plan, "calibration")
