#!/usr/bin/env python3
"""Before/after freeze check for Atlas-intake-only runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

WORKFLOW_ID = "atlas_intake_surface_freeze.v1"
DAILY_POOL = Path("site/src/data/lexicon-daily-pool.json")
PRACTICE_DECK_POINTER = Path("site/src/data/lexicon-practice-deck.pointer.json")
PRACTICE_REVIEWED_SOURCES = Path("site/src/data/lexicon-practice-reviewed-sources.json")
CLOZE_SOURCES = Path("site/src/data/lexicon-practice-cloze-sources.json")
HYDRATED_PRACTICE_GLOB = "site/public/lexicon/practice-*.json"


def build_surface_snapshot(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Return hashes and derived counts for frozen learner-facing surfaces."""
    files = _surface_files(project_root)
    file_hashes = {
        _display_path(path, project_root): _file_fingerprint(path) for path in files
    }
    daily_pool = _read_json(project_root / DAILY_POOL)
    practice_pointer = _read_json(project_root / PRACTICE_DECK_POINTER)
    reviewed_sources = _read_json(project_root / PRACTICE_REVIEWED_SOURCES)
    cloze_sources = _read_json(project_root / CLOZE_SOURCES)
    return {
        "workflow": WORKFLOW_ID,
        "surfaces": {
            "daily": {
                "count": len(daily_pool) if isinstance(daily_pool, list) else 0,
                "files": [str(DAILY_POOL)],
            },
            "practice": _practice_surface(practice_pointer),
            "cloze": {
                "source_count": len(cloze_sources) if isinstance(cloze_sources, list) else 0,
                "deck_cloze_count": _practice_cloze_count(practice_pointer),
                "reviewed_source_count": _reviewed_source_count(reviewed_sources),
                "files": [
                    str(PRACTICE_DECK_POINTER),
                    str(PRACTICE_REVIEWED_SOURCES),
                    str(CLOZE_SOURCES),
                ],
            },
        },
        "files": file_hashes,
    }


def compare_snapshots(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare two freeze snapshots."""
    surface_diffs = _mapping_diffs(before.get("surfaces"), after.get("surfaces"), prefix="surfaces")
    file_diffs = _mapping_diffs(before.get("files"), after.get("files"), prefix="files")
    diffs = surface_diffs + file_diffs
    return {
        "workflow": WORKFLOW_ID,
        "ok": not diffs,
        "diffs": diffs,
        "before_surfaces": before.get("surfaces"),
        "after_surfaces": after.get("surfaces"),
    }


def _surface_files(project_root: Path) -> list[Path]:
    tracked = [
        project_root / DAILY_POOL,
        project_root / PRACTICE_DECK_POINTER,
        project_root / PRACTICE_REVIEWED_SOURCES,
        project_root / CLOZE_SOURCES,
    ]
    hydrated = sorted(project_root.glob(HYDRATED_PRACTICE_GLOB))
    return [path for path in [*tracked, *hydrated] if path.exists()]


def _practice_surface(pointer_payload: object) -> dict[str, Any]:
    files = [str(PRACTICE_DECK_POINTER)]
    if not isinstance(pointer_payload, Mapping):
        return {
            "lexeme_count": 0,
            "cloze_count": 0,
            "deck_version": None,
            "package_sha256": None,
            "file_count": 0,
            "files": files,
        }
    pointer_files = pointer_payload.get("files")
    package_files = pointer_files if isinstance(pointer_files, list) else []
    return {
        "lexeme_count": _practice_lexeme_count(pointer_payload),
        "cloze_count": _practice_cloze_count(pointer_payload),
        "deck_version": pointer_payload.get("deck_version"),
        "package_sha256": pointer_payload.get("package_sha256"),
        "file_count": pointer_payload.get("file_count"),
        "files": files,
        "package_files": len(package_files),
    }


def _practice_lexeme_count(pointer_payload: object) -> int:
    return _practice_count(pointer_payload, "lexemes")


def _practice_cloze_count(pointer_payload: object) -> int:
    return _practice_count(pointer_payload, "cloze")


def _practice_count(pointer_payload: object, key: str) -> int:
    if not isinstance(pointer_payload, Mapping):
        return 0
    files = pointer_payload.get("files")
    if not isinstance(files, list):
        return 0
    total = 0
    for row in files:
        if not isinstance(row, Mapping):
            continue
        counts = row.get("counts")
        if isinstance(counts, Mapping) and isinstance(counts.get(key), int):
            total += counts[key]
    return total


def _reviewed_source_count(payload: object) -> int:
    if isinstance(payload, Mapping):
        reviewed = payload.get("reviewed")
        return len(reviewed) if isinstance(reviewed, list) else 0
    if isinstance(payload, list):
        return len(payload)
    return 0


def _file_fingerprint(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping_diffs(before: object, after: object, *, prefix: str) -> list[str]:
    if before == after:
        return []
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        return [prefix]
    diffs: list[str] = []
    for key in sorted(set(before) | set(after)):
        path = f"{prefix}.{key}"
        if key not in before:
            diffs.append(f"{path}: added")
        elif key not in after:
            diffs.append(f"{path}: removed")
        elif before[key] != after[key]:
            if isinstance(before[key], Mapping) and isinstance(after[key], Mapping):
                diffs.extend(_mapping_diffs(before[key], after[key], prefix=path))
            else:
                diffs.append(f"{path}: changed")
    return diffs


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-out", type=Path, help="Write the current snapshot to JSON.")
    parser.add_argument("--compare-to", type=Path, help="Compare current snapshot to a previous snapshot JSON.")
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    current = build_surface_snapshot()
    result: dict[str, Any] = current
    status = 0
    if args.compare_to:
        before = json.loads(args.compare_to.read_text(encoding="utf-8"))
        result = compare_snapshots(before, current)
        status = 0 if result["ok"] else 1
    if args.snapshot_out:
        args.snapshot_out.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot_out.write_text(
            json.dumps(current, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.compare_to:
        if result["ok"]:
            print("Atlas intake freeze OK: Daily/Practice/Cloze surfaces unchanged.")
        else:
            print("Atlas intake freeze failed:")
            for diff in result["diffs"]:
                print(f"- {diff}")
    else:
        surfaces = current["surfaces"]
        print(
            "Atlas intake freeze snapshot: "
            f"{surfaces['daily']['count']} daily words, "
            f"{surfaces['practice']['lexeme_count']} practice lexemes, "
            f"{surfaces['cloze']['source_count']} cloze source rows."
        )
    return status


if __name__ == "__main__":
    raise SystemExit(main())
