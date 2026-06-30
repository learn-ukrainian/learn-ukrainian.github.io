"""Generate compact Word Atlas search and browse indexes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.etymology.transliterate import transliterate

DEFAULT_MANIFEST = Path("site/src/data/lexicon-manifest.json")
DEFAULT_SEARCH_OUT = Path("site/src/data/lexicon-search-index.json")
DEFAULT_SEARCH_SHARDS_OUT = Path("site/src/data/lexicon-search-shards.json")
DEFAULT_SEARCH_SHARD_DIR: Path | None = None
DEFAULT_BROWSE_META_OUT = Path("site/src/data/lexicon-browse-meta.json")
DEFAULT_BROWSE_FLAGGED_OUT = Path("site/src/data/lexicon-browse-flagged.json")
DEFAULT_BROWSE_DIR = Path("site/public/lexicon/browse")

CEFR_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
UKRAINIAN_ALPHABET = tuple("АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ")
UKRAINIAN_LETTER_SET = set(UKRAINIAN_ALPHABET)
CLASSIFICATION_CODES = ("avoid", "rus", "calq", "arch", "dial", "hist", "borr")
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
    parser.add_argument("--out", type=Path, default=DEFAULT_SEARCH_OUT)
    parser.add_argument("--search-shards-out", type=Path, default=DEFAULT_SEARCH_SHARDS_OUT)
    parser.add_argument("--search-shard-dir", type=Path, default=DEFAULT_SEARCH_SHARD_DIR)
    parser.add_argument("--browse-meta-out", type=Path, default=DEFAULT_BROWSE_META_OUT)
    parser.add_argument("--browse-flagged-out", type=Path, default=DEFAULT_BROWSE_FLAGGED_OUT)
    parser.add_argument("--browse-dir", type=Path, default=DEFAULT_BROWSE_DIR)
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be list")

    rows = build_index(entries)
    search_shards, search_shard_rows = build_search_shards(rows)
    meta, shards, flagged_rows = build_browse_outputs(rows)
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
