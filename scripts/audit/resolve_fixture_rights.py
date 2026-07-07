"""Resolve qg bakeoff fixture evidence rights from local source databases.

This resolver is intentionally mechanical: fixture evidence text is searched
against SQLite rows first, and license labels come only from the committed
source_license_map.json table. Unmatched or unmapped quoted text fails closed
as UNKNOWN.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sqlite3
import unicodedata
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_DIR = REPO_ROOT / "tests/fixtures/qg_bakeoff"
DEFAULT_RIGHTS_JSON = REPO_ROOT / "tests/fixtures/qg_bakeoff_rights/rights.json"
DEFAULT_MATRIX_DOC = REPO_ROOT / "docs/projects/ua-eval-harness/fixture-rights-matrix.md"
DEFAULT_LICENSE_MAP = Path(__file__).with_name("source_license_map.json")
DEFAULT_SOURCES_DB = REPO_ROOT / "data/sources.db"
DEFAULT_VESUM_DB = REPO_ROOT / "data/vesum.db"

CHUNK_ID_RE = re.compile(r"\b(?:[a-f0-9]{8}_c\d{4}|[\w-]+_s\d{4}|ext-[\w-]+-\d+)\b")
QUOTE_RE = re.compile(r"«([^»]+)»")
TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яІіЇїЄєҐґ'’ʼ-]{2,}", re.UNICODE)
FTS_TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яІіЇїЄєҐґ]{2,}", re.UNICODE)


@dataclass(frozen=True)
class TableSpec:
    db_name: str
    table: str
    id_col: str
    text_cols: tuple[str, ...]
    chunk_col: str | None = None
    source_cols: tuple[str, ...] = ()
    fts_table: str | None = None


@dataclass(frozen=True)
class SourceHit:
    table: str
    row_id: str
    chunk_id: str
    source_file: str
    text: str
    quote: str
    score: float
    match_method: str
    matched_fragment: str


SOURCE_TABLES: tuple[TableSpec, ...] = (
    TableSpec(
        db_name="sources",
        table="external_articles",
        id_col="id",
        chunk_col="chunk_id",
        source_cols=("source_file", "url", "title"),
        text_cols=("text", "title", "speaker"),
        fts_table="external_fts",
    ),
    TableSpec(
        db_name="sources",
        table="literary_texts",
        id_col="id",
        chunk_col="chunk_id",
        source_cols=("source_file", "source_url", "title", "author", "work"),
        text_cols=("text", "title"),
        fts_table="literary_fts",
    ),
    TableSpec(
        db_name="sources",
        table="textbooks",
        id_col="id",
        chunk_col="chunk_id",
        source_cols=("source_file", "title", "author_uk", "author"),
        text_cols=("text", "title"),
        fts_table="textbooks_fts",
    ),
    TableSpec(
        db_name="sources",
        table="wikipedia",
        id_col="id",
        source_cols=("url", "title"),
        text_cols=("text", "title"),
        fts_table="wikipedia_fts",
    ),
    TableSpec(
        db_name="sources",
        table="ukrainian_wiki",
        id_col="id",
        chunk_col="passage_id",
        source_cols=("article_path", "source_registry_path", "article_title"),
        text_cols=("text", "article_title", "section_path"),
        fts_table="ukrainian_wiki_fts",
    ),
    TableSpec(
        db_name="sources",
        table="grinchenko",
        id_col="id",
        source_cols=("source", "word"),
        text_cols=("definition", "word"),
    ),
    TableSpec(
        db_name="sources",
        table="sum11",
        id_col="id",
        source_cols=("source", "word"),
        text_cols=("text", "definition", "word"),
    ),
    TableSpec(
        db_name="sources",
        table="frazeolohichnyi",
        id_col="id",
        source_cols=("source", "word"),
        text_cols=("text", "definition", "word"),
        fts_table="frazeolohichnyi_fts",
    ),
    TableSpec(
        db_name="sources",
        table="wiktionary",
        id_col="id",
        source_cols=("source", "word"),
        text_cols=("text", "definitions", "word"),
    ),
    TableSpec(
        db_name="sources",
        table="wiktionary_etymology",
        id_col="rowid",
        source_cols=("source_url", "headword", "requested_lemma"),
        text_cols=("etymology_text", "section_raw", "headword"),
    ),
    TableSpec(
        db_name="sources",
        table="goroh_etymology",
        id_col="rowid",
        source_cols=("source_url", "headword", "requested_lemma"),
        text_cols=("etymology_text", "headword"),
    ),
    TableSpec(
        db_name="vesum",
        table="forms",
        id_col="rowid",
        source_cols=("lemma", "word_form"),
        text_cols=("word_form", "lemma", "tags", "pos"),
    ),
)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    replacements = {
        "\r": " ",
        "\n": " ",
        "\t": " ",
        "\u00a0": " ",
        "’": "'",
        "ʼ": "'",
        "`": "'",
        "„": '"',
        "“": '"',
        "”": '"',
        "«": '"',
        "»": '"',
        "—": "-",
        "–": "-",
        "…": "...",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return re.sub(r"\s+", " ", text.casefold()).strip()


def display_text(text: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def quote_segments(quote: str) -> list[str]:
    parts = re.split(r"\.\.\.|…", quote)
    segments = [part.strip(" ;:,.—–-") for part in parts if part.strip(" ;:,.—–-")]
    if not segments:
        segments = [quote]
    return sorted(segments, key=len, reverse=True)


def score_quote(quote: str, text: str) -> tuple[float, str, str]:
    normalized_text = normalize_text(text)
    normalized_quote = normalize_text(quote)
    if not normalized_quote:
        return 0.0, "empty quote", ""

    for segment in quote_segments(quote):
        normalized_segment = normalize_text(segment)
        if len(normalized_segment) >= 8 and normalized_segment in normalized_text:
            method = "substring"
            if "..." in normalized_quote:
                method = "ellipsis-substring"
            return 1.0, method, segment

    tokens = [token for token in TOKEN_RE.findall(normalized_quote) if len(token) >= 4]
    if not tokens:
        return 0.0, "no searchable tokens", ""

    anchors = tokens[:3]
    windows: list[str] = []
    for anchor in anchors:
        start = 0
        while True:
            index = normalized_text.find(anchor, start)
            if index < 0:
                break
            left = max(0, index - 80)
            right = min(len(normalized_text), index + len(normalized_quote) + 120)
            windows.append(normalized_text[left:right])
            start = index + len(anchor)

    if not windows:
        return 0.0, "no token overlap", ""

    best = max(SequenceMatcher(None, normalized_quote, window).ratio() for window in windows)
    if best >= 0.72:
        return best, "fuzzy-window", ""
    return best, "low-similarity", ""


def extract_wikipedia_titles(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"uk\.wikipedia\s+«([^»]+)»", text)]


def is_pointer_quote(text: str, match: re.Match[str]) -> bool:
    prefix = text[max(0, match.start() - 90) : match.start()].casefold()
    suffix = text[match.end() : match.end() + 50].casefold()
    if re.search(
        r"(search_literary|search_heritage|query_wikipedia\s+search|"
        r"verify_source_attribution|verify_quote|search_text)\([^)]*$",
        prefix,
    ):
        return True
    return "uk.wikipedia" in prefix[-45:] and "§" in suffix


def extract_quote_candidates(text: str, row_kind: str) -> list[str]:
    candidates: list[str] = []
    for match in QUOTE_RE.finditer(text):
        quote = match.group(1).strip()
        if not quote or is_pointer_quote(text, match):
            continue
        if len(normalize_text(quote)) >= 8:
            candidates.append(quote)

    if row_kind == "distractor" and not candidates:
        stripped = text.strip()
        if stripped:
            candidates.append(stripped)
    return candidates


def classify_row(claim_id: str, row_kind: str, text: str) -> str:
    if claim_id == "root_vlog":
        return "POINTER"
    if row_kind == "distractor":
        return "QUOTED_TEXT"
    if extract_quote_candidates(text, row_kind):
        return "QUOTED_TEXT"
    return "POINTER"


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    except sqlite3.Error:
        return set()


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def row_value(row: sqlite3.Row, columns: set[str], column: str) -> str:
    if column not in columns:
        return ""
    value = row[column]
    return "" if value is None else str(value)


def source_file_for_row(spec: TableSpec, row: sqlite3.Row, columns: set[str]) -> str:
    for column in spec.source_cols:
        value = row_value(row, columns, column)
        if value:
            return value
    return spec.table


def chunk_id_for_row(spec: TableSpec, row: sqlite3.Row, columns: set[str]) -> str:
    if spec.chunk_col and spec.chunk_col in columns:
        value = row_value(row, columns, spec.chunk_col)
        if value:
            return value
    return f"{spec.table}:{row_value(row, columns, spec.id_col)}"


def text_for_row(spec: TableSpec, row: sqlite3.Row, columns: set[str]) -> str:
    parts = [row_value(row, columns, column) for column in spec.text_cols]
    return "\n".join(part for part in parts if part)


def make_hit(spec: TableSpec, row: sqlite3.Row, quote: str, score: float, method: str, fragment: str) -> SourceHit:
    columns = set(row.keys())
    return SourceHit(
        table=spec.table,
        row_id=row_value(row, columns, spec.id_col),
        chunk_id=chunk_id_for_row(spec, row, columns),
        source_file=source_file_for_row(spec, row, columns),
        text=text_for_row(spec, row, columns),
        quote=quote,
        score=score,
        match_method=method,
        matched_fragment=fragment,
    )


def candidate_hit(spec: TableSpec, row: sqlite3.Row, quotes: list[str], method_prefix: str) -> SourceHit | None:
    columns = set(row.keys())
    text = text_for_row(spec, row, columns)
    best: SourceHit | None = None
    for quote in quotes:
        score, method, fragment = score_quote(quote, text)
        if score < 0.72:
            continue
        hit = make_hit(spec, row, quote, score, f"{method_prefix}:{method}", fragment)
        if best is None or hit.score > best.score:
            best = hit
    return best


def select_columns(spec: TableSpec, conn: sqlite3.Connection) -> str:
    columns = table_columns(conn, spec.table)
    requested = [spec.id_col]
    requested.extend(spec.text_cols)
    requested.extend(spec.source_cols)
    if spec.chunk_col:
        requested.append(spec.chunk_col)
    present = []
    for column in requested:
        if column in columns and column not in present:
            present.append(column)
    if spec.id_col == "rowid" and "rowid" not in present:
        present.insert(0, "rowid")
    return ", ".join(present) if present else "*"


def lookup_chunk_ids(
    connections: dict[str, sqlite3.Connection],
    chunk_ids: list[str],
    quotes: list[str],
) -> SourceHit | None:
    best: SourceHit | None = None
    for spec in SOURCE_TABLES:
        if not spec.chunk_col:
            continue
        conn = connections.get(spec.db_name)
        if conn is None or not table_exists(conn, spec.table):
            continue
        columns = table_columns(conn, spec.table)
        if spec.chunk_col not in columns:
            continue
        selected = select_columns(spec, conn)
        for chunk_id in chunk_ids:
            rows = conn.execute(
                f"""
                SELECT {selected}
                FROM {spec.table}
                WHERE {spec.chunk_col} = ?
                ORDER BY {spec.id_col}
                """,
                (chunk_id,),
            ).fetchall()
            for row in rows:
                hit = candidate_hit(spec, row, quotes, "chunk-id")
                if hit and (best is None or hit.score > best.score):
                    best = hit
    return best


def lookup_wikipedia_titles(
    connections: dict[str, sqlite3.Connection],
    titles: list[str],
    quotes: list[str],
) -> SourceHit | None:
    conn = connections.get("sources")
    if conn is None or not titles or not table_exists(conn, "wikipedia"):
        return None

    spec = next(item for item in SOURCE_TABLES if item.table == "wikipedia")
    selected = select_columns(spec, conn)
    best: SourceHit | None = None
    for title in titles:
        rows = conn.execute(
            f"""
            SELECT {selected}
            FROM wikipedia
            WHERE title = ? OR title LIKE ?
            ORDER BY id
            """,
            (title, f"%{title}%"),
        ).fetchall()
        for row in rows:
            hit = candidate_hit(spec, row, quotes, "wikipedia-title")
            if hit and (best is None or hit.score > best.score):
                best = hit
    return best


def fts_query_for_quote(quote: str, max_tokens: int) -> str:
    tokens = []
    for token in FTS_TOKEN_RE.findall(normalize_text(quote)):
        if len(token) >= 3 and token not in tokens:
            tokens.append(token)
        if len(tokens) >= max_tokens:
            break
    return " AND ".join(tokens)


def lookup_fts(
    connections: dict[str, sqlite3.Connection],
    quotes: list[str],
) -> SourceHit | None:
    best: SourceHit | None = None
    for spec in SOURCE_TABLES:
        if not spec.fts_table:
            continue
        conn = connections.get(spec.db_name)
        if conn is None or not table_exists(conn, spec.table) or not table_exists(conn, spec.fts_table):
            continue
        selected = ", ".join(f"base.{col.strip()}" for col in select_columns(spec, conn).split(", "))
        for quote in quotes:
            for max_tokens in (8, 5, 3):
                query = fts_query_for_quote(quote, max_tokens)
                if not query:
                    continue
                try:
                    rows = conn.execute(
                        f"""
                        SELECT {selected}
                        FROM {spec.fts_table} AS fts
                        JOIN {spec.table} AS base ON base.{spec.id_col} = fts.rowid
                        WHERE {spec.fts_table} MATCH ?
                        ORDER BY base.{spec.id_col}
                        LIMIT 20
                        """,
                        (query,),
                    ).fetchall()
                except sqlite3.Error:
                    continue
                for row in rows:
                    hit = candidate_hit(spec, row, [quote], "fts")
                    if hit and (best is None or hit.score > best.score):
                        best = hit
                if best:
                    break
    return best


def lookup_substring(
    connections: dict[str, sqlite3.Connection],
    quotes: list[str],
) -> SourceHit | None:
    best: SourceHit | None = None
    substring_tables = {"external_articles", "literary_texts", "textbooks", "wikipedia", "ukrainian_wiki"}
    for spec in SOURCE_TABLES:
        if spec.table not in substring_tables:
            continue
        conn = connections.get(spec.db_name)
        if conn is None or not table_exists(conn, spec.table):
            continue
        columns = table_columns(conn, spec.table)
        searchable_cols = [column for column in spec.text_cols if column in columns]
        if not searchable_cols:
            continue
        selected = select_columns(spec, conn)
        for quote in quotes:
            for segment in quote_segments(quote)[:1]:
                normalized_segment = normalize_text(segment)
                if len(normalized_segment) < 16 or len(normalized_segment) > 160:
                    continue
                clauses = " OR ".join(f"{column} LIKE ?" for column in searchable_cols)
                params = tuple(f"%{segment}%" for _ in searchable_cols)
                try:
                    rows = conn.execute(
                        f"""
                        SELECT {selected}
                        FROM {spec.table}
                        WHERE {clauses}
                        ORDER BY {spec.id_col}
                        LIMIT 20
                        """,
                        params,
                    ).fetchall()
                except sqlite3.Error:
                    continue
                for row in rows:
                    hit = candidate_hit(spec, row, [quote], "substring-scan")
                    if hit and (best is None or hit.score > best.score):
                        best = hit
                if best:
                    return best
    return best


def resolve_hit(
    connections: dict[str, sqlite3.Connection],
    evidence_text: str,
    row_kind: str,
) -> SourceHit | None:
    quotes = extract_quote_candidates(evidence_text, row_kind)
    if not quotes:
        return None

    chunk_ids = CHUNK_ID_RE.findall(evidence_text)
    hit = lookup_chunk_ids(connections, chunk_ids, quotes)
    if hit:
        return hit

    hit = lookup_wikipedia_titles(connections, extract_wikipedia_titles(evidence_text), quotes)
    if hit:
        return hit

    hit = lookup_fts(connections, quotes)
    if hit:
        return hit

    return None


def load_license_map(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError(f"{path} must contain an entries list")
    required = {"table", "source_file_pattern", "license", "verdict", "basis_url", "basis_note"}
    for entry in entries:
        missing = required - set(entry)
        if missing:
            raise ValueError(f"License map entry missing {sorted(missing)}: {entry}")
    return entries


def license_for_hit(hit: SourceHit, license_entries: list[dict[str, str]]) -> dict[str, str] | None:
    for entry in license_entries:
        if entry["table"] != hit.table:
            continue
        if fnmatch.fnmatchcase(hit.source_file, entry["source_file_pattern"]):
            return entry
    return None


def fixture_evidence_rows(fixture_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(fixture_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        slug = path.stem
        verification_log = data.get("verification_log", "")
        if verification_log:
            rows.append(
                {
                    "fixture": slug,
                    "claim_id": "root_vlog",
                    "row_kind": "pointer",
                    "quote_or_ref": verification_log,
                }
            )
        for claim in data.get("claims", []):
            claim_id = claim.get("claim_id")
            distractor = claim.get("distractor_evidence")
            verified_by = claim.get("verified_by")
            if distractor:
                rows.append(
                    {
                        "fixture": slug,
                        "claim_id": f"{claim_id}_distractor",
                        "row_kind": "distractor",
                        "quote_or_ref": distractor,
                    }
                )
            if verified_by:
                rows.append(
                    {
                        "fixture": slug,
                        "claim_id": f"{claim_id}_verified",
                        "row_kind": "verified",
                        "quote_or_ref": verified_by,
                    }
                )
    return rows


def make_pointer_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "fixture": row["fixture"],
        "claim_id": row["claim_id"],
        "quote_or_ref": row["quote_or_ref"],
        "classification": "POINTER",
        "matched_table": None,
        "source_file": None,
        "chunk_id": None,
        "license": "N/A",
        "verdict": "SHIP",
        "evidence": {
            "match_method": "pointer-only provenance row; no source text redistributed",
            "similarity": None,
            "quote": None,
            "license_basis": "No license lookup needed for pointer-only provenance.",
            "license_basis_url": None,
        },
    }


def make_quoted_row(
    row: dict[str, str],
    hit: SourceHit | None,
    license_entry: dict[str, str] | None,
) -> dict[str, Any]:
    if hit is None:
        return {
            "fixture": row["fixture"],
            "claim_id": row["claim_id"],
            "quote_or_ref": row["quote_or_ref"],
            "classification": "QUOTED_TEXT",
            "matched_table": None,
            "source_file": None,
            "chunk_id": None,
            "license": "UNKNOWN",
            "verdict": "UNKNOWN",
            "evidence": {
                "match_method": "no matching source row found",
                "similarity": None,
                "quote": None,
                "license_basis": "Fail-closed: unmatched quoted evidence is UNKNOWN.",
                "license_basis_url": None,
            },
        }

    if license_entry is None:
        license_name = "UNKNOWN"
        verdict = "UNKNOWN"
        basis = "Fail-closed: matched source has no committed source_license_map.json entry."
        basis_url = None
    else:
        license_name = license_entry["license"]
        verdict = license_entry["verdict"]
        basis = license_entry["basis_note"]
        basis_url = license_entry["basis_url"]

    return {
        "fixture": row["fixture"],
        "claim_id": row["claim_id"],
        "quote_or_ref": row["quote_or_ref"],
        "classification": "QUOTED_TEXT",
        "matched_table": hit.table,
        "source_file": hit.source_file,
        "chunk_id": hit.chunk_id,
        "license": license_name,
        "verdict": verdict,
        "evidence": {
            "match_method": hit.match_method,
            "similarity": round(hit.score, 3),
            "quote": hit.quote,
            "matched_fragment": hit.matched_fragment or None,
            "source_snippet": display_text(hit.text),
            "license_basis": basis,
            "license_basis_url": basis_url,
        },
    }


def resolve_rows(
    fixture_dir: Path,
    sources_db: Path,
    vesum_db: Path,
    license_map: Path,
) -> list[dict[str, Any]]:
    license_entries = load_license_map(license_map)
    connections: dict[str, sqlite3.Connection] = {
        "sources": sqlite3.connect(sources_db),
        "vesum": sqlite3.connect(vesum_db),
    }
    for conn in connections.values():
        conn.row_factory = sqlite3.Row
    try:
        resolved: list[dict[str, Any]] = []
        for row in fixture_evidence_rows(fixture_dir):
            classification = classify_row(row["claim_id"], row["row_kind"], row["quote_or_ref"])
            if classification == "POINTER":
                resolved.append(make_pointer_row(row))
                continue

            hit = resolve_hit(connections, row["quote_or_ref"], row["row_kind"])
            license_entry = license_for_hit(hit, license_entries) if hit else None
            resolved.append(make_quoted_row(row, hit, license_entry))
        return resolved
    finally:
        for conn in connections.values():
            conn.close()


def markdown_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\n", " ").replace("|", "\\|")
    return display_text(text, 100)


def evidence_summary(row: dict[str, Any]) -> str:
    evidence = row.get("evidence", {})
    parts = [str(evidence.get("match_method") or "")]
    if evidence.get("similarity") is not None:
        parts.append(f"similarity={evidence['similarity']}")
    if evidence.get("license_basis"):
        parts.append(str(evidence["license_basis"]))
    return "; ".join(part for part in parts if part)


def render_matrix_doc(rows: list[dict[str, Any]], license_map: Path) -> str:
    fixture_count = len({row["fixture"] for row in rows})
    verdict_counts = Counter(row["verdict"] for row in rows)
    classification_counts = Counter(row["classification"] for row in rows)
    license_counts = Counter(row["license"] for row in rows)
    license_entries = load_license_map(license_map)

    lines = [
        "# Fixture Rights Matrix",
        "",
        "Generated by `.venv/bin/python -m scripts.audit.resolve_fixture_rights`.",
        "",
        "## Method",
        "",
        "This matrix replaces the prior LLM-labeled rights pass. The resolver now extracts fixture evidence rows mechanically, searches quoted text against local SQLite source rows, and applies only committed `scripts/audit/source_license_map.json` entries for license labels. Unmatched quotes and matched-but-unmapped sources are `UNKNOWN`; the resolver does not infer licenses from fixture prose.",
        "",
        "Pointer provenance rows contain no redistributable source quote and are classified `POINTER` with verdict `SHIP`.",
        "",
        "## Summary",
        "",
        f"- Fixtures: {fixture_count}",
        f"- Rows: {len(rows)}",
        "",
        "### Verdict Counts",
        "",
        "| Verdict | Count |",
        "|---|---:|",
    ]
    for verdict, count in sorted(verdict_counts.items()):
        lines.append(f"| {verdict} | {count} |")

    lines.extend(["", "### Classification Counts", "", "| Classification | Count |", "|---|---:|"])
    for classification, count in sorted(classification_counts.items()):
        lines.append(f"| {classification} | {count} |")

    lines.extend(["", "### License Counts", "", "| License | Count |", "|---|---:|"])
    for license_name, count in sorted(license_counts.items()):
        lines.append(f"| {license_name} | {count} |")

    lines.extend(
        [
            "",
            "## Committed License Map",
            "",
            "| Table | Source pattern | License | Verdict | Basis |",
            "|---|---|---|---|---|",
        ]
    )
    for entry in license_entries:
        basis = f"{entry['basis_note']} ({entry['basis_url']})"
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(entry["table"]),
                    markdown_cell(entry["source_file_pattern"]),
                    markdown_cell(entry["license"]),
                    markdown_cell(entry["verdict"]),
                    markdown_cell(basis),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Matrix",
            "",
            "| Fixture | Claim ID | Classification | Matched table | Chunk ID | Source file | License | Verdict | Evidence | Quote or Ref |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row["fixture"]),
                    markdown_cell(row["claim_id"]),
                    markdown_cell(row["classification"]),
                    markdown_cell(row["matched_table"]),
                    markdown_cell(row["chunk_id"]),
                    markdown_cell(row["source_file"]),
                    markdown_cell(row["license"]),
                    markdown_cell(row["verdict"]),
                    markdown_cell(evidence_summary(row)),
                    markdown_cell(row["quote_or_ref"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def write_outputs(rows: list[dict[str, Any]], rights_json: Path, matrix_doc: Path, license_map: Path) -> None:
    rights_json.parent.mkdir(parents=True, exist_ok=True)
    rights_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    matrix_doc.parent.mkdir(parents=True, exist_ok=True)
    matrix_doc.write_text(render_matrix_doc(rows, license_map), encoding="utf-8")


def print_summary(rows: list[dict[str, Any]], rights_json: Path, matrix_doc: Path, wrote: bool) -> None:
    fixture_count = len({row["fixture"] for row in rows})
    print(f"fixtures={fixture_count} rows={len(rows)}")
    print(f"classification_counts={dict(sorted(Counter(row['classification'] for row in rows).items()))}")
    print(f"verdict_counts={dict(sorted(Counter(row['verdict'] for row in rows).items()))}")
    print(f"license_counts={dict(sorted(Counter(row['license'] for row in rows).items()))}")
    for verdict in sorted({row["verdict"] for row in rows}):
        example = next(
            (
                row
                for row in rows
                if row["verdict"] == verdict and row["classification"] == "QUOTED_TEXT"
            ),
            next(row for row in rows if row["verdict"] == verdict),
        )
        print(f"example[{verdict}]=" + json.dumps(example, ensure_ascii=False, sort_keys=True))
    if wrote:
        print(f"wrote={rights_json}")
        print(f"wrote={matrix_doc}")
    else:
        print("wrote=false")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--rights-json", type=Path, default=DEFAULT_RIGHTS_JSON)
    parser.add_argument("--matrix-doc", type=Path, default=DEFAULT_MATRIX_DOC)
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--license-map", type=Path, default=DEFAULT_LICENSE_MAP)
    parser.add_argument("--check", action="store_true", help="Resolve and print summary without writing files.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rows = resolve_rows(args.fixtures, args.sources_db, args.vesum_db, args.license_map)
    if not args.check:
        write_outputs(rows, args.rights_json, args.matrix_doc, args.license_map)
    print_summary(rows, args.rights_json, args.matrix_doc, wrote=not args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
