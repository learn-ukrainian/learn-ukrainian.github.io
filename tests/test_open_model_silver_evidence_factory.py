"""Contracts and fail-closed behavior for Foundry non-human silver records."""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import silver_evidence_factory as factory

ROOT = Path(__file__).resolve().parents[1]


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _candidate(
    index: int,
    *,
    category: str,
    text: str | None = None,
    role: str = "narration",
    period: str = "modern",
    register: str = "reference",
    vesum: bool = False,
    russian: bool = False,
    r2u: bool = False,
    heritage: bool = False,
) -> dict[str, Any]:
    core = f"форма{index}"
    context = text or f"Контекст містить {core} для незалежної перевірки срібного запису."
    if core not in context:
        core = context[: min(12, len(context))]
    core_start = context.index(core)
    language_identity = {
        "protected_authentic_ukrainian": "ukrainian",
        "historical_unresolved": "historical_east_slavic_unresolved",
        "russian_quotation": "russian",
        "other_language": "other_language",
    }.get(category, "uncertain")
    downstream = {
        "protected_authentic_ukrainian": "protected_historical_or_register_variation",
        "historical_unresolved": "protected_historical_or_register_variation",
        "russian_quotation": "mask_from_modern_ukrainian_loss",
        "other_language": "retain_with_language_metadata",
        "modern_narration_interference": "correction_candidate",
    }.get(category, "human_review_required")
    value = {
        "schema_version": "language_contact_candidate_v1",
        "source_record_id": f"db.wikipedia:{index}",
        "source_family": "wikipedia",
        "locator": f"sqlite:data/sources.db#wikipedia/{index}",
        "record_id": str(index),
        "record_hash": _sha(context),
        "span": {
            "start_char": 0,
            "end_char": len(context),
            "core_start_char": core_start,
            "core_end_char": core_start + len(core),
            "original_text": context,
            "span_hash": _sha(context),
            "boundary_kind": "sentence",
            "max_chars": 240,
        },
        "classification": {
            "language_identity": language_identity,
            "representation": (
                "historical_orthography"
                if category == "historical_unresolved"
                else (
                    "ocr_or_encoding_candidate" if category == "ocr_or_encoding_candidate" else "standard_orthography"
                )
            ),
            "discourse_role": role,
            "downstream_disposition": downstream,
            "category": category,
            "confidence": "high" if category != "uncertain" else "low",
        },
        "metadata": {
            "period": period,
            "register": register,
            "origin": "human_authored_source",
        },
        "evidence": {
            "vesum": {
                "adapter_id": "fixture.vesum",
                "status": "used",
                "snapshot_id": "fixture-vesum",
                "tokens": [
                    {
                        "surface": core,
                        "analyses": ([{"lemma": core, "pos": "noun", "tags": "fixture"}] if vesum else []),
                    }
                ],
            },
            "russian_morphology": {
                "adapter_id": "fixture.ru",
                "status": "used",
                "tokens": ([{"token": core, "lemma": core, "confidence": 0.95}] if russian else []),
            },
            "r2u": {
                "adapter_id": "fixture.r2u",
                "status": "used",
                "cache_id": "fixture-r2u-cache",
                "lookups": (
                    [
                        {
                            "query": core,
                            "status": "hit",
                            "response_sha256": _sha(core + ":r2u"),
                        }
                    ]
                    if r2u
                    else []
                ),
            },
            "heritage": {
                "adapter_id": "fixture.heritage",
                "status": "used",
                "lookups": (
                    [
                        {
                            "surface": core,
                            "hits": [
                                {
                                    "dictionary_identity": "СУМ-11",
                                    "matched_headword": core,
                                }
                            ],
                        }
                    ]
                    if heritage
                    else []
                ),
            },
            "external_pending": [],
            "reconstruction_candidates": [],
            "valid_word_routes": [],
            "network_performed": False,
        },
        "automatic_error_label": False,
        "review_state": "unresolved",
        "queue_route": {
            "protected_authentic_ukrainian": "protected_rescue",
            "historical_unresolved": "historical_review",
            "russian_quotation": "quoted_russian",
            "modern_narration_interference": "modern_interference_review",
            "ocr_or_encoding_candidate": "technical_review",
        }.get(category, "unresolved_review"),
    }
    Draft202012Validator(json.loads(factory.CANDIDATE_SCHEMA.read_text())).validate(value)
    return value


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(_canonical(row) + "\n" for row in rows), encoding="utf-8")


def _detector_receipt(path: Path, candidates: Path, rows: list[dict[str, Any]]) -> None:
    categories: dict[str, int] = {}
    routes: dict[str, int] = {}
    for row in rows:
        categories[row["classification"]["category"]] = categories.get(row["classification"]["category"], 0) + 1
        routes[row["queue_route"]] = routes.get(row["queue_route"], 0) + 1
    value = {
        "schema_version": "language_contact_receipt_v1",
        "detector_id": "fixture-language-contact",
        "source_snapshot_id": "fixture-snapshot",
        "coverage": {
            "complete": True,
            "expected_rows": len(rows),
            "expected_lexical_words": len(rows),
            "processed_rows": len(rows),
            "processed_lexical_words": len(rows),
            "dropped_rows": 0,
            "dropped_lexical_words": 0,
            "inaccessible_sources": [],
            "source_results": [
                {
                    "source_family": "wikipedia",
                    "inventory_asset_id": "db.wikipedia",
                    "expected": {"rows": len(rows), "lexical_words": len(rows)},
                    "actual": {"rows": len(rows), "lexical_words": len(rows)},
                    "matches_expected": True,
                }
            ],
        },
        "candidate_arithmetic": {
            "total_candidates": len(rows),
            "unresolved_review_queue": routes.get("unresolved_review", 0),
            "protected_rescues": routes.get("protected_rescue", 0),
            "quoted_russian": routes.get("quoted_russian", 0),
            "modern_interference_candidates": routes.get("modern_interference_review", 0),
            "other_routes": 0,
            "queue_route_counts": routes,
        },
        "yields_by_category": categories,
        "yields_by_source_family": {"wikipedia": len(rows)},
        "yields_by_period": {"fixture": len(rows)},
        "yields_by_register": {"fixture": len(rows)},
        "offsets_rejected": 0,
        "prefilter": {"rows_with_signal": len(rows), "rows_without_signal": 0},
        "evidence_source_usage": {},
        "deterministic_sample_locators": [],
        "outputs": {
            "review_candidates": {
                "records": len(rows),
                "bytes": candidates.stat().st_size,
                "sha256": factory.sha256_file(candidates),
            }
        },
        "claims": {
            "correction_gold_created": False,
            "precision_or_recall_claimed": False,
            "source_admission_changed": False,
            "training_or_publication_performed": False,
        },
        "determinism": {
            "serialization": "fixture canonical JSONL",
            "candidate_order": "fixture order",
            "timestamps_omitted": True,
            "runtime_and_rss_omitted": True,
        },
    }
    Draft202012Validator(json.loads(factory.DETECTOR_RECEIPT_SCHEMA.read_text())).validate(value)
    path.write_text(_canonical(value) + "\n", encoding="utf-8")


def _config(path: Path) -> None:
    value = {
        "sources": [
            {
                "source_family": "wikipedia",
                "adapter": {"dimensions": {"genre": {"constant": "encyclopedia"}}},
            }
        ]
    }
    path.write_text(_canonical(value) + "\n", encoding="utf-8")


def _run(
    tmp_path: Path,
    rows: list[dict[str, Any]],
    *,
    observations: list[dict[str, Any]] | None = None,
    suffix: str = "one",
) -> factory.SilverRun:
    candidates = tmp_path / f"candidates-{suffix}.jsonl"
    detector_receipt = tmp_path / f"detector-{suffix}.json"
    config = tmp_path / f"config-{suffix}.json"
    output = tmp_path / f"silver-{suffix}.jsonl"
    receipt = tmp_path / f"silver-{suffix}.receipt.json"
    _write_jsonl(candidates, rows)
    _detector_receipt(detector_receipt, candidates, rows)
    _config(config)
    observation_path = None
    if observations is not None:
        observation_path = tmp_path / f"observations-{suffix}.jsonl"
        _write_jsonl(observation_path, observations)
    return factory.build_silver(
        candidates_path=candidates,
        detector_receipt_path=detector_receipt,
        detector_config_path=config,
        admission_receipt_path=factory.DEFAULT_ADMISSION_RECEIPT,
        operator_packet_path=factory.DEFAULT_OPERATOR_PACKET,
        input_root=tmp_path,
        observations_path=observation_path,
        output_path=output,
        receipt_path=receipt,
    )


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _observation(
    candidate: dict[str, Any],
    *,
    kind: str = "source_evidence",
) -> dict[str, Any]:
    candidate_id = "lcc." + _sha(_canonical(candidate))
    if kind == "source_evidence":
        return {
            "schema_version": "language_contact_silver_observation_v1",
            "observation_id": f"obs.ulif.{_sha(candidate_id)}",
            "candidate_id": candidate_id,
            "kind": "source_evidence",
            "source": "ulif_dictua",
            "source_identity": "ulif_dictua",
            "query": candidate["span"]["original_text"],
            "status": "attested",
            "supports": "alternative_candidate",
            "locator": "https://lcorp.ulif.org.ua/dictua/",
            "parser_status": "ok",
            "parser_version": "fixture-v1",
            "content_sha256": _sha("ulif fixture"),
            "rights_posture": "bounded_internal_reference",
            "raw_payload_export_allowed": False,
            "alternatives": [
                {
                    "text": "українська форма",
                    "transformation_path": ["ulif fixture alternative"],
                }
            ],
        }
    if kind == "model_proposal":
        return {
            "schema_version": "language_contact_silver_observation_v1",
            "observation_id": f"obs.model.{_sha(candidate_id)}",
            "candidate_id": candidate_id,
            "kind": "model_proposal",
            "model_family": "google",
            "model": "gemini-fixture",
            "harness": "agy-fixture",
            "task_id": "task.fixture-model",
            "prompt_sha256": _sha("prompt"),
            "response_sha256": _sha("response"),
            "stance": "propose",
            "challenge_targets": [],
            "alternatives": [{"text": "модельна пропозиція", "transformation_path": ["model proposal"]}],
        }
    return {
        "schema_version": "language_contact_silver_observation_v1",
        "observation_id": f"obs.hramatka.{_sha(candidate_id)}",
        "candidate_id": candidate_id,
        "kind": "hramatka_feedback",
        "feedback_id": "feedback.fixture-001",
        "pseudonymous_actor_id": "actor.fixture-001",
        "consent_receipt_sha256": _sha("consent"),
        "privacy_cleared": True,
        "permitted_use": "research_feedback",
        "observed_at": "2026-08-01T12:00:00Z",
        "source_surface": "hramatka",
        "selection_bias": {
            "population": "fixture teachers",
            "invitation_surface": "fixture",
            "self_selected": True,
            "limitations": ["synthetic test-only observation"],
        },
        "supports": "correction_candidate",
        "alternatives": [{"text": "відгукова пропозиція", "transformation_path": ["feedback"]}],
    }


def test_contracts_are_valid_and_distinct_from_human_gold() -> None:
    for path in (factory.OBSERVATION_SCHEMA, factory.RECORD_SCHEMA, factory.RECEIPT_SCHEMA):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
    record_schema = factory.RECORD_SCHEMA.read_text(encoding="utf-8")
    assert '"human_reviewed": {"const": false}' in record_schema
    assert '"qualified_human_gold": {"const": false}' in record_schema
    assert '"model_training_or_export_eligible": {"const": false}' in record_schema


def test_protected_quote_and_unresolved_routes_are_byte_stable(tmp_path: Path) -> None:
    rows = [
        _candidate(1, category="protected_authentic_ukrainian", vesum=True, heritage=True),
        _candidate(2, category="russian_quotation", role="quotation", russian=True, r2u=True),
        _candidate(3, category="modern_narration_interference", russian=True, r2u=True),
    ]
    first = _run(tmp_path, rows, suffix="first")
    second = _run(tmp_path, rows, suffix="second")

    assert first.output_path.read_bytes() == second.output_path.read_bytes()
    assert first.receipt_path.read_bytes() == second.receipt_path.read_bytes()
    produced = _rows(first.output_path)
    assert [row["decision"]["evidence_grade"] for row in produced] == [
        "protected",
        "protected",
        "unresolved",
    ]
    assert [row["decision"]["disposition"] for row in produced] == [
        "protected_variation",
        "quoted_or_multilingual",
        "unresolved",
    ]
    assert all(row["claim_boundary"]["human_reviewed"] is False for row in produced)
    assert first.receipt["hramatka"] == {
        "state": "empty_valid",
        "observations": 0,
        "blocking": False,
    }


def test_source_backed_correction_requires_corroboration_and_keeps_alternative(
    tmp_path: Path,
) -> None:
    candidate = _candidate(
        4,
        category="modern_narration_interference",
        russian=True,
        r2u=True,
    )
    without = _run(tmp_path, [candidate], suffix="without")
    assert _rows(without.output_path)[0]["decision"]["evidence_grade"] == "unresolved"

    source = _observation(candidate)
    with_source = _run(tmp_path, [candidate], observations=[source], suffix="with")
    record = _rows(with_source.output_path)[0]
    assert record["decision"]["evidence_grade"] == "deterministic_source_backed_silver"
    assert record["decision"]["disposition"] == "correction"
    assert record["decision"]["alternatives"] == [
        {
            "text": "українська форма",
            "supporting_observation_ids": [source["observation_id"]],
            "transformation_paths": [["ulif fixture alternative"]],
        }
    ]
    assert record["source_enrichment"]["correction_training_eligible"] is False


def test_case_distinct_supported_alternatives_are_not_collapsed(tmp_path: Path) -> None:
    candidate = _candidate(
        10,
        category="modern_narration_interference",
        russian=True,
        r2u=True,
    )
    upper = _observation(candidate)
    upper["alternatives"][0]["text"] = "Українська форма"
    lower = copy.deepcopy(upper)
    lower["observation_id"] = f"obs.slovnyk.{_sha(upper['candidate_id'])}"
    lower["source"] = "slovnyk_me"
    lower["source_identity"] = "sum11"
    lower["locator"] = "https://slovnyk.me/dict/sum11/example"
    lower["content_sha256"] = _sha("slovnyk fixture")
    lower["alternatives"][0]["text"] = "українська форма"

    run = _run(tmp_path, [candidate], observations=[upper, lower], suffix="case")
    alternatives = _rows(run.output_path)[0]["decision"]["alternatives"]

    assert [item["text"] for item in alternatives] == [
        "Українська форма",
        "українська форма",
    ]


def test_two_dictionary_sources_can_protect_authentic_variation(tmp_path: Path) -> None:
    candidate = _candidate(11, category="protected_authentic_ukrainian")
    ulif = _observation(candidate)
    ulif["supports"] = "protected_variation"
    ulif["alternatives"] = []
    slovnyk = copy.deepcopy(ulif)
    slovnyk["observation_id"] = f"obs.slovnyk.{_sha(ulif['candidate_id'])}"
    slovnyk["source"] = "slovnyk_me"
    slovnyk["source_identity"] = "hrinchenko"
    slovnyk["locator"] = "https://slovnyk.me/dict/hrinchenko/example"
    slovnyk["content_sha256"] = _sha("hrinchenko fixture")

    run = _run(tmp_path, [candidate], observations=[ulif, slovnyk], suffix="protect")
    record = _rows(run.output_path)[0]

    assert record["decision"]["evidence_grade"] == "protected"
    assert record["decision"]["disposition"] == "protected_variation"


def test_valid_word_lexical_attestation_does_not_claim_contextual_acceptability(
    tmp_path: Path,
) -> None:
    candidate = _candidate(
        12,
        category="valid_word_contact_candidate",
        vesum=True,
        heritage=True,
    )
    run = _run(tmp_path, [candidate], suffix="valid-word")
    record = _rows(run.output_path)[0]

    assert record["decision"]["evidence_grade"] == "unresolved"
    assert record["decision"]["disposition"] == "unresolved"
    assert any("contextual sense" in item for item in record["decision"]["uncertainty"])


def test_real_reconstruction_shape_is_preserved_without_becoming_an_alternative(
    tmp_path: Path,
) -> None:
    candidate = _candidate(
        14,
        category="ukrainian_phonetic_russian",
        russian=True,
        r2u=True,
    )
    candidate["evidence"]["reconstruction_candidates"] = [
        {
            "original_surface": "очєнь",
            "reconstructed_surface": "очень",
            "reconstructed_lemma": "очень",
            "transformation_path": ["configured:очєнь->очень"],
            "ru_morph": {
                "token": "очень",
                "lemma": "очень",
                "confidence": 1.0,
            },
            "r2u_cache": {
                "query": "очень",
                "query_kind": "surface",
                "status": "hit",
                "response_sha256": _sha("r2u response"),
                "result_count": 151,
                "headword_match": "surface",
            },
            "validated": True,
        }
    ]

    run = _run(tmp_path, [candidate], suffix="real-reconstruction")
    record = _rows(run.output_path)[0]

    assert record["decision"]["evidence_grade"] == "unresolved"
    assert record["decision"]["alternatives"] == []
    assert (
        record["detector_candidate"]["evidence"]["reconstruction_candidates"]
        == candidate["evidence"]["reconstruction_candidates"]
    )


def test_model_and_hramatka_inputs_never_self_promote(tmp_path: Path) -> None:
    candidate = _candidate(
        5,
        category="modern_narration_interference",
        russian=True,
        r2u=True,
    )
    model = _observation(candidate, kind="model_proposal")
    feedback = _observation(candidate, kind="hramatka_feedback")
    run = _run(tmp_path, [candidate], observations=[model, feedback], suffix="feedback")
    record = _rows(run.output_path)[0]

    assert record["decision"]["evidence_grade"] == "model_only_research"
    assert record["decision"]["disposition"] == "unresolved"
    assert run.receipt["hramatka"] == {
        "state": "bounded_feedback_ingested",
        "observations": 1,
        "blocking": False,
    }
    assert record["claim_boundary"]["reviewer_reliability_counted"] is False


def test_evaluation_text_is_omitted_from_silver_output(tmp_path: Path) -> None:
    manifest = json.loads(factory.DEFAULT_V011_MANIFEST.read_text(encoding="utf-8"))
    layout = manifest["record_layouts"]["item"]
    source_index = layout.index("source")
    evaluation_source = next(row[source_index] for row in manifest["items"] if 16 <= len(row[source_index]) <= 240)
    candidate = _candidate(6, category="uncertain", text=evaluation_source)
    run = _run(tmp_path, [candidate], suffix="evaluation")

    assert run.output_path.read_bytes() == b""
    assert run.receipt["candidate_arithmetic"] == {
        "input_candidates": 1,
        "output_records": 0,
        "evaluation_excluded": 1,
    }


def test_generated_evaluation_match_rolls_back_adapter_telemetry(tmp_path: Path) -> None:
    manifest = json.loads(factory.DEFAULT_V011_MANIFEST.read_text(encoding="utf-8"))
    layout = manifest["record_layouts"]["item"]
    source_index = layout.index("source")
    evaluation_source = next(row[source_index] for row in manifest["items"] if 16 <= len(row[source_index]) <= 240)
    candidate = _candidate(13, category="uncertain")
    core = factory.candidate_core(candidate)
    database = tmp_path / "data/sources.db"
    database.parent.mkdir(parents=True)
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            """
            CREATE TABLE ulif_dictua_entries (
                normalized_query TEXT,
                canonical_headword TEXT,
                raw_response_ref TEXT,
                response_sha256 TEXT,
                parser_version TEXT,
                status TEXT
            )
            """
        )
        connection.execute(
            "INSERT INTO ulif_dictua_entries VALUES (?, ?, ?, ?, ?, ?)",
            (
                factory.detector.tokenize_with_offsets(core)[0].normalized,
                evaluation_source,
                "fixture://eval",
                _sha(evaluation_source),
                "fixture-v1",
                "ok",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    run = _run(tmp_path, [candidate], suffix="generated-evaluation")

    assert run.output_path.read_bytes() == b""
    assert run.receipt["candidate_arithmetic"]["evaluation_excluded"] == 1
    adapter = run.receipt["evidence_adapters"]["ulif_dictua"]
    assert adapter["adapter_id"] == "sources.db:ulif_dictua_entries"
    assert adapter["status"] == "bounded_cache"
    assert adapter["source_snapshot"] is not None
    assert adapter["lookups"] == adapter["hits"] == adapter["misses"] == 0


def test_stale_detector_hash_fails_without_replacing_prior_outputs(tmp_path: Path) -> None:
    candidate = _candidate(7, category="uncertain")
    candidates = tmp_path / "candidates.jsonl"
    detector_receipt = tmp_path / "detector.json"
    config = tmp_path / "config.json"
    output = tmp_path / "silver.jsonl"
    receipt = tmp_path / "silver.receipt.json"
    _write_jsonl(candidates, [candidate])
    _detector_receipt(detector_receipt, candidates, [candidate])
    _config(config)
    output.write_text("existing-output\n", encoding="utf-8")
    receipt.write_text("existing-receipt\n", encoding="utf-8")
    changed = copy.deepcopy(candidate)
    changed["metadata"]["register"] = "changed"
    _write_jsonl(candidates, [changed])

    with pytest.raises(factory.SilverError, match="does not match its receipt"):
        factory.build_silver(
            candidates_path=candidates,
            detector_receipt_path=detector_receipt,
            detector_config_path=config,
            admission_receipt_path=factory.DEFAULT_ADMISSION_RECEIPT,
            operator_packet_path=factory.DEFAULT_OPERATOR_PACKET,
            input_root=tmp_path,
            observations_path=None,
            output_path=output,
            receipt_path=receipt,
        )

    assert output.read_text(encoding="utf-8") == "existing-output\n"
    assert receipt.read_text(encoding="utf-8") == "existing-receipt\n"


def test_invalid_candidate_span_fails_before_replacing_prior_outputs(tmp_path: Path) -> None:
    candidate = _candidate(8, category="uncertain")
    candidate["span"]["span_hash"] = "0" * 64
    candidates = tmp_path / "candidates.jsonl"
    detector_receipt = tmp_path / "detector.json"
    config = tmp_path / "config.json"
    output = tmp_path / "silver.jsonl"
    receipt = tmp_path / "silver.receipt.json"
    _write_jsonl(candidates, [candidate])
    _detector_receipt(detector_receipt, candidates, [candidate])
    _config(config)
    output.write_text("existing-output\n", encoding="utf-8")
    receipt.write_text("existing-receipt\n", encoding="utf-8")

    with pytest.raises(factory.SilverError, match="span hash does not match"):
        factory.build_silver(
            candidates_path=candidates,
            detector_receipt_path=detector_receipt,
            detector_config_path=config,
            admission_receipt_path=factory.DEFAULT_ADMISSION_RECEIPT,
            operator_packet_path=factory.DEFAULT_OPERATOR_PACKET,
            input_root=tmp_path,
            observations_path=None,
            output_path=output,
            receipt_path=receipt,
        )

    assert output.read_text(encoding="utf-8") == "existing-output\n"
    assert receipt.read_text(encoding="utf-8") == "existing-receipt\n"


def test_slovnyk_observation_requires_underlying_dictionary_identity(tmp_path: Path) -> None:
    candidate = _candidate(9, category="uncertain")
    observation = _observation(candidate)
    observation.update(
        {
            "observation_id": "obs.slovnyk.fixture",
            "source": "slovnyk_me",
            "source_identity": "wrong_dictionary",
            "locator": "https://slovnyk.me/dict/newsum/форма",
        }
    )
    with pytest.raises(factory.SilverError, match="source identity differs"):
        _run(tmp_path, [candidate], observations=[observation], suffix="bad-slovnyk")
