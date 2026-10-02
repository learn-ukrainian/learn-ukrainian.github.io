"""Read-only first-listed Pohribnyi dictionary choices, never ULIF's heuristic.

The ingested 1992 pronunciation booklet is prose, not a variant table. Only
explicitly attributed orthoepic dictionary entries with machine-readable
accented headwords can supply a teaching choice. Missing entries stay pending.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3


def dictionary_rows() -> list[dict] | None:
    """Return corpus entries; None denotes an unavailable dictionary mirror."""
    from scripts.wiki.sources_db import _get_conn

    try:
        return [
            dict(row)
            for row in _get_conn().execute(
                "SELECT id,word,normalized_word,dictionary_label,title,text,source_url "
                "FROM slovnyk_me_entries WHERE dictionary_slug='orthoepy' ORDER BY id"
            )
        ]
    except (sqlite3.Error, OSError):
        return None


def source_info() -> dict:
    """Hash the exact teaching-source corpus independently of ULIF and trie."""
    rows = dictionary_rows()
    return {
        "dictionary": "Pohribnyi orthoepic dictionary, first-listed variant",
        "available": rows is not None,
        "rows": len(rows or []),
        "digest": hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
    }


def sourced_teaching_choice(form: str, allowed: list[int]) -> dict | None:
    """Choose only an exact-form first variant in an explicitly attributed entry."""
    from scripts.verification.stress import _stress_positions_in_marked_string, _strip_stress, transfer_stress_marks
    from scripts.wiki.sources_db import normalize_ulif_dictua_query

    choices = {}
    for row in dictionary_rows() or []:
        attribution = f"{row['dictionary_label']} {row['title']}".casefold()
        if "погрібн" not in attribution and "pohribn" not in attribution:
            continue
        if normalize_ulif_dictua_query(row["word"]) != normalize_ulif_dictua_query(form):
            continue
        # Reject OCR with lost accents and embedded prose rather than inferring
        # stress from spacing, capitals, transcription or a different inflection.
        token = re.match(r"\s*([А-Яа-яЄєІіЇїҐґ'’ʼ\u0301\u0300-]+)", row["text"])
        if not token:
            continue
        marked = token.group(1)
        bare, indices = _stress_positions_in_marked_string(marked)
        if normalize_ulif_dictua_query(_strip_stress(bare)) != normalize_ulif_dictua_query(form):
            continue
        if len(indices) != 1 or indices[0] not in allowed:
            continue
        choice = transfer_stress_marks(marked, form)
        choices.setdefault(choice, []).append(
            {
                "dictionary": "Pohribnyi orthoepic dictionary",
                "row_id": row["id"],
                "url": row["source_url"],
                "text_sha256": hashlib.sha256(row["text"].encode()).hexdigest(),
            }
        )
    if len(choices) != 1:
        return None
    choice, evidence = next(iter(choices.items()))
    return {"pedagogical_stressed_form": choice, "pedagogical_source": evidence}
