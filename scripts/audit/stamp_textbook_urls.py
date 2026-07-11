#!/usr/bin/env python3
"""Stamp public read-online URLs onto `role: textbook` resource citations.

Textbook resources cite a school textbook via ``source_ref:
docs/references/private/textbooks-txt/<file>.txt`` (internal, load-bearing provenance) and,
historically, carry no ``url`` — so the learner surface shows only a title. This tool
adds a ``url:`` (from ``docs/references/textbook-urls.yaml``, keyed by the .txt filename
stem) so the renderer emits a clickable citation. Idempotent: an entry that already has
a ``url`` is left untouched, and a source_ref with no mapping is reported, not guessed.

Line-based (like the sibling strip/fix tools) to keep the diff surgical and formatting
intact. Reusable across every level (a2, seminars, … cite the same textbooks).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
URL_MAP_PATH = PROJECT_ROOT / "docs" / "references" / "textbook-urls.yaml"

_TEXTBOOK_REF_RE = re.compile(
    r"^(?P<indent>\s+)source_ref:\s*[\"']?docs/references/private/textbooks-txt/(?P<stem>[^\"'\s]+?)\.txt[\"']?\s*$"
)
_URL_LINE_RE = re.compile(r"^\s+url:\s*\S")
_ENTRY_START_RE = re.compile(r"^-\s")


def load_url_map() -> dict[str, str]:
    data = yaml.safe_load(URL_MAP_PATH.read_text(encoding="utf-8")) or {}
    return {str(k): str(v) for k, v in data.items()}


def _entry_has_url(lines: list[str], source_ref_index: int) -> bool:
    """Scan the entry block containing ``source_ref_index`` for an existing url line."""
    start = source_ref_index
    while start > 0 and not _ENTRY_START_RE.match(lines[start]):
        start -= 1
    end = source_ref_index + 1
    while end < len(lines) and not _ENTRY_START_RE.match(lines[end]):
        end += 1
    return any(_URL_LINE_RE.match(lines[i]) for i in range(start, end))


def stamp_text(text: str, url_map: dict[str, str]) -> tuple[str, int, list[str]]:
    """Return (new_text, added, unmapped_stems)."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    added = 0
    unmapped: list[str] = []
    for index, line in enumerate(lines):
        out.append(line)
        m = _TEXTBOOK_REF_RE.match(line.rstrip("\n"))
        if not m:
            continue
        stem = m.group("stem")
        if _entry_has_url(lines, index):
            continue
        url = url_map.get(stem)
        if not url:
            unmapped.append(stem)
            continue
        newline = "\n" if line.endswith("\n") else ""
        out.append(f'{m.group("indent")}url: "{url}"{newline}')
        added += 1
    return "".join(out), added, unmapped


def run(level: str, *, apply: bool) -> int:
    url_map = load_url_map()
    level_dir = CURRICULUM_ROOT / level
    total_added = 0
    unmapped: set[str] = set()
    changed_files = 0
    for res in sorted(level_dir.glob("*/resources.yaml")):
        original = res.read_text(encoding="utf-8")
        new_text, added, misses = stamp_text(original, url_map)
        unmapped.update(misses)
        if added:
            total_added += added
            changed_files += 1
            if apply:
                res.write_text(new_text, encoding="utf-8")
    verb = "Stamped" if apply else "Would stamp"
    print(f"{verb} {total_added} textbook url(s) across {changed_files} files (level {level}).")
    if unmapped:
        print(f"\n⚠️  {len(unmapped)} textbook stem(s) with NO url mapping — add to {URL_MAP_PATH.name}:")
        for stem in sorted(unmapped):
            print(f"  {stem}")
    return total_added


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", required=True, help="Level id, e.g. b1")
    parser.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    args = parser.parse_args()
    run(args.level, apply=args.apply)


if __name__ == "__main__":
    main()
