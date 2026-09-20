"""TypeSafe citation and source-grounding verifier (#8192, parent #4913).

Seminar citations must fail closed: a good citation may be sent to a human,
but a fabricated quote or a contradicted claim must never be auto-accepted.

Pipeline, per citation ``{id, claim, quote, source_text}``:

1. **Deterministic quote match.** No model call. Unicode NFC, collapsed
   whitespace, unified apostrophes / quotation marks / dashes, soft hyphens
   stripped. An elision marker inside the quote (``[...]``, ``[…]``, ``...``,
   ``…``) splits it; every segment must occur in the source, in order, and
   on a word boundary. An apostrophe is a word character only between two
   word characters (``п'ять``); at a word edge it is punctuation. A combining
   mark stays inside the word it follows, including one NFC cannot compose.
   A token counts as a word only when it contains a letter or digit, so a
   run of combining marks alone does not. No fuzzy match. Checks, in order:
   a non-string or empty quote or source is ``fabricated``; a quote with
   fewer than ``MIN_QUOTE_WORD_TOKENS`` word tokens, including zero, or whose
   every elision segment lacks a letter or digit, is ``needs_human_review``
   (``quote_too_short``) and the model is not called; a segment with no
   letter or digit cannot ground a match; then a miss is ``fabricated``.
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
# word tokens after ``normalize_for_match``. Zero tokens (``!!!``) are included.
# An apostrophe counts only when it sits inside the word. A token counts only
# when it contains a letter or digit; combining marks alone do not.
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


def _is_word_char(char: str) -> bool:
    """Unicode letter, digit, or combining mark.

    ``str.isalnum()`` is false for combining marks, so it splits a base letter
    from a mark NFC cannot compose (``q`` + U+0301). An apostrophe is not a
    word character here; ``_is_word_char_at`` counts it only between two.
    """
    if unicodedata.category(char).startswith("M"):
        return True
    return char.isalnum()


def _is_word_char_at(text: str, index: int) -> bool:
    """True when ``text[index]`` belongs to a word.

    An apostrophe counts only between two word characters (``п'ять``,
    ``м'який``). At a word edge it is punctuation, so a surrounding quote
    mark is a valid boundary.
    """
    char = text[index]
    if _is_word_char(char):
        return True
    if char != "'" or index == 0 or index + 1 >= len(text):
        return False
    return _is_word_char(text[index - 1]) and _is_word_char(text[index + 1])


def _has_letter_or_digit(text: str) -> bool:
    """True when ``text`` contains a Unicode letter or digit.

    ``str.isalnum`` is false for combining marks, so a token or segment of
    marks alone fails this bar. Check each character: ``"п'ять".isalnum()``
    is false because of the apostrophe, but the word still has letters.
    """
    return any(char.isalnum() for char in text)


def _elision_segments(normalized_quote: str) -> list[str]:
    """Non-empty pieces of an already normalised quote, split on elision markers."""
    segments = [part.strip() for part in _ELISION.split(normalized_quote)]
    return [part for part in segments if part]


def quote_word_tokens(text: str) -> list[str]:
    """Word tokens of ``text`` after ``normalize_for_match``.

    An apostrophe between two word characters does not split the token.
    A combining mark stays on the same token as the base letter. The token
    counts only when it contains a letter or digit.
    """
    normalized = normalize_for_match(text)
    tokens: list[str] = []
    index = 0
    length = len(normalized)
    while index < length:
        if not _is_word_char(normalized[index]):
            index += 1
            continue
        end = index + 1
        while end < length and _is_word_char_at(normalized, end):
            end += 1
        token = normalized[index:end]
        if _has_letter_or_digit(token):
            tokens.append(token)
        index = end
    return tokens


def _find_at_word_boundary(source: str, segment: str, cursor: int) -> int:
    """Index of ``segment`` at or after ``cursor``, or -1.

    The character before the match and the character after it must be absent
    or not part of the word. An internal apostrophe is part of the word, so
    ``п`` and ``ять`` do not match inside ``п'ять``. A combining mark is too,
    so ``q`` does not match inside ``q́r``.
    """
    start = cursor
    while True:
        found = source.find(segment, start)
        if found < 0:
            return -1
        end = found + len(segment)
        before_ok = found == 0 or not _is_word_char_at(source, found - 1)
        after_ok = end == len(source) or not _is_word_char_at(source, end)
        if before_ok and after_ok:
            return found
        start = found + 1


def quote_occurs_in_source(quote: str, source: str) -> bool:
    """True when every elision-split segment of ``quote`` occurs in ``source``, in order.

    Empty quote or empty source is a miss. Matching is exact after
    ``normalize_for_match`` — not fuzzy and not token overlap. Each segment
    must align to word boundaries in the normalised source. A segment with
    no letter or digit cannot ground a match, even if those marks occur in
    the source.
    """
    normalized_quote = normalize_for_match(quote)
    normalized_source = normalize_for_match(source)
    if not normalized_quote or not normalized_source:
        return False
    segments = _elision_segments(normalized_quote)
    if not segments:
        return False
    cursor = 0
    for segment in segments:
        if not _has_letter_or_digit(segment):
            return False
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
    if (
        not isinstance(quote, str)
        or not isinstance(source, str)
        or not normalize_for_match(quote)
        or not normalize_for_match(source)
    ):
        return _base_receipt(case, verdict="fabricated", decided_by="deterministic")
    token_count = len(quote_word_tokens(quote))
    segments = _elision_segments(normalize_for_match(quote))
    # ``not any`` is also true when elision ate the whole quote. A quote whose
    # every remaining segment lacks a letter or digit is too short, not a miss.
    every_segment_lacks_letter = not any(_has_letter_or_digit(segment) for segment in segments)
    if token_count < MIN_QUOTE_WORD_TOKENS or every_segment_lacks_letter:
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
