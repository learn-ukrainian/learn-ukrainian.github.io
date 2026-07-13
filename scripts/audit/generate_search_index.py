"""Generate compact Word Atlas search and browse indexes.

The database-backed command is deliberately executable as a file with the
system interpreter used by the frontend CI jobs. Keep that path stdlib-only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MANIFEST = Path("site/src/data/lexicon-manifest.json")
DEFAULT_SEARCH_OUT = Path("site/src/data/lexicon-search-index.json")
DEFAULT_SEARCH_ALIASES_OUT = Path("site/src/data/lexicon-search-aliases.json")
DEFAULT_SEARCH_SHARDS_OUT = Path("site/src/data/lexicon-search-shards.json")
DEFAULT_SEARCH_SHARD_DIR: Path | None = None
DEFAULT_BROWSE_META_OUT = Path("site/src/data/lexicon-browse-meta.json")
DEFAULT_BROWSE_FLAGGED_OUT = Path("site/src/data/lexicon-browse-flagged.json")
DEFAULT_BROWSE_DIR = Path("site/public/lexicon/browse")

CEFR_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
UKRAINIAN_ALPHABET = tuple("АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ")
UKRAINIAN_LETTER_SET = set(UKRAINIAN_ALPHABET)
CLASSIFICATION_CODES = ("avoid", "rus", "calq", "arch", "dial", "hist", "borr")
ENTRY_TYPES = (
    "lemma",
    "expression",
    "phraseologism",
    "proverb",
    "multiword_term",
    "proper_name",
)
AUTHENTIC_RUSSIANISM_EXEMPTIONS = {
    "authentic-archaism",
    "dialect",
    "historism",
}
_UK_SORT_ORDER = {letter: index for index, letter in enumerate(UKRAINIAN_ALPHABET)}
_TOKEN_RE = re.compile(r"[\w\u0400-\u04ff]+", re.UNICODE)


def _load_helper_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load helper module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_TRANSLITERATE = _load_helper_module(
    "_atlas_transliterate",
    PROJECT_ROOT / "scripts" / "etymology" / "transliterate.py",
)
transliterate = _TRANSLITERATE.transliterate

_LEXEME_FILTER = _load_helper_module(
    "_atlas_lexeme_filter",
    PROJECT_ROOT / "scripts" / "audit" / "lexeme_filter.py",
)
is_lexeme_entry = _LEXEME_FILTER.is_lexeme_entry
_SURZHYK_SOURCE = _LEXEME_FILTER.SURZHYK_SOURCE


def kind_for_source(source: Any) -> str:
    if isinstance(source, str) and source.startswith("built_vocabulary"):
        return "vyv"
    if source == "plan_required":
        return "obov"
    if source == "plan_recommended":
        return "rek"
    if source == _SURZHYK_SOURCE:
        return "avoid"
    return "other"


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalized_search_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return unicodedata.normalize("NFC", value).replace("\u0301", "").lower()


def _shard_key_for_char(char: str) -> str:
    if len(char) != 1:
        raise ValueError(f"search shard char must be exactly one character, got {char!r}")
    if "a" <= char <= "z":
        return f"latin-{char}"
    if "0" <= char <= "9":
        return f"digit-{char}"
    return f"u{ord(char):04x}"


def _first_token_chars(value: object) -> set[str]:
    normalized = _normalized_search_text(value)
    chars: set[str] = set()
    for token in _TOKEN_RE.findall(normalized):
        if token:
            chars.add(token[0])
    return chars


def _search_shard_chars(row: Mapping[str, Any]) -> set[str]:
    chars = set()
    chars.update(_first_token_chars(row.get("l")))
    chars.update(_first_token_chars(row.get("r")))
    chars.update(_first_token_chars(row.get("g")))
    return chars


def _heritage_status(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    enrichment = entry.get("enrichment")
    if isinstance(enrichment, Mapping):
        heritage = enrichment.get("heritage")
        if isinstance(heritage, Mapping):
            return heritage
    heritage_status = entry.get("heritage_status")
    if isinstance(heritage_status, Mapping):
        return heritage_status
    return {}


def _cefr_level(entry: Mapping[str, Any]) -> str | None:
    enrichment = entry.get("enrichment")
    if isinstance(enrichment, Mapping):
        cefr = enrichment.get("cefr")
        if isinstance(cefr, Mapping):
            level = _clean_text(cefr.get("level"))
            if level and level.strip().upper() in CEFR_LEVELS:
                return level.strip().upper()
    root_cefr = entry.get("cefr")
    if isinstance(root_cefr, Mapping):
        level = _clean_text(root_cefr.get("level"))
        if level and level.strip().upper() in CEFR_LEVELS:
            return level.strip().upper()
    else:
        level = _clean_text(root_cefr)
        if level and level.strip().upper() in CEFR_LEVELS:
            return level.strip().upper()
    return None


def _initial_letter(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    for char in value.strip().upper():
        if char in UKRAINIAN_LETTER_SET:
            return char
        if char.isalpha():
            return None
    return None


def _uk_sort_key(value: object) -> tuple[tuple[int, str], ...]:
    text = str(value or "").strip().upper()
    key: list[tuple[int, str]] = []
    for char in text:
        key.append((_UK_SORT_ORDER.get(char, len(_UK_SORT_ORDER) + ord(char)), char))
    return tuple(key)


def classification_code(entry: Mapping[str, Any]) -> str | None:
    """Return compact Atlas browse classification code, if any."""

    kind = kind_for_source(entry.get("primary_source"))
    if kind == "avoid":
        return "avoid"

    status = _heritage_status(entry)
    classification = _clean_text(status.get("classification"))
    warning_severity = _clean_text(status.get("warning_severity"))
    is_russianism = status.get("is_russianism") is True

    if classification not in AUTHENTIC_RUSSIANISM_EXEMPTIONS and (
        warning_severity == "russianism_red" or is_russianism
    ):
        return "rus"
    if warning_severity == "calque_yellow":
        return "calq"
    if classification == "authentic-archaism":
        return "arch"
    if classification == "dialect":
        return "dial"
    if classification == "historism":
        return "hist"
    if classification == "borrowing":
        return "borr"
    return None


def _translation_gloss(entry: Mapping[str, Any]) -> str | None:
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, Mapping):
        return None
    translation = enrichment.get("translation")
    if not isinstance(translation, Mapping):
        return None
    terms = translation.get("en")
    if not isinstance(terms, list):
        return None
    cleaned = [_clean_text(term) for term in terms]
    visible = [term for term in cleaned if term]
    return "; ".join(visible[:3]) if visible else None


def _search_gloss(entry: Mapping[str, Any]) -> str | None:
    return _clean_text(entry.get("gloss")) or _translation_gloss(entry)


def _search_row(entry: dict[str, Any]) -> dict[str, Any] | None:
    if not is_lexeme_entry(entry):
        return None

    lemma = entry.get("lemma")
    slug = entry.get("url_slug")
    gloss = _search_gloss(entry)
    row = {
        "l": lemma,
        "s": slug,
        "g": gloss,
        "r": transliterate(lemma),
        "k": kind_for_source(entry.get("primary_source")),
    }
    level = _cefr_level(entry)
    if level:
        row["c"] = level
    cls = classification_code(entry)
    if cls:
        row["cls"] = cls
    return row


def _browse_row(row: Mapping[str, Any]) -> dict[str, Any]:
    browse_row = {
        "l": row["l"],
        "s": row["s"],
        "g": row.get("g"),
        "c": row.get("c"),
        "hay": " ".join(
            str(value)
            for value in (row.get("l"), row.get("g"), row.get("r"))
            if isinstance(value, str) and value
        ).lower(),
    }
    cls = row.get("cls")
    if cls:
        browse_row["cls"] = cls
    return browse_row


def _flagged_browse_row(row: Mapping[str, Any], letter: str) -> dict[str, Any]:
    return {
        "l": row["l"],
        "s": row["s"],
        "g": row.get("g"),
        "c": row.get("c"),
        "cls": row.get("cls"),
        "letter": letter,
    }


def build_index(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [_search_row(entry) for entry in entries]
    visible = [row for row in rows if row is not None]
    return sorted(visible, key=lambda row: _uk_sort_key(row["l"]))


def _site_build_entry_model_gates(conn: sqlite3.Connection) -> None:
    """Fail the site artifact build on the entry-model's count/target gates.

    ``atlas_db`` runs the same checks while materializing the database. Repeating
    them here makes both gates part of the site build, so a stale or hand-edited
    database cannot reach a public search artifact without an explicit failure.
    """

    reviewed_entries = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE review_state = 'approved' AND visibility = 'public'"
    ).fetchone()[0]
    public_routes = conn.execute(
        "SELECT COUNT(*) FROM article_payloads WHERE is_public_route = 1"
    ).fetchone()[0]
    form_alias_routes = conn.execute(
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
    if reviewed_entries != public_routes - form_alias_routes or reviewed_entries != routed_reviewed:
        raise ValueError(
            "article_vs_alias_count failure: form_of and alias records must not increment "
            "reviewed entry totals — "
            f"reviewed entries={reviewed_entries}, public routes={public_routes}, "
            f"form_of routes={form_alias_routes}, routed approved-public articles={routed_reviewed}"
        )

    invalid_aliases = conn.execute(
        """SELECT alias.alias, alias.kind, alias.target_slug
           FROM aliases AS alias
           LEFT JOIN articles AS article ON article.slug = alias.target_slug
           WHERE alias.visibility = 'public'
             AND (
                 article.slug IS NULL
                 OR article.review_state != 'approved'
                 OR article.visibility != 'public'
             )
           ORDER BY alias.target_slug, alias.kind, alias.alias"""
    ).fetchall()
    if invalid_aliases:
        details = "; ".join(
            f"alias={alias!r} kind={kind!r} target_slug={target!r}"
            for alias, kind, target in invalid_aliases[:5]
        )
        raise ValueError(
            "alias_target_integrity failure: public aliases must resolve to approved public "
            f"articles ({len(invalid_aliases)} invalid): {details}"
        )


def build_atlas_db_search_artifacts(
    db_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Build public article and alias search artifacts from ``atlas.db`` only.

    Article records are the only rows counted as Atlas entries. Alias records
    retain their own artifact and resolve to an article slug at query time; they
    are deliberately never copied into the article index.
    """

    conn = sqlite3.connect(db_path)
    try:
        _site_build_entry_model_gates(conn)
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
        articles.sort(key=lambda row: _uk_sort_key(row["l"]))

        # The schema permits the same approved alias for a target through
        # different kinds. Public search needs one resolver row per normalized
        # alias+target pair, with deterministic kind selection.
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
        seen_alias_targets: set[tuple[str, str]] = set()
        for alias, kind, target_slug, target_head in alias_rows:
            key = (_normalized_search_text(alias), target_slug)
            if not key[0] or key in seen_alias_targets:
                continue
            seen_alias_targets.add(key)
            aliases.append(
                {
                    "a": alias,
                    "k": kind,
                    "s": target_slug,
                    "h": target_head,
                }
            )
        aliases.sort(key=lambda row: (_uk_sort_key(row["a"]), row["s"], row["k"]))

        by_type = {entry_type: 0 for entry_type in ENTRY_TYPES}
        by_type.update(
            {
                entry_type: count
                for entry_type, count in conn.execute(
                    """SELECT entry_type, COUNT(*)
                       FROM articles
                       WHERE review_state = 'approved' AND visibility = 'public'
                       GROUP BY entry_type"""
                )
            }
        )
        public_alias_records = conn.execute(
            "SELECT COUNT(*) FROM aliases WHERE visibility = 'public'"
        ).fetchone()[0]
        return articles, aliases, {
            "reviewed_entries": len(articles),
            "public_alias_records": public_alias_records,
            "emitted_aliases": len(aliases),
            "deduplicated_aliases": public_alias_records - len(aliases),
            **{f"entry_type_{entry_type}": count for entry_type, count in by_type.items()},
        }
    finally:
        conn.close()


def build_search_shards(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    shard_rows: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    prefix_map: dict[str, str] = {}
    for row in rows:
        for char in _search_shard_chars(row):
            key = _shard_key_for_char(char)
            prefix_map[char] = key
            shard_rows[key][str(row["s"])] = row

    shards = {
        key: sorted(slug_rows.values(), key=lambda row: _uk_sort_key(row["l"]))
        for key, slug_rows in sorted(shard_rows.items())
    }
    shard_meta: dict[str, dict[str, Any]] = {}
    for key, shard in shards.items():
        data = _json_bytes(shard)
        shard_meta[key] = {
            "path": f"/lexicon/search/{key}.json",
            "count": len(shard),
            "bytes": len(data),
            "sha256": _sha256(data),
        }

    full_index = _json_bytes(rows)
    return {
        "schema": "atlas-search-shards",
        "schemaVersion": 1,
        "strategy": "first-normalized-token-character",
        "total": len(rows),
        "fullIndex": {
            "path": "/lexicon/search-index.json",
            "count": len(rows),
            "bytes": len(full_index),
            "sha256": _sha256(full_index),
        },
        "shardCount": len(shards),
        "prefixMap": dict(sorted(prefix_map.items(), key=lambda item: item[0])),
        "shards": shard_meta,
    }, shards


def build_browse_outputs(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    letter_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    chip_counts: defaultdict[str, int] = defaultdict(int)
    letter_chip: dict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    flagged_rows: list[dict[str, Any]] = []

    for row in rows:
        letter = _initial_letter(row.get("l"))
        if not letter:
            continue
        browse_row = _browse_row(row)
        letter_rows[letter].append(browse_row)
        cls = browse_row.get("cls")
        if isinstance(cls, str):
            chip_counts[cls] += 1
            letter_chip[letter][cls] += 1
            flagged_rows.append(_flagged_browse_row(row, letter))

    shards = {
        letter: sorted(items, key=lambda item: _uk_sort_key(item["l"]))
        for letter, items in sorted(letter_rows.items(), key=lambda item: _uk_sort_key(item[0]))
    }
    browse_shards: dict[str, dict[str, Any]] = {}
    for letter, items in shards.items():
        data = _json_bytes(items)
        browse_shards[letter] = {
            "path": f"/lexicon/browse/{letter}.json",
            "count": len(items),
            "bytes": len(data),
            "sha256": _sha256(data),
        }

    meta = {
        "schema": "atlas-browse-meta",
        "schemaVersion": 1,
        "total": sum(len(items) for items in shards.values()),
        "letterCounts": {
            letter: len(shards.get(letter, [])) for letter in UKRAINIAN_ALPHABET
        },
        "chipCounts": {
            code: chip_counts[code]
            for code in CLASSIFICATION_CODES
            if chip_counts.get(code, 0) > 0
        },
        "letterChip": {
            letter: {
                code: letter_chip[letter].get(code, 0)
                for code in CLASSIFICATION_CODES
            }
            for letter in UKRAINIAN_ALPHABET
        },
        "browseShardCount": len(browse_shards),
        "browseShards": browse_shards,
    }
    flagged_rows = sorted(flagged_rows, key=lambda item: _uk_sort_key(item["l"]))
    return meta, shards, flagged_rows


def write_index(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(_json_bytes(rows))


def write_aliases(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(_json_bytes(rows))


def write_search_shards(
    payload: Mapping[str, Any],
    shards: Mapping[str, list[dict[str, Any]]],
    out_path: Path,
    shard_dir: Path | None,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(_json_bytes(payload))
    if shard_dir is None:
        return

    shard_dir.mkdir(parents=True, exist_ok=True)
    for old_shard in shard_dir.glob("*.json"):
        old_shard.unlink()
    for key, rows in shards.items():
        (shard_dir / f"{key}.json").write_bytes(_json_bytes(rows))


def write_browse_outputs(
    meta: Mapping[str, Any],
    shards: Mapping[str, list[dict[str, Any]]],
    flagged_rows: list[dict[str, Any]],
    meta_out: Path,
    flagged_out: Path,
    browse_dir: Path,
) -> None:
    meta_out.parent.mkdir(parents=True, exist_ok=True)
    meta_out.write_bytes(_json_bytes(meta))
    flagged_out.parent.mkdir(parents=True, exist_ok=True)
    flagged_out.write_bytes(_json_bytes(flagged_rows))

    browse_dir.mkdir(parents=True, exist_ok=True)
    for old_shard in browse_dir.glob("*.json"):
        old_shard.unlink()
    for letter, rows in shards.items():
        (browse_dir / f"{letter}.json").write_bytes(_json_bytes(rows))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--db",
        type=Path,
        help="Build public search artifacts from atlas.db instead of the legacy manifest.",
    )
    parser.add_argument(
        "--browse-only",
        action="store_true",
        help="Refresh legacy browse artifacts without overwriting DB-backed search artifacts.",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_SEARCH_OUT)
    parser.add_argument("--aliases-out", type=Path, default=DEFAULT_SEARCH_ALIASES_OUT)
    parser.add_argument("--search-shards-out", type=Path, default=DEFAULT_SEARCH_SHARDS_OUT)
    parser.add_argument("--search-shard-dir", type=Path, default=DEFAULT_SEARCH_SHARD_DIR)
    parser.add_argument("--browse-meta-out", type=Path, default=DEFAULT_BROWSE_META_OUT)
    parser.add_argument("--browse-flagged-out", type=Path, default=DEFAULT_BROWSE_FLAGGED_OUT)
    parser.add_argument("--browse-dir", type=Path, default=DEFAULT_BROWSE_DIR)
    args = parser.parse_args(argv)

    if args.db is not None and args.browse_only:
        parser.error("--browse-only cannot be combined with --db")

    if args.db is not None:
        rows, aliases, counts = build_atlas_db_search_artifacts(args.db)
        search_shards, search_shard_rows = build_search_shards(rows)
        write_index(rows, args.out)
        write_aliases(aliases, args.aliases_out)
        write_search_shards(
            search_shards,
            search_shard_rows,
            args.search_shards_out,
            args.search_shard_dir,
        )
        print(
            "atlas search artifacts: "
            f"reviewed_articles={counts['reviewed_entries']} "
            f"public_alias_records={counts['public_alias_records']} "
            f"emitted_aliases={counts['emitted_aliases']} "
            f"alias_deduplication={counts['deduplicated_aliases']}"
        )
        return 0

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be list")

    rows = build_index(entries)
    meta, shards, flagged_rows = build_browse_outputs(rows)
    if not args.browse_only:
        search_shards, search_shard_rows = build_search_shards(rows)
        write_index(rows, args.out)
        write_search_shards(search_shards, search_shard_rows, args.search_shards_out, args.search_shard_dir)
    write_browse_outputs(
        meta,
        shards,
        flagged_rows,
        args.browse_meta_out,
        args.browse_flagged_out,
        args.browse_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
