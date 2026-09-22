"""Per-tool search outcome classifier for review receipts (#8430, #8397).

Decides whether a tool call produced no hits, hits but no support, unavailable,
or error from structured facts captured at record time.

Real "no result" forms across the 16 review tools in .mcp/servers/sources/server.py:
----------------------------------------------------------------------------------
Tool                  Line(s) in server.py  "No result" wording / pattern
--------------------  --------------------  --------------------------------------
check_russian_shadow  1200-1202             JSON {"matches_russian": false, "confidence": 0.0}
verify_quote          1264-1275             JSON {"matched": false, "best_confidence": 0.0, "matched_lines": []}
search_text           1737                  "No results found."
search_ua_gec_errors  1891                  f"No UA-GEC results found for: \"{query}\""
verify_words          2095, 2260            "Found: 0/{total}" / all words "- **{word}** — NOT FOUND"
inspect_word          2212                  f"'{word}' — Status: NOT_FOUND"
inspect_words         2260                  all words "- **{word}** — NOT FOUND"
verify_stress         2296                  f"{label} — not_found" / f"{word} — no result"
query_grac            2533, 2546, 2548,     status: "unavailable" (2533), frequency = 0 (2548),
                      2564, 2573            "No concordance results for:" (2564),
                                            "No collocations found for:" (2573),
                                            "GRAC query failed for:" (2546)
query_ulif            2593, 2607, 2625      status: "unavailable" (2593), status: "not_found" (2607),
                                            f"No ULIF paradigm found for: '{word}'" (2625)
query_r2u             2690                  f"No r2u translation found for: '{word}'"
query_sum20           2734                  f"No official offline СУМ-20 entry is currently ingested for '{word}'."
query_pravopys        2838                  f"No pravopys section found for: '{topic}'"
search_style_guide    2924                  f"No results in Антоненко-Давидович for: \"{query}\""
query_cefr_level      2924                  f"No results in PULS CEFR for: \"{query}\""
search_heritage       3033                  f"No heritage evidence found for: \"{query}\""
"""

from __future__ import annotations

import json
import re
from typing import Any

# Table of 16 review tools with cited line numbers in server.py
# and their characteristic "no result" indicator.
REVIEW_TOOL_NO_RESULT_PATTERNS: dict[str, dict[str, Any]] = {
    "check_russian_shadow": {
        "line": 1202,
        "pattern": '{"matches_russian": false}',
    },
    "verify_quote": {
        "line": 1275,
        "pattern": '{"matched": false, "best_confidence": 0.0, "matched_lines": []}',
    },
    "search_text": {
        "line": 1737,
        "pattern": "No results found.",
    },
    "search_ua_gec_errors": {
        "line": 1891,
        "pattern": 'No UA-GEC results found for: "{query}"',
    },
    "verify_words": {
        "line": 2095,
        "pattern": "Found: 0/{total}",
    },
    "inspect_word": {
        "line": 2212,
        "pattern": "'{word}' — Status: NOT_FOUND",
    },
    "inspect_words": {
        "line": 2260,
        "pattern": "- **{word}** — NOT FOUND",
    },
    "verify_stress": {
        "line": 2296,
        "pattern": "{label} — not_found / {word} — no result",
    },
    "query_grac": {
        "line": 2548,
        "pattern": "**{word}**: frequency = 0, relative = 0.00 per million",
    },
    "query_ulif": {
        "line": 2625,
        "pattern": "No ULIF paradigm found for: '{word}'",
    },
    "query_r2u": {
        "line": 2690,
        "pattern": "No r2u translation found for: '{word}'",
    },
    "query_sum20": {
        "line": 2734,
        "pattern": "No official offline СУМ-20 entry is currently ingested for '{word}'.",
    },
    "query_pravopys": {
        "line": 2838,
        "pattern": "No pravopys section found for: '{topic}'",
    },
    "search_style_guide": {
        "line": 2924,
        "pattern": 'No results in Антоненко-Давидович for: "{query}"',
    },
    "query_cefr_level": {
        "line": 2924,
        "pattern": 'No results in PULS CEFR for: "{query}"',
    },
    "search_heritage": {
        "line": 3033,
        "pattern": 'No heritage evidence found for: "{query}"',
    },
}


def _extract_json(text: str) -> Any | None:
    stripped = text.strip()
    if (stripped.startswith("{") and stripped.endswith("}")) or (
        stripped.startswith("[") and stripped.endswith("]")
    ):
        try:
            return json.loads(stripped)
        except Exception:
            pass
    # Check for raw payload embedded in markdown
    raw_match = re.search(r"Raw payload:\s*\n(\{.*\})", stripped, re.DOTALL)
    if raw_match:
        try:
            return json.loads(raw_match.group(1))
        except Exception:
            pass
    return None


def _classify_tool_hits(tool: str, text: str, parsed: Any | None) -> int:
    if tool == "check_russian_shadow":
        if isinstance(parsed, dict):
            return 1 if parsed.get("matches_russian") else 0
        if '"matches_russian": false' in text:
            return 0
        if '"matches_russian": true' in text:
            return 1
        return 0

    if tool == "verify_quote":
        if isinstance(parsed, dict):
            matched_lines = parsed.get("matched_lines")
            if isinstance(matched_lines, list) and matched_lines:
                return len(matched_lines)
            if parsed.get("matched") or float(parsed.get("best_confidence", 0.0) or 0.0) > 0.0:
                return 1
            return 0
        if '"matched": false' in text and '"best_confidence": 0.0' in text:
            return 0
        return 1 if text.strip() else 0

    if tool == "verify_words":
        # Check Found: X/Y pattern first
        found_match = re.search(r"Found:\s*(\d+)/(\d+)", text)
        if found_match:
            return int(found_match.group(1))
        if isinstance(parsed, dict) and "found" in parsed:
            return int(parsed["found"])
        # Check per-word lines
        lines = [line.strip() for line in text.splitlines() if line.strip().startswith("- **")]
        if lines:
            found_count = sum(1 for line in lines if "— FOUND" in line or "— valid" in line)
            return found_count
        return 0 if "NOT FOUND" in text else (1 if text.strip() else 0)

    if tool == "inspect_word":
        if isinstance(parsed, dict) and parsed.get("status") == "NOT_FOUND":
            return 0
        if "— Status: NOT_FOUND" in text or "'status': 'NOT_FOUND'" in text or '"status": "NOT_FOUND"' in text:
            return 0
        if "— Status:" in text:
            return 1
        return 0 if "NOT_FOUND" in text else (1 if text.strip() else 0)

    if tool == "inspect_words":
        if isinstance(parsed, dict) and isinstance(parsed.get("words"), dict):
            found_words = [
                w for w, d in parsed["words"].items()
                if isinstance(d, dict) and d.get("status") != "NOT_FOUND"
            ]
            return len(found_words)
        lines = [line.strip() for line in text.splitlines() if line.strip().startswith("- **")]
        if lines:
            found_count = sum(1 for line in lines if "— NOT FOUND" not in line)
            return found_count
        return 0 if "NOT FOUND" in text else (1 if text.strip() else 0)

    if tool == "verify_stress":
        if isinstance(parsed, dict):
            status = parsed.get("status")
            if status in {"not_found", "invalid_input"}:
                return 0
            if status == "ok":
                matches = parsed.get("matches")
                return len(matches) if isinstance(matches, list) and matches else 1
        if "— not_found" in text or "— no result" in text:
            return 0
        if "— ok:" in text:
            return 1
        return 0 if "not_found" in text else (1 if text.strip() else 0)

    if tool == "query_sum20":
        if "No official offline СУМ-20 entry is currently ingested" in text:
            return 0
        if "**Official СУМ-20 entries for" in text:
            return 1
        return 0 if "No official" in text else (1 if text.strip() else 0)

    if tool == "query_ulif":
        if isinstance(parsed, dict) and parsed.get("status") == "not_found":
            return 0
        if "No ULIF paradigm found for:" in text:
            return 0
        if "Paradigm for" in text or "Ambiguous ULIF spelling" in text:
            return 1
        return 0 if "No ULIF" in text else (1 if text.strip() else 0)

    if tool == "query_r2u":
        if "No r2u translation found for:" in text:
            return 0
        if "translations for" in text:
            return 1
        return 0 if "No r2u" in text else (1 if text.strip() else 0)

    if tool == "query_pravopys":
        if "No pravopys section found for:" in text:
            return 0
        if "**Pravopys section" in text:
            return 1
        return 0 if "No pravopys" in text else (1 if text.strip() else 0)

    if tool == "search_style_guide":
        if "No results in Антоненко-Давидович for:" in text or "No results in style_guide for:" in text:
            return 0
        if "results in **Антоненко-Давидович**" in text or "Found " in text:
            return 1
        return 0 if "No results" in text else (1 if text.strip() else 0)

    if tool == "query_cefr_level":
        if "No results in PULS CEFR for:" in text:
            return 0
        if "results in **PULS CEFR**" in text or "Found " in text:
            return 1
        return 0 if "No results" in text else (1 if text.strip() else 0)

    if tool == "search_heritage":
        if "No heritage evidence found for:" in text:
            return 0
        if "heritage evidence row" in text or "Found " in text:
            return 1
        return 0 if "No heritage" in text else (1 if text.strip() else 0)

    if tool == "search_ua_gec_errors":
        if "No UA-GEC results found for:" in text or "No UA-GEC results found" in text:
            return 0
        if "human-annotated error pairs" in text or "Found " in text:
            return 1
        return 0 if "No UA-GEC" in text else (1 if text.strip() else 0)

    if tool == "search_text":
        if text.strip() == "No results found." or text.strip().startswith("No results found"):
            return 0
        if "results for:" in text or "Found " in text:
            return 1
        return 0 if "No results" in text else (1 if text.strip() else 0)

    if tool == "query_grac":
        if "frequency = 0," in text or "frequency = 0 " in text or "total frequency: 0" in text:
            return 0
        if (
            "No concordance results for:" in text
            or "No collocations found for:" in text
            or "GRAC query failed for:" in text
            or "GRAC lemma query failed for:" in text
        ):
            return 0
        if "frequency = " in text or "Concordance for" in text or "Collocations for" in text:
            return 1
        return 0 if "failed" in text or "No " in text else (1 if text.strip() else 0)

    # Generic fallback
    if any(marker in text.casefold() for marker in ("no result", "no hits", "not found", "0 results")):
        return 0
    return 1 if text.strip() else 0


def classify_outcome(tool: str, status: str, result: str) -> dict[str, Any]:
    """Derive structured outcome_facts from tool call status and result text/JSON."""
    if status == "error":
        return {"call_status": "error", "hits": 0, "status": "error", "unavailable": False}
    if status == "refused":
        return {"call_status": "refused", "hits": 0, "status": "refused", "unavailable": False}

    text = result if isinstance(result, str) else ""
    stripped = text.strip()
    parsed = _extract_json(text)

    # Check for unavailable status / marker
    unavailable = (
        "unavailable" in text.casefold()
        or (isinstance(parsed, dict) and parsed.get("status") == "unavailable")
    )
    if unavailable:
        return {"call_status": "ok", "hits": 0, "status": "unavailable", "unavailable": True}

    if stripped == "" or stripped == "No results found.":
        return {"call_status": "ok", "hits": 0, "status": "no_hits", "unavailable": False}

    hits = _classify_tool_hits(tool, text, parsed)
    if hits == 0:
        return {"call_status": "ok", "hits": 0, "status": "no_hits", "unavailable": False}
    return {"call_status": "ok", "hits": hits, "status": "hits_found", "unavailable": False}
