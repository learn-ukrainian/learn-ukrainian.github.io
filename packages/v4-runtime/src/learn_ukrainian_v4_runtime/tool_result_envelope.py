"""sources.tool-result.v1 — machine envelopes for Sources MCP tool results.

Additive fields for LLM/eval consumers. V4 authority keys
(``tool``, ``disposition``, ``success``, ``evidence_identifiers``, ``result``)
keep their existing semantics; envelope keys sit alongside them and must never
be folded into ``result`` or into evidence-identifier hash inputs.
"""

from __future__ import annotations

from typing import Any

SCHEMA_V1 = "sources.tool-result.v1"

# FTS keyword floor used by search_text / search_literary MCP handlers.
# Tokens shorter than this are dropped before SQLite FTS; empty results that
# dropped tokens expose them under diagnostics.dropped_tokens (#7956 option B).
FTS_MIN_TOKEN_LENGTH = 3
FTS_DROP_REASON_MIN_LENGTH = "min_token_length"

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


def split_fts_keywords(
    query: str,
    *,
    min_length: int = FTS_MIN_TOKEN_LENGTH,
) -> tuple[set[str], list[dict[str, str]]]:
    """Split a free-text query into kept FTS keywords and dropped-token records.

    Dropped entries use ``reason=min_token_length`` so empty envelopes can
    explain why a short Ukrainian pedagogical query produced zero hits.
    """
    kept: set[str] = set()
    dropped: list[dict[str, str]] = []
    for raw in query.lower().split():
        token = raw.strip()
        if not token:
            continue
        if len(token) >= min_length:
            kept.add(token)
        else:
            dropped.append({"token": token, "reason": FTS_DROP_REASON_MIN_LENGTH})
    return kept, dropped


def dropped_tokens_diagnostics(
    dropped: list[dict[str, str]],
) -> dict[str, Any] | None:
    """Build ``diagnostics`` only when at least one token was dropped."""
    if not dropped:
        return None
    return {"dropped_tokens": list(dropped)}


def build_search_envelope(
    *,
    tool: str,
    query: dict[str, Any],
    hits: list[Any],
    summary_prose: str,
    status: str | None = None,
    diagnostics: dict[str, Any] | None = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    """Envelope for prose-only search/dict tools (no V4 authority recording)."""
    match_count = len(hits)
    if status is None:
        status = "empty" if match_count == 0 else "ok"
    if status not in {"ok", "empty", "error"}:
        raise ValueError(f"invalid status: {status}")
    if status == "error" and not error_code:
        raise ValueError("error_code is required when status='error'")
    if status != "error" and error_code is not None:
        raise ValueError("error_code is only valid when status='error'")
    envelope: dict[str, Any] = {
        "schema": SCHEMA_V1,
        "tool": tool,
        "status": status,
        "query": dict(query),
        "match_count": match_count,
        "hits": list(hits),
        "summary_prose": summary_prose,
    }
    if diagnostics is not None:
        envelope["diagnostics"] = diagnostics
    if error_code is not None:
        envelope["error_code"] = error_code
    return envelope
