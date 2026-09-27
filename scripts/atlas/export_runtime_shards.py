"""Export versioned Atlas runtime shards (immutable data contract, PR #1).

Deterministic, read-only over ``atlas.db``. Does not deploy, does not change the
live ``/lexicon/<slug>`` route, and never commits the generated tree.

Memory is bounded by one shard, not the corpus: records are replayed from the
read-only database by indexed lookups, shard candidates are gzip-streamed with an
early abort past their size cap, accepted leaves are written straight into a
staging tree, uncapped objects (terminal search shards) are gzip-streamed to
their file at every compression level (level 0's stored-block framing is
planned from the length, then streamed from a replay), oversized buckets' error
sizes are counted, never held, and ``current.json`` is switched (last,
atomically) only after the whole tree (and, with ``--verify``, its streamed
verification) is installed. Search rows are kept as locators and replayed from
the read snapshot, never retained.
Installed version trees are immutable: a same-dataVersion tree with different
bytes is installed beside the first as ``<dataVersion>-transport-<sha256>``.
"""

from __future__ import annotations

import argparse
import codecs
import decimal
import functools
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import struct
import sys
import unicodedata
import uuid
import zlib
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, BinaryIO

import ijson

# Allow ``python scripts/atlas/export_runtime_shards.py`` (not only ``-m``).
if __package__ is None or __package__ == "":
    _REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

from scripts.atlas.normalization import normalize_atlas_text, normalize_slug_for_hash
from scripts.etymology.transliterate import transliterate

SCHEMA_VERSION = 1
ENTRY_SHARD_SCHEMA = "atlas-entry-shard"
MANIFEST_SCHEMA = "atlas-runtime-manifest"
CURRENT_SCHEMA = "atlas-current"
SEARCH_ARTICLE_SCHEMA = "atlas-search-article-shard"
SEARCH_ALIAS_SCHEMA = "atlas-search-alias-shard"

DEFAULT_ENTRY_MAX = 1_048_576
DEFAULT_ENTRY_TARGET_MIN = 524_288
DEFAULT_SEARCH_MAX = 524_288
DEFAULT_COMPRESSION = 9

PRACTICE_LEVELS = ("A1", "A2", "B1", "B2", "C1")
DECK_PARTS = ("index", "lexemes", "cloze")
# Search gloss tokens — twin of site/src/lib/lexicon/search.ts TOKEN_RE (/[\p{L}\p{N}_]+/gu).
TOKEN_RE = re.compile(r"[\w\u0400-\u04ff]+", re.UNICODE)

ARTICLE_ENTRY_TYPES = {
    "lemma",
    "expression",
    "phraseologism",
    "proverb",
    "multiword_term",
    "proper_name",
}
MORPHOLOGY_SUPPRESSED_TYPES = {
    "multiword_term",
    "expression",
    "phraseologism",
    "proverb",
}
# Component chips — Letter/Mark only (+ apostrophe joins). Twin of
# sqlite-atlas-data-source.ts COMPONENT_TOKEN_RE: /[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*/gu
# (std ``re`` has no \p{}; vectors in component_tokenization_vectors.json).
_COMPONENT_APOSTROPHES = frozenset("'’")
COMPONENT_TOKENIZATION_VECTORS_PATH = Path(__file__).with_name("component_tokenization_vectors.json")


class ExportError(RuntimeError):
    """Hard export failure (oversized record, CEFR conflict, integrity)."""


def _is_unicode_letter_or_mark(char: str) -> bool:
    """True for Unicode Letter (L*) or Mark (M*) — mirrors ``\\p{L}\\p{M}``."""
    return unicodedata.category(char)[0] in ("L", "M")


def find_component_tokens(text: str) -> list[str]:
    r"""Tokenize like TS ``/[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*/gu`` (no digit/underscore)."""
    tokens: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        if not _is_unicode_letter_or_mark(text[index]):
            index += 1
            continue
        start = index
        index += 1
        while index < length and _is_unicode_letter_or_mark(text[index]):
            index += 1
        while index < length and text[index] in _COMPONENT_APOSTROPHES:
            after = index + 1
            if after >= length or not _is_unicode_letter_or_mark(text[after]):
                break
            index = after + 1
            while index < length and _is_unicode_letter_or_mark(text[index]):
                index += 1
        tokens.append(text[start:index])
    return tokens


def load_component_tokenization_vectors() -> list[dict[str, object]]:
    payload = json.loads(COMPONENT_TOKENIZATION_VECTORS_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "atlas-component-tokenization-vectors":
        raise ValueError(f"invalid component tokenization vectors at {COMPONENT_TOKENIZATION_VECTORS_PATH}")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"component tokenization vectors missing cases: {COMPONENT_TOKENIZATION_VECTORS_PATH}")
    return cases


def canonical_json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=False) + "\n").encode(
        "utf-8"
    )


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def gzip_bytes(data: bytes, *, compression_level: int) -> bytes:
    return gzip.compress(data, compresslevel=compression_level, mtime=0)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def open_readonly_db(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


def entry_shard_id(bit_length: int, prefix_value: int) -> str:
    hex_width = max(1, (bit_length + 3) // 4)
    return f"p{bit_length:02d}-{prefix_value:0{hex_width}x}"


def search_shard_id(prefix: str) -> str:
    if not prefix:
        return "root"
    parts: list[str] = []
    for char in prefix:
        if "a" <= char <= "z":
            parts.append(f"latin-{char}")
        elif "0" <= char <= "9":
            parts.append(f"digit-{char}")
        else:
            parts.append(f"u{ord(char):04x}")
    return "-".join(parts) if len(parts) == 1 else f"p{len(prefix):02d}-{''.join(f'{ord(c):04x}' for c in prefix)}"


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _cefr_from_enrichment(entry: Mapping[str, Any]) -> str | None:
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, Mapping):
        return None
    cefr = enrichment.get("cefr")
    if isinstance(cefr, Mapping):
        level = _clean_text(cefr.get("level"))
        return level.upper() if level else None
    return None


def _assert_cefr_consistent(slug: str, article_cefr: str | None, entry: Mapping[str, Any]) -> None:
    payload_cefr = _cefr_from_enrichment(entry)
    left = _clean_text(article_cefr)
    right = _clean_text(payload_cefr)
    if left and right and left.upper() != right.upper():
        raise ExportError(
            f"CEFR conflict for slug={slug!r}: articles.cefr={left!r} enrichment.cefr={right!r}"
        )


def _site_build_entry_model_gates(conn: sqlite3.Connection) -> dict[str, int]:
    reviewed_entries = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE review_state = 'approved' AND visibility = 'public'"
    ).fetchone()[0]
    public_routes = conn.execute(
        "SELECT COUNT(*) FROM article_payloads WHERE is_public_route = 1"
    ).fetchone()[0]
    form_of_routes = conn.execute(
        """SELECT COUNT(*)
           FROM article_payloads AS payload
           LEFT JOIN articles AS article ON article.slug = payload.slug
           WHERE payload.is_public_route = 1 AND article.slug IS NULL"""
    ).fetchone()[0]
    routed_reviewed = conn.execute(
        """SELECT COUNT(*)
           FROM article_payloads AS payload
           JOIN articles AS article ON article.slug = payload.slug
           WHERE payload.is_public_route = 1
             AND article.review_state = 'approved'
             AND article.visibility = 'public'"""
    ).fetchone()[0]
    if reviewed_entries != public_routes - form_of_routes or reviewed_entries != routed_reviewed:
        raise ExportError(
            "article_vs_alias_count failure: "
            f"reviewed={reviewed_entries} public_routes={public_routes} "
            f"form_of={form_of_routes} routed={routed_reviewed}"
        )
    invalid_aliases = conn.execute(
        """SELECT COUNT(*)
           FROM aliases AS alias
           LEFT JOIN articles AS article ON article.slug = alias.target_slug
           WHERE alias.visibility = 'public'
             AND (
                 article.slug IS NULL
                 OR article.review_state != 'approved'
                 OR article.visibility != 'public'
             )"""
    ).fetchone()[0]
    if invalid_aliases:
        raise ExportError(f"alias_target_integrity failure: {invalid_aliases} invalid public aliases")
    public_aliases = conn.execute(
        "SELECT COUNT(*) FROM aliases WHERE visibility = 'public'"
    ).fetchone()[0]
    return {
        "articles": int(reviewed_entries),
        "formRoutes": int(form_of_routes),
        "publicRoutes": int(public_routes),
        "aliases": int(public_aliases),
    }


def _unique_component_targets(
    rows: Iterable[tuple[str, str]],
) -> dict[str, str | None]:
    """Normalized lookup → its single target slug, or ``None`` once ambiguous."""
    targets: dict[str, str | None] = {}
    for lookup_text, target_slug in rows:
        key = normalize_atlas_text(lookup_text)
        if not key:
            continue
        if key not in targets:
            targets[key] = target_slug
        elif targets[key] != target_slug:
            targets[key] = None
    return targets


def build_component_link_targets(
    article_rows: Iterable[tuple[str, str]],
    alias_rows: Iterable[tuple[str, str]],
) -> dict[str, str]:
    article_targets = _unique_component_targets(article_rows)
    alias_targets = _unique_component_targets(alias_rows)
    out: dict[str, str] = {}
    for lookup, matched in article_targets.items():
        if matched is not None:
            out[lookup] = matched
    for lookup, matched in alias_targets.items():
        if lookup in article_targets or matched is None:
            continue
        out[lookup] = matched
    return out


def component_links_for_entry(
    entry: Mapping[str, Any],
    *,
    component_targets: Mapping[str, str],
    lemma_slugs: set[str],
) -> list[dict[str, str | None]]:
    entry_type = entry.get("entry_type")
    if entry_type not in MORPHOLOGY_SUPPRESSED_TYPES:
        return []
    lemma = entry.get("lemma")
    if not isinstance(lemma, str):
        return []
    current_slug = str(entry.get("url_slug") or "")
    links: list[dict[str, str | None]] = []
    for text in find_component_tokens(lemma):
        target_slug = component_targets.get(normalize_atlas_text(text))
        if (
            target_slug
            and target_slug in lemma_slugs
            and target_slug != current_slug
        ):
            links.append({"text": text, "targetSlug": target_slug})
        else:
            links.append({"text": text, "targetSlug": None})
    return links


def practice_index_dir_candidates(deck_dir: Path) -> list[Path]:
    """Prefer ``public/api/lexicon`` before ``public/lexicon`` (SqliteAtlasDataSource)."""
    resolved = deck_dir.resolve()
    public_root: Path | None = None
    if resolved.name == "lexicon" and resolved.parent.name == "api":
        public_root = resolved.parent.parent
    elif resolved.name == "lexicon":
        public_root = resolved.parent
    if public_root is not None:
        return [public_root / "api" / "lexicon", public_root / "lexicon"]
    return [resolved]


def load_practice_levels_by_slug(deck_dir: Path | None) -> dict[str, list[str]]:
    """Index practice levels by ``lemmaId`` only; prefer api/lexicon over lexicon/.

    Mirrors ``SqliteAtlasDataSource.loadPracticeLevelsBySlug`` / legacy
    ``getPracticeLemmas``: first existing practice-index per level wins, and
    only ``lemmaId`` is indexed (lookup still falls back to ``entry.lemma``).
    """
    levels_by_slug: dict[str, set[str]] = defaultdict(set)
    if deck_dir is None:
        return {}
    candidates = practice_index_dir_candidates(deck_dir)
    for level in PRACTICE_LEVELS:
        for candidate_dir in candidates:
            path = candidate_dir / f"practice-index.{level}.json"
            if not path.is_file():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            items = payload.get("items") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                break
            for item in items:
                if not isinstance(item, dict):
                    continue
                # Legacy indexes only lemmaId; indexing lemma would widen visibility.
                lemma_id = item.get("lemmaId")
                if isinstance(lemma_id, str) and lemma_id:
                    levels_by_slug[lemma_id].add(level)
            break
    return {slug: sorted(levels) for slug, levels in levels_by_slug.items()}


def _sorted_alias_rows(rows: Iterable[sqlite3.Row]) -> list[dict[str, str | None]]:
    aliases = [
        {
            "alias": row["alias"],
            "kind": row["kind"],
            "source": row["source"],
            "target_slug": row["target_slug"],
        }
        for row in rows
    ]
    aliases.sort(key=lambda item: (item["kind"] or "", item["alias"] or "", item["source"] or ""))
    return aliases


def _sorted_relation_rows(rows: Iterable[sqlite3.Row]) -> list[dict[str, str | None]]:
    relations = [
        {
            "related_slug": row["related_slug"],
            "entry_type": row["entry_type"],
            "relation": row["relation"],
            "component_role": row["component_role"],
            "provenance": row["provenance"],
        }
        for row in rows
    ]
    relations.sort(
        key=lambda item: (
            item["relation"] or "",
            item["related_slug"] or "",
            item["provenance"] or "",
            item["component_role"] or "",
        )
    )
    return relations


def _sorted_provenance_rows(rows: Iterable[sqlite3.Row]) -> list[dict[str, str | None]]:
    provenance = [
        {
            "source_family": row["source_family"],
            "source_locator": row["source_locator"],
            "extraction_mode": row["extraction_mode"],
        }
        for row in rows
    ]
    # Stable order matches DB rowid insertion order already selected.
    return provenance


# ---------------------------------------------------------------------------
# Bounded-memory runtime export (#8672)
#
# The exporter never holds the corpus: records are replayed one at a time from
# the read-only SQLite source by indexed slug lookups, only compact partition
# metadata (slug + slug-hash digest, search rank + postings) stays resident, and
# every candidate shard is serialised and gzip-streamed with an early abort as
# soon as the compressed size passes its cap. Accepted leaves are written to a
# staging tree immediately; only their descriptors are kept.
# ---------------------------------------------------------------------------

_PAYLOAD_SELECT = """SELECT ap.slug AS slug,
                            ap.payload_json AS payload_json,
                            a.entry_type AS entry_type,
                            a.cefr AS cefr
                     FROM article_payloads ap
                     LEFT JOIN articles a ON a.slug = ap.slug
                     WHERE ap.is_public_route = 1"""


def _dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def _fragment_bytes(payload: Any) -> bytes:
    return _dumps(payload).encode("utf-8")


class EntryReplay:
    """Rebuild public-route entry records one at a time from the read-only source.

    Same record shape, ordering and validation as the historical whole-corpus
    loader; only the per-slug side tables are queried through their indexes
    (``idx_aliases_target`` / ``idx_related_entries_slug_relation`` /
    ``idx_prov_slug``) instead of being materialised for the whole corpus.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        *,
        practice_levels_by_slug: Mapping[str, Sequence[str]],
    ) -> None:
        self._conn = conn
        self._practice_levels_by_slug = practice_levels_by_slug
        self._component_targets = build_component_link_targets(
            conn.execute(
                """SELECT display_head, slug
                   FROM articles
                   WHERE review_state = 'approved' AND visibility = 'public' AND entry_type = 'lemma'"""
            ),
            conn.execute(
                """SELECT al.alias, al.target_slug
                   FROM aliases al
                   JOIN articles a ON a.slug = al.target_slug
                   WHERE al.visibility = 'public'
                     AND a.review_state = 'approved'
                     AND a.visibility = 'public'
                     AND a.entry_type = 'lemma'"""
            ),
        )
        self._lemma_slugs = {
            row[0]
            for row in conn.execute(
                """SELECT slug FROM articles
                   WHERE review_state = 'approved' AND visibility = 'public' AND entry_type = 'lemma'"""
            )
        }

    def iter_records(self) -> Iterator[dict[str, Any]]:
        """Yield every public-route record in ``(route_order, slug)`` order."""
        cursor = self._conn.execute(f"{_PAYLOAD_SELECT} ORDER BY ap.route_order, ap.slug")
        for row in cursor:
            yield self._record(row)

    def record_for_slug(self, slug: str) -> dict[str, Any]:
        row = self._conn.execute(f"{_PAYLOAD_SELECT} AND ap.slug = ?", (slug,)).fetchone()
        if row is None:
            raise ExportError(f"public route {slug!r} vanished from the source database during export")
        return self._record(row)

    def _record(self, row: sqlite3.Row) -> dict[str, Any]:
        entry = json.loads(row["payload_json"])
        if not isinstance(entry, dict):
            raise ExportError(f"payload_json for {row['slug']!r} is not an object")
        # Authoritative entry_type from articles (SSOT). form_of routes → null.
        entry["entry_type"] = row["entry_type"]
        _assert_cefr_consistent(row["slug"], row["cefr"], entry)

        kind = "article" if row["entry_type"] is not None else "form_route"
        slug = str(row["slug"])
        practice_levels = list(
            self._practice_levels_by_slug.get(slug)
            or self._practice_levels_by_slug.get(str(entry.get("lemma") or ""))
            or []
        )
        conn = self._conn
        aliases = conn.execute(
            """SELECT alias, kind, source, target_slug
               FROM aliases
               WHERE visibility = 'public' AND target_slug = ?
               ORDER BY kind, alias, source""",
            (slug,),
        ).fetchall()
        relations = conn.execute(
            """SELECT related_slug, entry_type, relation, component_role, provenance
               FROM related_entries
               WHERE slug = ?
               ORDER BY relation, related_slug, provenance, component_role""",
            (slug,),
        ).fetchall()
        provenance = conn.execute(
            """SELECT source_family, source_locator, extraction_mode
               FROM article_provenance
               WHERE slug = ?
               ORDER BY rowid""",
            (slug,),
        ).fetchall()
        return {
            "slug": slug,
            "kind": kind,
            "entry": entry,
            "aliases": _sorted_alias_rows(aliases),
            "relations": _sorted_relation_rows(relations),
            "provenance": _sorted_provenance_rows(provenance),
            "renderContext": {
                "componentLinks": component_links_for_entry(
                    entry,
                    component_targets=self._component_targets,
                    lemma_slugs=self._lemma_slugs,
                ),
                "practiceLevels": practice_levels,
            },
        }


def load_entry_records(
    conn: sqlite3.Connection,
    *,
    practice_levels_by_slug: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    """Whole-corpus compatibility wrapper over :class:`EntryReplay` (tests / fixtures)."""
    replay = EntryReplay(conn, practice_levels_by_slug=practice_levels_by_slug)
    return list(replay.iter_records())


def _article_search_row(
    slug: str, display_head: str, gloss: object, entry_type: str, cefr: object
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "l": display_head,
        "s": slug,
        "g": _clean_text(gloss),
        "r": transliterate(display_head),
        "t": entry_type,
    }
    level = _clean_text(cefr)
    if level:
        row["c"] = level
    return row


def _iter_article_search_rows(conn: sqlite3.Connection) -> Iterator[dict[str, Any]]:
    # Row order is irrelevant: slug is the primary key, so the (normalized head,
    # slug) sort applied afterwards is total.
    for slug, display_head, gloss, entry_type, cefr in conn.execute(
        """SELECT slug, display_head, gloss, entry_type, cefr
           FROM articles
           WHERE review_state = 'approved' AND visibility = 'public'"""
    ):
        yield _article_search_row(slug, display_head, gloss, entry_type, cefr)


def _replay_article_search_row(conn: sqlite3.Connection, slug: str) -> dict[str, Any]:
    """Re-read one article search row by primary key (same snapshot as the scan)."""
    found = conn.execute(
        "SELECT slug, display_head, gloss, entry_type, cefr FROM articles WHERE slug = ?", (slug,)
    ).fetchone()
    if found is None:
        raise ExportError(f"search article row vanished during export: {slug!r}")
    return _article_search_row(*found)


def _iter_located_alias_search_rows(conn: sqlite3.Connection) -> Iterator[tuple[int, dict[str, Any]]]:
    """Public aliases as ``(rowid, row)``; first row per ``(normalized alias, target)`` wins.

    The ORDER BY is load-bearing: which raw alias/kind survives the dedup depends
    on it, so it is kept verbatim and only *streamed* rather than fetched.
    """
    seen: set[tuple[str, str]] = set()
    for rowid, alias, kind, target_slug, target_head in conn.execute(
        """SELECT alias.rowid, alias.alias, alias.kind, alias.target_slug, article.display_head
           FROM aliases AS alias
           JOIN articles AS article ON article.slug = alias.target_slug
           WHERE alias.visibility = 'public'
             AND article.review_state = 'approved'
             AND article.visibility = 'public'
           ORDER BY alias.alias COLLATE NOCASE, alias.target_slug, alias.kind"""
    ):
        key = (normalize_atlas_text(alias), target_slug)
        if not key[0] or key in seen:
            continue
        seen.add(key)
        yield rowid, {"a": alias, "k": kind, "s": target_slug, "h": target_head}


def _iter_alias_search_rows(conn: sqlite3.Connection) -> Iterator[dict[str, Any]]:
    for _rowid, row in _iter_located_alias_search_rows(conn):
        yield row


def _replay_alias_search_row(conn: sqlite3.Connection, rowid: int) -> dict[str, Any]:
    """Re-read the winning alias row by rowid (same snapshot as the dedup scan)."""
    found = conn.execute(
        """SELECT alias.alias, alias.kind, alias.target_slug, article.display_head
           FROM aliases AS alias
           JOIN articles AS article ON article.slug = alias.target_slug
           WHERE alias.rowid = ?""",
        (rowid,),
    ).fetchone()
    if found is None:
        raise ExportError(f"search alias row vanished during export: rowid={rowid}")
    alias, kind, target_slug, target_head = found
    return {"a": alias, "k": kind, "s": target_slug, "h": target_head}


def _article_sort_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return (normalize_atlas_text(row["l"]), row["s"])


def _alias_sort_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (normalize_atlas_text(row["a"]), row["s"], row["k"])


def load_search_rows(conn: sqlite3.Connection) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Whole-corpus search rows in canonical order (compatibility / test oracle)."""
    articles = sorted(_iter_article_search_rows(conn), key=_article_sort_key)
    aliases = sorted(_iter_alias_search_rows(conn), key=_alias_sort_key)
    return articles, aliases


class SearchFamilyIndex:
    """Compact search-family state: row locators plus a sorted key index.

    No serialised row body is retained. ``locators[rank]`` identifies the source
    row at global sort ``rank`` (article slug / alias rowid) and ``replay`` re-reads
    it from the read snapshot on demand, so memory follows the locator and index
    key metadata, never the gloss bodies. ``postings`` is ``(index key, rank)``
    sorted, so every shard prefix is one contiguous range and shard row sets are
    just sorted unique ranks. Global rank order equals the historical per-shard
    order because both sort keys are total.
    """

    __slots__ = ("_replay", "locators", "postings")

    def __init__(
        self,
        locators: list[Any],
        postings: list[tuple[str, int]],
        replay: Callable[[Any], Mapping[str, Any]],
    ) -> None:
        self.locators = locators
        self.postings = postings
        self._replay = replay

    def __len__(self) -> int:
        return len(self.locators)

    def fragment(self, rank: int) -> bytes:
        """Canonical JSON of the row at global sort ``rank``, replayed from the source."""
        return _fragment_bytes(self._replay(self.locators[rank]))

    def iter_fragments(self) -> Iterator[bytes]:
        for rank in range(len(self.locators)):
            yield self.fragment(rank)

    @classmethod
    def build(
        cls,
        rows: Iterable[tuple[Any, Mapping[str, Any]]],
        *,
        sort_key: Callable[[Mapping[str, Any]], tuple[str, ...]],
        key_fn: Callable[[Mapping[str, Any]], list[str]],
        replay: Callable[[Any], Mapping[str, Any]],
    ) -> SearchFamilyIndex:
        """Index ``(locator, row)`` pairs; each row body is dropped once keyed."""
        interned: dict[str, str] = {}
        locators: list[Any] = []
        sort_keys: list[tuple[str, ...]] = []
        postings: list[tuple[str, int]] = []
        for locator, row in rows:
            position = len(locators)
            locators.append(locator)
            sort_keys.append(sort_key(row))
            postings.extend((interned.setdefault(key, key), position) for key in key_fn(row))
        order = sorted(range(len(locators)), key=sort_keys.__getitem__)
        del sort_keys
        rank_of = [0] * len(order)
        for rank, position in enumerate(order):
            rank_of[position] = rank
        locators = [locators[position] for position in order]
        del order
        postings = [(key, rank_of[position]) for key, position in postings]
        postings.sort()
        return cls(locators, postings, replay)


def object_descriptor(
    *,
    object_id: str,
    relative_url: str,
    count: int,
    raw: bytes,
    compressed: bytes,
) -> dict[str, Any]:
    return _descriptor(
        object_id=object_id,
        relative_url=relative_url,
        count=count,
        result=GzipResult(len(compressed), sha256_hex(compressed), len(raw), sha256_hex(raw)),
    )


def _descriptor(*, object_id: str, relative_url: str, count: int, result: GzipResult) -> dict[str, Any]:
    return {
        "id": object_id,
        "url": relative_url,
        "count": count,
        "bytes": result.compressed_bytes,
        "uncompressedBytes": result.uncompressed_bytes,
        "sha256": result.compressed_sha256,
        "jsonSha256": result.json_sha256,
        "encoding": "gzip",
    }


@dataclass(frozen=True)
class GzipResult:
    """Sizes and digests of one gzip object; never its bytes."""

    compressed_bytes: int
    compressed_sha256: str
    uncompressed_bytes: int
    json_sha256: str


@dataclass(frozen=True)
class CompressedObject:
    compressed: bytes
    uncompressed_bytes: int
    json_sha256: str


ChunkSource = Callable[[], Iterable[bytes]]
"""Replayable chunk stream: each call yields the same bytes again (level 0 reads it twice)."""

# ---------------------------------------------------------------------------
# Level 0 (stored blocks) without buffering the object.
#
# ``gzip_bytes(data, 0)`` is ``zlib.compress(data, 0, wbits=31)`` (CPython 3.12
# ``gzip.compress`` with ``mtime=0``). Its stored-block lengths are not a fixed
# 65535 split: zlib's ``deflate_stored`` sizes each block from the input left,
# its 64 KiB window and the *output space* CPython's growing output buffer hands
# it. Those decisions depend only on lengths, never on bytes, so the framing is
# planned from the raw length alone (pass 1: length/sha/crc), then the header,
# stored blocks and trailer are streamed from a replay of the same chunks
# (pass 2). The model is a length-only transcription of zlib v1.3.1 deflate.c
# (``deflate``/``deflate_stored``/``flush_pending``, trees.c ``_tr_stored_block``)
# driven exactly like CPython v3.12.8 ``zlib_compress_impl`` with the
# pycore_blocks_output_buffer.h block schedule. A runtime differential canary
# checks it against the live ``gzip_bytes`` before any level-0 object is framed
# and fails closed on any disagreement.
# ---------------------------------------------------------------------------

_Z_NO_FLUSH, _Z_FINISH = 0, 4
_Z_OK, _Z_STREAM_END, _Z_BUF_ERROR = 0, 1, -5
_UINT_MAX = 0xFFFFFFFF
_W_SIZE = 1 << 15  # windowBits 15
_WINDOW_SIZE = 2 * _W_SIZE
_PENDING_BUF_SIZE = (1 << (8 + 6)) * 4  # lit_bufsize * 4 at DEF_MEM_LEVEL 8
_MAX_STORED = 65535
_STORED_HEADER = 5  # (bi_valid + 42) >> 3: level 0 only ever emits byte-aligned stored blocks
_GZIP_HEADER_BYTES = 10
_GZIP_TRAILER_BYTES = 8
# CPython 3.12 Include/internal/pycore_blocks_output_buffer.h BUFFER_BLOCK_SIZE.
_KIB, _MIB = 1024, 1024 * 1024
_OUTPUT_BLOCK_SIZES = (
    32 * _KIB, 64 * _KIB, 256 * _KIB, 1 * _MIB, 4 * _MIB, 8 * _MIB, 16 * _MIB, 16 * _MIB,
    32 * _MIB, 32 * _MIB, 32 * _MIB, 32 * _MIB, 64 * _MIB, 64 * _MIB, 128 * _MIB, 128 * _MIB,
    256 * _MIB,
)


def _rank(flush: int) -> int:
    return flush * 2 - (9 if flush > 4 else 0)


class StoredDeflateModel:
    """Length-only zlib v1.3.1 ``deflate()`` state at level 0 with the gzip wrapper.

    Tracks exactly the fields that steer stored-block framing (``avail_in``,
    ``avail_out``, ``pending``, ``strstart``, ``block_start``, status, flush
    history, trailer) with C's unsigned 32-bit wraparound where deflate.c uses it.
    Every ``_tr_stored_block`` call is reported to ``on_block(length, last)`` in
    output order; bytes are never modelled. Only ``Z_NO_FLUSH``/``Z_FINISH`` (the
    flushes CPython's one-shot and compressobj paths use) are supported.
    """

    def __init__(self, on_block: Callable[[int, int], object]) -> None:
        self.avail_in = 0
        self.avail_out = 0
        self.total_out = 0
        self._pending = 0
        self._strstart = 0
        self._block_start = 0
        self._status = "gzip"
        self._last_flush = -2
        self._wrap = 2
        self._on_block = on_block

    def _flush_pending(self) -> None:
        moved = min(self._pending, self.avail_out)
        self._pending -= moved
        self.avail_out -= moved
        self.total_out += moved

    def _stored_block(self, length: int, last: int) -> None:
        self._on_block(length, last)
        self._pending += _STORED_HEADER

    def deflate(self, flush: int) -> int:
        if flush not in (_Z_NO_FLUSH, _Z_FINISH) or (self._status == "finish" and flush != _Z_FINISH):
            raise ExportError(f"stored deflate model: unsupported call (flush={flush}, status={self._status})")
        if self.avail_out == 0:
            return _Z_BUF_ERROR
        old_flush, self._last_flush = self._last_flush, flush
        if self._pending:
            self._flush_pending()
            if self.avail_out == 0:
                self._last_flush = -1
                return _Z_OK
        elif self.avail_in == 0 and _rank(flush) <= _rank(old_flush) and flush != _Z_FINISH:
            return _Z_BUF_ERROR
        if self._status == "finish" and self.avail_in != 0:
            return _Z_BUF_ERROR
        if self._status == "gzip":
            self._pending += _GZIP_HEADER_BYTES
            self._status = "busy"
            self._flush_pending()
            if self._pending:
                self._last_flush = -1
                return _Z_OK
        # ``s->lookahead`` stays 0 at level 0 (deflate_stored never fills it).
        if self.avail_in != 0 or (flush != _Z_NO_FLUSH and self._status != "finish"):
            state = self._deflate_stored(flush)
            if state in ("finish_started", "finish_done"):
                self._status = "finish"
            if state in ("need_more", "finish_started"):
                if self.avail_out == 0:
                    self._last_flush = -1
                return _Z_OK
        if flush != _Z_FINISH:
            return _Z_OK
        if self._wrap <= 0:
            return _Z_STREAM_END
        self._pending += _GZIP_TRAILER_BYTES
        self._flush_pending()
        self._wrap = -self._wrap
        return _Z_OK if self._pending else _Z_STREAM_END

    def _deflate_stored(self, flush: int) -> str:
        if self._pending:
            raise ExportError("stored deflate model: pending output on entry to deflate_stored")
        min_block = min(_PENDING_BUF_SIZE - 5, _W_SIZE)
        last = 0
        used = self.avail_in
        while True:
            length = _MAX_STORED
            if self.avail_out < _STORED_HEADER:
                break
            have = self.avail_out - _STORED_HEADER
            left = self._strstart - self._block_start
            if length > left + self.avail_in:  # (ulg) sum: no wrap
                length = left + self.avail_in
            if length > have:
                length = have
            whole = (left + self.avail_in) & _UINT_MAX  # unsigned sum: wraps like the C
            if length < min_block and (
                (length == 0 and flush != _Z_FINISH) or flush == _Z_NO_FLUSH or length != whole
            ):
                break
            last = 1 if flush == _Z_FINISH and length == whole else 0
            self._stored_block(length, last)
            self._flush_pending()
            if left:
                left = min(left, length)
                self.avail_out -= left
                self.total_out += left
                self._block_start += left
                length -= left
            if length:
                if length > self.avail_in:
                    raise ExportError("stored deflate model: direct copy exceeds available input")
                self.avail_in -= length
                self.avail_out -= length
                self.total_out += length
            if last:
                break
        used -= self.avail_in
        if used:
            if used >= _W_SIZE:
                self._strstart = _W_SIZE
            else:
                if _WINDOW_SIZE - self._strstart <= used:
                    self._strstart -= _W_SIZE
                self._strstart += used
            self._block_start = self._strstart
        if last:
            return "finish_done"
        have = _WINDOW_SIZE - self._strstart
        if self.avail_in > have and self._block_start >= _W_SIZE:
            self._block_start -= _W_SIZE
            self._strstart -= _W_SIZE
            have += _W_SIZE
        have = min(have, self.avail_in)
        if have:
            self.avail_in -= have
            self._strstart += have
        have = min(_PENDING_BUF_SIZE - _STORED_HEADER, _MAX_STORED)
        min_block = min(have, _W_SIZE)
        left = self._strstart - self._block_start
        if left >= min_block or (
            (left or flush == _Z_FINISH) and flush != _Z_NO_FLUSH and self.avail_in == 0 and left <= have
        ):
            length = min(left, have)
            last = 1 if flush == _Z_FINISH and self.avail_in == 0 and length == left else 0
            self._stored_block(length, last)
            self._pending += length
            self._block_start += length
            self._flush_pending()
        return "finish_started" if last else "need_more"


class OutputBlocks:
    """CPython ``_BlocksOutputBuffer`` growth schedule (``max_length == -1``)."""

    def __init__(self) -> None:
        self._count = 0

    def next_block(self) -> int:
        size = _OUTPUT_BLOCK_SIZES[min(self._count, len(_OUTPUT_BLOCK_SIZES) - 1)]
        self._count += 1
        return size


def stored_block_plan(raw_bytes: int) -> list[tuple[int, int]]:
    """``(length, last)`` of every stored block ``gzip_bytes(<raw_bytes bytes>, 0)`` emits.

    Drives :class:`StoredDeflateModel` like CPython 3.12.8 ``zlib_compress_impl``:
    input handed over in ``UINT_MAX`` slices (``Z_NO_FLUSH`` until the last,
    ``Z_FINISH``), ``deflate`` repeated while it fills the output, which grows by
    the output-buffer schedule only once full.
    """
    if raw_bytes < 0:
        raise ValueError("raw_bytes must be non-negative")
    blocks: list[tuple[int, int]] = []
    model = StoredDeflateModel(lambda length, last: blocks.append((length, last)))
    output = OutputBlocks()
    model.avail_out = output.next_block()
    remaining = raw_bytes
    status = _Z_OK
    while True:
        model.avail_in = min(remaining, _UINT_MAX)
        remaining -= model.avail_in
        flush = _Z_FINISH if remaining == 0 else _Z_NO_FLUSH
        while True:
            if model.avail_out == 0:
                model.avail_out = output.next_block()
            status = model.deflate(flush)
            if model.avail_out != 0:
                break
        if model.avail_in != 0:
            raise ExportError("stored block plan: zlib left input unconsumed")
        if flush == _Z_FINISH:
            break
    stored = sum(length for length, _last in blocks)
    framed = _GZIP_HEADER_BYTES + len(blocks) * _STORED_HEADER + stored + _GZIP_TRAILER_BYTES
    if (
        status != _Z_STREAM_END
        or stored != raw_bytes
        or [last for _length, last in blocks] != [0] * (len(blocks) - 1) + [1]
        or any(length > _MAX_STORED for length, _last in blocks)
        or framed != model.total_out
    ):
        raise ExportError(f"stored block plan is inconsistent for {raw_bytes} bytes")
    return blocks


def _stored_gzip_size(blocks: Sequence[tuple[int, int]], raw_bytes: int) -> int:
    return _GZIP_HEADER_BYTES + len(blocks) * _STORED_HEADER + raw_bytes + _GZIP_TRAILER_BYTES


def _frame_stored_gzip(
    source: ChunkSource, blocks: Sequence[tuple[int, int]], emit: Callable[[bytes], object]
) -> tuple[int, str, int]:
    """Emit header, stored blocks and trailer around a replay of ``source``.

    Returns ``(raw bytes, raw sha256, crc32)`` of the replay so the caller can
    prove it matched the planned pass.
    """
    raw_sha = hashlib.sha256()
    raw_bytes = 0
    crc = 0
    emit(gzip_bytes(b"", compression_level=0)[:_GZIP_HEADER_BYTES])
    plan = iter(blocks)
    remaining = 0

    def open_block() -> int:
        try:
            length, last = next(plan)
        except StopIteration:
            raise ExportError("level-0 replay produced more bytes than planned") from None
        emit(bytes((last,)) + struct.pack("<HH", length, length ^ 0xFFFF))
        return length

    for chunk in source():
        raw_sha.update(chunk)
        crc = zlib.crc32(chunk, crc)
        raw_bytes += len(chunk)
        view = memoryview(chunk)
        position = 0
        while position < len(chunk):
            while remaining == 0:
                remaining = open_block()
            take = min(remaining, len(chunk) - position)
            emit(bytes(view[position : position + take]))
            position += take
            remaining -= take
    if remaining:
        raise ExportError("level-0 replay produced fewer bytes than planned")
    for length, last in plan:  # only an empty final block can remain (empty input)
        if length:
            raise ExportError("level-0 replay produced fewer bytes than planned")
        emit(bytes((last,)) + struct.pack("<HH", 0, 0xFFFF))
    emit(struct.pack("<LL", crc, raw_bytes & 0xFFFFFFFF))
    return raw_bytes, raw_sha.hexdigest(), crc


# Lengths that exercise every deflate_stored branch (direct copy, window fill,
# slide, pending block, empty final block) and the first four output-buffer
# growths (32 KiB -> 64 KiB -> 256 KiB -> 1 MiB -> 4 MiB).
_STORED_CANARY_LENGTHS = (
    0, 1, 5, 32_752, 32_753, 32_754, 32_768, 65_530, 65_531, 65_532, 65_536, 98_304, 98_309,
    100_000, 131_072, 262_144, 400_000, 1_048_576, 1_500_000,
)
_stored_canary_passed = False


def check_stored_gzip_runtime() -> None:
    """Fail closed unless the planner reproduces this runtime's ``gzip_bytes(..., 0)``."""
    global _stored_canary_passed
    if _stored_canary_passed:
        return
    pattern = bytes(range(251)) * (max(_STORED_CANARY_LENGTHS) // 251 + 1)
    for length in _STORED_CANARY_LENGTHS:
        data = pattern[:length]
        pieces: list[bytes] = []
        _frame_stored_gzip(lambda data=data: (data,), stored_block_plan(length), pieces.append)
        if b"".join(pieces) != gzip_bytes(data, compression_level=0):
            raise ExportError(
                f"level-0 stored-block planner disagrees with this runtime's gzip (zlib "
                f"{zlib.ZLIB_RUNTIME_VERSION}, Python {sys.version.split()[0]}) at {length} bytes; "
                "refusing to frame level-0 objects"
            )
    _stored_canary_passed = True


def _plan_stored_gzip(source: ChunkSource, *, max_bytes: int | None) -> tuple[list[tuple[int, int]], tuple[int, str, int]] | None:
    """Level-0 pass 1: the block plan and ``(raw bytes, sha256, crc32)``; ``None`` past ``max_bytes``."""
    check_stored_gzip_runtime()
    raw_sha = hashlib.sha256()
    raw_bytes = 0
    crc = 0
    for chunk in source():
        raw_bytes += len(chunk)
        if max_bytes is not None and raw_bytes > max_bytes:
            return None  # stored output is never smaller than its input
        raw_sha.update(chunk)
        crc = zlib.crc32(chunk, crc)
    blocks = stored_block_plan(raw_bytes)
    if max_bytes is not None and _stored_gzip_size(blocks, raw_bytes) > max_bytes:
        return None
    return blocks, (raw_bytes, raw_sha.hexdigest(), crc)


def stream_gzip(
    source: ChunkSource,
    *,
    compression_level: int,
    sink: Callable[[bytes], object],
    max_bytes: int | None = None,
) -> GzipResult | None:
    """Gzip a replayable chunk stream into ``sink``, byte-identically to ``gzip_bytes`` of the joined chunks.

    Nothing is retained at any level: each compressed piece goes to ``sink`` as it
    is produced and only sizes/digests are kept. Returns ``None`` — abandoning the
    (lazy) chunk source — as soon as the compressed size is certain to exceed
    ``max_bytes``; ``sink`` has then seen a prefix (or nothing) and must be
    discarded by the caller. Levels 1-9: deflate output is independent of how the
    input is chunked, so one pass streams the one-shot payload (gzip header taken
    from ``gzip_bytes`` itself, raw deflate body, crc32/isize trailer) and the
    compressed prefix emitted so far is a strict lower bound on the final size.
    Level 0 (stored blocks) frames blocks the way the one-shot call does, which
    follows the whole input length: ``source`` is read once to plan (aborting once
    the raw bytes alone pass the cap) and once more to stream the framed blocks.
    """
    compressed_sha = hashlib.sha256()
    size = 0

    def emit(piece: bytes) -> bool:
        nonlocal size
        if piece:
            size += len(piece)
            compressed_sha.update(piece)
            sink(piece)
        return max_bytes is not None and size > max_bytes

    if compression_level == 0:
        planned = _plan_stored_gzip(source, max_bytes=max_bytes)
        if planned is None:
            return None
        blocks, raw = planned
        replayed = _frame_stored_gzip(source, blocks, emit)
        if replayed != raw or size != _stored_gzip_size(blocks, raw[0]):
            raise ExportError("level-0 replay differs from its planning pass; refusing to publish")
        return GzipResult(size, compressed_sha.hexdigest(), raw[0], raw[1])

    raw_sha = hashlib.sha256()
    raw_bytes = 0
    crc = 0
    deflater = zlib.compressobj(compression_level, zlib.DEFLATED, -zlib.MAX_WBITS)
    if emit(gzip_bytes(b"", compression_level=compression_level)[:10]):
        return None
    for chunk in source():
        raw_sha.update(chunk)
        crc = zlib.crc32(chunk, crc)
        raw_bytes += len(chunk)
        if emit(deflater.compress(chunk)):
            return None
    if emit(deflater.flush()) or emit(struct.pack("<LL", crc, raw_bytes & 0xFFFFFFFF)):
        return None
    return GzipResult(size, compressed_sha.hexdigest(), raw_bytes, raw_sha.hexdigest())


def compress_stream_bounded(
    source: ChunkSource,
    *,
    compression_level: int,
    max_bytes: int | None,
) -> CompressedObject | None:
    """``stream_gzip`` into memory: at most ``max_bytes`` (plus one piece) is held.

    Only for capped candidates; an uncapped object is streamed (``stream_gzip``)
    or measured (``gzip_size``), never materialized.
    """
    pieces: list[bytes] = []
    result = stream_gzip(source, compression_level=compression_level, sink=pieces.append, max_bytes=max_bytes)
    if result is None:
        return None
    return CompressedObject(b"".join(pieces), result.uncompressed_bytes, result.json_sha256)


def gzip_size(source: ChunkSource, *, compression_level: int) -> int:
    """Exact ``len(gzip_bytes(b"".join(chunks)))``, counted without keeping the output."""
    if compression_level == 0:  # the stored framing follows from the raw length alone
        planned = _plan_stored_gzip(source, max_bytes=None)
        assert planned is not None  # uncapped
        blocks, raw = planned
        return _stored_gzip_size(blocks, raw[0])
    result = stream_gzip(source, compression_level=compression_level, sink=lambda _piece: None)
    assert result is not None  # uncapped
    return result.compressed_bytes


def _write_compressed(
    open_object: Callable[[str], BinaryIO], relative: str, compressed: CompressedObject
) -> GzipResult:
    with open_object(relative) as handle:
        handle.write(compressed.compressed)
    return GzipResult(
        len(compressed.compressed),
        sha256_hex(compressed.compressed),
        compressed.uncompressed_bytes,
        compressed.json_sha256,
    )


def _shard_envelope(payload: Mapping[str, Any]) -> tuple[bytes, bytes]:
    """Split a shard payload's canonical JSON around its ``records`` array."""
    text = _dumps({**payload, "records": []})
    if not text.endswith('"records":[]}'):
        raise ExportError("shard payload envelope must end with its records array")
    return text[:-2].encode("utf-8"), b"]}\n"


def _shard_chunks(head: bytes, fragments: Iterable[bytes], tail: bytes) -> Iterator[bytes]:
    yield head
    for position, fragment in enumerate(fragments):
        yield fragment if position == 0 else b"," + fragment
    yield tail


def slug_digest(slug: str) -> bytes:
    return hashlib.sha256(normalize_slug_for_hash(slug).encode("utf-8")).digest()


def _first_one_bit(
    ordered: Sequence[tuple[bytes, str]], lo: int, hi: int, bit_index: int
) -> int:
    """First index in ``[lo, hi)`` whose digest has a 1 at ``bit_index`` (MSB first)."""
    byte, shift = bit_index >> 3, 7 - (bit_index & 7)
    while lo < hi:
        mid = (lo + hi) // 2
        if (ordered[mid][0][byte] >> shift) & 1:
            hi = mid
        else:
            lo = mid + 1
    return lo


def build_entry_shards(
    route_meta: Iterable[tuple[bytes, str]],
    fragment_for_slug: Callable[[str], bytes],
    *,
    data_version: str,
    max_gzip_bytes: int,
    compression_level: int,
    open_object: Callable[[str], BinaryIO],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Adaptive SHA-256 prefix trie over NFC-normalized slug hashes.

    ``route_meta`` is ``(slug digest, slug)`` per public route. A trie node is a
    contiguous range of the digest-sorted metadata; a leaf's records are replayed
    (slug order) through ``fragment_for_slug``, gzip-streamed and written straight
    through ``open_object``. Only descriptors are retained.
    """
    ordered = sorted(route_meta)
    head, tail = _shard_envelope(
        {"schema": ENTRY_SHARD_SCHEMA, "schemaVersion": SCHEMA_VERSION, "dataVersion": data_version}
    )
    descriptors: dict[str, dict[str, Any]] = {}

    def source(slugs: Sequence[str]) -> ChunkSource:
        return lambda: _shard_chunks(head, (fragment_for_slug(slug) for slug in slugs), tail)

    def materialize(bit_length: int, prefix_value: int, lo: int, hi: int, known_oversize: bool) -> None:
        slugs = sorted(item[1] for item in ordered[lo:hi])
        result = (
            None
            if known_oversize
            else compress_stream_bounded(
                source(slugs), compression_level=compression_level, max_bytes=max_gzip_bytes
            )
        )
        if result is not None:
            shard_id = entry_shard_id(bit_length, prefix_value)
            relative = f"entries/{shard_id}.json.gz"
            descriptors[shard_id] = _descriptor(
                object_id=shard_id,
                relative_url=relative,
                count=len(slugs),
                result=_write_compressed(open_object, relative, result),
            )
            return
        if len(slugs) <= 1:
            size = gzip_size(source(slugs), compression_level=compression_level)
            slug = slugs[0] if slugs else "?"
            raise ExportError(
                f"single entry record exceeds entry-max-gzip-bytes "
                f"({size} > {max_gzip_bytes}) slug={slug!r}"
            )
        if bit_length >= 256:
            raise ExportError(
                f"entry shard of {len(slugs)} records cannot split: slug hashes are identical"
            )
        del slugs
        mid = _first_one_bit(ordered, lo, hi, bit_length)
        child_bits = bit_length + 1
        # A one-sided split leaves the identical record set (and identical, still
        # oversized, payload) one bit deeper, so it needs no second probe.
        if mid == lo:
            materialize(child_bits, (prefix_value << 1) | 1, lo, hi, True)
        elif mid == hi:
            materialize(child_bits, prefix_value << 1, lo, hi, True)
        else:
            materialize(child_bits, prefix_value << 1, lo, mid, False)
            materialize(child_bits, (prefix_value << 1) | 1, mid, hi, False)

    materialize(0, 0, 0, len(ordered), False)

    # Prefix-free lookup tree: each leaf is a shard id; internal nodes branch on next bit.
    tree: dict[str, Any] = {"bitLength": 0, "children": {}}

    def insert_leaf(shard_id: str) -> None:
        # shard_id format pBB-HEX
        match = re.fullmatch(r"p(\d+)-([0-9a-f]+)", shard_id)
        if not match:
            raise ExportError(f"invalid entry shard id {shard_id!r}")
        bit_length = int(match.group(1))
        prefix_value = int(match.group(2), 16)
        node = tree
        value = prefix_value
        # Walk from MSB of the prefix.
        for depth in range(bit_length):
            shift = bit_length - depth - 1
            bit = "1" if (value >> shift) & 1 else "0"
            children = node.setdefault("children", {})
            if bit not in children:
                children[bit] = {"bitLength": depth + 1}
            node = children[bit]
        node["shardId"] = shard_id
        node.pop("children", None)

    for shard_id in sorted(descriptors):
        insert_leaf(shard_id)

    index = {
        "strategy": "sha256-prefix-trie",
        "hash": "sha256(NFC(slug))",
        "maxGzipBytes": max_gzip_bytes,
        "tree": tree,
        "shards": {key: descriptors[key] for key in sorted(descriptors)},
    }
    return index, descriptors


def _article_index_keys(row: Mapping[str, Any]) -> list[str]:
    keys: list[str] = []
    head = normalize_atlas_text(str(row.get("l") or ""))
    if head:
        keys.append(head)
    roman = normalize_atlas_text(str(row.get("r") or ""))
    if roman:
        keys.append(roman)
    gloss = normalize_atlas_text(str(row.get("g") or ""))
    if gloss:
        keys.extend(TOKEN_RE.findall(gloss))
    # Preserve insertion order, drop empties/dupes.
    seen: set[str] = set()
    ordered: list[str] = []
    for key in keys:
        if key and key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


def _alias_index_keys(row: Mapping[str, Any]) -> list[str]:
    text = normalize_atlas_text(str(row.get("a") or ""))
    return [text] if text else []


def build_search_family_shards(
    index: SearchFamilyIndex,
    *,
    family: str,
    data_version: str,
    max_gzip_bytes: int,
    compression_level: int,
    schema: str,
    open_object: Callable[[str], BinaryIO],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Adaptive Unicode-prefix trie over indexed keys for one search family.

    A node is a contiguous range of the sorted postings (all keys sharing the
    prefix). Its rows are the unique ranks in that range, streamed in rank order —
    the historical shard order — with an early abort past the gzip cap. Uncapped
    work never holds a shard: a terminal shard (exact-prefix rows, historically
    exempt from the cap) is gzip-streamed straight into ``open_object``, and an
    unsplittable bucket's error size is counted, not materialized.
    """
    postings = index.postings
    descriptors: dict[str, dict[str, Any]] = {}

    def ranks_in(lo: int, hi: int) -> list[int]:
        return sorted({postings[position][1] for position in range(lo, hi)})

    def source(prefix: str, ranks: Sequence[int], *, terminal: bool) -> ChunkSource:
        head, tail = _shard_envelope(
            {
                "schema": schema,
                "schemaVersion": SCHEMA_VERSION,
                "dataVersion": data_version,
                "prefix": prefix,
                "terminal": terminal,
            }
        )
        return lambda: _shard_chunks(head, (index.fragment(rank) for rank in ranks), tail)

    def emit(prefix: str, count: int, write: Callable[[str], GzipResult], *, terminal: bool = False) -> str:
        shard_id = search_shard_id(prefix) + (".term" if terminal else "")
        relative = f"search/{family}/{shard_id}.json.gz"
        descriptors[shard_id] = _descriptor(
            object_id=shard_id, relative_url=relative, count=count, result=write(relative)
        )
        return shard_id

    def stream_terminal(prefix: str, ranks: Sequence[int], relative: str) -> GzipResult:
        with open_object(relative) as handle:
            result = stream_gzip(
                source(prefix, ranks, terminal=True),
                compression_level=compression_level,
                sink=handle.write,
            )
        assert result is not None  # uncapped
        return result

    def split_or_write(prefix: str, lo: int, hi: int) -> dict[str, Any]:
        ranks = ranks_in(lo, hi)
        result = compress_stream_bounded(
            source(prefix, ranks, terminal=False),
            compression_level=compression_level,
            max_bytes=max_gzip_bytes,
        )
        node: dict[str, Any] = {"prefix": prefix}
        if result is not None:
            node["shardId"] = emit(
                prefix, len(ranks), lambda relative: _write_compressed(open_object, relative, result)
            )
            return node

        # Split on the next Unicode scalar of each indexed key under this prefix.
        # Keys equal to the prefix sort first (terminals); the rest group by next char.
        depth = len(prefix)
        terminal_end = lo
        while terminal_end < hi and len(postings[terminal_end][0]) == depth:
            terminal_end += 1
        children: list[tuple[str, int, int]] = []
        position = terminal_end
        while position < hi:
            char = postings[position][0][depth]
            end = position + 1
            while end < hi and postings[end][0][depth] == char:
                end += 1
            children.append((char, position, end))
            position = end

        if not children:
            # Cannot split further — hard fail (still oversized).
            size = gzip_size(source(prefix, ranks, terminal=False), compression_level=compression_level)
            raise ExportError(
                f"search {family} shard for prefix={prefix!r} exceeds max "
                f"({size} > {max_gzip_bytes}) and cannot split"
            )
        del ranks

        if terminal_end > lo:
            terminal_ranks = ranks_in(lo, terminal_end)
            node["terminalShardId"] = emit(
                prefix,
                len(terminal_ranks),
                lambda relative: stream_terminal(prefix, terminal_ranks, relative),
                terminal=True,
            )

        node["children"] = {
            char: split_or_write(prefix + char, child_lo, child_hi)
            for char, child_lo, child_hi in children
        }
        return node

    root_children: dict[str, Any] = {}
    position = 0
    while position < len(postings):
        char = postings[position][0][0]
        end = position + 1
        while end < len(postings) and postings[end][0][0] == char:
            end += 1
        root_children[char] = split_or_write(char, position, end)
        position = end

    search_index = {
        "strategy": "unicode-prefix-trie",
        "family": family,
        "maxGzipBytes": max_gzip_bytes,
        "tree": {"prefix": "", "children": root_children},
        "shards": {key: descriptors[key] for key in sorted(descriptors)},
    }
    return search_index, descriptors


def register_decks(
    deck_dir: Path | None,
    *,
    compression_level: int,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    if deck_dir is None:
        return {"levels": {}}, {}

    levels: dict[str, Any] = {}
    compressed_files: dict[str, bytes] = {}
    for level in PRACTICE_LEVELS:
        parts: dict[str, Any] = {}
        deck_versions: set[str] = set()
        for part in DECK_PARTS:
            source_name = f"practice-{part}.{level}.json"
            source = deck_dir / source_name
            if not source.is_file():
                raise ExportError(f"missing practice deck part: {source}")
            raw_text = source.read_bytes()
            # Normalize to canonical trailing newline without reshaping JSON keys.
            if not raw_text.endswith(b"\n"):
                raw_text = raw_text + b"\n"
            payload = json.loads(raw_text.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ExportError(f"deck part is not an object: {source}")
            version = payload.get("deckVersion")
            if isinstance(version, str) and version:
                deck_versions.add(version)
            compressed = gzip_bytes(raw_text, compression_level=compression_level)
            object_id = f"{level}-{part}"
            relative = f"decks/{level}/{part}.json.gz"
            parts[part] = object_descriptor(
                object_id=object_id,
                relative_url=relative,
                count=1,
                raw=raw_text,
                compressed=compressed,
            )
            compressed_files[f"{level}/{part}"] = compressed
        if len(deck_versions) != 1:
            raise ExportError(
                f"deck parts for {level} must share one deckVersion, got {sorted(deck_versions)}"
            )
        levels[level] = {
            "deckVersion": next(iter(deck_versions)),
            "parts": parts,
        }
    return {"levels": levels}, compressed_files


class DataVersionHasher:
    """Incremental SHA-256 of the dataVersion identity document.

    Feeds the exact bytes ``canonical_json_bytes`` of the historical identity
    structure would contain (entries, then searchArticles, searchAliases, decks),
    without ever building that corpus-sized structure.
    """

    def __init__(self, *, generated_at: str) -> None:
        self._sha = hashlib.sha256()
        self._entries = 0
        head = f'{{"schemaVersion":{_dumps(SCHEMA_VERSION)},"generatedAt":{_dumps(generated_at)},"entries":['
        self._sha.update(head.encode("utf-8"))

    def add_entry(self, record: Mapping[str, Any]) -> None:
        identity = {
            "slug": record["slug"],
            "kind": record["kind"],
            "entrySha256": sha256_hex(canonical_json_bytes(record["entry"])),
            "aliasesSha256": sha256_hex(canonical_json_bytes(record["aliases"])),
            "relationsSha256": sha256_hex(canonical_json_bytes(record["relations"])),
            "provenanceSha256": sha256_hex(canonical_json_bytes(record["provenance"])),
            "renderContextSha256": sha256_hex(canonical_json_bytes(record["renderContext"])),
        }
        self._sha.update((b"," if self._entries else b"") + _fragment_bytes(identity))
        self._entries += 1

    def _add_rows(self, name: bytes, fragments: Iterable[bytes]) -> None:
        self._sha.update(b'],"' + name + b'":[')
        for position, fragment in enumerate(fragments):
            self._sha.update(fragment if position == 0 else b"," + fragment)

    def finish(
        self,
        *,
        article_fragments: Iterable[bytes],
        alias_fragments: Iterable[bytes],
        deck_index: Mapping[str, Any],
    ) -> str:
        self._add_rows(b"searchArticles", article_fragments)
        self._add_rows(b"searchAliases", alias_fragments)
        decks = {
            level: info.get("deckVersion")
            for level, info in sorted((deck_index.get("levels") or {}).items())
        }
        self._sha.update(f'],"decks":{_dumps(decks)}}}\n'.encode())
        return f"atlas-v1-{self._sha.hexdigest()[:16]}"


def compute_data_version(
    *,
    generated_at: str,
    entry_records: Iterable[Mapping[str, Any]],
    article_rows: Iterable[Mapping[str, Any]],
    alias_rows: Iterable[Mapping[str, Any]],
    deck_index: Mapping[str, Any],
) -> str:
    hasher = DataVersionHasher(generated_at=generated_at)
    for record in entry_records:
        hasher.add_entry(record)
    return hasher.finish(
        article_fragments=(_fragment_bytes(row) for row in article_rows),
        alias_fragments=(_fragment_bytes(row) for row in alias_rows),
        deck_index=deck_index,
    )


def capacity_report(
    *,
    public_routes: int,
    total_entry_gzip_bytes: int,
    leaf_count: int,
    targets: Sequence[int],
) -> dict[str, Any]:
    density = total_entry_gzip_bytes / public_routes if public_routes else 0.0
    projections = []
    for target in targets:
        est_bytes = density * target
        # Assume leaves stay near mid of 0.5–1.0 MiB band (~0.75 MiB).
        est_leaves = max(1, math.ceil(est_bytes / ((DEFAULT_ENTRY_TARGET_MIN + DEFAULT_ENTRY_MAX) / 2)))
        projections.append(
            {
                "routes": target,
                "estimatedGzipBytes": int(est_bytes),
                "estimatedLeaves": est_leaves,
                "bytesPerRoute": round(density, 3),
            }
        )
    return {
        "observedRoutes": public_routes,
        "observedEntryGzipBytes": total_entry_gzip_bytes,
        "observedLeaves": leaf_count,
        "bytesPerRoute": round(density, 3),
        "projections": projections,
    }


# ---------------------------------------------------------------------------
# Streaming verification (#8672): an object is hashed, inflated and parsed as a
# stream by ijson, holding one record (or one top-level member) at a time —
# never the whole shard. Values are built as ``json.loads`` builds them: an
# integer literal is an exact ``int``, any other number is ``float`` of its text
# (ijson hands over a ``Decimal``, converted here, so ``1e400`` is ``inf``), and
# duplicate members keep last-wins semantics. The fast backend is yajl (ijson's ``yajl2_c``), whose
# known departures from ``json.loads`` are closed here, not inherited:
#
# * yajl accepts an unterminated string after the top-level value (``{...}"x``)
#   at EOF. The parser therefore reads ``_EOF_SENTINEL`` (never hashed) after the
#   real bytes, with ``multiple_values``: an open string meets its raw newline and
#   fails, and a complete document is followed by exactly the sentinel ``""``.
# * yajl treats ``\v``/``\f`` as whitespace. Those bytes are invalid anywhere in
#   JSON text (UTF-8 never uses them inside a multi-byte character), so their
#   presence alone rejects the document.
# * yajl turns an unpaired ``\uD800``-``\uDBFF`` escape into ``?`` or merges it
#   with the next ``\u`` escape, and rejects an unpaired ``\uDC00``-``\uDFFF``.
#   yajl therefore sees every surrogate escape rewritten to ``\u0000`` (same
#   length, same syntax wherever it sits), and a document that had one is decoded
#   again by the exact decoder (below); yajl has already judged its syntax. (The
#   exporter never writes one: canonical JSON is ``ensure_ascii=False``.)
# * ijson builds a ``Decimal`` from every non-integer literal, and ``Decimal``
#   cannot hold an exponent beyond about 10**18 (``1e-99999999999999999999``,
#   which ``json.loads`` reads as ``0.0``). yajl runs under a ``decimal`` context
#   that does not trap the failed conversion: the literal becomes ``NaN`` (never
#   a JSON value) with the context's flag raised, yajl finishes judging the
#   syntax, and the document is decoded again by the exact decoder.
# * ijson's ``yajl2_c`` mishandles the ``ValueError`` of an integer literal past
#   ``sys.get_int_max_str_digits()`` (a leaked ``SystemError``, or a crash of the
#   interpreter). yajl therefore sees every digit run that long cut to its first
#   four digits (same syntax wherever it sits), and a document that had one is
#   decoded again by the exact decoder, where ``int()`` raises as in ``json.loads``.
#
# The exact decoder is :func:`_exact_basic_parse`: the stdlib's own string scanner
# (``json.decoder.scanstring``) and number rules (``int``/``float`` of the literal
# text), token by token, so any valid document is read exactly as ``json.loads``
# reads it — one token in memory at a time, with no size or exponent cap.
#
# What remains fails closed, never open: ``NaN``/``Infinity``/``-Infinity``
# (``json.loads`` extensions, not JSON; the browser's ``JSON.parse`` rejects them
# too) are reported as invalid JSON.
# ---------------------------------------------------------------------------

_VERIFY_READ_BYTES = 1 << 16
_EOF_SENTINEL = b'\n""'
_FORBIDDEN_WS = re.compile(rb"[\x0b\x0c]")
_SURROGATE_ESCAPE = re.compile(rb"\\u[dD][89a-fA-F][0-9a-fA-F]{2}")
_SURROGATE_ESCAPE_HOLD = 5  # an escape is 6 bytes: at most 5 can wait for the next read
_NEUTRAL_ESCAPE = b"\\u0000"
_DIGITS = b"0123456789"
_DIGITS_AS_ZERO = bytes(0x30 if 0x30 <= byte <= 0x39 else 0x78 for byte in range(256))  # digits -> 0, rest -> x
_DIGIT_RUN_KEEP = 4  # digits a too-long run keeps: all of a ``\uXXXX`` escape's that it may start in
_CONTAINER_START = frozenset(("start_map", "start_array"))
_CONTAINER_END = frozenset(("end_map", "end_array"))
# yajl's pass: an out-of-range exponent becomes ``NaN`` and raises the flag instead of the error.
_UNTRAPPED_DECIMAL = decimal.Context(traps=[])
_JSON_WS = re.compile(r"[ \t\n\r]*")
_JSON_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?")
_JSON_NUMBER_RUN = re.compile(r"[-+.eE0-9]*")
_JSON_LITERALS = (("true", True), ("false", False), ("null", None))


class JsonStreamError(ValueError):
    """Invalid JSON text."""


@functools.cache
def _long_digit_run(limit: int) -> re.Pattern[bytes]:
    """A whole run of more than ``limit`` ASCII digits."""
    return re.compile(rb"(?<![0-9])[0-9]{%d,}" % (limit + 1))


class _ParserInput:
    """What the JSON parser reads: the text, then ``_EOF_SENTINEL``.

    Flags ``\\v``/``\\f`` bytes. Unless ``exact``, also rewrites every surrogate
    escape to ``\\u0000`` (same length and syntax, wherever it sits) so yajl's
    verdict never depends on how it decodes surrogates, and cuts every run of more
    than ``sys.get_int_max_str_digits()`` digits to its first four so yajl never
    converts an integer ``int()`` refuses. Four keeps the syntax wherever the run
    sits: a leading ``0`` stays followed by a digit, and a run that starts inside
    a ``\\uXXXX`` escape keeps all of that escape's digits. Either flag then tells
    the caller to take the values from an exact pass.
    """

    def __init__(self, binary: BinaryIO, *, exact: bool) -> None:
        self._binary = binary
        self._exact = exact
        self._sentinel = _EOF_SENTINEL
        self._held = b""  # tail the next read may still change: a surrogate escape's head, a digit run
        limit = sys.get_int_max_str_digits()
        self._long_digits = _long_digit_run(limit) if limit else None
        self._too_many_digits = b"0" * (limit + 1)  # in ``_DIGITS_AS_ZERO`` terms: C-speed pre-check
        self.forbidden_whitespace = False
        self.surrogate_escape = False
        self.long_digit_run = False

    def read(self, size: int = -1) -> bytes:
        if size == 0:
            return b""
        while True:
            data = self._binary.read(size)
            if not data:
                data, self._held, self._sentinel = self._held + self._sentinel, b"", b""
                return data
            if not self.forbidden_whitespace and _FORBIDDEN_WS.search(data):
                self.forbidden_whitespace = True
            if self._exact:
                return data
            text, count = _SURROGATE_ESCAPE.subn(lambda _match: _NEUTRAL_ESCAPE, self._held + data)
            self.surrogate_escape = self.surrogate_escape or count > 0
            hold = _SURROGATE_ESCAPE_HOLD  # an escape starting before it is complete: rewritten above
            if self._long_digits is not None:
                if self._too_many_digits in text.translate(_DIGITS_AS_ZERO):
                    text, count = self._long_digits.subn(lambda match: match[0][:_DIGIT_RUN_KEEP], text)
                    self.long_digit_run = self.long_digit_run or count > 0
                # A trailing digit run (at most the limit long, now) is held whole until it ends.
                hold = max(hold, len(text) - len(text.rstrip(_DIGITS)))
            data, self._held = text[:-hold], text[-hold:]
            if data:
                return data


@functools.cache
def _json_backend() -> Any:
    """ijson's ``yajl2_c`` backend: the fast pass, whose syntax check is relied on."""
    try:
        return ijson.get_backend("yajl2_c")
    except ImportError as exc:  # pragma: no cover - ijson wheels ship yajl2_c
        raise ExportError(f"streaming verify needs ijson's yajl2_c backend: {exc}") from exc


# Parser states of the exact decoder.
_VALUE, _VALUE_OR_END, _KEY, _KEY_OR_END, _COLON, _COMMA_OR_END = range(6)


def _exact_basic_parse(source: _ParserInput, read_bytes: int) -> Iterator[tuple[str, Any]]:
    """ijson ``basic_parse`` events (``multiple_values``) of ``source`` with ``json.loads`` values.

    Strings go through ``json.decoder.scanstring`` (strict, as ``json.loads``) and
    numbers are ``int``/``float`` of their literal text, so a surrogate escape or
    an exponent no ``Decimal`` holds reads exactly as ``json.loads`` reads it.
    One token is buffered at a time; anything that is not JSON raises
    :class:`JsonStreamError`.
    """
    decode = codecs.getincrementaldecoder("utf-8")().decode
    text, pos, eof = "", 0, False

    def more() -> bool:
        """Append the next read to the unconsumed text; False once the input is exhausted."""
        nonlocal text, pos, eof
        if eof:
            return False
        # Grow with the pending token, so a long string or number is read in linear time.
        data = source.read(max(read_bytes, len(text) - pos))
        try:
            decoded = decode(data, final=not data)
        except UnicodeDecodeError as exc:
            raise JsonStreamError(str(exc)) from None
        text, pos, eof = text[pos:] + decoded, 0, not data
        return True

    stack: list[bool] = []  # True for an object, False for an array
    state = _VALUE
    while True:
        while (pos := _JSON_WS.match(text, pos).end()) == len(text):
            if not more():
                if stack or state != _VALUE:
                    raise JsonStreamError("Expecting value")
                return
        char = text[pos]
        if state == _COLON:
            if char != ":":
                raise JsonStreamError("Expecting ':' delimiter")
            pos, state = pos + 1, _VALUE
            continue
        if state == _COMMA_OR_END and char == ",":
            pos, state = pos + 1, _KEY if stack[-1] else _VALUE
            continue
        if (char == "}" and state in (_KEY_OR_END, _COMMA_OR_END) and stack[-1]) or (
            char == "]" and state in (_VALUE_OR_END, _COMMA_OR_END) and not stack[-1]
        ):
            pos += 1
            yield ("end_map" if stack.pop() else "end_array"), None
        elif state in (_COMMA_OR_END, _COLON):
            raise JsonStreamError("Expecting ',' delimiter")
        elif char == '"':
            end = pos + 1
            while True:  # the closing quote: one preceded by an even run of backslashes
                end = text.find('"', end)
                if end < 0:
                    scanned = len(text) - pos
                    if not more():
                        raise JsonStreamError("Unterminated string")
                    end = pos + scanned  # ``more`` moved the token to the start of ``text``
                    continue
                escape = end - 1
                while text[escape] == "\\":
                    escape -= 1
                if (end - escape) % 2:
                    break
                end += 1
            try:
                value, pos = json.decoder.scanstring(text, pos + 1, True)
            except json.JSONDecodeError as exc:
                raise JsonStreamError(exc.msg) from None
            if state in (_KEY, _KEY_OR_END):
                yield "map_key", value
                state = _COLON
                continue
            yield "string", value
        elif state in (_KEY, _KEY_OR_END):
            raise JsonStreamError("Expecting property name enclosed in double quotes")
        elif char == "{" or char == "[":
            pos += 1
            stack.append(char == "{")
            yield ("start_map" if char == "{" else "start_array"), None
            state = _KEY_OR_END if char == "{" else _VALUE_OR_END
            continue
        elif char == "-" or "0" <= char <= "9":
            while _JSON_NUMBER_RUN.match(text, pos).end() == len(text) and more():
                pass
            match = _JSON_NUMBER.match(text, pos)
            if match is None:
                raise JsonStreamError("Expecting value")
            try:
                number = float(match.group()) if match.group(1) or match.group(2) else int(match.group())
            except ValueError as exc:  # past sys.get_int_max_str_digits(), as json.loads
                raise JsonStreamError(str(exc)) from None
            pos = match.end()
            yield "number", number
        else:
            while len(text) - pos < 5 and more():
                pass
            for word, literal in _JSON_LITERALS:
                if text.startswith(word, pos):
                    pos += len(word)
                    yield ("null" if literal is None else "boolean"), literal
                    break
            else:
                raise JsonStreamError("Expecting value")
        state = _COMMA_OR_END if stack else _VALUE


def _next_event(events: Iterator[tuple[str, Any]]) -> tuple[str, Any]:
    try:
        return next(events)
    except StopIteration:
        raise JsonStreamError("Expecting value") from None


def _build_value(events: Iterator[tuple[str, Any]], event: str, value: Any) -> Any:
    """The value that starts with ``(event, value)``, built like ``json.loads`` builds it."""
    if event not in _CONTAINER_START:
        return float(value) if isinstance(value, Decimal) else value
    builder = ijson.ObjectBuilder()
    builder.event(event, value)
    depth = 1
    for event, value in events:
        builder.event(event, float(value) if isinstance(value, Decimal) else value)
        if event in _CONTAINER_START:
            depth += 1
        elif event in _CONTAINER_END:
            depth -= 1
            if not depth:
                return builder.value
    raise JsonStreamError("Expecting value")


def _skip_value(events: Iterator[tuple[str, Any]], event: str) -> None:
    if event not in _CONTAINER_START:
        return
    depth = 1
    for event, _value in events:
        if event in _CONTAINER_START:
            depth += 1
        elif event in _CONTAINER_END:
            depth -= 1
            if not depth:
                return
    raise JsonStreamError("Expecting value")


@dataclass
class ScannedPayload:
    """What verification reads from one runtime object (``json.loads`` + ``dict.get`` semantics)."""

    is_object: bool
    schema_version: Any = None
    data_version: Any = None
    has_records: bool = False
    records_is_list: bool = False
    record_count: int = 0
    rows: list[Any] | None = None  # per-record summaries of the (last) records array
    # False when yajl's values are not exact (a surrogate escape, a digit run past
    # the int limit, an exponent no ``Decimal`` holds): values come from ``exact=True``.
    values_exact: bool = True


def scan_json_payload(
    binary: BinaryIO,
    *,
    summarize: Callable[[Any], Any] | None = None,
    read_bytes: int = _VERIFY_READ_BYTES,
    exact: bool = False,
) -> ScannedPayload:
    """Stream-parse one JSON document through EOF, keeping one record at a time.

    Top-level members keep ``json.loads`` last-wins semantics. The ``records``
    array is counted and, with ``summarize``, summarised record by record; other
    member values are skipped event by event unless they are
    ``schemaVersion``/``dataVersion``. Invalid JSON raises :class:`JsonStreamError`
    (a ``ValueError``). ``exact=True`` parses with :func:`_exact_basic_parse`,
    for a document whose ``values_exact`` came back False.
    """
    source = _ParserInput(binary, exact=exact)
    if exact:
        events = _exact_basic_parse(source, read_bytes)
    else:
        events = iter(_json_backend().basic_parse(source, buf_size=read_bytes, multiple_values=True))
    with decimal.localcontext(_UNTRAPPED_DECIMAL) as numbers:
        try:
            payload = _scan_document(events, summarize)
            if _next_event(events) != ("string", "") or next(events, None) is not None:
                raise JsonStreamError("Extra data")
        except ijson.JSONError as exc:
            raise JsonStreamError(str(exc) or type(exc).__name__) from None
    if source.forbidden_whitespace:
        raise JsonStreamError("Invalid character (vertical tab or form feed)")
    payload.values_exact = not (
        source.surrogate_escape or source.long_digit_run or numbers.flags[decimal.InvalidOperation]
    )
    return payload


def _scan_document(events: Iterator[tuple[str, Any]], summarize: Callable[[Any], Any] | None) -> ScannedPayload:
    event, _value = _next_event(events)
    if event != "start_map":
        _skip_value(events, event)
        return ScannedPayload(is_object=False)
    payload = ScannedPayload(is_object=True)
    while True:
        event, key = _next_event(events)
        if event == "end_map":
            return payload
        event, value = _next_event(events)
        if key == "records":
            payload.has_records = True
            payload.records_is_list = event == "start_array"
            payload.record_count = 0
            payload.rows = [] if summarize is not None and payload.records_is_list else None
            if not payload.records_is_list:
                _skip_value(events, event)
                continue
            while True:
                event, value = _next_event(events)
                if event == "end_array":
                    break
                payload.record_count += 1
                if payload.rows is not None and summarize is not None:
                    payload.rows.append(summarize(_build_value(events, event, value)))
                else:
                    _skip_value(events, event)
        elif key == "schemaVersion":
            payload.schema_version = _build_value(events, event, value)
        elif key == "dataVersion":
            payload.data_version = _build_value(events, event, value)
        else:
            _skip_value(events, event)


class _HashingReader:
    """Binary reader that hashes and counts every byte read through it."""

    def __init__(self, stream: BinaryIO) -> None:
        self._stream = stream
        self.sha = hashlib.sha256()
        self.size = 0

    def read(self, size: int = -1) -> bytes:
        data = self._stream.read(size)
        self.sha.update(data)
        self.size += len(data)
        return data

    def drain(self) -> None:
        while self.read(_VERIFY_READ_BYTES):
            pass


def _file_digest(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(_VERIFY_READ_BYTES):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def _entry_verify_row(record: Any) -> tuple[Any, str | None, int] | Exception:
    """``(slug, kind, alias-target mismatches)`` of one entry record, or the error reading it raised.

    Same lookups, in the same order, as the historical whole-shard pass; an
    exception is kept (not raised) so it surfaces only where that pass would have.
    """
    try:
        slug = record["slug"]
        hash(slug)
        kind = record["kind"]
        category = kind if kind in ("article", "form_route") else None
        mismatches = 0
        for alias in record.get("aliases") or []:
            if alias.get("target_slug") != slug:
                mismatches += 1
        return slug, category, mismatches
    except Exception as exc:  # replayed verbatim at commit time
        return exc


def verify_tree(out_dir: Path, base_path: str, *, manifest_path: Path | None = None) -> dict[str, Any]:
    current_path = out_dir / base_path / "current.json"
    if manifest_path is None:
        current = json.loads(current_path.read_text(encoding="utf-8"))
        manifest_rel = current["manifestUrl"]
        manifest_path = out_dir / base_path / manifest_rel
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version_root = manifest_path.parent

    errors: list[str] = []

    def check_descriptor(
        descriptor: Mapping[str, Any], *, family: str, summarize: Callable[[Any], Any] | None = None
    ) -> ScannedPayload | None:
        """Stream one object: compressed bytes, gzip integrity, raw bytes, then JSON through EOF."""
        rel = descriptor["url"]
        path = version_root / rel
        if not path.is_file():
            errors.append(f"missing {family} object {rel}")
            return None
        compressed_bytes, compressed_sha = _file_digest(path)
        if compressed_bytes != descriptor["bytes"]:
            errors.append(
                f"{family} {descriptor['id']}: bytes mismatch "
                f"file={compressed_bytes} desc={descriptor['bytes']}"
            )
        if compressed_sha != descriptor["sha256"]:
            errors.append(f"{family} {descriptor['id']}: sha256 mismatch")
        payload: ScannedPayload | None = None
        json_error: ValueError | None = None
        try:
            with path.open("rb") as handle, gzip.GzipFile(fileobj=handle, mode="rb") as inflated:
                raw = _HashingReader(inflated)  # type: ignore[arg-type]
                try:
                    payload = scan_json_payload(raw, summarize=summarize)  # type: ignore[arg-type]
                except ValueError as exc:  # invalid JSON / UTF-8; gzip integrity still decides first
                    json_error = exc
                raw.drain()
            if payload is not None and not payload.values_exact:
                # yajl mis-decodes surrogate escapes and cannot hold every exponent: decode exactly.
                with path.open("rb") as handle, gzip.GzipFile(fileobj=handle, mode="rb") as inflated:
                    try:
                        payload = scan_json_payload(inflated, summarize=summarize, exact=True)  # type: ignore[arg-type]
                    except ValueError as exc:
                        payload, json_error = None, exc
        except (OSError, EOFError, zlib.error) as exc:
            errors.append(f"{family} {descriptor['id']}: gzip decode failed: {exc}")
            return None
        if raw.sha.hexdigest() != descriptor["jsonSha256"]:
            errors.append(f"{family} {descriptor['id']}: jsonSha256 mismatch")
        if raw.size != descriptor["uncompressedBytes"]:
            errors.append(f"{family} {descriptor['id']}: uncompressedBytes mismatch")
        if json_error is not None:
            errors.append(f"{family} {descriptor['id']}: invalid JSON: {json_error}")
            return None
        assert payload is not None
        if family.startswith("deck"):
            if not payload.is_object:
                errors.append(f"{family} {descriptor['id']}: deck payload must be an object")
            return payload
        if not payload.is_object:
            errors.append(f"{family} {descriptor['id']}: payload must be an object")
            return None
        if payload.schema_version != SCHEMA_VERSION:
            errors.append(f"{family} {descriptor['id']}: unsupported schemaVersion")
        if payload.data_version != manifest.get("dataVersion"):
            errors.append(f"{family} {descriptor['id']}: dataVersion mismatch vs manifest")
        if payload.records_is_list and payload.record_count != descriptor["count"]:
            errors.append(
                f"{family} {descriptor['id']}: count mismatch "
                f"records={payload.record_count} desc={descriptor['count']}"
            )
        return payload

    # Every public route appears exactly once across entry shards. These checks
    # run in the same streamed pass but, as before, only count once every object
    # verified: their errors are held apart and a malformed record's exception is
    # raised only after the object checks passed.
    seen_slugs: dict[str, str] = {}
    article_count = 0
    form_count = 0
    entry_errors: list[str] = []
    entry_failure: Exception | None = None

    def commit_entry_rows(shard_id: str, payload: ScannedPayload) -> None:
        nonlocal article_count, form_count, entry_failure
        if entry_failure is not None:
            return
        if not payload.has_records:
            entry_failure = KeyError("records")
            return
        if payload.rows is None:
            entry_failure = ExportError(f"entries {shard_id}: records is not an array")
            return
        for row in payload.rows:
            if isinstance(row, Exception):
                entry_failure = row
                return
            slug, kind, mismatches = row
            if slug in seen_slugs:
                entry_errors.append(f"duplicate slug {slug!r} in {seen_slugs[slug]} and {shard_id}")
            seen_slugs[slug] = shard_id
            if kind == "article":
                article_count += 1
            elif kind == "form_route":
                form_count += 1
            entry_errors.extend([f"alias target mismatch on {slug!r}"] * mismatches)

    entry_shards = manifest["entries"]["shards"]
    for shard_id, descriptor in entry_shards.items():
        scanned = check_descriptor(descriptor, family="entries", summarize=_entry_verify_row)
        if descriptor["bytes"] > DEFAULT_ENTRY_MAX:
            errors.append(f"entries {descriptor['id']}: gzip exceeds 1 MiB")
        if scanned is not None:
            commit_entry_rows(shard_id, scanned)

    for family in ("articles", "aliases"):
        for descriptor in manifest["search"][family]["shards"].values():
            check_descriptor(descriptor, family=f"search.{family}")

    for level, info in (manifest.get("decks", {}).get("levels") or {}).items():
        for part, descriptor in (info.get("parts") or {}).items():
            check_descriptor(descriptor, family=f"decks.{level}.{part}")

    if errors:
        raise ExportError("verify failed:\n- " + "\n- ".join(errors))
    if entry_failure is not None:
        raise entry_failure
    errors.extend(entry_errors)

    expected = manifest["counts"]
    if article_count != expected["articles"]:
        errors.append(f"article count {article_count} != {expected['articles']}")
    if form_count != expected["formRoutes"]:
        errors.append(f"form_of count {form_count} != {expected['formRoutes']}")
    if len(seen_slugs) != expected["publicRoutes"]:
        errors.append(f"route count {len(seen_slugs)} != {expected['publicRoutes']}")

    if errors:
        raise ExportError("verify failed:\n- " + "\n- ".join(errors))
    return {
        "dataVersion": manifest["dataVersion"],
        "articles": article_count,
        "formRoutes": form_count,
        "publicRoutes": len(seen_slugs),
        "entryShards": len(entry_shards),
    }


def _tree_digest(root: Path) -> str:
    """SHA-256 over a tree's ordered relative paths, lengths and bytes.

    Each regular file contributes ``len(path) path len(bytes) bytes`` (8-byte
    big-endian lengths, so no two trees frame alike); anything that is not a
    regular file contributes a distinct marker, so it can never equal a staged tree.
    """
    digest = hashlib.sha256()
    buffer = memoryview(bytearray(1 << 16))
    entries: list[tuple[str, Path]] = []
    for directory, _dirs, files in os.walk(root):
        entries.extend(
            (Path(directory, name).relative_to(root).as_posix(), Path(directory, name)) for name in files
        )
    for relative, path in sorted(entries):
        encoded = relative.encode("utf-8")
        digest.update(struct.pack(">Q", len(encoded)) + encoded)
        if not path.is_file() or path.is_symlink():
            digest.update(b"\xff" + struct.pack(">Q", 0))
            continue
        digest.update(struct.pack(">Q", path.stat().st_size))
        with path.open("rb", buffering=0) as handle:
            while count := handle.readinto(buffer):
                digest.update(buffer[:count])
    return digest.hexdigest()


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@dataclass(frozen=True)
class Publication:
    """A committed ``current.json`` replacement: the export is published.

    ``durability_error`` is set when syncing the pointer's directory failed after
    the replacement. The pointer then resolves (to this tree, or to a later
    publisher's), but whether the rename survives a crash is unconfirmed; the
    pointer on disk is the previous or the new one, never torn, since its bytes
    were synced before the rename.
    """

    manifest_url: str
    durability_error: str | None = None

    @property
    def durable(self) -> bool:
        return self.durability_error is None


class StagedVersion:
    """Hidden staging directory beside the version trees it may join.

    Every object is written here first. Published trees are immutable: nothing is
    ever renamed away, deleted or rewritten once installed under ``versions/``.
    :meth:`publish` installs the staged tree at ``versions/<dataVersion>`` (reusing
    a byte-identical tree already there untouched) or, when that path holds a
    different tree, at ``versions/<dataVersion>-transport-<tree sha256>`` so every
    URL a reader already holds stays valid. ``current.json`` is replaced last and
    atomically, so a process that dies at any point leaves a pointer to a complete
    tree. A failed export leaves the pointer and every installed tree untouched
    and removes the staging tree. The replacement is the commit point: after it
    nothing can fail the export, and nothing restores the old pointer (a
    concurrent publisher may already have moved it on).
    """

    def __init__(self, base_root: Path, data_version: str) -> None:
        self._base_root = base_root
        self._data_version = data_version
        self._versions_dir = base_root / "versions"
        self._versions_dir.mkdir(parents=True, exist_ok=True)
        self._remove_stale(self._versions_dir)
        self._remove_stale_pointers(base_root)
        self._token = f"{os.getpid()}-{uuid.uuid4().hex[:8]}"
        self.root = self._versions_dir / f".export-{self._token}"
        self.root.mkdir()

    @staticmethod
    def _owner_is_dead(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        return False

    @classmethod
    def _remove_stale(cls, versions_dir: Path) -> None:
        """Drop staging trees left behind by exporters that were killed."""
        for path in versions_dir.glob(".export-*"):
            match = re.fullmatch(r"\.export-(\d+)-[0-9a-f]+", path.name)
            if match and path.is_dir() and cls._owner_is_dead(int(match.group(1))):
                shutil.rmtree(path, ignore_errors=True)

    @classmethod
    def _remove_stale_pointers(cls, base_root: Path) -> None:
        """Drop pending ``current.json`` writes left behind by killed exporters."""
        for path in base_root.glob(".current-*.json"):
            match = re.fullmatch(r"\.current-(\d+)-[0-9a-f]+\.json", path.name)
            if match and path.is_file() and cls._owner_is_dead(int(match.group(1))):
                path.unlink(missing_ok=True)

    def open(self, relative: str) -> BinaryIO:
        """New staged object opened for (streamed) binary writing."""
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.open("wb")

    def write(self, relative: str, data: bytes) -> None:
        with self.open(relative) as handle:
            handle.write(data)

    def discard(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _install_as(self, name: str, digest: str) -> bool:
        """Make ``versions/<name>`` hold the staged tree; False if it holds other bytes.

        A destination that appears concurrently is never overwritten: rename onto a
        non-empty directory fails, and the winner is then compared byte for byte.
        """
        target = self._versions_dir / name
        if not target.exists():
            try:
                os.rename(self.root, target)
            except OSError:
                if not target.exists():
                    raise
            else:
                _fsync_dir(self._versions_dir)
                return True
        return target.is_dir() and not target.is_symlink() and _tree_digest(target) == digest

    def install(self) -> str:
        """Install the staged tree; return the name of the version directory to point at."""
        digest = _tree_digest(self.root)
        canonical = self._data_version
        for name in (canonical, f"{canonical}-transport-{digest}"):
            if self._install_as(name, digest):
                return name
        raise ExportError(
            f"transport version {canonical}-transport-{digest} already holds different bytes; "
            "refusing to overwrite a published tree"
        )

    def publish(self, build_current: Callable[[str], bytes]) -> Publication:
        """Install the tree, then atomically point ``current.json`` at it (last step).

        ``build_current`` receives the relative manifest URL of the chosen tree.
        Anything failing up to the replacement (tree install and its directory
        sync, the pending pointer's write and fsync, the rename) raises with the
        pointer untouched. A failed directory sync after it is reported on the
        returned :class:`Publication`, not raised: the export is already published.
        """
        name = self.install()
        manifest_url = f"versions/{name}/manifest.json"
        current_path = self._base_root / "current.json"
        pending = self._base_root / f".current-{self._token}.json"
        try:
            with pending.open("wb") as handle:
                handle.write(build_current(manifest_url))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(pending, current_path)
        except BaseException:
            pending.unlink(missing_ok=True)
            raise
        try:
            _fsync_dir(self._base_root)
        except OSError as exc:
            return Publication(manifest_url, durability_error=f"fsync of {self._base_root} failed: {exc}")
        return Publication(manifest_url)


def export_runtime_shards(
    *,
    db_path: Path,
    out_dir: Path,
    base_path: str = "atlas",
    entry_max_gzip_bytes: int = DEFAULT_ENTRY_MAX,
    entry_target_min_gzip_bytes: int = DEFAULT_ENTRY_TARGET_MIN,
    search_max_gzip_bytes: int = DEFAULT_SEARCH_MAX,
    deck_dir: Path | None = None,
    compression_level: int = DEFAULT_COMPRESSION,
    expected_data_version: str | None = None,
    include_decks: bool = True,
    verify: bool = False,
) -> dict[str, Any]:
    conn = open_readonly_db(db_path)
    try:
        # One read snapshot for the whole export: the replay passes re-read rows.
        conn.execute("BEGIN")
        counts = _site_build_entry_model_gates(conn)
        meta_rows = {
            row["key"]: json.loads(row["value_json"])
            for row in conn.execute(
                "SELECT key, value_json FROM manifest_metadata WHERE key IN ('generated_at', 'version')"
            )
        }
        generated_at = str(meta_rows.get("generated_at") or "")
        if not generated_at:
            raise ExportError("manifest_metadata.generated_at is required")

        practice_levels = load_practice_levels_by_slug(deck_dir if include_decks else None)
        replay = EntryReplay(conn, practice_levels_by_slug=practice_levels)

        # Pass 1: identity hash + compact partition metadata; no record is retained.
        hasher = DataVersionHasher(generated_at=generated_at)
        route_meta: list[tuple[bytes, str]] = []
        article_kinds = 0
        for record in replay.iter_records():
            hasher.add_entry(record)
            route_meta.append((slug_digest(record["slug"]), record["slug"]))
            article_kinds += record["kind"] == "article"
        if len(route_meta) != counts["publicRoutes"]:
            raise ExportError("entry record count drifted from public route count")
        if article_kinds != counts["articles"]:
            raise ExportError("article kind count drifted from reviewed entry count")

        article_index = SearchFamilyIndex.build(
            ((row["s"], row) for row in _iter_article_search_rows(conn)),
            sort_key=_article_sort_key,
            key_fn=_article_index_keys,
            replay=lambda slug: _replay_article_search_row(conn, slug),
        )
        alias_index = SearchFamilyIndex.build(
            _iter_located_alias_search_rows(conn),
            sort_key=_alias_sort_key,
            key_fn=_alias_index_keys,
            replay=lambda rowid: _replay_alias_search_row(conn, rowid),
        )

        deck_index, deck_blobs = register_decks(
            deck_dir if include_decks else None,
            compression_level=compression_level,
        )
        data_version = hasher.finish(
            article_fragments=article_index.iter_fragments(),
            alias_fragments=alias_index.iter_fragments(),
            deck_index=deck_index,
        )
        if expected_data_version is not None and expected_data_version != data_version:
            raise ExportError(
                f"--data-version mismatch: expected {expected_data_version!r}, calculated {data_version!r}"
            )

        base_root = out_dir / base_path
        stage = StagedVersion(base_root, data_version)
        try:
            # Pass 2: replay each accepted leaf straight into the staging tree.
            entry_index, entry_descriptors = build_entry_shards(
                route_meta,
                lambda slug: _fragment_bytes(replay.record_for_slug(slug)),
                data_version=data_version,
                max_gzip_bytes=entry_max_gzip_bytes,
                compression_level=compression_level,
                open_object=stage.open,
            )
            del route_meta
            article_search_index, _ = build_search_family_shards(
                article_index,
                family="articles",
                data_version=data_version,
                max_gzip_bytes=search_max_gzip_bytes,
                compression_level=compression_level,
                schema=SEARCH_ARTICLE_SCHEMA,
                open_object=stage.open,
            )
            alias_search_index, _ = build_search_family_shards(
                alias_index,
                family="aliases",
                data_version=data_version,
                max_gzip_bytes=search_max_gzip_bytes,
                compression_level=compression_level,
                schema=SEARCH_ALIAS_SCHEMA,
                open_object=stage.open,
            )

            # Size band check for non-root leaves on the current corpus.
            leaf_sizes = [desc["bytes"] for desc in entry_descriptors.values()]
            for desc in entry_descriptors.values():
                if desc["bytes"] > entry_max_gzip_bytes:
                    raise ExportError(f"entry shard {desc['id']} exceeds max gzip bytes")

            for key, blob in deck_blobs.items():
                level, part = key.split("/", 1)
                stage.write(f"decks/{level}/{part}.json.gz", blob)

            # Rewrite deck relative URLs already set; ensure practice-index naming in docs example
            # uses practice-index.json.gz style via part name.
            for level, info in (deck_index.get("levels") or {}).items():
                for part, descriptor in (info.get("parts") or {}).items():
                    descriptor["url"] = f"decks/{level}/{part}.json.gz"

            manifest = {
                "schema": MANIFEST_SCHEMA,
                "schemaVersion": SCHEMA_VERSION,
                "dataVersion": data_version,
                "generatedAt": generated_at,
                "normalization": {
                    "unicode": "NFC",
                    "stripCodepoints": ["U+0301"],
                    "localeLower": "uk-UA",
                    "trim": True,
                },
                "counts": {
                    **counts,
                    "searchArticles": len(article_index),
                    "searchAliases": len(alias_index),
                    "entryShards": len(entry_descriptors),
                    "searchArticleShards": len(article_search_index["shards"]),
                    "searchAliasShards": len(alias_search_index["shards"]),
                },
                "limits": {
                    "entryMaxGzipBytes": entry_max_gzip_bytes,
                    "entryTargetMinGzipBytes": entry_target_min_gzip_bytes,
                    "searchMaxGzipBytes": search_max_gzip_bytes,
                    "compressionLevel": compression_level,
                },
                "entries": entry_index,
                "search": {
                    "articles": article_search_index,
                    "aliases": alias_search_index,
                },
                "decks": deck_index,
            }
            stage.write("manifest.json", canonical_json_bytes(manifest))

            report: dict[str, Any] = {
                "dataVersion": data_version,
                "generatedAt": generated_at,
                "counts": manifest["counts"],
                "entryShardBytes": sorted(leaf_sizes),
                "entryShardIds": sorted(entry_descriptors),
                "outDir": str(base_root),
            }
            if verify:
                # Verified before publishing: a bad tree never becomes current.
                report["verify"] = verify_tree(
                    out_dir, base_path, manifest_path=stage.root / "manifest.json"
                )

            def build_current(manifest_url: str) -> bytes:
                return canonical_json_bytes(
                    {
                        "schema": CURRENT_SCHEMA,
                        "schemaVersion": SCHEMA_VERSION,
                        "dataVersion": data_version,
                        "generatedAt": generated_at,
                        "manifestUrl": manifest_url,
                    }
                )

            publication = stage.publish(build_current)
            report["manifestUrl"] = publication.manifest_url
            if not publication.durable:
                report["publication"] = {
                    "committed": True,
                    "durable": False,
                    "error": publication.durability_error,
                }
        finally:
            stage.discard()
        return report
    finally:
        conn.close()


# Transport-only fields that legitimately differ across zlib builds (compressed
# size + compressed-body digest). Logical identity ignores these; jsonSha256 /
# uncompressedBytes remain and still catch payload drift.
_TRANSPORT_FINGERPRINT_KEYS = frozenset({"sha256", "bytes"})


def _strip_transport_fields(value: Any) -> Any:
    """Drop per-object zlib transport fields from manifest/current JSON."""
    if isinstance(value, Mapping):
        return {
            key: _strip_transport_fields(item)
            for key, item in value.items()
            if key not in _TRANSPORT_FINGERPRINT_KEYS
        }
    if isinstance(value, list):
        return [_strip_transport_fields(item) for item in value]
    return value


def _logical_file_payload(path: Path) -> bytes:
    """Bytes hashed for cross-platform content identity of one tree file."""
    if path.name.endswith(".json.gz"):
        try:
            return gzip.decompress(path.read_bytes())
        except (OSError, EOFError, gzip.BadGzipFile) as exc:
            raise ExportError(
                f"undecompressable runtime object (logical fingerprint): {path}"
            ) from exc
    if path.suffix == ".json" or path.name in {"current.json", "manifest.json"}:
        payload = json.loads(path.read_bytes().decode("utf-8"))
        return canonical_json_bytes(_strip_transport_fields(payload))
    return path.read_bytes()


def tree_fingerprint(root: Path) -> str:
    """Raw FILE-BYTE tree fingerprint — same-build determinism only.

    Not a cross-platform contract: zlib builds can emit different gzip bytes for
    identical logical content (burn: PR #5323 CI red, macOS-committed tree vs
    Linux CI). Use ``logical_tree_fingerprint`` for freshness / content identity.
    """
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def logical_tree_fingerprint(root: Path) -> str:
    """Logical CONTENT tree fingerprint — cross-platform identity.

    ``*.json.gz``: hash gunzipped payload. Plain JSON (``current.json``,
    ``manifest.json``): hash after stripping transport fields ``sha256``/``bytes``
    that track zlib output. Same-build raw identity remains ``tree_fingerprint``.
    Burn: PR #5323 CI red, macOS-committed tree vs Linux CI.
    """
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_logical_file_payload(path))
        digest.update(b"\0")
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/atlas.db"))
    parser.add_argument("--out-dir", type=Path, default=Path("build/atlas-runtime"))
    parser.add_argument("--base-path", default="atlas")
    parser.add_argument("--entry-max-gzip-bytes", type=int, default=DEFAULT_ENTRY_MAX)
    parser.add_argument("--entry-target-min-gzip-bytes", type=int, default=DEFAULT_ENTRY_TARGET_MIN)
    parser.add_argument("--search-max-gzip-bytes", type=int, default=DEFAULT_SEARCH_MAX)
    parser.add_argument("--deck-dir", type=Path, default=Path("site/public/lexicon"))
    parser.add_argument("--compression-level", type=int, default=DEFAULT_COMPRESSION)
    parser.add_argument("--data-version", default=None, help="Assert calculated dataVersion")
    parser.add_argument("--no-decks", action="store_true", help="Test-only: skip deck registration")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--verify-only", type=Path, default=None, help="Revalidate an existing manifest")
    parser.add_argument(
        "--capacity-report",
        default=None,
        help="Comma-separated route counts for projection, e.g. 33000,250000",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verify_only is not None:
        result = verify_tree(args.out_dir, args.base_path, manifest_path=args.verify_only)
        print(json.dumps({"verifyOnly": result}, ensure_ascii=False, indent=2))
        return 0

    report = export_runtime_shards(
        db_path=args.db,
        out_dir=args.out_dir,
        base_path=args.base_path,
        entry_max_gzip_bytes=args.entry_max_gzip_bytes,
        entry_target_min_gzip_bytes=args.entry_target_min_gzip_bytes,
        search_max_gzip_bytes=args.search_max_gzip_bytes,
        deck_dir=None if args.no_decks else args.deck_dir,
        compression_level=args.compression_level,
        expected_data_version=args.data_version,
        include_decks=not args.no_decks,
        verify=args.verify,
    )

    if args.capacity_report:
        targets = [int(part.strip()) for part in args.capacity_report.split(",") if part.strip()]
        total_gzip = sum(report["entryShardBytes"])
        report["capacity"] = capacity_report(
            public_routes=report["counts"]["publicRoutes"],
            total_entry_gzip_bytes=total_gzip,
            leaf_count=report["counts"]["entryShards"],
            targets=targets,
        )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if "publication" in report:
        print(
            f"warning: published {report['manifestUrl']}, but its durability is unconfirmed "
            f"({report['publication']['error']}); after a crash current.json may still name "
            "the previous version",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
