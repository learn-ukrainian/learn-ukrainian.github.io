"""Parser tolerance for the ``evidence_quotes`` array shape.

Background
----------
Build #11 a1/my-morning (2026-05-21) exposed a parser-vs-reviewer schema
mismatch. Gemini-pro emitted this for the ``pedagogical`` dim:

    {
      "score": 10.0,
      "evidence_quotes": [
        "Before adding -ся, fix the regular first-conjugation template...",
        "The routine vocabulary is small on purpose...",
        "This four-line template is the smallest complete monologue..."
      ],
      "evidence": "Before adding -ся, fix the regular first-conjugation template...",
      "verdict": "PASS"
    }

The reviewer provided three substantive supporting quotes — arguably a more
falsifiable evidence shape than a single ``evidence`` scalar — but the parser
checked the bare ``evidence`` field for literal quote markers (``"``/``«``/``""``)
and raised ``LLM QG evidence for pedagogical must include a quoted excerpt``.

Fix policy
----------
- Accept ``evidence_quotes`` as an alternative to ``evidence``-with-markers.
- A valid ``evidence_quotes`` list must contain at least one string ≥8 chars.
- The bare ``evidence`` scalar may still satisfy the contract via embedded
  quote markers (existing behavior preserved).
- Either path satisfies the falsifiability contract: the reviewer cannot
  claim PASS without citing concrete artifact text.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.build import linear_pipeline


def _placeholder_other_dims(
    target_dim: str, target_entry: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Build a full report with `target_dim` overridden + others placeholdered."""
    from scripts.build.linear_pipeline import (
        QG_DIMS,
        _placeholder_review_report,  # type: ignore[attr-defined]
    )
    base = _placeholder_review_report()
    assert target_dim in QG_DIMS
    base[target_dim] = target_entry
    return base


# ----- validate_llm_review_report -------------------------------------------

def test_evidence_quotes_array_satisfies_contract() -> None:
    """The exact shape gemini-pro emitted for build #11 pedagogical dim."""
    entry = {
        "score": 10.0,
        "evidence_quotes": [
            "Before adding -ся, fix the regular first-conjugation template in mind",
            "The routine vocabulary is small on purpose — fluency over breadth",
            "This four-line template is the smallest complete monologue",
        ],
        "evidence": "Before adding -ся, fix the regular first-conjugation template in mind",
        "verdict": "PASS",
    }
    # Must not raise.
    linear_pipeline.validate_llm_review_report(
        _placeholder_other_dims("pedagogical", entry)
    )


def test_evidence_quotes_array_accepts_when_bare_evidence_missing() -> None:
    """If the reviewer omits the bare scalar entirely, the array still counts."""
    entry = {
        "score": 9.0,
        "evidence_quotes": [
            "Before adding -ся, fix the regular first-conjugation template",
        ],
        "verdict": "PASS",
    }
    linear_pipeline.validate_llm_review_report(
        _placeholder_other_dims("pedagogical", entry)
    )


def test_evidence_quotes_short_strings_reject() -> None:
    """Defensive: quotes < 8 chars are not falsifiable evidence."""
    entry = {
        "score": 8.0,
        "evidence_quotes": ["short"],
        "evidence": "short",
        "verdict": "PASS",
    }
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match="must include a quoted excerpt",
    ):
        linear_pipeline.validate_llm_review_report(
            _placeholder_other_dims("pedagogical", entry)
        )


def test_evidence_quotes_empty_array_rejects() -> None:
    """An empty list is not evidence — fall back to bare-evidence check."""
    entry = {
        "score": 8.0,
        "evidence_quotes": [],
        "verdict": "PASS",
    }
    with pytest.raises(linear_pipeline.LinearPipelineError, match="missing evidence"):
        linear_pipeline.validate_llm_review_report(
            _placeholder_other_dims("pedagogical", entry)
        )


def test_evidence_quotes_non_list_rejects() -> None:
    """Defensive: a non-list `evidence_quotes` does not satisfy the contract."""
    entry = {
        "score": 8.0,
        "evidence_quotes": "not actually a list",
        "verdict": "PASS",
    }
    with pytest.raises(linear_pipeline.LinearPipelineError, match="missing evidence"):
        linear_pipeline.validate_llm_review_report(
            _placeholder_other_dims("pedagogical", entry)
        )


def test_bare_evidence_with_quote_markers_still_accepted() -> None:
    """Regression guard: the existing pre-PR shape still passes."""
    entry = {
        "score": 8.0,
        "evidence": '"This is a quoted excerpt with literal markers."',
        "verdict": "PASS",
    }
    linear_pipeline.validate_llm_review_report(
        _placeholder_other_dims("pedagogical", entry)
    )


def test_bare_evidence_without_markers_still_rejected() -> None:
    """Regression guard: pre-PR strict-marker check still applies when no
    `evidence_quotes` array is present."""
    entry = {
        "score": 8.0,
        "evidence": "This is text without any literal quote markers",
        "verdict": "PASS",
    }
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match="must include a quoted excerpt",
    ):
        linear_pipeline.validate_llm_review_report(
            _placeholder_other_dims("pedagogical", entry)
        )


# ----- parse_review_response (end-to-end through JSON parse) ----------------

def test_parse_review_response_preserves_evidence_quotes() -> None:
    """The entry returned to the caller should carry `evidence_quotes` so
    downstream telemetry + audit can surface the richer schema."""
    payload = {
        "score": 10.0,
        "evidence_quotes": [
            "Before adding -ся, fix the regular first-conjugation template",
            "The routine vocabulary is small on purpose",
        ],
        "evidence": "Before adding -ся, fix the regular first-conjugation template",
        "verdict": "PASS",
    }
    entry = linear_pipeline.parse_review_response(
        json.dumps(payload),
        dim="pedagogical",
    )
    assert entry["verdict"] == "PASS"
    assert entry.get("evidence_quotes") == payload["evidence_quotes"]


def test_parse_review_response_evidence_quotes_only() -> None:
    """Reviewer omits the bare scalar; only the array is present."""
    payload = {
        "score": 9.0,
        "evidence_quotes": [
            "Before adding -ся, fix the regular first-conjugation template",
        ],
        "verdict": "PASS",
    }
    entry = linear_pipeline.parse_review_response(
        json.dumps(payload),
        dim="pedagogical",
    )
    assert entry["verdict"] == "PASS"
    assert entry["evidence_quotes"] == payload["evidence_quotes"]


def test_parse_review_response_legacy_bare_evidence_still_works() -> None:
    """Regression guard: pre-PR response shape still parses."""
    payload = {
        "score": 8.5,
        "evidence": '"Bare evidence with literal quote markers."',
        "verdict": "PASS",
    }
    entry = linear_pipeline.parse_review_response(
        json.dumps(payload),
        dim="pedagogical",
    )
    assert entry["verdict"] == "PASS"
    assert entry["evidence"] == payload["evidence"]
    assert "evidence_quotes" not in entry
