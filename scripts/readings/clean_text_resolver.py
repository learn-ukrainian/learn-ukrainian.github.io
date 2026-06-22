#!/usr/bin/env python3
"""Resolve clean-text hosting metadata for demanded primary readings.

Emitted links are UNVERIFIED candidates; a browser-verify step must confirm
each before it is rendered into a reading.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict
from urllib.parse import quote, quote_plus

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_mdx.reading_links import normalize_work_title
from scripts.readings.primary_text_demand import DEFAULT_PLANS_DIR, build_manifest
from scripts.readings.rights_classifier import (
    classify_rights,
    normalize_author,
    normalize_token,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_DB = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_OUT = PROJECT_ROOT / "data" / "primary_text_clean_resolution.json"

CorpusMatch = Literal["exact", "substring"]
LinkSource = Literal[
    "corpus_source_url",
    "ukrlib_candidate",
    "wikisource_candidate",
]
WorkKey = tuple[str, str]
ChunkID = int | str

AUTHOR_PREFIX_RE = re.compile(r"^\s*(?P<prefix>[^.]{2,120})\.\s+(?P<title>.+)$")


class CleanTextSource(TypedDict):
    """Serializable reference to hostable clean text."""

    source_file: str
    chunk_ids: list[ChunkID]
    full_text_chars: int


class FreeFullTextLink(TypedDict):
    """Serializable unverified free-full-text link candidate."""

    url: str
    source: LinkSource
    verified: bool


class CleanTextResolution(TypedDict):
    """Serializable clean-text resolution for one demanded primary text."""

    in_corpus: bool
    corpus_match: CorpusMatch | None
    hostable_full: bool
    rights_class: str
    rights_basis: str
    rights_confidence: float
    matched_work: str | None
    matched_author: str | None
    source_file: str | None
    year: int | None
    language_period: str | None
    source_url: str | None
    chunk_ids: list[ChunkID]
    full_text_chars: int
    clean_text_source: CleanTextSource | None
    free_full_text_link: FreeFullTextLink | None


@dataclass(frozen=True)
class WorkChunk:
    """One ordered literary_texts chunk."""

    chunk_id: ChunkID
    text: str


@dataclass(frozen=True)
class WorkGroup:
    """One assembled literary work from literary_texts chunks."""

    work_id: str | None
    work: str
    stored_work: str
    author: str
    year: int | None
    source_file: str
    language_period: str
    source_url: str | None
    chunks: tuple[WorkChunk, ...]
    normalized_work: str
    normalized_full_work: str
    normalized_author: str

    @property
    def chunk_ids(self) -> list[ChunkID]:
        """Return chunk IDs in assembly order."""

        return [chunk.chunk_id for chunk in self.chunks]

    @property
    def full_text_chars(self) -> int:
        """Return assembled character count without exposing the text body."""

        return sum(len(chunk.text) for chunk in self.chunks)


@dataclass(frozen=True)
class WorkIndex:
    """In-memory read-only index of literary_texts work groups."""

    by_key: dict[WorkKey, tuple[WorkGroup, ...]]
    by_work_id: dict[str, WorkGroup]
    groups: tuple[WorkGroup, ...]


def load_work_index(db_path: Path = DEFAULT_DB) -> WorkIndex:
    """Load literary_texts into a deterministic in-memory work index."""

    uri = f"{db_path.resolve().as_uri()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                  id,
                  chunk_id,
                  title,
                  text,
                  source_file,
                  author,
                  work,
                  work_id,
                  year,
                  genre,
                  language_period,
                  char_count,
                  source_url
                FROM literary_texts
                ORDER BY work_id, chunk_id, id
                """
            ).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Unable to load literary_texts from {db_path}") from exc

    buckets: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for row in rows:
        author = _row_text(row, "author")
        stored_work = _row_text(row, "work") or _row_text(row, "title")
        work = _strip_leading_author_prefix(stored_work, author)
        normalized_work = normalize_work_title(work)
        normalized_author = normalize_author(author)
        work_id = _row_text(row, "work_id")
        if work_id:
            bucket_key = ("work_id", work_id)
        else:
            bucket_key = (
                "key",
                f"{normalized_work}::{normalized_author}::{_row_text(row, 'source_file')}",
            )
        buckets.setdefault(bucket_key, []).append(row)

    groups = tuple(sorted((_build_group(bucket) for bucket in buckets.values()), key=_group_key))
    by_work_id = {
        group.work_id: group for group in groups if group.work_id is not None
    }
    by_key_lists: dict[WorkKey, list[WorkGroup]] = {}
    for group in groups:
        _append_keyed_group(by_key_lists, (group.normalized_work, group.normalized_author), group)
        if group.normalized_full_work != group.normalized_work:
            _append_keyed_group(
                by_key_lists,
                (group.normalized_full_work, group.normalized_author),
                group,
            )

    by_key = {
        key: tuple(sorted(value, key=_group_rank_key))
        for key, value in by_key_lists.items()
    }
    return WorkIndex(by_key=by_key, by_work_id=by_work_id, groups=groups)


def resolve_clean_text(
    work: str,
    author: str,
    index: WorkIndex,
    *,
    current_year: int | None = None,
) -> CleanTextResolution:
    """Resolve clean-text hosting metadata for one demanded work."""

    group, corpus_match = _find_corpus_match(work, author, index)
    if group is None:
        verdict = classify_rights(
            author,
            work,
            None,
            "",
            "",
            current_year=current_year,
        )
        return _resolution_payload(
            work=work,
            author=author,
            group=None,
            corpus_match=None,
            verdict=verdict,
        )

    verdict = classify_rights(
        group.author or author,
        group.work or work,
        group.year,
        group.source_file,
        group.language_period,
        current_year=current_year,
    )
    return _resolution_payload(
        work=work,
        author=author,
        group=group,
        corpus_match=corpus_match,
        verdict=verdict,
    )


def build_clean_text_manifest(
    db_path: Path = DEFAULT_DB,
    plans_dir: Path = DEFAULT_PLANS_DIR,
    *,
    track: str | None = None,
    current_year: int | None = None,
) -> dict[str, Any]:
    """Build a clean-text resolution manifest for demanded primary works."""

    index = load_work_index(db_path)
    demand_manifest = build_manifest(plans_dir, track=track)
    entries: list[dict[str, Any]] = []

    for entry in demand_manifest["entries"]:
        work = str(entry.get("work") or "")
        author = str(entry.get("author") or "")
        resolution = resolve_clean_text(
            work,
            author,
            index,
            current_year=current_year,
        )
        entries.append(
            {
                "work": work,
                "author": author,
                "normalized_key": entry.get("normalized_key")
                or _normalized_key(work, author),
                "resolution": resolution,
            }
        )

    summary = {
        "total_works": len(entries),
        "in_corpus_count": sum(
            1 for entry in entries if entry["resolution"]["in_corpus"]
        ),
        "hostable_full_count": sum(
            1 for entry in entries if entry["resolution"]["hostable_full"]
        ),
        "needs_link_count": sum(
            1
            for entry in entries
            if entry["resolution"]["free_full_text_link"] is not None
        ),
    }
    return {"summary": summary, "entries": entries}


def write_manifest(manifest: dict[str, Any], out_path: Path) -> None:
    """Write clean-text resolution manifest JSON."""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def format_summary(summary: dict[str, Any]) -> str:
    """Render compact clean-text resolution summary CLI output."""

    lines = [
        "Clean text resolution summary",
        f"total_works: {summary['total_works']}",
        f"in_corpus_count: {summary['in_corpus_count']}",
        f"hostable_full_count: {summary['hostable_full_count']}",
        f"needs_link_count: {summary['needs_link_count']}",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Build command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite sources DB")
    parser.add_argument("--work", help="Work title single clean-text lookup")
    parser.add_argument("--author", help="Author name single clean-text lookup")
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="Resolve primary-text demand manifest clean-text metadata",
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
    """Run clean-text resolver CLI."""

    logging.basicConfig(level=logging.WARNING, format="warning: %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.manifest:
        manifest = build_clean_text_manifest(
            args.db,
            args.plans_dir,
            track=args.track,
        )
        if args.summary:
            print(format_summary(manifest["summary"]))
            return 0
        write_manifest(manifest, args.out)
        return 0

    if not args.work or not args.author:
        parser.error("--work and --author are required unless --manifest is set")

    index = load_work_index(args.db)
    resolution = resolve_clean_text(args.work, args.author, index)
    print(json.dumps(resolution, ensure_ascii=False, indent=2))
    return 0


def _build_group(rows: list[sqlite3.Row]) -> WorkGroup:
    ordered_rows = sorted(rows, key=_row_sort_key)
    author = _first_text(ordered_rows, "author")
    stored_work = _first_text(ordered_rows, "work") or _first_text(ordered_rows, "title")
    work = _strip_leading_author_prefix(stored_work, author)
    chunks = tuple(
        WorkChunk(
            chunk_id=_chunk_id(row, fallback=index),
            text=_row_text(row, "text", strip=False),
        )
        for index, row in enumerate(ordered_rows, start=1)
    )
    return WorkGroup(
        work_id=_first_text(ordered_rows, "work_id") or None,
        work=work,
        stored_work=stored_work,
        author=author,
        year=_first_int(ordered_rows, "year"),
        source_file=_first_text(ordered_rows, "source_file"),
        language_period=_first_text(ordered_rows, "language_period"),
        source_url=_first_text(ordered_rows, "source_url") or None,
        chunks=chunks,
        normalized_work=normalize_work_title(work),
        normalized_full_work=normalize_work_title(stored_work),
        normalized_author=normalize_author(author),
    )


def _find_corpus_match(
    work: str,
    author: str,
    index: WorkIndex,
) -> tuple[WorkGroup | None, CorpusMatch | None]:
    normalized_work = normalize_work_title(work)
    normalized_author = normalize_author(author)
    if not normalized_work:
        return None, None

    exact_groups = index.by_key.get((normalized_work, normalized_author))
    if exact_groups:
        return exact_groups[0], "exact"

    substring_groups = [
        group
        for group in index.groups
        if group.normalized_author == normalized_author
        and (
            _contains_normalized(group.normalized_work, normalized_work)
            or _contains_normalized(group.normalized_full_work, normalized_work)
        )
    ]
    if substring_groups:
        return sorted(substring_groups, key=_group_rank_key)[0], "substring"
    return None, None


def _resolution_payload(
    *,
    work: str,
    author: str,
    group: WorkGroup | None,
    corpus_match: CorpusMatch | None,
    verdict: dict[str, Any],
) -> CleanTextResolution:
    in_corpus = group is not None
    rights_class = str(verdict["rights_class"])
    hostable_full = in_corpus and rights_class == "public_domain"
    chunk_ids = group.chunk_ids if group else []
    full_text_chars = group.full_text_chars if group else 0

    clean_text_source: CleanTextSource | None = None
    if hostable_full and group is not None:
        clean_text_source = {
            "source_file": group.source_file,
            "chunk_ids": chunk_ids,
            "full_text_chars": full_text_chars,
        }

    free_full_text_link = None
    if not hostable_full:
        free_full_text_link = _free_full_text_link(
            group.work if group else work,
            group.author if group else author,
            group.source_url if group else None,
        )

    return {
        "in_corpus": in_corpus,
        "corpus_match": corpus_match,
        "hostable_full": hostable_full,
        "rights_class": rights_class,
        "rights_basis": str(verdict["basis"]),
        "rights_confidence": float(verdict["confidence"]),
        "matched_work": group.work if group else None,
        "matched_author": group.author if group else None,
        "source_file": group.source_file if group else None,
        "year": group.year if group else None,
        "language_period": group.language_period if group else None,
        "source_url": group.source_url if group else None,
        "chunk_ids": chunk_ids,
        "full_text_chars": full_text_chars,
        "clean_text_source": clean_text_source,
        "free_full_text_link": free_full_text_link,
    }


def _free_full_text_link(
    work: str,
    author: str,
    source_url: str | None,
) -> FreeFullTextLink:
    if source_url:
        return {
            "url": source_url,
            "source": "corpus_source_url",
            "verified": False,
        }

    title = _clean_query_text(work)
    author_name = _clean_query_text(author)
    if author_name:
        query = quote_plus(" ".join(part for part in (author_name, title) if part))
        return {
            "url": f"https://www.ukrlib.com.ua/books/?q={query}",
            "source": "ukrlib_candidate",
            "verified": False,
        }

    wiki_title = quote(title.replace(" ", "_") or "Special:Search", safe="/:_")
    return {
        "url": f"https://uk.wikisource.org/wiki/{wiki_title}",
        "source": "wikisource_candidate",
        "verified": False,
    }


def _strip_leading_author_prefix(work: str, author: str) -> str:
    clean_work = work.strip()
    match = AUTHOR_PREFIX_RE.match(clean_work)
    if match is None:
        return clean_work

    prefix = match.group("prefix")
    title = match.group("title").strip()
    if title and _looks_like_author_prefix(prefix, author):
        return title
    return clean_work


def _looks_like_author_prefix(prefix: str, author: str) -> bool:
    normalized_prefix = normalize_token(prefix)
    normalized_author = normalize_author(author)
    if not normalized_prefix or not normalized_author:
        return False
    if normalized_prefix in normalized_author or normalized_author in normalized_prefix:
        return True
    prefix_tokens = _significant_tokens(normalized_prefix)
    author_tokens = _significant_tokens(normalized_author)
    return bool(prefix_tokens & author_tokens)


def _significant_tokens(value: str) -> set[str]:
    return {token for token in value.split() if len(token) > 2}


def _contains_normalized(haystack: str, needle: str) -> bool:
    return bool(needle and haystack and f" {needle} " in f" {haystack} ")


def _append_keyed_group(
    by_key_lists: dict[WorkKey, list[WorkGroup]],
    key: WorkKey,
    group: WorkGroup,
) -> None:
    if not key[0]:
        return
    groups = by_key_lists.setdefault(key, [])
    if group not in groups:
        groups.append(group)


def _group_key(group: WorkGroup) -> tuple[str, str, str]:
    return (group.normalized_author, group.normalized_work, group.work_id or "")


def _group_rank_key(group: WorkGroup) -> tuple[int, str, str, str]:
    return (-group.full_text_chars, group.source_file, group.work_id or "", group.work)


def _row_sort_key(
    row: sqlite3.Row,
) -> tuple[tuple[int, int | str], tuple[int, int | str]]:
    return (_sort_mixed(row["chunk_id"]), _sort_mixed(row["id"]))


def _chunk_id(row: sqlite3.Row, *, fallback: int) -> ChunkID:
    chunk_id = _optional_int(row["chunk_id"])
    if chunk_id is not None:
        return chunk_id
    chunk_text = _row_text(row, "chunk_id")
    if chunk_text:
        return chunk_text
    row_id = _optional_int(row["id"])
    return row_id if row_id is not None else fallback


def _first_text(rows: Iterable[sqlite3.Row], column: str) -> str:
    for row in rows:
        value = _row_text(row, column)
        if value:
            return value
    return ""


def _first_int(rows: Iterable[sqlite3.Row], column: str) -> int | None:
    for row in rows:
        value = _optional_int(row[column])
        if value is not None:
            return value
    return None


def _row_text(row: sqlite3.Row, column: str, *, strip: bool = True) -> str:
    value = row[column]
    if value is None:
        return ""
    text = str(value)
    return text.strip() if strip else text


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _sort_mixed(value: object) -> tuple[int, int | str]:
    int_value = _optional_int(value)
    if int_value is not None:
        return (0, int_value)
    text = str(value).strip() if value is not None else ""
    if text:
        return (1, text)
    return (2, "")


def _clean_query_text(value: str) -> str:
    return " ".join(str(value or "").split())


def _normalized_key(work: str, author: str) -> str:
    return f"{normalize_work_title(work)}::{normalize_author(author)}"


if __name__ == "__main__":
    raise SystemExit(main())
