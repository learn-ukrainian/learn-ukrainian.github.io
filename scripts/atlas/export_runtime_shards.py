"""Export versioned Atlas runtime shards (immutable data contract, PR #1).

Deterministic, read-only over ``atlas.db``. Does not deploy, does not change the
live ``/lexicon/<slug>`` route, and never commits the generated tree.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

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


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


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


def slug_hash_bits(slug: str) -> str:
    digest = hashlib.sha256(normalize_slug_for_hash(slug).encode("utf-8")).digest()
    return "".join(f"{byte:08b}" for byte in digest)


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
    rows: Sequence[tuple[str, str]],
) -> dict[str, set[str]]:
    targets: dict[str, set[str]] = defaultdict(set)
    for lookup_text, target_slug in rows:
        key = normalize_atlas_text(lookup_text)
        if key:
            targets[key].add(target_slug)
    return targets


def build_component_link_targets(
    article_rows: Sequence[tuple[str, str]],
    alias_rows: Sequence[tuple[str, str]],
) -> dict[str, str]:
    article_targets = _unique_component_targets(article_rows)
    alias_targets = _unique_component_targets(alias_rows)
    out: dict[str, str] = {}
    for lookup, matched in article_targets.items():
        if len(matched) == 1:
            out[lookup] = next(iter(matched))
    for lookup, matched in alias_targets.items():
        if lookup in article_targets or len(matched) != 1:
            continue
        out[lookup] = next(iter(matched))
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


def load_entry_records(
    conn: sqlite3.Connection,
    *,
    practice_levels_by_slug: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    component_article_rows = conn.execute(
        """SELECT display_head, slug
           FROM articles
           WHERE review_state = 'approved' AND visibility = 'public' AND entry_type = 'lemma'
           ORDER BY display_head COLLATE NOCASE, slug"""
    ).fetchall()
    component_alias_rows = conn.execute(
        """SELECT al.alias, al.target_slug
           FROM aliases al
           JOIN articles a ON a.slug = al.target_slug
           WHERE al.visibility = 'public'
             AND a.review_state = 'approved'
             AND a.visibility = 'public'
             AND a.entry_type = 'lemma'
           ORDER BY al.alias COLLATE NOCASE, al.target_slug, al.kind"""
    ).fetchall()
    component_targets = build_component_link_targets(
        [(row[0], row[1]) for row in component_article_rows],
        [(row[0], row[1]) for row in component_alias_rows],
    )
    lemma_slugs = {
        row[0]
        for row in conn.execute(
            """SELECT slug FROM articles
               WHERE review_state = 'approved' AND visibility = 'public' AND entry_type = 'lemma'"""
        )
    }

    aliases_by_slug: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in conn.execute(
        """SELECT alias, kind, source, target_slug
           FROM aliases
           WHERE visibility = 'public'
           ORDER BY target_slug, kind, alias, source"""
    ):
        aliases_by_slug[row["target_slug"]].append(row)

    relations_by_slug: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in conn.execute(
        """SELECT slug, related_slug, entry_type, relation, component_role, provenance
           FROM related_entries
           ORDER BY slug, relation, related_slug, provenance, component_role"""
    ):
        relations_by_slug[row["slug"]].append(row)

    provenance_by_slug: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in conn.execute(
        """SELECT slug, source_family, source_locator, extraction_mode, rowid
           FROM article_provenance
           ORDER BY slug, rowid"""
    ):
        provenance_by_slug[row["slug"]].append(row)

    payload_rows = conn.execute(
        """SELECT ap.slug AS slug,
                  ap.route_order AS route_order,
                  ap.payload_json AS payload_json,
                  a.entry_type AS entry_type,
                  a.display_head AS display_head,
                  a.lemma AS lemma,
                  a.pos AS pos,
                  a.gloss AS gloss,
                  a.cefr AS cefr,
                  a.heritage_classification AS heritage_classification
           FROM article_payloads ap
           LEFT JOIN articles a ON a.slug = ap.slug
           WHERE ap.is_public_route = 1
           ORDER BY ap.route_order, ap.slug"""
    ).fetchall()

    records: list[dict[str, Any]] = []
    for row in payload_rows:
        entry = json.loads(row["payload_json"])
        if not isinstance(entry, dict):
            raise ExportError(f"payload_json for {row['slug']!r} is not an object")
        # Authoritative entry_type from articles (SSOT). form_of routes → null.
        entry["entry_type"] = row["entry_type"]
        _assert_cefr_consistent(row["slug"], row["cefr"], entry)

        kind = "article" if row["entry_type"] is not None else "form_route"
        slug = str(row["slug"])
        practice_levels = list(
            practice_levels_by_slug.get(slug)
            or practice_levels_by_slug.get(str(entry.get("lemma") or ""))
            or []
        )
        records.append(
            {
                "slug": slug,
                "kind": kind,
                "entry": entry,
                "aliases": _sorted_alias_rows(aliases_by_slug.get(slug, [])),
                "relations": _sorted_relation_rows(relations_by_slug.get(slug, [])),
                "provenance": _sorted_provenance_rows(provenance_by_slug.get(slug, [])),
                "renderContext": {
                    "componentLinks": component_links_for_entry(
                        entry,
                        component_targets=component_targets,
                        lemma_slugs=lemma_slugs,
                    ),
                    "practiceLevels": practice_levels,
                },
            }
        )
    return records


def load_search_rows(conn: sqlite3.Connection) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    article_rows = conn.execute(
        """SELECT slug, display_head, gloss, entry_type, cefr
           FROM articles
           WHERE review_state = 'approved' AND visibility = 'public'
           ORDER BY display_head COLLATE NOCASE, slug"""
    ).fetchall()
    articles: list[dict[str, Any]] = []
    for slug, display_head, gloss, entry_type, cefr in article_rows:
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
        articles.append(row)
    articles.sort(key=lambda row: (normalize_atlas_text(row["l"]), row["s"]))

    alias_rows = conn.execute(
        """SELECT alias.alias, alias.kind, alias.target_slug, article.display_head
           FROM aliases AS alias
           JOIN articles AS article ON article.slug = alias.target_slug
           WHERE alias.visibility = 'public'
             AND article.review_state = 'approved'
             AND article.visibility = 'public'
           ORDER BY alias.alias COLLATE NOCASE, alias.target_slug, alias.kind"""
    ).fetchall()
    aliases: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for alias, kind, target_slug, target_head in alias_rows:
        key = (normalize_atlas_text(alias), target_slug)
        if not key[0] or key in seen:
            continue
        seen.add(key)
        aliases.append({"a": alias, "k": kind, "s": target_slug, "h": target_head})
    aliases.sort(key=lambda row: (normalize_atlas_text(row["a"]), row["s"], row["k"]))
    return articles, aliases


def object_descriptor(
    *,
    object_id: str,
    relative_url: str,
    count: int,
    raw: bytes,
    compressed: bytes,
) -> dict[str, Any]:
    return {
        "id": object_id,
        "url": relative_url,
        "count": count,
        "bytes": len(compressed),
        "uncompressedBytes": len(raw),
        "sha256": sha256_hex(compressed),
        "jsonSha256": sha256_hex(raw),
        "encoding": "gzip",
    }


def build_entry_shards(
    records: Sequence[Mapping[str, Any]],
    *,
    data_version: str,
    max_gzip_bytes: int,
    compression_level: int,
) -> tuple[dict[str, Any], dict[str, bytes], dict[str, dict[str, Any]]]:
    """Adaptive SHA-256 prefix trie over NFC-normalized slug hashes."""

    prepared: list[tuple[str, dict[str, Any]]] = []
    for record in records:
        slug = str(record["slug"])
        prepared.append((slug_hash_bits(slug), dict(record)))
    prepared.sort(key=lambda item: (item[0], item[1]["slug"]))

    shards: dict[str, dict[str, Any]] = {}
    compressed_by_id: dict[str, bytes] = {}
    descriptors: dict[str, dict[str, Any]] = {}

    def materialize(bit_length: int, prefix_value: int, items: list[tuple[str, dict[str, Any]]]) -> None:
        shard_id = entry_shard_id(bit_length, prefix_value)
        ordered = [item[1] for item in sorted(items, key=lambda pair: pair[1]["slug"])]
        payload = {
            "schema": ENTRY_SHARD_SCHEMA,
            "schemaVersion": SCHEMA_VERSION,
            "dataVersion": data_version,
            "records": ordered,
        }
        raw = canonical_json_bytes(payload)
        compressed = gzip_bytes(raw, compression_level=compression_level)
        if len(compressed) > max_gzip_bytes:
            if len(items) <= 1:
                slug = items[0][1]["slug"] if items else "?"
                raise ExportError(
                    f"single entry record exceeds entry-max-gzip-bytes "
                    f"({len(compressed)} > {max_gzip_bytes}) slug={slug!r}"
                )
            next_bit = bit_length
            zeros: list[tuple[str, dict[str, Any]]] = []
            ones: list[tuple[str, dict[str, Any]]] = []
            for bits, record in items:
                if bits[next_bit] == "0":
                    zeros.append((bits, record))
                else:
                    ones.append((bits, record))
            child_bits = bit_length + 1
            if not zeros:
                materialize(child_bits, (prefix_value << 1) | 1, ones)
                return
            if not ones:
                materialize(child_bits, prefix_value << 1, zeros)
                return
            materialize(child_bits, prefix_value << 1, zeros)
            materialize(child_bits, (prefix_value << 1) | 1, ones)
            return

        relative = f"entries/{shard_id}.json.gz"
        shards[shard_id] = payload
        compressed_by_id[shard_id] = compressed
        descriptors[shard_id] = object_descriptor(
            object_id=shard_id,
            relative_url=relative,
            count=len(ordered),
            raw=raw,
            compressed=compressed,
        )

    materialize(0, 0, prepared)

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
    return index, compressed_by_id, descriptors


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
    rows: Sequence[Mapping[str, Any]],
    *,
    family: str,
    data_version: str,
    max_gzip_bytes: int,
    compression_level: int,
    key_fn,
    row_id_fn,
    schema: str,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Adaptive Unicode-prefix trie over indexed keys for one search family."""

    # Map prefix → {row_id → row}; also track exact short-key terminals separately.
    # Start with depth-1 first-character groups (existing strategy).
    depth1: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        for key in key_fn(row):
            chars = list(key)
            if not chars:
                continue
            prefix = chars[0]
            depth1[prefix][row_id_fn(row)] = dict(row)

    shards: dict[str, dict[str, Any]] = {}
    compressed_by_id: dict[str, bytes] = {}
    descriptors: dict[str, dict[str, Any]] = {}
    # tree nodes: {prefix, shardId?, terminalShardId?, children?}
    tree_children: dict[str, Any] = {}

    def write_shard(
        prefix: str,
        row_map: Mapping[str, Mapping[str, Any]],
        *,
        terminal: bool = False,
    ) -> str:
        shard_id = search_shard_id(prefix) + (".term" if terminal else "")
        ordered = sorted(row_map.values(), key=lambda item: (row_id_fn(item), json.dumps(item, sort_keys=True)))
        # Deterministic stable sort by natural key then slug/alias.
        if family == "articles":
            ordered.sort(key=lambda item: (normalize_atlas_text(str(item["l"])), item["s"]))
        else:
            ordered.sort(key=lambda item: (normalize_atlas_text(str(item["a"])), item["s"], item["k"]))
        payload = {
            "schema": schema,
            "schemaVersion": SCHEMA_VERSION,
            "dataVersion": data_version,
            "prefix": prefix,
            "terminal": terminal,
            "records": ordered,
        }
        raw = canonical_json_bytes(payload)
        compressed = gzip_bytes(raw, compression_level=compression_level)
        relative = f"search/{family}/{shard_id}.json.gz"
        shards[shard_id] = payload
        compressed_by_id[shard_id] = compressed
        descriptors[shard_id] = object_descriptor(
            object_id=shard_id,
            relative_url=relative,
            count=len(ordered),
            raw=raw,
            compressed=compressed,
        )
        return shard_id

    def split_or_write(prefix: str, row_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
        ordered = list(row_map.values())
        # Probe gzip size without committing.
        probe_payload = {
            "schema": schema,
            "schemaVersion": SCHEMA_VERSION,
            "dataVersion": data_version,
            "prefix": prefix,
            "terminal": False,
            "records": ordered,
        }
        probe = gzip_bytes(canonical_json_bytes(probe_payload), compression_level=compression_level)
        node: dict[str, Any] = {"prefix": prefix}
        if len(probe) <= max_gzip_bytes:
            shard_id = write_shard(prefix, row_map)
            node["shardId"] = shard_id
            return node

        # Split on next Unicode scalar of each indexed key that lives under this prefix.
        children: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        terminals: dict[str, dict[str, Any]] = {}
        for row in ordered:
            placed = False
            for key in key_fn(row):
                if not key.startswith(prefix):
                    continue
                if key == prefix:
                    terminals[row_id_fn(row)] = row
                    placed = True
                    continue
                next_char = key[len(prefix)]
                child_prefix = prefix + next_char
                children[child_prefix][row_id_fn(row)] = row
                placed = True
            if not placed:
                # Row reached this bucket via a key that equals/extends prefix; keep as terminal.
                terminals[row_id_fn(row)] = row

        if not children:
            # Cannot split further — hard fail if still oversized.
            if len(probe) > max_gzip_bytes:
                raise ExportError(
                    f"search {family} shard for prefix={prefix!r} exceeds max "
                    f"({len(probe)} > {max_gzip_bytes}) and cannot split"
                )
            shard_id = write_shard(prefix, row_map)
            node["shardId"] = shard_id
            return node

        if terminals:
            node["terminalShardId"] = write_shard(prefix, terminals, terminal=True)

        child_nodes: dict[str, Any] = {}
        for child_prefix in sorted(children):
            child_char = child_prefix[len(prefix)]
            child_nodes[child_char] = split_or_write(child_prefix, children[child_prefix])
        node["children"] = child_nodes
        return node

    root_children: dict[str, Any] = {}
    for prefix in sorted(depth1):
        root_children[prefix] = split_or_write(prefix, depth1[prefix])

    index = {
        "strategy": "unicode-prefix-trie",
        "family": family,
        "maxGzipBytes": max_gzip_bytes,
        "tree": {"prefix": "", "children": root_children},
        "shards": {key: descriptors[key] for key in sorted(descriptors)},
    }
    # silence unused
    _ = tree_children
    return index, compressed_by_id


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


def compute_data_version(
    *,
    generated_at: str,
    entry_records: Sequence[Mapping[str, Any]],
    article_rows: Sequence[Mapping[str, Any]],
    alias_rows: Sequence[Mapping[str, Any]],
    deck_index: Mapping[str, Any],
) -> str:
    identity = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": generated_at,
        "entries": [
            {
                "slug": record["slug"],
                "kind": record["kind"],
                "entrySha256": sha256_hex(canonical_json_bytes(record["entry"])),
                "aliasesSha256": sha256_hex(canonical_json_bytes(record["aliases"])),
                "relationsSha256": sha256_hex(canonical_json_bytes(record["relations"])),
                "provenanceSha256": sha256_hex(canonical_json_bytes(record["provenance"])),
                "renderContextSha256": sha256_hex(canonical_json_bytes(record["renderContext"])),
            }
            for record in entry_records
        ],
        "searchArticles": article_rows,
        "searchAliases": alias_rows,
        "decks": {
            level: info.get("deckVersion")
            for level, info in sorted((deck_index.get("levels") or {}).items())
        },
    }
    digest = sha256_hex(canonical_json_bytes(identity))
    return f"atlas-v1-{digest[:16]}"


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


def verify_tree(out_dir: Path, base_path: str, *, manifest_path: Path | None = None) -> dict[str, Any]:
    current_path = out_dir / base_path / "current.json"
    if manifest_path is None:
        current = json.loads(current_path.read_text(encoding="utf-8"))
        manifest_rel = current["manifestUrl"]
        manifest_path = out_dir / base_path / manifest_rel
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version_root = manifest_path.parent

    errors: list[str] = []

    def check_descriptor(descriptor: Mapping[str, Any], *, family: str) -> None:
        rel = descriptor["url"]
        path = version_root / rel
        if not path.is_file():
            errors.append(f"missing {family} object {rel}")
            return
        compressed = path.read_bytes()
        if len(compressed) != descriptor["bytes"]:
            errors.append(
                f"{family} {descriptor['id']}: bytes mismatch "
                f"file={len(compressed)} desc={descriptor['bytes']}"
            )
        if sha256_hex(compressed) != descriptor["sha256"]:
            errors.append(f"{family} {descriptor['id']}: sha256 mismatch")
        try:
            raw = gzip.decompress(compressed)
        except OSError as exc:
            errors.append(f"{family} {descriptor['id']}: gzip decode failed: {exc}")
            return
        if sha256_hex(raw) != descriptor["jsonSha256"]:
            errors.append(f"{family} {descriptor['id']}: jsonSha256 mismatch")
        if len(raw) != descriptor["uncompressedBytes"]:
            errors.append(f"{family} {descriptor['id']}: uncompressedBytes mismatch")
        payload = json.loads(raw.decode("utf-8"))
        if family.startswith("deck"):
            if not isinstance(payload, dict):
                errors.append(f"{family} {descriptor['id']}: deck payload must be an object")
            return
        if payload.get("schemaVersion") != SCHEMA_VERSION:
            errors.append(f"{family} {descriptor['id']}: unsupported schemaVersion")
        if payload.get("dataVersion") != manifest.get("dataVersion"):
            errors.append(f"{family} {descriptor['id']}: dataVersion mismatch vs manifest")
        records = payload.get("records")
        if isinstance(records, list) and len(records) != descriptor["count"]:
            errors.append(
                f"{family} {descriptor['id']}: count mismatch "
                f"records={len(records)} desc={descriptor['count']}"
            )

    entry_shards = manifest["entries"]["shards"]
    for descriptor in entry_shards.values():
        check_descriptor(descriptor, family="entries")
        if descriptor["bytes"] > DEFAULT_ENTRY_MAX:
            errors.append(f"entries {descriptor['id']}: gzip exceeds 1 MiB")

    for family in ("articles", "aliases"):
        for descriptor in manifest["search"][family]["shards"].values():
            check_descriptor(descriptor, family=f"search.{family}")

    for level, info in (manifest.get("decks", {}).get("levels") or {}).items():
        for part, descriptor in (info.get("parts") or {}).items():
            check_descriptor(descriptor, family=f"decks.{level}.{part}")

    if errors:
        raise ExportError("verify failed:\n- " + "\n- ".join(errors))

    # Every public route appears exactly once across entry shards.
    seen_slugs: dict[str, str] = {}
    article_count = 0
    form_count = 0
    for shard_id, descriptor in entry_shards.items():
        raw = gzip.decompress((version_root / descriptor["url"]).read_bytes())
        payload = json.loads(raw.decode("utf-8"))
        for record in payload["records"]:
            slug = record["slug"]
            if slug in seen_slugs:
                errors.append(f"duplicate slug {slug!r} in {seen_slugs[slug]} and {shard_id}")
            seen_slugs[slug] = shard_id
            if record["kind"] == "article":
                article_count += 1
            elif record["kind"] == "form_route":
                form_count += 1
            for alias in record.get("aliases") or []:
                if alias.get("target_slug") != slug:
                    errors.append(f"alias target mismatch on {slug!r}")

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
        entry_records = load_entry_records(conn, practice_levels_by_slug=practice_levels)
        article_rows, alias_rows = load_search_rows(conn)
        if len(entry_records) != counts["publicRoutes"]:
            raise ExportError("entry record count drifted from public route count")
        if sum(1 for r in entry_records if r["kind"] == "article") != counts["articles"]:
            raise ExportError("article kind count drifted from reviewed entry count")

        deck_index, deck_blobs = register_decks(
            deck_dir if include_decks else None,
            compression_level=compression_level,
        )
        data_version = compute_data_version(
            generated_at=generated_at,
            entry_records=entry_records,
            article_rows=article_rows,
            alias_rows=alias_rows,
            deck_index=deck_index,
        )
        if expected_data_version is not None and expected_data_version != data_version:
            raise ExportError(
                f"--data-version mismatch: expected {expected_data_version!r}, calculated {data_version!r}"
            )

        entry_index, entry_blobs, entry_descriptors = build_entry_shards(
            entry_records,
            data_version=data_version,
            max_gzip_bytes=entry_max_gzip_bytes,
            compression_level=compression_level,
        )
        article_search_index, article_search_blobs = build_search_family_shards(
            article_rows,
            family="articles",
            data_version=data_version,
            max_gzip_bytes=search_max_gzip_bytes,
            compression_level=compression_level,
            key_fn=_article_index_keys,
            row_id_fn=lambda row: str(row["s"]),
            schema=SEARCH_ARTICLE_SCHEMA,
        )
        alias_search_index, alias_search_blobs = build_search_family_shards(
            alias_rows,
            family="aliases",
            data_version=data_version,
            max_gzip_bytes=search_max_gzip_bytes,
            compression_level=compression_level,
            key_fn=_alias_index_keys,
            row_id_fn=lambda row: f"{row['a']}\0{row['s']}\0{row['k']}",
            schema=SEARCH_ALIAS_SCHEMA,
        )

        # Size band check for non-root leaves on the current corpus.
        leaf_sizes = [desc["bytes"] for desc in entry_descriptors.values()]
        for desc in entry_descriptors.values():
            if desc["bytes"] > entry_max_gzip_bytes:
                raise ExportError(f"entry shard {desc['id']} exceeds max gzip bytes")

        version_rel = f"versions/{data_version}"
        version_root = out_dir / base_path / version_rel
        if version_root.exists():
            # Deterministic re-export into a clean version directory.
            for path in sorted(version_root.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()

        for shard_id, blob in entry_blobs.items():
            write_bytes(version_root / f"entries/{shard_id}.json.gz", blob)
        for shard_id, blob in article_search_blobs.items():
            write_bytes(version_root / f"search/articles/{shard_id}.json.gz", blob)
        for shard_id, blob in alias_search_blobs.items():
            write_bytes(version_root / f"search/aliases/{shard_id}.json.gz", blob)
        for key, blob in deck_blobs.items():
            level, part = key.split("/", 1)
            write_bytes(version_root / f"decks/{level}/{part}.json.gz", blob)

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
                "searchArticles": len(article_rows),
                "searchAliases": len(alias_rows),
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
        manifest_bytes = canonical_json_bytes(manifest)
        write_bytes(version_root / "manifest.json", manifest_bytes)

        current = {
            "schema": CURRENT_SCHEMA,
            "schemaVersion": SCHEMA_VERSION,
            "dataVersion": data_version,
            "generatedAt": generated_at,
            "manifestUrl": f"{version_rel}/manifest.json",
        }
        write_bytes(out_dir / base_path / "current.json", canonical_json_bytes(current))

        report = {
            "dataVersion": data_version,
            "generatedAt": generated_at,
            "counts": manifest["counts"],
            "entryShardBytes": sorted(leaf_sizes),
            "entryShardIds": sorted(entry_descriptors),
            "outDir": str(out_dir / base_path),
        }
        if verify:
            report["verify"] = verify_tree(out_dir, base_path)
        return report
    finally:
        conn.close()


def tree_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
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
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
