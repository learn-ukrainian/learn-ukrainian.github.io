"""Generate compact Word Atlas search and browse indexes."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from scripts.audit.generate_daily_pool import kind_for_source
from scripts.audit.lexeme_filter import is_lexeme_entry
from scripts.etymology.transliterate import transliterate

DEFAULT_MANIFEST = Path("site/src/data/lexicon-manifest.json")
DEFAULT_SEARCH_OUT = Path("site/src/data/lexicon-search-index.json")
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


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _heritage_status(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    enrichment = entry.get("enrichment")
    if isinstance(enrichment, Mapping):
        heritage = enrichment.get("heritage")
        if isinstance(heritage, Mapping):
            return heritage
    status = entry.get("heritage_status")
    if isinstance(status, Mapping):
        return status
    return {}


def _cefr_level(entry: Mapping[str, Any]) -> str | None:
    enrichment = entry.get("enrichment")
    cefr = enrichment.get("cefr") if isinstance(enrichment, Mapping) else None
    level = cefr.get("level") if isinstance(cefr, Mapping) else cefr
    if not isinstance(level, str):
        root_cefr = entry.get("cefr")
        level = root_cefr.get("level") if isinstance(root_cefr, Mapping) else root_cefr
    if not isinstance(level, str):
        return None
    normalized = level.strip().upper()
    return normalized if normalized in CEFR_LEVELS else None


def _first_ukrainian_letter(value: str) -> str | None:
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
    """Return the compact Atlas browse classification code, if any."""

    kind = kind_for_source(entry.get("primary_source"))
    if kind == "avoid":
        return "avoid"

    status = _heritage_status(entry)
    classification = _clean_text(status.get("classification"))
    warning_severity = _clean_text(status.get("warning_severity"))
    is_russianism = status.get("is_russianism") is True

    # An authentic treasured class (archaism/dialect/historism) must NEVER be tagged
    # русизм, even when a stale/hand-edited row also carries warning_severity=russianism_red.
    # Mirrors compute_warning_severity, which gates russianism_red on the same exemption.
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


def _search_row(entry: dict[str, Any]) -> dict[str, Any] | None:
    # Grammar metaterms (pos == "grammar term") are not lemmas; keep them out.
    # is_lexeme_entry already guarantees non-empty lemma + url_slug.
    if not is_lexeme_entry(entry):
        return None

    lemma = entry.get("lemma")
    slug = entry.get("url_slug")
    gloss = entry.get("gloss")
    row = {
        "l": lemma,
        "s": slug,
        "g": gloss if isinstance(gloss, str) else None,
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
        "cls": row["cls"],
        "letter": letter,
    }


def build_index(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [row for entry in entries if (row := _search_row(entry))]
    return sorted(rows, key=lambda row: _uk_sort_key(row["l"]))


def build_browse_outputs(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    letter_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    letter_chip: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    chip_counts: dict[str, int] = defaultdict(int)
    flagged_rows: list[dict[str, Any]] = []

    for row in rows:
        letter = _first_ukrainian_letter(str(row["l"]))
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
    meta = {
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
    }
    flagged_rows = sorted(flagged_rows, key=lambda item: _uk_sort_key(item["l"]))
    return meta, shards, flagged_rows


def write_index(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def write_browse_outputs(
    meta: Mapping[str, Any],
    shards: Mapping[str, list[dict[str, Any]]],
    flagged_rows: list[dict[str, Any]],
    meta_out: Path,
    flagged_out: Path,
    browse_dir: Path,
) -> None:
    meta_out.parent.mkdir(parents=True, exist_ok=True)
    meta_out.write_text(
        json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    flagged_out.parent.mkdir(parents=True, exist_ok=True)
    flagged_out.write_text(
        json.dumps(flagged_rows, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    browse_dir.mkdir(parents=True, exist_ok=True)
    for old_shard in browse_dir.glob("*.json"):
        old_shard.unlink()
    for letter, rows in shards.items():
        (browse_dir / f"{letter}.json").write_text(
            json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_SEARCH_OUT)
    parser.add_argument("--browse-meta-out", type=Path, default=DEFAULT_BROWSE_META_OUT)
    parser.add_argument("--browse-flagged-out", type=Path, default=DEFAULT_BROWSE_FLAGGED_OUT)
    parser.add_argument("--browse-dir", type=Path, default=DEFAULT_BROWSE_DIR)
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be a list")

    rows = build_index(entries)
    meta, shards, flagged_rows = build_browse_outputs(rows)
    write_index(rows, args.out)
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
