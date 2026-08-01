"""Regression and safety tests for the Ukrainian correction-data factory."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.projects.open_model_data import correction_factory as factory

ROOT = Path(__file__).resolve().parents[1]


def _hash(text: str) -> str:
    return factory.sha256_text(text)


def _evidence(
    source: str,
    *,
    status: str,
    supports: str,
    source_identity: str | None = None,
    evidence_type: str = "form",
    parser_status: str = "ok",
    sense_groups: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    identity = source_identity or {
        "vesum": "vesum-pinned-snapshot",
        "russian_morphology": "pymorphy3-russian-dictionary",
        "r2u": "r2u.org.ua",
        "ulif_dictua": "ulif-dictua",
        "slovnyk_me": "sum20",
        "heritage_dictionary": "esum",
        "ukrainian_corpus": "foundry-corpus-snapshot",
    }[source]
    locator = (
        f"https://slovnyk.me/dict/{identity}/fixture-query"
        if source == "slovnyk_me"
        else f"fixture:{source}/{identity}"
    )
    return {
        "content_sha256": _hash(f"{source}:{identity}:{status}"),
        "evidence_type": evidence_type,
        "locator": locator,
        "official_url": None,
        "parser_status": parser_status,
        "parser_version": f"{source}-fixture-v1",
        "period": "modern_or_source_specific",
        "query": "fixture-query",
        "raw_payload_export_allowed": False,
        "register": "source_specific",
        "rights_posture": "bounded_internal_reference",
        "sense_groups": sense_groups or [],
        "source": source,
        "source_identity": identity,
        "status": status,
        "supports": supports,
    }


def _russian_evidence(*, vesum_status: str = "not_found") -> list[dict[str, Any]]:
    rows = [
        _evidence("vesum", status=vesum_status, supports="no_conclusion"),
        _evidence("russian_morphology", status="attested", supports="russian_attestation", evidence_type="morphology"),
        _evidence("r2u", status="attested", supports="russian_attestation", evidence_type="translation_equivalent"),
    ]
    if vesum_status == "not_found":
        rows.extend(
            [
                _evidence("ulif_dictua", status="not_found", supports="no_conclusion"),
                _evidence("heritage_dictionary", status="not_found", supports="no_conclusion"),
                _evidence("slovnyk_me", status="not_found", supports="no_conclusion"),
                _evidence("ukrainian_corpus", status="attested", supports="context_only", evidence_type="corpus_context"),
            ]
        )
    return rows


def _views(
    *,
    modern: str = "unresolved",
    correction: str = "unresolved",
    preference: str = "unresolved",
) -> dict[str, str]:
    return {
        "correction": correction,
        "evaluation": "excluded_from_non_evaluation_views",
        "faithful_literary": "retain_original",
        "modern_literary_ukrainian": modern,
        "preference": preference,
    }


@pytest.fixture(scope="module")
def evaluation_registry() -> factory.EvaluationRegistry:
    return factory.load_evaluation_registry()


def _candidate(
    registry: factory.EvaluationRegistry,
    *,
    candidate_id: str,
    text: str,
    span_text: str,
    language: str = "ukrainian",
    representation: str = "standard_orthography",
    role: str = "narration",
    disposition: str = "human_review_required",
    period: str = "modern",
    register: str = "neutral",
    origin: str = "human_authored",
    layers: list[str] | None = None,
    views: dict[str, str] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    reconstructions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    context_start = 100
    relative_start = text.index(span_text)
    span_start = context_start + relative_start
    contamination = factory.contamination_states(text, registry)
    contamination["registry_artifact_sha256"] = {
        "v0_1_1_manifest": registry.v011_manifest_sha256,
        "v0_2_packet": registry.v02_packet_sha256,
    }
    return {
        "candidate_id": candidate_id,
        "candidate_layers": layers or ["grammar"],
        "detector": {
            "automatic_error_label": False,
            "kind": "combined",
            "model_output_used_as_gold": False,
            "producer": "fixture-detector-v1",
        },
        "evidence": evidence or [_evidence("vesum", status="attested", supports="ukrainian_attestation")],
        "reconstructions": reconstructions or [],
        "review_state": "unresolved",
        "safety": {
            "contamination": contamination,
            "origin": "verified_synthetic" if origin != "human_authored" else "verified_human_authorship",
            "permitted_use": "correction_eligible",
            "private_data": "clear",
            "provenance": "complete",
            "rights": "granted",
        },
        "schema_version": "correction_candidate_v1",
        "source": {
            "content_sha256": _hash(text),
            "context": {
                "end": context_start + len(text),
                "sha256": _hash(text),
                "start": context_start,
                "text": text,
            },
            "genre": "fixture",
            "locator": f"fixture:{candidate_id}",
            "origin": origin,
            "period": period,
            "record_id": f"record-{candidate_id}",
            "region": "unknown",
            "register": register,
            "source_family": "fixture",
            "source_record_id": f"source:{candidate_id}",
        },
        "span": {
            "discourse_role": role,
            "downstream_disposition": disposition,
            "end": span_start + len(span_text),
            "language_identity": language,
            "representation": representation,
            "start": span_start,
            "text": span_text,
        },
        "uncertainty": ["qualified_ukrainian_review_required"],
        "upstream": {
            "candidate_schema_version": "review_candidate_v1",
            "candidate_sha256": _hash(f"upstream:{candidate_id}"),
            "profile_id": "fixture-profile-v1",
        },
        "views": views or _views(),
    }


def _validators():
    schemas, registry = factory._schema_bundle()
    return (
        factory._validator(factory.CANDIDATE_SCHEMA_PATH, schemas=schemas, registry=registry),
        factory._validator(factory.DECISION_SCHEMA_PATH, schemas=schemas, registry=registry),
    )


def _validate(candidate: dict[str, Any], registry: factory.EvaluationRegistry) -> None:
    candidate_validator, _ = _validators()
    factory.validate_candidate(
        candidate,
        validator=candidate_validator,
        evaluation_registry=registry,
    )


def _reconstruction(original: str, russian: str) -> dict[str, Any]:
    return {
        "candidate": russian,
        "gate": "discourse_context",
        "original_surface": original,
        "r2u": {"query": russian, "status": "attested"},
        "russian_morphology": {"lemma": russian, "status": "attested"},
        "score": 0.95,
        "transformation_path": [f"bounded:{original}->{russian}"],
    }


def _projection(
    *,
    decision: str,
    language: str,
    representation: str,
    role: str,
    correction: str | None = None,
) -> dict[str, Any]:
    is_correction = decision == "correction"
    return {
        "acceptable_alternatives": [correction] if correction else [],
        "accepted_correction": correction,
        "citations": [
            {
                "content_sha256": _hash("fixture-citation"),
                "locator": "fixture:review-source",
                "source_identity": "fixture-source",
                "source_kind": "dictionary",
                "supports": "The cited source supports the human decision.",
            }
        ],
        "decision": decision,
        "discourse_role": role,
        "language_identity": language,
        "rationale": "Qualified fixture review rationale for contract testing.",
        "representation": representation,
        "uncertainty": ["fixture_review_not_real_gold"],
        "views": {
            "correction": "eligible_intake" if is_correction else ("unresolved" if decision == "unresolved" else "not_applicable"),
            "evaluation": "excluded_from_non_evaluation_views",
            "faithful_literary": "retain_original",
            "modern_literary_ukrainian": (
                "mask_span_from_loss"
                if decision == "quoted_or_multilingual"
                else ("unresolved" if decision == "unresolved" else "retain_original")
            ),
            "preference": "eligible_intake" if is_correction else ("unresolved" if decision == "unresolved" else "not_applicable"),
        },
    }


def _review(reviewer_id: str, projection: dict[str, Any]) -> dict[str, Any]:
    return {
        "projection": copy.deepcopy(projection),
        "reviewer": {
            "human": True,
            "independence_attested": True,
            "qualification_evidence": "Synthetic test fixture; never valid as real qualification evidence.",
            "reviewer_id": reviewer_id,
            "test_fixture": True,
            "ukrainian_qualification": "qualified_ukrainian_language_reviewer",
        },
    }


def _decision(candidate: dict[str, Any], projection: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": _hash(factory.canonical_json(candidate)),
        "final": copy.deepcopy(projection),
        "final_resolution": {"kind": "first_pass_agreement"},
        "first_pass_reviews": [
            _review("fixture-reviewer-a", projection),
            _review("fixture-reviewer-b", projection),
        ],
        "review_state": "unresolved" if projection["decision"] == "unresolved" else "adjudicated",
        "schema_version": "correction_reviewer_decision_v1",
    }


def test_standard_russian_quotation_is_preserved_and_masked(evaluation_registry) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-russian-quotation",
        text="Автор згадує: «что вызвало смуту», а потім пояснює контекст.",
        span_text="что вызвало смуту",
        language="russian",
        role="quotation",
        disposition="retain_with_language_metadata",
        layers=["russian_interference", "language_span"],
        views=_views(modern="mask_span_from_loss", correction="not_applicable", preference="not_applicable"),
        evidence=_russian_evidence(),
    )
    _validate(candidate, evaluation_registry)
    projection = _projection(
        decision="quoted_or_multilingual",
        language="russian",
        representation="standard_orthography",
        role="quotation",
    )
    decision = _decision(candidate, projection)
    _, decision_validator = _validators()
    factory.validate_decision(
        decision,
        candidate,
        validator=decision_validator,
        allow_test_fixtures=True,
    )
    assert factory._record(candidate, decision)["export_control"]["handoff"] == "faithful_or_protected_only"


def test_dash_led_russian_dialogue_does_not_require_guillemets(evaluation_registry) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-dash-dialogue",
        text="— Они что, не разговаривают? — спитав герой.",
        span_text="Они что, не разговаривают?",
        language="russian",
        role="dialogue",
        disposition="retain_with_language_metadata",
        layers=["russian_interference", "language_span"],
        views=_views(modern="exclude_span_or_record", correction="not_applicable", preference="not_applicable"),
        evidence=_russian_evidence(),
    )
    _validate(candidate, evaluation_registry)


def test_phonetic_russian_requires_bounded_morphology_and_r2u_reconstruction(evaluation_registry) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-phonetic-russian",
        text="— Вот, что значіт цівілізація! — вигукнув персонаж.",
        span_text="значіт цівілізація",
        language="russian",
        representation="ukrainian_phonetic_rendering_of_russian",
        role="dialogue",
        disposition="retain_with_language_metadata",
        layers=["russian_interference", "language_span"],
        views=_views(modern="mask_span_from_loss", correction="not_applicable", preference="not_applicable"),
        evidence=_russian_evidence(),
        reconstructions=[
            _reconstruction("значіт", "значит"),
            _reconstruction("цівілізація", "цивилизация"),
        ],
    )
    _validate(candidate, evaluation_registry)
    broken = copy.deepcopy(candidate)
    broken["reconstructions"] = []
    with pytest.raises(factory.FactoryError, match="reconstructions must agree"):
        _validate(broken, evaluation_registry)


def test_vesum_slang_presence_does_not_override_phonetic_russian_span(evaluation_registry) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-ochen-context",
        text="Він відповів: «очєнь вєжліви с нєй».",
        span_text="очєнь вєжліви с нєй",
        language="russian",
        representation="ukrainian_phonetic_rendering_of_russian",
        role="quotation",
        disposition="retain_with_language_metadata",
        layers=["russian_interference", "language_span"],
        views=_views(modern="mask_span_from_loss", correction="not_applicable", preference="not_applicable"),
        evidence=_russian_evidence(vesum_status="attested"),
        reconstructions=[_reconstruction("очєнь", "очень"), _reconstruction("вєжліви", "вежливы")],
    )
    _validate(candidate, evaluation_registry)
    assert candidate["span"]["language_identity"] == "russian"
    assert candidate["review_state"] == "unresolved"


def test_historical_span_is_protected_from_modern_error_gold(evaluation_registry) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-historical-span",
        text="У документі читаємо: что вас порушило.",
        span_text="что вас порушило",
        language="historical_east_slavic_unresolved",
        representation="historical_orthography",
        role="citation_or_document",
        disposition="protected_historical_or_register_variation",
        period="historical_documents",
        layers=["language_span", "protected_variation"],
        views=_views(modern="protected", correction="protected", preference="protected"),
        evidence=_russian_evidence(),
    )
    _validate(candidate, evaluation_registry)
    correction = _projection(
        decision="correction",
        correction="що вас порушило",
        language="ukrainian",
        representation="standard_orthography",
        role="citation_or_document",
    )
    decision = _decision(candidate, correction)
    _, decision_validator = _validators()
    with pytest.raises(factory.FactoryError, match="protected variation"):
        factory.validate_decision(
            decision,
            candidate,
            validator=decision_validator,
            allow_test_fixtures=True,
        )


def test_pereklychka_is_rescued_by_source_specific_ukrainian_evidence(evaluation_registry) -> None:
    evidence = _russian_evidence()
    for item in evidence:
        if item["source"] == "heritage_dictionary":
            item.update(status="attested", supports="ukrainian_attestation", source_identity="esum-etymological-dictionary")
        if item["source"] == "slovnyk_me":
            item.update(status="attested", supports="ukrainian_attestation", source_identity="sum20")
        if item["source"] == "ukrainian_corpus":
            item.update(status="attested", supports="ukrainian_attestation")
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-pereklychka-rescue",
        text="Почалася перекличка учасників.",
        span_text="перекличка",
        disposition="human_review_required",
        layers=["russian_interference", "protected_variation"],
        views=_views(modern="protected", correction="protected", preference="protected"),
        evidence=evidence,
    )
    _validate(candidate, evaluation_registry)
    assert {item["source_identity"] for item in evidence if item["status"] == "attested"} >= {
        "esum-etymological-dictionary",
        "sum20",
    }


def test_shared_ukrainian_russian_surface_stays_unresolved_on_bare_r2u_hit(evaluation_registry) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-shared-form",
        text="Контекст містить форму, спільну для двох мов.",
        span_text="форму",
        language="uncertain",
        disposition="unresolved",
        layers=["russian_interference"],
        views=_views(),
        evidence=_russian_evidence(vesum_status="attested"),
    )
    _validate(candidate, evaluation_registry)
    broken = copy.deepcopy(candidate)
    broken["span"]["language_identity"] = "russian"
    with pytest.raises(factory.FactoryError, match="bare r2u hit"):
        _validate(broken, evaluation_registry)


def test_ulif_synonyms_retain_groups_and_incomplete_status_blocks_intake(evaluation_registry) -> None:
    sense_group = {
        "citations": ["Словник синонімів української мови, т. 1"],
        "register_labels": ["розм."],
        "sense_or_group_id": "synonyms:1",
        "source_order": 0,
        "terms": ["вітання", "привітання"],
    }
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-ulif-synonyms",
        text="Це звучить неприродно в цьому контексті.",
        span_text="звучить неприродно",
        evidence=[
            _evidence("vesum", status="attested", supports="ukrainian_attestation"),
            _evidence(
                "ulif_dictua",
                status="attested",
                supports="alternative_candidate",
                evidence_type="synonym_group",
                parser_status="ok",
                sense_groups=[sense_group],
            ),
        ],
        layers=["collocation_or_government"],
        views=_views(correction="candidate", preference="candidate"),
        disposition="correction_candidate",
    )
    _validate(candidate, evaluation_registry)
    assert candidate["evidence"][1]["sense_groups"][0]["register_labels"] == ["розм."]
    incomplete = copy.deepcopy(candidate)
    incomplete["evidence"][1].update(status="parse_error", parser_status="parse_error")
    projection = _projection(
        decision="correction",
        correction="Це неприродно звучить",
        language="ukrainian",
        representation="standard_orthography",
        role="narration",
    )
    decision = _decision(incomplete, projection)
    assert "evidence_incomplete" in factory._safety_blockers(incomplete, decision)


def test_slovnyk_me_must_retain_underlying_dictionary_identity(evaluation_registry) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-slovnyk-source",
        text="Потрібне джерельне підтвердження слова.",
        span_text="підтвердження",
        evidence=[
            _evidence("vesum", status="attested", supports="ukrainian_attestation"),
            _evidence("slovnyk_me", status="attested", supports="ukrainian_attestation", source_identity="slovnyk.me"),
        ],
    )
    with pytest.raises(factory.FactoryError, match="per-dictionary"):
        _validate(candidate, evaluation_registry)
    candidate["evidence"][1] = _evidence(
        "slovnyk_me",
        status="attested",
        supports="ukrainian_attestation",
        source_identity="sum20",
    )
    _validate(candidate, evaluation_registry)

    mismatch = copy.deepcopy(candidate)
    mismatch["evidence"][1]["locator"] = (
        "https://slovnyk.me/dict/newsum/fixture-query"
    )
    with pytest.raises(factory.FactoryError, match="must equal"):
        _validate(mismatch, evaluation_registry)


def test_evaluation_rights_and_private_data_gates_fail_closed(evaluation_registry) -> None:
    manifest = json.loads(factory.DEFAULT_EVALUATION_MANIFEST.read_text(encoding="utf-8"))
    layout = manifest["record_layouts"]["item"]
    source = manifest["items"][0][layout.index("source")]
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-evaluation-match",
        text=source,
        span_text=source.split()[0],
    )
    _validate(candidate, evaluation_registry)
    projection = _projection(
        decision="correction",
        correction="Виправлений тестовий варіант",
        language="ukrainian",
        representation="standard_orthography",
        role="narration",
    )
    decision = _decision(candidate, projection)
    blockers = factory._safety_blockers(candidate, decision)
    assert "contamination_v0_1_1_exact" in blockers

    near_source = source[:-1] + ("!" if not source.endswith("!") else ".")
    near = _candidate(
        evaluation_registry,
        candidate_id="candidate-evaluation-near",
        text=near_source,
        span_text=near_source.split()[0],
    )
    _validate(near, evaluation_registry)
    assert near["safety"]["contamination"]["v0_1_1_near"] == "match"
    near["safety"].update(rights="unknown", private_data="present")
    decision = _decision(near, projection | {"accepted_correction": "Виправлено", "acceptable_alternatives": ["Виправлено"]})
    blockers = factory._safety_blockers(near, decision)
    assert {"rights_not_granted", "private_data_not_clear"} <= set(blockers)

    containing_context = f"Передмова до фрагмента. {source} Післямова до фрагмента."
    contained = _candidate(
        evaluation_registry,
        candidate_id="candidate-evaluation-contained",
        text=containing_context,
        span_text=source,
    )
    _validate(contained, evaluation_registry)
    assert contained["safety"]["contamination"]["v0_1_1_near"] == "match"


def test_source_origin_and_safety_evidence_cannot_contradict(evaluation_registry) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-origin-consistency",
        text="Синтетичний приклад потребує перевірки.",
        span_text="потребує перевірки",
        origin="machine_generated",
    )
    _validate(candidate, evaluation_registry)
    candidate["safety"]["origin"] = "verified_human_authorship"
    with pytest.raises(factory.FactoryError, match="source origin"):
        _validate(candidate, evaluation_registry)


def test_packet_and_receipt_are_byte_stable(evaluation_registry, tmp_path: Path) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-determinism",
        text="Модель ужила невдалу конструкцію.",
        span_text="невдалу конструкцію",
        origin="machine_generated",
        disposition="correction_candidate",
        views=_views(correction="candidate", preference="candidate"),
    )
    candidate_input = tmp_path / "candidates.jsonl"
    candidate_input.write_text(factory.canonical_json(candidate) + "\n", encoding="utf-8")

    first_packet, second_packet = tmp_path / "packet-1.jsonl", tmp_path / "packet-2.jsonl"
    first_receipt, second_receipt = tmp_path / "receipt-1.json", tmp_path / "receipt-2.json"
    factory.prepare_review_packet(
        candidates_path=candidate_input,
        packet_output=first_packet,
        receipt_output=first_receipt,
        evaluation_registry=evaluation_registry,
    )
    factory.prepare_review_packet(
        candidates_path=candidate_input,
        packet_output=second_packet,
        receipt_output=second_receipt,
        evaluation_registry=evaluation_registry,
    )
    assert first_packet.read_bytes() == second_packet.read_bytes()
    assert first_receipt.read_bytes() == second_receipt.read_bytes()

    projection = _projection(
        decision="correction",
        correction="Модель використала невдалу конструкцію.",
        language="ukrainian",
        representation="standard_orthography",
        role="narration",
    )
    decisions = tmp_path / "decisions.jsonl"
    decisions.write_text(
        factory.canonical_json(_decision(candidate, projection)) + "\n",
        encoding="utf-8",
    )
    first_records, second_records = tmp_path / "records-1.jsonl", tmp_path / "records-2.jsonl"
    first_adjudication, second_adjudication = (
        tmp_path / "adjudication-1.json",
        tmp_path / "adjudication-2.json",
    )
    factory.adjudicate(
        packet_path=first_packet,
        decisions_path=decisions,
        records_output=first_records,
        receipt_output=first_adjudication,
        evaluation_registry=evaluation_registry,
        allow_test_fixtures=True,
    )
    factory.adjudicate(
        packet_path=second_packet,
        decisions_path=decisions,
        records_output=second_records,
        receipt_output=second_adjudication,
        evaluation_registry=evaluation_registry,
        allow_test_fixtures=True,
    )
    assert first_records.read_bytes() == second_records.read_bytes()
    assert first_adjudication.read_bytes() == second_adjudication.read_bytes()
    record = json.loads(first_records.read_text(encoding="utf-8"))
    assert record["export_control"]["model_training_or_export_eligible"] is False
    assert record["export_control"]["qualified_correction_intake"] is False


def test_detector_or_model_cannot_emit_gold(evaluation_registry) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-not-gold",
        text="Так звучит неправильно.",
        span_text="звучит",
        language="uncertain",
        layers=["russian_interference"],
        evidence=_russian_evidence(),
    )
    _validate(candidate, evaluation_registry)
    broken = copy.deepcopy(candidate)
    broken["detector"]["automatic_error_label"] = True
    with pytest.raises(factory.FactoryError, match="automatic_error_label"):
        _validate(broken, evaluation_registry)


def test_two_humans_and_distinct_third_reviewer_are_enforced(evaluation_registry) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-human-conflict",
        text="Модель створила сумнівний вислів.",
        span_text="сумнівний вислів",
        origin="machine_generated",
        disposition="correction_candidate",
        views=_views(correction="candidate", preference="candidate"),
    )
    correction = _projection(
        decision="correction",
        correction="невдалий вислів",
        language="ukrainian",
        representation="standard_orthography",
        role="narration",
    )
    acceptable = _projection(
        decision="acceptable_as_is",
        language="ukrainian",
        representation="standard_orthography",
        role="narration",
    )
    decision = _decision(candidate, correction)
    decision["first_pass_reviews"][1] = _review("fixture-reviewer-b", acceptable)
    decision["final_resolution"] = {
        "kind": "third_human_adjudication",
        "third_review": _review("fixture-reviewer-c", correction),
    }
    _, validator = _validators()
    factory.validate_decision(
        decision,
        candidate,
        validator=validator,
        allow_test_fixtures=True,
    )
    record = factory._record(candidate, decision)
    assert record["conflict_state"] == "resolved_by_third_human"
    assert record["export_control"] == {
        "handoff": "unresolved",
        "model_training_or_export_eligible": False,
        "owner_issue": 6122,
        "qualified_correction_intake": False,
    }
    assert "test_fixture_reviewer" in record["safety_blockers"]

    decision["final_resolution"]["third_review"]["reviewer"]["reviewer_id"] = "fixture-reviewer-a"
    with pytest.raises(factory.FactoryError, match="third reviewer must be distinct"):
        factory.validate_decision(
            decision,
            candidate,
            validator=validator,
            allow_test_fixtures=True,
        )


def test_first_pass_core_agreement_merges_independent_evidence(evaluation_registry) -> None:
    candidate = _candidate(
        evaluation_registry,
        candidate_id="candidate-core-agreement",
        text="Це нормативний український вислів.",
        span_text="український вислів",
    )
    projection = _projection(
        decision="acceptable_as_is",
        language="ukrainian",
        representation="standard_orthography",
        role="narration",
    )
    decision = _decision(candidate, projection)
    decision["first_pass_reviews"][1]["projection"]["rationale"] = "Інше незалежне пояснення."
    decision["first_pass_reviews"][1]["projection"]["uncertainty"] = ["інша примітка"]
    decision["final"] = factory.merge_first_pass_agreement(decision["first_pass_reviews"])
    _, validator = _validators()
    factory.validate_decision(
        decision,
        candidate,
        validator=validator,
        allow_test_fixtures=True,
    )
    assert decision["final_resolution"]["kind"] == "first_pass_agreement"
    assert decision["final"]["uncertainty"] == ["fixture_review_not_real_gold", "інша примітка"]
    assert "Первинний рецензент B:" in decision["final"]["rationale"]


def test_adjudication_rejects_reordered_or_mismatched_decisions(evaluation_registry, tmp_path: Path) -> None:
    candidates = [
        _candidate(
            evaluation_registry,
            candidate_id=f"candidate-order-{suffix}",
            text=f"Контекст для кандидата {suffix}.",
            span_text="кандидата",
        )
        for suffix in ("one", "two")
    ]
    packet = tmp_path / "packet.jsonl"
    packet.write_text("".join(factory.canonical_json(row) + "\n" for row in candidates), encoding="utf-8")
    decisions = [
        _decision(
            candidate,
            _projection(
                decision="acceptable_as_is",
                language="ukrainian",
                representation="standard_orthography",
                role="narration",
            ),
        )
        for candidate in reversed(candidates)
    ]
    decision_path = tmp_path / "decisions.jsonl"
    decision_path.write_text("".join(factory.canonical_json(row) + "\n" for row in decisions), encoding="utf-8")
    output = tmp_path / "records.jsonl"
    output.write_text("prior-output\n", encoding="utf-8")
    with pytest.raises(factory.FactoryError, match="decision candidate ID mismatch"):
        factory.adjudicate(
            packet_path=packet,
            decisions_path=decision_path,
            records_output=output,
            receipt_output=tmp_path / "receipt.json",
            evaluation_registry=evaluation_registry,
            allow_test_fixtures=True,
        )
    assert output.read_text(encoding="utf-8") == "prior-output\n"
