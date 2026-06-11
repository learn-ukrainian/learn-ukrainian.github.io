#!/usr/bin/env python3
"""Ingest bounded uk.wiktionary etymology snapshots for Word Atlas lemmas."""

from __future__ import annotations

import argparse
import bz2
import datetime as dt
import hashlib
import html
import json
import re
import sqlite3
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO / "data" / "sources.db"
DEFAULT_MANIFEST = REPO / "starlight" / "src" / "data" / "lexicon-manifest.json"

WIKTIONARY_DUMP_DATE = "20260601"
WIKTIONARY_DUMP_FILENAME = f"ukwiktionary-{WIKTIONARY_DUMP_DATE}-pages-articles.xml.bz2"
WIKTIONARY_DUMP_URL = (
    f"https://dumps.wikimedia.org/ukwiktionary/{WIKTIONARY_DUMP_DATE}/{WIKTIONARY_DUMP_FILENAME}"
)
WIKTIONARY_DUMP_SHA256 = "a3544dc777eb152d0bdb57c394c0cf7074f0f0a3e70b0ec953449055dea5d604"
DEFAULT_DUMP = REPO / "tmp" / "wiktionary" / WIKTIONARY_DUMP_FILENAME
DEFAULT_USER_AGENT = (
    "learn-ukrainian-wiktionary-etymology/1.0 "
    "(noncommercial educational lookup; issue 2882)"
)

WIKTIONARY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS wiktionary_etymology (
    requested_lemma TEXT PRIMARY KEY,
    headword TEXT NOT NULL DEFAULT '',
    lang TEXT NOT NULL DEFAULT 'uk',
    etymology_text TEXT NOT NULL DEFAULT '',
    section_raw TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL DEFAULT '',
    dump_date TEXT NOT NULL DEFAULT '',
    retrieved_at TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_wiktionary_etymology_exact_lemma
    ON wiktionary_etymology(requested_lemma);
CREATE INDEX IF NOT EXISTS idx_wiktionary_etymology_headword
    ON wiktionary_etymology(headword);
"""

UPSERT_SQL = """
INSERT INTO wiktionary_etymology (
    requested_lemma,
    headword,
    lang,
    etymology_text,
    section_raw,
    source_url,
    dump_date,
    retrieved_at,
    content_hash
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(requested_lemma) DO UPDATE SET
    headword = excluded.headword,
    lang = excluded.lang,
    etymology_text = excluded.etymology_text,
    section_raw = excluded.section_raw,
    source_url = excluded.source_url,
    dump_date = excluded.dump_date,
    retrieved_at = excluded.retrieved_at,
    content_hash = excluded.content_hash
"""

_SPACE_RE = re.compile(r"\s+")
_STRESS_MARK_RE = re.compile("[\u0300\u0301]")
_APOSTROPHES = ("'", "’", "ʼ")
_LANG_TEMPLATE_RE = re.compile(r"(?m)^\s*\{\{\s*=([a-z-]+)=\s*\}\}\s*$")
_LEVEL_2_UK_RE = re.compile(r"(?m)^\s*==\s*Українська\s*==\s*$")
_LEVEL_2_HEADING_RE = re.compile(r"(?m)^\s*==\s*[^=\n].*?==\s*$")
_HEADING_RE = re.compile(r"(?m)^\s*(?P<level>={2,6})\s*(?P<title>[^=\n]+?)\s*(?P=level)\s*$")
_INNER_TEMPLATE_RE = re.compile(r"\{\{([^{}]+)\}\}")
_REDIRECT_RE = re.compile(r"(?is)^\s*#(?:ПЕРЕНАПРАВЛЕННЯ|REDIRECT)\s*\[\[([^|\]#]+)")
_WIKI_LINK_RE = re.compile(r"\[\[([^|\]#]+)(?:#[^|\]]*)?(?:\|([^\]]+))?\]\]")
_EXTERNAL_LINK_RE = re.compile(r"\[(?:https?|ftp)://[^\s\]]+\s+([^\]]+)\]")
_TAG_RE = re.compile(r"</?[^>]+>")
_CYRILLIC_OR_LATIN_RE = re.compile(r"[A-Za-zА-Яа-яЄєІіЇїҐґ]")
_QUALITY_TOKEN_RE = re.compile(r"[*]?[0-9A-Za-zА-Яа-яЄєІіЇїҐґ'’ʼ-]+")
_CYRILLIC_WORD_RE = re.compile(r"[А-Яа-яЄєІіЇїҐґ][А-Яа-яЄєІіЇїҐґ'’ʼ-]*")
_CATEGORY_LINK_RE = re.compile(r"\[\[\s*(?:Категорія|Category)\s*:[^\]]+\]\]", re.IGNORECASE)
_MARKUP_RESIDUE_RE = re.compile(
    r"\{\{|\}\}|\[\[\s*Категорія|Категорія\s*:|довжина слова|Предметні слова|мова\s*=",
    re.IGNORECASE,
)
_EMPTY_TEMPLATE_RE = re.compile(r"\bВід\s+\?", re.IGNORECASE)
_LANG_CODE_AFTER_FROM_RE = re.compile(r"\bВід\s+(?:uk|be|ru|pl|cs|sh|bg|chu)\b", re.IGNORECASE)
_DUPLICATED_FROM_FRAGMENT_RE = re.compile(r"\bвід\s+від\b", re.IGNORECASE)
_FOREIGN_SOURCE_MARKER_RE = re.compile(
    r"\b(?:англ|араб|гр|дав.-гр|лат|нім|п|р|тур|фр)\.\s+\*?[A-Za-z][A-Za-z'’ʼ-]{2,}",
    re.IGNORECASE,
)

_LANG_CODE_TOKENS = {"uk", "be", "ru", "pl", "cs", "sh", "bg", "chu"}
_NON_LEXICAL_CYRILLIC_TOKENS = {"від"}

# This Wiktionary page currently expands to an informal circular editor note
# rather than curriculum-grade etymology prose.
_LOW_QUALITY_SKIP = {"робота"}

_LANG_LABELS = {
    "ar": "араб.",
    "de": "нім.",
    "el": "гр.",
    "en": "англ.",
    "fr": "фр.",
    "grc": "дав.-гр.",
    "la": "лат.",
    "pl": "п.",
    "ru": "р.",
    "uk": "укр.",
}


@dataclass(frozen=True)
class WiktionaryPage:
    title: str
    text: str


def ensure_wiktionary_etymology_schema(conn: sqlite3.Connection) -> None:
    """Create the bounded Wiktionary etymology cache table if missing."""
    conn.executescript(WIKTIONARY_SCHEMA_SQL)


def clean_text(value: str) -> str:
    """Collapse dump text to plain single-spaced text."""
    cleaned = html.unescape(str(value or "")).replace("\xa0", " ")
    cleaned = _SPACE_RE.sub(" ", cleaned).strip()
    return cleaned


def has_whitespace(value: str) -> bool:
    """Return whether a lemma is a multi-token phrase for etymology purposes."""
    return bool(re.search(r"\s", str(value or "").strip()))


def lookup_key(value: str) -> str:
    """Return a lookup key without stress marks or apostrophe variants."""
    normalized = unicodedata.normalize("NFKD", clean_text(value))
    normalized = _STRESS_MARK_RE.sub("", normalized)
    normalized = unicodedata.normalize("NFC", normalized)
    normalized = normalized.replace("`", "'").replace("’", "'").replace("ʼ", "'")
    return normalized.casefold()


def content_hash(text: str) -> str:
    """Return a stable content hash for one cached prose extract."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dump_sha256(path: Path) -> str:
    """Hash a local dump file using sha256."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_dump_checksum(path: Path, expected_sha256: str = WIKTIONARY_DUMP_SHA256) -> str:
    """Verify that the downloaded dump matches the pinned checksum."""
    actual = dump_sha256(path)
    if actual != expected_sha256:
        raise ValueError(
            f"{path} sha256 mismatch: expected {expected_sha256}, got {actual}"
        )
    return actual


def download_dump(path: Path, *, user_agent: str = DEFAULT_USER_AGENT) -> None:
    """Download the pinned uk.wiktionary dump to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(WIKTIONARY_DUMP_URL, headers={"User-Agent": user_agent})
    with urlopen(request, timeout=120) as response, path.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)


def load_atlas_lemmas(manifest_path: Path = DEFAULT_MANIFEST) -> list[str]:
    """Read Word Atlas lemmas from the generated manifest."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lemmas: list[str] = []
    seen: set[str] = set()
    for entry in manifest.get("entries", []):
        lemma = clean_text(str(entry.get("lemma", "")))
        if not lemma or lemma in seen:
            continue
        seen.add(lemma)
        lemmas.append(lemma)
    return lemmas


def lookup_candidates(lemma: str) -> list[str]:
    """Return bounded uk.wiktionary lookup candidates for one Atlas lemma string."""
    candidates: list[str] = [clean_text(lemma)]
    for part in re.split(r"[/,]", lemma):
        part = clean_text(part)
        if part:
            candidates.append(part)
    for candidate in list(candidates):
        if any(mark in candidate for mark in _APOSTROPHES):
            for apostrophe in _APOSTROPHES:
                candidates.append(
                    candidate.replace("'", apostrophe).replace("’", apostrophe).replace("ʼ", apostrophe)
                )
    seen: set[str] = set()
    return [item for item in candidates if item and not (lookup_key(item) in seen or seen.add(lookup_key(item)))]


def wiktionary_url(title: str) -> str:
    """Build a canonical uk.wiktionary page URL."""
    return f"https://uk.wiktionary.org/wiki/{quote(title.replace(' ', '_'), safe='')}"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(elem: ET.Element, name: str) -> str:
    for child in elem.iter():
        if _local_name(child.tag) == name:
            return child.text or ""
    return ""


def _revision_text(page: ET.Element) -> str:
    for child in page:
        if _local_name(child.tag) != "revision":
            continue
        for revision_child in child:
            if _local_name(revision_child.tag) == "text":
                return revision_child.text or ""
    return ""


def iter_dump_pages(dump_path: Path) -> list[WiktionaryPage]:
    """Read all dump pages into small page records.

    The pinned uk.wiktionary dump is roughly 16 MB compressed, so this bounded
    ingest keeps the XML traversal straightforward and deterministic.
    """
    pages: list[WiktionaryPage] = []
    with bz2.open(dump_path, "rb") as fh:
        for _, elem in ET.iterparse(fh, events=("end",)):
            if _local_name(elem.tag) != "page":
                continue
            title = _child_text(elem, "title")
            text = _revision_text(elem)
            ns = _child_text(elem, "ns")
            if title and text and ns in {"0", "10"}:
                pages.append(WiktionaryPage(title=title, text=text))
            elem.clear()
    return pages


def _find_uk_template_section(wikitext: str) -> str | None:
    matches = list(_LANG_TEMPLATE_RE.finditer(wikitext))
    for index, match in enumerate(matches):
        if match.group(1) != "uk":
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(wikitext)
        return wikitext[start:end].strip()
    return None


def _find_uk_heading_section(wikitext: str) -> str | None:
    match = _LEVEL_2_UK_RE.search(wikitext)
    if not match:
        return None
    next_match = _LEVEL_2_HEADING_RE.search(wikitext, match.end())
    end = next_match.start() if next_match else len(wikitext)
    return wikitext[match.end():end].strip()


def extract_ukrainian_section(wikitext: str) -> str | None:
    """Keep only the Ukrainian language section from a uk.wiktionary page."""
    return _find_uk_template_section(wikitext) or _find_uk_heading_section(wikitext)


def _section_end(headings: list[re.Match[str]], index: int, section_end: int) -> int:
    level = len(headings[index].group("level"))
    for next_heading in headings[index + 1 :]:
        if len(next_heading.group("level")) <= level:
            return next_heading.start()
    return section_end


def extract_etymology_section_raw(wikitext: str) -> str | None:
    """Extract one or more Ukrainian ``Етимологія`` sections as raw wikitext."""
    ukrainian = extract_ukrainian_section(wikitext)
    if not ukrainian:
        return None
    headings = list(_HEADING_RE.finditer(ukrainian))
    sections: list[str] = []
    for index, heading in enumerate(headings):
        title = clean_text(heading.group("title"))
        if not title.casefold().startswith("етимологія"):
            continue
        body_start = heading.end()
        body_end = _section_end(headings, index, len(ukrainian))
        body = ukrainian[body_start:body_end].strip()
        if body:
            sections.append(f"{title}\n{body}" if title.casefold() != "етимологія" else body)
    if not sections:
        return None
    return "\n\n".join(sections).strip()


def _split_template_parts(raw: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    link_depth = 0
    index = 0
    while index < len(raw):
        pair = raw[index : index + 2]
        if pair == "[[":
            link_depth += 1
            current.append(pair)
            index += 2
            continue
        if pair == "]]" and link_depth:
            link_depth -= 1
            current.append(pair)
            index += 2
            continue
        char = raw[index]
        if char == "|" and not link_depth:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1
    parts.append("".join(current).strip())
    return parts


def _template_key(name: str) -> str:
    name = clean_text(name)
    if name.startswith("Шаблон:"):
        name = name.removeprefix("Шаблон:")
    return lookup_key(name)


def _render_template(raw: str, template_map: dict[str, str]) -> str:
    parts = _split_template_parts(raw)
    if not parts:
        return ""
    name = clean_text(parts[0])
    name_key = _template_key(name)
    if name_key.startswith("етимологія:"):
        return template_map.get(name_key, "")
    if name_key == "етимологія":
        args = [part for part in parts[1:] if part and "=" not in part]
        if args and args[0].casefold() in _LANG_CODE_TOKENS:
            args = args[1:]
        return " ".join(part for part in args if part != "?")
    if name_key.startswith("lang-"):
        lang = name_key.removeprefix("lang-")
        label = _LANG_LABELS.get(lang, lang)
        rendered_args = " ".join(part for part in parts[1:] if part and "=" not in part)
        return f"{label} {rendered_args}".strip()
    if name_key in {"ety", "etyl", "похідне"}:
        return " ".join(part for part in parts[1:] if part and "=" not in part)
    return " ".join(part for part in parts[1:] if part and "=" not in part)


def expand_templates(raw: str, template_map: dict[str, str]) -> str:
    """Expand local etymology templates and simplify safe inline templates."""
    text = html.unescape(raw)
    text = re.sub(r"(?is)<noinclude>.*?</noinclude>", "", text)
    text = re.sub(r"(?is)<!--.*?-->", "", text)
    for _ in range(12):
        updated = _INNER_TEMPLATE_RE.sub(lambda match: _render_template(match.group(1), template_map), text)
        if updated == text:
            break
        text = updated
    text = re.sub(r"(?is)<noinclude>.*?</noinclude>", "", text)
    text = re.sub(r"(?is)<!--.*?-->", "", text)
    return text


def clean_wikitext(raw: str, template_map: dict[str, str]) -> str:
    """Render a conservative display string from raw Wiktionary etymology wikitext."""
    text = expand_templates(raw, template_map)
    text = re.sub(r"(?is)<ref\b.*?</ref>", " ", text)
    text = _TAG_RE.sub(" ", text)
    text = _CATEGORY_LINK_RE.sub(" ", text)
    text = _EXTERNAL_LINK_RE.sub(r"\1", text)
    text = _WIKI_LINK_RE.sub(lambda match: match.group(2) or match.group(1), text)
    text = text.replace("'''", "").replace("''", "")
    text = text.replace("–", "—")
    text = re.sub(r"^[*:;#]+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[\[[^\]]+\]\]", " ", text)
    text = re.sub(r"\[|\]|\{|\}", " ", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = _SPACE_RE.sub(" ", text).strip(" \t\r\n.,;:—-")
    text = re.sub(r"(?i)(?:,\s*)?\bВід\s*$", "", text)
    return text.strip(" \t\r\n.,;:—-")


def _quality_tokens(text: str) -> list[str]:
    return [token.casefold().strip("'’ʼ-") for token in _QUALITY_TOKEN_RE.findall(text) if token.strip("'’ʼ-")]


def _has_high_token_repetition(tokens: list[str]) -> bool:
    if len(tokens) <= 3:
        return False
    return len(set(tokens)) / len(tokens) <= 0.5


def _has_etymon_marker(text: str) -> bool:
    folded = text.casefold()
    if "*" in text or "псл" in folded or "psl" in folded or "запозич" in folded:
        return True
    return "прасл" in folded or bool(_FOREIGN_SOURCE_MARKER_RE.search(text))


def _has_real_lexical_content(text: str) -> bool:
    if _has_etymon_marker(text):
        return True
    for word in _CYRILLIC_WORD_RE.findall(text):
        token = word.casefold().strip("'’ʼ-")
        if len(token) >= 3 and token not in _NON_LEXICAL_CYRILLIC_TOKENS and token not in _LANG_CODE_TOKENS:
            return True
    return False


def etymology_rejection_reason(text: str, lemma: str | None = None) -> str | None:
    """Return why a Wiktionary etymology extract is not safe to cache."""
    if lemma and lookup_key(lemma) in _LOW_QUALITY_SKIP:
        return "known low-quality Wiktionary etymology"

    cleaned = clean_text(text).strip(" .,:;—-")
    if _MARKUP_RESIDUE_RE.search(cleaned):
        return "markup/template/category residue"
    if _EMPTY_TEMPLATE_RE.search(cleaned):
        return "empty etymology template residue"
    if _LANG_CODE_AFTER_FROM_RE.search(cleaned):
        return "language-code residue after Від"

    real_chars = re.sub(r"[^0-9A-Za-zА-Яа-яЄєІіЇїҐґ*]", "", cleaned)
    if len(real_chars) < 15 and not _has_etymon_marker(cleaned):
        return "too short"

    tokens = _quality_tokens(cleaned)
    if _has_high_token_repetition(tokens):
        return "high token repetition"
    if _DUPLICATED_FROM_FRAGMENT_RE.search(cleaned):
        return "duplicated or truncated Від fragment"
    if cleaned.casefold() in {"від", "від слова", "походить від"}:
        return "uninformative etymology fragment"
    if not _has_real_lexical_content(cleaned):
        return "no lexical Ukrainian or etymon content"
    if not _CYRILLIC_OR_LATIN_RE.search(cleaned):
        return "no lexical text"
    return None


def is_clean_etymology(text: str, lemma: str | None = None) -> bool:
    """Return whether a cleaned Wiktionary etymology extract is safe to cache."""
    return etymology_rejection_reason(text, lemma=lemma) is None


def parse_wiktionary_page(
    page: WiktionaryPage,
    *,
    requested_lemma: str,
    template_map: dict[str, str],
    max_text_chars: int = 1200,
) -> dict[str, str] | None:
    """Parse one uk.wiktionary page into a bounded cache row."""
    raw = extract_etymology_section_raw(page.text)
    if not raw:
        return None
    text = clean_wikitext(raw, template_map)
    rejection_reason = etymology_rejection_reason(text, lemma=requested_lemma)
    if rejection_reason:
        print(f"{requested_lemma}: rejected Wiktionary etymology ({rejection_reason})")
        return None
    if len(text) > max_text_chars:
        text = text[: max_text_chars - 1].rstrip(" ,.;:") + "…"
    return {
        "requested_lemma": clean_text(requested_lemma),
        "headword": clean_text(page.title),
        "lang": "uk",
        "etymology_text": text,
        "section_raw": raw,
        "source_url": wiktionary_url(page.title),
        "dump_date": WIKTIONARY_DUMP_DATE,
        "retrieved_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "content_hash": content_hash(text),
    }


def _redirect_target(page: WiktionaryPage) -> str | None:
    match = _REDIRECT_RE.match(page.text)
    return clean_text(match.group(1)) if match else None


def _template_map_from_pages(pages: list[WiktionaryPage]) -> dict[str, str]:
    templates: dict[str, str] = {}
    for page in pages:
        if page.title.startswith("Шаблон:етимологія:"):
            templates[_template_key(page.title)] = page.text
    return templates


def _pages_by_lookup_key(pages: list[WiktionaryPage], wanted_keys: set[str]) -> dict[str, list[WiktionaryPage]]:
    grouped: dict[str, list[WiktionaryPage]] = defaultdict(list)
    for page in pages:
        key = lookup_key(page.title)
        if key in wanted_keys:
            grouped[key].append(page)
    return grouped


def _candidate_pages(
    pages_by_key: dict[str, list[WiktionaryPage]],
    candidate: str,
) -> list[WiktionaryPage]:
    pages = pages_by_key.get(lookup_key(candidate), [])
    return sorted(
        pages,
        key=lambda page: (
            page.title != candidate,
            page.title.casefold() != candidate.casefold(),
            page.title,
        ),
    )


def _resolve_pages(
    pages_by_key: dict[str, list[WiktionaryPage]],
    page: WiktionaryPage,
    *,
    seen: set[str] | None = None,
) -> list[WiktionaryPage]:
    seen = seen or set()
    if page.title in seen:
        return []
    seen.add(page.title)
    target = _redirect_target(page)
    if not target:
        return [page]
    resolved: list[WiktionaryPage] = []
    for target_page in pages_by_key.get(lookup_key(target), []):
        resolved.extend(_resolve_pages(pages_by_key, target_page, seen=seen))
    return resolved


def _row_for_lemma(
    lemma: str,
    *,
    pages_by_key: dict[str, list[WiktionaryPage]],
    template_map: dict[str, str],
    max_text_chars: int,
) -> dict[str, str] | None:
    for candidate in lookup_candidates(lemma):
        for page in _candidate_pages(pages_by_key, candidate):
            for resolved_page in _resolve_pages(pages_by_key, page):
                row = parse_wiktionary_page(
                    resolved_page,
                    requested_lemma=lemma,
                    template_map=template_map,
                    max_text_chars=max_text_chars,
                )
                if row:
                    return row
    return None


def extract_wiktionary_etymology_rows(
    dump_path: Path,
    lemmas: list[str],
    *,
    max_text_chars: int = 1200,
) -> dict[str, dict[str, str]]:
    """Extract requested single-word lemma rows from the pinned dump."""
    single_word_lemmas = [clean_text(lemma) for lemma in lemmas if not has_whitespace(lemma)]
    wanted_keys = {
        lookup_key(candidate)
        for lemma in single_word_lemmas
        for candidate in lookup_candidates(lemma)
    }
    pages = iter_dump_pages(dump_path)
    template_map = _template_map_from_pages(pages)
    pages_by_key = _pages_by_lookup_key(pages, wanted_keys)

    rows: dict[str, dict[str, str]] = {}
    for lemma in single_word_lemmas:
        row = _row_for_lemma(
            lemma,
            pages_by_key=pages_by_key,
            template_map=template_map,
            max_text_chars=max_text_chars,
        )
        if row:
            rows[lemma] = row
    return rows


def upsert_wiktionary_row(conn: sqlite3.Connection, row: dict[str, str]) -> None:
    """Upsert one parsed Wiktionary etymology row."""
    conn.execute(
        UPSERT_SQL,
        (
            row["requested_lemma"],
            row["headword"],
            row["lang"],
            row["etymology_text"],
            row["section_raw"],
            row["source_url"],
            row["dump_date"],
            row["retrieved_at"],
            row["content_hash"],
        ),
    )


def _is_cached(conn: sqlite3.Connection, lemma: str) -> bool:
    row = conn.execute(
        "SELECT etymology_text FROM wiktionary_etymology WHERE requested_lemma = ? LIMIT 1",
        (clean_text(lemma),),
    ).fetchone()
    if row is None:
        return False
    rejection_reason = etymology_rejection_reason(row[0], lemma=lemma)
    if rejection_reason:
        print(f"{lemma}: removed cached Wiktionary etymology ({rejection_reason})")
        with conn:
            conn.execute(
                "DELETE FROM wiktionary_etymology WHERE requested_lemma = ?",
                (clean_text(lemma),),
            )
        return False
    return True


def ingest_wiktionary_etymology(
    db_path: Path,
    dump_path: Path,
    lemmas: list[str],
    *,
    refresh: bool,
    dry_run: bool,
    max_text_chars: int,
) -> tuple[int, int, int]:
    """Load Atlas-bounded uk.wiktionary etymology rows into sources.db."""
    conn = None if dry_run else sqlite3.connect(str(db_path))
    skipped_phrases = 0
    loaded = 0
    pending: list[str] = []
    try:
        if conn is not None:
            ensure_wiktionary_etymology_schema(conn)
        for lemma in lemmas:
            if has_whitespace(lemma):
                print(f"{lemma}: skipped phrase")
                skipped_phrases += 1
                continue
            if conn is not None and not refresh and _is_cached(conn, lemma):
                print(f"{lemma}: cached")
                continue
            pending.append(clean_text(lemma))

        rows = extract_wiktionary_etymology_rows(
            dump_path,
            pending,
            max_text_chars=max_text_chars,
        ) if pending else {}
        for lemma in pending:
            row = rows.get(lemma)
            if not row:
                print(f"{lemma}: no uk.wiktionary etymology")
                if conn is not None and refresh:
                    with conn:
                        conn.execute(
                            "DELETE FROM wiktionary_etymology WHERE requested_lemma = ?",
                            (clean_text(lemma),),
                        )
                continue
            if row["headword"] != lemma:
                print(f"{lemma}: {row['headword']}")
            else:
                print(f"{lemma}: loaded")
            if dry_run:
                loaded += 1
                continue
            assert conn is not None
            with conn:
                upsert_wiktionary_row(conn, row)
            loaded += 1
        return len(pending), loaded, skipped_phrases
    finally:
        if conn is not None:
            conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract uk.wiktionary etymology sections from the pinned XML dump and cache bounded prose.\n"
            "Build/enrich code must read sources.db only; this ingest is the offline dump step."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""Pinned dump:
  {WIKTIONARY_DUMP_URL}
  sha256 {WIKTIONARY_DUMP_SHA256}

Examples:
  .venv/bin/python scripts/ingest/wiktionary_etymology_ingest.py --download
  .venv/bin/python scripts/ingest/wiktionary_etymology_ingest.py --refresh

Outputs:
  Creates/updates the wiktionary_etymology table in data/sources.db for Atlas lemmas only.
  Stores a conservative plain-text extract, raw etymology section, source URL, dump date, and hash.
""",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f"Lexicon manifest to read. Default: {DEFAULT_MANIFEST}",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"SQLite sources.db path to update. Default: {DEFAULT_DB}",
    )
    parser.add_argument(
        "--dump",
        type=Path,
        default=DEFAULT_DUMP,
        help=f"Pinned uk.wiktionary XML bz2 dump. Default: {DEFAULT_DUMP}",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the pinned dump before ingest if it is missing.",
    )
    parser.add_argument(
        "--lemma",
        action="append",
        default=[],
        help="Specific lemma to ingest. Repeatable. Defaults to all manifest lemmas.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-extract lemmas even when a cached Wiktionary row already exists.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract and report rows but do not create or update the SQLite database.",
    )
    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=1200,
        help="Maximum etymology prose characters stored per row. Default: 1200.",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help=f"HTTP User-Agent for dump download. Default: {DEFAULT_USER_AGENT}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.download and not args.dump.exists():
        download_dump(args.dump, user_agent=args.user_agent)
    if not args.dump.exists():
        print(f"Dump not found: {args.dump}")
        print(f"Download with: .venv/bin/python {Path(__file__)} --download")
        return 2
    actual_sha256 = verify_dump_checksum(args.dump)
    print(f"dump {WIKTIONARY_DUMP_DATE} sha256 {actual_sha256}")

    lemmas = [clean_text(lemma) for lemma in args.lemma] if args.lemma else load_atlas_lemmas(args.manifest)
    if not lemmas:
        print(f"No Atlas lemmas found in {args.manifest}")
        return 2
    scanned, loaded, skipped_phrases = ingest_wiktionary_etymology(
        args.db,
        args.dump,
        lemmas,
        refresh=args.refresh,
        dry_run=args.dry_run,
        max_text_chars=max(1, args.max_text_chars),
    )
    print(
        f"Scanned {scanned} single-word lemma(s); loaded {loaded} row(s); "
        f"skipped {skipped_phrases} phrase(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
