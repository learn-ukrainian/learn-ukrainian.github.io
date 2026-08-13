#!/usr/bin/env python3
"""Inventory unused attested thin-mode practice sources vs live shards.

Reports, for synonym / antonym / paronym / homonym:

- attested source pair count
- unique lemmas if all source pairs were emitted
- unique lemmas in current practice shards
- unused attested pairs still not in shards
- whether ≥1000 unique lemmas is possible from current attested files

Does not invent pairs, regenerate decks, or touch heritage sources.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "thin-mode-source-inventory.v1"
UNIQUE_LEMMA_BAR = 1000
THIN_MODES = ("synonym", "antonym", "paronym", "homonym")

DEFAULT_PRACTICE_DIR = ROOT / "site" / "public" / "lexicon"
DEFAULT_SYNONYM_VERDICTS = ROOT / "data" / "lexicon" / "synonym_pair_verdicts.yaml"
DEFAULT_ANTONYM_PAIRS = ROOT / "data" / "lexicon" / "antonym_pairs.yaml"
DEFAULT_PARONYM_PAIRS = ROOT / "data" / "lexicon" / "paronym_pairs.yaml"
DEFAULT_HOMONYM_PAIRS = ROOT / "data" / "lexicon" / "homonym_pairs.yaml"

MODE_SHARD_RE = {
    "synonym": "practice-synonym.*.json",
    "antonym": "practice-antonym.*.json",
    "paronym": "practice-paronym.*.json",
    "homonym": "practice-homonym.*.json",
}
INDEX_GLOB = "practice-index.*.json"


def _plain(value: Any) -> str:
    text = str(value or "")
    return (
        text.casefold()
        .replace("\u0301", "")
        .replace("́", "")
        .replace("’", "'")
        .replace("ʼ", "'")
        .strip()
    )


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _synonym_pair_key(a: Any, b: Any, polarity: Any) -> tuple[str, str, str]:
    left = _plain(a)
    right = _plain(b)
    if left > right:
        left, right = right, left
    return (left, right, _plain(polarity))


def _pair_leg_key(slug_a: Any, slug_b: Any) -> frozenset[str]:
    return frozenset({_plain(slug_a), _plain(slug_b)})


def _lemma_from_item(item: dict[str, Any]) -> str:
    raw = item.get("lemmaId")
    if raw is None or str(raw).strip() == "":
        raw = item.get("lemma")
    return _plain(raw)


def _lemmas_from_mode_item(mode: str, item: dict[str, Any]) -> set[str]:
    lemmas: set[str] = set()
    primary = _lemma_from_item(item)
    if primary:
        lemmas.add(primary)
    if mode == "synonym":
        target = _plain(item.get("targetLemmaId"))
        if target:
            lemmas.add(target)
    return lemmas


def load_synonym_attested_pairs(path: Path) -> list[tuple[str, str, str]]:
    """Approved synonym-verdict pairs (both polarities feed the synonym deck)."""
    if not path.is_file():
        raise FileNotFoundError(f"synonym verdicts not found: {path}")
    payload = _load_yaml(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected mapping with approved list")
    out: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in payload.get("approved") or []:
        if not isinstance(row, dict):
            continue
        a = _plain(row.get("a"))
        b = _plain(row.get("b"))
        polarity = _plain(row.get("polarity"))
        if not a or not b or not polarity:
            continue
        key = _synonym_pair_key(a, b, polarity)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def load_curated_attested_pairs(path: Path) -> list[tuple[frozenset[str], str]]:
    """Curated antonym/paronym/homonym pairs keyed by legs + distinction gloss."""
    if not path.is_file():
        raise FileNotFoundError(f"pair YAML not found: {path}")
    payload = _load_yaml(path) or []
    rows = payload.get("pairs") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError(f"{path}: expected list or object with pairs list")
    out: list[tuple[frozenset[str], str]] = []
    seen: set[tuple[frozenset[str], str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        slug_a = _plain(row.get("slugA"))
        slug_b = _plain(row.get("slugB"))
        gloss = _plain(row.get("distinction_gloss_uk"))
        if not slug_a or not slug_b or not gloss:
            continue
        key = (_pair_leg_key(slug_a, slug_b), gloss)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _iter_mode_items(practice_dir: Path, mode: str) -> list[dict[str, Any]]:
    if not practice_dir.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(practice_dir.glob(MODE_SHARD_RE[mode])):
        if not path.is_file():
            continue
        payload = _load_json(path)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}: expected object")
        rows = payload.get(mode)
        if rows is None:
            rows = payload.get("items")
        if rows is None:
            continue
        if not isinstance(rows, list):
            raise ValueError(f"{path}: {mode}/items must be a list")
        for row in rows:
            if isinstance(row, dict):
                items.append(row)
    return items


def _lemmas_from_index(practice_dir: Path, mode: str) -> set[str]:
    """Fallback lemma set from practice-index.*.json mode membership."""
    if not practice_dir.is_dir():
        return set()
    lemmas: set[str] = set()
    for path in sorted(practice_dir.glob(INDEX_GLOB)):
        if not path.is_file():
            continue
        payload = _load_json(path)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}: expected object")
        rows = payload.get("items")
        if not isinstance(rows, list):
            raise ValueError(f"{path}: items must be a list")
        for item in rows:
            if not isinstance(item, dict):
                continue
            modes = item.get("modes")
            if not isinstance(modes, list):
                continue
            if mode not in {str(m).strip() for m in modes}:
                continue
            key = _lemma_from_item(item)
            if key:
                lemmas.add(key)
    return lemmas


def collect_shard_state(
    practice_dir: Path,
    mode: str,
    *,
    prefer_index: bool = False,
) -> dict[str, Any]:
    items = _iter_mode_items(practice_dir, mode)
    shard_lemmas: set[str] = set()
    for item in items:
        shard_lemmas.update(_lemmas_from_mode_item(mode, item))
    index_lemmas = _lemmas_from_index(practice_dir, mode)
    source = "mode-shards"
    if prefer_index or (not items and index_lemmas):
        shard_lemmas = index_lemmas
        source = "practice-index" if prefer_index or not items else source
    synonym_pairs: set[tuple[str, str, str]] = set()
    glosses: set[str] = set()
    for item in items:
        gloss = _plain(item.get("distinction_gloss_uk"))
        if gloss:
            glosses.add(gloss)
        if mode == "synonym":
            lemma = item.get("lemmaId")
            target = item.get("targetLemmaId")
            polarity = item.get("polarity")
            if lemma and target and polarity:
                synonym_pairs.add(_synonym_pair_key(lemma, target, polarity))
    return {
        "item_count": len(items),
        "unique_lemmas": shard_lemmas,
        "synonym_pairs": synonym_pairs,
        "glosses": glosses,
        "lemma_source": source,
        "shard_files_present": bool(items) or bool(index_lemmas),
    }


def _unique_from_synonym_pairs(pairs: list[tuple[str, str, str]]) -> set[str]:
    lemmas: set[str] = set()
    for a, b, _polarity in pairs:
        lemmas.add(a)
        lemmas.add(b)
    return lemmas


def _unique_from_curated_pairs(pairs: list[tuple[frozenset[str], str]]) -> set[str]:
    lemmas: set[str] = set()
    for legs, _gloss in pairs:
        lemmas.update(legs)
    return lemmas


def inventory_mode(
    mode: str,
    *,
    attested_pairs: list[Any],
    shard: dict[str, Any],
) -> dict[str, Any]:
    if mode == "synonym":
        pairs = list(attested_pairs)
        attested_count = len(pairs)
        source_lemmas = _unique_from_synonym_pairs(pairs)
        used = sum(1 for key in pairs if key in shard["synonym_pairs"])
    else:
        pairs = list(attested_pairs)
        attested_count = len(pairs)
        source_lemmas = _unique_from_curated_pairs(pairs)
        used = sum(1 for _legs, gloss in pairs if gloss in shard["glosses"])

    unused = attested_count - used
    shard_unique = len(shard["unique_lemmas"])
    source_unique = len(source_lemmas)
    return {
        "mode": mode,
        "attested_pair_count": attested_count,
        "unique_lemmas_if_all_emitted": source_unique,
        "unique_lemmas_in_shards": shard_unique,
        "unused_attested_pairs": unused,
        "used_attested_pairs": used,
        "possible_ge_1000_from_attested": source_unique >= UNIQUE_LEMMA_BAR,
        "lemma_source": shard["lemma_source"],
        "shard_item_count": shard["item_count"],
        "shard_files_present": shard["shard_files_present"],
    }


def build_inventory(
    *,
    practice_dir: Path = DEFAULT_PRACTICE_DIR,
    synonym_verdicts: Path = DEFAULT_SYNONYM_VERDICTS,
    antonym_pairs: Path = DEFAULT_ANTONYM_PAIRS,
    paronym_pairs: Path = DEFAULT_PARONYM_PAIRS,
    homonym_pairs: Path = DEFAULT_HOMONYM_PAIRS,
    prefer_index: bool = False,
) -> dict[str, Any]:
    attested = {
        "synonym": load_synonym_attested_pairs(synonym_verdicts),
        "antonym": load_curated_attested_pairs(antonym_pairs),
        "paronym": load_curated_attested_pairs(paronym_pairs),
        "homonym": load_curated_attested_pairs(homonym_pairs),
    }
    modes: dict[str, Any] = {}
    for mode in THIN_MODES:
        shard = collect_shard_state(practice_dir, mode, prefer_index=prefer_index)
        modes[mode] = inventory_mode(mode, attested_pairs=attested[mode], shard=shard)
    return {
        "schema": SCHEMA,
        "unique_lemma_bar": UNIQUE_LEMMA_BAR,
        "practice_dir": str(practice_dir),
        "sources": {
            "synonym": str(synonym_verdicts),
            "antonym": str(antonym_pairs),
            "paronym": str(paronym_pairs),
            "homonym": str(homonym_pairs),
        },
        "modes": modes,
    }


def format_table(report: dict[str, Any]) -> str:
    bar = int(report.get("unique_lemma_bar") or UNIQUE_LEMMA_BAR)
    lines = [
        f"schema={report.get('schema')}  bar>={bar}",
        "",
        "Mode       Attested  SrcLemmas  ShardLemmas  Unused  ≥1000 possible?",
        "-" * 72,
    ]
    modes = report.get("modes") or {}
    for mode in THIN_MODES:
        row = modes.get(mode) or {}
        possible = "YES" if row.get("possible_ge_1000_from_attested") else "no"
        lines.append(
            f"{mode:<10} {int(row.get('attested_pair_count', 0)):8d}  "
            f"{int(row.get('unique_lemmas_if_all_emitted', 0)):9d}  "
            f"{int(row.get('unique_lemmas_in_shards', 0)):11d}  "
            f"{int(row.get('unused_attested_pairs', 0)):6d}  {possible}"
        )
    lines.append("")
    lines.append(f"practice_dir={report.get('practice_dir')}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--practice-dir", type=Path, default=DEFAULT_PRACTICE_DIR)
    parser.add_argument("--synonym-verdicts", type=Path, default=DEFAULT_SYNONYM_VERDICTS)
    parser.add_argument("--antonym-pairs", type=Path, default=DEFAULT_ANTONYM_PAIRS)
    parser.add_argument("--paronym-pairs", type=Path, default=DEFAULT_PARONYM_PAIRS)
    parser.add_argument("--homonym-pairs", type=Path, default=DEFAULT_HOMONYM_PAIRS)
    parser.add_argument(
        "--prefer-index",
        action="store_true",
        help="Count shard lemmas from practice-index.*.json instead of mode shards.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write the inventory JSON.",
    )
    parser.add_argument(
        "--stdout-json",
        action="store_true",
        help="Print the JSON report to stdout.",
    )
    parser.add_argument(
        "--table",
        action="store_true",
        default=True,
        help="Print the human-readable table (default).",
    )
    parser.add_argument(
        "--no-table",
        action="store_true",
        help="Suppress the human-readable table.",
    )
    args = parser.parse_args(argv)

    report = build_inventory(
        practice_dir=args.practice_dir,
        synonym_verdicts=args.synonym_verdicts,
        antonym_pairs=args.antonym_pairs,
        paronym_pairs=args.paronym_pairs,
        homonym_pairs=args.homonym_pairs,
        prefer_index=args.prefer_index,
    )
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(serialized, encoding="utf-8")

    show_table = args.table and not args.no_table
    if show_table:
        print(format_table(report), end="")
    if args.stdout_json or (args.no_table and not show_table):
        print(serialized, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
