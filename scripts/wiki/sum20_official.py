"""Official СУМ-20 parsing, storage, and polite per-wordid fetching.

The public СУМ-20 interface exposes article pages at sequential ``wordid``
values.  This module deliberately keeps collection access offline after an
explicit ingest run: callers query ``sum20_articles`` rather than the web.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path

import requests

try:
    from scripts.lib.readonly_sqlite import SQLiteConnection
except ModuleNotFoundError as exc:
    # Script execution puts the script directory on sys.path, so the
    # top-level package is absent (exc.name == "scripts"). Any other
    # import failure must propagate.
    if exc.name != "scripts":
        raise
    # lib.readonly_sqlite lives in scripts/, which file execution does not put on sys.path.
    _scripts_dir = next(parent for parent in Path(__file__).resolve().parents if parent.name == "scripts")
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
    from lib.readonly_sqlite import SQLiteConnection  # type: ignore[no-redef]

SUM20_SOURCE_ID = "sum20_official"
SUM20_OFFICIAL_BASE_URL = "https://sum20ua.com"
SUM20_ATTRIBUTION_LABEL = (
    "Словник української мови у 20 томах (УМІФ НАН України; Інститут мовознавства ім. О. О. Потебні НАН України)"
)
PARSER_VERSION = "sum20_official_v3"
QUARANTINE_COLUMN = "quarantine_reason"
DEFAULT_USER_AGENT = "learn-ukrainian-sum20-ingest/1.0 (noncommercial educational corpus; issue 5228)"

_ARTICLE_RE = re.compile(r"<article\b[^>]*>.*?</article\s*>", re.IGNORECASE | re.DOTALL)
_ACUTE_RE = re.compile("[\u0300\u0301]")
_SPACE_RE = re.compile(r"\s+")
_POS_RE = re.compile(
    r"\b(ч\.|ж\.|с\.|мн\.|прикм\.|присл\.|дієсл\.|займ\.|виг\.|спол\.|част\.)",
    re.IGNORECASE,
)
_ADJECTIVE_ENDINGS_RE = re.compile(r",\s*[а-яіїєґ]\s*,\s*[а-яіїєґ]\.$", re.IGNORECASE)
_BLOCK_TAGS = frozenset({"article", "div", "p", "li", "br", "h1", "h2", "h3", "tr", "td"})
_ENTRY_BOUNDARIES = frozenset({"ENTRY", "LINKENTRY"})


class Sum20ParseError(ValueError):
    """Raised when an official response does not contain a usable article."""


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    children: list[_Node | str]


class _ArticleTreeParser(HTMLParser):
    """Tiny HTML tree builder sufficient for the stable article markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("root", {}, [])
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag.lower(), {key: value or "" for key, value in attrs}, [])
        self._stack[-1].children.append(node)
        if tag.lower() not in {"br", "img", "meta", "link", "input", "hr"}:
            self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in {"br", "img", "meta", "link", "input", "hr"}:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == lowered:
                del self._stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if data:
            self._stack[-1].children.append(data)


def _classes(node: _Node) -> set[str]:
    return set(node.attrs.get("class", "").split())


def _walk(node: _Node, *, stop_classes: frozenset[str] = _ENTRY_BOUNDARIES) -> Iterable[_Node]:
    """Walk owned fields, pruning nested articles unless explicitly requested."""
    yield node
    for child in node.children:
        if isinstance(child, _Node) and not (_classes(child) & stop_classes):
            yield from _walk(child, stop_classes=stop_classes)


def _first_with_class(
    node: _Node, class_name: str, *, stop_classes: frozenset[str] = _ENTRY_BOUNDARIES
) -> _Node | None:
    return next(
        (candidate for candidate in _walk(node, stop_classes=stop_classes) if class_name in _classes(candidate)),
        None,
    )


def _all_with_class(node: _Node, class_name: str) -> list[_Node]:
    return [candidate for candidate in _walk(node) if class_name in _classes(candidate)]


def _clean_text(value: str) -> str:
    return _SPACE_RE.sub(" ", html.unescape(value)).strip()


def _node_text(node: _Node, *, include_entries: bool = False) -> str:
    parts: list[str] = []

    def collect(candidate: _Node | str) -> None:
        if isinstance(candidate, str):
            parts.append(candidate)
            return
        if candidate is not node and not include_entries and _classes(candidate) & _ENTRY_BOUNDARIES:
            return
        if candidate.tag in _BLOCK_TAGS:
            parts.append(" ")
        for child in candidate.children:
            collect(child)
        if candidate.tag in _BLOCK_TAGS:
            parts.append(" ")

    collect(node)
    return _clean_text("".join(parts))


def _has_reference_target(entry: _Node, root: _Node) -> bool:
    """Require one primary reference and one matching, defined linked article."""
    links = _all_with_class(entry, "LINK")
    references = _all_with_class(entry, "LINKTXT")
    if len(links) != 1 or len(references) != 1:
        return False
    link_references = _all_with_class(links[0], "LINKTXT")
    if len(link_references) != 1 or link_references[0] is not references[0]:
        return False
    reference = _node_text(references[0])
    if not reference:
        return False
    linked_containers = [node for node in _walk(root, stop_classes=frozenset()) if "LINKENTRY" in _classes(node)]
    if len(linked_containers) != 1:
        return False
    linked_entries = [
        node for node in _walk(linked_containers[0], stop_classes=frozenset({"LINKENTRY"})) if "ENTRY" in _classes(node)
    ]
    if len(linked_entries) != 1:
        return False
    target = linked_entries[0]
    words = _all_with_class(target, "WORD")
    if len(words) != 1 or not _node_text(words[0]):
        return False
    if normalize_sum20_lookup(reference) != normalize_sum20_lookup(_node_text(words[0])):
        return False
    for sense in _all_with_class(target, "INTF") + _all_with_class(target, "INTN"):
        formula = _first_with_class(sense, "FORMULA")
        if formula is not None and _node_text(formula):
            return True
    return False


def _has_phrase_reference(entry: _Node, root: _Node) -> bool:
    """Recognize the source-only phrase-reference shape observed at wordid 172."""
    shape = (
        ("ENTRY", None),
        ("WORD", "ENTRY"),
        ("LPART", "ENTRY"),
        ("PHRF", "ENTRY"),
        ("PHRSYM", "PHRF"),
        ("PHRASE", "PHRF"),
        ("PHRTXT", "PHRASE"),
        ("LINK", "PHRASE"),
        ("LINKTXT", "LINK"),
    )
    # Inspect the whole article: orphan fields, foreign entries, embedded
    # LINKENTRY targets and even empty definition markers invalidate this shape.
    nodes = list(_walk(root, stop_classes=frozenset()))
    fields: dict[str, _Node] = {}
    for class_name, parent_class in shape:
        matches = [node for node in nodes if class_name in _classes(node)]
        if len(matches) != 1 or not _node_text(matches[0]):
            return False
        field = matches[0]
        if _classes(field) != {class_name}:
            return False
        if parent_class is not None and not any(child is field for child in fields[parent_class].children):
            return False
        fields[class_name] = field
    if fields["ENTRY"] is not entry:
        return False
    return all(not _classes(node) or any(node is field for field in fields.values()) for node in nodes)


def normalize_sum20_lookup(value: str) -> str:
    """Normalize a headword/query for exact offline СУМ-20 lookup."""
    normalized = _ACUTE_RE.sub("", str(value or "").strip().lower())
    normalized = normalized.replace("’", "'").replace("`", "'")
    return _clean_text(normalized)


def official_url_for_wordid(wordid: int) -> str:
    """Return the stable official URL stored with each offline record."""
    return f"{SUM20_OFFICIAL_BASE_URL}/?wordid={int(wordid)}"


def _extract_article_html(document_html: str) -> str:
    match = _ARTICLE_RE.search(document_html)
    if not match:
        raise Sum20ParseError("official response has no <article> element")
    return match.group(0)


def _grammar_and_pos(entry: _Node) -> tuple[str, str]:
    grammar_node = _first_with_class(entry, "LPART")
    grammar = _node_text(grammar_node) if grammar_node else ""
    grammar = grammar.lstrip(", ")
    match = _POS_RE.search(grammar)
    if match:
        return grammar, match.group(1).lower()
    if _ADJECTIVE_ENDINGS_RE.search(grammar):
        return grammar, "прикм."
    return grammar, ""


def _parsed_bib_fields(source: str) -> dict[str, str]:
    cleaned = _clean_text(source).strip("() ")
    if not cleaned:
        return {}
    if cleaned.lower().startswith(("з ", "із ")):
        return {"source": cleaned}
    return {"author": cleaned}


@dataclass(frozen=True)
class Sum20Citation:
    sense_ref: int
    citation_order: int
    citation_text: str
    parsed_bib_fields: dict[str, str]


@dataclass(frozen=True)
class Sum20Sense:
    sense_order: int
    definition: str
    register_labels: list[str]


@dataclass(frozen=True)
class Sum20Article:
    wordid: int
    headword: str
    stressed_headword: str
    pos: str
    grammar: str
    article_html: str
    article_text: str
    normalized_lookup_key: str
    senses: list[Sum20Sense]
    citations: list[Sum20Citation]

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256(self.article_html.encode("utf-8")).hexdigest()


def parse_sum20_article(document_html: str, wordid: int) -> Sum20Article:
    """Parse one official page into a loss-aware, structured СУМ-20 article."""
    article_html = _extract_article_html(document_html)
    parser = _ArticleTreeParser()
    parser.feed(article_html)
    parser.close()

    entries = [node for node in _walk(parser.root, stop_classes=frozenset({"LINKENTRY"})) if "ENTRY" in _classes(node)]
    if not entries:
        raise Sum20ParseError("official article contains no .ENTRY")
    if len(entries) != 1:
        raise Sum20ParseError("official article contains ambiguous primary .ENTRY elements")
    entry = entries[0]
    words = _all_with_class(entry, "WORD")
    if len(words) > 1:
        raise Sum20ParseError("official article contains ambiguous primary headwords")
    stressed_headword = _node_text(words[0]) if words else ""
    if not stressed_headword:
        raise Sum20ParseError("official article contains no headword")
    headword = _ACUTE_RE.sub("", stressed_headword)
    grammar, pos = _grammar_and_pos(entry)

    first_sense = _first_with_class(entry, "INTF")
    sense_nodes = ([first_sense] if first_sense is not None else []) + _all_with_class(entry, "INTN")
    senses: list[Sum20Sense] = []
    citations: list[Sum20Citation] = []
    citation_order = 0
    for sense_order, sense_node in enumerate(sense_nodes, start=1):
        formula = _first_with_class(sense_node, "FORMULA")
        definition = _node_text(formula) if formula else ""
        if not definition:
            continue
        labels = [_node_text(label) for label in _all_with_class(sense_node, "PARAM")]
        senses.append(Sum20Sense(sense_order, definition, [label for label in labels if label]))
        for illustration in _all_with_class(sense_node, "ILL"):
            text_node = _first_with_class(illustration, "ILLTXT")
            citation_text = _node_text(text_node) if text_node else ""
            if not citation_text:
                continue
            source_node = _first_with_class(illustration, "ILLSRC")
            source = _node_text(source_node) if source_node else ""
            citation_order += 1
            citations.append(
                Sum20Citation(
                    sense_ref=sense_order,
                    citation_order=citation_order,
                    citation_text=citation_text,
                    parsed_bib_fields=_parsed_bib_fields(source),
                )
            )
    if not senses:
        # Phrase references are source-only units; a matching embedded target
        # must not let them enter through the ordinary word-reference path.
        has_reference = (
            _has_phrase_reference(entry, parser.root)
            if _all_with_class(entry, "PHRF")
            else _has_reference_target(entry, parser.root)
        )
        if not has_reference:
            raise Sum20ParseError("official article contains no definition senses")

    return Sum20Article(
        wordid=int(wordid),
        headword=headword,
        stressed_headword=stressed_headword,
        pos=pos,
        grammar=grammar,
        article_html=article_html,
        article_text=_node_text(parser.root, include_entries=True),
        normalized_lookup_key=normalize_sum20_lookup(headword),
        senses=senses,
        citations=citations,
    )


SUM20_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sum20_articles (
    id INTEGER PRIMARY KEY,
    wordid INTEGER NOT NULL UNIQUE,
    normalized_lookup_key TEXT NOT NULL,
    headword TEXT NOT NULL,
    stressed_headword TEXT NOT NULL,
    pos TEXT NOT NULL DEFAULT '',
    grammar TEXT NOT NULL DEFAULT '',
    article_html TEXT NOT NULL,
    article_text TEXT NOT NULL,
    definition_text TEXT NOT NULL DEFAULT '',
    official_url TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    quarantine_reason TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS sum20_senses (
    id INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES sum20_articles(id) ON DELETE CASCADE,
    sense_order INTEGER NOT NULL,
    definition TEXT NOT NULL,
    register_labels TEXT NOT NULL DEFAULT '[]',
    UNIQUE(article_id, sense_order)
);
CREATE TABLE IF NOT EXISTS sum20_citations (
    id INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES sum20_articles(id) ON DELETE CASCADE,
    sense_ref INTEGER NOT NULL,
    "order" INTEGER NOT NULL,
    citation_text TEXT NOT NULL,
    parsed_bib_fields TEXT NOT NULL DEFAULT '{}',
    UNIQUE(article_id, "order")
);
CREATE INDEX IF NOT EXISTS idx_sum20_articles_lookup
    ON sum20_articles(normalized_lookup_key, wordid);
CREATE INDEX IF NOT EXISTS idx_sum20_senses_article
    ON sum20_senses(article_id, sense_order);
CREATE INDEX IF NOT EXISTS idx_sum20_citations_article
    ON sum20_citations(article_id, "order");
CREATE VIRTUAL TABLE IF NOT EXISTS sum20_articles_fts USING fts5(
    normalized_lookup_key UNINDEXED,
    headword,
    definition_text,
    content='sum20_articles',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS sum20_articles_ai
AFTER INSERT ON sum20_articles BEGIN
    INSERT INTO sum20_articles_fts(rowid, normalized_lookup_key, headword, definition_text)
    VALUES (new.id, new.normalized_lookup_key, new.headword, new.definition_text);
END;
CREATE TRIGGER IF NOT EXISTS sum20_articles_ad
AFTER DELETE ON sum20_articles BEGIN
    INSERT INTO sum20_articles_fts(
        sum20_articles_fts, rowid, normalized_lookup_key, headword, definition_text
    )
    VALUES ('delete', old.id, old.normalized_lookup_key, old.headword, old.definition_text);
END;
CREATE TRIGGER IF NOT EXISTS sum20_articles_au
AFTER UPDATE ON sum20_articles BEGIN
    INSERT INTO sum20_articles_fts(
        sum20_articles_fts, rowid, normalized_lookup_key, headword, definition_text
    )
    VALUES ('delete', old.id, old.normalized_lookup_key, old.headword, old.definition_text);
    INSERT INTO sum20_articles_fts(rowid, normalized_lookup_key, headword, definition_text)
    VALUES (new.id, new.normalized_lookup_key, new.headword, new.definition_text);
END;
CREATE TABLE IF NOT EXISTS sum20_crawl_checkpoint (
    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
    last_wordid INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT ''
);
INSERT OR IGNORE INTO sum20_crawl_checkpoint(singleton, last_wordid, updated_at)
VALUES (1, 0, '');
CREATE TABLE IF NOT EXISTS sum20_crawl_outcomes (
    wordid INTEGER PRIMARY KEY,
    status TEXT NOT NULL CHECK(status IN ('ok', 'not_found', 'transient_error', 'parse_error')),
    content_sha256 TEXT NOT NULL DEFAULT '',
    attempted_at TEXT NOT NULL,
    error_text TEXT NOT NULL DEFAULT ''
);
"""


def ensure_sum20_official_schema(conn: SQLiteConnection) -> None:
    """Create the official СУМ-20 collection and resumable-crawl metadata."""
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SUM20_SCHEMA_SQL)
    ensure_sum20_quarantine_column(conn)


def ensure_sum20_quarantine_column(conn: SQLiteConnection) -> bool:
    """Add ``sum20_articles.quarantine_reason`` to a table created before #9609; return whether it was added."""
    columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(sum20_articles)")}
    if not columns or QUARANTINE_COLUMN in columns:
        return False
    conn.execute(f"ALTER TABLE sum20_articles ADD COLUMN {QUARANTINE_COLUMN} TEXT NOT NULL DEFAULT ''")
    return True


def live_article_predicate(columns: Iterable[str], alias: str = "") -> str:
    """SQL predicate that keeps only non-quarantined ``sum20_articles`` rows.

    Quarantined rows stay in the table (never deleted) but no retrieval path
    returns them.  A restored table may predate the quarantine column while retaining
    unverified codification rows; their parser version remains excluded.
    """
    prefix = f"{alias}." if alias else ""
    columns = set(columns)
    predicates = []
    if QUARANTINE_COLUMN in columns:
        predicates.append(f"{prefix}{QUARANTINE_COLUMN} = ''")
    if "parser_version" in columns:
        predicates.append(f"{prefix}parser_version != 'v1-official-codification'")
    return " AND ".join(predicates) or "1 = 1"


def live_article_predicate_for(conn: SQLiteConnection | sqlite3.Cursor, alias: str = "") -> str:
    """``live_article_predicate`` for the ``sum20_articles`` table behind a connection or cursor."""
    rows = conn.execute("PRAGMA table_info(sum20_articles)").fetchall()
    return live_article_predicate((str(row[1]) for row in rows), alias)


def utc_now() -> str:
    """Return a stable, timezone-aware timestamp for crawl provenance."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def upsert_sum20_article(conn: SQLiteConnection, article: Sum20Article, *, fetched_at: str | None = None) -> bool:
    """Replace changed content or parser output, retaining row identity/quarantine.

    Fresh fetches omit ``fetched_at`` to refresh retrieval provenance. Offline
    reparses must explicitly supply the stored retrieval timestamp.
    """
    fetched_at = utc_now() if fetched_at is None else fetched_at
    content_sha256 = article.content_sha256
    existing = conn.execute(
        "SELECT id, content_sha256, parser_version FROM sum20_articles WHERE wordid = ?", (article.wordid,)
    ).fetchone()
    if (
        existing is not None
        and str(existing["content_sha256"] if isinstance(existing, sqlite3.Row) else existing[1]) == content_sha256
        and str(existing["parser_version"] if isinstance(existing, sqlite3.Row) else existing[2]) == PARSER_VERSION
    ):
        article_id = int(existing["id"] if isinstance(existing, sqlite3.Row) else existing[0])
        conn.execute("UPDATE sum20_articles SET fetched_at = ? WHERE id = ?", (fetched_at, article_id))
        return False

    definition_text = "\n".join(sense.definition for sense in article.senses)
    conn.execute(
        """
        INSERT INTO sum20_articles (
            wordid, normalized_lookup_key, headword, stressed_headword, pos, grammar,
            article_html, article_text, definition_text, official_url, fetched_at,
            content_sha256, parser_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(wordid) DO UPDATE SET
            normalized_lookup_key = excluded.normalized_lookup_key,
            headword = excluded.headword,
            stressed_headword = excluded.stressed_headword,
            pos = excluded.pos,
            grammar = excluded.grammar,
            article_html = excluded.article_html,
            article_text = excluded.article_text,
            definition_text = excluded.definition_text,
            official_url = excluded.official_url,
            fetched_at = excluded.fetched_at,
            content_sha256 = excluded.content_sha256,
            parser_version = excluded.parser_version
        """,
        (
            article.wordid,
            article.normalized_lookup_key,
            article.headword,
            article.stressed_headword,
            article.pos,
            article.grammar,
            article.article_html,
            article.article_text,
            definition_text,
            official_url_for_wordid(article.wordid),
            fetched_at,
            content_sha256,
            PARSER_VERSION,
        ),
    )
    article_id = int(conn.execute("SELECT id FROM sum20_articles WHERE wordid = ?", (article.wordid,)).fetchone()[0])
    conn.execute("DELETE FROM sum20_senses WHERE article_id = ?", (article_id,))
    conn.execute("DELETE FROM sum20_citations WHERE article_id = ?", (article_id,))
    conn.executemany(
        """
        INSERT INTO sum20_senses(article_id, sense_order, definition, register_labels)
        VALUES (?, ?, ?, ?)
        """,
        [
            (article_id, sense.sense_order, sense.definition, json.dumps(sense.register_labels, ensure_ascii=False))
            for sense in article.senses
        ],
    )
    conn.executemany(
        """
        INSERT INTO sum20_citations(
            article_id, sense_ref, "order", citation_text, parsed_bib_fields
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                article_id,
                citation.sense_ref,
                citation.citation_order,
                citation.citation_text,
                json.dumps(citation.parsed_bib_fields, ensure_ascii=False, sort_keys=True),
            )
            for citation in article.citations
        ],
    )
    return True


def record_crawl_outcome(
    conn: SQLiteConnection,
    *,
    wordid: int,
    status: str,
    content_sha256: str = "",
    error_text: str = "",
) -> None:
    """Persist a fetch attempt without conflating transient failures with misses."""
    if status not in {"ok", "not_found", "transient_error", "parse_error"}:
        raise ValueError(f"unsupported СУМ-20 crawl status: {status}")
    conn.execute(
        """
        INSERT INTO sum20_crawl_outcomes(wordid, status, content_sha256, attempted_at, error_text)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(wordid) DO UPDATE SET
            status = excluded.status,
            content_sha256 = excluded.content_sha256,
            attempted_at = excluded.attempted_at,
            error_text = excluded.error_text
        """,
        (wordid, status, content_sha256, utc_now(), error_text),
    )


def advance_crawl_checkpoint(conn: SQLiteConnection, wordid: int) -> None:
    """Advance only after an unambiguous terminal outcome."""
    conn.execute(
        """
        UPDATE sum20_crawl_checkpoint
        SET last_wordid = MAX(last_wordid, ?), updated_at = ?
        WHERE singleton = 1
        """,
        (int(wordid), utc_now()),
    )


def crawl_resume_wordid(conn: SQLiteConnection) -> int:
    """Return the next safe wordid after the durable terminal checkpoint."""
    row = conn.execute("SELECT last_wordid FROM sum20_crawl_checkpoint WHERE singleton = 1").fetchone()
    last_wordid = int(row[0]) if row else 0
    return last_wordid + 1


@dataclass(frozen=True)
class FetchOutcome:
    status: str
    document_html: str = ""
    error_text: str = ""
    http_status: int | None = None
    terminal: bool = False


def _retry_delay(response: requests.Response | None, retry_backoff_s: float, attempt: int) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After", "")
        if retry_after.isdigit():
            return max(float(retry_after), retry_backoff_s)
    return retry_backoff_s * (2**attempt)


def fetch_sum20_wordid(
    wordid: int,
    *,
    session: requests.Session | None = None,
    timeout_s: float = 30.0,
    retries: int = 3,
    retry_backoff_s: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
) -> FetchOutcome:
    """GET one official wordid with bounded exponential backoff.

    Network/408/425/429/5xx failures are bounded retries. Other non-200
    responses stop on the first response, stored lossily as ``transient_error``
    with numeric HTTP evidence and ``terminal=True``. Only 404 proves a miss.
    """
    client = session or requests.Session()
    # A requests.Session already carries "python-requests/<version>" and
    # "Accept: */*", so setdefault() never applied the project's identifying
    # headers. sum20ua.com answers 403 to the python-requests agent (#5228).
    # Replace only the library defaults; a caller's explicit header is kept.
    if client.headers.get("User-Agent") in (None, requests.utils.default_user_agent()):
        client.headers["User-Agent"] = DEFAULT_USER_AGENT
    if client.headers.get("Accept") in (None, "*/*"):
        client.headers["Accept"] = "text/html,application/xhtml+xml"
    url = official_url_for_wordid(wordid)
    last_error = ""
    last_code = None
    for attempt in range(max(0, retries) + 1):
        response: requests.Response | None = None
        try:
            response = client.get(url, params={"page": 0}, timeout=timeout_s, allow_redirects=False)
            last_code = response.status_code
            if last_code == 404:
                return FetchOutcome("not_found", http_status=last_code)
            if last_code in {408, 425, 429} or 500 <= last_code <= 599:
                last_error = f"HTTP {last_code}"
            elif last_code != 200:
                # Keep the four-status storage contract; terminal evidence is separate.
                return FetchOutcome(
                    "transient_error", error_text=f"HTTP {last_code}", http_status=last_code, terminal=True
                )
            else:
                try:
                    parse_sum20_article(response.text, wordid)
                except (Sum20ParseError, ValueError, TypeError, RecursionError):
                    return FetchOutcome(
                        "parse_error", error_text="unusable article", http_status=last_code, terminal=True
                    )
                return FetchOutcome("ok", document_html=response.text, http_status=last_code)
        except requests.RequestException:
            last_code = None
            last_error = "network request failure"
        if attempt < max(0, retries):
            sleep(_retry_delay(response, retry_backoff_s, attempt))
    return FetchOutcome("transient_error", error_text=last_error or "request retries exhausted", http_status=last_code)
