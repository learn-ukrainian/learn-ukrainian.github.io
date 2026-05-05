"""Helpers for bounded slovnyk.me dictionary lookups.

The project deliberately does not bulk-crawl slovnyk.me. The helpers here
support explicit per-word lookup plus a small SQLite table for curated
verification snapshots / URL references.
"""

from __future__ import annotations

import datetime as dt
import html
import re
import sqlite3
from html.parser import HTMLParser
from typing import Any
from urllib.parse import quote

import requests

try:
    from audit.sum11_sovietization_scan import classify_entry
except ImportError:  # pragma: no cover - direct package import fallback
    from scripts.audit.sum11_sovietization_scan import classify_entry

SLOVNYK_ME_BASE = "https://slovnyk.me"
DEFAULT_USER_AGENT = (
    "learn-ukrainian-slovnyk-me/1.0 "
    "(noncommercial educational verification; issue 1715)"
)

# Canonical slugs are taken from https://slovnyk.me/ direct dictionary links.
SLOVNYK_ME_DICTS: dict[str, str] = {
    "newsum": "Словник української мови у 20 томах (СУМ-20)",
    "sum": "Словник української мови в 11 томах (СУМ-11)",
    "vts": "Великий тлумачний словник сучасної української мови",
    "hrinchenko": "Словник української мови Грінченка",
    "holoskevych": "Правописний словник Голоскевича (1929)",
    "obsolete_words": "Словник застарілих та маловживаних слів",
    "bukovina": "Українська літературна мова на Буковині",
    "franko": "Словник з творів Івана Франка",
    "literary_encyclopedia": "Українська літературна енциклопедія",
    "slang_lviv": "Лексикон львівський: поважно і на жарт",
    "slang": "Словник жарґонної лексики української мови",
    "slang_modern": "Словник сучасного українського сленгу",
    "synonyms_karavansky": "Словник синонімів Караванського",
    "synonyms": "Словник синонімів української мови",
    "phraseology": "Фразеологічний словник української мови",
    "davydov": "«Як ми говоримо» Антоненка-Давидовича",
    "khreshchatyk": "«Уроки державної мови» з газети «Хрещатик»",
    "linguistic_norm": "Літературне слововживання",
    "voloschak": "Неправильно-правильно",
    "orthography": "Орфографічний словник української мови",
    "orthoepy": "Орфоепічний словник української мови",
    "foreign_melnychuk": "Словник іншомовних слів Мельничука",
    "polukr": "Польсько-український словник",
    "ukrpol": "Українсько-польський словник",
    "engukr": "Англо-український словник",
    "ukreng": "Українсько-англійський словник",
    "rusukr": "Російсько-український словник",
    "ukrrus": "Українсько-російський словник",
}

SLOVNYK_ME_DICT_ALIASES: dict[str, str] = {
    "antonenko": "davydov",
    "karavansky": "synonyms_karavansky",
    "ukrlit_ency": "literary_encyclopedia",
    "khreshchatyk_lessons": "khreshchatyk",
    "eng_ukr": "engukr",
    "ukr_eng": "ukreng",
    "rus_ukr": "rusukr",
    "ukr_rus": "ukrrus",
    "pol_ukr": "polukr",
    "ukr_pol": "ukrpol",
}

DEFAULT_SLOVNYK_ME_DICTS: tuple[str, ...] = (
    "newsum",
    "vts",
    "holoskevych",
    "obsolete_words",
    "bukovina",
    "franko",
    "slang_lviv",
)
HERITAGE_SLOVNYK_ME_DICTS: tuple[str, ...] = (
    "newsum",
    "holoskevych",
    "obsolete_words",
    "bukovina",
    "franko",
    "slang_lviv",
)
MODERN_DICTS: frozenset[str] = frozenset({"newsum", "vts"})
DIALECT_OR_HERITAGE_DICTS: frozenset[str] = frozenset(
    {"holoskevych", "obsolete_words", "bukovina", "franko", "slang_lviv", "slang", "slang_modern"}
)
RUSSIANISM_GUIDE_DICTS: frozenset[str] = frozenset({"davydov", "linguistic_norm", "voloschak"})
OVERLAP_BLOCKED_DICTS: dict[str, str] = {
    "sum": "search_definitions",
    "hrinchenko": "search_grinchenko_1907",
    "davydov": "search_style_guide",
    "phraseology": "search_idioms",
    "engukr": "translate_en_uk",
}
QUERY_ALIASES: dict[str, tuple[str, ...]] = {
    # User-facing spelling from #1715. slovnyk.me / СУМ-20 and regional
    # dictionaries index the Ukrainianized Polish loan as кобіта.
    "кобета": ("кобіта",),
}

SLOVNYK_ME_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS slovnyk_me_entries (
    id INTEGER PRIMARY KEY,
    query TEXT NOT NULL DEFAULT '',
    word TEXT NOT NULL,
    normalized_word TEXT NOT NULL DEFAULT '',
    dictionary_slug TEXT NOT NULL,
    dictionary_label TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT 'slovnyk_me',
    source_url TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    snippet TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    is_modern INTEGER NOT NULL DEFAULT 0,
    is_dialect INTEGER NOT NULL DEFAULT 0,
    is_russianism INTEGER NOT NULL DEFAULT 0,
    sovietization_risk INTEGER NOT NULL DEFAULT 0,
    sovietization_keywords TEXT NOT NULL DEFAULT '',
    fetched_at TEXT NOT NULL DEFAULT '',
    UNIQUE(normalized_word, dictionary_slug, source_url)
);
CREATE VIRTUAL TABLE IF NOT EXISTS slovnyk_me_entries_fts USING fts5(
    word,
    title,
    snippet,
    text,
    dictionary_label,
    content='slovnyk_me_entries',
    content_rowid='id',
    tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS slovnyk_me_entries_ai
AFTER INSERT ON slovnyk_me_entries BEGIN
    INSERT INTO slovnyk_me_entries_fts(rowid, word, title, snippet, text, dictionary_label)
    VALUES (new.id, new.word, new.title, new.snippet, new.text, new.dictionary_label);
END;
CREATE TRIGGER IF NOT EXISTS slovnyk_me_entries_ad
AFTER DELETE ON slovnyk_me_entries BEGIN
    INSERT INTO slovnyk_me_entries_fts(
        slovnyk_me_entries_fts, rowid, word, title, snippet, text, dictionary_label
    )
    VALUES ('delete', old.id, old.word, old.title, old.snippet, old.text, old.dictionary_label);
END;
CREATE TRIGGER IF NOT EXISTS slovnyk_me_entries_au
AFTER UPDATE ON slovnyk_me_entries BEGIN
    INSERT INTO slovnyk_me_entries_fts(
        slovnyk_me_entries_fts, rowid, word, title, snippet, text, dictionary_label
    )
    VALUES ('delete', old.id, old.word, old.title, old.snippet, old.text, old.dictionary_label);
    INSERT INTO slovnyk_me_entries_fts(rowid, word, title, snippet, text, dictionary_label)
    VALUES (new.id, new.word, new.title, new.snippet, new.text, new.dictionary_label);
END;
CREATE INDEX IF NOT EXISTS idx_slovnyk_me_word
    ON slovnyk_me_entries(normalized_word COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_slovnyk_me_dict
    ON slovnyk_me_entries(dictionary_slug);
CREATE INDEX IF NOT EXISTS idx_slovnyk_me_modern
    ON slovnyk_me_entries(is_modern) WHERE is_modern = 1;
CREATE INDEX IF NOT EXISTS idx_slovnyk_me_dialect
    ON slovnyk_me_entries(is_dialect) WHERE is_dialect = 1;
"""

_BLOCK_TAGS = {"p", "li", "br", "div", "h1", "h2", "h3", "small"}
_SPACE_RE = re.compile(r"\s+")
_ACUTE_RE = re.compile("[\u0301\u0300]")


class _SlovnykHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.section_parts: dict[str, list[str]] = {
            "dictionary-acticle": [],
            "dictionary-more": [],
        }
        self.h1_parts: list[str] = []
        self.meta_description = ""
        self.canonical_url = ""
        self._in_title = False
        self._in_h1 = False
        self._in_article = False
        self._active_section: str | None = None

    def _should_collect(self) -> bool:
        if self._active_section == "dictionary-acticle":
            return self._in_article
        return self._active_section in self.section_parts

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        if tag == "article" and self._active_section == "dictionary-acticle":
            self._in_article = True
        if tag == "h1" and self._active_section == "dictionary-acticle" and self._in_article:
            self._in_h1 = True
        if tag == "section" and attr.get("id") in self.section_parts:
            self._active_section = attr["id"]
        if tag in _BLOCK_TAGS and self._should_collect():
            self.section_parts[self._active_section].append("\n")
        if tag == "meta" and attr.get("name") == "description":
            self.meta_description = attr.get("content", "")
        if tag == "link" and attr.get("rel") == "canonical":
            self.canonical_url = attr.get("href", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag == "h1":
            self._in_h1 = False
        if tag == "article" and self._active_section == "dictionary-acticle":
            self._in_article = False
        if tag == "section" and self._active_section:
            self._active_section = None
        if tag in _BLOCK_TAGS and self._should_collect():
            self.section_parts[self._active_section].append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._should_collect():
            self.section_parts[self._active_section].append(data)
        if self._in_h1:
            self.h1_parts.append(data)


def ensure_slovnyk_me_schema(conn: sqlite3.Connection) -> None:
    """Create the curated slovnyk.me table and FTS index if missing."""
    conn.executescript(SLOVNYK_ME_SCHEMA_SQL)


def normalize_word(word: str) -> str:
    """Normalize a Ukrainian headword for lookup keys."""
    normalized = html.unescape(str(word or "")).strip().lower()
    normalized = _ACUTE_RE.sub("", normalized)
    normalized = normalized.replace("’", "'").replace("`", "'")
    return _SPACE_RE.sub(" ", normalized)


def resolve_dict_slug(slug: str) -> str:
    """Return the canonical slovnyk.me dictionary slug for a slug or alias."""
    cleaned = str(slug or "").strip()
    return SLOVNYK_ME_DICT_ALIASES.get(cleaned, cleaned)


def overlap_block_reason(slug: str) -> str | None:
    """Return the canonical local tool when a slovnyk.me dictionary overlaps."""
    return OVERLAP_BLOCKED_DICTS.get(resolve_dict_slug(slug))


def query_variants(query: str) -> list[str]:
    """Return direct-entry lookup variants without using /search."""
    normalized = normalize_word(query)
    variants = [normalized]
    for alias in QUERY_ALIASES.get(normalized, ()):
        normalized_alias = normalize_word(alias)
        if normalized_alias not in variants:
            variants.append(normalized_alias)
    return variants


def _clean_text(value: str) -> str:
    return _SPACE_RE.sub(" ", html.unescape(value)).strip()


def _truncate(value: str, max_chars: int) -> str:
    cleaned = _clean_text(value)
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip() + "…"


def _source_type(dict_slug: str, is_modern: bool, is_dialect: bool, is_russianism: bool) -> str:
    if is_russianism:
        return "usage_warning"
    if is_dialect:
        return "heritage_or_regional"
    if is_modern:
        return "modern_explanatory"
    return "dictionary"


def _classify_flags(dict_slug: str, text: str) -> tuple[bool, bool, bool, int, str]:
    lower = text.lower()
    is_modern = dict_slug in MODERN_DICTS
    is_dialect = dict_slug in DIALECT_OR_HERITAGE_DICTS or any(
        marker in lower
        for marker in (" діал.", " зах.", " заст.", " маловжив", "регіон", "говір", "жарґ", "львів")
    )
    is_russianism = dict_slug in RUSSIANISM_GUIDE_DICTS and any(
        marker in lower
        for marker in ("росіянізм", "російськ", "кальк", "неправильно", "не слід", "краще")
    )
    risk, keywords = classify_entry("", text)
    return is_modern, is_dialect, is_russianism, risk, ",".join(keywords)


def parse_entry_html(
    page_html: str,
    *,
    query: str,
    word: str,
    dict_slug: str,
    url: str,
    max_text_chars: int = 500,
) -> dict[str, Any] | None:
    """Parse one direct slovnyk.me dictionary page into a bounded row."""
    parser = _SlovnykHTMLParser()
    parser.feed(page_html)

    section_text = _clean_text(" ".join(parser.section_parts["dictionary-acticle"]))
    if not section_text:
        return None

    headword = _clean_text(" ".join(parser.h1_parts)) or normalize_word(word)
    title = _clean_text(" ".join(parser.title_parts)) or headword
    canonical_url = parser.canonical_url or url
    text = _truncate(section_text, max_text_chars)
    snippet = _truncate(parser.meta_description or section_text, min(max_text_chars, 500))
    is_modern, is_dialect, is_russianism, risk, keywords = _classify_flags(dict_slug, text)

    return {
        "query": query,
        "word": headword,
        "normalized_word": normalize_word(headword),
        "dictionary_slug": dict_slug,
        "dictionary_label": SLOVNYK_ME_DICTS.get(dict_slug, dict_slug),
        "source_type": _source_type(dict_slug, is_modern, is_dialect, is_russianism),
        "source_url": canonical_url,
        "title": title,
        "snippet": snippet,
        "text": text,
        "is_modern": is_modern,
        "is_dialect": is_dialect,
        "is_russianism": is_russianism,
        "sovietization_risk": risk,
        "sovietization_keywords": keywords,
        "fetched_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
    }


def fetch_entry(
    word: str,
    dict_slug: str,
    *,
    query: str | None = None,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout: int = 20,
    max_text_chars: int = 500,
) -> dict[str, Any] | None:
    """Fetch one direct slovnyk.me dictionary entry.

    This intentionally uses /dict/{slug}/{word}, not /search, because /search
    is disallowed in robots.txt.
    """
    canonical_slug = resolve_dict_slug(dict_slug)
    if canonical_slug not in SLOVNYK_ME_DICTS:
        return None
    if canonical_slug in OVERLAP_BLOCKED_DICTS:
        return None
    url = f"{SLOVNYK_ME_BASE}/dict/{canonical_slug}/{quote(word)}"
    response = requests.get(url, timeout=timeout, headers={"User-Agent": user_agent})
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return parse_entry_html(
        response.text,
        query=query or word,
        word=word,
        dict_slug=canonical_slug,
        url=url,
        max_text_chars=max_text_chars,
    )


def fetch_entries(
    query: str,
    *,
    dictionaries: list[str] | tuple[str, ...] | None = None,
    limit: int = 10,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout: int = 20,
    max_text_chars: int = 500,
) -> list[dict[str, Any]]:
    """Fetch bounded direct-entry rows for a query across selected dictionaries."""
    dicts = dictionaries or DEFAULT_SLOVNYK_ME_DICTS
    variants = query_variants(query)
    results: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for slug in dicts:
        canonical_slug = resolve_dict_slug(slug)
        if canonical_slug not in SLOVNYK_ME_DICTS:
            continue
        if canonical_slug in OVERLAP_BLOCKED_DICTS:
            continue
        for variant in variants:
            try:
                row = fetch_entry(
                    variant,
                    canonical_slug,
                    query=query,
                    user_agent=user_agent,
                    timeout=timeout,
                    max_text_chars=max_text_chars,
                )
            except requests.RequestException:
                row = None
            if not row:
                continue
            key = (row["dictionary_slug"], row["source_url"])
            if key in seen:
                continue
            seen.add(key)
            results.append(row)
            break
        if len(results) >= limit:
            break

    results.sort(key=lambda row: score_slovnyk_row(row, query), reverse=True)
    return results[:limit]


def score_slovnyk_row(row: dict[str, Any], query: str) -> float:
    """Rank slovnyk.me rows for direct verification."""
    normalized_query = normalize_word(query)
    normalized_word = normalize_word(str(row.get("normalized_word") or row.get("word") or ""))
    score = 40.0
    if normalized_word == normalized_query or normalized_word in query_variants(normalized_query):
        score += 35.0
    elif normalized_word.startswith(normalized_query):
        score += 20.0
    if bool(row.get("is_modern")):
        score += 15.0
    if bool(row.get("is_dialect")):
        score += 18.0
    if bool(row.get("is_russianism")):
        score -= 45.0
    score -= 5.0 * int(row.get("sovietization_risk") or 0)
    return score


def db_row_values(row: dict[str, Any]) -> tuple[Any, ...]:
    """Return insert values for slovnyk_me_entries."""
    return (
        row.get("query", ""),
        row.get("word", ""),
        row.get("normalized_word") or normalize_word(str(row.get("word", ""))),
        row.get("dictionary_slug", ""),
        row.get("dictionary_label", ""),
        row.get("source_type", "slovnyk_me"),
        row.get("source_url", ""),
        row.get("title", ""),
        row.get("snippet", ""),
        row.get("text", ""),
        int(bool(row.get("is_modern"))),
        int(bool(row.get("is_dialect"))),
        int(bool(row.get("is_russianism"))),
        int(row.get("sovietization_risk") or 0),
        row.get("sovietization_keywords", ""),
        row.get("fetched_at", ""),
    )
