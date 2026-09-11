"""sources.tool-result.v1 — machine envelopes for Sources MCP tool results.

Additive fields for LLM/eval consumers. V4 authority keys
(``tool``, ``disposition``, ``success``, ``evidence_identifiers``, ``result``)
keep their existing semantics; envelope keys sit alongside them and must never
be folded into ``result`` or into evidence-identifier hash inputs.
"""

from __future__ import annotations

from typing import Any

SCHEMA_V1 = "sources.tool-result.v1"

_STATUS_BY_DISPOSITION: dict[str, str] = {
    "supported": "ok",
    "partial": "ok",
    "not_found": "empty",
    "negative": "empty",
    "ambiguous": "error",
    "invalid_input": "error",
}


def disposition_to_status(disposition: str | None) -> str:
    """Map V4 authority disposition → consumer ``status`` (ok|empty|error)."""
    if not disposition:
        return "error"
    return _STATUS_BY_DISPOSITION.get(disposition, "error")


def enrich_typed_outcome(
    outcome: dict[str, Any],
    *,
    query: dict[str, Any],
    match_count: int,
    hits: list[Any],
    summary_prose: str,
) -> dict[str, Any]:
    """Add v1 envelope keys onto an existing V4 typed outcome (in place + return).

    Does not alter ``disposition`` / ``success`` / ``evidence_identifiers`` /
    ``result``. ``match_count`` should equal ``len(hits)`` when hits are listed.
    """
    if match_count < 0:
        raise ValueError("match_count must be non-negative")
    if match_count != len(hits):
        raise ValueError(f"match_count ({match_count}) must equal len(hits) ({len(hits)})")

    disposition = outcome.get("disposition")
    if not isinstance(disposition, str):
        raise ValueError("typed outcome requires disposition")

    status = disposition_to_status(disposition)
    # Zero listed hits are never "ok" for consumers (e.g. all-missing verify_words
    # keeps disposition=partial but must surface status=empty).
    if match_count == 0 and status == "ok":
        status = "empty"

    outcome["schema"] = SCHEMA_V1
    outcome["status"] = status
    outcome["query"] = dict(query)
    outcome["match_count"] = match_count
    outcome["hits"] = list(hits)
    outcome["summary_prose"] = summary_prose
    return outcome


def build_search_envelope(
    *,
    tool: str,
    query: dict[str, Any],
    hits: list[Any],
    summary_prose: str,
    status: str | None = None,
) -> dict[str, Any]:
    """Envelope for prose-only search/dict tools (no V4 authority recording)."""
    match_count = len(hits)
    if status is None:
        status = "empty" if match_count == 0 else "ok"
    if status not in {"ok", "empty", "error"}:
        raise ValueError(f"invalid status: {status}")
    return {
        "schema": SCHEMA_V1,
        "tool": tool,
        "status": status,
        "query": dict(query),
        "match_count": match_count,
        "hits": list(hits),
        "summary_prose": summary_prose,
    }
