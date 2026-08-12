#!/usr/bin/env python3
"""Dump Practice Hub inventory counts for later PRs to re-measure against bars.

Reads local ``practice-index.*.json``, ``practice-zno.*.json``, and the optional
teacher-table deck. Writes ``practice-coverage-report.v1`` JSON (default:
``batch_state/practice/coverage-report.json``). No network.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "practice-coverage-report.v1"
UNIQUE_LEMMA_BAR = 1000
DEFAULT_PRACTICE_DIR = ROOT / "site" / "public" / "lexicon"
DEFAULT_ZNO_DIR = ROOT / "site" / "src" / "data"
DEFAULT_TEACHER_TABLE = ROOT / "site" / "src" / "data" / "lexicon-teacher-table-deck.json"
DEFAULT_JSON_OUT = ROOT / "batch_state" / "practice" / "coverage-report.json"
INDEX_RE = re.compile(r"^practice-index\.(?P<level>[A-C][12])\.json$")
ZNO_RE = re.compile(r"^practice-zno\.(?P<deck>.+)\.json$")
LEVEL_ORDER = ("A1", "A2", "B1", "B2", "C1")


def _lemma_key(item: dict[str, Any]) -> str:
    raw = item.get("lemmaId")
    if raw is None or str(raw).strip() == "":
        raw = item.get("lemma")
    return str(raw or "").strip()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _index_paths(practice_dir: Path) -> list[Path]:
    if not practice_dir.is_dir():
        return []
    paths = [
        path
        for path in sorted(practice_dir.iterdir())
        if path.is_file() and INDEX_RE.match(path.name)
    ]
    return paths


def _zno_paths(zno_dir: Path) -> list[Path]:
    if not zno_dir.is_dir():
        return []
    return [
        path
        for path in sorted(zno_dir.iterdir())
        if path.is_file() and ZNO_RE.match(path.name)
    ]


def collect_mode_inventory(practice_dir: Path) -> dict[str, Any]:
    """Unique lemmas per mode (global + per level) from practice-index shards."""
    by_mode_global: dict[str, set[str]] = defaultdict(set)
    by_mode_level: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    lexemes_by_level: dict[str, int] = {}
    index_files: list[str] = []

    for path in _index_paths(practice_dir):
        match = INDEX_RE.match(path.name)
        assert match is not None
        payload = _load_json(path)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}: expected object")
        level = str(payload.get("level") or match.group("level"))
        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError(f"{path}: items must be a list")
        index_files.append(path.name)
        lexemes_by_level[level] = len(items)
        for item in items:
            if not isinstance(item, dict):
                continue
            key = _lemma_key(item)
            if not key:
                continue
            modes = item.get("modes")
            if not isinstance(modes, list):
                continue
            for mode in modes:
                mode_name = str(mode).strip()
                if not mode_name:
                    continue
                by_mode_global[mode_name].add(key)
                by_mode_level[mode_name][level].add(key)

    modes_out: dict[str, Any] = {}
    for mode in sorted(by_mode_global):
        unique_all = len(by_mode_global[mode])
        by_level = {
            level: len(by_mode_level[mode].get(level, ()))
            for level in LEVEL_ORDER
            if level in by_mode_level[mode]
        }
        # Include any unexpected levels (stable sort after CEFR order).
        for level in sorted(by_mode_level[mode]):
            if level not in by_level:
                by_level[level] = len(by_mode_level[mode][level])
        modes_out[mode] = {
            "unique_lemmas_all_levels": unique_all,
            "below_1000": unique_all < UNIQUE_LEMMA_BAR,
            "by_level": by_level,
        }

    below = sorted(
        mode for mode, row in modes_out.items() if row["below_1000"]
    )

    def _level_section(level: str) -> dict[str, Any]:
        mode_counts = {
            mode: int(row["by_level"].get(level, 0))
            for mode, row in modes_out.items()
            if int(row["by_level"].get(level, 0)) > 0
        }
        ordered = dict(
            sorted(mode_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        )
        return {
            "lexeme_count": int(lexemes_by_level.get(level, 0)),
            "modes": ordered,
        }

    return {
        "index_files": index_files,
        "lexemes_by_level": {
            level: lexemes_by_level[level]
            for level in LEVEL_ORDER
            if level in lexemes_by_level
        }
        | {
            level: count
            for level, count in sorted(lexemes_by_level.items())
            if level not in LEVEL_ORDER
        },
        "modes": modes_out,
        "modes_below_1000": below,
        "b2": _level_section("B2"),
        "c1": _level_section("C1"),
    }


def collect_zno_inventory(zno_dir: Path) -> dict[str, Any]:
    decks: dict[str, Any] = {}
    for path in _zno_paths(zno_dir):
        match = ZNO_RE.match(path.name)
        assert match is not None
        deck_id = match.group("deck")
        payload = _load_json(path)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}: expected object")
        items = payload.get("items")
        if items is None:
            items = []
        if not isinstance(items, list):
            raise ValueError(f"{path}: items must be a list")
        exam_counts = Counter(
            str(item.get("exam") or "unknown")
            for item in items
            if isinstance(item, dict)
        )
        decks[deck_id] = {
            "path": path.name,
            "item_count": len(items),
            "thinDeck": bool(payload.get("thinDeck")) if "thinDeck" in payload else None,
            "exam": dict(sorted(exam_counts.items())),
        }
    return decks


def collect_teacher_table(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"present": False, "path": str(path), "lemma_keys_count": None}
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected object")
    keys = payload.get("lemma_keys")
    if keys is None:
        count = 0
    elif not isinstance(keys, list):
        raise ValueError(f"{path}: lemma_keys must be a list")
    else:
        count = len(keys)
    return {"present": True, "path": path.name, "lemma_keys_count": count}


def build_coverage_report(
    *,
    practice_dir: Path = DEFAULT_PRACTICE_DIR,
    zno_dir: Path = DEFAULT_ZNO_DIR,
    teacher_table: Path = DEFAULT_TEACHER_TABLE,
) -> dict[str, Any]:
    mode_inv = collect_mode_inventory(practice_dir)
    return {
        "schema": SCHEMA,
        "unique_lemma_bar": UNIQUE_LEMMA_BAR,
        "practice_dir": str(practice_dir),
        "zno_dir": str(zno_dir),
        "index_files": mode_inv["index_files"],
        "lexemes_by_level": mode_inv["lexemes_by_level"],
        "modes": mode_inv["modes"],
        "modes_below_1000": mode_inv["modes_below_1000"],
        "b2": mode_inv["b2"],
        "c1": mode_inv["c1"],
        "zno_decks": collect_zno_inventory(zno_dir),
        "teacher_table": collect_teacher_table(teacher_table),
    }


def format_table(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"schema={report.get('schema')}  bar>={report.get('unique_lemma_bar')}")
    lines.append("")
    lines.append("Mode                  Unique  <1000?  A1   A2   B1   B2   C1")
    lines.append("-" * 64)
    modes = report.get("modes") or {}
    for mode, row in sorted(
        modes.items(),
        key=lambda kv: (-int(kv[1].get("unique_lemmas_all_levels", 0)), kv[0]),
    ):
        by_level = row.get("by_level") or {}
        flag = "YES" if row.get("below_1000") else "no"
        lines.append(
            f"{mode:<20} {int(row.get('unique_lemmas_all_levels', 0)):6d}  {flag:<5}  "
            f"{int(by_level.get('A1', 0)):4d} "
            f"{int(by_level.get('A2', 0)):4d} "
            f"{int(by_level.get('B1', 0)):4d} "
            f"{int(by_level.get('B2', 0)):4d} "
            f"{int(by_level.get('C1', 0)):4d}"
        )
    lines.append("")
    lines.append("B2 section:")
    b2 = report.get("b2") or {}
    lines.append(f"  lexemes={b2.get('lexeme_count', 0)}")
    for mode, count in (b2.get("modes") or {}).items():
        lines.append(f"  {mode}: {count}")
    lines.append("C1 section:")
    c1 = report.get("c1") or {}
    lines.append(f"  lexemes={c1.get('lexeme_count', 0)}")
    for mode, count in (c1.get("modes") or {}).items():
        lines.append(f"  {mode}: {count}")
    lines.append("")
    lines.append("ZNO decks:")
    for deck_id, row in sorted((report.get("zno_decks") or {}).items()):
        lines.append(
            f"  {deck_id}: items={row.get('item_count')} thinDeck={row.get('thinDeck')} "
            f"exam={row.get('exam')}"
        )
    teacher = report.get("teacher_table") or {}
    lines.append("")
    if teacher.get("present"):
        lines.append(f"Teacher table keys: {teacher.get('lemma_keys_count')}")
    else:
        lines.append("Teacher table: absent")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--practice-dir", type=Path, default=DEFAULT_PRACTICE_DIR)
    parser.add_argument("--zno-dir", type=Path, default=DEFAULT_ZNO_DIR)
    parser.add_argument("--teacher-table", type=Path, default=DEFAULT_TEACHER_TABLE)
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="Write report JSON (default: batch_state/practice/coverage-report.json).",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing --json-out (stdout only).",
    )
    parser.add_argument(
        "--table",
        action="store_true",
        help="Print a human-readable table to stdout (JSON still written unless --no-write).",
    )
    parser.add_argument(
        "--stdout-json",
        action="store_true",
        help="Print the JSON report to stdout.",
    )
    args = parser.parse_args(argv)

    report = build_coverage_report(
        practice_dir=args.practice_dir,
        zno_dir=args.zno_dir,
        teacher_table=args.teacher_table,
    )
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"

    if not args.no_write:
        out_path: Path = args.json_out
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(serialized, encoding="utf-8")

    if args.table:
        print(format_table(report), end="")
    if args.stdout_json or (args.no_write and not args.table):
        print(serialized, end="")
    elif not args.table and not args.no_write:
        print(f"Wrote {args.json_out}", file=sys.stderr)
        print(format_table(report), end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
