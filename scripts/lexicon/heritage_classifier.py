#!/usr/bin/env python3
"""Deterministic local heritage-status classifier for Word Atlas and gates.

The classifier is deliberately source-backed and offline-only. VESUM proves
modern standard status; heritage dictionaries and verified corpus quotes prove
authentic non-VESUM status; Russian-shadow morphology is recorded as a warning
signal but never decides by itself.
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCES_DB = ROOT / "data" / "sources.db"
LT_REPLACEMENTS = ROOT / "data" / "lt_replacements.json"

_CYRILLIC_WORD_CHARS = "A-Za-zА-Яа-яЄєІіЇїҐґ0-9'’ʼ-"
_ACUTE_RE = re.compile("[\u0301\u0300]")
_SPACE_RE = re.compile(r"\s+")

_AUTHENTIC_CLASSIFICATIONS = {
    "authentic-archaism",
    "dialect",
    "historism",
    "borrowing",
    "standard",
}

_KNOWN_STANDARD_ALTERNATIVES: dict[str, tuple[str, ...]] = {
    "аранжировка": ("аранжування",),
    "діюча": ("чинна",),
    "діючий": ("чинний", "дійовий"),
    "діючі": ("чинні",),
    "протиріччя": ("суперечність",),
}

_SURFACE_QUOTE_HINTS: dict[str, tuple[str, str]] = {
    # Spec evidence case: exact Kupala quotation in ЕУ-1955 literary_texts.
    "другоє": ("на другоє літо поховаємо", "authentic-archaism"),
}

_DIALECT_OR_FOLK_TERMS = {
    "гагілка",
    "гагілки",
    "гаївка",
    "гаївки",
    "риндзівка",
    "риндзівки",
    "ягівка",
    "ягівки",
    "ягілка",
    "ягілки",
}


def classify_lemma(lemma: str) -> dict[str, Any]:
    """Classify a lemma for Word Atlas ``heritage_status`` badges."""
    variants = _lemma_variants(lemma)
    if len(variants) <= 1:
        return _classify(variants[0] if variants else "", surface=False)
    return _merge_variant_statuses([_classify(variant, surface=False) for variant in variants])


def classify_surface_form(form: str) -> dict[str, Any]:
    """Classify an inflected/surface form for VESUM-gate importers."""
    term = _normalize_word(form)
    return _classify(term, surface=True)


def _classify(term: str, *, surface: bool) -> dict[str, Any]:
    if not term:
        return _status("unknown", [], is_russianism=False, russian_shadow=False)

    russian_shadow, russian_shadow_detail = _check_russian_shadow(term)
    sovietization_risk = _sum11_sovietization_risk_for_term(term)

    vesum = _vesum_attestation(term, surface=surface)
    if vesum:
        return _status(
            "standard",
            [vesum],
            is_russianism=False,
            russian_shadow=russian_shadow,
            sovietization_risk=sovietization_risk,
        )

    russianism = _russianism_status(term, russian_shadow=russian_shadow)

    attestations: list[dict[str, Any]] = []
    classification = "unknown"
    with _source_conn() as conn:
        auth_hits = _dictionary_attestations(conn, term, surface=surface)
        for hit in auth_hits:
            attestations.append(hit["attestation"])
            classification = _prefer_classification(classification, hit["classification"])
            sovietization_risk = max(sovietization_risk, int(hit.get("sovietization_risk") or 0))

        if surface and not attestations and russianism and term in _KNOWN_STANDARD_ALTERNATIVES:
            return russianism

        if surface and (not attestations or term in _SURFACE_QUOTE_HINTS):
            quote_hits = _literary_surface_attestations(conn, term)
            for hit in quote_hits:
                attestations.append(hit["attestation"])
                classification = _prefer_classification(classification, hit["classification"])

    if attestations and classification in _AUTHENTIC_CLASSIFICATIONS:
        return _status(
            classification,
            attestations,
            is_russianism=False,
            russian_shadow=russian_shadow,
            sovietization_risk=sovietization_risk,
        )

    if russianism:
        return russianism

    calque_warning = _calque_warning(term, russian_shadow_detail)
    return _status(
        "unknown",
        [],
        is_russianism=False,
        russian_shadow=russian_shadow,
        calque_warning=calque_warning,
    )


def _status(
    classification: str,
    attestations: list[dict[str, Any]],
    *,
    is_russianism: bool,
    russian_shadow: bool,
    sovietization_risk: int = 0,
    calque_warning: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "classification": classification,
        "attestations": _dedupe_attestations(attestations),
        "is_russianism": is_russianism,
        "russian_shadow": russian_shadow,
        "sovietization_risk": sovietization_risk,
        "calque_warning": calque_warning,
    }


def _source_conn() -> sqlite3.Connection:
    if not SOURCES_DB.exists():
        raise FileNotFoundError(f"local sources database not found: {SOURCES_DB}")
    conn = sqlite3.connect(f"file:{SOURCES_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _normalize_word(word: str) -> str:
    text = html.unescape(str(word or "")).strip().casefold()
    text = _ACUTE_RE.sub("", text)
    text = text.replace("`", "'").replace("’", "ʼ")
    return _SPACE_RE.sub(" ", text)


def _lemma_variants(lemma: str) -> list[str]:
    variants: list[str] = []
    seen: set[str] = set()
    for part in re.split(r"[/,]", str(lemma or "")):
        term = _normalize_word(part)
        if term and term not in seen:
            seen.add(term)
            variants.append(term)
    return variants


def _is_single_token(term: str) -> bool:
    return bool(re.fullmatch(r"[А-Яа-яЄєІіЇїҐґ'’ʼ-]+", term))


def _clean_text(text: object, *, limit: int = 500) -> str:
    cleaned = _SPACE_RE.sub(" ", html.unescape(str(text or ""))).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _whole_token_pattern(term: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![{_CYRILLIC_WORD_CHARS}]){re.escape(term)}(?![{_CYRILLIC_WORD_CHARS}])",
        re.IGNORECASE,
    )


def _contains_whole_token(text: str, term: str) -> bool:
    return bool(_whole_token_pattern(term).search(_normalize_word(text)))


def _apostrophe_variants(term: str) -> tuple[str, ...]:
    variants = {term}
    for char in ("'", "’", "ʼ"):
        if char in term:
            for replacement in ("'", "’", "ʼ"):
                variants.add(term.replace(char, replacement))
    return tuple(sorted(variants))


def _vesum_attestation(term: str, *, surface: bool) -> dict[str, Any] | None:
    try:
        if surface:
            from scripts.verification.vesum import verify_word

            matches = verify_word(term)
            if not matches:
                return None
            lemmas = sorted({str(match.get("lemma") or "") for match in matches if match.get("lemma")})
            return {
                "source": "VESUM",
                "ref": ",".join(lemmas) or term,
                "detail": f"word_form match ({len(matches)} form analysis)",
            }

        from scripts.verification.vesum import verify_lemma, verify_word

        forms = verify_lemma(term)
        if forms:
            return {
                "source": "VESUM",
                "ref": term,
                "detail": f"lemma match ({len(forms)} forms)",
            }
        matches = verify_word(term)
        if matches:
            lemmas = sorted({str(match.get("lemma") or "") for match in matches if match.get("lemma")})
            return {
                "source": "VESUM",
                "ref": ",".join(lemmas) or term,
                "detail": "word_form match for lemma query",
            }
    except Exception:
        return None
    return None


def _check_russian_shadow(term: str) -> tuple[bool, dict[str, Any]]:
    if not _is_single_token(term):
        return False, {"available": False, "reason": "not_single_token"}
    try:
        from scripts.verification.check_ru_morph import is_russian_pattern

        result = is_russian_pattern(term)
    except Exception as exc:
        return False, {"available": False, "error": str(exc)}
    return bool(result.get("matches_russian")), {"available": True, **result}


def _dictionary_attestations(
    conn: sqlite3.Connection,
    term: str,
    *,
    surface: bool,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    hits.extend(_grinchenko_exact_hits(conn, term))
    hits.extend(_esum_exact_hits(conn, term))
    hits.extend(_sum11_exact_hits(conn, term))
    hits.extend(_wiktionary_exact_hits(conn, term))
    hits.extend(_grinchenko_crossref_hits(conn, term))
    hits.extend(_esum_variant_hits(conn, term))
    if surface:
        hits.extend(_grinchenko_surface_usage_hits(conn, term))
    return hits


def _grinchenko_exact_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    hits = []
    for variant in _apostrophe_variants(term):
        rows = conn.execute(
            "SELECT id, word, definition, source FROM grinchenko WHERE lower(word) = ? LIMIT 3",
            (variant,),
        ).fetchall()
        for row in rows:
            text = _clean_text(row["definition"])
            hits.append(
                {
                    "classification": _classification_from_definition(text, default="authentic-archaism"),
                    "attestation": {
                        "source": "grinchenko_1907",
                        "ref": str(row["id"]),
                        "word": row["word"],
                        "detail": text,
                    },
                    "sovietization_risk": 0,
                }
            )
    return hits


def _grinchenko_crossref_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, word, definition, source FROM grinchenko WHERE lower(definition) LIKE ? LIMIT 20",
        (f"%{term}%",),
    ).fetchall()
    hits = []
    crossref_re = re.compile(rf"(?:=|див\.)\s*{re.escape(term)}(?=\W|$)", re.IGNORECASE)
    for row in rows:
        definition = _normalize_word(row["definition"])
        if not crossref_re.search(definition):
            continue
        text = _clean_text(row["definition"])
        hits.append(
            {
                "classification": _classification_from_definition(text, default="dialect"),
                "attestation": {
                    "source": "grinchenko_1907",
                    "ref": str(row["id"]),
                    "word": row["word"],
                    "detail": text,
                },
                "sovietization_risk": 0,
            }
        )
    return hits


def _grinchenko_surface_usage_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, word, definition, source FROM grinchenko WHERE lower(definition) LIKE ? LIMIT 8",
        (f"%{term}%",),
    ).fetchall()
    hits = []
    for row in rows:
        if not _contains_whole_token(str(row["definition"]), term):
            continue
        text = _clean_text(row["definition"])
        hits.append(
            {
                "classification": _classification_from_definition(text, default=_form_default_classification(term)),
                "attestation": {
                    "source": "grinchenko_1907",
                    "ref": str(row["id"]),
                    "word": row["word"],
                    "detail": text,
                },
                "sovietization_risk": 0,
            }
        )
    return hits


def _sum11_exact_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    hits = []
    has_flag_columns = _source_sum11_has_flag_columns()
    fields = "id, word, definition, text, source"
    if has_flag_columns:
        fields += ", sovietization_risk, sovietization_keywords"
    for variant in _apostrophe_variants(term):
        rows = conn.execute(
            f"SELECT {fields} FROM sum11 WHERE lower(word) = ? LIMIT 3",
            (variant,),
        ).fetchall()
        for row in rows:
            text = _clean_text(row["definition"])
            risk = _sum11_row_sovietization_risk(row, has_flag_columns=has_flag_columns)
            hits.append(
                {
                    "classification": _classification_from_definition(text, default="standard"),
                    "attestation": {
                        "source": "sum11",
                        "ref": str(row["id"]),
                        "word": row["word"],
                        "detail": text,
                    },
                    "sovietization_risk": risk,
                }
            )
    return hits


def _sum11_has_flag_columns(conn: sqlite3.Connection) -> bool:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(sum11);").fetchall()}
    return {"sovietization_risk", "sovietization_keywords"}.issubset(cols)


@lru_cache(maxsize=8)
def _sum11_has_flag_columns_for_db(
    db_path: str,
    mtime_ns: int,
    size: int,
) -> bool:
    del mtime_ns, size  # cache-key invalidators; not used in the query itself.
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return _sum11_has_flag_columns(conn)
    finally:
        conn.close()


def _source_sum11_has_flag_columns() -> bool:
    try:
        stat = SOURCES_DB.stat()
        return _sum11_has_flag_columns_for_db(
            str(SOURCES_DB.resolve()),
            stat.st_mtime_ns,
            stat.st_size,
        )
    except (OSError, sqlite3.Error):
        return False


def _sum11_row_sovietization_risk(
    row: sqlite3.Row,
    *,
    has_flag_columns: bool,
) -> int:
    if has_flag_columns:
        try:
            return int(row["sovietization_risk"] or 0)
        except (IndexError, KeyError, TypeError, ValueError):
            return 0
    return _sum11_sovietization_risk(str(row["definition"] or ""), str(row["text"] or ""))


def _sum11_sovietization_risk_for_term(term: str) -> int:
    try:
        has_flag_columns = _source_sum11_has_flag_columns()
        with _source_conn() as conn:
            if has_flag_columns:
                risk = 0
                for variant in _apostrophe_variants(term):
                    row = conn.execute(
                        "SELECT MAX(sovietization_risk) FROM sum11 WHERE lower(word) = ?",
                        (variant,),
                    ).fetchone()
                    if row:
                        risk = max(risk, int(row[0] or 0))
                return risk

            risk = 0
            for variant in _apostrophe_variants(term):
                rows = conn.execute(
                    "SELECT definition, text FROM sum11 WHERE lower(word) = ? LIMIT 3",
                    (variant,),
                ).fetchall()
                for row in rows:
                    risk = max(
                        risk,
                        _sum11_sovietization_risk(
                            str(row["definition"] or ""),
                            str(row["text"] or ""),
                        ),
                    )
            return risk
    except (FileNotFoundError, sqlite3.Error):
        return 0


def _esum_exact_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    if not _table_exists(conn, "esum_etymology_meta"):
        return []
    hits = []
    for variant in _apostrophe_variants(term):
        rows = conn.execute(
            """
            SELECT id, lemma, etymology_text, cognates, vol, page, source
            FROM esum_etymology_meta
            WHERE lemma = ? COLLATE NOCASE
            ORDER BY vol, page, lemma
            LIMIT 3
            """,
            (variant,),
        ).fetchall()
        for row in rows:
            hits.append(_esum_hit(term, row, exact=True))
    return hits


def _esum_variant_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    if not _table_exists(conn, "esum_etymology_meta"):
        return []
    if term not in _DIALECT_OR_FOLK_TERMS:
        return []

    rows: list[sqlite3.Row] = []
    if _table_exists(conn, "esum_etymology"):
        try:
            rows = conn.execute(
                """
                SELECT rowid AS id, lemma, etymology_text, cognates, vol, page, 'ЕСУМ' AS source
                FROM esum_etymology
                WHERE esum_etymology MATCH ?
                ORDER BY rank
                LIMIT 20
                """,
                (_fts_phrase_query(term),),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []

    if not rows:
        rows = conn.execute(
            """
            SELECT id, lemma, etymology_text, cognates, vol, page, source
            FROM esum_etymology_meta
            WHERE lower(etymology_text) LIKE ?
            ORDER BY vol, page, lemma
            LIMIT 20
            """,
            (f"%{term}%",),
        ).fetchall()

    hits = []
    for row in rows:
        if _normalize_word(row["lemma"]) == term:
            continue
        if not _contains_whole_token(str(row["etymology_text"] or ""), term):
            continue
        hit = _esum_hit(term, row, exact=False)
        if hit["classification"] == "standard":
            continue
        hits.append(hit)
    return hits


def _esum_hit(term: str, row: sqlite3.Row, *, exact: bool) -> dict[str, Any]:
    text = _clean_text(row["etymology_text"])
    return {
        "classification": _classification_from_etymology(text, term, exact=exact),
        "attestation": {
            "source": "esum",
            "ref": f"{row['lemma']}:{row['vol']}:{row['page']}",
            "word": row["lemma"] if not exact else term,
            "detail": text,
        },
        "sovietization_risk": 0,
    }


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _wiktionary_exact_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    hits = []
    for variant in _apostrophe_variants(term):
        rows = conn.execute(
            "SELECT id, word, definitions, text, source FROM wiktionary WHERE lower(word) = ? LIMIT 3",
            (variant,),
        ).fetchall()
        for row in rows:
            text = _clean_text(row["text"] or row["definitions"])
            hits.append(
                {
                    "classification": _classification_from_definition(text, default="standard"),
                    "attestation": {
                        "source": "wiktionary",
                        "ref": str(row["id"]),
                        "word": row["word"],
                        "detail": text,
                    },
                    "sovietization_risk": 0,
                }
            )
    return hits


def _classification_from_definition(text: str, *, default: str) -> str:
    lower = _normalize_word(text)
    if "діал." in lower or " діал " in lower or "діалект" in lower:
        return "dialect"
    if "іст." in lower or "істор." in lower:
        return "historism"
    if "заст." in lower or "застар" in lower:
        return "authentic-archaism"
    return default


def _classification_from_etymology(text: str, term: str, *, exact: bool) -> str:
    lower = _normalize_word(text)
    if term in _DIALECT_OR_FOLK_TERMS:
        return "dialect"
    if any(marker in lower for marker in (" діал", "діал.", "говір", "гуц", "бойк", "лемк", "поділ")):
        return "dialect"
    if "іст." in lower or "істор." in lower:
        return "historism"
    if "заст." in lower or "застар" in lower:
        return "authentic-archaism"
    if "запозич" in lower:
        return "borrowing"
    return "authentic-archaism" if exact else "standard"


def _sum11_sovietization_risk(definition: str, text: str) -> int:
    try:
        from scripts.audit.sum11_sovietization_scan import classify_entry

        risk, _keywords = classify_entry(definition, text)
    except Exception:
        return 0
    return int(risk)


def _literary_surface_attestations(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    hint = _SURFACE_QUOTE_HINTS.get(term)
    if hint:
        phrase, classification = hint
        rows = _verified_literary_quote_rows(conn, phrase)
        hits = []
        for row in rows:
            if phrase not in _normalize_quote(row["text"]):
                continue
            hits.append(
                {
                    "classification": classification,
                    "attestation": {
                        "source": "literary_fts",
                        "ref": row["chunk_id"],
                        "quote": phrase,
                        "score": 1.0,
                        "detail": _literary_ref_detail(row),
                    },
                }
            )
        if hits:
            return hits

    return _literary_term_hits(conn, term)


def _verified_literary_quote_rows(conn: sqlite3.Connection, phrase: str) -> list[sqlite3.Row]:
    query = _fts_phrase_query(phrase)
    rows: list[sqlite3.Row] = []
    if query:
        try:
            rows = conn.execute(
                """
                SELECT t.chunk_id, t.author, t.work, t.source_file, t.year, t.language_period, t.text
                FROM literary_fts f
                JOIN literary_texts t ON t.id = f.rowid
                WHERE literary_fts MATCH ?
                ORDER BY t.chunk_id
                LIMIT 50
                """,
                (query,),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []

    normalized_phrase = _normalize_quote(phrase)
    verified = [row for row in rows if normalized_phrase in _normalize_quote(row["text"])]
    if verified:
        return verified

    return conn.execute(
        """
        SELECT chunk_id, author, work, source_file, year, language_period, text
        FROM literary_texts
        WHERE lower(text) LIKE ?
        ORDER BY chunk_id
        LIMIT 50
        """,
        (f"%{normalized_phrase}%",),
    ).fetchall()


def _literary_term_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    query = _fts_phrase(term)
    if not query:
        return []
    try:
        rows = conn.execute(
            """
            SELECT t.chunk_id, t.author, t.work, t.source_file, t.year, t.language_period, t.text,
                   bm25(literary_fts) AS rank
            FROM literary_fts f
            JOIN literary_texts t ON t.id = f.rowid
            WHERE literary_fts MATCH ?
            ORDER BY rank
            LIMIT 10
            """,
            (query,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []

    hits = []
    for row in rows:
        if not _contains_whole_token(str(row["text"]), term):
            continue
        hits.append(
            {
                "classification": _literary_classification(term, row),
                "attestation": {
                    "source": "literary_fts",
                    "ref": row["chunk_id"],
                    "quote": _snippet_around(str(row["text"]), term),
                    "score": 1.0,
                    "detail": _literary_ref_detail(row),
                },
            }
        )
    return hits[:3]


def _fts_phrase(term: str) -> str:
    if not re.fullmatch(r"[А-Яа-яЄєІіЇїҐґ'’ʼ-]+", term):
        return ""
    return '"' + term.replace('"', '""') + '"'


def _fts_phrase_query(text: str) -> str:
    tokens = re.findall(r"[А-Яа-яЄєІіЇїҐґA-Za-z0-9'’ʼ-]+", _normalize_word(text))
    if not tokens:
        return ""
    return '"' + " ".join(token.replace('"', '""') for token in tokens) + '"'


def _normalize_quote(text: object) -> str:
    return _SPACE_RE.sub(" ", _normalize_word(str(text))).strip(" .,;:!?«»\"“”")


def _snippet_around(text: str, term: str, *, radius: int = 90) -> str:
    normalized_text = _normalize_word(text)
    idx = normalized_text.find(term)
    if idx < 0:
        return _clean_text(text, limit=220)
    start = max(0, idx - radius)
    end = min(len(text), idx + len(term) + radius)
    return _clean_text(text[start:end], limit=220)


def _literary_ref_detail(row: sqlite3.Row) -> str:
    pieces = [str(row[key] or "") for key in ("author", "work", "source_file") if row[key]]
    if row["year"]:
        pieces.append(str(row["year"]))
    if row["language_period"]:
        pieces.append(str(row["language_period"]))
    return "; ".join(pieces)


def _literary_classification(term: str, row: sqlite3.Row) -> str:
    period = str(row["language_period"] or "")
    if period in {"middle_ukrainian", "old_east_slavic"} or _looks_archaic_form(term):
        return "authentic-archaism"
    if term in _DIALECT_OR_FOLK_TERMS:
        return "dialect"
    return "standard"


def _form_default_classification(term: str) -> str:
    if _looks_archaic_form(term):
        return "authentic-archaism"
    if term in _DIALECT_OR_FOLK_TERMS:
        return "dialect"
    return "standard"


def _looks_archaic_form(term: str) -> bool:
    return term.endswith(("ая", "еє", "єє", "оє", "ую"))


def _russianism_status(term: str, *, russian_shadow: bool) -> dict[str, Any] | None:
    alternatives = _standard_alternatives(term)
    if not alternatives:
        return None
    attestations = [
        {
            "source": "standard_alternative",
            "ref": alternative,
            "detail": f"Ukrainian standard alternative for {term}",
        }
        for alternative in alternatives
    ]
    source = "heritage_spec"
    if _lt_alternatives(term):
        source = "lt_replacements"
    attestations.append(
        {
            "source": source,
            "ref": "docs/best-practices/heritage-attestation-engine.md",
            "detail": "local correction evidence; no authentic dictionary attestation found",
        }
    )
    return _status(
        "russianism",
        attestations,
        is_russianism=True,
        russian_shadow=russian_shadow,
        calque_warning={"standard_alternatives": alternatives},
    )


def _standard_alternatives(term: str) -> list[str]:
    alternatives = list(_KNOWN_STANDARD_ALTERNATIVES.get(term, ()))
    for alternative in _lt_alternatives(term):
        if alternative not in alternatives:
            alternatives.append(alternative)
    return alternatives


def _lt_alternatives(term: str) -> list[str]:
    if not LT_REPLACEMENTS.exists():
        return []
    try:
        data = json.loads(LT_REPLACEMENTS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    row = data.get(term)
    if not isinstance(row, dict):
        return []
    suggestions = row.get("suggestions")
    if not isinstance(suggestions, list):
        return []
    return [str(suggestion) for suggestion in suggestions[:5] if suggestion]


def _calque_warning(term: str, russian_shadow_detail: dict[str, Any]) -> dict[str, Any] | None:
    if russian_shadow_detail.get("matches_russian"):
        return {
            "type": "russian_shadow_only",
            "russian_lemma": russian_shadow_detail.get("russian_lemma"),
            "confidence": russian_shadow_detail.get("confidence"),
            "note": "negative signal only; no Ukrainian standard alternative was found",
        }
    return None


def _prefer_classification(current: str, candidate: str) -> str:
    priority = {
        "dialect": 80,
        "historism": 75,
        "authentic-archaism": 70,
        "borrowing": 60,
        "standard": 50,
        "unknown": 0,
    }
    return candidate if priority.get(candidate, 0) > priority.get(current, 0) else current


def _merge_variant_statuses(statuses: list[dict[str, Any]]) -> dict[str, Any]:
    classification = "unknown"
    attestations: list[dict[str, Any]] = []
    calque_warning = None
    for status in statuses:
        if status["classification"] in _AUTHENTIC_CLASSIFICATIONS:
            classification = _prefer_classification(classification, str(status["classification"]))
        elif classification == "unknown" and status["classification"] == "russianism":
            classification = "russianism"
        attestations.extend(status.get("attestations") or [])
        if not calque_warning and status.get("calque_warning"):
            calque_warning = status["calque_warning"]

    is_russianism = classification == "russianism" and all(status.get("is_russianism") for status in statuses)
    return _status(
        classification,
        attestations,
        is_russianism=is_russianism,
        russian_shadow=any(bool(status.get("russian_shadow")) for status in statuses),
        sovietization_risk=max(int(status.get("sovietization_risk") or 0) for status in statuses),
        calque_warning=calque_warning if classification == "russianism" else None,
    )


def _dedupe_attestations(attestations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped = []
    for item in attestations:
        source = str(item.get("source") or "")
        ref = str(item.get("ref") or "")
        key = (source, ref)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
