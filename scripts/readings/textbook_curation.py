#!/usr/bin/env python3
"""Lookup demanded primary texts in Ukrainian textbook section metadata."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_mdx.reading_links import normalize_work_title
from scripts.readings.primary_text_demand import DEFAULT_PLANS_DIR, build_manifest
from scripts.readings.rights_classifier import normalize_author, normalize_token

LOGGER = logging.getLogger(__name__)

DEFAULT_DB = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_OUT = PROJECT_ROOT / "data" / "primary_text_curation.json"
MAX_RETURNED_HITS = 10

PAGE_DECORATION_RE = re.compile(r"\s*[\ue000-\uf8ff⦿●•]\s*\d+\s*$")
PUA_RE = re.compile(r"[\ue000-\uf8ff]")
GUILLEMET_RE = re.compile(r"«(?P<title>[^»]+)»")
WHITESPACE_RE = re.compile(r"\s+")

WorkMatch = Literal["exact", "substring"]


@dataclass(frozen=True)
class Section:
    """One row from textbook_sections."""

    section_id: int
    source_file: str
    grade: int | None
    section_title: str
    section_number: str
    page_start: int | None
    page_end: int | None
    chunk_count: int | None
    full_text: str


class CurationHit(TypedDict):
    """Serializable textbook section hit for one demanded work."""

    source_file: str
    grade: int | None
    section_title: str
    page_start: int | None
    page_end: int | None
    full_text_chars: int
    work_match: WorkMatch
    author_match: bool


class ExcerptBoundary(TypedDict):
    """Boundary metadata for the best textbook excerpt."""

    page_start: int | None
    page_end: int | None
    full_text_chars: int
    source_file: str
    section_title: str


class CurationResult(TypedDict):
    """Serializable curation verdict for one demanded work."""

    in_school_canon: bool
    confidence: float
    grades: list[int]
    hit_count: int
    best_hit: CurationHit | None
    excerpt_boundary: ExcerptBoundary | None
    hits: list[CurationHit]


@dataclass(frozen=True)
class _PreparedSection:
    section: Section
    normalized_title: str
    guillemet_tokens: frozenset[str]


def load_sections(db_path: Path) -> list[Section]:
    """Load textbook_sections rows from a read-only SQLite connection."""

    uri = f"{db_path.resolve().as_uri()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    section_id,
                    source_file,
                    grade,
                    section_title,
                    section_number,
                    page_start,
                    page_end,
                    chunk_count,
                    full_text
                FROM textbook_sections
                ORDER BY section_id
                """
            ).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Unable to load textbook sections from {db_path}") from exc

    return [
        Section(
            section_id=_optional_int(row["section_id"]) or 0,
            source_file=str(row["source_file"] or ""),
            grade=_optional_int(row["grade"]),
            section_title=str(row["section_title"] or ""),
            section_number=str(row["section_number"] or ""),
            page_start=_optional_int(row["page_start"]),
            page_end=_optional_int(row["page_end"]),
            chunk_count=_optional_int(row["chunk_count"]),
            full_text=str(row["full_text"] or ""),
        )
        for row in rows
    ]


def lookup_curation(
    work: str,
    author: str,
    sections: Sequence[Section],
    *,
    current_year: int | None = None,
) -> CurationResult:
    """Return textbook curation metadata for a demanded work/author pair."""

    return _lookup_prepared(
        work,
        author,
        _prepare_sections(sections),
        current_year=current_year,
    )


def _lookup_prepared(
    work: str,
    author: str,
    prepared_sections: Sequence[_PreparedSection],
    *,
    current_year: int | None = None,
) -> CurationResult:
    normalized_work = normalize_work_title(work)
    normalized_author = normalize_author(author)
    ranked_hits: list[tuple[float, CurationHit]] = []

    for prepared in prepared_sections:
        section = prepared.section
        work_match = _work_match(
            normalized_work,
            prepared.normalized_title,
            prepared.guillemet_tokens,
        )
        if work_match is None:
            continue

        author_match = bool(
            normalized_author and normalized_author in prepared.normalized_title
        )
        confidence = _hit_confidence(work_match, author_match)
        hit: CurationHit = {
            "source_file": section.source_file,
            "grade": section.grade,
            "section_title": section.section_title,
            "page_start": section.page_start,
            "page_end": section.page_end,
            "full_text_chars": len(section.full_text),
            "work_match": work_match,
            "author_match": author_match,
        }
        ranked_hits.append((confidence, hit))

    ranked_hits.sort(
        key=lambda item: (
            -item[0],
            _sort_int(item[1]["grade"]),
            _sort_int(item[1]["page_start"]),
        )
    )
    hits = [hit for _, hit in ranked_hits]
    canon_hits = [(confidence, hit) for confidence, hit in ranked_hits if confidence >= 0.7]
    best_hit = hits[0] if hits else None

    return {
        "in_school_canon": bool(canon_hits),
        "confidence": ranked_hits[0][0] if ranked_hits else 0.0,
        "grades": sorted(
            {
                hit["grade"]
                for _, hit in canon_hits
                if hit["grade"] is not None
            }
        ),
        "hit_count": len(hits),
        "best_hit": best_hit,
        "excerpt_boundary": _excerpt_boundary(best_hit),
        "hits": hits[:MAX_RETURNED_HITS],
    }


def build_curation_manifest(
    db_path: Path = DEFAULT_DB,
    plans_dir: Path = DEFAULT_PLANS_DIR,
    *,
    track: str | None = None,
) -> dict[str, Any]:
    """Build an enriched primary-text manifest with textbook curation results."""

    sections = load_sections(db_path)
    prepared_sections = _prepare_sections(sections)
    demand_manifest = build_manifest(plans_dir, track=track)
    entries: list[dict[str, Any]] = []

    for entry in demand_manifest["entries"]:
        work = str(entry.get("work") or "")
        author = str(entry.get("author") or "")
        curation = _lookup_prepared(work, author, prepared_sections)
        entries.append(
            {
                "work": work,
                "author": author,
                "normalized_key": entry.get("normalized_key")
                or _normalized_key(work, author),
                "curation": curation,
            }
        )

    summary = {
        "total_works": len(entries),
        "in_canon_count": sum(
            1 for entry in entries if entry["curation"]["in_school_canon"]
        ),
        "high_confidence_count": sum(
            1 for entry in entries if entry["curation"]["confidence"] >= 1.0
        ),
        "no_hit_count": sum(1 for entry in entries if entry["curation"]["hit_count"] == 0),
    }
    return {"summary": summary, "entries": entries}


def write_manifest(manifest: dict[str, Any], out_path: Path) -> None:
    """Write curation manifest JSON."""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def format_summary(summary: dict[str, Any]) -> str:
    """Render a compact manifest curation summary for CLI output."""

    lines = [
        "Textbook curation summary",
        f"total_works: {summary['total_works']}",
        f"in_canon_count: {summary['in_canon_count']}",
        f"high_confidence_count: {summary['high_confidence_count']}",
        f"no_hit_count: {summary['no_hit_count']}",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite sources DB")
    parser.add_argument("--work", help="Work title for a single curation lookup")
    parser.add_argument("--author", help="Author name for a single curation lookup")
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="Enrich the primary-text demand manifest with curation results",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Manifest JSON output")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print manifest summary stdout and skip writing manifest file",
    )
    parser.add_argument("--track", help="Only scan plans whose parent directory matches track")
    parser.add_argument("--plans-dir", type=Path, default=DEFAULT_PLANS_DIR, help="Plan YAML root")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run curation lookup CLI."""

    logging.basicConfig(level=logging.WARNING, format="warning: %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.manifest:
        manifest = build_curation_manifest(args.db, args.plans_dir, track=args.track)
        if args.summary:
            print(format_summary(manifest["summary"]))
            return 0
        write_manifest(manifest, args.out)
        return 0

    if not args.work or not args.author:
        parser.error("--work and --author are required unless --manifest is set")

    sections = load_sections(args.db)
    result = lookup_curation(args.work, args.author, sections)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _work_match(
    normalized_work: str,
    normalized_title: str,
    guillemet_tokens: frozenset[str],
) -> WorkMatch | None:
    if not normalized_work:
        return None

    if normalized_work in guillemet_tokens or normalized_work == normalized_title:
        return "exact"
    if _contains_whitespace_bounded(normalized_title, normalized_work):
        return "substring"
    return None


def _hit_confidence(work_match: WorkMatch, author_match: bool) -> float:
    if work_match == "exact" and author_match:
        return 1.0
    if (work_match == "exact") != author_match:
        return 0.7
    return 0.4


def _excerpt_boundary(hit: CurationHit | None) -> ExcerptBoundary | None:
    if hit is None:
        return None
    if (
        hit["page_start"] is None
        and hit["page_end"] is None
        and hit["full_text_chars"] <= 0
    ):
        return None
    return {
        "page_start": hit["page_start"],
        "page_end": hit["page_end"],
        "full_text_chars": hit["full_text_chars"],
        "source_file": hit["source_file"],
        "section_title": hit["section_title"],
    }


def _clean_section_title(title: str) -> str:
    text = PAGE_DECORATION_RE.sub("", str(title or ""))
    text = PUA_RE.sub(" ", text)
    return WHITESPACE_RE.sub(" ", text).strip()


def _contains_whitespace_bounded(haystack: str, needle: str) -> bool:
    return f" {needle} " in f" {haystack} "


def _prepare_sections(sections: Sequence[Section]) -> list[_PreparedSection]:
    return [_prepare_section(section) for section in sections]


def _prepare_section(section: Section) -> _PreparedSection:
    clean_title = _clean_section_title(section.section_title)
    return _PreparedSection(
        section=section,
        normalized_title=normalize_token(clean_title),
        guillemet_tokens=frozenset(
            normalize_work_title(match.group("title"))
            for match in GUILLEMET_RE.finditer(clean_title)
        ),
    )


def _normalized_key(work: str, author: str) -> str:
    return f"{normalize_work_title(work)}::{normalize_author(author)}"


def _sort_int(value: int | None) -> int:
    return value if value is not None else 1_000_000


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


if __name__ == "__main__":
    raise SystemExit(main())
