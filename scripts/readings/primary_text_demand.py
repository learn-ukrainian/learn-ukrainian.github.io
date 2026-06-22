#!/usr/bin/env python3
"""Build the primary-text demand manifest from curriculum plan references."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import unicodedata
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_mdx.reading_links import normalize_work_title

LOGGER = logging.getLogger(__name__)

DEFAULT_PLANS_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans"
DEFAULT_OUT = PROJECT_ROOT / "data" / "primary_text_demand.json"
STRESS_MARKS = {"\u0300", "\u0301"}
WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class PrimaryReference:
    """One primary reference selected from one plan."""

    work: str
    author: str
    note: str
    path: str
    slug: str
    track: str
    grade: Any


@dataclass
class RegistryAccumulator:
    """Mutable aggregation bucket for one normalized work/author key."""

    work: str
    author: str
    normalized_key: str
    taught_by: dict[tuple[str, str, str], dict[str, Any]] = field(default_factory=dict)
    note_samples: set[str] = field(default_factory=set)
    paths: set[str] = field(default_factory=set)

    def add(self, ref: PrimaryReference) -> None:
        module_key = (ref.track, ref.slug, _grade_key(ref.grade))
        self.taught_by.setdefault(
            module_key,
            {
                "slug": ref.slug,
                "track": ref.track,
                "grade": ref.grade,
            },
        )
        if ref.note:
            self.note_samples.add(ref.note)
        if ref.path:
            self.paths.add(ref.path)

    def to_json(self) -> dict[str, Any]:
        return {
            "work": self.work,
            "author": self.author,
            "normalized_key": self.normalized_key,
            "taught_by": sorted(
                self.taught_by.values(),
                key=lambda item: (item["track"], item["slug"], _grade_key(item["grade"])),
            ),
            "note_samples": sorted(self.note_samples),
            "paths": sorted(self.paths),
        }


def normalize_author(author: str) -> str:
    """Normalize an author name for registry dedupe."""
    if not author:
        return ""

    decomposed = unicodedata.normalize("NFD", author)
    chars: list[str] = []
    for char in decomposed:
        if char in STRESS_MARKS:
            continue
        if unicodedata.category(char).startswith("P"):
            chars.append(" ")
            continue
        chars.append(char)

    normalized = unicodedata.normalize("NFC", "".join(chars))
    return WHITESPACE_RE.sub(" ", normalized).strip().casefold()


def normalized_key(work: str, author: str) -> str:
    """Return the stable manifest key for a work/author pair."""
    return f"{normalize_work_title(work)}::{normalize_author(author)}"


def build_manifest(plans_dir: Path = DEFAULT_PLANS_DIR, *, track: str | None = None) -> dict[str, Any]:
    """Scan plan YAML files and return the demand manifest payload."""
    refs = collect_primary_references(plans_dir, track=track)
    buckets: dict[str, RegistryAccumulator] = {}
    per_track_counts: Counter[str] = Counter()

    for ref in refs:
        key = normalized_key(ref.work, ref.author)
        if not key.startswith("::"):
            buckets.setdefault(key, RegistryAccumulator(ref.work, ref.author, key)).add(ref)
            per_track_counts[ref.track] += 1

    entries = [bucket.to_json() for _, bucket in sorted(buckets.items())]
    summary = {
        "total_distinct_works": len(entries),
        "total_primary_refs": sum(per_track_counts.values()),
        "per_track_counts": dict(sorted(per_track_counts.items())),
        "works_taught_by_multiple_modules": sum(1 for entry in entries if len(entry["taught_by"]) > 1),
    }
    return {"summary": summary, "entries": entries}


def collect_primary_references(plans_dir: Path, *, track: str | None = None) -> list[PrimaryReference]:
    """Collect valid ``type: primary`` references from plan files."""
    refs: list[PrimaryReference] = []
    for plan_path in _plan_paths(plans_dir, track=track):
        plan = _load_plan(plan_path)
        if plan is None:
            continue
        references = plan.get("references")
        if references is None:
            LOGGER.warning("Skipping %s: no references list", _display_path(plan_path))
            continue
        if not isinstance(references, list):
            LOGGER.warning("Skipping %s: references is not a list", _display_path(plan_path))
            continue

        grade = _grade_hint(plan)
        plan_track = plan_path.parent.name
        slug = plan_path.stem
        for index, item in enumerate(references):
            if not isinstance(item, dict):
                continue
            if item.get("type") != "primary":
                continue
            work = _text_field(item.get("work")) or _text_field(item.get("title"))
            if not work:
                LOGGER.warning("Skipping %s reference %s: primary reference has no work/title", plan_path, index)
                continue
            refs.append(
                PrimaryReference(
                    work=work,
                    author=_text_field(item.get("author")),
                    note=_text_field(item.get("note")),
                    path=_text_field(item.get("path")),
                    slug=slug,
                    track=plan_track,
                    grade=grade,
                )
            )
    return refs


def write_manifest(manifest: dict[str, Any], out_path: Path) -> None:
    """Write the manifest JSON with stable formatting."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def format_summary(summary: dict[str, Any]) -> str:
    """Render the summary block for CLI output."""
    lines = [
        "Primary text demand summary",
        f"total_distinct_works: {summary['total_distinct_works']}",
        f"total_primary_refs: {summary['total_primary_refs']}",
        f"works_taught_by_multiple_modules: {summary['works_taught_by_multiple_modules']}",
        "per_track_counts:",
    ]
    for track, count in summary["per_track_counts"].items():
        lines.append(f"  {track}: {count}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Manifest JSON output path")
    parser.add_argument("--track", help="Only scan plans whose parent directory matches this track")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary to stdout and skip writing the manifest file",
    )
    parser.add_argument("--plans-dir", type=Path, default=DEFAULT_PLANS_DIR, help="Plan YAML root to scan")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="warning: %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest = build_manifest(args.plans_dir, track=args.track)

    if args.summary:
        print(format_summary(manifest["summary"]))
        return 0

    write_manifest(manifest, args.out)
    return 0


def _plan_paths(plans_dir: Path, *, track: str | None) -> list[Path]:
    if not plans_dir.is_dir():
        LOGGER.warning("Skipping %s: plans directory does not exist", _display_path(plans_dir))
        return []
    paths = [
        path
        for path in sorted(plans_dir.rglob("*.yaml"))
        if len(path.relative_to(plans_dir).parts) == 2
    ]
    if track is None:
        return paths
    return [path for path in paths if path.parent.name == track]


def _load_plan(plan_path: Path) -> dict[str, Any] | None:
    try:
        raw = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        LOGGER.warning("Skipping %s: malformed YAML: %s", _display_path(plan_path), exc)
        return None
    except OSError as exc:
        LOGGER.warning("Skipping %s: cannot read file: %s", _display_path(plan_path), exc)
        return None
    if not isinstance(raw, dict):
        LOGGER.warning("Skipping %s: YAML document is not a mapping", _display_path(plan_path))
        return None
    return raw


def _text_field(value: Any) -> str:
    if value is None or isinstance(value, bool | list | dict):
        return ""
    return str(value).strip()


def _grade_hint(plan: dict[str, Any]) -> Any:
    for key in ("grade", "level"):
        if key in plan and plan[key] is not None:
            return plan[key]
    return None


def _grade_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
