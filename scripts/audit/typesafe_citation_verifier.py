"""TypeSafe citation and source-grounding verifier (#8192, parent #4913).

Seminar citations must fail closed: a good citation may be sent to a human,
but a fabricated quote or a contradicted claim must never be auto-accepted.

Pipeline, per citation ``{id, claim, quote, source_text}``:

1. **Deterministic quote match.** No model call. Unicode NFC, collapsed
   whitespace, unified apostrophes / quotation marks / dashes, soft hyphens
   stripped. An elision marker inside the quote (``[...]``, ``[…]``, ``...``,
   ``…``) splits it; every segment must occur in the source, in order, and
   on a word boundary. An apostrophe inside a word (``п'ять``) is not a
   boundary. No fuzzy match. A quote with fewer than ``MIN_QUOTE_WORD_TOKENS``
   word tokens is ``needs_human_review`` (``quote_too_short``) and the model
   is not called. A miss, or an empty quote or source, is ``fabricated``.
2. **One System One request.** A single Choice — ``supports`` /
   ``contradicts`` / ``says_nothing`` — judged on the source passage versus
   the claim. Thresholds live in ``ACCEPT_CONFIDENCE``, not in the prompt.

Routing (only ``verified`` is an accept):

- ``supports`` with confidence >= ``ACCEPT_CONFIDENCE`` → ``verified``
- ``contradicts`` at any confidence → ``contradicted``
- ``says_nothing`` with confidence >= ``ACCEPT_CONFIDENCE`` → ``unsupported``
- anything else, including API failure, a malformed answer, a missing or
  unusable key, or an unexpected error on one citation
  → ``needs_human_review``

``--mock`` injects a fail-closed stub (no keyword heuristics, no network).
Tests pass their own client into ``verify_citation``.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import unicodedata
import urllib.error
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from scripts.typesafe.client import (
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    HttpSystemOneClient,
    TypeSafeError,
)

# High-stakes accept bar (docs/best-practices/typesafe-jev.md §4). One constant
# gates both auto-accept (supports) and auto-reject-as-unsupported (says_nothing).
# ``contradicts`` is not gated: any confidence is enough to refuse the citation.
ACCEPT_CONFIDENCE = 0.80
# A quote this short cannot show that the source says the claim. Count is
# word tokens after ``normalize_for_match``, apostrophes kept inside the word.
MIN_QUOTE_WORD_TOKENS = 3
# Float noise only. A distribution that is off by a percentage point is malformed.
PROBABILITY_SUM_TOLERANCE = 1e-6

QUESTION_ID = "source_relation"
CHOICE_OPTIONS = ("supports", "contradicts", "says_nothing")

CHOICE_INSTRUCTIONS = (
    "Judge only `source_passage` against `claim`. "
    "Does the source passage support the claim, contradict the claim, or say nothing about the claim? "
    "`quote` is the span the citation attributes to that passage; it is not extra evidence, "
    "and the claim itself is not evidence. "
    "Support means the passage states or directly entails the claim. "
    "Contradict means the passage states the opposite, or a fact that cannot be true if the claim is true. "
    "Say nothing when the passage does not address the claim, even if the quoted words occur in it."
)
CHOICE_CRITERIA = {
    "supports": "The source passage states or directly entails the claim.",
    "contradicts": (
        "The source passage states the opposite of the claim, or a fact that cannot be true together with the claim."
    ),
    "says_nothing": "The source passage does not address the claim, even if the quoted words occur in it.",
}

VERDICTS = ("verified", "fabricated", "contradicted", "unsupported", "needs_human_review")
_PASSTHROUGH = ("expected", "table", "row_id", "invented_quote", "quote_origin")

_APOSTROPHES = "\u0027\u2019\u02bc"
_QUOTES = "\u0022\u201c\u201d\u201e\u00ab\u00bb\u201f\u2018\u201a\u2039\u203a"
_DASHES = "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"
_SOFT_HYPHEN = "\u00ad"
_TRANSLATION = str.maketrans(
    {**{ch: "'" for ch in _APOSTROPHES}, **{ch: '"' for ch in _QUOTES}, **{ch: "-" for ch in _DASHES}}
)
# Bracketed ellipsis before a bare one, so `[...]` is one separator.
_ELISION = re.compile(r"\[\s*(?:\.\.\.|…)\s*\]|\.\.\.|…")
_WHITESPACE = re.compile(r"\s+")


class MalformedAnswer(ValueError):
    """System One returned JSON, but not a usable Choice on this citation."""


class SystemOneClient(Protocol):
    def system_one(
        self,
        state: Any,
        questions: Mapping[str, Any],
        *,
        model: str = ...,
        timeout: float = ...,
    ) -> dict[str, Any]: ...


class OfflineMockClient:
    """Fail-closed stub for ``--mock``. No network and no keyword heuristics.

    Stage 1 still runs. Any citation that reaches stage 2 becomes
    ``needs_human_review``. Tests that need a particular Choice inject their
    own client instead of using this one.
    """

    def system_one(
        self,
        state: Any,
        questions: Mapping[str, Any],
        *,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        raise TypeSafeError("offline mock: System One is not called")


def normalize_for_match(text: str) -> str:
    """NFC, strip soft hyphens, unify apostrophes, quotes, and dashes, collapse whitespace."""
    normalized = unicodedata.normalize("NFC", text).replace(_SOFT_HYPHEN, "")
    normalized = normalized.translate(_TRANSLATION)
    return _WHITESPACE.sub(" ", normalized).strip()


def _is_letter_or_digit(char: str) -> bool:
    return char.isalnum()


def _is_word_char(char: str) -> bool:
    """Letter, digit, or an apostrophe that sits inside a word such as ``п'ять``."""
    return char == "'" or _is_letter_or_digit(char)


def quote_word_tokens(text: str) -> list[str]:
    """Word tokens of ``text`` after ``normalize_for_match``.

    An apostrophe between two letters or digits does not split the token.
    """
    normalized = normalize_for_match(text)
    tokens: list[str] = []
    index = 0
    length = len(normalized)
    while index < length:
        if not _is_letter_or_digit(normalized[index]):
            index += 1
            continue
        end = index + 1
        while end < length:
            char = normalized[end]
            if _is_letter_or_digit(char):
                end += 1
                continue
            if char == "'" and end + 1 < length and _is_letter_or_digit(normalized[end + 1]):
                end += 2
                continue
            break
        tokens.append(normalized[index:end])
        index = end
    return tokens


def _find_at_word_boundary(source: str, segment: str, cursor: int) -> int:
    """Index of ``segment`` at or after ``cursor``, or -1.

    The character before the match and the character after it must be absent
    or not a word character. Apostrophes count as word characters, so ``ять``
    does not match inside ``п'ять``.
    """
    start = cursor
    while True:
        found = source.find(segment, start)
        if found < 0:
            return -1
        end = found + len(segment)
        before_ok = found == 0 or not _is_word_char(source[found - 1])
        after_ok = end == len(source) or not _is_word_char(source[end])
        if before_ok and after_ok:
            return found
        start = found + 1


def quote_occurs_in_source(quote: str, source: str) -> bool:
    """True when every elision-split segment of ``quote`` occurs in ``source``, in order.

    Empty quote or empty source is a miss. Matching is exact after
    ``normalize_for_match`` — not fuzzy and not token overlap. Each segment
    must align to word boundaries in the normalised source.
    """
    normalized_quote = normalize_for_match(quote)
    normalized_source = normalize_for_match(source)
    if not normalized_quote or not normalized_source:
        return False
    segments = [part.strip() for part in _ELISION.split(normalized_quote)]
    segments = [part for part in segments if part]
    if not segments:
        return False
    cursor = 0
    for segment in segments:
        found = _find_at_word_boundary(normalized_source, segment, cursor)
        if found < 0:
            return False
        cursor = found + len(segment)
    return True


def _questions() -> dict[str, Any]:
    return {
        QUESTION_ID: {
            "type": "choice",
            "instructions": CHOICE_INSTRUCTIONS,
            "criteria": dict(CHOICE_CRITERIA),
        }
    }


def _blank_usage() -> dict[str, int | None]:
    return {"input_tokens": None, "output_tokens": None}


def _coerce_finite_float(value: Any) -> float:
    """Coerce one API number. Bool, str, and overflow are ``MalformedAnswer``."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MalformedAnswer("value is not a number")
    try:
        number = float(value)
    except (OverflowError, ValueError, TypeError) as exc:
        raise MalformedAnswer("value is not a number") from exc
    if not math.isfinite(number):
        raise MalformedAnswer("value is not a finite number")
    return number


def _usage_from(response: Mapping[str, Any] | None) -> dict[str, int | None]:
    usage = _blank_usage()
    if not isinstance(response, Mapping):
        return usage
    raw = response.get("usage")
    if not isinstance(raw, Mapping):
        return usage
    for key in ("input_tokens", "output_tokens"):
        value = raw.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            continue
        _coerce_finite_float(value)
        usage[key] = value
    return usage


def _base_receipt(case: Mapping[str, Any], *, verdict: str, decided_by: str) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "id": case.get("id"),
        "verdict": verdict,
        "decided_by": decided_by,
        "accepted": verdict == "verified",
        "model": None,
        "question_ids": [],
        "usage": _blank_usage(),
        "choice": None,
        "probabilities": None,
        "confidence": None,
    }
    for key in _PASSTHROUGH:
        if key in case:
            receipt[key] = case[key]
    return receipt


def _route(choice: str, confidence: float) -> str:
    if choice == "supports" and confidence >= ACCEPT_CONFIDENCE:
        return "verified"
    if choice == "contradicts":
        return "contradicted"
    if choice == "says_nothing" and confidence >= ACCEPT_CONFIDENCE:
        return "unsupported"
    return "needs_human_review"


def _parse_choice(response: Any) -> tuple[str, float, dict[str, float]]:
    if not isinstance(response, Mapping):
        raise MalformedAnswer("response is not an object")
    answers = response.get("answers")
    if not isinstance(answers, Mapping):
        raise MalformedAnswer("answers is not an object")
    answer = answers.get(QUESTION_ID)
    if not isinstance(answer, Mapping):
        raise MalformedAnswer(f"missing {QUESTION_ID} answer")
    choice = answer.get("choice")
    if choice not in CHOICE_OPTIONS:
        raise MalformedAnswer("choice is not one of the closed options")
    if "confidence" not in answer:
        raise MalformedAnswer("confidence is not a number")
    confidence_value = _coerce_finite_float(answer.get("confidence"))
    if not 0.0 <= confidence_value <= 1.0:
        raise MalformedAnswer("confidence is outside [0, 1]")
    if "probabilities" not in answer:
        raise MalformedAnswer("probabilities is missing")
    probabilities = answer.get("probabilities")
    if not isinstance(probabilities, Mapping):
        raise MalformedAnswer("probabilities is not an object")
    if set(probabilities) != set(CHOICE_OPTIONS):
        raise MalformedAnswer("probabilities keys are not the closed options")
    parsed: dict[str, float] = {}
    for option in CHOICE_OPTIONS:
        number = _coerce_finite_float(probabilities[option])
        if not 0.0 <= number <= 1.0:
            raise MalformedAnswer("probability is outside [0, 1]")
        parsed[option] = number
    if not math.isclose(sum(parsed.values()), 1.0, abs_tol=PROBABILITY_SUM_TOLERANCE):
        raise MalformedAnswer("probabilities do not sum to 1")
    peak = max(parsed.values())
    winners = [
        option
        for option, number in parsed.items()
        if math.isclose(number, peak, abs_tol=PROBABILITY_SUM_TOLERANCE)
    ]
    if winners != [choice]:
        raise MalformedAnswer("choice is not the arg-max")
    return choice, confidence_value, parsed


def verify_citation(
    case: Mapping[str, Any],
    *,
    client: SystemOneClient | None = None,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Verify one citation. ``client`` defaults to the real HTTP client.

    Pass a fake to stay offline. A missing key or any client error on a quote
    that did match becomes ``needs_human_review`` and does not raise.
    """
    quote = case.get("quote")
    source = case.get("source_text")
    if not isinstance(quote, str) or not isinstance(source, str):
        return _base_receipt(case, verdict="fabricated", decided_by="deterministic")
    token_count = len(quote_word_tokens(quote))
    if 0 < token_count < MIN_QUOTE_WORD_TOKENS:
        receipt = _base_receipt(case, verdict="needs_human_review", decided_by="deterministic")
        receipt["reason"] = "quote_too_short"
        return receipt
    if not quote_occurs_in_source(quote, source):
        return _base_receipt(case, verdict="fabricated", decided_by="deterministic")

    active = client if client is not None else HttpSystemOneClient()
    state = {
        "citation_id": case.get("id"),
        "claim": case.get("claim"),
        "quote": quote,
        "source_passage": source,
    }
    questions = _questions()
    try:
        response = active.system_one(state, questions, model=model, timeout=timeout)
    except (TypeSafeError, OSError, TimeoutError, urllib.error.URLError):
        receipt = _base_receipt(case, verdict="needs_human_review", decided_by="system_one")
        receipt["question_ids"] = [QUESTION_ID]
        return receipt

    receipt = _base_receipt(case, verdict="needs_human_review", decided_by="system_one")
    receipt["question_ids"] = list(questions)
    try:
        if isinstance(response, Mapping):
            model_id = response.get("model")
            receipt["model"] = model_id if isinstance(model_id, str) else None
            receipt["usage"] = _usage_from(response)
        choice, confidence, probabilities = _parse_choice(response)
    except MalformedAnswer:
        return receipt
    receipt["choice"] = choice
    receipt["confidence"] = confidence
    receipt["probabilities"] = probabilities
    verdict = _route(choice, confidence)
    receipt["verdict"] = verdict
    receipt["accepted"] = verdict == "verified"
    return receipt


def verify_citations(
    cases: Sequence[Mapping[str, Any]],
    *,
    client: SystemOneClient | None = None,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[dict[str, Any]]:
    """Verify each citation. An unexpected error on one row does not stop the run."""
    receipts: list[dict[str, Any]] = []
    for case in cases:
        try:
            receipts.append(verify_citation(case, client=client, model=model, timeout=timeout))
        except Exception as exc:
            safe_case = case if isinstance(case, Mapping) else {}
            receipt = _base_receipt(safe_case, verdict="needs_human_review", decided_by="deterministic")
            receipt["reason"] = "internal_error"
            receipt["exception_type"] = type(exc).__name__
            receipts.append(receipt)
    return receipts


def load_cases(path: Path) -> list[dict[str, Any]]:
    """Load JSONL citations. Raises ``OSError`` or ``ValueError`` on I/O or shape errors."""
    text = path.read_text(encoding="utf-8")
    cases: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{line_no}: not valid JSON") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path.name}:{line_no}: expected a JSON object")
        for key in ("id", "claim", "quote", "source_text"):
            if key not in row or not isinstance(row[key], str):
                raise ValueError(f"{path.name}:{line_no}: {key} must be a string")
        cases.append(row)
    return cases


def _sum_tokens(citations: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    totals = {"input_tokens": 0, "output_tokens": 0}
    for citation in citations:
        usage = citation.get("usage")
        if not isinstance(usage, Mapping):
            continue
        for key in totals:
            value = usage.get(key)
            if isinstance(value, bool) or not isinstance(value, int):
                continue
            try:
                number = float(value)
            except (OverflowError, ValueError, TypeError):
                continue
            if math.isfinite(number):
                totals[key] += value
    return totals


def build_receipt(
    cases: Sequence[Mapping[str, Any]],
    *,
    client: SystemOneClient | None = None,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT,
    mock: bool = False,
) -> dict[str, Any]:
    active: SystemOneClient | None
    if client is not None:
        active = client
    elif mock:
        active = OfflineMockClient()
    else:
        active = None
    started = time.perf_counter()
    citations = verify_citations(cases, client=active, model=model, timeout=timeout)
    wall = time.perf_counter() - started
    counts = {verdict: 0 for verdict in VERDICTS}
    for citation in citations:
        verdict = citation["verdict"]
        if verdict in counts:
            counts[verdict] += 1
    return {
        "schema": "typesafe_citation_verifier_receipt_v1",
        "issue": 8192,
        "model_requested": model,
        "accept_confidence": ACCEPT_CONFIDENCE,
        "mock": mock and client is None,
        "wall_time_seconds": round(wall, 6),
        "usage": _sum_tokens(citations),
        "counts": counts,
        "n": len(citations),
        "citations": citations,
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=(
            "Check each citation's quote against its source, then ask TypeSafe whether that source supports the claim.\n"
            "Use for seminar citation grounding (history, biography, folklore, literature); "
            "do not use it as a merge gate, to rewrite Ukrainian, or to replace a human on a low-confidence call."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.audit.typesafe_citation_verifier \\\n"
            "    --input tests/fixtures/typesafe_citation_cases.jsonl \\\n"
            "    --out audit/2026-09-19-typesafe-citation-verifier/receipt.json\n"
            "  .venv/bin/python -m scripts.audit.typesafe_citation_verifier \\\n"
            "    --input cases.jsonl --out receipt.json --mock\n\n"
            "Outputs:\n"
            "  One JSON receipt at --out. Per citation: model id, question ids, token usage,\n"
            "  choice, probabilities, confidence, verdict, and which stage decided.\n"
            "  The API key is never written. Only verdict `verified` is an accept.\n\n"
            "Exit codes:\n"
            "  0  the run finished (including when every row is needs_human_review).\n"
            "  1  input/output error (missing file, bad JSONL, unwritable --out).\n"
            "  2  usage error (argparse).\n\n"
            "Related:\n"
            "  Client: scripts/typesafe/client.py\n"
            "  Practice: docs/best-practices/typesafe-jev.md §3.5 and §5\n"
            "  Fixture: tests/fixtures/typesafe_citation_cases.jsonl\n"
            "  Issue: #8192 (parent #4913)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def main(argv: Sequence[str] | None = None, *, client: SystemOneClient | None = None) -> int:
    parser = build_parser()
    parser.add_argument(
        "--input",
        required=True,
        metavar="PATH",
        help="JSONL of citations, one object per line with string fields id, claim, quote, source_text (example: cases.jsonl).",
    )
    parser.add_argument(
        "--out",
        required=True,
        metavar="PATH",
        help="Where to write the JSON receipt (example: receipt.json). Overwrites an existing file.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help=(
            "Offline stub: stage 1 still runs; stage 2 does not call the API and fail-closes to "
            "needs_human_review (default: false). Not a keyword scorer — inject a fake client in tests for scripted Choices."
        ),
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"System One model id (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Per-citation HTTP timeout in seconds (default: {DEFAULT_TIMEOUT:g}).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    input_path = Path(args.input)
    out_path = Path(args.out)
    try:
        cases = load_cases(input_path)
    except (OSError, ValueError) as exc:
        print(f"typesafe_citation_verifier: {exc}", file=sys.stderr)
        return 1
    receipt = build_receipt(
        cases,
        client=client,
        model=args.model,
        timeout=args.timeout,
        mock=args.mock,
    )
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"typesafe_citation_verifier: cannot write {out_path.name}: {exc.strerror or type(exc).__name__}", file=sys.stderr)
        return 1
    print(
        f"typesafe_citation_verifier: n={receipt['n']} "
        + " ".join(f"{name}={receipt['counts'][name]}" for name in VERDICTS)
        + f" wall_s={receipt['wall_time_seconds']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
