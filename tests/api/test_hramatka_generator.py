"""Tests for bounded, quality-qualified Hramatka generation routing."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.error import HTTPError

from scripts.api.hramatka_generator import (
    MAX_PROVIDER_ATTEMPTS,
    PRIMARY_MODEL,
    SECONDARY_MODEL,
    GenerationState,
    ProviderHTTPError,
    generate_qualified_lesson,
    is_transient_provider_failure,
    normalize_hramatka_level,
)
from scripts.audit.hramatka_qg_rules import DIMENSION_ORDER


def _passing_evidence() -> dict[str, Any]:
    return {
        "verdict": "PASS",
        "terminal_verdict": "PASS",
        "detector_status": {},
        "dimensions": {
            dimension: {"verdict": "PASS", "score": 10.0} for dimension in DIMENSION_ORDER
        },
    }


class RecordingTransport:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = iter(outcomes)
        self.models: list[str] = []

    def generate(self, *, model: str, request: Mapping[str, Any]) -> Mapping[str, Any]:
        self.models.append(model)
        outcome = next(self.outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        assert isinstance(outcome, Mapping)
        return outcome


def test_primary_route_success_uses_gemini_36_flash_and_marks_ready() -> None:
    lesson = {"title": "Чистий урок", "blocks": [{"id": "b1", "type": "intro"}]}
    transport = RecordingTransport([lesson])
    qg_calls: list[Mapping[str, Any]] = []

    def qg_scan(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
        qg_calls.append(candidate)
        return _passing_evidence()

    result = generate_qualified_lesson({"prompt": "Створіть урок"}, transport=transport, qg_scan=qg_scan)

    assert result.state is GenerationState.READY
    assert result.lesson == lesson
    assert result.failure_reason is None
    assert transport.models == [PRIMARY_MODEL]
    assert qg_calls == [{"title": "Чистий урок", "blocks": [{"id": "b1", "type": "intro"}], "level": "b1"}]
    assert [attempt.outcome for attempt in result.attempts] == ["ready"]


def test_5xx_primary_failure_uses_secondary_route_once() -> None:
    lesson = {"title": "Резервний урок", "blocks": [{"id": "b1", "type": "intro"}]}
    transport = RecordingTransport([ProviderHTTPError(503), lesson])

    result = generate_qualified_lesson(
        {"prompt": "Створіть урок"},
        transport=transport,
        qg_scan=lambda _lesson: _passing_evidence(),
    )

    assert result.state is GenerationState.READY
    assert transport.models == [PRIMARY_MODEL, SECONDARY_MODEL]
    assert [attempt.outcome for attempt in result.attempts] == ["transient_failure", "ready"]


def test_empty_blocks_payload_fails_validation_without_ready() -> None:
    lesson = {"title": "Порожній урок", "blocks": []}
    transport = RecordingTransport([lesson])

    result = generate_qualified_lesson(
        {"prompt": "Створіть урок"},
        transport=transport,
        qg_scan=lambda _lesson: _passing_evidence(),
    )

    assert result.state is GenerationState.FAILED
    assert result.failure_reason == "invalid_provider_payload"
    assert result.lesson is None


def test_malformed_block_payload_fails_validation_without_ready() -> None:
    lesson = {"title": "Зламаний урок", "blocks": [{}]}
    transport = RecordingTransport([lesson])

    result = generate_qualified_lesson(
        {"prompt": "Створіть урок"},
        transport=transport,
        qg_scan=lambda _lesson: _passing_evidence(),
    )

    assert result.state is GenerationState.FAILED
    assert result.failure_reason == "invalid_provider_payload"
    assert result.lesson is None


def test_timeout_retries_never_exceed_four_provider_calls() -> None:
    transport = RecordingTransport([TimeoutError("provider timeout")] * MAX_PROVIDER_ATTEMPTS)

    result = generate_qualified_lesson(
        {"prompt": "Створіть урок"},
        transport=transport,
        qg_scan=lambda _lesson: _passing_evidence(),
    )

    assert result.state is GenerationState.FAILED
    assert result.failure_reason == "provider_retry_budget_exhausted"
    assert len(result.attempts) == MAX_PROVIDER_ATTEMPTS
    assert transport.models == [PRIMARY_MODEL, SECONDARY_MODEL, PRIMARY_MODEL, SECONDARY_MODEL]


def test_4xx_provider_failure_fails_closed_without_fallback() -> None:
    transport = RecordingTransport([ProviderHTTPError(404)])

    result = generate_qualified_lesson(
        {"prompt": "Створіть урок"},
        transport=transport,
        qg_scan=lambda _lesson: _passing_evidence(),
    )

    assert result.state is GenerationState.FAILED
    assert result.failure_reason == "provider_failure"
    assert transport.models == [PRIMARY_MODEL]
    assert [attempt.outcome for attempt in result.attempts] == ["provider_failure"]


def test_qg_warning_cannot_transition_generated_lesson_to_ready() -> None:
    lesson = {"title": "Урок із попередженням", "blocks": [{"id": "b1", "type": "intro"}]}
    transport = RecordingTransport([lesson])
    evidence = _passing_evidence()
    evidence["dimensions"][DIMENSION_ORDER[0]] = {"verdict": "WARN", "score": 9.2}
    evidence["verdict"] = "WARN"

    result = generate_qualified_lesson(
        {"prompt": "Створіть урок"},
        transport=transport,
        qg_scan=lambda _lesson: evidence,
    )

    assert result.state is GenerationState.FAILED
    assert result.lesson is None
    assert result.qg_evidence == evidence
    assert result.failure_reason == "qg_rejected"
    assert transport.models == [PRIMARY_MODEL]
    assert [attempt.outcome for attempt in result.attempts] == ["qg_rejected"]


def test_absent_or_malformed_detector_status_fails_qualification() -> None:
    lesson = {"title": "Урок без статусу детекторів", "blocks": [{"id": "b1", "type": "intro"}]}
    transport = RecordingTransport([lesson])
    evidence = _passing_evidence()
    del evidence["detector_status"]

    result = generate_qualified_lesson(
        {"prompt": "Створіть урок"},
        transport=transport,
        qg_scan=lambda _lesson: evidence,
    )

    assert result.state is GenerationState.FAILED
    assert result.failure_reason == "qg_rejected"


def test_urllib_http_error_handling_differentiates_4xx_and_5xx() -> None:
    error_401 = HTTPError("http://example.com", 401, "Unauthorized", {}, None)  # type: ignore[arg-type]
    error_502 = HTTPError("http://example.com", 502, "Bad Gateway", {}, None)  # type: ignore[arg-type]

    assert is_transient_provider_failure(error_401) is False
    assert is_transient_provider_failure(error_502) is True


def test_normalize_hramatka_level_handles_aliases_and_missing_levels() -> None:
    assert normalize_hramatka_level("Intermediate") == "b1"
    assert normalize_hramatka_level("Beginner") == "a1"
    assert normalize_hramatka_level(None) == "b1"
    assert normalize_hramatka_level("") == "b1"
    assert normalize_hramatka_level("A2") == "a2"
    assert normalize_hramatka_level("c3") is None
    assert normalize_hramatka_level("   ") is None


def test_unrecognized_or_whitespace_level_fails_validation_without_ready() -> None:
    lesson = {"title": "Урок з невідомим рівнем", "level": "c3", "blocks": [{"id": "b1", "type": "intro"}]}
    transport = RecordingTransport([lesson])

    result = generate_qualified_lesson(
        {"prompt": "Створіть урок"},
        transport=transport,
        qg_scan=lambda _lesson: _passing_evidence(),
    )

    assert result.state is GenerationState.FAILED
    assert result.failure_reason == "invalid_provider_payload"
    assert result.lesson is None


