"""Qualified Gemini routing for Hramatka lesson generation.

The private Hramatka service supplies an AGY/provider API client through
``AGYProviderTransport``.  Keeping credentials and process management outside
this public module makes the routing policy deterministic and testable.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):  # noqa: UP042
        """Fallback StrEnum implementation for Python 3.10 support."""

        def __str__(self) -> str:
            return str(self.value)

from scripts.audit.hramatka_qg_rules import DIMENSION_ORDER, scan_hramatka_lesson

PRIMARY_MODEL = "gemini-3.6-flash-high"
SECONDARY_MODEL = "gemini-3.1-pro-high"
MAX_PROVIDER_ATTEMPTS = 4
_PERFECT_QG_SCORE = 10.0


class GenerationState(StrEnum):
    """Terminal lifecycle states emitted by this router."""

    READY = "ready"
    FAILED = "failed"


class ProviderHTTPError(RuntimeError):
    """Provider HTTP failure with a status code available to routing policy."""

    def __init__(self, status_code: int, message: str = "provider HTTP failure") -> None:
        super().__init__(message)
        self.status_code = status_code


class ProviderTransport(Protocol):
    """Minimal provider API surface required by qualified routing."""

    def generate(self, *, model: str, request: Mapping[str, Any]) -> Mapping[str, Any]:
        """Generate a Hramatka lesson JSON document with ``model``."""


@dataclass(frozen=True, slots=True)
class AGYProviderTransport:
    """Adapter for the AGY/provider API client owned by the service layer.

    The client is intentionally injected: this repository does not contain
    provider credentials or the private Hramatka service's request plumbing.
    """

    client: Callable[[str, Mapping[str, Any]], Mapping[str, Any]]

    def generate(self, *, model: str, request: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.client(model, request)


@dataclass(frozen=True, slots=True)
class GenerationAttempt:
    """A redacted record of one provider call."""

    number: int
    model: str
    outcome: str
    error_kind: str | None = None


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Qualified generation output; only ``READY`` results contain a lesson."""

    state: GenerationState
    lesson: Mapping[str, Any] | None
    qg_evidence: Mapping[str, Any] | None
    attempts: tuple[GenerationAttempt, ...]
    failure_reason: str | None = None


QualityGate = Callable[[Mapping[str, Any]], Mapping[str, Any]]


def is_transient_provider_failure(error: BaseException) -> bool:
    """Return whether an error permits one of the bounded retry attempts.

    Only provider network failures, timeouts, and HTTP 5xx responses are
    retryable. Authentication, validation, rate-limit, and provider 4xx errors
    deliberately fail closed rather than consuming the retry budget.
    """

    if isinstance(error, HTTPError):
        return 500 <= error.code <= 599

    if isinstance(error, (ConnectionError, TimeoutError, URLError)):
        return True

    status_code = getattr(error, "status_code", None)
    if not isinstance(status_code, int):
        response = getattr(error, "response", None)
        status_code = getattr(response, "status_code", None)
    return isinstance(status_code, int) and 500 <= status_code <= 599


def passes_all_hramatka_qg_rules(evidence: Mapping[str, Any]) -> bool:
    """Require a complete, perfect deterministic Hramatka QG result.

    ``terminal_verdict == PASS`` alone is insufficient because the QG scanner
    can return warnings or report an unavailable detector.  A lesson reaches
    ``ready`` only when every declared dimension is present and fully passes.
    """

    if evidence.get("verdict") != "PASS" or evidence.get("terminal_verdict") != "PASS":
        return False
    detector_status = evidence.get("detector_status")
    if not isinstance(detector_status, Mapping) or len(detector_status) != 0:
        return False

    dimensions = evidence.get("dimensions")
    if not isinstance(dimensions, Mapping):
        return False
    for dimension in DIMENSION_ORDER:
        result = dimensions.get(dimension)
        if not isinstance(result, Mapping):
            return False
        if result.get("verdict") != "PASS" or result.get("score") != _PERFECT_QG_SCORE:
            return False
    return True


def generate_qualified_lesson(
    request: Mapping[str, Any],
    *,
    transport: ProviderTransport,
    qg_scan: QualityGate = scan_hramatka_lesson,
    primary_model: str = PRIMARY_MODEL,
    secondary_model: str = SECONDARY_MODEL,
) -> GenerationResult:
    """Generate once-qualified lesson content with bounded provider failover.

    A route cycle makes one primary call followed by one secondary call only
    after a transient primary failure.  At most two cycles are allowed, which
    gives the fixed four-call budget: primary, secondary, primary, secondary.
    Content rejected by QG is never retried as a transport failure.
    """

    attempts: list[GenerationAttempt] = []
    models = (primary_model, secondary_model)

    for number in range(1, MAX_PROVIDER_ATTEMPTS + 1):
        model = models[(number - 1) % len(models)]
        try:
            lesson = transport.generate(model=model, request=request)
        except Exception as error:
            transient = is_transient_provider_failure(error)
            attempts.append(
                GenerationAttempt(
                    number=number,
                    model=model,
                    outcome="transient_failure" if transient else "provider_failure",
                    error_kind=type(error).__name__,
                )
            )
            if transient and number < MAX_PROVIDER_ATTEMPTS:
                continue
            return _failed(attempts, f"provider_{'retry_budget_exhausted' if transient else 'failure'}")

        blocks = lesson.get("blocks") if isinstance(lesson, Mapping) else None
        valid_blocks = (
            isinstance(blocks, list)
            and len(blocks) > 0
            and all(
                isinstance(block, Mapping)
                and isinstance(block.get("type"), str)
                and bool(block.get("type").strip())
                for block in blocks
            )
        )
        if not isinstance(lesson, Mapping) or not valid_blocks:
            attempts.append(
                GenerationAttempt(number=number, model=model, outcome="invalid_provider_payload")
            )
            return _failed(attempts, "invalid_provider_payload")

        try:
            evidence = qg_scan(lesson)
        except Exception as error:
            attempts.append(
                GenerationAttempt(
                    number=number,
                    model=model,
                    outcome="qg_unavailable",
                    error_kind=type(error).__name__,
                )
            )
            return _failed(attempts, "qg_unavailable")

        if not passes_all_hramatka_qg_rules(evidence):
            attempts.append(GenerationAttempt(number=number, model=model, outcome="qg_rejected"))
            return GenerationResult(
                state=GenerationState.FAILED,
                lesson=None,
                qg_evidence=evidence,
                attempts=tuple(attempts),
                failure_reason="qg_rejected",
            )

        attempts.append(GenerationAttempt(number=number, model=model, outcome="ready"))
        return GenerationResult(
            state=GenerationState.READY,
            lesson=lesson,
            qg_evidence=evidence,
            attempts=tuple(attempts),
        )

    raise AssertionError("provider retry loop exceeded its bounded attempt budget")


def _failed(attempts: list[GenerationAttempt], reason: str) -> GenerationResult:
    return GenerationResult(
        state=GenerationState.FAILED,
        lesson=None,
        qg_evidence=None,
        attempts=tuple(attempts),
        failure_reason=reason,
    )
